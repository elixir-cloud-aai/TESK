"""Tests that no Docker build context of the repository sends secret files.

Every Dockerfile must be listed in `CONTEXTS` with its build context, and
the `.dockerignore` that Docker applies to that context must exclude
`.env` files (except `.env.example`) and other secret files at any depth,
so that they never reach an image or the cache of a build stage. The
repository root counts as a build context too (`docker build .`).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Each Dockerfile (relative to the root) with its build context: the
# directory that its build scripts send to Docker
CONTEXTS = {
    # `source/tesk-core/dockerBuild` and `cloudbuild.yaml` build from
    # `source/tesk-core`
    "source/tesk-core/containers/filer.Dockerfile": "source/tesk-core",
    "source/tesk-core/containers/taskmaster.Dockerfile": "source/tesk-core",
}

# Paths in a build context that must be excluded
SECRETS = [
    ".env",
    ".env.local",
    "src/.env",
    "src/deep/.env.production",
    ".netrc",
    "src/.netrc",
    "tls.pem",
    "src/tls.key",
    "id_rsa",
    "src/id_ed25519",
]

# Paths in a build context that must still be sent
KEPT = [".env.example", "src/.env.example"]


def _dockerfiles() -> list[str]:
    """Return the Dockerfiles of the repository.

    Returns:
        The paths of the Dockerfiles (`Dockerfile`, `Dockerfile.*`,
        `*.Dockerfile`, `Containerfile` and the like) that Git tracks, or
        would track (untracked, not ignored), relative to the root, sorted.
    """
    files = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    found = []
    for path in filter(None, files):
        name = PurePosixPath(path).name
        if name.endswith(".dockerignore") or not (ROOT / path).is_file():
            continue
        if (
            name in {"Dockerfile", "Containerfile"}
            or name.startswith(("Dockerfile.", "Containerfile."))
            or name.endswith((".Dockerfile", ".Containerfile"))
        ):
            found.append(path)
    return sorted(found)


def _pattern_regex(pattern: str) -> re.Pattern[str]:
    """Translate a `.dockerignore` pattern to a regular expression.

    It follows Docker's matching (`moby/patternmatcher`): `*` matches any
    characters but `/`, `?` one character but `/`, `**` any number of
    directories, `[...]` a character class (`[^...]` negated), and a
    backslash escapes the next character.

    Args:
        pattern: The pattern, without a leading `!`.

    Returns:
        The regular expression that matches the paths of the pattern.
    """
    pattern = pattern.strip("/")
    regex = ""
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**/", index):
            regex += "(?:.*/)?"
            index += 3
            continue
        if pattern.startswith("**", index):
            regex += ".*"
            index += 2
            continue
        if char == "*":
            regex += "[^/]*"
        elif char == "?":
            regex += "[^/]"
        elif char == "[":
            end = pattern.index("]", index + 1)
            regex += "[" + pattern[index + 1 : end] + "]"
            index = end
        elif char == "\\" and index + 1 < len(pattern):
            index += 1
            regex += re.escape(pattern[index])
        else:
            regex += re.escape(char)
        index += 1
    return re.compile(regex)


def _rules(ignore_file: Path) -> list[tuple[bool, re.Pattern[str]]]:
    """Read the rules of a `.dockerignore` file.

    Args:
        ignore_file: The file.

    Returns:
        For each pattern in order, whether it excludes (not `!`) and its
        regular expression.
    """
    rules = []
    for line in ignore_file.read_text().splitlines():
        pattern = line.strip()
        if not pattern or pattern.startswith("#"):
            continue
        excludes = not pattern.startswith("!")
        rules.append((excludes, _pattern_regex(pattern.lstrip("!").strip())))
    return rules


def _excluded(rules: list[tuple[bool, re.Pattern[str]]], path: str) -> bool:
    """Tell whether Docker leaves a path out of the build context.

    The last rule that matches the path, or one of its parent directories,
    decides, as in Docker.

    Args:
        rules: The rules of the `.dockerignore` file.
        path: The path, relative to the build context.

    Returns:
        Whether the path is excluded.
    """
    parts = path.split("/")
    prefixes = ["/".join(parts[: end + 1]) for end in range(len(parts))]
    excluded = False
    for excludes, regex in rules:
        if any(regex.fullmatch(prefix) for prefix in prefixes):
            excluded = excludes
    return excluded


def _ignore_file(dockerfile: str | None, context: str) -> Path:
    """Return the `.dockerignore` file that Docker applies to a build.

    BuildKit prefers `<Dockerfile>.dockerignore` next to the Dockerfile over
    the `.dockerignore` at the root of the build context.

    Args:
        dockerfile: The Dockerfile relative to the root, or `None` for a
            build of the context with its default Dockerfile.
        context: The build context relative to the root.

    Returns:
        The path of the file (which may not exist).
    """
    if dockerfile is not None:
        specific = ROOT / f"{dockerfile}.dockerignore"
        if specific.is_file():
            return specific
    return ROOT / context / ".dockerignore"


BUILDS = [*CONTEXTS.items(), (None, ".")]


def test_every_dockerfile_has_a_context() -> None:
    """Every Dockerfile is listed in `CONTEXTS`, and every listed one exists."""
    assert _dockerfiles() == sorted(CONTEXTS)


@pytest.mark.parametrize(("dockerfile", "context"), BUILDS)
def test_context_excludes_secrets(dockerfile: str | None, context: str) -> None:
    """The build context leaves out secret files and keeps `.env.example`.

    Args:
        dockerfile: The Dockerfile relative to the root, or `None`.
        context: The build context relative to the root.
    """
    ignore_file = _ignore_file(dockerfile, context)
    assert ignore_file.is_file(), f"{ignore_file} is missing"
    rules = _rules(ignore_file)
    sent = [path for path in SECRETS if not _excluded(rules, path)]
    assert not sent, f"{ignore_file} sends {sent}"
    dropped = [path for path in KEPT if _excluded(rules, path)]
    assert not dropped, f"{ignore_file} leaves out {dropped}"


@pytest.mark.parametrize(
    ("lines", "path", "excluded"),
    [
        (["*.env"], "a.env", True),
        (["*.env"], "src/a.env", False),
        (["**/.env*", "!**/.env.example"], "src/.env.example", False),
        (["**/.env*", "!**/.env.example"], "src/.envrc", True),
        (["src"], "src/deep/file", True),
        (["src/**"], "src/deep/file", True),
        (["/src/*.py"], "src/a.py", True),
        (["src/?.py"], "src/ab.py", False),
        (["[^a]b"], "cb", True),
        (["[^a]b"], "ab", False),
        (["\\*"], "*", True),
        (["\\*"], "a", False),
        (["# comment", "", "  .netrc  "], ".netrc", True),
        (["*", "!src/"], "src/a", False),
    ],
)
def test_matcher(lines: list[str], path: str, excluded: bool, tmp_path: Path) -> None:
    """The matcher follows Docker's rules for `.dockerignore` patterns.

    Args:
        lines: The lines of the `.dockerignore` file.
        path: The path to check, relative to the build context.
        excluded: Whether Docker leaves the path out.
        tmp_path: A temporary directory for the file.
    """
    ignore_file = tmp_path / ".dockerignore"
    ignore_file.write_text("\n".join(lines))
    assert _excluded(_rules(ignore_file), path) is excluded


def test_specific_ignore_file_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`<Dockerfile>.dockerignore` takes precedence over the context's file.

    Args:
        tmp_path: A temporary directory as the repository root.
        monkeypatch: Replaces the repository root.
    """
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    (tmp_path / "ctx").mkdir()
    (tmp_path / "ctx/.dockerignore").touch()
    assert _ignore_file("ctx/app.Dockerfile", "ctx") == tmp_path / "ctx/.dockerignore"
    (tmp_path / "ctx/app.Dockerfile.dockerignore").touch()
    assert (
        _ignore_file("ctx/app.Dockerfile", "ctx")
        == tmp_path / "ctx/app.Dockerfile.dockerignore"
    )
