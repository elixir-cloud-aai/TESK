"""Builder aimed at building k8s object structure of a task or a list of tasks."""

from typing import Dict, List, Optional

from kubernetes.client.models import V1Job, V1Pod, V1PodList

from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.data.build_strategy import BuildStrategy
from tesk.k8s.converter.data.job import Job
from tesk.k8s.converter.data.single_task_strategy import SingleTaskStrategy
from tesk.k8s.converter.data.task import Task
from tesk.k8s.converter.data.task_list_strategy import TaskListStrategy


class TaskBuilder:
    """Builder aimed at building k8s object structure of a task or a list of tasks.

    Done by gradually adding to it objects returned by calls to Kubernetes API (jobs and
    pods).This class takes care of matching jobs with corresponding pods and holds a
    flat collection (mapped by name) of resulting Job objects (can be both taskmasters
    and executors belonging to the same or different task). Accepts a BuildStrategy,
    which implementing classes are responsible of creating, storing and maintaining the
    actual Task object or Task object's list by implementing
    BuildStrategy.addTaskMasterJob(Job)and BuildStrategy.addExecutorJob(Job).

    Arguments:
      build_strategy: BuildStrategy object responsible for creating the actual Task
        object.
      all_jobs_by_name: Dictionary of all jobs added to the builder, mapped by job name.
    """

    def __init__(self, build_strategy):
        """Initialise the TaskBuilder.

        Args:
            build_strategy: BuildStrategy object responsible for creating the actual
                Task object.
        """
        self.build_strategy: BuildStrategy = build_strategy
        self.all_jobs_by_name: Dict[str, Job] = {}

    @classmethod
    def new_single_task(cls):
        """Use SingleTaskStrategy for building a single task."""
        return cls(SingleTaskStrategy())

    @classmethod
    def new_task_list(cls):
        """Use TaskListStrategy for building a list of tasks."""
        return cls(TaskListStrategy())

    def add_job(self, job: V1Job) -> "TaskBuilder":
        """Add a job to the composite.

        Args:
            job: K8s V1Job object for any of the job, ie taskmaster
                executor or output filer.
        """
        wrapped_job = Job(job)
        labels: Optional[Dict[str, str]] = job.metadata.labels
        assert labels, "Job metadata labels must be present"
        job_type_label: str = labels.get(
            tesk_k8s_constants.label_constants.LABEL_JOB_TYPE_KEY
        )

        # Add job to the strategy based on its type
        match job_type_label:
            case tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_TASKM:
                self.build_strategy.add_taskmaster_job(wrapped_job)
            case tesk_k8s_constants.label_constants.LABEL_JOBTYPE_VALUE_EXEC:
                self.build_strategy.add_executor_job(wrapped_job)
            case _:
                self.build_strategy.add_output_filer_job(wrapped_job)

        # If job is not already in the collection, add it
        name: Optional[str] = job.metadata.name
        assert name, "Job metadata name must be present"
        if name not in self.all_jobs_by_name:
            self.all_jobs_by_name[job.metadata.name] = wrapped_job

        return self

    def add_job_list(self, jobs: List[V1Job]) -> "TaskBuilder":
        """Adds a list of jobs to the composite.

        Args:
            jobs: List of K8s V1Job objects.
        """
        for job in jobs:
            self.add_job(job)
        return self

    def add_pod_list(self, pods: List[V1PodList]) -> "TaskBuilder":
        """Adds a list of pods to the composite.

        Tries to find a matching job for each pod, If there is a match, a pod is placed
        in the Job object. Will accept a collection of any pods, the ones that don't
        match get discarded.

        Args:
            pods: List of K8s V1PodList objects.
        """
        for pod in pods:
            self.add_pod(pod)
        return self

    def add_pod(self, pod: V1Pod) -> None:
        """Adds a pod to the composite.

        Tries to find a matching job for it. If there is a match, a pod is placed in
        the matching Job object. Match is done by comparing match labels
        (only match expressions are ignored) of job's selector and comparing them with
        labels of the pod. If all selectors of the job are present in pod's label set,
        match is detected (first job-pod match stops search).Will accept also unmatching
        pod, which won't get stored.

        Args:
            pod: K8s V1Pod object.
        """
        for job in self.all_jobs_by_name.values():
            selectors = job.get_job().spec.selector.match_labels or {}
            pod_labels = pod.metadata.labels or {}
            # Check if all selector key-value pairs are present in the pod's labels
            if selectors.items() <= pod_labels.items():
                # Found a matching job; add the pod to this job
                job.add_pod(pod)
                break

    def get_task(self) -> Task:
        """Get the task.

        Returns:
            Task: Task object according to the strategy.
        """
        return self.build_strategy.get_task()

    def get_task_list(self) -> List[Task]:
        """Get the task list.

        Returns:
            List[Task]: List of Task objects according to the strategy.
        """
        return self.build_strategy.get_task_list()

    def get_all_jobs_by_name(self) -> Dict[str, Job]:
        """Get all jobs.

        Returns:
            Dict[str, Job]: Dictionary of all jobs added to the builder,
                mapped by job name.
        """
        return self.all_jobs_by_name
