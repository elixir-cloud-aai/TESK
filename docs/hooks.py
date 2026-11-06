"""MkDocs hooks: the docs of tesk-api and tesk-core, pulled into the site.

TESK's site covers TESK, tesk-api and tesk-core. Each of these repositories
keeps its own docs in its own `docs/`, built strictly in its own CI, and
publishes nothing itself. At build time, these hooks pull the `docs/` of each
repository listed in `docs-sources.yml` at the commit pinned there (a GitHub
tarball, over HTTPS), and add its pages to the site under `<name>/`, as the
nav section that the marker `external:<name>` stands for in `mkdocs.yml`
(e.g., `- tesk-core: external:tesk-core`). The section's pages and their
order come from the `nav` of the repository's own `mkdocs.yml`; without one,
its pages are listed in alphabetical order, `index.md` first. A source whose
`ref` is empty gets a placeholder page instead. "Edit" links of pulled pages
point to the page in its repository.

The pulled pages are built with TESK's `mkdocs.yml` (theme, Markdown
extensions and plugins), so they must not need others, and must not link to
files outside their `docs/`; see "Docs of tesk-api and tesk-core" in
`docs/development.md`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import time
from typing import Any, cast
import urllib.request

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
import yaml

LOGGER = logging.getLogger("mkdocs.hooks.external_docs")

# Next to `mkdocs.yml`
SOURCES = "docs-sources.yml"
MARKER = "external:"
ARCHIVE_URL = "https://codeload.github.com/{repository}/tar.gz/{ref}"
EDIT_URL = "https://github.com/{repository}/edit/{branch}/docs/{path}"
# Seconds: of each network operation, and of a whole download
TIMEOUT = 60
DEADLINE = 300
# Limits of a pulled repository, against runaway downloads and extraction:
# the size of the compressed tarball, and the number and total size of what
# is extracted from it (`docs/` and `mkdocs.yml`)
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_MEMBERS = 10_000
MAX_EXTRACTED_BYTES = 200 * 1024 * 1024

NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPOSITORY = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")

PLACEHOLDER = """# {name}

