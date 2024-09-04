"""Constants for Kubernetes API."""

from enum import Enum
from typing import Set

from pydantic import BaseModel


class JobConstants(BaseModel):
    """Constants related to job and tasks.

    Attributes:
        TASKMASTER_INPUT = ENV var that serves as taskmaster script input (JSON
            format)
        TASKMASTER_INPUT_EXEC_KEY = Key in JSON taskmaster input, which holds list
            of executors
        VOLUME_NAME = Volume name
        JOB_CREATE_ATTEMPTS_NO = Number of attempts of job creation in case of name
            collision
        JOB_NAME_TASKM_PREFIX = Constant prefix of taskmaster's job name (== TES
            task ID)
        JOB_NAME_EXEC_PREFIX = Part of executor's job name, that follows
            taskmaster's name
        JOB_NAME_TASKM_RAND_PART_LENGTH = No of bytes of random part of task
            master's name (which end up encoded to hex)
        JOB_NAME_EXEC_NO_LENGTH = No of digits reserved for executor number in
            executor's job name. Ends up padded with '0' for numbers < 10
        JOB_NAME_FILER_SUF = Output filer name suffix
        RESOURCE_DISK_DEFAULT: float = Default resource disk value
        COMPLETED_STATES = TES task states, indicating task is not running and
            cannot be cancelled
        EXECUTOR_BACKOFF_LIMIT = Set a number of retries of a job execution.
        FILER_BACKOFF_LIMIT = Set a number of retries of a filer job execution.
    """

    TASKMASTER_INPUT: str = "JSON_INPUT"
    TASKMASTER_INPUT_EXEC_KEY: str = "executors"
    VOLUME_NAME: str = "PVC"
    JOB_CREATE_ATTEMPTS_NO: int = 5
    JOB_NAME_TASKM_PREFIX: str = "task-"
    JOB_NAME_EXEC_PREFIX: str = "-ex-"
    JOB_NAME_TASKM_RAND_PART_LENGTH: int = 4
    JOB_NAME_EXEC_NO_LENGTH: int = (2,)
    JOB_NAME_FILER_SUF: str = "-outputs-filer"
    RESOURCE_DISK_DEFAULT: float = 0.1
    COMPLETED_STATES: Set[str] = {
        "CANCELED",
        "COMPLETE",
        "EXECUTOR_ERROR",
        "SYSTEM_ERROR",
    }
    EXECUTOR_BACKOFF_LIMIT: str = "EXECUTOR_BACKOFF_LIMIT"
    FILER_BACKOFF_LIMIT: str = "FILER_BACKOFF_LIMIT"

    class Config:
        """Configuration for class."""

        frozen = True


class AnnotationConstants(BaseModel):
    """Constants related to Kubernetes annotations.

    Attributes:
        ANN_TESTASK_NAME_KEY = Key of the annotation, that stores name of TES task
            in both taskmaster's job and executor's jobs
        ANN_JSON_INPUT_KEY = Key of the annotation, that stores whole input TES
            task serialized to JSON
    """

    ANN_TESTASK_NAME_KEY: str = "tes-task-name"
    ANN_JSON_INPUT_KEY: str = "json-input"

    class Config:
        """Configuration for class."""

        frozen = True


class LabelConstants(BaseModel):
    """Constants related to Kubernetes labels.

    Attributes:
        LABEL_TESTASK_ID_KEY = Key of the label, that stores taskmaster's name (==
            TES task generated ID) in executor jobs
        LABEL_JOBTYPE_KEY = Key of the label, that stores type of a job (taskmaster
            or executor)
        LABEL_JOBTYPE_VALUE_TASKM = Value of the label with taskmaster's job type
        LABEL_JOBTYPE_VALUE_EXEC = Value of the label with executor's job type
        LABEL_EXECNO_KEY = Key of the label, that holds executor number for
            executor jobs
        LABEL_TASKSTATE_KEY = Key of the label, that holds executor's state
        LABEL_TASKSTATE_VALUE_CANC = Value of the label, that holds executor's
            Cancelled state
        LABEL_USERID_KEY = Key of the label, that holds user id
        LABEL_GROUPNAME_KEY = Key of the label, that holds user's group name
    """

    LABEL_TESTASK_ID_KEY: str = "taskmaster-name"
    LABEL_JOBTYPE_KEY: str = "job-type"
    LABEL_JOBTYPE_VALUE_TASKM: str = "taskmaster"
    LABEL_JOBTYPE_VALUE_EXEC: str = "executor"
    LABEL_EXECNO_KEY: str = "executor-no"
    LABEL_TASKSTATE_KEY: str = "task-status"
    LABEL_TASKSTATE_VALUE_CANC: str = "Cancelled"
    LABEL_USERID_KEY: str = "creator-user-id"
    LABEL_GROUPNAME_KEY: str = "creator-group-name"

    class Config:
        """Configuration for class."""

        frozen = True


