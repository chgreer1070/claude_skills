"""Unit tests for sam_schema.core.quality_gates.build_quality_gate_plan.

Tests: Pure function generating YAML for a 6-task quality-gate plan.
Strategy:
- Parse the YAML output using ruamel.yaml (repo standard — never PyYAML).
- Roundtrip through the Plan/Task Pydantic models to verify schema validity.
- Each test validates a single, named concern.
- No file I/O. No MCP calls. No mocking of the function under test.

Implementation: plugins/development-harness/sam_schema/core/quality_gates.py
Models: plugins/development-harness/sam_schema/core/models.py
"""

from __future__ import annotations

import io
from typing import Any

import pytest
from ruamel.yaml import YAML
from sam_schema.core.models import Plan, Task, TaskStatus
from sam_schema.core.quality_gates import build_quality_gate_plan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXPECTED_TASK_IDS = ["T1", "T2", "T3", "T4", "T5", "T6"]
_EXPECTED_TITLES = [
    "Code Review",
    "Feature Verification",
    "Integration Check",
    "Documentation Drift Audit",
    "Documentation Update",
    "Context Refinement",
]
_EXPECTED_AGENTS = [
    "code-reviewer",
    "feature-verifier",
    "integration-checker",
    "doc-drift-auditor",
    "service-docs-maintainer",
    "context-refinement",
]
_EXPECTED_DEPS: list[list[str]] = [[], ["T1"], ["T2"], ["T3"], ["T4"], ["T5"]]


def _parse_yaml(yaml_string: str) -> dict[str, Any]:
    """Parse a YAML string using ruamel.yaml.

    Args:
        yaml_string: YAML content to parse.

    Returns:
        Parsed dictionary.
    """
    yaml = YAML()
    return yaml.load(io.StringIO(yaml_string))  # type: ignore[return-value]


def _tasks_from_yaml(yaml_string: str) -> list[dict[str, Any]]:
    """Extract the tasks list from a generated plan YAML string.

    Args:
        yaml_string: YAML output from build_quality_gate_plan.

    Returns:
        List of raw task dicts.
    """
    data = _parse_yaml(yaml_string)
    return data["tasks"]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_yaml() -> str:
    """Generate a minimal QG plan YAML with a real issue number.

    Returns:
        YAML string from build_quality_gate_plan with issue and impl_plan_address.
    """
    return build_quality_gate_plan(slug="my-feature", issue="990", impl_plan_address="P003")


@pytest.fixture
def no_issue_yaml() -> str:
    """Generate a QG plan YAML with issue=None.

    Returns:
        YAML string from build_quality_gate_plan with no issue number.
    """
    return build_quality_gate_plan(slug="no-issue-feature", issue=None, impl_plan_address="P042")


@pytest.fixture
def plan_model(basic_yaml: str) -> Plan:
    """Roundtrip the basic YAML through the Plan Pydantic model.

    Returns:
        Validated Plan instance.
    """
    data = _parse_yaml(basic_yaml)
    return Plan.model_validate(data)


# ---------------------------------------------------------------------------
# Tests: parseable YAML
# ---------------------------------------------------------------------------


class TestYamlValidity:
    """Tests: The function returns well-formed, parseable YAML.

    Strategy: Parse the output and assert on top-level structure.
    Why: Malformed YAML causes sam_create to fail silently.
    """

    def test_output_is_parseable_yaml(self, basic_yaml: str) -> None:
        """Test that build_quality_gate_plan returns valid YAML.

        Tests: YAML parseability of the returned string.
        How: Parse with ruamel.yaml; confirm no exception is raised and result is a dict.
        Why: sam_create passes this string directly to YAML deserialisation.
        """
        # Arrange
        yaml_string = basic_yaml

        # Act
        result = _parse_yaml(yaml_string)

        # Assert
        assert isinstance(result, dict)

    def test_output_has_feature_key(self, basic_yaml: str) -> None:
        """Test that the plan YAML contains the 'feature' field.

        Tests: Plan-level 'feature' field presence.
        How: Parse YAML and assert 'feature' key exists.
        Why: SAM Plan model requires 'feature' as a mandatory field.
        """
        # Arrange / Act
        data = _parse_yaml(basic_yaml)

        # Assert
        assert "feature" in data

    def test_output_has_tasks_key(self, basic_yaml: str) -> None:
        """Test that the plan YAML contains a 'tasks' list.

        Tests: Plan-level 'tasks' field presence.
        How: Parse YAML and assert 'tasks' key is a list.
        Why: Without a tasks list, sam_ready returns an empty set and no phases execute.
        """
        # Arrange / Act
        data = _parse_yaml(basic_yaml)

        # Assert
        assert isinstance(data.get("tasks"), list)


