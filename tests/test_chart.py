"""Tests of the Helm chart (`charts/tesk`), rendered with `helm template`.

They need `helm` on the `PATH` and are skipped without it, unless
`REQUIRE_HELM` is `1`, `true` or `yes` (as in CI's chart job,
`.github/actions/test-chart`), so that a missing `helm` can't skip them
unnoticed there. CI's test job leaves them out, so that they run with the
pinned Helm version only.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest
import yaml

from tests.helm import (
    CHART,
    HELM,
    LEGACY_CHART,
    LEGACY_VALUES,
    METADATA,
    NAMESPACE,
    VALUES,
    Manifest,
    container,
    copy_chart,
    env,
    find,
    get,
    notes,
    render,
    without_labels,
    without_probes,
)

# The deprecated keys (as `--set` options with values other than the
# defaults; the last option sets the key) and the same settings with their
# new keys
RENAMED: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("--set", "host_name=a.example.org"), ("--set", "hostName=a.example.org")),
    (
        ("--set", "tesk.image=example.org/api:2"),
        (
            "--set",
            "tesk.image.repository=example.org/api",
            "--set",
            "tesk.image.tag=2",
        ),
    ),
    (("--set", "tesk.tes_api_base_path=/tes"), ("--set", "tesk.tesApiBasePath=/tes")),
    (("--set", "tesk.tes_api_base_path="), ("--set", "tesk.tesApiBasePath=")),
    (
        ("--set", "tesk.taskmaster_image_name=example.org/taskmaster"),
        ("--set", "tesk.taskmaster.image.repository=example.org/taskmaster"),
    ),
    (
        ("--set", "tesk.taskmaster_image_version=v1"),
        ("--set", "tesk.taskmaster.image.tag=v1"),
    ),
    (
        ("--set", "tesk.taskmaster_filer_image_name=example.org/filer"),
        ("--set", "tesk.filer.image.repository=example.org/filer"),
    ),
    (
        ("--set", "tesk.taskmaster_filer_image_version=v2"),
        ("--set", "tesk.filer.image.tag=v2"),
    ),
    (("--set", "tesk.executor_retries=5"), ("--set", "tesk.executorRetries=5")),
    (("--set", "tesk.filer_retries=3"), ("--set", "tesk.filerRetries=3")),
    (("--set", "tesk.limitsCpu=2"), ("--set", "tesk.resources.limits.cpu=2")),
    (
        ("--set", "tesk.limitsMemory=4Gi"),
        ("--set", "tesk.resources.limits.memory=4Gi"),
    ),
    (
        ("--set", "tesk.requestsCpu=500m"),
        ("--set", "tesk.resources.requests.cpu=500m"),
    ),
    (
        ("--set", "tesk.requestsMemory=1Gi"),
        ("--set", "tesk.resources.requests.memory=1Gi"),
    ),
    (
        ("--set", "transfer.active=true", "--set", "transfer.wes_base_path=/data"),
        ("--set", "transfer.active=true", "--set", "transfer.wesBasePath=/data"),
    ),
    (
        ("--set", "transfer.active=true", "--set", "transfer.tes_base_path=/t"),
        ("--set", "transfer.active=true", "--set", "transfer.tesBasePath=/t"),
    ),
    (
        ("--set", "transfer.active=true", "--set", "transfer.pvc_name=shared"),
        ("--set", "transfer.active=true", "--set", "transfer.pvcName=shared"),
    ),
    (("--set", "auth.env_subgroup=EBI"), ("--set", "auth.envSubgroup=EBI")),
    (("--set", "auth.env_basegroup=BASE"), ("--set", "auth.envBasegroup=BASE")),
    (
        ("--set", "auth.service_info_public=false"),
        ("--set", "auth.serviceInfoPublic=false"),
    ),
    (
        ("--set", "auth.service_info_public=null"),
        ("--set", "auth.serviceInfoPublic=null"),
    ),
    (
        ("--set", "auth.mode=auth", "--set", "auth.client_id=client"),
        ("--set", "auth.mode=auth", "--set", "auth.clientId=client"),
    ),
    (
        ("--set", "auth.mode=auth", "--set", "auth.client_secret=secret"),
        ("--set", "auth.mode=auth", "--set", "auth.clientSecret=secret"),
    ),
    (
        ("--set", "service.type=NodePort", "--set", "service.node_port=31567"),
        ("--set", "service.type=NodePort", "--set", "service.nodePort=31567"),
    ),
    (("--set", "ftp.classic_ftp_secret="), ("--set", "ftp.classicFtpSecret=")),
    (
        ("--set", "ftp.classic_ftp_secret=null"),
        ("--set", "ftp.classicFtpSecret=null"),
    ),
    (
        ("--set", "ftp.classic_ftp_secret=other"),
        ("--set", "ftp.classicFtpSecret=other"),
    ),
    (("--set", "ftp.netrc_secret=netrc"), ("--set", "ftp.netrcSecret=netrc")),
    (
        ("--set", "ingress.tls_secret_name=tls"),
        ("--set", "ingress.tlsSecretName=tls"),
    ),
]

# The deprecated keys (as in `NOTES.txt`) and their new keys
DEPRECATED: dict[str, str] = {
    "host_name": "hostName",
    "tesk.image (a string)": "tesk.image.repository and tesk.image.tag",
    "tesk.tes_api_base_path": "tesk.tesApiBasePath",
    "tesk.taskmaster_image_name": "tesk.taskmaster.image.repository",
    "tesk.taskmaster_image_version": "tesk.taskmaster.image.tag",
    "tesk.taskmaster_filer_image_name": "tesk.filer.image.repository",
    "tesk.taskmaster_filer_image_version": "tesk.filer.image.tag",
    "tesk.executor_retries": "tesk.executorRetries",
    "tesk.filer_retries": "tesk.filerRetries",
    "tesk.limitsCpu": "tesk.resources.limits.cpu",
    "tesk.limitsMemory": "tesk.resources.limits.memory",
    "tesk.requestsCpu": "tesk.resources.requests.cpu",
    "tesk.requestsMemory": "tesk.resources.requests.memory",
    "transfer.wes_base_path": "transfer.wesBasePath",
    "transfer.tes_base_path": "transfer.tesBasePath",
    "transfer.pvc_name": "transfer.pvcName",
    "auth.env_subgroup": "auth.envSubgroup",
    "auth.env_basegroup": "auth.envBasegroup",
    "auth.service_info_public": "auth.serviceInfoPublic",
    "auth.client_id": "auth.clientId",
    "auth.client_secret": "auth.clientSecret",
    "service.node_port": "service.nodePort",
    "ftp.classic_ftp_secret": "ftp.classicFtpSecret",
    "ftp.netrc_secret": "ftp.netrcSecret",
    "ingress.tls_secret_name": "ingress.tlsSecretName",
}

STANDARD_LABELS = {
    "app.kubernetes.io/name": "tesk",
    "app.kubernetes.io/instance": "tesk",
    "app.kubernetes.io/version": str(METADATA["appVersion"]),
    "app.kubernetes.io/managed-by": "Helm",
    "helm.sh/chart": f"tesk-{METADATA['version']}",
}

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
    # The tag of the API's image defaults to the chart's `appVersion`
    assert tesk["image"]["tag"] == ""
    assert container(manifests)["image"] == (
        f"{tesk['image']['repository']}:{METADATA['appVersion']}"
    )
    assert "imagePullPolicy" not in container(manifests)
    assert (
        variables["TESK_API_TASKMASTER_IMAGE_NAME"]
        == tesk["taskmaster"]["image"]["repository"]
    )
    assert (
        variables["TESK_API_TASKMASTER_IMAGE_VERSION"]
        == tesk["taskmaster"]["image"]["tag"]
    )
    assert (
        variables["TESK_API_TASKMASTER_FILER_IMAGE_NAME"]
        == tesk["filer"]["image"]["repository"]
    )
    assert (
        variables["TESK_API_TASKMASTER_FILER_IMAGE_VERSION"]
        == tesk["filer"]["image"]["tag"]
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
        (("--set", "tesk.tesApiBasePath=/tes"), "/tes"),
        (("--set", "tesk.tesApiBasePath="), None),
    ],
)
def test_base_path(args: tuple[str, ...], expected: str | None) -> None:
    """The TES API's base path is passed on, unless it is empty."""
    assert env(render(*args)).get("OPENAPI_TASKEXECUTIONSERVICE_BASE_PATH") == expected


