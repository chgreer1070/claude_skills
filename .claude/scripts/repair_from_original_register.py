#!/usr/bin/env python3
"""Repair truncated backlog items and GitHub issues from the original register.

Reads .claude/original-backlog-register.md (pre-migration BACKLOG.md with full
untruncated descriptions), maps each item to its GitHub issue number, updates
per-item files in .claude/backlog/ with correct descriptions, then rebuilds
GitHub issue bodies with proper story format including groomed content.

Usage:
    uv run .claude/scripts/repair_from_original_register.py --dry-run
    uv run .claude/scripts/repair_from_original_register.py
"""

from __future__ import annotations

import os
import re
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from github import Auth, Github
from ruamel.yaml import YAML

if TYPE_CHECKING:
    from github.Issue import Issue

REPO_NAME = "Jamie-BitFlight/claude_skills"
REGISTER_PATH = Path(".claude/original-backlog-register.md")
BACKLOG_DIR = Path(".claude/backlog")

ROLE_MAP = {
    "Feature": "developer using Claude Code skills",
    "Bug": "developer relying on this plugin",
    "Refactor": "maintainer of the codebase",
    "Docs": "developer reading the documentation",
    "Chore": "maintainer of the project infrastructure",
}

BENEFIT_MAP = {
    "Feature": "the tooling becomes more capable and complete",
    "Bug": "the tool works correctly and reliably",
    "Refactor": "the code is cleaner and more maintainable",
    "Docs": "documentation is accurate and trustworthy",
    "Chore": "the project infrastructure stays healthy",
}

# Bold-key field prefix → dict key mapping (single-line fields)
_FIELD_MAP: dict[str, str] = {
    "**Source**:": "source",
    "**Added**:": "added",
    "**Priority**:": "priority_field",
    "**Description**:": "description",
    "**Research first**:": "research_first",
    "**Suggested location**:": "suggested_location",
    "**Files**:": "files",
    "**Plan**:": "plan",
    "**Completed**:": "completed",
    "**Status**:": "status",
    "**Type**:": "type",
    "**Issue**:": "issue_field",
}

# Fields whose values may span multiple lines (content continues until next
# bold-key field or end of body).  The parser collects continuation lines.
_MULTILINE_FIELDS: set[str] = {"**Description**:", "**Files**:", "**Status**:", "**Citations**:"}

_yaml = YAML()
_yaml.preserve_quotes = True


def parse_register() -> list[dict[str, str]]:
    """Parse the original backlog register into structured items.

    Captures both extracted fields AND the full raw body text so that
    non-standard content (sub-issues, validation steps, citations, etc.)
    is never lost.

    Returns:
        List of dicts with title, priority, full_body, and all field values
    """
    text = REGISTER_PATH.read_text(encoding="utf-8")
    items: list[dict[str, str]] = []
    current_priority = ""

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        current_priority = _detect_priority(line, current_priority)

        if line.startswith("### "):
            title = line[4:].strip()
            item: dict[str, str] = {"title": title, "priority": current_priority}

            i += 1
            body_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith(("### ", "## ")):
                body_lines.append(lines[i])
                i += 1

            body = "\n".join(body_lines).strip()
            item["full_body"] = body
            _extract_fields(body, item)
            items.append(item)
            continue

        i += 1

    return items


def _detect_priority(line: str, current: str) -> str:
    """Detect priority section from H2 heading line.

    Args:
        line: Current line being parsed
        current: Current priority value

    Returns:
        Updated priority string
    """
    priority_prefixes = {"## P0": "P0", "## P1": "P1", "## P2": "P2", "## Ideas": "Ideas", "## Completed": "Completed"}
    for prefix, priority in priority_prefixes.items():
        if line.startswith(prefix):
            return priority
    return current


def _match_field_prefix(stripped: str) -> tuple[str | None, str | None]:
    """Match a line against known bold-key field prefixes.

    Args:
        stripped: Stripped line text

    Returns:
        Tuple of (matched prefix, dict key) or (None, None)
    """
    for prefix, key in _FIELD_MAP.items():
        if stripped.startswith(prefix):
            return prefix, key
    return None, None


def _is_bold_key_line(line: str) -> bool:
    """Check if a line starts with any recognized bold-key field prefix.

    Args:
        line: Stripped line text

    Returns:
        True if the line is a bold-key field header
    """
    return _match_field_prefix(line)[0] is not None


def _collect_multiline_value(lines: list[str], start: int, first_value: str) -> tuple[str, int]:
    """Collect a multi-line field value from consecutive lines.

    Reads continuation lines until the next bold-key field or end of body.

    Args:
        lines: All body lines
        start: Index of the first continuation line (after the field header)
        first_value: Value text from the header line itself

    Returns:
        Tuple of (collected value string, next line index to process)
    """
    value_lines = [first_value] if first_value else []
    i = start
    while i < len(lines):
        if _is_bold_key_line(lines[i].strip()):
            break
        if lines[i].strip():
            value_lines.append(lines[i].rstrip())
        elif value_lines:
            value_lines.append("")
        i += 1
    return "\n".join(value_lines).strip(), i