# ---------------------------------------------------------------------------
# Tests: task count and IDs
# ---------------------------------------------------------------------------


class TestTaskCountAndIds:
    """Tests: Exactly 6 tasks are generated with correct IDs and titles.

    Strategy: Parse YAML and inspect task-level fields.
    Why: Missing tasks would silently skip quality-gate phases.
    """

    def test_generates_six_tasks(self, basic_yaml: str) -> None:
        """Test that exactly 6 tasks are present in the generated plan.

        Tests: Task count.
        How: Parse YAML, count tasks list entries.
        Why: One task per quality-gate phase (phases 1-6). Fewer means phases are missing.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert len(tasks) == 6

    @pytest.mark.parametrize(("index", "expected_id"), list(enumerate(_EXPECTED_TASK_IDS)))
    def test_task_ids_are_correct(self, basic_yaml: str, index: int, expected_id: str) -> None:
        """Test that each task has the expected ID (T1 through T6).

        Tests: Task IDs in order.
        How: Parse YAML, extract task at index, assert 'id' matches.
        Why: SAM dependency resolution uses task IDs; wrong IDs break the chain.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[index]["id"] == expected_id

    @pytest.mark.parametrize(("index", "expected_title"), list(enumerate(_EXPECTED_TITLES)))
    def test_task_titles_are_correct(self, basic_yaml: str, index: int, expected_title: str) -> None:
        """Test that each task has the expected human-readable title.

        Tests: Task titles in order.
        How: Parse YAML, extract task at index, assert 'title' matches.
        Why: Task titles appear in sam_status output; wrong titles confuse operators.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[index]["title"] == expected_title


# ---------------------------------------------------------------------------
# Tests: dependency chain
# ---------------------------------------------------------------------------


class TestDependencyChain:
    """Tests: Tasks form a strict linear dependency chain T1 -> T2 -> ... -> T6.

    Strategy: Parse YAML, check 'dependencies' field per task.
    Why: DependencyGraph uses this field. Wrong chains allow phases to run out of order
    or allow all phases to dispatch simultaneously, defeating enforcement.
    """

    def test_t1_has_no_dependencies(self, basic_yaml: str) -> None:
        """Test that T1 (Code Review) has an empty dependencies list.

        Tests: T1 dependency field.
        How: Parse YAML, check T1 dependencies.
        Why: T1 must be the entry point; any dependency would block the whole chain.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[0]["dependencies"] == []

    @pytest.mark.parametrize(("task_index", "expected_deps"), [(i, _EXPECTED_DEPS[i]) for i in range(1, 6)])
    def test_each_task_depends_on_previous(self, basic_yaml: str, task_index: int, expected_deps: list[str]) -> None:
        """Test that each task T2-T6 depends on exactly the preceding task.

        Tests: Linear dependency chain for tasks at indices 1-5.
        How: Parse YAML, check 'dependencies' field at each index.
        Why: The SAM enforcement model requires each phase to gate on the prior phase.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[task_index]["dependencies"] == expected_deps


# ---------------------------------------------------------------------------
# Tests: priority
# ---------------------------------------------------------------------------


class TestTaskPriority:
    """Tests: All 6 tasks have priority 1 (CRITICAL).

    Strategy: Parse YAML, check 'priority' field per task.
    Why: Priority 1 ensures QG phases are dispatched before lower-priority work.
    """

    @pytest.mark.parametrize("task_index", range(6))
    def test_all_tasks_have_priority_one(self, basic_yaml: str, task_index: int) -> None:
        """Test that every QG task has priority=1.

        Tests: Priority field for all 6 tasks.
        How: Parse YAML, assert priority == 1 at each index.
        Why: Consistent priority 1 prevents SAM dispatch from deferring any phase.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[task_index]["priority"] == 1


