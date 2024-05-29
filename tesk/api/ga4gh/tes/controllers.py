"""Controllers for GA4GH TES API endpoints."""

import logging

# from connexion import request  # type: ignore
from foca.utils.logging import log_traffic  # type: ignore

# Get logger instance
logger = logging.getLogger(__name__)


# POST /tasks/{id}:cancel
@log_traffic
def CancelTask(id, *args, **kwargs) -> dict:  # type: ignore
	pass


# POST /tasks
@log_traffic
def CreateTask(*args, **kwargs) -> dict:  # type: ignore
	pass


# GET /tasks/service-info
@log_traffic
def GetServiceInfo(*args, **kwargs) -> dict:  # type: ignore
	pass


# GET /tasks
@log_traffic
def ListTasks(*args, **kwargs) -> dict:  # type: ignore
	pass


# GET /tasks
@log_traffic
def GetTask(*args, **kwargs) -> dict:  # type: ignore
	pass
