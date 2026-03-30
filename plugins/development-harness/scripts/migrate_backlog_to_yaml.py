#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ruamel.yaml>=0.18.0",
#   "pydantic>=2.12.3",
#   "typer>=0.21.0",
#   "python-frontmatter>=1.1.0",
#   "gitpython>=3.1.0",
#   "pygithub>=2.8.1",
# ]
# ///
"""migrate_backlog_to_yaml — bulk migration of .md backlog files to .yaml format.

Each file is parsed, structured, round-trip verified, then atomically
replaced (.yaml written, .md deleted only after verification passes).

Usage
-----
    uv run plugins/development-harness/scripts/migrate_backlog_to_yaml.py --dry-run
    uv run plugins/development-harness/scripts/migrate_backlog_to_yaml.py
    uv run plugins/development-harness/scripts/migrate_backlog_to_yaml.py --backlog-dir /path/to/backlog
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Annotated

# Bootstrap: make the development-harness package importable from within the
# PEP 723 isolated environment.  The script lives at:
#   plugins/development-harness/scripts/migrate_backlog_to_yaml.py
# so parents[1] is plugins/development-harness/.
_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

import typer
from backlog_core.entry_blocks import parse_entries
from backlog_core.models import BacklogItem, GroomedData, Section
from backlog_core.parsing import extract_sections, parse_item_file
from backlog_core.yaml_io import load_item, load_item_text, save_item
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML, YAMLError

app = typer.Typer(
    name="migrate_backlog_to_yaml",
    help="Bulk migration of .md backlog files to pure YAML format.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

# Extracts the grooming date from "## Groomed (2026-03-15)" headings.
_GROOMED_DATE_RE = re.compile(r"## Groomed\s*\(([^)]*)\)")
# Extracts ### subsection names and their body text from a groomed section.
_GROOMED_SUBSECTION_RE = re.compile(r"### ([^\n]+)\n([\s\S]*?)(?=\n### |\Z)")


# ---------------------------------------------------------------------------
# Report dataclass
# ---------------------------------------------------------------------------


@dataclass
class MigrationReport:
    """Aggregate results from a migration run."""

    total_found: int = 0
    """Total .md files discovered in the backlog directory."""

    migrated: int = 0
    """Files successfully migrated to .yaml."""

    skipped: int = 0
    """Files skipped because they lack YAML frontmatter (not backlog items)."""

    errors: list[tuple[str, str]] = field(default_factory=list)
    """(file_path, error_message) pairs for every file that failed."""

    @property
    def error_count(self) -> int:
        """Number of migration failures."""
        return len(self.errors)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _has_frontmatter(text: str) -> bool:
    """Return True when text begins with a YAML frontmatter block (--- ... ---).

    Args:
        text: Raw file content.

    Returns:
        True if a frontmatter block is present.
    """
    if not text.startswith("---"):
        return False
    return "---" in text[3:]


def _parse_groomed_data(groomed_heading: str, groomed_body: str) -> GroomedData:
    """Parse a '## Groomed (date)' section into a GroomedData model.

    Args:
        groomed_heading: The full heading line, e.g. '## Groomed (2026-01-15)'.
        groomed_body: Content below the heading (### subsections).

    Returns:
        GroomedData with date and subsections populated.
    """
    date_match = _GROOMED_DATE_RE.match(groomed_heading)
    date = date_match.group(1).strip() if date_match else ""

    subsections: dict[str, str] = {}
    for m in _GROOMED_SUBSECTION_RE.finditer(groomed_body):
        subsections[m.group(1).strip()] = m.group(2).strip()

    return GroomedData(date=date, subsections=subsections)


def _build_sections(item: BacklogItem) -> dict[str, Section | GroomedData]:
    """Convert a legacy item's raw_body into typed Section / GroomedData objects.

    Walks every '## heading' block in raw_body:
    - '## Groomed …' blocks become GroomedData (date + ### subsections).
    - All other blocks become Section (list of Entry objects).

    Args:
        item: BacklogItem parsed from a legacy .md file (raw_body populated).

    Returns:
        Dict mapping heading string to Section or GroomedData.
    """
    if not item.raw_body:
        return {}

    raw_sections = extract_sections(item.raw_body)
    result: dict[str, Section | GroomedData] = {}

    for heading, body in raw_sections.items():
        if heading.startswith("## Groomed"):
            result[heading] = _parse_groomed_data(heading, body)
        else:
            entries = parse_entries(body, show="all", added_date=item.metadata.added or "0000-00-00")
            result[heading] = Section(entries=entries)

    return result


def _item_to_yaml_str(item: BacklogItem) -> str:
    """Serialise a BacklogItem to a YAML string without touching the filesystem.

    Args:
        item: BacklogItem to serialise.

    Returns:
        YAML-formatted string, using the same settings as yaml_io.save_item.
    """
    data = item.model_dump(exclude={"file_path", "skip"})
    yaml = YAML(typ="rt")
    yaml.default_flow_style = False
    yaml.width = 2147483647
    out = StringIO()
    yaml.dump(data, out)
    return out.getvalue()


def _collect_state(item: BacklogItem) -> dict[str, object]:
    """Collect verifiable state from a BacklogItem for round-trip comparison.

    Args:
        item: BacklogItem to inspect (may be either the pre-save or reloaded instance).

    Returns:
        Dict with:
          - entry_count: total Entry objects across all Section values
          - entry_ids: frozenset of non-empty Entry.id strings
          - groomed_keys: frozenset of GroomedData subsection names
    """
    entry_count = 0
    entry_ids: set[str] = set()
    groomed_keys: set[str] = set()

    for sec in item.sections.values():
        if isinstance(sec, Section):
            for e in sec.entries:
                entry_count += 1
                if e.id:
                    entry_ids.add(e.id)
        elif isinstance(sec, GroomedData):
            groomed_keys.update(sec.subsections.keys())

    return {"entry_count": entry_count, "entry_ids": frozenset(entry_ids), "groomed_keys": frozenset(groomed_keys)}


# ---------------------------------------------------------------------------
# Core migration functions
# ---------------------------------------------------------------------------


def migrate_file(md_path: Path, *, dry_run: bool = False) -> Path:
    """Migrate a single .md backlog file to .yaml format.

    Steps:
    1. Read source text from md_path.
    2. Parse via parse_item_file() (legacy .md path).
    3. Build typed sections from raw_body via extract_sections() / parse_entries()
       and extract_groomed_section subsections.
    4. Construct new BacklogItem with populated sections dict.
    5. Verify round-trip fidelity (entry count, entry ids, groomed subsection keys).
    6. Write .yaml and delete .md (omitted when dry_run=True).

    Args:
        md_path: Path to the source .md file.
        dry_run: When True, run all logic but do not write .yaml or delete .md.

    Returns:
        Path to the .yaml file (or where it would be written in dry_run mode).

    Raises:
        ValueError: When round-trip verification detects data loss.
        OSError: When file I/O fails.
    """
    text = md_path.read_text(encoding="utf-8")

    # Step 2: Parse legacy .md into BacklogItem
    legacy_item = parse_item_file(text, md_path)

    # Steps 3-4: Build structured sections and construct the new item
    sections = _build_sections(legacy_item)
    new_item = BacklogItem(
        title=legacy_item.title,
        description=legacy_item.description,
        type_=legacy_item.type_,
        section=legacy_item.section,
        metadata=legacy_item.metadata,
        sections=sections,
    )

    yaml_path = md_path.with_suffix(".yaml")
    orig_state = _collect_state(new_item)

    if dry_run:
        # Step 5 (dry-run): verify via in-memory serialise → deserialise
        yaml_str = _item_to_yaml_str(new_item)
        reloaded = load_item_text(yaml_str, yaml_path)
        reload_state = _collect_state(reloaded)

        if orig_state != reload_state:
            raise ValueError(
                f"Round-trip verification failed (dry-run).\n"
                f"  original state : {orig_state}\n"
                f"  reloaded state : {reload_state}"
            )
        return yaml_path

    # Step 5+6 (live): write yaml, verify from disk, then delete md
    save_item(new_item, yaml_path)

    reloaded = load_item(yaml_path)
    reload_state = _collect_state(reloaded)

    if orig_state != reload_state:
        # Delete the corrupted yaml — leave the .md intact for manual inspection
        yaml_path.unlink(missing_ok=True)
        raise ValueError(
            f"Round-trip verification failed — .yaml deleted, .md preserved.\n"
            f"  original state : {orig_state}\n"
            f"  reloaded state : {reload_state}"
        )

    md_path.unlink()

    return yaml_path


def migrate_all(backlog_dir: Path, *, dry_run: bool = False) -> MigrationReport:
    """Migrate all .md backlog item files in backlog_dir to .yaml.

    Files without YAML frontmatter (README.md, loose notes, etc.) are counted
    as skipped and left untouched.

    Args:
        backlog_dir: Directory containing .md backlog files.
        dry_run: When True, run full logic without writing or deleting files.

    Returns:
        MigrationReport with per-file outcomes.
    """
    report = MigrationReport()

    if not backlog_dir.exists():
        return report

    for md_path in sorted(backlog_dir.glob("*.md")):
        report.total_found += 1
        text = md_path.read_text(encoding="utf-8")

        if not _has_frontmatter(text):
            report.skipped += 1
            continue

        try:
            migrate_file(md_path, dry_run=dry_run)
            report.migrated += 1
        except (OSError, ValueError, KeyError, TypeError, AttributeError, YAMLError, ValidationError) as exc:
            report.errors.append((str(md_path), str(exc)))

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    backlog_dir: Annotated[
        Path,
        typer.Option("--backlog-dir", help="Directory containing .md backlog files to migrate.", show_default=True),
    ] = Path(".claude/backlog"),
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run/--no-dry-run", help=("Parse and verify without writing .yaml files or deleting .md files.")
        ),
    ] = False,
) -> None:
    """Migrate .md backlog files to pure YAML format.

    Each file is parsed, its sections structured, and round-trip fidelity verified
    before the original .md is removed.  Use --dry-run for a rehearsal pass.
    """
    mode_label = "[yellow]DRY RUN — no files will be written or deleted[/yellow]"
    if not dry_run:
        mode_label = "[green]LIVE — files will be written and originals deleted[/green]"

    console.print(f"\n:gear: Backlog migration: [bold]{backlog_dir}[/bold]")
    console.print(f"   Mode: {mode_label}\n")

    if not backlog_dir.exists():
        err_console.print(f"[red]Error:[/red] Directory not found: {backlog_dir}")
        raise typer.Exit(code=1)

    report = migrate_all(backlog_dir, dry_run=dry_run)

    table = Table(title="Migration Report", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("Total .md files found", str(report.total_found))
    table.add_row("Successfully migrated", str(report.migrated), style="green" if report.migrated else "")
    table.add_row("Skipped (no frontmatter)", str(report.skipped))
    table.add_row("Errors", str(report.error_count), style="red" if report.error_count else "")

    console.print(table)

    if report.errors:
        console.print("\n[red bold]:x: Errors:[/red bold]")
        for file_path, msg in report.errors:
            console.print(f"  [red]:x:[/red] {file_path}")
            # Indent the error message for readability
            for line in msg.splitlines():
                console.print(f"     {line}")
            console.print()
        raise typer.Exit(code=1)

    if dry_run:
        console.print("\n[yellow]:warning:  Dry run complete — no files modified.[/yellow]")
    else:
        console.print(f"\n[green]:white_check_mark: Done — {report.migrated} file(s) converted to YAML.[/green]")


if __name__ == "__main__":
    app()
