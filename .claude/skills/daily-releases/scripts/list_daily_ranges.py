#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0"]
# ///
"""List daily commit ranges for the daily releases pipeline.

Outputs a JSON array of days with base_ref/head_ref pairs, suitable for
driving analyze_git_changes.py and publish_daily_release.py.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, date
from typing import Annotated

import typer
from rich.console import Console

EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
REPO = "Jamie-BitFlight/claude_skills"

# Must match GENERATOR_VERSION in publish_daily_release.py.
# Bump both to force regeneration of all existing releases on next run.
GENERATOR_VERSION = "1.0"
_MARKER_RE = re.compile(r"<!-- created-by-release-generator: v([\d.]+) -->")

app = typer.Typer(
    name="list_daily_ranges",
    help="List daily commit ranges for release pipeline processing",
    add_completion=False,
)
console = Console()


class ListRangesError(Exception):
    """Error listing daily ranges."""


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
        raise ListRangesError(msg) from e


def run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a gh command against the configured repo."""
    try:
        return subprocess.run(
            ["gh", *args, "-R", REPO],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )
    except subprocess.CalledProcessError as e:
        msg = f"gh command failed: {' '.join(args)}\n{e.stderr}"
        raise ListRangesError(msg) from e


def get_release_generator_version(tag: str) -> str | None:
    """Return the generator version embedded in an existing release body, or None.

    Returns None if the release does not exist, the body is missing, or the
    marker comment is not present.
    """
    result = run_gh(["release", "view", tag, "--json", "body"], check=False)
    if result.returncode != 0:
        return None
    try:
        body = json.loads(result.stdout).get("body", "")
    except (json.JSONDecodeError, AttributeError):
        return None
    match = _MARKER_RE.search(body)
    return match.group(1) if match else None


def get_parent(commit_hash: str) -> str:
    """Get parent commit hash, or empty-tree SHA for root commits."""
    result = run_git(["rev-list", "--parents", "-n", "1", commit_hash], check=False)
    if result.returncode != 0:
        return EMPTY_TREE_SHA
    parts = result.stdout.strip().split()
    # parts[0] = commit, parts[1] = parent (if exists)
    if len(parts) < 2:
        return EMPTY_TREE_SHA
    return parts[1]


def tag_exists(tag: str) -> bool:
    """Check if a git tag exists locally."""
    result = run_git(["rev-parse", "--verify", f"refs/tags/{tag}"], check=False)
    return result.returncode == 0


def get_tag_commit(tag: str) -> str | None:
    """Get the commit hash a tag points to (dereferenced to commit)."""
    result = run_git(["rev-list", "-n", "1", tag], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_commits_by_day(branch: str) -> dict[str, list[str]]:
    """Get commits grouped by UTC date, oldest-first within each day.

    Returns dict mapping YYYY-MM-DD to [oldest_hash, ..., newest_hash].
    """
    fmt = "%H %cd"
    result = run_git(
        ["log", branch, f"--format={fmt}", "--date=format:%Y-%m-%d", "--no-merges"],
        check=True,
    )

    # git log is reverse-chronological; collect then reverse per-day
    days: dict[str, list[str]] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        commit_hash, day = line.split(" ", 1)
        days.setdefault(day, []).append(commit_hash)

    # Each day's list is newest-first from git log; reverse to oldest-first
    return {day: list(reversed(commits)) for day, commits in days.items()}


@dataclass
class DayRange:
    """Commit range data for a single calendar day."""

    date: str
    tag: str
    base_ref: str
    head_ref: str
    commit_count: int
    release_exists: bool
    needs_update: bool


@app.command()
def main(
    branch: Annotated[str, typer.Option(help="Git branch to read commits from")] = "origin/main",
    start_date: Annotated[str | None, typer.Option(help="Only process days on or after YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, typer.Option(help="Only process days on or before YYYY-MM-DD")] = None,
    include_existing: Annotated[bool, typer.Option(help="Include days that already have up-to-date releases")] = False,
) -> None:
    """List daily commit ranges for release processing.

    Outputs JSON array to stdout. Each entry includes base_ref and head_ref
    for use with analyze_git_changes.py, plus release status flags.
    """
    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else date.today()
    except ValueError as e:
        console.print(f"[red]Invalid date: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1) from e

    try:
        commits_by_day = get_commits_by_day(branch)
    except ListRangesError as e:
        console.print(f"[red]{e}[/red]", file=sys.stderr)
        raise typer.Exit(1) from e

    results: list[dict] = []

    for day_str in sorted(commits_by_day):
        try:
            day = date.fromisoformat(day_str)
        except ValueError:
            continue

        if start and day < start:
            continue
        if day > end:
            continue

        commits = commits_by_day[day_str]
        oldest_commit = commits[0]
        newest_commit = commits[-1]

        base_ref = get_parent(oldest_commit)
        tag = f"v{day_str.replace('-', '.')}"
        exists = tag_exists(tag)
        current_tag_commit = get_tag_commit(tag) if exists else None
        commit_changed = exists and current_tag_commit != newest_commit
        # Only fetch the release body when the tag exists and commits haven't
        # changed — if commits changed we're already updating.
        if exists and not commit_changed:
            release_version = get_release_generator_version(tag)
            version_outdated = release_version != GENERATOR_VERSION
        else:
            version_outdated = False
        needs_update = exists and (commit_changed or version_outdated)

        entry = DayRange(
            date=day_str,
            tag=tag,
            base_ref=base_ref,
            head_ref=newest_commit,
            commit_count=len(commits),
            release_exists=exists,
            needs_update=needs_update,
        )

        if include_existing or not exists or needs_update:
            results.append(asdict(entry))

    print(json.dumps(results, indent=2))


def entry_point() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    entry_point()
