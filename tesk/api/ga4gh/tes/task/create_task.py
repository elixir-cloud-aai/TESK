"""TESK API module for creating a task."""

import logging
from http import HTTPStatus

from tesk.api.ga4gh.tes.models import TesCreateTaskResponse, TesResources, TesTask
from tesk.api.ga4gh.tes.task.task_request import TesTaskRequest
from tesk.exceptions import KubernetesError

logger = logging.getLogger(__name__)


class CreateTesTask(TesTaskRequest):
    """Create TES task."""

    def __init__(
        self,
        task: TesTask,
    ):
        """Initialize the CreateTask class.

        Args:
          task: TES task to create.
        """
        super().__init__()
        self.task = task

    def handle_request(self) -> TesCreateTaskResponse:
        """Create TES task."""
        attempts_no: int = 0
        total_attempts_no: int = (
            self.tesk_k8s_constants.job_constants.JOB_CREATE_ATTEMPTS_NO
        )

        while (
            attempts_no < self.tesk_k8s_constants.job_constants.JOB_CREATE_ATTEMPTS_NO
        ):
            try:
                logger.debug(
                    f"Creating K8s job, attempt no: {attempts_no}/{total_attempts_no}."
                )
                attempts_no += 1
                minimum_ram_gb = self.kubernetes_client_wrapper.minimum_ram_gb()

                if self.task.resources is None:
                    self.task.resources = TesResources(cpu_cores=int(minimum_ram_gb))
                elif (
                    self.task.resources.ram_gb is None
                    or self.task.resources.ram_gb < minimum_ram_gb
                ):
                    self.task.resources.ram_gb = minimum_ram_gb

                taskmaster_job = self.tes_kubernetes_converter.from_tes_task_to_k8s_job(
                    self.task,
                )
                taskmaster_config_map = (
                    self.tes_kubernetes_converter.from_tes_task_to_k8s_config_map(
                        self.task,
                        taskmaster_job,
                    )
                )

                _ = self.kubernetes_client_wrapper.create_config_map(
                    taskmaster_config_map
                )
                created_job = self.kubernetes_client_wrapper.create_job(taskmaster_job)

                assert created_job.metadata is not None
                assert created_job.metadata.name is not None

                return TesCreateTaskResponse(id=created_job.metadata.name)

            except KubernetesError as e:
                if (
                    e.status != HTTPStatus.CONFLICT
                    or attempts_no
                    >= self.tesk_k8s_constants.job_constants.JOB_CREATE_ATTEMPTS_NO
                ):
                    raise e

        return TesCreateTaskResponse(id="")  # To silence mypy, should never be reached
