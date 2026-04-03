"""Shared fixtures for dispatch_schema tests."""

from __future__ import annotations

from pathlib import Path

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

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def minimal_wave_item() -> WaveItem:
    """A minimal valid WaveItem with only required fields."""
    return WaveItem(title="Fix auth bug", issue=42, priority=ItemPriority.P1)


@pytest.fixture
def simple_plan() -> DispatchPlan:
    """A minimal valid DispatchPlan with one wave and one item, no conflicts."""
    return DispatchPlan(
        milestone=MilestoneHeader(number=1, title="Sprint 1", integration_branch="milestone/1-sprint"),
        waves=[Wave(wave=1, parallel=True, items=[WaveItem(title="First item", issue=10, priority=ItemPriority.P1)])],
    )


@pytest.fixture
def two_wave_plan() -> DispatchPlan:
    """A valid two-wave plan where wave 2 depends on wave 1 items."""
    return DispatchPlan(
        milestone=MilestoneHeader(number=2, title="Sprint 2", integration_branch="milestone/2-sprint"),
        conflict_groups=[ConflictGroup(group_id=1, reason="Shared file", items=["Alpha task", "Beta task"])],
        waves=[
            Wave(
                wave=1,
                parallel=True,
                items=[WaveItem(title="Alpha task", issue=100, priority=ItemPriority.P0, conflict_group=1)],
            ),
            Wave(
                wave=2,
                parallel=True,
                items=[
                    WaveItem(
                        title="Beta task", issue=101, priority=ItemPriority.P1, conflict_group=1, depends_on=[100]
                    ),
                    WaveItem(title="Gamma task", issue=102, priority=ItemPriority.P2),
                ],
            ),
        ],
        quality_gates=QualityGates(pre_merge=["uv run pytest"], post_merge=[]),
    )
