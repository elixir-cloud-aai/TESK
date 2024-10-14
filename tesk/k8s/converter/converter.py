"""Module for converting TES tasks to Kubernetes jobs."""

import base64
import gzip
import json
import logging
from decimal import Decimal
from enum import Enum
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
    V1PodList,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
    V1Volume,
)
from kubernetes.client.models import V1Job
from kubernetes.utils.quantity import parse_quantity  # type: ignore
from pydantic import ValidationError

from tesk.api.ga4gh.tes.models import (
    TesExecutor,
    TesExecutorLog,
    TesResources,
    TesState,
    TesTask,
    TesTaskLog,
    TesTaskMinimal,
)
from tesk.custom_config import Taskmaster
from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.data.job import Job, JobStatus
from tesk.k8s.converter.data.task import Task
from tesk.k8s.converter.executor_command_wrapper import ExecutorCommandWrapper
from tesk.k8s.converter.template import KubernetesTemplateSupplier
from tesk.k8s.wrapper import KubernetesClientWrapper
from tesk.utils import (
    format_datetime,
    get_taskmaster_env_property,
    pydantic_model_list_dict,
)

logger = logging.getLogger(__name__)


class TesKubernetesConverter:
    """Convert TES requests to Kubernetes resources.

    Attributes:
        taskmaster_env_properties: taskmaster environment properties
        template_supplier: Kubernetes template supplier
        tesk_k8s_constants: TESK Kubernetes constants
        kubernetes_client_wrapper: Kubernetes client wrapper
    """

    def __init__(self):
        """Initialize the converter.

        Args:
            taskmaster_env_properties: taskmaster environment properties
            template_supplier: Kubernetes template supplier
            tesk_k8s_constants: TESK Kubernetes constants
            kubernetes_client_wrapper: Kubernetes client wrapper
        """
        self.taskmaster_env_properties: Taskmaster = get_taskmaster_env_property()
        self.template_supplier = KubernetesTemplateSupplier()
        self.tesk_k8s_constants = tesk_k8s_constants
        self.kubernetes_client_wrapper = KubernetesClientWrapper()

    def from_tes_task_to_k8s_job(self, task: TesTask) -> V1Job:
        """Convert TES task to Kubernetes job.

        Args:
            task: TES task

        Returns:
            V1Job: Kubernetes job, taskmaster job
        """
        taskmaster_job: V1Job = (
            self.template_supplier.get_taskmaster_template_with_value_from_config()
        )

        if taskmaster_job.metadata is None:
            taskmaster_job.metadata = V1ObjectMeta()

        if taskmaster_job.metadata.annotations is None:
            taskmaster_job.metadata.annotations = {}

        if taskmaster_job.metadata.labels is None:
            taskmaster_job.metadata.labels = {}

        if task.name:
            taskmaster_job.metadata.annotations[
                self.tesk_k8s_constants.annotation_constants.ANN_TESTASK_NAME_KEY
            ] = task.name

        json_input = json.dumps(
            task.dict(),
            indent=2,
            default=lambda enum: str(enum.name) if isinstance(enum, Enum) else None,
        )

        try:
            taskmaster_job.metadata.annotations[
                self.tesk_k8s_constants.annotation_constants.ANN_JSON_INPUT_KEY
            ] = json_input
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
    ) -> V1ConfigMap:
        """Create a Kubernetes ConfigMap from a TES task.

        Args:
            task: TES task
            taskmaster_job: Kubernetes job

        Returns:
            V1ConfigMap: Kubernetes ConfigMap
        """
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

        task_name = task.name or "String"

        taskmaster_config_map.metadata.annotations[
            self.tesk_k8s_constants.annotation_constants.ANN_TESTASK_NAME_KEY
        ] = task_name

        if task.tags and "GROUP_NAME" in task.tags:
            taskmaster_config_map.metadata.labels[
                self.tesk_k8s_constants.label_constants.LABEL_GROUPNAME_KEY
            ] = task.tags["GROUP_NAME"]

        assert taskmaster_config_map.metadata.name is not None
        assert task.resources is not None

        executors_as_jobs = [
            self.from_tes_executor_to_k8s_job(
                generated_task_id=taskmaster_config_map.metadata.name,
                tes_task_name=task_name,
                executor=executor,
                executor_index=idx,
                resources=task.resources,
            )
            for idx, executor in enumerate(task.executors)
        ]

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
        taskmaster_input[
            self.tesk_k8s_constants.job_constants.TASKMASTER_INPUT_EXEC_KEY
        ] = [exec_job.to_dict() for exec_job in executors_as_jobs]

        taskmaster_input_as_json = json.loads(
            json.dumps(
                taskmaster_input,
                default=lambda obj: float(obj)
                if isinstance(obj, Decimal)
                else TypeError,
            )
        )

        try:
            with BytesIO() as obj:
                with gzip.GzipFile(fileobj=obj, mode="wb") as gzip_file:
                    json_data = json.dumps(taskmaster_input_as_json)
                    gzip_file.write(json_data.encode("utf-8"))
                taskmaster_config_map.binary_data = {
                    f"{self.tesk_k8s_constants.job_constants.TASKMASTER_INPUT}.gz": base64.b64encode(  # noqa: E501
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

    def from_tes_executor_to_k8s_job(  # noqa: PLR0913, PLR0912
        self,
        generated_task_id: str,
        tes_task_name: Optional[str],
        executor: TesExecutor,
        executor_index: int,
        resources: TesResources,
    ) -> V1Job:
        """Create a Kubernetes job from a TES executor.

        Args:
            generated_task_id: generated task ID
            tes_task_name: TES task name
            executor: TES executor
            executor_index: executor index
            resources: TES resources

        Returns:
            V1Job: Kubernetes job, executor job
        """
        # Get new template executor Job object
        executor_job: V1Job = (
            self.template_supplier.get_executor_template_with_value_from_config()
        )

        # Set executors name based on taskmaster's job name
        Job(executor_job).change_job_name(
            Task(taskmaster_name=generated_task_id).get_executor_name(executor_index)
        )

        if executor_job.metadata is None:
            executor_job.metadata = V1ObjectMeta()

        # Put arbitrary labels and annotations
        executor_job.metadata.labels = executor_job.metadata.labels or {}
        executor_job.metadata.labels[
            self.tesk_k8s_constants.label_constants.LABEL_TESTASK_ID_KEY
        ] = generated_task_id
        executor_job.metadata.labels[
            self.tesk_k8s_constants.label_constants.LABEL_EXECNO_KEY
        ] = str(executor_index)
        # job.metadata.labels[self.constants.label_userid_key] = user.username

        if executor_job.metadata is None:
            executor_job.metadata = V1ObjectMeta()
        if executor_job.metadata.annotations is None:
            executor_job.metadata.annotations = {}

        if tes_task_name:
            executor_job.metadata.annotations[
                self.tesk_k8s_constants.annotation_constants.ANN_TESTASK_NAME_KEY
            ] = tes_task_name

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

        # # FIXME: Workaround
        # # Check if volumes is None and set it to an empty list if it is
        if (
            executor_job.spec
            and executor_job.spec.template.spec
            and executor_job.spec.template.spec.volumes is None
        ):
            executor_job.spec.template.spec.volumes = []

        return executor_job

    def is_job_in_status(
        self, tested_object: V1JobStatus, test_objective: JobStatus
    ) -> bool:
        """Check if the job is in the given status.

        Args:
            tested_object: tested object, V1JobStatus of a job
            test_objective: test object, status to be checked against

        Returns:
            bool: True if the job is in the given status, False otherwise
        """
        no_of_pods_in_state: Optional[int] = None

        match test_objective:
            case JobStatus.ACTIVE:
                no_of_pods_in_state = tested_object.active()
            case JobStatus.SUCCEEDED:
                no_of_pods_in_state = tested_object.succeeded()
            case JobStatus.FAILED:
                succeeded_pods = tested_object.succeeded()
                if succeeded_pods and succeeded_pods > 0:
                    # if there are any successful, the job has not FAILED
                    return False
                no_of_pods_in_state = tested_object.failed()

        return no_of_pods_in_state is not None and no_of_pods_in_state > 0

    def extract_state_from_k8s_jobs(self, taskmaster_with_executors: Task) -> TesState:
        """Derives TES task's status from task's object graph.

        Uses status of taskmaster's and executor's jobs and taskmaster's and executor's
        pods.

        Args:
            taskmaster_with_executors: taskMaster's full object graph

        Returns:
            TesState: TES task's state
        """
        taskmaster_job = taskmaster_with_executors.get_taskmaster().get_job()
        last_executor: Optional[Job] = taskmaster_with_executors.get_last_executor()
        output_filer: Optional[Job] = taskmaster_with_executors.get_output_filer()

        taskmaster_cancelled: bool = (
            taskmaster_job.metadata.labels.get(
                self.tesk_k8s_constants.label_constants.LABEL_TASKSTATE_KEY
            )
            == self.tesk_k8s_constants.label_constants.LABEL_TASKSTATE_VALUE_CANC
        )
        taskmaster_running = self.is_job_in_status(
            taskmaster_job.status, JobStatus.ACTIVE
        )
        taskmaster_completed = self.is_job_in_status(
            taskmaster_job.status, JobStatus.SUCCEEDED
        )

        executor_present = last_executor is not None
        last_executor_failed = executor_present and self.is_job_in_status(
            last_executor.get_job().status, JobStatus.FAILED
        )
        last_executor_completed = executor_present and self.is_job_in_status(
            last_executor.get_job().status, JobStatus.SUCCEEDED
        )
        output_filer_failed = output_filer is not None and self.is_job_in_status(
            output_filer.get_job().status, JobStatus.FAILED
        )

        pending = self.tesk_k8s_constants.k8s_constants.PodPhase.PENDING.get_code()
        taskmaster_pending = any(
            pod.status.phase == pending
            for pod in taskmaster_with_executors.get_taskmaster().get_pods()
        )
        last_executor_pending = executor_present and any(
            pod.status.phase == pending for pod in last_executor.get_pods()
        )

        state = TesState.SYSTEM_ERROR

        if taskmaster_cancelled:
            state = TesState.CANCELED
        elif taskmaster_completed and output_filer_failed:
            state = TesState.SYSTEM_ERROR
        elif taskmaster_completed and last_executor_completed:
            state = TesState.COMPLETE
        elif taskmaster_completed and last_executor_failed:
            state = TesState.EXECUTOR_ERROR
        elif taskmaster_pending:
            state = TesState.QUEUED
        elif taskmaster_running and not executor_present:
            state = TesState.INITIALIZING
        elif last_executor_pending:
            state = TesState.QUEUED
        elif taskmaster_running:
            state = TesState.RUNNING

        return state

    def executor_logs_from_k8s_job_and_pod(executor: Job) -> TesExecutorLog:
        """Extracts TesExecutorLog from executor job and pod objects.

        Args:
            executor: executor job object

        Note:
            - Does not contain stdout (which needs access to pod log).
            - If exit code is not available, it is set to -1.

        Returns:
            TesExecutorLog: executor log object (part of basic and full output)
        """
        # Initialize with a sentinel value
        exit_code: int = -1

        if executor.has_pods():
            pod_status = executor.get_first_pod().status
            if pod_status:
                container_statuses = pod_status.container_statuses
                if container_statuses and len(container_statuses) > 0:
                    container_status = container_statuses[0]
                    state = container_status.state
                    if state and state.terminated:
                        exit_code = state.terminated.exit_code
        log = TesExecutorLog(exit_code=exit_code)

        executor_job = executor.get_job()

        # Set start_time and end_time with proper handling
        start_time = executor_job.status.start_time
        log.start_time = format_datetime(start_time) if start_time else None

        completion_time = executor_job.status.completion_time
        log.end_time = format_datetime(completion_time) if completion_time else None

        return log

    def from_k8s_jobs_to_tes_task_minimal(
        self, taskmaster_with_executors: Task, is_list: bool
    ) -> TesTaskMinimal:
        """Extracts a minimal view of TesTask from taskmaster's, executor's and pod.

        Minimal view of the task will only include the ID and the state of the task.

        Args:
            taskmaster_with_executors: The Task object containing Kubernetes resources.
            is_list: Flag indicating if the method is called in a list context.

        Returns:
            TesTask: The minimal TesTask object.
        """
        task_master_job = taskmaster_with_executors.get_taskmaster().get_job()

        metadata = task_master_job.metadata
        id = metadata.name

        task = TesTaskMinimal(id=id)
        task.state = self.extract_state_from_k8s_jobs(taskmaster_with_executors)

        if not is_list:
            # NOTE: Java implementation add TesTaskLog to the response here
            #       but it is not clear what it is for, assuming it is for
            #       post-authentication logging, is so it can be ommitted.
            #       cf. https://github.com/elixir-cloud-aai/tesk-api/blob/12754b840a0931d4d51a5619161f7b3684ccfded/src/main/java/uk/ac/ebi/tsc/tesk/k8s/convert/TesKubernetesConverter.java#L309C1-L317C10
            logger.info("Returning a single task")

        return task

    def from_k8s_jobs_to_tes_task_basic(
        self, taskmaster_with_executors: Task, nullify_input_content: bool
    ) -> TesTask:
        """Extracts a basic view of TesTask from taskmaster's. executors' job and pod.

        Args:
            taskmaster_with_executors: The Task object containing k8s resources.
            nullify_input_content: Flag to remove input content in the result.

        Returns:
            TesTask: The basic TesTask object.
        """
        task_master_job = taskmaster_with_executors.get_taskmaster().get_job()
        task_master_job_metadata = task_master_job.metadata
        annotations = task_master_job_metadata.annotations or {}
        input_json = annotations.get(
            self.tesk_k8s_constants.annotation_constants.ANN_JSON_INPUT_KEY, ""
        )

        try:
            if input_json:
                task = TesTask.parse_raw(input_json)
                if nullify_input_content and task.inputs:
                    for input_item in task.inputs:
                        input_item.content = None
        except ValidationError as ex:
            logger.info(
                f"Deserializing task {task_master_job_metadata.name} from JSON failed;"
                f"{ex}"
            )
            task = TesTask()

        task.id = task_master_job_metadata.name
        task.state = self.extract_state_from_k8s_jobs(taskmaster_with_executors)
        task.creation_time = (
            format_datetime(task_master_job_metadata.creation_timestamp)
            if task_master_job_metadata.creation_timestamp
            else None
        )

        # Create and append TesTaskLog
        log = TesTaskLog()
        task.logs.append(log)

        user_id = task_master_job_metadata.labels.get(
            self.tesk_k8s_constants.label_constants.LABEL_USERID_KEY
        )
        if user_id:
            log.metadata[self.tesk_k8s_constants.label_constants.LABEL_USERID_KEY] = (
                user_id
            )

        group_name = task_master_job_metadata.labels.get(
            self.tesk_k8s_constants.label_constants.LABEL_GROUPNAME_KEY
        )
        if group_name:
            log.metadata[
                self.tesk_k8s_constants.label_constants.LABEL_GROUPNAME_KEY
            ] = group_name

        # Set start_time and end_time
        start_time = task_master_job.status.start_time
        log.start_time = format_datetime(start_time) if start_time else None

        completion_time = task_master_job.status.completion_time
        log.end_time = format_datetime(completion_time) if completion_time else None

        # Extract and add executor logs
        for executor_job in taskmaster_with_executors.get_executors():
            executor_log = self.extract_executor_log_from_k8s_job_and_pod(executor_job)
            log.logs.append(executor_log)

        return task

    def get_name_of_first_running_pod(pod_list: V1PodList) -> Optional[str]:
        """Retrieves the name of the first pod in the 'Running' phase.

        Args:
            pod_list (V1PodList): The list of pods to search.

        Returns:
            Optional[str]: The name of the first running pod, or None if not found.
        """
        for pod in pod_list.items:
            if pod.status.phase == "Running":
                return pod.metadata.name
        return None
