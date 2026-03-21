"""dispatch_schema — public API for dispatch plan models, I/O, and validation.

Import directly from this package:

    from dispatch_schema import DispatchPlan, read_dispatch_plan, write_dispatch_plan
    from dispatch_schema import validate_plan_integrity, detect_stale_plan
"""

from __future__ import annotations

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
from dispatch_schema.core.validator import StalePlanResult, ValidationResult, detect_stale_plan, validate_plan_integrity
from dispatch_schema.readers.yaml_reader import read_dispatch_plan
from dispatch_schema.writers.yaml_writer import write_dispatch_plan

__all__ = [
    # Models
    "ConflictGroup",
    "DispatchPlan",
    "ItemPriority",
    "ItemStatus",
    "MilestoneHeader",
    "QualityGates",
    # Validation
    "StalePlanResult",
    "ValidationResult",
    "Wave",
    "WaveItem",
    "detect_stale_plan",
    # I/O
    "read_dispatch_plan",
    "validate_plan_integrity",
    "write_dispatch_plan",
]
