"""Dependency graph with cycle detection and task readiness queries.

Builds a directed acyclic graph (DAG) from task dependencies and provides
cycle detection, readiness checks, and blocked task reporting.
"""

from __future__ import annotations

import re

from sam_schema.core.models import Task, TaskStatus

# Statuses that satisfy a dependency requirement — tasks depending on a task
# in one of these statuses may proceed.
TERMINAL_STATUSES: frozenset[str] = frozenset({TaskStatus.COMPLETE, TaskStatus.DEFERRED, TaskStatus.SKIPPED})

# Pattern used to extract the numeric portion of a task ID for ordering.
# Matches "T1", "1", "T2.3", "1.1" — captures the leading numeric part.
_ID_NUMERIC_RE: re.Pattern[str] = re.compile(r"[A-Za-z]*(\d+)(?:\.(\d+))?$")


def _task_id_sort_key(task_id: str) -> tuple[int, int]:
    """Return a (major, minor) integer tuple for stable task ID ordering.

    Args:
        task_id: A validated task ID string such as "T1", "2.3", or "T10".

    Returns:
        A tuple ``(major, minor)`` suitable for ascending numeric sort.
        IDs without a minor component use ``minor=0``.
    """
    m = _ID_NUMERIC_RE.match(task_id)
    if not m:
        return (0, 0)
    major = int(m.group(1))
    minor = int(m.group(2)) if m.group(2) else 0
    return (major, minor)


class DependencyGraph:
    """Task dependency graph with cycle detection and readiness queries.

    Args:
        tasks: All tasks in a plan. Each task's ``dependencies`` list is
               used to build the directed graph edges.
    """

    def __init__(self, tasks: list[Task]) -> None:
        """Build the dependency graph from a list of tasks.

        Constructs an index of all tasks by ID and an adjacency mapping
        (``task_id -> list[dep_id]``) for O(1) lookups during graph queries.

        Args:
            tasks: All tasks in the plan.
        """
        self._tasks: list[Task] = tasks
        # Primary lookup: task ID -> Task
        self._by_id: dict[str, Task] = {t.id: t for t in tasks}
        # Adjacency list: task ID -> direct dependency IDs (raw from model)
        self._deps: dict[str, list[str]] = {t.id: list(t.dependencies) for t in tasks}

    # ------------------------------------------------------------------
    # Public query API
    # ------------------------------------------------------------------

    def get_ready_tasks(self) -> list[Task]:
        """Return tasks that are ready for dispatch.

        A task is ready when:

        1. Its status is ``not-started``.
        2. All tasks listed in its ``dependencies`` are in a terminal status
           (``complete``, ``deferred``, or ``skipped``).

        Tasks referencing dependency IDs that do not exist in the task list
        are treated as having an unsatisfied dependency and are therefore
        **not** ready.

        Returns:
            Tasks ready for dispatch, sorted by priority (ascending integer
            value, lower = higher priority) then numeric task ID (ascending).
        """
        ready: list[Task] = []
        for task in self._tasks:
            if task.status != TaskStatus.NOT_STARTED:
                continue
            if self._all_deps_terminal(task):
                ready.append(task)

        ready.sort(key=lambda t: (int(t.priority), _task_id_sort_key(t.id)))
        return ready

    def has_cycles(self) -> bool:
        """Check whether the dependency graph contains any cycles.

        Uses a DFS-based three-colour algorithm (white/grey/black) to detect
        back edges, which indicate cycles.

        Returns:
            ``True`` if at least one cycle exists, ``False`` otherwise.
        """
        return bool(self.get_cycles())

    def get_cycles(self) -> list[list[str]]:
        """Return all dependency cycles as lists of task IDs.

        Each cycle is represented as the minimal ordered sequence of task IDs
        that form the loop (e.g., ``["T1", "T2", "T3"]`` for T1→T2→T3→T1).
        The reported path starts and ends at the node that first closed the
        cycle during DFS traversal.

        Returns:
            List of cycles, where each cycle is a list of task ID strings.
            Empty list if no cycles exist.
        """
        # Three-colour DFS: 0=unvisited, 1=in-stack, 2=done
        colour: dict[str, int] = dict.fromkeys(self._by_id, 0)
        # Stack path for cycle reconstruction
        stack: list[str] = []
        cycles: list[list[str]] = []
        # Track cycles already found (by frozenset) to avoid duplicates
        seen_cycles: set[frozenset[str]] = set()

        def dfs(node: str) -> None:
            colour[node] = 1
            stack.append(node)
            for dep_id in self._deps.get(node, []):
                if dep_id not in colour:
                    # Dependency not in the task list — skip (not a cycle node)
                    continue
                if colour[dep_id] == 1:
                    # Back edge — cycle found. Extract cycle from stack.
                    cycle_start = stack.index(dep_id)
                    cycle = stack[cycle_start:]
                    key = frozenset(cycle)
                    if key not in seen_cycles:
                        seen_cycles.add(key)
                        cycles.append(list(cycle))
                elif colour[dep_id] == 0:
                    dfs(dep_id)
            stack.pop()
            colour[node] = 2

        for task_id in list(self._by_id):
            if colour[task_id] == 0:
                dfs(task_id)

        return cycles

    def get_blocked_tasks(self) -> list[tuple[Task, list[str]]]:
        """Return tasks that are blocked by unsatisfied dependencies.

        A task is *blocked* when it is in ``not-started`` status and has at
        least one dependency that is not in a terminal status.  Dependencies
        that reference task IDs absent from the plan are also treated as
        unsatisfied and reported.

        Note: tasks that are already in ``in-progress`` or ``blocked`` status
        are excluded — this method reports tasks that *cannot start* due to
        unmet prerequisites.

        Returns:
            List of ``(task, missing_dep_ids)`` tuples where ``missing_dep_ids``
            are the IDs of dependencies not yet in a terminal status.
        """
        result: list[tuple[Task, list[str]]] = []
        for task in self._tasks:
            if task.status != TaskStatus.NOT_STARTED:
                continue
            unsatisfied = self._unsatisfied_deps(task)
            if unsatisfied:
                result.append((task, unsatisfied))
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _dep_is_terminal(self, dep_id: str) -> bool:
        """Return True when *dep_id* exists and is in a terminal status.

        Args:
            dep_id: Task ID of the dependency to check.

        Returns:
            ``True`` if the dependency exists and its status is terminal,
            ``False`` if the dependency is missing or not yet terminal.
        """
        dep_task = self._by_id.get(dep_id)
        if dep_task is None:
            return False
        return dep_task.status in TERMINAL_STATUSES

    def _all_deps_terminal(self, task: Task) -> bool:
        """Return True when all of *task*'s dependencies are in terminal status.

        Args:
            task: The task whose dependencies are checked.

        Returns:
            ``True`` when every dependency ID resolves to a task in a terminal
            status.  ``True`` for tasks with no dependencies.
        """
        return all(self._dep_is_terminal(dep_id) for dep_id in task.dependencies)

    def _unsatisfied_deps(self, task: Task) -> list[str]:
        """Return dependency IDs that are not yet in a terminal status.

        Args:
            task: The task whose dependencies are examined.

        Returns:
            List of dependency IDs (may include IDs absent from the plan)
            that are not in a terminal status.
        """
        return [dep_id for dep_id in task.dependencies if not self._dep_is_terminal(dep_id)]