The documentation of {name} will appear here. It is kept in its repository,
[{repository}](https://github.com/{repository}), and pulled into this site
at a pinned commit.
"""


@dataclass(frozen=True)
class Source:
    """A repository whose docs are pulled into the site.

    Attributes:
        name: Directory of its pages in the site, and the name of its marker.
        repository: GitHub repository, as `<owner>/<name>`.
        ref: Full commit SHA of the docs to pull; empty for a placeholder.
        branch: Branch that "Edit" links of its pages point to.
    """

    name: str
    repository: str
    ref: str
    branch: str = "dev"


@dataclass
class Pulled:
    """Docs pulled from a source, or its placeholder.

    Attributes:
        source: Where the docs come from.
        root: Directory with the pulled `docs/`; `None` for a placeholder.
        nav: Nav of the section, with paths relative to the site's docs.
    """

    source: Source
    root: Path | None
    nav: list[Any]


# Pulled docs by source, kept across rebuilds of `mkdocs serve` and removed
# when MkDocs shuts down (`on_shutdown`)
_cache: dict[Source, Pulled] = {}
# Pulled docs of the current build, in the order of the sources file
_current: list[Pulled] = []


def load_sources(path: Path) -> list[Source]:
    """Read and check the list of sources.

    Args:
        path: The sources file (a mapping of names to `repository`, `ref` and
            optionally `branch`).

    Returns:
        The sources, in the order of the file.

    Raises:
        PluginError: If the file or an entry is invalid.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise PluginError(f"{path}: expected a mapping of names to sources")
    sources = []
    for name, entry in data.items():
        if not isinstance(entry, dict):
            raise PluginError(f"{path}: {name}: expected a mapping")
        repository = entry.get("repository")
        # Missing or null: no docs yet (`ref`), or the default branch
        ref = entry.get("ref")
        ref = "" if ref is None else ref
        branch = entry.get("branch")
        branch = "dev" if branch is None else branch
        if not isinstance(name, str) or not NAME.match(name):
            raise PluginError(f"{path}: invalid name {name!r}")
        if not isinstance(repository, str) or not REPOSITORY.match(repository):
            raise PluginError(f"{path}: {name}: invalid repository {repository!r}")
        if not isinstance(ref, str) or (ref and not COMMIT.match(ref)):
            raise PluginError(
                f"{path}: {name}: `ref` must be a full commit SHA or empty"
            )
        if not isinstance(branch, str) or not branch:
            raise PluginError(f"{path}: {name}: invalid branch {branch!r}")
        sources.append(Source(name, repository, ref, branch))
    return sources


def download(url: str, target: Path) -> None:
    """Download a file.

    Args:
        url: HTTPS URL of the file.
        target: Where to save it.

    Raises:
        PluginError: If the URL is not HTTPS, the download fails, takes
            longer than `DEADLINE`, or the file is larger than
            `MAX_ARCHIVE_BYTES`.
    """
    if not url.startswith("https://"):
        raise PluginError(f"Refusing to download {url}: not HTTPS")
    deadline = time.monotonic() + DEADLINE
    try:
        with (
            urllib.request.urlopen(url, timeout=TIMEOUT) as response,  # noqa: S310
            target.open("wb") as file,
        ):
            while chunk := response.read(1024 * 1024):
                if file.tell() + len(chunk) > MAX_ARCHIVE_BYTES:
                    raise PluginError(f"{url}: larger than {MAX_ARCHIVE_BYTES} bytes")
                if time.monotonic() > deadline:
                    raise PluginError(f"{url}: took longer than {DEADLINE} s")
                file.write(chunk)
    except OSError as error:
        raise PluginError(f"Could not download {url}: {error}") from error


def extract_docs(archive: Path, target: Path) -> None:
    """Extract `docs/` and `mkdocs.yml` of a repository tarball.

    The tarball has a single top-level directory (`<repo>-<ref>/`), which is
    dropped. Only regular files and directories are extracted, with the
    `data` filter, which rejects absolute paths and paths leaving `target`.

    Args:
        archive: The tarball (gzip-compressed).
        target: Directory to extract into.

    Raises:
        PluginError: If the extracted files and directories are more than
            `MAX_MEMBERS` or larger than `MAX_EXTRACTED_BYTES` in total, or
            if the repository has no `docs/`.
    """
    with tarfile.open(archive, "r:gz") as tar:
        members = []
        size = 0
        for member in tar:
            parts = member.name.split("/", 1)
            if len(parts) < 2 or not (member.isfile() or member.isdir()):
                continue
            path = parts[1]
            if path == "mkdocs.yml" or path.startswith("docs/"):
                member.name = path
                members.append(member)
                size += member.size
                if len(members) > MAX_MEMBERS:
                    raise PluginError(
                        f"{archive.name}: more than {MAX_MEMBERS} docs files"
                    )
                if size > MAX_EXTRACTED_BYTES:
                    raise PluginError(
                        f"{archive.name}: docs larger than {MAX_EXTRACTED_BYTES} bytes"
                    )
        if not any(member.name.startswith("docs/") for member in members):
            raise PluginError(f"{archive.name}: no `docs/` in the repository")
        tar.extractall(target, members=members, filter="data")


def _ignore_tags(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> Any:
    """Load a node with an unknown tag (e.g., `!ENV`) as plain YAML.

    Args:
        loader: The YAML loader.
        suffix: The tag.
        node: The node.

    Returns:
        The node's value, without the tag.
    """
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(cast(yaml.MappingNode, node))


class _Loader(yaml.SafeLoader):
    """Safe YAML loader that tolerates MkDocs' tags in `mkdocs.yml`."""


_Loader.add_multi_constructor("!", _ignore_tags)
_Loader.add_multi_constructor("tag:yaml.org,2002:python/", _ignore_tags)


def prefix_nav(nav: Any, prefix: str) -> Any:
    """Prefix the page paths of a nav with a directory.

    Args:
        nav: A nav as in `mkdocs.yml`: a page path, a mapping of titles to
            paths or sections, or a list of these. URLs are left as they are.
        prefix: Directory to prepend, e.g., `tesk-core`.

    Returns:
        The nav, with prefixed paths.
    """
    if isinstance(nav, list):
        return [prefix_nav(item, prefix) for item in nav]
    if isinstance(nav, dict):
        return {title: prefix_nav(value, prefix) for title, value in nav.items()}
    if isinstance(nav, str) and "://" not in nav:
        return f"{prefix}/{nav}"
    return nav


def section_nav(root: Path, name: str) -> list[Any]:
    """Get the nav of pulled docs.

    Args:
        root: Directory with the pulled `docs/` and `mkdocs.yml`.
        name: Name of the source, the directory of its pages in the site.

    Returns:
        The nav from the repository's `mkdocs.yml`, or of all its pages
        (alphabetically, `index.md` first) if it has none, with paths
        relative to the site's docs.
    """
    config = root / "mkdocs.yml"
    if config.is_file():
        data = yaml.load(config.read_text(encoding="utf-8"), Loader=_Loader)  # noqa: S506
        if isinstance(data, dict) and data.get("nav"):
            return cast(list[Any], prefix_nav(data["nav"], name))
    docs = root / "docs"
    pages = sorted(
        (path.relative_to(docs).as_posix() for path in docs.rglob("*.md")),
        key=lambda page: (page != "index.md", page),
    )
    return [f"{name}/{page}" for page in pages]


def pull(source: Source, fetch: Callable[[str, Path], None] = download) -> Pulled:
    """Pull the docs of a source, or make its placeholder.

    Args:
        source: The source.
        fetch: Downloads a URL to a file (for tests).

    Returns:
        The pulled docs, in a temporary directory that is removed on failure
        or when MkDocs shuts down.
    """
    if not source.ref:
        LOGGER.info("%s: no `ref` in %s, adding a placeholder", source.name, SOURCES)
        return Pulled(source, None, [f"{source.name}/index.md"])
    if source in _cache:
        return _cache[source]
    root = Path(tempfile.mkdtemp(prefix=f"tesk-docs-{source.name}-"))
    archive = root / "archive.tar.gz"
    url = ARCHIVE_URL.format(repository=source.repository, ref=source.ref)
    LOGGER.info("%s: pulling the docs of %s", source.name, url)
    try:
        fetch(url, archive)
        extract_docs(archive, root)
        archive.unlink()
        pulled = Pulled(source, root, section_nav(root, source.name))
    except BaseException:
        shutil.rmtree(root, ignore_errors=True)
        raise
    _cache[source] = pulled
    return pulled


def replace_markers(nav: Any, sections: dict[str, list[Any]]) -> Any:
    """Replace the markers of the nav with the sections of pulled docs.

    Args:
        nav: The site's nav.
        sections: Navs of the pulled docs, by source name.

    Returns:
        The nav with the sections.

    Raises:
        PluginError: If a marker names no source.
    """
    if isinstance(nav, list):
        return [replace_markers(item, sections) for item in nav]
    if isinstance(nav, dict):
        return {title: replace_markers(value, sections) for title, value in nav.items()}
    if isinstance(nav, str) and nav.startswith(MARKER):
        name = nav.removeprefix(MARKER)
        if name not in sections:
            raise PluginError(f"Nav marker {nav!r}: no such source in {SOURCES}")
        return sections[name]
    return nav


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    """Pull the docs of all sources and add their sections to the nav.

    The sources file is read from the directory of `mkdocs.yml`.

    Args:
        config: The MkDocs configuration.

    Returns:
        The configuration, with the sections in its nav.
    """
    sources = Path(config.config_file_path).parent / SOURCES
    _current.clear()
    _current.extend(pull(source) for source in load_sources(sources))
    sections = {pulled.source.name: pulled.nav for pulled in _current}
    config.nav = replace_markers(config.nav, sections)
    return config


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Add the pages and other files of the pulled docs to the site.

    Args:
        files: The site's files.
        config: The MkDocs configuration.

    Returns:
        The files, with the pulled ones.

    Raises:
        PluginError: If a pulled file or placeholder page is also a file of
            the site.
    """
    for pulled in _current:
        name = pulled.source.name
        if pulled.root is None:
            uri = f"{name}/index.md"
            if files.get_file_from_path(uri) is not None:
                raise PluginError(f"{uri}: placeholder page is also a file of the site")
            content = PLACEHOLDER.format(name=name, repository=pulled.source.repository)
            files.append(File.generated(config, uri, content=content))
            continue
        docs = pulled.root / "docs"
        for path in sorted(docs.rglob("*")):
            if (
                not path.is_file()
                or path.suffix == ".py"
                or "__pycache__" in path.parts
            ):
                continue
            uri = f"{name}/{path.relative_to(docs).as_posix()}"
            if files.get_file_from_path(uri) is not None:
                raise PluginError(f"{uri}: pulled file is also a file of the site")
            files.append(File.generated(config, uri, abs_src_path=str(path)))
    return files


def on_page_markdown(
    markdown: str, page: Page, config: MkDocsConfig, files: Files
) -> str:
    """Point the "Edit" link of a pulled page to its repository.

    Placeholder pages get none, as their source isn't in any repository.

    Args:
        markdown: The page's Markdown, unchanged.
        page: The page.
        config: The MkDocs configuration.
        files: The site's files.

    Returns:
        The Markdown, unchanged.
    """
    for pulled in _current:
        prefix = f"{pulled.source.name}/"
        if not page.file.src_uri.startswith(prefix):
            continue
        if pulled.root is None:
            page.edit_url = None
        else:
            page.edit_url = EDIT_URL.format(
                repository=pulled.source.repository,
                branch=pulled.source.branch,
                path=page.file.src_uri.removeprefix(prefix),
            )
    return markdown


def on_shutdown() -> None:
    """Remove the temporary directories of the pulled docs."""
    for pulled in _cache.values():
        # Only pulled docs are cached, but the type allows placeholders
        if pulled.root is not None:
            shutil.rmtree(pulled.root, ignore_errors=True)
    _cache.clear()
    _current.clear()
