"""Tests of the release notes check and body (`scripts/release_notes.py`)."""

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/release_notes.py"

# `scripts/` is not a package, so the script is loaded from its file
_spec = importlib.util.spec_from_file_location("release_notes", SCRIPT)
assert _spec and _spec.loader
release_notes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_notes)

CURATED = """\
The release brings a feature. See the [upgrade
guide](https://example.org/upgrading/).

## Breaking changes

- A breaking change, described
  over two lines (#1, #2)
- Another one, with a lazy
continuation line (#3; #4, #5)

## Features

- A feature with an example (#6, #7):

  ```yaml
  key: value
  ## not a heading
  ```

  And more text about it (#8)
* A bullet with another marker (#9)

## Maintenance

1. A numbered item (#10)
"""

# As GitHub's `generate-notes` API returns them (`body`)
GENERATED = """\
## What's Changed
* feat: add a feature by @someone in https://github.com/o/r/pull/7
* fix: fix a bug by @newcomer in https://github.com/o/r/pull/11

## New Contributors
* @newcomer made their first contribution in https://github.com/o/r/pull/11

**Full Changelog**: https://github.com/o/r/compare/v0.2.0...v0.3.0"""


def _messages(markdown: str) -> list[tuple[int, str]]:
    """Return the line and the start of the message of each finding.

    Args:
        markdown: Curated release notes.

    Returns:
        Line and first three words of the message of each finding.
    """
    return [
        (finding.line, " ".join(finding.message.split()[:3]))
        for finding in release_notes.check(markdown)
    ]


@pytest.mark.parametrize(
    "markdown",
    [
        CURATED,
        # The intro alone, and sections with closing hashes
        "A fix release.\n",
        "Intro.\n\n## Fixes ##\n\n- Fix (#1)\n",
        # Code blocks in the intro, headings in code blocks
        "Intro.\n\n```text\n## Unknown\n```\n\n## Fixes\n\n- Fix (#1)\n",
        # Fences close only with the same character, at least as long, and
        # nothing else on the line
        "Intro.\n\n## Fixes\n\n- Fix (#1):\n\n  ````md\n  ```\n  ## No\n  ```\n"
        "  ````\n\n  More (#2)\n",
        "Intro.\n\n## Fixes\n\n- Fix (#1):\n\n  ```\n  ~~~\n  ``` x\n  ```\n\n"
        "  More (#2)\n",
        # HTML comments, and a byte order mark
        "<!-- Notes of 0.3.0 -->\nIntro.\n\n## Fixes\n\n<!-- comment -->\n- Fix (#1)\n",
        "\ufeffIntro.\n\n## Fixes\n\n- Fix (#1)\n",
        "Intro.\n\n## Fixes\n\n- Fix (#1)\n    <!-- c -->\n- Fix (#2)\n<!-- c -->\n",
        "Intro.\n\n## Fixes\n\n- Fix (#1)\n\n<!-- c -->\n\n- Fix (#2)\n",
        # Code blocks may show the generated parts
        "Intro.\n\n```md\n**Full Changelog**: https://x/compare/a...b\n```\n",
        # Numbers wrapped over lines
        "Intro.\n\n## Fixes\n\n- Fix (#1,\n  #2; #3,\n  #4)\n",
        # Hashes that are no headings
        "Intro.\n\n## Fixes\n\n- Fix of\n#12 (#13)\n",
    ],
)
def test_check_valid(markdown: str) -> None:
    """Notes in the agreed format have no findings."""
    assert release_notes.check(markdown) == []


