"""Tests of the MkDocs hooks that pull the docs of tesk-api and tesk-core."""

from __future__ import annotations

from collections.abc import Callable, Iterator
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import tarfile
from types import ModuleType
from typing import Any

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
import pytest

ROOT = Path(__file__).resolve().parents[1]
SHA = "0123456789abcdef0123456789abcdef01234567"


def _load_hooks() -> ModuleType:
    """Load `docs/hooks.py` (not a package) as a module.

    Returns:
        The hooks module.
    """
    spec = importlib.util.spec_from_file_location("hooks", ROOT / "docs/hooks.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["hooks"] = module
    spec.loader.exec_module(module)
    return module


hooks = _load_hooks()


def _tarball(path: Path, files: dict[str, bytes], top: str = "repo-sha") -> None:
    """Write a gzip-compressed tarball like GitHub's.

    Args:
        path: Where to write it.
        files: Contents by path, relative to the top-level directory.
        top: The top-level directory.
    """
    with tarfile.open(path, "w:gz") as tar:
        directory = tarfile.TarInfo(top)
        directory.type = tarfile.DIRTYPE
        tar.addfile(directory)
        for name, content in files.items():
            info = tarfile.TarInfo(f"{top}/{name}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))


@pytest.fixture(autouse=True)
def _clear_state() -> Iterator[None]:
    """Clear the hooks' cache and pulled docs around each test.

    Yields:
        Nothing.
    """
    hooks._cache.clear()
    hooks._current.clear()
    yield
    for pulled in hooks._cache.values():
        if pulled.root is not None:
            shutil.rmtree(pulled.root, ignore_errors=True)
    hooks._cache.clear()
    hooks._current.clear()


@pytest.fixture
def config(tmp_path: Path) -> MkDocsConfig:
    """MkDocs configuration with an empty docs directory.

    Args:
        tmp_path: Temporary directory.

    Returns:
        The configuration.
    """
    (tmp_path / "docs").mkdir()
    cfg = MkDocsConfig(config_file_path=str(tmp_path / "mkdocs.yml"))
    cfg.load_dict(
        {
            "site_name": "Test",
            "docs_dir": str(tmp_path / "docs"),
            "site_dir": str(tmp_path / "site"),
            "nav": ["index.md", {"tesk-core": "external:tesk-core"}],
        }
    )
    errors, _ = cfg.validate()
    assert not errors
    # Set by MkDocs while it runs a plugin's or hook's events; generated
    # files record it
    cfg.plugins._current_plugin = "hooks"
    return cfg


def _sources(tmp_path: Path, text: str) -> Path:
    """Write a sources file.

    Args:
        tmp_path: Temporary directory.
        text: Contents of the file.

    Returns:
        Path of the file.
    """
    path = tmp_path / "docs-sources.yml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_sources(tmp_path: Path) -> None:
    """Sources are read in order, with the default branch."""
    path = _sources(
        tmp_path,
        f"tesk-api:\n  repository: a/b\n  ref: ''\n"
        f"tesk-core:\n  repository: c/d\n  ref: {SHA}\n  branch: main\n",
    )
    assert hooks.load_sources(path) == [
        hooks.Source("tesk-api", "a/b", "", "dev"),
        hooks.Source("tesk-core", "c/d", SHA, "main"),
    ]


def test_load_sources_empty(tmp_path: Path) -> None:
    """An empty file has no sources."""
    assert hooks.load_sources(_sources(tmp_path, "")) == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("- a\n", "expected a mapping of names"),
        ("x: 1\n", "expected a mapping"),
        ("Bad_Name:\n  repository: a/b\n", "invalid name"),
        ("x:\n  repository: nope\n", "invalid repository"),
        ("x:\n  repository: a/b\n  ref: main\n", "full commit SHA"),
        ("x:\n  repository: a/b\n  branch: 1\n", "invalid branch"),
    ],
)
def test_load_sources_invalid(tmp_path: Path, text: str, message: str) -> None:
    """Invalid files and entries fail the build."""
    with pytest.raises(PluginError, match=message):
        hooks.load_sources(_sources(tmp_path, text))


