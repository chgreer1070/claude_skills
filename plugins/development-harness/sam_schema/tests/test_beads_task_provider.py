"""Unit tests for BeadsTaskProvider.

All tests mock the bd CLI via _FakeBdRunner — no live bd binary required.
"""

from __future__ import annotations

import json

import pytest

from sam_schema.core.action_models import TaskDefinition
from sam_schema.core.backends.beads import BeadsTaskProvider
from sam_schema.core.exceptions import DocumentNotFoundError, PlanNotFoundError, TaskNotFoundError, TaskValidationError

from .conftest import _FakeBdRunner, make_task_record

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_def(
    task_id: str, title: str, deps: list[str] | None = None, priority: int = 2, description: str = ""
) -> TaskDefinition:
    return TaskDefinition.model_validate({
        "id": task_id,
        "title": title,
        "status": "not-started",
        "priority": priority,
        "complexity": "low",
        "body": "",
        "description": description,
        "dependencies": deps or [],
        "agent": None,
        "skills": [],
    })


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------


class TestCreatePlan:
    def test_creates_epic_and_indexes_plan(self, fake_runner: _FakeBdRunner) -> None:
        """create_plan must create exactly one epic and register it in bd remember."""
        provider = BeadsTaskProvider(runner=fake_runner)
        tasks = [_task_def("T01", "Do something")]
        result = provider.create_plan("my-slug", "Goal text", tasks)

        plan_id = result["plan_id"]
        assert plan_id.startswith("P")

        # The epic was created
        epics = [i for i in fake_runner._issues.values() if i["type"] == "epic"]
        assert len(epics) == 1
        epic = epics[0]
        assert epic["title"] == "my-slug"
        assert epic["description"] == "Goal text"

        # Plan index written to bd remember
        idx_key = f"dh.plan-index.{plan_id}"
        assert idx_key in fake_runner._memory
        assert fake_runner._memory[idx_key] == epic["id"]

    def test_creates_child_task_issue(self, fake_runner: _FakeBdRunner) -> None:
        """Each task in the plan must become a child issue with --parent set."""
        provider = BeadsTaskProvider(runner=fake_runner)
        tasks = [_task_def("T01", "Write tests")]
        result = provider.create_plan("slug", "goal", tasks)

        # Exactly one child task issue
        task_issues = [i for i in fake_runner._issues.values() if i["type"] == "task"]
        assert len(task_issues) == 1

        # Task index entry was written
        plan_id = result["plan_id"]
        task_idx_key = f"dh.task-index.{plan_id}.T01"
        assert task_idx_key in fake_runner._memory
        payload = json.loads(fake_runner._memory[task_idx_key])
        assert payload["bd_id"] == task_issues[0]["id"]

    def test_returns_plan_data_with_tasks(self, fake_runner: _FakeBdRunner) -> None:
        """create_plan must return PlanData with tasks list."""
        provider = BeadsTaskProvider(runner=fake_runner)
        tasks = [_task_def("T01", "First"), _task_def("T02", "Second")]
        result = provider.create_plan("slug", "goal", tasks)

        assert result["feature"] == "slug"
        assert result["goal"] == "goal"
        assert len(result["tasks"]) == 2

    def test_raises_task_validation_error_on_duplicate_id(self, fake_runner: _FakeBdRunner) -> None:
        """create_plan must raise TaskValidationError when two tasks share the same ID."""
        provider = BeadsTaskProvider(runner=fake_runner)
        tasks = [_task_def("T01", "First"), _task_def("T01", "Duplicate")]
        with pytest.raises(TaskValidationError):
            provider.create_plan("slug", "goal", tasks)

    def test_context_appended_to_description(self, fake_runner: _FakeBdRunner) -> None:
        """Context string must appear in epic description when provided."""
        provider = BeadsTaskProvider(runner=fake_runner)
        provider.create_plan("slug", "goal", [], context="Extra context")

        epics = [i for i in fake_runner._issues.values() if i["type"] == "epic"]
        assert len(epics) == 1
        desc = epics[0]["description"] or ""
        assert "Extra context" in desc


