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
    TesResources,
    TesTask,
)
from tesk.custom_config import Taskmaster
from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.data.job import Job
from tesk.k8s.converter.data.task import Task
from tesk.k8s.converter.executor_command_wrapper import ExecutorCommandWrapper
from tesk.k8s.converter.template import KubernetesTemplateSupplier
from tesk.k8s.wrapper import KubernetesClientWrapper
from tesk.utils import (
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
