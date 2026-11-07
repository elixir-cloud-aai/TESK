"""Helpers for the tests of the Helm chart (`charts/tesk`)."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import yaml

CHART = Path(__file__).parents[1] / "charts" / "tesk"
HELM = shutil.which("helm")
NAMESPACE = "tesk"
# The chart's default values and metadata
VALUES: dict[str, Any] = yaml.safe_load((CHART / "values.yaml").read_text())
METADATA: dict[str, Any] = yaml.safe_load((CHART / "Chart.yaml").read_text())

# A rendered Kubernetes object
Manifest = dict[str, Any]

# Renders the notes of the chart (`templates/NOTES.txt`, which `helm
# template` doesn't output) into a ConfigMap
_NOTES_TEMPLATE = """\
apiVersion: v1
kind: ConfigMap
metadata:
  name: notes
data:
  notes: |
{{ include "tesk.notes" . | indent 4 }}
"""


def render(*args: str, chart: Path = CHART, release: str = "tesk") -> list[Manifest]:
    """Render the chart with `helm template` arguments.

    Args:
        args: Further arguments of `helm template`, e.g., `--set` options.
        chart: The chart directory (e.g., a copy with added files).
        release: The name of the release.

    Returns:
        The rendered objects.
    """
    assert HELM is not None
    output = subprocess.run(  # noqa: S603 (fixed executable and arguments)
        [HELM, "template", release, str(chart), "--namespace", NAMESPACE, *args],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return [doc for doc in yaml.safe_load_all(output) if doc]


def copy_chart(tmp_path: Path) -> Path:
    """Copy the chart, e.g., to add files to it.

    Args:
        tmp_path: A directory for the copy; each call makes a new one in it.

    Returns:
        The copy.
    """
    chart = Path(tempfile.mkdtemp(dir=tmp_path)) / "tesk"
    shutil.copytree(CHART, chart)
    return chart


def notes(*args: str, tmp_path: Path) -> str:
    """Render the notes of the chart with `helm template` arguments.

    Args:
        args: Further arguments of `helm template`, e.g., `--set` options.
        tmp_path: A directory for a copy of the chart.

    Returns:
        The notes, as `helm install` prints them (`templates/NOTES.txt` only
        includes the template rendered here).
    """
    chart = copy_chart(tmp_path)
    (chart / "templates" / "notes-test.yaml").write_text(_NOTES_TEMPLATE)
    configmap = get(render(*args, chart=chart), "ConfigMap", "notes")
    text: str = configmap["data"]["notes"]
    return text


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


def deployment(manifests: list[Manifest]) -> Manifest:
    """Get the API's Deployment, the only one of the chart.

    Args:
        manifests: The rendered objects.

    Returns:
        The Deployment.
    """
    deployments = [m for m in manifests if m["kind"] == "Deployment"]
    assert len(deployments) == 1
    return deployments[0]


def container(manifests: list[Manifest]) -> dict[str, Any]:
    """Get the API container of the Deployment.

    Args:
        manifests: The rendered objects.

    Returns:
        The container.
    """
    pod = deployment(manifests)["spec"]["template"]["spec"]
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
