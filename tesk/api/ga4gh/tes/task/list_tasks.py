"""TESK API modeule to list tasks."""

from typing import List

from kubernetes.client.models import V1JobList

from tesk.api.ga4gh.tes.models import TaskView, TesListTasksResponse, TesTask
from tesk.api.ga4gh.tes.task.task_request import TesTaskRequest
from tesk.k8s.converter.data.task_builder import TaskBuilder


class ListTesTask(TesTaskRequest):
    """Gets a full list of tasks.

    Performs Kubernetes API batch calls (all taskmasters, all executors, all pods),
    combines them together into valid Task objects and converts to result with
    means of the converter.

    Arguments:
        page_size: The maximum number of tasks to return in a single page.
        page_token: The continuation token, which is used to page through large result
            sets.
        view: Verbosity of the task in the list.
        namePrefix: The prefix of the task name.
    """

    def __init__(
        self,
        page_size: int,
        page_token: str,
        view: TaskView,
        namePrefix: str,
    ):
        """Initialise the ListTesTask class.

        Args:
            page_size: The maximum number of tasks to return in a single page.
            page_token: The continuation token, which is used to page through large
                result sets.
            view: Verbosity of the task in the list.
            namePrefix: The prefix of the task name.
        """
        self.page_size = page_size
        self.page_token = page_token
        self.view = view
        self.namePrefix = namePrefix

    def handle_request(self) -> TesListTasksResponse:
        """Business logic for the list tasks request.

        Returns:
            TesListTasksResponse: The response containing the list of tasks and next
                page token.
        """
        taskmaster_jobs: V1JobList = (
            self.kubernetes_client_wrapper.list_all_taskmaster_jobs_for_user(
                page_token=self.page_token,
                items_per_page=self.page_size,
            )
        )
        executor_jobs: V1JobList = (
            self.kubernetes_client_wrapper.list_all_task_executor_jobs()
        )
        filer_jobs: V1JobList = self.kubernetes_client_wrapper.list_all_filer_jobs()
        job_pods = self.kubernetes_client_wrapper.list_all_job_pods()
        task_list_builder: TaskBuilder = (
            TaskBuilder.new_task_list()
            .add_job_list(taskmaster_jobs.items())
            .add_job_list(executor_jobs.items())
            .add_job_list(filer_jobs.items())
            .add_pod_list(job_pods.items())
        )

        tasks: List[TesTask] = [
            self._get_task(task, self.view, True)
            for task in task_list_builder.get_task_list()
        ]

        next_page_token = taskmaster_jobs.metadata._continue()

        return TesListTasksResponse(tasks=tasks, next_page_token=next_page_token)
