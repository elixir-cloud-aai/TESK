"""Module for converting TES tasks to Kubernetes jobs."""

import base64
import gzip
import json
import logging
from decimal import Decimal
from io import BytesIO
from typing import Any, Optional

from kubernetes.client import (
    V1ConfigMap,
    V1ConfigMapVolumeSource,
    V1Container,
    V1EnvVar,
    V1JobSpec,
    V1JobStatus,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
    V1Volume,
)
from kubernetes.client.models import V1Job
from kubernetes.utils.quantity import parse_quantity  # type: ignore

from tesk.api.ga4gh.tes.models import (
    TesExecutor,
    TesExecutorLog,
    TesResources,
    TesState,
    TesTask,
    TesTaskLog,
)
from tesk.api.kubernetes.client_wrapper import KubernetesClientWrapper
from tesk.api.kubernetes.constants import Constants, K8sConstants
from tesk.api.kubernetes.convert.data.job import Job, JobStatus
from tesk.api.kubernetes.convert.data.task import Task
from tesk.api.kubernetes.convert.executor_command_wrapper import ExecutorCommandWrapper
from tesk.api.kubernetes.convert.template import KubernetesTemplateSupplier
from tesk.custom_config import TaskmasterEnvProperties
from tesk.utils import (
    decimal_to_float,
    enum_to_string,
    get_taskmaster_env_property,
    pydantic_model_list_dict,
    time_formatter,
)

logger = logging.getLogger(__name__)


