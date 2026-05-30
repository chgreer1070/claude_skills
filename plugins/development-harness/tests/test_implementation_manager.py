"""Behavioral tests for implementation_manager.get_ready_tasks().

Regression coverage for the dependency-satisfaction path.

Regression: commit 806e945f fixed a case-sensitivity bug where
_SUCCESSFUL_STATUSES membership check always returned False because
TaskStatus enum values are uppercase (e.g. "COMPLETE") but the comparison
operated on lowercased strings.  These tests guard against recurrence.
"""

from __future__ import annotations

from implementation_manager import Task, TaskPriority, TaskStatus, get_ready_tasks


def _task(task_id: str, status: TaskStatus, dependencies: list[str] | None = None, name: str | None = None) -> Task:
    """Minimal Task factory for test fixtures."""
    return Task(
        id=task_id,
        name=name or f"Task {task_id}",
        status=status,
        dependencies=dependencies or [],
        priority=TaskPriority.MEDIUM,
    )


# ---------------------------------------------------------------------------
# Dependency-satisfaction path — the regression guard
# ---------------------------------------------------------------------------


class TestGetReadyTasksDependencySatisfaction:
    """get_ready_tasks() must treat COMPLETE, DEFERRED, and SKIPPED deps as satisfied."""

    def test_all_deps_complete_returns_task_as_ready(self) -> None:
        """Task whose dependency is COMPLETE is returned as ready."""
        dep = _task("T1", TaskStatus.COMPLETE)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent in result

    def test_all_deps_deferred_returns_task_as_ready(self) -> None:
        """Task whose dependency is DEFERRED is returned as ready."""
        dep = _task("T1", TaskStatus.DEFERRED)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent in result

    def test_all_deps_skipped_returns_task_as_ready(self) -> None:
        """Task whose dependency is SKIPPED is returned as ready."""
        dep = _task("T1", TaskStatus.SKIPPED)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent in result

    def test_dep_in_progress_blocks_dependent_task(self) -> None:
        """Task whose dependency is IN_PROGRESS is NOT returned as ready."""
        dep = _task("T1", TaskStatus.IN_PROGRESS)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent not in result

    def test_no_dependencies_returns_task_as_ready(self) -> None:
        """Task with no dependencies is ready for execution."""
        standalone = _task("T1", TaskStatus.NOT_STARTED, dependencies=[])

        result = get_ready_tasks([standalone])

        assert standalone in result

    # -----------------------------------------------------------------------
    # Additional correctness assertions
    # -----------------------------------------------------------------------

    def test_dep_not_started_blocks_dependent_task(self) -> None:
        """Task whose dependency is NOT_STARTED is NOT returned as ready."""
        dep = _task("T1", TaskStatus.NOT_STARTED)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent not in result

    def test_dep_blocked_blocks_dependent_task(self) -> None:
        """Task whose dependency is BLOCKED is NOT returned as ready."""
        dep = _task("T1", TaskStatus.BLOCKED)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent not in result

    def test_dep_failed_blocks_dependent_task(self) -> None:
        """FAILED is not a satisfying status — downstream tasks must not be dispatched."""
        dep = _task("T1", TaskStatus.FAILED)
        dependent = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])

        result = get_ready_tasks([dep, dependent])

        assert dependent not in result

    def test_mixed_deps_all_satisfied_returns_ready(self) -> None:
        """Task with multiple deps — each in a different satisfying status — is ready."""
        dep_complete = _task("T1", TaskStatus.COMPLETE)
        dep_deferred = _task("T2", TaskStatus.DEFERRED)
        dep_skipped = _task("T3", TaskStatus.SKIPPED)
        dependent = _task("T4", TaskStatus.NOT_STARTED, dependencies=["T1", "T2", "T3"])

        result = get_ready_tasks([dep_complete, dep_deferred, dep_skipped, dependent])

        assert dependent in result

    def test_mixed_deps_one_unsatisfied_blocks_task(self) -> None:
        """Task is blocked if even one dependency is not in a satisfying status."""
        dep_complete = _task("T1", TaskStatus.COMPLETE)
        dep_in_progress = _task("T2", TaskStatus.IN_PROGRESS)
        dependent = _task("T3", TaskStatus.NOT_STARTED, dependencies=["T1", "T2"])

        result = get_ready_tasks([dep_complete, dep_in_progress, dependent])

        assert dependent not in result

    def test_already_in_progress_task_excluded(self) -> None:
        """Tasks that are already IN_PROGRESS are not in the ready list."""
        running = _task("T1", TaskStatus.IN_PROGRESS, dependencies=[])

        result = get_ready_tasks([running])

        assert running not in result

    def test_complete_task_excluded_from_ready_list(self) -> None:
        """Completed tasks are not returned as ready — they are already done."""
        done = _task("T1", TaskStatus.COMPLETE, dependencies=[])

        result = get_ready_tasks([done])

        assert done not in result

    def test_empty_task_list_returns_empty(self) -> None:
        """Empty input returns empty list without error."""
        result = get_ready_tasks([])

        assert result == []

    def test_only_ready_tasks_are_returned(self) -> None:
        """Result contains exactly the tasks that satisfy the ready criteria."""
        dep = _task("T1", TaskStatus.COMPLETE)
        ready = _task("T2", TaskStatus.NOT_STARTED, dependencies=["T1"])
        blocked = _task("T3", TaskStatus.NOT_STARTED, dependencies=["T2"])  # T2 not done

        result = get_ready_tasks([dep, ready, blocked])

        assert result == [ready]
