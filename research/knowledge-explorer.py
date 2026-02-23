#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "ruamel.yaml>=0.18.0",
#     "python-frontmatter>=1.1.0",
# ]
# ///
"""Knowledge base explorer for research/ directory.

Manages entries in the research/ knowledge base. Reads both inline-header and
YAML frontmatter formats; always writes in frontmatter format. Six subcommands
share a single Typer entry point.
"""

from __future__ import annotations

import base64
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Literal
from urllib.parse import urlparse

import frontmatter
import typer
from frontmatter.default_handlers import YAMLHandler
from rich.console import Console
from rich.measure import Measurement
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KB_ROOT: Path = Path(__file__).parent.resolve()
_README_SUMMARY_MAX_LEN: int = 120
_LEVENSHTEIN_MAX_DISTANCE: int = 2
_MAX_SUGGESTIONS: int = 3
_MIN_GITHUB_PATH_PARTS: int = 2
_DEFAULT_REVIEW_DAYS: int = 90
_NAME_MAX_LEN: int = 64
_DESCRIPTION_MAX_LEN: int = 1024

VALID_CATEGORIES: frozenset[str] = frozenset({
    "agent-frameworks",
    "agent-infrastructure",
    "ai-design-tools",
    "ai-observability",
    "ai-research-tools",
    "ai-writing-tools",
    "api-frameworks",
    "async-libraries",
    "code-auditing",
    "coding-agents",
    "context-management",
    "data-infrastructure",
    "developer-tooling",
    "developer-tools",
    "documentation-tools",
    "evaluation-testing",
    "installer-tools",
    "llm-infrastructure",
    "low-code-platforms",
    "mcp-ecosystem",
    "ml-infrastructure",
    "python-runtimes",
    "research-agent-patterns",
    "rust-python-bindings",
    "skill-generation-tools",
    "task-management",
})

_GH_PATH: str | None = shutil.which("gh")

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class KBError(Exception):
    """Base exception. All knowledge-explorer errors inherit from this."""


@dataclass
class ParseError(KBError):
    """Format unrecognisable or required field missing during parse."""

    path: Path
    detail: str

    def __str__(self) -> str:
        """Return string representation."""
        return f"Parse error in {self.path}: {self.detail}"


@dataclass
class FrontmatterValidationError(KBError):
    """Frontmatter present but fails schema constraints."""

    path: Path
    missing_fields: list[str]
    invalid_fields: list[str]

    def __str__(self) -> str:
        """Return string representation."""
        parts: list[str] = []
        if self.missing_fields:
            parts.append(f"missing: {', '.join(self.missing_fields)}")
        if self.invalid_fields:
            parts.append(f"invalid: {', '.join(self.invalid_fields)}")
        return f"Validation error in {self.path}: {'; '.join(parts)}"


@dataclass
class TopicNotFoundError(KBError):
    """Topic slug not found in any entry. Includes suggestions."""

    topic: str
    suggestions: list[str]

    def __str__(self) -> str:
        """Return string representation."""
        msg = f"Topic '{self.topic}' not found."
        if self.suggestions:
            msg += f" Did you mean: {', '.join(self.suggestions)}?"
        return msg


@dataclass
class TopicConflictError(KBError):
    """Target path exists with a different topic slug."""

    target_path: Path
    existing_topic: str
    new_topic: str

    def __str__(self) -> str:
        """Return string representation."""
        return (
            f"Target {self.target_path} already exists with topic "
            f"'{self.existing_topic}', cannot overwrite with '{self.new_topic}'."
        )


@dataclass
class ExternalCommandError(KBError):
    """gh CLI not found or returned non-zero exit code."""

    command: str
    hint: str
    stderr: str = ""

    def __str__(self) -> str:
        """Return string representation."""
        msg = f"External command error: {self.command}\n{self.hint}"
        if self.stderr:
            msg += f"\nstderr: {self.stderr}"
        return msg


@dataclass
class ReadmeUpdateError(KBError):
    """README.md structure not recognised; update could not be applied."""

    detail: str

    def __str__(self) -> str:
        """Return string representation."""
        return f"README update error: {self.detail}"


# ---------------------------------------------------------------------------
# Layer 6: YAML Handler (embedded _RuamelYAMLHandler)
# ---------------------------------------------------------------------------


class _RuamelYAMLHandler(YAMLHandler):
    """Frontmatter handler using ruamel.yaml in round-trip mode.

    Overrides the default pyyaml-based handler so that:
    - Values without special YAML characters stay unquoted.
    - Values requiring quotes (colon-space) get single-quoted.
    - Unnecessary quotes from the source are stripped on round-trip.
    - Long scalar values do not get wrapped into block scalars.
    """

    def __init__(self) -> None:
        """Initialize handler with ruamel.yaml round-trip instance."""
        super().__init__()
        self._yaml = YAML(typ="rt")
        self._yaml.preserve_quotes = False
        self._yaml.width = 2147483647

    def load(self, fm: str, **kwargs: Any) -> Any:
        """Parse YAML frontmatter string using ruamel.yaml round-trip loader.

        Args:
            fm: Raw YAML frontmatter string (without delimiters).
            **kwargs: Ignored (present for API compatibility).

        Returns:
            Parsed YAML data as a CommentedMap or None for empty input.
        """
        return self._yaml.load(fm)

    def export(self, metadata: dict[str, Any], **kwargs: Any) -> str:
        """Serialize metadata dict to YAML string using ruamel.yaml.

        Args:
            metadata: Frontmatter metadata dictionary.
            **kwargs: Ignored (present for API compatibility).

        Returns:
            YAML-formatted string without trailing newline.
        """
        buf = StringIO()
        self._yaml.dump(metadata, buf)
        return buf.getvalue().strip()


_handler = _RuamelYAMLHandler()

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class KBEntry:
    """Canonical in-memory representation of a knowledge base entry."""

    # Required frontmatter fields
    topic: str
    name: str
    category: str
    source_url: str
    verified: date
    next_review: date

    # Top-level skill spec fields
    description: str = ""

    # Optional frontmatter fields
    github: str | None = None
    version: str | None = None
    license: str | None = None
    tags: list[str] = field(default_factory=list)

    # Runtime-only fields — not written to frontmatter
    file_path: Path = field(default_factory=Path)
    body: str = ""
    has_frontmatter: bool = False
    is_overdue: bool = field(init=False)

    def __post_init__(self) -> None:
        """Compute derived fields."""
        self.is_overdue = self.next_review < date.today()


@dataclass
class MigrationResult:
    """Result of a migrate operation."""

    migrated: list[Path] = field(default_factory=list)
    already_migrated: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)


@dataclass
class GitHubMetadata:
    """Metadata fetched from GitHub API."""

    slug: str
    name: str
    description: str
    license: str | None
    latest_tag: str | None
    default_branch: str
    has_docs_dir: bool
    docs_files: list[str]
    topics: list[str]


# ---------------------------------------------------------------------------
# Layer 5: External I/O
# ---------------------------------------------------------------------------


def _require_gh() -> str:
    """Return the gh binary path or raise ExternalCommandError.

    Returns:
        Path to gh binary.

    Raises:
        ExternalCommandError: If gh is not found on PATH.
    """
    if _GH_PATH is None:
        raise ExternalCommandError(
            command="gh", hint="Install gh CLI: https://cli.github.com/"
        )
    return _GH_PATH