def test_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Downloads write the response to the file."""

    def urlopen(url: str, timeout: int) -> io.BytesIO:
        assert url == "https://example.org/x"
        assert timeout == hooks.TIMEOUT
        return io.BytesIO(b"data")

    monkeypatch.setattr(hooks.urllib.request, "urlopen", urlopen)
    target = tmp_path / "x"
    hooks.download("https://example.org/x", target)
    assert target.read_bytes() == b"data"


def test_download_not_https(tmp_path: Path) -> None:
    """Only HTTPS URLs are downloaded."""
    with pytest.raises(PluginError, match="not HTTPS"):
        hooks.download("http://example.org/x", tmp_path / "x")


def test_download_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failed downloads fail the build."""

    def urlopen(url: str, timeout: int) -> io.BytesIO:
        raise OSError("offline")

    monkeypatch.setattr(hooks.urllib.request, "urlopen", urlopen)
    with pytest.raises(PluginError, match="offline"):
        hooks.download("https://example.org/x", tmp_path / "x")


def test_extract_docs(tmp_path: Path) -> None:
    """Only `docs/` and `mkdocs.yml` are extracted, without the top directory."""
    archive = tmp_path / "a.tar.gz"
    _tarball(
        archive,
        {"docs/index.md": b"# A", "mkdocs.yml": b"nav: []", "src/x.py": b"x"},
    )
    target = tmp_path / "out"
    hooks.extract_docs(archive, target)
    assert (target / "docs/index.md").read_text() == "# A"
    assert (target / "mkdocs.yml").is_file()
    assert not (target / "src").exists()


def test_extract_docs_links_skipped(tmp_path: Path) -> None:
    """Links in the tarball are not extracted."""
    archive = tmp_path / "a.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("repo-sha/docs/index.md")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
        link = tarfile.TarInfo("repo-sha/docs/link.md")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        tar.addfile(link)
    hooks.extract_docs(archive, tmp_path / "out")
    assert not (tmp_path / "out/docs/link.md").exists()


def test_extract_docs_without_docs(tmp_path: Path) -> None:
    """Repositories without `docs/` fail the build."""
    archive = tmp_path / "a.tar.gz"
    _tarball(archive, {"README.md": b"x"})
    with pytest.raises(PluginError, match="no `docs/`"):
        hooks.extract_docs(archive, tmp_path / "out")


def test_prefix_nav() -> None:
    """Page paths are prefixed; URLs and other values are kept."""
    nav = [
        "index.md",
        {"A": "a.md"},
        {"S": ["b.md", {"Ext": "https://example.org/"}]},
        1,
    ]
    assert hooks.prefix_nav(nav, "p") == [
        "p/index.md",
        {"A": "p/a.md"},
        {"S": ["p/b.md", {"Ext": "https://example.org/"}]},
        1,
    ]


