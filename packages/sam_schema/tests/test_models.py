"""Tests for sam_schema.core.models — Pydantic model validation and enums.

Tests: Pydantic model validation, alias handling, enum coercion, field validators.
How: Construct models with valid/invalid data, verify validation and coercion.
Why: The Task and Plan models are the canonical data layer — all readers normalize
to them. Incorrect validation rules silently corrupt data downstream.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from sam_schema.core.models import (
    STATUS_MAP,
    TASK_ID_PATTERN,
    AnalysisMethod,
    Complexity,
    IssueClassification,
    Plan,
    PlanStatus,
    Priority,
    ReadResult,
    SchemaGap,
    Task,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# TaskStatus enum
# ---------------------------------------------------------------------------


class TestTaskStatusEnum:
    """Verify TaskStatus StrEnum members and values.

    Tests: Canonical status values used throughout the SAM pipeline.
    How: Check each member name maps to the expected kebab-case value.
    Why: Status values are stored on disk — mismatch causes silent failures.
    """

    def test_not_started_value(self) -> None:
        """Verify NOT_STARTED maps to 'not-started'."""
        assert TaskStatus.NOT_STARTED == "not-started"

    def test_in_progress_value(self) -> None:
        """Verify IN_PROGRESS maps to 'in-progress'."""
        assert TaskStatus.IN_PROGRESS == "in-progress"

    def test_complete_value(self) -> None:
        """Verify COMPLETE maps to 'complete'."""
        assert TaskStatus.COMPLETE == "complete"

    def test_blocked_value(self) -> None:
        """Verify BLOCKED maps to 'blocked'."""
        assert TaskStatus.BLOCKED == "blocked"

    def test_deferred_value(self) -> None:
        """Verify DEFERRED maps to 'deferred'."""
        assert TaskStatus.DEFERRED == "deferred"

    def test_skipped_value(self) -> None:
        """Verify SKIPPED maps to 'skipped'."""
        assert TaskStatus.SKIPPED == "skipped"

    def test_all_members_count(self) -> None:
        """Verify the total number of status values.

        Tests: TaskStatus completeness.
        How: Count enum members.
        Why: Adding a status without a test means no coverage of its downstream impact.
        """
        assert len(TaskStatus) == 6


# ---------------------------------------------------------------------------
# Complexity enum
# ---------------------------------------------------------------------------


class TestComplexityEnum:
    """Verify Complexity StrEnum values."""

    def test_low_value(self) -> None:
        """Verify LOW maps to 'low'."""
        assert Complexity.LOW == "low"

    def test_medium_value(self) -> None:
        """Verify MEDIUM maps to 'medium'."""
        assert Complexity.MEDIUM == "medium"

    def test_high_value(self) -> None:
        """Verify HIGH maps to 'high'."""
        assert Complexity.HIGH == "high"


# ---------------------------------------------------------------------------
# Priority enum
# ---------------------------------------------------------------------------


class TestPriorityEnum:
    """Verify Priority IntEnum values."""

    def test_critical_value(self) -> None:
        """Verify CRITICAL is 1."""
        assert Priority.CRITICAL == 1

    def test_high_value(self) -> None:
        """Verify HIGH is 2."""
        assert Priority.HIGH == 2

    def test_medium_value(self) -> None:
        """Verify MEDIUM is 3."""
        assert Priority.MEDIUM == 3

    def test_low_value(self) -> None:
        """Verify LOW is 4."""
        assert Priority.LOW == 4

    def test_lowest_value(self) -> None:
        """Verify LOWEST is 5."""
        assert Priority.LOWEST == 5

    def test_priority_ordering(self) -> None:
        """Verify CRITICAL < LOWEST for sort ordering.

        Tests: Priority comparison semantics.
        How: Compare int values directly.
        Why: DependencyGraph sorts by priority — wrong ordering produces wrong dispatch order.
        """
        assert Priority.CRITICAL < Priority.LOWEST


# ---------------------------------------------------------------------------
# IssueClassification and AnalysisMethod enums
# ---------------------------------------------------------------------------


class TestIssueClassification:
    """Verify IssueClassification StrEnum values."""

    def test_procedural_value(self) -> None:
        """Verify PROCEDURAL maps to 'procedural'."""
        assert IssueClassification.PROCEDURAL == "procedural"

    def test_defect_value(self) -> None:
        """Verify DEFECT maps to 'defect'."""
        assert IssueClassification.DEFECT == "defect"

    def test_recurring_pattern_value(self) -> None:
        """Verify RECURRING_PATTERN maps to 'recurring-pattern'."""
        assert IssueClassification.RECURRING_PATTERN == "recurring-pattern"


class TestAnalysisMethod:
    """Verify AnalysisMethod StrEnum values."""

    def test_none_value(self) -> None:
        """Verify NONE maps to 'none'."""
        assert AnalysisMethod.NONE == "none"

    def test_five_whys_value(self) -> None:
        """Verify FIVE_WHYS maps to '5-whys'."""
        assert AnalysisMethod.FIVE_WHYS == "5-whys"


# ---------------------------------------------------------------------------
# TASK_ID_PATTERN
# ---------------------------------------------------------------------------


class TestTaskIdPattern:
    """Verify the TASK_ID_PATTERN regex matches expected patterns.

    Tests: Task ID validation pattern.
    How: Test match/non-match for valid/invalid ID strings.
    Why: Invalid task IDs silently break dependency graph lookups.
    """

    @pytest.mark.parametrize("valid_id", ["1", "42", "1.1", "T1", "T2.3", "t99"])
    def test_valid_task_ids_match(self, valid_id: str) -> None:
        """Verify valid task IDs match the pattern."""
        assert TASK_ID_PATTERN.match(valid_id)

    @pytest.mark.parametrize("invalid_id", ["", "TT1", "T1a", "abc", "T", "1.2.3", "T-1"])
    def test_invalid_task_ids_do_not_match(self, invalid_id: str) -> None:
        """Verify invalid task IDs do not match the pattern."""
        assert not TASK_ID_PATTERN.match(invalid_id)


# ---------------------------------------------------------------------------
# STATUS_MAP
# ---------------------------------------------------------------------------


class TestStatusMap:
    """Verify STATUS_MAP contains expected normalization mappings."""

    def test_not_started_mapping(self) -> None:
        """Verify 'NOT STARTED' maps to 'not-started'."""
        assert STATUS_MAP["NOT STARTED"] == "not-started"

    def test_in_progress_mapping(self) -> None:
        """Verify 'IN PROGRESS' maps to 'in-progress'."""
        assert STATUS_MAP["IN PROGRESS"] == "in-progress"

    def test_complete_mapping(self) -> None:
        """Verify 'COMPLETE' maps to 'complete'."""
        assert STATUS_MAP["COMPLETE"] == "complete"

    def test_emoji_complete_mapping(self) -> None:
        """Verify ':white_check_mark:' emoji maps to 'complete'."""
        assert STATUS_MAP[":white_check_mark:"] == "complete"

    def test_emoji_not_started_mapping(self) -> None:
        """Verify ':x:' emoji maps to 'not-started'."""
        assert STATUS_MAP[":x:"] == "not-started"

    def test_deferred_marker_mapping(self) -> None:
        """Verify '[DEFERRED]' title marker maps to 'deferred'."""
        assert STATUS_MAP["[DEFERRED]"] == "deferred"

    def test_skipped_marker_mapping(self) -> None:
        """Verify '[SKIPPED]' title marker maps to 'skipped'."""
        assert STATUS_MAP["[SKIPPED]"] == "skipped"


# ---------------------------------------------------------------------------
# Task model — required fields
# ---------------------------------------------------------------------------


class TestTaskRequiredFields:
    """Verify Task model required field validation.

    Tests: id, title, status are mandatory and validated.
    How: Construct with valid/missing fields, check ValidationError.
    Why: Missing required fields must fail loud, not silently produce bad models.
    """

    def test_minimal_valid_task(self) -> None:
        """Verify Task with only required fields constructs successfully."""
        task = Task(id="T1", title="A task", status=TaskStatus.NOT_STARTED)
        assert task.id == "T1"
        assert task.title == "A task"
        assert task.status == TaskStatus.NOT_STARTED

    def test_missing_id_raises_validation_error(self) -> None:
        """Verify missing 'id' raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(title="No ID", status=TaskStatus.NOT_STARTED)

    def test_missing_title_raises_validation_error(self) -> None:
        """Verify missing 'title' raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(id="T1", status=TaskStatus.NOT_STARTED)

    def test_missing_status_raises_validation_error(self) -> None:
        """Verify missing 'status' raises ValidationError."""
        with pytest.raises(ValidationError):
            Task(id="T1", title="No status")  # type: ignore[call-arg]

    def test_empty_title_raises_validation_error(self) -> None:
        """Verify empty string title fails min_length=1 validation."""
        with pytest.raises(ValidationError):
            Task(id="T1", title="", status=TaskStatus.NOT_STARTED)

    def test_title_max_length_200_accepts_boundary(self) -> None:
        """Verify a 200-char title is accepted."""
        task = Task(id="T1", title="x" * 200, status=TaskStatus.NOT_STARTED)
        assert len(task.title) == 200

    def test_title_over_max_length_raises_validation_error(self) -> None:
        """Verify a 201-char title is rejected."""
        with pytest.raises(ValidationError):
            Task(id="T1", title="x" * 201, status=TaskStatus.NOT_STARTED)

    def test_invalid_id_pattern_raises_validation_error(self) -> None:
        """Verify an ID not matching the regex pattern is rejected."""
        with pytest.raises(ValidationError):
            Task(id="invalid-id", title="Bad ID", status=TaskStatus.NOT_STARTED)


# ---------------------------------------------------------------------------
# Task model — alias handling
# ---------------------------------------------------------------------------


class TestTaskAliasHandling:
    """Verify Task model populate_by_name and alias behavior.

    Tests: Kebab-case YAML aliases accepted alongside snake_case Python names.
    How: Construct via model_validate with alias keys.
    Why: Readers produce kebab-case dicts from YAML; model must accept both forms.
    """

    def test_populate_by_alias_blocked_by(self) -> None:
        """Verify 'blocked-by' alias populates blocked_by."""
        data = {"id": "T1", "title": "T", "status": "not-started", "blocked-by": ["T2"]}
        task = Task.model_validate(data)
        assert task.blocked_by == ["T2"]

    def test_populate_by_name_blocked_by(self) -> None:
        """Verify 'blocked_by' Python name also works."""
        task = Task.model_validate({"id": "T1", "title": "T", "status": "not-started", "blocked_by": ["T2"]})
        assert task.blocked_by == ["T2"]

    def test_populate_by_alias_last_activity(self) -> None:
        """Verify 'last-activity' alias populates last_activity."""
        ts = datetime.now(UTC)
        data = {"id": "T1", "title": "T", "status": "not-started", "last-activity": ts.isoformat()}
        task = Task.model_validate(data)
        assert task.last_activity is not None

    def test_populate_by_alias_github_issue(self) -> None:
        """Verify 'github-issue' alias populates github_issue."""
        data = {"id": "T1", "title": "T", "status": "not-started", "github-issue": 42}
        task = Task.model_validate(data)
        assert task.github_issue == 42

    def test_populate_by_alias_issue_classification(self) -> None:
        """Verify 'issue-classification' alias populates issue_classification."""
        data = {"id": "T1", "title": "T", "status": "not-started", "issue-classification": "defect"}
        task = Task.model_validate(data)
        assert task.issue_classification == IssueClassification.DEFECT

    def test_populate_by_alias_analysis_method(self) -> None:
        """Verify 'analysis-method' alias populates analysis_method."""
        data = {"id": "T1", "title": "T", "status": "not-started", "analysis-method": "5-whys"}
        task = Task.model_validate(data)
        assert task.analysis_method == AnalysisMethod.FIVE_WHYS

    def test_populate_by_alias_expected_outputs(self) -> None:
        """Verify 'expected-outputs' alias populates expected_outputs."""
        data = {"id": "T1", "title": "T", "status": "not-started", "expected-outputs": "file.py"}
        task = Task.model_validate(data)
        assert task.expected_outputs == "file.py"

    def test_populate_by_alias_divergence_notes(self) -> None:
        """Verify 'divergence-notes' alias populates divergence_notes."""
        data = {"id": "T1", "title": "T", "status": "not-started", "divergence-notes": 3}
        task = Task.model_validate(data)
        assert task.divergence_notes == 3


# ---------------------------------------------------------------------------
# Task model — enum coercion
# ---------------------------------------------------------------------------


class TestTaskEnumCoercion:
    """Verify Task model coerces string values to enum values.

    Tests: use_enum_values in model_config.
    How: Construct with string status, check the stored value type.
    Why: YAML readers pass strings, not enum members — coercion must work.
    """

    def test_status_string_coerced_to_enum_value(self) -> None:
        """Verify 'not-started' string is accepted as TaskStatus."""
        task = Task(id="T1", title="T", status="not-started")  # type: ignore[arg-type]
        assert task.status == TaskStatus.NOT_STARTED

    def test_priority_int_coerced_to_enum_value(self) -> None:
        """Verify integer priority is accepted as Priority."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED, priority=Priority(1))
        assert task.priority == Priority.CRITICAL

    def test_complexity_string_coerced_to_enum_value(self) -> None:
        """Verify 'high' string is accepted as Complexity."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED, complexity="high")  # type: ignore[arg-type]
        assert task.complexity == Complexity.HIGH


# ---------------------------------------------------------------------------
# Task model — field validators
# ---------------------------------------------------------------------------


class TestTaskFieldValidators:
    """Verify Task.validate_task_id_list field validator.

    Tests: dependencies and parallelize_with accept various input formats.
    How: Pass lists, comma-separated strings, None, and empty markers.
    Why: Legacy and YAML formats produce different dependency representations.
    """

    def test_dependencies_list_input(self) -> None:
        """Verify list of task IDs accepted."""
        task = Task(id="T2", title="T", status=TaskStatus.NOT_STARTED, dependencies=["T1"])
        assert task.dependencies == ["T1"]

    def test_dependencies_comma_separated_string(self) -> None:
        """Verify comma-separated string parsed into list."""
        data = {"id": "T3", "title": "T", "status": "not-started", "dependencies": "T1, T2"}
        task = Task.model_validate(data)
        assert task.dependencies == ["T1", "T2"]

    def test_dependencies_none_returns_empty_list(self) -> None:
        """Verify None dependency returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": None}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_dependencies_none_string_returns_empty_list(self) -> None:
        """Verify 'none' string returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": "none"}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_dependencies_na_string_returns_empty_list(self) -> None:
        """Verify 'n/a' string returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": "n/a"}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_dependencies_dash_string_returns_empty_list(self) -> None:
        """Verify '-' string returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": "-"}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_dependencies_empty_string_returns_empty_list(self) -> None:
        """Verify empty string returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": ""}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_dependencies_invalid_task_id_raises_validation_error(self) -> None:
        """Verify invalid task ID in dependency list raises ValueError."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": ["invalid-id"]}
        with pytest.raises(ValidationError):
            Task.model_validate(data)

    def test_dependencies_non_list_non_string_returns_empty(self) -> None:
        """Verify non-list, non-string input returns empty list."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": 42}
        task = Task.model_validate(data)
        assert task.dependencies == []

    def test_parallelize_with_comma_separated(self) -> None:
        """Verify parallelize_with accepts comma-separated string."""
        data = {"id": "T1", "title": "T", "status": "not-started", "parallelize-with": "T2,T3"}
        task = Task.model_validate(data)
        assert task.parallelize_with == ["T2", "T3"]

    def test_dependencies_list_with_none_items_filtered(self) -> None:
        """Verify None items in dependency list are filtered out."""
        data = {"id": "T1", "title": "T", "status": "not-started", "dependencies": [None, "T2", None]}
        task = Task.model_validate(data)
        assert task.dependencies == ["T2"]


