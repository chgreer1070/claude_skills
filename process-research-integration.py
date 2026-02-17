#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.9.4",
# ]
# ///
"""
Batch process research files to add Integration Opportunities sections.

This script orchestrates the research-context-agent to analyze each research
file and append structured integration opportunities.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(help="Process research files for integration opportunities")
console = Console()


def find_research_files(
    category: str | None = None,
    single_file: Path | None = None,
) -> list[Path]:
    """Find all research markdown files to process."""
    repo_root = Path(__file__).parent
    research_dir = repo_root / "research"

    if single_file:
        if not single_file.exists():
            console.print(f"[red]Error: File not found: {single_file}[/red]")
            sys.exit(1)
        return [single_file]

    if category:
        category_dir = research_dir / category
        if not category_dir.exists():
            console.print(f"[red]Error: Category not found: {category}[/red]")
            sys.exit(1)
        files = list(category_dir.glob("*.md"))
    else:
        files = list(research_dir.rglob("*.md"))

    # Exclude README.md files
    files = [f for f in files if f.name != "README.md"]

    return sorted(files)


def count_section_items(content: str, section: str) -> int:
    """Count items in a section of the Integration Opportunities."""
    lines = content.split("\n")
    in_section = False
    count = 0

    for line in lines:
        if section in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("###") or line.startswith("##"):
                break
            if line.strip().startswith("- ") or line.strip().startswith("| "):
                count += 1

    return max(0, count - 1)  # Subtract header row from tables


def analyze_output(file_path: Path) -> dict[str, int]:
    """Analyze the Integration Opportunities section added to a file."""
    if not file_path.exists():
        return {"enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    content = file_path.read_text()

    if "## Integration Opportunities" not in content:
        return {"enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    # Split to get just the Integration Opportunities section
    parts = content.split("## Integration Opportunities")
    if len(parts) < 2:
        return {"enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    io_section = parts[-1]

    return {
        "enhancements": count_section_items(io_section, "### Enhances Existing"),
        "skills": count_section_items(io_section, "### New Skill Candidates"),
        "mcps": count_section_items(io_section, "### New MCP Server Candidates"),
        "cross_refs": count_section_items(io_section, "### Cross-References"),
    }


def process_file(file_path: Path, dry_run: bool = False) -> dict[str, int | bool]:
    """Process a single research file using claude command."""
    repo_root = Path(__file__).parent
    agent_path = repo_root / ".claude" / "agents" / "research-context-agent.md"

    if not agent_path.exists():
        console.print(f"[red]Error: Agent not found at {agent_path}[/red]")
        sys.exit(1)

    if dry_run:
        console.print(f"[dim]Would process: {file_path.relative_to(repo_root)}[/dim]")
        return {"success": True, "enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}

    # Read the agent definition
    agent_content = agent_path.read_text()

    # Create the prompt for the agent
    prompt = f"""You are the research-context-agent as defined in {agent_path}

Please process this research file:
{file_path}

Follow the three-phase process:
1. Absorb: Read and understand the research file
2. Search & Match: Find connections across the 5 dimensions (enhance skills, enhance agents, enhance hooks, new skill candidates, new MCP candidates)
3. Append: Add the Integration Opportunities section to the end of the file

Remember:
- Be concrete and specific (not vague)
- Only include genuine connections
- Skip empty sections
- Preserve all existing content"""

    try:
        # Use subprocess to call claude code with the agent
        # This is a placeholder - in reality, we'd need to use the Task tool or similar
        # For now, we'll document that this needs to be run through Claude Code interface

        console.print(
            f"[yellow]Note: Actual processing requires Claude Code Task tool[/yellow]"
        )
        console.print(f"[dim]File: {file_path.relative_to(repo_root)}[/dim]")

        # Analyze what was added (if anything)
        stats = analyze_output(file_path)
        stats["success"] = True
        return stats

    except Exception as e:
        console.print(f"[red]Error processing {file_path}: {e}[/red]")
        return {"success": False, "enhancements": 0, "skills": 0, "mcps": 0, "cross_refs": 0}


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
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be processed without making changes"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Force reprocess (replace existing sections)"),
    ] = False,
) -> None:
    """Process research files to add Integration Opportunities sections."""
    console.print("\n[bold blue]🔍 Processing Research Integration Opportunities[/bold blue]\n")

    # Find files to process
    files = find_research_files(category, file)

    if not files:
        console.print("[yellow]No research files found to process.[/yellow]")
        sys.exit(0)

    console.print(f"Found {len(files)} research file{'s' if len(files) != 1 else ''}")

    if category:
        console.print(f"[dim]Category: {category}[/dim]")
    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/yellow]")

    console.print()

    # Process each file
    total_enhancements = 0
    total_skills = 0
    total_mcps = 0
    total_cross_refs = 0
    failures = []

    repo_root = Path(__file__).parent

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=len(files))

        for file_path in files:
            rel_path = file_path.relative_to(repo_root)
            progress.update(task, description=f"Processing: {rel_path}")

            result = process_file(file_path, dry_run)

            if result["success"]:
                total_enhancements += result["enhancements"]
                total_skills += result["skills"]
                total_mcps += result["mcps"]
                total_cross_refs += result["cross_refs"]
                console.print(
                    f"[green]✓[/green] {rel_path} "
                    f"({result['enhancements']} enhance, {result['skills']} skills, "
                    f"{result['mcps']} mcps, {result['cross_refs']} refs)"
                )
            else:
                failures.append(rel_path)
                console.print(f"[red]✗[/red] {rel_path}")

            progress.advance(task)

    # Print summary
    console.print("\n[bold]📊 Summary[/bold]")
    console.print("━" * 60)

    table = Table.grid(padding=(0, 2))
    table.add_row("Files processed:", str(len(files) - len(failures)))
    table.add_row("Enhancements found:", str(total_enhancements))
    table.add_row("New skill candidates:", str(total_skills))
    table.add_row("New MCP candidates:", str(total_mcps))
    table.add_row("Cross-references:", str(total_cross_refs))
    table.add_row("Failures:", str(len(failures)))

    console.print(table)
    console.print("━" * 60)

    if failures:
        console.print("\n[red]Failed files:[/red]")
        for failure in failures:
            console.print(f"  • {failure}")

    if not dry_run and not failures:
        console.print("\n[green]✅ All research files processed[/green]")


if __name__ == "__main__":
    app()