class TesKubernetesConverter:
    """Convert TES requests to Kubernetes resources."""

    def __init__(self):
        """Initialize the converter."""
        self.taskmaster_env_properties: TaskmasterEnvProperties = (
            get_taskmaster_env_property()
        )
        self.template_supplier = KubernetesTemplateSupplier()
        self.constants = Constants()
        self.k8s_constants = K8sConstants()
        self.kubernetes_client_wrapper = KubernetesClientWrapper()

    def from_tes_task_to_k8s_job(self, task: TesTask):
        """Convert TES task to Kubernetes job."""
        taskmaster_job: V1Job = (
            self.template_supplier.get_taskmaster_template_with_value_from_config()
        )

        if taskmaster_job.metadata is None:
            taskmaster_job.metadata = V1ObjectMeta()

        if taskmaster_job.metadata.annotations is None:
            taskmaster_job.metadata.annotations = {}

        if taskmaster_job.metadata.labels is None:
            taskmaster_job.metadata.labels = {}

        # taskmaster_job.metadata.name = task.name
        if task.name:
            taskmaster_job.metadata.annotations[self.constants.ann_testask_name_key] = (
                task.name
            )
        # taskmaster_job.metadata.labels[self.constants.label_userid_key] = user[
        #     "username"
        # ]

        # if task.tags and "GROUP_NAME" in task.tags:
        #     taskmaster_job.metadata.labels[self.constants.label_userid_key] = task[
        #         "tags"
        #     ]["GROUP_NAME"]
        # elif user["is_member"]:
        #     taskmaster_job.metadata.labels[self.constants.label_groupname_key] = user[
        #         "any_group"
        #     ]

        # Convert Pydantic model to dictionary
        task_dict = task.dict()

        # Serialize to JSON with indentation
        json_input = json.dumps(task_dict, indent=2, default=enum_to_string)

        try:
            taskmaster_job.metadata.annotations[self.constants.ann_json_input_key] = (
                json_input
            )
        except Exception as ex:
            logger.info(
                f"Serializing task {taskmaster_job.metadata.name} to JSON failed", ex
            )

        volume = V1Volume(
            name="jsoninput",
            config_map=V1ConfigMapVolumeSource(name=taskmaster_job.metadata.name),
        )

        if taskmaster_job.spec is None:
            taskmaster_job.spec = V1JobSpec(template=V1PodTemplateSpec())
        if taskmaster_job.spec.template.spec is None:
            taskmaster_job.spec.template.spec = V1PodSpec(containers=[])
        if taskmaster_job.spec.template.spec.volumes is None:
            taskmaster_job.spec.template.spec.volumes = []

        taskmaster_job.spec.template.spec.volumes.append(volume)
        return taskmaster_job

    def from_tes_task_to_k8s_config_map(
        self,
        task: TesTask,
        taskmaster_job: V1Job,
        # user,
    ) -> V1ConfigMap:
        """Create a Kubernetes ConfigMap from a TES task."""
        assert taskmaster_job.metadata is not None, (
            "Taskmaster job metadata should have already been set while create"
            " taskmaster!"
        )

        taskmaster_config_map = V1ConfigMap(
            metadata=V1ObjectMeta(name=taskmaster_job.metadata.name)
        )

        assert (
            taskmaster_config_map.metadata is not None
        ), "Taskmaster metadata is should have already been set!"

        if taskmaster_config_map.metadata.labels is None:
            taskmaster_config_map.metadata.labels = {}

        if taskmaster_config_map.metadata.annotations is None:
            taskmaster_config_map.metadata.annotations = {}

        # FIXME: Figure out what to do if task.name is none.
        task_name = task.name or "String"

        taskmaster_config_map.metadata.annotations[
            self.constants.ann_testask_name_key
        ] = task_name

        # taskmaster_config_map.metadata.labels[self.constants.label_userid_key]
        # = user["username"]

        if task.tags and "GROUP_NAME" in task.tags:
            taskmaster_config_map.metadata.labels[
                self.constants.label_groupname_key
            ] = task.tags["GROUP_NAME"]
        # elif user["is_member"]:
        #     taskmaster_config_map.metadata.labels[self.constants.label_groupname_key]
        #       = user["any_group"]

        assert taskmaster_config_map.metadata.name is not None
        assert task.resources is not None

        executors_as_jobs = [
            self.from_tes_executor_to_k8s_job(
                generated_task_id=taskmaster_config_map.metadata.name,
                tes_task_name=task_name,
                executor=executor,
                executor_index=idx,
                resources=task.resources,
                # user=user,
            )
            for idx, executor in enumerate(task.executors)
        ]

        print("nice")
        print(task)
        print(task.volumes)
        print("nice")

        taskmaster_input: dict[str, Any] = {
            "inputs": pydantic_model_list_dict(task.inputs) if task.inputs else [],
            "outputs": pydantic_model_list_dict(task.outputs) if task.outputs else [],
            "volumes": task.volumes or [],
            "resources": {
                "disk_gb": float(task.resources.disk_gb)
                if task.resources.disk_gb
                else 10.0
            },
        }
        print(taskmaster_input)
        taskmaster_input[self.constants.taskmaster_input_exec_key] = [
            exec_job.to_dict() for exec_job in executors_as_jobs
        ]

        print(taskmaster_input)
        taskmaster_input_as_json = json.loads(
            json.dumps(taskmaster_input, default=decimal_to_float)
        )
        print(taskmaster_input_as_json)

        try:
            with BytesIO() as obj:
                with gzip.GzipFile(fileobj=obj, mode="wb") as gzip_file:
                    json_data = json.dumps(taskmaster_input_as_json)
                    gzip_file.write(json_data.encode("utf-8"))
                taskmaster_config_map.binary_data = {
                    f"{self.constants.taskmaster_input}.gz": base64.b64encode(
                        obj.getvalue()
                    ).decode("utf-8")
                }
        except Exception as e:
            logger.info(
                (
                    f"Compression of task {taskmaster_config_map.metadata.name}"
                    f" JSON configmap failed"
                ),
                e,
            )

        return taskmaster_config_map

    def from_tes_executor_to_k8s_job(  # noqa: PLR0913
        self,
        generated_task_id: str,
        tes_task_name: Optional[str],
        executor: TesExecutor,
        executor_index: int,
        resources: TesResources,
        # user: User
    ) -> V1Job:
        """Create a Kubernetes job from a TES executor."""
        # Get new template executor Job object
        executor_job: V1Job = (
            self.template_supplier.get_executor_template_with_value_from_config()
        )

        # Set executors name based on taskmaster's job name
        Job(executor_job).change_job_name(Task(taskmaster_name=generated_task_id).get_executor_name(executor_index))

        if executor_job.metadata is None:
            executor_job.metadata = V1ObjectMeta()

        # Put arbitrary labels and annotations
        executor_job.metadata.labels = executor_job.metadata.labels or {}
        executor_job.metadata.labels[self.constants.label_testask_id_key] = (
            generated_task_id
        )
        executor_job.metadata.labels[self.constants.label_execno_key] = str(
            executor_index
        )
        # job.metadata.labels[self.constants.label_userid_key] = user.username

        if executor_job.metadata is None:
            executor_job.metadata = V1ObjectMeta()
        if executor_job.metadata.annotations is None:
            executor_job.metadata.annotations = {}

        if tes_task_name:
            executor_job.metadata.annotations[self.constants.ann_testask_name_key] = (
                tes_task_name
            )

        if executor_job.spec is None:
            executor_job.spec = V1JobSpec(template=V1PodTemplateSpec())
        if executor_job.spec.template.spec is None:
            executor_job.spec.template.spec = V1PodSpec(containers=[])

        container: V1Container = executor_job.spec.template.spec.containers[0]

        # TODO: Not sure what to do with this
        # Convert potential TRS URI into docker image
        container.image = executor.image

        if not container.command:
            container.command = []

        for command in ExecutorCommandWrapper(
            executor
        ).get_commands_with_stream_redirects():
            container.command.append(command)

        if executor.env:
            container.env = [
                V1EnvVar(name=key, value=value) for key, value in executor.env.items()
            ]
        else:
            container.env = []

        container.working_dir = executor.workdir
        container.resources = V1ResourceRequirements(requests={})

        assert container.resources.requests is not None

        if resources.cpu_cores:
            container.resources.requests["cpu"] = parse_quantity(
                str(resources.cpu_cores)
            )

        if resources.ram_gb:
            container.resources.requests["memory"] = parse_quantity(
                f"{resources.ram_gb:.6f}Gi"
            )

            # # Workaround
            # # Check if volumes is None and set it to an empty list if it is
            # if (
            #     executor_job.spec
            #     and executor_job.spec.spec
            #     and executor_job.spec.spec.volumes is None
            # ):
            #     executor_job.spec.spec.volumes = []

        return executor_job

    def is_job_in_status(tested_object: V1JobStatus, test_objective: JobStatus) -> bool:
        no_of_pods_in_state = None
        if test_objective == JobStatus.ACTIVE:
            no_of_pods_in_state = tested_object.active
        elif test_objective == JobStatus.SUCCEEDED:
            no_of_pods_in_state = tested_object.succeeded
        elif test_objective == JobStatus.FAILED:
            if tested_object.succeeded is not None and tested_object.succeeded > 0:
                return False
            no_of_pods_in_state = tested_object.failed

        return no_of_pods_in_state is not None and no_of_pods_in_state > 0

    def extract_state_from_k8s_jobs(self, taskmaster_with_executors: Task) -> TesState:
        # taskmaster_job: V1Job = taskmaster_with_executors.get_taskmaster().get_job()
        # last_executor: Optional[Job] = taskmaster_with_executors.get_last_executor()
        # output_filer: Optional[Job] = taskmaster_with_executors.get_output_filer()
        # taskmaster_cancelled = (
        #     taskmaster_job.metadata.labels.get(self.constants.label_taskstate_key)
        #     == self.constants.label_taskstate_value_canc
        # )
        # taskmaster_running = self.is_job_in_status(
        #     tested_object=taskmaster_job.status,
        #     test_objective=JobStatus.ACTIVE
        # )
        # print(taskmaster_running)
        # taskmaster_completed = self.is_job_in_status(
        #     taskmaster_job.status, JobStatus.SUCCEEDED
        # )
        # print(taskmaster_completed)
        # executor_present = last_executor is not None
        # last_executor_failed = executor_present and self.is_job_in_status(
        #     last_executor.get_job().status, JobStatus.FAILED
        # )
        # print(last_executor_failed)
        # last_executor_completed = executor_present and self.is_job_in_status(
        #     last_executor.get_job().status, JobStatus.SUCCEEDED
        # )
        # print(last_executor_completed)
        # output_filer_failed = output_filer is not None and self.is_job_in_status(
        #     output_filer.get_job().status, JobStatus.FAILED
        # )
        # print(output_filer_failed)
        # pending = self.k8s_constants.PodPhase.PENDING
        # taskmaster_pending = any(
        #     pod.status.phase == pending
        #     for pod in taskmaster_with_executors.get_taskmaster().get_pods()
        # )
        # last_executor_pending = executor_present and any(
        #     pod.status.phase == pending for pod in last_executor.get_pods()
        # )

        # if taskmaster_cancelled:
        #     return TesState.CANCELED
        # if taskmaster_completed and output_filer_failed:
        #     return TesState.SYSTEM_ERROR
        # if taskmaster_completed and last_executor_completed:
        #     return TesState.COMPLETE
        # if taskmaster_completed and last_executor_failed:
        #     return TesState.EXECUTOR_ERROR
        # if taskmaster_pending:
        #     return TesState.QUEUED
        # if taskmaster_running and not executor_present:
        #     return TesState.INITIALIZING
        # if last_executor_pending:
        #     return TesState.QUEUED
        # if taskmaster_running:
        #     return TesState.RUNNING
        return TesState.SYSTEM_ERROR

    def extract_executor_log_from_k8s_job_and_pod(
        self, executor: Job
    ) -> TesExecutorLog:
        """Extracts TesExecutorLog from executor job and pod objects.

        Does not contain stdout (which needs access to pod log).
        """
        log = TesExecutorLog()
        executor_job: V1Job = executor.get_job()
        start_time = getattr(executor_job.status, "start_time", None)
        log.start_time = time_formatter(start_time)

        end_time = getattr(executor_job.status, "completion_time", None)
        log.end_time = time_formatter(end_time)

        log.stdout = ""

        if executor.has_pods():
            first_pod_status = getattr(executor.get_first_pod(), "status", None)
            exit_code = None

            if first_pod_status:
                container_statuses = getattr(first_pod_status, "container_statuses", [])
                if container_statuses:
                    container_status = container_statuses[0]
                    container_state = getattr(container_status, "state", None)
                    if container_state:
                        terminated = getattr(container_state, "terminated", None)
                        if terminated:
                            exit_code = getattr(terminated, "exit_code", None)

            log.exit_code = exit_code

        return log

    def from_k8s_jobs_to_tes_task_minimal(
        self, taskmaster_with_executors: Task, is_list: bool
    ) -> TesTask:
        """Convert Kubernetes jobs to TES task."""

        executors = taskmaster_with_executors.get_executors()
        task = TesTask(
            # FIXME: I don't think this is it :'(
            executors=[
                TesExecutor(
                    image=executor.image or None, command=executor.command or None
                )
                for executor in executors
            ]
        )
        metadata: V1ObjectMeta = (
            taskmaster_with_executors.get_taskmaster().get_job().metadata
        )
        task.id = metadata.name
        task.state = self.extract_state_from_k8s_jobs(taskmaster_with_executors)
        if not is_list:
            # FIXME: This is a hack, we need to get the real values
            log = TesTaskLog(logs=TesExecutorLog(exit_code=0))
            task.logs.append(log)
            metadata = taskmaster_with_executors.taskmaster.job["metadata"]["labels"]
            log.metadata["USER_ID"] = metadata[self.constants.label_userid_key]
            if self.constants.label_groupname_key in metadata:
                log.metadata["GROUP_NAME"] = metadata[
                    self.constants.label_groupname_key
                ]
        return task

    def from_k8s_jobs_to_tes_task_basic(
        self, taskmaster_with_executors: Task, nullify_input_content: bool
    ) -> TesTask:
        task = TesTask()
        taskmaster_job: V1Job = taskmaster_with_executors.taskmaster.job
        taskmaster_job_metadata: V1ObjectMeta = taskmaster_job.metadata
        input_json = (taskmaster_job_metadata.annotations or {}).get(
            self.constants.ann_json_input_key, ""
        )
        try:
            task = TesTask.parse_raw(input_json)
            if nullify_input_content and task.inputs:
                for input_item in task.inputs:
                    input_item["content"] = None
        except json.JSONDecodeError as ex:
            print(
                f"Deserializing task {taskmaster_job_metadata['name']} from JSON failed; {ex}"
            )

        task.id = taskmaster_job_metadata["name"]
        task.state = self.extract_state_from_k8s_jobs(taskmaster_with_executors)
        task.creation_time = time_formatter(
            taskmaster_job_metadata["creation_timestamp"]
        )
        log = TesTaskLog()
        task.logs.append(log)
        log.metadata["USER_ID"] = taskmaster_job_metadata["labels"][
            self.constants.label_userid_key
        ]
        if self.constants.label_groupname_key in taskmaster_job_metadata["labels"]:
            log["GROUP_NAME"] = taskmaster_job_metadata["labels"][
                self.constants.label_groupname_key
            ]
        log.start_time = (
            time_formatter(taskmaster_job.status.start_time)
            if taskmaster_job.status.start_time
            else None
        )
        log.end_time = (
            time_formatter(taskmaster_job.status.completion_time)
            if taskmaster_job.status.completion_time
            else None
        )
        for executor_job in taskmaster_with_executors.get_executors():
            executor_log = self.extract_executor_log_from_k8s_job_and_pod(executor_job)
            task.logs.append(executor_log)
        return task
