"""Helpers for the tests of the Helm chart (`charts/tesk`)."""

from __future__ import annotations

import copy
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
# A copy of the chart before the values were renamed, and its default values,
# with the deprecated keys
LEGACY_CHART = Path(__file__).parent / "data" / "legacy-chart"
LEGACY_VALUES = LEGACY_CHART / "values.yaml"

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


def copy_chart(tmp_path: Path, values: Path | None = None) -> Path:
    """Copy the chart, e.g., to add files to it.

    Args:
        tmp_path: A directory for the copy; each call makes a new one in it.
        values: A file to replace the default values with (e.g., as
            `helm upgrade --reuse-values` replaces them with those of the
            installed chart).

    Returns:
        The copy.
    """
    chart = Path(tempfile.mkdtemp(dir=tmp_path)) / "tesk"
    shutil.copytree(CHART, chart)
    if values is not None:
        shutil.copyfile(values, chart / "values.yaml")
    return chart


def notes(*args: str, tmp_path: Path, values: Path | None = None) -> str:
    """Render the notes of the chart with `helm template` arguments.

    Args:
        args: Further arguments of `helm template`, e.g., `--set` options.
        tmp_path: A directory for a copy of the chart.
        values: A file to replace the default values with (see `copy_chart`).

    Returns:
        The notes, as `helm install` prints them (`templates/NOTES.txt` only
        includes the template rendered here).
    """
    chart = copy_chart(tmp_path, values)
    (chart / "templates" / "notes-test.yaml").write_text(_NOTES_TEMPLATE)
    configmap = get(render(*args, chart=chart), "ConfigMap", "notes")
    text: str = configmap["data"]["notes"]
    return text


def without_labels(manifests: list[Manifest]) -> list[Manifest]:
    """Remove the standard labels from rendered objects.

    Args:
        manifests: The rendered objects (not changed).

    Returns:
        Copies of the objects without the labels `app.kubernetes.io/*` and
        `helm.sh/chart` (and without empty label maps), to compare them with
        the objects of earlier versions of the chart, which had none.
    """
    manifests = copy.deepcopy(manifests)
    for manifest in manifests:
        metadatas = [manifest["metadata"]]
        template = manifest.get("spec", {}).get("template")
        if isinstance(template, dict):
            metadatas.append(template["metadata"])
        for metadata in metadatas:
            labels = {
                key: value
                for key, value in (metadata.get("labels") or {}).items()
                if not key.startswith(("app.kubernetes.io/", "helm.sh/"))
            }
            metadata.pop("labels", None)
            if labels:
                metadata["labels"] = labels
    return manifests


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