def test_auth_groups() -> None:
    """The groups that authorise users are passed on."""
    manifests = render(
        "--set", "auth.envSubgroup=EBI", "--set", "auth.envBasegroup=BASE"
    )
    variables = env(manifests)
    assert variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"] == "EBI"
    assert variables["TESK_API_AUTHORISATION_BASE_GROUP"] == "BASE"


def test_resources() -> None:
    """The API container's resources come from the values."""
    manifests = render(
        "--set",
        "tesk.resources.limits.cpu=2",
        "--set",
        "tesk.resources.limits.memory=4Gi",
        "--set",
        "tesk.resources.requests.cpu=500m",
        "--set",
        "tesk.resources.requests.memory=1Gi",
    )
    assert container(manifests)["resources"] == {
        "limits": {"cpu": 2, "memory": "4Gi"},
        "requests": {"cpu": "500m", "memory": "1Gi"},
    }


def test_resources_block() -> None:
    """The `resources` block is passed on as is, e.g., with further resources."""
    resources = {
        "limits": {"memory": "4Gi", "ephemeral-storage": "1Gi"},
        "requests": {"cpu": "250m"},
    }
    manifests = render("--set-json", f"tesk.resources={json.dumps(resources)}")
    # Maps are merged with the default resources
    assert container(manifests)["resources"] == {
        "limits": {"cpu": 1, "memory": "4Gi", "ephemeral-storage": "1Gi"},
        "requests": {"cpu": "250m", "memory": "2048Mi"},
    }


