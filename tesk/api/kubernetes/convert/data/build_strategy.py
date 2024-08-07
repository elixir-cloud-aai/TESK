"""Part of the toolset aimed at building Kubernetes object structure of a task or tasks.

Gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
Implementing classes are responsible of creating,
storing and maintaining the actual `Task` object or `Task` object's list.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from tesk.api.kubernetes.convert.data.job import Job
from tesk.api.kubernetes.convert.data.task import Task


class BuildStrategy(ABC):
    """Part of the toolset aimed at building Kubernetes object structure of a task/s.

    Gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
    Implementing classes are responsible of creating,
    storing and maintaining the actual `Task` object or `Task` object's list.
    """

    @abstractmethod
    def add_task_master_job(self, taskmaster_job: Job):
        """Add taskmaster job.

        Method should optionally filter and place the passed taskmaster's job object
        in the resulting structure.
        """
        pass

    @abstractmethod
    def add_executor_job(self, executor_job: Job):
        """Add executor job.

        Method should optionally filter and place the passed executor's job object
        in the resulting structure (and match it to appropriate taskmaster).
        """
        pass

    @abstractmethod
    def add_output_filer_job(self, filer_job: Job):
        """Add output filer job.

        Method should optionally filter and place the passed output filer's job object
        in the resulting structure (and match it to appropriate taskmaster).
        """
        pass

    @abstractmethod
    def get_task(self) -> Optional[Task]:
        """Return the single task object."""
        pass

    @abstractmethod
    def get_task_list(self) -> List[Task]:
        """Return the list of task objects."""
        pass
