"""Utility functions for the TESK package."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

from foca import Foca
from kubernetes.client.models import (
    V1Container,
    V1DownwardAPIVolumeFile,
    V1DownwardAPIVolumeSource,
    V1EnvVar,
    V1EnvVarSource,
    V1Job,
    V1JobSpec,
    V1ObjectFieldSelector,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1SecretKeySelector,
    V1Volume,
    V1VolumeMount,
)
from pydantic import BaseModel

from tesk.custom_config import (
    CustomConfig,
    Taskmaster,
)
from tesk.exceptions import ConfigInvalidError, ConfigNotFoundError
from tesk.k8s.constants import tesk_k8s_constants


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
        raise ConfigInvalidError(
            "Custom configuration not found in config file."
        ) from None


def get_taskmaster_config() -> Taskmaster:
    """Get the taskmaster env property from the custom configuration.

    Returns:
        The taskmaster env property.
    """
    custom_conf = get_custom_config()
    try:
        return custom_conf.taskmaster
    except AttributeError:
        raise ConfigInvalidError(
            "Custom configuration doesn't seem to have taskmaster_env_properties in "
            "config file."
            f"Custom config:\n{custom_conf}"
        ) from None


def get_taskmaster_template() -> V1Job:
    """Get the taskmaster template from the custom configuration.

    This will be used to create the taskmaster job, API will inject values
    into the template, depending upon the type of job and request.

    Returns:
        The taskmaster template.
    """
    taskmaster_conf: Taskmaster = get_taskmaster_config()

    return V1Job(
        api_version=tesk_k8s_constants.k8s_constants.K8S_BATCH_API_VERSION,
        kind=tesk_k8s_constants.k8s_constants.K8S_BATCH_API_JOB_TYPE,
        metadata=V1ObjectMeta(
            name=tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_TASKM,
        ),
        spec=V1JobSpec(
            template=V1PodTemplateSpec(
                metadata=V1ObjectMeta(
                    name=tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_TASKM
                ),
                spec=V1PodSpec(
                    service_account_name=taskmaster_conf.serviceAccountName,
                    containers=[
                        V1Container(
                            name=tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_TASKM,
                            image=f"{taskmaster_conf.imageName}:{taskmaster_conf.imageVersion}",
                            args=[
                                "-f",
                                f"/jsoninput/{tesk_k8s_constants.job_constants.TASKMASTER_INPUT}.gz",
                            ],
                            env=[
                                V1EnvVar(
                                    name=tesk_k8s_constants.ftp_constants.FTP_SECRET_USERNAME_ENV,
                                    value_from=V1EnvVarSource(
                                        secret_key_ref=V1SecretKeySelector(
                                            name="ftp-secret",
                                            key="username",
                                            optional=True,
                                        )
                                    ),
                                ),
                                V1EnvVar(
                                    name=tesk_k8s_constants.ftp_constants.FTP_SECRET_PASSWORD_ENV,
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
                    volumes=[
                        V1Volume(
                            name="podinfo",
                            downward_api=V1DownwardAPIVolumeSource(
                                items=[
                                    V1DownwardAPIVolumeFile(
                                        path="labels",
                                        field_ref=V1ObjectFieldSelector(
                                            field_path="metadata.labels"
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ],
                    restart_policy=tesk_k8s_constants.k8s_constants.JOB_RESTART_POLICY,
                ),
            )
        ),
    )


def get_taskmaster_env_property() -> Taskmaster:
    """Get the taskmaster env property from the custom configuration.

    Returns:
      The taskmaster env property.
    """
    custom_conf = get_custom_config()
    try:
        return custom_conf.taskmaster
    except AttributeError:
        raise ConfigNotFoundError(
            "Custom configuration doesn't seem to have taskmaster_env_properties in "
            "config file."
            f"Custom config:\n{custom_conf}"
        ) from None


def pydantic_model_list_dict(model_list: Sequence[BaseModel]) -> List[str]:
    """Convert a list of pydantic models to a list of dictionaries."""
    return [json.loads(item.json()) for item in model_list]


def format_datetime(dt: datetime) -> str:
    """Formats a datetime object into time with UTC timezone.

    Args:
        dt: The datetime object to format.

    Returns:
        str: The formatted datetime string.
    """
    return dt.astimezone(timezone.utc).isoformat()