def test_resources_old_keys() -> None:
    """The old keys of the resources take precedence over the block."""
    manifests = render(
        "--set",
        "tesk.limitsCpu=3",
        "--set",
        "tesk.requestsMemory=1Gi",
        "--set",
        "tesk.resources.limits.cpu=2",
        "--set-string",
        "tesk.resources.limits.ephemeral-storage=1Gi",
    )
    assert container(manifests)["resources"] == {
        "limits": {"cpu": 3, "memory": "2048Mi", "ephemeral-storage": "1Gi"},
        "requests": {"cpu": 1, "memory": "1Gi"},
    }


def test_image_block() -> None:
    """The API's image is built from repository and tag, with a pull policy."""
    manifests = render(
        "--set",
        "tesk.image.repository=example.org/api",
        "--set",
        "tesk.image.tag=2.0.0",
        "--set",
        "tesk.image.pullPolicy=Always",
    )
    assert container(manifests)["image"] == "example.org/api:2.0.0"
    assert container(manifests)["imagePullPolicy"] == "Always"


def test_image_tag_zero() -> None:
    """A tag that is falsy but set (0) is used, not the chart's `appVersion`."""
    manifests = render("--set", "tesk.image.tag=0")
    assert container(manifests)["image"].endswith(":0")


def test_images() -> None:
    """The images of the API, taskmaster and filer come from the values."""
    manifests = render(
        # The old form of `tesk.image`, with the tag
        "--set",
        "tesk.image=example.org/api:1",
        "--set",
        "tesk.taskmaster.image.repository=example.org/taskmaster",
        "--set",
        "tesk.taskmaster.image.tag=v1",
        "--set",
        "tesk.filer.image.repository=example.org/filer",
        "--set",
        "tesk.filer.image.tag=v2",
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


PROBES = ("startupProbe", "readinessProbe", "livenessProbe")
SERVICE_INFO = "/ga4gh/tes/v1/service-info"


def test_probes_defaults() -> None:
    """The API container has probes that wait for the API to answer."""
    api = container(render())
    http_get = {"path": SERVICE_INFO, "port": 8080}
    for name in PROBES:
        assert api[name]["httpGet"] == http_get
    # The slow start (about a minute) is covered by the startup probe, which
    # holds off the others
    timing = {"timeoutSeconds": 5}
    assert {k: v for k, v in api["startupProbe"].items() if k != "httpGet"} == {
        **timing,
        "periodSeconds": 5,
        "failureThreshold": 60,
    }
    assert {k: v for k, v in api["readinessProbe"].items() if k != "httpGet"} == {
        **timing,
        "periodSeconds": 10,
        "failureThreshold": 3,
    }
    assert {k: v for k, v in api["livenessProbe"].items() if k != "httpGet"} == {
        **timing,
        "periodSeconds": 20,
        "failureThreshold": 3,
    }


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("--set", "tesk.readinessProbe=null"), {"httpGet": {"path": SERVICE_INFO}}),
        (
            ("--set-string", "tesk.readinessProbe.enabled=false"),
            None,
        ),
        (
            ("--set", "tesk.readinessProbe.httpGet.port=9000"),
            {"httpGet": {"path": SERVICE_INFO, "port": 9000}},
        ),
        (
            (
                "--set",
                "auth.mode=auth",
                "--set",
                "auth.serviceInfoPublic=false",
                "--set",
                "tesk.readinessProbe.tcpSocket.host=h",
            ),
            {"tcpSocket": {"port": 8080, "host": "h"}},
        ),
    ],
)
def test_probes_edge_cases(
    args: tuple[str, ...], expected: dict[str, Any] | None
) -> None:
    """Null probes, string flags and partial actions are handled."""
    probe = container(render(*args)).get("readinessProbe")
    if expected is None:
        assert probe is None
    else:
        assert probe is not None
        for key, value in expected.items():
            assert value.items() <= probe[key].items()


def test_probes_pod_unchanged() -> None:
    """The probes change neither the selector nor the names."""
    manifests = render()
    deployment = get(manifests, "Deployment", "tesk-api")
    assert deployment["spec"]["selector"] == {"matchLabels": {"app": "tesk-api"}}
    assert deployment["spec"]["template"]["metadata"]["labels"]["app"] == "tesk-api"
    assert container(manifests)["name"] == "tesk-api"


@pytest.mark.parametrize(
    ("args", "path"),
    [
        (("--set", "ingress.path=/tesk"), "/tesk" + SERVICE_INFO),
        (("--set", "ingress.path=/tesk/"), "/tesk" + SERVICE_INFO),
        (("--set", "tesk.tesApiBasePath=/tes"), "/tes/service-info"),
        (("--set", "tesk.tesApiBasePath=/tes/"), "/tes/service-info"),
        (("--set", "tesk.tesApiBasePath="), SERVICE_INFO),
        (
            ("--set", "ingress.path=/tesk", "--set", "tesk.tesApiBasePath=/tes"),
            "/tesk/tes/service-info",
        ),
    ],
)
def test_probes_path(args: tuple[str, ...], path: str) -> None:
    """The probes follow the context path and the base path of the API."""
    api = container(render(*args))
    for name in PROBES:
        assert api[name]["httpGet"]["path"] == path


