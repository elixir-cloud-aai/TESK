"""TESK API module for creating a task."""

import logging

from pydantic import BaseModel

from tesk.api.ga4gh.tes.models import TesResources, TesTask
from tesk.api.kubernetes.client_wrapper import KubernetesClientWrapper
from tesk.api.kubernetes.constants import Constants
from tesk.api.kubernetes.convert.converter import TesKubernetesConverter
from tesk.constants import TeskConstants
from tesk.exceptions import KubernetesError
from tesk.api.ga4gh.tes.task.task_request import TesTaskRequest
from tesk.api.ga4gh.tes.models import TesCreateTaskResponse

logger = logging.getLogger(__name__)


class CreateTesTask(TesTaskRequest):
    """Create TES task."""

    # TODO: Add user to the class when auth implemented in FOCA
    def __init__(self, task: TesTask, namespace=TeskConstants.tesk_namespace):
        """Initialize the CreateTask class.

        Args:
          task: TES task to create.
          namespace: Kubernetes namespace where the task is created.
        """
        self.task = task
        # self.user = user
        self.namespace = namespace
        self.kubernetes_client_wrapper = KubernetesClientWrapper()
        self.tes_kubernetes_converter = TesKubernetesConverter(self.namespace)
        self.constants = Constants()

    def create_task(self) -> TesCreateTaskResponse:
        """Create TES task."""
        attempts_no = 0
        while attempts_no < self.constants.job_create_attempts_no:
            try:
                attempts_no += 1
                resources = self.task.resources

                minimum_ram_gb = self.kubernetes_client_wrapper.minimum_ram_gb()
                if not self.task.resources:
                    self.task.resources = TesResources(cpu_cores=int(minimum_ram_gb))
                if resources and resources.ram_gb and resources.ram_gb < minimum_ram_gb:
                    self.task.resources.ram_gb = minimum_ram_gb

                task_master_job = (
                    self.tes_kubernetes_converter.from_tes_task_to_k8s_job(
                        self.task,
                        # self.user
                    )
                )

                task_master_config_map = (
                    self.tes_kubernetes_converter.from_tes_task_to_k8s_config_map(
                        self.task,
                        task_master_job,
                        # self.user
                    )
                )

                # Create ConfigMap and Job
                _ = self.kubernetes_client_wrapper.create_config_map(
                    task_master_config_map
                )
                created_job = self.kubernetes_client_wrapper.create_job(task_master_job)

                assert created_job.metadata is not None
                assert created_job.metadata.name is not None

                return TesCreateTaskResponse(id=created_job.metadata.name)

            except KubernetesError as e:
                if (
                    not e.is_object_name_duplicated()
                    or attempts_no >= self.constants.job_create_attempts_no
                ):
                    raise e

            except Exception as exc:
                logging.error("ERROR: In createTask", exc_info=True)
                raise exc
        return {}  # Dummy return to silence mypy

    def handle_request(self) -> BaseModel:
        return self.create_task()