def _gh_api(endpoint: str) -> Any:
    """Call gh api and return parsed JSON.

    Args:
        endpoint: API endpoint path (e.g. 'repos/owner/repo').

    Returns:
        Parsed JSON response.

    Raises:
        ExternalCommandError: If gh returns non-zero exit code.
    """
    gh = _require_gh()
    try:
        result = subprocess.run(
            [gh, "api", endpoint], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as exc:
        raise ExternalCommandError(
            command=f"gh api {endpoint}",
            hint="Ensure you are authenticated: gh auth login",
            stderr=exc.stderr,
        ) from exc
    return json.loads(result.stdout)


def fetch_github_metadata(repo_slug: str) -> GitHubMetadata:
    """Fetch metadata for a GitHub repository.

    Args:
        repo_slug: Repository in 'owner/repo' format.

    Returns:
        GitHubMetadata populated from GitHub API.

    Raises:
        ExternalCommandError: If any gh API call fails.
    """
    repo_data = _gh_api(f"repos/{repo_slug}")

    # Fetch latest release tag (404 = no releases)
    latest_tag: str | None = None
    try:
        release_data = _gh_api(f"repos/{repo_slug}/releases/latest")
        latest_tag = release_data.get("tag_name")
    except ExternalCommandError as exc:
        if "404" not in exc.stderr:
            raise
        latest_tag = None

    # Check for docs/ or doc/ directory
    contents = _gh_api(f"repos/{repo_slug}/contents")
    has_docs_dir = False
    docs_dirname: str | None = None
    for item in contents:
        if item.get("type") == "dir" and item.get("name") in {"docs", "doc"}:
            has_docs_dir = True
            docs_dirname = item["name"]
            break

    docs_files: list[str] = []
    if has_docs_dir and docs_dirname:
        try:
            docs_contents = _gh_api(f"repos/{repo_slug}/contents/{docs_dirname}")
            docs_files = [
                item["path"] for item in docs_contents if isinstance(item, dict)
            ]
        except ExternalCommandError:
            docs_files = []

    # Parse license
    license_info = repo_data.get("license") or {}
    license_spdx: str | None = license_info.get("spdx_id") if license_info else None
    if license_spdx in {"NOASSERTION", ""}:
        license_spdx = None

    return GitHubMetadata(
        slug=repo_slug,
        name=repo_data.get("name", repo_slug.rsplit("/", maxsplit=1)[-1]),
        description=repo_data.get("description") or "",
        license=license_spdx,
        latest_tag=latest_tag,
        default_branch=repo_data.get("default_branch", "main"),
        has_docs_dir=has_docs_dir,
        docs_files=docs_files,
        topics=repo_data.get("topics") or [],
    )


def find_entry_by_topic(topic: str, kb_root: Path) -> Path | None:
    """Search all .md files for an entry matching the topic slug.

    Args:
        topic: Kebab-case topic slug to find.
        kb_root: Root directory of the knowledge base.

    Returns:
        Path to the matching file, or None if not found.
    """
    for md_file in _iter_kb_files(kb_root):
        text = md_file.read_text(encoding="utf-8")
        fmt = _detect_format_safe(text)
        if fmt == "frontmatter":
            with contextlib.suppress(Exception):
                post = frontmatter.loads(text, handler=_handler)
                meta = post.metadata
                # New skill-spec format: topic is inside metadata block
                raw_inner = meta.get("metadata")
                inner: dict[str, Any] = raw_inner if isinstance(raw_inner, dict) else {}
                stored_topic = inner.get("topic") if inner else meta.get("topic")
                if stored_topic == topic:
                    return md_file
        elif md_file.stem == topic:
            return md_file
    return None


def _build_readme_row(entry: KBEntry) -> str:
    """Build a README table row string for an entry.

    Args:
        entry: Entry to build the row for.

    Returns:
        Markdown table row string.
    """
    today_iso = date.today().isoformat()
    summary = _extract_first_paragraph(entry.body) or entry.name
    if len(summary) > _README_SUMMARY_MAX_LEN:
        summary = summary[: _README_SUMMARY_MAX_LEN - 1] + "\u2026"
    return (
        f"| [{entry.topic}.md](./{entry.category}/{entry.topic}.md)"
        f" | {summary} | {today_iso} |"
    )


def _update_existing_section(
    text: str, new_row: str, entry: KBEntry, section_start: int
) -> str:
    """Update a README table row inside an existing category section.

    Args:
        text: Full README text.
        new_row: New table row to insert or replace.
        entry: Entry being added/updated.
        section_start: Character offset of the category section start.

    Returns:
        Updated README text.

    Raises:
        ReadmeUpdateError: If no table is found in the section.
    """
    table_header_pat = re.compile(r"\| Document \|.*\n\|[-| ]+\|", re.IGNORECASE)
    table_match = table_header_pat.search(text, section_start)
    if not table_match:
        raise ReadmeUpdateError(
            detail=f"No table found in section for '{entry.category}'"
        )

    table_end = table_match.end()
    row_pattern = re.compile(r"\n(\|[^\n]+\|)")
    rows: list[tuple[int, int, str]] = []
    pos = table_end
    while pos < len(text):
        row_match = row_pattern.match(text, pos)
        if not row_match:
            break
        rows.append((row_match.start(), row_match.end(), row_match.group(1)))
        pos = row_match.end()

    topic_marker_a = f"/{entry.topic}.md)"
    topic_marker_b = f"/{entry.topic}.md |"
    existing_idx = next(
        (
            i
            for i, (_, _, row_content) in enumerate(rows)
            if topic_marker_a in row_content or topic_marker_b in row_content
        ),
        None,
    )

    if existing_idx is not None:
        start, end, _ = rows[existing_idx]
        return text[:start] + "\n" + new_row + text[end:]

    # Insert alphabetically
    insert_pos = table_end
    for _, row_end, row_content in rows:
        link_match = re.search(r"\[([^\]]+)\.md\]", row_content)
        if link_match and link_match.group(1) < entry.topic:
            insert_pos = row_end
        else:
            break
    return text[:insert_pos] + "\n" + new_row + text[insert_pos:]


def _append_new_section(text: str, new_row: str, entry: KBEntry) -> str:
    """Append a new category section to README text.

    Args:
        text: Full README text.
        new_row: Table row for the entry.
        entry: Entry being added.

    Returns:
        Updated README text with new section inserted.
    """
    new_section = (
        f"\n\n### {entry.category.replace('-', ' ').title()}\n\n"
        f"**Location**: [./{entry.category}/](./{entry.category}/)\n\n"
        f"| Document | Description | Last Updated |\n"
        f"|---|---|---|\n"
        f"{new_row}\n"
    )
    planned_pat = re.compile(r"^## Planned", re.MULTILINE)
    planned_match = planned_pat.search(text)
    if planned_match:
        return (
            text[: planned_match.start()] + new_section + text[planned_match.start() :]
        )
    return text.rstrip() + new_section


def update_readme(kb_root: Path, entry: KBEntry) -> None:
    """Update README.md with the new or updated entry row.

    Args:
        kb_root: Root directory of the knowledge base.
        entry: Entry to add/update in the README table.

    Raises:
        ReadmeUpdateError: If README structure is not recognised.
    """
    readme_path = kb_root / "README.md"
    if not readme_path.exists():
        raise ReadmeUpdateError(detail="README.md not found")

    text = readme_path.read_text(encoding="utf-8")
    new_row = _build_readme_row(entry)

    location_pattern = re.compile(
        rf"\*\*Location\*\*:.*\[.*{re.escape(entry.category)}.*\]", re.IGNORECASE
    )
    section_match = location_pattern.search(text)

    if section_match:
        text = _update_existing_section(text, new_row, entry, section_match.start())
    else:
        text = _append_new_section(text, new_row, entry)

    tmp = readme_path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(readme_path)


# ---------------------------------------------------------------------------
# Layer 3: Parsers
# ---------------------------------------------------------------------------


def detect_format(text: str) -> Literal["frontmatter", "inline-header"]:
    """Detect whether text uses frontmatter or inline-header format.

    Args:
        text: Raw file content.

    Returns:
        'frontmatter' or 'inline-header'.

    Raises:
        ParseError: If format cannot be determined.
    """
    if text.startswith("---\n"):
        return "frontmatter"
    # Check inline-header: first non-blank line is '# Heading' and
    # block before '---' or '##' contains at least one **Field** marker.
    first_nonblank = next((line for line in text.splitlines() if line.strip()), "")
    if first_nonblank.startswith(("# ", "|")):
        # Look for bold field or table row before first ## heading
        pre_body = text
        separator_match = re.search(r"^##\s", text, re.MULTILINE)
        if separator_match:
            pre_body = text[: separator_match.start()]
        bold_field = re.search(r"\*\*[A-Za-z ]+\*\*\s*:", pre_body)
        table_field = re.search(r"^\|\s*Research Date\s*\|", pre_body, re.MULTILINE)
        if bold_field or table_field:
            return "inline-header"
    raise ParseError(
        path=Path("<text>"),
        detail="Cannot determine format: not frontmatter and no inline-header fields found.",
    )


def _detect_format_safe(text: str) -> Literal["frontmatter", "inline-header"] | None:
    """Detect format without raising.

    Args:
        text: Raw file content.

    Returns:
        Format string or None on error.
    """
    try:
        return detect_format(text)
    except ParseError:
        return None


def _parse_research_date(value: str) -> date:
    """Parse a research date in ISO or long format.

    Args:
        value: Date string, e.g. '2026-01-26' or 'January 26, 2026'.

    Returns:
        Parsed date object.

    Raises:
        ParseError: If neither pattern matches.
    """
    value = value.strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%B %d, %Y").date()
    except ValueError:
        pass
    raise ParseError(
        path=Path("<date>"),
        detail=f"Cannot parse date: '{value}'. Expected YYYY-MM-DD or 'Month DD, YYYY'.",
    )


def _extract_github_slug(url: str) -> str | None:
    """Extract 'owner/repo' from a GitHub URL.

    Args:
        url: Full GitHub URL such as 'https://github.com/owner/repo'.

    Returns:
        'owner/repo' string, or None if pattern does not match.
    """
    url = url.strip().strip("<>")
    parsed = urlparse(url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= _MIN_GITHUB_PATH_PARTS:
        return f"{parts[0]}/{parts[1]}"
    return None


def _merge_freshness_fields(
    fields: dict[str, str], freshness_block: str, table_pattern: re.Pattern[str]
) -> None:
    """Extract freshness table values and merge into fields dict.

    Args:
        fields: Existing fields dict to update in-place.
        freshness_block: Text of the Freshness Tracking section.
        table_pattern: Compiled regex for table row matching.
    """
    for match in table_pattern.finditer(freshness_block):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if re.match(r"^[-:]+$", key):
            continue
        key_lower = key.lower()
        if "last verified" in key_lower:
            fields.setdefault("Last Verified", value)
        elif "version at verif" in key_lower:
            fields["Version at Verification"] = value
        elif "next review" in key_lower:
            cleaned = re.sub(r"\s*\([^)]+\)\s*$", "", value).strip()
            fields.setdefault("Next Review Recommended", cleaned)


def _trim_body_section(body_lines: list[str]) -> str:
    """Trim trailing Change Detection / Review Triggers noise from body lines.

    Args:
        body_lines: Lines of the body section (before Freshness Tracking).

    Returns:
        Stripped body text.
    """
    trimmed: list[str] = []
    for line in body_lines:
        if re.match(r"^\*\*(Change Detection|Review Triggers)", line):
            break
        trimmed.append(line)
    return "".join(trimmed).strip()


def strip_inline_header_and_freshness(text: str) -> tuple[dict[str, str], str]:
    """Extract fields and body from inline-header format.

    Parses **Field**: value pairs from the header region and removes the
    Freshness Tracking section.

    Args:
        text: Full file content in inline-header format.

    Returns:
        Tuple of (fields_dict, body).
    """
    lines = text.splitlines(keepends=True)
    fields: dict[str, str] = {}

    # Detect header end: first line starting with ## after a non-heading section
    header_end_line = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("## ") and i > 0:
            header_end_line = i
            break

    header_block = "".join(lines[:header_end_line])

    # Parse **Field**: value patterns
    bold_pattern = re.compile(r"\*\*([^*]+)\*\*\s*:\s*(.+)")
    for match in bold_pattern.finditer(header_block):
        key = match.group(1).strip()
        value = match.group(2).strip()
        fields[key] = value

    # Parse table-style: | Field | Value |
    table_pattern = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
    for match in table_pattern.finditer(header_block):
        key = match.group(1).strip()
        value = match.group(2).strip()
        # Skip separator rows like | --- |
        if re.match(r"^[-:]+$", key) or re.match(r"^[-:]+$", value):
            continue
        if key.lower() in {"field", "document", "description"}:
            continue
        fields[key] = value

    body_lines = lines[header_end_line:]
    freshness_start = next(
        (
            i
            for i, line in enumerate(body_lines)
            if re.match(r"^## Freshness", line, re.IGNORECASE)
        ),
        None,
    )

    if freshness_start is not None:
        _merge_freshness_fields(
            fields, "".join(body_lines[freshness_start:]), table_pattern
        )
        body_text = _trim_body_section(body_lines[:freshness_start])
    else:
        body_text = "".join(body_lines).strip()

    body_text = re.sub(r"\n---\s*$", "", body_text).strip()
    return fields, body_text


def _extract_optional_inline_fields(
    fields: dict[str, str], stem: str
) -> tuple[str, str | None, str | None, str | None]:
    """Extract source_url, github, version, license from inline-header fields dict.

    Args:
        fields: Parsed inline-header fields.
        stem: File stem used as fallback for source_url.

    Returns:
        Tuple of (source_url, github, version, license).
    """
    source_url_raw = fields.get("Source URL") or fields.get("Primary URL") or ""
    source_url = source_url_raw.strip().strip("<>") or f"https://github.com/{stem}"

    github_raw = (
        (fields.get("GitHub Repository") or fields.get("GitHub") or "")
        .strip()
        .strip("<>")
    )
    github: str | None = _extract_github_slug(github_raw) if github_raw else None

    version_raw = (
        fields.get("Version at Verification")
        or fields.get("Version at Research")
        or fields.get("Version")
        or fields.get("Version Documented")
    )
    version: str | None = (
        re.sub(r"\s*\(.*\)\s*$", "", version_raw).strip() or None
        if version_raw
        else None
    )

    license_raw = fields.get("License")
    lic: str | None = license_raw.strip() if license_raw else None

    return source_url, github, version, lic


def _parse_inline_dates(
    fields: dict[str, str], path: Path, verified_raw: str
) -> tuple[date, date]:
    """Parse verified and next_review dates from inline-header fields dict.

    Args:
        fields: Parsed inline-header field dict.
        path: File path for error context.
        verified_raw: Raw string for the verified date.

    Returns:
        Tuple of (verified, next_review) date objects.

    Raises:
        ParseError: If verified_raw cannot be parsed.
    """
    try:
        verified = _parse_research_date(verified_raw)
    except ParseError as exc:
        raise ParseError(path=path, detail=str(exc)) from exc

    next_review_raw = (
        fields.get("Next Review Recommended") or fields.get("Next Review Date") or ""
    )
    if next_review_raw:
        try:
            next_review = _parse_research_date(next_review_raw)
        except ParseError:
            next_review = verified + timedelta(days=_DEFAULT_REVIEW_DAYS)
    else:
        next_review = verified + timedelta(days=_DEFAULT_REVIEW_DAYS)

    return verified, next_review


def parse_inline_header_entry(text: str, path: Path) -> KBEntry:
    """Parse an entry in inline-header format.

    Args:
        text: Raw file content.
        path: File path for error reporting.

    Returns:
        KBEntry populated from inline-header fields.

    Raises:
        ParseError: If required fields are missing or unparseable.
    """
    fields, body = strip_inline_header_and_freshness(text)

    topic = path.stem
    category = path.parent.name

    heading_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    name = heading_match.group(1).strip() if heading_match else topic

    verified_raw = (
        fields.get("Research Date")
        or fields.get("Last Verified")
        or fields.get("Version Documented")
        or ""
    )
    if not verified_raw:
        raise ParseError(
            path=path, detail="Cannot find Research Date or Last Verified field."
        )

    verified, next_review = _parse_inline_dates(fields, path, verified_raw)
    source_url, github, version, lic = _extract_optional_inline_fields(
        fields, path.stem
    )

    first_para = _extract_first_paragraph(body)
    if first_para:
        description = first_para[:_DESCRIPTION_MAX_LEN]
    else:
        description = (
            f"Research entry for {name}. Use when working with {name} or related tools."
        )

    return KBEntry(
        topic=topic,
        name=name,
        description=description,
        category=category,
        source_url=source_url,
        verified=verified,
        next_review=next_review,
        github=github,
        version=version,
        license=lic,
        tags=[],
        file_path=path,
        body=body,
        has_frontmatter=False,
    )


def _parse_tags_field(tags_raw: Any) -> list[str]:
    """Parse a tags value from frontmatter into a list of strings.

    Accepts a list, a comma-separated string, or None/empty.

    Args:
        tags_raw: Raw value from frontmatter metadata.

    Returns:
        List of tag strings.
    """
    if isinstance(tags_raw, list):
        return [str(t) for t in tags_raw]
    if tags_raw:
        return [t.strip() for t in str(tags_raw).split(",") if t.strip()]
    return []


def _parse_date_field(raw: Any) -> date:
    """Parse a date field that may already be a date or a string.

    Args:
        raw: Raw value from frontmatter (date object or string).

    Returns:
        Parsed date object.

    Raises:
        ParseError: If the value cannot be parsed.
    """
    if isinstance(raw, date):
        return raw
    return _parse_research_date(str(raw))


def _from_skill_spec_meta(top: Any, path: Path) -> KBEntry:
    """Parse a KBEntry from new skill-spec frontmatter (metadata sub-mapping).

    Args:
        top: Full parsed frontmatter metadata dict.
        path: File path for error reporting.

    Returns:
        KBEntry populated from skill-spec format.

    Raises:
        FrontmatterValidationError: If required fields are missing.
        ParseError: If date fields cannot be parsed.
    """
    inner: dict[str, Any] = top["metadata"]
    required_top = [f for f in ("name",) if f not in top]
    required_inner = [
        f
        for f in ("topic", "category", "source_url", "verified", "next_review")
        if f not in inner
    ]
    missing = required_top + required_inner
    if missing:
        raise FrontmatterValidationError(
            path=path, missing_fields=missing, invalid_fields=[]
        )

    license_val: str | None = (
        str(top["license"]) if top.get("license") is not None else None
    )
    github_val: str | None = (
        str(inner["github"]) if inner.get("github") is not None else None
    )
    version_val: str | None = (
        str(inner["version"]) if inner.get("version") is not None else None
    )

    return KBEntry(
        topic=str(inner["topic"]),
        name=str(top["name"]),
        description=str(top.get("description") or ""),
        category=str(inner["category"]),
        source_url=str(inner["source_url"]),
        verified=_parse_date_field(inner["verified"]),
        next_review=_parse_date_field(inner["next_review"]),
        github=github_val,
        version=version_val,
        license=license_val,
        tags=_parse_tags_field(inner.get("tags")),
        file_path=path,
        body="",  # filled by caller
        has_frontmatter=True,
    )


def _from_flat_meta(meta: Any, path: Path) -> KBEntry:
    """Parse a KBEntry from old flat frontmatter format.

    Args:
        meta: Full parsed frontmatter metadata dict (flat, no metadata sub-key).
        path: File path for error reporting.

    Returns:
        KBEntry populated from flat format.

    Raises:
        FrontmatterValidationError: If required fields are missing.
        ParseError: If date fields cannot be parsed.
    """
    missing = [
        f
        for f in ("topic", "name", "category", "source_url", "verified", "next_review")
        if f not in meta
    ]
    if missing:
        raise FrontmatterValidationError(
            path=path, missing_fields=missing, invalid_fields=[]
        )

    github_val: str | None = (
        str(meta["github"]) if meta.get("github") is not None else None
    )
    version_val: str | None = (
        str(meta["version"]) if meta.get("version") is not None else None
    )
    license_val: str | None = (
        str(meta["license"]) if meta.get("license") is not None else None
    )

    return KBEntry(
        topic=str(meta["topic"]),
        name=str(meta["name"]),
        description=str(meta.get("description") or ""),
        category=str(meta["category"]),
        source_url=str(meta["source_url"]),
        verified=_parse_date_field(meta["verified"]),
        next_review=_parse_date_field(meta["next_review"]),
        github=github_val,
        version=version_val,
        license=license_val,
        tags=_parse_tags_field(meta.get("tags")),
        file_path=path,
        body="",  # filled by caller
        has_frontmatter=True,
    )


def parse_frontmatter_entry(text: str, path: Path) -> KBEntry:
    """Parse an entry in YAML frontmatter format.

    Handles both formats:
    - New skill-spec format: top-level ``name``, ``description``, ``license``; KB
      fields inside a ``metadata`` mapping.
    - Old flat format: all KB fields at top level (topic, name, category, …).

    Args:
        text: Raw file content.
        path: File path for error reporting.

    Returns:
        KBEntry populated from frontmatter fields.

    Raises:
        ParseError: If required fields are missing.
        FrontmatterValidationError: If fields fail schema constraints.
    """
    try:
        post = frontmatter.loads(text, handler=_handler)
    except Exception as exc:
        raise ParseError(path=path, detail=f"YAML parse error: {exc}") from exc

    top = post.metadata
    entry = (
        _from_skill_spec_meta(top, path)
        if isinstance(top.get("metadata"), dict)
        else _from_flat_meta(top, path)
    )
    entry.body = post.content
    return entry


# ---------------------------------------------------------------------------
# Layer 2: Core operations
# ---------------------------------------------------------------------------


def parse_entry(path: Path) -> KBEntry:
    """Read a file and return a KBEntry.

    Args:
        path: Path to a markdown knowledge base file.

    Returns:
        KBEntry parsed from the file.

    Raises:
        ParseError: If file format is unrecognisable.
    """
    text = path.read_text(encoding="utf-8")
    fmt = detect_format(text)
    if fmt == "frontmatter":
        return parse_frontmatter_entry(text, path)
    return parse_inline_header_entry(text, path)


def _iter_kb_files(kb_root: Path) -> list[Path]:
    """Return all .md files in kb_root excluding README.md and the script.

    Args:
        kb_root: Root directory to scan.

    Returns:
        Sorted list of Path objects.
    """
    excluded = {kb_root / "README.md", kb_root / "knowledge-explorer.py"}
    result: list[Path] = []
    for category_dir in sorted(kb_root.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        result.extend(
            md_file
            for md_file in sorted(category_dir.glob("*.md"))
            if md_file not in excluded
        )
    return result


def build_tree(kb_root: Path) -> list[KBEntry]:
    """Scan kb_root and return all successfully parsed entries.

    Args:
        kb_root: Root directory to scan.

    Returns:
        List of KBEntry objects; parse failures are silently skipped.
    """
    entries: list[KBEntry] = []
    for path in _iter_kb_files(kb_root):
        with contextlib.suppress(KBError):
            entries.append(parse_entry(path))
    return entries


def write_entry(entry: KBEntry, path: Path) -> None:
    """Write a KBEntry to disk in frontmatter format atomically.

    Args:
        entry: Entry to serialize.
        path: Destination file path.
    """
    post = entry_to_post(entry)
    content = frontmatter.dumps(post, handler=_handler)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def migrate_entry(entry: KBEntry) -> KBEntry:
    """Return a copy of the entry ready for serialization in skill-spec format.

    Preserves all fields. Sets ``has_frontmatter=True`` so the caller knows the
    entry will be written in frontmatter format.

    Args:
        entry: Entry in any format.

    Returns:
        Entry ready for serialization as skill-compatible frontmatter.
    """
    return KBEntry(
        topic=entry.topic,
        name=entry.name,
        description=entry.description,
        category=entry.category,
        source_url=entry.source_url,
        verified=entry.verified,
        next_review=entry.next_review,
        github=entry.github,
        version=entry.version,
        license=entry.license,
        tags=entry.tags,
        file_path=entry.file_path,
        body=entry.body,
        has_frontmatter=True,
    )


def _infer_category(meta: GitHubMetadata) -> str | None:
    """Infer a VALID_CATEGORIES category from GitHub repo topics.

    Args:
        meta: GitHubMetadata fetched from GitHub API.

    Returns:
        Matching category string, or None if no topic matches.
    """
    for topic in meta.topics:
        if topic in VALID_CATEGORIES:
            return topic
    return None


def build_draft(repo_slug: str, meta: GitHubMetadata, category: str) -> KBEntry:
    """Construct a draft KBEntry from GitHub metadata.

    Args:
        repo_slug: 'owner/repo' slug.
        meta: GitHubMetadata fetched from GitHub API.
        category: Resolved category (must be a member of VALID_CATEGORIES).

    Returns:
        Draft KBEntry with the provided category.
    """
    topic_slug = re.sub(r"[^a-z0-9-]", "-", meta.name.lower()).strip("-")
    today = date.today()

    # Build description from GitHub repo description (max 1024 chars)
    desc_max = 1024
    raw_desc = (meta.description or "").strip()
    if raw_desc:
        description = raw_desc[:desc_max]
    else:
        description = (
            f"Research entry for {meta.name}. "
            f"Use when working with {meta.name} or related tools."
        )

    return KBEntry(
        topic=topic_slug,
        name=meta.name,
        description=description,
        category=category,
        source_url=f"https://github.com/{repo_slug}",
        verified=today,
        next_review=today + timedelta(days=_DEFAULT_REVIEW_DAYS),
        github=repo_slug,
        version=meta.latest_tag,
        license=meta.license,
        tags=[t for t in meta.topics if t in VALID_CATEGORIES],
        file_path=KB_ROOT / category / f"{topic_slug}.md",
        body=f"> {meta.description}\n\n<!-- DRAFT: Review category and tags, then run: ./knowledge-explorer.py add <this-file> -->",
        has_frontmatter=True,
    )


# ---------------------------------------------------------------------------
# Layer 4: Serializers
# ---------------------------------------------------------------------------


def entry_to_post(entry: KBEntry) -> frontmatter.Post:
    """Serialize a KBEntry to a frontmatter.Post in skill-spec format.

    Top-level keys: ``name``, ``description``, ``license`` (if set).
    All KB tracking fields go into the ``metadata`` sub-mapping with string values.
    Date fields are serialized as ISO date strings. Tags are serialized as a
    comma-separated string, or omitted when empty.

    Args:
        entry: Entry to serialize.

    Returns:
        frontmatter.Post with ordered metadata and body.
    """
    meta: CommentedMap = CommentedMap()

    # Top-level Agent Skills spec fields
    meta["name"] = entry.name
    meta["description"] = entry.description
    if entry.license is not None:
        meta["license"] = entry.license

    # KB fields in metadata sub-mapping (all string values)
    inner: CommentedMap = CommentedMap()
    inner["topic"] = entry.topic
    inner["category"] = entry.category
    inner["source_url"] = entry.source_url
    if entry.github is not None:
        inner["github"] = entry.github
    if entry.version is not None:
        inner["version"] = DoubleQuotedScalarString(entry.version)
    # Dates serialized as ISO strings (not YAML date objects)
    inner["verified"] = DoubleQuotedScalarString(str(entry.verified))
    inner["next_review"] = DoubleQuotedScalarString(str(entry.next_review))
    if entry.tags:
        inner["tags"] = DoubleQuotedScalarString(",".join(entry.tags))

    meta["metadata"] = inner

    return frontmatter.Post(entry.body, handler=_handler, **meta)


def format_update_block(content: str, today: date) -> str:
    """Format an update section block.

    Args:
        content: Update content text.
        today: Date to label the section.

    Returns:
        Formatted markdown update block.
    """
    return f"\n\n## Update: {today.isoformat()}\n\n{content.strip()}"


# ---------------------------------------------------------------------------
# Name validation (Agent Skills spec)
# ---------------------------------------------------------------------------


def validate_name(name: str) -> bool:
    """Check whether a name satisfies the Agent Skills spec constraints.

    Rules:
    - 1-64 characters
    - Lowercase alphanumeric characters and hyphens only
    - No leading or trailing hyphen
    - No consecutive hyphens

    Args:
        name: Kebab-case slug to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not name or len(name) > _NAME_MAX_LEN:
        return False
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", name):
        return False
    return "--" not in name


# ---------------------------------------------------------------------------
# Levenshtein distance for suggestions
# ---------------------------------------------------------------------------


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings.

    Args:
        a: First string.
        b: Second string.

    Returns:
        Integer edit distance.
    """
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for ch_a in a:
        curr = [prev[0] + 1]
        for j, ch_b in enumerate(b):
            curr.append(min(prev[j] + (ch_a != ch_b), curr[-1] + 1, prev[j + 1] + 1))
        prev = curr
    return prev[-1]


def _find_suggestions(topic: str, all_topics: list[str]) -> list[str]:
    """Find close topic slug suggestions using Levenshtein distance.

    Args:
        topic: The requested topic slug.
        all_topics: All known topic slugs.

    Returns:
        Up to 3 suggestions with distance <= 2.
    """
    candidates = [
        t for t in all_topics if _levenshtein(topic, t) <= _LEVENSHTEIN_MAX_DISTANCE
    ]
    return sorted(candidates, key=lambda t: _levenshtein(topic, t))[:_MAX_SUGGESTIONS]


# ---------------------------------------------------------------------------
# Helper: first paragraph extraction
# ---------------------------------------------------------------------------


def _extract_first_paragraph(body: str) -> str:
    """Extract the first non-heading, non-blank paragraph from body text.

    Args:
        body: Markdown body text.

    Returns:
        First paragraph text, or empty string.
    """
    in_para = False
    para_lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_para:
                break
            continue
        if stripped.startswith("#"):
            if in_para:
                break
            continue
        in_para = True
        para_lines.append(stripped)
    return " ".join(para_lines)


# ---------------------------------------------------------------------------
# Rich helper
# ---------------------------------------------------------------------------


def _show_error(
    message: str, *, verbose: bool = False, exc: BaseException | None = None
) -> None:
    """Display an error panel on stderr.

    Args:
        message: Error message to display.
        verbose: If True and exc is provided, print traceback.
        exc: Exception to optionally print traceback for.
    """
    err_console.print(Panel(message, title="Error", border_style="red", expand=False))
    if verbose and exc is not None:
        err_console.print_exception()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _auto_description(entry: KBEntry) -> tuple[str, str | None]:
    """Compute a description for an entry that has none, with a warning message.

    Args:
        entry: Entry whose description is empty or missing.

    Returns:
        Tuple of (description, warning_message). warning_message is None when no
        auto-generation was necessary.
    """
    first_para = _extract_first_paragraph(entry.body)
    if first_para:
        desc = first_para[:_DESCRIPTION_MAX_LEN]
        warn = "description not set; auto-generated from body first paragraph."
    else:
        desc = (
            f"Research entry for {entry.name}. "
            f"Use when working with {entry.name} or related tools."
        )
        warn = (
            "description not set; using auto-generated fallback. "
            "Consider adding a description."
        )
    return desc, warn


def _validate_add_entry(entry: KBEntry) -> str | None:
    """Run all add-command validations on entry.

    Returns an error string (exit code 2) or None when valid.
    Mutates entry.description if it was empty.

    Args:
        entry: Entry to validate.

    Returns:
        Error message string, or None when the entry is valid.
    """
    if not validate_name(entry.topic):
        return (
            f"Topic '{entry.topic}' is not a valid Agent Skills name.\n"
            "Must be 1-64 chars, lowercase alphanumeric + hyphens, "
            "no leading/trailing/consecutive hyphens."
        )
    if entry.category not in VALID_CATEGORIES:
        return (
            f"Invalid category '{entry.category}'.\n"
            f"Valid categories: {', '.join(sorted(VALID_CATEGORIES))}"
        )
    missing = [
        f
        for f in ("topic", "name", "category", "source_url", "verified", "next_review")
        if not getattr(entry, f, None)
    ]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"
    if len(entry.description) > _DESCRIPTION_MAX_LEN:
        return (
            f"description is {len(entry.description)} chars; "
            f"max is {_DESCRIPTION_MAX_LEN}.\n"
            "Shorten the description field."
        )
    return None


# ---------------------------------------------------------------------------
# Typer app
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="knowledge-explorer",
    help="Manage the research/ knowledge base.",
    no_args_is_help=False,
    add_completion=False,
)

_verbose_state: dict[str, bool] = {"verbose": False}


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show tracebacks on error.")
    ] = False,
) -> None:
    """Knowledge base explorer. Run without a subcommand to list entries.

    Args:
        ctx: Typer context.
        verbose: Enable verbose error output.
    """
    _verbose_state["verbose"] = verbose
    if ctx.invoked_subcommand is None:
        list_kb()