def test_probes_port() -> None:
    """The probes use the API's port."""
    api = container(render("--set", "tesk.port=9000"))
    for name in PROBES:
        assert api[name]["httpGet"]["port"] == 9000


@pytest.mark.parametrize(
    ("args", "http"),
    [
        ((), True),
        (("--set", "auth.mode=auth"), True),
        (("--set", "auth.mode=auth", "--set", "auth.serviceInfoPublic=null"), True),
        (("--set", "auth.mode=noauth", "--set", "auth.serviceInfoPublic=false"), True),
        (("--set", "auth.mode=auth", "--set", "auth.serviceInfoPublic=false"), False),
        (
            ("--set", "auth.mode=auth", "--set-string", "auth.serviceInfoPublic=false"),
            False,
        ),
    ],
)
def test_probes_auth(args: tuple[str, ...], http: bool) -> None:
    """The probes check the port if the service info needs a token."""
    api = container(render(*args))
    for name in PROBES:
        if http:
            assert "httpGet" in api[name]
            assert "tcpSocket" not in api[name]
        else:
            assert api[name]["tcpSocket"] == {"port": 8080}
            assert "httpGet" not in api[name]


def test_probes_values() -> None:
    """Values of a probe are merged with its defaults."""
    default = container(render())
    api = container(
        render(
            "--set",
            "tesk.readinessProbe.periodSeconds=3",
            "--set",
            "tesk.livenessProbe.initialDelaySeconds=30",
            "--set",
            "tesk.startupProbe.failureThreshold=7",
        )
    )
    assert api["readinessProbe"]["periodSeconds"] == 3
    assert (
        api["readinessProbe"]["timeoutSeconds"]
        == (default["readinessProbe"]["timeoutSeconds"])
    )
    assert api["livenessProbe"]["initialDelaySeconds"] == 30
    assert api["startupProbe"]["failureThreshold"] == 7
    assert (
        api["startupProbe"]["periodSeconds"]
        == (default["startupProbe"]["periodSeconds"])
    )
    assert api["readinessProbe"]["httpGet"] == default["readinessProbe"]["httpGet"]


def test_probes_action() -> None:
    """A probe's own action replaces the default one."""
    api = container(
        render(
            "--set-json",
            'tesk.livenessProbe.exec={"command": ["true"]}',
            "--set",
            "tesk.readinessProbe.tcpSocket.port=8080",
        )
    )
    assert api["livenessProbe"]["exec"] == {"command": ["true"]}
    assert "httpGet" not in api["livenessProbe"]
    assert api["readinessProbe"]["tcpSocket"] == {"port": 8080}
    assert "httpGet" not in api["readinessProbe"]
    assert api["startupProbe"]["httpGet"]["path"] == SERVICE_INFO


@pytest.mark.parametrize("name", PROBES)
def test_probes_disabled(name: str) -> None:
    """Each probe can be disabled."""
    api = container(render("--set", f"tesk.{name}.enabled=false"))
    assert name not in api
    assert {other for other in PROBES if other in api} == set(PROBES) - {name}


def test_probes_reuse_values(tmp_path: Path) -> None:
    """With the earlier defaults (`--reuse-values`), the probes are set too."""
    chart = copy_chart(tmp_path, LEGACY_VALUES)
    api = container(render(chart=chart))
    default = container(render())
    for name in PROBES:
        assert api[name] == default[name]


@pytest.mark.parametrize("name", PROBES)
def test_probes_schema_invalid(name: str) -> None:
    """The schema rejects probes of the wrong type."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"tesk.{name}=[]")
    assert "values don't meet the specifications of the schema" in error.value.stderr


def test_auth() -> None:
    """With authentication, the OAuth client secret is rendered."""
    manifests = render(
        "--set",
        "auth.mode=auth",
        "--set",
        "auth.clientId=client",
        "--set",
        "auth.clientSecret=secret",
    )
    assert env(manifests)["SPRING_PROFILES_ACTIVE"] == "auth"
    secret = get(manifests, "Secret", "oauth-client-secret")
    assert secret["stringData"] == {"id": "client", "secret": "secret"}
    assert find(render(), "Secret", "oauth-client-secret") is None


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), "true"),
        (("--set", "auth.serviceInfoPublic=false"), "false"),
        (("--set", "auth.serviceInfoPublic=null"), None),
    ],
)
def test_service_info_public(args: tuple[str, ...], expected: str | None) -> None:
    """`auth.serviceInfoPublic` is passed on, unless it is null."""
    assert env(render(*args)).get("TESK_API_SERVICE_INFO_PUBLIC") == expected


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), "false"),
        (("--set", "tesk.swaggerUi.enabled=true"), "true"),
        (("--set", "tesk.swaggerUi.enabled=false"), "false"),
        (("--set", "tesk.swaggerUi.enabled=null"), None),
        (("--set", "tesk.swaggerUi=null"), None),
        (("--set-string", "tesk.swaggerUi.enabled=TRUE"), "true"),
        (("--set-string", "tesk.swaggerUi.enabled=False"), "false"),
    ],
)
def test_swagger_ui(args: tuple[str, ...], expected: str | None) -> None:
    """`tesk.swaggerUi.enabled` is passed on, unless it is null."""
    assert env(render(*args)).get("TESK_API_SWAGGER_UI_ENABLED") == expected


@pytest.mark.parametrize(
    "args",
    [
        ("--set-string", "tesk.swaggerUi.enabled=yes"),
        ("--set-string", "tesk.swaggerUi.enabled=off"),
        ("--set-string", "tesk.swaggerUi.enabled="),
        ("--set", "tesk.swaggerUi.enabled=1"),
        ("--set-json", "tesk.swaggerUi.enabled=[true]"),
        ("--set-json", "tesk.swaggerUi=true"),
        ("--set-json", "tesk.swaggerUi=false"),
    ],
)
def test_swagger_ui_invalid(args: tuple[str, ...]) -> None:
    """Anything but true or false (or null) fails, as it would stop tesk-api."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
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
        "hostName=tes.example.org",
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
        "hostName=tes.example.org",
        "--set",
        "ingress.tlsSecretName=tls",
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
        *openshift, "--set", "ingress.rules=false", "--set", "hostName=tes.example.org"
    )
    route = get(manifests, "Route", "tesk-svc")
    assert route["spec"]["host"] == "tes.example.org"
    assert route["spec"]["to"]["name"] == "tesk-api"
    assert route["spec"]["tls"]["termination"] == "edge"
    assert find(render(*openshift), "Route", "tesk-svc") is None


