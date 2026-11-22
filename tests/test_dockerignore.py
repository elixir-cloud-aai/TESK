"""Tests that no Docker build context of the repository sends secret files.

Every Dockerfile must be listed in `CONTEXTS` with its build context, and
the ignore files that Docker and buildah apply to that context must exclude
`.env` files (except `.env.example`) and other secret files at any depth,
so that they never reach an image or the cache of a build stage. The
repository root counts as a build context too (`docker build .`).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Each Dockerfile (relative to the root) with its build context: the
# directory that its build scripts send to Docker. Kept by hand: check the
# context against the build scripts when adding a Dockerfile
CONTEXTS = {
    # `source/tesk-core/dockerBuild` and `cloudbuild*.yaml` build from
    # `source/tesk-core`
    "source/tesk-core/containers/filer.Dockerfile": "source/tesk-core",
    "source/tesk-core/containers/taskmaster.Dockerfile": "source/tesk-core",
}

# Paths in any build context that must be excluded: at least one per rule
SECRETS = [
    ".env",
    ".env.local",
    "src/.env",
    "src/deep/.env.production",
    ".envrc",
    "src/.env_local",
    "src/.envs/prod",
    "src/.env.example/token",
    ".git/config",
    "src/.ssh/deploy_key",
    ".config/gcloud/application_default_credentials.json",
    "src/application_default_credentials.json",
    ".netrc",
    "src/.netrc",
    "src/.git-credentials",
    "src/.pypirc",
    "src/.npmrc",
    "src/.aws/credentials",
    "src/.docker/config.json",
    "src/.kube/config",
    "kubeconfig",
    "src/kind-kubeconfig",
    "src/cluster.kubeconfig",
    "tls.pem",
    "src/tls.key",
    "src/tls.crt",
    "src/client.p12",
    "src/client.pfx",
    "src/store.jks",
    "src/store.keystore",
    "id_rsa",
    "src/id_dsa",
    "src/id_ecdsa",
    "src/id_ed25519",
    "src/secrets.yaml",
    "src/secrets.yml",
    "src/tls-secret.yaml",
    "src/ftp-secret.yaml",
]

# Paths at the repository root that must be excluded, too: the files that
# the deployment docs have operators create in the checkout
ROOT_SECRETS = [
    "secrets.yaml",
    "charts/tesk/tls-secret.yaml",
    "charts/tesk/s3-config/config",
    "charts/tesk/s3-config/credentials",
]

# Paths in a build context that must still be sent
KEPT = [".env.example", "src/.env.example"]

# Paths at the repository root that must still be sent: the templates of
# the storage credentials
ROOT_KEPT = [
    "charts/tesk/s3-config/config-TEMPLATE",
    "charts/tesk/s3-config/credentials-TEMPLATE",
]

# Names of Dockerfiles (compared in lower case): `Dockerfile`,
# `Dockerfile.dev`, `Dockerfile-dev`, `app.Dockerfile`, and the same for
# `Containerfile`
_DOCKERFILE_NAME = re.compile(r"(?:.+\.)?(?:docker|container)file(?:[.-].+)?")


def _is_dockerfile(name: str) -> bool:
    """Tell whether a file name is the name of a Dockerfile.

    Args:
        name: The file name.

    Returns:
        Whether it names a Dockerfile (not an ignore file).
    """
    lower = name.lower()
    return not lower.endswith((".dockerignore", ".containerignore")) and bool(
        _DOCKERFILE_NAME.fullmatch(lower)
    )


def _dockerfiles() -> list[str]:
    """Return the Dockerfiles of the repository.

    Returns:
        The paths of the Dockerfiles that Git tracks, or would track
        (untracked, not ignored), relative to the root, sorted.
    """
    files = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\0")
    return sorted(
        path
        for path in filter(None, files)
        if _is_dockerfile(PurePosixPath(path).name) and (ROOT / path).is_file()
    )


def _pattern_regex(pattern: str) -> re.Pattern[str]:
    """Translate a `.dockerignore` pattern to a regular expression.

    It follows Docker's matching (`moby/patternmatcher`): `*` matches any
    characters but `/`, `?` one character but `/`, `**` any number of
    directories (any characters at the end of the pattern), `[...]` a
    character class (`[^...]` negated), and a backslash escapes the next
    character.

    Args:
        pattern: The pattern, without a leading `!`.

    Returns:
        The regular expression that matches the paths of the pattern.

    Raises:
        ValueError: If a character class isn't closed (Docker fails then).
    """
    pattern = pattern.strip("/")
    regex = ""
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern.startswith("**", index):
            index += 2
            if pattern.startswith("/", index):
                index += 1
            regex += ".*" if index == len(pattern) else "(?:.*/)?"
            continue
        if char == "*":
            regex += "[^/]*"
        elif char == "?":
            regex += "[^/]"
        elif char == "[":
            end = pattern.find("]", index + 1)
            if end == -1:
                raise ValueError(f"unclosed character class in {pattern!r}")
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
        # As `dockerignore.ReadAll`: comments start in the first column,
        # one `!` negates, and patterns are cleaned
        if line.startswith("#"):
            continue
        pattern = line.strip()
        if not pattern:
            continue
        excludes = not pattern.startswith("!")
        if not excludes:
            pattern = pattern[1:].strip()
        pattern = posixpath.normpath(pattern) if pattern else pattern
        rules.append((excludes, _pattern_regex(pattern)))
    return rules


def _excluded(rules: list[tuple[bool, re.Pattern[str]]], path: str) -> bool:
    """Tell whether Docker leaves a path out of the build context.

    The last rule that matches the path, or one of its parent directories,
    decides, as in Docker (a `!` rule re-includes a path below an excluded
    directory, unlike in Git).

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