# ---------------------------------------------------------------------------
# list command
# ---------------------------------------------------------------------------


@app.command("list")
def list_kb() -> None:
    """Show a tree view of all knowledge base entries.

    Displays category summaries with entry count and overdue count,
    plus per-entry version, verified date, review date, and overdue status.
    """
    entries = build_tree(KB_ROOT)
    if not entries:
        console.print("[yellow]No entries found in knowledge base.[/yellow]")
        return

    # Group by category
    by_category: dict[str, list[KBEntry]] = {}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(entry)

    tree = Tree("[bold blue]research/[/bold blue]")
    for cat in sorted(by_category):
        cat_entries = sorted(by_category[cat], key=lambda e: e.file_path.name)
        overdue_count = sum(1 for e in cat_entries if e.is_overdue)
        cat_label = (
            f"[cyan]{cat}/[/cyan]"
            f"  [dim]({len(cat_entries)} entries, {overdue_count} overdue)[/dim]"
        )
        cat_branch = tree.add(cat_label)
        for entry in cat_entries:
            version_str = entry.version or "no version"
            overdue_str = " [red][OVERDUE][/red]" if entry.is_overdue else ""
            label = (
                f"[green]{entry.file_path.name}[/green]"
                f"  {version_str}"
                f"  [dim]verified {entry.verified.isoformat()}"
                f"  review {entry.next_review.isoformat()}[/dim]"
                f"{overdue_str}"
            )
            cat_branch.add(label)

    # Measure and print
    temp_con = Console(width=9999)
    measurement = Measurement.get(temp_con, temp_con.options, tree)
    tree_width = int(measurement.maximum)
    console.print(
        tree,
        crop=False,
        overflow="ignore",
        no_wrap=True,
        soft_wrap=True,
        width=max(tree_width, 80),
    )


