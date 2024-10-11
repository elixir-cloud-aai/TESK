"""A composite that represents Kubernetes object's graph of a single TES task.

- Taskmaster job with its pods.
- Executor jobs with its pods.
"""

import re
from typing import Dict, List, Optional

from kubernetes.client.models import V1Job, V1ObjectMeta

from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.data.job import Job


class Task:
    """Task is a composite.

    It represents Kubernetes object's graph of a single TES task.
    
    Attributes:
        taskmaster: taskmaster job with its pods
        executors_by_name: executors jobs with its pods
        output_filer: output filer job with its pods
        tesk_k8s_constants: TESK Kubernetes constants
    """

    def __init__(
        self, taskmaster: Optional[Job] = None, taskmaster_name: Optional[str] = None
    ):
        """Initialize the Task.
        
        Args:
            taskmaster: taskmaster job with its pods
            taskmaster_name: name of the taskmaster job
        """
        if taskmaster:
            self.taskmaster = taskmaster
        elif taskmaster_name:
            job = V1Job(metadata=V1ObjectMeta(name=taskmaster_name))
            self.taskmaster = Job(job)
        else:
            raise ValueError("Either taskmaster or taskmaster_name must be provided.")

        self.executors_by_name: Dict[str, Job] = {}
        self.output_filer: Optional[Job] = None
        self.tesk_k8s_constants = tesk_k8s_constants

    def add_executor(self, executor: Job) -> None:
        """Add executor to the task."""
        metadata = executor.get_job().metadata
        assert metadata is not None

        name = metadata.name
        assert name is not None

        self.executors_by_name.setdefault(name, executor)

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
        assert taskmaster_name is not None

        prefix = (
            taskmaster_name + self.tesk_k8s_constants.job_constants.JOB_NAME_EXEC_PREFIX
        )

        inf = 2**31 - 1

        if not (exec_name := executor.get_job_name()):
            return inf

        if match := re.match(f"{re.escape(prefix)}(\d+)", exec_name):
            return int(match.group(1))

        return inf

    def get_executor_name(self, executor_index: int) -> str:
        """Get executor name based on the taskmaster's job name and executor index."""
        taskmaster_name = self.taskmaster.get_job_name()
        return (
            f"{taskmaster_name}"
            f"{self.tesk_k8s_constants.job_constants.JOB_NAME_EXEC_PREFIX}"
            f"{str(executor_index).zfill(self.tesk_k8s_constants.job_constants.JOB_NAME_EXEC_NO_LENGTH)}"
        )
