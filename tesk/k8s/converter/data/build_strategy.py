"""Baseclass of strategy for building Kubernetes structure of task or list of tasks."""

from abc import ABC, abstractmethod
from typing import List

from tesk.k8s.converter.data.job import Job
from tesk.k8s.converter.data.task import Task


class BuildStrategy(ABC):
    """Baseclass of strategy for building Kubernetes structure of task or list of tasks.

    Aimed at building Kubernetes object structure of a task or a list of tasks, by
    gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
    Implementing classes are responsible for creating, storing, and maintaining the
    actual Task object or Task object's list.
    """

    @abstractmethod
    def add_taskmaster_job(self, taskmaster_job: Job) -> None:
        """Add taskmaster job to the strategy.

        Implementing method should optionally filter and then place
        the passed taskmaster's job object in the resulting structure.

        Args:
            taskmaster_job: Job object representing the taskmaster's job.
        """
        pass

    @abstractmethod
    def add_executor_job(self, executor_job: Job) -> None:
        """Add executor job to the strategy.

        Implementing method should optionally filter and then place
        the passed executor's job object in the resulting structure (and match it to
        appropriate taskmaster).

        Args:
            executor_job: Job object representing the executor's job.
        """
        pass

    @abstractmethod
    def add_output_filer_job(self, filer_job: Job) -> None:
        """Add output filer job to the strategy.

        Implementing method should filter and then place the passed filer's job
        object in the resulting structure (and match it to
        appropriate taskmaster).

        Args:
            filer_job: Job object representing the filer's job.
        """
        pass

    @abstractmethod
    def get_task(self) -> Task:
        """Get the task.

        Return a single Task composite object.

        Returns:
            Task: Task object.
        """
        pass

    @abstractmethod
    def get_task_list(self) -> List[Task]:
        """Get the task list.

        Return a list of Task composite objects.

        Returns:
            List[Task]: List of Task objects.
        """
        pass
