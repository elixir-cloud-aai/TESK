"""Tests of the check of the inputs filer's job, `tests/smoke/check-filer.sh`.

The script reads the Jobs of a namespace as `kubectl get jobs -o json` prints
them; the chart-install job of CI runs it against a real installation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/smoke/check-filer.sh"

# Skipped locally without the tools, but not in CI, where the tests must run
pytestmark = pytest.mark.skipif(
    not all(shutil.which(tool) for tool in ("bash", "jq")) and not os.environ.get("CI"),
    reason="needs bash and jq",
)


def _job(name: str, succeeded: int | None = 1) -> dict[str, Any]:
    """Build a Job as the taskmaster of tesk-core 0.12.0 creates it.

    Args:
        name: The name of the Job.
        succeeded: The number of its pods that succeeded; None leaves the
            field out, as Kubernetes does before the first one.

    Returns:
        The Job, with the filer's default security contexts.
    """
    job: dict[str, Any] = {
        "metadata": {"name": name},
        "status": {},
        "spec": {
            "template": {
                "spec": {
                    "securityContext": {
                        "runAsNonRoot": True,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "filer",
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "capabilities": {"drop": ["ALL"]},
                                "readOnlyRootFilesystem": True,
                            },
                        }
                    ],
                }
            }
        },
    }
    if succeeded is not None:
        job["status"]["succeeded"] = succeeded
    return job


def _run(*jobs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    """Run the script on a list of Jobs.

    Args:
        *jobs: The Jobs of the namespace.

    Returns:
        The finished process, with its output.
    """
    return subprocess.run(  # noqa: S603
        [str(SCRIPT)],
        input=json.dumps({"items": list(jobs)}),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_passes_with_hardened_filer() -> None:
    """A completed inputs filer with the default contexts passes."""
    executor = _job("task-1-ex-00")
    executor["spec"]["template"]["spec"]["securityContext"] = {}
    result = _run(_job("task-0"), executor, _job("task-1-inputs-filer"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"name":"task-1-inputs-filer"' in result.stdout
    assert "task-1-ex-00" not in result.stdout
    assert "ok: the inputs filer completed" in result.stdout


def test_fails_without_filer() -> None:
    """Without an inputs filer job (no task with inputs ran), it fails."""
    result = _run(_job("task-1"), _job("task-1-ex-00"))
    assert result.returncode == 1
    assert "::error::No completed inputs filer job" in result.stdout


def test_fails_if_filer_did_not_complete() -> None:
    """An inputs filer job without a succeeded pod fails."""
    result = _run(_job("task-1-inputs-filer", succeeded=None))
    assert result.returncode == 1
    assert "::error::" in result.stdout


@pytest.mark.parametrize(
    ("part", "field", "value"),
    [
        ("pod", "runAsNonRoot", False),
        ("pod", "seccompProfile", None),
        ("container", "readOnlyRootFilesystem", False),
        ("container", "allowPrivilegeEscalation", True),
        ("container", "capabilities", {"drop": ["NET_RAW"]}),
        ("container", "capabilities", None),
    ],
)
def test_fails_without_hardening(part: str, field: str, value: Any) -> None:
    """A filer without one of its hardened defaults fails.

    Args:
        part: `pod` or `container`, the security context to change.
        field: The field of the security context.
        value: Its new value; None removes it.
    """
    job = _job("task-1-inputs-filer")
    spec = job["spec"]["template"]["spec"]
    context = (
        spec["securityContext"]
        if part == "pod"
        else spec["containers"][0]["securityContext"]
    )
    if value is None:
        del context[field]
    else:
        context[field] = value
    result = _run(_job("task-0-inputs-filer"), job)
    assert result.returncode == 1
    assert "::error::" in result.stdout
