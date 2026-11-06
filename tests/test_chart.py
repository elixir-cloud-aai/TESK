"""Tests of the Helm chart (`charts/tesk`), rendered with `helm template`.

They need `helm` on the `PATH` and are skipped without it, unless
`REQUIRE_HELM` is set (as in CI's chart job, `.github/actions/test-chart`),
so that a missing `helm` can't skip them unnoticed there.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest
import yaml

CHART = Path(__file__).parents[1] / "charts" / "tesk"
HELM = shutil.which("helm")
NAMESPACE = "tesk"

if HELM is None:
    if os.environ.get("REQUIRE_HELM"):
        raise RuntimeError("helm is required (REQUIRE_HELM is set) but not found")
    pytest.skip("helm is not installed", allow_module_level=True)

# A rendered Kubernetes object
Manifest = dict[str, Any]


def render(*args: str) -> list[Manifest]:
    """Render the chart with `helm template` arguments.

    Args:
        args: Further arguments of `helm template`, e.g., `--set` options.

    Returns:
        The rendered objects.
    """
    assert HELM is not None
    output = subprocess.run(  # noqa: S603 (fixed executable and arguments)
        [HELM, "template", "tesk", str(CHART), "--namespace", NAMESPACE, *args],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [doc for doc in yaml.safe_load_all(output) if doc]


def find(manifests: list[Manifest], kind: str, name: str) -> Manifest | None:
    """Find a rendered object by kind and name.

    Args:
        manifests: The rendered objects.
        kind: Kind of the object.
        name: Name of the object.

    Returns:
        The object, or `None` if it isn't rendered.
    """
    for manifest in manifests:
        if manifest["kind"] == kind and manifest["metadata"]["name"].strip() == name:
            return manifest
    return None


def get(manifests: list[Manifest], kind: str, name: str) -> Manifest:
    """Get a rendered object by kind and name.

    Args:
        manifests: The rendered objects.
        kind: Kind of the object.
        name: Name of the object.

    Returns:
        The object.
    """
    manifest = find(manifests, kind, name)
    assert manifest is not None, f"{kind} {name} is not rendered"
    return manifest


def container(manifests: list[Manifest]) -> dict[str, Any]:
    """Get the API container of the Deployment.

    Args:
        manifests: The rendered objects.

    Returns:
        The container.
    """
    pod = get(manifests, "Deployment", "tesk-api")["spec"]["template"]["spec"]
    containers: list[dict[str, Any]] = pod["containers"]
    assert [c["name"] for c in containers] == ["tesk-api"]
    return containers[0]


def env(manifests: list[Manifest]) -> dict[str, Any]:
    """Get the environment of the API container.

    Args:
        manifests: The rendered objects.

    Returns:
        Values (or `valueFrom` sources) of the environment variables by name.
    """
    return {
        var["name"]: var.get("value", var.get("valueFrom"))
        for var in container(manifests)["env"]
    }


def test_defaults() -> None:
    """The default values render the API, its RBAC, service and ingress."""
    manifests = render()
    kinds = sorted((m["kind"], m["metadata"]["name"].strip()) for m in manifests)
    assert kinds == [
        ("ConfigMap", "service-info-config"),
        ("Deployment", "tesk-api"),
        ("Ingress", "ingress-rules"),
        ("Role", "taskmaster"),
        ("RoleBinding", "taskmaster-role-binding"),
        ("Secret", "ftp-secret"),
        ("Service", "tesk-api"),
        ("ServiceAccount", "taskmaster"),
    ]
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_IMAGE_VERSION"] == "v0.10.6"
    assert variables["TESK_API_TASKMASTER_FILER_IMAGE_VERSION"] == "v0.10.6"
    assert variables["TESK_API_K8S_NAMESPACE"] == NAMESPACE
    assert variables["SPRING_PROFILES_ACTIVE"] == "noauth"
    assert variables["TESK_API_SERVICE_INFO_PUBLIC"] == "true"
    assert variables["TESK_API_TASKMASTER_FTP_SECRET_NAME"] == "ftp-secret"  # noqa: S105 (a name)
    assert variables["OPENAPI_TASKEXECUTIONSERVICE_BASE_PATH"] == "/ga4gh/tes/v1"
    for name in (
        "TESK_API_TASKMASTER_ENVIRONMENT_NETRC_SECRET_NAME",
        "TESK_API_TASKMASTER_ENVIRONMENT_TRANSFER_PVC_NAME",
        "TESK_API_TASKMASTER_ENVIRONMENT_STORAGE_CLASS_NAME",
    ):
        assert name not in variables
    service = get(manifests, "Service", "tesk-api")["spec"]
    assert service["type"] == "ClusterIP"
    assert service["ports"] == [{"port": 8080}]


def test_resources() -> None:
    """The API container's resources come from the values."""
    manifests = render(
        "--set",
        "tesk.limitsCpu=2",
        "--set",
        "tesk.limitsMemory=4Gi",
        "--set",
        "tesk.requestsCpu=500m",
        "--set",
        "tesk.requestsMemory=1Gi",
    )
    assert container(manifests)["resources"] == {
        "limits": {"cpu": 2, "memory": "4Gi"},
        "requests": {"cpu": "500m", "memory": "1Gi"},
    }


