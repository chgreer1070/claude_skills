#!/usr/bin/env python3
"""Add all open GitHub issues to the Projects V2 board and set Priority field.

Uses PyGithub for issue listing and gh CLI for Projects V2 GraphQL mutations
(PyGithub doesn't support Projects V2 yet).

Usage:
    uv run .claude/scripts/sync_issues_to_project.py --dry-run
    uv run .claude/scripts/sync_issues_to_project.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import TYPE_CHECKING

from github import Auth, Github

if TYPE_CHECKING:
    from github.Issue import Issue
    from github.Label import Label

REPO_NAME = "Jamie-BitFlight/claude_skills"

# Project V2 IDs — hardcoded from project creation
PROJECT_ID = "PVT_kwHOAX6fMM4BQMJM"
PRIORITY_FIELD_ID = "PVTSSF_lAHOAX6fMM4BQMJMzg-YasY"
STATUS_FIELD_ID = "PVTSSF_lAHOAX6fMM4BQMJMzg-YaiU"

PRIORITY_OPTIONS = {"P0": "b0ccc2bd", "P1": "13595533", "P2": "43cab69c", "Idea": "5183890e", "Ideas": "5183890e"}

STATUS_OPTIONS = {
    "Backlog": "1ffc676b",
    "In Progress": "d6aa9a31",
    "In Review": "01ac4008",
    "Blocked": "2f9f58fc",
    "Done": "da483541",
}

GH_CLI = "/usr/local/bin/gh"


def gh_graphql(query: str) -> dict:
    """Execute a GraphQL query via gh CLI.

    Args:
        query: GraphQL query string

    Returns:
        Parsed JSON response
    """
    result = subprocess.run(
        [GH_CLI, "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def get_priority_from_labels(labels: list[Label]) -> str:
    """Extract priority from issue labels, defaulting to P2.

    Args:
        labels: List of GitHub Label objects

    Returns:
        Priority string (P0, P1, P2, Idea)
    """
    for label in labels:
        if label.name.startswith("priority:"):
            p = label.name.split(":")[1]
            return p.upper() if p.startswith("p") else p.capitalize()
    return "P2"


def add_issue_to_project(issue_node_id: str) -> str | None:
    """Add an issue to the project board via GraphQL.

    Args:
        issue_node_id: GitHub GraphQL node ID for the issue

    Returns:
        Project item ID or None on failure
    """
    query = (
        "mutation {"
        f'  addProjectV2ItemById(input: {{projectId: "{PROJECT_ID}", contentId: "{issue_node_id}"}}) {{'
        "    item { id }"
        "  }"
        "}"
    )
    resp = gh_graphql(query)
    item = resp.get("data", {}).get("addProjectV2ItemById", {}).get("item", {})
    return item.get("id")


def set_field_value(item_id: str, field_id: str, option_id: str) -> None:
    """Set a single-select field value on a project item.

    Args:
        item_id: Project item ID
        field_id: Field ID (Priority or Status)
        option_id: Option ID to set
    """
    query = (
        "mutation {"
        "  updateProjectV2ItemFieldValue(input: {"
        f'    projectId: "{PROJECT_ID}", itemId: "{item_id}",'
        f'    fieldId: "{field_id}",'
        f'    value: {{singleSelectOptionId: "{option_id}"}}'
        "  }) { projectV2Item { id } }"
        "}"
    )
    gh_graphql(query)


def sync_issue(issue: Issue, priority: str, *, dry_run: bool) -> bool:
    """Add a single issue to the project board and set its fields.

    Args:
        issue: PyGithub Issue object
        priority: Priority string (P0, P1, P2, Idea)
        dry_run: If True, only print what would happen

    Returns:
        True if added successfully
    """
    priority_option = PRIORITY_OPTIONS.get(priority)
    if not priority_option:
        print(f"  SKIP #{issue.number}: unknown priority '{priority}'")
        return False

    if dry_run:
        print(f"  WOULD ADD #{issue.number}: {issue.title} (Priority: {priority})")
        return True

    item_id = add_issue_to_project(issue.node_id)
    if not item_id:
        print(f"  ERROR #{issue.number}: failed to add to project")
        return False

    set_field_value(item_id, PRIORITY_FIELD_ID, priority_option)
    set_field_value(item_id, STATUS_FIELD_ID, STATUS_OPTIONS["Backlog"])
    print(f"  ADDED #{issue.number}: {issue.title} (Priority: {priority})")
    return True


def main() -> None:
    """Sync all open issues to the project board with Priority and Status fields."""
    dry_run = "--dry-run" in sys.argv

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    gh = Github(auth=Auth.Token(token))
    repo = gh.get_repo(REPO_NAME)
    open_issues = [i for i in repo.get_issues(state="open") if not i.pull_request]
    print(f"Found {len(open_issues)} open issues")

    added = 0
    errors = 0

    for issue in open_issues:
        priority = get_priority_from_labels(list(issue.labels))
        try:
            if sync_issue(issue, priority, dry_run=dry_run):
                added += 1
            else:
                errors += 1
        except subprocess.CalledProcessError as exc:
            print(f"  ERROR #{issue.number}: {exc.stderr or exc}")
            errors += 1

    print(f"\nDone: {added} added, {errors} errors")


if __name__ == "__main__":
    main()
