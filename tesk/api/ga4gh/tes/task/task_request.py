"""Base class for tesk request."""

import json
import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.converter import TesKubernetesConverter
from tesk.k8s.wrapper import KubernetesClientWrapper
from tesk.k8s.converter.data.task import Task
from tesk.api.ga4gh.tes.models import TaskView
from tesk.api.ga4gh.tes.models import TesTask

logger = logging.getLogger(__name__)


class TesTaskRequest(ABC):
    """Base class for tesk request ecapsulating common methods and members.

    Attributes:
        kubernetes_client_wrapper: kubernetes client wrapper
        tes_kubernetes_converter: TES Kubernetes converter, used to convert TES requests
            to Kubernetes resource
        tesk_k8s_constants: TESK Kubernetes constants
    """

    def __init__(self):
        """Initialise base class for tesk request."""
        self.kubernetes_client_wrapper = KubernetesClientWrapper()
        self.tes_kubernetes_converter = TesKubernetesConverter()
        self.tesk_k8s_constants = tesk_k8s_constants

    @abstractmethod
    def handle_request(self) -> BaseModel:
        """Business logic for the request."""
        pass

    def response(self) -> dict:
        """Get response for the request."""
        response: BaseModel = self.handle_request()
        try:
            res: dict = json.loads(json.dumps(response))
            return res
        except (TypeError, ValueError) as e:
            logger.info(e)
            return response.dict()

    def _get_task(self, task_object: Task, view: TaskView, is_list: bool) -> TesTask:
        """Shared method to process Task objects into TesTask responses.

        Args:
            task_object: The Task object containing Kubernetes resources.
            view: Verbosity level for the response.
            is_list: Whether the response is a list of tasks.

        Returns:
            TesTask: The processed TES task.
        """
        if view == TaskView.MINIMAL:
            return self.tes_kubernetes_converter.from_k8s_jobs_to_tes_task_minimal(
                task_object, is_list
            )

        task = self.tes_kubernetes_converter.from_k8s_jobs_to_tes_task_basic(
            task_object, view == TaskView.BASIC
        )

        if view == TaskView.BASIC:
            return task

        for i, executor_job in enumerate(task_object.get_executors()):
            if executor_job.has_pods():
                executor_log = task.logs[0].logs[i]
                if view == TaskView.FULL:
                    executor_pod_name = executor_job.get_first_pod().metadata.name
                    executor_pod_log = self.kubernetes_client_wrapper.read_pod_log(
                        executor_pod_name
                    )
                    if executor_pod_log:
                        executor_log.stdout = executor_pod_log

        if task_object.taskmaster.has_pods():
            taskmaster_pod_name = task_object.taskmaster.get_first_pod().metadata.name
            taskmaster_pod_log = self.kubernetes_client_wrapper.read_pod_log(
                taskmaster_pod_name
            )
            if taskmaster_pod_log:
                task.logs[0].system_logs.append(taskmaster_pod_log)

        return task
