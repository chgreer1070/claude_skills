"""Tests for dispatch_schema.writers.yaml_writer.

Covers: write_dispatch_plan() happy path, kebab-case key output, atomic rename
behaviour (no partial file on failure), parent directory creation, symlink
rejection, and the internal _keys_to_kebab helper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from dispatch_schema.core.models import (
    ConflictGroup,
    DispatchPlan,
    ItemPriority,
    MilestoneHeader,
    QualityGates,
    Wave,
    WaveItem,
)
from dispatch_schema.writers.yaml_writer import _keys_to_kebab, write_dispatch_plan

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_plan() -> DispatchPlan:
    """Return a minimal valid DispatchPlan with one wave and one conflict group."""
    return DispatchPlan(
        milestone=MilestoneHeader(number=3, title="Test Milestone", integration_branch="milestone/3-test"),
        conflict_groups=[ConflictGroup(group_id=1, reason="overlapping files", items=["A", "B"])],
        waves=[Wave(wave=1, parallel=True, items=[WaveItem(title="Issue One", issue=100, priority=ItemPriority.P1)])],
        quality_gates=QualityGates(pre_merge=["make test"], post_merge=[]),
    )


@pytest.fixture
def plan_with_nested_fields() -> DispatchPlan:
    """Return a plan with fields that have kebab-case aliases (depends_on, conflict_group)."""
    return DispatchPlan(
        milestone=MilestoneHeader(number=1, title="Nested Field Milestone", integration_branch="milestone/1-nested"),
        conflict_groups=[ConflictGroup(group_id=2, reason="shared model", items=["C", "D", "E"])],
        waves=[
            Wave(
                wave=1,
                parallel=False,
                items=[
                    WaveItem(
                        title="Dependent Issue", issue=200, priority=ItemPriority.P0, conflict_group=2, depends_on=[100]
                    )
                ],
            )
        ],
        quality_gates=QualityGates(pre_merge=[], post_merge=["make verify"]),
    )


# ---------------------------------------------------------------------------
# _keys_to_kebab unit tests
# ---------------------------------------------------------------------------


def test_keys_to_kebab_flat_dict_converts_underscores():
    # Arrange
    data = {"conflict_groups": [], "quality_gates": {}}
    # Act
    result = _keys_to_kebab(data)
    # Assert
    assert "conflict-groups" in result
    assert "quality-gates" in result
    assert "conflict_groups" not in result


def test_keys_to_kebab_nested_dict_converts_recursively():
    # Arrange
    data = {"outer_key": {"inner_key": "value", "another_key": 1}}
    # Act
    result = _keys_to_kebab(data)
    # Assert
    assert "outer-key" in result
    assert "inner-key" in result["outer-key"]
    assert "another-key" in result["outer-key"]


def test_keys_to_kebab_list_of_dicts_converts_each_item():
    # Arrange
    data = [{"group_id": 1}, {"group_id": 2}]
    # Act
    result = _keys_to_kebab(data)
    # Assert
    assert all("group-id" in item for item in result)
    assert all("group_id" not in item for item in result)


def test_keys_to_kebab_scalar_values_unchanged():
    # Arrange
    data = {"key_name": "snake_value_stays"}
    # Act
    result = _keys_to_kebab(data)
    # Assert — values are not transformed, only keys
    assert result["key-name"] == "snake_value_stays"


def test_keys_to_kebab_non_dict_returns_unchanged():
    # Arrange / Act / Assert
    assert _keys_to_kebab("string") == "string"
    assert _keys_to_kebab(42) == 42
    assert _keys_to_kebab(None) is None


# ---------------------------------------------------------------------------
# write_dispatch_plan happy path
# ---------------------------------------------------------------------------


def test_write_dispatch_plan_creates_file(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "milestone-3-dispatch.yaml"
    # Act
    result = write_dispatch_plan(minimal_plan, target)
    # Assert
    assert target.exists()
    assert result == target


def test_write_dispatch_plan_returns_written_path(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "output.yaml"
    # Act
    returned = write_dispatch_plan(minimal_plan, target)
    # Assert
    assert returned == target


def test_write_dispatch_plan_outputs_kebab_case_conflict_groups(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    content = target.read_text()
    # Assert
    assert "conflict-groups:" in content
    assert "conflict_groups:" not in content


def test_write_dispatch_plan_outputs_kebab_case_quality_gates(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    content = target.read_text()
    # Assert
    assert "quality-gates:" in content
    assert "quality_gates:" not in content


def test_write_dispatch_plan_outputs_kebab_case_integration_branch(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    content = target.read_text()
    # Assert
    assert "integration-branch:" in content
    assert "integration_branch:" not in content


def test_write_dispatch_plan_outputs_kebab_case_nested_wave_fields(
    tmp_path: Path, plan_with_nested_fields: DispatchPlan
):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(plan_with_nested_fields, target)
    content = target.read_text()
    # Assert
    assert "conflict-group:" in content
    assert "depends-on:" in content
    assert "conflict_group:" not in content
    assert "depends_on:" not in content


def test_write_dispatch_plan_creates_parent_directories(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "deep" / "nested" / "dir" / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    # Assert
    assert target.exists()


def test_write_dispatch_plan_produces_valid_yaml_parseable_content(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    from ruamel.yaml import YAML

    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    y = YAML(typ="safe")
    with target.open() as fh:
        parsed = y.load(fh)
    # Assert
    assert isinstance(parsed, dict)
    assert "milestone" in parsed
    assert "conflict-groups" in parsed
    assert "waves" in parsed


def test_write_dispatch_plan_overwrites_existing_file(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    target.write_text("old content")
    # Act
    write_dispatch_plan(minimal_plan, target)
    # Assert
    content = target.read_text()
    assert "old content" not in content
    assert "milestone:" in content


# ---------------------------------------------------------------------------
# Atomic rename: no partial file on failure
# ---------------------------------------------------------------------------


def test_write_dispatch_plan_no_partial_file_when_rename_fails(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    assert not target.exists()

    # Act — patch os.rename to simulate failure after temp file is written
    with (
        patch("dispatch_schema.writers.yaml_writer.os.rename", side_effect=OSError("rename failed")),
        pytest.raises(OSError, match="rename failed"),
    ):
        write_dispatch_plan(minimal_plan, target)

    # Assert — target file must not exist, temp file must be cleaned up
    assert not target.exists()
    remaining_tmp = list(tmp_path.glob(".milestone-3-dispatch-*.tmp"))
    assert remaining_tmp == [], f"Temp files not cleaned up: {remaining_tmp}"


# ---------------------------------------------------------------------------
# Symlink rejection
# ---------------------------------------------------------------------------


def test_write_dispatch_plan_rejects_symlink_target(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    real_file = tmp_path / "real.yaml"
    real_file.write_text("real")
    symlink = tmp_path / "link.yaml"
    symlink.symlink_to(real_file)
    # Act / Assert
    with pytest.raises(ValueError, match="symlink"):
        write_dispatch_plan(minimal_plan, symlink)


# ---------------------------------------------------------------------------
# Pre-merge / post-merge field serialization
# ---------------------------------------------------------------------------


def test_write_dispatch_plan_outputs_kebab_case_pre_merge(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    content = target.read_text()
    # Assert
    assert "pre-merge:" in content
    assert "pre_merge:" not in content


def test_write_dispatch_plan_outputs_kebab_case_group_id(tmp_path: Path, minimal_plan: DispatchPlan):
    # Arrange
    target = tmp_path / "plan.yaml"
    # Act
    write_dispatch_plan(minimal_plan, target)
    content = target.read_text()
    # Assert
    assert "group-id:" in content
    assert "group_id:" not in content
