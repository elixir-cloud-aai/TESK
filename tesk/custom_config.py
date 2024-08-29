"""Custom configuration model for the FOCA app."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models import Service
from tesk.api.kubernetes.convert.taskmaster_env_properties import (
    TaskmasterEnvProperties,
)


class PydanticK8sSecretKeyRef(BaseModel):
    """Reference to a secret key."""

    name: str
    key: str
    optional: Optional[bool] = Field(False, description="If the reference is optional")


class PydanticK8sEnvVarSource(BaseModel):
    """Source for an environment variable."""

    secretKeyRef: Optional[PydanticK8sSecretKeyRef] = None


class PydanticK8sEnvVar(BaseModel):
    """Environment variable."""

    name: str
    valueFrom: Optional[PydanticK8sEnvVarSource] = None


class PydanticK8sVolumeMount(BaseModel):
    """Volume mount configuration."""

    name: str
    mountPath: str
    readOnly: bool


class PydanticK8sDownwardAPIItem(BaseModel):
    """Downward API item configuration."""

    path: str
    fieldRef: Dict[str, str]


class PydanticK8sVolume(BaseModel):
    """Volume configuration."""

    name: str
    downwardAPI: Optional[Dict[str, List[PydanticK8sDownwardAPIItem]]] = None


class PydanticK8sContainer(BaseModel):
    """Container configuration."""

    name: str
    image: str
    args: List[str]
    env: List[PydanticK8sEnvVar]
    volumeMounts: List[PydanticK8sVolumeMount]


class PydanticK8sPodSpec(BaseModel):
    """Pod specification."""

    serviceAccountName: str
    containers: List[PydanticK8sContainer]
    volumes: List[PydanticK8sVolume]
    restartPolicy: str


class PydanticK8sPodMetadata(BaseModel):
    """Pod metadata."""

    name: str


class PydanticK8sPodTemplate(BaseModel):
    """Pod template configuration."""

    metadata: PydanticK8sPodMetadata
    spec: PydanticK8sPodSpec


class PydanticK8sJobSpec(BaseModel):
    """Job specification."""

    template: PydanticK8sPodTemplate


class PydanticK8sJobMetadata(BaseModel):
    """Job metadata."""

    name: str
    labels: Dict[str, str]


class PydanticK8sJob(BaseModel):
    """Kubernetes Job configuration."""

    apiVersion: str
    kind: str
    metadata: PydanticK8sJobMetadata
    spec: PydanticK8sJobSpec


class CustomConfig(BaseModel):
    """Custom configuration model for the FOCA app."""

    # Define custom configuration fields here
    service_info: Service
    taskmaster_template: PydanticK8sJob  # This is Pydantic model for V1Job
    taskmaster_env_properties: TaskmasterEnvProperties