@pytest.mark.parametrize(
    ("markdown", "messages"),
    [
        # No intro
        ("", [(1, "No intro paragraph")]),
        ("<!-- comment -->\n", [(1, "No intro paragraph")]),
        # Lists and code blocks are no intro paragraph
        ("- Item\n\n## Fixes\n\n- Fix (#1)\n", [(3, "No intro paragraph")]),
        ("```\ncode\n```\n\n## Fixes\n\n- Fix (#1)\n", [(5, "No intro paragraph")]),
        (
            "<!-- a --> Intro <!-- b -->\n\n## Fixes\n\n- Fix (#1)\n",
            [],
        ),
        (
            "<!-- comment -->\n## Fixes\n\n- Fix (#1)\n",
            [(2, "No intro paragraph")],
        ),
        ("\ufeff## Fixes\n\n- Fix (#1)\n", [(1, "No intro paragraph")]),
        ("\n\n", [(2, "No intro paragraph")]),
        (
            "## Fixes\n\n- Fix (#1)\n",
            [(1, "No intro paragraph")],
        ),
        # Other headings
        (
            "# Cloud Registry 0.3.0\n\nIntro.\n",
            [(1, "Heading of level"), (1, "No intro paragraph")],
        ),
        (
            "Intro.\n\n## Fixes\n\n### API\n\n- Fix (#1)\n",
            [(3, "Empty section"), (5, "Heading of level")],
        ),
        (
            "Intro.\n\n## New features\n\n- Feature (#1)\n",
            [(3, "Unknown section 'New")],
        ),
        (
            "Intro.\n\n#\n",
            [(3, "Heading of level")],
        ),
        # Setext headings and thematic breaks
        ("Intro\n===\n", [(2, "Setext heading or")]),
        ("Intro.\n\n## Fixes\n\n- Fix (#1)\n\n---\n", [(7, "Setext heading or")]),
        ("Intro.\n\n***\n", [(3, "Setext heading or")]),
        # Order, duplicates and empty sections
        (
            "Intro.\n\n## Fixes\n\n- Fix (#1)\n\n## Features\n\n- Feature (#2)\n",
            [(7, "Section 'Features' after")],
        ),
        (
            "Intro.\n\n## Fixes\n\n- Fix (#1)\n\n## Fixes\n\n- Fix (#2)\n",
            [(7, "Section 'Fixes' after")],
        ),
        (
            "Intro.\n\n## Fixes\n\n## Maintenance\n\n- Chore (#1)\n",
            [(3, "Empty section")],
        ),
        ("Intro.\n\n## Fixes\n", [(3, "Empty section")]),
        # Parts that the release workflow adds
        (
            "Intro.\n\n## Commits\n\n* fix by @a in https://x/pull/1\n",
            [(3, "Section 'Commits': the")],
        ),
        (
            "Intro.\n\n**Full Changelog**: https://x/compare/a...b\n",
            [(3, "'**Full Changelog**' line:")],
        ),
        # Sections hold bullets only
        (
            "Intro.\n\n## Fixes\n\n- Fix (#1)\n\nA paragraph.\n",
            [(7, "Sections hold bullets")],
        ),
        (
            "Intro.\n\n## Fixes\n\nA paragraph.\n\n- Fix (#1)\n",
            [(5, "Sections hold bullets")],
        ),
        (
            "Intro.\n\n## Fixes\n\n```\ncode\n```\n\n- Fix (#1)\n",
            [(5, "Sections hold bullets")],
        ),
        # Bullets end with their issue and pull request numbers
        (
            "Intro.\n\n## Fixes\n\n- Fix\n- Fix (#1).\n- Fix (#1) more\n"
            "- Fix (1, 2)\n- Fix (#a)\n- Fix #1\n",
            [
                (5, "Bullet doesn't end"),
                (6, "Bullet doesn't end"),
                (7, "Bullet doesn't end"),
                (8, "Bullet doesn't end"),
                (9, "Bullet doesn't end"),
                (10, "Bullet doesn't end"),
            ],
        ),
        (
            "Intro.\n\n## Fixes\n\n- Fix (#1):\n\n  More text.\n",
            [(7, "Bullet doesn't end")],
        ),
        # Unclosed code blocks
        (
            "Intro.\n\n## Fixes\n\n- Fix (#1)\n\n  ```\n  code\n",
            [(8, "Bullet doesn't end"), (8, "Unclosed fenced code")],
        ),
    ],
)
def test_check_invalid(markdown: str, messages: list[tuple[int, str]]) -> None:
    """Notes that differ from the agreed format have findings."""
    assert _messages(markdown) == messages


