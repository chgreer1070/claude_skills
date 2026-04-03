"""Pydantic models for dispatch plan schema.

Canonical data model for plan/milestone-{N}-dispatch.yaml files.
All format-specific readers normalize to these models.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field


class _DispatchBase(BaseModel):
    """Base class providing shared Pydantic configuration for all dispatch models."""

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)


class ItemPriority(StrEnum):
    """Priority level for a dispatch wave item."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ItemStatus(StrEnum):
    """Dispatch-level status for a wave item.

    Not the same as SAM TaskStatus — this tracks dispatch execution state.
    """

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"


class MilestoneHeader(_DispatchBase):
    """Top-level milestone identification block."""

    number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    integration_branch: str = Field(..., validation_alias=AliasChoices("integration_branch", "integration-branch"))


class ConflictGroup(_DispatchBase):
    """A set of backlog items whose Impact Radii overlap at the file level."""

    group_id: int = Field(..., ge=1, validation_alias=AliasChoices("group_id", "group-id"))
    reason: str = Field(..., min_length=1)
    items: list[str] = Field(..., min_length=2)


class WaveItem(_DispatchBase):
    """A single backlog item assigned to a wave."""

    title: str = Field(..., min_length=1)
    issue: int = Field(..., ge=1)
    priority: ItemPriority
    conflict_group: int | None = Field(default=None, validation_alias=AliasChoices("conflict_group", "conflict-group"))
    depends_on: list[int] = Field(default_factory=list, validation_alias=AliasChoices("depends_on", "depends-on"))
    status: ItemStatus = Field(default=ItemStatus.PENDING)


class Wave(_DispatchBase):
    """An ordered execution wave containing parallelizable items."""

    wave: int = Field(..., ge=1)
    parallel: bool = Field(default=True)
    items: list[WaveItem] = Field(..., min_length=1)


class QualityGates(_DispatchBase):
    """Commands to run at pre-merge and post-merge checkpoints."""

    pre_merge: list[str] = Field(default_factory=list, validation_alias=AliasChoices("pre_merge", "pre-merge"))
    post_merge: list[str] = Field(default_factory=list, validation_alias=AliasChoices("post_merge", "post-merge"))


class GateRunMode(StrEnum):
    """Execution strategy for a quality gate run."""

    FAIL_FAST = "fail-fast"
    """Stop after the first failing command."""

    RUN_ALL = "run-all"
    """Run all commands and collect all results."""


class CommandResult(_DispatchBase):
    """Result of executing one gate command."""

    command: str = Field(..., description="Original command string as declared in the dispatch plan.")
    exit_code: int = Field(..., description="Process exit code. 127 when command was not found.")
    stdout: str = Field(default="")
    stderr: str = Field(default="")

    @computed_field
    @property
    def passed(self) -> bool:
        """True iff exit_code == 0."""
        return self.exit_code == 0


class GateResult(_DispatchBase):
    """Aggregate result of a quality gate run."""

    passed: bool = Field(..., description="True iff every CommandResult.passed is True.")
    results: list[CommandResult] = Field(default_factory=list)
    mode: GateRunMode = Field(..., description="Execution mode used for this run.")


class DispatchPlan(_DispatchBase):
    """Root model for plan/milestone-{N}-dispatch.yaml."""

    milestone: MilestoneHeader
    conflict_groups: list[ConflictGroup] = Field(
        default_factory=list, validation_alias=AliasChoices("conflict_groups", "conflict-groups")
    )
    waves: list[Wave] = Field(..., min_length=1)
    quality_gates: QualityGates = Field(
        default_factory=QualityGates, validation_alias=AliasChoices("quality_gates", "quality-gates")
    )
