"""Check curated release notes and build the body of a GitHub release.

Ported from cloud-registry's `scripts/release_notes.py`. Release notes
follow the format agreed for all repositories of the organization (see
"Releases" in `docs/development.md`):

1. An intro paragraph saying what the release brings, with a link to the
   upgrade or migration guide if there is one.
2. Grouped sections, in the order of `SECTIONS`, with empty ones left out;
   each bullet ends with its issue and pull request numbers, e.g.,
   `(#12, #34)`.
3. `## Commits`: GitHub's generated notes, verbatim (including "New
   Contributors"), without their `## What's Changed` header.
4. Last, GitHub's generated `**Full Changelog**: ...` line.

The release body never changes, so curated notes must not link to versions
that move (`UNVERSIONED`, e.g., the latest docs or branch `dev`), but to the
release's (e.g., `/en/vX.Y.Z/`, `blob/vX.Y.Z/`), and must be finished (no
`TODO`).

The curated notes (`docs/releases/<version>.md`) hold parts 1 and 2; every
release needs them. The release workflow (`.github/workflows/release.yml`)
adds parts 3 and 4 from GitHub's `generate-notes` API, since the previous
release, which every release has (the first one of the workflow follows
`v0.2`).

Commands:
    `check <notes>`: check the structure of curated notes.
    `body <notes> <generated>`: check curated notes, then print the body of
        the release to standard output: the curated notes, then the
        generated notes (the `body` of the `generate-notes` response, in a
        file).
    `require <version> [--releases <dir>]`: fail if the curated notes of a
        release (`<dir>/<version>.md`, by default in `docs/releases/`) are
        missing.

Errors (and warnings) are printed as GitHub annotations to standard error.
Only the stdlib is used, so the workflows run it without installing anything.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

# Headings of the curated notes, in their order; all are optional
SECTIONS = (
    "Breaking changes",
    "Features",
    "Security",
    "Fixes",
    "Documentation",
    "Maintenance",
)
# Added by the release workflow, after the curated sections
COMMITS = "Commits"
# Header of GitHub's generated notes, which is dropped
WHATS_CHANGED = "## What's Changed"
# Start of the last line of GitHub's generated notes, which the curated notes
# must not have
FULL_CHANGELOG = "**Full Changelog**"

# ATX headings (`## Title`)
HEADING = re.compile(
    r" {0,3}(?P<level>#{1,6})(?:[ \t]+(?P<title>.*?))??(?:[ \t]+#*)?[ \t]*"
)
# Setext heading underlines (`---`, `===`) and thematic breaks (also `***`,
# `___`), which are rejected: a line of `-` or `=` under a paragraph makes it
# a heading
UNDERLINE = re.compile(r" {0,3}(?:(?:-[ \t]*)+|=+[ \t]*|(?:[*_][ \t]*){3,})")
# Opening and closing lines of fenced code blocks: a block closes with a line
# of the same character, at least as long as the opening one, and nothing else
FENCE = re.compile(r"[ \t]*(?P<marker>`{3,}|~{3,})(?P<rest>.*)")
# Top-level list items (bullets or numbered)
ITEM = re.compile(r"(?:[-*+]|[0-9]+[.)])(?:[ \t]|$)")
# The end of a bullet: its issue and pull request numbers, e.g., `(#12, #34)`
# (only the pull request's if it closes no issue)
REFERENCES = re.compile(r".*\(#[0-9]+(?:[,;][ \t]*#[0-9]+)*\)", re.ASCII)

BULLETS_ONLY = "Sections hold bullets only, e.g., - <change> (#12, #34)"

# Release versions as the release workflow accepts them (tag `v<version>`):
# X.Y.Z, or X.Y.Z-alpha.N, -beta.N or -rc.N (SemVer, as chart versions must
# be)
VERSION = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:alpha|beta|rc)\.(?:0|[1-9][0-9]*))?",
    re.ASCII,
)
# Docs on Read the Docs and repository on GitHub, and links to versions of
# them that move
DOCS_HOST = "tesk.readthedocs.io"
REPOSITORY = "elixir-cloud-aai/TESK"
_MOVING = r"(?![\w.-])"
UNVERSIONED = re.compile(
    rf"{re.escape(DOCS_HOST)}/(?:en/)?(?:latest|stable){_MOVING}"
    rf"|github\.com/{re.escape(REPOSITORY)}/"
    rf"(?:blob|tree|raw|edit|blame|commits)/(?:refs/heads/)?(?:dev|main|HEAD)"
    rf"{_MOVING}"
    rf"|github\.com/{re.escape(REPOSITORY)}/releases/latest{_MOVING}"
    rf"|raw\.githubusercontent\.com/{re.escape(REPOSITORY)}/"
    rf"(?:refs/heads/)?(?:dev|main|HEAD){_MOVING}",
    re.ASCII | re.IGNORECASE,
)
MOVING_LINK = (
    "Link to a version that moves (e.g., latest docs, branch dev): the release"
    " body never changes, so link the release's (/en/vX.Y.Z/, blob/vX.Y.Z/)"
)
# Marks unfinished notes, which must not be published
TODO = "TODO"
UNFINISHED = "TODO: finish the release notes before the release"


@dataclass(frozen=True)
class Finding:
    """A problem in the structure of curated release notes.

    Attributes:
        line: Number of the line (from 1).
        message: What is wrong.
    """

    line: int
    message: str


def _is_comment(line: str) -> bool:
    """Return whether a line is a single HTML comment, which counts as blank.

    Comments over several lines are not supported. Lines are checked one by
    one, so this is no HTML filter (the notes are published as written).

    Args:
        line: Line of the notes.

    Returns:
        Whether the line, without surrounding whitespace, is one comment.
    """
    text = line.strip()
    return (
        len(text) >= len("<!---->")
        and text.startswith("<!--")
        and text.endswith("-->")
        and "-->" not in text[len("<!--") : -len("-->")]
    )


def _heading_finding(
    number: int, level: int, title: str, last: int | None
) -> Finding | None:
    """Return the problem of a heading of curated notes, if any.

    Args:
        number: Number of the heading's line.
        level: Level of the heading (number of `#`).
        title: Title of the heading.
        last: Index in `SECTIONS` of the last valid section before, if any.

    Returns:
        A finding unless the heading is a section of `SECTIONS` after `last`.
    """
    allowed = ", ".join(SECTIONS)
    if level != 2:
        return Finding(
            number,
            f"Heading of level {level} ('{title}'): only sections"
            f" ('## <title>') are allowed: {allowed}",
        )
    if title == COMMITS:
        return Finding(
            number,
            f"Section '{COMMITS}': the release workflow adds it from GitHub's"
            " generated notes",
        )
    if title not in SECTIONS:
        return Finding(
            number, f"Unknown section '{title}': allowed are, in this order: {allowed}"
        )
    if last is not None and SECTIONS.index(title) <= last:
        return Finding(
            number,
            f"Section '{title}' after '{SECTIONS[last]}': sections are in this"
            f" order, each once: {allowed}",
        )
    return None


@dataclass
class _Checker:
    """State of the check of curated release notes, line by line.

    Attributes:
        findings: Findings so far.
        intro: Whether the intro has a paragraph (not only lists or code).
        heading_line: Line of the current heading (0 in the intro).
        valid: Whether the current heading is a valid section.
        bullets: Number of bullets in the current section.
        last: Index in `SECTIONS` of the last valid section, if any.
        item: Lines of the current bullet (number, text).
        fence: Marker of the open fenced code block (e.g., ```` ``` ````), if
            any.
        previous_blank: Whether the previous line is blank.
    """

    findings: list[Finding] = field(default_factory=list)
    intro: bool = False
    heading_line: int = 0
    valid: bool = False
    bullets: int = 0
    last: int | None = None
    item: list[tuple[int, str]] = field(default_factory=list)
    fence: str | None = None
    previous_blank: bool = True

    def run(self, lines: list[str]) -> list[Finding]:
        """Check the lines of curated notes.

        Args:
            lines: Lines of the notes.

        Returns:
            The findings, in the order of their lines.
        """
        for number, line in enumerate(lines, start=1):
            self._line(number, line)
        self._close_section()
        if self.fence:
            self.findings.append(Finding(len(lines), "Unclosed fenced code block"))
        if not self.intro:
            self.findings.append(Finding(max(len(lines), 1), "No intro paragraph"))
        return sorted(self.findings, key=lambda finding: finding.line)

    def _line(self, number: int, line: str) -> None:
        """Check a line.

        Args:
            number: Number of the line.
            line: Text of the line.
        """
        fence = FENCE.fullmatch(line)
        if self.fence or fence:
            self._code(number, line, fence)
            return
        if line.lstrip().startswith(FULL_CHANGELOG):
            self.findings.append(
                Finding(
                    number,
                    f"'{FULL_CHANGELOG}' line: the release workflow adds GitHub's",
                )
            )
        heading = HEADING.fullmatch(line)
        if heading:
            self._heading(number, len(heading["level"]), heading["title"] or "")
            return
        blank = not line.strip() or _is_comment(line)
        if not blank and UNDERLINE.fullmatch(line):
            self.findings.append(
                Finding(
                    number,
                    "Setext heading or thematic break: use no headings but the"
                    " sections, and no rules",
                )
            )
        elif self.heading_line == 0:
            # A paragraph, not a list
            self.intro = self.intro or not (blank or ITEM.match(line))
        elif blank:
            if self.item:
                # As a blank line (also comments)
                self.item.append((number, ""))
        elif ITEM.match(line):
            self._close_item()
            self.item = [(number, line)]
            self.bullets += 1
        elif self.item and (line[0] in " \t" or not self.previous_blank):
            # Indented content of the bullet, or a lazy continuation line of
            # its paragraph
            self.item.append((number, line))
        elif self.valid:
            self.findings.append(Finding(number, BULLETS_ONLY))
        self.previous_blank = blank

    def _code(self, number: int, line: str, fence: re.Match[str] | None) -> None:
        """Check a line of a fenced code block, or a fence.

        Code blocks belong to the intro or to a bullet.

        Args:
            number: Number of the line.
            line: Text of the line.
            fence: Match of `FENCE` on the line, if any.
        """
        if self.fence is None and fence:
            self.fence = fence["marker"]
            # Code blocks in the intro don't make it one
            if self.heading_line and not self.item and self.valid:
                self.findings.append(Finding(number, BULLETS_ONLY))
        elif (
            self.fence
            and fence
            and fence["marker"][0] == self.fence[0]
            and len(fence["marker"]) >= len(self.fence)
            and not fence["rest"].strip()
        ):
            self.fence = None
        if self.heading_line and self.item:
            self.item.append((number, line))
        self.previous_blank = False

    def _heading(self, number: int, level: int, title: str) -> None:
        """Check a heading, which starts a section.

        Args:
            number: Number of the heading's line.
            level: Level of the heading (number of `#`).
            title: Title of the heading.
        """
        self._close_section()
        title = title.strip()
        finding = _heading_finding(number, level, title, self.last)
        if finding:
            self.findings.append(finding)
        else:
            self.last = SECTIONS.index(title)
        self.heading_line, self.valid, self.bullets = number, finding is None, 0
        if not self.intro:
            self.findings.append(
                Finding(number, "No intro paragraph before the first section")
            )
            self.intro = True
        self.previous_blank = False

    def _close_item(self) -> None:
        """Check that the current bullet ends with its numbers, and end it."""
        content = [(number, line) for number, line in self.item if line.strip()]
        # The numbers may be wrapped over lines
        text = " ".join(line.strip() for _, line in content)
        # Only in valid sections, as invalid headings have findings already
        if self.valid and content and not REFERENCES.fullmatch(text):
            self.findings.append(
                Finding(
                    content[-1][0],
                    "Bullet doesn't end with its issue and pull request"
                    " numbers, e.g., (#12, #34)",
                )
            )
        self.item = []

    def _close_section(self) -> None:
        """End the current bullet and section; valid ones must have bullets."""
        self._close_item()
        if self.valid and self.bullets == 0:
            self.findings.append(Finding(self.heading_line, "Empty section"))


def check(markdown: str) -> list[Finding]:
    """Return the problems in the structure of curated release notes.

    Args:
        markdown: Curated release notes (parts 1 and 2 of the format).

    Returns:
        The findings, in the order of their lines; none if the notes have an
        intro paragraph (lists and code blocks alone don't count), then only
        headings of `SECTIONS` (level 2, each once, in their order, none
        empty), holding bullets only, each ending with its issue and pull
        request numbers, and none of the parts that the release workflow adds
        (`## Commits`, the `**Full Changelog**` line), and no links to
        versions that move (`UNVERSIONED`), and no `TODO` (unfinished
        notes, also in comments). An HTML comment on a line of its own
        counts as a blank line.
    """
    lines = markdown.removeprefix("\ufeff").splitlines()
    findings = _Checker().run(lines)
    for number, line in enumerate(lines, start=1):
        if UNVERSIONED.search(line):
            findings.append(Finding(number, MOVING_LINK))
        if TODO in line:
            findings.append(Finding(number, UNFINISHED))
    return sorted(findings, key=lambda finding: finding.line)


def body(curated: str, generated: str) -> tuple[str, list[str]]:
    """Return the body of a release: curated notes, then generated ones.

    Args:
        curated: Curated release notes (parts 1 and 2 of the format); they
            are not checked here (see `check`).
        generated: GitHub's generated notes (the `body` of the
            `generate-notes` response).

    Returns:
        The body: the curated notes, then `## Commits` with the generated
        notes without their `## What's Changed` header (left out if they list
        no changes), whose last line is the `**Full Changelog**` line; and
        warnings about unexpected generated notes, which are then kept as
        they are (so that an unexpected format doesn't fail the release
        workflow after the chart was attested and signed).
    """
    # Split at line breaks only (`splitlines` also splits at, e.g., U+2028,
    # which could make a title of a pull request a heading)
    text = generated.strip().replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    warnings = []
    # Also after a comment (e.g., with a configuration in `.github/release.yml`)
    if WHATS_CHANGED in lines:
        lines.remove(WHATS_CHANGED)
    if not lines or not lines[-1].startswith(f"{FULL_CHANGELOG}: "):
        warnings.append(f"Generated notes don't end with a '{FULL_CHANGELOG}: ' line")
        changes, last = "\n".join(lines).strip(), []
    else:
        changes, last = "\n".join(lines[:-1]).strip(), [lines[-1]]
    parts = [curated.strip()]
    if changes:
        parts.append(f"## {COMMITS}\n\n{changes}")
    return "\n\n".join(parts + last) + "\n", warnings


def missing_notes(version: str, releases: Path) -> Path | None:
    """Get the curated notes that a release lacks, if any.

    Every release needs curated notes; a version that the release workflow
    doesn't accept (`VERSION`) has none.

    Args:
        version: Version of the release, e.g., `1.2.3` or `1.2.3-rc.1`.
        releases: Directory with the curated notes, one `<version>.md` each.

    Returns:
        The path of the missing notes, or `None` if they exist.

    Raises:
        ValueError: If the version is not a release version.
    """
    if not VERSION.fullmatch(version):
        raise ValueError(f"'{version}' is not a release version (e.g., 1.2.3)")
    notes = releases / f"{version}.md"
    return None if notes.is_file() else notes


def _require(args: argparse.Namespace) -> int:
    """Fail if a release lacks curated notes (command `require`).

    Args:
        args: Parsed arguments of the command.

    Returns:
        The exit status: 0 if the notes exist, 1 if they are missing or the
        version is not a release version.
    """
    try:
        notes = missing_notes(args.version, args.releases)
    except ValueError as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1
    if notes is None:
        return 0
    print(
        f"::error::{notes} is missing: every release needs curated release"
        " notes (see 'Releases' in docs/development.md)",
        file=sys.stderr,
    )
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run a command (see the module's docstring).

    Args:
        argv: Command-line arguments, without the program name; those of the
            process if `None`.

    Returns:
        The exit status: 0 on success, 1 if the curated notes have findings or
        are missing (`require`), or a file can't be read.
    """
    parser = argparse.ArgumentParser(
        description="Check curated release notes and build the release body."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check", help="check curated notes")
    check_parser.add_argument("notes", type=Path, help="curated notes")
    body_parser = commands.add_parser("body", help="print the release body")
    body_parser.add_argument("notes", type=Path, help="curated notes")
    body_parser.add_argument(
        "generated", type=Path, help="generated notes (`body` of generate-notes)"
    )
    require_parser = commands.add_parser(
        "require", help="fail if the curated notes of a release are missing"
    )
    require_parser.add_argument("version", help="release version, e.g., 1.2.3")
    require_parser.add_argument(
        "--releases",
        type=Path,
        default=Path("docs/releases"),
        help="directory with the curated notes (default: docs/releases)",
    )
    args = parser.parse_args(argv)
    if args.command == "require":
        return _require(args)
    notes: Path = args.notes
    try:
        curated = notes.read_text(encoding="utf-8")
        generated = (
            args.generated.read_text(encoding="utf-8") if args.command == "body" else ""
        )
    except (OSError, UnicodeDecodeError) as error:
        print(f"::error::Can't read the notes: {error}", file=sys.stderr)
        return 1
    findings = check(curated)
    for finding in findings:
        print(
            f"::error file={notes},line={finding.line}::{finding.message}",
            file=sys.stderr,
        )
    if findings:
        return 1
    if args.command == "body":
        text, warnings = body(curated, generated)
        for warning in warnings:
            print(f"::warning::{warning}; kept as they are", file=sys.stderr)
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
