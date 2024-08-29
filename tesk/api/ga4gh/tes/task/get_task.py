"""Module for getting task."""

from typing import List

from kubernetes.client.models import V1JobList
from pydantic import BaseModel

from tesk.api.ga4gh.tes.models import TaskView, TesListTasksResponse, TesTask
from tesk.api.ga4gh.tes.task.task_request import TesTaskRequest
from tesk.api.kubernetes.convert.data.task import Task
from tesk.api.kubernetes.convert.data.task_builder import TaskBuilder


class GetTesTaskInterface(TesTaskRequest):
    """Base class for listing task request."""

    def __init__(self):
        """Initialise base class for listing task."""
        super().__init__()

    def get_task(
        self,
        task_id: str,
        view: TaskView,
        #  user: User
    ) -> TesTask:
        taskmaster_job = self.kubernetes_client_wrapper.read_taskmaster_job(task_id)
        executor_jobs = self.kubernetes_client_wrapper.list_single_task_executor_jobs(
            taskmaster_job.metadata.name
        )
        taskmaster_pods = self.kubernetes_client_wrapper.list_single_job_pods(
            taskmaster_job
        )
        task_builder = (
            TaskBuilder.new_single_task()
            .add_job(taskmaster_job)
            .add_job_list(executor_jobs.items)
            .add_pod_list(taskmaster_pods.items)
        )

        for executor_job in executor_jobs.items:
            executor_job_pods = self.kubernetes_client_wrapper.list_single_job_pods(
                executor_job
            )
            task_builder.add_pod_list(executor_job_pods.items)

        output_filer_job = (
            self.kubernetes_client_wrapper.get_single_task_output_filer_job(
                taskmaster_job.metadata.name
            )
        )
        if output_filer_job:
            task_builder.add_job(output_filer_job)

        return self._get_task(task_builder.get_task(), view, False)

    def _get_task(self, task_objects: Task, view: TaskView, is_list: bool) -> TesTask:
        if view == TaskView.MINIMAL:
            return self.tes_kubernetes_converter.from_k8s_jobs_to_tes_task_minimal(
                task_objects, is_list
            )

        task = self.tes_kubernetes_converter.from_k8s_jobs_to_tes_task_basic(
            task_objects, view == TaskView.BASIC
        )

        if view == TaskView.BASIC:
            return task

        for i, executor_job in enumerate(task_objects.get_executors()):
            if executor_job.has_pods():
                executor_log = task.logs[0].logs[i]
                if view == TaskView.FULL:
                    executor_pod_log = self.kubernetes_client_wrapper.read_pod_log(
                        executor_job.get_first_pod().metadata.name
                    )
                    if executor_pod_log is not None:
                        executor_log.stdout = executor_pod_log

        if task_objects.taskmaster.has_pods():
            taskmaster_pod_log = self.kubernetes_client_wrapper.read_pod_log(
                task_objects.get_taskmaster().get_first_pod().metadata.name
            )
            if taskmaster_pod_log is not None:
                task.logs[0].system_logs.append(taskmaster_pod_log)

        return task

    def list_tasks(
        self,
        name_prefix: str,
        page_size: int,
        page_token: str,
        view: TaskView,
        # user: User,
    ) -> TesListTasksResponse:
        taskmaster_jobs: V1JobList = (
            self.kubernetes_client_wrapper.list_all_taskmaster_jobs_for_user(
                page_token,
                page_size,
                # user
            )
        )
        executor_jobs = self.kubernetes_client_wrapper.list_all_task_executor_jobs()
        filer_jobs = self.kubernetes_client_wrapper.list_all_filer_jobs()
        job_pods = self.kubernetes_client_wrapper.list_all_job_pods()
        task_list_builder = (
            TaskBuilder.new_task_list()
            .add_job_list(taskmaster_jobs.items)
            .add_job_list(executor_jobs.items)
            .add_job_list(filer_jobs.items)
            .add_pod_list(job_pods.items)
        )

        tasks: List[TesTask] = [
            self._get_task(task, view, True)
            for task in task_list_builder.get_task_list()
        ]

        response = TesListTasksResponse(
            tasks=tasks, next_page_token=taskmaster_jobs.metadata._continue
        )

        return response


class GetTesTask(GetTesTaskInterface):
    def handle_request(
        self,
        name_prefix: str,
        page_size: int,
        page_token: str,
        view: TaskView,
        # user: User,
    ) -> BaseModel:
        return self.list_tasks(
            name_prefix=name_prefix,
            page_size=page_size,
            page_token=page_token,
            view=view,
        )