@pytest.mark.parametrize("notes", sorted((ROOT / "docs/releases").glob("*.md")))
def test_curated_notes(notes: Path) -> None:
    """The curated notes in the repository are in the agreed format."""
    assert release_notes.check(notes.read_text(encoding="utf-8")) == []


def test_body() -> None:
    """The body is the curated notes, then the generated ones, without header."""
    text, warnings = release_notes.body(CURATED, GENERATED)
    assert text == (
        f"{CURATED.strip()}\n\n## Commits\n\n"
        f"{GENERATED.removeprefix("## What's Changed\n")}\n"
    )
    assert text.endswith(
        "\n\n**Full Changelog**: https://github.com/o/r/compare/v0.2.0...v0.3.0\n"
    )
    assert "What's Changed" not in text
    assert warnings == []


def test_body_comment() -> None:
    """The header is also dropped after a comment (e.g., of a configuration)."""
    generated = f"<!-- Release notes generated using configuration -->\n\n{GENERATED}"
    text, warnings = release_notes.body("Intro.\n", generated)
    assert text.startswith(
        "Intro.\n\n## Commits\n\n<!-- Release notes generated using configuration"
        " -->\n\n* feat: add a feature"
    )
    assert "What's Changed" not in text
    assert warnings == []


def test_body_no_changes() -> None:
    """Without changes in the generated notes, the body has no `Commits`."""
    generated = "**Full Changelog**: https://github.com/o/r/commits/v0.3.0\n"
    assert release_notes.body("Intro.\n", generated) == (
        "Intro.\n\n**Full Changelog**: https://github.com/o/r/commits/v0.3.0\n",
        [],
    )


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_body_crlf(newline: str) -> None:
    """Generated notes with CRLF or CR line endings are normalized.

    Args:
        newline: Line ending of the generated notes.
    """
    generated = GENERATED.replace("\n", newline) + newline
    assert release_notes.body(CURATED, generated) == release_notes.body(
        CURATED, GENERATED
    )


@pytest.mark.parametrize(
    ("generated", "commits"),
    [
        ("", ""),
        (
            "## What's Changed\n* fix by @a in https://x/pull/1\n",
            "\n\n## Commits\n\n* fix by @a in https://x/pull/1",
        ),
        (
            "**Full Changelog**: https://x/commits/v1\n\nMore text.\n",
            "\n\n## Commits\n\n**Full Changelog**: https://x/commits/v1\n\nMore text.",
        ),
    ],
)
def test_body_unexpected_generated(generated: str, commits: str) -> None:
    """Generated notes without a final `**Full Changelog**` line are kept."""
    assert release_notes.body("Intro.\n", generated) == (
        f"Intro.{commits}\n",
        ["Generated notes don't end with a '**Full Changelog**: ' line"],
    )


def test_main_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`check` passes for notes in the agreed format."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text(CURATED, encoding="utf-8")
    assert release_notes.main(["check", str(notes)]) == 0
    assert capsys.readouterr() == ("", "")


def test_main_check_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`check` prints findings as error annotations."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text("Intro.\n\n## Fixes\n", encoding="utf-8")
    assert release_notes.main(["check", str(notes)]) == 1
    assert capsys.readouterr() == ("", f"::error file={notes},line=3::Empty section\n")