# ---------------------------------------------------------------------------
# show-template command
# ---------------------------------------------------------------------------


@app.command("show-template")
def show_template() -> None:
    """Print the skill-spec compatible frontmatter template with body structure."""
    today = date.today()
    next_review = today + timedelta(days=_DEFAULT_REVIEW_DAYS)
    cats_comment = f"# one of: {', '.join(sorted(VALID_CATEGORIES))}"
    template = (
        "---\n"
        "name: kebab-case-identifier\n"
        "description: >-\n"
        "  Verified reference for <topic>. Use when configuring or working with\n"
        "  <topic> in deployments. Max 1024 chars.\n"
        "license: MIT\n"
        "metadata:\n"
        "  topic: kebab-case-identifier\n"
        f"  category: category-dir-name  {cats_comment}\n"
        "  source_url: https://...\n"
        "  github: owner/repo\n"
        '  version: "1.0.0"\n'
        f'  verified: "{today.isoformat()}"\n'
        f'  next_review: "{next_review.isoformat()}"\n'
        '  tags: "tag1,tag2"\n'
        "---\n"
        "\n"
        "# Display Name\n"
        "\n"
        "[Body content here — body must not repeat the inline header block or include a Freshness Tracking table]\n"
    )
    syntax = Syntax(template, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)


