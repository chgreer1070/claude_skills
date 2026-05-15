"""Unit tests for BeadsContextBackend.

All tests mock the bd CLI via _FakeBdRunner — no live bd binary required.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sam_schema.core.backends.beads import BeadsContextBackend
from sam_schema.core.models import ActiveTaskContext

if TYPE_CHECKING:
    from .conftest import _FakeBdRunner

# ---------------------------------------------------------------------------
# set_active_task
# ---------------------------------------------------------------------------


class TestSetActiveTask:
    def test_stores_context_in_bd_remember(self, fake_runner: _FakeBdRunner) -> None:
        """set_active_task must write JSON to bd remember under the correct key."""
        backend = BeadsContextBackend(runner=fake_runner)
        ctx = backend.set_active_task(session_id="sess-abc", plan="Pabc1234", task="T01", plan_dir="/tmp/plans")

        key = "dh.active-task.sess-abc"
        assert key in fake_runner._memory
        stored = json.loads(fake_runner._memory[key])
        assert stored["task_id"] == "T01"
        assert stored["session_id"] == "sess-abc"
        assert isinstance(ctx, ActiveTaskContext)

    def test_stores_parent_issue_number_int(self, fake_runner: _FakeBdRunner) -> None:
        """set_active_task must persist integer parent_issue_number correctly."""
        backend = BeadsContextBackend(runner=fake_runner)
        backend.set_active_task(session_id="sess-int", plan="Pabc", task="T02", plan_dir="/tmp", parent_issue_number=42)

        key = "dh.active-task.sess-int"
        stored = json.loads(fake_runner._memory[key])
        assert stored["parent_issue_number"] == 42

    def test_stores_parent_issue_number_beads_str(self, fake_runner: _FakeBdRunner) -> None:
        """set_active_task must persist a beads-format string parent_issue_number."""
        backend = BeadsContextBackend(runner=fake_runner)
        backend.set_active_task(
            session_id="sess-bd", plan="Pxyz", task="T03", plan_dir="/tmp", parent_issue_number="bd-a1b2"
        )

        key = "dh.active-task.sess-bd"
        stored = json.loads(fake_runner._memory[key])
        assert stored["parent_issue_number"] == "bd-a1b2"


# ---------------------------------------------------------------------------
# get_active_task
# ---------------------------------------------------------------------------


class TestGetActiveTask:
    def test_returns_context_when_stored(self, fake_runner: _FakeBdRunner) -> None:
        """get_active_task must return the stored ActiveTaskContext."""
        backend = BeadsContextBackend(runner=fake_runner)
        backend.set_active_task("sess-get", "Pplan", "T01", "/tmp")

        result = backend.get_active_task("sess-get")
        assert result is not None
        assert result.task_id == "T01"

    def test_returns_none_for_missing_session(self, fake_runner: _FakeBdRunner) -> None:
        """get_active_task must return None when the session has no stored context."""
        backend = BeadsContextBackend(runner=fake_runner)
        result = backend.get_active_task("no-such-session")
        assert result is None


# ---------------------------------------------------------------------------
# clear_active_task
# ---------------------------------------------------------------------------


class TestClearActiveTask:
    def test_clear_existing_returns_true(self, fake_runner: _FakeBdRunner) -> None:
        """clear_active_task must return True and remove the entry."""
        backend = BeadsContextBackend(runner=fake_runner)
        backend.set_active_task("sess-clr", "Pplan", "T01", "/tmp")

        removed = backend.clear_active_task("sess-clr")
        assert removed is True
        assert "dh.active-task.sess-clr" not in fake_runner._memory

    def test_clear_missing_returns_false(self, fake_runner: _FakeBdRunner) -> None:
        """clear_active_task must return False when no context exists."""
        backend = BeadsContextBackend(runner=fake_runner)
        result = backend.clear_active_task("no-such-session")
        assert result is False


# ---------------------------------------------------------------------------
# list_active_tasks
# ---------------------------------------------------------------------------


class TestListActiveTasks:
    def test_returns_all_stored_contexts(self, fake_runner: _FakeBdRunner) -> None:
        """list_active_tasks must return one entry per stored active-task key."""
        backend = BeadsContextBackend(runner=fake_runner)
        backend.set_active_task("sess-1", "Pa", "T01", "/tmp")
        backend.set_active_task("sess-2", "Pb", "T02", "/tmp")

        tasks = backend.list_active_tasks()
        task_ids = {t.task_id for t in tasks}
        assert task_ids == {"T01", "T02"}

    def test_ignores_non_context_entries(self, fake_runner: _FakeBdRunner) -> None:
        """list_active_tasks must skip bd remember entries with unrelated keys."""
        backend = BeadsContextBackend(runner=fake_runner)
        # Manually inject a non-context key
        fake_runner._memory["dh.plan-index.Pabc"] = "bd-t0001"
        backend.set_active_task("sess-only", "Px", "T01", "/tmp")

        tasks = backend.list_active_tasks()
        assert len(tasks) == 1
        assert tasks[0].task_id == "T01"

    def test_returns_empty_when_nothing_stored(self, fake_runner: _FakeBdRunner) -> None:
        """list_active_tasks must return an empty list with an empty memory store."""
        backend = BeadsContextBackend(runner=fake_runner)
        assert backend.list_active_tasks() == []
