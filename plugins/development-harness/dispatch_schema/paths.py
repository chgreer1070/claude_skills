"""Path helpers for dispatch plan file locations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def dispatch_plan_path(milestone_number: int, project_root: Path) -> Path:
    """Return the canonical dispatch plan path for a milestone.

    Args:
        milestone_number: GitHub milestone number.
        project_root: Absolute path to the project root directory.

    Returns:
        Path to ``plan/milestone-{N}-dispatch.yaml`` under ``project_root``.
    """
    return project_root / "plan" / f"milestone-{milestone_number}-dispatch.yaml"
