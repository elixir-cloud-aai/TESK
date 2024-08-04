"""Taskmaster environment properties model for the TESK."""

from typing import Dict, Optional

from pydantic import BaseModel, Field

from tesk.constants import TeskConstants


class FtpConfig(BaseModel):
    """Ftp configuration model for the TESK."""

    secretName: Optional[str] = Field(
        default=None, description="Name of the secret with FTP account credentials"
    )
    enabled: bool = Field(
        default=False,
        description="If FTP account enabled (based on non-emptiness of secretName)",
    )


class ExecutorSecret(BaseModel):
    """Executor secret configuration."""

    name: Optional[str] = Field(
        default=None,
        description=(
            "Name of a secret that will be mounted as volume to each executor. The same"
            " name will be used for the secret and the volume"
        ),
    )
    mountPath: Optional[str] = Field(
        default=None,
        alias="mountPath",
        description="The path where the secret will be mounted to executors",
    )
    enabled: bool = Field(
        default=False, description="Indicates whether the secret is enabled"
    )


class TaskmasterEnvProperties(BaseModel):
    """Taskmaster environment properties model for the TESK."""

    imageName: str = Field(
        default=TeskConstants.taskmaster_image_name,
        description="Taskmaster image name",
    )
    imageVersion: str = Field(
        default=TeskConstants.taskmaster_image_version,
        description="Taskmaster image version",
    )
    filerImageName: str = Field(
        default=TeskConstants.filer_image_name, description="Filer image name"
    )
    filerImageVersion: str = Field(
        default=TeskConstants.filer_image_version, description="Filer image version"
    )
    ftp: FtpConfig = Field(default=None, description="Test FTP account settings")
    debug: bool = Field(
        default=False,
        description="If verbose (debug) mode of taskmaster is on (passes additional "
        "flag to taskmaster and sets image pull policy to Always)",
    )
    environment: Dict[str, str] = Field(
        default={"key": "value"},
        description="Environment variables, that will be passed to taskmaster",
    )
    serviceAccountName: str = Field(
        default="default", description="Service Account name for taskmaster"
    )
    executorSecret: Optional[ExecutorSecret] = Field(
        default=None, description="Executor secret configuration"
    )
