"""Controllers for GA4GH TES API endpoints."""

import logging
import json
from foca.utils.logging import log_traffic  # type: ignore

from tesk.api.ga4gh.tes.models import TesTask
from tesk.api.ga4gh.tes.service_info.service_info import ServiceInfo
from tesk.api.ga4gh.tes.task.create_task import CreateTesTask
from tesk.exceptions import BadRequest, InternalServerError
from tesk.api.ga4gh.tes.task.get_task import GetTesTask
from tesk.api.ga4gh.tes.models import TaskView
from tesk.utils import enum_to_string

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
        request_body = kwargs.get("body")
        if request_body is None:
            logger.error("Nothing received in request body.")
            raise BadRequest("No request body received.")
        tes_task = TesTask(**request_body)
        response = CreateTesTask(tes_task).response()
        return response
    except Exception as e:
        raise InternalServerError from e


# GET /tasks/service-info
@log_traffic
def GetServiceInfo() -> dict:
    """Get service info."""
    service_info = ServiceInfo()
    return service_info.response()


# GET /tasks
@log_traffic
def ListTasks(*args, **kwargs):
    """List all available tasks.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    get_tes_task = GetTesTask()
    view = TaskView(kwargs.get("view"))
    name_prefix = kwargs.get("name_prefix")
    page_size = kwargs.get("page_size")
    page_token = kwargs.get("page_token")
    response = get_tes_task.list_tasks(
        view=view, name_prefix=name_prefix, page_size=page_size, page_token=page_token
    )
    return json.loads(response.json())


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