def test_node_port() -> None:
    """A NodePort service gets its port from the values."""
    manifests = render(
        "--set", "service.type=NodePort", "--set", "service.nodePort=31567"
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
        "ftp.classicFtpSecret=",
        "--set",
        "ftp.netrcSecret=netrc",
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


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), None),
        (("--set-json", "ftp.hosts=[]"), None),
        (("--set", "ftp.hosts=null"), None),
        (("--set", "ftp.hosts={ftp.example.org}"), "ftp.example.org"),
        (
            ("--set", "ftp.hosts={ftp.example.org,data.example.org:2121}"),
            "ftp.example.org,data.example.org:2121",
        ),
        (("--set-json", 'ftp.hosts=["[2001:db8::1]:21"]'), "[2001:db8::1]:21"),
    ],
)
def test_ftp_hosts(args: tuple[str, ...], expected: str | None) -> None:
    """`ftp.hosts` reaches the taskmaster as `TESK_FTP_HOSTS`, if not empty.

    Args:
        args: The `helm template` arguments.
        expected: The value of the variable, or `None` if it is not set.
    """
    variables = env(render(*args))
    assert variables.get("TESK_API_TASKMASTER_ENVIRONMENT_TESK_FTP_HOSTS") == expected


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "ftp.hosts=ftp.example.org"),
        ("--set-json", "ftp.hosts=[1]"),
        ("--set-json", 'ftp.hosts=["a,b"]'),
        ("--set-json", 'ftp.hosts=[""]'),
        ("--set-json", 'ftp.hosts=["ftp://ftp.example.org"]'),
        ("--set-json", 'ftp.hosts=["user@ftp.example.org"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org/"]'),
        ("--set-json", 'ftp.hosts=[" ftp.example.org"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org:"]'),
    ],
)
def test_ftp_hosts_invalid(args: tuple[str, ...]) -> None:
    """`ftp.hosts` entries are hosts, with a port or not, and nothing else.

    Args:
        args: The `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError):
        render(*args)


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), True),
        (("--set", "ftp.hosts={ftp.example.org}"), False),
        (("--set", "ftp.classicFtpSecret="), False),
        (("--set", "ftp.netrcSecret=netrc"), False),
    ],
)
def test_notes_ftp_hosts(tmp_path: Path, args: tuple[str, ...], warned: bool) -> None:
    """The notes warn about FTP credentials without `ftp.hosts`.

    Only if the credentials are used: with `ftp.classicFtpSecret` and
    without `.netrc`.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: Further `helm template` arguments.
        warned: Whether the notes warn.
    """
    credentials = ("--set", "ftp.username=user", "--set", "ftp.password=s3cr3t")
    text = notes(*credentials, *args, tmp_path=tmp_path)
    assert f"release tesk in namespace {NAMESPACE}" in text
    assert ("ftp.hosts is empty" in text) is warned
    assert "s3cr3t" not in text


def test_ftp_secret() -> None:
    """The FTP secret holds the credentials from the values."""
    manifests = render("--set", "ftp.username=user", "--set", "ftp.password=pass")
    secret = get(manifests, "Secret", "ftp-secret")
    assert secret["stringData"] == {"username": "user", "password": "pass"}


TRICKY_VALUES = [
    "pa#ss",
    "a: b",
    "123456",
    "-",
    "true",
    "null",
    "0123",
    '"quoted" \\ back',
    "{braces}",
    "x #y: z",
]


@pytest.mark.parametrize("value", TRICKY_VALUES)
def test_ftp_secret_quoting(value: str, tmp_path: Path) -> None:
    """The FTP credentials are strings, whatever they contain."""
    values = tmp_path / "secrets.yaml"
    values.write_text(yaml.safe_dump({"ftp": {"username": value, "password": value}}))
    manifests = render("-f", str(values))
    secret = get(manifests, "Secret", "ftp-secret")
    assert secret["stringData"] == {"username": value, "password": value}


def test_ftp_secret_numeric() -> None:
    """Numbers set with `--set` are rendered as strings."""
    manifests = render("--set", "ftp.username=123", "--set", "ftp.password=456")
    secret = get(manifests, "Secret", "ftp-secret")
    assert secret["stringData"] == {"username": "123", "password": "456"}


@pytest.mark.parametrize("value", TRICKY_VALUES)
@pytest.mark.parametrize(
    ("id_key", "secret_key"),
    [("clientId", "clientSecret"), ("client_id", "client_secret")],
)
def test_auth_quoting(value: str, id_key: str, secret_key: str, tmp_path: Path) -> None:
    """The OAuth client ID and secret are strings (new and old keys)."""
    values = tmp_path / "secrets.yaml"
    values.write_text(
        yaml.safe_dump(
            {
                "auth": {
                    "mode": "auth",
                    id_key: value,
                    secret_key: value,
                }
            }
        )
    )
    manifests = render("-f", str(values))
    secret = get(manifests, "Secret", "oauth-client-secret")
    assert secret["stringData"] == {"id": value, "secret": value}


def test_auth_numeric() -> None:
    """Numbers set with `--set` are strings (new and old key mixed)."""
    manifests = render(
        "--set",
        "auth.mode=auth",
        "--set",
        "auth.clientId=123",
        "--set",
        "auth.client_secret=456",
    )
    secret = get(manifests, "Secret", "oauth-client-secret")
    assert secret["stringData"] == {"id": "123", "secret": "456"}


@pytest.mark.parametrize(
    ("number", "expected"),
    [(123456789012, "123456789012"), (1000000, "1000000"), (1.5, "1.5")],
)
def test_secret_numbers_values_file(
    number: float, expected: str, tmp_path: Path
) -> None:
    """Numbers in a values file are rendered as written, not as floats."""
    values = tmp_path / "secrets.yaml"
    values.write_text(
        yaml.safe_dump(
            {
                "ftp": {"username": number, "password": number},
                "auth": {"mode": "auth", "clientId": number, "clientSecret": number},
            }
        )
    )
    manifests = render("-f", str(values))
    expected_data = {"username": expected, "password": expected}
    assert get(manifests, "Secret", "ftp-secret")["stringData"] == expected_data
    assert get(manifests, "Secret", "oauth-client-secret")["stringData"] == {
        "id": expected,
        "secret": expected,
    }


def test_secret_unset() -> None:
    """Unset credentials render as before (null), not as empty strings."""
    manifests = render("--set", "auth.mode=auth")
    assert get(manifests, "Secret", "ftp-secret")["stringData"] == {
        "username": None,
        "password": None,
    }
    assert get(manifests, "Secret", "oauth-client-secret")["stringData"] == {
        "id": None,
        "secret": None,
    }


def test_secret_number_too_large(tmp_path: Path) -> None:
    """A number that a float can't hold exactly fails with a hint."""
    values = tmp_path / "secrets.yaml"
    values.write_text("ftp:\n  username: 12345678901234567890\n")
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("-f", str(values))
    assert "too large" in error.value.stderr
    assert "--set-string" in error.value.stderr
    assert "12345678901234567890" not in error.value.stderr
    assert "1.2345678901234567e+19" not in error.value.stderr