def test_images() -> None:
    """The images of the API, taskmaster and filer come from the values."""
    manifests = render(
        "--set",
        "tesk.image=example.org/api:1",
        "--set",
        "tesk.taskmaster_image_name=example.org/taskmaster",
        "--set",
        "tesk.taskmaster_image_version=v1",
        "--set",
        "tesk.taskmaster_filer_image_name=example.org/filer",
        "--set",
        "tesk.taskmaster_filer_image_version=v2",
    )
    assert container(manifests)["image"] == "example.org/api:1"
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_IMAGE_NAME"] == "example.org/taskmaster"
    assert variables["TESK_API_TASKMASTER_IMAGE_VERSION"] == "v1"
    assert variables["TESK_API_TASKMASTER_FILER_IMAGE_NAME"] == "example.org/filer"
    assert variables["TESK_API_TASKMASTER_FILER_IMAGE_VERSION"] == "v2"


def test_security_context() -> None:
    """The API runs as non-root without privileges, unless disabled."""
    manifests = render()
    pod = get(manifests, "Deployment", "tesk-api")["spec"]["template"]["spec"]
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert container(manifests)["securityContext"] == {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
    }
    manifests = render("--set", "tesk.securityContext.enabled=false")
    pod = get(manifests, "Deployment", "tesk-api")["spec"]["template"]["spec"]
    assert "securityContext" not in pod
    assert "securityContext" not in container(manifests)


def test_auth() -> None:
    """With authentication, the OAuth client secret is rendered."""
    manifests = render(
        "--set",
        "auth.mode=auth",
        "--set",
        "auth.client_id=client",
        "--set",
        "auth.client_secret=secret",
    )
    assert env(manifests)["SPRING_PROFILES_ACTIVE"] == "auth"
    secret = get(manifests, "Secret", "oauth-client-secret")
    assert secret["stringData"] == {"id": "client", "secret": "secret"}
    assert find(render(), "Secret", "oauth-client-secret") is None


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), "true"),
        (("--set", "auth.service_info_public=false"), "false"),
        (("--set", "auth.service_info_public=null"), None),
    ],
)
def test_service_info_public(args: tuple[str, ...], expected: str | None) -> None:
    """`auth.service_info_public` is passed on, unless it is null."""
    assert env(render(*args)).get("TESK_API_SERVICE_INFO_PUBLIC") == expected


def test_service_info() -> None:
    """The service info is mounted from the chart's `service-info/`."""
    manifests = render()
    config = get(manifests, "ConfigMap", "service-info-config")
    assert "service-info.yaml" in config["data"]
    assert container(manifests)["volumeMounts"] == [
        {"name": "service-info-config", "mountPath": "/etc/tesk/service-info"}
    ]


def test_ingress() -> None:
    """The ingress routes the host to the API, with TLS if a secret is set."""
    manifests = render(
        "--set",
        "host_name=tes.example.org",
        "--set",
        "ingress.ingressClassName=nginx",
    )
    spec = get(manifests, "Ingress", "ingress-rules")["spec"]
    assert spec["ingressClassName"] == "nginx"
    assert "tls" not in spec
    assert spec["rules"][0]["host"] == "tes.example.org"
    backend = spec["rules"][0]["http"]["paths"][0]["backend"]["service"]
    assert backend == {"name": "tesk-api", "port": {"number": 8080}}
    manifests = render(
        "--set",
        "host_name=tes.example.org",
        "--set",
        "ingress.tls_secret_name=tls",
    )
    spec = get(manifests, "Ingress", "ingress-rules")["spec"]
    assert spec["tls"] == [{"hosts": ["tes.example.org"], "secretName": "tls"}]