class PathValidationConstants(BaseModel):
    """Constants related to path validation.

    Attributes:
        ABSOLUTE_PATH_REGEX = Pattern to validate path
        ABSOLUTE_PATH_MESSAGE = Message for absolute path validation (to avoid
            message.property)
    """

    ABSOLUTE_PATH_REGEXP: str = "^\\/.*"
    ABSOLUTE_PATH_MESSAGE: str = "must be an absolute path"

    class Config:
        """Configuration for class."""

        frozen = True


class FTPConstants(BaseModel):
    """Constants related to FTP configuration.

    Attributes:
        FTP_SECRET_USERNAME_ENV = Environment variable name for FTP username
        FTP_SECRET_PASSWORD_ENV = Environment variable name for FTP password
    """

    FTP_SECRET_USERNAME_ENV: str = "TESK_FTP_USERNAME"
    FTP_SECRET_PASSWORD_ENV: str = "TESK_FTP_PASSWORD"

    class Config:
        """Configuration for class."""

        frozen = True


class PatchConstants(BaseModel):
    """Constants related to patch operations.

    Attributes:
        CANCEL_PATH = Patch object passed to job API, when cancelling task
    """

    CANCEL_PATCH: str = '{"metadata":{"labels":{"task-status":"Cancelled"}}}'

    class Config:
        """Configuration for class."""

        frozen = True


class K8sConstants(BaseModel):
    """Constants related to Kubernetes.

    Attribute:
        K8S_BATCH_API_VERSION: Kubernetes Batch API version
        K8S_BATCH_API_JOB_TYPE: Kubernetes Job object type
        JOB_RESTART_POLICY: Kubernetes Job restart policy
        RESOURCE_CPU_KEY: Executor CPU resource label
        RESOURCE_MEM_KEY: Executor memory resource label
        RESOURCE_MEM_UNIT: Executor memory resource unit
        RESOURCE_MEM_ONE_GB: One Gibibyte (Gi) in bytes
    """

    K8S_BATCH_API_VERSION: str = "batch/v1"
    K8S_BATCH_API_JOB_TYPE: str = "Job"
    JOB_RESTART_POLICY: str = "Never"
    RESOURCE_CPU_KEY: str = "cpu"
    RESOURCE_MEM_KEY: str = "memory"
    RESOURCE_MEM_UNIT: str = "Gi"
    RESOURCE_MEM_ONE_GB: int = 1073741824

    class Config:
        """Configuration for class."""

        frozen = True

    class PodPhase(Enum):
        """Pod state.

        Attribute:
            PENDING = pending
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
        JOB_CONSTANTS
        ANNOTATION_CONSTANTS
        LABEL_CONSTANTS
        PATH_VALIDATION_CONSTANTS
        FTP_CONSTANTS
        PATCH_CONSTANTS
        K8S_CONSTANTS
    """

    JOB_CONSTANTS: JobConstants = JobConstants()
    ANNOTATION_CONSTANTS: AnnotationConstants = AnnotationConstants()
    LABEL_CONSTANTS: LabelConstants = LabelConstants()
    PATH_VALIDATION_CONSTANTS: PathValidationConstants = PathValidationConstants()
    FTP_CONSTANTS: FTPConstants = FTPConstants()
    PATCH_CONSTANTS: PatchConstants = PatchConstants()
    K8S_CONSTANTS: K8sConstants = K8sConstants()

    class Config:
        """Configuration for class."""

        frozen = True


tesk_k8s_constants = TeskK8sConstants()
