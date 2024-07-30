"""Custom configuration model for the FOCA app."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models import Service
from tesk.constants import TeskConstants


class FtpConfig(BaseModel):
    """Ftp configuration model for the TESK."""

    secretName: Optional[str] = Field(
        default=None, description="Name of the secret with FTP account credentials"
    )
    enabled: bool = Field(
        default=False,
        description="If FTP account enabled (based on non-emptiness of secretName)",
    )


class TaskmasterEnvProperties(BaseModel):
    """Taskmaster environment properties model for the TESK."""

    imageName: str = Field(
        default=TeskConstants.taskmaster_image_name,
        description="Taskmaster image name",
    )
    imageVersion: str = Field(
        default=TeskConstants.taskmaster_image_version,
        description="Taskmaster image version",
    )
    filerImageName: str = Field(
        default=TeskConstants.filer_image_name, description="Filer image name"
    )
    filerImageVersion: str = Field(
        default=TeskConstants.filer_image_version, description="Filer image version"
    )
    ftp: FtpConfig = Field(default=None, description="Test FTP account settings")
    debug: bool = Field(
        default=False,
        description="If verbose (debug) mode of taskmaster is on (passes additional "
        "flag to taskmaster and sets image pull policy to Always)",
    )
    environment: Dict[str, str] = Field(
        default={"key": "value"},
        description="Environment variables, that will be passed to taskmaster",
    )
    serviceAccountName: str = Field(
        default="default", description="Service Account name for taskmaster"
    )


class SecretKeyRef(BaseModel):
    """Reference to a secret key."""

    name: str
    key: str
    optional: Optional[bool] = Field(False, description="If the reference is optional")


class EnvVarSource(BaseModel):
    """Source for an environment variable."""

    secretKeyRef: Optional[SecretKeyRef] = None


class EnvVar(BaseModel):
    """Environment variable."""

    name: str
    valueFrom: Optional[EnvVarSource] = None


class VolumeMount(BaseModel):
    """Volume mount configuration."""

    name: str
    mountPath: str
    readOnly: bool


class DownwardAPIItem(BaseModel):
    """Downward API item configuration."""

    path: str
    fieldRef: Dict[str, str]


class Volume(BaseModel):
    """Volume configuration."""

    name: str
    downwardAPI: Optional[Dict[str, List[DownwardAPIItem]]] = None


class Container(BaseModel):
    """Container configuration."""

    name: str
    image: str
    args: List[str]
    env: List[EnvVar]
    volumeMounts: List[VolumeMount]


class PodSpec(BaseModel):
    """Pod specification."""

    serviceAccountName: str
    containers: List[Container]
    volumes: List[Volume]
    restartPolicy: str


class PodMetadata(BaseModel):
    """Pod metadata."""

    name: str


class PodTemplate(BaseModel):
    """Pod template configuration."""

    metadata: PodMetadata
    spec: PodSpec


class JobSpec(BaseModel):
    """Job specification."""

    template: PodTemplate


class JobMetadata(BaseModel):
    """Job metadata."""

    name: str
    labels: Dict[str, str]


class Job(BaseModel):
    """Kubernetes Job configuration."""

    apiVersion: str
    kind: str
    metadata: JobMetadata
    spec: JobSpec


class CustomConfig(BaseModel):
    """Custom configuration model for the FOCA app."""

    # Define custom configuration fields here
    service_info: Service
    taskmaster_template: Job  # This is Pydantic model for V1Job
    taskmaster_env_properties: TaskmasterEnvProperties
