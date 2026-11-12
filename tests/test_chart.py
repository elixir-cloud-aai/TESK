"""Tests of the Helm chart (`charts/tesk`), rendered with `helm template`.

They need `helm` on the `PATH` and are skipped without it, unless
`REQUIRE_HELM` is `1`, `true` or `yes` (as in CI's chart job,
`.github/actions/test-chart`), so that a missing `helm` can't skip them
unnoticed there. CI's test job leaves them out, so that they run with the
pinned Helm version only.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import pytest
import yaml

from tests.helm import (
    CHART,
    HELM,
    METADATA,
    NAMESPACE,
    VALUES,
    Manifest,
    container,
    copy_chart,
    deployment,
    env,
    find,
    get,
    notes,
    render,
)

# The keys that earlier versions of the chart had, as `--set` options, and
# what the chart's error names as their replacement
REMOVED: list[tuple[tuple[str, ...], str]] = [
    (("--set", "host_name=a.example.org"), "host_name: use hostName"),
    (
        ("--set", "tesk.image=example.org/api:2"),
        "tesk.image (a string): use tesk.image.repository and tesk.image.tag",
    ),
    (
        ("--set", "tesk.tes_api_base_path=/tes"),
        "tesk.tes_api_base_path: use tesk.tesApiBasePath",
    ),
    (
        ("--set", "tesk.taskmaster_image_name=t"),
        "tesk.taskmaster_image_name: use tesk.taskmaster.image.repository",
    ),
    (
        ("--set", "tesk.taskmaster_image_version=v1"),
        "tesk.taskmaster_image_version: use tesk.taskmaster.image.tag",
    ),
    (
        ("--set", "tesk.taskmaster_filer_image_name=f"),
        "tesk.taskmaster_filer_image_name: use tesk.filer.image.repository",
    ),
    (
        ("--set", "tesk.taskmaster_filer_image_version=v2"),
        "tesk.taskmaster_filer_image_version: use tesk.filer.image.tag",
    ),
    (
        ("--set", "tesk.executor_retries=5"),
        "tesk.executor_retries: use tesk.executorRetries",
    ),
    (("--set", "tesk.filer_retries=3"), "tesk.filer_retries: use tesk.filerRetries"),
    (("--set", "tesk.limitsCpu=2"), "tesk.limitsCpu: use tesk.resources.limits.cpu"),
    (
        ("--set", "tesk.limitsMemory=4Gi"),
        "tesk.limitsMemory: use tesk.resources.limits.memory",
    ),
    (
        ("--set", "tesk.requestsCpu=1"),
        "tesk.requestsCpu: use tesk.resources.requests.cpu",
    ),
    (
        ("--set", "tesk.requestsMemory=1Gi"),
        "tesk.requestsMemory: use tesk.resources.requests.memory",
    ),
    (
        ("--set", "transfer.wes_base_path=/data"),
        "transfer.wes_base_path: use transfer.wesBasePath",
    ),
    (
        ("--set", "transfer.tes_base_path=/t"),
        "transfer.tes_base_path: use transfer.tesBasePath",
    ),
    (
        ("--set", "transfer.pvc_name=shared"),
        "transfer.pvc_name: use transfer.pvcName",
    ),
    (("--set", "auth.env_subgroup=EBI"), "auth.env_subgroup: use auth.envSubgroup"),
    (
        ("--set", "auth.env_basegroup=BASE"),
        "auth.env_basegroup: use auth.envBaseGroup",
    ),
    (
        ("--set", "auth.service_info_public=false"),
        "auth.service_info_public: use auth.serviceInfoPublic",
    ),
    (("--set", "auth.client_id=client"), "auth.client_id: use auth.clientId"),
    (
        ("--set", "auth.client_secret=s3cr3t"),
        "auth.client_secret: use nothing (auth.clientSecret",
    ),
    (("--set", "service.node_port=31567"), "service.node_port: use service.nodePort"),
    (
        ("--set", "ftp.classic_ftp_secret=other"),
        "ftp.classic_ftp_secret: use ftp.classicFtpSecret",
    ),
    (("--set", "ftp.netrc_secret=netrc"), "ftp.netrc_secret: use ftp.netrcSecret"),
    (
        ("--set", "ingress.tls_secret_name=tls"),
        "ingress.tls_secret_name: use ingress.tlsSecretName",
    ),
    (
        ("--set", "tesk.securityContext.enabled=false"),
        "tesk.securityContext.enabled: use tesk.podSecurityContext and"
        " tesk.securityContext",
    ),
    (("--set", "transfer.active=true"), "transfer.active: use transfer.enabled"),
    (
        ("--set", "auth.envBasegroup=BASE"),
        "auth.envBasegroup: use auth.envBaseGroup",
    ),
    (("--set", "ftp.hostip=10.0.0.1"), "ftp.hostip: use ftp.hostIp"),
    (("--set", "ingress.rules=false"), "ingress.rules: use ingress.enabled"),
    (
        ("--set", "ingress.ingressClassName=nginx"),
        "ingress.ingressClassName: use ingress.className",
    ),
]

# Removed keys set to null or empty fail too
REMOVED_EMPTY: list[tuple[tuple[str, ...], str]] = [
    (("--set", "tesk.limitsCpu=null"), "tesk.limitsCpu: use"),
    (("--set", "host_name="), "host_name: use hostName"),
]

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
        ("ConfigMap", "tesk-service-info"),
        ("Deployment", "tesk-api"),
        ("Ingress", "tesk"),
        ("Role", "tesk-taskmaster"),
        ("RoleBinding", "tesk-taskmaster"),
        ("Secret", "tesk-ftp"),
        ("Service", "tesk-api"),
        ("ServiceAccount", "tesk-taskmaster"),
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
    assert variables["TESK_API_TASKMASTER_FTP_SECRET_NAME"] == "tesk-ftp"  # noqa: S105 (a name)
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
    spec = get(manifests, "Ingress", "tesk")["spec"]
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
        "--set", "auth.envSubgroup=EBI", "--set", "auth.envBaseGroup=BASE"
    )
    variables = env(manifests)
    assert variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"] == "EBI"
    assert variables["TESK_API_AUTHORISATION_BASE_GROUP"] == "BASE"


# The settings of the OIDC provider and the group model, by value under
# `auth`, and the variable of tesk-api that each sets
PROVIDER = {
    "userInfoUri": "SECURITY_OAUTH2_RESOURCE_USER_INFO_URI",
    "groups.claim": "TESK_API_AUTHORISATION_GROUPS_CLAIM",
    "groups.prefix": "TESK_API_AUTHORISATION_GROUP_PREFIX",
    "groups.suffix": "TESK_API_AUTHORISATION_GROUP_SUFFIX",
    "groups.parentGroup": "TESK_API_AUTHORISATION_PARENT_GROUP",
    "groups.adminSubgroup": "TESK_API_AUTHORISATION_ADMIN_SUBGROUP",
    "swaggerOauth.authorizationEndpoint": (
        "TESK_API_SWAGGER_OAUTH_AUTHORIZATION_ENDPOINT"
    ),
    "swaggerOauth.tokenEndpoint": "TESK_API_SWAGGER_OAUTH_TOKEN_ENDPOINT",
    "swaggerOauth.scopes": "TESK_API_SWAGGER_OAUTH_SCOPES",
}
# Valid values of each
PROVIDER_VALUES = {
    "userInfoUri": "https://login.example.org/oidc/userinfo",
    "groups.claim": "entitlements",
    "groups.prefix": "urn:geant:example.org:group:",
    "groups.suffix": "#aai.example.org",
    "groups.parentGroup": "vo:tesk",
    "groups.adminSubgroup": "MANAGERS",
    "swaggerOauth.authorizationEndpoint": "https://login.example.org/oidc/authorize",
    "swaggerOauth.tokenEndpoint": "https://login.example.org/oidc/token",
    "swaggerOauth.scopes": "openid:Standard openid,entitlements:Groups",
}


def test_auth_provider_defaults() -> None:
    """By default, the chart leaves tesk-api's provider and group settings.

    tesk-api's defaults (of ELIXIR AAI) apply then, also for the scopes of
    the Swagger UI, which follow the groups claim.
    """
    assert PROVIDER.keys() == PROVIDER_VALUES.keys()
    for mode in ("noauth", "auth"):
        variables = env(render("--set", f"auth.mode={mode}"))
        for variable in PROVIDER.values():
            assert variable not in variables
        assert "TESK_API_SWAGGER-OAUTH_SCOPES" not in variables
        assert "TESK_API_AUTHORISATION_DELIMITER" not in variables
        assert (
            variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"]
            == VALUES["auth"]["envSubgroup"]
        )
        assert (
            variables["TESK_API_AUTHORISATION_BASE_GROUP"]
            == VALUES["auth"]["envBaseGroup"]
        )
    for key in PROVIDER:
        *maps, name = key.split(".")
        node = VALUES["auth"]
        for part in maps:
            node = node[part]
        assert node[name] == "", key


@pytest.mark.parametrize("mode", ["noauth", "auth"])
@pytest.mark.parametrize("key", list(PROVIDER))
def test_auth_provider(key: str, mode: str) -> None:
    """Each provider or group setting is passed on as it is, when set.

    Args:
        key: The value under `auth`.
        mode: `auth.mode`.
    """
    value = PROVIDER_VALUES[key]
    # `--set` separates values by commas
    escaped = value.replace(",", "\\,")
    variables = env(
        render("--set", f"auth.mode={mode}", "--set-string", f"auth.{key}={escaped}")
    )
    assert variables[PROVIDER[key]] == value
    others = set(PROVIDER.values()) - {PROVIDER[key]}
    assert not others & set(variables)


def test_auth_provider_all(tmp_path: Path) -> None:
    """All provider and group settings together, from a values file.

    Args:
        tmp_path: A directory for the values file.
    """
    values: dict[str, Any] = {"auth": {"mode": "auth"}}
    for key, value in PROVIDER_VALUES.items():
        *maps, name = key.split(".")
        node = values["auth"]
        for part in maps:
            node = node.setdefault(part, {})
        node[name] = value
    path = tmp_path / "values.yaml"
    path.write_text(yaml.safe_dump(values))
    variables = env(render("--values", str(path)))
    for key, variable in PROVIDER.items():
        assert variables[variable] == PROVIDER_VALUES[key]


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "auth.userInfoUri=null"),
        ("--set", "auth.groups=null"),
        ("--set", "auth.groups.prefix=null"),
        ("--set", "auth.swaggerOauth=null"),
        ("--set", "auth.swaggerOauth.scopes=null"),
    ],
)
def test_auth_provider_null(args: tuple[str, ...]) -> None:
    """Null maps and values leave tesk-api's defaults too.

    Args:
        args: More `helm template` arguments.
    """
    variables = env(render(*args))
    for variable in PROVIDER.values():
        assert variable not in variables


@pytest.mark.parametrize(
    ("args", "variable", "expected"),
    [
        (
            ("--set", "auth.groups.adminSubgroup=0"),
            "TESK_API_AUTHORISATION_ADMIN_SUBGROUP",
            "0",
        ),
        (
            ("--set", "auth.groups.parentGroup=false"),
            "TESK_API_AUTHORISATION_PARENT_GROUP",
            "false",
        ),
        (
            ("--set", "auth.groups.suffix=123"),
            "TESK_API_AUTHORISATION_GROUP_SUFFIX",
            "123",
        ),
        (("--set", "auth.envSubgroup=0"), "TESK_API_AUTHORISATION_ENV_SUBGROUP", "0"),
    ],
)
def test_auth_provider_scalars(
    args: tuple[str, ...], variable: str, expected: str
) -> None:
    """Group settings that `--set` reads as numbers or booleans keep their text.

    Args:
        args: More `helm template` arguments.
        variable: The variable of tesk-api.
        expected: Its value.
    """
    manifests = render(*args)
    assert env(manifests)[variable] == expected
    # Rendered as strings, as Kubernetes requires
    for var in container(manifests)["env"]:
        if "value" in var:
            assert isinstance(var["value"], str), var


def test_auth_provider_numbers_values_file(tmp_path: Path) -> None:
    """Whole numbers from a values file aren't rendered in scientific notation.

    Helm reads numbers in values files as floats.

    Args:
        tmp_path: A directory for the values file.
    """
    path = tmp_path / "values.yaml"
    path.write_text("auth:\n  envSubgroup: 12345678\n  groups:\n    adminSubgroup: 0\n")
    variables = env(render("--values", str(path)))
    assert variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"] == "12345678"
    assert variables["TESK_API_AUTHORISATION_ADMIN_SUBGROUP"] == "0"


def test_auth_provider_number_too_large(tmp_path: Path) -> None:
    """A whole number too large to be exact fails, instead of changing.

    Args:
        tmp_path: A directory for the values file.
    """
    path = tmp_path / "values.yaml"
    path.write_text("auth:\n  envSubgroup: 12345678901234567890\n")
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--values", str(path))
    assert "provider or group value under auth" in error.value.stderr
    assert "too large" in error.value.stderr


@pytest.mark.parametrize(
    ("key", "variable"),
    [
        ("envSubgroup", "TESK_API_AUTHORISATION_ENV_SUBGROUP"),
        ("envBaseGroup", "TESK_API_AUTHORISATION_BASE_GROUP"),
    ],
)
@pytest.mark.parametrize("value", ["", "null"])
def test_auth_groups_unset(key: str, variable: str, value: str) -> None:
    """An empty or null environment group leaves tesk-api's default.

    So that `auth.groups.parentGroup` and `auth.envSubgroup` make up the
    environment group without `auth.envBaseGroup`, which replaces both.

    Args:
        key: The value under `auth`.
        variable: The variable of tesk-api.
        value: The empty value, as a `--set` value.
    """
    assert variable not in env(render("--set", f"auth.{key}={value}"))


def test_auth_parent_group() -> None:
    """Without `auth.envBaseGroup`, the parent group and subgroup are passed on."""
    variables = env(
        render(
            "--set",
            "auth.envBaseGroup=",
            "--set",
            "auth.groups.parentGroup=vo:tesk",
            "--set",
            "auth.envSubgroup=prod",
        )
    )
    assert variables["TESK_API_AUTHORISATION_PARENT_GROUP"] == "vo:tesk"
    assert variables["TESK_API_AUTHORISATION_ENV_SUBGROUP"] == "prod"
    assert "TESK_API_AUTHORISATION_BASE_GROUP" not in variables


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        (("--set", "auth.groups.parentGroup=vo:tesk"), True),
        (("--set", "auth.envBaseGroup=", "--set", "auth.groups.parentGroup=v"), False),
        (("--set", "auth.groups=null"), False),
        ((), False),
    ],
)
def test_notes_parent_group(
    tmp_path: Path, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn if `auth.envBaseGroup` overrides the parent group.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: More `helm template` arguments.
        warned: Whether the notes warn.
    """
    text = notes(*args, tmp_path=tmp_path)
    assert ("WARNING: auth.groups.parentGroup is set" in text) == warned


