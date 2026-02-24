#!/usr/bin/env python3
"""GitLab merge request fetcher - extracts MR metadata and changes via glab CLI.

This script fetches merge request details from GitLab including metadata,
commits, and diffs, outputting structured JSON for further processing.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Annotated, Any

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

_DESCRIPTION_PREVIEW_MAX_LENGTH = 200  # Max characters for MR description preview

app = typer.Typer(name="fetch_gitlab_mr", help="Fetch GitLab merge request metadata and changes", add_completion=False)
console = Console()


class GitLabFetchError(Exception):
    """Custom exception for GitLab fetch errors."""


def run_glab_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a glab CLI command and return the result.

    Args:
        args: glab command arguments (without 'glab' prefix)
        check: Whether to raise on non-zero exit code

    Returns:
        Completed process result

    Raises:
        GitLabFetchError: If command fails and check=True
    """
    try:
        return subprocess.run(["glab", *args], capture_output=True, text=True, check=check)
    except FileNotFoundError as e:
        msg = "glab CLI not found. Install it from https://gitlab.com/gitlab-org/cli"
        raise GitLabFetchError(msg) from e
    except subprocess.CalledProcessError as e:
        msg = f"glab command failed: {e.stderr.strip()}"
        raise GitLabFetchError(msg) from e


def extract_mr_id(mr_identifier: str) -> str:
    """Extract MR ID from URL or direct ID.

    Args:
        mr_identifier: MR URL or ID (e.g., "123", "!123", "https://gitlab.com/org/project/-/merge_requests/123")

    Returns:
        MR ID as string

    Raises:
        GitLabFetchError: If MR ID cannot be extracted
    """
    # Try URL pattern first
    url_pattern = r"merge_requests/(\d+)"
    url_match = re.search(url_pattern, mr_identifier)
    if url_match:
        return url_match.group(1)

    # Try direct ID pattern (with or without !)
    id_pattern = r"!?(\d+)"
    id_match = re.fullmatch(id_pattern, mr_identifier)
    if id_match:
        return id_match.group(1)

    msg = f"Could not extract MR ID from '{mr_identifier}'. Provide ID as number (123), !123, or full URL."
    raise GitLabFetchError(msg)


def fetch_mr_metadata(mr_id: str) -> dict[str, Any]:
    """Fetch merge request metadata using glab CLI.

    Args:
        mr_id: MR ID

    Returns:
        Dictionary containing MR metadata

    Raises:
        GitLabFetchError: If fetch fails
    """
    result = run_glab_command(["mr", "view", mr_id, "--json"])

    try:
        mr_data: dict[str, Any] = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON response from glab: {e}"
        raise GitLabFetchError(msg) from e

    if not mr_data:
        msg = f"No data returned for MR {mr_id}"
        raise GitLabFetchError(msg)

    return mr_data


def fetch_mr_commits(mr_id: str) -> list[dict[str, str]]:
    """Fetch commit list for merge request.

    Args:
        mr_id: MR ID

    Returns:
        List of commit dictionaries with sha, title, and author

    Raises:
        GitLabFetchError: If fetch fails
    """
    result = run_glab_command(["mr", "view", mr_id, "--json", "--jq", ".commits"])

    try:
        commits_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON response for commits: {e}"
        raise GitLabFetchError(msg) from e

    if not commits_data:
        return []

    # Transform commit data to simpler format
    return [
        {"sha": commit.get("sha", ""), "title": commit.get("title", ""), "author": commit.get("author_name", "")}
        for commit in commits_data
    ]


def fetch_mr_changes(mr_id: str) -> str:
    """Fetch unified diff for merge request.

    Args:
        mr_id: MR ID

    Returns:
        Unified diff as string

    Raises:
        GitLabFetchError: If fetch fails
    """
    result = run_glab_command(["mr", "diff", mr_id])
    return result.stdout


def parse_labels(labels_list: list[str] | None) -> list[str]:
    """Parse and clean labels list.

    Args:
        labels_list: Raw labels list from API

    Returns:
        Cleaned labels list
    """
    if not labels_list:
        return []

    # Filter out empty strings and strip whitespace
    return [label.strip() for label in labels_list if label and label.strip()]


