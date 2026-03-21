"""Tests for dispatch_schema.core.models.

Covers: valid construction of each model class, field alias acceptance (kebab-case
dict input), enum coercion, validation errors for missing required fields and
constraint violations, and default values for optional WaveItem fields.

Test naming: test_{model}_{scenario}_{expected_result}
Structure: AAA (Arrange / Act / Assert)
"""

from __future__ import annotations

import pytest
from dispatch_schema.core.models import (
    ConflictGroup,
    DispatchPlan,
    ItemPriority,
    ItemStatus,
    MilestoneHeader,
    QualityGates,
    Wave,
    WaveItem,
)
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# ItemPriority enum
# ---------------------------------------------------------------------------


class TestItemPriorityEnum:
    """ItemPriority StrEnum values and coercion behaviour."""

    def test_item_priority_all_values_are_accessible(self) -> None:
        """ItemPriority exposes P0-P3 as StrEnum members.

        Tests: ItemPriority enum membership.
        How: Access each member and compare string value.
        Why: Callers depend on exact string values for YAML serialization.
        """
        # Arrange / Act / Assert
        assert ItemPriority.P0 == "P0"
        assert ItemPriority.P1 == "P1"
        assert ItemPriority.P2 == "P2"
        assert ItemPriority.P3 == "P3"

    def test_item_priority_coerced_from_string_in_wave_item(self) -> None:
        """WaveItem accepts a plain string for priority and coerces to ItemPriority.

        Tests: StrEnum coercion via Pydantic.
        How: Construct WaveItem with priority as plain str; check type.
        Why: YAML parser returns strings; Pydantic must coerce them correctly.
        """
        # Arrange
        item = WaveItem(title="Fix bug", issue=1, priority="P2")  # ty: ignore[invalid-argument-type]

        # Act / Assert — use_enum_values=True means .priority is a str
        assert item.priority == "P2"

    @pytest.mark.parametrize("bad_value", ["P4", "p0", "HIGH", "", "0"])
    def test_item_priority_invalid_string_raises_validation_error(self, bad_value: str) -> None:
        """WaveItem raises ValidationError for a priority value not in ItemPriority.

        Tests: Enum validation rejection.
        How: Parametrize over invalid strings; assert ValidationError raised.
        Why: Data integrity — invalid priorities must not enter the model.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            WaveItem(title="Task", issue=1, priority=bad_value)  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# ItemStatus enum
# ---------------------------------------------------------------------------


class TestItemStatusEnum:
    """ItemStatus StrEnum values and coercion behaviour."""

    def test_item_status_all_values_are_defined(self) -> None:
        """ItemStatus exposes all five status strings.

        Tests: ItemStatus enum completeness.
        How: Compare each member's string value.
        Why: SAM hooks and YAML serialization depend on exact status strings.
        """
        # Arrange / Act / Assert
        assert ItemStatus.PENDING == "pending"
        assert ItemStatus.IN_PROGRESS == "in-progress"
        assert ItemStatus.COMPLETE == "complete"
        assert ItemStatus.FAILED == "failed"
        assert ItemStatus.SKIPPED == "skipped"

    @pytest.mark.parametrize("status_str", ["pending", "in-progress", "complete", "failed", "skipped"])
    def test_item_status_coerced_from_valid_string(self, status_str: str) -> None:
        """WaveItem accepts each valid ItemStatus string via Pydantic coercion.

        Tests: StrEnum coercion for all valid ItemStatus values.
        How: Parametrize over valid strings; construct WaveItem; check equality.
        Why: YAML reader supplies strings; they must round-trip through coercion.
        """
        # Arrange
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P1, status=status_str)  # ty: ignore[invalid-argument-type]

        # Act / Assert
        assert item.status == status_str

    def test_item_status_invalid_string_raises_validation_error(self) -> None:
        """WaveItem raises ValidationError for an unrecognised status string.

        Tests: ItemStatus rejection of unknown values.
        How: Pass 'unknown' as status; assert ValidationError raised.
        Why: Prevents garbage status values from silently entering the model.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            WaveItem(title="Task", issue=1, priority=ItemPriority.P1, status="unknown")  # ty: ignore[invalid-argument-type]


# ---------------------------------------------------------------------------
# MilestoneHeader
# ---------------------------------------------------------------------------


