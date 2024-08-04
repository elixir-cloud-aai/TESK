"""Wrapper Abstraction of Kubernetes Python client API for TESK."""

import logging
from typing import Optional

from kubernetes import client, config
from kubernetes.client import (
    V1ConfigMap,
    V1Job,
    V1LabelSelector,
    V1LimitRangeList,
    V1PodList,
)
from kubernetes.utils.quantity import parse_quantity  # type: ignore

from tesk.api.kubernetes.constants import Constants
from tesk.constants import TeskConstants
from tesk.exceptions import KubernetesError, NotFound

logger = logging.getLogger(__name__)


class KubernetesClientWrapper:
    """Kubernetes client wrapper class."""

    def __init__(self, namespace=TeskConstants.tesk_namespace):
        """Initialize the Kubernetes client wrapper.

        Args:
          namespace: Namespace to use for Kubernetes.
        """
        config.load_kube_config()
        self.batch_api = client.BatchV1Api()
        self.core_api = client.CoreV1Api()
        self.namespace = namespace
        self.constant = Constants()

    def create_job(self, job: V1Job) -> V1Job:
        """Create a job in the Kubernetes cluster.

        Returns:
                Job object created in the Kubernetes cluster.
        """
        try:
            v1_job: V1Job = self.batch_api.create_namespaced_job(
                namespace=self.namespace, body=job
            )
            return v1_job
        except KubernetesError as e:
            logger.error(f"Exception when creating job: {e}")
            raise

    def create_config_map(self, config_map: V1ConfigMap) -> V1ConfigMap:
        """Create a config map in the Kubernetes cluster.

        Args:
            config_map: ConfigMap object to create.
        """
        try:
            v1_config_map: V1ConfigMap = self.core_api.create_namespaced_config_map(
                namespace=self.namespace, body=config_map
            )
            return v1_config_map
        except KubernetesError as e:
            logger.error(f"Exception when creating config map: {e}")
            raise

    def read_taskmaster_job(self, task_id: str) -> V1Job:
        """Read a taskmaster job from the Kubernetes cluster.

        task_id: Task identifier.

        Returns:
                Job object read from the Kubernetes cluster

        Raises:
                Exception: If the task is not found.
        """
        try:
            job: V1Job = self.batch_api.read_namespaced_job(
                name=task_id, namespace=self.namespace
            )
            if (
                job.metadata
                and job.metadata.labels
                and self.constant.label_jobtype_key in job.metadata.labels
                and job.metadata.labels[self.constant.label_jobtype_key]
                == self.constant.label_jobtype_value_taskm
            ):
                return job
        except KubernetesError as e:
            if e.status != NotFound.code:
                logger.error(f"Exception when reading job: {e}")
                raise
        raise Exception(f"Task {task_id} not found")

    def list_jobs(self, label_selector=None, limit=None):
        """List jobs in the Kubernetes cluster.

        Args:
                label_selector: Label selector to filter jobs.
                limit: Maximum number of jobs to return.
        """
        try:
            return self.batch_api.list_namespaced_job(
                namespace=self.namespace, label_selector=label_selector, limit=limit
            )
        except KubernetesError as e:
            logger.error(f"Exception when listing jobs: {e}")
            raise

    def list_limits(self, label_selector=None, limit=None) -> V1LimitRangeList:
        """List limit ranges in the Kubernetes cluster.

        Args:
            label_selector: Label selector to filter limit ranges.
            limit: Maximum number of limit ranges to return.
        """
        try:
            limits: V1LimitRangeList = self.core_api.list_namespaced_limit_range(
                namespace=self.namespace, label_selector=label_selector, limit=limit
            )
            return limits
        except KubernetesError as e:
            logger.error(f"Exception when listing limits: {e}")
            raise

    def minimum_ram_gb(self) -> float:
        """Get the minimum amount of RAM in the cluster.

        Returns:
            Minimum amount of RAM in the cluster in GB.
        """
        try:
            min_ram = 0
            limits = self.list_limits().items
            for limit in limits:
                if limit.spec:
                    for item in limit.spec.limits:
                        if item.min and "memory" in item.min:
                            mem_quantity = item.min["memory"]
                            mem_bytes = self.quantity_to_bytes(mem_quantity)
                            min_ram = max(min_ram, mem_bytes)
            return min_ram / (1024**3)
        except (ValueError, TypeError) as e:
            logger.error(f"Error in minimum_ram_gb: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Unexpected error in minimum_ram_gb: {e}")
            raise

    def quantity_to_bytes(self, quantity: str) -> int:
        """Convert quantity(resource) to bytes."""
        parsed_quantity: int = parse_quantity(quantity)
        return parsed_quantity

    def list_single_job_pods(self, job: V1Job) -> V1PodList:
        """List pods associated with a single job.

        Args:
          job: Job object to list pods for.
        """
        try:
            if (
                job.spec
                and job.spec.selector
                and isinstance(job.spec.selector, V1LabelSelector)
                and job.spec.selector.match_labels
            ):
                label_selector = ",".join(
                    f"{k}={v}" for k, v in job.spec.selector.match_labels.items()
                )
                namespaced_pods: V1PodList = self.core_api.list_namespaced_pod(
                    namespace=self.namespace, label_selector=label_selector
                )
                return namespaced_pods
            else:
                logger.error("Job spec, selector, or match_labels is None or invalid")
                return V1PodList(items=[])
        except KubernetesError as e:
            logger.error(f"Exception when listing pods: {e}")
            raise

    def read_pod_log(self, pod_name: str) -> Optional[str]:
        """Read logs from a pod.

        Args:
            pod_name: Name of the pod to read logs from.
        """
        try:
            pod_log: str = self.core_api.read_namespaced_pod_log(
                name=pod_name, namespace=self.namespace
            )
            return pod_log
        except KubernetesError as e:
            logger.error(f"Exception when reading pod log: {e}")
            return None

    def label_job_as_cancelled(self, task_id: str) -> None:
        """Label a job as cancelled.

        Args:
            task_id: Task identifier.
        """
        try:
            patch = {"metadata": {"labels": {"status": "cancelled"}}}
            self.batch_api.patch_namespaced_job(
                name=task_id, namespace=self.namespace, body=patch
            )
        except KubernetesError as e:
            logger.error(f"Exception when labeling job as cancelled: {e}")
            raise

    def label_pod_as_cancelled(self, pod_name: str) -> None:
        """Label a pod as cancelled.

        Args:
            pod_name: Pod name.
        """
        try:
            patch = {"metadata": {"labels": {"status": "cancelled"}}}
            self.core_api.patch_namespaced_pod(
                name=pod_name, namespace=self.namespace, body=patch
            )
        except KubernetesError as e:
            logger.error(f"Exception when labeling pod as cancelled: {e}")
            raise