def _extract_fields(body: str, item: dict[str, str]) -> None:
    """Extract bold-key fields from item body text, including multi-line values.

    Multi-line fields (Description, Files, Status, Citations) collect
    continuation lines until the next bold-key field or end of body.

    Args:
        body: Raw body text of the backlog item
        item: Dict to populate with extracted fields
    """
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        matched_prefix, matched_key = _match_field_prefix(stripped)

        if not matched_prefix or not matched_key:
            i += 1
            continue

        first_line_value = stripped.split(":", 1)[1].strip()

        # Extract issue number from **Issue**: field
        if matched_key == "issue_field":
            issue_match = re.search(r"#(\d+)", first_line_value)
            if issue_match:
                item["issue_number"] = issue_match.group(1)
            i += 1
            continue

        # For multi-line fields, collect continuation lines
        if matched_prefix in _MULTILINE_FIELDS:
            item[matched_key], i = _collect_multiline_value(lines, i + 1, first_line_value)
        else:
            item[matched_key] = first_line_value
            i += 1


def normalize_title(title: str) -> str:
    """Normalize a title for matching.

    Args:
        title: Raw title string

    Returns:
        Lowercased, prefix-stripped title
    """
    clean = re.sub(r"^(feat|fix|chore|docs|refactor):\s*", "", title)
    clean = re.sub(r"^P[012]:\s*", "", clean)
    return clean.lower().strip()


def match_items_to_issues(
    items: list[dict[str, str]], issues: list[Issue]
) -> list[tuple[dict[str, str], Issue | None]]:
    """Match register items to GitHub issues by title.

    Args:
        items: Parsed register items
        issues: Open GitHub issues

    Returns:
        List of (item, matched_issue_or_None) tuples
    """
    issue_map: dict[str, Issue] = {}
    for issue in issues:
        key = normalize_title(issue.title)
        issue_map[key] = issue

    results: list[tuple[dict[str, str], Issue | None]] = []
    for item in items:
        key = normalize_title(item["title"])
        matched = issue_map.get(key)
        if not matched:
            matched = _fuzzy_match(key, issue_map)
        results.append((item, matched))

    return results


def _fuzzy_match(key: str, issue_map: dict[str, Issue]) -> Issue | None:
    """Fuzzy match a key against issue map by substring containment.

    Args:
        key: Normalized title to match
        issue_map: Map of normalized titles to issues

    Returns:
        Matched issue or None
    """
    for issue_key, issue in issue_map.items():
        if issue_key in key or key in issue_key:
            return issue
    return None


def _find_per_item_file(item: dict[str, str]) -> Path | None:
    """Find the per-item backlog file for a register item.

    Args:
        item: Parsed item dict

    Returns:
        Path to the per-item file or None
    """
    slug = re.sub(r"[^a-z0-9]+", "-", item["title"].lower()).strip("-")[:60]
    priority = item["priority"].lower()

    candidates = list(BACKLOG_DIR.glob(f"{priority}-{slug[:30]}*.md"))
    if not candidates:
        candidates = list(BACKLOG_DIR.glob(f"*{slug[:20]}*.md"))
    if candidates:
        return candidates[0]
    return None


