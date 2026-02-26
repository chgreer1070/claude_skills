#!/usr/bin/env python3
"""Rebuild GitHub issue bodies from backlog per-item files into proper story format.

Reads .claude/backlog/*.md files, matches them to open GitHub issues via PyGithub,
and updates each issue body to follow the story template.

Usage:
    uv run .claude/scripts/rebuild_issue_bodies.py --dry-run
    uv run .claude/scripts/rebuild_issue_bodies.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from github import Auth, Github
from ruamel.yaml import YAML

REPO_NAME = "Jamie-BitFlight/claude_skills"
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

_yaml = YAML(typ="safe")


def parse_backlog_file(path: Path) -> dict[str, str]:
    """Parse a backlog per-item file using ruamel.yaml for frontmatter.

    Args:
        path: Path to the markdown file

    Returns:
        Flat dictionary with name, description, source, added, priority, type, extra_body
    """
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return {}

    fm = _yaml.load(match.group(1))
    if not isinstance(fm, dict):
        return {}

    body_text = match.group(2).strip()
    metadata = fm.get("metadata", {}) or {}

    result: dict[str, str] = {
        "name": str(fm.get("name", "")),
        "description": str(fm.get("description", "")),
        "source": str(metadata.get("source", "Not specified")),
        "added": str(metadata.get("added", "Unknown")),
        "priority": str(metadata.get("priority", "Unknown")),
        "type": str(metadata.get("type", "Feature")),
    }
    if body_text:
        result["extra_body"] = body_text

    return result


def extract_extra_fields(extra: str) -> dict[str, str]:
    """Extract structured fields from the extra body text.

    Args:
        extra: Body text after frontmatter

    Returns:
        Dictionary with research_first, suggested_location, files, notes
    """
    fields: dict[str, str] = {}
    notes_lines: list[str] = []

    for raw_line in extra.split("\n"):
        if raw_line.startswith("**Research first**:"):
            fields["research_first"] = raw_line.split(":", 1)[1].strip()
        elif raw_line.startswith("**Suggested location**:"):
            fields["suggested_location"] = raw_line.split(":", 1)[1].strip()
        elif raw_line.startswith("**Files**:"):
            fields["files"] = raw_line.split(":", 1)[1].strip()
        elif raw_line.strip() and not raw_line.startswith("---"):
            notes_lines.append(raw_line)

    if notes_lines:
        fields["notes"] = "\n".join(notes_lines)

    return fields


def build_story_body(item: dict[str, str]) -> str:
    """Build a story-format issue body from backlog item data.

    Args:
        item: Parsed item dict from per-item file

    Returns:
        Formatted issue body string
    """
    description = item.get("description", "No description")
    item_type = item.get("type", "Feature")
    role = ROLE_MAP.get(item_type, "developer using Claude Code skills")
    benefit = BENEFIT_MAP.get(item_type, "the product improves")
    goal = description.rstrip(".")

    extra_fields = extract_extra_fields(item.get("extra_body", ""))

    sections = [
        f"## Story\n\nAs a **{role}**, I want to **{goal.lower()}** so that **{benefit}**.",
        f"## Description\n\n{description}",
    ]

    if extra_fields.get("files"):
        sections.append(f"## Files\n\n{extra_fields['files']}")

    if extra_fields.get("suggested_location"):
        sections.append(f"## Suggested Location\n\n{extra_fields['suggested_location']}")

    context_lines = [
        f"- **Source**: {item.get('source', 'Not specified')}",
        f"- **Priority**: {item.get('priority', 'Unknown')}",
        f"- **Added**: {item.get('added', 'Unknown')}",
        f"- **Research questions**: {extra_fields.get('research_first', 'None')}",
    ]
    sections.append("## Context\n\n" + "\n".join(context_lines))

    if extra_fields.get("notes"):
        sections.append(f"## Notes\n\n{extra_fields['notes']}")

    return "\n\n".join(sections) + "\n"


def normalize_title(title: str) -> str:
    """Normalize an issue title for matching.

    Args:
        title: Raw issue title

    Returns:
        Lowercased title with common prefixes stripped
    """
    clean = re.sub(r"^(feat|fix|chore|docs|refactor):\s*", "", title)
    clean = re.sub(r"^P[012]:\s*", "", clean)
    return clean.lower().strip()


def main() -> None:
    """Rebuild all open GitHub issue bodies from backlog per-item files."""
    dry_run = "--dry-run" in sys.argv

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    items: dict[str, dict[str, str]] = {}
    for path in sorted(BACKLOG_DIR.glob("*.md")):
        if path.name.startswith("completed-"):
            continue
        data = parse_backlog_file(path)
        if data.get("name"):
            items[data["name"].lower().strip()] = data

    print(f"Loaded {len(items)} backlog items from {BACKLOG_DIR}")

    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(REPO_NAME)
    open_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    print(f"Found {len(open_issues)} open GitHub issues")

    updated = 0
    skipped = 0
    no_match = 0

    for issue in open_issues:
        key = normalize_title(issue.title)
        item = items.get(key)
        if not item:
            for item_key, item_data in items.items():
                if item_key in key or key in item_key:
                    item = item_data
                    break

        if not item:
            print(f"  SKIP #{issue.number}: no backlog match — {issue.title}")
            no_match += 1
            continue

        if issue.body and "## Story" in issue.body:
            skipped += 1
            continue

        new_body = build_story_body(item)

        if dry_run:
            print(f"  WOULD UPDATE #{issue.number}: {issue.title}")
        else:
            issue.edit(body=new_body)
            print(f"  UPDATED #{issue.number}: {issue.title}")

        updated += 1

    print(f"\nDone: {updated} updated, {skipped} already story format, {no_match} no match")


if __name__ == "__main__":
    main()
