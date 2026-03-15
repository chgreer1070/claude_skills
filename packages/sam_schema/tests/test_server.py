"""Tests for sam_schema.server — MCP tool functions.

Tests: All four MCP tools (sam_read, sam_state, sam_ready, sam_status).
How: Write real plan files to tmp_path, create a plan directory with
     tasks-{N}-{slug}.yaml naming so resolve_plan_address can find them,
     then call each MCP tool function directly and assert on returned dicts.
Why: server.py has zero test coverage; the tools are the primary interface
     used by Claude Code agents to query and mutate SAM plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sam_schema.core.models import Complexity, Plan, Priority, Task, TaskStatus
from sam_schema.server import sam_read, sam_ready, sam_state, sam_status
from sam_schema.writers.yaml_writer import write_plan

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_task(
    task_id: str,
    status: TaskStatus = TaskStatus.NOT_STARTED,
    dependencies: list[str] | None = None,
    priority: Priority = Priority.MEDIUM,
) -> Task:
    """Return a minimal Task for test use."""
    return Task(
        id=task_id,
        title=f"Task {task_id}",
        status=status,
        dependencies=dependencies or [],
        priority=priority,
        complexity=Complexity.MEDIUM,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def plan_dir(tmp_path: Path) -> Path:
    """Create a plan directory with a two-task plan file.

    Directory layout::

        tmp_path/
        └── plan/
            └── tasks-1-test-feature.yaml   (T1 complete, T2 depends on T1)

    Returns:
        Path to the plan directory (``tmp_path/plan``).
    """
    p_dir = tmp_path / "plan"
    p_dir.mkdir()

    tasks = [make_task("T1", status=TaskStatus.COMPLETE), make_task("T2", dependencies=["T1"])]
    plan = Plan(feature="test-feature", version="1.0", tasks=tasks)

    plan_file = p_dir / "tasks-1-test-feature.yaml"
    write_plan(plan, plan_file, force_single=True)
    return p_dir


@pytest.fixture
def plan_dir_str(plan_dir: Path) -> str:
    """Return plan directory as string (MCP tool signature accepts str)."""
    return str(plan_dir)


# ---------------------------------------------------------------------------
# sam_read
# ---------------------------------------------------------------------------


def test_sam_read_existing_task_returns_task_fields(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_read returns task fields dict for an existing task.

    Tests: sam_read happy path.
    How: Address 'P1', task 'T1' on a plan dir with tasks-1-test-feature.yaml.
    Why: sam_read is the primary read tool used by agents to inspect task state.
    """
    # Arrange — plan_dir fixture provides tasks-1-test-feature.yaml

    # Act
    result = sam_read(plan="P1", task="T1", plan_dir=plan_dir_str)

    # Assert
    assert "error" not in result
    assert result["id"] == "T1"
    assert result["status"] == "complete"