def test_transfer() -> None:
    """A shared file system for transfers is passed on."""
    manifests = render(
        "--set",
        "transfer.active=true",
        "--set",
        "transfer.pvcName=shared",
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
        "tesk.executorRetries=5",
        "--set",
        "tesk.filerRetries=3",
        "--set",
        "tesk.debug=true",
    )
    variables = env(manifests)
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_EXECUTOR_BACKOFF_LIMIT"] == "5"
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_FILER_BACKOFF_LIMIT"] == "3"
    assert variables["TESK_API_TASKMASTER_DEBUG"] == "true"


def _sorted(manifests: list[Manifest]) -> list[Manifest]:
    """Sort rendered objects by kind and name, to compare renderings.

    Args:
        manifests: The rendered objects.

    Returns:
        The objects, sorted.
    """
    return sorted(manifests, key=lambda m: (m["kind"], m["metadata"]["name"]))


# Values that render the same objects with the earlier chart (see
# `LEGACY_CHART`), apart from the standard labels: the deprecated keys, also
# with empty, null or string values, and values that the schema must accept
LEGACY_CASES: list[tuple[str, ...]] = [
    (),
    ("--values", str(LEGACY_VALUES)),
    *(old for old, _ in RENAMED),
    ("--set", "tesk.limitsCpu="),
    ("--set-json", 'tesk={"limitsCpu": "", "requestsMemory": null}'),
    ("--set", "tesk.limitsCpu=0.5"),
    ("--set-string", "tesk.limitsCpu=1"),
    ("--set", "tesk.limitsMemory=2147483648"),
    ("--set", "tesk.executor_retries=1000000"),
    ("--set", "tesk.port=9000"),
    ("--set", "tesk.debug=1"),
    ("--set", "storageClass=5"),
    ("--set", "ingress.annotations="),
    ("--set", "service.type=NodePort"),
    ("--set", "transfer.active=true"),
    ("--set", "storage=openstack"),
    ("--set", "ftp.hostip=10.0.0.1"),
    ("--set", "auth.mode=auth", "--set", "auth.client_id=c"),
    (
        "--api-versions",
        "route.openshift.io/v1",
        "--set",
        "ingress.rules=false",
        "--set",
        "host_name=tes.example.org",
    ),
]


