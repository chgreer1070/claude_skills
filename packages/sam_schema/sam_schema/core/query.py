"""Query layer for SAM task/plan files.

High-level functions for loading, querying, and updating plans. All operations
route through the format detection and reader pipeline, then delegate writes to
the YAML writer. This is the primary API consumed by the CLI and MCP server.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sam_schema.core.dependencies import DependencyGraph
from sam_schema.core.models import Plan, PlanStatus, ReadResult, Task, TaskStatus
from sam_schema.readers.detect import read_plan
from sam_schema.readers.normalize import normalize_plan
from sam_schema.writers.yaml_writer import update_fields

if TYPE_CHECKING:
    from pathlib import Path


def load_plan(plan_path: Path) -> ReadResult:
    """Load a plan from any supported format.

    Delegates to ``readers.detect.read_plan`` for format detection and reading,
    then normalizes to Pydantic models via ``readers.normalize.normalize_plan``.

    Args:
        plan_path: Path to a task/plan file or directory.

    Returns:
        A ``ReadResult`` containing the parsed ``Plan`` and any ``SchemaGap``
        records for non-canonical fields.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
        FormatDetectionError: If the file format cannot be identified.
    """
    plan_meta, task_dicts, fmt = read_plan(plan_path)
    return normalize_plan(plan_meta, task_dicts, fmt, plan_path)


def get_task(plan_path: Path, task_id: str) -> Task:
    """Get a single task by ID from a plan file.

    Args:
        plan_path: Path to the plan file or directory.
        task_id: Task ID to retrieve (e.g., ``"T1"``).

    Returns:
        The matching ``Task`` model.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
        KeyError: If no task with ``task_id`` is found in the plan.
    """
    result = load_plan(plan_path)
    for task in result.plan.tasks:
        if task.id == task_id:
            return task
    msg = f"Task '{task_id}' not found in plan '{plan_path}'"
    raise KeyError(msg)


def list_tasks(plan_path: Path) -> list[Task]:
    """List all tasks in a plan.

    Args:
        plan_path: Path to the plan file or directory.

    Returns:
        All ``Task`` models in the plan, in file order.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
    """
    result = load_plan(plan_path)
    return result.plan.tasks


def get_ready_tasks(plan_path: Path) -> list[Task]:
    """Get tasks that are ready for dispatch.

    A task is ready when its status is ``not-started`` and all tasks it
    depends on are in a terminal status (``complete``, ``deferred``,
    ``skipped``).

    Args:
        plan_path: Path to the plan file or directory.

    Returns:
        Tasks ready for dispatch, sorted by priority then numeric ID.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
    """
    result = load_plan(plan_path)
    graph = DependencyGraph(result.plan.tasks)
    return graph.get_ready_tasks()


def update_status(plan_path: Path, task_id: str, new_status: TaskStatus, timestamp_field: str | None = None) -> Task:
    """Update a task's status and optional timestamp.

    Uses ``writers.yaml_writer.update_field`` for atomic field updates that
    preserve comments and field order.

    Args:
        plan_path: Path to the plan file or directory.
        task_id: ID of the task to update (e.g., ``"T1"``).
        new_status: New status value.
        timestamp_field: If provided, also set this timestamp field to the
                         current UTC time (e.g., ``"started"``, ``"completed"``).

    Returns:
        The updated ``Task`` model after the write.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
        KeyError: If ``task_id`` is not found in the plan.
    """
    # Resolve to the concrete file path for the writer.
    file_path = _resolve_writable_path(plan_path, task_id)

    # Build all field updates and write them in a single read-modify-write cycle.
    field_updates: dict[str, str | int | list[str]] = {"status": str(new_status)}
    if timestamp_field is not None:
        field_updates[timestamp_field] = datetime.now(UTC).isoformat()
    update_fields(file_path, task_id, field_updates)

    return get_task(plan_path, task_id)


def get_plan_status(plan_path: Path) -> PlanStatus:
    """Get a plan-level status summary.

    Computes task counts by status, identifies ready and blocked tasks, and
    checks for dependency cycles.

    Args:
        plan_path: Path to the plan file or directory.

    Returns:
        A ``PlanStatus`` summary with counts, ready/blocked task lists,
        completion percentage, and cycle detection result.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
    """
    result = load_plan(plan_path)
    plan = result.plan
    graph = DependencyGraph(plan.tasks)

    by_status: dict[str, int] = {}
    for task in plan.tasks:
        by_status[task.status] = by_status.get(task.status, 0) + 1

    ready_tasks = [t.id for t in graph.get_ready_tasks()]
    blocked_tasks = [{t.id: missing_deps} for t, missing_deps in graph.get_blocked_tasks()]

    total = len(plan.tasks)
    complete_count = by_status.get(TaskStatus.COMPLETE, 0)
    completion_pct = (complete_count / total * 100.0) if total > 0 else 0.0

    return PlanStatus(
        feature=plan.feature,
        total_tasks=total,
        by_status=by_status,
        ready_tasks=ready_tasks,
        blocked_tasks=blocked_tasks,
        completion_pct=completion_pct,
        has_cycles=graph.has_cycles(),
    )


def claim_task(plan_path: Path, task_id: str) -> Task:
    """Atomically claim a task by transitioning it to ``in-progress``.

    Guards against double-claiming by verifying the task is currently
    ``not-started`` before updating. Raises if the task is already claimed
    or in a terminal state.

    Args:
        plan_path: Path to the plan file or directory.
        task_id: ID of the task to claim.

    Returns:
        The updated ``Task`` model with status ``in-progress`` and ``started``
        timestamp set.

    Raises:
        FileNotFoundError: If ``plan_path`` does not exist.
        KeyError: If ``task_id`` is not found.
        ValueError: If the task is not in ``not-started`` status.
    """
    task = get_task(plan_path, task_id)
    if task.status != TaskStatus.NOT_STARTED:
        msg = f"Cannot claim task '{task_id}': expected status 'not-started' but found '{task.status}'."
        raise ValueError(msg)

    return update_status(plan_path, task_id, TaskStatus.IN_PROGRESS, timestamp_field="started")


def _resolve_writable_path(plan_path: Path, task_id: str) -> Path:
    """Resolve the concrete YAML file path that contains ``task_id``.

    For a single ``.yaml`` file, returns ``plan_path`` directly.
    For a directory layout, searches ``task-{task_id}.yaml`` inside it.

    Args:
        plan_path: Plan path as provided by the caller.
        task_id: Task ID whose file should be located.

    Returns:
        Path to the ``.yaml`` file containing the task.

    Raises:
        FileNotFoundError: If the resolved path does not exist.
        KeyError: If no file containing ``task_id`` can be found in a
                  directory layout.
    """
    if plan_path.is_file():
        return plan_path

    # Directory layout: look for per-task file first
    per_task = plan_path / f"task-{task_id}.yaml"
    if per_task.exists():
        return per_task

    # Fall back to plan.yaml (tasks embedded in plan file)
    plan_yaml = plan_path / "plan.yaml"
    if plan_yaml.exists():
        return plan_yaml

    msg = f"Cannot find writable file for task '{task_id}' in directory '{plan_path}'"
    raise KeyError(msg)


# Re-export Plan for callers that only need the plan model
__all__ = [
    "Plan",
    "claim_task",
    "get_plan_status",
    "get_ready_tasks",
    "get_task",
    "list_tasks",
    "load_plan",
    "update_status",
]