@pytest.mark.parametrize(
    ("value", "warned"),
    [
        ("http://keycloak.auth.svc/realms/tes/protocol/openid-connect/userinfo", True),
        ("https://login.example.org/userinfo", False),
        ("", False),
        ("null", False),
    ],
)
def test_notes_user_info_http(tmp_path: Path, value: str, warned: bool) -> None:
    """The notes warn if tokens go to the user info endpoint unencrypted.

    Args:
        tmp_path: A directory for a copy of the chart.
        value: `auth.userInfoUri`, as a `--set` value.
        warned: Whether the notes warn.
    """
    text = notes("--set", f"auth.userInfoUri={value}", tmp_path=tmp_path)
    assert ("WARNING: auth.userInfoUri is an http:// URL" in text) == warned


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "auth.userInfoUri=login.example.org/oidc/userinfo"),
        ("--set", "auth.userInfoUri=ftp://login.example.org/userinfo"),
        ("--set", "auth.swaggerOauth.authorizationEndpoint=/oidc/authorize"),
        ("--set", "auth.swaggerOauth.tokenEndpoint=https://"),
        ("--set-json", "auth.userInfoUri=[]"),
        ("--set-json", "auth.groups=[]"),
        ("--set-json", "auth.groups.prefix={}"),
        ("--set-json", "auth.swaggerOauth=true"),
        ("--set-json", 'auth.swaggerOauth.scopes=["openid"]'),
    ],
)
def test_auth_provider_invalid(args: tuple[str, ...]) -> None:
    """The schema rejects endpoints that aren't HTTP(S) URLs, and wrong types.

    Args:
        args: More `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "values don't meet the specifications of the schema" in error.value.stderr


def _yaml_block(path: Path, heading: str) -> dict[str, Any]:
    """Get the first YAML code block below a heading of a Markdown file.

    Args:
        path: The Markdown file.
        heading: The heading, with its `#` signs.

    Returns:
        The block, parsed.
    """
    text = path.read_text()
    assert f"\n{heading}\n" in text, heading
    section = text.split(f"\n{heading}\n", 1)[1]
    match = re.search(r"```yaml\n(.*?)```", section, re.DOTALL)
    assert match is not None, heading
    block: dict[str, Any] = yaml.safe_load(match[1])
    return block


def test_auth_ls_login_example(tmp_path: Path) -> None:
    """The LS Login example of the deployment guide renders as documented.

    Its endpoints are those of LS Login's discovery document
    (https://login.aai.lifescience-ri.eu/oidc/.well-known/openid-configuration).

    Args:
        tmp_path: A directory for the values file.
    """
    values = _yaml_block(
        CHART.parents[1] / "docs" / "deployment.md", "### LS Login and other providers"
    )
    path = tmp_path / "values.yaml"
    path.write_text(yaml.safe_dump(values))
    variables = env(render("--values", str(path)))
    login = "https://login.aai.lifescience-ri.eu/oidc"
    assert variables["SPRING_PROFILES_ACTIVE"] == "auth"
    assert variables["SECURITY_OAUTH2_RESOURCE_USER_INFO_URI"] == f"{login}/userinfo"
    assert variables["TESK_API_AUTHORISATION_GROUPS_CLAIM"] == "eduperson_entitlement"
    assert (
        variables["TESK_API_AUTHORISATION_GROUP_PREFIX"]
        == "urn:geant:lifescience-ri.eu:group:"
    )
    assert variables["TESK_API_AUTHORISATION_GROUP_SUFFIX"] == "#aai.lifescience-ri.eu"
    assert (
        variables["TESK_API_SWAGGER_OAUTH_AUTHORIZATION_ENDPOINT"]
        == f"{login}/authorize"
    )
    assert variables["TESK_API_SWAGGER_OAUTH_TOKEN_ENDPOINT"] == f"{login}/token"


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
        "--set",
        "tesk.image.repository=example.org/api",
        "--set",
        "tesk.image.tag=1",
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
    """The API runs as non-root without privileges by default."""
    manifests = render()
    pod = deployment(manifests)["spec"]["template"]["spec"]
    assert pod["securityContext"] == {
        "runAsUser": 1000,
        "runAsNonRoot": True,
        "seccompProfile": {"type": "RuntimeDefault"},
    }
    assert container(manifests)["securityContext"] == {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
    }


def test_security_context_values() -> None:
    """The security contexts are merged with the values; null removes a field."""
    manifests = render(
        "--set",
        "tesk.podSecurityContext.runAsUser=null",
        "--set",
        "tesk.podSecurityContext.fsGroup=2000",
        "--set",
        "tesk.securityContext.readOnlyRootFilesystem=true",
    )
    pod = deployment(manifests)["spec"]["template"]["spec"]
    # E.g., on OpenShift, which assigns the user
    assert pod["securityContext"] == {
        "fsGroup": 2000,
        "runAsNonRoot": True,
        "seccompProfile": {"type": "RuntimeDefault"},
    }
    assert container(manifests)["securityContext"] == {
        "allowPrivilegeEscalation": False,
        "capabilities": {"drop": ["ALL"]},
        "readOnlyRootFilesystem": True,
    }


def test_security_context_null() -> None:
    """Null removes the security contexts of the API's pod and container."""
    manifests = render(
        "--set", "tesk.podSecurityContext=null", "--set", "tesk.securityContext=null"
    )
    pod = deployment(manifests)["spec"]["template"]["spec"]
    assert "securityContext" not in pod
    assert "securityContext" not in container(manifests)


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("--set-json", "tesk.executor.securityContext={}"),
        ("--set-json", "tesk.executor.securityContext=null"),
        ("--set-json", "tesk.executor=null"),
    ],
)
def test_executor_security_context_default(args: tuple[str, ...]) -> None:
    """Without a security context, executors run as before.

    No ConfigMap, no `CONFIGMAP`, and no checksum annotation of the
    executors.

    Args:
        args: The `helm template` arguments.
    """
    manifests = render(*args)
    assert find(manifests, "ConfigMap", "tesk-executor") is None
    assert "CONFIGMAP" not in env(manifests)
    metadata = deployment(manifests)["spec"]["template"]["metadata"]
    assert "checksum/executor-config" not in metadata.get("annotations", {})


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (
            (
                "--set",
                "tesk.executor.securityContext.runAsUser=1000",
                "--set",
                "tesk.executor.securityContext.runAsGroup=3000",
                "--set",
                "tesk.executor.securityContext.fsGroup=2000",
                "--set",
                "tesk.executor.securityContext.runAsNonRoot=true",
            ),
            {"runAsUser": 1000, "runAsGroup": 3000, "fsGroup": 2000, "nonRoot": True},
        ),
        (
            ("--set", "tesk.executor.securityContext.fsGroup=2000"),
            {"fsGroup": 2000},
        ),
        (
            ("--set", "tesk.executor.securityContext.runAsNonRoot=false"),
            {"nonRoot": False},
        ),
        (
            ("--set", "tesk.executor.securityContext.runAsUser=0"),
            {"runAsUser": 0},
        ),
    ],
)
def test_executor_security_context(
    args: tuple[str, ...], expected: dict[str, Any]
) -> None:
    """The executors' security context reaches tesk-api through a ConfigMap.

    tesk-api reads the ConfigMap named in `CONFIGMAP` at startup (key
    `securityContext`, with `nonRoot` for `runAsNonRoot`).

    Args:
        args: The `helm template` arguments.
        expected: The fields that tesk-api reads.
    """
    manifests = render(*args, release="prod")
    config = get(manifests, "ConfigMap", "prod-tesk-executor")
    assert yaml.safe_load(config["data"]["securityContext"]) == expected
    assert env(manifests)["CONFIGMAP"] == "prod-tesk-executor"


def test_executor_security_context_checksum() -> None:
    """A checksum of the ConfigMap's data restarts the API's pod on changes.

    tesk-api reads the ConfigMap only at startup.
    """
    checksums = []
    for group in (1, 2):
        manifests = render("--set", f"tesk.executor.securityContext.fsGroup={group}")
        data = get(manifests, "ConfigMap", "tesk-executor")["data"]["securityContext"]
        metadata = deployment(manifests)["spec"]["template"]["metadata"]
        checksum = metadata["annotations"]["checksum/executor-config"]
        # The block scalar adds a final newline that the checksum leaves out
        assert checksum == hashlib.sha256(data.rstrip("\n").encode()).hexdigest()
        checksums.append(checksum)
    assert checksums[0] != checksums[1]