# ---------------------------------------------------------------------------
# fetch-github command
# ---------------------------------------------------------------------------


@app.command("fetch-github")
def fetch_github(
    repo: Annotated[str, typer.Argument(help="owner/repo slug")],
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write draft to file")
    ] = None,
    category: Annotated[
        str | None, typer.Option("--category", "-c", help="Override inferred category")
    ] = None,
) -> None:
    """Fetch README and docs/ from GitHub and output a draft entry.

    Args:
        repo: GitHub 'owner/repo' slug.
        output: Optional file path to write draft to.
        category: Override inferred category.
    """
    verbose = _verbose_state["verbose"]
    try:
        if category is not None and category not in VALID_CATEGORIES:
            _show_error(
                f"Invalid category '{category}'.\n"
                f"Valid categories: {', '.join(sorted(VALID_CATEGORIES))}"
            )
            raise typer.Exit(code=2)

        with console.status(f"Fetching metadata for [cyan]{repo}[/cyan]..."):
            meta = fetch_github_metadata(repo)

        # Resolve category: explicit > inferred from topics > prompt user
        resolved_category: str
        if category is not None:
            resolved_category = category
        else:
            inferred = _infer_category(meta)
            if inferred is not None:
                resolved_category = inferred
                console.print(
                    f"[dim]Category inferred from GitHub topics:[/dim] [cyan]{resolved_category}[/cyan]"
                )
            else:
                valid_sorted = sorted(VALID_CATEGORIES)
                console.print(
                    "[yellow]No matching category found in GitHub topics.[/yellow]\n"
                    f"Valid categories: {', '.join(valid_sorted)}"
                )
                while True:
                    chosen = typer.prompt("Enter category")
                    if chosen in VALID_CATEGORIES:
                        resolved_category = chosen
                        break
                    console.print(
                        f"[red]'{chosen}' is not a valid category.[/red] "
                        f"Choose from: {', '.join(valid_sorted)}"
                    )

        # Fetch README text
        readme_text = ""
        try:
            _require_gh()
            readme_data = _gh_api(f"repos/{repo}/readme")
            readme_text = base64.b64decode(readme_data["content"]).decode("utf-8")
        except (ExternalCommandError, KeyError):
            readme_text = "<!-- README not available -->"

        entry = build_draft(repo, meta, resolved_category)

        body_parts = [
            f"# {entry.name}",
            "",
            f"> {meta.description}",
            "",
            "<!-- DRAFT: Review category and tags, then run: ./knowledge-explorer.py add <this-file> -->",
            "",
            readme_text,
        ]
        if meta.has_docs_dir and meta.docs_files:
            doc_lines = "\n".join(meta.docs_files)
            body_parts.extend([
                "",
                "<!-- docs/ files found (fetch manually if needed):",
                doc_lines,
                "-->",
            ])
        entry.body = "\n".join(body_parts)

        post = entry_to_post(entry)
        draft_content = frontmatter.dumps(post, handler=_handler)

        if output is not None:
            tmp = output.with_suffix(".tmp")
            tmp.write_text(draft_content, encoding="utf-8")
            tmp.replace(output)
            console.print(f"[green]OK[/green] Draft written to [green]{output}[/green]")
        else:
            console.print(draft_content)

    except KBError as exc:
        _show_error(str(exc), verbose=verbose, exc=exc)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# update-append command
