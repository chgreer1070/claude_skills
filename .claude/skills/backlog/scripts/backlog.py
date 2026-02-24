#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "PyGithub>=2.1.1",
#   "typer>=0.21.0",
#   "python-frontmatter>=1.1.0",
#   "ruamel.yaml>=0.18.0",
# ]
# ///
"""Backlog CLI — single interface for BACKLOG.md and GitHub Issues.

All backlog and issue operations go through this script. Skills invoke it;
no direct edits to BACKLOG.md or GitHub.

Usage:
    backlog add --title X --priority P1 --description D [--source S] [--type T] [--create-issue]
    backlog list [--format text|json]
    backlog sync [--dry-run]
    backlog close <selector> --plan PATH --checklist-pass [--cleanup]
    backlog resolve <selector> --reason "reason" [--cleanup]
    backlog update <selector> [--plan PATH] [--status in-progress] [--create-issue]
    backlog groom <selector> [--groomed-content "..." | --groomed-file PATH | --section X --content "..." | stdin]
    backlog normalize  # one-off: rewrite per-item files to research-style metadata, remove body duplication
    backlog validate  # verify all index links resolve; exit 1 if any broken
    backlog fix-links  # rewrite .claude/backlog/ → backlog/ for editor click-to-open

Environment:
    GITHUB_TOKEN  Required for issue operations.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime

# Ensure UTF-8 output on Windows (cp1252 default cannot encode emoji/spinner chars).
# reconfigure() is available on Python 3.7+ when stdout is a TextIOWrapper.
from io import TextIOWrapper
from pathlib import Path
from typing import Annotated, Any

if isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from github import Auth, Github, GithubException
from github.Repository import Repository
from rich import box
from rich.console import Console
from rich.measure import Measurement
from rich.table import Table

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
# Add plugin-creator scripts for shared frontmatter_utils (before importing it)
_plugin_scripts = _REPO_ROOT / "plugins" / "plugin-creator" / "scripts"
if (_plugin_scripts / "frontmatter_utils.py").exists() and str(_plugin_scripts) not in sys.path:
    sys.path.insert(0, str(_plugin_scripts))

import frontmatter
from frontmatter_utils import dump_frontmatter, loads_frontmatter

BACKLOG_PATH = _REPO_ROOT / ".claude" / "BACKLOG.md"
BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"
DEFAULT_REPO = "Jamie-BitFlight/claude_skills"

# Regex
ITEM_HEADER_RE = re.compile(r"^###\s+(.+)$")
FIELD_RE = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$", re.DOTALL)
SECTION_RE = re.compile(r"^##\s+(P0|P1|P2|Ideas)")
SECTION_RE_MIGRATE = re.compile(r"^##\s+(P0|P1|P2|Ideas|Completed|Format Guide)")
SKIP_STATUS = ("DONE", "RESOLVED", "COMPLETED")
GITHUB_ISSUE_TITLE_TRUNCATE = 80
MIN_FRONTMATTER_PARTS = 3
TYPE_TO_LABEL = {
    "feature": "type:feature",
    "bug": "type:bug",
    "refactor": "type:refactor",
    "docs": "type:docs",
    "chore": "type:chore",
}

app = typer.Typer(help="Backlog and GitHub Issue CRUD — single interface")
_console = Console()


def _get_table_width(table: Table) -> int:
    """Get natural width of a Rich table for correct display."""
    temp_console = Console(width=9999)
    measurement = Measurement.get(temp_console, temp_console.options, table)
    return int(measurement.maximum)


def _get_github(repo: str) -> Repository:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        typer.echo("ERROR: GITHUB_TOKEN not set", err=True)
        raise typer.Exit(1)
    gh = Github(auth=Auth.Token(token))
    return gh.get_repo(repo)


def _infer_type(description: str, title: str) -> str:
    text = f"{title} {description}".lower()
    if any(w in text for w in ("fix", "bug", "broken", "vulnerability")):
        return "type:bug"
    if any(w in text for w in ("add", "create", "implement", "build")):
        return "type:feature"
    if any(w in text for w in ("refactor", "remove dead", "consolidate")):
        return "type:refactor"
    if any(w in text for w in ("document", "update readme", "docs")):
        return "type:docs"
    return "type:feature"


def _title_to_slug(title: str, max_len: int = 60) -> str:
    """Convert item title to filename slug."""
    # Strip strikethrough and status suffixes
    t = re.sub(r"^~~(.+)~~\s*(RESOLVED|COMPLETED)?\s*$", r"\1", title.strip())
    t = t.lower()
    t = re.sub(r"[:\[\]\(\)]", " ", t)
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"-+", "-", t).strip("-")
    return t[:max_len] if len(t) > max_len else t


def _is_index_format(path: Path) -> bool:
    """Check if BACKLOG.md uses index format (links to per-item files)."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "format: index" in text[:500] or ("- [" in text and ("](.claude/backlog/" in text or "](backlog/" in text))


def parse_backlog(path: Path) -> list[dict]:
    """Parse BACKLOG.md into items — supports both monolithic and index format."""
    if _is_index_format(path):
        return _parse_backlog_index(path)
    return _parse_backlog_monolithic(path)


def _flush_parsed_item(
    current_item: dict | None, current_body: list[str], current_field_value: list[str], items: list[dict], line_idx: int
) -> None:
    """Flush current item to items list, normalizing list values to strings."""
    if current_item is None:
        return
    for k, v in list(current_item.items()):
        if isinstance(v, list):
            current_item[k] = "\n".join(v).strip()
    current_item["_raw_body"] = "\n".join(current_body)
    current_item["_line_end"] = line_idx + 1
    items.append(current_item)


def _apply_field_to_item(current_item: dict, key: str, val: str, current_field_value: list[str]) -> list[str]:
    """Apply a field match to current_item. Returns new current_field_value."""
    key_lower = key.lower()
    if key_lower == "issue":
        current_item["_issue"] = val
        return []
    if (key_lower == "status" and val.upper().split()[0] in SKIP_STATUS) or key_lower in {"completed", "resolved"}:
        current_item["_skip"] = True
        return []
    if key_lower in {"source", "added", "priority", "type", "description", "research first"}:
        store_key = "**Research first**" if key_lower == "research first" else f"**{key}**"
        current_item[store_key] = [val]
        return current_item[store_key]
    return []


def _parse_backlog_lines(lines: list[str], section_re: re.Pattern[str], skip_strikethrough: bool) -> list[dict]:
    """Parse backlog lines into items. Shared by monolithic and migrate parsers."""
    items: list[dict] = []
    current_section: str | None = None
    current_item: dict | None = None
    current_body: list[str] = []
    current_field_value: list[str] = []

    for i, line in enumerate(lines):
        section_m = section_re.match(line)
        if section_m:
            _flush_parsed_item(current_item, current_body, current_field_value, items, i)
            current_section = section_m.group(1)
            current_item, current_body, current_field_value = None, [], []
            continue

        item_m = ITEM_HEADER_RE.match(line)
        if item_m:
            _flush_parsed_item(current_item, current_body, current_field_value, items, i)
            title = item_m.group(1).strip()
            if skip_strikethrough and title.startswith("~~") and "~~" in title[2:]:
                continue
            current_item = {"_section": current_section or "", "_title": title, "_line_start": i + 1}
            current_body = [line]
            current_field_value = []
            continue

        field_m = FIELD_RE.match(line)
        if field_m and current_item is not None:
            key, val = field_m.group(1).strip(), field_m.group(2).strip()
            current_field_value = _apply_field_to_item(current_item, key, val, current_field_value)
            current_body.append(line)
            continue

        if current_item is not None and current_field_value:
            if line.strip():
                current_field_value.append(line.strip())
            current_body.append(line)

    _flush_parsed_item(current_item, current_body, current_field_value, items, len(lines))
    return items


def _parse_backlog_monolithic(path: Path) -> list[dict]:
    """Parse monolithic BACKLOG.md into items with section, title, and fields."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return _parse_backlog_lines(lines, SECTION_RE, skip_strikethrough=True)


def _resolve_index_link_path(rel_path: str, backlog_path: Path) -> Path:
    """Resolve rel_path from index link to absolute filepath. Supports backlog/ and .claude/backlog/."""
    if rel_path.startswith(".claude/backlog/"):
        return (_REPO_ROOT / rel_path).resolve()
    return (backlog_path.parent / rel_path).resolve()


def _parse_backlog_index(path: Path) -> list[dict]:
    """Parse index-format BACKLOG.md and load items from per-item files."""
    text = path.read_text(encoding="utf-8")
    items: list[dict] = []
    link_re = re.compile(r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s*(#\d+)?\s*$")
    section_re = re.compile(r"^##\s+(P0|P1|P2|Ideas|Completed)")
    current_section = ""
    for line in text.splitlines():
        sec_m = section_re.match(line)
        if sec_m:
            current_section = sec_m.group(1)
            continue
        link_m = link_re.match(line)
        if link_m:
            title, rel_path, issue_link = (link_m.group(1), link_m.group(2), link_m.group(3) or "")
            if ".claude/backlog/" not in rel_path and "backlog/" not in rel_path:
                continue
            filepath = _resolve_index_link_path(rel_path, path)
            if not filepath.exists():
                typer.echo(f"WARNING: Index link target missing: {rel_path} (resolved to {filepath})", err=True)
                continue
            item_text = filepath.read_text(encoding="utf-8")
            item = _parse_item_file(item_text, filepath)
            item["_section"] = current_section
            item["_title"] = title
            # Prefer index link issue, fallback to per-item file (parser merge for 1:1 cache)
            item["_issue"] = (issue_link.strip() or item.get("_issue", "") or "").strip()
            item["_file_path"] = str(filepath)
            items.append(item)
    return items


def _parse_item_file(text: str, path: Path) -> dict:
    """Parse a single per-item backlog file (frontmatter + body). Handles both flat and research-style metadata block."""
    item: dict = {}
    if not text.startswith("---"):
        return {"_raw_body": text}
    try:
        post = loads_frontmatter(text)
        fm = post.metadata or {}
        body = post.content or ""
    except (ValueError, KeyError, TypeError):
        parts = text.split("---", 2)
        fm, body = {}, parts[2].strip() if len(parts) >= MIN_FRONTMATTER_PARTS else text
    meta_raw = fm.get("metadata")
    meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    # Research-style: name, description, metadata.*
    # Flat (legacy): title, source, added, ...
    item["_title"] = str(fm.get("name") or fm.get("title") or "")
    item["**Description**"] = str(fm.get("description") or "")
    item["**Source**"] = str(meta.get("source") or fm.get("source") or "")
    item["**Added**"] = str(meta.get("added") or fm.get("added") or "")
    item["**Priority**"] = str(meta.get("priority") or fm.get("priority") or "")
    item["_issue"] = str(meta.get("issue") or fm.get("issue") or "")
    item["**Plan**"] = str(meta.get("plan") or fm.get("plan") or "")
    status = str(meta.get("status") or fm.get("status") or "").lower()
    if status in {"done", "resolved"}:
        item["_skip"] = True
    groomed = meta.get("groomed") or fm.get("groomed")
    if groomed:
        item["_groomed"] = str(groomed)
    item["_raw_body"] = body
    if "_groomed" not in item and "## Groomed" in body:
        item["_groomed"] = "true"
    return item


def parse_backlog_migrate(path: Path) -> list[dict]:
    """Parse BACKLOG.md for migration — includes Completed section."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return _parse_backlog_lines(lines, SECTION_RE_MIGRATE, skip_strikethrough=False)


def find_item(items: list[dict], selector: str) -> dict | None:
    """Find item by title substring or #N."""
    selector = selector.strip()
    if selector.startswith("#"):
        num = selector.lstrip("#").strip()
        if num.isdigit():
            for it in items:
                issue_ref = it.get("_issue") or ""
                if issue_ref.lstrip("#") == num:
                    return it
            return None
    # Title substring match (case-insensitive)
    selector_lower = selector.lower()
    matches = [it for it in items if selector_lower in it.get("_title", "").lower()]
    return matches[0] if len(matches) == 1 else (matches[0] if matches else None)


def items_needing_issues(items: list[dict]) -> list[dict]:
    """Return backlog items in P0/P1 that lack GitHub issues and are not skipped."""
    return [it for it in items if it.get("_section") in {"P0", "P1"} and not it.get("_skip") and not it.get("_issue")]


def build_issue_body(item: dict) -> str:
    """Build GitHub issue body from backlog item fields."""
    title = item.get("_title", "")
    desc = item.get("**Description**", "")
    source = item.get("**Source**", "Not specified")
    added = item.get("**Added**", "")
    priority = item.get("**Priority**", "")
    research = item.get("**Research first**", "")
    first_sent = desc.split(".")[0].strip() if desc else title
    if len(first_sent) > GITHUB_ISSUE_TITLE_TRUNCATE:
        first_sent = first_sent[: GITHUB_ISSUE_TITLE_TRUNCATE - 3] + "..."
    return f"""## Story

As a **developer**, I want **{first_sent}** so that **backlog items are tracked in GitHub**.

## Description

{desc}

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: {source}
- **Priority**: {priority}
- **Added**: {added}
- **Research questions**: {research or "None"}
"""


def create_issue_for_item(repo: Repository, item: dict, dry_run: bool = False) -> int | None:
    """Create GitHub issue for backlog item. Returns issue number or None."""
    title = item.get("_title", "")
    if not title:
        return None
    type_label = item.get("**Type**", "")
    type_map = {"feature": "feat", "bug": "fix", "refactor": "refactor", "docs": "docs", "chore": "chore"}
    prefix = type_map.get(type_label.lower(), "feat")
    issue_title = f"{prefix}: {title}"
    body = build_issue_body(item)
    priority = item.get("**Priority**", "P1")
    type_gh = TYPE_TO_LABEL.get(type_label.lower()) or _infer_type(item.get("**Description**", ""), title)
    priority_gh = f"priority:{priority.lower()}"
    if dry_run:
        typer.echo(f"  [dry-run] Would create: {issue_title}")
        return None
    labels = ["status:needs-grooming", priority_gh, type_gh]
    label_objs = []
    for name in labels:
        try:
            label_objs.append(repo.get_label(name))
        except GithubException:
            typer.echo(f"  WARNING: label '{name}' not found", err=True)
    issue = repo.create_issue(title=issue_title, body=body, labels=label_objs)
    typer.echo(f"  Created #{issue.number}: {issue_title[:60]}...")
    return issue.number


def _create_issue_and_update_content(item: dict, content: str, repo: str) -> tuple[str, bool]:
    """Create GitHub issue for item and update content with issue link. Returns (content, modified)."""
    try:
        repository = _get_github(repo)
        issue_num = create_issue_for_item(repository, item, dry_run=False)
        if not issue_num:
            return content, False
        if _is_index_format(BACKLOG_PATH):
            filepath_str = item.get("_file_path")
            if filepath_str:
                _update_item_metadata(Path(filepath_str), {"metadata": {"issue": f"#{issue_num}"}})
                old_line = _find_index_link_line(content, item)
                if old_line:
                    title = item.get("_title", "")
                    filename = Path(filepath_str).name
                    rel_path = f"backlog/{filename}"
                    new_line = _index_link_line(title, rel_path, f"#{issue_num}")
                    return content.replace(old_line, new_line), True
            return content, False
        return insert_issue_into_content(content, item, issue_num), True
    except GithubException as e:
        typer.echo(f"  WARNING: Issue creation failed: {e}", err=True)
        return content, False


def insert_issue_into_content(content: str, item: dict, issue_num: int) -> str:
    """Insert **Issue**: #N line into BACKLOG.md content for given item."""
    new_line = f"**Issue**: #{issue_num}"
    if new_line in item.get("_raw_body", ""):
        return content
    lines = content.splitlines()
    start = max(0, item.get("_line_start", 1) - 1)
    for i in range(start, min(start + 25, len(lines))):
        if i > start and (lines[i].startswith("###") or lines[i].startswith("## ")):
            break
        if re.match(r"^\*\*Priority\*\*:", lines[i]) or re.match(r"^\*\*Type\*\*:", lines[i]):
            indent = "  " if lines[i].startswith("  ") else ""
            lines.insert(i + 1, f"{indent}{new_line}")
            return "\n".join(lines) + "\n"
    for i in range(start, min(start + 15, len(lines))):
        if re.match(r"^\*\*[^*]+\*\*:", lines[i]):
            indent = "  " if lines[i].startswith("  ") else ""
            lines.insert(i + 1, f"{indent}{new_line}")
            return "\n".join(lines) + "\n"
    return content


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _update_item_metadata(filepath: Path, updates: dict[str, Any]) -> None:
    """Update per-item file frontmatter. Supports nested metadata.plan, metadata.issue, etc."""
    post = loads_frontmatter(filepath.read_text(encoding="utf-8"))
    meta = post.metadata or {}
    for key, value in updates.items():
        if key == "metadata" and isinstance(value, dict):
            nested = meta.get("metadata")
            if nested is None or not isinstance(nested, dict):
                nested = {}
            nested.update(value)
            meta["metadata"] = nested
        else:
            meta[key] = value
    post.metadata = meta
    filepath.write_text(dump_frontmatter(post), encoding="utf-8")


def _index_link_line(title: str, rel_path: str, issue: str | None) -> str:
    """Build index link line. rel_path canonical: backlog/{filename}."""
    suffix = f" {issue}" if issue else ""
    return f"- [{title}]({rel_path}){suffix}"


def _add_index_link(content: str, section_heading: str, link_line: str) -> str:
    """Add link to section. Replaces _(Empty)_ if present."""
    section_pos = content.find(section_heading)
    if section_pos == -1:
        return content
    next_section = content.find("\n## ", section_pos + 1)
    section_content = content[section_pos:next_section] if next_section != -1 else content[section_pos:]
    rest = content[next_section:] if next_section != -1 else ""
    if "_(Empty)_" in section_content:
        section_content = section_content.replace("_(Empty)_", link_line.strip(), 1)
    else:
        section_content = section_content.rstrip() + "\n\n" + link_line.strip()
    return content[:section_pos] + section_content + rest


def _remove_index_link(content: str, link_line: str) -> str:
    """Remove the matching link line from content."""
    lines = content.splitlines()
    out: list[str] = []
    for line in lines:
        if line.strip() == link_line.strip():
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def _move_index_link(content: str, link_line: str, _from_section: str, to_section: str) -> str:
    """Remove link from content, add to to_section."""
    content = _remove_index_link(content, link_line)
    return _add_index_link(content, to_section, link_line)


def _replace_link_with_issue_url(content: str, link_line: str, title: str, issue_num: int, repo: str) -> str:
    """Replace local file link with GitHub issue URL. Used when --cleanup removes local file."""
    new_line = f"- [{title}](https://github.com/{repo}/issues/{issue_num})"
    lines = content.splitlines()
    out = []
    for line in lines:
        if line.strip() == link_line.strip():
            out.append(new_line)
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _find_index_link_line(content: str, item: dict) -> str | None:
    """Find the index link line for this item. Returns the full line or None."""
    title = item.get("_title", "")
    file_path = item.get("_file_path", "")
    issue = item.get("_issue", "")
    if not file_path:
        return None
    filename = Path(file_path).name
    rel_path = f"backlog/{filename}"
    expected = _index_link_line(title, rel_path, issue) if issue else _index_link_line(title, rel_path, None)
    legacy_rel = f".claude/backlog/{filename}"
    expected_legacy = _index_link_line(title, legacy_rel, issue) if issue else _index_link_line(title, legacy_rel, None)
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in {expected, expected_legacy}:
            return line
        if f"]({rel_path})" in line or f"]({legacy_rel})" in line:
            return line
    return None


# --- Subcommands ---


def _add_item_index_format(
    title: str,
    description: str,
    source: str,
    today: str,
    priority: str,
    type_: str,
    research_first: str,
    section_heading: str,
    create_issue: bool,
    repo: str,
) -> None:
    """Add item when BACKLOG.md is in index format."""
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    slug = _title_to_slug(title)
    filename = f"{priority.lower()}-{slug}.md"
    filepath = BACKLOG_DIR / filename
    idx = 0
    while filepath.exists():
        idx += 1
        filename = f"{priority.lower()}-{slug}-{idx}.md"
        filepath = BACKLOG_DIR / filename
    rel_path = f"backlog/{filename}"
    fm_str = _build_backlog_frontmatter(title, description, source, today, priority, type_, "open", "", "", "")
    body = f"**Research first**: {research_first}\n" if research_first else ""
    filepath.write_text(fm_str.rstrip() + "\n\n" + body, encoding="utf-8")
    issue_num: int | None = None
    if create_issue and priority in {"P0", "P1"}:
        try:
            repository = _get_github(repo)
            item = {
                "_title": title,
                "**Description**": description,
                "**Source**": source,
                "**Added**": today,
                "**Priority**": priority,
                "**Type**": type_,
                "**Research first**": research_first,
            }
            issue_num = create_issue_for_item(repository, item, dry_run=False)
            if issue_num:
                _update_item_metadata(filepath, {"metadata": {"issue": f"#{issue_num}"}})
        except typer.Exit:
            raise
        except GithubException as e:
            typer.echo(f"  WARNING: Issue creation failed: {e}", err=True)
    link_line = _index_link_line(title, rel_path, f"#{issue_num}" if issue_num else None)
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    content = _add_index_link(content, section_heading, link_line)
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    typer.echo(f"Backlog item created.\n  Title: {title}\n  Priority: {priority}\n  File: {filepath.name}")
    if issue_num:
        typer.echo(f"  Issue: #{issue_num}")
    typer.echo(f"Next steps: /groom-backlog-item {title}  /work-backlog-item {title}")


def _add_item_monolithic_format(
    title: str,
    description: str,
    source: str,
    today: str,
    priority: str,
    type_: str,
    research_first: str,
    section_heading: str,
    create_issue: bool,
    repo: str,
) -> None:
    """Add item when BACKLOG.md is in monolithic format."""
    block = f"""### {title}

**Source**: {source}
**Added**: {today}
**Priority**: {priority}
**Type**: {type_}
**Description**: {description}
"""
    if research_first:
        block += f"**Research first**: {research_first}\n"
    block += "\n"

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    section_pos = content.find(section_heading)
    if section_pos == -1:
        typer.echo(f"ERROR: Section {section_heading} not found", err=True)
        raise typer.Exit(1)
    next_section = content.find("\n## ", section_pos + 1)
    section_content = content[section_pos:next_section] if next_section != -1 else content[section_pos:]
    rest = content[next_section:] if next_section != -1 else ""
    if "_(Empty)_" in section_content:
        section_content = section_content.replace("_(Empty)_", block.strip(), 1)
    else:
        section_content = section_content.rstrip() + "\n\n" + block
    content = content[:section_pos] + section_content + rest

    count_key = {
        "P0": "p0-count",
        "P1": "p1-count",
        "P2": "p2-count",
        "Idea": "ideas-count",
        "Ideas": "ideas-count",
    }.get(priority, "p1-count")
    content = re.sub(rf"({count_key}):\s*(\d+)", lambda m: f"{count_key}: {int(m.group(2)) + 1}", content, count=1)
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    typer.echo(f"Backlog item created.\n  Title: {title}\n  Priority: {priority}\n  Section: {section_heading}")

    if create_issue and priority in {"P0", "P1"}:
        items = parse_backlog(BACKLOG_PATH)
        item = find_item(items, title)
        if item and not item.get("_issue"):
            try:
                repository = _get_github(repo)
                issue_num = create_issue_for_item(repository, item, dry_run=False)
                if issue_num:
                    content = BACKLOG_PATH.read_text(encoding="utf-8")
                    content = insert_issue_into_content(content, item, issue_num)
                    BACKLOG_PATH.write_text(content, encoding="utf-8")
                    typer.echo(f"  Issue: #{issue_num}")
            except typer.Exit:
                raise
            except GithubException as e:
                typer.echo(f"  WARNING: Issue creation failed: {e}", err=True)
    typer.echo(f"Next steps: /groom-backlog-item {title}  /work-backlog-item {title}")


@app.command()
def add(
    title: Annotated[str, typer.Option("--title", "-t")],
    priority: Annotated[str, typer.Option("--priority", "-p")],
    description: Annotated[str, typer.Option("--description", "-d")],
    source: Annotated[str, typer.Option("--source")] = "Not specified",
    type_: Annotated[str, typer.Option("--type")] = "Feature",
    research_first: Annotated[str, typer.Option("--research-first")] = "",
    create_issue: Annotated[bool, typer.Option("--create-issue/--no-create-issue")] = True,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Add item to BACKLOG.md. Creates GitHub issue if P0/P1 and --create-issue."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    today = _today()
    section_map = {
        "P0": "## P0 - Must Have",
        "P1": "## P1 - Should Have",
        "P2": "## P2 - Could Have",
        "Idea": "## Ideas",
        "Ideas": "## Ideas",
    }
    section_heading = section_map.get(priority, "## P1 - Should Have")
    if _is_index_format(BACKLOG_PATH):
        _add_item_index_format(
            title, description, source, today, priority, type_, research_first, section_heading, create_issue, repo
        )
    else:
        _add_item_monolithic_format(
            title, description, source, today, priority, type_, research_first, section_heading, create_issue, repo
        )


def _fetch_item_status(item: dict, repo: str) -> str:
    """Fetch status label from GitHub issue for an item."""
    if not item.get("_issue"):
        return ""
    try:
        repository = _get_github(repo)
        num = item.get("_issue", "").lstrip("#")
        gh_issue = repository.get_issue(int(num))
        labels = [lb.name for lb in gh_issue.labels if lb.name.startswith("status:")]
        return labels[0] if labels else ""
    except GithubException:
        return ""


def _list_items_json(open_items: list[dict], with_status: bool, repo: str) -> None:
    """Output backlog items as JSON."""
    out = []
    for it in open_items:
        entry: dict[str, Any] = {
            "section": it.get("_section"),
            "title": it.get("_title"),
            "issue": it.get("_issue"),
            "plan": it.get("**Plan**"),
        }
        if it.get("_file_path"):
            entry["file_path"] = it.get("_file_path")
        if it.get("_groomed"):
            entry["groomed"] = True
        if with_status and it.get("_issue"):
            try:
                repository = _get_github(repo)
                num = it.get("_issue", "").lstrip("#")
                issue = repository.get_issue(int(num))
                status_labels = [label.name for label in issue.labels if label.name.startswith("status:")]
                entry["status"] = status_labels[0] if status_labels else ""
                entry["milestone"] = issue.milestone.title if issue.milestone else ""
            except GithubException:
                entry["status"] = ""
                entry["milestone"] = ""
        out.append(entry)
    typer.echo(json.dumps(out, indent=2))


def _list_items_table(open_items: list[dict], with_status: bool, repo: str) -> None:
    """Output backlog items as Rich table."""
    table = Table(title=":clipboard: Backlog Items", box=box.MINIMAL_DOUBLE_HEAD, title_style="bold blue")
    table.add_column("Section", style="cyan", no_wrap=True)
    table.add_column("Plan", justify="center", no_wrap=True)
    table.add_column("Title", style="white", max_width=50)
    table.add_column("Issue", style="dim", no_wrap=True)
    if with_status:
        table.add_column("Status", style="magenta", no_wrap=True)
    for it in open_items:
        issue = it.get("_issue", "no issue")
        plan = ":white_check_mark:" if it.get("**Plan**") else ":clipboard:"
        title = (it.get("_title", "") or "")[:50]
        row: list[str] = [it.get("_section", ""), plan, title, issue]
        if with_status:
            row.append(_fetch_item_status(it, repo))
        table.add_row(*row)
    table.width = _get_table_width(table)
    _console.print(table, crop=False, overflow="ignore", no_wrap=True, soft_wrap=True)


@app.command("list")
def list_items(
    output_format: Annotated[str, typer.Option("--format", "-f")] = "text",
    with_status: Annotated[bool, typer.Option("--with-status")] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """List backlog items. Use for interactive browser."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    open_items = [it for it in items if not it.get("_skip") and it.get("_section")]
    if output_format == "json":
        _list_items_json(open_items, with_status, repo)
    else:
        _list_items_table(open_items, with_status, repo)


@app.command()
def sync(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Create GitHub issues for P0/P1 items missing them."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    needed = items_needing_issues(items)
    if not needed:
        typer.echo("No P0/P1 items need GitHub issues.")
        return
    typer.echo(f"Found {len(needed)} P0/P1 item(s) without GitHub issues:")
    for it in needed:
        typer.echo(f"  - {it.get('_title', '')[:60]}")
    repository = _get_github(repo)
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    modified = False
    if _is_index_format(BACKLOG_PATH):
        for item in needed:
            issue_num = create_issue_for_item(repository, item, dry_run=dry_run)
            if issue_num and not dry_run:
                filepath_str = item.get("_file_path")
                if filepath_str:
                    _update_item_metadata(Path(filepath_str), {"metadata": {"issue": f"#{issue_num}"}})
                    old_line = _find_index_link_line(content, item)
                    if old_line:
                        title = item.get("_title", "")
                        filename = Path(filepath_str).name
                        rel_path = f"backlog/{filename}"
                        new_line = _index_link_line(title, rel_path, f"#{issue_num}")
                        content = content.replace(old_line, new_line)
                        modified = True
    else:
        for item in needed:
            issue_num = create_issue_for_item(repository, item, dry_run=dry_run)
            if issue_num and not dry_run:
                content = insert_issue_into_content(content, item, issue_num)
                modified = True
    if modified:
        BACKLOG_PATH.write_text(content, encoding="utf-8")
        typer.echo(f"Updated {BACKLOG_PATH}")


def _close_item_index(item: dict, plan: str, today: str) -> bool:
    """Apply close to item in index format. Returns False if already closed."""
    filepath_str = item.get("_file_path")
    if not filepath_str:
        typer.echo("ERROR: Item has no file path (index format)", err=True)
        raise typer.Exit(1)
    filepath = Path(filepath_str)
    raw = item.get("_raw_body", "")
    if "**Status**: DONE" in raw or "**Completed**:" in raw:
        typer.echo("Item already closed.")
        return False
    _update_item_metadata(filepath, {"metadata": {"status": "done", "priority": "completed", "plan": plan}})
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    link_line = _find_index_link_line(content, item)
    if link_line:
        content = _move_index_link(content, link_line, "", "## Completed")
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    content = re.sub(r"last-completed:\s*\S+", f"last-completed: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    return True


def _close_item_monolithic(item: dict, plan: str, today: str) -> bool:
    """Apply close to item in monolithic format. Returns False if already closed."""
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    raw = item.get("_raw_body", "")
    if "**Status**: DONE" in raw or "**Completed**:" in raw:
        typer.echo("Item already closed.")
        return False
    new_suffix = f"\n\n**Completed**: {today}\n**Status**: DONE — verified by checklist + acceptance criteria\n**Plan**: {plan}\n"
    lines = content.splitlines()
    start = item.get("_line_start", 1) - 1
    end = min(start + 50, len(lines))
    for i in range(start + 1, min(start + 50, len(lines))):
        if lines[i].startswith("###") or lines[i].startswith("## "):
            end = i
            break
        end = i + 1
    before = "\n".join(lines[:start])
    block = "\n".join(lines[start:end])
    after = "\n".join(lines[end:]) if end < len(lines) else ""
    new_block = block.rstrip() + new_suffix
    content = before + "\n" + new_block + ("\n" + after if after else "") + "\n"
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    content = re.sub(r"last-completed:\s*\S+", f"last-completed: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    return True


def _close_github_issue(issue_ref: str, plan: str, repo: str) -> None:
    """Close GitHub issue with completion comment."""
    try:
        repository = _get_github(repo)
        num = issue_ref.lstrip("#")
        issue = repository.get_issue(int(num))
        issue.create_comment(f"Completed. Checklist verified. Plan: {plan}")
        issue.edit(state="closed")
        typer.echo(f"  GitHub issue #{num} closed.")
    except GithubException as e:
        typer.echo(f"  WARNING: Could not close issue: {e}", err=True)


def _close_cleanup(item: dict, issue_ref: str, repo: str) -> None:
    """Remove local file and replace index link with issue URL."""
    filepath_str = item.get("_file_path")
    if not filepath_str:
        return
    filepath = Path(filepath_str)
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    link_line = _find_index_link_line(content, item)
    if link_line:
        content = _replace_link_with_issue_url(
            content, link_line, item.get("_title", ""), int(issue_ref.lstrip("#")), repo
        )
        content = re.sub(r"last-updated:\s*\S+", f"last-updated: {_today()}", content, count=1)
        BACKLOG_PATH.write_text(content, encoding="utf-8")
    if filepath.exists():
        filepath.unlink()
        typer.echo(f"  Removed local file {filepath.name} (canonical: GH #{issue_ref.lstrip('#')})")


@app.command()
def close(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    plan: Annotated[str, typer.Option("--plan", "-p")],
    checklist_pass: Annotated[bool, typer.Option("--checklist-pass")] = False,
    cleanup: Annotated[
        bool,
        typer.Option(
            "--cleanup",
            help="Remove local file after close; index link becomes GH issue URL (like git delete merged branch)",
        ),
    ] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Mark item DONE and close GitHub issue. Requires --checklist-pass from skill."""
    if not checklist_pass:
        typer.echo("ERROR: --checklist-pass required (skill must verify checklist first)", err=True)
        raise typer.Exit(1)
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    item = find_item(items, selector)
    if not item:
        typer.echo(f"ERROR: No item found for: {selector}", err=True)
        raise typer.Exit(1)
    today = _today()
    if _is_index_format(BACKLOG_PATH):
        if not _close_item_index(item, plan, today):
            return
    elif not _close_item_monolithic(item, plan, today):
        return
    typer.echo(f'Backlog item "{item.get("_title")}" closed.')
    issue_ref = item.get("_issue")
    if issue_ref:
        _close_github_issue(issue_ref, plan, repo)
    if cleanup and issue_ref and _is_index_format(BACKLOG_PATH):
        _close_cleanup(item, issue_ref, repo)


def _resolve_item_index(item: dict, reason: str, today: str) -> bool:
    """Apply resolve to item in index format. Returns False if already resolved."""
    filepath_str = item.get("_file_path")
    if not filepath_str:
        typer.echo("ERROR: Item has no file path (index format)", err=True)
        raise typer.Exit(1)
    raw = item.get("_raw_body", "")
    if "**Resolved**:" in raw:
        typer.echo("Item already resolved.")
        return False
    _update_item_metadata(Path(filepath_str), {"metadata": {"status": "resolved"}})
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    link_line = _find_index_link_line(content, item)
    if link_line:
        content = _move_index_link(content, link_line, "", "## Completed")
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    return True


def _resolve_item_monolithic(item: dict, reason: str, today: str) -> bool:
    """Apply resolve to item in monolithic format. Returns False if already resolved."""
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    raw = item.get("_raw_body", "")
    if "**Resolved**:" in raw:
        typer.echo("Item already resolved.")
        return False
    lines = content.splitlines()
    start = item.get("_line_start", 1) - 1
    new_line = f"**Resolved**: {today} — {reason}"
    for i in range(start, min(start + 30, len(lines))):
        if i > start and (lines[i].startswith("###") or lines[i].startswith("## ")):
            break
        if re.match(r"^\*\*Description\*\*:", lines[i]):
            lines.insert(i + 1, new_line)
            break
    else:
        lines.insert(start + 1, new_line)
    content = "\n".join(lines) + "\n"
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)
    BACKLOG_PATH.write_text(content, encoding="utf-8")
    return True


def _resolve_github_issue(issue_ref: str, reason: str, repo: str) -> None:
    """Close GitHub issue with resolve comment."""
    try:
        repository = _get_github(repo)
        num = issue_ref.lstrip("#")
        issue = repository.get_issue(int(num))
        issue.create_comment(f"Resolved: {reason}")
        issue.edit(state="closed")
        typer.echo(f"  GitHub issue #{num} closed.")
    except GithubException as e:
        typer.echo(f"  WARNING: Could not close issue: {e}", err=True)


@app.command()
def resolve(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    reason: Annotated[str, typer.Option("--reason", "-r")],
    cleanup: Annotated[
        bool, typer.Option("--cleanup", help="Remove local file after resolve; index link becomes GH issue URL")
    ] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Mark item RESOLVED and close GitHub issue."""
    if not reason.strip():
        typer.echo("ERROR: --reason required", err=True)
        raise typer.Exit(1)
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    item = find_item(items, selector)
    if not item:
        typer.echo(f"ERROR: No item found for: {selector}", err=True)
        raise typer.Exit(1)
    today = _today()
    if _is_index_format(BACKLOG_PATH):
        if not _resolve_item_index(item, reason, today):
            return
    elif not _resolve_item_monolithic(item, reason, today):
        return
    typer.echo(f'Backlog item "{item.get("_title")}" resolved.')
    issue_ref = item.get("_issue")
    if issue_ref:
        _resolve_github_issue(issue_ref, reason, repo)
    if cleanup and issue_ref and _is_index_format(BACKLOG_PATH):
        _close_cleanup(item, issue_ref, repo)


def _build_backlog_frontmatter(
    name: str,
    description: str,
    source: str,
    added: str,
    priority: str,
    type_val: str,
    status: str,
    issue: str = "",
    plan: str = "",
    groomed: str = "",
) -> str:
    """Build research-style frontmatter with metadata block."""
    meta: dict[str, str] = {
        "topic": _title_to_slug(name),
        "source": source[:200] if source else "Not specified",
        "added": added or _today(),
        "priority": priority,
        "type": type_val,
        "status": status,
    }
    if issue:
        meta["issue"] = issue
    if plan:
        meta["plan"] = plan
    if groomed:
        meta["groomed"] = groomed
    post = frontmatter.Post(
        "", name=name.replace('"', "'"), description=(description or "").replace('"', "'")[:500], metadata=meta
    )
    return dump_frontmatter(post)


def _apply_field_to_result(key_lower: str, val: str) -> tuple[str, str, str, str, str, str]:
    """Return (desc, suggested, research, decision, files_val, required_work) with val applied to the matching key."""
    match key_lower:
        case "description":
            return (val, "", "", "", "", "")
        case "suggested location":
            return ("", val, "", "", "", "")
        case "research first":
            return ("", "", val, "", "", "")
        case "decision needed":
            return ("", "", "", val, "", "")
        case "files":
            return ("", "", "", "", val, "")
        case "required work":
            return ("", "", "", "", "", val)
        case _:
            return ("", "", "", "", "", "")


def _extract_body_field_pairs(body: str) -> list[tuple[str, str]]:
    """Extract (key, value) pairs from body until first ## heading. Stops at ## Groomed or ## ."""
    field_re = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$", re.DOTALL)
    pairs: list[tuple[str, str]] = []
    current_key = ""
    current_val: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_key:
                pairs.append((current_key, "\n".join(current_val).strip()))
            return pairs
        m = field_re.match(line)
        if m:
            if current_key:
                pairs.append((current_key, "\n".join(current_val).strip()))
            current_key = m.group(1).strip()
            current_val = [m.group(2).strip()] if m.group(2).strip() else []
        elif current_key:
            current_val.append(line)
    if current_key:
        pairs.append((current_key, "\n".join(current_val).strip()))
    return pairs


def _merge_field_into_result(
    key: str, val: str, desc: str, suggested: str, research: str, decision: str, files_val: str, required_work: str
) -> tuple[str, str, str, str, str, str]:
    """Merge one field (key, val) into result tuple. Returns updated (desc, suggested, research, decision, files_val, required_work)."""
    d, s, r, dec, f, req = _apply_field_to_result(key.lower(), val)
    return (d or desc, s or suggested, r or research, dec or decision, f or files_val, req or required_work)


def _parse_body_extra_fields(body: str) -> tuple[str, str, str, str, str, str]:
    """Extract Description, Suggested location, Research first, Decision needed, Files, Required work from body."""
    desc, suggested, research, decision, files_val, required_work = "", "", "", "", "", ""
    for key, val in _extract_body_field_pairs(body):
        desc, suggested, research, decision, files_val, required_work = _merge_field_into_result(
            key, val, desc, suggested, research, decision, files_val, required_work
        )
    return desc, suggested, research, decision, files_val, required_work


def _extract_groomed_section(body: str) -> str:
    """Extract full ## Groomed (date) ... section from body."""
    m = re.search(r"(## Groomed\s*\([^)]*\)\s*\n[\s\S]*?)(?=\n## |\Z)", body)
    return m.group(1).rstrip() if m else ""


def _build_body_extra_only(
    suggested: str, research: str, decision: str, files_val: str, required_work: str, groomed_section: str
) -> str:
    """Build body with only extra fields (no duplication) and ## Groomed if present."""
    parts: list[str] = []
    if suggested:
        parts.append(f"**Suggested location**: {suggested}")
    if research:
        parts.append(f"**Research first**: {research}")
    if decision:
        parts.append(f"**Decision needed**: {decision}")
    if files_val:
        parts.append(f"**Files**: {files_val}")
    if required_work:
        parts.append(f"**Required work**:\n{required_work}")
    if groomed_section:
        parts.append(groomed_section)
    return "\n\n".join(parts) + "\n" if parts else ""


def _append_or_replace_section(body: str, section_name: str, content: str) -> str:
    """Append or replace a section in body. section_name: Fact-Check, RT-ICA, or groomed subsection (Reproducibility, Priority, etc.)."""
    content = content.strip()
    if not content:
        return body
    today = _today()
    groomed_subsections = (
        "reproducibility",
        "output / evidence",
        "priority",
        "impact",
        "benefits",
        "expected behavior",
        "desired structure",
        "acceptance criteria",
        "human input",
        "questions for human",
        "resources",
        "dependencies",
        "blockers",
        "effort",
    )
    section_lower = section_name.strip().lower()
    if section_lower in {"fact-check", "rt-ica"}:
        header = f"## {section_name.strip()}\n\n"
        section_re = re.compile(
            rf"\n## {re.escape(section_name.strip())}\s*\n[\s\S]*?(?=\n## |\Z)", re.IGNORECASE | re.MULTILINE
        )
        new_block = header + content + "\n"
        if section_re.search(body):
            return section_re.sub(f"\n{new_block}", body)
        return body.rstrip() + "\n\n" + new_block
    if section_lower in groomed_subsections:
        groomed_header = f"## Groomed ({today})"
        sub_header = f"### {section_name.strip()}\n\n"
        sub_re = re.compile(
            rf"\n### {re.escape(section_name.strip())}\s*\n[\s\S]*?(?=\n### |\n## |\Z)", re.IGNORECASE | re.MULTILINE
        )
        new_block = sub_header + content + "\n"
        groomed_re = re.compile(r"(## Groomed\s*\([^)]*\)\s*\n)([\s\S]*?)(?=\n## |\Z)", re.MULTILINE)
        match = groomed_re.search(body)
        if match:
            groomed_body = match.group(2)
            if sub_re.search(groomed_body):
                new_groomed_body = sub_re.sub(f"\n{new_block}", groomed_body)
            else:
                new_groomed_body = groomed_body.rstrip() + "\n\n" + new_block
            return groomed_re.sub(match.group(1) + new_groomed_body + "\n", body, count=1)
        return body.rstrip() + "\n\n" + groomed_header + "\n\n" + new_block
    return body


def _write_groomed_to_item_file(filepath: Path, groomed_content: str, section_name: str | None = None) -> None:
    """Merge groomed content into per-item file.

    Updates frontmatter groomed date and body.
    If section_name is set, append/replace that section only (incremental).
    Else replace full ## Groomed.
    """
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        typer.echo("ERROR: Item file has no frontmatter", err=True)
        raise typer.Exit(1)
    parts = text.split("---", 2)
    if len(parts) < MIN_FRONTMATTER_PARTS:
        typer.echo("ERROR: Malformed item file", err=True)
        raise typer.Exit(1)
    fm_text, body = parts[1].strip(), parts[2].strip()
    today = _today()
    if section_name:
        new_body = _append_or_replace_section(body, section_name, groomed_content)
    else:
        groomed_section = f"## Groomed ({today})\n\n{groomed_content.strip()}"
        groomed_re = re.compile(r"\n## Groomed\s*\([^)]*\)\s*\n[\s\S]*?(?=\n## |\Z)", re.MULTILINE)
        if groomed_re.search(body):
            new_body = groomed_re.sub(f"\n{groomed_section}\n", body)
        else:
            new_body = body.rstrip() + "\n\n" + groomed_section + "\n"
    try:
        post = loads_frontmatter(text)
        meta_block = post.metadata.get("metadata")
        if isinstance(meta_block, dict):
            updated = dict(meta_block)
            updated["groomed"] = today
            post.metadata["metadata"] = updated
        else:
            post.metadata["groomed"] = today
        post.content = new_body
        new_content = dump_frontmatter(post)
    except (ValueError, KeyError, TypeError):
        new_content = "---\n" + fm_text + "\n---\n\n" + new_body
        if "groomed:" not in fm_text:
            new_content = new_content.replace("---\n", f'---\ngroomed: "{today}"\n', 1)
    filepath.write_text(new_content, encoding="utf-8")


def _sync_groomed_to_github_issue(
    repo_obj: Repository, issue_num: int, groomed_content: str, section_name: str | None = None
) -> None:
    """Append or merge groomed content into GitHub issue body. GitHub is canonical."""
    try:
        issue = repo_obj.get_issue(issue_num)
        body = issue.body or ""
        content = groomed_content.strip()
        if not content:
            return
        today = _today()
        if section_name and section_name.lower() not in {"groomed", ""}:
            new_body = _append_or_replace_section(body, section_name, content)
        else:
            groomed_re = re.compile(r"\n## Groomed\s*\([^)]*\)\s*\n[\s\S]*?(?=\n## |\Z)", re.MULTILINE)
            block = f"\n## Groomed ({today})\n\n{content}\n"
            new_body = groomed_re.sub(block, body) if groomed_re.search(body) else body.rstrip() + "\n\n" + block
        if new_body == body:
            return
        issue.edit(body=new_body)
    except GithubException as e:
        typer.echo(f"  WARNING: Could not sync to GitHub issue: {e}", err=True)


def _resolve_groomed_content(
    section: str | None, content: str | None, groomed_content: str | None, groomed_file: str | None
) -> tuple[str, str | None]:
    """Resolve groomed content from section/content, groomed_content, groomed_file, or stdin."""
    if section is not None and content is not None:
        return content, section
    if groomed_content is not None:
        return groomed_content, None
    if groomed_file:
        return Path(groomed_file).read_text(encoding="utf-8"), None
    return sys.stdin.read(), None


def _handle_update_groomed(item: dict, groomed_content_val: str, section_name: str | None, repo: str) -> None:
    """Handle groomed content update: write to file, create issue if needed, sync to GitHub."""
    filepath = Path(item["_file_path"])
    _write_groomed_to_item_file(filepath, groomed_content_val, section_name)
    typer.echo(f"Updated {filepath.name} with groomed content")
    issue_ref = item.get("_issue")
    if not issue_ref and not item.get("_skip") and item.get("_section") in {"P0", "P1", "P2", "Ideas"}:
        try:
            repository = _get_github(repo)
            issue_num = create_issue_for_item(repository, item, dry_run=False)
            if issue_num:
                _update_item_metadata(filepath, {"metadata": {"issue": f"#{issue_num}"}})
                index_content = BACKLOG_PATH.read_text(encoding="utf-8")
                old_line = _find_index_link_line(index_content, item)
                if old_line:
                    new_line = _index_link_line(item.get("_title", ""), f"backlog/{filepath.name}", f"#{issue_num}")
                    index_content = index_content.replace(old_line, new_line)
                    index_content = re.sub(r"last-updated:\s*\S+", f"last-updated: {_today()}", index_content, count=1)
                    BACKLOG_PATH.write_text(index_content, encoding="utf-8")
                issue_ref = f"#{issue_num}"
                typer.echo(f"  Created GitHub issue #{issue_num}")
        except typer.Exit:
            raise
        except GithubException as e:
            typer.echo(f"  WARNING: Could not create issue: {e}", err=True)
    if issue_ref:
        try:
            repository = _get_github(repo)
            num = issue_ref.lstrip("#")
            _sync_groomed_to_github_issue(repository, int(num), groomed_content_val, section_name)
            typer.echo(f"  Synced to GitHub issue #{num}")
        except typer.Exit:
            raise
        except GithubException as e:
            typer.echo(f"  WARNING: Could not sync to GitHub: {e}", err=True)


def _apply_status_in_progress(item: dict, repo: str) -> None:
    """Set GitHub issue label to status:in-progress."""
    try:
        repository = _get_github(repo)
        num = item.get("_issue", "").lstrip("#")
        issue = repository.get_issue(int(num))
        labels = [label.name for label in issue.labels]
        if "status:in-progress" not in labels:
            lbl = repository.get_label("status:in-progress")
            issue.add_to_labels(lbl)
            if "status:needs-grooming" in labels:
                ng = repository.get_label("status:needs-grooming")
                issue.remove_from_labels(ng)
        typer.echo("  Status: in-progress")
    except GithubException as e:
        typer.echo(f"  WARNING: Could not set status: {e}", err=True)


def _apply_plan_to_content(item: dict, content: str, plan: str) -> tuple[str, bool]:
    """Apply plan update to content. Returns (new_content, modified)."""
    if _is_index_format(BACKLOG_PATH):
        filepath_str = item.get("_file_path")
        if filepath_str:
            _update_item_metadata(Path(filepath_str), {"metadata": {"plan": plan}})
            return content, True
        return content, False
    raw = item.get("_raw_body", "")
    if f"**Plan**: {plan}" in raw or "**Plan**: " in raw:
        return content, False
    lines = content.splitlines()
    start = item.get("_line_start", 1) - 1
    for i in range(start, min(start + 30, len(lines))):
        if i > start and (lines[i].startswith("###") or lines[i].startswith("## ")):
            break
        if re.match(r"^\*\*Description\*\*:", lines[i]):
            lines.insert(i + 1, f"**Plan**: {plan}")
            return "\n".join(lines) + "\n", True
    new_body = item.get("_raw_body", "") + f"\n**Plan**: {plan}\n"
    return content.replace(item.get("_raw_body", ""), new_body), True


@app.command()
def update(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    plan: Annotated[str | None, typer.Option("--plan", "-p")] = None,
    status: Annotated[str | None, typer.Option("--status")] = None,
    create_issue: Annotated[bool, typer.Option("--create-issue")] = False,
    groomed_file: Annotated[str | None, typer.Option("--groomed-file")] = None,
    groomed_content: Annotated[str | None, typer.Option("--groomed-content")] = None,
    section: Annotated[str | None, typer.Option("--section")] = None,
    content: Annotated[str | None, typer.Option("--content")] = None,
    groomed: Annotated[bool, typer.Option("--groomed")] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Update item: add Plan, set status:in-progress, create issue, or write groomed content."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    item = find_item(items, selector)
    if not item:
        typer.echo(f"ERROR: No item found for: {selector}", err=True)
        raise typer.Exit(1)

    has_groomed = groomed or groomed_file or groomed_content or (section and content)
    if has_groomed:
        if not _is_index_format(BACKLOG_PATH):
            typer.echo("ERROR: --groomed only works with index format (per-item files)", err=True)
            raise typer.Exit(1)
        if not item.get("_file_path"):
            typer.echo("ERROR: Item has no file path", err=True)
            raise typer.Exit(1)
        groomed_content_val, section_name = _resolve_groomed_content(section, content, groomed_content, groomed_file)
        if not groomed_content_val.strip():
            typer.echo("ERROR: No groomed content provided", err=True)
            raise typer.Exit(1)
        _handle_update_groomed(item, groomed_content_val, section_name, repo)
        return

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    modified = False

    if plan:
        content, plan_modified = _apply_plan_to_content(item, content, plan)
        modified = modified or plan_modified
        typer.echo(f"  Plan: {plan}")

    if create_issue and not item.get("_issue") and item.get("_section") in {"P0", "P1"}:
        content, issue_modified = _create_issue_and_update_content(item, content, repo)
        modified = modified or issue_modified

    if status == "in-progress" and item.get("_issue"):
        _apply_status_in_progress(item, repo)

    if modified:
        BACKLOG_PATH.write_text(content, encoding="utf-8")
        typer.echo("Updated BACKLOG.md")


@app.command()
def groom(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    groomed_file: Annotated[str | None, typer.Option("--groomed-file")] = None,
    groomed_content: Annotated[str | None, typer.Option("--groomed-content")] = None,
    section: Annotated[str | None, typer.Option("--section")] = None,
    content: Annotated[str | None, typer.Option("--content")] = None,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Write groomed content into per-item file. Use --groomed-content, --groomed-file, --section/--content (incremental), or stdin. Syncs to GitHub issue when item has one."""
    has_input = groomed_file or groomed_content or (section and content)
    update(
        selector=selector,
        plan=None,
        status=None,
        create_issue=False,
        groomed_file=groomed_file,
        groomed_content=groomed_content,
        section=section,
        content=content,
        groomed=not has_input,
        repo=repo,
    )


def _item_priority_for_migrate(item: dict) -> str:
    """Derive priority for migration (P0, P1, P2, Ideas, Completed)."""
    section = item.get("_section") or ""
    title = item.get("_title", "")
    if section == "Completed":
        return "completed"
    if section == "Format Guide":
        if title.startswith("P0:"):
            return "P0"
        if title.startswith("P1:"):
            return "P1"
        if title.startswith("P2:"):
            return "P2"
        return "Ideas"
    return section


def _item_status_for_migrate(item: dict) -> str:
    """Derive status from item content."""
    if item.get("_skip"):
        raw = item.get("_raw_body", "")
        if "**Resolved**:" in raw:
            return "resolved"
        if "**Completed**:" in raw or "**Status**: DONE" in raw:
            return "done"
    return "open"


def _build_migrate_item_content(item: dict, priority: str, slug: str) -> str:
    """Build file content for one migrated backlog item."""
    title = item.get("_title", "")
    source = item.get("**Source**", "Not specified")
    added = item.get("**Added**", _today())
    type_val = item.get("**Type**", "Feature")
    issue = item.get("_issue", "")
    plan = item.get("**Plan**", "")
    status = _item_status_for_migrate(item)
    frontmatter_lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f'source: "{str(source).replace(chr(34), chr(39))[:200]}"',
        f'added: "{added}"',
        f"priority: {priority}",
        f"type: {type_val}",
        f"status: {status}",
    ]
    if issue:
        frontmatter_lines.append(f'issue: "{issue}"')
    if plan:
        frontmatter_lines.append(f'plan: "{plan}"')
    frontmatter_lines.extend(("---", ""))
    return "\n".join(frontmatter_lines) + "\n" + (item.get("_raw_body", ""))


def _process_migrate_items(items: list, dry_run: bool) -> tuple[dict[str, list[tuple[str, str, str]]], int]:
    """Process items into per-item files and by_section index entries. Returns (by_section, count)."""
    section_order = ["P0", "P1", "P2", "Ideas", "completed"]
    by_section: dict[str, list[tuple[str, str, str]]] = {s: [] for s in section_order}
    seen_slugs: dict[str, int] = {}
    for item in items:
        section = item.get("_section") or ""
        if section not in {"P0", "P1", "P2", "Ideas", "Completed", "Format Guide"}:
            continue
        title = item.get("_title", "")
        if not title or (title.startswith("~~") and "~~" in title[2:]):
            continue
        priority = _item_priority_for_migrate(item)
        base_slug = _title_to_slug(title)
        if base_slug in seen_slugs:
            seen_slugs[base_slug] += 1
            slug = f"{base_slug}-{seen_slugs[base_slug]}"
        else:
            seen_slugs[base_slug] = 0
            slug = base_slug
        filename = f"{priority.lower()}-{slug}.md"
        filepath = BACKLOG_DIR / filename
        content = _build_migrate_item_content(item, priority, slug)
        if not dry_run:
            filepath.write_text(content, encoding="utf-8")
        rel_path = f"backlog/{filename}"
        issue = item.get("_issue", "")
        by_section[priority].append((title, rel_path, f" {issue}" if issue else ""))
    return by_section, len(seen_slugs)


def _build_migrate_index_content(by_section: dict[str, list[tuple[str, str, str]]]) -> str:
    """Build index markdown content from by_section."""
    section_order = ["P0", "P1", "P2", "Ideas", "completed"]
    section_headings = {
        "P0": "## P0 - Must Have",
        "P1": "## P1 - Should Have",
        "P2": "## P2 - Could Have",
        "Ideas": "## Ideas",
        "completed": "## Completed",
    }
    index_lines = [
        "---",
        "last-updated: " + _today(),
        "format: index",
        "---",
        "",
        "# Backlog",
        "",
        "Tracked features, ideas, and deferred work. Each item lives in `.claude/backlog/`.",
        "",
        "---",
        "",
    ]
    for sec in section_order:
        entries = by_section.get(sec, [])
        if not entries:
            if sec == "P0":
                index_lines.extend((section_headings[sec], "", "_(Empty)_", ""))
            continue
        index_lines.extend((section_headings[sec], ""))
        for title, rel_path, issue_suffix in entries:
            index_lines.append(f"- [{title}]({rel_path}){issue_suffix}")
        index_lines.append("")
    index_lines.extend((
        "---",
        "",
        "## Format Guide",
        "",
        "See [.claude/docs/backlog-item-groomed-schema.md](.claude/docs/backlog-item-groomed-schema.md) for groomed item structure.",
    ))
    return "\n".join(index_lines)


@app.command()
def migrate(dry_run: Annotated[bool, typer.Option("--dry-run")] = False) -> None:
    """Migrate monolithic BACKLOG.md to index + per-item files in .claude/backlog/."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    items = parse_backlog_migrate(BACKLOG_PATH)
    by_section, item_count = _process_migrate_items(items, dry_run)
    index_content = _build_migrate_index_content(by_section)
    if dry_run:
        typer.echo(f"[dry-run] Would create {item_count} item files in {BACKLOG_DIR}")
        typer.echo("[dry-run] Would write new BACKLOG.md index")
        return
    backup = BACKLOG_PATH.with_suffix(".md.bak")
    backup.write_text(BACKLOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    BACKLOG_PATH.write_text(index_content, encoding="utf-8")
    broken = _validate_index_links(BACKLOG_PATH)
    if broken:
        for rel in broken:
            typer.echo(f"  Broken link: {rel}", err=True)
        typer.echo("ERROR: Migrate produced broken links. Restoring backup.", err=True)
        BACKLOG_PATH.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        raise typer.Exit(1)
    typer.echo(f"Migrated {item_count} items to {BACKLOG_DIR}")
    typer.echo(f"Backup: {backup}")
    typer.echo("Updated BACKLOG.md to index format")


def _extract_normalize_metadata(fm: dict, meta: dict) -> dict[str, str]:
    """Extract normalized metadata from frontmatter and metadata dicts."""
    return {
        "name": str(fm.get("name") or fm.get("title") or "").strip(),
        "description": str(fm.get("description") or "").strip(),
        "source": str(meta.get("source") or fm.get("source") or "Not specified"),
        "added": str(meta.get("added") or fm.get("added") or _today()),
        "priority": str(meta.get("priority") or fm.get("priority") or "P2"),
        "type_val": str(meta.get("type") or fm.get("type") or "Feature"),
        "status": str(meta.get("status") or fm.get("status") or "open"),
        "issue": str(meta.get("issue") or fm.get("issue") or ""),
        "plan": str(meta.get("plan") or fm.get("plan") or ""),
        "groomed": str(meta.get("groomed") or fm.get("groomed") or ""),
    }


def _build_normalized_content(filepath: Path) -> str | None:
    """Build normalized content for one file. Returns None if skip."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError as e:
        typer.echo(f"  Skip {filepath.name}: {e}", err=True)
        return None
    if not text.startswith("---"):
        return None
    try:
        post = loads_frontmatter(text)
        fm = post.metadata or {}
        body = post.content or ""
    except (ValueError, KeyError, TypeError):
        return None
    meta_raw = fm.get("metadata")
    meta = dict(meta_raw) if isinstance(meta_raw, dict) else {}
    md = _extract_normalize_metadata(fm, meta)
    if not md["name"]:
        return None
    parsed = _parse_body_extra_fields(body)
    if parsed[0] and not md["description"]:
        md["description"] = parsed[0]
    groomed = _extract_groomed_section(body)
    new_body = _build_body_extra_only(parsed[1], parsed[2], parsed[3], parsed[4], parsed[5], groomed)
    fm_str = _build_backlog_frontmatter(
        md["name"],
        md["description"],
        md["source"],
        md["added"],
        md["priority"],
        md["type_val"],
        md["status"],
        md["issue"],
        md["plan"],
        md["groomed"],
    )
    out = fm_str.rstrip()
    return out + ("\n" if not out.endswith("\n\n") else "") + new_body


def _normalize_item_file(filepath: Path, dry_run: bool) -> bool:
    """Normalize one backlog item file. Returns True if updated, False if skipped."""
    content = _build_normalized_content(filepath)
    if content is None:
        return False
    if not dry_run:
        filepath.write_text(content, encoding="utf-8")
    return True


@app.command()
def normalize(dry_run: Annotated[bool, typer.Option("--dry-run")] = False) -> None:
    """One-off: rewrite per-item files to research-style metadata, remove body duplication."""
    if not BACKLOG_DIR.exists():
        typer.echo(f"ERROR: {BACKLOG_DIR} not found", err=True)
        raise typer.Exit(1)
    pattern = re.compile(r"^(p0|p1|p2|ideas|completed)-[a-z0-9-]+\.md$", re.IGNORECASE)
    files = sorted(f for f in BACKLOG_DIR.glob("*.md") if pattern.match(f.name))
    if not files:
        typer.echo("No backlog item files found")
        return
    updated = sum(1 for f in files if _normalize_item_file(f, dry_run))
    typer.echo(f"Normalized {updated} item file(s)" + (" [dry-run]" if dry_run else ""))


def _validate_index_links(path: Path) -> list[str]:
    """Validate all index links resolve to existing files. Returns list of broken rel_paths."""
    if not _is_index_format(path):
        return []
    text = path.read_text(encoding="utf-8")
    link_re = re.compile(r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s*(#\d+)?\s*$")
    broken: list[str] = []
    for line in text.splitlines():
        link_m = link_re.match(line)
        if link_m:
            rel_path = link_m.group(2)
            if ".claude/backlog/" not in rel_path and "backlog/" not in rel_path:
                continue
            filepath = _resolve_index_link_path(rel_path, path)
            if not filepath.exists():
                broken.append(rel_path)
    return broken


@app.command()
def validate() -> None:
    """Validate all index links resolve to existing files. Exit 1 if any broken."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    if not _is_index_format(BACKLOG_PATH):
        typer.echo("Not index format — nothing to validate.")
        return
    broken = _validate_index_links(BACKLOG_PATH)
    if broken:
        for rel in broken:
            typer.echo(f"  Broken link: {rel}", err=True)
        typer.echo(f"ERROR: {len(broken)} broken link(s)", err=True)
        raise typer.Exit(1)
    typer.echo("All index links valid.")


@app.command("fix-links")
def fix_links(dry_run: Annotated[bool, typer.Option("--dry-run")] = False) -> None:
    """Rewrite index links from .claude/backlog/ to backlog/ for editor click-to-open."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    if not _is_index_format(BACKLOG_PATH):
        typer.echo("Not index format — nothing to fix.")
        return
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    new_content = content.replace("](.claude/backlog/", "](backlog/")
    if new_content == content:
        typer.echo("No links to fix.")
        return
    if dry_run:
        typer.echo("[dry-run] Would rewrite .claude/backlog/ → backlog/ in index links")
        return
    BACKLOG_PATH.write_text(new_content, encoding="utf-8")
    typer.echo("Fixed index links.")


if __name__ == "__main__":
    app()