class TestMilestoneHeaderConstruction:
    """MilestoneHeader construction with snake_case and kebab-case aliases."""

    def test_milestone_header_valid_snake_case_construction(self) -> None:
        """MilestoneHeader accepts snake_case field names at construction time.

        Tests: MilestoneHeader valid construction.
        How: Construct with snake_case kwargs; assert all fields set.
        Why: Python callers use snake_case; model must accept it.
        """
        # Arrange / Act
        header = MilestoneHeader(number=5, title="Sprint 5", integration_branch="milestone/5")

        # Assert
        assert header.number == 5
        assert header.title == "Sprint 5"
        assert header.integration_branch == "milestone/5"

    def test_milestone_header_accepts_kebab_case_alias_via_model_validate(self) -> None:
        """MilestoneHeader.model_validate accepts kebab-case 'integration-branch' key.

        Tests: AliasChoices kebab-case input.
        How: Call model_validate with dict using 'integration-branch'.
        Why: YAML files use kebab-case; model_validate must coerce correctly.
        """
        # Arrange
        data = {"number": 2, "title": "Sprint 2", "integration-branch": "milestone/2"}

        # Act
        header = MilestoneHeader.model_validate(data)

        # Assert
        assert header.integration_branch == "milestone/2"

    @pytest.mark.parametrize("number", [0, -1, -100])
    def test_milestone_header_number_below_one_raises_validation_error(self, number: int) -> None:
        """MilestoneHeader rejects number values below the ge=1 constraint.

        Tests: ge=1 constraint on number field.
        How: Parametrize over invalid values; assert ValidationError raised.
        Why: Milestone numbers are positive GitHub milestone integers.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            MilestoneHeader(number=number, title="Sprint", integration_branch="milestone/1")

    def test_milestone_header_empty_title_raises_validation_error(self) -> None:
        """MilestoneHeader rejects an empty title string.

        Tests: min_length=1 constraint on title field.
        How: Pass empty string as title; assert ValidationError raised.
        Why: An empty title is not a valid milestone identifier.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            MilestoneHeader(number=1, title="", integration_branch="milestone/1")

    def test_milestone_header_missing_required_fields_raises_validation_error(self) -> None:
        """MilestoneHeader raises ValidationError when required fields are absent.

        Tests: Required field enforcement.
        How: Call model_validate with only 'number' provided.
        Why: All three fields are required; partial input must be rejected.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            MilestoneHeader.model_validate({"number": 1})


# ---------------------------------------------------------------------------
# ConflictGroup
# ---------------------------------------------------------------------------


class TestConflictGroupConstruction:
    """ConflictGroup construction including alias and constraint checks."""

    def test_conflict_group_valid_snake_case_construction(self) -> None:
        """ConflictGroup constructs correctly with snake_case field names.

        Tests: ConflictGroup valid construction.
        How: Supply all required fields with snake_case keys.
        Why: Validates basic model construction path.
        """
        # Arrange / Act
        group = ConflictGroup(group_id=1, reason="Shared file", items=["A", "B"])

        # Assert
        assert group.group_id == 1
        assert group.reason == "Shared file"
        assert group.items == ["A", "B"]

    def test_conflict_group_accepts_kebab_case_group_id_via_model_validate(self) -> None:
        """ConflictGroup.model_validate accepts 'group-id' kebab-case alias.

        Tests: AliasChoices for group_id field.
        How: Call model_validate with 'group-id' key in dict.
        Why: YAML uses kebab-case; alias must resolve to group_id attribute.
        """
        # Arrange
        data = {"group-id": 3, "reason": "Overlap", "items": ["X", "Y"]}

        # Act
        group = ConflictGroup.model_validate(data)

        # Assert
        assert group.group_id == 3

    def test_conflict_group_items_below_two_raises_validation_error(self) -> None:
        """ConflictGroup rejects an items list with fewer than two elements.

        Tests: min_length=2 constraint on items field.
        How: Pass a single-element list; assert ValidationError raised.
        Why: A conflict group with one item is semantically meaningless.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            ConflictGroup(group_id=1, reason="Single", items=["only-one"])

    def test_conflict_group_group_id_below_one_raises_validation_error(self) -> None:
        """ConflictGroup rejects group_id values below ge=1.

        Tests: ge=1 constraint on group_id.
        How: Pass 0 as group_id; assert ValidationError raised.
        Why: Group IDs are positive integers used as references.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            ConflictGroup(group_id=0, reason="Bad", items=["A", "B"])

    def test_conflict_group_empty_reason_raises_validation_error(self) -> None:
        """ConflictGroup rejects an empty reason string.

        Tests: min_length=1 constraint on reason field.
        How: Pass empty string as reason; assert ValidationError raised.
        Why: An empty reason provides no value for conflict analysis.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            ConflictGroup(group_id=1, reason="", items=["A", "B"])


