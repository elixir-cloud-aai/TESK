"""A composite that represents Kubernetes object's graph of a single TES task.

- Taskmaster job with its pods.
- Executor jobs with its pods.
"""

import re
from typing import Dict, List, Optional

from kubernetes.client.models import V1Job, V1ObjectMeta

from tesk.api.kubernetes.constants import Constants
from tesk.api.kubernetes.convert.data.job import Job


class Task:
    """Task is a composite.

    It represents Kubernetes object's graph of a single TES task.
    """

    def __init__(
        self, taskmaster: Optional[Job] = None, taskmaster_name: Optional[str] = None
    ):
        """Initialize the Task."""
        if taskmaster:
            self.taskmaster = taskmaster
        elif taskmaster_name:
            job = V1Job(metadata=V1ObjectMeta(name=taskmaster_name))
            self.taskmaster = Job(job)
        else:
            raise ValueError("Either taskmaster or taskmaster_name must be provided")

        self.executors_by_name: Dict[str, Job] = {}
        self.output_filer: Optional[Job] = None
        self.constants = Constants()

    def add_executor(self, executor: Job):
        """Add executor to the task."""
        self.executors_by_name.setdefault(executor.get_job().metadata.name, executor)

    def set_output_filer(self, filer: Job):
        """Set output filer for the task."""
        self.output_filer = filer

    def get_taskmaster(self) -> Job:
        """Get taskmaster job."""
        return self.taskmaster

    def get_executors(self) -> List[Job]:
        """Get executors."""
        return sorted(self.executors_by_name.values(), key=self.extract_executor_number)

    def get_last_executor(self) -> Optional[Job]:
        """Get last executor."""
        if not self.executors_by_name:
            return None
        executors = self.get_executors()
        return executors[-1] if executors else None

    def get_output_filer(self) -> Optional[Job]:
        """Get output filer."""
        return self.output_filer

    def extract_executor_number(self, executor: Job) -> int:
        """Extract executor number from the executor's name."""
        taskmaster_name = self.taskmaster.get_job_name()
        prefix = taskmaster_name + self.constants.job_name_exec_prefix
        match = re.match(f"{re.escape(prefix)}(\d+)", executor.get_job_name())
        if match:
            return int(match.group(1))
        return float("inf")

    def get_executor_name(self, executor_index: int) -> str:
        """Get executor name based on the taskmaster's job name and executor index."""
        taskmaster_name = self.taskmaster.get_job_name()
        return (
            f"{taskmaster_name}"
            f"{self.constants.job_name_exec_prefix}"
            f"{str(executor_index).zfill(self.constants.job_name_exec_no_length)}"
        )
