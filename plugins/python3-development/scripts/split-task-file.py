#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0", "pyyaml>=6.0.0", "rich>=13.0.0"]
# ///
"""Split multi-task markdown file into one-task-per-file directory structure.

This script converts a task file containing multiple tasks (either YAML frontmatter
format or legacy markdown format) into a directory of individual task files.

Usage:
    split-task-file.py <input-file> [output-directory]

Examples:
    # Split into tasks/ subdirectory
    split-task-file.py plugin-validator-tasks.md

    # Split into custom directory
    split-task-file.py tasks.md ./my-tasks/

File Naming Convention:
    Output files are named: {task-id}-{slug}.md
    Examples: T1-data-models.md, 1.1-prepare-host.md, T15-cli-tests.md

    Slug is derived from task title:
    - Lowercase
    - Spaces and special chars → hyphens
    - Multiple hyphens collapsed to single hyphen
    - Max 50 characters
"""

from __future__ import annotations

import re

# Import from implementation_manager in same repository
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills/implementation-manager/scripts")
)

from implementation_manager import Task, parse_task_file

app = typer.Typer(
    name="split-task-file",
    help="Split multi-task file into one-task-per-file directory",
    no_args_is_help=True,
)
console = Console()


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug.

    Args:
        text: Input text to slugify
        max_length: Maximum slug length (default 50)

    Returns:
        Lowercase slug with hyphens, max_length characters
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and special chars with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    return slug


def generate_task_filename(task: Task) -> str:
    """Generate filename for task file.

    Args:
        task: Task object with id and name

    Returns:
        Filename in format: {task-id}-{slug}.md
        Example: T1-data-models.md
    """
    slug = slugify(task.name)
    return f"{task.id}-{slug}.md"


def write_task_file(task: Task, output_path: Path) -> None:
    """Write single task to file with YAML frontmatter.

    Args:
        task: Task object to write
        output_path: Path to output file
    """
    # Build YAML frontmatter
    frontmatter_lines = ["---"]
    frontmatter_lines.extend((f'task: "{task.id}"', f'title: "{task.name}"'))

    # Status (convert enum value back to hyphenated format)
    status_value = task.status.value.lower().replace(" ", "-")
    frontmatter_lines.append(f"status: {status_value}")

    # Optional fields
    if task.agent:
        frontmatter_lines.append(f'agent: "{task.agent}"')

    if task.dependencies:
        deps_str = ", ".join(f'"{d}"' for d in task.dependencies)
        frontmatter_lines.append(f"dependencies: [{deps_str}]")

    frontmatter_lines.extend((
        f"priority: {task.priority.value}",
        f"complexity: {task.complexity.lower()}",
    ))

    if task.started:
        frontmatter_lines.append(f'started: "{task.started}"')

    if task.completed:
        frontmatter_lines.append(f'completed: "{task.completed}"')

    frontmatter_lines.append("---")

    # Write file
    content = "\n".join(frontmatter_lines) + "\n\n"
    content += "## Context\n\n"
    content += f"Task {task.id}: {task.name}\n\n"
    content += "## Objective\n\n"
    content += "[Task objective to be filled in]\n\n"
    content += "## Requirements\n\n"
    content += "1. [Requirement 1]\n"
    content += "2. [Requirement 2]\n\n"
    content += "## Expected Outputs\n\n"
    content += "- [Output 1]\n"
    content += "- [Output 2]\n"

    output_path.write_text(content, encoding="utf-8")


@app.command()
def main(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to multi-task markdown file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    output_dir: Annotated[
        Path | None,
        typer.Argument(
            help="Output directory for task files (default: {input-stem}/tasks/)"
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Overwrite existing task files without prompting"
        ),
    ] = False,
) -> None:
    """Split multi-task file into one-task-per-file directory.

    Args:
        input_file: Path to input task file
        output_dir: Output directory (default: tasks/ in input file directory)
        force: Overwrite existing files without prompting
    """
    console.print(f"[blue]:file_folder: Reading {input_file}...[/blue]")

    # Parse tasks from input file
    try:
        tasks = parse_task_file(input_file)
    except Exception as e:
        console.print(f"[red]:cross_mark: Failed to parse {input_file}: {e}[/red]")
        raise typer.Exit(1) from e

    if not tasks:
        console.print("[yellow]:warning: No tasks found in input file[/yellow]")
        raise typer.Exit(0)

    console.print(f"[green]:white_check_mark: Found {len(tasks)} tasks[/green]")

    # Determine output directory
    if output_dir is None:
        # Default: tasks/ subdirectory next to input file
        output_dir = input_file.parent / "tasks"

    # Create output directory
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[blue]:file_folder: Created directory: {output_dir}[/blue]")
    elif not force:
        # Check if directory is empty
        existing_files = list(output_dir.glob("*.md"))
        if existing_files:
            console.print(
                f"[yellow]:warning: Directory {output_dir} already contains "
                f"{len(existing_files)} .md files[/yellow]"
            )
            overwrite = typer.confirm("Overwrite existing files?")
            if not overwrite:
                console.print("[red]:cross_mark: Aborted[/red]")
                raise typer.Exit(1)

    # Write each task to individual file
    console.print(f"[blue]:writing_hand: Writing {len(tasks)} task files...[/blue]")

    for task in tasks:
        filename = generate_task_filename(task)
        output_path = output_dir / filename

        write_task_file(task, output_path)
        console.print(f"  [green]:white_check_mark: {filename}[/green]")

    console.print(
        f"\n[green]:tada: Successfully split {len(tasks)} tasks "
        f"into {output_dir}[/green]"
    )
    console.print(
        f"\n[blue]Next steps:[/blue]\n"
        f"  1. Review generated files in {output_dir}\n"
        f"  2. Fill in Context, Objective, Requirements for each task\n"
        f"  3. Test with: implementation_manager.py status {output_dir.parent} tasks"
    )


if __name__ == "__main__":
    app()
