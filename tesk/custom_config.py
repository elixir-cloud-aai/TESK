"""Custom configuration model for the FOCA app."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models import Service
from tesk.api.kubernetes.convert.taskmaster_env_properties import (
    TaskmasterEnvProperties,
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
