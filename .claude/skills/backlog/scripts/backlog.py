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
    backlog close <selector> --plan PATH --checklist-pass
    backlog resolve <selector> --reason "reason"
    backlog update <selector> [--plan PATH] [--status in-progress] [--create-issue]
    backlog groom <selector> [--groomed-file PATH]  # writes groomed content to per-item file (stdin if no file)
    backlog normalize  # one-off: rewrite per-item files to research-style metadata, remove body duplication

Environment:
    GITHUB_TOKEN  Required for issue operations.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

# Ensure UTF-8 output on Windows (cp1252 default cannot encode emoji/spinner chars).
# reconfigure() is available on Python 3.7+ when stdout is a TextIOWrapper.
from io import TextIOWrapper
if isinstance(sys.stdout, TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if isinstance(sys.stderr, TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from github import Auth, Github, GithubException

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
TYPE_TO_LABEL = {
    "feature": "type:feature",
    "bug": "type:bug",
    "refactor": "type:refactor",
    "docs": "type:docs",
    "chore": "type:chore",
}

app = typer.Typer(help="Backlog and GitHub Issue CRUD — single interface")


def _get_github(repo: str):
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
    return "format: index" in text[:500] or "- [" in text and "](.claude/backlog/" in text


def parse_backlog(path: Path) -> list[dict]:
    """Parse BACKLOG.md into items — supports both monolithic and index format."""
    if _is_index_format(path):
        return _parse_backlog_index(path)
    return _parse_backlog_monolithic(path)


def _parse_backlog_monolithic(path: Path) -> list[dict]:
    """Parse monolithic BACKLOG.md into items with section, title, and fields."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    items: list[dict] = []
    current_section: str | None = None
    current_item: dict | None = None
    current_body: list[str] = []
    current_field_value: list[str] = []

    def flush_item():
        nonlocal current_item, current_body, current_field_value
        if current_item is not None:
            for k, v in list(current_item.items()):
                if isinstance(v, list):
                    current_item[k] = "\n".join(v).strip()
            current_item["_raw_body"] = "\n".join(current_body)
            current_item["_line_end"] = i + 1
            items.append(current_item)
        current_item = None
        current_body = []
        current_field_value = []

    for i, line in enumerate(lines):
        section_m = SECTION_RE.match(line)
        if section_m:
            flush_item()
            current_section = section_m.group(1)
            continue

        item_m = ITEM_HEADER_RE.match(line)
        if item_m:
            flush_item()
            title = item_m.group(1).strip()
            if title.startswith("~~") and "~~" in title[2:]:
                continue
            current_item = {
                "_section": current_section or "",
                "_title": title,
                "_line_start": i + 1,
            }
            current_body = [line]
            current_field_value = []
            continue

        field_m = FIELD_RE.match(line)
        if field_m and current_item is not None:
            key, val = field_m.group(1).strip(), field_m.group(2).strip()
            key_lower = key.lower()
            if key_lower == "issue":
                current_item["_issue"] = val
                current_field_value = []
            elif key_lower == "status" and val.upper().split()[0] in SKIP_STATUS:
                current_item["_skip"] = True
                current_field_value = []
            elif key_lower in ("completed", "resolved"):
                current_item["_skip"] = True
                current_field_value = []
            elif key_lower in ("source", "added", "priority", "type", "description", "research first"):
                store_key = "**Research first**" if key_lower == "research first" else f"**{key}**"
                current_item[store_key] = [val]
                current_field_value = current_item[store_key]
            else:
                current_field_value = []
            current_body.append(line)
            continue

        if current_item is not None and current_field_value:
            if line.strip():
                current_field_value.append(line.strip())
            current_body.append(line)

    flush_item()
    return items


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
            title, rel_path, issue = link_m.group(1), link_m.group(2), link_m.group(3) or ""
            if ".claude/backlog/" not in rel_path:
                continue
            filepath = (_REPO_ROOT / rel_path).resolve()
            if not filepath.exists():
                continue
            item_text = filepath.read_text(encoding="utf-8")
            item = _parse_item_file(item_text, filepath)
            item["_section"] = current_section
            item["_title"] = title
            item["_issue"] = issue.strip()
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
    except Exception:
        parts = text.split("---", 2)
        fm, body = {}, parts[2].strip() if len(parts) >= 3 else text
    meta = fm.get("metadata") or {}
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
    if status in ("done", "resolved"):
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
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    items: list[dict] = []
    current_section: str | None = None
    current_item: dict | None = None
    current_body: list[str] = []
    current_field_value: list[str] = []

    def flush_item():
        nonlocal current_item, current_body, current_field_value
        if current_item is not None:
            for k, v in list(current_item.items()):
                if isinstance(v, list):
                    current_item[k] = "\n".join(v).strip()
            current_item["_raw_body"] = "\n".join(current_body)
            current_item["_line_end"] = i + 1
            items.append(current_item)
        current_item = None
        current_body = []
        current_field_value = []

    for i, line in enumerate(lines):
        section_m = SECTION_RE_MIGRATE.match(line)
        if section_m:
            flush_item()
            current_section = section_m.group(1)
            continue

        item_m = ITEM_HEADER_RE.match(line)
        if item_m:
            flush_item()
            title = item_m.group(1).strip()
            current_item = {
                "_section": current_section or "",
                "_title": title,
                "_line_start": i + 1,
            }
            current_body = [line]
            current_field_value = []
            continue

        field_m = FIELD_RE.match(line)
        if field_m and current_item is not None:
            key, val = field_m.group(1).strip(), field_m.group(2).strip()
            key_lower = key.lower()
            if key_lower == "issue":
                current_item["_issue"] = val
                current_field_value = []
            elif key_lower == "status" and val.upper().split()[0] in SKIP_STATUS:
                current_item["_skip"] = True
                current_field_value = []
            elif key_lower in ("completed", "resolved"):
                current_item["_skip"] = True
                current_field_value = []
            elif key_lower in ("source", "added", "priority", "type", "description", "research first"):
                store_key = "**Research first**" if key_lower == "research first" else f"**{key}**"
                current_item[store_key] = [val]
                current_field_value = current_item[store_key]
            else:
                current_field_value = []
            current_body.append(line)
            continue

        if current_item is not None and current_field_value:
            if line.strip():
                current_field_value.append(line.strip())
            current_body.append(line)

    flush_item()
    return items


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
    return [it for it in items if it.get("_section") in ("P0", "P1") and not it.get("_skip") and not it.get("_issue")]


def build_issue_body(item: dict) -> str:
    title = item.get("_title", "")
    desc = item.get("**Description**", "")
    source = item.get("**Source**", "Not specified")
    added = item.get("**Added**", "")
    priority = item.get("**Priority**", "")
    research = item.get("**Research first**", "")
    first_sent = desc.split(".")[0].strip() if desc else title
    if len(first_sent) > 80:
        first_sent = first_sent[:77] + "..."
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


def create_issue_for_item(repo, item: dict, dry_run: bool = False) -> int | None:
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


def insert_issue_into_content(content: str, item: dict, issue_num: int) -> str:
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


# --- Subcommands ---


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
    section_map = {"P0": "## P0 - Must Have", "P1": "## P1 - Should Have", "P2": "## P2 - Could Have", "Idea": "## Ideas — MCP Servers for Plugins", "Ideas": "## Ideas — MCP Servers for Plugins"}
    section_heading = section_map.get(priority, "## P1 - Should Have")
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

    # Update frontmatter
    count_key = {"P0": "p0-count", "P1": "p1-count", "P2": "p2-count", "Idea": "ideas-count", "Ideas": "ideas-count"}.get(priority, "p1-count")
    content = re.sub(rf"({count_key}):\s*(\d+)", lambda m: f"{count_key}: {int(m.group(2)) + 1}", content, count=1)
    content = re.sub(r"last-updated:\s*\S+", f"last-updated: {today}", content, count=1)

    BACKLOG_PATH.write_text(content, encoding="utf-8")
    typer.echo(f"Backlog item created.\n  Title: {title}\n  Priority: {priority}\n  Section: {section_heading}")

    if create_issue and priority in ("P0", "P1"):
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
            except Exception as e:
                typer.echo(f"  WARNING: Issue creation failed: {e}", err=True)

    typer.echo("Next steps: /groom-backlog-item {title}  /work-backlog-item {title}")


@app.command("list")
def list_items(
    format: Annotated[str, typer.Option("--format", "-f")] = "text",
    with_status: Annotated[bool, typer.Option("--with-status")] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """List backlog items. Use for interactive browser."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    open_items = [it for it in items if not it.get("_skip") and it.get("_section")]

    if format == "json":
        out = []
        for it in open_items:
            entry = {
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
                    status_labels = [l.name for l in issue.labels if l.name.startswith("status:")]
                    entry["status"] = status_labels[0] if status_labels else ""
                    entry["milestone"] = issue.milestone.title if issue.milestone else ""
                except Exception:
                    entry["status"] = ""
                    entry["milestone"] = ""
            out.append(entry)
        typer.echo(json.dumps(out, indent=2))
        return

    for it in open_items:
        issue = it.get("_issue", "no issue")
        plan = "✅" if it.get("**Plan**") else "📋"
        typer.echo(f"  {it.get('_section')} | {plan} | {it.get('_title', '')[:50]:<50} | {issue}")


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
    try:
        repository = _get_github(repo)
    except typer.Exit:
        raise
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    modified = False
    for item in needed:
        issue_num = create_issue_for_item(repository, item, dry_run=dry_run)
        if issue_num and not dry_run:
            content = insert_issue_into_content(content, item, issue_num)
            modified = True
    if modified:
        BACKLOG_PATH.write_text(content, encoding="utf-8")
        typer.echo(f"Updated {BACKLOG_PATH}")


@app.command()
def close(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    plan: Annotated[str, typer.Option("--plan", "-p")],
    checklist_pass: Annotated[bool, typer.Option("--checklist-pass")] = False,
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
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    raw = item.get("_raw_body", "")
    if "**Status**: DONE" in raw or "**Completed**:" in raw:
        typer.echo("Item already closed.")
        return
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
    typer.echo(f'Backlog item "{item.get("_title")}" closed.')

    issue_ref = item.get("_issue")
    if issue_ref:
        try:
            repository = _get_github(repo)
            num = issue_ref.lstrip("#")
            issue = repository.get_issue(int(num))
            issue.create_comment(f"Completed. Checklist verified. Plan: {plan}")
            issue.edit(state="closed")
            typer.echo(f"  GitHub issue #{num} closed.")
        except Exception as e:
            typer.echo(f"  WARNING: Could not close issue: {e}", err=True)


@app.command()
def resolve(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    reason: Annotated[str, typer.Option("--reason", "-r")],
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
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    raw = item.get("_raw_body", "")
    if "**Resolved**:" in raw:
        typer.echo("Item already resolved.")
        return
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
    typer.echo(f'Backlog item "{item.get("_title")}" resolved.')

    issue_ref = item.get("_issue")
    if issue_ref:
        try:
            repository = _get_github(repo)
            num = issue_ref.lstrip("#")
            issue = repository.get_issue(int(num))
            issue.create_comment(f"Resolved: {reason}")
            issue.edit(state="closed")
            typer.echo(f"  GitHub issue #{num} closed.")
        except Exception as e:
            typer.echo(f"  WARNING: Could not close issue: {e}", err=True)


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
    post = frontmatter.Post("", name=name.replace('"', "'"), description=(description or "").replace('"', "'")[:500], metadata=meta)
    return dump_frontmatter(post)


def _parse_body_extra_fields(body: str) -> tuple[str, str, str, str, str, str]:
    """Extract Description, Suggested location, Research first, Decision needed, Files, Required work from body."""
    desc = ""
    suggested = ""
    research = ""
    decision = ""
    files_val = ""
    required_work = ""
    field_re = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$", re.DOTALL)
    current_key = ""
    current_val: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_key:
                val = "\n".join(current_val).strip()
                key_lower = current_key.lower()
                if key_lower == "description":
                    desc = val
                elif key_lower == "suggested location":
                    suggested = val
                elif key_lower == "research first":
                    research = val
                elif key_lower == "decision needed":
                    decision = val
                elif key_lower == "files":
                    files_val = val
                elif key_lower == "required work":
                    required_work = val
            current_key = ""
            current_val = []
            break
        m = field_re.match(line)
        if m:
            if current_key:
                val = "\n".join(current_val).strip()
                key_lower = current_key.lower()
                if key_lower == "description":
                    desc = val
                elif key_lower == "suggested location":
                    suggested = val
                elif key_lower == "research first":
                    research = val
                elif key_lower == "decision needed":
                    decision = val
                elif key_lower == "files":
                    files_val = val
                elif key_lower == "required work":
                    required_work = val
            current_key = m.group(1).strip()
            current_val = [m.group(2).strip()] if m.group(2).strip() else []
        elif current_key:
            current_val.append(line)
    if current_key:
        val = "\n".join(current_val).strip()
        key_lower = current_key.lower()
        if key_lower == "description":
            desc = val
        elif key_lower == "suggested location":
            suggested = val
        elif key_lower == "research first":
            research = val
        elif key_lower == "decision needed":
            decision = val
        elif key_lower == "files":
            files_val = val
        elif key_lower == "required work":
            required_work = val
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


def _write_groomed_to_item_file(filepath: Path, groomed_content: str) -> None:
    """Merge groomed content into per-item file. Updates frontmatter groomed date and body."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        typer.echo("ERROR: Item file has no frontmatter", err=True)
        raise typer.Exit(1)
    parts = text.split("---", 2)
    if len(parts) < 3:
        typer.echo("ERROR: Malformed item file", err=True)
        raise typer.Exit(1)
    fm_text, body = parts[1].strip(), parts[2].strip()
    today = _today()
    groomed_section = f"## Groomed ({today})\n\n{groomed_content.strip()}"
    groomed_re = re.compile(r"\n## Groomed\s*\([^)]*\)\s*\n[\s\S]*?(?=\n## |\Z)", re.MULTILINE)
    if groomed_re.search(body):
        new_body = groomed_re.sub(f"\n{groomed_section}\n", body)
    else:
        new_body = body.rstrip() + "\n\n" + groomed_section + "\n"
    try:
        post = loads_frontmatter(text)
        if "metadata" in post.metadata and isinstance(post.metadata["metadata"], dict):
            post.metadata["metadata"]["groomed"] = today
        else:
            post.metadata["groomed"] = today
        post.content = new_body
        new_content = dump_frontmatter(post)
    except Exception:
        new_content = "---\n" + fm_text + "\n---\n\n" + new_body
        if "groomed:" not in fm_text:
            new_content = new_content.replace("---\n", f"---\ngroomed: \"{today}\"\n", 1)
    filepath.write_text(new_content, encoding="utf-8")


@app.command()
def update(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    plan: Annotated[str | None, typer.Option("--plan", "-p")] = None,
    status: Annotated[str | None, typer.Option("--status")] = None,
    create_issue: Annotated[bool, typer.Option("--create-issue")] = False,
    groomed_file: Annotated[str | None, typer.Option("--groomed-file")] = None,
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

    if groomed or groomed_file:
        if not _is_index_format(BACKLOG_PATH):
            typer.echo("ERROR: --groomed only works with index format (per-item files)", err=True)
            raise typer.Exit(1)
        filepath = item.get("_file_path")
        if not filepath:
            typer.echo("ERROR: Item has no file path", err=True)
            raise typer.Exit(1)
        filepath = Path(filepath)
        if groomed_file:
            groomed_content = Path(groomed_file).read_text(encoding="utf-8")
        else:
            groomed_content = sys.stdin.read()
        if not groomed_content.strip():
            typer.echo("ERROR: No groomed content provided", err=True)
            raise typer.Exit(1)
        _write_groomed_to_item_file(filepath, groomed_content)
        typer.echo(f"Updated {filepath.name} with groomed content")
        return

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    modified = False

    if plan:
        raw = item.get("_raw_body", "")
        if f"**Plan**: {plan}" in raw or "**Plan**: " in raw:
            pass
        else:
            lines = content.splitlines()
            start = item.get("_line_start", 1) - 1
            for i in range(start, min(start + 30, len(lines))):
                if i > start and (lines[i].startswith("###") or lines[i].startswith("## ")):
                    break
                if re.match(r"^\*\*Description\*\*:", lines[i]):
                    lines.insert(i + 1, f"**Plan**: {plan}")
                    content = "\n".join(lines) + "\n"
                    modified = True
                    break
            else:
                content = content.replace(item.get("_raw_body", ""), item.get("_raw_body", "") + f"\n**Plan**: {plan}\n")
                modified = True
        typer.echo(f"  Plan: {plan}")

    if create_issue and not item.get("_issue") and item.get("_section") in ("P0", "P1"):
        try:
            repository = _get_github(repo)
            issue_num = create_issue_for_item(repository, item, dry_run=False)
            if issue_num:
                content = insert_issue_into_content(content, item, issue_num)
                modified = True
        except Exception as e:
            typer.echo(f"  WARNING: Issue creation failed: {e}", err=True)

    if status == "in-progress" and item.get("_issue"):
        try:
            repository = _get_github(repo)
            num = item.get("_issue", "").lstrip("#")
            issue = repository.get_issue(int(num))
            labels = [l.name for l in issue.labels]
            if "status:in-progress" not in labels:
                repo_obj = repository
                lbl = repo_obj.get_label("status:in-progress")
                issue.add_to_labels(lbl)
                if "status:needs-grooming" in labels:
                    ng = repo_obj.get_label("status:needs-grooming")
                    issue.remove_from_labels(ng)
            typer.echo("  Status: in-progress")
        except Exception as e:
            typer.echo(f"  WARNING: Could not set status: {e}", err=True)

    if modified:
        BACKLOG_PATH.write_text(content, encoding="utf-8")
        typer.echo("Updated BACKLOG.md")


@app.command()
def groom(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    groomed_file: Annotated[str | None, typer.Option("--groomed-file")] = None,
) -> None:
    """Write groomed content into per-item file. Reads from --groomed-file or stdin."""
    update(
        selector=selector,
        plan=None,
        status=None,
        create_issue=False,
        groomed_file=groomed_file,
        groomed=not groomed_file,
        repo=DEFAULT_REPO,
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


@app.command()
def migrate(
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Migrate monolithic BACKLOG.md to index + per-item files in .claude/backlog/."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    items = parse_backlog_migrate(BACKLOG_PATH)
    seen_slugs: dict[str, int] = {}
    index_lines: list[str] = [
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
    section_order = ["P0", "P1", "P2", "Ideas", "completed"]
    section_headings = {
        "P0": "## P0 - Must Have",
        "P1": "## P1 - Should Have",
        "P2": "## P2 - Could Have",
        "Ideas": "## Ideas",
        "completed": "## Completed",
    }
    by_section: dict[str, list[tuple[str, str, str]]] = {s: [] for s in section_order}
    for item in items:
        section = item.get("_section") or ""
        if section not in ("P0", "P1", "P2", "Ideas", "Completed", "Format Guide"):
            continue
        title = item.get("_title", "")
        if not title or (title.startswith("~~") and "~~" in title[2:]):
            continue
        priority = _item_priority_for_migrate(item)
        slug = _title_to_slug(title)
        if slug in seen_slugs:
            seen_slugs[slug] += 1
            slug = f"{slug}-{seen_slugs[slug]}"
        else:
            seen_slugs[slug] = 0
        filename = f"{priority.lower()}-{slug}.md"
        filepath = BACKLOG_DIR / filename
        source = item.get("**Source**", "Not specified")
        added = item.get("**Added**", _today())
        priority_val = item.get("**Priority**", priority if priority != "completed" else "")
        type_val = item.get("**Type**", "Feature")
        issue = item.get("_issue", "")
        plan = item.get("**Plan**", "")
        status = _item_status_for_migrate(item)
        frontmatter_lines = [
            "---",
            f'title: "{title.replace(chr(34), chr(39))}"',
            f"source: \"{str(source).replace(chr(34), chr(39))[:200]}\"",
            f"added: \"{added}\"",
            f"priority: {priority}",
            f"type: {type_val}",
            f"status: {status}",
        ]
        if issue:
            frontmatter_lines.append(f"issue: \"{issue}\"")
        if plan:
            frontmatter_lines.append(f"plan: \"{plan}\"")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        raw_body = item.get("_raw_body", "")
        body = raw_body
        content = "\n".join(frontmatter_lines) + "\n" + body
        if not dry_run:
            filepath.write_text(content, encoding="utf-8")
        rel_path = f".claude/backlog/{filename}"
        issue_suffix = f" {issue}" if issue else ""
        by_section[priority].append((title, rel_path, issue_suffix))
    for sec in section_order:
        entries = by_section.get(sec, [])
        if not entries:
            if sec == "P0":
                index_lines.append(section_headings[sec])
                index_lines.append("")
                index_lines.append("_(Empty)_")
                index_lines.append("")
            continue
        index_lines.append(section_headings[sec])
        index_lines.append("")
        for title, rel_path, issue_suffix in entries:
            index_lines.append(f"- [{title}]({rel_path}){issue_suffix}")
        index_lines.append("")
    index_lines.append("---")
    index_lines.append("")
    index_lines.append("## Format Guide")
    index_lines.append("")
    index_lines.append("See [.claude/docs/backlog-item-groomed-schema.md](.claude/docs/backlog-item-groomed-schema.md) for groomed item structure.")
    index_content = "\n".join(index_lines)
    if dry_run:
        typer.echo(f"[dry-run] Would create {len(seen_slugs)} item files in {BACKLOG_DIR}")
        typer.echo("[dry-run] Would write new BACKLOG.md index")
        return
    backup = BACKLOG_PATH.with_suffix(".md.bak")
    backup.write_text(BACKLOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    BACKLOG_PATH.write_text(index_content, encoding="utf-8")
    typer.echo(f"Migrated {len(seen_slugs)} items to {BACKLOG_DIR}")
    typer.echo(f"Backup: {backup}")
    typer.echo("Updated BACKLOG.md to index format")


@app.command()
def normalize(
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """One-off: rewrite per-item files to research-style metadata, remove body duplication."""
    if not BACKLOG_DIR.exists():
        typer.echo(f"ERROR: {BACKLOG_DIR} not found", err=True)
        raise typer.Exit(1)
    pattern = re.compile(r"^(p0|p1|p2|ideas|completed)-[a-z0-9-]+\.md$", re.I)
    files = sorted(f for f in BACKLOG_DIR.glob("*.md") if pattern.match(f.name))
    if not files:
        typer.echo("No backlog item files found")
        return
    updated = 0
    for filepath in files:
        try:
            text = filepath.read_text(encoding="utf-8")
        except Exception as e:
            typer.echo(f"  Skip {filepath.name}: {e}", err=True)
            continue
        if not text.startswith("---"):
            continue
        try:
            post = loads_frontmatter(text)
            fm = post.metadata or {}
            body = post.content or ""
        except Exception:
            continue
        meta = fm.get("metadata") or {}
        name = str(fm.get("name") or fm.get("title") or "").strip()
        description = str(fm.get("description") or "").strip()
        source = str(meta.get("source") or fm.get("source") or "Not specified")
        added = str(meta.get("added") or fm.get("added") or _today())
        priority = str(meta.get("priority") or fm.get("priority") or "P2")
        type_val = str(meta.get("type") or fm.get("type") or "Feature")
        status = str(meta.get("status") or fm.get("status") or "open")
        issue = str(meta.get("issue") or fm.get("issue") or "")
        plan = str(meta.get("plan") or fm.get("plan") or "")
        groomed = str(meta.get("groomed") or fm.get("groomed") or "")
        if not name:
            continue
        desc, suggested, research, decision, files_val, required_work = _parse_body_extra_fields(body)
        if desc and not description:
            description = desc
        groomed_section = _extract_groomed_section(body)
        new_body = _build_body_extra_only(suggested, research, decision, files_val, required_work, groomed_section)
        fm_str = _build_backlog_frontmatter(name, description, source, added, priority, type_val, status, issue, plan, groomed)
        new_content = fm_str.rstrip()
        if not new_content.endswith("\n\n"):
            new_content += "\n"
        new_content += new_body
        if not dry_run:
            filepath.write_text(new_content, encoding="utf-8")
        updated += 1
    typer.echo(f"Normalized {updated} item file(s)" + (" [dry-run]" if dry_run else ""))


if __name__ == "__main__":
    app()
