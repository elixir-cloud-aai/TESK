"""Constants for Kubernetes API."""

from typing import Set

from pydantic import BaseModel, Field


class Constants(BaseModel):
    taskmaster_input: str = Field(
        default="JSON_INPUT",
        description="ENV var that serves as taskmaster script input (JSON format)",
    )
    taskmaster_input_exec_key: str = Field(
        default="executors",
        description="Key in JSON taskmaster input, which holds list of executors",
    )
    volume_name: str = Field("PVC", description="Volume name")
    job_create_attempts_no: int = Field(
        default=5,
        description="Number of attempts of job creation in case of name collision",
    )
    job_name_taskm_prefix: str = Field(
        default="task-",
        description="Constant prefix of taskmaster's job name (== TES task ID)",
    )
    job_name_exec_prefix: str = Field(
        default="-ex-",
        description="Part of executor's job name, that follows taskmaster's name",
    )
    job_name_taskm_rand_part_length: int = Field(
        default=4,
        description="No of bytes of random part of task master's name (which end up encoded to hex)",
    )
    job_name_exec_no_length: int = Field(
        default=2,
        description="No of digits reserved for executor number in executor's job name. Ends up padded with '0' for numbers < 10",
    )
    job_name_filer_suf: str = Field(
        default="-outputs-filer", description="Output filer name suffix"
    )
    ann_testask_name_key: str = Field(
        default="tes-task-name",
        description="Key of the annotation, that stores name of TES task in both taskmaster's job and executor's jobs",
    )
    ann_json_input_key: str = Field(
        default="json-input",
        description="Key of the annotation, that stores whole input TES task serialized to JSON",
    )
    label_testask_id_key: str = Field(
        default="taskmaster-name",
        description="Key of the label, that stores taskmaster's name (==TES task generated ID) in executor jobs",
    )
    label_jobtype_key: str = Field(
        default="job-type",
        description="Key of the label, that stores type of a job (taskmaster or executor)",
    )
    label_jobtype_value_taskm: str = Field(
        default="taskmaster",
        description="Value of the label with taskmaster's job type",
    )
    label_jobtype_value_exec: str = Field(
        default="executor", description="Value of the label with executor's job type"
    )
    label_execno_key: str = Field(
        default="executor-no",
        description="Key of the label, that holds executor number for executor jobs",
    )
    label_taskstate_key: str = Field(
        default="task-status",
        description="Key of the label, that holds executor's state",
    )
    label_taskstate_value_canc: str = Field(
        default="Cancelled",
        description="Value of the label, that holds executor's Cancelled state",
    )
    label_userid_key: str = Field(
        default="creator-user-id", description="Key of the label, that holds user id"
    )
    label_groupname_key: str = Field(
        default="creator-group-name",
        description="Key of the label, that holds user's group name",
    )
    absolute_path_regexp: str = Field(
        default="^\\/.*", description="Pattern to validate paths"
    )
    absolute_path_message: str = Field(
        default="must be an absolute path",
        description="Message for absolute path validation (to avoid message.properties)",
    )
    resource_disk_default: float = Field(0.1, description="Default resource disk value")
    completed_states: Set[str] = Field(
        default={"CANCELED", "COMPLETE", "EXECUTOR_ERROR", "SYSTEM_ERROR"},
        description="TES task states, indicating task is not running and cannot be cancelled",
    )
    ftp_secret_username_env: str = Field(
        default="TESK_FTP_USERNAME",
        description="Name of taskmaster's ENV variable with username of FTP account used for storage",
    )
    ftp_secret_password_env: str = Field(
        default="TESK_FTP_PASSWORD",
        description="Name of taskmaster's ENV variable with password of FTP account used for storage",
    )
    cancel_patch: str = Field(
        default='{"metadata":{"labels":{"task-status":"Cancelled"}}}',
        description="Patch object passed to job API, when cancelling task",
    )


class PodPhase(BaseModel):
    code: str = Field(default="Pending", description="The phase code of the pod")


class K8sConstants(BaseModel):
    k8s_batch_api_version: str = Field(
        default="batch/v1", description="Kubernetes Batch API version"
    )
    k8s_batch_api_job_type: str = Field(
        default="Job", description="Kubernetes Job object type"
    )
    job_restart_policy: str = Field(
        default="Never", description="Kubernetes Job restart policy"
    )
    resource_cpu_key: str = Field("cpu", description="Executor CPU resource label")
    resource_mem_key: str = Field(
        default="memory", description="Executor memory resource label"
    )
    resource_mem_unit: str = Field(
        default="Gi", description="Executor memory resource unit"
    )
    resource_mem_one_gb: int = Field(
        default=1073741824, description="One Gibibyte (Gi) in bytes"
    )
