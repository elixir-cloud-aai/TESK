"""Constants for Kubernetes API."""

from enum import Enum
from typing import Set

from pydantic import BaseModel


class JobConstants(BaseModel):
    """Constants related to job and tasks.

    Attributes:
        taskmaster_input: str = ENV var that serves as taskmaster script input (JSON
            format)
        taskmaster_input_exec_key: str = Key in JSON taskmaster input, which holds list
            of executors
        volume_name: str = Volume name
        job_create_attempts_no: int = Number of attempts of job creation in case of name
            collision
        job_name_taskm_prefix: str = Constant prefix of taskmaster's job name (== TES
            task ID)
        job_name_exec_prefix: str = Part of executor's job name, that follows
            taskmaster's name
        job_name_taskm_rand_part_length: int = No of bytes of random part of task
            master's name (which end up encoded to hex)
        job_name_exec_no_length: int = No of digits reserved for executor number in
            executor's job name. Ends up padded with '0' for numbers < 10
        job_name_filer_suf: str = Output filer name suffix
        resource_disk_default: float = Default resource disk value
        completed_states: Set[str] = TES task states, indicating task is not running and
            cannot be cancelled
        executor_backoff_limit: str = Set a number of retries of a job execution.
        filer_backoff_limit: str = Set a number of retries of a filer job execution.
    """

    taskmaster_input: str = "JSON_INPUT"
    taskmaster_input_exec_key: str = "executors"
    volume_name: str = "PVC"
    job_create_attempts_no: int = 5
    job_name_taskm_prefix: str = "task-"
    job_name_exec_prefix: str = "-ex-"
    job_name_taskm_rand_part_length: int = 4
    job_name_exec_no_length: int = (2,)
    job_name_filer_suf: str = "-outputs-filer"
    resource_disk_default: float = 0.1
    completed_states: Set[str] = {
        "CANCELED",
        "COMPLETE",
        "EXECUTOR_ERROR",
        "SYSTEM_ERROR",
    }
    executor_backoff_limit: str = "EXECUTOR_BACKOFF_LIMIT"
    filer_backoff_limit: str = "FILER_BACKOFF_LIMIT"

    class Config:
        """Configuration for class."""

        frozen = True


class AnnotationConstants(BaseModel):
    """Constants related to Kubernetes annotations.

    Attributes:
        ann_testask_name_key: str = Key of the annotation, that stores name of TES task
            in both taskmaster's job and executor's jobs
        ann_json_input_key: str = Key of the annotation, that stores whole input TES
            task serialized to JSON
    """

    ann_testask_name_key: str = "tes-task-name"
    ann_json_input_key: str = "json-input"

    class Config:
        """Configuration for class."""

        frozen = True


class LabelConstants(BaseModel):
    """Constants related to Kubernetes labels.

    Attributes:
        label_testask_id_key: str = Key of the label, that stores taskmaster's name (==
            TES task generated ID) in executor jobs
        label_jobtype_key: str = Key of the label, that stores type of a job (taskmaster
            or executor)
        label_jobtype_value_taskm: str = Value of the label with taskmaster's job type
        label_jobtype_value_exec: str = Value of the label with executor's job type
        label_execno_key: str = Key of the label, that holds executor number for
            executor jobs
        label_taskstate_key: str = Key of the label, that holds executor's state
        label_taskstate_value_canc: str = Value of the label, that holds executor's
            Cancelled state
        label_userid_key: str = Key of the label, that holds user id
        label_groupname_key: str = Key of the label, that holds user's group name
    """

    label_testask_id_key: str = "taskmaster-name"
    label_jobtype_key: str = "job-type"
    label_jobtype_value_taskm: str = "taskmaster"
    label_jobtype_value_exec: str = "executor"
    label_execno_key: str = "executor-no"
    label_taskstate_key: str = "task-status"
    label_taskstate_value_canc: str = "Cancelled"
    label_userid_key: str = "creator-user-id"
    label_groupname_key: str = "creator-group-name"

    class Config:
        """Configuration for class."""

        frozen = True


class PathValidationConstants(BaseModel):
    """Constants related to path validation.

    Attributes:
        absolute_path_regex: str = Pattern to validate path
        absolute_path_message: str = Message for absolute path validation (to avoid
            message.property)
    """

    absolute_path_regexp: str = "^\\/.*"
    absolute_path_message: str = "must be an absolute path"

    class Config:
        """Configuration for class."""

        frozen = True


class FTPConstants(BaseModel):
    """Constants related to FTP configuration.

    Attributes:
        ftp_secret_username_env: str = Environment variable name for FTP username
        ftp_secret_password_env: str = Environment variable name for FTP password
    """

    ftp_secret_username_env: str = "TESK_FTP_USERNAME"
    ftp_secret_password_env: str = "TESK_FTP_PASSWORD"

    class Config:
        """Configuration for class."""

        frozen = True


class PatchConstants(BaseModel):
    """Constants related to patch operations.

    Attributes:
        cancel_path: str = Patch object passed to job API, when cancelling task
    """

    cancel_patch: str = '{"metadata":{"labels":{"task-status":"Cancelled"}}}'

    class Config:
        """Configuration for class."""

        frozen = True


class K8sConstants(BaseModel):
    """Constants related to Kubernetes.

    Attribute:
        k8s_batch_api_version: Kubernetes Batch API version
        k8s_batch_api_job_type: Kubernetes Job object type
        job_restart_policy: Kubernetes Job restart policy
        resource_cpu_key: Executor CPU resource label
        resource_mem_key: Executor memory resource label
        resource_mem_unit: Executor memory resource unit
        resource_mem_one_gb: One Gibibyte (Gi) in bytes
    """

    k8s_batch_api_version: str = "batch/v1"
    k8s_batch_api_job_type: str = "Job"
    job_restart_policy: str = "Never"
    resource_cpu_key: str = "cpu"
    resource_mem_key: str = "memory"
    resource_mem_unit: str = "Gi"
    resource_mem_one_gb: int = 1073741824

    class Config:
        """Configuration for class."""

        frozen = True

    class PodPhase(Enum):
        """Pod state.

        Attribute:
            PENDING: str = pending
        """

        PENDING = "Pending"

        class Config:
            """Configuration for class."""

            frozen = True

        def get_code(self) -> str:
            """Return the pod state."""
            return self.value


class TeskK8sConstants(BaseModel):
    """All the constants related to k8s and job creation.

    Attributes:
        job_constants
        annotation_constants
        label_constants
        path_validation_constants
        ftp_constants
        patch_constants
        k8s_constants
    """

    job_constants: JobConstants = JobConstants()
    annotation_constants: AnnotationConstants = AnnotationConstants()
    label_constants: LabelConstants = LabelConstants()
    path_validation_constants: PathValidationConstants = PathValidationConstants()
    ftp_constants: FTPConstants = FTPConstants()
    patch_constants: PatchConstants = PatchConstants()
    k8s_constants: K8sConstants = K8sConstants()

    class Config:
        """Configuration for class."""

        frozen = True


tesk_k8s_constants = TeskK8sConstants()
