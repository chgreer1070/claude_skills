"""Tests for sam_schema.core.dependencies — dependency graph and cycle detection."""

from __future__ import annotations

from sam_schema.core.dependencies import DependencyGraph, _task_id_sort_key
from sam_schema.core.models import Complexity, Priority, Task, TaskStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_task(
    task_id: str,
    status: TaskStatus = TaskStatus.NOT_STARTED,
    dependencies: list[str] | None = None,
    priority: Priority = Priority.MEDIUM,
) -> Task:
    """Return a minimal Task with the given ID and optional dependencies."""
    return Task(
        id=task_id,
        title=f"Task {task_id}",
        status=status,
        dependencies=dependencies or [],
        priority=priority,
        complexity=Complexity.MEDIUM,
    )


# ---------------------------------------------------------------------------
# _task_id_sort_key unit tests
# ---------------------------------------------------------------------------


def test_task_id_sort_key_numeric_only_returns_correct_tuple() -> None:
    # Arrange / Act / Assert
    assert _task_id_sort_key("1") == (1, 0)


def test_task_id_sort_key_t_prefix_returns_correct_tuple() -> None:
    assert _task_id_sort_key("T5") == (5, 0)


def test_task_id_sort_key_with_minor_component_returns_correct_tuple() -> None:
    assert _task_id_sort_key("T2.3") == (2, 3)


def test_task_id_sort_key_non_matching_returns_zero_tuple() -> None:
    assert _task_id_sort_key("unknown") == (0, 0)


def test_task_id_sort_key_orders_correctly_in_sort() -> None:
    # Arrange
    ids = ["T10", "T2", "T1", "T3"]
    # Act
    sorted_ids = sorted(ids, key=_task_id_sort_key)
    # Assert
    assert sorted_ids == ["T1", "T2", "T3", "T10"]


# ---------------------------------------------------------------------------
# DependencyGraph.get_ready_tasks
# ---------------------------------------------------------------------------


def test_get_ready_tasks_no_dependencies_returns_all_not_started() -> None:
    # Arrange
    tasks = [make_task("T1"), make_task("T2")]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert
    assert {t.id for t in ready} == {"T1", "T2"}