# ---------------------------------------------------------------------------
# Task model — optional field defaults
# ---------------------------------------------------------------------------


class TestTaskDefaults:
    """Verify Task model optional field defaults.

    Tests: Default values for all optional fields.
    How: Construct minimal Task, check defaults.
    Why: Readers may omit fields — defaults must match schema expectations.
    """

    def test_default_agent_is_none(self) -> None:
        """Verify agent defaults to None."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.agent is None

    def test_default_dependencies_is_empty_list(self) -> None:
        """Verify dependencies defaults to empty list."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.dependencies == []

    def test_default_priority_is_medium(self) -> None:
        """Verify priority defaults to MEDIUM (3)."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.priority == Priority.MEDIUM

    def test_default_complexity_is_medium(self) -> None:
        """Verify complexity defaults to MEDIUM."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.complexity == Complexity.MEDIUM

    def test_default_skills_is_empty_list(self) -> None:
        """Verify skills defaults to empty list."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.skills == []

    def test_default_analysis_method_is_none(self) -> None:
        """Verify analysis_method defaults to NONE."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.analysis_method == AnalysisMethod.NONE

    def test_default_divergence_notes_is_zero(self) -> None:
        """Verify divergence_notes defaults to 0."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.divergence_notes == 0

    def test_default_description_is_empty_string(self) -> None:
        """Verify description defaults to empty string."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.description == ""

    def test_default_github_issue_is_none(self) -> None:
        """Verify github_issue defaults to None."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.github_issue is None

    def test_default_started_is_none(self) -> None:
        """Verify started defaults to None."""
        task = Task(id="T1", title="T", status=TaskStatus.NOT_STARTED)
        assert task.started is None


# ---------------------------------------------------------------------------
# Plan model
# ---------------------------------------------------------------------------


class TestPlanModel:
    """Verify Plan model construction and field defaults.

    Tests: Plan-level metadata model.
    How: Construct with valid/minimal data, check fields.
    Why: Plan wraps task lists — wrong defaults break plan-level queries.
    """

    def test_minimal_plan(self) -> None:
        """Verify Plan with only feature field constructs."""
        plan = Plan(feature="test-feature")
        assert plan.feature == "test-feature"
        assert plan.version == "1.0"
        assert plan.tasks == []

    def test_plan_with_tasks(self, sample_plan: Plan) -> None:
        """Verify Plan contains its tasks.

        Tests: Plan task list population.
        How: Use sample_plan fixture.
        Why: Empty task list is a regression indicator.
        """
        assert len(sample_plan.tasks) == 4

    def test_plan_default_description_is_empty(self) -> None:
        """Verify Plan description defaults to empty string."""
        plan = Plan(feature="test")
        assert plan.description == ""

    def test_plan_source_path_default_is_none(self) -> None:
        """Verify source_path defaults to None."""
        plan = Plan(feature="test")
        assert plan.source_path is None


# ---------------------------------------------------------------------------
# SchemaGap model
# ---------------------------------------------------------------------------


class TestSchemaGapModel:
    """Verify SchemaGap model construction.

    Tests: SchemaGap data model for gap reporting.
    How: Construct with valid data, check fields.
    Why: Gap reports are consumed by the normalizer to flag missing fields.
    """

    def test_schema_gap_construction(self) -> None:
        """Verify SchemaGap with all fields."""
        gap = SchemaGap(task_id="T1", field_name="agent", gap_type="missing", expected="Agent name")
        assert gap.task_id == "T1"
        assert gap.field_name == "agent"
        assert gap.gap_type == "missing"
        assert gap.actual is None

    def test_schema_gap_with_actual(self) -> None:
        """Verify SchemaGap with actual value populated."""
        gap = SchemaGap(task_id="T1", field_name="status", gap_type="invalid_type", expected="str", actual="42")
        assert gap.actual == "42"


# ---------------------------------------------------------------------------
# ReadResult model
# ---------------------------------------------------------------------------


class TestReadResultModel:
    """Verify ReadResult model construction.

    Tests: ReadResult wrapping a Plan with gaps and source info.
    How: Construct from Plan, verify all fields.
    Why: ReadResult is the return type from all load operations.
    """

    def test_read_result_construction(self, sample_plan: Plan) -> None:
        """Verify ReadResult wraps a Plan correctly."""
        result = ReadResult(plan=sample_plan, gaps=[], source_format="pure_yaml", source_path=Path("/fake/plan.yaml"))
        assert result.plan.feature == "test-feature"
        assert result.gaps == []
        assert result.source_format == "pure_yaml"

    def test_read_result_with_gaps(self) -> None:
        """Verify ReadResult includes schema gaps."""
        plan = Plan(feature="test")
        gap = SchemaGap(task_id="T1", field_name="agent", gap_type="missing", expected="Agent")
        result = ReadResult(plan=plan, gaps=[gap], source_format="legacy_markdown", source_path=Path("/fake"))
        assert len(result.gaps) == 1


# ---------------------------------------------------------------------------
# PlanStatus model
# ---------------------------------------------------------------------------


class TestPlanStatusModel:
    """Verify PlanStatus model construction.

    Tests: PlanStatus summary model.
    How: Construct with realistic data.
    Why: PlanStatus is consumed by CLI and MCP server for status output.
    """

    def test_plan_status_construction(self) -> None:
        """Verify PlanStatus with all fields."""
        status = PlanStatus(
            feature="test",
            total_tasks=3,
            by_status={"not-started": 1, "complete": 2},
            ready_tasks=["T2"],
            blocked_tasks=[],
            completion_pct=66.7,
            has_cycles=False,
        )
        assert status.feature == "test"
        assert status.total_tasks == 3
        assert abs(status.completion_pct - 66.7) < 0.1
        assert not status.has_cycles