# ---------------------------------------------------------------------------
# WaveItem
# ---------------------------------------------------------------------------


class TestWaveItemDefaults:
    """WaveItem default values for optional fields."""

    def test_wave_item_conflict_group_defaults_to_none(self) -> None:
        """WaveItem.conflict_group defaults to None when not provided.

        Tests: Default value for conflict_group.
        How: Construct WaveItem without conflict_group; assert None.
        Why: Most items are not in conflict groups.
        """
        # Arrange / Act
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P2)

        # Assert
        assert item.conflict_group is None

    def test_wave_item_depends_on_defaults_to_empty_list(self) -> None:
        """WaveItem.depends_on defaults to an empty list when not provided.

        Tests: Default value for depends_on.
        How: Construct WaveItem without depends_on; assert [].
        Why: Items without dependencies should have a stable empty list default.
        """
        # Arrange / Act
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P1)

        # Assert
        assert item.depends_on == []

    def test_wave_item_status_defaults_to_pending(self) -> None:
        """WaveItem.status defaults to ItemStatus.PENDING when not provided.

        Tests: Default value for status.
        How: Construct WaveItem without status; check value equals 'pending'.
        Why: All newly created items start in pending state.
        """
        # Arrange / Act
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P0)

        # Assert — use_enum_values=True means .status is a plain str
        assert item.status == "pending"

    def test_wave_item_depends_on_default_is_independent_per_instance(self) -> None:
        """WaveItem.depends_on uses default_factory, so each instance gets its own list.

        Tests: Mutable default isolation via default_factory.
        How: Create two WaveItems; append to first; assert second is unchanged.
        Why: Shared mutable defaults cause subtle cross-instance contamination bugs.
        """
        # Arrange
        item_a = WaveItem(title="A", issue=1, priority=ItemPriority.P1)
        item_b = WaveItem(title="B", issue=2, priority=ItemPriority.P1)

        # Act
        item_a.depends_on.append(99)

        # Assert
        assert item_b.depends_on == []


class TestWaveItemKebabCaseAliases:
    """WaveItem accepts kebab-case keys for aliased fields via model_validate."""

    def test_wave_item_accepts_conflict_group_kebab_alias(self) -> None:
        """WaveItem.model_validate accepts 'conflict-group' kebab-case alias.

        Tests: AliasChoices for conflict_group field.
        How: Use model_validate with 'conflict-group' key.
        Why: YAML reader supplies kebab-case dicts; alias must map correctly.
        """
        # Arrange
        data = {"title": "Task", "issue": 5, "priority": "P1", "conflict-group": 2}

        # Act
        item = WaveItem.model_validate(data)

        # Assert
        assert item.conflict_group == 2

    def test_wave_item_accepts_depends_on_kebab_alias(self) -> None:
        """WaveItem.model_validate accepts 'depends-on' kebab-case alias.

        Tests: AliasChoices for depends_on field.
        How: Use model_validate with 'depends-on' key.
        Why: YAML files use 'depends-on'; alias must populate depends_on list.
        """
        # Arrange
        data = {"title": "Task", "issue": 7, "priority": "P3", "depends-on": [3, 4]}

        # Act
        item = WaveItem.model_validate(data)

        # Assert
        assert item.depends_on == [3, 4]


