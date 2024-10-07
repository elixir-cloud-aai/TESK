"""Controllers for GA4GH TES API endpoints."""

import logging
from typing import Any

from foca.utils.logging import log_traffic  # type: ignore
from pydantic import ValidationError

from tesk.api.ga4gh.tes.models import TesTask
from tesk.api.ga4gh.tes.service_info.service_info import ServiceInfo
from tesk.api.ga4gh.tes.task.create_task import CreateTesTask
from tesk.exceptions import BadRequest, InternalServerError

# Get logger instance
logger = logging.getLogger(__name__)


# POST /tasks/{id}:cancel
@log_traffic
def CancelTask(id, *args, **kwargs) -> dict:  # type: ignore
    """Cancel unfinished task.

    Args:
        id: Task identifier.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    pass


# POST /tasks
@log_traffic
def CreateTask(**kwargs) -> dict:
    """Create task.

    Args:
        **kwargs: Arbitrary keyword arguments.
    """
    try:
        request_body: Any = kwargs.get("body")
        try:
            tes_task = TesTask(**request_body)
        except ValidationError as e:
            raise BadRequest(str(e)) from e
        return CreateTesTask(tes_task).response()
    except Exception as e:
        raise InternalServerError from e


# GET /tasks/service-info
@log_traffic
def GetServiceInfo() -> dict:  # type: ignore
    """Get service info."""
    service_info = ServiceInfo()
    return service_info.response()


# GET /tasks
@log_traffic
def ListTasks(*args, **kwargs) -> dict:  # type: ignore
    """List all available tasks.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    pass


# GET /tasks
@log_traffic
def GetTask(*args, **kwargs) -> dict:  # type: ignore
    """Get info for individual task.

    Args:
        id: Task identifier.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    pass
