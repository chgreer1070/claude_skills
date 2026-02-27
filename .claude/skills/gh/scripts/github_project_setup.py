#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.21.0",
#   "PyGithub>=2.1.1",
# ]
# ///
"""GitHub Project Setup — multi-step project management automation.

Orchestrates: label creation, milestone management, project setup, and
backlog item issue import using the PyGithub native library.

Authentication: reads GITHUB_TOKEN from environment.
No subprocess / shell-out to gh CLI.

Usage:
    github_project_setup.py setup    --repo OWNER/REPO [--project-title TITLE]
    github_project_setup.py labels   --repo OWNER/REPO [--force]
    github_project_setup.py milestone create --repo OWNER/REPO --title TITLE [--due YYYY-MM-DD]
    github_project_setup.py milestone list   --repo OWNER/REPO
    github_project_setup.py milestone start  --repo OWNER/REPO --number N [--dry-run]
    github_project_setup.py milestone close  --repo OWNER/REPO --number N [--dry-run]
    github_project_setup.py issue create     --repo OWNER/REPO --title TITLE [options]
    github_project_setup.py issue list       --repo OWNER/REPO [--priority p1] [--state open]
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated

import typer
from github import Auth, Github, GithubException

if TYPE_CHECKING:
    from github.Issue import Issue
    from github.Label import Label
    from github.Repository import Repository

app = typer.Typer(help="GitHub Project management automation via PyGithub")
milestone_app = typer.Typer(help="Milestone operations")
issue_app = typer.Typer(help="Issue operations")
app.add_typer(milestone_app, name="milestone")
app.add_typer(issue_app, name="issue")

DEFAULT_REPO = "Jamie-BitFlight/claude_skills"

# Standard label taxonomy
LABELS: list[dict[str, str]] = [
    # Priority
    {"name": "priority:p0", "color": "D73A4A", "description": "Critical — blocks work or production"},
    {"name": "priority:p1", "color": "E99695", "description": "High — should be done next"},
    {"name": "priority:p2", "color": "F9D0C4", "description": "Medium — do when P0/P1 are clear"},
    {"name": "priority:idea", "color": "BFD4F2", "description": "Unscoped — future consideration"},
    # Type
    {"name": "type:feature", "color": "0E8A16", "description": "New capability or skill"},
    {"name": "type:bug", "color": "B60205", "description": "Something is broken"},
    {"name": "type:refactor", "color": "5319E7", "description": "Internal improvement, no behavior change"},
    {"name": "type:docs", "color": "0075CA", "description": "Documentation only"},
    {"name": "type:chore", "color": "EDEDED", "description": "Maintenance, tooling, CI"},
    # Status
    {"name": "status:in-progress", "color": "1D76DB", "description": "Actively being worked on"},
    {"name": "status:done", "color": "0E8A16", "description": "Work complete, milestone closing"},
    {"name": "status:blocked", "color": "B60205", "description": "Waiting on external dependency"},
    {"name": "status:needs-grooming", "color": "FEF2C0", "description": "Captured but not yet groomed"},
    {"name": "status:needs-review", "color": "D876E3", "description": "Implementation done, needs review"},
]

PRIORITY_LABEL_MAP = {"P0": "priority:p0", "P1": "priority:p1", "P2": "priority:p2", "IDEAS": "priority:idea"}


def get_github() -> Github:
    """Return an authenticated Github client from GITHUB_TOKEN."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        typer.echo("ERROR: GITHUB_TOKEN environment variable not set", err=True)
        raise typer.Exit(1)
    return Github(auth=Auth.Token(token))


def get_repo(gh: Github, repo_slug: str) -> Repository:
    """Return a Repository object, exit on failure.

    Args:
        gh: Authenticated Github client.
        repo_slug: Repository identifier in ``owner/repo`` format.

    Returns:
        Repository object for the given slug.
    """
    try:
        return gh.get_repo(repo_slug)
    except GithubException as exc:
        typer.echo(f"ERROR: Cannot access repo '{repo_slug}': {exc}", err=True)
        raise typer.Exit(1) from exc