def test_sam_read_returns_dict_with_all_required_fields(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_read result contains 'id', 'title', and 'status' keys.

    Tests: Return structure of sam_read.
    How: Call sam_read for T2 and check key presence.
    Why: Agents rely on these keys being present to make routing decisions.
    """
    # Act
    result = sam_read(plan="P1", task="T2", plan_dir=plan_dir_str)

    # Assert
    assert "error" not in result
    assert "id" in result
    assert "title" in result
    assert "status" in result


def test_sam_read_missing_task_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_read returns {'error': ...} for a task ID that does not exist.

    Tests: sam_read error handling for missing task.
    How: Request task 'T99' which is not in the plan.
    Why: MCP tools must never raise exceptions; they return error dicts instead.
    """
    # Act
    result = sam_read(plan="P1", task="T99", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result
    assert "T99" in result["error"]


def test_sam_read_invalid_plan_address_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_read returns {'error': ...} for an unresolvable plan address.

    Tests: sam_read error handling for invalid plan address.
    How: Request plan 'P999' which has no matching file in the directory.
    Why: Agents must be able to detect addressing failures from the return value.
    """
    # Act
    result = sam_read(plan="P999", task="T1", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


def test_sam_read_nonexistent_plan_dir_returns_error_dict(tmp_path: Path) -> None:
    """sam_read returns {'error': ...} when plan_dir does not exist.

    Tests: sam_read error handling for missing plan directory.
    How: Pass a path that does not exist.
    Why: The tool must handle filesystem errors gracefully without raising.
    """
    # Act
    result = sam_read(plan="P1", task="T1", plan_dir=str(tmp_path / "missing"))

    # Assert
    assert "error" in result


# ---------------------------------------------------------------------------
# sam_state
# ---------------------------------------------------------------------------


def test_sam_state_updates_task_status(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_state writes new status and returns updated task.

    Tests: sam_state happy path for status update.
    How: Transition T2 from not-started to in-progress.
    Why: sam_state is the mutation tool agents use to advance task lifecycle.
    """
    # Act
    result = sam_state(plan="P1", task="T2", status="in-progress", plan_dir=plan_dir_str)

    # Assert
    assert "error" not in result
    assert result["id"] == "T2"
    assert result["status"] == "in-progress"


def test_sam_state_accepts_all_valid_status_values(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_state accepts every value from the TaskStatus enum.

    Tests: sam_state with each canonical status string.
    How: Cycle through valid statuses on T2.
    Why: Agents use all status values during the task lifecycle.
    """
    for status_str in ("in-progress", "blocked", "complete", "deferred", "skipped", "not-started"):
        result = sam_state(plan="P1", task="T2", status=status_str, plan_dir=plan_dir_str)
        assert "error" not in result, f"Unexpected error for status '{status_str}': {result}"
        assert result["status"] == status_str


def test_sam_state_invalid_status_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_state returns {'error': ...} for an unrecognized status string.

    Tests: sam_state error handling for invalid status values.
    How: Pass 'typo-status' which is not in TaskStatus.
    Why: Prevents agents from writing garbage status values that would corrupt
    plan files and trigger silent re-dispatch of completed tasks.
    """
    # Act
    result = sam_state(plan="P1", task="T2", status="typo-status", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


def test_sam_state_missing_task_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_state returns {'error': ...} when the task ID is not found.

    Tests: sam_state error handling for missing task.
    How: Attempt to update status on 'T99' which does not exist.
    Why: Tools must never raise; error dicts allow callers to inspect failures.
    """
    # Act
    result = sam_state(plan="P1", task="T99", status="complete", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


def test_sam_state_invalid_plan_address_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_state returns {'error': ...} for an unresolvable plan address.

    Tests: sam_state error handling for invalid plan address.
    How: Address 'P999' does not match any file in the plan directory.
    Why: Addressing failures must surface via return value, not exceptions.
    """
    # Act
    result = sam_state(plan="P999", task="T1", status="complete", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


# ---------------------------------------------------------------------------
# sam_ready
# ---------------------------------------------------------------------------


def test_sam_ready_returns_ready_tasks_list(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_ready returns tasks whose dependencies are all complete.

    Tests: sam_ready happy path.
    How: T1 is complete, T2 depends on T1 — T2 is the only ready task.
    Why: sam_ready is the tool agents poll to find their next task to execute.
    """
    # Act
    result = sam_ready(plan="P1", plan_dir=plan_dir_str)

    # Assert
    assert "error" not in result
    assert "ready_tasks" in result
    assert "count" in result
    assert result["count"] == 1
    assert result["ready_tasks"][0]["id"] == "T2"


def test_sam_ready_count_matches_ready_tasks_length(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_ready 'count' field matches len(ready_tasks).

    Tests: sam_ready return value consistency.
    How: Check count == len(ready_tasks).
    Why: Callers may use count for quick checks before iterating the list.
    """
    # Act
    result = sam_ready(plan="P1", plan_dir=plan_dir_str)

    # Assert
    assert result["count"] == len(result["ready_tasks"])


def test_sam_ready_invalid_plan_address_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_ready returns {'error': ...} for an unresolvable plan address.

    Tests: sam_ready error handling.
    How: Pass 'P999' which does not match any file.
    Why: Addressing failures must be surfaced as error dicts.
    """
    # Act
    result = sam_ready(plan="P999", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


def test_sam_ready_all_complete_plan_returns_empty_list(tmp_path: Path) -> None:
    """sam_ready returns empty ready_tasks when all tasks are complete.

    Tests: sam_ready with no ready tasks.
    How: Create a plan where all tasks are COMPLETE.
    Why: Agents must handle the empty case to know the plan is finished.
    """
    # Arrange
    p_dir = tmp_path / "plan"
    p_dir.mkdir()

    tasks = [
        make_task("T1", status=TaskStatus.COMPLETE),
        make_task("T2", status=TaskStatus.COMPLETE, dependencies=["T1"]),
    ]
    plan = Plan(feature="done-feature", version="1.0", tasks=tasks)
    write_plan(plan, p_dir / "tasks-1-done-feature.yaml", force_single=True)

    # Act
    result = sam_ready(plan="P1", plan_dir=str(p_dir))

    # Assert
    assert "error" not in result
    assert result["count"] == 0
    assert result["ready_tasks"] == []


# ---------------------------------------------------------------------------
# sam_status
# ---------------------------------------------------------------------------


def test_sam_status_returns_plan_summary(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_status returns a plan-level progress summary dict.

    Tests: sam_status happy path.
    How: Call sam_status on a two-task plan (T1 complete, T2 not-started).
    Why: sam_status gives agents and orchestrators an overview of plan progress.
    """
    # Act
    result = sam_status(plan="P1", plan_dir=plan_dir_str)

    # Assert
    assert "error" not in result
    assert result["total_tasks"] == 2
    assert "by_status" in result
    assert "ready_tasks" in result
    assert "completion_pct" in result
    assert "has_cycles" in result


def test_sam_status_completion_pct_reflects_completed_tasks(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_status completion_pct equals completed/total * 100.

    Tests: sam_status completion percentage calculation.
    How: T1 is complete out of 2 tasks — expected 50.0%.
    Why: Callers use completion_pct to report plan progress.
    """
    # Act
    result = sam_status(plan="P1", plan_dir=plan_dir_str)

    # Assert
    assert result["completion_pct"] == pytest.approx(50.0)


def test_sam_status_by_status_contains_complete_and_not_started(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_status by_status dict reflects actual task statuses.

    Tests: sam_status by_status aggregation.
    How: Verify complete=1, not-started=1 for the two-task fixture plan.
    Why: Agents and dashboards rely on by_status for per-state counts.
    """
    # Act
    result = sam_status(plan="P1", plan_dir=plan_dir_str)

    # Assert
    by_status = result["by_status"]
    assert by_status.get("complete", 0) == 1
    assert by_status.get("not-started", 0) == 1


def test_sam_status_invalid_plan_address_returns_error_dict(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_status returns {'error': ...} for an unresolvable plan address.

    Tests: sam_status error handling.
    How: Pass 'P999' which does not match any file.
    Why: Tools must return error dicts, not raise exceptions.
    """
    # Act
    result = sam_status(plan="P999", plan_dir=plan_dir_str)

    # Assert
    assert "error" in result


def test_sam_status_has_cycles_false_for_acyclic_plan(plan_dir: Path, plan_dir_str: str) -> None:
    """sam_status has_cycles is False for an acyclic dependency graph.

    Tests: sam_status cycle detection reporting.
    How: The fixture plan (T1 <- T2) has no cycles.
    Why: has_cycles must be accurate so agents do not treat valid plans as broken.
    """
    # Act
    result = sam_status(plan="P1", plan_dir=plan_dir_str)

    # Assert
    assert result["has_cycles"] is False


def test_sam_status_has_cycles_true_for_cyclic_plan(tmp_path: Path) -> None:
    """sam_status has_cycles is True when the dependency graph contains a cycle.

    Tests: sam_status cycle detection with a real cyclic plan.
    How: Create T1 -> T2 -> T1 (cycle), write to tmp dir, call sam_status.
    Why: Agents must detect cycles to avoid infinite dispatch loops.
    """
    # Arrange
    p_dir = tmp_path / "plan"
    p_dir.mkdir()

    # Build a cyclic plan: T1 depends on T2 and T2 depends on T1
    tasks = [
        Task(
            id="T1",
            title="Task 1",
            status=TaskStatus.NOT_STARTED,
            dependencies=["T2"],
            complexity=Complexity.MEDIUM,
            priority=Priority.MEDIUM,
        ),
        Task(
            id="T2",
            title="Task 2",
            status=TaskStatus.NOT_STARTED,
            dependencies=["T1"],
            complexity=Complexity.MEDIUM,
            priority=Priority.MEDIUM,
        ),
    ]
    plan = Plan(feature="cyclic-feature", version="1.0", tasks=tasks)
    write_plan(plan, p_dir / "tasks-1-cyclic-feature.yaml", force_single=True)

    # Act
    result = sam_status(plan="P1", plan_dir=str(p_dir))

    # Assert
    assert "error" not in result
    assert result["has_cycles"] is True
