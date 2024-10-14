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

from tesk.constants import tesk_constants
from tesk.custom_config import Taskmaster
from tesk.k8s.constants import tesk_k8s_constants
from tesk.utils import get_taskmaster_env_property, get_taskmaster_template

logger = logging.getLogger(__name__)


class KubernetesTemplateSupplier:
    """Templates for tasmaster's and executor's job object.

    Attributes:
        taskmaster_template: template for the taskmaster job
        taskmaster: taskmaster environment properties
        tesk_k8s_constants: TESK Kubernetes constants
        tesk_constants: TESK constants
    """

    def __init__(
        self,
    ):
        """Initialize the converter.

        Args:
            taskmaster_template: template for the taskmaster job
            taskmaster: taskmaster environment properties
            tesk_k8s_constants: TESK Kubernetes constants
            tesk_constants: TESK constants
        """
        self.taskmaster_template: V1Job = get_taskmaster_template()
        self.taskmaster: Taskmaster = get_taskmaster_env_property()
        self.tesk_k8s_constants = tesk_k8s_constants
        self.tesk_constants = tesk_constants

    def get_taskmaster_name(self) -> str:
        """Generate a unique name for the taskmaster job."""
        name: str = self.tesk_k8s_constants.job_constants.JOB_NAME_TASKM_PREFIX + str(
            uuid.uuid4()
        )
        return name

    def get_taskmaster_template_with_value_from_config(self) -> V1Job:
        """Create a template for the taskmaster job.

        Returns:
            V1Job: template for the taskmaster job with values from config
        """
        job: V1Job = self.taskmaster_template

        if job.spec is None:
            job.spec = V1JobSpec(template=V1PodTemplateSpec())
        if job.spec.template.spec is None:
            job.spec.template.spec = V1PodSpec(containers=[])

        job.spec.template.spec.service_account_name = self.taskmaster.serviceAccountName

        container = job.spec.template.spec.containers[0]
        container.image = (
            f"{self.taskmaster.imageName}:" f"{self.taskmaster.imageVersion}"
        )

        assert isinstance(container.args, Iterable)

        container.args.extend(
            [
                "-n",
                self.tesk_constants.TESK_NAMESPACE,
                "-fn",
                self.taskmaster.filerImageName,
                "-fv",
                self.taskmaster.filerImageVersion,
            ]
        )

        if self.taskmaster.debug:
            container.args.append("-d")
            container.image_pull_policy = "Always"

        if job.metadata is None:
            job.metadata = V1ObjectMeta(labels={})

        if job.metadata.labels is None:
            job.metadata.labels = {}

        job.metadata.labels[
            self.tesk_k8s_constants.label_constants.LABEL_JOBTYPE_KEY
        ] = self.tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_TASKM

        # Assign a unique name to the taskmaster job
        taskmaster_name = self.get_taskmaster_name()
        job.metadata.name = taskmaster_name
        container.name = taskmaster_name

        assert isinstance(container.env, Iterable)

        if container.env is None:
            container.env = V1EnvVar()

        if self.taskmaster and self.taskmaster.environment:
            container.env.extend(
                [
                    V1EnvVar(name=key.upper().replace(".", "_"), value=value)
                    for key, value in self.taskmaster.environment.items()
                ]
            )

        # Set backoff env variables for `filer` and `executor`
        backoff_limits = {
            self.tesk_k8s_constants.job_constants.FILER_BACKOFF_LIMIT: self.tesk_constants.FILER_BACKOFF_LIMIT,  # noqa: E501
            self.tesk_k8s_constants.job_constants.EXECUTOR_BACKOFF_LIMIT: self.tesk_constants.EXECUTOR_BACKOFF_LIMIT,  # noqa: E501
        }

        container.env.extend(
            [V1EnvVar(name=key, value=value) for key, value in backoff_limits.items()]
        )

        ftp_secrets = [
            self.tesk_k8s_constants.ftp_constants.FTP_SECRET_USERNAME_ENV,
            self.tesk_k8s_constants.ftp_constants.FTP_SECRET_PASSWORD_ENV,
        ]
        container.env = [
            env
            for env in container.env
            if env.name not in ftp_secrets or self.taskmaster.ftp.enabled
        ]

        if self.taskmaster.ftp.enabled:
            for env in container.env:
                if env.name in ftp_secrets:
                    assert env.value_from is not None
                    assert env.value_from.secret_key_ref is not None
                    env.value_from.secret_key_ref.name = self.taskmaster.ftp.secretName

        return job

    def get_executor_template_with_value_from_config(self) -> V1Job:
        """Create a template for the executor job.

        Returns:
            V1Job: template for the executor job with values from config
        """
        container = V1Container(
            name=self.tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_EXEC,
            resources=V1ResourceRequirements(),
        )

        if self.taskmaster.executorSecret is not None:
            container.volume_mounts = [
                V1VolumeMount(
                    read_only=True,
                    name=str(self.taskmaster.executorSecret.name),
                    mount_path=str(self.taskmaster.executorSecret.mountPath),
                )
            ]

        pod_spec = V1PodSpec(
            containers=[container],
            restart_policy=self.tesk_k8s_constants.k8s_constants.JOB_RESTART_POLICY,
        )

        job = V1Job(
            api_version=self.tesk_k8s_constants.k8s_constants.K8S_BATCH_API_VERSION,
            kind=self.tesk_k8s_constants.k8s_constants.K8S_BATCH_API_JOB_TYPE,
            metadata=V1ObjectMeta(
                labels={
                    self.tesk_k8s_constants.label_constants.LABEL_JOBTYPE_KEY: (
                        self.tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_EXEC
                    )
                }
            ),
            spec=V1JobSpec(
                template=V1PodTemplateSpec(metadata=V1ObjectMeta(), spec=pod_spec)
            ),
        )

        if self.taskmaster.executorSecret is not None:
            if job.spec is None:
                job.spec = V1JobSpec(template=V1PodTemplateSpec())
            if job.spec.template.spec is None:
                job.spec.template.spec = V1PodSpec(containers=[])

            job.spec.template.spec.volumes = [
                V1Volume(
                    name=str(self.taskmaster.executorSecret.name),
                    secret=V1SecretVolumeSource(
                        secret_name=self.taskmaster.executorSecret.name
                    ),
                )
            ]

        assert job.spec is not None
        assert job.spec.template.spec is not None

        return job