def _ignore_files(dockerfile: str | None, context: str) -> list[Path]:
    """Return the ignore files that a build of a context may apply.

    Each builder applies one of them: BuildKit prefers
    `<Dockerfile>.dockerignore` next to the Dockerfile, buildah (which
    `dockerBuild` prefers) `.containerignore`, and all of them fall back to
    `.dockerignore` at the root of the context, which must exist.

    Args:
        dockerfile: The Dockerfile relative to the root, or `None` for a
            build of the context with its default Dockerfile.
        context: The build context relative to the root.

    Returns:
        The context's `.dockerignore` (which may not exist), then the other
        ignore files that exist.
    """
    candidates = [ROOT / context / ".containerignore"]
    if dockerfile is not None:
        candidates.append(ROOT / f"{dockerfile}.dockerignore")
    return [ROOT / context / ".dockerignore"] + [
        path for path in candidates if path.is_file()
    ]


BUILDS = [
    pytest.param(dockerfile, context, SECRETS, KEPT, id=dockerfile)
    for dockerfile, context in CONTEXTS.items()
] + [pytest.param(None, ".", SECRETS + ROOT_SECRETS, KEPT + ROOT_KEPT, id="root")]


def test_every_dockerfile_has_a_context() -> None:
    """Every Dockerfile is listed in `CONTEXTS`, and every listed one exists."""
    assert _dockerfiles() == sorted(CONTEXTS)


@pytest.mark.parametrize(("dockerfile", "context", "secrets", "kept"), BUILDS)
def test_context_excludes_secrets(
    dockerfile: str | None, context: str, secrets: list[str], kept: list[str]
) -> None:
    """The build context leaves out secret files and keeps `.env.example`.

    Args:
        dockerfile: The Dockerfile relative to the root, or `None`.
        context: The build context relative to the root.
        secrets: The paths that must be left out.
        kept: The paths that must be sent.
    """
    for ignore_file in _ignore_files(dockerfile, context):
        assert ignore_file.is_file(), f"{ignore_file} is missing"
        rules = _rules(ignore_file)
        sent = [path for path in secrets if not _excluded(rules, path)]
        assert not sent, f"{ignore_file} sends {sent}"
        dropped = [path for path in kept if _excluded(rules, path)]
        assert not dropped, f"{ignore_file} leaves out {dropped}"


@pytest.mark.parametrize(
    ("lines", "path", "excluded"),
    [
        (["*.env"], "a.env", True),
        (["*.env"], "src/a.env", False),
        (["**/.env*", "!**/.env.example"], "src/.env.example", False),
        (["**/.env*", "!**/.env.example"], "src/.envrc", True),
        (["src"], "src/deep/file", True),
        (["src", "!src/a"], "src/a", False),
        (["src", "!src/a"], "src/b", True),
        (["src/**"], "src/deep/file", True),
        (["src/**/"], "src/deep/file", True),
        (["**.pem"], "a/b.pem", False),
        (["**.pem"], "a/.pem", True),
        (["/src/*.py"], "src/a.py", True),
        (["src/?.py"], "src/ab.py", False),
        (["[^a]b"], "cb", True),
        (["[^a]b"], "ab", False),
        (["\\*"], "*", True),
        (["\\*"], "a", False),
        (["# comment", "", "  .netrc  "], ".netrc", True),
        (["  #x"], "#x", True),
        (["*", "!!a"], "!a", False),
        (["*", "!!a"], "a", True),
        (["./src/../x"], "x", True),
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


def test_matcher_unclosed_class() -> None:
    """A pattern with an unclosed character class is an error, as in Docker."""
    with pytest.raises(ValueError, match="unclosed character class"):
        _pattern_regex("[ab")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Dockerfile", True),
        ("dockerfile", True),
        ("Dockerfile.dev", True),
        ("Dockerfile-dev", True),
        ("filer.Dockerfile", True),
        ("dev.dockerfile", True),
        ("Containerfile", True),
        ("Containerfile-x", True),
        ("filer.Dockerfile.dockerignore", False),
        ("Dockerfile.dockerignore", False),
        ("README.md", False),
        ("dockerBuild", False),
        ("Dockerfiles", False),
    ],
)
def test_is_dockerfile(name: str, expected: bool) -> None:
    """Dockerfiles are recognized by name, in any case.

    Args:
        name: The file name.
        expected: Whether it names a Dockerfile.
    """
    assert _is_dockerfile(name) is expected


def test_ignore_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The ignore files that some builders prefer are checked, too.

    Args:
        tmp_path: A temporary directory as the repository root.
        monkeypatch: Replaces the repository root.
    """
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    (tmp_path / "ctx").mkdir()
    (tmp_path / "ctx/.dockerignore").touch()
    assert _ignore_files("ctx/app.Dockerfile", "ctx") == [
        tmp_path / "ctx/.dockerignore"
    ]
    (tmp_path / "ctx/app.Dockerfile.dockerignore").touch()
    (tmp_path / "ctx/.containerignore").touch()
    assert _ignore_files("ctx/app.Dockerfile", "ctx") == [
        tmp_path / "ctx/.dockerignore",
        tmp_path / "ctx/.containerignore",
        tmp_path / "ctx/app.Dockerfile.dockerignore",
    ]
    assert _ignore_files(None, "ctx") == [
        tmp_path / "ctx/.dockerignore",
        tmp_path / "ctx/.containerignore",
    ]
