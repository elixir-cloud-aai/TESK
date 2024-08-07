"""Tool aimed at building Kubernetes object structure of a single task.

Job objects passed to its methods must be prefiltered and belong to a single task
(the class does not perform job objects filtering itself).
Pods must be added, when all jobs have already been added.
Thus, correct order of calls:
- Taskmaster TaskBuilder#addJobList(List) or TaskBuilder#addJob(V1Job)
- Executors and outputFiler TaskBuilder#addJobList(List) or TaskBuilder#addJob(V1Job)
- Pods by TaskBuilder#addPodList(List)
"""

from typing import List, Optional

from tesk.api.kubernetes.convert.data.build_strategy import BuildStrategy
from tesk.api.kubernetes.convert.data.job import Job
from tesk.api.kubernetes.convert.data.task import Task


class SingleTaskStrategy(BuildStrategy):
    """Tool aimed at building Kubernetes object structure of a single task.

    Job objects passed to its methods must be prefiltered and belong to a single task
    (the class does not perform job objects filtering itself).
    Pods must be added, when all jobs have already been added.
    Thus, correct order of calls:
    - Taskmaster TaskBuilder#addJobList(List) or TaskBuilder#addJob(V1Job)
    - Executors and outputFiler TaskBuilder#addJobList(List) or
      TaskBuilder#addJob(V1Job)
    - Pods by TaskBuilder#addPodList(List)
    """

    def __init__(self):
        """Initialise SingleTaskStrategy."""
        self.task = None

    def add_task_master_job(self, taskmaster_job: Job):
        """Add taskmaster job."""
        self.task = Task(taskmaster_job)

    def add_executor_job(self, executor_job: Job):
        """Add executor job."""
        if self.task:
            self.task.add_executor(executor_job)

    def add_output_filer_job(self, filer_job: Job):
        """Add output filer job."""
        if self.task:
            self.task.set_output_filer(filer_job)

    def get_task(self) -> Optional[Task]:
        """Get task."""
        return self.task

    def get_task_list(self) -> List[Task]:
        """Get single task as list."""
        return [self.task] if self.task else []
