"""Custom configuration model for the FOCA app."""

from typing import Dict, Optional

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models import Service
from tesk.constants import tesk_constants


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


class Taskmaster(BaseModel):
    """Taskmaster environment properties model for the TESK."""

    imageName: str = Field(
        default=tesk_constants.TASKMASTER_IMAGE_NAME,
        description="Taskmaster image name",
    )
    imageVersion: str = Field(
        default=tesk_constants.TASKMASTER_IMAGE_VERSION,
        description="Taskmaster image version",
    )
    filerImageName: str = Field(
        default=tesk_constants.FILER_IMAGE_NAME, description="Filer image name"
    )
    filerImageVersion: str = Field(
        default=tesk_constants.FILER_IMAGE_VERSION, description="Filer image version"
    )
    ftp: FtpConfig = Field(default=None, description="Test FTP account settings")
    debug: bool = Field(
        default=False,
        description="If verbose (debug) mode of taskmaster is on (passes additional "
        "flag to taskmaster and sets image pull policy to Always)",
    )
    environment: Optional[Dict[str, str]] = Field(
        default=None,
        description="Environment variables, that will be passed to taskmaster",
    )
    serviceAccountName: str = Field(
        default="default", description="Service Account name for taskmaster"
    )
    executorSecret: Optional[ExecutorSecret] = Field(
        default=None, description="Executor secret configuration"
    )


class CustomConfig(BaseModel):
    """Custom configuration model for the FOCA app."""

    # Define custom configuration fields here
    service_info: Service
    taskmaster: Taskmaster
