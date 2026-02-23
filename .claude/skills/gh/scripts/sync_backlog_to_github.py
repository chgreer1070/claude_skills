#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "PyGithub>=2.1.1",
# ]
# ///
"""Sync P0/P1 backlog items to GitHub Issues.

Parses .claude/BACKLOG.md, finds P0/P1 items without **Issue**: #N,
creates GitHub issues, and updates BACKLOG.md with issue numbers.

Usage:
    sync_backlog_to_github.py [--repo OWNER/REPO] [--dry-run]

Environment:
    GITHUB_TOKEN  Required for API access.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add parent for github_project_setup imports
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from github import Auth, Github, GithubException

DEFAULT_REPO = "Jamie-BitFlight/claude_skills"
BACKLOG_PATH = _REPO_ROOT / ".claude" / "BACKLOG.md"

# Match ### Title (strip ~~strikethrough~~)
ITEM_HEADER_RE = re.compile(r"^###\s+(.+)$")
# Match **Field**: value
FIELD_RE = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$", re.DOTALL)
# Section headers
SECTION_RE = re.compile(r"^##\s+(P0|P1|P2|Ideas)")

# Skip items with these (case-insensitive substring)
SKIP_STATUS = ("DONE", "RESOLVED", "COMPLETED")
TYPE_TO_LABEL = {
    "feature": "type:feature",
    "bug": "type:bug",
    "refactor": "type:refactor",
    "docs": "type:docs",
    "chore": "type:chore",
}


def _infer_type(description: str, title: str) -> str:
    """Infer type label from description or title."""
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
            # Join multiline field values
            for k, v in current_item.items():
                if isinstance(v, list):
                    current_item[k] = "\n".join(v).strip()
            current_item["_raw_body"] = "\n".join(current_body)
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
            # Skip strikethrough (completed/resolved)
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
            elif key_lower == "completed":
                current_item["_skip"] = True
                current_field_value = []
            elif key_lower == "resolved":
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


def items_needing_issues(items: list[dict]) -> list[dict]:
    """Filter to P0/P1 items without Issue and not skipped."""
    out = []
    for it in items:
        if it.get("_section") not in ("P0", "P1"):
            continue
        if it.get("_skip"):
            continue
        if it.get("_issue"):
            continue
        out.append(it)
    return out


def build_issue_body(item: dict) -> str:
    """Build story-format issue body."""
    title = item.get("_title", "")
    desc = item.get("**Description**", "")
    source = item.get("**Source**", "Not specified")
    added = item.get("**Added**", "")
    priority = item.get("**Priority**", "")
    research = item.get("**Research first**", "")

    # One-line goal from first sentence of description
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


def create_issue(repo: str, item: dict, dry_run: bool) -> int | None:
    """Create GitHub issue, return issue number or None."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set", file=sys.stderr)
        return None

    gh = Github(auth=Auth.Token(token))
    try:
        repository = gh.get_repo(repo)
    except GithubException as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None

    title = item.get("_title", "")
    if not title:
        return None

    # Conventional commit style title
    type_label = item.get("**Type**", "")
    type_map = {"feature": "feat", "bug": "fix", "refactor": "refactor", "docs": "docs", "chore": "chore"}
    prefix = type_map.get(type_label.lower(), "feat")
    issue_title = f"{prefix}: {title}"

    body = build_issue_body(item)
    priority = item.get("**Priority**", "P1")
    type_gh = TYPE_TO_LABEL.get(type_label.lower()) or _infer_type(
        item.get("**Description**", ""), title
    )
    priority_gh = f"priority:{priority.lower()}"

    if dry_run:
        print(f"  [dry-run] Would create: {issue_title}")
        return None

    labels = ["status:needs-grooming", priority_gh, type_gh]
    label_objs = []
    for name in labels:
        try:
            label_objs.append(repository.get_label(name))
        except GithubException:
            print(f"  WARNING: label '{name}' not found", file=sys.stderr)

    issue = repository.create_issue(title=issue_title, body=body, labels=label_objs)
    print(f"  Created #{issue.number}: {issue_title[:60]}...")
    return issue.number


def insert_issue_into_item(content: str, item: dict, issue_num: int) -> str:
    """Insert **Issue**: #N after **Priority** or **Type** in the item block."""
    new_line = f"**Issue**: #{issue_num}"
    if new_line in item.get("_raw_body", ""):
        return content  # Already present

    lines = content.splitlines()
    start = max(0, item.get("_line_start", 1) - 1)
    # Search within item block (stop at next ### or ##)
    for i in range(start, min(start + 25, len(lines))):
        if i > start and (lines[i].startswith("###") or lines[i].startswith("## ")):
            break
        if re.match(r"^\*\*Priority\*\*:", lines[i]) or re.match(r"^\*\*Type\*\*:", lines[i]):
            indent = "  " if lines[i].startswith("  ") else ""
            lines.insert(i + 1, f"{indent}{new_line}")
            return "\n".join(lines) + "\n"
    # Fallback: insert after first ** field
    for i in range(start, min(start + 15, len(lines))):
        if re.match(r"^\*\*[^*]+\*\*:", lines[i]):
            indent = "  " if lines[i].startswith("  ") else ""
            lines.insert(i + 1, f"{indent}{new_line}")
            return "\n".join(lines) + "\n"
    return content


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Sync P0/P1 backlog items to GitHub")
    parser.add_argument("--repo", "-R", default=DEFAULT_REPO, help="GitHub repo OWNER/REPO")
    parser.add_argument("--dry-run", action="store_true", help="Do not create issues or write")
    args = parser.parse_args()

    if not BACKLOG_PATH.exists():
        print(f"ERROR: {BACKLOG_PATH} not found", file=sys.stderr)
        return 1

    items = parse_backlog(BACKLOG_PATH)
    needed = items_needing_issues(items)
    if not needed:
        print("No P0/P1 items need GitHub issues.")
        return 0

    print(f"Found {len(needed)} P0/P1 item(s) without GitHub issues:")
    for it in needed:
        print(f"  - {it.get('_title', '')[:60]}")

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    modified = False

    for item in needed:
        issue_num = create_issue(args.repo, item, args.dry_run)
        if issue_num and not args.dry_run:
            content = insert_issue_into_item(content, item, issue_num)
            modified = True

    if modified and not args.dry_run:
        BACKLOG_PATH.write_text(content, encoding="utf-8")
        print(f"Updated {BACKLOG_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
