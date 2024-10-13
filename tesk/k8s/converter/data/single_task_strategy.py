"""Single task strategy for building Kubernetes object structure of a single task."""

from typing import List

from tesk.k8s.converter.data.build_strategy import BuildStrategy
from tesk.k8s.converter.data.job import Job
from tesk.k8s.converter.data.task import Task


class SingleTaskStrategy(BuildStrategy):
    """Single task strategy for building Kubernetes object structure of a single task.

    Aimed at building Kubernetes object structure of a single task. Job objects passed
    to its methods must be prefiltered and belong to a single task (the class does not
    perform job objects filtering itself). Pods must be added, when all jobs have
    already been added. Thus, correct order of calls:
    1) taskmaster (`TaskBuilder.add_job_list` or `TaskBuilder.add_job`)
    2) executors and outputFiler (`TaskBuilder.add_job_list` or
        `TaskBuilder.add_job`)
    3) pods by (`TaskBuilder.add_pod_list`)

    Arguments:
        task: Task object.
    """

    def __init__(self):
        """Initialise the SingleTaskStrategy."""
        self.task: Task = None

    def add_taskmaster_job(self, taskmaster_job: Job) -> None:
        """Add taskmaster job to the strategy.

        Args:
            taskmaster_job: Taskmaster job.

        Returns:
            None
        """
        self.task = Task(taskmaster=taskmaster_job)

    def add_executor_job(self, executor_job: Job) -> None:
        """Add executor job to the strategy.

        Args:
            executor_job: Executor job.

        Returns:
            None
        """
        if self.task:
            self.task.add_executor(executor_job)

    def add_output_filer_job(self, executor_job: Job) -> None:
        """Add output filer job to the strategy.

        Args:
            executor_job: Output filer job.

        Returns:
            None
        """
        if self.task:
            self.task.set_output_filer(executor_job)

    def get_task(self) -> Task:
        """Get the task.

        Returns:
            Task: Task object.
        """
        return self.task

    def get_task_list(self) -> List[Task]:
        """Get the task list.

        Returns:
            List[Task]: List of Task objects.
        """
        return [self.task]