@pytest.mark.parametrize("args", LEGACY_CASES)
def test_legacy_chart(args: tuple[str, ...]) -> None:
    """Values of the earlier chart render its objects, apart from labels."""
    assert _sorted(without_probes(without_labels(render(*args)))) == _sorted(
        render(*args, chart=LEGACY_CHART)
    )


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("--set", "host_name=tes.example.org"),
        ("--set", "tesk.limitsCpu="),
        # Null removes the old default, so the new key (missing) is read
        ("--set", "tesk.taskmaster_image_version=null"),
    ],
)
def test_reuse_values(args: tuple[str, ...], tmp_path: Path) -> None:
    """With the earlier defaults, the chart renders the earlier objects.

    `helm upgrade --reuse-values` replaces the chart's default values with
    those of the installed chart, so the templates get the old keys only.
    """
    chart = copy_chart(tmp_path, LEGACY_VALUES)
    assert _sorted(
        without_probes(without_labels(render(*args, chart=chart)))
    ) == _sorted(render(*args, chart=LEGACY_CHART))


def test_reuse_values_null_resource(tmp_path: Path) -> None:
    """With the earlier defaults, a null resource drops it, as before.

    The earlier chart rendered `cpu: null`; the chart leaves it out, which
    Kubernetes reads the same way.
    """
    chart = copy_chart(tmp_path, LEGACY_VALUES)
    resources = container(render("--set", "tesk.limitsCpu=null", chart=chart))[
        "resources"
    ]
    assert resources == {
        "limits": {"memory": "2048Mi"},
        "requests": {"cpu": 1, "memory": "2048Mi"},
    }


@pytest.mark.parametrize(
    ("args", "image", "pull_policy"),
    [
        (("--set", "tesk.image.tag=1.2.0"), "tesk-api:1.2.0", None),
        (
            ("--set", "tesk.image.pullPolicy=Always"),
            f"tesk-api:{METADATA['appVersion']}",
            "Always",
        ),
    ],
)
def test_reuse_values_image(
    args: tuple[str, ...], image: str, pull_policy: str | None, tmp_path: Path
) -> None:
    """With the earlier defaults, the new image block works on its own.

    The earlier default of `tesk.image` is a string, which a map set with
    `--reuse-values` replaces, so the repository comes from the template.
    """
    chart = copy_chart(tmp_path, LEGACY_VALUES)
    api = container(render(*args, chart=chart))
    repository = VALUES["tesk"]["image"]["repository"].rsplit("/", 1)[0]
    assert api["image"] == f"{repository}/{image}"
    assert api.get("imagePullPolicy") == pull_policy


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("--set-json", "tesk.resources=null"), {}),
        (
            ("--set-json", "tesk.resources.limits=null"),
            {"requests": {"cpu": 1, "memory": "2048Mi"}},
        ),
    ],
)
def test_resources_null(args: tuple[str, ...], expected: dict[str, Any]) -> None:
    """Null resources (or limits) render without them."""
    assert container(render(*args))["resources"] == expected


@pytest.mark.parametrize(
    ("args", "variable"),
    [
        (("--set-json", "tesk.taskmaster=null"), "TESK_API_TASKMASTER_IMAGE_NAME"),
        (
            ("--set-json", "tesk.filer.image=null"),
            "TESK_API_TASKMASTER_FILER_IMAGE_NAME",
        ),
    ],
)
def test_images_null(args: tuple[str, ...], variable: str) -> None:
    """A null taskmaster or filer image renders an empty image name."""
    assert env(render(*args))[variable] is None