def test_executor_security_context_values_file(tmp_path: Path) -> None:
    """Numbers in a values file (floats to Helm) are rendered as integers.

    Args:
        tmp_path: A directory for the values file.
    """
    values = tmp_path / "values.yaml"
    values.write_text(
        "tesk:\n  executor:\n    securityContext:\n"
        "      runAsUser: 1000000\n      fsGroup: 2000\n"
    )
    config = get(render("-f", str(values)), "ConfigMap", "tesk-executor")
    # Without a conversion, Helm would render 1000000 as 1e+06
    assert yaml.safe_load(config["data"]["securityContext"]) == {
        "fsGroup": 2000,
        "runAsUser": 1000000,
    }


@pytest.mark.parametrize(
    "value",
    [
        '{"runAsUser": 0, "runAsNonRoot": true}',
        '{"runAsUser": 0.0, "runAsNonRoot": true}',
    ],
)
def test_executor_security_context_root_and_non_root(value: str) -> None:
    """Root with `runAsNonRoot` fails, as Kubernetes wouldn't start executors.

    Args:
        value: The security context, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"tesk.executor.securityContext={value}")
    assert "runAsUser 0 contradicts runAsNonRoot" in error.value.stderr


@pytest.mark.parametrize(
    "value",
    [
        '{"runAsUser": -1}',
        '{"runAsUser": 2147483648}',
        '{"fsGroup": 2147483648}',
        '{"runAsUser": 1.5}',
        '{"runAsUser": "1000"}',
        '{"runAsNonRoot": "yes"}',
        '{"privileged": true}',
        "[]",
    ],
)
def test_executor_security_context_invalid(value: str) -> None:
    """The schema accepts only the fields that tesk-api reads, as numbers.

    Args:
        value: The security context, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"tesk.executor.securityContext={value}")
    assert "values don't meet the specifications of the schema" in error.value.stderr


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
    secret = get(manifests, "Secret", "tesk-oauth-client")
    assert secret["stringData"] == {"id": "client", "secret": "secret"}
    assert find(render(), "Secret", "tesk-oauth-client") is None


@pytest.mark.parametrize(
    "args", [(), ("--set", "auth.clientSecret="), ("--set", "auth.clientSecret=null")]
)
def test_auth_without_client_secret(args: tuple[str, ...]) -> None:
    """Without `auth.clientSecret` (deprecated), the secret's `secret` is empty.

    Empty, not left out, so that an upgrade also clears a value set before.

    Args:
        args: More `helm template` arguments.
    """
    manifests = render(
        "--set", "auth.mode=auth", "--set", "auth.clientId=client", *args
    )
    secret = get(manifests, "Secret", "tesk-oauth-client")
    assert secret["stringData"] == {"id": "client", "secret": ""}


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


CLAIM = (
    "TESK_API_AUTHORISATION_CLAIM_ENABLED",
    "TESK_API_AUTHORISATION_CLAIM_NAME",
    "TESK_API_AUTHORISATION_CLAIM_VALUES",
)


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("--set", "auth.claim.enabled=false", "--set", "auth.claim.name=x"),
        ("--set-string", "auth.claim.enabled=false"),
        ("--set-json", "auth.claim=null"),
        ("--set-json", "auth.claim.enabled=null"),
        (
            "--set",
            "auth.mode=noauth",
            "--set-json",
            'auth.claim={"enabled": true, "name": "x", "values": ["a"]}',
        ),
        ("--set", "auth.mode=noauth", "--set", "auth.claim.enabled=true"),
    ],
)
def test_auth_claim_off(args: tuple[str, ...]) -> None:
    """Off by default, and with mode noauth: none of the claim's variables.

    Rendered with mode auth, unless the arguments set noauth: with mode
    noauth, all endpoints are open, so the claim isn't checked.

    Args:
        args: The `helm template` arguments.
    """
    variables = env(render("--set", "auth.mode=auth", *args))
    assert not set(CLAIM) & set(variables)


@pytest.mark.parametrize(
    ("args", "name", "values"),
    [
        (
            (
                "--set-json",
                'auth.claim={"enabled": true, "name": "eduperson_entitlement",'
                ' "values": ["urn:geant:example.org:group:tesk#example.org"]}',
            ),
            "eduperson_entitlement",
            "urn:geant:example.org:group:tesk#example.org",
        ),
        (
            (
                "--set-string",
                "auth.claim.enabled=true",
                "--set",
                "auth.claim.name=eduperson_assurance",
                "--set-json",
                'auth.claim.values=["a", "b c", "d"]',
            ),
            "eduperson_assurance",
            "a,b c,d",
        ),
        (
            (
                "--set-json",
                'auth.claim={"enabled": true, "name": " entitlements ",'
                ' "values": [" a ", "\\u000b", "b"]}',
            ),
            "entitlements",
            "a,b",
        ),
    ],
)
def test_auth_claim(args: tuple[str, ...], name: str, values: str) -> None:
    """With `auth.claim.enabled`, the claim's name and values are passed on.

    The values are trimmed, blank ones left out, and joined with commas,
    as tesk-api splits them.

    Args:
        args: The `helm template` arguments.
        name: The expected `TESK_API_AUTHORISATION_CLAIM_NAME`.
        values: The expected `TESK_API_AUTHORISATION_CLAIM_VALUES`.
    """
    variables = env(render("--set", "auth.mode=auth", *args))
    assert variables["TESK_API_AUTHORISATION_CLAIM_ENABLED"] == "true"
    assert variables["TESK_API_AUTHORISATION_CLAIM_NAME"] == name
    assert variables["TESK_API_AUTHORISATION_CLAIM_VALUES"] == values


@pytest.mark.parametrize(
    "claim",
    [
        '{"enabled": true, "values": ["a"]}',
        '{"enabled": true, "name": "", "values": ["a"]}',
        '{"enabled": true, "name": "  ", "values": ["a"]}',
        '{"enabled": true, "name": "x"}',
        '{"enabled": true, "name": "x", "values": []}',
        '{"enabled": true, "name": "x", "values": null}',
        '{"enabled": true, "name": "x", "values": ["\\u000b"]}',
        '{"enabled": true, "name": "x", "values": ["\\u00a0"]}',
    ],
)
def test_auth_claim_incomplete(claim: str) -> None:
    """Turned on without a name or values, the chart fails, as tesk-api would.

    Args:
        claim: `auth.claim`, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", "auth.mode=auth", "--set-json", f"auth.claim={claim}")
    assert "auth.claim.enabled needs auth.claim.name and" in error.value.stderr


@pytest.mark.parametrize(
    "claim",
    [
        '{"enabled": "yes", "name": "x", "values": ["a"]}',
        '{"enabled": 1, "name": "x", "values": ["a"]}',
        '{"enabled": true, "name": "x", "values": ["a,b"]}',
        '{"enabled": true, "name": "x", "values": [""]}',
        '{"enabled": true, "name": "x", "values": [" "]}',
        '{"enabled": true, "name": "x", "values": "a"}',
        '{"enabled": true, "name": "x", "values": [1]}',
        '{"enabled": true, "name": ["x"], "values": ["a"]}',
        '{"enabled": true, "name": "x", "values": ["a"], "value": "b"}',
    ],
)
def test_auth_claim_invalid(claim: str) -> None:
    """The schema rejects values that tesk-api would split or ignore.

    Args:
        claim: `auth.claim`, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"auth.claim={claim}")
    assert "values don't meet the specifications of the schema" in error.value.stderr


LEGACY_USER_LABELS = "TESK_API_AUTHORISATION_LEGACY_USER_LABELS"


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("--set", "auth.legacyUserLabels=false"),
        ("--set-string", "auth.legacyUserLabels=false"),
        ("--set-json", "auth.legacyUserLabels=null"),
        ("--set", "auth.mode=noauth", "--set", "auth.legacyUserLabels=true"),
    ],
)
def test_auth_legacy_user_labels_off(args: tuple[str, ...]) -> None:
    """Off by default, and with mode noauth: tesk-api's default (off) applies.

    Rendered with mode auth, unless the arguments set noauth: with mode
    noauth, all endpoints are open, so tasks aren't matched to creators.

    Args:
        args: The `helm template` arguments.
    """
    variables = env(render("--set", "auth.mode=auth", *args))
    assert LEGACY_USER_LABELS not in variables


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "auth.legacyUserLabels=true"),
        ("--set-string", "auth.legacyUserLabels=true"),
    ],
)
def test_auth_legacy_user_labels(args: tuple[str, ...]) -> None:
    """With mode auth, `auth.legacyUserLabels: true` turns the setting on.

    Args:
        args: The `helm template` arguments.
    """
    variables = env(render("--set", "auth.mode=auth", *args))
    assert variables[LEGACY_USER_LABELS] == "true"


def test_auth_legacy_user_labels_values_file(tmp_path: Path) -> None:
    """A boolean from a values file is passed on as the string `true`.

    Args:
        tmp_path: A directory for the values file.
    """
    values = tmp_path / "values.yaml"
    values.write_text("auth:\n  mode: auth\n  legacyUserLabels: true\n")
    assert env(render("-f", str(values)))[LEGACY_USER_LABELS] == "true"


def test_auth_legacy_user_labels_with_claim() -> None:
    """The setting and authorisation by a claim can be on together."""
    variables = env(
        render(
            "--set",
            "auth.mode=auth",
            "--set",
            "auth.legacyUserLabels=true",
            "--set",
            "auth.serviceInfoPublic=false",
            "--set-json",
            'auth.claim={"enabled": true, "name": "x", "values": ["a"]}',
        )
    )
    assert variables[LEGACY_USER_LABELS] == "true"
    assert variables["TESK_API_AUTHORISATION_CLAIM_ENABLED"] == "true"
    assert variables["TESK_API_SERVICE_INFO_PUBLIC"] == "false"