class TestWaveItemConstraints:
    """WaveItem field constraint violations raise ValidationError."""

    def test_wave_item_issue_below_one_raises_validation_error(self) -> None:
        """WaveItem rejects issue numbers below ge=1.

        Tests: ge=1 constraint on issue field.
        How: Pass 0 as issue; assert ValidationError raised.
        Why: GitHub issue numbers are positive integers.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            WaveItem(title="Task", issue=0, priority=ItemPriority.P1)

    def test_wave_item_empty_title_raises_validation_error(self) -> None:
        """WaveItem rejects an empty title string.

        Tests: min_length=1 constraint on title field.
        How: Pass empty string as title; assert ValidationError raised.
        Why: An untitled item cannot be identified or dispatched.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            WaveItem(title="", issue=1, priority=ItemPriority.P2)


# ---------------------------------------------------------------------------
# Wave
# ---------------------------------------------------------------------------


class TestWaveConstruction:
    """Wave construction and constraint validation."""

    def test_wave_valid_construction(self) -> None:
        """Wave constructs correctly with wave number, parallel flag, and items.

        Tests: Wave valid construction.
        How: Construct Wave with one WaveItem; assert all fields populated.
        Why: Wave is a structural container; basic construction must work.
        """
        # Arrange
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P1)

        # Act
        wave = Wave(wave=1, parallel=True, items=[item])

        # Assert
        assert wave.wave == 1
        assert wave.parallel is True
        assert len(wave.items) == 1

    def test_wave_number_below_one_raises_validation_error(self) -> None:
        """Wave rejects wave numbers below ge=1.

        Tests: ge=1 constraint on wave field.
        How: Pass 0 as wave number; assert ValidationError raised.
        Why: Wave sequence is 1-based; wave 0 has no defined semantics.
        """
        # Arrange
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P1)

        # Act / Assert
        with pytest.raises(ValidationError):
            Wave(wave=0, parallel=True, items=[item])

    def test_wave_empty_items_raises_validation_error(self) -> None:
        """Wave rejects an empty items list.

        Tests: min_length=1 constraint on items field.
        How: Pass empty list as items; assert ValidationError raised.
        Why: An empty wave is meaningless in dispatch scheduling.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValidationError):
            Wave(wave=1, parallel=True, items=[])

    def test_wave_parallel_defaults_to_true(self) -> None:
        """Wave.parallel defaults to True when not supplied.

        Tests: Default value for parallel field.
        How: Construct Wave without parallel kwarg; assert True.
        Why: Most waves run in parallel; True is the correct default.
        """
        # Arrange
        item = WaveItem(title="Task", issue=1, priority=ItemPriority.P0)

        # Act
        wave = Wave(wave=1, items=[item])

        # Assert
        assert wave.parallel is True


# ---------------------------------------------------------------------------
# QualityGates
# ---------------------------------------------------------------------------


class TestQualityGatesConstruction:
    """QualityGates construction and defaults."""

    def test_quality_gates_default_empty_lists(self) -> None:
        """QualityGates constructs with empty pre_merge and post_merge lists by default.

        Tests: Default values for pre_merge and post_merge.
        How: Construct QualityGates with no arguments; assert both empty.
        Why: Quality gates are optional; empty defaults prevent None-check boilerplate.
        """
        # Arrange / Act
        gates = QualityGates()

        # Assert
        assert gates.pre_merge == []
        assert gates.post_merge == []

    def test_quality_gates_accepts_kebab_case_pre_merge_alias(self) -> None:
        """QualityGates.model_validate accepts 'pre-merge' kebab-case alias.

        Tests: AliasChoices for pre_merge field.
        How: Call model_validate with 'pre-merge' key.
        Why: YAML files use kebab-case; alias must map to pre_merge attribute.
        """
        # Arrange
        data = {"pre-merge": ["uv run pytest"], "post-merge": []}

        # Act
        gates = QualityGates.model_validate(data)

        # Assert
        assert gates.pre_merge == ["uv run pytest"]

    def test_quality_gates_accepts_kebab_case_post_merge_alias(self) -> None:
        """QualityGates.model_validate accepts 'post-merge' kebab-case alias.

        Tests: AliasChoices for post_merge field.
        How: Call model_validate with 'post-merge' key.
        Why: Symmetric to pre-merge — both must be aliased identically.
        """
        # Arrange
        data = {"post-merge": ["uv run pytest --integration"]}

        # Act
        gates = QualityGates.model_validate(data)

        # Assert
        assert gates.post_merge == ["uv run pytest --integration"]


# ---------------------------------------------------------------------------
# DispatchPlan
# ---------------------------------------------------------------------------


class TestDispatchPlanConstruction:
    """DispatchPlan top-level model construction and defaults."""

    def test_dispatch_plan_valid_minimal_construction(self, simple_plan: DispatchPlan) -> None:
        """DispatchPlan constructs correctly given a minimal valid set of fields.

        Tests: DispatchPlan minimal valid construction.
        How: Use conftest simple_plan fixture; assert milestone and waves present.
        Why: Verifies the root model integrates its submodels correctly.
        """
        # Arrange (via fixture) / Act (construction in fixture) / Assert
        assert simple_plan.milestone.number == 1
        assert len(simple_plan.waves) == 1
        assert simple_plan.conflict_groups == []
        # quality_gates uses default_factory=QualityGates — always an instance, never None
        assert simple_plan.quality_gates.pre_merge == []
        assert simple_plan.quality_gates.post_merge == []

    def test_dispatch_plan_with_all_optional_fields(self, two_wave_plan: DispatchPlan) -> None:
        """DispatchPlan constructs with conflict_groups and quality_gates populated.

        Tests: DispatchPlan full construction with optional fields.
        How: Use conftest two_wave_plan fixture; assert optional fields set.
        Why: Ensures the root model correctly accepts all optional submodels.
        """
        # Arrange (via fixture) / Act / Assert
        assert len(two_wave_plan.conflict_groups) == 1
        assert two_wave_plan.quality_gates is not None
        assert two_wave_plan.quality_gates.pre_merge == ["uv run pytest"]

    def test_dispatch_plan_missing_milestone_raises_validation_error(self) -> None:
        """DispatchPlan raises ValidationError when milestone is absent.

        Tests: Required field enforcement on milestone.
        How: Call model_validate without milestone key; assert ValidationError.
        Why: milestone is required — a plan without it cannot be processed.
        """
        # Arrange
        data = {"waves": [{"wave": 1, "items": [{"title": "T", "issue": 1, "priority": "P1"}]}]}

        # Act / Assert
        with pytest.raises(ValidationError):
            DispatchPlan.model_validate(data)

    def test_dispatch_plan_missing_waves_raises_validation_error(self) -> None:
        """DispatchPlan raises ValidationError when waves is absent.

        Tests: Required field enforcement on waves.
        How: Call model_validate without waves key; assert ValidationError.
        Why: A dispatch plan with no waves has no executable content.
        """
        # Arrange
        data = {"milestone": {"number": 1, "title": "Sprint", "integration-branch": "milestone/1"}}

        # Act / Assert
        with pytest.raises(ValidationError):
            DispatchPlan.model_validate(data)

    def test_dispatch_plan_conflict_groups_defaults_to_empty_list(self) -> None:
        """DispatchPlan.conflict_groups defaults to an empty list.

        Tests: Default value for conflict_groups.
        How: Construct DispatchPlan without conflict_groups; assert [].
        Why: Plans without conflicts are valid; empty list is the correct default.
        """
        # Arrange
        plan = DispatchPlan(
            milestone=MilestoneHeader(number=1, title="Sprint", integration_branch="milestone/1"),
            waves=[Wave(wave=1, items=[WaveItem(title="T", issue=1, priority=ItemPriority.P1)])],
        )

        # Assert
        assert plan.conflict_groups == []

    def test_dispatch_plan_accepts_kebab_case_conflict_groups_alias(self) -> None:
        """DispatchPlan.model_validate accepts 'conflict-groups' kebab-case alias.

        Tests: AliasChoices for conflict_groups field.
        How: Call model_validate with 'conflict-groups' key in dict.
        Why: YAML files use kebab-case; top-level keys must also be aliased.
        """
        # Arrange
        data = {
            "milestone": {"number": 1, "title": "S", "integration-branch": "milestone/1"},
            "conflict-groups": [{"group-id": 1, "reason": "Overlap", "items": ["A", "B"]}],
            "waves": [{"wave": 1, "items": [{"title": "A", "issue": 1, "priority": "P1"}]}],
        }

        # Act
        plan = DispatchPlan.model_validate(data)

        # Assert
        assert len(plan.conflict_groups) == 1
        assert plan.conflict_groups[0].group_id == 1