@app.command()
def labels(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Create standard label taxonomy. Skips labels that already exist unless --force."""
    gh = get_github()
    repository = get_repo(gh, repo)

    existing = {lbl.name: lbl for lbl in repository.get_labels()}
    created = updated = skipped = 0

    for spec in LABELS:
        name = spec["name"]
        if name in existing:
            if force:
                existing[name].edit(name=name, color=spec["color"], description=spec["description"])
                typer.echo(f"  updated: {name}")
                updated += 1
            else:
                typer.echo(f"  exists:  {name}  (--force to update)")
                skipped += 1
        else:
            repository.create_label(name=name, color=spec["color"], description=spec["description"])
            typer.echo(f"  created: {name}")
            created += 1

    typer.echo(f"\nLabels: {created} created, {updated} updated, {skipped} skipped")


@milestone_app.command("create")
def milestone_create(
    title: Annotated[str, typer.Option("--title")],
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    description: Annotated[str, typer.Option("--description")] = "",
    due: Annotated[str | None, typer.Option("--due", help="Due date YYYY-MM-DD")] = None,
) -> None:
    """Create a milestone."""
    gh = get_github()
    repository = get_repo(gh, repo)

    due_dt = datetime.strptime(due, "%Y-%m-%d").replace(tzinfo=UTC) if due else None
    if due_dt is not None and description:
        milestone = repository.create_milestone(title=title, description=description, due_on=due_dt)
    elif due_dt is not None:
        milestone = repository.create_milestone(title=title, due_on=due_dt)
    elif description:
        milestone = repository.create_milestone(title=title, description=description)
    else:
        milestone = repository.create_milestone(title=title)
    typer.echo(f"Created milestone #{milestone.number}: {milestone.title}")
    typer.echo(f"  URL: {milestone.html_url}")


@milestone_app.command("list")
def milestone_list(repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO) -> None:
    """List all open milestones."""
    gh = get_github()
    repository = get_repo(gh, repo)

    milestones = list(repository.get_milestones(state="all"))
    if not milestones:
        typer.echo("No milestones.")
        return
    for m in milestones:
        due = m.due_on.strftime("%Y-%m-%d") if m.due_on else "no due date"
        typer.echo(
            f"  #{m.number:3d}  [{m.state}]  {m.title}  ({m.open_issues} open, {m.closed_issues} closed)  due: {due}"
        )


@milestone_app.command("start")
def milestone_start(
    number: Annotated[int, typer.Option("--number", "-n", help="Milestone number")],
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Transition open milestone issues from status:needs-grooming to status:in-progress."""
    gh = get_github()
    repository = get_repo(gh, repo)

    try:
        milestone = repository.get_milestone(number)
    except GithubException as exc:
        typer.echo(f"ERROR: Milestone #{number} not found.", err=True)
        open_milestones = list(repository.get_milestones(state="open"))
        if open_milestones:
            typer.echo("Open milestones:", err=True)
            for m in open_milestones:
                typer.echo(f"  #{m.number}  {m.title}", err=True)
        raise typer.Exit(1) from exc

    if milestone.state == "closed":
        typer.echo(f"ERROR: Milestone #{number} '{milestone.title}' is already closed.", err=True)
        raise typer.Exit(1)

    if milestone.open_issues == 0:
        typer.echo(
            f"WARNING: Milestone #{number} '{milestone.title}' has no open issues. "
            "Add items first with /group-items-to-milestone."
        )
        raise typer.Exit(0)

    open_issues = list(repository.get_issues(milestone=milestone, state="open"))
    typer.echo(f"Milestone #{milestone.number}: {milestone.title}")
    typer.echo(f"  {milestone.open_issues} open issue(s) — transitioning labels:\n")

    for issue in open_issues:
        label_names = [lbl.name for lbl in issue.labels]
        typer.echo(f"  #{issue.number:4d}  {issue.title[:60]:<60}  [{', '.join(label_names)}]")

    if dry_run:
        typer.echo("\n[dry-run] No changes made.")
        return

    in_progress_label = _ensure_label(repository, "status:in-progress", "1D76DB", "Actively being worked on")
    succeeded, skipped, failed = _transition_issues(open_issues, in_progress_label)

    typer.echo(
        f"\nMilestone #{milestone.number} '{milestone.title}' started.\n"
        f"  {succeeded} transitioned, {skipped} already in-progress, {failed} failed.\n"
        f"\nWork on individual items:\n"
        f"  /work-backlog-item {{title}}\n"
        f"\nTrack progress:\n"
        f"  uv run .claude/skills/gh/scripts/github_project_setup.py issue list "
        f"--repo {repo}"
    )
    if failed:
        raise typer.Exit(1)


@milestone_app.command("close")
def milestone_close(
    number: Annotated[int, typer.Option("--number", "-n", help="Milestone number")],
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Close a milestone: transition open issues to status:done and close the milestone."""
    gh = get_github()
    repository = get_repo(gh, repo)

    try:
        milestone = repository.get_milestone(number)
    except GithubException as exc:
        typer.echo(f"ERROR: Milestone #{number} not found.", err=True)
        open_milestones = list(repository.get_milestones(state="open"))
        if open_milestones:
            typer.echo("Open milestones:", err=True)
            for m in open_milestones:
                typer.echo(f"  #{m.number}  {m.title}", err=True)
        raise typer.Exit(1) from exc

    if milestone.state == "closed":
        typer.echo(f"ERROR: Milestone #{number} '{milestone.title}' is already closed.", err=True)
        raise typer.Exit(1)

    open_issues = list(repository.get_issues(milestone=milestone, state="open"))
    closed_issues = list(repository.get_issues(milestone=milestone, state="closed"))
    total = len(open_issues) + len(closed_issues)

    typer.echo(f"Milestone #{milestone.number}: {milestone.title}")
    typer.echo(f"  {len(closed_issues)} closed, {len(open_issues)} open\n")

    if open_issues:
        typer.echo("Open issues (will be transitioned to status:done):")
        for issue in open_issues:
            label_names = [lbl.name for lbl in issue.labels]
            typer.echo(f"  #{issue.number:4d}  {issue.title[:60]:<60}  [{', '.join(label_names)}]")
        typer.echo()

    if dry_run:
        typer.echo("[dry-run] No changes made.")
        return

    succeeded = skipped = failed = 0
    if open_issues:
        done_label = _ensure_label(repository, "status:done", "0E8A16", "Work complete, milestone closing")
        succeeded, skipped, failed = _transition_to_done(open_issues, done_label)

    # Close the milestone
    milestone.edit(title=milestone.title, state="closed")
    typer.echo(f"\nMilestone #{milestone.number} '{milestone.title}' closed.")
    if open_issues:
        typer.echo(f"  {succeeded} transitioned to status:done, {skipped} already done, {failed} failed.")
    typer.echo(f"  {len(closed_issues)}/{total} issues were closed before milestone close.")
    if failed:
        raise typer.Exit(1)


def _transition_to_done(open_issues: list[Issue], done_label: Label) -> tuple[int, int, int]:
    """Apply status:done label to each open issue.

    Returns:
        Tuple of (succeeded, skipped, failed) counts.
    """
    status_labels_to_remove = {"status:in-progress", "status:needs-grooming"}
    succeeded = failed = skipped = 0
    typer.echo()
    for issue in open_issues:
        label_names = [lbl.name for lbl in issue.labels]
        if "status:done" in label_names:
            typer.echo(f"  #{issue.number}  already has status:done — skipped")
            skipped += 1
            continue
        try:
            new_label_names = [lbl.name for lbl in issue.labels if lbl.name not in status_labels_to_remove]
            new_label_names.append(done_label.name)
            issue.edit(labels=new_label_names)
            typer.echo(f"  #{issue.number}  {issue.title[:60]}  → status:done")
            succeeded += 1
        except GithubException as exc:
            typer.echo(f"  #{issue.number}  FAILED: {exc}", err=True)
            failed += 1
    return succeeded, skipped, failed


def _ensure_label(repository: Repository, name: str, color: str, description: str) -> Label:
    """Return the label, creating it if it does not exist.

    Args:
        repository: GitHub repository object.
        name: Label name to find or create.
        color: Hex color code for the label (without ``#`` prefix).
        description: Human-readable label description.

    Returns:
        The existing or newly created Label object.
    """
    try:
        return repository.get_label(name)
    except GithubException:
        label = repository.create_label(name=name, color=color, description=description)
        typer.echo(f"\n  Created label: {name}")
        return label


def _transition_issues(open_issues: list[Issue], in_progress_label: Label) -> tuple[int, int, int]:
    """Apply label transition from ``status:needs-grooming`` to ``status:in-progress``.

    Args:
        open_issues: List of open Issue objects to transition.
        in_progress_label: The ``status:in-progress`` Label to apply.

    Returns:
        Tuple of (succeeded, skipped, failed) counts.
    """
    succeeded = failed = skipped = 0
    typer.echo()
    for issue in open_issues:
        label_names = [lbl.name for lbl in issue.labels]
        if "status:in-progress" in label_names:
            typer.echo(f"  #{issue.number}  already has status:in-progress — skipped")
            skipped += 1
            continue
        try:
            new_label_names = [lbl.name for lbl in issue.labels if lbl.name != "status:needs-grooming"]
            new_label_names.append(in_progress_label.name)
            issue.edit(labels=new_label_names)
            typer.echo(f"  #{issue.number}  {issue.title[:60]}  → status:in-progress")
            succeeded += 1
        except GithubException as exc:
            typer.echo(f"  #{issue.number}  FAILED: {exc}", err=True)
            failed += 1
    return succeeded, skipped, failed


@issue_app.command("create")
def issue_create(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    title: Annotated[str, typer.Option("--title")] = "",
    body: Annotated[str, typer.Option("--body")] = "",
    priority_label: Annotated[str, typer.Option("--priority-label")] = "",
    type_label: Annotated[str, typer.Option("--type-label")] = "",
    milestone_number: Annotated[int, typer.Option("--milestone")] = 0,
) -> None:
    """Create a GitHub issue with priority/type labels and optional milestone."""
    if not title:
        typer.echo("ERROR: --title is required", err=True)
        raise typer.Exit(1)

    gh = get_github()
    repository = get_repo(gh, repo)

    label_names = ["status:needs-grooming"]
    if priority_label:
        label_names.append(priority_label)
    if type_label:
        label_names.append(type_label)

    label_objects = []
    for lbl_name in label_names:
        try:
            label_objects.append(repository.get_label(lbl_name))
        except GithubException:
            typer.echo(f"  WARNING: label '{lbl_name}' not found — skipping", err=True)

    milestone_obj = None
    if milestone_number:
        try:
            milestone_obj = repository.get_milestone(milestone_number)
        except GithubException:
            typer.echo(f"  WARNING: milestone #{milestone_number} not found — skipping", err=True)

    if milestone_obj is not None:
        issue = repository.create_issue(title=title, body=body or "", labels=label_objects, milestone=milestone_obj)
    else:
        issue = repository.create_issue(title=title, body=body or "", labels=label_objects)
    typer.echo(f"Created issue #{issue.number}: {issue.title}")
    typer.echo(f"  URL: {issue.html_url}")


@issue_app.command("list")
def issue_list(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    priority: Annotated[str, typer.Option("--priority")] = "",
    state: Annotated[str, typer.Option("--state")] = "open",
) -> None:
    """List issues, optionally filtered by priority."""
    gh = get_github()
    repository = get_repo(gh, repo)

    kwargs: dict = {"state": state}
    if priority:
        label_name = PRIORITY_LABEL_MAP.get(priority.upper(), f"priority:{priority.lower()}")
        try:
            kwargs["labels"] = [repository.get_label(label_name)]
        except GithubException:
            typer.echo(f"Label '{label_name}' not found", err=True)

    issues = list(repository.get_issues(**kwargs))
    if not issues:
        typer.echo("No issues found.")
        return
    for issue in issues:
        milestone_title = issue.milestone.title if issue.milestone else "—"
        label_names = ", ".join(lbl.name for lbl in issue.labels)
        typer.echo(f"  #{issue.number:4d}  {issue.title[:55]:<55}  [{label_names}]  {milestone_title}")


@app.command()
def setup(
    repo: Annotated[str, typer.Option("--repo", "-R")] = DEFAULT_REPO,
    project_title: Annotated[str, typer.Option("--project-title")] = "claude_skills Backlog",
) -> None:
    """Full project setup: create label taxonomy and report next steps."""
    typer.echo(f"Setting up GitHub project for {repo}...")
    typer.echo("\n1. Creating label taxonomy...")

    gh = get_github()
    repository = get_repo(gh, repo)

    existing = {lbl.name: lbl for lbl in repository.get_labels()}
    created = skipped = 0
    for spec in LABELS:
        if spec["name"] not in existing:
            repository.create_label(name=spec["name"], color=spec["color"], description=spec["description"])
            typer.echo(f"   created: {spec['name']}")
            created += 1
        else:
            skipped += 1

    typer.echo(f"   Labels: {created} created, {skipped} already existed")

    typer.echo(f"\n2. Project '{project_title}' — create via gh CLI:")
    typer.echo(f'   gh project create --owner {repo.split("/")[0]} --title "{project_title}"')
    typer.echo("\nNote: GitHub Projects V2 requires project OAuth scope.")
    typer.echo("      Use gh project commands or the GraphQL API for project creation.")
    typer.echo("      See .claude/skills/gh/references/projects-v2.md for field setup commands.")


if __name__ == "__main__":
    app()