@pytest.mark.parametrize("value", ['"yes"', "1", "[]", '{"enabled": true}'])
def test_auth_legacy_user_labels_invalid(value: str) -> None:
    """The schema accepts only booleans (also as strings) and null.

    Args:
        value: `auth.legacyUserLabels`, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"auth.legacyUserLabels={value}")
    assert "values don't meet the specifications of the schema" in error.value.stderr


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
    """The service info is rendered from the values into a ConfigMap."""
    manifests = render()
    config = get(manifests, "ConfigMap", "tesk-service-info")
    assert list(config["data"]) == ["service-info.yaml"]
    assert container(manifests)["volumeMounts"] == [
        {"name": "service-info", "mountPath": "/etc/tesk/service-info"}
    ]
    volumes = deployment(manifests)["spec"]["template"]["spec"]["volumes"]
    assert volumes == [
        {"name": "service-info", "configMap": {"name": "tesk-service-info"}}
    ]
    assert (
        env(manifests)["TESK_API_SERVICE_INFO_LOCATION"]
        == "file:///etc/tesk/service-info/service-info.yaml"
    )


def _service_info(*args: str) -> tuple[dict[str, Any], str]:
    """Render the service info.

    Args:
        args: More `helm template` arguments.

    Returns:
        The service info, parsed, and its text.
    """
    config = get(render(*args), "ConfigMap", "tesk-service-info")
    text: str = config["data"]["service-info.yaml"]
    info: dict[str, Any] = yaml.safe_load(text)
    return info, text


def test_service_info_defaults() -> None:
    """The defaults describe EMBL-EBI's deployment, as the file of 0.1.x did.

    Except for the contact and documentation URLs, which point to this
    repository and its docs, and `type` and `version`, which the chart sets
    (`version` to the tag of the API's image).
    """
    manifests = render()
    assert container(manifests)["image"].endswith(f":{METADATA['appVersion']}")
    info, text = _service_info()
    assert info == {
        "id": "uk.ac.ebi.tsc.tesk",
        "name": "TESK",
        "type": {"group": "org.ga4gh", "artifact": "TES", "version": "1.0.0"},
        "description": "GA4GH TES Server implementation for Kubernetes",
        "organization": {"name": "EMBL-EBI", "url": "https://www.ebi.ac.uk/"},
        "contactUrl": "https://github.com/elixir-cloud-aai/TESK/issues",
        "documentationUrl": "https://tesk.readthedocs.io/",
        "createdAt": datetime.date(2021, 4, 6),
        "environment": "dev",
        "version": str(METADATA["appVersion"]),
        "storage": ["ftp://ftp-private.ebi.ac.uk"],
    }
    # A YAML timestamp, as tesk-api reads `createdAt` (a quoted string fails)
    assert "\ncreatedAt: 2021-04-06\n" in text


def test_service_info_type_artifact() -> None:
    """The artifact of the service info's type is `TES`, in capitals.

    The TES specification and clients use `tes`, but `TES` is right here:
    tesk-api reads `service-info.yaml` with SnakeYAML, which matches the
    name of the Java enum constant `TES`, and serves `"artifact": "tes"`.
    With `tes` in the file, tesk-api (1.2.0) can't read the service info
    and serves an empty body (elixir-cloud-aai/TESK#290).
    """
    info, text = _service_info()
    assert info["type"] == {"group": "org.ga4gh", "artifact": "TES", "version": "1.0.0"}
    assert '\n  artifact: "TES"\n' in text


@pytest.mark.parametrize("tag", ["1.2.1", "dev", "0"])
def test_service_info_version(tag: str) -> None:
    """The version of the service info is the tag of the API's image.

    Args:
        tag: `tesk.image.tag`.
    """
    manifests = render("--set-string", f"tesk.image.tag={tag}")
    assert container(manifests)["image"].endswith(f":{tag}")
    config = get(manifests, "ConfigMap", "tesk-service-info")
    assert yaml.safe_load(config["data"]["service-info.yaml"])["version"] == tag


def test_service_info_version_number(tmp_path: Path) -> None:
    """A numeric tag from a values file is the image's tag and version as written.

    Args:
        tmp_path: A directory for the values file.
    """
    path = tmp_path / "values.yaml"
    path.write_text("tesk:\n  image:\n    tag: 20261110\n")
    manifests = render("--values", str(path))
    assert container(manifests)["image"].endswith(":20261110")
    config = get(manifests, "ConfigMap", "tesk-service-info")
    info = yaml.safe_load(config["data"]["service-info.yaml"])
    assert info["version"] == "20261110"


def test_image_tag_number_too_large(tmp_path: Path) -> None:
    """A numeric tag that a float can't hold exactly fails with its key.

    Helm would otherwise render a rounded tag, for the image and the
    version of the service info.

    Args:
        tmp_path: A directory for the values file.
    """
    path = tmp_path / "values.yaml"
    path.write_text("tesk:\n  image:\n    tag: 12345678901234567890\n")
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--values", str(path))
    assert "tesk.image.tag is a number too large" in error.value.stderr


@pytest.mark.parametrize("character", ["\\u0081", "\\u009f", "\\ufffe"])
def test_service_info_control_characters(character: str) -> None:
    """Characters that YAML doesn't allow, and JSON doesn't escape, fail.

    Args:
        character: The character, as a JSON escape.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f'serviceInfo.description="a{character}b"')
    assert "serviceInfo.description has a control character" in error.value.stderr


def test_service_info_values(tmp_path: Path) -> None:
    """All fields of the service info come from the values.

    Args:
        tmp_path: A directory for the values file.
    """
    service_info: dict[str, Any] = {
        "id": "org.example.tes",
        "name": "Example TES",
        "description": 'Text with "quotes", # and: colons',
        "organization": {"name": "Example", "url": "https://example.org/"},
        "contactUrl": "mailto:tes@example.org",
        "documentationUrl": "https://example.org/docs",
        "createdAt": "2026-11-10T12:00:00Z",
        "updatedAt": "2026-11-11",
        "environment": "prod",
        "storage": ["s3://bucket", "ftp://ftp.example.org"],
    }
    values = {"tesk": {"image": {"tag": "1.2.1"}}, "serviceInfo": service_info}
    path = tmp_path / "values.yaml"
    path.write_text(yaml.safe_dump(values))
    info, text = _service_info("--values", str(path))
    expected = dict(service_info)
    expected["createdAt"] = datetime.datetime(2026, 11, 10, 12, tzinfo=datetime.UTC)
    expected["updatedAt"] = datetime.date(2026, 11, 11)
    expected["type"] = {"group": "org.ga4gh", "artifact": "TES", "version": "1.0.0"}
    expected["version"] = "1.2.1"
    assert info == expected
    assert "\ncreatedAt: 2026-11-10T12:00:00Z\n" in text


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "serviceInfo.description="),
        ("--set", "serviceInfo.description=null"),
    ],
)
def test_service_info_optional(args: tuple[str, ...]) -> None:
    """Optional fields that are empty or null are left out.

    Args:
        args: More `helm template` arguments.
    """
    info, _ = _service_info(
        *args,
        "--set",
        "serviceInfo.contactUrl=",
        "--set",
        "serviceInfo.documentationUrl=null",
        "--set",
        "serviceInfo.createdAt=",
        "--set",
        "serviceInfo.environment=",
        "--set-json",
        "serviceInfo.storage=[]",
    )
    for field in (
        "description",
        "contactUrl",
        "documentationUrl",
        "createdAt",
        "updatedAt",
        "environment",
        "storage",
    ):
        assert field not in info, field
    assert set(info) == {"id", "name", "type", "organization", "version"}


@pytest.mark.parametrize(
    ("field", "args", "value"),
    [
        ("id", ("--set", "serviceInfo.id=12345"), "12345"),
        ("name", ("--set", "serviceInfo.name=true"), "true"),
        (
            "environment",
            ("--set-string", "serviceInfo.environment=2026-11-10"),
            "2026-11-10",
        ),
        ("name", ("--set-json", 'serviceInfo.name="a\\u007fb\\u0085c"'), "a\x7fb\x85c"),
        ("description", ("--set-json", 'serviceInfo.description="a\\nb"'), "a\nb"),
    ],
)
def test_service_info_strings(field: str, args: tuple[str, ...], value: str) -> None:
    """Text fields stay strings, also if YAML would read them otherwise.

    tesk-api reads them as strings; a date would fail as one. Characters that
    YAML doesn't allow as they are (DEL, NEL) are escaped.

    Args:
        field: The field of the service info.
        args: More `helm template` arguments.
        value: The expected text.
    """
    info, _ = _service_info(*args)
    assert isinstance(info[field], str)
    assert info[field] == value


def test_service_info_numbers_values_file(tmp_path: Path) -> None:
    """Whole numbers from a values file are rendered as written, up to 2^53.

    Args:
        tmp_path: A directory for the values files.
    """
    path = tmp_path / "values.yaml"
    path.write_text("serviceInfo:\n  id: 12345678\n")
    info, _ = _service_info("--values", str(path))
    assert info["id"] == "12345678"
    path.write_text("serviceInfo:\n  id: 12345678901234567890\n")
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--values", str(path))
    assert "serviceInfo.id is a number too large" in error.value.stderr


@pytest.mark.parametrize(
    "field",
    ["id", "name", "organization.name", "organization.url"],
)
def test_service_info_required(field: str) -> None:
    """The fields that the service info specification requires must be set.

    Args:
        field: The field under `serviceInfo`.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", f"serviceInfo.{field}=")
    assert f"serviceInfo.{field} must be set" in error.value.stderr


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "serviceInfo.createdAt=yesterday"),
        ("--set", "serviceInfo.updatedAt=2026-13-01x"),
        ("--set", "serviceInfo.createdAt=10.11.2026"),
        # YAML 1.1 reads dates with one-digit months or days as text
        ("--set", "serviceInfo.createdAt=2026-1-5"),
        ("--set", "serviceInfo.updatedAt=2026-11-1"),
        ("--set", "serviceInfo.existingConfigMap=false"),
        ("--set-json", "serviceInfo.storage=[1]"),
        ("--set-json", "serviceInfo.organization=[]"),
        ("--set-json", "serviceInfo.storage={}"),
        ("--set", "serviceInfo.organization.email=a@example.org"),
        ("--set", "serviceInfo.type.group=org.example"),
        ("--set", "serviceInfo.version=2"),
    ],
)
def test_service_info_invalid(args: tuple[str, ...]) -> None:
    """The schema rejects dates that aren't YAML timestamps, and unknown keys.

    tesk-api can't read the file otherwise, and answers without service
    info; `type` and `version` are set by the chart.

    Args:
        args: More `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "values don't meet the specifications of the schema" in error.value.stderr


@pytest.mark.parametrize("value", ["today", "2026-1-5"])
def test_service_info_invalid_without_schema(value: str) -> None:
    """The templates check the dates too, also without the schema.

    Args:
        value: `serviceInfo.createdAt`.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--skip-schema-validation", "--set", f"serviceInfo.createdAt={value}")
    assert "serviceInfo.createdAt must be a date" in error.value.stderr


@pytest.mark.parametrize(
    "value",
    [
        "2021-02-30",
        "2021-13-01",
        "2021-2-30T12:00:00Z",
        "2021-04-06T24:00:00Z",
        "2021-04-06T12:60:00Z",
        "2021-04-06T12:00:60Z",
    ],
)
def test_service_info_impossible_dates(value: str) -> None:
    """Dates and times that don't exist fail, though they look like timestamps.

    SnakeYAML would read them as other dates (e.g., 2021-02-30 as
    2021-03-02).

    Args:
        value: `serviceInfo.createdAt`.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-string", f"serviceInfo.createdAt={value}")
    assert "serviceInfo.createdAt must be a date" in error.value.stderr


def test_service_info_existing_config_map_schema() -> None:
    """With an existing ConfigMap, the other fields are still checked."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(
            "--set",
            "serviceInfo.existingConfigMap=my-service-info",
            "--set",
            "serviceInfo.createdAt=today",
        )
    assert "values don't meet the specifications of the schema" in error.value.stderr


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-11-10", datetime.date(2026, 11, 10)),
        (
            "2026-1-5T1:00:00Z",
            datetime.datetime(2026, 1, 5, 1, tzinfo=datetime.UTC),
        ),
        (
            "2026-11-10 12:00:00.5 +01:00",
            datetime.datetime(
                2026,
                11,
                10,
                12,
                0,
                0,
                500000,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
            ),
        ),
    ],
)
def test_service_info_timestamps(value: str, expected: datetime.date) -> None:
    """Dates that pass the checks are YAML 1.1 timestamps.

    PyYAML resolves timestamps as SnakeYAML, which tesk-api uses, does.

    Args:
        value: `serviceInfo.createdAt`.
        expected: The timestamp that YAML reads.
    """
    info, _ = _service_info("--set-string", f"serviceInfo.createdAt={value}")
    assert info["createdAt"] == expected


def test_service_info_existing_config_map_unset() -> None:
    """Without the schema, `existingConfigMap: false` is set, consistently."""
    manifests = render(
        "--skip-schema-validation", "--set", "serviceInfo.existingConfigMap=false"
    )
    assert find(manifests, "ConfigMap", "tesk-service-info") is None
    volumes = deployment(manifests)["spec"]["template"]["spec"]["volumes"]
    assert volumes[0]["configMap"] == {"name": "false"}


def test_service_info_existing_config_map() -> None:
    """An existing ConfigMap replaces the chart's."""
    manifests = render("--set", "serviceInfo.existingConfigMap=my-service-info")
    assert find(manifests, "ConfigMap", "tesk-service-info") is None
    volumes = deployment(manifests)["spec"]["template"]["spec"]["volumes"]
    assert volumes == [
        {"name": "service-info", "configMap": {"name": "my-service-info"}}
    ]
    annotations = deployment(manifests)["spec"]["template"]["metadata"].get(
        "annotations", {}
    )
    assert "checksum/service-info" not in annotations


def test_service_info_checksum() -> None:
    """A change of the service info restarts the API's pod.

    tesk-api reads the file at startup, and then only every hour.
    """

    def checksum(*args: str) -> str:
        meta = deployment(render(*args))["spec"]["template"]["metadata"]
        value: str = meta["annotations"]["checksum/service-info"]
        return value

    assert checksum() == checksum()
    assert checksum() != checksum("--set", "serviceInfo.environment=prod")
    # Together with the executors' checksum
    meta = deployment(
        render("--set-json", 'tesk.executor.securityContext={"runAsUser": 1000}')
    )["spec"]["template"]["metadata"]
    assert set(meta["annotations"]) == {
        "checksum/service-info",
        "checksum/executor-config",
    }


@pytest.mark.parametrize(
    ("args", "noted"),
    [
        ((), True),
        (("--set", "serviceInfo.id=org.example.tes"), False),
        (("--set", "serviceInfo.existingConfigMap=mine"), False),
    ],
)
def test_notes_service_info(tmp_path: Path, args: tuple[str, ...], noted: bool) -> None:
    """The notes remind operators to describe their deployment.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: More `helm template` arguments.
        noted: Whether the notes have the reminder.
    """
    # The notes compare the ID with the default of `values.yaml`
    assert VALUES["serviceInfo"]["id"] == "uk.ac.ebi.tsc.tesk"
    text = notes(*args, tmp_path=tmp_path)
    assert ("NOTE: serviceInfo.id is the chart's default" in text) == noted


def test_service_info_file_removed() -> None:
    """The service info no longer comes from a file of the chart."""
    assert not (CHART / "service-info").exists()


def test_ingress() -> None:
    """The ingress routes the host to the API, with TLS if a secret is set."""
    manifests = render(
        "--set",
        "hostName=tes.example.org",
        "--set",
        "ingress.className=nginx",
    )
    spec = get(manifests, "Ingress", "tesk")["spec"]
    assert spec["ingressClassName"] == "nginx"
    # Also a class that YAML reads as 0; empty uses the cluster's default
    zero = get(render("--set", "ingress.className=0"), "Ingress", "tesk")["spec"]
    assert zero["ingressClassName"] == "0"
    assert "ingressClassName" not in get(render(), "Ingress", "tesk")["spec"]
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
    spec = get(manifests, "Ingress", "tesk")["spec"]
    assert spec["tls"] == [{"hosts": ["tes.example.org"], "secretName": "tls"}]


def test_ingress_path_and_annotations() -> None:
    """The ingress path is the API's context path; annotations are optional."""
    manifests = render(
        "--set",
        "ingress.path=/tesk",
        "--set-json",
        'ingress.annotations={"a.example.org/b":"c"}',
    )
    ingress = get(manifests, "Ingress", "tesk")
    # Maps are merged with the default annotations
    assert ingress["metadata"]["annotations"]["a.example.org/b"] == "c"
    assert ingress["spec"]["rules"][0]["http"]["paths"][0]["path"] == "/tesk"
    assert env(manifests)["SERVER_SERVLET_CONTEXT_PATH"] == "/tesk"
    manifests = render("--set", "ingress.annotations=null")
    ingress = get(manifests, "Ingress", "tesk")
    assert "annotations" not in ingress["metadata"]


def test_ingress_disabled() -> None:
    """Without the ingress, there is no route either outside OpenShift."""
    manifests = render("--set", "ingress.enabled=false")
    assert find(manifests, "Ingress", "tesk") is None
    assert find(manifests, "Route", "tesk") is None


def test_openshift_route() -> None:
    """On OpenShift, a route replaces the ingress, if that is disabled."""
    openshift = ("--api-versions", "route.openshift.io/v1")
    manifests = render(
        *openshift,
        "--set",
        "ingress.enabled=false",
        "--set",
        "hostName=tes.example.org",
    )
    route = get(manifests, "Route", "tesk")
    assert route["spec"]["host"] == "tes.example.org"
    assert route["spec"]["to"]["name"] == "tesk-api"
    assert route["spec"]["tls"]["termination"] == "edge"
    assert find(render(*openshift), "Route", "tesk") is None
    # Only false creates a route, not a missing switch
    manifests = render(*openshift, "--set", "ingress.enabled=null")
    assert find(manifests, "Route", "tesk") is None


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
    storage_class = get(manifests, "StorageClass", "tesk-gold")
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
        "ftp.hostIp=10.0.0.1",
    )
    assert find(manifests, "Secret", "tesk-ftp") is None
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
        ("--set-json", 'ftp.hosts=["2001:db8::1"]'),
        ("--set-json", 'ftp.hosts=["[::1"]'),
        ("--set-json", 'ftp.hosts=[":21"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org:abc"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org:0"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org\\u000b"]'),
        ("--set-json", 'ftp.hosts=["*.example.org"]'),
        ("--set-json", 'ftp.hosts=["ftp.example.org:65536"]'),
    ],
)
def test_ftp_hosts_invalid(args: tuple[str, ...]) -> None:
    """`ftp.hosts` entries are hosts, with a port or not, and nothing else.

    Args:
        args: The `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError):
        render(*args)


