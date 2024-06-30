"""Models for TES API."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TesCancelTaskResponse(BaseModel):
  """Represents a response for task cancellation in TES."""


class TesCreateTaskResponse(BaseModel):
  """Represents a response for task creation in TES.

  Attributes:
      id (str): Task identifier assigned by the server.
  """

  id: str = Field(..., description="Task identifier assigned by the server.")


class TesExecutor(BaseModel):
  """Represents an executor configuration for TES tasks.

  Attributes:
      image (str): Name of the container image.
      command (List[str]): Sequence of program arguments to execute.
      workdir (Optional[str]): Working directory for the command.
      stdin (Optional[str]): Path to file for executor's stdin.
      stdout (Optional[str]): Path to file for executor's stdout.
      stderr (Optional[str]): Path to file for executor's stderr.
      env (Optional[Dict[str, str]]): Environmental variables for the container.
      ignore_error (Optional[bool]): Flag to continue on errors.
  """

  image: str = Field(
    ...,
    description="Name of the container image. The string will be passed as the image\n"
    "argument to the containerization run command. Examples:\n"
    "   - `ubuntu`\n"
    "   - `quay.io/aptible/ubuntu`\n"
    "   - `gcr.io/my-org/my-image`\n"
    "   - `myregistryhost:5000/fedora/httpd:version1.0`",
    example="ubuntu:20.04",
  )
  command: list[str] = Field(
    ...,
    description="A sequence of program arguments to execute, where the first argument\n"
    "is the program to execute (i.e. argv). Example:\n"
    "```\n"
    "{\n"
    '  "command" : ["/bin/md5", "/data/file1"]\n'
    "}\n"
    "```",
    example=["/bin/md5", "/data/file1"],
  )
  workdir: Optional[str] = Field(
    None,
    description="The working directory that the command will be executed in.\n"
    "If not defined, the system will default to the directory set by\n"
    "the container image.",
    example="/data/",
  )
  stdin: Optional[str] = Field(
    None,
    description="Path inside the container to a file which will be piped\n"
    "to the executor's stdin. This must be an absolute path. This mechanism\n"
    "could be used in conjunction with the input declaration to process\n"
    "a data file using a tool that expects STDIN.\n\n"
    "For example, to get the MD5 sum of a file by reading it into the STDIN\n"
    "```\n"
    "{\n"
    '  "command" : ["/bin/md5"],\n'
    '  "stdin" : "/data/file1"\n'
    "}\n"
    "```",
    example="/data/file1",
  )
  stdout: Optional[str] = Field(
    None,
    description="Path inside the container to a file where the executor's\n"
    "stdout will be written to. Must be an absolute path. Example:\n"
    "```\n"
    "{\n"
    '  "stdout" : "/tmp/stdout.log"\n'
    "}\n"
    "```",
    example="/tmp/stdout.log",
  )
  stderr: Optional[str] = Field(
    None,
    description="Path inside the container to a file where the executor's\n"
    "stderr will be written to. Must be an absolute path. Example:\n"
    "```\n"
    "{\n"
    '  "stderr" : "/tmp/stderr.log"\n'
    "}\n"
    "```",
    example="/tmp/stderr.log",
  )
  env: Optional[Dict[str, str]] = Field(
    None,
    description="Environmental variables to set within the container. Example:\n"
    "```\n"
    "{\n"
    '  "env" : {\n'
    '    "ENV_CONFIG_PATH" : "/data/config.file",\n'
    '    "BLASTDB" : "/data/GRC38",\n'
    '    "HMMERDB" : "/data/hmmer"\n'
    "  }\n"
    "}\n"
    "```",
    example={"BLASTDB": "/data/GRC38", "HMMERDB": "/data/hmmer"},
  )
  ignore_error: Optional[bool] = Field(
    None,
    description="Default behavior of running an array of executors is that execution\n"
    "stops on the first error. If `ignore_error` is `True`, then the\n"
    "runner will record error exit codes, but will continue on to the next\n"
    "tesExecutor.",
  )


class TesExecutorLog(BaseModel):
  """Represents the log of an executor in TES.

  Attributes:
      start_time (Optional[str]): Start time of the executor.
      end_time (Optional[str]): End time of the executor.
      stdout (Optional[str]): Stdout content.
      stderr (Optional[str]): Stderr content.
      exit_code (int): Exit code.
  """

  start_time: Optional[str] = Field(
    None,
    description="Time the executor started, in RFC 3339 format.",
    example="2020-10-02T10:00:00-05:00",
  )
  end_time: Optional[str] = Field(
    None,
    description="Time the executor ended, in RFC 3339 format.",
    example="2020-10-02T11:00:00-05:00",
  )
  stdout: Optional[str] = Field(
    None,
    description="Stdout content.\n\nThis is meant for convenience. No guarantees are "
    "made about the content.\n Implementations may chose different approaches: only "
    "the head, only the tail,\n a URL reference only, etc.\n\nIn order to capture the "
    "full stdout client should set Executor.stdout\n to a container file path, and "
    "use Task.outputs to upload that file\n to permanent storage.",
  )
  stderr: Optional[str] = Field(
    None,
    description="Stderr content.\n\nThis is meant for convenience. No guarantees are "
    "made about the content.\n Implementations may chose different approaches: only "
    "the head, only the tail,\n a URL reference only, etc.\n\nIn order to capture the "
    "full stderr client should set Executor.stderr\n to a container file path, and "
    "use Task.outputs to upload that file\n to permanent storage.",
  )
  exit_code: int = Field(..., description="Exit code.")


class TesFileType(Enum):
  """Enum for TES file types."""

  FILE = "FILE"
  DIRECTORY = "DIRECTORY"


class TesInput(BaseModel):
  """Represents an input file for a TES task.

  Attributes:
      name (Optional[str]): Name of the input file.
      description (Optional[str]): Description of the input file.
      url (Optional[str]): URL in long term storage.
      path (str): Path of the file inside the container.
      type (Optional[TesFileType]): Type of the file.
      content (Optional[str]): File content literal.
      streamable (Optional[bool]): Flag for streaming interface.
  """

  name: Optional[str] = None
  description: Optional[str] = None
  url: Optional[str] = Field(
    None,
    description='REQUIRED, unless "content" is set.\n\n'
    "URL in long term storage, for example:\n"
    " - s3://my-object-store/file1\n"
    " - gs://my-bucket/file2\n"
    " - file:///path/to/my/file\n"
    " - /path/to/my/file",
    example="s3://my-object-store/file1",
  )
  path: str = Field(
    ...,
    description="Path of the file inside the container.\n" "Must be an absolute path.",
    example="/data/file1",
  )
  type: Optional[TesFileType] = "FILE"
  content: Optional[str] = Field(
    None,
    description="File content literal.\n\n"
    "Implementations should support a minimum of 128 KiB in this field\n"
    "and may define their own maximum.\n\n"
    "UTF-8 encoded\n\n"
    'If content is not empty, "url" must be ignored.',
  )
  streamable: Optional[bool] = Field(
    None,
    description="Indicate that a file resource could be accessed using a streaming\n"
    "interface, ie a FUSE mounted s3 object. This flag indicates that\n"
    "using a streaming mount, as opposed to downloading the whole file to\n"
    "the local scratch space, may be faster despite the latency and\n"
    "overhead. This does not mean that the backend will use a streaming\n"
    "interface, as it may not be provided by the vendor, but if the\n"
    "capacity is available it can be used without degrading the\n"
    "performance of the underlying program.",
  )


class TesOutput(BaseModel):
  """Represents an output file for a TES task.

  Attributes:
      name (Optional[str]): Name of the output file.
      description (Optional[str]): Description of the output file.
      url (Optional[str]): URL in long term storage.
      path (str): Path of the file inside the container.
      type (Optional[TesFileType]): Type of the file.
  """

  name: Optional[str] = None
  description: Optional[str] = None
  url: Optional[str] = Field(
    None,
    description='REQUIRED, unless "content" is set.\n\n'
    "URL in long term storage, for example:\n"
    " - s3://my-object-store/file1\n"
    " - gs://my-bucket/file2\n"
    " - file:///path/to/my/file\n"
    " - /path/to/my/file",
    example="s3://my-object-store/file1",
  )
  path: str = Field(
    ...,
    description="Path of the file inside the container.\n" "Must be an absolute path.",
    example="/data/file1",
  )
  type: Optional[TesFileType] = "FILE"


class TesLogs(BaseModel):
  """Represents the logs for a TES task.

  Attributes:
      logs (Optional[List[TesExecutorLog]]): Logs for the task.
  """

  logs: Optional[List[TesExecutorLog]] = Field(
    None,
    description="Executor logs.\n\n"
    "If no logs are available, it should be set to an empty array.",
  )


class TesResources(BaseModel):
  """Represents resource requirements for a TES task.

  Attributes:
      cpu_cores (Optional[int]): Number of CPU cores.
      preemptible (Optional[bool]): Flag for preemptible resources.
      ram_gb (Optional[float]): Amount of RAM in GB.
      disk_gb (Optional[float]): Amount of disk space in GB.
      zones (Optional[List[str]]): Compute zones.
      backend_parameters (Optional[Dict[str, str]]): Additional backend parameters.
  """

  cpu_cores: Optional[int] = Field(
    None,
    description="Number of CPU cores.",
    example=4,
  )
  preemptible: Optional[bool] = Field(
    None,
    description="Flag for preemptible resources.\n"
    "If true, indicates that the work does not need to complete,\n"
    "but it would be nice if it could.",
  )
  ram_gb: Optional[float] = Field(
    None,
    description="Amount of RAM in GB.",
    example=2.0,
  )
  disk_gb: Optional[float] = Field(
    None,
    description="Amount of disk space in GB.",
    example=10.0,
  )
  zones: Optional[List[str]] = Field(
    None,
    description='Compute zones, e.g. Amazon EC2 "us-east-1a", GCE "us-central1".',
    example=["us-east-1a", "us-central1"],
  )
  backend_parameters: Optional[Dict[str, str]] = Field(
    None,
    description="Arbitrary parameters to pass to the backend. Must be\n"
    "JSON-encodable.",
  )


class TesState(Enum):
  """Enum for TES task states."""

  UNKNOWN = "UNKNOWN"
  QUEUED = "QUEUED"
  INITIALIZING = "INITIALIZING"
  RUNNING = "RUNNING"
  PAUSED = "PAUSED"
  COMPLETE = "COMPLETE"
  CANCELED = "CANCELED"
  EXECUTOR_ERROR = "EXECUTOR_ERROR"
  SYSTEM_ERROR = "SYSTEM_ERROR"


class TesTask(BaseModel):
  """Represents a TES task.

  Attributes:
      id (Optional[str]): Task identifier.
      state (Optional[TesState]): State of the task.
      name (Optional[str]): Name of the task.
      description (Optional[str]): Description of the task.
      executors (List[TesExecutor]): Executors for the task.
      inputs (Optional[List[TesInput]]): Input files.
      outputs (Optional[List[TesOutput]]): Output files.
      resources (Optional[TesResources]): Resource requirements.
      creation_time (Optional[str]): Creation time.
      start_time (Optional[str]): Start time.
      end_time (Optional[str]): End time.
      logs (Optional[List[TesLogs]]): Logs for the task.
  """

  id: Optional[str] = Field(
    None,
    description="Task identifier, assigned by the server.",
  )
  state: Optional[TesState] = Field(
    TesState.UNKNOWN,
    description="Task state.",
  )
  name: Optional[str] = Field(
    None,
    description="Optional, must be a non-empty string.",
    example="Example Task",
  )
  description: Optional[str] = Field(
    None,
    description="Optional, must be a non-empty string.",
  )
  executors: List[TesExecutor] = Field(
    ...,
    description="At least one Executor must be present.",
  )
  inputs: Optional[List[TesInput]] = Field(
    None,
    description="Array of input files.",
  )
  outputs: Optional[List[TesOutput]] = Field(
    None,
    description="Array of output files.",
  )
  resources: Optional[TesResources] = Field(
    None,
    description="Resource requirements.",
  )
  creation_time: Optional[str] = Field(
    None,
    description="Time the task was created, in RFC 3339 format.",
    example="2020-10-02T10:00:00-05:00",
  )
  start_time: Optional[str] = Field(
    None,
    description="Time the task was started, in RFC 3339 format.",
    example="2020-10-02T10:05:00-05:00",
  )
  end_time: Optional[str] = Field(
    None,
    description="Time the task ended, in RFC 3339 format.",
    example="2020-10-02T11:00:00-05:00",
  )
  logs: Optional[List[TesLogs]] = Field(
    None,
    description="Task logs.\n\n"
    "If no logs are available, it should be set to an empty array.",
  )


class TesTaskLog(BaseModel):
  """Represents the log for a TES task.

  Attributes:
      logs (Optional[List[TesExecutorLog]]): Executor logs.
  """

  logs: Optional[List[TesExecutorLog]] = Field(
    None,
    description="Executor logs.\n\n"
    "If no logs are available, it should be set to an empty array.",
  )
