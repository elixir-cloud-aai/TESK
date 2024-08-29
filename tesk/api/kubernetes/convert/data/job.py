"""A container for a single Kubernetes job object.

Can be both a taskmaster and an executor, it list of worker pods (Kubernetes
Pod objects).
"""

from enum import Enum
from typing import List, Optional

from kubernetes.client import V1Job, V1ObjectMeta, V1Pod


class Job:
    """Class to list worker pods (Kubernetes Pod objects)."""

    def __init__(self, job: V1Job):
        """Initializes the Job with a Kubernetes job object."""
        self.job: V1Job = job
        self.pods: List[V1Pod] = []

    def get_job(self) -> V1Job:
        """Returns the Kubernetes job object."""
        return self.job

    def add_pod(self, pod: V1Pod):
        """Adds a single pod to the list."""
        self.pods.append(pod)

    def has_pods(self) -> bool:
        """Checks if the job has any pods."""
        return bool(self.pods)

    def get_first_pod(self) -> Optional[V1Pod]:
        """Returns arbitrarily chosen pod from the list.

        Currently the first one added or None if the job has no pods.
        """
        if not self.has_pods():
            return None
        return self.pods[0]

    def get_pods(self) -> List[V1Pod]:
        """Returns the list of job pods.

        Returns in the order of addition to the list or an empty list if no pods.
        """
        return self.pods

    def change_job_name(self, new_name: str):
        """Changes the job name.

        Also the names in its metadata and container specs.
        """
        if self.job.metadata is None:
            self.job.metadata = V1ObjectMeta(name=new_name)
        else:
            self.job.metadata.name = new_name

        if (
            self.job is not None
            and self.job.spec is not None
            and self.job.spec.template is not None
            and self.job.spec.template.metadata is not None
        ):
            self.job.spec.template.metadata.name = new_name

            if self.job.spec.template.spec and self.job.spec.template.spec.containers:
                self.job.spec.template.spec.containers[0].name = new_name

    def get_job_name(self) -> Optional[str]:
        """Returns the job name."""
        return self.job.metadata.name if self.job.metadata else None


class JobStatus(Enum):
    """State of job."""

    ACTIVE = "Active"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