# Filer tags for cases with a taskmaster of another tag: `dev` isn't a
# release version, so the chart doesn't check that it is of the
# taskmaster's release
FILER_DEV = ("--set", "tesk.filer.image.tag=dev")
FILER_OLD = ("--set", "tesk.filer.image.tag=v0.10.6")
FILER_OLD_BARE = ("--set", "tesk.filer.image.tag=0.10.6")
USER = ("--set", "ftp.username=user")
PASSWORD = ("--set", "ftp.password=s3cr3t")


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((*USER, *PASSWORD), True),
        (USER, True),
        (("--set", "ftp.username=0", *PASSWORD), True),
        (("--set", "ftp.username=false", *PASSWORD), True),
        (PASSWORD, False),
        ((), False),
        ((*USER, *PASSWORD, "--set", "ftp.hosts={ftp.example.org}"), False),
        ((*USER, *PASSWORD, "--set", "ftp.classicFtpSecret="), False),
        ((*USER, *PASSWORD, "--set", "ftp.netrcSecret=netrc"), False),
    ],
)
def test_notes_ftp_hosts(tmp_path: Path, args: tuple[str, ...], warned: bool) -> None:
    """The notes warn about an FTP user name without `ftp.hosts`.

    Any user name, also one that YAML reads as 0 or false, but only if the
    credentials are used: with `ftp.classicFtpSecret` and without `.netrc`.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: The `helm template` arguments.
        warned: Whether the notes warn.
    """
    text = notes(*args, tmp_path=tmp_path)
    assert f"release tesk in namespace {NAMESPACE}" in text
    assert ("ftp.hosts is empty" in text) is warned
    assert "s3cr3t" not in text


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), False),
        (("--set", "auth.clientSecret="), False),
        (("--set", "auth.clientSecret=s3cr3t"), True),
        (("--set", "auth.clientSecret=0"), True),
        (("--set", "auth.mode=auth", "--set", "auth.clientSecret=s3cr3t"), True),
    ],
)
def test_notes_client_secret(
    tmp_path: Path, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn that `auth.clientSecret` is deprecated, if it is set.

    With any value, also one that YAML reads as 0.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: The `helm template` arguments.
        warned: Whether the notes warn.
    """
    text = notes(*args, tmp_path=tmp_path)
    assert ("auth.clientSecret is deprecated" in text) is warned
    assert "s3cr3t" not in text


@pytest.mark.parametrize(
    ("args", "keys"),
    [
        ((), []),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=v0.10.6",
                "--set",
                "tesk.filer.image.tag=v0.10.6",
            ),
            ["tesk.taskmaster.image.tag", "tesk.filer.image.tag"],
        ),
        (
            ("--set", "tesk.taskmaster.image.tag=v0.10.6", *FILER_DEV),
            ["tesk.taskmaster.image.tag"],
        ),
        (
            ("--set", "tesk.taskmaster.image.tag=dev", *FILER_OLD),
            ["tesk.filer.image.tag"],
        ),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=0.9.0",
                "--set",
                "tesk.filer.image.tag=0.10.6",
            ),
            ["tesk.taskmaster.image.tag", "tesk.filer.image.tag"],
        ),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=0.11.0",
                "--set",
                "tesk.filer.image.tag=0.11.0",
            ),
            [],
        ),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=v0.10.7",
                "--set",
                "tesk.filer.image.tag=dev",
            ),
            [],
        ),
    ],
)
def test_notes_ftp_hosts_old_images(
    tmp_path: Path, args: tuple[str, ...], keys: list[str]
) -> None:
    """The notes warn if `ftp.hosts` is set, but images are too old for it.

    Release tags up to v0.10.6 (with or without the `v`) ignore `ftp.hosts`;
    other tags (e.g., `0.11.0` or `dev`) are assumed to support it.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: Further `helm template` arguments (image tags).
        keys: The keys of the old image tags that the warning names.
    """
    hosts = ("--set", "ftp.hosts={ftp.example.org}")
    text = notes(*hosts, *args, tmp_path=tmp_path)
    if keys:
        assert f"WARNING: ftp.hosts is set, but {' and '.join(keys)} " in text
    else:
        assert "ftp.hosts is set" not in text
    assert "ftp.hosts is set" not in notes(*args, tmp_path=tmp_path)


def test_ftp_secret() -> None:
    """The FTP secret holds the credentials from the values."""
    manifests = render("--set", "ftp.username=user", "--set", "ftp.password=pass")
    secret = get(manifests, "Secret", "tesk-ftp")
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
    secret = get(manifests, "Secret", "tesk-ftp")
    assert secret["stringData"] == {"username": value, "password": value}


def test_ftp_secret_numeric() -> None:
    """Numbers set with `--set` are rendered as strings."""
    manifests = render("--set", "ftp.username=123", "--set", "ftp.password=456")
    secret = get(manifests, "Secret", "tesk-ftp")
    assert secret["stringData"] == {"username": "123", "password": "456"}


@pytest.mark.parametrize("value", TRICKY_VALUES)
def test_auth_quoting(value: str, tmp_path: Path) -> None:
    """The OAuth client ID and secret are strings."""
    values = tmp_path / "secrets.yaml"
    values.write_text(
        yaml.safe_dump(
            {
                "auth": {
                    "mode": "auth",
                    "clientId": value,
                    "clientSecret": value,
                }
            }
        )
    )
    manifests = render("-f", str(values))
    secret = get(manifests, "Secret", "tesk-oauth-client")
    assert secret["stringData"] == {"id": value, "secret": value}


def test_auth_numeric() -> None:
    """Numbers set with `--set` are strings."""
    manifests = render(
        "--set",
        "auth.mode=auth",
        "--set",
        "auth.clientId=123",
        "--set",
        "auth.clientSecret=456",
    )
    secret = get(manifests, "Secret", "tesk-oauth-client")
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
    assert get(manifests, "Secret", "tesk-ftp")["stringData"] == expected_data
    assert get(manifests, "Secret", "tesk-oauth-client")["stringData"] == {
        "id": expected,
        "secret": expected,
    }


def test_secret_unset() -> None:
    """Unset credentials render as before: null, the client secret empty.

    The FTP credentials and the client ID stay null, not empty strings; the
    deprecated client secret is empty, so that an upgrade clears it.
    """
    manifests = render("--set", "auth.mode=auth")
    assert get(manifests, "Secret", "tesk-ftp")["stringData"] == {
        "username": None,
        "password": None,
    }
    assert get(manifests, "Secret", "tesk-oauth-client")["stringData"] == {
        "id": None,
        "secret": "",
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
        "transfer.enabled=true",
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


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), None),
        (("--set", "tesk.filerHttpTimeout="), None),
        (("--set", "tesk.filerHttpTimeout=null"), None),
        (("--set", "tesk.filerHttpTimeout=600"), "600"),
        (("--set", "tesk.filerHttpTimeout=0.5"), "0.5"),
        (("--set-string", "tesk.filerHttpTimeout=120"), "120"),
    ],
)
def test_filer_http_timeout(args: tuple[str, ...], expected: str | None) -> None:
    """The filer's HTTP timeout is passed on as a string, if it is set.

    Args:
        args: The `helm template` arguments.
        expected: The value of the environment variable; `None` if unset.
    """
    variables = env(render(*args))
    key = "TESK_API_TASKMASTER_ENVIRONMENT_FILER_HTTP_TIMEOUT"
    if expected is None:
        assert key not in variables
    else:
        assert variables[key] == expected


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "tesk.filerHttpTimeout=0"),
        ("--set", "tesk.filerHttpTimeout=-5"),
        ("--set-string", "tesk.filerHttpTimeout=0"),
        ("--set-string", "tesk.filerHttpTimeout=abc"),
        ("--set-string", "tesk.filerHttpTimeout=1e3"),
        ("--set-json", "tesk.filerHttpTimeout=[]"),
        ("--set", "tesk.filerHttpTimeout=1000001"),
        ("--set-string", "tesk.filerHttpTimeout=1000000.5"),
        ("--set-json", "tesk.filerHttpTimeout=1e10"),
    ],
)
def test_filer_http_timeout_invalid(args: tuple[str, ...]) -> None:
    """The schema rejects timeouts that aren't positive numbers.

    Args:
        args: The `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "values don't meet the specifications of the schema" in error.value.stderr


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), False),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=v0.10.6",
                "--set",
                "tesk.filer.image.tag=v0.10.6",
            ),
            True,
        ),
        (("--set", "tesk.taskmaster.image.tag=dev", *FILER_OLD), True),
        (("--set", "tesk.taskmaster.image.tag=dev", *FILER_OLD_BARE), True),
        (("--set", "tesk.taskmaster.image.tag=0.10.6", *FILER_DEV), True),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=0.11.0",
                "--set",
                "tesk.filer.image.tag=0.11.0",
            ),
            False,
        ),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=v0.11.0",
                "--set",
                "tesk.filer.image.tag=dev",
            ),
            False,
        ),
    ],
)
def test_notes_filer_http_timeout_old_images(
    tmp_path: Path, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn if the timeout is set, but images are too old for it.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: Further `helm template` arguments (image tags).
        warned: Whether the notes warn.
    """
    text = notes("--set", "tesk.filerHttpTimeout=600", *args, tmp_path=tmp_path)
    assert ("tesk.filerHttpTimeout is set" in text) is warned
    assert "tesk.filerHttpTimeout is set" not in notes(tmp_path=tmp_path)


def test_filer_http_timeout_values_file(tmp_path: Path) -> None:
    """Numbers in a values file are passed on in a form the filer reads.

    Helm reads them as floats, which Go renders in scientific notation from
    1e6 on; the filer parses that as a number too.

    Args:
        tmp_path: A directory for the values file.
    """
    values = tmp_path / "values.yaml"
    values.write_text("tesk:\n  filerHttpTimeout: 1000000\n")
    variables = env(render("-f", str(values)))
    value = variables["TESK_API_TASKMASTER_ENVIRONMENT_FILER_HTTP_TIMEOUT"]
    assert float(value) == 1_000_000


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((), None),
        (("--set", "tesk.keepFailedPvcs=false"), None),
        (("--set", "tesk.keepFailedPvcs=null"), None),
        (("--set", "tesk.keepFailedPvcs=true"), "true"),
        (("--set-string", "tesk.keepFailedPvcs=true"), "true"),
        (("--set-string", "tesk.keepFailedPvcs=false"), None),
        (("--set-string", "tesk.keepFailedPvcs="), None),
    ],
)
def test_keep_failed_pvcs(args: tuple[str, ...], expected: str | None) -> None:
    """Keeping the PVCs of failed tasks sets the taskmaster's setting.

    Unset or false leaves the setting out, so that the taskmaster deletes
    them (its default). Strings are accepted for tools that set only
    strings.

    Args:
        args: The `helm template` arguments.
        expected: The value of the environment variable; `None` if unset.
    """
    variables = env(render(*args))
    key = "TESK_API_TASKMASTER_ENVIRONMENT_KEEP_FAILED_PVC"
    if expected is None:
        assert key not in variables
    else:
        assert variables[key] == expected


@pytest.mark.parametrize("value", ['"yes"', '"True"', "1", "[]"])
def test_keep_failed_pvcs_invalid(value: str) -> None:
    """The schema rejects values other than true, false, empty or null.

    The strings "true" and "false" pass too, in lowercase only.

    Args:
        value: The value, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set-json", f"tesk.keepFailedPvcs={value}")
    assert "values don't meet the specifications of the schema" in error.value.stderr


def test_keep_failed_pvcs_values_file(tmp_path: Path) -> None:
    """A YAML boolean in a values file keeps the PVCs too.

    Args:
        tmp_path: A directory for the values file.
    """
    values = tmp_path / "values.yaml"
    values.write_text("tesk:\n  keepFailedPvcs: true\n")
    variables = env(render("-f", str(values)))
    assert variables["TESK_API_TASKMASTER_ENVIRONMENT_KEEP_FAILED_PVC"] == "true"


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


# Values that render every object of the chart (but the OpenShift Route)
ALL_OBJECTS = (
    "--set",
    "ftp.hostIp=10.0.0.1",
    "--set",
    "ftp.netrcSecret=netrc",
    "--set",
    "storage=openstack",
    "--set",
    "auth.mode=auth",
    "--set",
    "tesk.executor.securityContext.fsGroup=1",
)


def test_labels() -> None:
    """All objects have the standard labels; selectors use name and instance."""
    manifests = render(*ALL_OBJECTS)
    for manifest in manifests:
        labels = manifest["metadata"]["labels"]
        assert labels.items() >= STANDARD_LABELS.items(), manifest["kind"]
        assert "app" not in labels
    selector = {
        "app.kubernetes.io/name": "tesk",
        "app.kubernetes.io/instance": "tesk",
    }
    spec = deployment(manifests)["spec"]
    assert spec["selector"] == {"matchLabels": selector}
    assert spec["template"]["metadata"]["labels"] == selector
    service = get(manifests, "Service", "tesk-api")
    assert service["spec"]["selector"] == selector


def _names(manifests: list[Manifest]) -> set[tuple[str, str]]:
    """Get the kinds and names of rendered objects.

    Args:
        manifests: The rendered objects.

    Returns:
        The kinds and names.
    """
    return {(m["kind"], m["metadata"]["name"]) for m in manifests}


# Objects whose names are fixed, as others read them by name: the filer
# mounts the secret `aws-secret`, and tasks reach the host's FTP server as
# `ftp`
FIXED_NAMES = {("Secret", "aws-secret"), ("Service", "ftp"), ("Endpoints", "ftp")}


def test_names_from_release(tmp_path: Path) -> None:
    """The objects' names start with the release's name (`tesk.fullname`).

    Args:
        tmp_path: A directory for a copy of the chart with S3 files.
    """
    chart = copy_chart(tmp_path)
    for name in ("config", "credentials"):
        (chart / "s3-config" / name).write_text("[default]\n")
    manifests = render(*ALL_OBJECTS, "--set", "storage=s3", chart=chart)
    manifests += render(*ALL_OBJECTS, chart=chart)
    manifests += render(
        "--api-versions", "route.openshift.io/v1", "--set", "ingress.enabled=false"
    )
    assert _names(manifests) == {
        ("ConfigMap", "tesk-executor"),
        ("ConfigMap", "tesk-service-info"),
        ("Deployment", "tesk-api"),
        ("Endpoints", "ftp"),
        ("Ingress", "tesk"),
        ("Role", "tesk-taskmaster"),
        ("RoleBinding", "tesk-taskmaster"),
        ("Route", "tesk"),
        ("Secret", "aws-secret"),
        ("Secret", "netrc"),
        ("Secret", "tesk-ftp"),
        ("Secret", "tesk-oauth-client"),
        ("Service", "ftp"),
        ("Service", "tesk-api"),
        ("ServiceAccount", "tesk-taskmaster"),
        ("StorageClass", "tesk-gold"),
    }


@pytest.mark.parametrize(
    ("release", "args", "prefix", "name"),
    [
        ("tesk", (), "tesk", "tesk"),
        ("prod", (), "prod-tesk", "tesk"),
        ("tesk-prod", (), "tesk-prod", "tesk"),
        ("prod", ("--set", "nameOverride=tes"), "prod-tes", "tes"),
        ("prod", ("--set", "fullnameOverride=tes"), "tes", "tesk"),
        ("x" * 53, (), "x" * 50, "tesk"),
        ("prod", ("--set", "fullnameOverride=" + "y" * 49 + "-z"), "y" * 49, "tesk"),
        ("prod", ("--set", "fullnameOverride=" + "y" * 48 + "--z"), "y" * 48, "tesk"),
    ],
)
def test_fullname(release: str, args: tuple[str, ...], prefix: str, name: str) -> None:
    """The prefix of the names follows `helm create` (`tesk.fullname`).

    It is cut to 50 characters, without a trailing dash, so that the longest
    name (`-service-info`) has at most 63.

    Args:
        release: The release name.
        args: More `helm template` arguments.
        prefix: The expected prefix.
        name: The expected label `app.kubernetes.io/name`.
    """
    manifests = render(*ALL_OBJECTS, *args, release=release)
    names = _names(manifests) - FIXED_NAMES
    assert ("Deployment", f"{prefix}-api") in names
    assert ("ConfigMap", f"{prefix}-service-info") in names
    for _, object_name in names:
        assert len(object_name) <= 63
    labels = deployment(manifests)["spec"]["selector"]["matchLabels"]
    assert labels == {
        "app.kubernetes.io/name": name,
        "app.kubernetes.io/instance": release,
    }


def test_two_releases() -> None:
    """Two releases in one namespace have objects and selectors of their own.

    Apart from the objects with fixed names (`aws-secret`, `ftp`), and those
    named in the values (here, the `.netrc` secret).
    """
    first = render(*ALL_OBJECTS, "--set", "ftp.netrcSecret=netrc-one", release="one")
    second = render(*ALL_OBJECTS, "--set", "ftp.netrcSecret=netrc-two", release="two")
    assert not (_names(first) & _names(second)) - FIXED_NAMES
    assert (
        deployment(first)["spec"]["selector"] != deployment(second)["spec"]["selector"]
    )


def test_names_passed_on() -> None:
    """References between the objects use the derived names.

    tesk-api gets the names of the taskmasters' service account and of the
    FTP secret from its environment.
    """
    manifests = render(*ALL_OBJECTS, release="prod")
    pod = deployment(manifests)["spec"]["template"]["spec"]
    variables = env(manifests)
    account = get(manifests, "ServiceAccount", "prod-tesk-taskmaster")
    name = account["metadata"]["name"]
    assert pod["serviceAccountName"] == name
    assert variables["TESK_API_TASKMASTER_SERVICE_ACCOUNT_NAME"] == name
    binding = get(manifests, "RoleBinding", "prod-tesk-taskmaster")
    assert binding["subjects"] == [{"kind": "ServiceAccount", "name": name}]
    assert binding["roleRef"]["name"] == "prod-tesk-taskmaster"
    get(manifests, "Role", "prod-tesk-taskmaster")
    get(manifests, "Secret", "prod-tesk-ftp")
    assert variables["TESK_API_TASKMASTER_FTP_SECRET_NAME"] == "prod-tesk-ftp"  # noqa: S105
    get(manifests, "Secret", "prod-tesk-oauth-client")
    for key in (
        "TESK_API_SWAGGER_OAUTH_CLIENT_ID",
        "TESK_API_SWAGGER_OAUTH_CLIENT_SECRET",
    ):
        assert variables[key]["secretKeyRef"]["name"] == "prod-tesk-oauth-client"
    get(manifests, "ConfigMap", "prod-tesk-service-info")
    assert pod["volumes"][0]["configMap"]["name"] == "prod-tesk-service-info"
    get(manifests, "Service", "prod-tesk-api")
    ingress = get(manifests, "Ingress", "prod-tesk")["spec"]
    backend = ingress["rules"][0]["http"]["paths"][0]["backend"]["service"]
    assert backend["name"] == "prod-tesk-api"
    route = get(
        render(
            "--api-versions",
            "route.openshift.io/v1",
            "--set",
            "ingress.enabled=false",
            release="prod",
        ),
        "Route",
        "prod-tesk",
    )
    assert route["spec"]["to"]["name"] == "prod-tesk-api"


@pytest.mark.parametrize(
    ("args", "name"),
    [
        ((), "tesk-ftp"),
        (("--set", "ftp.classicFtpSecret=null"), "tesk-ftp"),
        (("--set", "ftp.classicFtpSecret=ftp-secret"), "ftp-secret"),
        (("--set", "ftp.classicFtpSecret="), None),
        (("--set", "ftp.classicFtpSecret=false"), None),
        (("--values", "null"), "tesk-ftp"),
    ],
)
def test_ftp_secret_name(
    args: tuple[str, ...], name: str | None, tmp_path: Path
) -> None:
    """The FTP secret is `<fullname>-ftp`, unless named; empty creates none.

    False (as in earlier versions of the chart) creates none too.

    Args:
        args: The `helm template` arguments; `--values null` stands for a
            values file that sets `ftp.classicFtpSecret` to null.
        name: The name of the secret, or `None` if there is none.
        tmp_path: A directory for the values file.
    """
    if args == ("--values", "null"):
        values = tmp_path / "values.yaml"
        values.write_text("ftp:\n  classicFtpSecret: null\n")
        args = ("--values", str(values))
    manifests = render(*args)
    secrets = {m["metadata"]["name"] for m in manifests if m["kind"] == "Secret"}
    variable = env(manifests).get("TESK_API_TASKMASTER_FTP_SECRET_NAME")
    assert variable == name
    assert secrets == ({name} if name else set())


@pytest.mark.parametrize(("args", "message"), REMOVED + REMOVED_EMPTY)
def test_removed_keys(args: tuple[str, ...], message: str) -> None:
    """Keys of earlier versions of the chart fail, naming their replacements.

    Args:
        args: The `helm template` arguments.
        message: Part of the line of the error that names the key.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "no longer reads" in error.value.stderr
    assert f"  - {message}" in error.value.stderr
    assert "s3cr3t" not in error.value.stderr


def test_removed_keys_all() -> None:
    """The error lists all the removed keys in use at once."""
    args = [arg for options, _ in REMOVED for arg in options]
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    listed = [
        line for line in error.value.stderr.splitlines() if line.startswith("  - ")
    ]
    assert len(listed) == len(REMOVED)
    for _, message in REMOVED:
        assert f"  - {message}" in error.value.stderr


def _removed_keys_of_chart() -> set[str]:
    """Get the removed keys that the chart checks (`tesk.removedValues`).

    Returns:
        The keys, with the maps that hold them (e.g., `tesk.limitsCpu`).
    """
    text = (CHART / "templates" / "_helpers.tpl").read_text()
    start = text.index('{{- define "tesk.removedValues" -}}')
    block = text[start : text.index("{{- end -}}", start)].splitlines()[1:]
    entries = yaml.safe_load("\n".join(block))
    return {".".join(part for part in entry[:2] if part) for entry in entries}


def test_removed_keys_lists() -> None:
    """The chart, these tests and the upgrade notes list the same keys."""
    keys = {args[-1].split("=")[0] for args, _ in REMOVED}
    keys.discard("tesk.image")
    assert keys == _removed_keys_of_chart()
    upgrading = (CHART.parents[1] / "docs" / "upgrading.md").read_text()
    documented = {
        line.split("`")[1]
        for line in upgrading[upgrading.index("| Old name | New name |") :]
        .split("\n\n")[0]
        .splitlines()[2:]
    }
    documented.discard("tesk.image")
    assert documented == keys