# ---------------------------------------------------------------------------


@app.command("update-append")
def update_append(
    topic: Annotated[str, typer.Argument(help="kebab-case topic slug")],
) -> None:
    """Find entry by topic, open editor for update content, append section.

    Args:
        topic: Kebab-case topic slug to find and update.
    """
    verbose = _verbose_state["verbose"]
    try:
        path = find_entry_by_topic(topic, KB_ROOT)
        if path is None:
            entries = build_tree(KB_ROOT)
            all_topics = [e.topic for e in entries]
            suggestions = _find_suggestions(topic, all_topics)
            raise TopicNotFoundError(topic=topic, suggestions=suggestions)

        entry = parse_entry(path)

        # Migrate if needed
        if not entry.has_frontmatter:
            entry = migrate_entry(entry)
            write_entry(entry, path)
            entry = parse_entry(path)

        # Open editor
        template = "<!-- Replace this with your update content -->"
        update_content = typer.edit(template) or ""
        if not update_content.strip() or update_content.strip() == template.strip():
            console.print("[yellow]No update content provided. Aborted.[/yellow]")
            raise typer.Exit(code=0)

        today = date.today()
        update_block = format_update_block(update_content, today)

        # Update frontmatter dates
        entry.verified = today
        entry.next_review = today + timedelta(days=_DEFAULT_REVIEW_DAYS)
        entry.body = entry.body.rstrip() + update_block

        write_entry(entry, path)
        rel = path.relative_to(KB_ROOT)
        console.print(f"[green]OK[/green] Updated [green]{rel}[/green]")

    except KBError as exc:
        _show_error(str(exc), verbose=verbose, exc=exc)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# add command
