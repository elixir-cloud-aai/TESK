"""Utility functions for the TESK package."""

import os
from pathlib import Path
from typing import List, Optional, Sequence

from foca import Foca
from kubernetes.client.models import (
    V1Container,
    V1DownwardAPIVolumeFile,
    V1DownwardAPIVolumeSource,
    V1EnvVar,
    V1EnvVarSource,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1SecretKeySelector,
    V1Volume,
    V1VolumeMount,
)
from pydantic import BaseModel

from tesk.custom_config import (
    Container,
    CustomConfig,
    DownwardAPIItem,
    EnvVar,
    EnvVarSource,
    Job,
    JobMetadata,
    JobSpec,
    PodSpec,
    PodTemplate,
    TaskmasterEnvProperties,
    Volume,
    VolumeMount,
)
from tesk.exceptions import ConfigNotFoundError


def get_config_path() -> Path:
    """Get the configuration path.

    Returns:
      The path of the config file.
    """
    # Determine the configuration path
    if config_path_env := os.getenv("TESK_FOCA_CONFIG_PATH"):
        return Path(config_path_env).resolve()
    else:
        return (Path(__file__).parents[1] / "deployment" / "config.yaml").resolve()


def get_custom_config() -> CustomConfig:
    """Get the custom configuration.

    Returns:
      The custom configuration.
    """
    conf = Foca(config_file=get_config_path()).conf
    try:
        return CustomConfig(**conf.custom)
    except AttributeError:
        raise ConfigNotFoundError(
            "Custom configuration not found in config file."
        ) from None


def get_taskmaster_template() -> V1Job:
    """Get the taskmaster template from the custom configuration.

    Returns:
      The taskmaster template.
    """
    custom_conf = get_custom_config()
    try:
        return job_to_v1job(custom_conf.taskmaster_template)
    except AttributeError:
        raise ConfigNotFoundError(
            "Custom configuration doesn't seem to have taskmaster_template in config "
            "file."
        ) from None


def get_taskmaster_env_property() -> TaskmasterEnvProperties:
    """Get the taskmaster env property from the custom configuration.

    Returns:
      The taskmaster env property.
    """
    custom_conf = get_custom_config()
    try:
        return custom_conf.taskmaster_env_properties
    except AttributeError:
        raise ConfigNotFoundError(
            "Custom configuration doesn't seem to have taskmaster_env_properties in "
            "config file."
        ) from None


def job_to_v1job(job: Job) -> V1Job:
    """Convert a pydantic job model to a V1Job object.

    Returns:
        The V1Job object.
    """

    def convert_env_var_source(
        env_var_source: Optional[EnvVarSource],
    ) -> Optional[V1EnvVarSource]:
        if env_var_source is None:
            return None
        if env_var_source.secretKeyRef:
            return V1EnvVarSource(
                secret_key_ref=V1SecretKeySelector(
                    name=env_var_source.secretKeyRef.name,
                    key=env_var_source.secretKeyRef.key,
                    optional=env_var_source.secretKeyRef.optional,
                )
            )
        return None

    def convert_downward_api_item(
        downward_api_item: DownwardAPIItem,
    ) -> V1DownwardAPIVolumeFile:
        return V1DownwardAPIVolumeFile(
            path=downward_api_item.path,
            field_ref=downward_api_item.fieldRef,
        )

    def convert_volume(volume: Volume) -> V1Volume:
        if volume.downwardAPI:
            return V1Volume(
                name=volume.name,
                downward_api=V1DownwardAPIVolumeSource(
                    items=[
                        convert_downward_api_item(item)
                        for item in volume.downwardAPI["items"]
                    ]
                ),
            )
        return V1Volume(name=volume.name)

    def convert_env_var(env_var: EnvVar) -> V1EnvVar:
        return V1EnvVar(
            name=env_var.name, value_from=convert_env_var_source(env_var.valueFrom)
        )

    def convert_volume_mount(volume_mount: VolumeMount) -> V1VolumeMount:
        return V1VolumeMount(
            name=volume_mount.name,
            mount_path=volume_mount.mountPath,
            read_only=volume_mount.readOnly,
        )

    def convert_container(container: Container) -> V1Container:
        return V1Container(
            name=container.name,
            image=container.image,
            args=container.args,
            env=[convert_env_var(env) for env in container.env],
            volume_mounts=[convert_volume_mount(vm) for vm in container.volumeMounts],
        )

    def convert_pod_spec(pod_spec: PodSpec) -> V1PodSpec:
        return V1PodSpec(
            service_account_name=pod_spec.serviceAccountName,
            containers=[
                convert_container(container) for container in pod_spec.containers
            ],
            volumes=[convert_volume(volume) for volume in pod_spec.volumes],
            restart_policy=pod_spec.restartPolicy,
        )

    def convert_pod_template(pod_template: PodTemplate) -> V1PodTemplateSpec:
        return V1PodTemplateSpec(
            metadata=V1ObjectMeta(name=pod_template.metadata.name),
            spec=convert_pod_spec(pod_template.spec),
        )

    def convert_job_spec(job_spec: JobSpec) -> V1JobSpec:
        return V1JobSpec(template=convert_pod_template(job_spec.template))

    def convert_job_metadata(job_metadata: JobMetadata) -> V1ObjectMeta:
        return V1ObjectMeta(name=job_metadata.name, labels=job_metadata.labels)

    return V1Job(
        api_version=job.apiVersion,
        kind=job.kind,
        metadata=convert_job_metadata(job.metadata),
        spec=convert_job_spec(job.spec),
    )


def pydantic_model_list_json(model_list: Sequence[BaseModel]) -> List[str]:
    """Convert a list of pydantic models to a list of JSON objects."""
    json_list = []
    for item in model_list:
        json_list.append(item.json())
    return json_list
