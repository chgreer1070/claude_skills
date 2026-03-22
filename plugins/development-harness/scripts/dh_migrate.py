#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.21.0",
#   "rich>=13.0",
# ]
# ///
"""dh_migrate — migrate project state from legacy .claude/ layout to ~/.dh/.

Commands
--------
verify      Report current layout state without modifying anything.
migrate     Move files from the old layout to the new one.

Usage
-----
    uv run plugins/development-harness/scripts/dh_migrate.py verify
    uv run plugins/development-harness/scripts/dh_migrate.py migrate --dry-run
    uv run plugins/development-harness/scripts/dh_migrate.py migrate
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

# ---------------------------------------------------------------------------
# Bootstrap: make the development-harness package importable from within the
# PEP 723 isolated environment.  The script lives at:
#   plugins/development-harness/scripts/dh_migrate.py
# so parents[1] is plugins/development-harness/.
# ---------------------------------------------------------------------------
_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

import dh_paths
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="dh_migrate", help="Migrate DH project state from legacy .claude/ layout to ~/.dh/.", no_args_is_help=True
)

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Mapping: old repo-relative path (relative to project root) → dh_paths fn name
_OLD_TO_NEW: dict[str, str] = {
    ".claude/backlog": "backlog_dir",
    ".claude/context": "context_dir",
    ".claude/reports": "reports_dir",
    "plan": "plan_dir",
}


def _project_root() -> Path:
    """Resolve git project root; exit with message on failure.

    Returns:
        Absolute path to the git project root.

    Raises:
        typer.Exit: With code 1 if git is unavailable or not in a repo.
    """
    try:
        return dh_paths.git_project_root()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        err_console.print(f":cross_mark: Cannot determine git project root: {exc}")
        raise typer.Exit(code=1) from exc


def _old_dirs(project_root: Path) -> dict[str, Path]:
    """Return mapping of old-relative-path → absolute path for each legacy directory."""
    return {old: project_root / old for old in _OLD_TO_NEW}


def _detect_layout(project_root: Path) -> dict[str, bool]:
    """Return presence flags for old and new layout indicators.

    Returns:
        Dict with keys ``old_present`` and ``new_present``.
    """
    old_present = any((project_root / old).exists() for old in _OLD_TO_NEW)
    new_present = dh_paths.backlog_dir(project_root).exists()
    return {"old_present": old_present, "new_present": new_present}


# ---------------------------------------------------------------------------
# verify command
# ---------------------------------------------------------------------------


@app.command()
def verify() -> None:
    """Scan the current project and report layout state.

    Exits 0 if the project is on the new layout (or already migrated).
    Exits 1 if old layout directories are detected (action required).
    """
    project_root = _project_root()
    slug = dh_paths.compute_slug(project_root)
    state = _detect_layout(project_root)

    table = Table(title="DH Layout State", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="dim")
    table.add_column("Status")
    table.add_column("Path")

    # Old layout indicators
    for label, old_path in _old_dirs(project_root).items():
        exists = old_path.exists()
        status = ":cross_mark: [red]present[/red]" if exists else ":white_check_mark: [green]absent[/green]"
        table.add_row(f"Old: {label}/", status, str(old_path))

    # New layout indicator
    new_backlog = dh_paths.backlog_dir(project_root)
    new_status = (
        ":white_check_mark: [green]present[/green]" if state["new_present"] else ":cross_mark: [red]absent[/red]"
    )
    table.add_row("New: backlog/", new_status, str(new_backlog))

    console.print(table)
    console.print(f"\n[dim]Project slug:[/dim] {slug}")

    if state["old_present"] and not state["new_present"]:
        console.print(
            Panel(
                "[yellow]Old layout detected (.claude/backlog/ present).[/yellow]\n"
                "Run [bold]dh_migrate migrate --dry-run[/bold] to preview changes,\n"
                "then [bold]dh_migrate migrate[/bold] to apply.",
                title="Action Required",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)
    if state["old_present"] and state["new_present"]:
        console.print(
            Panel(
                "[yellow]Partial migration detected — both old and new layout present.[/yellow]\n"
                "Run [bold]dh_migrate migrate[/bold] to complete the migration.",
                title="Partial Migration",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)
    console.print(
        Panel(
            f"[green]New layout active — backlog under[/green]\n{new_backlog}",
            title=":white_check_mark: Migrated",
            border_style="green",
        )
    )


# ---------------------------------------------------------------------------
# migrate command
# ---------------------------------------------------------------------------


@app.command()
def migrate(
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be moved without making any changes.")
    ] = False,
) -> None:
    """Move state directories from the old layout to the new DH layout.

    Moves .claude/backlog/, .claude/context/, .claude/reports/, and plan/
    to ~/.dh/projects/{slug}/. Removes old directories only when empty
    after migration. Creates .dh/.gitkeep in-repo. Does NOT touch
    .claude/CLAUDE.md or other project config files.

    Use --dry-run to preview without making changes.
    """
    project_root = _project_root()
    state = _detect_layout(project_root)

    prefix = "[dim][DRY-RUN][/dim] " if dry_run else ""

    console.print(
        Panel(
            f"Project root: {project_root}\nState home:   {dh_paths.state_root(project_root)}",
            title="DH Migration",
            border_style="blue",
        )
    )

    if not state["old_present"]:
        console.print(":white_check_mark: No old layout directories found — nothing to migrate.")
        return

    # Build move plan
    move_plan: list[tuple[Path, Path]] = []  # (src, dest)
    new_fn_map = {
        ".claude/backlog": dh_paths.backlog_dir,
        ".claude/context": dh_paths.context_dir,
        ".claude/reports": dh_paths.reports_dir,
        "plan": dh_paths.plan_dir,
    }
    for label, fn in new_fn_map.items():
        src = project_root / label
        if src.exists():
            dest = fn(project_root)
            move_plan.append((src, dest))

    # Display plan
    plan_table = Table(title="Migration Plan", show_header=True, header_style="bold cyan")
    plan_table.add_column("Source (old)", style="dim red")
    plan_table.add_column("Destination (new)", style="dim green")
    for src, dest in move_plan:
        plan_table.add_row(str(src), str(dest))

    console.print(plan_table)

    if dry_run:
        console.print("\n:magnifying_glass: Dry-run complete — no files were changed.")
        return

    # Execute moves
    errors: list[str] = []
    for src, dest in move_plan:
        console.print(f"{prefix}Moving [dim]{src}[/dim] → [green]{dest}[/green]")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                # Merge: copy individual items from src into existing dest
                _merge_dir(src, dest, console)
            else:
                shutil.move(str(src), str(dest))
        except Exception as exc:  # noqa: BLE001 — shutil.move/copytree raise varied OS-level errors
            msg = f"Failed to move {src} → {dest}: {exc}"
            err_console.print(f":cross_mark: {msg}")
            errors.append(msg)

    if errors:
        err_console.print(Panel("\n".join(errors), title=":cross_mark: Migration Errors", border_style="red"))
        raise typer.Exit(code=1)

    # Remove old empty directories (only if now empty)
    _remove_empty_old_dirs(project_root, console)

    # Create .dh/.gitkeep in-repo (Tier 1 marker)
    dh_dir = dh_paths.project_dh_dir(project_root)
    dh_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = dh_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        console.print(f":white_check_mark: Created [green]{gitkeep}[/green]")
    else:
        console.print(f":white_check_mark: [dim]{gitkeep}[/dim] already present")

    console.print(
        Panel(
            f"[green]Migration complete.[/green]\nState is now at: {dh_paths.state_root(project_root)}",
            title=":white_check_mark: Done",
            border_style="green",
        )
    )

    # Artifact manifest update (best-effort; warn on failure)
    _update_artifact_manifests(project_root, console)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _merge_dir(src: Path, dest: Path, out: Console) -> None:
    """Copy all items from src into dest, then remove src.

    Args:
        src: Source directory.
        dest: Destination directory (must already exist).
        out: Rich Console for progress output.
    """
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(target), dirs_exist_ok=True)
        else:
            shutil.copy2(str(item), str(target))
        out.print(f"  [dim]merged[/dim] {item.name}")
    shutil.rmtree(src)


def _remove_empty_old_dirs(project_root: Path, out: Console) -> None:
    """Remove legacy directories if they are now empty.

    Does NOT remove .claude/ itself — other config files (CLAUDE.md, rules/,
    hooks/) may still live there.

    Args:
        project_root: Absolute project root path.
        out: Rich Console for output.
    """
    # Order matters: remove children before parents
    candidates = [
        project_root / ".claude" / "backlog",
        project_root / ".claude" / "context",
        project_root / ".claude" / "reports",
        project_root / "plan",
    ]
    for candidate in candidates:
        if candidate.exists() and not any(candidate.iterdir()):
            candidate.rmdir()
            out.print(f":white_check_mark: Removed empty [dim]{candidate}[/dim]")
        elif candidate.exists():
            out.print(f"[yellow]Skipped removal of {candidate} — not empty after merge.[/yellow]")


def _update_artifact_manifests(project_root: Path, out: Console) -> None:
    """Log artifact manifest update instructions.

    Artifact manifests are stored in GitHub Issue bodies and managed by the
    backlog MCP server.  Path updates must be applied via the MCP
    ``artifact_register`` tool — this CLI script cannot call MCP tools directly.

    This function logs actionable instructions so the operator can complete
    the manifest update step using the MCP tools after migration.

    Args:
        project_root: Absolute project root path.
        out: Rich Console for output.
    """
    old_prefixes = ("plan/", ".claude/backlog/", ".claude/context/", ".claude/reports/")
    state = dh_paths.state_root(project_root)

    out.print("\n[dim]Artifact manifest update instructions:[/dim]")
    out.print("[yellow]:warning:  Artifact manifests in GitHub Issue bodies may contain old path prefixes.[/yellow]")
    out.print(
        "Run the following via the backlog MCP server for each affected issue:\n"
        "  [dim]artifact_list(issue_number=N)[/dim] — find entries with old prefixes\n"
        "  [dim]artifact_register(issue_number=N, type=T, path=<new_relative_path>)[/dim]"
        " — re-register with new path\n"
    )
    out.print("[dim]Old prefixes to look for:[/dim]")
    for prefix in old_prefixes:
        out.print(f"  [dim red]{prefix!r}[/dim red]")
    out.print(f"[dim]New base directory:[/dim] {state}")
    out.print(
        "[dim]New relative paths are relative to the state root shown above.[/dim]\n"
        "Example: [dim]plan/P981-foo.yaml[/dim] → [dim]plan/P981-foo.yaml[/dim] "
        "(filename unchanged; resolution base changes to state root)."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