def create_mr_summary(mr_data: dict[str, Any], commits: list[dict[str, str]]) -> dict[str, Any]:
    """Create structured MR summary from raw data.

    Args:
        mr_data: Raw MR metadata from glab
        commits: List of commits

    Returns:
        Structured MR summary dictionary
    """
    return {
        "id": mr_data.get("number", ""),
        "iid": mr_data.get("iid", ""),
        "title": mr_data.get("title", ""),
        "description": mr_data.get("description", ""),
        "state": mr_data.get("state", ""),
        "source_branch": mr_data.get("source_branch", ""),
        "target_branch": mr_data.get("target_branch", ""),
        "author": {
            "username": mr_data.get("author", {}).get("username", ""),
            "name": mr_data.get("author", {}).get("name", ""),
        },
        "web_url": mr_data.get("web_url", ""),
        "labels": parse_labels(mr_data.get("labels")),
        "created_at": mr_data.get("created_at", ""),
        "updated_at": mr_data.get("updated_at", ""),
        "merged_at": mr_data.get("merged_at"),
        "commits": commits,
        "commit_count": len(commits),
        "has_conflicts": mr_data.get("has_conflicts", False),
        "work_in_progress": mr_data.get("work_in_progress", False),
    }


def create_summary_table(mr_summary: dict[str, Any]) -> Table:
    """Create a Rich table for MR summary display.

    Args:
        mr_summary: MR summary dictionary

    Returns:
        Rich Table object
    """
    table = Table(
        title=f":merge: Merge Request !{mr_summary['iid']}", box=box.MINIMAL_DOUBLE_HEAD, title_style="bold blue"
    )

    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Title", mr_summary["title"])
    table.add_row("State", mr_summary["state"])
    table.add_row("Author", mr_summary["author"]["name"])
    table.add_row("Source Branch", mr_summary["source_branch"])
    table.add_row("Target Branch", mr_summary["target_branch"])
    table.add_row("Commits", str(mr_summary["commit_count"]))

    if mr_summary["labels"]:
        table.add_row("Labels", ", ".join(mr_summary["labels"]))

    if mr_summary["has_conflicts"]:
        table.add_row("Conflicts", ":cross_mark: Has conflicts")

    if mr_summary["work_in_progress"]:
        table.add_row("Status", ":construction: Work in Progress")

    return table


@app.command()
def fetch(
    mr_identifier: Annotated[str, typer.Argument(help="MR ID, URL, or !ID (e.g., '123', '!123', or full GitLab URL)")],
    output_file: Annotated[
        Path, typer.Option("--output", "-o", help="Output file for JSON data", file_okay=True, dir_okay=False)
    ] = Path("mr_data.json"),
    include_diff: Annotated[
        bool, typer.Option("--include-diff/--no-diff", help="Include unified diff in output")
    ] = True,
) -> None:
    """Fetch GitLab merge request metadata and changes.

    This command fetches comprehensive MR data including metadata, commits,
    and optionally the full diff, outputting structured JSON for analysis.
    """
    try:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            # Extract MR ID
            task = progress.add_task("Parsing MR identifier...", total=None)
            mr_id = extract_mr_id(mr_identifier)
            progress.update(task, description=f":white_check_mark: MR ID: {mr_id}")

            # Fetch MR metadata
            progress.update(task, description="Fetching MR metadata...")
            mr_data = fetch_mr_metadata(mr_id)
            progress.update(task, description=":white_check_mark: Metadata fetched")

            # Fetch commits
            progress.update(task, description="Fetching commit list...")
            commits = fetch_mr_commits(mr_id)
            progress.update(task, description=f":white_check_mark: Fetched {len(commits)} commits")

            # Create summary
            progress.update(task, description="Creating summary...")
            mr_summary = create_mr_summary(mr_data, commits)
            progress.update(task, description=":white_check_mark: Summary created")

            # Fetch diff if requested
            if include_diff:
                progress.update(task, description="Fetching unified diff...")
                diff = fetch_mr_changes(mr_id)
                mr_summary["diff"] = diff
                progress.update(task, description=":white_check_mark: Diff fetched")

            # Write output
            progress.update(task, description="Writing output file...")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(mr_summary, indent=2, ensure_ascii=False) + "\n")
            progress.update(task, description=":white_check_mark: Output written")

            progress.remove_task(task)

        # Display summary
        console.print()
        console.print(
            Panel.fit(
                f"MR data written to [cyan]{output_file.absolute()}[/cyan]",
                title=":white_check_mark: Success",
                border_style="green",
            )
        )
        console.print()

        summary_table = create_summary_table(mr_summary)
        console.print(summary_table)

        # Show description preview if present
        if mr_summary["description"]:
            description_preview = mr_summary["description"][:_DESCRIPTION_PREVIEW_MAX_LENGTH]
            if len(mr_summary["description"]) > _DESCRIPTION_PREVIEW_MAX_LENGTH:
                description_preview += "..."

            console.print()
            console.print(Panel(description_preview, title=":page_facing_up: Description Preview", border_style="blue"))

    except GitLabFetchError as e:
        console.print(Panel.fit(f"[red]{e}[/red]", title=":cross_mark: Error", border_style="red"))
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130) from None


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
