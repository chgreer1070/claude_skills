#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "PyGithub>=2.1.1",
#   "typer>=0.21.0",
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

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from github import Auth, Github, GithubException

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
BACKLOG_PATH = _REPO_ROOT / ".claude" / "BACKLOG.md"
DEFAULT_REPO = "Jamie-BitFlight/claude_skills"

# Regex
ITEM_HEADER_RE = re.compile(r"^###\s+(.+)$")
FIELD_RE = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$", re.DOTALL)
SECTION_RE = re.compile(r"^##\s+(P0|P1|P2|Ideas)")
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


def parse_backlog(path: Path) -> list[dict]:
    """Parse BACKLOG.md into items with section, title, and fields."""
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


@app.command()
def update(
    selector: Annotated[str, typer.Argument(help="Title substring or #N")],
    plan: Annotated[str | None, typer.Option("--plan", "-p")] = None,
    status: Annotated[str | None, typer.Option("--status")] = None,
    create_issue: Annotated[bool, typer.Option("--create-issue")] = False,
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
) -> None:
    """Update item: add Plan, set status:in-progress, or create issue."""
    if not BACKLOG_PATH.exists():
        typer.echo(f"ERROR: {BACKLOG_PATH} not found", err=True)
        raise typer.Exit(1)
    items = parse_backlog(BACKLOG_PATH)
    item = find_item(items, selector)
    if not item:
        typer.echo(f"ERROR: No item found for: {selector}", err=True)
        raise typer.Exit(1)
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


if __name__ == "__main__":
    app()
