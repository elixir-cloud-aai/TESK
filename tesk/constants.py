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

    Note:
        Below are the mentioned environment variable with which these constants can be
        configured, otherwise mentioned default will be assigned.

        variable:
            ENV_VARIABLE = default

        FILER_IMAGE_NAME:
            TESK_API_TASKMASTER_FILER_IMAGE_NAME = docker.io/elixircloud/tesk-core-filer
        FILER_IMAGE_VERSION:
            TESK_API_TASKMASTER_FILER_IMAGE_VERSION = latest
        TASKMASTER_IMAGE_NAME:
            TESK_API_TASKMASTER_IMAGE_NAME = docker.io/elixircloud/tesk-core-taskmaster
        TASKMASTER_IMAGE_VERSION:
            TESK_API_TASKMASTER_IMAGE_VERSION = latest
        TESK_NAMESPACE:
            TESK_API_K8S_NAMESPACE = tesk
        TASKMASTER_SERVICE_ACCOUNT_NAME:
            TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME = taskmaster
        TASKMASTER_ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT:
            ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT = 6
        FILER_BACKOFF_LIMIT:
            FILER_BACKOFF_LIMIT = 2
        EXECUTOR_BACKOFF_LIMIT:
            EXECUTOR_BACKOFF_LIMIT = 2
    """

    FILER_IMAGE_NAME: str = os.getenv(
        "TESK_API_TASKMASTER_FILER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-filer"
    )
    FILER_IMAGE_VERSION: str = os.getenv(
        "TESK_API_TASKMASTER_FILER_IMAGE_VERSION", "latest"
    )
    TASKMASTER_IMAGE_NAME: str = os.getenv(
        "TESK_API_TASKMASTER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-taskmaster"
    )
    TASKMASTER_IMAGE_VERSION: str = os.getenv(
        "TESK_API_TASKMASTER_IMAGE_VERSION", "latest"
    )
    TESK_NAMESPACE: str = os.getenv("TESK_API_K8S_NAMESPACE", "tesk")
    TASKMASTER_SERVICE_ACCOUNT_NAME: str = os.getenv(
        "TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME", "taskmaster"
    )
    TASKMASTER_ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT: str = os.getenv(
        "ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT", "6"
    )
    FILER_BACKOFF_LIMIT: str = os.getenv("FILER_BACKOFF_LIMIT", "2")
    EXECUTOR_BACKOFF_LIMIT: str = os.getenv("EXECUTOR_BACKOFF_LIMIT", "2")

    class Config:
        """Configuration for class."""

        frozen = True


tesk_constants = TeskConstants()
