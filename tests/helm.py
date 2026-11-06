"""Helpers for the tests of the Helm chart (`charts/tesk`)."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

import yaml

CHART = Path(__file__).parents[1] / "charts" / "tesk"
HELM = shutil.which("helm")
NAMESPACE = "tesk"
# The chart's default values
VALUES: dict[str, Any] = yaml.safe_load((CHART / "values.yaml").read_text())

# A rendered Kubernetes object
Manifest = dict[str, Any]


def render(*args: str, chart: Path = CHART) -> list[Manifest]:
    """Render the chart with `helm template` arguments.

    Args:
        args: Further arguments of `helm template`, e.g., `--set` options.
        chart: The chart directory (e.g., a copy with added files).

    Returns:
        The rendered objects.
    """
    assert HELM is not None
    output = subprocess.run(  # noqa: S603 (fixed executable and arguments)
        [HELM, "template", "tesk", str(chart), "--namespace", NAMESPACE, *args],
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
        if manifest["kind"] == kind and manifest["metadata"]["name"] == name:
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
