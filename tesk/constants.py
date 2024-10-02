"""Tesk scoped constants."""

import os

from pydantic import BaseModel


class TeskConstants(BaseModel):
    """Tesk's K8s scoped constants.

    Attributes:
        FILER_IMAGE_NAME: Name of the filer image
        FILER_IMAGE_VERSION: Version of the filer image
        TASKMASTER_IMAGE_NAME:  Name of the taskmaster image
        TASKMASTER_IMAGE_VERSION: Version of the taskmaster image
        TESK_NAMESPACE: Namespace in which api will create K8s resources from TES
            request
        TASKMASTER_SERVICE_ACCOUNT_NAME: Taskmaster service account name
        TASKMASTER_ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT:  Backoff limit for taskmaster env
        FILER_BACKOFF_LIMIT: Backoff limit got filer job
        EXECUTOR_BACKOFF_LIMIT: Backoff limit for executor job
    """

    TESK_NAMESPACE: str = os.getenv("TESK_API_K8S_NAMESPACE", "tesk")
    FILER_IMAGE_NAME: str = "docker.io/elixircloud/tesk-core-filer"
    FILER_IMAGE_VERSION: str = "latest"
    TASKMASTER_IMAGE_NAME: str = "docker.io/elixircloud/tesk-core-taskmaster"
    TASKMASTER_IMAGE_VERSION: str = "latest"
    TASKMASTER_SERVICE_ACCOUNT_NAME: str = "taskmaster"
    FILER_BACKOFF_LIMIT: int = 2
    EXECUTOR_BACKOFF_LIMIT: int = 2

    class Config:
        """Configuration for class."""

        frozen = True


tesk_constants = TeskConstants()
