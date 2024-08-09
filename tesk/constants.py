"""Tesk scoped constants."""

import os


class TeskConstants:
    """Tesk's K8s scoped constants."""

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
    # FIXME: IDK what to do with this
    tesk_api_taskmaster_environment_filer_backoff_limit: str = os.getenv(
        "TESK_API_TASKMASTER_ENVIRONMENT_FILER_BACKOFF_LIMIT", "6"
    )
