"""Utility functions for the TESK package."""

import os
from pathlib import Path

from foca import Foca
from kubernetes.client.models import (
    V1Container,
    V1EnvVar,
    V1EnvVarSource,
    V1Job,
    V1JobSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1SecretKeySelector,
    V1VolumeMount,
)

from tesk.api.kubernetes.constants import Constants, K8sConstants
from tesk.custom_config import (
    CustomConfig,
    TaskmasterEnvProperties,
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
    job = V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=V1ObjectMeta(name="taskmaster", labels={"app": "taskmaster"}),
        spec=V1JobSpec(
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(name="taskmaster"),
                spec=V1PodSpec(
                    service_account_name="default",
                    containers=[
                        V1Container(
                            name="taskmaster",
                            image="docker.io/elixircloud/tesk-core-taskmaster:v0.10.2",
                            args=["-f", f"/jsoninput/{Constants.taskmaster_input}.gz"],
                            env=[
                                V1EnvVar(
                                    name=Constants.ftp_secret_username_env,
                                    value_from=V1EnvVarSource(
                                        secret_key_ref=V1SecretKeySelector(
                                            name="ftp-secret",
                                            key="username",
                                            optional=True,
                                        )
                                    ),
                                ),
                                V1EnvVar(
                                    name=Constants.ftp_secret_password_env,
                                    value_from=V1EnvVarSource(
                                        secret_key_ref=V1SecretKeySelector(
                                            name="ftp-secret",
                                            key="password",
                                            optional=True,
                                        )
                                    ),
                                ),
                            ],
                            volume_mounts=[
                                V1VolumeMount(
                                    name="podinfo",
                                    mount_path="/podinfo",
                                    read_only=True,
                                ),
                                V1VolumeMount(
                                    name="jsoninput",
                                    mount_path="/jsoninput",
                                    read_only=True,
                                ),
                            ],
                        )
                    ],
                    volumes=[],
                    restart_policy=K8sConstants.job_restart_policy,
                ),
            )
        ),
    )
    return job


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