def test_section_nav_from_config(tmp_path: Path) -> None:
    """The nav comes from the repository's `mkdocs.yml`, despite its tags."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "mkdocs.yml").write_text(
        "site_url: !ENV [X, 'https://x/']\n"
        "extra: !!python/name:os.getcwd\n"
        "seq: !custom [1]\n"
        "map: !custom {a: 1}\n"
        "nav:\n  - Home: index.md\n  - b.md\n",
        encoding="utf-8",
    )
    assert hooks.section_nav(tmp_path, "c") == [{"Home": "c/index.md"}, "c/b.md"]


def test_section_nav_without_config(tmp_path: Path) -> None:
    """Without a nav, all pages are listed, `index.md` first."""
    docs = tmp_path / "docs"
    (docs / "sub").mkdir(parents=True)
    for name in ("b.md", "index.md", "a.md", "sub/c.md", "image.png"):
        (docs / name).write_text("x", encoding="utf-8")
    (tmp_path / "mkdocs.yml").write_text("site_name: x\n", encoding="utf-8")
    assert hooks.section_nav(tmp_path, "c") == [
        "c/index.md",
        "c/a.md",
        "c/b.md",
        "c/sub/c.md",
    ]


def test_pull_placeholder() -> None:
    """Sources without `ref` get a placeholder page."""
    pulled = hooks.pull(hooks.Source("x", "a/b", ""))
    assert pulled.root is None
    assert pulled.nav == ["x/index.md"]


def test_pull(tmp_path: Path) -> None:
    """The pinned commit is pulled once, and cached."""
    urls = []

    def fetch(url: str, target: Path) -> None:
        urls.append(url)
        _tarball(target, {"docs/index.md": b"# Core"})

    source = hooks.Source("tesk-core", "o/r", SHA)
    pulled = hooks.pull(source, fetch)
    assert hooks.pull(source, fetch) is pulled
    assert urls == [f"https://codeload.github.com/o/r/tar.gz/{SHA}"]
    assert pulled.root is not None
    assert (pulled.root / "docs/index.md").read_text() == "# Core"
    assert not (pulled.root / "archive.tar.gz").exists()
    assert pulled.nav == ["tesk-core/index.md"]


def test_replace_markers() -> None:
    """Markers are replaced with the sections; other entries are kept."""
    nav = ["index.md", {"Core": "external:core"}, {"S": ["a.md"]}]
    assert hooks.replace_markers(nav, {"core": ["core/index.md"]}) == [
        "index.md",
        {"Core": ["core/index.md"]},
        {"S": ["a.md"]},
    ]


def test_replace_markers_unknown() -> None:
    """Markers without a source fail the build."""
    with pytest.raises(PluginError, match="no such source"):
        hooks.replace_markers(["external:nope"], {})


def _pulled(tmp_path: Path, files: dict[str, str]) -> Any:
    """Make pulled docs of `tesk-core` from files.

    Args:
        tmp_path: Temporary directory.
        files: Contents by path, relative to `docs/`.

    Returns:
        The pulled docs.
    """
    root = tmp_path / "pulled"
    for name, content in files.items():
        path = root / "docs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    source = hooks.Source("tesk-core", "o/r", SHA)
    return hooks.Pulled(source, root, ["tesk-core/index.md"])


def test_on_config(config: MkDocsConfig, tmp_path: Path) -> None:
    """The nav gets the sections of the sources next to `mkdocs.yml`."""
    _sources(tmp_path, "tesk-core:\n  repository: o/r\n  ref: ''\n")
    result = hooks.on_config(config)
    assert result.nav == ["index.md", {"tesk-core": ["tesk-core/index.md"]}]
    assert [pulled.source.name for pulled in hooks._current] == ["tesk-core"]


def test_on_files_placeholder(config: MkDocsConfig) -> None:
    """Placeholders are generated pages naming the repository."""
    hooks._current.append(hooks.pull(hooks.Source("tesk-core", "o/r", "")))
    files = hooks.on_files(Files([]), config)
    page = files.get_file_from_path("tesk-core/index.md")
    assert page is not None
    assert "o/r" in page.content_string


def test_on_files(config: MkDocsConfig, tmp_path: Path) -> None:
    """Pulled files are added, except Python files and bytecode."""
    hooks._current.append(
        _pulled(
            tmp_path,
            {
                "index.md": "# Core",
                "images/a.png": "png",
                "hooks.py": "x",
                "__pycache__/x.txt": "x",
            },
        )
    )
    files = hooks.on_files(Files([]), config)
    assert sorted(file.src_uri for file in files) == [
        "tesk-core/images/a.png",
        "tesk-core/index.md",
    ]


def test_on_files_conflict(config: MkDocsConfig, tmp_path: Path) -> None:
    """Pulled files must not replace files of the site."""
    hooks._current.append(_pulled(tmp_path, {"index.md": "# Core"}))
    existing = File.generated(config, "tesk-core/index.md", content="# Mine")
    with pytest.raises(PluginError, match="also a file of the site"):
        hooks.on_files(Files([existing]), config)


def _page(config: MkDocsConfig, uri: str) -> Page:
    """Make a page.

    Args:
        config: The MkDocs configuration.
        uri: Source path of the page.

    Returns:
        The page.
    """
    page = Page(None, File.generated(config, uri, content="# X"), config)
    page.edit_url = "https://github.com/elixir-cloud-aai/TESK/edit/dev/docs/x"
    return page


def test_on_page_markdown(config: MkDocsConfig, tmp_path: Path) -> None:
    """Pulled pages link to their repository for editing; others don't change."""
    hooks._current.append(_pulled(tmp_path, {"index.md": "# Core"}))
    pulled = _page(config, "tesk-core/sub/a.md")
    own = _page(config, "index.md")
    assert hooks.on_page_markdown("# X", pulled, config, Files([])) == "# X"
    hooks.on_page_markdown("# X", own, config, Files([]))
    assert pulled.edit_url == "https://github.com/o/r/edit/dev/docs/sub/a.md"
    assert own.edit_url == "https://github.com/elixir-cloud-aai/TESK/edit/dev/docs/x"


def test_on_page_markdown_placeholder(config: MkDocsConfig) -> None:
    """Placeholder pages have no "Edit" link."""
    hooks._current.append(hooks.pull(hooks.Source("tesk-core", "o/r", "")))
    page = _page(config, "tesk-core/index.md")
    hooks.on_page_markdown("# X", page, config, Files([]))
    assert page.edit_url is None


class _Response(io.BytesIO):
    """Response of a fake `urlopen`, usable as a context manager."""