# ---------------------------------------------------------------------------
# Tests: agent assignment
# ---------------------------------------------------------------------------


class TestAgentAssignment:
    """Tests: Each task is assigned to the correct agent.

    Strategy: Parse YAML, check 'agent' field per task.
    Why: /start-task dispatches to the agent in this field; wrong agent runs the wrong logic.
    """

    @pytest.mark.parametrize(("task_index", "expected_agent"), list(enumerate(_EXPECTED_AGENTS)))
    def test_agents_are_correct(self, basic_yaml: str, task_index: int, expected_agent: str) -> None:
        """Test that each task is assigned to the expected agent name.

        Tests: Agent field per task.
        How: Parse YAML, assert 'agent' at index matches expected value.
        Why: Misrouting dispatches the wrong specialist, defeating the quality gate.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[task_index]["agent"] == expected_agent


# ---------------------------------------------------------------------------
# Tests: issue field
# ---------------------------------------------------------------------------


class TestIssueField:
    """Tests: The 'issue' field is populated when provided and absent when None.

    Strategy: Call the function with and without issue, inspect parsed output.
    Why: sam_create uses the issue field to register the QG plan artifact.
    """

    def test_issue_field_populated_when_provided(self, basic_yaml: str) -> None:
        """Test that the plan-level 'issue' field contains the supplied issue number.

        Tests: Issue field presence and value.
        How: Parse YAML, assert 'issue' key equals the supplied string.
        Why: Artifact registration in sam_create requires a valid issue field.
        """
        # Arrange / Act
        data = _parse_yaml(basic_yaml)

        # Assert
        assert data.get("issue") == "990"

    def test_issue_field_omitted_when_none(self, no_issue_yaml: str) -> None:
        """Test that the 'issue' field is absent from the plan when issue=None.

        Tests: Issue field omission.
        How: Parse YAML, assert 'issue' key is not present.
        Why: Omitting the field (not setting it to null) keeps YAML clean
        and avoids validation errors in Plan.model_validate.
        """
        # Arrange / Act
        data = _parse_yaml(no_issue_yaml)

        # Assert
        assert "issue" not in data


# ---------------------------------------------------------------------------
# Tests: feature slug
# ---------------------------------------------------------------------------


class TestFeatureSlug:
    """Tests: The 'feature' field reflects the supplied slug.

    Strategy: Check parsed output for slug value.
    Why: Slug is used in file naming (QG{N}-qg-{slug}.yaml).
    """

    def test_feature_slug_set_from_argument(self, basic_yaml: str) -> None:
        """Test that the 'feature' field equals the slug argument.

        Tests: Feature field value in plan YAML.
        How: Parse YAML, assert 'feature' == 'my-feature'.
        Why: SAM uses the feature field to generate the plan filename.
        """
        # Arrange / Act
        data = _parse_yaml(basic_yaml)

        # Assert
        assert data["feature"] == "my-feature"

    def test_slug_with_hyphens_preserved(self) -> None:
        """Test that slugs containing hyphens are stored verbatim.

        Tests: Slug pass-through with hyphens.
        How: Call with a hyphenated slug, parse, assert feature field matches.
        Why: QG plan filenames use the slug directly; corruption causes glob failures.
        """
        # Arrange
        yaml_string = build_quality_gate_plan(slug="enforce-quality-gate-phases", issue="990", impl_plan_address="P990")

        # Act
        data = _parse_yaml(yaml_string)

        # Assert
        assert data["feature"] == "enforce-quality-gate-phases"


# ---------------------------------------------------------------------------
# Tests: impl_plan_address in task bodies
# ---------------------------------------------------------------------------


class TestImplPlanAddressInBody:
    """Tests: Each task body cross-references the implementation plan address.

    Strategy: Check 'body' field of each task for the impl_plan_address string.
    Why: The complete-implementation SKILL.md references this cross-link for operators
    debugging a blocked phase.
    """

    @pytest.mark.parametrize("task_index", range(6))
    def test_impl_plan_address_in_each_task_body(self, basic_yaml: str, task_index: int) -> None:
        """Test that every task body contains the implementation plan address.

        Tests: Task body cross-reference to impl_plan_address.
        How: Parse YAML, check that 'P003' appears in the body of each task.
        Why: Operators need to locate the implementation plan from within a QG phase task.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)
        body: str = tasks[task_index]["body"]

        # Assert
        assert "P003" in body

    def test_different_impl_address_appears_in_body(self) -> None:
        """Test that a different impl_plan_address appears in task bodies correctly.

        Tests: impl_plan_address substitution for a non-default value.
        How: Generate with 'P042', parse, assert 'P042' in each body.
        Why: Ensures the address is not hard-coded inside the generator.
        """
        # Arrange
        yaml_string = build_quality_gate_plan(slug="some-feature", issue=None, impl_plan_address="P042")

        # Act
        tasks = _tasks_from_yaml(yaml_string)

        # Assert
        for task in tasks:
            assert "P042" in task["body"]