@pytest.mark.parametrize("command", ["check", "body"])
def test_main_unreadable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    """Files that can't be read fail with an error annotation."""
    notes = tmp_path / "0.3.0.md"
    args = [command, str(notes)] + (
        [str(tmp_path / "x.md")] if command == "body" else []
    )
    assert release_notes.main(args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("::error::Can't read the notes: ")


def test_main_body(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`body` prints the body of the release."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text(CURATED, encoding="utf-8")
    generated = tmp_path / "generated.md"
    generated.write_text(GENERATED, encoding="utf-8")
    assert release_notes.main(["body", str(notes), str(generated)]) == 0
    assert capsys.readouterr() == (release_notes.body(CURATED, GENERATED)[0], "")


def test_main_body_findings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`body` fails without output if the curated notes have findings."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text("## Fixes\n\n- Fix (#1)\n", encoding="utf-8")
    generated = tmp_path / "generated.md"
    generated.write_text(GENERATED, encoding="utf-8")
    assert release_notes.main(["body", str(notes), str(generated)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "No intro paragraph" in captured.err


def test_main_body_unexpected_generated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`body` warns of unexpected generated notes, and keeps them."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text("Intro.\n", encoding="utf-8")
    generated = tmp_path / "generated.md"
    generated.write_text("Changes.\n", encoding="utf-8")
    assert release_notes.main(["body", str(notes), str(generated)]) == 0
    assert capsys.readouterr() == (
        "Intro.\n\n## Commits\n\nChanges.\n",
        "::warning::Generated notes don't end with a '**Full Changelog**: ' line;"
        " kept as they are\n",
    )


@pytest.mark.parametrize(
    "files",
    [
        # no notes at all: still required
        [],
        # notes of other releases, or other files, don't count
        ["0.2.0.md", "0.4.0.md"],
        ["0.3.0-rc.1.md", "README.md", "draft-0.3.0.md"],
    ],
)
def test_missing_notes(tmp_path: Path, files: list[str]) -> None:
    """Every release needs notes of its own version."""
    for name in files:
        (tmp_path / name).write_text(CURATED, encoding="utf-8")
    assert release_notes.missing_notes("0.3.0", tmp_path) == tmp_path / "0.3.0.md"
    (tmp_path / "0.3.0.md").write_text(CURATED, encoding="utf-8")
    assert release_notes.missing_notes("0.3.0", tmp_path) is None


def test_missing_notes_without_directory(tmp_path: Path) -> None:
    """Without a directory of notes, the notes are missing."""
    releases = tmp_path / "releases"
    assert release_notes.missing_notes("0.3.0", releases) == releases / "0.3.0.md"


@pytest.mark.parametrize("version", ["0.3.0", "1.0.0-alpha.0", "1.2.3-rc.10"])
def test_missing_notes_versions(tmp_path: Path, version: str) -> None:
    """Release versions, also of pre-releases, are accepted."""
    (tmp_path / f"{version}.md").write_text(CURATED, encoding="utf-8")
    assert release_notes.missing_notes(version, tmp_path) is None


@pytest.mark.parametrize(
    "version", ["0.3", "v0.3.0", "0.3.0rc1", "0.3.0-rc1", "01.2.3", "../0.3.0", ""]
)
def test_missing_notes_invalid_version(tmp_path: Path, version: str) -> None:
    """Versions that the release workflow doesn't accept fail."""
    with pytest.raises(ValueError, match="is not a release version"):
        release_notes.missing_notes(version, tmp_path)


def test_main_require(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """`require` fails with an error annotation if the notes are missing."""
    args = ["require", "0.3.0", "--releases", str(tmp_path)]
    assert release_notes.main(args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"::error::{tmp_path / '0.3.0.md'} is missing")
    (tmp_path / "0.3.0.md").write_text(CURATED, encoding="utf-8")
    assert release_notes.main(args) == 0
    assert capsys.readouterr() == ("", "")


def test_main_require_invalid_version(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`require` fails with an error annotation for an invalid version."""
    args = ["require", "v0.3.0", "--releases", str(tmp_path)]
    assert release_notes.main(args) == 1
    assert capsys.readouterr() == (
        "",
        "::error::'v0.3.0' is not a release version (e.g., 1.2.3)\n",
    )


def test_main_require_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """`require` reads the notes in `docs/releases/` by default."""
    releases = tmp_path / "docs" / "releases"
    releases.mkdir(parents=True)
    (releases / "0.3.0.md").write_text(CURATED, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert release_notes.main(["require", "0.3.1"]) == 1
    assert release_notes.main(["require", "0.3.0"]) == 0


@pytest.mark.parametrize(
    "markdown",
    [
        "Intro. TODO: link the upgrade notes.\n",
        "Intro.\n\n<!-- TODO -->\n",
        "Intro.\n\n## Fixes\n\n- A fix, TODO (#1)\n",
    ],
)
def test_check_todo(markdown: str) -> None:
    """Unfinished notes (with `TODO`, also in a comment) have a finding."""
    line = next(
        number
        for number, text in enumerate(markdown.splitlines(), start=1)
        if "TODO" in text
    )
    assert _messages(markdown) == [(line, "TODO: finish the")]


def test_script(tmp_path: Path) -> None:
    """The script runs as the release workflow calls it."""
    notes = tmp_path / "0.3.0.md"
    notes.write_text(CURATED, encoding="utf-8")
    generated = tmp_path / "generated.md"
    generated.write_text(GENERATED, encoding="utf-8")
    result = subprocess.run(  # noqa: S603 (fixed arguments, no shell)
        [sys.executable, "-I", str(SCRIPT), "body", str(notes), str(generated)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        release_notes.body(CURATED, GENERATED)[0],
        "",
    )


@pytest.mark.parametrize(
    "link",
    [
        "https://tesk.readthedocs.io/en/latest/upgrading/",
        "https://tesk.readthedocs.io/en/stable/",
        "https://tesk.readthedocs.io/latest/",
        "https://tesk.readthedocs.io",
        "https://tesk.readthedocs.io/",
        "https://tesk.readthedocs.io/en/",
        "https://tesk.readthedocs.io/upgrading/",
        "https://tesk.readthedocs.io/#releases",
        "https://github.com/elixir-cloud-aai/TESK/blob/dev/README.md",
        "https://github.com/elixir-cloud-aai/TESK/compare/main...v0.3.0",
        "https://github.com/elixir-cloud-aai/TESK/compare/v0.2...dev",
        "https://github.com/elixir-cloud-aai/TESK/compare/v0.2..HEAD",
        "https://github.com/elixir-cloud-aai/tesk/tree/main/docs",
        "https://github.com/elixir-cloud-aai/TESK/releases/latest",
        "https://raw.githubusercontent.com/elixir-cloud-aai/TESK/dev/x",
    ],
)
def test_check_moving_links(link: str) -> None:
    """Links to versions that move are rejected, also in sections."""
    markdown = f"Intro, [docs]({link}).\n\n## Fixes\n\n- Fix, see <{link}> (#1)\n"
    assert _messages(markdown) == [(1, "Link to a"), (5, "Link to a")]


@pytest.mark.parametrize(
    "link",
    [
        "https://tesk.readthedocs.io/en/v0.3.0/upgrading/",
        "https://tesk.readthedocs.io/en/0.3.0/",
        "https://github.com/elixir-cloud-aai/TESK/blob/v0.3.0/README.md",
        "https://github.com/elixir-cloud-aai/TESK/compare/v0.2...v0.3.0",
        "https://github.com/elixir-cloud-aai/TESK/compare/dev-notes...v0.3.0",
        "https://github.com/elixir-cloud-aai/TESK/compare/v0.2...main-notes",
        "https://github.com/elixir-cloud-aai/TESK/tree/dev-notes/docs",
        "https://github.com/elixir-cloud-aai/tesk-api/releases/tag/v1.2.0",
        "https://example.org/en/latest/",
    ],
)
def test_check_versioned_links(link: str) -> None:
    """Links to a release, and other sites' links, are accepted."""
    assert release_notes.check(f"Intro, [docs]({link}).\n") == []


def test_body_splits_at_line_breaks_only() -> None:
    """Other line separators (e.g., U+2028) in generated notes start no line."""
    generated = "* x\u2028## Security by @a in u\n\n**Full Changelog**: c\n"
    text, warnings = release_notes.body("Intro.\n", generated)
    assert "\n## Security" not in text
    assert warnings == []
