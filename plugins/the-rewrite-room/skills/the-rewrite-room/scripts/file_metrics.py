#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0", "rich>=14.0.0"]
# ///
"""File Metrics — token counting and file size analysis for documentation files."""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="file-metrics",
    help="Token counting and file size analysis for documentation files",
)
console = Console()
err_console = Console(stderr=True)

# Characters-per-token approximation used across this codebase (matches plugin_validator.py convention)
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Estimate token count using chars/4 approximation."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def _measure_file(filepath: Path) -> dict[str, int | str]:
    """Return metrics dict for a single file."""
    content = filepath.read_text(encoding="utf-8")
    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    chars = len(content)
    tokens = _estimate_tokens(content)
    return {
        "path": str(filepath),
        "lines": lines,
        "chars": chars,
        "estimated_tokens": tokens,
    }


@app.command()
def count(file: Annotated[Path, typer.Argument(help="File to measure")]) -> None:
    """Estimate token count and report size metrics for a single file."""
    if not file.exists():
        err_console.print(f"[red]ERROR[/red] File not found: {file}")
        raise typer.Exit(1)

    metrics = _measure_file(file)
    console.print(f"\n[bold]{file}[/bold]")
    console.print(f"  Lines:             {metrics['lines']:>8,}")
    console.print(f"  Characters:        {metrics['chars']:>8,}")
    console.print(f"  Estimated tokens:  {metrics['estimated_tokens']:>8,}")


@app.command()
def scan(
    directory: Annotated[Path, typer.Argument(help="Directory to scan for .md files")],
    top: Annotated[
        int, typer.Option("--top", help="Show top N files by token count")
    ] = 20,
) -> None:
    """Scan all .md files in a directory and report metrics sorted by estimated token count."""
    if not directory.is_dir():
        err_console.print(f"[red]ERROR[/red] Not a directory: {directory}")
        raise typer.Exit(1)

    md_files = sorted(directory.rglob("*.md"))
    if not md_files:
        console.print(f"[yellow]No .md files found in {directory}[/yellow]")
        raise typer.Exit(0)

    all_metrics = [_measure_file(f) for f in md_files]
    all_metrics.sort(key=operator.itemgetter("estimated_tokens"), reverse=True)

    table = Table(
        title=f"File Metrics — {directory}", show_header=True, header_style="bold cyan"
    )
    table.add_column("File", min_width=50)
    table.add_column("Lines", justify="right", min_width=8)
    table.add_column("Chars", justify="right", min_width=10)
    table.add_column("Est. Tokens", justify="right", min_width=12)

    shown = all_metrics[:top]
    for m in shown:
        rel_path = (
            Path(str(m["path"])).relative_to(directory)
            if directory in Path(str(m["path"])).parents
            else Path(str(m["path"]))
        )
        table.add_row(
            str(rel_path),
            f"{m['lines']:,}",
            f"{m['chars']:,}",
            f"{m['estimated_tokens']:,}",
        )

    console.print(table)

    total_tokens = sum(int(m["estimated_tokens"]) for m in all_metrics)
    console.print(
        f"\n[bold]Total:[/bold] {len(md_files)} files, ~{total_tokens:,} estimated tokens"
    )
    if len(all_metrics) > top:
        console.print(f"[dim](showing top {top} of {len(all_metrics)} files)[/dim]")


if __name__ == "__main__":
    app()