def test_get_ready_tasks_with_complete_dep_returns_dependent_task() -> None:
    # Arrange
    tasks = [make_task("T1", status=TaskStatus.COMPLETE), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert
    assert len(ready) == 1
    assert ready[0].id == "T2"


def test_get_ready_tasks_with_not_started_dep_excludes_blocked_task() -> None:
    # Arrange
    tasks = [make_task("T1"), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert — only T1 is ready; T2 depends on not-yet-complete T1
    assert [t.id for t in ready] == ["T1"]


def test_get_ready_tasks_deferred_dep_satisfies_dependency() -> None:
    # Arrange
    tasks = [make_task("T1", status=TaskStatus.DEFERRED), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert — deferred is terminal, so T2 is ready
    assert [t.id for t in ready] == ["T2"]


def test_get_ready_tasks_skipped_dep_satisfies_dependency() -> None:
    # Arrange
    tasks = [make_task("T1", status=TaskStatus.SKIPPED), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert
    assert [t.id for t in ready] == ["T2"]


def test_get_ready_tasks_in_progress_dep_does_not_satisfy() -> None:
    # Arrange
    tasks = [make_task("T1", status=TaskStatus.IN_PROGRESS), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert — in-progress is not terminal
    assert ready == []


def test_get_ready_tasks_missing_dep_id_blocks_task() -> None:
    # Arrange — T2 depends on T99 which doesn't exist
    tasks = [make_task("T2", dependencies=["T99"])]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert
    assert ready == []


def test_get_ready_tasks_sorted_by_priority_then_id() -> None:
    # Arrange — T3 has higher priority (lower number) than T1
    tasks = [
        make_task("T1", priority=Priority.LOW),
        make_task("T3", priority=Priority.HIGH),
        make_task("T2", priority=Priority.LOW),
    ]
    graph = DependencyGraph(tasks)

    # Act
    ready = graph.get_ready_tasks()

    # Assert — T3 (priority=2) comes first, then T1/T2 by ID
    assert ready[0].id == "T3"
    assert ready[1].id == "T1"
    assert ready[2].id == "T2"


def test_get_ready_tasks_empty_task_list_returns_empty() -> None:
    # Arrange
    graph = DependencyGraph([])

    # Act / Assert
    assert graph.get_ready_tasks() == []


# ---------------------------------------------------------------------------
# DependencyGraph.has_cycles / get_cycles
# ---------------------------------------------------------------------------


def test_has_cycles_no_cycles_returns_false() -> None:
    # Arrange
    tasks = [make_task("T1"), make_task("T2", dependencies=["T1"]), make_task("T3", dependencies=["T2"])]
    graph = DependencyGraph(tasks)

    # Act / Assert
    assert graph.has_cycles() is False


def test_has_cycles_simple_two_node_cycle_returns_true() -> None:
    # Arrange: T1 -> T2 -> T1
    tasks = [make_task("T1", dependencies=["T2"]), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act / Assert
    assert graph.has_cycles() is True


def test_has_cycles_three_node_cycle_returns_true() -> None:
    # Arrange: T1 -> T2 -> T3 -> T1
    tasks = [
        make_task("T1", dependencies=["T3"]),
        make_task("T2", dependencies=["T1"]),
        make_task("T3", dependencies=["T2"]),
    ]
    graph = DependencyGraph(tasks)

    # Act / Assert
    assert graph.has_cycles() is True


def test_get_cycles_returns_cycle_members() -> None:
    # Arrange: T1 -> T2 -> T3 -> T1
    tasks = [
        make_task("T1", dependencies=["T3"]),
        make_task("T2", dependencies=["T1"]),
        make_task("T3", dependencies=["T2"]),
    ]
    graph = DependencyGraph(tasks)

    # Act
    cycles = graph.get_cycles()

    # Assert — at least one cycle reported, all members are from the cycle
    assert len(cycles) >= 1
    assert set(cycles[0]).issubset({"T1", "T2", "T3"})


def test_get_cycles_empty_task_list_returns_empty() -> None:
    # Arrange / Act / Assert
    assert DependencyGraph([]).get_cycles() == []


def test_get_cycles_acyclic_graph_returns_empty() -> None:
    # Arrange
    tasks = [make_task("T1"), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act / Assert
    assert graph.get_cycles() == []


# ---------------------------------------------------------------------------
# DependencyGraph.get_blocked_tasks
# ---------------------------------------------------------------------------


def test_get_blocked_tasks_with_not_started_dep_reports_task() -> None:
    # Arrange
    tasks = [make_task("T1"), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    blocked = graph.get_blocked_tasks()

    # Assert — T2 blocked by T1 (not-started)
    assert len(blocked) == 1
    task, missing = blocked[0]
    assert task.id == "T2"
    assert "T1" in missing


def test_get_blocked_tasks_complete_dep_does_not_block() -> None:
    # Arrange
    tasks = [make_task("T1", status=TaskStatus.COMPLETE), make_task("T2", dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    blocked = graph.get_blocked_tasks()

    # Assert — T2 is NOT blocked (T1 is complete)
    assert blocked == []


def test_get_blocked_tasks_nonexistent_dep_reports_as_unsatisfied() -> None:
    # Arrange — T1 depends on T99 which is absent from the plan
    tasks = [make_task("T1", dependencies=["T99"])]
    graph = DependencyGraph(tasks)

    # Act
    blocked = graph.get_blocked_tasks()

    # Assert
    assert len(blocked) == 1
    _, missing = blocked[0]
    assert "T99" in missing


def test_get_blocked_tasks_in_progress_task_excluded_from_blocked() -> None:
    # Arrange — T2 is in-progress, T1 is not terminal
    tasks = [make_task("T1"), make_task("T2", status=TaskStatus.IN_PROGRESS, dependencies=["T1"])]
    graph = DependencyGraph(tasks)

    # Act
    blocked = graph.get_blocked_tasks()

    # Assert — only not-started tasks are reported as blocked
    assert all(t.status == TaskStatus.NOT_STARTED for t, _ in blocked)
