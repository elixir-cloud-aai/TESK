"""Controllers for GA4GH TES API endpoints."""

import logging

from foca.utils.logging import log_traffic  # type: ignore

from tesk.api.kubernetes.template import KubernetesTemplateSupplier
from tesk.api.ga4gh.tes.models import TesTask
from tesk.utils import get_custom_config
from tesk.api.kubernetes.converter import TesKubernetesConverter
from tesk.exceptions import BadRequest, InternalServerError
# from tesk.api.ga4gh.tes.task.create_task import CreateTask as TaskCreater

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
def CreateTask(**kwargs) -> dict:  # type: ignore
    """Create task.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    try:
        request_body = kwargs.get("body")
        if request_body is None:
            logger("Nothing recieved in request body.")
            raise BadRequest("No request body recieved.")
    except Exception as e:
        raise InternalServerError from e


# GET /tasks/service-info
@log_traffic
def GetServiceInfo(*args, **kwargs) -> dict:  # type: ignore
    """Get service info.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    pass


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
