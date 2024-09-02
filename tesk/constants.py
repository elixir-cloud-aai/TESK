"""Tesk scoped constants."""

import os

from pydantic import BaseModel


class TeskConstants(BaseModel):
    """Tesk's K8s scoped constants.

    Attributes:
        filer_image_name: Name of the filer image
        filer_image_version: Version of the filer image
        taskmaster_image_name:  Name of the taskmaster image
        taskmaster_image_version: Version of the taskmaster image
        tesk_namespace: Namespace in which api will create K8s resources from TES
            request
        taskmaster_service_account_name: Taskmaster service account name
        taskmaster_environment_executor_backoff_limit:  Backoff limit for taskmaster env
        filer_backoff_limit: Backoff limit got filer job
        executor_backoff_limit: Backoff limit for executor job

    Note:
        Below are the mentioned environment variable with which these constants can be
        configured, otherwise mentioned default will be assigned.

        variable:
            ENV_VARIABLE = default

        filer_image_name:
            TESK_API_TASKMASTER_FILER_IMAGE_NAME = docker.io/elixircloud/tesk-core-filer
        filer_image_version:
            TESK_API_TASKMASTER_FILER_IMAGE_VERSION = latest
        taskmaster_image_name:
            TESK_API_TASKMASTER_IMAGE_NAME = docker.io/elixircloud/tesk-core-taskmaster
        taskmaster_image_version:
            TESK_API_TASKMASTER_IMAGE_VERSION = latest
        tesk_namespace:
            TESK_API_K8S_NAMESPACE = tesk
        taskmaster_service_account_name:
            TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME = taskmaster
        taskmaster_environment_executor_backoff_limit:
            ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT = 6
        filer_backoff_limit:
            FILER_BACKOFF_LIMIT = 2
        executor_backoff_limit:
            EXECUTOR_BACKOFF_LIMIT = 2
    """

    filer_image_name: str = os.getenv(
        "TESK_API_TASKMASTER_FILER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-filer"
    )
    filer_image_version: str = os.getenv(
        "TESK_API_TASKMASTER_FILER_IMAGE_VERSION", "latest"
    )
    taskmaster_image_name: str = os.getenv(
        "TESK_API_TASKMASTER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-taskmaster"
    )
    taskmaster_image_version: str = os.getenv(
        "TESK_API_TASKMASTER_IMAGE_VERSION", "latest"
    )
    tesk_namespace: str = os.getenv("TESK_API_K8S_NAMESPACE", "tesk")
    taskmaster_service_account_name: str = os.getenv(
        "TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME", "taskmaster"
    )
    taskmaster_environment_executor_backoff_limit: str = os.getenv(
        "ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT", "6"
    )
    filer_backoff_limit: str = os.getenv("FILER_BACKOFF_LIMIT", "2")
    executor_backoff_limit: str = os.getenv("EXECUTOR_BACKOFF_LIMIT", "2")
