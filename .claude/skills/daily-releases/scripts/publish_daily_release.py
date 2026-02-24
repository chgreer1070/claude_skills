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
"""Publish a daily GitHub release from a pre-rendered markdown file.

Handles git tag creation/movement, pushing, and GitHub release creation or
update. Designed to be called after analyze_git_changes + AI analysis +
format_mr_description have produced the release notes markdown.

Uses GitPython and PyGithub — no subprocess / shell-out to git or gh.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from git import Repo
from git.exc import BadName, InvalidGitRepositoryError, NoSuchPathError
from github import Auth, Github, GithubException
from rich.console import Console

if TYPE_CHECKING:
    from github.Repository import Repository

app = typer.Typer(
    name="publish_daily_release",
    help="Publish a daily GitHub release from a pre-rendered markdown file",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

DEFAULT_REPO = "Jamie-BitFlight/claude_skills"

# Bump this to force regeneration of all existing releases on next run.
GENERATOR_VERSION = "1.0"
GENERATOR_MARKER = f"<!-- created-by-release-generator: v{GENERATOR_VERSION} -->"


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


def gh_release_exists(gh_repo: Repository, tag: str) -> bool:
    """Check if a GitHub release exists for the given tag.

    Returns:
        True if release exists, False otherwise.
    """
    try:
        gh_repo.get_release(tag)
    except GithubException:
        return False
    else:
        return True


def get_next_revision_tag(repo: Repo, base_tag: str) -> str:
    """Get the next available revision tag (e.g., v2026.02.21-r2).

    Returns:
        Next available revision tag string.
    """
    revision = 2
    while tag_exists(repo, f"{base_tag}-r{revision}"):
        revision += 1
    return f"{base_tag}-r{revision}"


@app.command()
def main(
    release_date: Annotated[str, typer.Option("--date", help="Date in YYYY-MM-DD format")],
    tag: Annotated[str, typer.Option(help="Git tag name (e.g., v2026.02.21)")],
    head_ref: Annotated[str, typer.Option(help="Commit hash the tag should point to")],
    notes_file: Annotated[Path, typer.Option(help="Path to rendered markdown release notes")],
    dry_run: Annotated[bool, typer.Option(help="Print what would happen without making changes")] = False,
    keep_existing_tag: Annotated[
        bool, typer.Option(help="If tag exists, rename it to -r2 instead of moving it")
    ] = True,
    repo_slug: Annotated[str, typer.Option("--repo", "-R", help="GitHub repo OWNER/REPO")] = DEFAULT_REPO,
) -> None:
    """Publish a daily GitHub release.

    Creates or updates a git tag and GitHub release for the given date.
    If the tag already exists, the old tag is renamed to a revision suffix
    (vYYYY.MM.DD-r2) before the new tag is created at head_ref.
    """
    if not notes_file.exists():
        raise AppExit(code=1, message=f"Notes file not found: {notes_file}")

    title = f"Daily Release - {release_date}"
    notes_content = notes_file.read_text(encoding="utf-8").rstrip() + f"\n\n{GENERATOR_MARKER}\n"

    if dry_run:
        console.print("[dim]DRY RUN - would publish:[/dim]")
        console.print(f"  Tag:   {tag} -> {head_ref[:12]}")
        console.print(f"  Title: {title}")
        console.print(f"  Notes: {len(notes_content)} chars from {notes_file}")
        return

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise AppExit(code=1, message="GITHUB_TOKEN environment variable not set")

    git_repo = get_git_repo()
    gh = Github(auth=Auth.Token(token))
    gh_repo = get_github_repo(gh, repo_slug)
    existing_release = gh_release_exists(gh_repo, tag)
    deleted_release_in_rename = False

    if tag_exists(git_repo, tag) and keep_existing_tag:
        old_tag_ref = git_repo.tags[tag]
        old_commit = old_tag_ref.commit.hexsha

        if old_commit != head_ref:
            # Delete release before deleting tag — otherwise the release becomes
            # orphaned (draft) and we'd create a duplicate when we recreate the tag.
            if existing_release:
                release = gh_repo.get_release(tag)
                release.delete_release()
                deleted_release_in_rename = True
                console.print(f"Deleted release for {tag} (will recreate after tag move)")

            # Rename existing tag to revision suffix
            revision_tag = get_next_revision_tag(git_repo, tag)
            console.print(f"Moving existing tag {tag} -> {revision_tag}")
            git_repo.create_tag(revision_tag, ref=tag)
            git_repo.remotes.origin.push(revision_tag)
            git_repo.delete_tag(old_tag_ref)
            git_repo.remotes.origin.push(refspec=f":refs/tags/{tag}")

    # Create or move the tag to head_ref
    git_repo.create_tag(tag, ref=head_ref, force=True)
    git_repo.remotes.origin.push(tag, force=True)
    console.print(f"[green]Tagged {head_ref[:12]} as {tag}[/green]")

    if existing_release and not deleted_release_in_rename:
        release = gh_repo.get_release(tag)
        release.update_release(name=title, message=notes_content)
        console.print(f"[green]Updated release {tag}[/green]")
    else:
        gh_repo.create_git_release(tag=tag, name=title, message=notes_content, draft=False)
        console.print(f"[green]Created release {tag}[/green]")


if __name__ == "__main__":
    app()
