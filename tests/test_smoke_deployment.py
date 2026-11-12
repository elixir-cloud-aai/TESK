"""Tests of the check script for deployed instances, `tests/smoke/deployment.sh`.

The script runs against a fake TES API in a thread, which follows tesk-api's
answers (states, logs, access control) closely enough for the script's
checks; the chart-install job of CI runs it against a real installation.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
from typing import Any
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/smoke/deployment.sh"
BASE = "/ga4gh/tes/v1"
TOKEN = "a-valid-token"  # noqa: S105

# Skipped locally without the tools, but not in CI, where the tests must run
pytestmark = pytest.mark.skipif(
    not all(shutil.which(tool) for tool in ("bash", "curl", "jq"))
    and not os.environ.get("CI"),
    reason="needs bash, curl and jq",
)


@dataclass
class FakeTes:
    """State and behaviour of the fake TES API.

    Attributes:
        auth: Whether the task endpoints need the token `TOKEN`.
        echo_states: The states of tasks that echo, one per poll; the last
            one stays.
        sleep_states: The states of tasks that sleep, likewise.
        stdout: The stdout of tasks that echo; None echoes their argument.
        cancellable: Whether cancelling a task ends it CANCELED.
        cancel_status: The HTTP status of the answer to a cancel.
        artifact: The artifact of the service info's type.
        service_info_public: Whether the service info needs no token (with
            `auth`).
        images: The executor images of the tasks created, in order.
        tasks: Tasks by identifier: their command and state.
        cancels: The identifiers of the tasks cancelled, in order.
        authorizations: The `Authorization` headers received.
    """

    auth: bool = False
    echo_states: list[str] = field(default_factory=lambda: ["RUNNING", "COMPLETE"])
    sleep_states: list[str] = field(default_factory=lambda: ["RUNNING"])
    stdout: str | None = None
    cancellable: bool = True
    cancel_status: int = 200
    artifact: str = "tes"
    service_info_public: bool = True
    images: list[str] = field(default_factory=list)
    tasks: dict[str, dict[str, Any]] = field(default_factory=dict)
    cancels: list[str] = field(default_factory=list)
    authorizations: list[str] = field(default_factory=list)


def _handler(fake: FakeTes) -> type[BaseHTTPRequestHandler]:
    """Build a request handler class for a fake TES API.

    Args:
        fake: The state and behaviour of the API.

    Returns:
        The handler class.
    """

    class Handler(BaseHTTPRequestHandler):
        """Handles the requests of the script."""

        def log_message(self, format: str, *args: Any) -> None:
            """Log nothing.

            Args:
                format: The message format.
                *args: The message arguments.
            """

        def _send(self, status: int, payload: Any = None) -> None:
            """Send a JSON response, or an empty one.

            Args:
                status: The HTTP status.
                payload: The JSON body; None sends no body.
            """
            data = b"" if payload is None else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self) -> bool:
            """Check the token, as tesk-api does with `auth.mode: auth`.

            Returns:
                Whether the request may go on; if not, a 401 was sent.
            """
            header = self.headers.get("Authorization", "")
            fake.authorizations.append(header)
            if not fake.auth or header == f"Bearer {TOKEN}":
                return True
            self._send(401, {"error": "unauthorized"})
            return False

        def do_GET(self) -> None:
            """Answer the service info, the task list and single tasks."""
            url = urlsplit(self.path)
            path = url.path.removeprefix(BASE)
            if path == "/service-info":
                if not fake.service_info_public and not self._authorized():
                    return
                self._send(
                    200,
                    {
                        "id": "org.example.tes",
                        "type": {
                            "group": "org.ga4gh",
                            "artifact": fake.artifact,
                            "version": "1.0.0",
                        },
                    },
                )
                return
            if not self._authorized():
                return
            if path == "/tasks":
                self._send(200, {"tasks": []})
                return
            task_id = path.removeprefix("/tasks/")
            task = fake.tasks[task_id]
            # Each poll moves a task on to its next state
            states = task["states"]
            answer: dict[str, Any] = {
                "id": task_id,
                "state": states[min(task["polls"], len(states) - 1)],
            }
            task["polls"] += 1
            if "view=FULL" in url.query:
                stdout = fake.stdout
                if stdout is None:
                    stdout = task["command"][1] + "\n"
                answer["logs"] = [{"logs": [{"exit_code": 0, "stdout": stdout}]}]
            self._send(200, answer)

        def do_POST(self) -> None:
            """Create and cancel tasks."""
            if not self._authorized():
                return
            path = urlsplit(self.path).path.removeprefix(BASE)
            if path == "/tasks":
                length = int(self.headers["Content-Length"])
                task = json.loads(self.rfile.read(length))
                task_id = f"task-{len(fake.tasks) + 1}"
                command = task["executors"][0]["command"]
                fake.images.append(task["executors"][0]["image"])
                states = fake.echo_states if command[0] == "echo" else fake.sleep_states
                fake.tasks[task_id] = {"command": command, "states": states, "polls": 0}
                self._send(200, {"id": task_id})
                return
            task_id = path.removeprefix("/tasks/").removesuffix(":cancel")
            fake.cancels.append(task_id)
            if fake.cancellable and fake.cancel_status == 200:
                fake.tasks[task_id].update(states=["CANCELED"], polls=0)
            self._send(fake.cancel_status)

    return Handler


@pytest.fixture
def fake() -> Iterator[tuple[FakeTes, str]]:
    """Serve a fake TES API on a free local port.

    Yields:
        The fake's state and the base URL of its TES API.
    """
    state = FakeTes()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, f"http://127.0.0.1:{server.server_port}{BASE}"
    finally:
        server.shutdown()
        server.server_close()


def _run(url: str, **env: str) -> subprocess.CompletedProcess[str]:
    """Run the script against a URL.

    Args:
        url: The base URL of the TES API.
        **env: Environment variables of the script, which replace those of
            the tests' environment (without `TOKEN`, `ALLOW_HTTP` and `IMAGE`).

    Returns:
        The finished process, with its output.
    """
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in {"TOKEN", "ALLOW_HTTP", "IMAGE"}
    }
    return subprocess.run(  # noqa: S603
        [str(SCRIPT), url],
        env={**environment, "TASK_TIMEOUT": "20", **env},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_passes_without_auth(fake: tuple[FakeTes, str]) -> None:
    """All checks pass on an instance without auth; auth checks are skipped."""
    state, url = fake
    result = _run(url)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "skip: access control (TOKEN isn't set)" in result.stdout
    assert "ok: task task-1 ended COMPLETE" in result.stdout
    assert "ok: task task-2 ended CANCELED" in result.stdout
    assert result.stdout.endswith("Deployment checks passed\n")
    assert state.cancels == ["task-2"]
    assert set(state.authorizations) == {""}


def test_passes_with_auth(fake: tuple[FakeTes, str]) -> None:
    """With TOKEN, requests without a valid token must be refused."""
    state, url = fake
    state.auth = True
    result = _run(url, TOKEN=TOKEN, ALLOW_HTTP="true")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: GET /tasks without a token is refused (401)" in result.stdout
    assert "ok: GET /tasks with an invalid token is refused (401)" in result.stdout
    assert "ok: GET /tasks with TOKEN answers (200)" in result.stdout
    assert result.stdout.endswith("Deployment checks passed\n")
    assert state.cancels == ["task-2"]
    assert TOKEN not in result.stdout + result.stderr
    # Only the two checks of the refusal go without the token
    assert state.authorizations.count("") == 1
    assert state.authorizations.count("Bearer not-a-token") == 1
    assert set(state.authorizations) == {"", "Bearer not-a-token", f"Bearer {TOKEN}"}


def test_fails_if_auth_is_not_enforced(fake: tuple[FakeTes, str]) -> None:
    """With TOKEN, an instance that answers without a token fails."""
    _, url = fake
    result = _run(url, TOKEN=TOKEN, ALLOW_HTTP="true")
    assert result.returncode == 1
    assert "status 200, expected 401" in result.stdout


def test_fails_without_token_if_auth_is_needed(fake: tuple[FakeTes, str]) -> None:
    """Without TOKEN, an instance with auth fails with a hint."""
    state, url = fake
    state.auth = True
    result = _run(url)
    assert result.returncode == 1
    assert "the instance needs a token; set TOKEN" in result.stdout
    assert not state.tasks


def test_refuses_token_over_http(fake: tuple[FakeTes, str]) -> None:
    """TOKEN isn't sent over plain HTTP unless ALLOW_HTTP is true."""
    state, url = fake
    result = _run(url, TOKEN=TOKEN)
    assert result.returncode == 1
    assert "isn't an HTTPS URL" in result.stdout
    assert not state.authorizations


