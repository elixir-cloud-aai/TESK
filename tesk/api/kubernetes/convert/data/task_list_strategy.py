"""Module aimed at building Kubernetes object structure of a list of tasks.

Accomplised by passing to it results of Kubernetes batch method calls.
All taskmaster jobs with unique names passed to it will get stored.
Only those executor jobs that match already stored taskmaster jobs will be stored
(filtering done by taskmaster's name and corresponding executor's label).
Pods must be added, when all jobs have already been added.
Thus, correct order of calls:
- Taskmasters by TaskBuilder#addJobList(List)
- Executors and outputFilers by TaskBuilder#addJobList(List)
- Pods by TaskBuilder#addPodList(List)
"""

from typing import Dict, List, Optional

from tesk.api.kubernetes.constants import Constants
from tesk.api.kubernetes.convert.data.build_strategy import BuildStrategy
from tesk.api.kubernetes.convert.data.job import Job
from tesk.api.kubernetes.convert.data.task import Task


class TaskListStrategy(BuildStrategy):
    """Class for building Kubernetes object structure of a list of tasks.

    Accomplised by passing to it results of Kubernetes batch method calls.
    All taskmaster jobs with unique names passed to it will get stored.
    Only those executor jobs that match already stored taskmaster jobs will be stored
    (filtering done by taskmaster's name and corresponding executor's label).
    Pods must be added, when all jobs have already been added.
    Thus, correct order of calls:
    - Taskmasters by TaskBuilder#addJobList(List)
    - Executors and outputFilers by TaskBuilder#addJobList(List)
    - Pods by TaskBuilder#addPodList(List)
    """

    def __init__(self):
        """Intialize TaskListStrategy."""
        self.tasks_by_id: Dict[str, Task] = {}
        self.constants = Constants()

    def add_task_master_job(self, taskmaster_job: Job):
        """Add taskmater job."""
        task_name = taskmaster_job.get_job().metadata.name
        if task_name not in self.tasks_by_id:
            self.tasks_by_id[task_name] = Task(taskmaster_job)

    def add_executor_job(self, executor_job: Job):
        """Add executor Job."""
        taskmaster_name = executor_job.get_job().metadata.labels.get(
            self.constants.label_testask_id_key
        )
        if taskmaster_name in self.tasks_by_id:
            self.tasks_by_id[taskmaster_name].add_executor(executor_job)

    def add_output_filer_job(self, filer_job: Job):
        """Add output filer job."""
        output_filer_suffix = filer_job.get_job_name().find(
            self.constants.job_name_filer_suf
        )
        if output_filer_suffix == -1:
            return
        taskmaster_name = filer_job.get_job_name()[:output_filer_suffix]
        if taskmaster_name in self.tasks_by_id:
            self.tasks_by_id[taskmaster_name].set_output_filer(filer_job)

    def get_task(self) -> Optional[Task]:
        """Get task."""
        raise NotImplementedError("This method is not supported for TaskListStrategy")

    def get_task_list(self) -> List[Task]:
        """Get list of tasks."""
        return list(self.tasks_by_id.values())
