"""Shared fixtures for the experiment-registry test suite.

Provides:
- experiment_dir: tmp_path-based directory tree matching the expected layout.
- make_state: factory fixture for constructing ExperimentState instances.
- make_artefact_file: factory fixture for writing files into tmp_path.
- mock_loader: a MagicMock RegistryLoader with a controllable merge_type output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# Ensure the package root is importable when tests are run from any working directory.
_PACKAGE_ROOT = Path(__file__).parent.parent
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from models import ArtefactIntegrity, ExperimentState, StepDefinition, ValidationRule

# ---------------------------------------------------------------------------
# experiment_dir
# ---------------------------------------------------------------------------


@pytest.fixture
def experiment_dir(tmp_path: Path) -> Path:
    """Create a temporary experiment directory tree.

    Creates the standard layout::

        tmp_path/
        └── .claude/
            └── experiments/
                └── exp-test-001/

    Returns:
        Path to the ``exp-test-001`` experiment directory (where artefact files live).
    """
    exp_dir = tmp_path / ".claude" / "experiments" / "exp-test-001"
    exp_dir.mkdir(parents=True)
    return exp_dir


# ---------------------------------------------------------------------------
# make_state
# ---------------------------------------------------------------------------


@pytest.fixture
def make_state(experiment_dir: Path):
    """Factory fixture that returns a callable for creating ExperimentState objects.

    The factory creates a minimal valid ExperimentState with sensible defaults
    and merges any keyword arguments provided by the caller.

    Usage::

        def test_something(make_state):
            state = make_state(status="complete", iteration_count=3)

    Returns:
        Callable[..., ExperimentState] — call with keyword arguments to override defaults.
    """
    DEFAULT_STEPS = [
        StepDefinition(
            id="hypothesis",
            name="State hypothesis",
            required_artefacts=["hypothesis.md"],
            validation_rules=[
                ValidationRule(type="non_empty", params={}),
                ValidationRule(
                    type="required_sections",
                    params={"sections": ["HYPOTHESIS:", "CURRENT BEHAVIOUR:", "SUCCESS CRITERION:"]},
                ),
            ],
            frozen_artefacts=[],
        ),
        StepDefinition(
            id="fixture",
            name="Build fixture",
            required_artefacts=["fixture.md"],
            validation_rules=[
                ValidationRule(type="non_empty", params={}),
                ValidationRule(
                    type="no_forbidden_content",
                    params={"patterns": ["EXPECTED:", "CORRECT ANSWER:", "SUCCESS CRITERION:", "RUBRIC:"]},
                ),
            ],
            frozen_artefacts=["fixture.md"],
        ),
        StepDefinition(
            id="rubric",
            name="Write rubric",
            required_artefacts=["rubric.md"],
            validation_rules=[
                ValidationRule(type="non_empty", params={}),
                ValidationRule(type="min_criteria_count", params={"min": 1}),
            ],
            frozen_artefacts=["rubric.md"],
        ),
        StepDefinition(
            id="baseline",
            name="Run baseline",
            required_artefacts=["output-iter0.md", "log.md"],
            validation_rules=[ValidationRule(type="non_empty", params={})],
            frozen_artefacts=[],
        ),
        StepDefinition(
            id="iterate",
            name="Iterate",
            required_artefacts=["log.md"],
            validation_rules=[
                ValidationRule(type="non_empty", params={}),
                ValidationRule(type="required_sections", params={"sections": ["## Iteration"]}),
            ],
            frozen_artefacts=[],
        ),
    ]

    def _factory(
        *,
        experiment_id: str = "exp-test-001",
        base: str = "experiment_core",
        current_step: str = "hypothesis",
        status: str = "in_progress",
        iteration_count: int = 0,
        artefacts: dict[str, str] | None = None,
        artefact_integrity: dict[str, ArtefactIntegrity] | None = None,
        merged_steps: list[StepDefinition] | None = None,
        completed_steps: list[str] | None = None,
        **kwargs: Any,
    ) -> ExperimentState:
        """Create an ExperimentState with the given overrides applied.

        Args:
            experiment_id: Experiment identifier.
            base: Experiment type name.
            current_step: Step ID that is currently active.
            status: Experiment lifecycle status string.
            iteration_count: Number of completed iterate steps.
            artefacts: Artefacts dict (defaults to empty).
            artefact_integrity: Frozen artefact integrity records (defaults to empty).
            merged_steps: Full step list (defaults to experiment_core steps).
            completed_steps: Steps already completed (defaults to empty).
            **kwargs: Additional fields forwarded directly to ExperimentState.

        Returns:
            A constructed ExperimentState.
        """
        return ExperimentState(
            id=experiment_id,
            base=base,
            current_step=current_step,
            status=status,
            iteration_count=iteration_count,
            artefacts=artefacts or {},
            artefact_integrity=artefact_integrity or {},
            merged_steps=merged_steps if merged_steps is not None else DEFAULT_STEPS,
            completed_steps=completed_steps or [],
            **kwargs,
        )

    return _factory


# ---------------------------------------------------------------------------
# make_artefact_file
# ---------------------------------------------------------------------------


@pytest.fixture
def make_artefact_file(experiment_dir: Path):
    """Factory fixture that writes a named file into the experiment directory.

    Usage::

        def test_something(make_artefact_file):
            path = make_artefact_file("hypothesis.md", "HYPOTHESIS: ...\nCURRENT BEHAVIOUR: ...\n")

    Returns:
        Callable[[str, str], str] — writes the file and returns its absolute path as a string.
    """

    def _factory(filename: str, content: str) -> str:
        """Write *content* to *filename* in the experiment directory.

        Args:
            filename: Name of the file (relative to experiment_dir).
            content: Text content to write.

        Returns:
            Absolute path to the written file as a string (suitable for use as an
            artefact value in complete_step calls).
        """
        file_path = experiment_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    return _factory


# ---------------------------------------------------------------------------
# mock_loader
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_loader():
    """Return a MagicMock RegistryLoader with a controllable merge_type output.

    The mock's ``merge_type`` method returns an empty list by default.
    Tests that need specific steps should configure ``mock_loader.merge_type.return_value``.

    Usage::

        def test_something(mock_loader, make_state):
            mock_loader.merge_type.return_value = [...]
            manager = StateManager(tmp_path, mock_loader)

    Returns:
        MagicMock configured to stand in for RegistryLoader.
    """
    loader = MagicMock()
    loader.merge_type.return_value = []
    return loader
