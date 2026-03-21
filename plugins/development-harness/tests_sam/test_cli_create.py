"""Tests for sam CLI ``create`` command.

Tests: Plan creation via CLI with stdin YAML, slug, goal, context, and issue options.
How: Invoke ``sam create`` via CliRunner, verify JSON output and file creation.
Why: ``create`` is the entry point for all new plan files -- errors here prevent
plan creation across the entire SAM pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sam_schema.cli import app
from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def plan_dir(tmp_path: Path) -> Path:
    """Create an empty temporary plan directory.

    Returns:
        Path to a ``plan/`` directory inside ``tmp_path``.
    """
    d = tmp_path / "plan"
    d.mkdir()
    return d


MINIMAL_TASKS_YAML = """\
tasks:
  - task: T1
    title: First task
    status: not-started
    agent: test-agent
    dependencies: []
    priority: 3
    complexity: medium
  - task: T2
    title: Second task
    status: not-started
    agent: test-agent
    dependencies:
      - T1
    priority: 3
    complexity: medium
"""

BARE_LIST_YAML = """\
- task: T1
  title: Solo task
  status: not-started
  agent: test-agent
  dependencies: []
  priority: 3
  complexity: medium
"""


# ---------------------------------------------------------------------------
# sam create -- basic creation
# ---------------------------------------------------------------------------


class TestSamCreateBasic:
    """Test basic ``sam create`` functionality.

    Tests: Plan file creation with minimal required arguments.
    How: Invoke CLI with slug and goal, verify JSON output and file on disk.
    Why: Every plan begins with ``sam create`` -- the happy path must work.
    """

    def test_create_with_slug_and_goal_returns_json(self, plan_dir: Path) -> None:
        """Create a plan with slug and goal, verify JSON response.

        Tests: CLI output format.
        How: Invoke create, parse JSON, check required keys.
        Why: Downstream tools parse the JSON output to locate the created file.
        """
        # Arrange -- empty plan_dir
        # Act
        result = runner.invoke(
            app,
            ["create", "my-feature", "--goal", "Implement feature X", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "path" in data
        assert "plan_number" in data
        assert "task_count" in data
        assert data["task_count"] == 0

    def test_create_assigns_plan_number_starting_at_1(self, plan_dir: Path) -> None:
        """First plan in empty directory gets plan number 1.

        Tests: Plan number assignment.
        How: Create in empty dir, check plan_number == 1.
        Why: Sequential numbering is the addressing foundation.
        """
        # Arrange -- empty plan_dir
        # Act
        result = runner.invoke(
            app, ["create", "first-plan", "--goal", "Goal", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"}
        )
        # Assert
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plan_number"] == 1

    def test_create_writes_file_to_disk(self, plan_dir: Path) -> None:
        """Created plan file exists on disk at the reported path.

        Tests: File creation side effect.
        How: Invoke create, check file exists at reported path.
        Why: If the file is not written, all downstream operations fail.
        """
        # Arrange
        # Act
        result = runner.invoke(
            app, ["create", "disk-test", "--goal", "Test goal", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"}
        )
        # Assert
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert Path(data["path"]).exists()

    def test_create_file_has_yaml_extension(self, plan_dir: Path) -> None:
        """Created file uses .yaml extension.

        Tests: File naming convention.
        How: Check suffix of created file.
        Why: Pure YAML format is the canonical plan format per ADR-001.
        """
        # Arrange / Act
        result = runner.invoke(
            app, ["create", "ext-test", "--goal", "Goal", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"}
        )
        # Assert
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["path"].endswith(".yaml")

    def test_create_sequential_numbering(self, plan_dir: Path) -> None:
        """Second plan gets plan_number 2 when plan_number 1 already exists.

        Tests: Sequential numbering across multiple creates.
        How: Create two plans, verify plan_numbers are 1 and 2.
        Why: Collisions in plan numbers break addressing.
        """
        # Arrange -- create first plan
        runner.invoke(app, ["create", "first", "--goal", "First", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Act -- create second plan
        result = runner.invoke(
            app, ["create", "second", "--goal", "Second", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"}
        )
        # Assert
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plan_number"] == 2


# ---------------------------------------------------------------------------
# sam create -- with stdin tasks
# ---------------------------------------------------------------------------


class TestSamCreateWithStdin:
    """Test ``sam create --stdin`` for reading tasks from stdin.

    Tests: Task ingestion from stdin YAML.
    How: Pass YAML via CliRunner input parameter, verify task_count in output.
    Why: ``--stdin`` is how task planners feed structured tasks into new plans.
    """

    def test_create_with_stdin_tasks_dict_format(self, plan_dir: Path) -> None:
        """Create with --stdin reads tasks from a YAML dict with 'tasks' key.

        Tests: Dict-format stdin parsing.
        How: Pass YAML with top-level ``tasks:`` list.
        Why: This is the canonical stdin format.
        """
        # Arrange
        # Act
        result = runner.invoke(
            app,
            ["create", "stdin-test", "--goal", "Goal", "--stdin", "--plan-dir", str(plan_dir)],
            input=MINIMAL_TASKS_YAML,
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["task_count"] == 2

    def test_create_with_stdin_bare_list_format(self, plan_dir: Path) -> None:
        """Create with --stdin reads tasks from a bare YAML list.

        Tests: Bare-list stdin parsing.
        How: Pass YAML that is a list of task dicts (no top-level key).
        Why: Some task generators emit bare lists without a ``tasks:`` wrapper.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "bare-list", "--goal", "Goal", "--stdin", "--plan-dir", str(plan_dir)],
            input=BARE_LIST_YAML,
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["task_count"] == 1

    def test_create_with_stdin_empty_input_creates_zero_tasks(self, plan_dir: Path) -> None:
        """Create with --stdin and empty input creates plan with 0 tasks.

        Tests: Empty stdin handling.
        How: Pass empty string as stdin.
        Why: Edge case -- must not crash on empty input.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "empty-stdin", "--goal", "Goal", "--stdin", "--plan-dir", str(plan_dir)],
            input="",
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task_count"] == 0

    def test_create_with_stdin_invalid_yaml_exits_with_error(self, plan_dir: Path) -> None:
        """Create with --stdin and invalid YAML structure exits 1.

        Tests: Invalid stdin rejection.
        How: Pass a YAML scalar (not list or dict) via stdin.
        Why: Malformed stdin must produce a clear error, not a crash.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "bad-stdin", "--goal", "Goal", "--stdin", "--plan-dir", str(plan_dir)],
            input="just a string, not a list or dict",
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 1

    def test_create_with_stdin_invalid_task_schema_exits_with_error(self, plan_dir: Path) -> None:
        """Create with --stdin containing invalid task schema exits 1.

        Tests: Task validation during create.
        How: Pass a task dict missing required ``title`` field.
        Why: Invalid tasks must be rejected at creation time.
        """
        # Arrange
        bad_task = "tasks:\n  - task: T1\n    status: not-started\n"
        # Act
        result = runner.invoke(
            app,
            ["create", "bad-schema", "--goal", "Goal", "--stdin", "--plan-dir", str(plan_dir)],
            input=bad_task,
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# sam create -- optional fields
# ---------------------------------------------------------------------------


class TestSamCreateOptionalFields:
    """Test ``sam create`` with optional --context and --issue flags.

    Tests: Plan-level metadata population.
    How: Create with optional flags, read back the file, verify fields.
    Why: Context and issue are used by downstream agents for plan discovery.
    """

    def test_create_with_context_stores_context_in_plan(self, plan_dir: Path) -> None:
        """Create with --context persists the context field.

        Tests: Context field persistence.
        How: Create with --context, load plan, check context value.
        Why: Plan context drives agent behavior during task execution.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "ctx-test", "--goal", "Goal", "--context", "Some shared context", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0
        # Verify by reading back
        json.loads(result.output)
        read_result = runner.invoke(app, ["read", "P1", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        assert read_result.exit_code == 0
        plan_data = json.loads(read_result.output)
        assert plan_data.get("context") == "Some shared context"

    def test_create_with_issue_stores_issue_in_plan(self, plan_dir: Path) -> None:
        """Create with --issue persists the issue number.

        Tests: Issue field persistence.
        How: Create with --issue 42, load plan, check issue value.
        Why: Issue links plans to GitHub issues for traceability.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "issue-test", "--goal", "Goal", "--issue", "42", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0
        # --issue 42 produces P42, not P1
        read_result = runner.invoke(app, ["read", "P42", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        assert read_result.exit_code == 0
        plan_data = json.loads(read_result.output)
        assert plan_data.get("issue") == "42"


# ---------------------------------------------------------------------------
# sam create -- round-trip verification
# ---------------------------------------------------------------------------


class TestSamCreateRoundTrip:
    """Test create-then-read round-trip fidelity.

    Tests: Data survives create -> read cycle.
    How: Create plan with tasks, read back via ``sam read``, compare.
    Why: AC4 -- sam create round-trips (create then read produces identical data).
    """

    def test_create_then_read_preserves_task_data(self, plan_dir: Path) -> None:
        """Tasks created via stdin can be read back with identical fields.

        Tests: Task data round-trip fidelity.
        How: Create with tasks, read P1/T1, verify fields match.
        Why: Data loss during create->read breaks the entire workflow.
        """
        # Arrange / Act -- create
        create_result = runner.invoke(
            app,
            ["create", "roundtrip", "--goal", "Round-trip test", "--stdin", "--plan-dir", str(plan_dir)],
            input=MINIMAL_TASKS_YAML,
            env={"NO_COLOR": "1"},
        )
        assert create_result.exit_code == 0

        # Act -- read back
        read_result = runner.invoke(app, ["read", "P1/T1", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Assert
        assert read_result.exit_code == 0
        data = json.loads(read_result.output)
        task = data["task"]
        assert task["id"] == "T1"
        assert task["title"] == "First task"
        assert task["status"] == "not-started"

    def test_create_then_read_preserves_task_count(self, plan_dir: Path) -> None:
        """Number of tasks after round-trip matches creation input.

        Tests: Task count fidelity.
        How: Create with 2 tasks, read plan, count tasks.
        Why: Lost tasks during round-trip would silently drop work items.
        """
        # Arrange / Act -- create
        create_result = runner.invoke(
            app,
            ["create", "count-test", "--goal", "Count test", "--stdin", "--plan-dir", str(plan_dir)],
            input=MINIMAL_TASKS_YAML,
            env={"NO_COLOR": "1"},
        )
        assert create_result.exit_code == 0

        # Act -- read plan-level
        read_result = runner.invoke(app, ["read", "P1", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Assert
        assert read_result.exit_code == 0
        plan_data = json.loads(read_result.output)
        assert len(plan_data.get("tasks", [])) == 2

    def test_create_then_read_assignment_includes_plan_goal(self, plan_dir: Path) -> None:
        """TaskAssignment from read includes the plan goal set during create.

        Tests: Plan-level field propagation in TaskAssignment.
        How: Create with goal, read P1/T1, check plan-goal field.
        Why: AC5 -- sam read includes plan context in TaskAssignment response.
        """
        # Arrange / Act
        create_result = runner.invoke(
            app,
            ["create", "goal-test", "--goal", "My specific goal", "--stdin", "--plan-dir", str(plan_dir)],
            input=MINIMAL_TASKS_YAML,
            env={"NO_COLOR": "1"},
        )
        assert create_result.exit_code == 0

        read_result = runner.invoke(app, ["read", "P1/T1", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Assert
        assert read_result.exit_code == 0
        data = json.loads(read_result.output)
        assert data.get("plan-goal") == "My specific goal"

    def test_create_with_stdin_preserves_task_body_content(self, plan_dir: Path) -> None:
        """Task ``body`` field round-trips through create -> read without data loss.

        Tests: body field preservation during stdin create.
        How: Create with a task containing a multiline body, read back P1/T1, verify body.
        Why: Pydantic drops unknown fields silently -- body was missing from Task model,
             causing body content to be discarded at validation time (reproduced on P577, P964).
        """
        # Arrange
        tasks_with_body = """\
tasks:
  - task: T1
    title: Body preservation test
    status: not-started
    agent: python-cli-architect
    dependencies: []
    priority: 3
    complexity: medium
    body: |
      ## Objective
      This is a test body that should be preserved.

      ## Acceptance Criteria
      - Body content is not empty after create
"""
        # Act -- create
        create_result = runner.invoke(
            app,
            ["create", "body-test", "--goal", "Test body preservation", "--stdin", "--plan-dir", str(plan_dir)],
            input=tasks_with_body,
            env={"NO_COLOR": "1"},
        )
        assert create_result.exit_code == 0, create_result.output

        # Act -- read back
        read_result = runner.invoke(app, ["read", "P1/T1", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Assert
        assert read_result.exit_code == 0, read_result.output
        data = json.loads(read_result.output)
        task = data["task"]
        assert task.get("body"), "body field is empty -- content was dropped at model validation"
        assert "## Objective" in task["body"]
        assert "This is a test body that should be preserved." in task["body"]

    def test_create_plan_dir_auto_created_if_missing(self, tmp_path: Path) -> None:
        """Plan directory is auto-created if it does not exist.

        Tests: Directory auto-creation.
        How: Pass non-existent plan_dir, verify plan is created.
        Why: First-time users should not need to mkdir before create.
        """
        # Arrange
        new_dir = tmp_path / "auto-created-plan"
        assert not new_dir.exists()
        # Act
        result = runner.invoke(
            app, ["create", "auto-dir", "--goal", "Goal", "--plan-dir", str(new_dir)], env={"NO_COLOR": "1"}
        )
        # Assert
        assert result.exit_code == 0
        assert new_dir.exists()


# ---------------------------------------------------------------------------
# sam create -- --issue as plan number
# ---------------------------------------------------------------------------


class TestSamCreateIssueAsPlanNumber:
    """Test that --issue N makes the plan number N, not the next sequential number.

    Tests: Issue-number-as-plan-number behaviour.
    How: Invoke create with --issue, verify path, plan_number, and file on disk.
    Why: GitHub issue number == plan number makes addressing unambiguous and
         eliminates the collision class where sequential plan numbering and
         sequential issue numbering independently produce the same integer.
    """

    def test_create_with_issue_uses_issue_as_plan_number(self, plan_dir: Path) -> None:
        """--issue 951 produces a plan file named P951-{slug}.yaml.

        Tests: File naming when --issue is provided.
        How: Create with --issue 951, check plan_number and path in JSON output.
        Why: plan_number must equal the issue number so callers can rely on
             the identity plan-file = P{issue}.
        """
        # Arrange -- empty plan_dir
        # Act
        result = runner.invoke(
            app,
            ["create", "my-feature", "--goal", "Test", "--issue", "951", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["plan_number"] == 951
        assert "P951-my-feature.yaml" in data["path"]
        assert Path(data["path"]).exists()

    def test_create_with_issue_file_exists_at_reported_path(self, plan_dir: Path) -> None:
        """File created with --issue exists on disk at the path returned in JSON.

        Tests: Disk write side effect for issue-numbered plans.
        How: Create with --issue, stat the reported path.
        Why: If the file is not written, all downstream read/claim operations fail.
        """
        # Arrange / Act
        result = runner.invoke(
            app,
            ["create", "disk-check", "--goal", "Test", "--issue", "42", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert Path(data["path"]).exists()

    def test_create_with_issue_skips_sequential_numbering(self, plan_dir: Path) -> None:
        """Sequential fallback is bypassed when --issue is provided.

        Tests: --issue overrides sequential assignment.
        How: Create P1 sequentially, then create with --issue 500; verify P500.
        Why: Without this, --issue might still return plan_number 2 because
             sequential scanning found P1 and returned 2.
        """
        # Arrange -- create a sequential plan first (will be P1)
        runner.invoke(app, ["create", "first", "--goal", "First", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Act -- create with explicit issue number
        result = runner.invoke(
            app,
            ["create", "jumped", "--goal", "Jumped", "--issue", "500", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["plan_number"] == 500

    def test_create_without_issue_still_sequential(self, plan_dir: Path) -> None:
        """Sequential numbering is preserved when --issue is not given.

        Tests: Fallback to sequential numbering when --issue is absent.
        How: Create two plans without --issue, verify numbers 1 and 2.
        Why: The sequential path must continue to work after adding --issue support.
        """
        # Arrange / Act
        r1 = runner.invoke(app, ["create", "seq-a", "--goal", "A", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        r2 = runner.invoke(app, ["create", "seq-b", "--goal", "B", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        # Assert
        assert r1.exit_code == 0
        assert r2.exit_code == 0
        assert json.loads(r1.output)["plan_number"] == 1
        assert json.loads(r2.output)["plan_number"] == 2


# ---------------------------------------------------------------------------
# sam create -- collision guard
# ---------------------------------------------------------------------------


class TestSamCreateCollisionGuard:
    """Test that creating a plan with a duplicate issue number is rejected.

    Tests: Collision guard behaviour.
    How: Create a plan, then attempt to create another with the same --issue.
    Why: Duplicate plan numbers break addressing -- two P951 files cannot coexist.
    """

    def test_create_collision_on_duplicate_issue_exits_1(self, plan_dir: Path) -> None:
        """Second create with same --issue exits 1 with error message.

        Tests: Collision detection on duplicate issue number.
        How: Create P951, attempt to create P951 again, expect exit 1.
        Why: Silent overwrite would destroy the existing plan file.
        """
        # Arrange -- create the first plan with issue 951
        first = runner.invoke(
            app,
            ["create", "original", "--goal", "Original", "--issue", "951", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        assert first.exit_code == 0, first.output
        # Act -- attempt duplicate
        second = runner.invoke(
            app,
            ["create", "duplicate", "--goal", "Duplicate", "--issue", "951", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert
        assert second.exit_code == 1
        assert "P951" in second.output

    def test_create_collision_error_message_names_existing_file(self, plan_dir: Path) -> None:
        """Collision error message includes the existing plan path.

        Tests: Error message content for collision.
        How: Create P10, attempt duplicate, check stderr/output mentions the file.
        Why: Error must tell the caller what already exists so they can act.
        """
        # Arrange
        runner.invoke(
            app,
            ["create", "existing", "--goal", "Existing", "--issue", "10", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Act
        result = runner.invoke(
            app,
            ["create", "collision", "--goal", "Collision", "--issue", "10", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert -- error text should mention the existing plan path
        assert result.exit_code == 1
        combined = result.output + (result.stderr if hasattr(result, "stderr") and result.stderr else "")
        assert "P10" in combined

    def test_create_collision_does_not_overwrite_existing_file(self, plan_dir: Path) -> None:
        """Rejected duplicate create leaves the original file intact.

        Tests: File preservation on collision.
        How: Create P7, attempt duplicate, read P7, verify original goal survives.
        Why: Collision must be a hard stop -- no partial overwrites.
        """
        # Arrange
        runner.invoke(
            app,
            ["create", "safe-original", "--goal", "Original goal", "--issue", "7", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Act -- collision attempt
        runner.invoke(
            app,
            ["create", "intruder", "--goal", "Intruder goal", "--issue", "7", "--plan-dir", str(plan_dir)],
            env={"NO_COLOR": "1"},
        )
        # Assert -- original plan still readable with original goal
        read_result = runner.invoke(app, ["read", "P7", "--plan-dir", str(plan_dir)], env={"NO_COLOR": "1"})
        assert read_result.exit_code == 0
        plan_data = json.loads(read_result.output)
        assert plan_data.get("goal") == "Original goal"