# ---------------------------------------------------------------------------


@app.command("add")
def add(
    file: Annotated[
        Path | None,
        typer.Argument(help="Entry file with frontmatter; omit to read stdin"),
    ] = None,
) -> None:
    """Read a frontmatter entry and add it to the knowledge base.

    Validates, routes to the correct category directory, and updates README.md.

    Args:
        file: Path to entry file. Reads stdin if omitted.
    """
    verbose = _verbose_state["verbose"]
    try:
        text = (
            file.read_text(encoding="utf-8") if file is not None else sys.stdin.read()
        )

        # Pre-write validation
        if _detect_format_safe(text) != "frontmatter":
            _show_error(
                "Input is not in frontmatter format.\n"
                "Run [bold]./knowledge-explorer.py show-template[/bold] to see the required format."
            )
            raise typer.Exit(code=1)

        entry = parse_frontmatter_entry(text, file or Path("<stdin>"))

        # Warn (don't error) if description is missing — auto-generate from body
        if not entry.description.strip():
            entry.description, warn = _auto_description(entry)
            console.print(f"[yellow]Warning:[/yellow] {warn}")

        # Validate all fields; returns error string or None
        err = _validate_add_entry(entry)
        if err:
            _show_error(err)
            raise typer.Exit(code=2)

        # Determine target path
        target_dir = KB_ROOT / entry.category
        target_path = target_dir / f"{entry.topic}.md"

        # Check for conflicts
        if target_path.exists():
            existing = parse_entry(target_path)
            if existing.topic != entry.topic:
                raise TopicConflictError(
                    target_path=target_path,
                    existing_topic=existing.topic,
                    new_topic=entry.topic,
                )

        # Ensure category directory exists
        if not KB_ROOT.exists():
            _show_error(f"KB_ROOT does not exist: {KB_ROOT}")
            raise typer.Exit(code=1)
        target_dir.mkdir(parents=False, exist_ok=True)

        write_entry(entry, target_path)

        try:
            update_readme(KB_ROOT, entry)
        except ReadmeUpdateError as exc:
            console.print(f"[yellow]Warning: README update failed: {exc}[/yellow]")

        rel = target_path.relative_to(KB_ROOT)
        console.print(f"[green]OK[/green] Added [green]{rel}[/green]")

    except KBError as exc:
        _show_error(str(exc), verbose=verbose, exc=exc)
        raise typer.Exit(code=1) from exc


# ---------------------------------------------------------------------------
# migrate command
# ---------------------------------------------------------------------------


def _migrate_frontmatter_path(
    path: Path, text: str, dry_run: bool, result: MigrationResult
) -> None:
    """Migrate a single frontmatter file from old flat format to skill-spec.

    Skips files already in new format. Appends to result in-place.

    Args:
        path: Path to the file being processed.
        text: Raw file content.
        dry_run: When True, log intent without writing.
        result: MigrationResult to update in-place.
    """
    try:
        post = frontmatter.loads(text, handler=_handler)
    except (ValueError, KeyError, TypeError) as yaml_exc:
        result.failed.append((path, f"YAML parse error: {yaml_exc}"))
        return

    if _is_new_skill_format(post.metadata):
        result.already_migrated.append(path)
        return

    try:
        entry = parse_frontmatter_entry(text, path)
    except KBError as exc:
        result.failed.append((path, str(exc)))
        return

    if entry.category not in VALID_CATEGORIES:
        result.failed.append((path, f"Unknown category '{entry.category}'"))
        return

    migrated = migrate_entry(entry)
    rel = path.relative_to(KB_ROOT)
    if dry_run:
        console.print(
            f"[yellow]Would upgrade[/yellow] {rel} "
            f"[dim](flat frontmatter -> skill-spec)[/dim]"
        )
    else:
        write_entry(migrated, path)
        console.print(
            f"[green]Upgraded[/green] {rel} [dim](flat frontmatter -> skill-spec)[/dim]"
        )
    result.migrated.append(path)


def _migrate_inline_path(
    path: Path, text: str, dry_run: bool, result: MigrationResult
) -> None:
    """Migrate a single inline-header file to skill-spec frontmatter.

    Appends to result in-place.

    Args:
        path: Path to the file being processed.
        text: Raw file content.
        dry_run: When True, log intent without writing.
        result: MigrationResult to update in-place.
    """
    try:
        entry = parse_inline_header_entry(text, path)
    except KBError as exc:
        result.failed.append((path, str(exc)))
        return

    if entry.category not in VALID_CATEGORIES:
        result.failed.append((path, f"Unknown category '{entry.category}'"))
        return

    migrated = migrate_entry(entry)
    rel = path.relative_to(KB_ROOT)
    if dry_run:
        console.print(
            f"[yellow]Would migrate[/yellow] {rel} "
            f"[dim](inline-header -> skill-spec)[/dim]"
        )
    else:
        write_entry(migrated, path)
        console.print(
            f"[green]Migrated[/green] {rel} [dim](inline-header -> skill-spec)[/dim]"
        )
    result.migrated.append(path)


def _is_new_skill_format(meta: dict[str, Any]) -> bool:
    """Return True when frontmatter already uses the new skill-spec layout.

    The new format has a ``metadata`` sub-mapping containing ``topic``.

    Args:
        meta: Parsed frontmatter metadata dict.

    Returns:
        True if already in new skill-spec format.
    """
    inner = meta.get("metadata")
    return isinstance(inner, dict) and "topic" in inner


@app.command("migrate")
def migrate(
    all_entries: Annotated[
        bool, typer.Option("--all", help="Migrate all entries (default behaviour)")
    ] = True,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would change without writing")
    ] = False,
) -> None:
    """Migrate entries to skill-spec compatible frontmatter format in-place.

    Handles two source formats:
    - Inline-header (``# Heading`` + bold/table fields) → skill-spec frontmatter
    - Old flat frontmatter (top-level KB fields) → skill-spec frontmatter (fields
      moved into ``metadata`` sub-mapping)

    Entries already in skill-spec format are skipped.

    Args:
        all_entries: Migrate all entries (default).
        dry_run: Show what would change without writing.
    """
    verbose = _verbose_state["verbose"]
    result = MigrationResult()

    for path in _iter_kb_files(KB_ROOT):
        try:
            text = path.read_text(encoding="utf-8")
            fmt = _detect_format_safe(text)

            if fmt == "frontmatter":
                _migrate_frontmatter_path(path, text, dry_run, result)
            elif fmt == "inline-header":
                _migrate_inline_path(path, text, dry_run, result)
            else:
                result.failed.append((path, "Unrecognised format"))

        except KBError as exc:
            result.failed.append((path, str(exc)))
            if verbose:
                err_console.print(f"[red]Failed[/red] {path}: {exc}")

    console.print(
        f"\nMigrated: [green]{len(result.migrated)}[/green]  "
        f"Already done: [blue]{len(result.already_migrated)}[/blue]  "
        f"Failed: [red]{len(result.failed)}[/red]"
    )
    if result.failed:
        for fail_path, reason in result.failed:
            console.print(
                f"  [red]FAILED[/red] {fail_path.relative_to(KB_ROOT)}: {reason}"
            )


# ---------------------------------------------------------------------------
# generate-descriptions command
# ---------------------------------------------------------------------------

_FALLBACK_DESCRIPTION_PATTERN: re.Pattern[str] = re.compile(
    r"^Research entry for .+\. Use when working with .+ or related tools\.$"
)

_GENERATE_PROMPT_TEMPLATE = """\
Write a single-line frontmatter description for a knowledge base entry about "{name}" in the "{category}" category.

Rules:
- Single line, no newlines
- No colons (:) -- rephrase around them
- Max 1024 characters
- Front-load what the KB covers, then when an agent should load it
- Include specific trigger keywords (tool name, alternatives, use cases)
- Format: "{{what it covers}}. Use when {{trigger scenarios}}."

Tags: {tags}

Entry body (first 2000 chars):
{body}

Output ONLY the description string. No quotes, no YAML, no explanation."""


