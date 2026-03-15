"""FastMCP server for SAM task/plan operations.

Exposes the same operations as the Typer CLI as MCP tools for use by
Claude Code agents and other MCP clients.

Tools:
    sam_read    — Read a task by address
    sam_state   — Update a task's status
    sam_ready   — List ready tasks for a plan
    sam_status  — Get plan-level progress summary
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from sam_schema.core.addressing import resolve_plan_address
from sam_schema.core.models import TaskStatus
from sam_schema.core.query import get_plan_status, get_ready_tasks, get_task, update_status

mcp: FastMCP = FastMCP("sam")


@mcp.tool()
def sam_read(
    plan: Annotated[str, Field(description="Plan address (e.g., 'P1' or slug)")],
    task: Annotated[str, Field(description="Task ID (e.g., 'T3')")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Read a task by address and return its fields as a dict.

    Args:
        plan: Plan address component (numeric index or slug).
        task: Task ID component (e.g., ``T3``).
        plan_dir: Path to the directory containing plan files.

    Returns:
        Task fields as a JSON-serializable dict, or a dict with an ``error``
        key on failure.
    """
    try:
        plan_path = resolve_plan_address(plan, Path(plan_dir))
        result = get_task(plan_path, task)
        return result.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@mcp.tool()
def sam_state(
    plan: Annotated[str, Field(description="Plan address")],
    task: Annotated[str, Field(description="Task ID")],
    status: Annotated[str, Field(description="New status value")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Update a task's status.

    Args:
        plan: Plan address component.
        task: Task ID component.
        status: New status string (e.g., ``complete``, ``in-progress``).
        plan_dir: Path to the directory containing plan files.

    Returns:
        Updated task fields as a JSON-serializable dict, or a dict with an
        ``error`` key on failure.
    """
    try:
        new_status = TaskStatus(status)
        plan_path = resolve_plan_address(plan, Path(plan_dir))
        result = update_status(plan_path, task, new_status)
        return result.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@mcp.tool()
def sam_ready(
    plan: Annotated[str, Field(description="Plan address")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """List tasks ready for dispatch.

    Args:
        plan: Plan address component.
        plan_dir: Path to the directory containing plan files.

    Returns:
        Dict with ``ready_tasks`` list of task field dicts and ``count``, or
        a dict with an ``error`` key on failure.
    """
    try:
        plan_path = resolve_plan_address(plan, Path(plan_dir))
        tasks = get_ready_tasks(plan_path)
        return {"ready_tasks": [t.model_dump(mode="json") for t in tasks], "count": len(tasks)}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


@mcp.tool()
def sam_status(
    plan: Annotated[str, Field(description="Plan address")],
    plan_dir: Annotated[str, Field(description="Plan directory path")] = "plan",
) -> dict:
    """Get plan-level progress summary.

    Args:
        plan: Plan address component.
        plan_dir: Path to the directory containing plan files.

    Returns:
        ``PlanStatus`` fields as a JSON-serializable dict including
        ``total_tasks``, ``by_status``, ``ready_tasks``, ``blocked_tasks``,
        ``completion_pct``, and ``has_cycles``, or a dict with an ``error``
        key on failure.
    """
    try:
        plan_path = resolve_plan_address(plan, Path(plan_dir))
        result = get_plan_status(plan_path)
        return result.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