def test_rejects_invalid_timeout(fake: tuple[FakeTes, str]) -> None:
    """TASK_TIMEOUT must be a positive number."""
    _, url = fake
    result = _run(url, TASK_TIMEOUT="soon")
    assert result.returncode == 1
    assert "TASK_TIMEOUT must be a positive number of seconds" in result.stdout


def test_fails_without_response() -> None:
    """A URL that doesn't answer fails at the service info."""
    # A port that was free a moment ago, so that nothing listens on it
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    result = _run(f"http://127.0.0.1:{port}/ga4gh/tes/v1")
    assert result.returncode == 1
    assert "GET /service-info: status 000, expected 200" in result.stdout


def test_fails_on_other_service_info(fake: tuple[FakeTes, str]) -> None:
    """The service info must be that of a TES."""
    state, url = fake
    state.artifact = "wes"
    result = _run(url)
    assert result.returncode == 1
    assert "GET /service-info: the response doesn't match" in result.stdout
    assert '"artifact": "wes"' in result.stdout


def test_fails_if_task_fails(fake: tuple[FakeTes, str]) -> None:
    """A task that ends in another state fails, with the task."""
    state, url = fake
    state.echo_states = ["RUNNING", "EXECUTOR_ERROR"]
    result = _run(url)
    assert result.returncode == 1
    assert "task task-1 ended EXECUTOR_ERROR, expected COMPLETE" in result.stdout
    assert '"state": "EXECUTOR_ERROR"' in result.stdout
    assert not state.cancels


