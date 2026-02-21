#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0"]
# ///
"""Publish a daily GitHub release from a pre-rendered markdown file.

Handles git tag creation/movement, pushing, and GitHub release creation or
update. Designed to be called after analyze_git_changes + AI analysis +
format_mr_description have produced the release notes markdown.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(
    name="publish_daily_release",
    help="Publish a daily GitHub release from a pre-rendered markdown file",
    add_completion=False,
)
console = Console()


class PublishError(Exception):
    """Error during release publishing."""


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git command."""
    try:
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )
    except subprocess.CalledProcessError as e:
        msg = f"Git command failed: {' '.join(args)}\n{e.stderr}"
        raise PublishError(msg) from e


def run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command."""
    try:
        return subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )
    except subprocess.CalledProcessError as e:
        msg = f"gh command failed: {' '.join(args)}\n{e.stderr}"
        raise PublishError(msg) from e


def tag_exists(tag: str) -> bool:
    """Check if a git tag exists locally or on remote."""
    result = run_git(["rev-parse", "--verify", f"refs/tags/{tag}"], check=False)
    return result.returncode == 0


def gh_release_exists(tag: str) -> bool:
    """Check if a GitHub release exists for the given tag."""
    result = run_gh(["release", "view", tag, "--json", "tagName"], check=False)
    return result.returncode == 0


def get_next_revision_tag(base_tag: str) -> str:
    """Get the next available revision tag (e.g., v2026.02.21-r2)."""
    revision = 2
    while tag_exists(f"{base_tag}-r{revision}"):
        revision += 1
    return f"{base_tag}-r{revision}"


@app.command()
def main(
    release_date: Annotated[str, typer.Option("--date", help="Date in YYYY-MM-DD format")],
    tag: Annotated[str, typer.Option(help="Git tag name (e.g., v2026.02.21)")],
    head_ref: Annotated[str, typer.Option(help="Commit hash the tag should point to")],
    notes_file: Annotated[Path, typer.Option(help="Path to rendered markdown release notes")],
    dry_run: Annotated[bool, typer.Option(help="Print what would happen without making changes")] = False,
    keep_existing_tag: Annotated[bool, typer.Option(help="If tag exists, rename it to -r2 instead of moving it")] = True,
) -> None:
    """Publish a daily GitHub release.

    Creates or updates a git tag and GitHub release for the given date.
    If the tag already exists, the old tag is renamed to a revision suffix
    (vYYYY.MM.DD-r2) before the new tag is created at head_ref.
    """
    if not notes_file.exists():
        console.print(f"[red]Notes file not found: {notes_file}[/red]", file=sys.stderr)
        raise typer.Exit(1)

    title = f"Daily Release - {release_date}"
    notes_content = notes_file.read_text(encoding="utf-8")

    if dry_run:
        console.print(f"[dim]DRY RUN - would publish:[/dim]")
        console.print(f"  Tag:   {tag} → {head_ref[:12]}")
        console.print(f"  Title: {title}")
        console.print(f"  Notes: {len(notes_content)} chars from {notes_file}")
        return

    try:
        existing_release = gh_release_exists(tag)

        if tag_exists(tag) and keep_existing_tag:
            old_commit_result = run_git(["rev-list", "-n", "1", tag], check=False)
            old_commit = old_commit_result.stdout.strip() if old_commit_result.returncode == 0 else None

            if old_commit and old_commit != head_ref:
                # Rename existing tag to revision suffix
                revision_tag = get_next_revision_tag(tag)
                console.print(f"Moving existing tag {tag} → {revision_tag}")
                run_git(["tag", revision_tag, tag])
                run_git(["push", "origin", revision_tag])
                run_git(["tag", "-d", tag])
                run_git(["push", "origin", f":refs/tags/{tag}"])

        # Create or move the tag to head_ref
        run_git(["tag", "-f", tag, head_ref])
        run_git(["push", "origin", tag, "--force"])
        console.print(f"[green]Tagged {head_ref[:12]} as {tag}[/green]")

        if existing_release:
            run_gh(["release", "edit", tag, "--title", title, "--notes-file", str(notes_file)])
            console.print(f"[green]Updated release {tag}[/green]")
        else:
            run_gh(["release", "create", tag, "--title", title, "--notes-file", str(notes_file)])
            console.print(f"[green]Created release {tag}[/green]")

    except PublishError as e:
        console.print(f"[red]{e}[/red]", file=sys.stderr)
        raise typer.Exit(1) from e


def entry_point() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    entry_point()
