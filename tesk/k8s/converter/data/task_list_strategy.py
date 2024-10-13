"""Strategy aimed at building Kubernetes object structure of a list of tasks."""

import logging
from typing import Dict, Optional

from kubernetes.client.models import V1Job

from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.data.build_strategy import BuildStrategy
from tesk.k8s.converter.data.job import Job
from tesk.k8s.converter.data.task import Task

logger = logging.getLogger(__name__)


class TaskListStrategy(BuildStrategy):
    """Strategy aimed at building Kubernetes object structure of a list of tasks.

    All taskmaster jobs with unique names passed to it will get stored.
    Only those executor jobs that match already stored taskmaster jobs will be stored
    (filtering done by taskmaster's name and corresponding executor's label).
    Pods must be added, when all jobs have already been added.
    Thus, correct order of calls:
    1) taskmasters (`TaskBuilder.add_job_list`)
    2) executors and outputFilers (`TaskBuilder.add_job_list`)
    3) pods by (`TaskBuilder.add_pod_list`)

    Arguments:
        tasks_by_id: Dictionary of tasks by their IDs
    """

    def __init__(self):
        """Initialise the TaskListStrategy."""
        self.tasks_by_id: Dict[str, Task] = {}

    def add_taskmaster_job(self, taskmaster_job: Job) -> None:
        """Add taskmaster job as task the list.

        Args:
            taskmaster_job: Taskmaster job.

        Returns:
            None
        """
        job: V1Job = taskmaster_job.get_job()
        name: Optional[str] = job.metadata.labels.get(
            tesk_k8s_constants.label_constants.LABEL_TESTASK_ID_KEY
        )
        assert (
            name is not None
        ), "LABEL_TESTASK_ID_KEY must be present in job metadata labels"

        if name not in self.tasks_by_id:
            self.tasks_by_id[name] = Task(taskmaster=taskmaster_job)

    def add_executor_job(self, executor_job) -> None:
        """Add executor job to its corresponding taskmaster.

        Args:
            executor_job: Executor job.

        Returns:
            None
        """
        job: V1Job = executor_job.get_job()
        name: Optional[str] = job.metadata.labels.get(
            tesk_k8s_constants.label_constants.LABEL_TESTASK_ID_KEY
        )
        assert (
            name is not None
        ), "LABEL_TESTASK_ID_KEY must be present in job metadata labels"

        if name in self.tasks_by_id:
            self.tasks_by_id[name].add_executor(executor_job)

    def add_output_filer_job(self, executor_job: Job) -> None:
        """Add output filer job to its corresponding taskmaster.

        Args:
            executor_job: Output filer job.

        Returns:
            None
        """
        try:
            output_filer_suffix: int = executor_job.get_job_name().find(
                tesk_k8s_constants.job_constants.JOB_NAME_FILER_SUF
            )
        except ValueError as e:
            logger.debug(f"Output filer job name does not contain suffix: {e}")
            return
        job_name = executor_job.get_job_name()
        assert job_name is not None, "Job name should not be None"
        taskmaster_name: str = job_name[:output_filer_suffix]

        taskmaster: Task = self.tasks_by_id.get(taskmaster_name)
        if taskmaster:
            taskmaster.set_output_filer(executor_job)

    def get_task(self):
        """Unsupported method for TaskListStrategy."""
        raise NotImplementedError("Method is not supported for TaskListStrategy/")

    def get_task_list(self):
        """Get the task list.

        Returns:
            List[Task]: List of Task objects.
        """
        return list(self.tasks_by_id.values())
