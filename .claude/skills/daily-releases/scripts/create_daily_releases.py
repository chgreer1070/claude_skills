#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0"]
# ///
"""Create daily GitHub releases with changelogs from git commits.

Groups commits by UTC date, parses conventional commit types, generates
categorized changelogs, and creates GitHub releases with git tags.

Reuses format_mr_description.py to render the final markdown output.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="create_daily_releases",
    help="Create daily GitHub releases with categorized changelogs",
    add_completion=False,
)
console = Console()


@dataclass
class CommitInfo:
    """Commit information parsed from git log."""

    hash: str
    date: str  # YYYY-MM-DD in UTC
    author: str
    subject: str
    body: str


class ReleasesError(Exception):
    """Custom exception for release creation errors."""


def run_git_command(
    args: list[str], check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        args: Git command arguments (without 'git' prefix)
        check: Whether to raise on non-zero exit code

    Returns:
        Completed process result

    Raises:
        ReleasesError: If command fails and check is True
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        msg = f"Git command failed: {' '.join(args)}\n{e.stderr}"
        raise ReleasesError(msg) from e


def get_commits_by_day(branch: str = "HEAD") -> dict[str, list[CommitInfo]]:
    """Get all commits grouped by UTC date.

    Args:
        branch: Git branch/ref to read from

    Returns:
        dict mapping YYYY-MM-DD to list of CommitInfo

    Raises:
        ReleasesError: If git log fails
    """
    # Format: hash|date|author|subject|body separated by records with |||
    fmt = "%H%n%ai%n%an%n%s%n%b%n|||"

    result = run_git_command(
        ["log", branch, "--format=" + fmt, "--date=short"],
        check=True,
    )

    commits_by_day: dict[str, list[CommitInfo]] = {}

    for record in result.stdout.split("|||"):
        record = record.strip()
        if not record:
            continue

        lines = record.split("\n", 4)
        if len(lines) < 4:
            continue

        commit_hash = lines[0]
        full_date = lines[1]  # ISO 8601: YYYY-MM-DD HH:MM:SS +TZXX
        author = lines[2]
        subject = lines[3]
        body = lines[4] if len(lines) > 4 else ""

        # Extract date from full ISO timestamp
        date_str = full_date.split()[0]  # YYYY-MM-DD

        commit = CommitInfo(
            hash=commit_hash,
            date=date_str,
            author=author,
            subject=subject,
            body=body.strip(),
        )

        if date_str not in commits_by_day:
            commits_by_day[date_str] = []

        commits_by_day[date_str].append(commit)

    return commits_by_day


def parse_conventional_commit(subject: str) -> tuple[str, str, str]:
    """Parse conventional commit format.

    Args:
        subject: Commit subject line

    Returns:
        (commit_type, scope, description) tuple

    Example:
        "feat(auth): add JWT support" -> ("feat", "auth", "add JWT support")
    """
    # Pattern: type(scope): description or just type: description
    pattern = r"^([a-z]+)(?:\(([^)]*)\))?\s*:\s*(.*)$"
    match = re.match(pattern, subject)

    if match:
        commit_type = match.group(1)
        scope = match.group(2) or ""
        description = match.group(3)
        return (commit_type, scope, description)

    # No conventional commit format, treat entire subject as description
    return ("unknown", "", subject)


def categorize_commit(commit: CommitInfo) -> tuple[str, dict[str, Any]]:
    """Categorize a single commit into change type.

    Args:
        commit: CommitInfo object

    Returns:
        (category, entry_dict) where category is like "enhancements" or "bug_fixes"
        and entry_dict is a JSON object matching the format_mr_description schema
    """
    commit_type, scope, description = parse_conventional_commit(commit.subject)

    # Map conventional commit type to schema category
    category_map = {
        "feat": "enhancements",
        "fix": "bug_fixes",
        "refactor": "tech_debt",
        "docs": "documentation",
        "test": "testing",
        "ci": "build_ci",
        "build": "build_ci",
        "perf": "non_functional",  # Could be enhancements, but group with non-functional for simplicity
        "chore": "non_functional",
        "style": "non_functional",
        "unknown": "non_functional",
    }

    category = category_map.get(commit_type, "non_functional")

    # Build entry matching the format_mr_description schema
    if category == "enhancements":
        entry = {
            "title": description,
            "description": f"Feature added by {commit.author}",
            "benefits": f"{scope}" if scope else "general improvement",
            "usage": "",
            "files_affected": [],
            "technical_details": commit.hash[:7],
        }
    elif category == "bug_fixes":
        entry = {
            "title": description,
            "description": f"Bug fixed by {commit.author}",
            "impact": f"{scope}" if scope else "general",
            "files_affected": [],
            "technical_details": commit.hash[:7],
        }
    elif category == "tech_debt":
        entry = {
            "title": description,
            "purpose": "refactoring",
            "changes": f"Refactored by {commit.author}",
            "impact": f"{scope}" if scope else "general",
            "files_affected": [],
        }
    elif category == "documentation":
        entry = {
            "title": description,
            "updates": f"Updated by {commit.author}",
            "location": [scope] if scope else [],
            "importance": "documentation",
            "files_affected": [],
        }
    elif category == "testing":
        entry = {
            "title": description,
            "coverage": f"Test added by {commit.author}",
            "test_type": scope or "unit",
            "files_affected": [],
        }
    elif category == "build_ci":
        entry = {
            "title": description,
            "changes": f"Updated by {commit.author}",
            "impact": f"{scope}" if scope else "general",
            "files_affected": [],
        }
    else:  # non_functional
        entry = {
            "type": f"{commit_type}/{scope}" if scope else commit_type,
            "description": description,
            "files_affected": [],
        }

    return category, entry


def categorize_commits(commits: list[CommitInfo]) -> dict[str, Any]:
    """Build the format_mr_description JSON schema from commits.

    Args:
        commits: List of CommitInfo objects

    Returns:
        Dictionary matching format_mr_description.py schema
    """
    analysis: dict[str, Any] = {
        "title": f"Daily Release - {commits[0].date if commits else 'unknown'}",
        "summary": f"Daily changes from {len(commits)} commit{'s' if len(commits) != 1 else ''}",
        "statistics": {
            "commits": len(commits),
            "files_changed": 0,  # Can't extract without diff
            "lines_added": 0,
            "lines_deleted": 0,
        },
        "change_categories": {
            "bug_fixes": [],
            "enhancements": [],
            "tech_debt": [],
            "documentation": [],
            "testing": [],
            "build_ci": [],
            "non_functional": [],
        },
        "components_affected": [],
        "breaking_changes": [],
    }

    # Categorize each commit
    for commit in commits:
        category, entry = categorize_commit(commit)
        if category in analysis["change_categories"]:
            analysis["change_categories"][category].append(entry)

    return analysis


def release_exists(tag: str) -> bool:
    """Check if a GitHub release tag already exists.

    Args:
        tag: Tag/release name

    Returns:
        True if release exists, False otherwise
    """
    result = run_git_command(
        ["rev-parse", tag],
        check=False,
    )
    return result.returncode == 0


def get_tag_commit(tag: str) -> str | None:
    """Get the commit hash a tag points to.

    Args:
        tag: Tag name

    Returns:
        Commit hash or None if tag doesn't exist
    """
    result = run_git_command(
        ["rev-list", "-n", "1", tag],
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_next_revision_tag(base_tag: str) -> str:
    """Get the next revision tag (e.g., daily-2026-02-21-r2).

    Args:
        base_tag: Base tag name (e.g., daily-2026-02-21)

    Returns:
        Next revision tag name
    """
    revision = 2
    while release_exists(f"{base_tag}-r{revision}"):
        revision += 1
    return f"{base_tag}-r{revision}"


def create_git_tag(tag: str, commit_hash: str) -> None:
    """Create a git tag.

    Args:
        tag: Tag name
        commit_hash: Commit hash to tag

    Raises:
        ReleasesError: If tag creation fails
    """
    run_git_command(
        ["tag", "-f", tag, commit_hash],
        check=True,
    )


def push_tag(tag: str) -> None:
    """Push a git tag to remote.

    Args:
        tag: Tag name

    Raises:
        ReleasesError: If push fails
    """
    run_git_command(
        ["push", "origin", tag, "--force"],
        check=True,
    )


def update_github_release(
    tag: str, date: str, markdown_body: str
) -> None:
    """Update an existing GitHub release body.

    Args:
        tag: Release tag
        date: Date string for title
        markdown_body: Release notes markdown

    Raises:
        ReleasesError: If release update fails
    """
    title = f"Daily Release - {date}"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(markdown_body)
        temp_file = f.name

    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "edit",
                tag,
                "--title",
                title,
                "--notes-file",
                temp_file,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        if result.returncode != 0:
            msg = f"Failed to update release: {result.stderr}"
            raise ReleasesError(msg)
    finally:
        Path(temp_file).unlink()


def create_github_release(
    tag: str, date: str, markdown_body: str, dry_run: bool = False
) -> None:
    """Create a GitHub release.

    Args:
        tag: Release tag
        date: Date string for title
        markdown_body: Release notes markdown
        dry_run: If True, print what would be done without running gh

    Raises:
        ReleasesError: If release creation fails
    """
    title = f"Daily Release - {date}"

    if dry_run:
        console.print(f"[dim]Would create release:[/dim] {title}")
        return

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(markdown_body)
        temp_file = f.name

    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "create",
                tag,
                "--title",
                title,
                "--notes-file",
                temp_file,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

        if result.returncode != 0:
            msg = f"Failed to create release: {result.stderr}"
            raise ReleasesError(msg)
    finally:
        Path(temp_file).unlink()


def format_changelog(analysis_json: dict[str, Any]) -> str:
    """Generate markdown changelog from categorized analysis.

    Args:
        analysis_json: Categorized analysis dictionary

    Returns:
        Rendered markdown string
    """
    lines = []

    # Title
    lines.append(f"# {analysis_json.get('title', 'Daily Release')}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append(analysis_json.get("summary", "Daily changes"))
    lines.append("")

    # Statistics
    stats = analysis_json.get("statistics", {})
    lines.append("## Statistics")
    lines.append(f"- **Commits**: {stats.get('commits', 0)}")
    lines.append(f"- **Files Changed**: {stats.get('files_changed', 0)}")
    lines.append(f"- **Lines Added**: {stats.get('lines_added', 0)}")
    lines.append(f"- **Lines Deleted**: {stats.get('lines_deleted', 0)}")
    lines.append("")

    # Changes by category
    categories = analysis_json.get("change_categories", {})

    if any(categories.values()):
        lines.append("## Changes by Category")
        lines.append("")

        # Enhancements
        if categories.get("enhancements"):
            lines.append("### Enhancements")
            for item in categories["enhancements"]:
                lines.append(f"- **{item.get('title', 'Enhancement')}**")
                if item.get("description"):
                    lines.append(f"  - {item['description']}")
            lines.append("")

        # Bug Fixes
        if categories.get("bug_fixes"):
            lines.append("### Bug Fixes")
            for item in categories["bug_fixes"]:
                lines.append(f"- **{item.get('title', 'Fix')}**")
                if item.get("description"):
                    lines.append(f"  - {item['description']}")
            lines.append("")

        # Tech Debt
        if categories.get("tech_debt"):
            lines.append("### Technical Debt")
            for item in categories["tech_debt"]:
                lines.append(f"- **{item.get('title', 'Refactor')}**")
                if item.get("purpose"):
                    lines.append(f"  - Purpose: {item['purpose']}")
            lines.append("")

        # Documentation
        if categories.get("documentation"):
            lines.append("### Documentation")
            for item in categories["documentation"]:
                lines.append(f"- **{item.get('title', 'Docs')}**")
                if item.get("updates"):
                    lines.append(f"  - {item['updates']}")
            lines.append("")

        # Testing
        if categories.get("testing"):
            lines.append("### Testing")
            for item in categories["testing"]:
                lines.append(f"- **{item.get('title', 'Test')}**")
                if item.get("coverage"):
                    lines.append(f"  - {item['coverage']}")
            lines.append("")

        # Build & CI
        if categories.get("build_ci"):
            lines.append("### Build & CI")
            for item in categories["build_ci"]:
                lines.append(f"- **{item.get('title', 'Build')}**")
                if item.get("changes"):
                    lines.append(f"  - {item['changes']}")
            lines.append("")

        # Non-Functional
        if categories.get("non_functional"):
            lines.append("### Non-Functional Changes")
            for item in categories["non_functional"]:
                item_type = item.get("type", "change")
                desc = item.get("description", "")
                lines.append(f"- **{item_type}**: {desc}")
            lines.append("")

    # Components affected
    components = analysis_json.get("components_affected", [])
    if components:
        lines.append("## Components Affected")
        for component in components:
            lines.append(f"- {component}")
        lines.append("")

    # Breaking changes
    breaking = analysis_json.get("breaking_changes", [])
    if breaking:
        lines.append("## Breaking Changes")
        for item in breaking:
            lines.append(f"- **{item.get('change', 'Change')}**")
            if item.get("migration"):
                lines.append(f"  - Migration: {item['migration']}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `/create-merge-request-changelog` skill*")

    return "\n".join(lines)


def process_day(
    date: str,
    commits: list[CommitInfo],
    dry_run: bool = False,
) -> None:
    """Process one day end-to-end: categorize, format, tag, and release.

    Handles three scenarios:
    1. No release exists → create new tag and release
    2. Release exists, new commits added → rename tag to -r2/-r3, create new tag and release
    3. Release exists, same commits → update release notes only

    Args:
        date: Date string YYYY-MM-DD
        commits: List of commits for this day
        dry_run: If True, print what would be done

    Raises:
        ReleasesError: If any step fails
    """
    if not commits:
        return

    tag = f"daily-{date}"

    # Get last commit hash of the day
    last_commit_hash = commits[-1].hash

    # Categorize commits
    analysis = categorize_commits(commits)

    # Format changelog
    try:
        markdown = format_changelog(analysis)
    except ReleasesError as e:
        console.print(f"[red]Error formatting changelog for {date}: {e}[/red]")
        raise

    if dry_run:
        console.print(f"\n[cyan]Day: {date}[/cyan]")
        console.print(f"[dim]Tag:[/dim] {tag}")
        console.print(f"[dim]Commit:[/dim] {last_commit_hash}")
        console.print(f"[dim]Commits:[/dim] {len(commits)}")
        console.print(f"[dim]Markdown preview (first 500 chars):[/dim]")
        console.print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        return

    try:
        # Check if release tag already exists
        if release_exists(tag):
            existing_commit = get_tag_commit(tag)

            if existing_commit == last_commit_hash:
                # Same commits, just update release notes
                update_github_release(tag, date, markdown)
                console.print(f"[yellow]Updated release notes: {tag}[/yellow]")
            else:
                # New commits added, rename old tag and create new one
                revision_tag = get_next_revision_tag(tag)

                # Rename old tag (via git command)
                run_git_command(
                    ["tag", "-m", f"Revision of {tag}", revision_tag, tag],
                    check=True,
                )
                # Push revision tag
                run_git_command(
                    ["push", "origin", revision_tag],
                    check=True,
                )

                # Create new main tag
                create_git_tag(tag, last_commit_hash)
                push_tag(tag)

                # Update release for new tag
                create_github_release(tag, date, markdown, dry_run=False)
                console.print(
                    f"[green]Updated {tag} (moved old to {revision_tag})[/green]"
                )
        else:
            # New release, create tag and release
            create_git_tag(tag, last_commit_hash)
            push_tag(tag)
            create_github_release(tag, date, markdown, dry_run=False)
            console.print(f"[green]Created release: {tag}[/green]")

    except ReleasesError as e:
        console.print(f"[red]Error processing {date}: {e}[/red]")
        raise


@app.command()
def create_releases(
    start_date: Annotated[
        str | None,
        typer.Option(
            help="Start date (YYYY-MM-DD), inclusive. Default: all history"
        ),
    ] = None,
    end_date: Annotated[
        str | None,
        typer.Option(help="End date (YYYY-MM-DD), inclusive. Default: today"),
    ] = None,
    branch: Annotated[
        str,
        typer.Option(help="Git branch/ref to read from"),
    ] = "HEAD",
    dry_run: Annotated[
        bool,
        typer.Option(help="Print what would be created without making changes"),
    ] = False,
    skip_existing: Annotated[
        bool,
        typer.Option(
            help="Skip days where a release already exists (default: True)",
        ),
    ] = True,
) -> None:
    """Create daily GitHub releases with changelogs from git commits.

    Groups commits by UTC date, categorizes by conventional commit type,
    generates changelogs, and creates GitHub releases with git tags.

    Examples:

        # Dry run: see what would be created
        uv run create_daily_releases.py --dry-run

        # Process all history
        uv run create_daily_releases.py

        # Process specific date range
        uv run create_daily_releases.py --start-date 2026-02-20 --end-date 2026-02-21

        # One specific day
        uv run create_daily_releases.py --start-date 2026-02-21 --end-date 2026-02-21
    """
    console.print("[cyan]Fetching commits by day...[/cyan]")

    try:
        commits_by_day = get_commits_by_day(branch)
    except ReleasesError as e:
        console.print(f"[red]Error fetching commits: {e}[/red]")
        sys.exit(1)

    if not commits_by_day:
        console.print("[yellow]No commits found[/yellow]")
        sys.exit(0)

    # Filter by date range
    dates = sorted(commits_by_day.keys())
    if start_date:
        dates = [d for d in dates if d >= start_date]
    if end_date:
        dates = [d for d in dates if d <= end_date]

    console.print(
        f"[cyan]Found {len(commits_by_day)} days with commits, "
        f"processing {len(dates)} days[/cyan]"
    )

    if dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")

    # Process each day
    failed = False
    if len(dates) == 0:
        console.print("[yellow]No dates to process[/yellow]")
    else:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing...", total=len(dates))

                for date in dates:
                    progress.update(task, description=f"Processing {date}...")

                    try:
                        process_day(date, commits_by_day[date], dry_run=dry_run)
                    except ReleasesError as e:
                        console.print(f"[red]Error: {e}[/red]")
                        failed = True

                    progress.advance(task)
        except UnicodeEncodeError:
            # Fallback for Windows console encoding issues
            for date in dates:
                console.print(f"Processing {date}...")
                try:
                    process_day(date, commits_by_day[date], dry_run=dry_run)
                except ReleasesError as e:
                    console.print(f"[red]Error: {e}[/red]")
                    failed = True

    if failed:
        console.print("[red]Some days failed - see errors above[/red]")
        sys.exit(1)
    else:
        if dry_run:
            console.print("[cyan]Dry run complete![/cyan]")
        else:
            console.print("[green]All releases created successfully![/green]")


def main() -> None:
    """Run the CLI app."""
    app()


if __name__ == "__main__":
    main()
