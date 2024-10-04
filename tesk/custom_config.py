"""Custom configuration model for the FOCA app."""

from typing import Dict, Optional

from pydantic import BaseModel

from tesk.api.ga4gh.tes.models import Service
from tesk.constants import tesk_constants


class FtpConfig(BaseModel):
    """Ftp configuration model for the TESK.

    Args:
        secretName: Name of the secret with FTP account credentials.
        enabled: If FTP account enabled (based on non-emptiness of secretName).
    """

    secretName: Optional[str] = None
    enabled: bool = False


class ExecutorSecret(BaseModel):
    """Executor secret configuration.

    Args:
        name: Name of a secret that will be mounted as volume to each executor. The same
            name will be used for the secret and the volume.
        mountPath: The path where the secret will be mounted to executors.
        enabled: Indicates whether the secret is enabled.
    """

    name: Optional[str] = None
    mountPath: Optional[str] = None
    enabled: bool = False


class Taskmaster(BaseModel):
    """Taskmaster's configuration model for the TESK.

    Args:
        imageName: Taskmaster image name.
        imageVersion: Taskmaster image version.
        filerImageName: Filer image name.
        filerImageVersion: Filer image version.
        ftp: FTP account settings.
        debug: If verbose (debug) mode of taskmaster is on (passes additional flag to
            taskmaster and sets image pull policy to Always).
        environment: Environment variables, that will be passed to taskmaster.
        serviceAccountName: Service Account name for taskmaster.
        executorSecret: Executor secret configuration
    """

    imageName: str = tesk_constants.TASKMASTER_IMAGE_NAME
    imageVersion: str = tesk_constants.TASKMASTER_IMAGE_VERSION
    filerImageName: str = tesk_constants.FILER_IMAGE_NAME
    filerImageVersion: str = tesk_constants.FILER_IMAGE_VERSION
    ftp: FtpConfig = FtpConfig()
    debug: bool = False
    environment: Optional[Dict[str, str]] = None
    serviceAccountName: str = tesk_constants.TASKMASTER_SERVICE_ACCOUNT_NAME
    executorSecret: Optional[ExecutorSecret] = None
    filerBackoffLimit: str = tesk_constants.FILER_BACKOFF_LIMIT
    executorBackoffLimit: str = tesk_constants.EXECUTOR_BACKOFF_LIMIT


class CustomConfig(BaseModel):
    """Custom configuration model for the FOCA app.

    Args:
        service_info: Service information.
        taskmaster: Taskmaster environment.
    """

    # Define custom configuration fields here
    service_info: Service
    taskmaster: Taskmaster = Taskmaster()
