#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.21.0",
#   "GitPython>=3.1.45",
#   "PyGithub>=2.1.1",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""List daily commit ranges for the daily releases pipeline.

Outputs a JSON array of days with base_ref/head_ref pairs, suitable for
driving analyze_git_changes.py and publish_daily_release.py.

Uses GitPython and PyGithub — no subprocess / shell-out to git or gh.
"""

from __future__ import annotations

import json

from dotenv import load_dotenv

load_dotenv()
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from git import Repo
from git.exc import BadName, InvalidGitRepositoryError, NoSuchPathError
from github import Auth, Github, GithubException
from rich.console import Console

if TYPE_CHECKING:
    from github.Repository import Repository

EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_REPO = "Jamie-BitFlight/claude_skills"
_MIN_PARENT_PARTS = 2

# Must match GENERATOR_VERSION in publish_daily_release.py.
# Bump both to force regeneration of all existing releases on next run.
GENERATOR_VERSION = "1.0"
_MARKER_RE = re.compile(r"<!-- created-by-release-generator: v([\d.]+) -->")

app = typer.Typer(
    name="list_daily_ranges", help="List daily commit ranges for release pipeline processing", add_completion=False
)
console = Console()
err_console = Console(stderr=True)


class AppExit(typer.Exit):
    """Exit with user-friendly error message to stderr."""

    def __init__(self, code: int = 1, message: str | None = None) -> None:
        """Print message to stderr and exit with code."""
        if message is not None:
            err_console.print(f"[red]{message}[/red]")
        super().__init__(code=code)


def get_git_repo() -> Repo:
    """Return GitPython Repo for the current directory.

    Raises:
        AppExit: If not a git repository.
    """
    try:
        return Repo(Path.cwd(), search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        raise AppExit(code=1, message=f"Not a git repository: {e}") from e


def get_github_repo(gh: Github, repo_slug: str) -> Repository:
    """Return PyGithub Repository object.

    Raises:
        AppExit: If repo cannot be accessed.
    """
    try:
        return gh.get_repo(repo_slug)
    except GithubException as e:
        raise AppExit(code=1, message=f"Cannot access repo '{repo_slug}': {e}") from e


def get_release_generator_version(gh_repo: Repository, tag: str) -> str | None:
    """Return the generator version embedded in an existing release body, or None.

    Returns None if the release does not exist, the body is missing, or the
    marker comment is not present.
    """
    try:
        release = gh_repo.get_release(tag)
    except GithubException:
        return None
    body = release.body or ""
    match = _MARKER_RE.search(body)
    return match.group(1) if match else None


def tag_exists(repo: Repo, tag: str) -> bool:
    """Check if a git tag exists locally.

    Returns:
        True if tag exists, False otherwise.
    """
    try:
        repo.rev_parse(f"refs/tags/{tag}")
    except BadName:
        return False
    else:
        return True


def get_tag_commit(repo: Repo, tag: str) -> str | None:
    """Get the commit hash a tag points to (dereferenced to commit).

    Returns:
        Commit hexsha, or None if tag does not exist.
    """
    try:
        return repo.rev_parse(tag).hexsha
    except BadName:
        return None


def get_all_commits_by_day(repo: Repo, branch: str) -> dict[str, list[str]]:
    """Get ALL commits (including merges) grouped by UTC date, oldest-first.

    All returned commits are reachable from ``branch``, so they are
    guaranteed to exist locally and have a common ancestor with any other
    commit on the same branch.

    Returns:
        Dict mapping YYYY-MM-DD to [oldest_hash, ..., newest_hash].
    """
    days: dict[str, list[str]] = {}
    for commit in repo.iter_commits(branch):
        day = commit.committed_datetime.astimezone(UTC).strftime("%Y-%m-%d")
        days.setdefault(day, []).append(commit.hexsha)

    # iter_commits is newest-first; reverse each day to oldest-first
    return {day: list(reversed(commits)) for day, commits in days.items()}


def get_non_merge_commits_by_day(repo: Repo, branch: str) -> dict[str, list[str]]:
    """Get non-merge commits grouped by UTC date, oldest-first.

    Returns:
        Dict mapping YYYY-MM-DD to [oldest_hash, ..., newest_hash].
    """
    days: dict[str, list[str]] = {}
    for commit in repo.iter_commits(branch, no_merges=True):
        day = commit.committed_datetime.astimezone(UTC).strftime("%Y-%m-%d")
        days.setdefault(day, []).append(commit.hexsha)

    # iter_commits is newest-first; reverse each day to oldest-first
    return {day: list(reversed(commits)) for day, commits in days.items()}


def get_day_base_ref(all_commits_by_day: dict[str, list[str]], day_str: str) -> str:
    """Return the last commit on main strictly before ``day_str``.

    Iterates sorted day keys and returns the last commit SHA of the most
    recent day that precedes ``day_str``. All candidates come from the
    branch timeline, so the returned SHA is guaranteed to be on-branch and
    locally present.

    Returns:
        Commit SHA, or EMPTY_TREE_SHA if no commits precede ``day_str``.
    """
    base_ref = EMPTY_TREE_SHA
    for day in sorted(all_commits_by_day):
        if day >= day_str:
            break
        base_ref = all_commits_by_day[day][-1]  # last commit of that day
    return base_ref


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


def _check_day_release_status(repo: Repo, gh_repo: Repository, tag: str, newest_commit: str) -> tuple[bool, bool]:
    """Return ``(release_exists, needs_update)`` for the given tag and commit.

    Checks whether the tag exists, whether its commit has changed, and whether
    the release was generated by an older version of the generator.
    """
    exists = tag_exists(repo, tag)
    if not exists:
        return False, False
    current_tag_commit = get_tag_commit(repo, tag)
    commit_changed = current_tag_commit != newest_commit
    if commit_changed:
        return True, True
    version_outdated = get_release_generator_version(gh_repo, tag) != GENERATOR_VERSION
    return True, version_outdated


def _build_day_range(
    day_str: str,
    all_by_day: dict[str, list[str]],
    non_merge_by_day: dict[str, list[str]],
    repo: Repo,
    gh_repo: Repository,
) -> DayRange:
    """Build a DayRange entry for a single calendar day.

    Extracted to keep ``main()`` under the local-variable limit (PLR0914).

    Returns:
        Populated DayRange dataclass for ``day_str``.
    """
    non_merge_commits = non_merge_by_day[day_str]
    head_ref = all_by_day.get(day_str, non_merge_commits)[-1]
    tag = f"v{day_str.replace('-', '.')}"
    exists, needs_update = _check_day_release_status(repo, gh_repo, tag, head_ref)
    return DayRange(
        date=day_str,
        tag=tag,
        base_ref=get_day_base_ref(all_by_day, day_str),
        head_ref=head_ref,
        commit_count=len(non_merge_commits),
        release_exists=exists,
        needs_update=needs_update,
    )


@app.command()
def main(
    branch: Annotated[str, typer.Option(help="Git branch to read commits from")] = "origin/main",
    start_date: Annotated[str | None, typer.Option(help="Only process days on or after YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, typer.Option(help="Only process days on or before YYYY-MM-DD")] = None,
    include_existing: Annotated[bool, typer.Option(help="Include days that already have up-to-date releases")] = False,
    repo_slug: Annotated[str, typer.Option("--repo", "-R", help="GitHub repo OWNER/REPO")] = DEFAULT_REPO,
) -> None:
    """List daily commit ranges for release processing.

    Outputs JSON array to stdout. Each entry includes base_ref and head_ref
    for use with analyze_git_changes.py, plus release status flags.
    """
    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else datetime.now(tz=UTC).date()
    except ValueError as e:
        raise AppExit(code=1, message=f"Invalid date: {e}") from e

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise AppExit(code=1, message="GITHUB_TOKEN environment variable not set")

    repo = get_git_repo()
    gh = Github(auth=Auth.Token(token))
    gh_repo = get_github_repo(gh, repo_slug)
    all_by_day = get_all_commits_by_day(repo, branch)
    non_merge_by_day = get_non_merge_commits_by_day(repo, branch)

    results: list[dict] = []

    for day_str in sorted(non_merge_by_day):
        try:
            day = date.fromisoformat(day_str)
        except ValueError:
            continue

        if start and day < start:
            continue
        if day > end:
            continue

        entry = _build_day_range(day_str, all_by_day, non_merge_by_day, repo, gh_repo)

        if include_existing or not entry.release_exists or entry.needs_update:
            results.append(asdict(entry))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    app()
