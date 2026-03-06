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
"""Collect per-day dataset for the daily-releases chunked pipeline.

Extracts per-file diffs, commit metadata, and GitHub issues referenced in
commits for a given base_ref..head_ref range, writing structured JSON and
diff files into ``<output_dir>/dataset/``.

Uses GitPython and PyGithub — no subprocess / shell-out to git or gh.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from dotenv import load_dotenv

load_dotenv()

import os

import typer
from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from github import Auth, Github, GithubException
from rich.console import Console

if TYPE_CHECKING:
    from git.diff import Diff
    from git.objects.commit import Commit
    from github.Repository import Repository

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_REPO: str = os.environ.get("DEFAULT_REPO") or "Jamie-BitFlight/claude_skills"
EMPTY_TREE_SHA: str = os.environ.get("EMPTY_TREE_SHA") or "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

#: Source file extensions to include in the dataset.
SOURCE_EXTENSIONS: frozenset[str] = frozenset({
    ".py",
    ".js",
    ".cjs",
    ".mjs",
    ".ts",
    ".tsx",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
})

#: Path prefixes whose files are excluded from diff output (is_excluded=true).
EXCLUDED_PREFIXES: tuple[str, ...] = (
    "dist/",
    "build/",
    ".cache/",
    "node_modules/",
    "vendor/",
    "third_party/",
    ".venv/",
    "__pycache__/",
)

#: Regex matching "closes/fixes/resolves #N" in commit messages (case-insensitive).
_ISSUE_REF_RE: re.Pattern[str] = re.compile(r"(?:closes|fixes|resolves)\s+#(\d+)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Typer app
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="collect_day_dataset",
    help="Collect per-file diffs, commit metadata, and GitHub issues into dataset/.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# AppExit helper
# ---------------------------------------------------------------------------


class AppExit(typer.Exit):
    """Exit with a user-friendly error message printed to stderr."""

    exit_code: int

    def __init__(self, code: int = 1, message: str | None = None) -> None:
        """Initialise exit with optional message.

        Args:
            code: Process exit code (default 1).
            message: Human-readable error message printed to stderr in red.
        """
        if message is not None:
            err_console.print(f"[red]{message}[/red]")
        self.exit_code = code
        super().__init__(code=code)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class FileRecord:
    """Metadata for a single changed source file.

    Attributes:
        path: Repository-relative file path (uses b_path for additions/modifications).
        status: Single-letter git status: A (added), M (modified), D (deleted), R (renamed).
        lines_added: Number of lines added in this file's diff.
        lines_deleted: Number of lines removed in this file's diff.
        is_source: True when the file extension is in SOURCE_EXTENSIONS.
        is_excluded: True when the file path starts with an excluded prefix.
        diff_file: Relative path inside the dataset directory where the diff is stored,
            or empty string when no diff was written.
    """

    path: str
    status: str
    lines_added: int
    lines_deleted: int
    is_source: bool
    is_excluded: bool
    diff_file: str


@dataclass
class CommitRecord:
    """Metadata for a single commit.

    Attributes:
        sha: Full 40-character commit SHA.
        subject: First line of the commit message.
        body: Remainder of the commit message after the subject line.
        author: Author name and e-mail formatted as ``Name <email>``.
        date: ISO 8601 UTC timestamp.
        files_touched: Sorted list of repository-relative paths changed by this commit.
    """

    sha: str
    subject: str
    body: str
    author: str
    date: str
    files_touched: list[str]


@dataclass
class IssueRecord:
    """Minimal GitHub issue/PR record.

    Attributes:
        number: GitHub issue number.
        title: Issue title.
        state: ``open`` or ``closed``.
        url: HTML URL of the issue.
    """

    number: int
    title: str
    state: str
    url: str


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def get_git_repo() -> Repo:
    """Return a GitPython Repo for the current working directory.

    Raises:
        AppExit: When the current directory is not inside a git repository.
    """
    try:
        return Repo(Path.cwd(), search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as exc:
        raise AppExit(code=1, message=f"Not a git repository: {exc}") from exc


def _sanitize_path(file_path: str) -> str:
    """Sanitize a repository file path for use as a diff filename.

    Replaces ``/`` with ``_`` and keeps other characters unchanged.
    Example: ``src/module/file.py`` becomes ``src_module_file.py``.

    Args:
        file_path: Repository-relative path to the file.

    Returns:
        Sanitized filename suitable for use inside the ``diffs/`` directory.
    """
    return file_path.replace("/", "_")


def _diff_status(diff_item: Diff) -> str:
    """Extract a single-letter status from a GitPython DiffItem.

    Args:
        diff_item: A single entry from a ``repo.commit().diff()`` result.

    Returns:
        ``A`` (new file), ``D`` (deleted), ``R`` (renamed), or ``M`` (modified).
    """
    if diff_item.new_file:
        return "A"
    if diff_item.deleted_file:
        return "D"
    if diff_item.renamed_file:
        return "R"
    return "M"


def _count_diff_lines(raw_diff: bytes) -> tuple[int, int]:
    """Count added and deleted lines in a unified diff.

    Args:
        raw_diff: Raw unified diff bytes from GitPython.

    Returns:
        Tuple of ``(lines_added, lines_deleted)``.
    """
    added = 0
    deleted = 0
    for line in raw_diff.splitlines():
        decoded = line.decode("utf-8", errors="replace")
        if decoded.startswith("+") and not decoded.startswith("+++"):
            added += 1
        elif decoded.startswith("-") and not decoded.startswith("---"):
            deleted += 1
    return added, deleted


def _write_diff_file(diffs_dir: Path, file_path: str, raw_diff: bytes) -> str:
    """Write a raw diff to the diffs directory and return the relative path.

    Args:
        diffs_dir: Directory where individual diff files are stored.
        file_path: Repository-relative file path (used to derive the filename).
        raw_diff: Raw unified diff bytes to write.

    Returns:
        Relative path string of the form ``dataset/diffs/<name>.diff``.
    """
    diff_filename = f"{_sanitize_path(file_path)}.diff"
    (diffs_dir / diff_filename).write_bytes(raw_diff)
    return f"dataset/diffs/{diff_filename}"


def _build_file_record(item: Diff, diffs_dir: Path) -> FileRecord | None:
    """Build a FileRecord for a single DiffItem, or return None to skip it.

    Skips items whose path cannot be resolved or whose extension is not in
    SOURCE_EXTENSIONS.

    Args:
        item: A single entry from a GitPython diff index.
        diffs_dir: Directory where per-file diffs are written.

    Returns:
        Populated FileRecord, or None if the item should be skipped.
    """
    raw_path: str | None = item.b_path or item.a_path
    if raw_path is None:
        return None
    if Path(raw_path).suffix.lower() not in SOURCE_EXTENSIONS:
        return None

    raw_diff: bytes = item.diff if isinstance(item.diff, bytes) else b""
    lines_added, lines_deleted = _count_diff_lines(raw_diff)
    is_excluded = any(raw_path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)
    diff_file_rel = "" if is_excluded else _write_diff_file(diffs_dir, raw_path, raw_diff)

    return FileRecord(
        path=raw_path,
        status=_diff_status(item),
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        is_source=True,
        is_excluded=is_excluded,
        diff_file=diff_file_rel,
    )


def collect_file_records(repo: Repo, base_ref: str, head_ref: str, diffs_dir: Path) -> list[FileRecord]:
    """Extract per-file diff records for the given commit range.

    Iterates ``repo.commit(base_ref).diff(repo.commit(head_ref))``, writes
    per-file ``.diff`` files for non-excluded source files, and returns a
    list of FileRecord instances.

    Args:
        repo: Initialised GitPython Repo.
        base_ref: Git commit SHA for the start of the range (exclusive).
        head_ref: Git commit SHA for the end of the range (inclusive).
        diffs_dir: Directory path where individual diff files are written.

    Returns:
        List of FileRecord instances, one per changed file that matches
        SOURCE_EXTENSIONS.
    """
    err_console.print(f"[dim]Extracting file diffs {base_ref[:8]}..{head_ref[:8]}[/dim]")
    diffs_dir.mkdir(parents=True, exist_ok=True)

    if base_ref == EMPTY_TREE_SHA:
        diff_index = repo.tree(base_ref).diff(repo.commit(head_ref).tree)
    else:
        diff_index = repo.commit(base_ref).diff(repo.commit(head_ref))
    records = [r for item in diff_index if (r := _build_file_record(item, diffs_dir)) is not None]

    err_console.print(f"[dim]  {len(records)} source files processed[/dim]")
    return records


def collect_commit_records(repo: Repo, base_ref: str, head_ref: str) -> list[CommitRecord]:
    """Collect commit metadata for the range base_ref..head_ref.

    Args:
        repo: Initialised GitPython Repo.
        base_ref: Git commit SHA for the start of the range (exclusive).
        head_ref: Git commit SHA for the end of the range (inclusive).

    Returns:
        List of CommitRecord instances ordered oldest-first.
    """
    err_console.print(f"[dim]Collecting commits {base_ref[:8]}..{head_ref[:8]}[/dim]")

    if base_ref == EMPTY_TREE_SHA:
        commits: list[Commit] = list(repo.iter_commits(head_ref))
    else:
        commits: list[Commit] = list(repo.iter_commits(f"{base_ref}..{head_ref}"))
    # iter_commits returns newest-first; reverse to oldest-first
    commits.reverse()

    records: list[CommitRecord] = []
    for commit in commits:
        raw_message = commit.message
        message: str = raw_message if isinstance(raw_message, str) else ""
        lines = message.splitlines()
        subject = lines[0] if lines else ""
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        author_name: str = commit.author.name or ""
        author_email: str = commit.author.email or ""
        author_str = f"{author_name} <{author_email}>"

        date_str = commit.committed_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        files_touched: list[str] = sorted(str(k) for k in commit.stats.files)

        records.append(
            CommitRecord(
                sha=commit.hexsha,
                subject=subject,
                body=body,
                author=author_str,
                date=date_str,
                files_touched=files_touched,
            )
        )

    err_console.print(f"[dim]  {len(records)} commits collected[/dim]")
    return records


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def _make_github_client(token: str) -> Github:
    """Create a Github client respecting proxy/SSL environment variables.

    Reads:
        GITHUB_API_URL: Custom API base URL (default: https://api.github.com).
        GITHUB_SSL_VERIFY: Set to 'false', '0', or 'no' to disable SSL verification.

    Returns:
        Configured Github client instance.
    """
    base_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    verify_ssl_str = os.environ.get("GITHUB_SSL_VERIFY", "true").lower()
    verify: bool = verify_ssl_str not in {"false", "0", "no"}
    return Github(auth=Auth.Token(token), base_url=base_url, verify=verify)


def get_github_repo(gh: Github, repo_slug: str) -> Repository:
    """Return a PyGithub Repository object.

    Args:
        gh: Authenticated Github client.
        repo_slug: Repository slug in ``OWNER/REPO`` format.

    Returns:
        PyGithub Repository instance.

    Raises:
        AppExit: When the repository cannot be accessed.
    """
    try:
        return gh.get_repo(repo_slug)
    except GithubException as exc:
        raise AppExit(code=1, message=f"Cannot access repo '{repo_slug}': {exc}") from exc


def _extract_issue_numbers(commit_records: list[CommitRecord]) -> list[int]:
    """Extract unique GitHub issue numbers referenced in commit messages.

    Scans subject and body of each commit for patterns matching
    ``closes/fixes/resolves #N`` (case-insensitive) and returns a deduplicated
    sorted list of issue numbers.

    Args:
        commit_records: List of CommitRecord instances to scan.

    Returns:
        Sorted list of unique referenced issue numbers.
    """
    seen: set[int] = set()
    for record in commit_records:
        text = f"{record.subject}\n{record.body}"
        seen.update(int(match.group(1)) for match in _ISSUE_REF_RE.finditer(text))
    return sorted(seen)


def collect_issue_records(commit_records: list[CommitRecord], repo_slug: str) -> list[IssueRecord]:
    """Fetch GitHub issues/PRs referenced in commit messages.

    If ``GITHUB_TOKEN`` is not set, prints a warning to stderr and returns an
    empty list rather than failing.

    Args:
        commit_records: Commits to scan for issue references.
        repo_slug: GitHub ``OWNER/REPO`` slug used to fetch issues.

    Returns:
        List of IssueRecord instances for each referenced issue number.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        err_console.print("[yellow]Warning: GITHUB_TOKEN not set — skipping GitHub issue fetch[/yellow]")
        return []

    issue_numbers = _extract_issue_numbers(commit_records)
    if not issue_numbers:
        err_console.print("[dim]No issue references found in commits[/dim]")
        return []

    err_console.print(f"[dim]Fetching {len(issue_numbers)} referenced GitHub issues[/dim]")
    gh = _make_github_client(token)
    gh_repo = get_github_repo(gh, repo_slug)

    records: list[IssueRecord] = []
    for number in issue_numbers:
        try:
            issue = gh_repo.get_issue(number)
            records.append(IssueRecord(number=issue.number, title=issue.title, state=issue.state, url=issue.html_url))
        except GithubException as exc:
            err_console.print(f"[yellow]Warning: could not fetch issue #{number}: {exc}[/yellow]")

    err_console.print(f"[dim]  {len(records)} issues fetched[/dim]")
    return records


# ---------------------------------------------------------------------------
# Dataset writer
# ---------------------------------------------------------------------------


def write_dataset(
    output_dir: Path,
    file_records: list[FileRecord],
    commit_records: list[CommitRecord],
    issue_records: list[IssueRecord],
) -> None:
    """Write the dataset JSON files to ``<output_dir>/dataset/``.

    Creates the directory if it does not exist, then writes:
    - ``files.json``
    - ``commits.json``
    - ``issues.json``

    The ``diffs/`` subdirectory is created earlier by ``collect_file_records``.

    Args:
        output_dir: Root output directory (e.g. ``./daily-releases/2026-02-10/``).
        file_records: Per-file metadata records.
        commit_records: Commit metadata records.
        issue_records: GitHub issue records (may be empty).
    """
    dataset_dir = output_dir / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    files_payload = [
        {
            "path": r.path,
            "status": r.status,
            "lines_added": r.lines_added,
            "lines_deleted": r.lines_deleted,
            "is_source": r.is_source,
            "is_excluded": r.is_excluded,
            "diff_file": r.diff_file,
        }
        for r in file_records
    ]

    commits_payload = [
        {
            "sha": r.sha,
            "subject": r.subject,
            "body": r.body,
            "author": r.author,
            "date": r.date,
            "files_touched": r.files_touched,
        }
        for r in commit_records
    ]

    issues_payload = [{"number": r.number, "title": r.title, "state": r.state, "url": r.url} for r in issue_records]

    (dataset_dir / "files.json").write_text(json.dumps(files_payload, indent=2), encoding="utf-8")
    (dataset_dir / "commits.json").write_text(json.dumps(commits_payload, indent=2), encoding="utf-8")
    (dataset_dir / "issues.json").write_text(json.dumps(issues_payload, indent=2), encoding="utf-8")

    err_console.print(
        f"[dim]Dataset written to {dataset_dir}: "
        f"{len(file_records)} files, {len(commit_records)} commits, "
        f"{len(issue_records)} issues[/dim]"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    base_ref: Annotated[str, typer.Argument(help="Git commit SHA before the day's first commit")],
    head_ref: Annotated[str, typer.Argument(help="Git commit SHA of the day's last commit")],
    output_dir: Annotated[
        Path, typer.Argument(help="Directory under which dataset/ subdirectory will be created", writable=True)
    ],
    repo_slug: Annotated[
        str, typer.Option("--repo", "-R", help="GitHub OWNER/REPO slug (default from DEFAULT_REPO env var)")
    ] = DEFAULT_REPO,
) -> None:
    """Collect per-file diffs, commit metadata, and GitHub issues into dataset/.

    Writes three JSON files and per-file diffs under ``<output_dir>/dataset/``:

    - ``files.json``: changed source files with diff stats and diff_file path
    - ``commits.json``: commit metadata for the base_ref..head_ref range
    - ``issues.json``: GitHub issues referenced via closes/fixes/resolves #N

    Progress summaries are printed to stderr; no output is written to stdout.
    """
    err_console.print(f"[bold]collect_day_dataset[/bold] {base_ref[:8]}..{head_ref[:8]} -> {output_dir}")

    repo = get_git_repo()
    diffs_dir = output_dir / "dataset" / "diffs"

    err_console.print("[dim]Step 1/3: file diffs[/dim]")
    file_records = collect_file_records(repo, base_ref, head_ref, diffs_dir)

    err_console.print("[dim]Step 2/3: commit metadata[/dim]")
    commit_records = collect_commit_records(repo, base_ref, head_ref)

    err_console.print("[dim]Step 3/3: GitHub issues[/dim]")
    issue_records = collect_issue_records(commit_records, repo_slug)

    write_dataset(output_dir, file_records, commit_records, issue_records)

    err_console.print(":white_check_mark: [green]Dataset collection complete[/green]")


if __name__ == "__main__":
    try:
        app()
    except AppExit as exc:
        sys.exit(exc.exit_code)