# ---------------------------------------------------------------------------
# read_plan
# ---------------------------------------------------------------------------


class TestReadPlan:
    def test_raises_plan_not_found_for_unknown_plan(self, fake_runner: _FakeBdRunner) -> None:
        """read_plan must raise PlanNotFoundError for an unregistered plan."""
        provider = BeadsTaskProvider(runner=fake_runner)
        with pytest.raises(PlanNotFoundError):
            provider.read_plan("Punknown")

    def test_reads_plan_and_tasks(self, fake_runner: _FakeBdRunner) -> None:
        """read_plan must reconstruct PlanData from the epic and task issues."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        tasks = [_task_def("T01", "Alpha"), _task_def("T02", "Beta")]
        created = provider.create_plan("test-plan", "Test goal", tasks)
        plan_id = created["plan_id"]

        plan = provider.read_plan(plan_id)
        assert plan["plan_id"] == plan_id
        assert plan["feature"] == "test-plan"
        assert len(plan["tasks"]) == 2


# ---------------------------------------------------------------------------
# claim_task
# ---------------------------------------------------------------------------


class TestClaimTask:
    def test_claim_succeeds_on_open_task(self, fake_runner: _FakeBdRunner) -> None:
        """claim_task must return True and mark issue as hooked when task is open."""
        plan_id, runner = "Pclaim01", fake_runner
        runner._memory["dh.plan-index.Pclaim01"] = runner._new_id()
        epic_id = runner._memory["dh.plan-index.Pclaim01"]
        runner._issues[epic_id] = runner._make_issue(epic_id, "epic", issue_type="epic")
        bd_id = make_task_record(runner, plan_id, "T01", status="open", parent_id=epic_id)

        provider = BeadsTaskProvider(runner=runner)
        result = provider.claim_task(plan_id, "T01")

        assert result is True
        assert runner._issues[bd_id]["status"] == "hooked"

    def test_claim_returns_false_when_already_claimed(self, fake_runner: _FakeBdRunner) -> None:
        """claim_task must return False when the issue is already claimed (hooked)."""
        plan_id = "Pclaim02"
        runner = fake_runner
        epic_id = runner._new_id()
        runner._issues[epic_id] = runner._make_issue(epic_id, "epic", issue_type="epic")
        runner._memory[f"dh.plan-index.{plan_id}"] = epic_id
        make_task_record(runner, plan_id, "T01", status="hooked", parent_id=epic_id)

        provider = BeadsTaskProvider(runner=runner)
        result = provider.claim_task(plan_id, "T01")

        assert result is False

    def test_claim_raises_task_not_found(self, fake_runner: _FakeBdRunner) -> None:
        """claim_task must raise TaskNotFoundError for an unregistered task ID."""
        plan_id = "Pclaim03"
        runner = fake_runner
        epic_id = runner._new_id()
        runner._issues[epic_id] = runner._make_issue(epic_id, "epic", issue_type="epic")
        runner._memory[f"dh.plan-index.{plan_id}"] = epic_id

        provider = BeadsTaskProvider(runner=runner)
        with pytest.raises(TaskNotFoundError):
            provider.claim_task(plan_id, "T99")


# ---------------------------------------------------------------------------
# update_task_status
# ---------------------------------------------------------------------------


class TestUpdateTaskStatus:
    def test_update_status_valid(self, fake_runner: _FakeBdRunner) -> None:
        """update_task_status must call bd update --status with mapped value."""
        plan_id = "Pstat01"
        runner = fake_runner
        epic_id = runner._new_id()
        runner._issues[epic_id] = runner._make_issue(epic_id, "epic", issue_type="epic")
        runner._memory[f"dh.plan-index.{plan_id}"] = epic_id
        bd_id = make_task_record(runner, plan_id, "T01", parent_id=epic_id)

        provider = BeadsTaskProvider(runner=runner)
        provider.update_task_status(plan_id, "T01", "complete")

        # Check that bd update --status closed was called
        update_calls = [c for c in runner.text_calls if c[0] == "update" and "--status" in c]
        assert any(bd_id in c and "closed" in c for c in update_calls)

    def test_update_status_invalid_raises(self, fake_runner: _FakeBdRunner) -> None:
        """update_task_status must raise TaskValidationError for unknown status."""
        plan_id = "Pstat02"
        runner = fake_runner
        epic_id = runner._new_id()
        runner._issues[epic_id] = runner._make_issue(epic_id, "epic", issue_type="epic")
        runner._memory[f"dh.plan-index.{plan_id}"] = epic_id
        make_task_record(runner, plan_id, "T01", parent_id=epic_id)

        provider = BeadsTaskProvider(runner=runner)
        with pytest.raises(TaskValidationError):
            provider.update_task_status(plan_id, "T01", "bogus-status")


# ---------------------------------------------------------------------------
# store_document / read_document
# ---------------------------------------------------------------------------


class TestDocumentRoundTrip:
    def test_store_and_read_plan_level_document(self, fake_runner: _FakeBdRunner) -> None:
        """store_document followed by read_document must return the same content."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        tasks = [_task_def("T01", "task")]
        created = provider.create_plan("doc-plan", "goal", tasks)
        plan_id = created["plan_id"]

        handle = provider.store_document(plan_id, None, "architect", "spec", "My Doc", "# Content here")

        assert handle["content_ref"].startswith("bd://")
        doc_data = provider.read_document(handle)
        assert doc_data["content"] == "# Content here"
        assert doc_data["title"] == "My Doc"

    def test_store_task_level_document(self, fake_runner: _FakeBdRunner) -> None:
        """store_document at task level must embed content in task issue notes."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        tasks = [_task_def("T01", "task")]
        created = provider.create_plan("tdoc-plan", "goal", tasks)
        plan_id = created["plan_id"]

        handle = provider.store_document(plan_id, "T01", "stage", "type", "T Title", "task content")
        doc = provider.read_document(handle)
        assert "task content" in doc["content"]

    def test_read_document_raises_for_missing_ref(self, fake_runner: _FakeBdRunner) -> None:
        """read_document must raise DocumentNotFoundError for a made-up content_ref."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        tasks = [_task_def("T01", "task")]
        created = provider.create_plan("missing-plan", "goal", tasks)
        plan_id = created["plan_id"]
        # Register valid plan so epic lookup succeeds, but ref won't be in notes
        fake_handle = {
            "content_ref": f"bd://{plan_id}/{plan_id}/stage/type/deadbeef",
            "owner_type": "plan",
            "owner_id": plan_id,
            "stage": "stage",
            "doc_type": "type",
            "title": "Missing",
            "fmt": "md",
        }
        with pytest.raises(DocumentNotFoundError):
            provider.read_document(fake_handle)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# append_task
# ---------------------------------------------------------------------------


class TestAppendTask:
    def test_append_task_creates_issue_and_indexes(self, fake_runner: _FakeBdRunner) -> None:
        """append_task must create a new child issue and register it in bd remember."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        created = provider.create_plan("ap-plan", "goal", [])
        plan_id = created["plan_id"]

        new_task = _task_def("T01", "Appended task")
        result = provider.append_task(plan_id, new_task)  # type: ignore[arg-type]

        assert result["appended"] is True
        assert result["task_id"] == "T01"
        idx_key = f"dh.task-index.{plan_id}.T01"
        assert idx_key in runner._memory

    def test_append_task_raises_for_duplicate(self, fake_runner: _FakeBdRunner) -> None:
        """append_task must raise TaskValidationError when the task ID already exists."""
        runner = fake_runner
        provider = BeadsTaskProvider(runner=runner)
        created = provider.create_plan("ap-plan2", "goal", [_task_def("T01", "Existing")])
        plan_id = created["plan_id"]

        with pytest.raises(TaskValidationError):
            provider.append_task(plan_id, _task_def("T01", "Duplicate"))  # type: ignore[arg-type]
