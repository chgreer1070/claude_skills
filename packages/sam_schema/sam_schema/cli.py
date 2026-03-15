"""Typer CLI for SAM task/plan operations.

Provides the ``sam`` command with subcommands for reading tasks, updating
status, listing ready tasks, and showing plan progress.

Usage::

    sam read P1/T3
    sam state P1/T3 complete
    sam ready P1
    sam status P1
    sam migrate P1
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

from sam_schema.core.addressing import AddressingError, parse_address, resolve_plan_address
from sam_schema.core.models import TaskStatus
from sam_schema.core.query import get_plan_status, get_ready_tasks, get_task, load_plan, update_status
from sam_schema.readers.detect import FormatDetectionError
from sam_schema.writers.yaml_writer import write_plan

app = typer.Typer(name="sam", help="SAM task/plan file interface.", no_args_is_help=True)

_OUTPUT_FORMATS = ("json", "yaml", "rich")


def _err(msg: str, exit_code: int = 1) -> NoReturn:
    """Print an error message to stderr and exit.

    Args:
        msg: Human-readable error message.
        exit_code: Process exit code (1 for user errors, 2 for internal errors).
    """
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(exit_code)


def _resolve_plan(address_part: str, plan_dir: Path) -> Path:
    """Resolve the plan portion of an address to a filesystem path.

    Args:
        address_part: Plan address component (e.g., ``"1"``, ``"auth-system"``).
        plan_dir: Directory to search for plan files.

    Returns:
        Resolved path to the plan file or directory.

    Raises:
        SystemExit(1): If the address cannot be resolved or the directory is missing.
    """
    try:
        return resolve_plan_address(address_part, plan_dir)
    except FileNotFoundError as exc:
        _err(str(exc))
    except AddressingError as exc:
        _err(str(exc))


def _output_json(data: object) -> None:
    """Print ``data`` as formatted JSON to stdout.

    Args:
        data: Any JSON-serializable object.
    """
    typer.echo(json.dumps(data, indent=2, default=str))


def _output_yaml(data: object) -> None:
    """Print ``data`` as YAML to stdout.

    Args:
        data: Any YAML-serializable object.
    """
    y = YAML()
    y.default_flow_style = False
    buf = io.StringIO()
    y.dump(data, buf)
    typer.echo(buf.getvalue(), nl=False)


def _output_rich_task(task_data: dict[str, object]) -> None:
    """Print task fields as a Rich table.

    Args:
        task_data: Task dict from ``model_dump(mode="json")``.
    """
    console = Console()
    table = Table(title=str(task_data.get("title", "")), show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, value in task_data.items():
        if value is not None and value not in ("", []):
            table.add_row(str(key), str(value))

    console.print(table)


def _output_rich_status(status_data: dict[str, object]) -> None:
    """Print plan status as Rich tables.

    Args:
        status_data: PlanStatus dict from ``model_dump(mode="json")``.
    """
    console = Console()

    feature = str(status_data.get("feature", ""))
    total = status_data.get("total_tasks", 0)
    completion = status_data.get("completion_pct", 0.0)
    has_cycles = status_data.get("has_cycles", False)

    meta = Table(title=f"Plan: {feature}", show_header=False)
    meta.add_column("Field", style="cyan")
    meta.add_column("Value", style="green")
    meta.add_row("Total tasks", str(total))
    meta.add_row("Completion", f"{float(completion):.1f}%")  # type: ignore[arg-type]
    meta.add_row("Has cycles", str(has_cycles))
    console.print(meta)

    raw_by_status = status_data.get("by_status")
    by_status: dict[str, int] = raw_by_status if isinstance(raw_by_status, dict) else {}  # type: ignore[assignment]
    if by_status:
        st_table = Table(title="By Status", show_header=True, header_style="bold")
        st_table.add_column("Status", style="cyan")
        st_table.add_column("Count", style="green", justify="right")
        for s, count in by_status.items():
            st_table.add_row(str(s), str(count))
        console.print(st_table)

    raw_ready = status_data.get("ready_tasks")
    ready_list: list[str] = [str(t) for t in raw_ready] if isinstance(raw_ready, list) else []
    if ready_list:
        console.print(f"Ready tasks: {', '.join(ready_list)}")


@app.command()
def read(
    address: Annotated[str, typer.Argument(help="Task address: P{plan}/T{task}")],
    plan_dir: Annotated[Path, typer.Option("--plan-dir", help="Plan directory")] = Path("plan"),
    output_format: Annotated[str, typer.Option("--format", help="Output format: json|yaml|rich")] = "json",
) -> None:
    """Read a task and print its fields.

    Args:
        address: Task address in ``P{N}/T{M}`` format.
        plan_dir: Directory to search for plan files.
        output_format: Output serialization format.
    """
    if output_format not in _OUTPUT_FORMATS:
        _err(f"Invalid format '{output_format}'. Must be one of: {', '.join(_OUTPUT_FORMATS)}")

    try:
        plan_ref, task_ref = parse_address(address)
    except ValueError as exc:
        _err(str(exc))

    if task_ref is None:
        _err(f"Address '{address}' does not include a task component (expected P{{N}}/T{{M}})")

    plan_path = _resolve_plan(plan_ref, plan_dir)
    task_id = f"T{task_ref}" if task_ref.isdigit() else task_ref

    try:
        task = get_task(plan_path, task_id)
    except FileNotFoundError as exc:
        _err(str(exc))
    except KeyError as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    data = task.model_dump(mode="json", by_alias=True, exclude_none=True)

    if output_format == "json":
        _output_json(data)
    elif output_format == "yaml":
        _output_yaml(data)
    else:
        _output_rich_task(data)


@app.command()
def state(
    address: Annotated[str, typer.Argument(help="Task address: P{plan}/T{task}")],
    new_status: Annotated[str, typer.Argument(help="New status value")],
    plan_dir: Annotated[Path, typer.Option("--plan-dir", help="Plan directory")] = Path("plan"),
) -> None:
    """Update a task's status.

    Args:
        address: Task address in ``P{N}/T{M}`` format.
        new_status: New status string (e.g., ``complete``, ``in-progress``).
        plan_dir: Directory to search for plan files.
    """
    try:
        plan_ref, task_ref = parse_address(address)
    except ValueError as exc:
        _err(str(exc))

    if task_ref is None:
        _err(f"Address '{address}' does not include a task component (expected P{{N}}/T{{M}})")

    try:
        parsed_status = TaskStatus(new_status)
    except ValueError:
        valid = ", ".join(str(s) for s in TaskStatus)
        _err(f"Invalid status '{new_status}'. Must be one of: {valid}")

    plan_path = _resolve_plan(plan_ref, plan_dir)
    task_id = f"T{task_ref}" if task_ref.isdigit() else task_ref

    try:
        old_task = get_task(plan_path, task_id)
    except FileNotFoundError as exc:
        _err(str(exc))
    except KeyError as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    old_status = old_task.status

    try:
        updated_task = update_status(plan_path, task_id, parsed_status)
    except FileNotFoundError as exc:
        _err(str(exc))
    except (KeyError, ValueError) as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    typer.echo(f"Task {task_id}: {old_status} -> {updated_task.status}")


@app.command()
def ready(
    plan_address: Annotated[str, typer.Argument(help="Plan address: P{plan}")],
    plan_dir: Annotated[Path, typer.Option("--plan-dir", help="Plan directory")] = Path("plan"),
) -> None:
    """List tasks ready for dispatch.

    Args:
        plan_address: Plan address in ``P{N}`` format.
        plan_dir: Directory to search for plan files.
    """
    try:
        plan_ref, _ = parse_address(plan_address)
    except ValueError as exc:
        _err(str(exc))

    plan_path = _resolve_plan(plan_ref, plan_dir)

    try:
        tasks = get_ready_tasks(plan_path)
    except FileNotFoundError as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    data = [t.model_dump(mode="json", by_alias=True, exclude_none=True) for t in tasks]
    _output_json(data)


@app.command()
def status(
    plan_address: Annotated[str, typer.Argument(help="Plan address: P{plan}")],
    plan_dir: Annotated[Path, typer.Option("--plan-dir", help="Plan directory")] = Path("plan"),
    output_format: Annotated[str, typer.Option("--format", help="Output format: json|rich")] = "json",
) -> None:
    """Show plan-level progress summary.

    Args:
        plan_address: Plan address in ``P{N}`` format.
        plan_dir: Directory to search for plan files.
        output_format: Output serialization format (json or rich).
    """
    try:
        plan_ref, _ = parse_address(plan_address)
    except ValueError as exc:
        _err(str(exc))

    plan_path = _resolve_plan(plan_ref, plan_dir)

    try:
        plan_status = get_plan_status(plan_path)
    except FileNotFoundError as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    data = plan_status.model_dump(mode="json")

    if output_format == "rich":
        _output_rich_status(data)
    else:
        _output_json(data)


@app.command()
def migrate(
    plan_address: Annotated[str, typer.Argument(help="Plan address: P{plan}")],
    plan_dir: Annotated[Path, typer.Option("--plan-dir", help="Plan directory")] = Path("plan"),
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview changes without writing")] = False,
) -> None:
    """Migrate a legacy or YAML-frontmatter plan to canonical pure-YAML format.

    Args:
        plan_address: Plan address in ``P{N}`` format.
        plan_dir: Directory to search for plan files.
        dry_run: If ``True``, print what would change without writing to disk.
    """
    try:
        plan_ref, _ = parse_address(plan_address)
    except ValueError as exc:
        _err(str(exc))

    plan_path = _resolve_plan(plan_ref, plan_dir)

    try:
        result = load_plan(plan_path)
    except FileNotFoundError as exc:
        _err(str(exc))
    except FormatDetectionError as exc:
        _err(str(exc), exit_code=2)

    source_format = result.source_format
    plan = result.plan

    # Determine output path: always write to .yaml extension alongside source
    output_path = plan_path if plan_path.is_dir() else plan_path.with_suffix(".yaml")

    if dry_run:
        typer.echo(f"Would migrate: {plan_path}")
        typer.echo(f"  Source format: {source_format}")
        typer.echo(f"  Output path:   {output_path}")
        typer.echo(f"  Tasks:         {len(plan.tasks)}")
        typer.echo(f"  Schema gaps:   {len(result.gaps)}")
        if result.gaps:
            for gap in result.gaps:
                typer.echo(f"    [{gap.task_id}] {gap.field_name}: {gap.gap_type}")
        return

    try:
        written = write_plan(plan, output_path)
    except (ValueError, OSError) as exc:
        _err(str(exc), exit_code=2)

    typer.echo(f"Migrated {plan_path} -> {written}")
    typer.echo(f"  Source format: {source_format}")
    typer.echo(f"  Tasks written: {len(plan.tasks)}")


if __name__ == "__main__":  # pragma: no cover
    app()
