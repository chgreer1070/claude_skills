#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer>=0.21.0", "rich>=14.0.0"]
# ///
"""Link Checker — validates markdown cross-references resolve to real files."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from pathlib import Path

app = typer.Typer(name="link-checker", help="Validate markdown cross-references resolve to real files")
console = Console()
err_console = Console(stderr=True)

# Matches [text](./path) and [text](../path) — relative links only
RELATIVE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((\.\.?/[^)]+)\)")


def _extract_links(content: str) -> list[tuple[int, str, str]]:
    """Extract (line_number, link_text, link_path) from markdown content.

    Returns:
        List of (line_number, link_text, link_path) tuples.
    """
    links = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        for match in RELATIVE_LINK_PATTERN.finditer(line):
            text = match.group(1)
            path = match.group(2)
            # Strip anchors (#section)
            path = path.split("#")[0]
            if path:
                links.append((line_num, text, path))
    return links


def _check_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Check all relative links in a single file.

    Returns:
        List of (line, text, broken_path) for broken links.
    """
    broken = []
    content = filepath.read_text(encoding="utf-8")
    links = _extract_links(content)
    file_dir = filepath.parent
    for line_num, text, link_path in links:
        target = (file_dir / link_path).resolve()
        if not target.exists():
            broken.append((line_num, text, link_path))
    return broken


@app.command()
def check(file: Annotated[Path, typer.Argument(help="Markdown file to check")]) -> None:
    """Check all relative [text](./path) links in a markdown file resolve to existing files."""
    if not file.exists():
        err_console.print(f"[red]ERROR[/red] File not found: {file}")
        raise typer.Exit(1)

    broken = _check_file(file)

    if not broken:
        console.print(f"[green]PASS[/green] {file} — all links resolve")
        raise typer.Exit(0)

    console.print(f"[red]FAIL[/red] {file} — {len(broken)} broken link(s):\n")
    for line_num, text, path in broken:
        console.print(f"  {file}:{line_num} — [{text}]({path})")

    raise typer.Exit(1)


@app.command(name="check-dir")
def check_dir(directory: Annotated[Path, typer.Argument(help="Directory to scan for .md files")]) -> None:
    """Check all .md files in a directory for broken relative links."""
    if not directory.is_dir():
        err_console.print(f"[red]ERROR[/red] Not a directory: {directory}")
        raise typer.Exit(1)

    md_files = sorted(directory.rglob("*.md"))
    if not md_files:
        console.print(f"[yellow]No .md files found in {directory}[/yellow]")
        raise typer.Exit(0)

    all_broken: list[tuple[Path, int, str, str]] = []
    for md_file in md_files:
        broken = _check_file(md_file)
        for line_num, text, path in broken:
            all_broken.append((md_file, line_num, text, path))

    if not all_broken:
        console.print(f"[green]PASS[/green] {len(md_files)} file(s) checked — all links resolve")
        raise typer.Exit(0)

    table = Table(title=f"Broken Links in {directory}", show_header=True, header_style="bold red")
    table.add_column("File", min_width=40)
    table.add_column("Line", justify="right", min_width=6)
    table.add_column("Link Text", min_width=20)
    table.add_column("Broken Path")

    for md_file, line_num, text, path in all_broken:
        table.add_row(str(md_file.relative_to(directory)), str(line_num), text, path)

    console.print(table)
    console.print(f"\n[red]FAIL[/red] {len(all_broken)} broken link(s) across {len(md_files)} file(s)")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