def test_download_too_large(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Downloads larger than the limit fail the build."""
    monkeypatch.setattr(hooks, "MAX_ARCHIVE_BYTES", 3)
    monkeypatch.setattr(
        hooks.urllib.request, "urlopen", lambda url, timeout: _Response(b"data")
    )
    with pytest.raises(PluginError, match="larger than 3 bytes"):
        hooks.download("https://example.org/x", tmp_path / "x")


def test_extract_docs_too_many_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """More docs files than the limit fail the build; others don't count."""
    monkeypatch.setattr(hooks, "MAX_MEMBERS", 2)
    archive = tmp_path / "a.tar.gz"
    _tarball(archive, {"src/x": b"x", "src/y": b"y", "docs/a.md": b"a"})
    hooks.extract_docs(archive, tmp_path / "ok")
    _tarball(archive, {"docs/a.md": b"a", "docs/b.md": b"b", "mkdocs.yml": b""})
    with pytest.raises(PluginError, match="more than 2 docs files"):
        hooks.extract_docs(archive, tmp_path / "out")


def test_extract_docs_too_large(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Docs larger than the limit fail the build; other files don't count."""
    monkeypatch.setattr(hooks, "MAX_EXTRACTED_BYTES", 3)
    archive = tmp_path / "a.tar.gz"
    _tarball(archive, {"src/big": b"0123456789", "docs/a.md": b"abc"})
    hooks.extract_docs(archive, tmp_path / "ok")
    _tarball(archive, {"docs/a.md": b"ab", "docs/b.md": b"cd"})
    with pytest.raises(PluginError, match="larger than 3 bytes"):
        hooks.extract_docs(archive, tmp_path / "out")


def _fetch_offline(url: str, target: Path) -> None:
    """Fail like a download without network.

    Args:
        url: Ignored.
        target: Ignored.

    Raises:
        PluginError: Always.
    """
    raise PluginError("offline")


def _fetch_without_docs(url: str, target: Path) -> None:
    """Fetch a tarball of a repository without `docs/`.

    Args:
        url: Ignored.
        target: Where to write the tarball.
    """
    _tarball(target, {"README.md": b"# Repo"})


@pytest.mark.parametrize(
    ("fetch", "error"),
    [(_fetch_offline, "offline"), (_fetch_without_docs, "no `docs/`")],
)
def test_pull_failure_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fetch: Callable[[str, Path], None],
    error: str,
) -> None:
    """A failed pull removes its temporary directory and caches nothing."""
    monkeypatch.setattr(hooks.tempfile, "tempdir", str(tmp_path))
    with pytest.raises(PluginError, match=error):
        hooks.pull(hooks.Source("tesk-core", "o/r", SHA), fetch)
    assert list(tmp_path.glob("tesk-docs-*")) == []
    assert hooks._cache == {}


def test_on_shutdown(tmp_path: Path) -> None:
    """Shutting down removes all pulled docs, also those not in use."""

    def fetch(url: str, target: Path) -> None:
        _tarball(target, {"docs/index.md": b"# Core"})

    pulled = hooks.pull(hooks.Source("tesk-core", "o/r", SHA), fetch)
    unused = hooks.pull(hooks.Source("tesk-core", "o/r", "0" * 40), fetch)
    hooks._current.append(pulled)
    assert pulled.root is not None
    assert unused.root is not None
    hooks.on_shutdown()
    assert not pulled.root.exists()
    assert not unused.root.exists()
    assert hooks._cache == {}
    assert hooks._current == []


def test_build_with_pulled_docs(
    config: MkDocsConfig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The events together pull a source and add its nav, pages and links."""
    _sources(tmp_path, f"tesk-core:\n  repository: o/r\n  ref: {SHA}\n")
    tarball = tmp_path / "core.tar.gz"
    _tarball(
        tarball,
        {
            "mkdocs.yml": b"nav:\n  - Home: index.md\n  - sub/a.md\n",
            "docs/index.md": b"# Core",
            "docs/sub/a.md": b"# A",
        },
    )
    monkeypatch.setattr(
        hooks.urllib.request,
        "urlopen",
        lambda url, timeout: _Response(tarball.read_bytes()),
    )
    hooks.on_config(config)
    assert config.nav == [
        "index.md",
        {"tesk-core": [{"Home": "tesk-core/index.md"}, "tesk-core/sub/a.md"]},
    ]
    files = hooks.on_files(Files([]), config)
    assert sorted(file.src_uri for file in files) == [
        "tesk-core/index.md",
        "tesk-core/sub/a.md",
    ]
    page = _page(config, "tesk-core/sub/a.md")
    hooks.on_page_markdown("# A", page, config, files)
    assert page.edit_url == "https://github.com/o/r/edit/dev/docs/sub/a.md"
