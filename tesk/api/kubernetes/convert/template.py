"""Create template for kubernetes objects."""

import logging
import uuid
from typing import Iterable

from kubernetes.client import (
    V1Container,
    V1EnvVar,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ResourceRequirements,
    V1SecretVolumeSource,
    V1Volume,
    V1VolumeMount,
)
from kubernetes.client.models import V1Job

from tesk.api.kubernetes.constants import Constants, K8sConstants
from tesk.constants import TeskConstants
from tesk.custom_config import TaskmasterEnvProperties
from tesk.utils import get_taskmaster_env_property, get_taskmaster_template

logger = logging.getLogger(__name__)


class KubernetesTemplateSupplier:
    """Templates for tasmaster's and executor's job object.."""

    def __init__(
        self,
        # security_context=None
    ):
        """Initialize the converter."""
        self.taskmaster_template: V1Job = get_taskmaster_template()
        self.taskmaster_env_properties: TaskmasterEnvProperties = (
            get_taskmaster_env_property()
        )
        self.constants = Constants()
        self.k8s_constants = K8sConstants()
        self.tesk_constants = TeskConstants()
        self.namespace = self.tesk_constants.tesk_namespace
        # self.security_context = security_context

    def get_taskmaster_name(self) -> str:
        """Generate a unique name for the taskmaster job."""
        name: str = self.constants.job_name_taskm_prefix + str(uuid.uuid4())
        return name

    def get_taskmaster_template_with_value_from_config(self) -> V1Job:
        """Create a template for the taskmaster job."""
        job: V1Job = self.taskmaster_template

        if job.spec is None:
            job.spec = V1JobSpec(template=V1PodTemplateSpec())
        if job.spec.template.spec is None:
            job.spec.template.spec = V1PodSpec(containers=[])

        job.spec.template.spec.service_account_name = (
            self.taskmaster_env_properties.serviceAccountName
        )

        container = job.spec.template.spec.containers[0]
        container.image = (
            f"{self.taskmaster_env_properties.imageName}:"
            f"{self.taskmaster_env_properties.imageVersion}"
        )

        assert isinstance(container.args, Iterable)

        container.args.extend(
            [
                "-n",
                self.namespace,
                "-fn",
                self.taskmaster_env_properties.filerImageName,
                "-fv",
                self.taskmaster_env_properties.filerImageVersion,
            ]
        )

        if self.taskmaster_env_properties.debug:
            container.args.append("-d")
            container.image_pull_policy = "Always"

        if job.metadata is None:
            job.metadata = V1ObjectMeta(labels={})

        if job.metadata.labels is None:
            job.metadata.labels = V1ObjectMeta()

        job.metadata.labels[self.constants.label_jobtype_key] = (
            self.constants.label_jobtype_value_taskm
        )
        taskmaster_name = self.get_taskmaster_name()
        job.metadata.name = taskmaster_name
        container.name = taskmaster_name

        assert isinstance(container.env, Iterable)

        if container.env is None:
            container.env = V1EnvVar()

        if self.taskmaster_env_properties:
            container.env.extend(
                [
                    V1EnvVar(name=key.upper().replace(".", "_"), value=value)
                    for key, value in self.taskmaster_env_properties.environment.items()
                ]
            )

        # Set backoff env variables for `filer` and `executor`
        backoff_limits = {
            self.constants.filer_backoff_limit: self.tesk_constants.filer_backoff_limit,
            self.constants.executor_backoff_limit: self.tesk_constants.executor_backoff_limit,
        }
        container.env.extend(
            [V1EnvVar(name=key, value=value) for key, value in backoff_limits.items()]
        )

        ftp_secrets = [
            self.constants.ftp_secret_username_env,
            self.constants.ftp_secret_password_env,
        ]
        container.env = [
            env
            for env in container.env
            if env.name not in ftp_secrets or self.taskmaster_env_properties.ftp.enabled
        ]

        if self.taskmaster_env_properties.ftp.enabled:
            for env in container.env:
                if env.name in ftp_secrets:
                    assert env.value_from is not None
                    assert env.value_from.secret_key_ref is not None
                    env.value_from.secret_key_ref.name = (
                        self.taskmaster_env_properties.ftp.secretName
                    )

        return job

    def get_executor_template_with_value_from_config(self) -> V1Job:
        """Create a template for the executor job."""
        container = V1Container(
            name=self.constants.label_jobtype_value_exec,
            resources=V1ResourceRequirements(),
        )

        if self.taskmaster_env_properties.executorSecret is not None:
            container.volume_mounts = [
                V1VolumeMount(
                    read_only=True,
                    name=str(self.taskmaster_env_properties.executorSecret.name),
                    mount_path=str(
                        self.taskmaster_env_properties.executorSecret.mountPath
                    ),
                )
            ]

        pod_spec = V1PodSpec(
            containers=[container],
            restart_policy=self.k8s_constants.job_restart_policy,
        )

        # if self.security_context:
        #     pod_spec.security_context = self.security_context

        job = V1Job(
            api_version=self.k8s_constants.k8s_batch_api_version,
            kind=self.k8s_constants.k8s_batch_api_job_type,
            metadata=V1ObjectMeta(
                labels={
                    self.constants.label_jobtype_key: (
                        self.constants.label_jobtype_value_exec
                    )
                }
            ),
            spec=V1JobSpec(
                template=V1PodTemplateSpec(metadata=V1ObjectMeta(), spec=pod_spec)
            ),
        )

        if self.taskmaster_env_properties.executorSecret is not None:
            if job.spec is None:
                job.spec = V1JobSpec(template=V1PodTemplateSpec())
            if job.spec.template.spec is None:
                job.spec.template.spec = V1PodSpec(containers=[])

            job.spec.template.spec.volumes = [
                V1Volume(
                    name=str(self.taskmaster_env_properties.executorSecret.name),
                    secret=V1SecretVolumeSource(
                        secret_name=self.taskmaster_env_properties.executorSecret.name
                    ),
                )
            ]

        job.spec.template.spec.containers[0].restart_policy = "Never"

        return job