def _is_bad_description(entry: KBEntry) -> bool:
    """Return True when the entry's description should be regenerated.

    Heuristics:
    - Empty or missing description.
    - Description ends with '...' (truncated auto-generated text).
    - Description matches the fallback pattern used during inline-header migration.
    - Description is identical to or a leading substring of the first body paragraph.

    Args:
        entry: Entry to evaluate.

    Returns:
        True if the description is absent or low-quality.
    """
    desc = entry.description.strip()
    if not desc:
        return True
    if desc.endswith("..."):
        return True
    if _FALLBACK_DESCRIPTION_PATTERN.match(desc):
        return True
    first_para = _extract_first_paragraph(entry.body)
    return bool(first_para and (desc == first_para or first_para.startswith(desc)))


def _require_claude() -> str:
    """Return the claude binary path or raise ExternalCommandError.

    Returns:
        Path to claude binary.

    Raises:
        ExternalCommandError: If claude is not found on PATH.
    """
    path = shutil.which("claude")
    if path is None:
        raise ExternalCommandError(
            command="claude", hint="Install Claude Code CLI: https://claude.ai/code"
        )
    return path


def _call_claude_for_description(entry: KBEntry, claude_path: str) -> str:
    """Call the claude CLI to generate a description for the entry.

    Args:
        entry: KB entry to generate a description for.
        claude_path: Absolute path to the claude binary.

    Returns:
        Generated description string (stripped, unquoted).

    Raises:
        ExternalCommandError: If the claude CLI returns a non-zero exit code.
        ValueError: If the generated description fails validation.
    """
    tags_str = ",".join(entry.tags) if entry.tags else "(none)"
    body_excerpt = entry.body[:2000]
    prompt = _GENERATE_PROMPT_TEMPLATE.format(
        name=entry.name, category=entry.category, tags=tags_str, body=body_excerpt
    )
    # Unset CLAUDECODE so that the nested claude invocation is not blocked by
    # the nested-session guard that Claude Code sets when it launches.
    # On Windows, Claude Code requires CLAUDE_CODE_GIT_BASH_PATH. We probe common
    # Scoop and system locations so the subprocess can start regardless of whether
    # the parent session had the variable set.
    bash_candidates: list[str] = [
        r"C:\Users\{}\scoop\apps\git\current\usr\bin\bash.exe".format(
            os.environ.get("USERNAME", "")
        ),
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
    ]
    clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    if not clean_env.get("CLAUDE_CODE_GIT_BASH_PATH"):
        for candidate in bash_candidates:
            if Path(candidate).is_file():
                clean_env["CLAUDE_CODE_GIT_BASH_PATH"] = candidate
                break
    try:
        result = subprocess.run(
            [
                claude_path,
                "--print",
                "--model",
                "claude-haiku-4-5-20251001",
                "-p",
                prompt,
            ],
            capture_output=True,
            text=True,
            check=True,
            env=clean_env,
        )
    except subprocess.CalledProcessError as exc:
        raise ExternalCommandError(
            command="claude --print",
            hint="Check claude CLI authentication and model availability.",
            stderr=exc.stderr,
        ) from exc

    raw = result.stdout.strip()
    # Strip surrounding quotes the model may have added
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        raw = raw[1:-1].strip()

    if "\n" in raw:
        raise ValueError(f"Generated description contains newlines: {raw!r}")
    if len(raw) > _DESCRIPTION_MAX_LEN:
        raise ValueError(
            f"Generated description is {len(raw)} chars; max is {_DESCRIPTION_MAX_LEN}."
        )
    if not raw:
        raise ValueError("Generated description is empty.")

    return raw


def _collect_candidates(
    topic: str | None, all_entries: bool, verbose: bool
) -> list[KBEntry]:
    """Resolve the list of KB entries to process for description generation.

    Args:
        topic: When provided, restrict to the single entry with this slug.
        all_entries: When True, include entries with good descriptions too.
        verbose: Pass through to error display.

    Returns:
        List of KBEntry objects to process.

    Raises:
        typer.Exit: On topic-not-found or parse errors.
    """
    if topic is not None:
        path = find_entry_by_topic(topic, KB_ROOT)
        if path is None:
            all_known = build_tree(KB_ROOT)
            suggestions = _find_suggestions(topic, [e.topic for e in all_known])
            _show_error(str(TopicNotFoundError(topic=topic, suggestions=suggestions)))
            raise typer.Exit(code=1)
        try:
            return [parse_entry(path)]
        except KBError as exc:
            _show_error(str(exc), verbose=verbose, exc=exc)
            raise typer.Exit(code=1) from exc

    candidates = build_tree(KB_ROOT)
    if not all_entries:
        candidates = [e for e in candidates if _is_bad_description(e)]
    return candidates


def _process_one_entry(
    entry: KBEntry, claude_path: str, dry_run: bool, verbose: bool
) -> bool:
    """Generate and optionally write a description for a single KB entry.

    Args:
        entry: Entry to update.
        claude_path: Path to the claude CLI binary.
        dry_run: When True, print but do not write.
        verbose: Pass through to error display.

    Returns:
        True when the entry was processed successfully, False on failure.
    """
    rel = entry.file_path.relative_to(KB_ROOT)
    try:
        with console.status(
            f"Generating description for [cyan]{entry.topic}[/cyan]..."
        ):
            description = _call_claude_for_description(entry, claude_path)
    except (ExternalCommandError, ValueError) as exc:
        _show_error(
            f"Failed to generate description for '{entry.topic}': {exc}",
            verbose=verbose,
            exc=exc,
        )
        return False

    if dry_run:
        console.print(
            f"[yellow]DRY-RUN[/yellow] [cyan]{entry.topic}[/cyan] "
            f"({len(description)} chars)\n  {description}"
        )
        return True

    entry.description = description
    target = migrate_entry(entry) if not entry.has_frontmatter else entry
    write_entry(target, entry.file_path)
    console.print(f"[green]OK[/green] {rel} \u2014 {len(description)} chars")
    return True


@app.command("generate-descriptions")
def generate_descriptions(
    all_entries: Annotated[
        bool,
        typer.Option("--all", help="Regenerate all descriptions, not just bad ones."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print generated descriptions without writing."),
    ] = False,
    topic: Annotated[
        str | None,
        typer.Option("--topic", help="Regenerate description for a single topic only."),
    ] = None,
) -> None:
    """Generate skill-compatible descriptions for KB entries using the Claude CLI.

    Scans for entries whose descriptions are missing, empty, truncated, or were
    auto-generated from body prose. Calls the claude CLI subprocess (claude haiku)
    to produce a proper single-line description following the write-frontmatter-description
    rules: no colons, max 1024 chars, front-loaded trigger keywords.

    Args:
        all_entries: When True, regenerate descriptions for every entry regardless of
            current quality.
        dry_run: When True, print generated descriptions but do not write files.
        topic: When provided, process only the entry with this topic slug.
    """
    verbose = _verbose_state["verbose"]

    try:
        claude_path = _require_claude()
    except ExternalCommandError as exc:
        _show_error(str(exc))
        raise typer.Exit(code=1) from exc

    candidates = _collect_candidates(topic, all_entries, verbose)

    if not candidates:
        console.print(
            "[green]All descriptions are already good. Nothing to do.[/green]"
        )
        return

    noun = "entry" if len(candidates) == 1 else "entries"
    console.print(f"[dim]Found {len(candidates)} {noun} to process.[/dim]")

    results = [
        _process_one_entry(entry, claude_path, dry_run, verbose) for entry in candidates
    ]
    ok_count = sum(results)
    fail_count = len(results) - ok_count

    summary_parts = [f"Processed: [green]{ok_count}[/green]"]
    if fail_count:
        summary_parts.append(f"Failed: [red]{fail_count}[/red]")
    console.print("\n" + "  ".join(summary_parts))

    if fail_count:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt as exc:
        err_console.print("\n[yellow]Interrupted.[/yellow]")
        raise typer.Exit(code=130) from exc