def _read_groomed_content(path: Path) -> str:
    """Read groomed content from a per-item backlog file.

    Extracts everything after the first '## Groomed' heading.

    Args:
        path: Path to the per-item markdown file

    Returns:
        Groomed content string, or empty string if none found
    """
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(## Groomed.*)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_additional_content(item: dict[str, str]) -> str:
    """Extract content from full_body not covered by extracted fields.

    Removes lines that were already captured by _extract_fields (bold-key
    metadata lines) and returns everything else — sub-issues, bullet lists,
    numbered steps, citations, free-form paragraphs, etc.

    Args:
        item: Parsed item dict with full_body and extracted fields

    Returns:
        Additional content string, or empty if nothing extra
    """
    full_body = item.get("full_body", "")
    if not full_body:
        return ""

    # Keys whose content we already include in structured sections
    covered_prefixes = set(_FIELD_MAP.keys()) | {"**Issue**:"}

    result_lines: list[str] = []
    lines = full_body.split("\n")
    i = 0
    skip_continuation = False

    while i < len(lines):
        stripped = lines[i].strip()

        # Check if this line starts a bold-key field we already extract
        is_covered = any(stripped.startswith(p) for p in covered_prefixes)

        if is_covered:
            # Skip this line and its multi-line continuation
            skip_continuation = stripped.startswith(tuple(_MULTILINE_FIELDS))
            i += 1
            if skip_continuation:
                while i < len(lines) and not _is_bold_key_line(lines[i].strip()):
                    i += 1
                skip_continuation = False
            continue

        # Not a covered field — include this line
        result_lines.append(lines[i].rstrip())
        i += 1

    content = "\n".join(result_lines).strip()

    # Remove separator lines (---)
    return re.sub(r"^---+\s*$", "", content, flags=re.MULTILINE).strip()


def build_story_body(item: dict[str, str], groomed_content: str = "") -> str:
    """Build a proper story-format issue body from a register item.

    Includes ALL content from the original register: structured fields
    in their proper sections, plus any additional free-text content
    (sub-issues, validation steps, citations, etc.) that doesn't fit
    into a named field.

    Args:
        item: Parsed item dict with full untruncated fields and full_body
        groomed_content: Optional groomed content from per-item file

    Returns:
        Formatted issue body string
    """
    title = item.get("title", "No title")
    description = item.get("description", title)
    item_type = item.get("type", "Feature")
    priority = item.get("priority", "Unknown")
    role = ROLE_MAP.get(item_type, "developer using Claude Code skills")
    benefit = BENEFIT_MAP.get(item_type, "the product improves")
    goal = title.rstrip(".")

    sections = [
        f"## Story\n\nAs a **{role}**, I want to **{goal.lower()}** so that **{benefit}**.",
        f"## Description\n\n{description}",
    ]

    # Additional content not captured by named fields
    additional = _extract_additional_content(item)
    if additional:
        sections.append(f"## Details\n\n{additional}")

    if item.get("files"):
        sections.append(f"## Files\n\n{item['files']}")

    if item.get("suggested_location"):
        sections.append(f"## Suggested Location\n\n{item['suggested_location']}")

    context_lines = [
        f"- **Source**: {item.get('source', 'Not specified')}",
        f"- **Priority**: {priority}",
        f"- **Added**: {item.get('added', 'Unknown')}",
        f"- **Research questions**: {item.get('research_first', 'None')}",
    ]
    if item.get("status"):
        context_lines.append(f"- **Status**: {item['status']}")
    sections.append("## Context\n\n" + "\n".join(context_lines))

    if item.get("plan"):
        sections.append(f"## Plan\n\n{item['plan']}")

    if groomed_content:
        sections.append(groomed_content)

    return "\n\n".join(sections) + "\n"


def update_per_item_file(item: dict[str, str]) -> bool:
    """Update the per-item backlog file with untruncated description.

    Args:
        item: Parsed item dict with full fields

    Returns:
        True if a file was updated
    """
    path = _find_per_item_file(item)
    if not path:
        return False

    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return False

    fm = _yaml.load(match.group(1))
    if not isinstance(fm, dict):
        return False

    old_desc = str(fm.get("description", ""))
    new_desc = item.get("description", old_desc)

    if len(new_desc) <= len(old_desc):
        return False

    fm["description"] = new_desc
    if item.get("source") and fm.get("metadata", {}).get("source") == "Not specified":
        fm["metadata"]["source"] = item["source"]

    stream = StringIO()
    _yaml.dump(fm, stream)
    new_fm = stream.getvalue().rstrip("\n")
    new_body = match.group(2).strip()

    path.write_text(f"---\n{new_fm}\n---\n\n{new_body}\n" if new_body else f"---\n{new_fm}\n---\n", encoding="utf-8")
    return True


def _process_pair(item: dict[str, str], issue: Issue | None, *, dry_run: bool) -> tuple[int, int, int]:
    """Process a single register-item / issue pair.

    Args:
        item: Parsed register item
        issue: Matched GitHub issue or None
        dry_run: If True, only print what would happen

    Returns:
        Tuple of (files_updated, issues_updated, no_issue) counts
    """
    title = item["title"]

    groomed_content = ""
    per_item_path = _find_per_item_file(item)
    if per_item_path:
        groomed_content = _read_groomed_content(per_item_path)

    if dry_run:
        issue_str = f"#{issue.number}" if issue else "NO MATCH"
        groomed_str = " [groomed]" if groomed_content else ""
        print(f"  {issue_str}\t{title}{groomed_str}")
        return 0, int(issue is not None), int(issue is None)

    files_updated = int(update_per_item_file(item))

    if issue:
        new_body = build_story_body(item, groomed_content)
        issue.edit(body=new_body)
        groomed_str = " [+groomed]" if groomed_content else ""
        print(f"  UPDATED #{issue.number}: {title}{groomed_str}")
        return files_updated, 1, 0

    print(f"  NO ISSUE: {title}")
    return files_updated, 0, 1


def main() -> None:
    """Repair truncated items from the original register."""
    dry_run = "--dry-run" in sys.argv

    if not REGISTER_PATH.exists():
        print(f"ERROR: {REGISTER_PATH} not found")
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    register_items = parse_register()
    active_items = [
        i
        for i in register_items
        if i["priority"] != "Completed"
        and "completed" not in i
        and "~~" not in i["title"]
        and not (i.get("status", "").upper().startswith(("DONE", "RESOLVED")))
    ]
    print(f"Parsed {len(register_items)} items from register ({len(active_items)} active)")

    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(REPO_NAME)
    open_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    print(f"Found {len(open_issues)} open GitHub issues")

    pairs = match_items_to_issues(active_items, open_issues)
    totals = [0, 0, 0]

    for item, issue in pairs:
        counts = _process_pair(item, issue, dry_run=dry_run)
        for idx in range(3):
            totals[idx] += counts[idx]

    print(f"\nDone: {totals[0]} files updated, {totals[1]} issues updated, {totals[2]} no match")


if __name__ == "__main__":
    main()