def test_removed_keys_link() -> None:
    """The error links to the section of the upgrade notes that exists."""
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", "host_name=x")
    anchor = "resource-names-from-the-release-name"
    assert f"upgrading/#{anchor}" in error.value.stderr
    upgrading = (CHART.parents[1] / "docs" / "upgrading.md").read_text()
    assert "\n### Resource names from the release name\n" in upgrading


@pytest.mark.parametrize(
    ("value", "label"),
    [("tes--", "tes"), ("TESK", "TESK"), ("a_b.c", "a_b.c")],
)
def test_name_override_label(value: str, label: str) -> None:
    """`nameOverride` becomes the label, without trailing dashes.

    Args:
        value: The value of `nameOverride`.
        label: The expected label `app.kubernetes.io/name`.
    """
    manifests = render("--set", f"nameOverride={value}", "--set", "fullnameOverride=t")
    selector = deployment(manifests)["spec"]["selector"]["matchLabels"]
    assert selector["app.kubernetes.io/name"] == label


@pytest.mark.parametrize("value", ["a/b", "-a", "a b"])
def test_name_override_invalid(value: str) -> None:
    """A `nameOverride` that isn't a valid label value fails, with a hint.

    Args:
        value: The value of `nameOverride`.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", f"nameOverride={value}", "--set", "fullnameOverride=t")
    assert "isn't a valid label value" in error.value.stderr


def test_labels_numeric_release() -> None:
    """A release name or `nameOverride` that looks like a number is a string."""
    manifests = render(
        "--set", "fullnameOverride=tesk", "--set", "nameOverride=456", release="123"
    )
    for manifest in manifests:
        labels = manifest["metadata"]["labels"]
        assert labels["app.kubernetes.io/instance"] == "123"
        assert labels["app.kubernetes.io/name"] == "456"


@pytest.mark.parametrize(
    ("release", "args"),
    [
        ("123", ()),
        ("tesk.prod", ()),
        ("prod", ("--set", "fullnameOverride=Prod")),
        ("prod", ("--set", "nameOverride=TESK")),
    ],
)
def test_invalid_prefix(release: str, args: tuple[str, ...]) -> None:
    """A prefix that isn't a valid Service name fails, with a hint.

    Helm accepts release names that start with a digit or contain dots,
    which Service names can't.

    Args:
        release: The release name.
        args: More `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args, release=release)
    assert "isn't a valid Service name" in error.value.stderr
    assert "fullnameOverride" in error.value.stderr


def test_labels_openshift() -> None:
    """The OpenShift route has the standard labels too."""
    manifests = render(
        "--api-versions", "route.openshift.io/v1", "--set", "ingress.enabled=false"
    )
    labels = get(manifests, "Route", "tesk")["metadata"]["labels"]
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
        {"auth": {"legacyUserLabels": "true"}},
        {"global": {"anything": True}},
        {"ingress": {"className": 123}},
        {"tesk": {"resources": {"limits": {"nvidia.com/gpu": 1}}}},
        {"tesk": {"podSecurityContext": {"fsGroup": 2000}}},
        {"tesk": {"securityContext": {"readOnlyRootFilesystem": True}}},
        {"tesk": {"readinessProbe": {"initialDelaySeconds": 5}}},
        {"ingress": {"annotations": {"a.example.org/b": "c"}}},
    ],
)
def test_schema_permissive(values: dict[str, Any], tmp_path: Path) -> None:
    """The schema accepts strings for scalars, and keys of open maps.

    Open maps are those with Kubernetes' keys (e.g., resources, security
    contexts, probes, annotations), and `global`, which Helm passes on to
    all charts.

    Args:
        values: The values.
        tmp_path: A directory for the values file.
    """
    path = tmp_path / "values.yaml"
    path.write_text(json.dumps(values))
    assert render("--values", str(path))


@pytest.mark.parametrize(
    "key",
    [
        "hostname",
        "tesk.imagePullPolicy",
        "tesk.image.digest",
        "tesk.taskmaster.tag",
        "tesk.filer.image.pullPolicy",
        "tesk.executor.retries",
        "tesk.swaggerUi.enable",
        "transfer.pvc",
        "auth.envSubGroup",
        "auth.groups.delimiter",
        "auth.swaggerOauth.implicit",
        "auth.userInfoURI",
        "service.port",
        "ftp.hostIP",
        "ingress.tls",
    ],
)
def test_schema_unknown_keys(key: str) -> None:
    """The schema rejects unknown keys (e.g., typos) of the chart's own maps.

    Args:
        key: The unknown key.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--set", f"{key}=x")
    assert "values don't meet the specifications of the schema" in error.value.stderr
    assert "additional properties" in error.value.stderr.lower()


def test_schema_removed_keys() -> None:
    """The schema lets the removed keys through, for the chart's hints.

    The templates fail on them with their replacements (`test_removed_keys`);
    the schema describes them as removed.
    """
    schema = json.loads((CHART / "values.schema.json").read_text())
    for key in _removed_keys_of_chart():
        *maps, name = key.split(".")
        node = schema
        for part in maps:
            node = node["properties"][part]
        assert node["properties"][name] == {"$ref": "#/$defs/removed"}, key


def test_dependency(tmp_path: Path) -> None:
    """The chart renders as a dependency switched on by `condition: tesk.enabled`.

    Parent charts set `tesk.enabled`, and Helm passes it on to the chart,
    whose schema must accept it.

    Args:
        tmp_path: A directory for the parent chart.
    """
    parent = tmp_path / "parent"
    (parent / "charts").mkdir(parents=True)
    shutil.copytree(CHART, parent / "charts" / "tesk")
    (parent / "Chart.yaml").write_text(
        "apiVersion: v2\nname: parent\nversion: 0.1.0\n"
        "dependencies:\n  - name: tesk\n"
        f"    version: {METADATA['version']}\n    condition: tesk.enabled\n"
    )
    (parent / "values.yaml").write_text("tesk:\n  enabled: true\n")
    manifests = render(chart=parent)
    assert find(manifests, "Deployment", "tesk-api") is not None
    (parent / "values.yaml").write_text("tesk:\n  enabled: false\n")
    assert render(chart=parent) == []


def test_file_names() -> None:
    """The chart's files have dashed names and the extension `.yaml`.

    Helm's conventions; the names of the partials (`_helpers.tpl`) start with
    an underscore.
    """
    for path in CHART.rglob("*"):
        if path.is_dir():
            continue
        name = path.name.removeprefix("_") if path.suffix == ".tpl" else path.name
        assert "_" not in name, path
        assert ".yml" not in name, path
    template = yaml.safe_load((CHART / "tls-secret.yaml-TEMPLATE").read_text())
    assert re.fullmatch(r"[a-z]([-a-z0-9]*[a-z0-9])?", template["metadata"]["name"])


# Without a tag, tesk-api's version is the chart's appVersion (major and
# minor; (0, 0) if it isn't a version)
_APP_VERSION = re.match(r"v?(\d+)\.(\d+)", str(METADATA["appVersion"]))
APP_VERSION = (int(_APP_VERSION[1]), int(_APP_VERSION[2])) if _APP_VERSION else (0, 0)
SECONDS = {
    "taskTtlSeconds": "TESK_API_TASKMASTER_ENVIRONMENT_TASK_TTL_SECONDS",
    "maxQueueSeconds": "TESK_API_TASKMASTER_ENVIRONMENT_TESK_MAX_QUEUE_SECONDS",
}


@pytest.mark.parametrize("key", list(SECONDS))
@pytest.mark.parametrize(
    "args",
    [(), ("--set", "{}="), ("--set", "{}=null"), ("--set-string", "{}=")],
)
def test_seconds_unset(key: str, args: tuple[str, ...]) -> None:
    """Unset or empty, the taskmasters get no variable (keep, wait forever).

    Args:
        key: The value under `tesk`.
        args: The `helm template` arguments, with `{}` for the value's path.
    """
    variables = env(render(*(arg.format(f"tesk.{key}") for arg in args)))
    assert SECONDS[key] not in variables


@pytest.mark.parametrize(
    ("key", "args", "expected"),
    [
        ("taskTtlSeconds", ("--set", "tesk.taskTtlSeconds=86400"), "86400"),
        ("taskTtlSeconds", ("--set", "tesk.taskTtlSeconds=0"), "0"),
        ("taskTtlSeconds", ("--set-string", "tesk.taskTtlSeconds=3600"), "3600"),
        (
            "taskTtlSeconds",
            ("--set", "tesk.taskTtlSeconds=2147483647"),
            "2147483647",
        ),
        ("maxQueueSeconds", ("--set", "tesk.maxQueueSeconds=3600"), "3600"),
        ("maxQueueSeconds", ("--set", "tesk.maxQueueSeconds=1"), "1"),
        ("maxQueueSeconds", ("--set-string", "tesk.maxQueueSeconds=0600"), "600"),
        (
            "taskTtlSeconds",
            ("--set-string", "tesk.taskTtlSeconds=0000000000086400"),
            "86400",
        ),
        ("taskTtlSeconds", ("--set-string", "tesk.taskTtlSeconds=000"), "0"),
    ],
)
def test_seconds(key: str, args: tuple[str, ...], expected: str) -> None:
    """Set, the value is passed on to the taskmasters as whole seconds.

    Args:
        key: The value under `tesk`.
        args: The `helm template` arguments.
        expected: The value of the environment variable.
    """
    assert env(render(*args))[SECONDS[key]] == expected


def test_seconds_values_file(tmp_path: Path) -> None:
    """Numbers in a values file (floats to Helm) are passed on as integers.

    Args:
        tmp_path: A directory for the values file.
    """
    values = tmp_path / "values.yaml"
    values.write_text(
        "tesk:\n  taskTtlSeconds: 2592000\n  maxQueueSeconds: 2147483647\n"
    )
    variables = env(render("-f", str(values)))
    assert variables[SECONDS["taskTtlSeconds"]] == "2592000"
    assert variables[SECONDS["maxQueueSeconds"]] == "2147483647"


@pytest.mark.parametrize(
    "value",
    ["true", "1.5", "-0.5", '{"a": 1}', "[1]"],
)
def test_seconds_invalid_without_schema(value: str) -> None:
    """Without the schema, the chart still fails on values that aren't seconds.

    Otherwise, e.g., `-0.5` would become a TTL of 0, which deletes every task
    as soon as it finishes.

    Args:
        value: The TTL, as JSON.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render("--skip-schema-validation", "--set-json", f"tesk.taskTtlSeconds={value}")
    assert "tesk.taskTtlSeconds must be whole seconds" in error.value.stderr


@pytest.mark.parametrize(
    "args",
    [
        ("--set", "tesk.taskTtlSeconds=-1"),
        ("--set", "tesk.taskTtlSeconds=1.5"),
        ("--set", "tesk.taskTtlSeconds=2147483648"),
        ("--set-string", "tesk.taskTtlSeconds=1h"),
        ("--set-string", "tesk.taskTtlSeconds=-1"),
        ("--set-json", "tesk.taskTtlSeconds=[]"),
        ("--set", "tesk.taskTtlSeconds=true"),
        ("--set", "tesk.maxQueueSeconds=0"),
        ("--set", "tesk.maxQueueSeconds=2147483648"),
        ("--set-string", "tesk.maxQueueSeconds=3600s"),
    ],
)
def test_seconds_invalid_schema(args: tuple[str, ...]) -> None:
    """The schema rejects values that aren't whole seconds in range.

    Args:
        args: The `helm template` arguments.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert "values don't meet the specifications of the schema" in error.value.stderr


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (
            ("--set-string", "tesk.taskTtlSeconds=2147483648"),
            "tesk.taskTtlSeconds must be whole seconds from 0 to 2147483647",
        ),
        (
            ("--set-string", "tesk.maxQueueSeconds=0"),
            "tesk.maxQueueSeconds must be whole seconds from 1 to 2147483647",
        ),
        (
            ("--set-string", "tesk.maxQueueSeconds=9999999999"),
            "tesk.maxQueueSeconds must be whole seconds from 1 to 2147483647",
        ),
        (
            ("--set-string", "tesk.taskTtlSeconds=99999999999999999999"),
            "tesk.taskTtlSeconds must be whole seconds from 0 to 2147483647",
        ),
        (
            ("--set-string", "tesk.maxQueueSeconds=0000"),
            "tesk.maxQueueSeconds must be whole seconds from 1 to 2147483647",
        ),
    ],
)
def test_seconds_invalid_range(args: tuple[str, ...], message: str) -> None:
    """Strings of digits out of range fail, as the taskmaster would ignore them.

    Args:
        args: The `helm template` arguments.
        message: The expected error.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert message in error.value.stderr


@pytest.mark.parametrize("key", list(SECONDS))
@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), False),
        (("--set", "tesk.taskmaster.image.tag=v0.10.6", *FILER_DEV), True),
        (("--set", "tesk.taskmaster.image.tag=0.10.6", *FILER_DEV), True),
        (("--set", "tesk.taskmaster.image.tag=v0.11.0"), False),
        (("--set", "tesk.taskmaster.image.tag=0.11.0"), False),
        (("--set", "tesk.taskmaster.image.tag=dev", *FILER_OLD), False),
        (("--set", "tesk.taskmaster.image.tag=dev"), False),
    ],
)
def test_notes_seconds_old_taskmaster(
    tmp_path: Path, key: str, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn if a value is set, but the taskmaster ignores it.

    Args:
        tmp_path: A directory for a copy of the chart.
        key: The value under `tesk`.
        args: Further `helm template` arguments (image tags).
        warned: Whether the notes warn.
    """
    text = notes("--set", f"tesk.{key}=3600", *args, tmp_path=tmp_path)
    assert (f"tesk.{key} is set, but tesk.taskmaster.image.tag" in text) is warned
    # Only the max queue time depends on the version of tesk-api
    if key == "taskTtlSeconds":
        assert "but tesk-api" not in text
    assert f"tesk.{key} is set" not in notes(tmp_path=tmp_path)


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), APP_VERSION < (1, 2)),
        (("--set", "tesk.image.tag=1.1.0"), True),
        (("--set", "tesk.image.tag=v1.1"), True),
        (("--set", "tesk.image.tag=1.1.1-rc.1"), True),
        (("--set", "tesk.image.tag=1.2.0-rc.1"), False),
        (("--set", "tesk.image.tag=1.2.0"), False),
        (("--set", "tesk.image.tag=dev"), False),
    ],
)
def test_notes_max_queue_old_api(
    tmp_path: Path, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn if the max queue time is set with tesk-api 1.1 or older.

    These report a task whose executor was deleted as `COMPLETE`.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: Further `helm template` arguments (image tags).
        warned: Whether the notes warn.
    """
    new_taskmaster = ("--set", "tesk.taskmaster.image.tag=0.11.0")
    text = notes(
        "--set", "tesk.maxQueueSeconds=3600", *new_taskmaster, *args, tmp_path=tmp_path
    )
    assert ("tesk.maxQueueSeconds is set, but tesk-api" in text) is warned


@pytest.mark.parametrize(
    ("args", "warned"),
    [
        ((), APP_VERSION < (1, 2)),
        (("--set", "tesk.image.tag=1.1.0"), True),
        (("--set", "tesk.image.tag=v1.1"), True),
        (("--set", "tesk.image.tag=1.2.0-rc.1"), False),
        (("--set", "tesk.image.tag=1.2.0"), False),
        (("--set", "tesk.image.tag=dev"), False),
        (("--set", "tesk.image.tag=1.1.0", "--set", "auth.mode=noauth"), False),
        (
            ("--set", "tesk.image.tag=1.1.0", "--set", "auth.legacyUserLabels=false"),
            False,
        ),
    ],
)
def test_notes_legacy_user_labels_old_api(
    tmp_path: Path, args: tuple[str, ...], warned: bool
) -> None:
    """The notes warn if `auth.legacyUserLabels` is on with tesk-api before 1.2.0.

    Those versions ignore the setting.

    Args:
        tmp_path: A directory for a copy of the chart.
        args: Further `helm template` arguments (image tag, mode, setting).
        warned: Whether the notes warn.
    """
    text = notes(
        "--set",
        "auth.mode=auth",
        "--set",
        "auth.legacyUserLabels=true",
        *args,
        tmp_path=tmp_path,
    )
    assert ("auth.legacyUserLabels is on, but tesk-api" in text) is warned
    assert "auth.legacyUserLabels is on" not in notes(tmp_path=tmp_path)


@pytest.mark.parametrize(
    ("group", "resource", "verbs"),
    [
        ("batch", "jobs", {"create", "delete", "get", "list", "patch"}),
        ("", "configmaps", {"create", "delete", "get"}),
    ],
)
def test_role_rights(group: str, resource: str, verbs: set[str]) -> None:
    """The API and the taskmasters (one service account) may manage their objects.

    tesk-api creates a task's job and then its ConfigMap, owned by the job,
    and deletes the job if the ConfigMap fails (tesk-api#117); deleting the
    ConfigMap needs `delete` where OwnerReferencesPermissionEnforcement is
    on. The taskmaster patches its own job with the TTL.

    Args:
        group: The API group.
        resource: The resource.
        verbs: The verbs that the role must grant.
    """
    manifests = render()
    assert (
        deployment(manifests)["spec"]["template"]["spec"]["serviceAccountName"]
        == "tesk-taskmaster"
    )
    granted = {
        verb
        for rule in get(manifests, "Role", "tesk-taskmaster")["rules"]
        if group in rule["apiGroups"] and resource in rule["resources"]
        for verb in rule["verbs"]
    }
    assert verbs <= granted


@pytest.mark.parametrize(
    ("taskmaster", "filer"),
    [
        ("0.11.0", "0.11.0"),
        ("v0.11.0", "0.11.0"),
        ("v0.10.6", "v0.10.6"),
        ("v0.10.2", "v0.10.6"),
        ("0.10.6", "v0.10.2"),
        ("dev", "0.11.0"),
        ("v0.10.6", "latest"),
    ],
)
def test_image_releases_match(taskmaster: str, filer: str) -> None:
    """Taskmaster and filer of the same release, or tags that aren't releases.

    Releases up to v0.10.6 could be mixed; tags that aren't release
    versions (e.g., `dev`) are not checked.

    Args:
        taskmaster: The tag of the taskmaster image.
        filer: The tag of the filer image.
    """
    variables = env(
        render(
            "--set",
            f"tesk.taskmaster.image.tag={taskmaster}",
            "--set",
            f"tesk.filer.image.tag={filer}",
        )
    )
    assert variables["TESK_API_TASKMASTER_IMAGE_VERSION"] == taskmaster
    assert variables["TESK_API_TASKMASTER_FILER_IMAGE_VERSION"] == filer


@pytest.mark.parametrize(
    ("args", "taskmaster", "filer"),
    [
        (("--set", "tesk.taskmaster.image.tag=v0.10.6"), "v0.10.6", "0.11.0"),
        (("--set", "tesk.filer.image.tag=0.10.6"), "0.11.0", "0.10.6"),
        (
            (
                "--set",
                "tesk.taskmaster.image.tag=0.12.0",
                "--set",
                "tesk.filer.image.tag=v0.11.0",
            ),
            "0.12.0",
            "v0.11.0",
        ),
    ],
)
def test_image_releases_mismatch(
    args: tuple[str, ...], taskmaster: str, filer: str
) -> None:
    """Taskmaster and filer of different releases from 0.11.0 on fail.

    The filer of 0.11.0 and later must be of the taskmaster's release.

    Args:
        args: Further `helm template` arguments (image tags).
        taskmaster: The taskmaster's tag that the message names.
        filer: The filer's tag that the message names.
    """
    with pytest.raises(subprocess.CalledProcessError) as error:
        render(*args)
    assert (
        f"tesk.taskmaster.image.tag ({taskmaster}) and tesk.filer.image.tag "
        f"({filer}) must be the same release" in error.value.stderr
    )