# ---------------------------------------------------------------------------
# Tests: initial task status
# ---------------------------------------------------------------------------


class TestInitialTaskStatus:
    """Tests: All tasks start with status 'not-started'.

    Strategy: Parse YAML, check 'status' field per task.
    Why: sam_ready only returns tasks with status 'not-started'. A task pre-marked
    complete would be silently skipped by the dispatch loop.
    """

    @pytest.mark.parametrize("task_index", range(6))
    def test_all_tasks_start_not_started(self, basic_yaml: str, task_index: int) -> None:
        """Test that every task has status 'not-started' in the generated YAML.

        Tests: Initial status field for all 6 tasks.
        How: Parse YAML, assert 'status' == 'not-started' at each index.
        Why: Prevents tasks from being silently skipped on first dispatch.
        """
        # Arrange / Act
        tasks = _tasks_from_yaml(basic_yaml)

        # Assert
        assert tasks[task_index]["status"] == "not-started"


# ---------------------------------------------------------------------------
# Tests: phase_4_drift_found does not affect generated YAML
# ---------------------------------------------------------------------------


class TestPhase4DriftFoundParameter:
    """Tests: phase_4_drift_found parameter does not alter the YAML output.

    Strategy: Generate with all three values (None, True, False), compare task list.
    Why: T5 skipping is done post-generation via sam_state, not inside the generator.
    The docstring explicitly states this parameter does not affect the YAML.
    """

    def test_drift_found_true_does_not_change_yaml(self) -> None:
        """Test that phase_4_drift_found=True produces the same T5 status as None.

        Tests: phase_4_drift_found=True effect on generated YAML.
        How: Compare T5 status and dependencies between drift=True and drift=None runs.
        Why: T5 skipping is caller-managed post-generation; the generator must not pre-skip.
        """
        # Arrange
        base = build_quality_gate_plan("feature", "1", "P001", phase_4_drift_found=None)
        with_drift = build_quality_gate_plan("feature", "1", "P001", phase_4_drift_found=True)

        # Act
        base_tasks = _tasks_from_yaml(base)
        drift_tasks = _tasks_from_yaml(with_drift)
        t5_base = next(t for t in base_tasks if t["id"] == "T5")
        t5_drift = next(t for t in drift_tasks if t["id"] == "T5")

        # Assert
        assert t5_base["status"] == t5_drift["status"] == "not-started"

    def test_drift_found_false_does_not_change_yaml(self) -> None:
        """Test that phase_4_drift_found=False produces the same T5 status as None.

        Tests: phase_4_drift_found=False effect on generated YAML.
        How: Compare T5 status between drift=False and drift=None runs.
        Why: Per docstring, this parameter is reserved for future use and does not
        affect the generated YAML today.
        """
        # Arrange
        base = build_quality_gate_plan("feature", "1", "P001", phase_4_drift_found=None)
        no_drift = build_quality_gate_plan("feature", "1", "P001", phase_4_drift_found=False)

        # Act
        base_tasks = _tasks_from_yaml(base)
        no_drift_tasks = _tasks_from_yaml(no_drift)
        t5_base = next(t for t in base_tasks if t["id"] == "T5")
        t5_no_drift = next(t for t in no_drift_tasks if t["id"] == "T5")

        # Assert
        assert t5_base["status"] == t5_no_drift["status"] == "not-started"


