"""Tesk scoped constants."""

import os


class TeskConstants:
    """Tesk scoped constants."""

    filer_image_name: str = os.getenv(
        "FILER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-filer"
    )
    filer_image_version: str = os.getenv("FILER_IMAGE_VERSION", "latest")
    taskmaster_image_name: str = os.getenv(
        "TASKMASTER_IMAGE_NAME", "docker.io/elixircloud/tesk-core-taskmaster"
    )
    taskmaster_image_version: str = os.getenv("TASKMASTER_IMAGE_VERSION", "latest")
    tesk_namespace: str = os.getenv("TESK_NAMESPACE", "tesk")