def test_ingress_disabled() -> None:
    """Without ingress rules, there is no ingress, nor a route outside OpenShift."""
    manifests = render("--set", "ingress.rules=false")
    assert find(manifests, "Ingress", "ingress-rules") is None
    assert find(manifests, "Route", "tesk-svc") is None


def test_openshift_route() -> None:
    """On OpenShift, a route replaces the ingress, if its rules are disabled."""
    openshift = ("--api-versions", "route.openshift.io/v1")
    manifests = render(*openshift, "--set", "ingress.rules=false")
    route = get(manifests, "Route", "tesk-svc")
    assert route["spec"]["to"]["name"] == "tesk-api"
    assert route["spec"]["tls"]["termination"] == "edge"
    assert find(render(*openshift), "Route", "tesk-svc") is None


def test_node_port() -> None:
    """A NodePort service gets its port from the values."""
    manifests = render(
        "--set", "service.type=NodePort", "--set", "service.node_port=31567"
    )
    service = get(manifests, "Service", "tesk-api")["spec"]
    assert service["type"] == "NodePort"
    assert service["ports"] == [{"port": 8080, "nodePort": 31567}]


def test_storage_s3() -> None:
    """S3 storage renders the secret with the AWS configuration."""
    manifests = render("--set", "storage=s3")
    assert set(get(manifests, "Secret", "aws-secret")["data"]) == {
        "config",
        "credentials",
    }
    assert find(render(), "Secret", "aws-secret") is None


def test_storage_openstack() -> None:
    """OpenStack storage renders a default Cinder storage class."""
    manifests = render("--set", "storage=openstack")
    storage_class = get(manifests, "StorageClass", "gold")
    assert storage_class["provisioner"] == "kubernetes.io/cinder"


def test_storage_class() -> None:
    """A storage class for the tasks' volumes is passed on."""
    manifests = render("--set", "storageClass=fast")
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_STORAGE_CLASS_NAME"] == "fast"


def test_ftp() -> None:
    """FTP credentials, a netrc secret and a host FTP server are optional."""
    manifests = render(
        "--set",
        "ftp.classic_ftp_secret=",
        "--set",
        "ftp.netrc_secret=netrc",
        "--set",
        "ftp.hostip=10.0.0.1",
    )
    assert find(manifests, "Secret", "ftp-secret") is None
    assert ".netrc" in get(manifests, "Secret", "netrc")["stringData"]
    variables = env(manifests)
    assert "TESK_API_TASKMASTER_FTP_SECRET_NAME" not in variables
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_NETRC_SECRET_NAME"] == "netrc"  # noqa: S105
    endpoints = get(manifests, "Endpoints", "ftp")
    assert endpoints["subsets"][0]["addresses"] == [{"ip": "10.0.0.1"}]
    assert get(manifests, "Service", "ftp")["spec"]["ports"][0]["port"] == 21


def test_ftp_secret() -> None:
    """The FTP secret holds the credentials from the values."""
    manifests = render("--set", "ftp.username=user", "--set", "ftp.password=pass")
    secret = get(manifests, "Secret", "ftp-secret")
    assert secret["stringData"] == {"username": "user", "password": "pass"}


def test_transfer() -> None:
    """A shared file system for transfers is passed on."""
    manifests = render(
        "--set",
        "transfer.active=true",
        "--set",
        "transfer.pvc_name=shared",
    )
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_TRANSFER_PVC_NAME"] == "shared"
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_HOST_BASE_PATH"] == "/tmp"  # noqa: S108
    assert (
        variables["TESK_API_TASKMASTER_ENVIRONMENT_CONTAINER_BASE_PATH"] == "/transfer"
    )


def test_retries_and_debug() -> None:
    """Retries and debugging are passed on as strings."""
    manifests = render(
        "--set",
        "tesk.executor_retries=5",
        "--set",
        "tesk.filer_retries=3",
        "--set",
        "tesk.debug=true",
    )
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT"] == "5"
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_FILER_BACKOFF_LIMIT"] == "3"
    assert variables["TESK_API_TASKMASTER_DEBUG"] == "true"