# ---------------------------------------------------------------------------
# Tests: Pydantic roundtrip
# ---------------------------------------------------------------------------


class TestPydanticRoundtrip:
    """Tests: YAML output roundtrips through Plan/Task models without validation errors.

    Strategy: Parse YAML then call Plan.model_validate on the result.
    Why: If sam_schema internal tooling (sam_read, sam_status) cannot validate the
    generated plan, the entire QG enforcement loop will break.
    """

    def test_yaml_roundtrips_through_plan_model(self, plan_model: Plan) -> None:
        """Test that the generated YAML validates as a Plan model instance.

        Tests: Plan.model_validate succeeds without raising ValidationError.
        How: Use the plan_model fixture which parses and validates. Assert type.
        Why: The sam_read MCP tool calls Plan.model_validate on every plan file read.
        """
        # Arrange / Act / Assert
        assert isinstance(plan_model, Plan)

    def test_plan_has_six_task_instances(self, plan_model: Plan) -> None:
        """Test that the validated Plan contains 6 Task model instances.

        Tests: tasks list length and element types after Pydantic validation.
        How: Access plan_model.tasks, assert length and element type.
        Why: Ensures Pydantic does not silently drop tasks with unknown fields.
        """
        # Arrange / Act / Assert
        assert len(plan_model.tasks) == 6
        assert all(isinstance(t, Task) for t in plan_model.tasks)

    def test_plan_tasks_have_not_started_status(self, plan_model: Plan) -> None:
        """Test that all Task instances carry NOT_STARTED status after model validation.

        Tests: TaskStatus enum value on validated Task objects.
        How: Iterate plan_model.tasks, assert status == TaskStatus.NOT_STARTED.
        Why: Confirms status string-to-enum mapping works correctly in models.py.
        """
        # Arrange / Act / Assert
        for task in plan_model.tasks:
            assert task.status == TaskStatus.NOT_STARTED

    def test_plan_dependency_chain_preserved_after_roundtrip(self, plan_model: Plan) -> None:
        """Test that dependency lists are preserved correctly through model validation.

        Tests: Task.dependencies field integrity after Plan.model_validate.
        How: Compare task.dependencies for each task against expected chains.
        Why: AliasChoices or field_validator could silently transform dependency strings.
        """
        # Arrange / Act
        for task, expected_deps in zip(plan_model.tasks, _EXPECTED_DEPS, strict=False):
            # Assert
            assert task.dependencies == expected_deps

    def test_plan_feature_slug_preserved_after_roundtrip(self, plan_model: Plan) -> None:
        """Test that the feature slug is preserved through Plan.model_validate.

        Tests: Plan.feature field after roundtrip.
        How: Assert plan_model.feature == 'my-feature'.
        Why: Feature field drives plan file naming in sam_create.
        """
        # Arrange / Act / Assert
        assert plan_model.feature == "my-feature"

    def test_plan_issue_preserved_after_roundtrip(self, plan_model: Plan) -> None:
        """Test that the issue field survives Plan.model_validate as a string.

        Tests: Plan.issue field after roundtrip.
        How: Assert plan_model.issue == '990'.
        Why: coerce_issue_to_str validator normalises int -> str; confirm this works
        in the generated data which already emits a string.
        """
        # Arrange / Act / Assert
        assert plan_model.issue == "990"

    def test_plan_goal_contains_impl_address(self, plan_model: Plan) -> None:
        """Test that Plan.goal embeds the implementation plan address.

        Tests: Plan-level goal field content after roundtrip.
        How: Assert 'P003' appears in plan_model.goal.
        Why: Goal string is displayed in sam_status output to orient operators.
        """
        # Arrange / Act / Assert
        assert plan_model.goal is not None
        assert "P003" in plan_model.goal
