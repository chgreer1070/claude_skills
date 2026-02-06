#!/usr/bin/env python3
"""Git change analysis script - extracts commits, diffs, and statistics.

This script analyzes git changes between two references and outputs detailed
information including commits, diffs, and statistics to a specified directory.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

_MIN_NUMSTAT_FIELDS = (
    2  # Minimum fields in git diff --numstat output (added, deleted, filename)
)

app = typer.Typer(
    name="analyze_git_changes",
    help="Extract commits, diffs, and statistics from git changes",
    add_completion=False,
)
console = Console()


class GitAnalysisError(Exception):
    """Custom exception for git analysis errors."""


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
        GitAnalysisError: If command fails and check=True
    """
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=check
        )
    except subprocess.CalledProcessError as e:
        msg = f"Git command failed: {e.stderr.strip()}"
        raise GitAnalysisError(msg) from e


def verify_git_repository() -> None:
    """Verify that current directory is a git repository.

    Raises:
        GitAnalysisError: If not in a git repository
    """
    result = run_git_command(["rev-parse", "--git-dir"], check=False)
    if result.returncode != 0:
        msg = "Not a git repository"
        raise GitAnalysisError(msg)


def find_merge_base(base_ref: str, head_ref: str) -> str:
    """Find the merge base between two git references.

    Args:
        base_ref: Base reference (e.g., 'main')
        head_ref: Head reference (e.g., 'HEAD')

    Returns:
        Merge base commit hash

    Raises:
        GitAnalysisError: If merge base cannot be found
    """
    result = run_git_command(["merge-base", base_ref, head_ref], check=False)
    if result.returncode != 0:
        msg = f"Could not find merge base between {base_ref} and {head_ref}"
        raise GitAnalysisError(msg)

    merge_base = result.stdout.strip()
    if not merge_base:
        msg = "Merge base is empty"
        raise GitAnalysisError(msg)

    return merge_base


def get_current_branch() -> str:
    """Get the name of the current git branch.

    Returns:
        Current branch name

    Raises:
        GitAnalysisError: If branch name cannot be determined
    """
    result = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    branch = result.stdout.strip()
    if not branch:
        msg = "Could not determine current branch"
        raise GitAnalysisError(msg)
    return branch


