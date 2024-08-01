"""Module for converting TES tasks to Kubernetes jobs."""

import gzip
import json
import logging
from io import BytesIO

from kubernetes.client import (
    V1ConfigMap,
    V1ConfigMapVolumeSource,
    V1ObjectMeta,
    V1Volume,
)
from kubernetes.client.models import V1Job

from tesk.api.ga4gh.tes.models import TesExecutor, TesResources, TesTask
from tesk.api.kubernetes.constants import Constants, K8sConstants
from tesk.api.kubernetes.template import KubernetesTemplateSupplier
from tesk.constants import TeskConstants
from tesk.custom_config import TaskmasterEnvProperties
from tesk.utils import get_taskmaster_env_property, get_taskmaster_template

logger = logging.getLogger(__name__)


class TesKubernetesConverter:
    def __init__(self, namespace=TeskConstants.tesk_namespace):
        """Initialize the converter."""
        self.taskmaster_env_properties: TaskmasterEnvProperties = (
            get_taskmaster_env_property()
        )
        self.constants = Constants()
        self.k8s_constants = K8sConstants()
        self.namespace = namespace

    # TODO: Add user to the mmethod when auth implemented in FOCA
    def from_tes_task_to_k8s_job(self, task: TesTask):
        taskmsater_job: V1Job = KubernetesTemplateSupplier(
            self.namespace
        ).task_master_template()

        if taskmsater_job.metadata is None:
            taskmsater_job.metadata = V1ObjectMeta()

        if taskmsater_job.metadata.annotations is None:
            taskmsater_job.metadata.annotations = {}

        if taskmsater_job.metadata.labels is None:
            taskmsater_job.metadata.labels = {}

        taskmsater_job.metadata.annotations[self.constants.ann_testask_name_key] = (
            task.name
        )
        # taskmsater_job.metadata.labels[self.constants.label_userid_key] = user[
        #     "username"
        # ]

        # if task.tags and "GROUP_NAME" in task.tags:
        #     taskmsater_job.metadata.labels[self.constants.label_userid_key] = task[
        #         "tags"
        #     ]["GROUP_NAME"]
        # elif user["is_member"]:
        #     taskmsater_job.metadata.labels[self.constants.label_groupname_key] = user[
        #         "any_group"
        #     ]

        try:
            taskmsater_job.metadata.annotations[self.constants.ann_json_input_key] = (
                task.json()
            )
        except Exception as ex:
            logger.info(
                f"Serializing task {taskmsater_job.metadata.name} to JSON failed", ex
            )

        volume = V1Volume(
            name="jsoninput",
            config_map=V1ConfigMapVolumeSource(name=taskmsater_job.metadata.name),
        )
        taskmsater_job.spec.template.spec.volumes.append(volume)

        return taskmsater_job

    def from_tes_task_to_k8s_config_map(
        self,
        task: TesTask,
        # user,
        job,
    ):
        task_master_config_map = V1ConfigMap(
            metadata=V1ObjectMeta(name=job.metadata.name)
        )
        task_master_config_map.metadata.annotations[
            self.constants.ann_testask_name_key
        ] = task["name"]
        # task_master_config_map.metadata.labels[self.constants.label_userid_key] = user["username"]

        if "tags" in task and "GROUP_NAME" in task["tags"]:
            task_master_config_map.metadata.labels[
                self.constants.label_groupname_key
            ] = task["tags"]["GROUP_NAME"]
        # elif user["is_member"]:
        #     task_master_config_map.metadata.labels[self.constants.label_groupname_key] = user[
        #         "any_group"
        #     ]

        executors_as_jobs = [
            self.from_tes_executor_to_k8s_job(
                task_master_config_map.metadata.name,
                task["name"],
                executor,
                idx,
                task["resources"],
                # user,
            )
            for idx, executor in enumerate(task["executors"])
        ]

        task_master_input = {
            "inputs": task.inputs or [],
            "outputs": task.outputs or [],
            "volumes": task.volumes or [],
            "resources": {"disk_gb": task.resources.disk_gb or 10.0},
        }
        task_master_input[self.constants.taskmaster_input_exec_key] = executors_as_jobs

        task_master_input_as_json = json.dumps(task_master_input)
        try:
            with BytesIO() as obj:
                with gzip.GzipFile(fileobj=obj, mode="wb") as gzip_file:
                    gzip_file.write(task_master_input_as_json.encode("utf-8"))
                task_master_config_map.binary_data = {
                    f"{self.constants.taskmaster_input}.gz": obj.getvalue()
                }
        except Exception as e:
            logger.info(
                f"Compression of task {task_master_config_map.metadata.name} JSON configmap failed",
                e,
            )

        return task_master_config_map


    def from_tes_executor_to_k8s_job(
        self,
        generated_task_id: str,
        tes_task_name: str,
        executor: TesExecutor,
        executor_index: int,
        resources: TesResources,
        # user: User
    ) -> V1Job:
        # Get new template executor Job object
        job = self.executor_template_supplier()
        
        # Set executors name based on taskmaster's job name
        Job(job).change_job_name(Task(generated_task_id).get_executor_name(executor_index))
        
        # Put arbitrary labels and annotations
        job.metadata.labels = job.metadata.labels or {}
        job.metadata.labels["taskId"] = generated_task_id
        job.metadata.labels["execNo"] = str(executor_index)
        job.metadata.labels["userId"] = user.username
        
        job.metadata.annotations = job.metadata.annotations or {}
        job.metadata.annotations["tesTaskName"] = tes_task_name
        
        container = job.spec.template.spec.containers[0]
        
        # Convert potential TRS URI into docker image
        container.image = self.trs_client.get_docker_image_for_tool_version_uri(executor.image)
        
        # Map executor's command to job container's command
        for command in ExecutorCommandWrapper(executor).get_commands_with_stream_redirects():
            container.add_command_item(command)
        
        if executor.env:
            container.env = [V1EnvVar(name=key, value=value) for key, value in executor.env.items()]
        
        container.working_dir = executor.workdir
        
        if resources.cpu_cores:
            container.resources.requests['cpu'] = QuantityFormatter().parse(str(resources.cpu_cores))
        
        if resources.ram_gb:
            container.resources.requests['memory'] = QuantityFormatter().parse(f"{resources.ram_gb:.6f}Gi")
        
        return job