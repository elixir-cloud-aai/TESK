"""Module aimed at building Kubernetes object structure of a task or a list of tasks,.

Gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
This class takes care of matching jobs with corresponding pods and holds a flat
collection (mapped by name) of resulting Job objects (can be both taskmasters and
executors belonging to the same or different task).Accepts a BuildStrategy BuildStrategy
, which implementing classes are responsible of creating, storing and maintaining the
actual {@link Task} object or {@link Task} object's list by implementing
BuildStrategy#addTaskMasterJob(Job) and BuildStrategy#addExecutorJob(Job).
"""

from kubernetes.client import V1Job, V1Pod

from tesk.api.kubernetes.constants import Constants
from tesk.api.kubernetes.convert.data.build_strategy import BuildStrategy
from tesk.api.kubernetes.convert.data.job import Job
from tesk.api.kubernetes.convert.data.single_task_strategy import SingleTaskStrategy
from tesk.api.kubernetes.convert.data.task_list_strategy import TaskListStrategy


class TaskBuilder:
    @staticmethod
    def new_single_task():
        return TaskBuilder(SingleTaskStrategy())

    @staticmethod
    def new_task_list():
        return TaskBuilder(TaskListStrategy())

    def __init__(self, build_strategy: BuildStrategy):
        self.build_strategy = build_strategy
        self.all_jobs_by_name = {}
        self.constants = Constants()

    def add_job(self, job: V1Job):
        wrapped_job = Job(job)
        job_type = job.metadata.labels.get(self.constants.label_jobtype_key)
        if job_type == self.constants.label_jobtype_value_taskm:
            self.build_strategy.add_taskmaster_job(wrapped_job)
        elif job_type == self.constants.label_jobtype_value_exec:
            self.build_strategy.add_executor_job(wrapped_job)
        else:
            self.build_strategy.add_output_filer_job(wrapped_job)
        self.all_jobs_by_name[job.metadata.name] = wrapped_job
        return self

    def add_job_list(self, jobs: list[V1Job]):
        for job in jobs:
            self.add_job(job)
        return self

    def add_pod_list(self, pods: list[V1Pod]):
        for pod in pods:
            self.add_pod(pod)
        return self

    def add_pod(self, pod: V1Pod):
        for job in self.all_jobs_by_name.values():
            selectors = job.job.spec.selector.match_labels
            labels = pod.metadata.labels
            if all(item in labels.items() for item in selectors.items()):
                job.add_pod(pod)
                break

    def get_task(self):
        return self.build_strategy.get_task()

    def get_task_list(self):
        return self.build_strategy.get_task_list()

    def get_all_jobs_by_name(self):
        return self.all_jobs_by_name