def extract_commits_oneline(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract one-line commit list.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command([
        "log",
        "--oneline",
        "--no-merges",
        f"{merge_base}..{head_ref}",
    ])
    output_file.write_text(result.stdout, encoding="utf-8")


def extract_commits_detailed(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract detailed commit messages.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command([
        "log",
        "--format=%H%n%an%n%ae%n%at%n%s%n%b%n---COMMIT-SEPARATOR---",
        "--no-merges",
        f"{merge_base}..{head_ref}",
    ])
    output_file.write_text(result.stdout, encoding="utf-8")


def count_commits(merge_base: str, head_ref: str) -> int:
    """Count commits between merge base and head.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference

    Returns:
        Number of commits
    """
    result = run_git_command([
        "rev-list",
        "--count",
        "--no-merges",
        f"{merge_base}..{head_ref}",
    ])
    return int(result.stdout.strip())


def extract_diff(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract unified diff of changes.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command(["diff", f"{merge_base}..{head_ref}"])
    output_file.write_text(result.stdout, encoding="utf-8")


def extract_diff_stat(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract diff statistics.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command(["diff", "--stat", f"{merge_base}..{head_ref}"])
    output_file.write_text(result.stdout, encoding="utf-8")


def extract_changed_files(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract list of changed files with status.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command(["diff", "--name-status", f"{merge_base}..{head_ref}"])
    output_file.write_text(result.stdout, encoding="utf-8")


def extract_numstat(merge_base: str, head_ref: str, output_file: Path) -> None:
    """Extract per-file line change statistics.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference
        output_file: Output file path
    """
    result = run_git_command(["diff", "--numstat", f"{merge_base}..{head_ref}"])
    output_file.write_text(result.stdout, encoding="utf-8")


def calculate_statistics(merge_base: str, head_ref: str) -> dict[str, int]:
    """Calculate total lines added, deleted, and files changed.

    Args:
        merge_base: Merge base commit hash
        head_ref: Head reference

    Returns:
        Dictionary with lines_added, lines_deleted, files_changed
    """
    # Get numstat output
    result = run_git_command(["diff", "--numstat", f"{merge_base}..{head_ref}"])

    lines_added = 0
    lines_deleted = 0
    files_changed = 0

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        files_changed += 1
        parts = line.split("\t")
        if len(parts) >= _MIN_NUMSTAT_FIELDS:
            # Handle binary files (shown as '-')
            added = parts[0]
            deleted = parts[1]

            if added != "-":
                lines_added += int(added)
            if deleted != "-":
                lines_deleted += int(deleted)

    return {
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "files_changed": files_changed,
    }


def create_summary_json(
    current_branch: str,
    base_ref: str,
    head_ref: str,
    merge_base: str,
    commit_count: int,
    *,
    stats: dict[str, int],
    output_file: Path,
) -> None:
    """Create machine-readable summary JSON.

    Args:
        current_branch: Current branch name
        base_ref: Base reference
        head_ref: Head reference
        merge_base: Merge base commit hash
        commit_count: Number of commits
        stats: Statistics dictionary
        output_file: Output file path
    """
    summary = {
        "current_branch": current_branch,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "merge_base": merge_base,
        "commit_count": commit_count,
        "files_changed": stats["files_changed"],
        "lines_added": stats["lines_added"],
        "lines_deleted": stats["lines_deleted"],
        "analysis_timestamp": datetime.now(UTC).isoformat(),
    }

    output_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def create_summary_text(
    current_branch: str,
    base_ref: str,
    head_ref: str,
    merge_base: str,
    commit_count: int,
    *,
    stats: dict[str, int],
    output_file: Path,
) -> None:
    """Create human-readable summary text.

    Args:
        current_branch: Current branch name
        base_ref: Base reference
        head_ref: Head reference
        merge_base: Merge base commit hash
        commit_count: Number of commits
        stats: Statistics dictionary
        output_file: Output file path
    """
    summary = f"""Git Change Analysis Summary
============================

Branch: {current_branch}
Comparing: {base_ref}..{head_ref}
Merge Base: {merge_base}

Statistics:
- Commits: {commit_count}
- Files Changed: {stats["files_changed"]}
- Lines Added: {stats["lines_added"]}
- Lines Deleted: {stats["lines_deleted"]}

Output Files:
- commits_oneline.txt: One-line commit list
- commits_detailed.txt: Full commit messages
- changes.diff: Unified diff of all changes
- changes_stat.txt: Diffstat summary
- changed_files.txt: List of changed files with status
- changes_numstat.txt: Per-file line changes
- summary.json: Machine-readable summary
"""
    output_file.write_text(summary, encoding="utf-8")


def create_summary_table(
    current_branch: str,
    base_ref: str,
    head_ref: str,
    merge_base: str,
    commit_count: int,
    *,
    stats: dict[str, int],
) -> Table:
    """Create a Rich table for summary display.

    Args:
        current_branch: Current branch name
        base_ref: Base reference
        head_ref: Head reference
        merge_base: Merge base commit hash
        commit_count: Number of commits
        stats: Statistics dictionary

    Returns:
        Rich Table object
    """
    table = Table(
        title=":bar_chart: Git Change Analysis Summary",
        box=box.MINIMAL_DOUBLE_HEAD,
        title_style="bold blue",
    )

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Current Branch", current_branch)
    table.add_row("Comparing", f"{base_ref}..{head_ref}")
    table.add_row("Merge Base", merge_base[:12])
    table.add_row("Commits", str(commit_count))
    table.add_row("Files Changed", str(stats["files_changed"]))
    table.add_row("Lines Added", f"+{stats['lines_added']}")
    table.add_row("Lines Deleted", f"-{stats['lines_deleted']}")

    return table


@app.command()
def analyze(
    base_ref: Annotated[
        str,
        typer.Argument(
            help="Base git reference to compare from (e.g., 'main', 'develop')"
        ),
    ] = "main",
    head_ref: Annotated[
        str,
        typer.Argument(
            help="Head git reference to compare to (e.g., 'HEAD', 'feature-branch')"
        ),
    ] = "HEAD",
    output_dir: Annotated[
        Path,
        typer.Argument(
            help="Directory to write analysis output files",
            file_okay=False,
            dir_okay=True,
        ),
    ] = Path(),
) -> None:
    """Analyze git changes and extract commits, diffs, and statistics.

    This command analyzes changes between BASE_REF and HEAD_REF, generating
    detailed reports including commit history, diffs, and change statistics.

    All output files are written to OUTPUT_DIR.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Verify git repository
            task = progress.add_task("Verifying git repository...", total=None)
            verify_git_repository()
            progress.update(
                task, description=":white_check_mark: Git repository verified"
            )

            # Find merge base
            progress.update(task, description="Finding merge base...")
            merge_base = find_merge_base(base_ref, head_ref)
            progress.update(task, description=":white_check_mark: Merge base found")

            # Get current branch
            progress.update(task, description="Getting current branch...")
            current_branch = get_current_branch()
            progress.update(
                task, description=":white_check_mark: Current branch identified"
            )

            # Create output directory
            progress.update(task, description="Creating output directory...")
            output_dir.mkdir(parents=True, exist_ok=True)
            progress.update(
                task, description=":white_check_mark: Output directory ready"
            )

            # Extract commits
            progress.update(task, description="Extracting commit history...")
            extract_commits_oneline(
                merge_base, head_ref, output_dir / "commits_oneline.txt"
            )
            extract_commits_detailed(
                merge_base, head_ref, output_dir / "commits_detailed.txt"
            )
            commit_count = count_commits(merge_base, head_ref)
            progress.update(
                task, description=f":white_check_mark: Extracted {commit_count} commits"
            )

            # Extract diffs
            progress.update(task, description="Extracting diffs...")
            extract_diff(merge_base, head_ref, output_dir / "changes.diff")
            extract_diff_stat(merge_base, head_ref, output_dir / "changes_stat.txt")
            extract_changed_files(
                merge_base, head_ref, output_dir / "changed_files.txt"
            )
            extract_numstat(merge_base, head_ref, output_dir / "changes_numstat.txt")
            progress.update(task, description=":white_check_mark: Diffs extracted")

            # Calculate statistics
            progress.update(task, description="Calculating statistics...")
            stats = calculate_statistics(merge_base, head_ref)
            progress.update(
                task, description=":white_check_mark: Statistics calculated"
            )

            # Create summaries
            progress.update(task, description="Creating summaries...")
            create_summary_json(
                current_branch,
                base_ref,
                head_ref,
                merge_base,
                commit_count,
                stats=stats,
                output_file=output_dir / "summary.json",
            )
            create_summary_text(
                current_branch,
                base_ref,
                head_ref,
                merge_base,
                commit_count,
                stats=stats,
                output_file=output_dir / "summary.txt",
            )
            progress.update(task, description=":white_check_mark: Summaries created")

            progress.remove_task(task)

        # Display summary
        console.print()
        console.print(
            Panel.fit(
                f"Analysis complete. Results written to [cyan]{output_dir.absolute()}[/cyan]",
                title=":white_check_mark: Success",
                border_style="green",
            )
        )
        console.print()

        summary_table = create_summary_table(
            current_branch, base_ref, head_ref, merge_base, commit_count, stats=stats
        )
        console.print(summary_table)

    except GitAnalysisError as e:
        console.print(
            Panel.fit(f"[red]{e}[/red]", title=":cross_mark: Error", border_style="red")
        )
        raise typer.Exit(code=1) from e
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130) from None


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