def test_fails_on_other_output(fake: tuple[FakeTes, str]) -> None:
    """A task without the expected output in its logs fails."""
    state, url = fake
    state.stdout = "something else\n"
    result = _run(url)
    assert result.returncode == 1
    assert "?view=FULL: the response doesn't match" in result.stdout


def test_cancels_first_task_on_timeout(fake: tuple[FakeTes, str]) -> None:
    """A task that doesn't complete in time fails, and is cancelled."""
    state, url = fake
    state.echo_states = ["RUNNING"]
    result = _run(url, TASK_TIMEOUT="3")
    assert result.returncode == 1
    assert "task task-1 is RUNNING after 3 s, expected COMPLETE" in result.stdout
    assert "Cancelling task task-1" in result.stdout
    assert state.cancels == ["task-1"]
    assert list(state.tasks) == ["task-1"]


def test_cancels_task_on_timeout(fake: tuple[FakeTes, str]) -> None:
    """A task that isn't cancelled in time fails, and is cancelled again."""
    state, url = fake
    state.cancellable = False
    result = _run(url, TASK_TIMEOUT="3")
    assert result.returncode == 1
    assert "task task-2 is RUNNING after 3 s, expected CANCELED" in result.stdout
    assert "Cancelling task task-2" in result.stdout
    assert state.cancels == ["task-2", "task-2"]


def test_waits_through_transient_states(fake: tuple[FakeTes, str]) -> None:
    """INITIALIZING, QUEUED and a SYSTEM_ERROR of a moment don't end a task."""
    state, url = fake
    state.echo_states = [
        "SYSTEM_ERROR",
        "QUEUED",
        "INITIALIZING",
        "RUNNING",
        "SYSTEM_ERROR",
        "COMPLETE",
    ]
    state.sleep_states = ["SYSTEM_ERROR", "INITIALIZING", "RUNNING"]
    result = _run(url)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ok: task task-1 ended COMPLETE" in result.stdout
    assert "ok: task task-2 ended CANCELED" in result.stdout


def test_fails_on_lasting_system_error(fake: tuple[FakeTes, str]) -> None:
    """A SYSTEM_ERROR that lasts ends the task, which isn't cancelled then."""
    state, url = fake
    state.echo_states = ["RUNNING", "SYSTEM_ERROR"]
    result = _run(url)
    assert result.returncode == 1
    assert "task task-1 ended SYSTEM_ERROR, expected COMPLETE" in result.stdout
    # It may still have pods
    assert state.cancels == ["task-1"]


def test_fails_if_cancel_is_refused(fake: tuple[FakeTes, str]) -> None:
    """A cancel that isn't accepted fails, and the task is cancelled again."""
    state, url = fake
    state.cancel_status = 400
    result = _run(url)
    assert result.returncode == 1
    assert "POST /tasks/task-2:cancel: status 400, expected 200" in result.stdout
    assert "POST /tasks/task-2:cancel: status 400; cancel the task" in result.stdout
    assert state.cancels == ["task-2", "task-2"]


def test_fails_if_cancelled_task_completes(fake: tuple[FakeTes, str]) -> None:
    """A task that ends COMPLETE despite the cancel fails."""
    state, url = fake
    state.cancellable = False
    state.sleep_states = ["RUNNING", "RUNNING", "COMPLETE"]
    result = _run(url)
    assert result.returncode == 1
    assert "task task-2 ended COMPLETE, expected CANCELED" in result.stdout
    assert state.cancels == ["task-2"]


def test_fails_without_token_if_service_info_needs_one(
    fake: tuple[FakeTes, str],
) -> None:
    """Without TOKEN, a service info that needs a token fails with a hint."""
    state, url = fake
    state.auth = True
    state.service_info_public = False
    result = _run(url)
    assert result.returncode == 1
    assert "GET /service-info: status 401: the instance needs a token" in result.stdout


def test_passes_with_private_service_info(fake: tuple[FakeTes, str]) -> None:
    """With TOKEN, the service info may need a token too."""
    state, url = fake
    state.auth = True
    state.service_info_public = False
    result = _run(url, TOKEN=TOKEN, ALLOW_HTTP="true")
    assert result.returncode == 0, result.stdout + result.stderr


def test_uses_image(fake: tuple[FakeTes, str]) -> None:
    """IMAGE replaces the image of the tasks."""
    state, url = fake
    result = _run(url, IMAGE="example.org/busybox:1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert state.images == ["example.org/busybox:1", "example.org/busybox:1"]
