"""TESK API module to retrieve a task."""

import logging
from typing import Optional

from kubernetes.client.models import V1Job, V1JobList, V1PodList

from tesk.api.ga4gh.tes.models import (
    TaskView,
)
from tesk.api.ga4gh.tes.task.task_request import TesTaskRequest
from tesk.k8s.converter.data.task_builder import TaskBuilder

logger = logging.getLogger(__name__)


class GetTesTask(TesTaskRequest):
    """Retrieve a TES task.

    Arguments:
        task_id: TES task ID.
        task_view: Verbosity of the task in the list.
    """

    def __init__(
        self,
        task_id: str,
        task_view: TaskView,
    ):
        """Initialize the CreateTask class.

        Args:
            task_id: TES task ID.
            task_view: Verbosity of the task in the list.
        """
        super().__init__()
        self.task_id = task_id
        self.task_view = task_view

    def handle_request(self):
        """Return the response."""
        taskmaster_job: V1Job = self.kubernetes_client_wrapper.read_taskmaster_job(
            self.task_id
        )

        taskmaster_job_name: Optional[str] = taskmaster_job.metadata.name
        assert taskmaster_job_name is not None

        execution_job_list: V1JobList = (
            self.kubernetes_client_wrapper.list_single_task_executor_jobs(
                taskmaster_job_name
            )
        )
        taskmaster_pods: V1PodList = (
            self.kubernetes_client_wrapper.list_single_job_pods(taskmaster_job)
        )

        task_builder = (
            TaskBuilder.new_single_task()
            .add_job(taskmaster_job)
            .add_job_list(execution_job_list.items)
            .add_pod_list(taskmaster_pods.items)
        )

        for executor_job in execution_job_list.items:
            executor_job_pods: V1PodList = (
                self.kubernetes_client_wrapper.list_single_job_pods(executor_job)
            )
            task_builder.add_pod_list(executor_job_pods.items)

        output_filer_job_list: Optional[V1Job] = (
            self.kubernetes_client_wrapper.get_single_task_output_filer_job(
                taskmaster_job_name
            )
        )

        return self._get_task(task_builder, output_filer_job_list, self.task_view)
