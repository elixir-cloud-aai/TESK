"""Controllers for GA4GH TES API endpoints."""

import logging

from foca.utils.logging import log_traffic  # type: ignore

from tesk.api.kubernetes.template import KubernetesTemplateSupplier
from tesk.api.ga4gh.tes.models import TesTask
from tesk.utils import get_custom_config
from tesk.api.kubernetes.converter import TesKubernetesConverter

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
    request_body = kwargs["body"]
    create_task_request = TesTask(**request_body)
    user = {
        "username": "test",
        "is_member": True,
        "any_group": "test_group",
    }
    tkc = TesKubernetesConverter().from_tes_task_to_k8s_job(create_task_request, user)
    print(tkc)
    pass


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
