#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
# ]
# ///
"""Batch process research files to add Integration Opportunities sections.

This script orchestrates the research-context-agent to analyze each research
file and append structured integration opportunities by cross-referencing with
existing skills, agents, commands, and plugins in the repository.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    help="Process research files for integration opportunities",
    no_args_is_help=True,
)
console = Console()
error_console = Console(stderr=True, style="bold red")


def find_research_files(
    category: str | None = None,
    single_file: Path | None = None,
) -> list[Path]:
    """Find all research markdown files to process.

    Args:
        category: Optional category to filter by (e.g., "developer-tools")
        single_file: Optional single file path to process

    Returns:
        List of research file paths to process

    Raises:
        typer.Exit: If specified file or category doesn't exist
    """
    repo_root = Path(__file__).parent.parent
    research_dir = repo_root / "research"

    if not research_dir.exists():
        error_console.print(f"[red]Error: Research directory not found: {research_dir}[/red]")
        raise typer.Exit(1)

    if single_file:
        if not single_file.exists():
            error_console.print(f"[red]Error: File not found: {single_file}[/red]")
            raise typer.Exit(1)
        return [single_file]

    if category:
        category_dir = research_dir / category
        if not category_dir.exists():
            error_console.print(f"[red]Error: Category not found: {category}[/red]")
            error_console.print(f"[yellow]Available categories:[/yellow]")
            for d in sorted(research_dir.iterdir()):
                if d.is_dir():
                    error_console.print(f"  - {d.name}")
            raise typer.Exit(1)
        files = list(category_dir.glob("*.md"))
    else:
        files = list(research_dir.rglob("*.md"))

    # Exclude README.md files
    files = [f for f in files if f.name != "README.md"]

    return sorted(files)


def count_section_items(content: str, section_marker: str) -> int:
    """Count items in a specific section of the Integration Opportunities.

    Args:
        content: The file content
        section_marker: The section header to look for

    Returns:
        Count of items (list items or table rows minus header)
    """
    lines = content.split("\n")
    in_section = False
    count = 0

    for line in lines:
        if section_marker in line and line.startswith("###"):
            in_section = True
            continue
        if in_section:
            if line.startswith("###") or line.startswith("##"):
                break
            if line.strip().startswith("- ") or (line.strip().startswith("|") and "|" in line[1:]):
                count += 1

    # Subtract header row from tables
    return max(0, count - 1) if "|" in section_marker else count


def analyze_output(file_path: Path) -> dict[str, int]:
    """Analyze the Integration Opportunities section to count discoveries.

    Args:
        file_path: Path to the processed file

    Returns:
        Dictionary with counts of enhancements, skills, mcps, cross_refs
    """
    if not file_path.exists():
        return {"enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    content = file_path.read_text(encoding="utf-8")

    if "## Integration Opportunities" not in content:
        return {"enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    return {
        "enhancements": count_section_items(content, "### Enhances Existing"),
        "skills": count_section_items(content, "### New Skill Candidates"),
        "mcps": count_section_items(content, "### New MCP Server Candidates"),
        "cross_refs": count_section_items(content, "### Cross-References"),
    }


def process_file(file_path: Path, force: bool = False, dry_run: bool = False) -> dict[str, int | str]:
    """Process a single research file with the research-context-agent.

    Args:
        file_path: Path to the research file
        force: Whether to force reprocessing even if already processed
        dry_run: Whether to simulate without making changes

    Returns:
        Dictionary with status and counts
    """
    # Check if already processed
    content = file_path.read_text(encoding="utf-8")
    if "## Integration Opportunities" in content and not force:
        return {
            "status": "skipped",
            "reason": "already_processed",
            "enhancements": 0,
            "skills": 0,
            "mcps": 0,
            "cross_refs": 0,
        }

    if dry_run:
        return {
            "status": "would_process",
            "enhancements": 0,
            "skills": 0,
            "mcps": 0,
            "cross_refs": 0,
        }

    # TODO: Invoke the research-context-agent via Task tool
    # For now, this is a placeholder that would need to be connected
    # to Claude Code's Task system
    
    error_console.print(
        f"[yellow]Warning: Agent invocation not yet implemented. "
        f"Would process: {file_path}[/yellow]"
    )
    
    return {
        "status": "not_implemented",
        "enhancements": 0,
        "skills": 0,
        "mcps": 0,
        "cross_refs": 0,
    }


@app.command()
def main(
    category: Annotated[
        str | None,
        typer.Option("--category", "-c", help="Process only files in this category"),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Process a single file"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Force reprocess files with existing Integration Opportunities"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be processed without making changes"),
    ] = False,
) -> None:
    """Batch process research files to add Integration Opportunities sections.

    This script finds research markdown files and processes each one through the
    research-context-agent, which cross-references the file content with existing
    repository capabilities and appends structured integration opportunities.

    Examples:
        # Process all research files
        ./process-research-integration.py

        # Process a specific category
        ./process-research-integration.py --category developer-tools

        # Process a single file
        ./process-research-integration.py --file research/developer-tools/loguru.md

        # Force reprocess all files
        ./process-research-integration.py --force

        # Dry run to see what would be processed
        ./process-research-integration.py --dry-run
    """
    console.print(
        Panel.fit(
            "[bold blue]Research Integration Opportunities - Batch Processor[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Find files to process
    try:
        files = find_research_files(category, file)
    except typer.Exit:
        raise

    if not files:
        console.print("[yellow]No research files found matching the criteria.[/yellow]")
        raise typer.Exit(0)

    console.print(f"[green]Found {len(files)} research file(s)[/green]")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    console.print()

    # Process files
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing files...", total=len(files))

        for file_path in files:
            progress.update(task, description=f"Processing {file_path.name}")
            result = process_file(file_path, force, dry_run)
            result["file"] = str(file_path.relative_to(Path.cwd()))
            results.append(result)
            progress.advance(task)

    # Summary table
    console.print()
    table = Table(title="Processing Summary", show_header=True, header_style="bold magenta")
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Status", style="green")
    table.add_column("Enhancements", justify="right")
    table.add_column("Skills", justify="right")
    table.add_column("MCPs", justify="right")
    table.add_column("Cross-Refs", justify="right")

    total_enhancements = 0
    total_skills = 0
    total_mcps = 0
    total_cross_refs = 0
    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for result in results:
        status_display = {
            "completed": "[green]✓ Completed[/green]",
            "skipped": "[yellow]⊘ Skipped[/yellow]",
            "would_process": "[blue]→ Would process[/blue]",
            "not_implemented": "[yellow]⚠ Not implemented[/yellow]",
            "failed": "[red]✗ Failed[/red]",
        }.get(result["status"], result["status"])

        table.add_row(
            result["file"],
            status_display,
            str(result["enhancements"]),
            str(result["skills"]),
            str(result["mcps"]),
            str(result["cross_refs"]),
        )

        if result["status"] == "completed":
            processed_count += 1
            total_enhancements += result["enhancements"]
            total_skills += result["skills"]
            total_mcps += result["mcps"]
            total_cross_refs += result["cross_refs"]
        elif result["status"] == "skipped":
            skipped_count += 1
        elif result["status"] == "failed":
            failed_count += 1

    console.print(table)
    console.print()

    # Final summary
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right", style="cyan")

    summary_table.add_row("Files processed", str(processed_count))
    summary_table.add_row("Files skipped", str(skipped_count))
    if failed_count > 0:
        summary_table.add_row("Files failed", f"[red]{failed_count}[/red]")
    summary_table.add_row("", "")
    summary_table.add_row("Enhancements found", str(total_enhancements))
    summary_table.add_row("New skill candidates", str(total_skills))
    summary_table.add_row("New MCP candidates", str(total_mcps))
    summary_table.add_row("Cross-references", str(total_cross_refs))

    console.print(Panel(summary_table, title="[bold]Summary[/bold]", border_style="green"))

    if dry_run:
        console.print()
        console.print("[yellow]This was a dry run. Use without --dry-run to process files.[/yellow]")

    if failed_count > 0:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
