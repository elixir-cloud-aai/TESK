"""Tests of the Helm chart (`charts/tesk`), rendered with `helm template`.

They need `helm` on the `PATH` and are skipped without it, unless
`REQUIRE_HELM` is `1`, `true` or `yes` (as in CI's chart job,
`.github/actions/test-chart`), so that a missing `helm` can't skip them
unnoticed there. CI's test job leaves them out, so that they run with the
pinned Helm version only.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from tests.helm import (
    CHART,
    HELM,
    NAMESPACE,
    VALUES,
    container,
    env,
    find,
    get,
    render,
)

if HELM is None:
    if os.environ.get("REQUIRE_HELM", "").lower() in {"1", "true", "yes"}:
        raise RuntimeError("helm is required (REQUIRE_HELM is set) but not found")
    pytest.skip("helm is not installed", allow_module_level=True)


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
    tesk = VALUES["tesk"]
    assert container(manifests)["image"] == tesk["image"]
    assert (
        variables["TESK_API_TASKMASTER_IMAGE_VERSION"]
        == tesk["taskmaster_image_version"]
    )
    assert (
        variables["TESK_API_TASKMASTER_FILER_IMAGE_VERSION"]
        == tesk["taskmaster_filer_image_version"]
    )
    assert variables["SERVER_SERVLET_CONTEXT_PATH"] == "/"
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
    assert find(manifests, "Endpoints", "ftp") is None
    assert find(manifests, "Service", "ftp") is None


def test_port() -> None:
    """The API's port is used by its container, service and ingress."""
    manifests = render("--set", "tesk.port=9000")
    assert container(manifests)["ports"] == [{"containerPort": 9000}]
    service = get(manifests, "Service", "tesk-api")["spec"]
    assert service["ports"] == [{"port": 9000}]
    spec = get(manifests, "Ingress", "ingress-rules")["spec"]
    port = spec["rules"][0]["http"]["paths"][0]["backend"]["service"]["port"]
    assert port == {"number": 9000}


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("--set", "tesk.tes_api_base_path=/tes"), "/tes"),
        (("--set", "tesk.tes_api_base_path="), None),
    ],
)
def test_base_path(args: tuple[str, ...], expected: str | None) -> None:
    """The TES API's base path is passed on, unless it is empty."""
    assert env(render(*args)).get("OPENAPI_TASKEXECUTIONSERVICE_BASE_PATH") == expected


def test_auth_groups() -> None:
    """The groups that authorise users are passed on."""
    manifests = render(
        "--set", "auth.env_subgroup=EBI", "--set", "auth.env_basegroup=BASE"
    )
    variables = env(manifests)
    assert variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"] == "EBI"
    assert variables["TESK_API_AUTHORISATION_BASE_GROUP"] == "BASE"


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


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), "false"),
        (("--set", "tesk.swaggerUi.enabled=true"), "true"),
        (("--set", "tesk.swaggerUi.enabled=false"), "false"),
        (("--set", "tesk.swaggerUi.enabled=null"), None),
        (("--set", "tesk.swaggerUi=null"), None),
    ],
)
def test_swagger_ui(args: tuple[str, ...], expected: str | None) -> None:
    """`tesk.swaggerUi.enabled` is passed on, unless it is null."""
    assert env(render(*args)).get("TESK_API_SWAGGER_UI_ENABLED") == expected


@pytest.mark.parametrize("value", ["yes", "off", "1", "true"])
def test_swagger_ui_invalid(value: str) -> None:
    """`tesk.swaggerUi.enabled` must be a boolean, not a string."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-string", f"tesk.swaggerUi.enabled={value}")
    assert "tesk.swaggerUi.enabled must be true or false" in error.value.stderr


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


def test_ingress_path_and_annotations() -> None:
    """The ingress path is the API's context path; annotations are optional."""
    manifests = render(
        "--set",
        "ingress.path=/tesk",
        "--set-json",
        'ingress.annotations={"a.example.org/b":"c"}',
    )
    ingress = get(manifests, "Ingress", "ingress-rules")
    # Maps are merged with the default annotations
    assert ingress["metadata"]["annotations"]["a.example.org/b"] == "c"
    assert ingress["spec"]["rules"][0]["http"]["paths"][0]["path"] == "/tesk"
    assert env(manifests)["SERVER_SERVLET_CONTEXT_PATH"] == "/tesk"
    manifests = render("--set", "ingress.annotations=null")
    ingress = get(manifests, "Ingress", "ingress-rules")
    assert "annotations" not in ingress["metadata"]


def test_ingress_disabled() -> None:
    """Without ingress rules, there is no ingress, nor a route outside OpenShift."""
    manifests = render("--set", "ingress.rules=false")
    assert find(manifests, "Ingress", "ingress-rules") is None
    assert find(manifests, "Route", "tesk-svc") is None


def test_openshift_route() -> None:
    """On OpenShift, a route replaces the ingress, if its rules are disabled."""
    openshift = ("--api-versions", "route.openshift.io/v1")
    manifests = render(
        *openshift, "--set", "ingress.rules=false", "--set", "host_name=tes.example.org"
    )
    route = get(manifests, "Route", "tesk-svc")
    assert route["spec"]["host"] == "tes.example.org"
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


def test_storage_s3(tmp_path: Path) -> None:
    """S3 storage renders the secret from the files in `s3-config/`."""
    chart = tmp_path / "tesk"
    shutil.copytree(CHART, chart)
    files = {
        "config": "[default]\nregion = eu-north-1\n",
        "credentials": "[default]\naws_access_key_id = test\n",
    }
    for name, content in files.items():
        (chart / "s3-config" / name).write_text(content)
    manifests = render("--set", "storage=s3", chart=chart)
    data = get(manifests, "Secret", "aws-secret")["data"]
    assert {name: base64.b64decode(value).decode() for name, value in data.items()} == (
        files
    )
    assert find(render(chart=chart), "Secret", "aws-secret") is None


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
