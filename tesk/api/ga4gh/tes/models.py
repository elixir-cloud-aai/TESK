"""Models for TES API."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import AnyUrl, BaseModel, Field


class TesCancelTaskResponse(BaseModel):
  """CancelTaskResponse describes a response from the CancelTask endpoint."""

  pass


class TesCreateTaskResponse(BaseModel):
  """CreateTaskResponse describes a response from the CreateTask endpoint.

  It will include the task ID that can be used to look up the status of the job.
  """

  id: str = Field(..., description="Task identifier assigned by the server.")


class TesExecutor(BaseModel):
  """An executor is a command to be run in a container."""

  image: str = Field(
    ...,
    description=(
      "Name of the container image. The string will be passed as the image"
      "\nargument to the containerization run command. Examples:\n   - `ubuntu`\n   - "
      "`quay.io/aptible/ubuntu`\n   - `gcr.io/my-org/my-image`\n   - "
      "`myregistryhost:5000/fedora/httpd:version1.0`"
    ),
    example="ubuntu:20.04",
  )
  command: List[str] = Field(
    ...,
    description="A sequence of program arguments to execute, where the first argument\n"
    'is the program to execute (i.e. argv). Example:\n```\n{\n  "command" : ["/bin/md5"'
    ', "/data/file1"]\n}\n```',
    example=["/bin/md5", "/data/file1"],
  )
  workdir: Optional[str] = Field(
    default=None,
    description=(
      "The working directory that the command will be executed in.\nIf not "
      "defined, the system will default to the directory set by\nthe container image."
    ),
    example="/data/",
  )
  stdin: Optional[str] = Field(
    default=None,
    description=(
      "Path inside the container to a file which will be piped\nto the "
      "executor's stdin. This must be an absolute path. This mechanism"
      "\ncould be used in conjunction with the input declaration to "
      "process\na data file using a tool that expects STDIN.\n\nFor "
      "example, to get the MD5 sum of a file by reading it into the "
      'STDIN\n```\n{\n  "command" : ["/bin/md5"],\n  "stdin" : "/data/file1"'
      "\n}\n```"
    ),
    example="/data/file1",
  )
  stdout: Optional[str] = Field(
    default=None,
    description="Path inside the container to a file where the executor's\nstdout will "
    'be written to. Must be an absolute path. Example:\n```\n{\n  "stdout" : '
    '"/tmp/stdout.log"\n}\n```',
    example="/tmp/stdout.log",
  )
  stderr: Optional[str] = Field(
    default=None,
    description="Path inside the container to a file where the executor's\nstderr "
    'will be written to. Must be an absolute path. Example:\n```\n{\n  "stderr" : '
    '"/tmp/stderr.log"\n}\n```',
    example="/tmp/stderr.log",
  )
  env: Optional[Dict[str, str]] = Field(
    default=None,
    description="Environmental variables to set within the container. Example:\n```\n"
    '{\n  "env" : {\n    "ENV_CONFIG_PATH" : "/data/config.file",\n    "BLASTDB" : '
    '"/data/GRC38",\n    "HMMERDB" : "/data/hmmer"\n  }\n}\n```',
    example={"BLASTDB": "/data/GRC38", "HMMERDB": "/data/hmmer"},
  )
  ignore_error: Optional[bool] = Field(
    default=None,
    description="Default behavior of running an array of executors is that "
    "execution\nstops on the first error. If `ignore_error` is `True`, then "
    "the\nrunner will record error exit codes, but will continue on to the "
    "next\ntesExecutor.",
  )


class TesExecutorLog(BaseModel):
  """ExecutorLog describes logging information related to an Executor."""

  start_time: Optional[str] = Field(
    default=None,
    description="Time the executor started, in RFC 3339 format.",
    example="2020-10-02T10:00:00-05:00",
  )
  end_time: Optional[str] = Field(
    default=None,
    description="Time the executor ended, in RFC 3339 format.",
    example="2020-10-02T11:00:00-05:00",
  )
  stdout: Optional[str] = Field(
    default=None,
    description="Stdout content.\n\nThis is meant for convenience. No guarantees are "
    "made about the content.\nImplementations may chose different approaches: only the "
    "head, only the tail,\na URL reference only, etc.\n\nIn order to capture the full "
    "stdout client should set Executor.stdout\nto a container file path, and use Task."
    "outputs to upload that file\nto permanent storage.",
  )
  stderr: Optional[str] = Field(
    default=None,
    description="Stderr content.\n\nThis is meant for convenience. No guarantees are "
    "made about the content.\nImplementations may chose different approaches: only the "
    "head, only the tail,\na URL reference only, etc.\n\nIn order to capture the full "
    "stderr client should set Executor.stderr\nto a container file path, and use Task."
    "outputs to upload that file\nto permanent storage.",
  )
  exit_code: int = Field(..., description="Exit code.")


class TesFileType(Enum):
  """Define if input/output element is a file or a directory.

  It is not required that the user provide this value, but it is required that
  the server fill in the value once the information is available at run time.
  """

  FILE = "FILE"
  DIRECTORY = "DIRECTORY"


class TesInput(BaseModel):
  """Input describes Task input files."""

  name: Optional[str] = None
  description: Optional[str] = None
  url: Optional[str] = Field(
    default=None,
    description='REQUIRED, unless "content" is set.\n\nURL in long term storage, for '
    "example:\n - s3://my-object-store/file1\n - gs://my-bucket/file2\n - "
    "file:///path/to/my/file\n - /path/to/my/file",
    example="s3://my-object-store/file1",
  )
  path: str = Field(
    ...,
    description="Path of the file inside the container.\nMust be an absolute path.",
    example="/data/file1",
  )
  type: Optional[TesFileType] = TesFileType.FILE
  content: Optional[str] = Field(
    default=None,
    description="File content literal.\n\nImplementations should support a minimum of "
    "128 KiB in this field\nand may define their own maximum.\n\nUTF-8 encoded\n\nIf "
    'content is not empty, "url" must be ignored.',
  )
  streamable: Optional[bool] = Field(
    default=None,
    description="Indicate that a file resource could be accessed using a streaming"
    "\ninterface, ie a FUSE mounted s3 object. This flag indicates that\nusing a "
    "streaming mount, as opposed to downloading the whole file to\nthe local scratch "
    "space, may be faster despite the latency and\noverhead. This does not mean that "
    "the backend will use a streaming\ninterface, as it may not be provided by the "
    "vendor, but if the\ncapacity is available it can be used without degrading "
    "the\nperformance of the underlying program.",
  )


class TesOutput(BaseModel):
  """Output describes Task output files."""

  name: Optional[str] = Field(None, description="User-provided name of output file")
  description: Optional[str] = Field(
    default=None,
    description="Optional users provided description field, can be used for "
    "documentation.",
  )
  url: str = Field(
    ...,
    description="URL at which the TES server makes the output accessible after the "
    "task is complete.\nWhen tesOutput.path contains wildcards, it must be a "
    "directory; see\n`tesOutput.path_prefix` for details on how output URLs are "
    "constructed in this case.\nFor Example:\n - `s3://my-object-store/file1`\n - "
    "`gs://my-bucket/file2`\n - `file:///path/to/my/file`",
  )
  path: str = Field(
    ...,
    description="Absolute path of the file inside the container.\nMay contain pattern "
    "matching wildcards to select multiple outputs at once, but mind\nimplications for "
    "`tesOutput.url` and `tesOutput.path_prefix`.\nOnly wildcards defined in IEEE Std "
    "1003.1-2017 (POSIX), 12.3 are supported; "
    "see\nhttps://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_13",
  )
  path_prefix: Optional[str] = Field(
    default=None,
    description="Prefix to be removed from matching outputs if `tesOutput.path` "
    "contains wildcards;\noutput URLs are constructed by appending pruned paths to the "
    "directory specified\nin `tesOutput.url`.\nRequired if `tesOutput.path` contains "
    "wildcards, ignored otherwise.",
  )
  type: Optional[TesFileType] = TesFileType.FILE


class TesOutputFileLog(BaseModel):
  """OutputFileLog describes a single output file.

  This describes file details after the task has completed successfully, for logging
  purposes.
  """

  url: str = Field(
    ..., description="URL of the file in storage, e.g. s3://bucket/file.txt"
  )
  path: str = Field(
    ...,
    description="Path of the file inside the container. Must be an absolute path.",
  )
  size_bytes: str = Field(
    ...,
    description="Size of the file in bytes. Note, this is currently coded as a "
    "string\nbecause official JSON doesn't support int64 numbers.",
    example=["1024"],
  )


class TesResources(BaseModel):
  """Resources describes the resources requested by a task."""

  cpu_cores: Optional[int] = Field(
    default=None, description="Requested number of CPUs", example=4
  )
  preemptible: Optional[bool] = Field(
    default=None,
    description="Define if the task is allowed to run on preemptible compute instances,"
    "\nfor example, AWS Spot. This option may have no effect when utilized\non some "
    "backends that don't have the concept of preemptible jobs.",
    example=False,
  )
  ram_gb: Optional[float] = Field(
    default=None, description="Requested RAM required in gigabytes (GB)", example=8
  )
  disk_gb: Optional[float] = Field(
    default=None, description="Requested disk size in gigabytes (GB)", example=40
  )
  zones: Optional[List[str]] = Field(
    default=None,
    description="Request that the task be run in these compute zones. How this string\n"
    "is utilized will be dependent on the backend system. For example, a\nsystem based "
    "on a cluster queueing system may use this string to define\npriority queue to "
    "which the job is assigned.",
    example="us-west-1",
  )
  backend_parameters: Optional[Dict[str, str]] = Field(
    default=None,
    description="Key/value pairs for backend configuration.\nServiceInfo shall return "
    "a list of keys that a backend supports.\nKeys are case insensitive.\nIt is "
    "expected that clients pass all runtime or hardware requirement key/values\nthat "
    "are not mapped to existing tesResources properties to backend_parameters.\n"
    "Backends shall log system warnings if a key is passed that is unsupported.\n"
    "Backends shall not store or return unsupported keys if included in a task.\nIf "
    "backend_parameters_strict equals true,\nbackends should fail the task if any "
    "key/values are unsupported, otherwise,\nbackends should attempt to run the "
    "task\nIntended uses include VM size selection, coprocessor configuration, etc."
    '\nExample:\n```\n{\n  "backend_parameters" : {\n    "VmSize" : "Standard_D64_v3"\n'
    "  }\n}\n```",
    example={"VmSize": "Standard_D64_v3"},
  )
  backend_parameters_strict: Optional[bool] = Field(
    False,
    description="If set to true, backends should fail the task if any "
    "backend_parameters\nkey/values are unsupported, otherwise, backends should "
    "attempt to run the task",
    example=False,
  )


class Artifact(Enum):
  """Artifact type."""

  tes = "tes"


class ServiceType(BaseModel):
  """Type of a GA4GH service."""

  group: str = Field(
    ...,
    description="Namespace in reverse domain name format. Use `org.ga4gh` for "
    "implementations compliant with official GA4GH specifications. For services with "
    "custom APIs not standardized by GA4GH, or implementations diverging from official "
    "GA4GH specifications, use a different namespace (e.g. your organization's reverse "
    "domain name).",
    example="org.ga4gh",
  )
  artifact: str = Field(
    ...,
    description="Name of the API or GA4GH specification implemented. Official GA4GH "
    "types should be assigned as part of standards approval process. Custom artifacts "
    "are supported.",
    example="beacon",
  )
  version: str = Field(
    ...,
    description="Version of the API or specification. GA4GH specifications use "
    "semantic versioning.",
    example="1.0.0",
  )


class Organization(BaseModel):
  """Organization responsible for a GA4GH service."""

  name: str = Field(
    ...,
    description="Name of the organization responsible for the service",
    example="My organization",
  )
  url: AnyUrl = Field(
    ...,
    description="URL of the website of the organization (RFC 3986 format)",
    example="https://example.com",
  )


class Service(BaseModel):
  """GA4GH service."""

  id: str = Field(
    ...,
    description="Unique ID of this service. Reverse domain name notation is "
    "recommended, though not required. The identifier should attempt to be globally "
    "unique so it can be used in downstream aggregator services e.g. Service Registry.",
    example="org.ga4gh.myservice",
  )
  name: str = Field(
    ...,
    description="Name of this service. Should be human readable.",
    example="My project",
  )
  type: ServiceType
  description: Optional[str] = Field(
    default=None,
    description="Description of the service. Should be human readable and provide "
    "information about the service.",
    example="This service provides...",
  )
  organization: Organization = Field(
    ..., description="Organization providing the service"
  )
  contactUrl: Optional[AnyUrl] = Field(
    default=None,
    description="URL of the contact for the provider of this service, e.g. a link to a "
    "contact form (RFC 3986 format), or an email (RFC 2368 format).",
    example="mailto:support@example.com",
  )
  documentationUrl: Optional[AnyUrl] = Field(
    default=None,
    description="URL of the documentation of this service (RFC 3986 format). This "
    "should help someone learn how to use your service, including any specifics "
    "required to access data, e.g. authentication.",
    example="https://docs.myservice.example.com",
  )
  createdAt: Optional[datetime] = Field(
    default=None,
    description="Timestamp describing when the service was first deployed and available"
    " (RFC 3339 format)",
    example="2019-06-04T12:58:19Z",
  )
  updatedAt: Optional[datetime] = Field(
    default=None,
    description="Timestamp describing when the service was last updated (RFC 3339"
    " format)",
    example="2019-06-04T12:58:19Z",
  )
  environment: Optional[str] = Field(
    default=None,
    description="Environment the service is running in. Use this to distinguish between"
    " production, development and testing/staging deployments. Suggested values are "
    "prod, test, dev, staging. However this is advised and not enforced.",
    example="test",
  )
  version: str = Field(
    ...,
    description="Version of the service being described. Semantic versioning is "
    "recommended, but other identifiers, such as dates or commit hashes, are also "
    "allowed. The version should be changed whenever the service is updated.",
    example="1.0.0",
  )


class TesState(Enum):
  """Task state."""

  UNKNOWN = "UNKNOWN"
  QUEUED = "QUEUED"
  INITIALIZING = "INITIALIZING"
  RUNNING = "RUNNING"
  PAUSED = "PAUSED"
  COMPLETE = "COMPLETE"
  EXECUTOR_ERROR = "EXECUTOR_ERROR"
  SYSTEM_ERROR = "SYSTEM_ERROR"
  CANCELED = "CANCELED"
  PREEMPTED = "PREEMPTED"
  CANCELING = "CANCELING"


class TesTaskLog(BaseModel):
  """TaskLog describes logging information related to a Task."""

  logs: List[TesExecutorLog] = Field(..., description="Logs for each executor")
  metadata: Optional[Dict[str, str]] = Field(
    default=None,
    description="Arbitrary logging metadata included by the implementation.",
    example={"host": "worker-001", "slurmm_id": 123456},
  )
  start_time: Optional[str] = Field(
    default=None,
    description="When the task started, in RFC 3339 format.",
    example="2020-10-02T10:00:00-05:00",
  )
  end_time: Optional[str] = Field(
    default=None,
    description="When the task ended, in RFC 3339 format.",
    example="2020-10-02T11:00:00-05:00",
  )
  outputs: List[TesOutputFileLog] = Field(
    ...,
    description="Information about all output files. Directory outputs are\nflattened "
    "into separate items.",
  )
  system_logs: Optional[List[str]] = Field(
    default=None,
    description="System logs are any logs the system decides are relevant,\nwhich are "
    "not tied directly to an Executor process.\nContent is implementation specific: "
    "format, size, etc.\n\nSystem logs may be collected here to provide convenient "
    "access.\n\nFor example, the system may include the name of the host\nwhere the "
    "task is executing, an error message that caused\na SYSTEM_ERROR state (e.g. disk "
    "is full), etc.\n\nSystem logs are only included in the FULL task view.",
  )


class TesServiceType(ServiceType):
  """Type of a TES service."""

  artifact: Artifact = Field(..., example="tes")  # type: ignore


class TesServiceInfo(Service):
  """ServiceInfo describes the service that is running the TES API."""

  storage: Optional[List[str]] = Field(
    default=None,
    description="Lists some, but not necessarily all, storage locations supported\nby "
    "the service.",
    example=[
      "file:///path/to/local/funnel-storage",
      "s3://ohsu-compbio-funnel/storage",
    ],
  )
  tesResources_backend_parameters: Optional[List[str]] = Field(
    default=None,
    description="Lists all tesResources.backend_parameters keys supported\nby the "
    "service",
    example=["VmSize"],
  )
  type: Optional[TesServiceType] = None # type: ignore


class TesTask(BaseModel):
  """Task describes a task to be run."""

  id: Optional[str] = Field(
    default=None,
    description="Task identifier assigned by the server.",
    example="job-0012345",
  )
  state: Optional[TesState] = TesState.UNKNOWN
  name: Optional[str] = Field(None, description="User-provided task name.")
  description: Optional[str] = Field(
    default=None,
    description="Optional user-provided description of task for documentation "
    "purposes.",
  )
  inputs: Optional[List[TesInput]] = Field(
    default=None,
    description="Input files that will be used by the task. Inputs will be downloaded"
    "\nand mounted into the executor container as defined by the task "
    "request\ndocument.",
    example=[{"url": "s3://my-object-store/file1", "path": "/data/file1"}],
  )
  outputs: Optional[List[TesOutput]] = Field(
    default=None,
    description="Output files.\nOutputs will be uploaded from the executor container "
    "to long-term storage.",
    example=[
      {
        "path": "/data/outfile",
        "url": "s3://my-object-store/outfile-1",
        "type": "FILE",
      }
    ],
  )
  resources: Optional[TesResources] = None
  executors: List[TesExecutor] = Field(
    ...,
    description="An array of executors to be run. Each of the executors will run "
    "one\nat a time sequentially. Each executor is a different command that\nwill be "
    "run, and each can utilize a different docker image. But each of\nthe executors "
    "will see the same mapped inputs and volumes that are declared\nin the parent "
    "CreateTask message.\n\nExecution stops on the first error.",
  )
  volumes: Optional[List[str]] = Field(
    default=None,
    description="Volumes are directories which may be used to share data between\n"
    "Executors. Volumes are initialized as empty directories by the\nsystem when the "
    "task starts and are mounted at the same path\nin each Executor.\n\nFor example, "
    "given a volume defined at `/vol/A`,\nexecutor 1 may write a file to "
    "`/vol/A/exec1.out.txt`, then\nexecutor 2 may read from that file.\n\n(Essentially,"
    "this translates to a `docker run -v` flag where\nthe container path is the same "
    "for each executor).",
    example=["/vol/A/"],
  )
  tags: Optional[Dict[str, str]] = Field(
    default=None,
    description="A key-value map of arbitrary tags. These can be used to store "
    '"meta-data\nand annotations about a task. Example:\n```\n{\n  "tags" : {\n      '
    '"WORKFLOW_ID" : "cwl-01234",\n      "PROJECT_GROUP" : "alice-lab"\n  }\n}\n```',
    example={"WORKFLOW_ID": "cwl-01234", "PROJECT_GROUP": "alice-lab"},
  )
  logs: Optional[List[TesTaskLog]] = Field(
    default=None,
    description="Task logging information.\nNormally, this will contain only one entry,"
    " but in the case where\na task fails and is retried, an entry will be appended to "
    "this list.",
  )
  creation_time: Optional[str] = Field(
    default=None,
    description="Date + time the task was created, in RFC 3339 format.\nThis is set by"
    " the system, not the client.",
    example="2020-10-02T10:00:00-05:00",
  )


class TesListTasksResponse(BaseModel):
  """ListTasksResponse describes a response from the ListTasks endpoint."""

  tasks: List[TesTask] = Field(
    ...,
    description="List of tasks. These tasks will be based on the original "
    "submitted\ntask document, but with other fields, such as the job state "
    "and\nlogging info, added/changed as the job progresses.",
  )
  next_page_token: Optional[str] = Field(
    default=None,
    description="Token used to return the next page of results. This value can be "
    "used\nin the `page_token` field of the next ListTasks request.",
  )