def test_resources_old_keys_invalid() -> None:
    """An old resource value that isn't valid YAML fails, as before."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", "tesk.limitsMemory=a: b")
    assert "tesk.limitsMemory" in error.value.stderr


def test_renamed_lists() -> None:
    """`RENAMED` and `DEPRECATED` cover the same deprecated keys."""
    keys = {old[-1].split("=")[0] for old, _ in RENAMED}
    keys = {"tesk.image (a string)" if k == "tesk.image" else k for k in keys}
    assert keys == set(DEPRECATED)


@pytest.mark.parametrize(("old", "new"), RENAMED)
def test_renamed(old: tuple[str, ...], new: tuple[str, ...]) -> None:
    """A deprecated key has the same effect as its new key."""
    manifests = render(*old)
    assert manifests == render(*new)
    assert manifests != render(*old[:-2])


@pytest.mark.parametrize(("old", "new"), RENAMED)
def test_renamed_precedence(old: tuple[str, ...], new: tuple[str, ...]) -> None:
    """A deprecated key takes precedence over its new key, even if empty."""
    # The new key (the last option) with another value
    other = (*new[:-1], f"{new[-1]}x")
    assert render(*other, *old) == render(*old)


def test_labels() -> None:
    """All objects have the standard labels; the selectors are unchanged."""
    manifests = render(
        "--set",
        "ftp.hostip=10.0.0.1",
        "--set",
        "storage=openstack",
        "--set",
        "auth.mode=auth",
    )
    for manifest in manifests:
        labels = manifest["metadata"]["labels"]
        assert labels.items() >= STANDARD_LABELS.items(), manifest["kind"]
    deployment = get(manifests, "Deployment", "tesk-api")["spec"]
    assert deployment["selector"] == {"matchLabels": {"app": "tesk-api"}}
    pod_labels = deployment["template"]["metadata"]["labels"]
    assert pod_labels == {
        "app": "tesk-api",
        "app.kubernetes.io/name": "tesk",
        "app.kubernetes.io/instance": "tesk",
    }
    service = get(manifests, "Service", "tesk-api")
    assert service["spec"]["selector"] == {"app": "tesk-api"}
    assert service["metadata"]["labels"]["app"] == "tesk-api"


def test_labels_numeric_release() -> None:
    """A release name that looks like a number is a string label."""
    for manifest in render(release="123"):
        assert manifest["metadata"]["labels"]["app.kubernetes.io/instance"] == "123"


def test_labels_openshift() -> None:
    """The OpenShift route has the standard labels too."""
    manifests = render(
        "--api-versions", "route.openshift.io/v1", "--set", "ingress.rules=false"
    )
    labels = get(manifests, "Route", "tesk-svc")["metadata"]["labels"]
    assert labels.items() >= STANDARD_LABELS.items()


def test_notes_template() -> None:
    """`NOTES.txt` only includes the template that `notes` renders."""
    text = (CHART / "templates" / "NOTES.txt").read_text()
    assert text.strip() == '{{- include "tesk.notes" . -}}'


def test_notes(tmp_path: Path) -> None:
    """The notes name the release, without warnings for the defaults."""
    text = notes(tmp_path=tmp_path)
    assert f"release tesk in namespace {NAMESPACE}" in text
    assert "deprecated" not in text


def test_notes_deprecated(tmp_path: Path) -> None:
    """The notes list the deprecated keys in use, with their new keys."""
    text = notes("--values", str(LEGACY_VALUES), tmp_path=tmp_path)
    assert "WARNING" in text
    listed = dict(
        line.removeprefix("  - ").split(": use ")
        for line in text.splitlines()
        if line.startswith("  - ")
    )
    # All but those that the earlier defaults left unset
    unset = {"auth.client_id", "auth.client_secret"}
    assert listed == {k: v for k, v in DEPRECATED.items() if k not in unset}
    text = notes(
        "--set", "auth.client_id=a", "--set", "auth.client_secret=b", tmp_path=tmp_path
    )
    assert "  - auth.client_id: use auth.clientId" in text
    assert "  - auth.client_secret: use auth.clientSecret" in text
    assert "host_name" not in text


def test_chart_metadata() -> None:
    """`Chart.yaml` has the metadata that Helm recommends."""
    assert "EXILIR" not in METADATA["description"]
    assert METADATA["home"] == "https://tesk.readthedocs.io/"
    assert METADATA["sources"]
    assert METADATA["maintainers"]
    assert METADATA["keywords"]
    assert METADATA["icon"].startswith("https://")
    assert METADATA["appVersion"] != "dev"


@pytest.mark.parametrize(
    "args",
    [
        ("--set-json", "tesk=[]"),
        ("--set-json", "tesk.resources=[]"),
        ("--set-json", "tesk.image=[]"),
        ("--set-json", "tesk.port=[]"),
        ("--set-json", "hostName={}"),
        ("--set-json", "auth.serviceInfoPublic=[]"),
        ("--set", "tesk.image.pullPolicy=Sometimes"),
    ],
)
def test_schema_invalid(args: tuple[str, ...]) -> None:
    """The schema rejects values of the wrong type."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "values don't meet the specifications of the schema" in error.value.stderr


@pytest.mark.parametrize(
    "values",
    [
        {"tesk": {"port": "8080", "debug": "true", "executorRetries": "2"}},
        {"service": {"nodePort": "31567", "type": "NodePort"}},
        {"tesk": {"image": {"tag": 1.2}}},
        {"auth": {"serviceInfoPublic": "false"}},
        {"extra": {"anything": True}, "tesk": {"extra": 1}},
    ],
)
def test_schema_permissive(values: dict[str, Any], tmp_path: Path) -> None:
    """The schema accepts strings for scalars, and unknown keys."""
    path = tmp_path / "values.yaml"
    path.write_text(json.dumps(values))
    assert render("--values", str(path))


def test_notes_reuse_values(tmp_path: Path) -> None:
    """The notes explain warnings for the earlier defaults (`--reuse-values`)."""
    text = notes(tmp_path=tmp_path, values=LEGACY_VALUES)
    assert "  - host_name: use hostName" in text
    assert "--reuse-values" in text
