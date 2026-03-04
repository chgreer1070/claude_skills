"""State manager for the experiment-registry MCP server.

Handles the full lifecycle of experiment state — creation, loading, step
advancement, validation, and listing. State is persisted as JSON files under
``{project_root}/.claude/experiments/{id}/state.json``.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING

from models import ExperimentState, StepDefinition, StepExtension

if TYPE_CHECKING:
    from registry_loader import RegistryLoader


class StateManager:
    """Manages experiment state persistence and lifecycle transitions.

    Args:
        project_root: Root directory of the project. Experiments are stored
            under ``{project_root}/.claude/experiments/``.
        loader: Configured ``RegistryLoader`` used to resolve step definitions.
    """

    def __init__(self, project_root: str | Path, loader: RegistryLoader) -> None:
        """Initialise the state manager.

        Args:
            project_root: Root directory of the project.
            loader: Configured ``RegistryLoader`` instance.
        """
        self._project_root = Path(project_root)
        self._loader = loader
        self._experiments_dir = self._project_root / ".claude" / "experiments"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _state_path(self, experiment_id: str) -> Path:
        """Return the path to the state JSON file for *experiment_id*.

        Args:
            experiment_id: Unique experiment identifier.

        Returns:
            Absolute path to ``state.json``.
        """
        return self._experiments_dir / experiment_id / "state.json"

    def _save(self, state: ExperimentState) -> None:
        """Persist *state* to disk as JSON.

        Args:
            state: The experiment state to persist.
        """
        path = self._state_path(state.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def _generate_id(self) -> str:
        """Generate a sequential experiment ID in the format ``exp-YYYY-MM-DD-NNN``.

        The sequence number NNN is determined by counting existing experiments
        created on the same calendar date.

        Returns:
            A unique experiment identifier string.
        """
        today = datetime.datetime.now(datetime.UTC).date().isoformat()
        prefix = f"exp-{today}-"
        existing = [
            p.parent.name for p in self._experiments_dir.glob("*/state.json") if p.parent.name.startswith(prefix)
        ]
        seq = len(existing) + 1
        return f"{prefix}{seq:03d}"

    def _now_iso(self) -> str:
        """Return the current UTC time as an ISO 8601 string.

        Returns:
            ISO 8601 formatted timestamp.
        """
        return datetime.datetime.now(datetime.UTC).isoformat()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_experiment(
        self, base: str, context: str, extensions: dict[str, StepExtension] | None = None, max_iterations: int = 10
    ) -> ExperimentState:
        """Create a new experiment and persist its initial state.

        Args:
            base: Name of the experiment type (e.g. ``"ai_agent_testing"``).
            context: Human-readable description of the experiment purpose.
            extensions: Optional inline step extensions keyed by step id,
                applied on top of the domain-type extensions.
            max_iterations: Maximum allowed iterations before the experiment
                is marked ``"inconclusive"``.

        Returns:
            The newly created ``ExperimentState``.

        Raises:
            ValueError: If *base* is not a known experiment type.
        """
        experiment_id = self._generate_id()
        merged_steps = self._loader.merge_type(base, extensions)
        first_step = merged_steps[0].id if merged_steps else ""

        state = ExperimentState(
            id=experiment_id,
            base=base,
            inline_extensions=extensions or {},
            merged_steps=merged_steps,
            current_step=first_step,
            context=context,
            max_iterations=max_iterations,
            status="in_progress",
        )

        self._save(state)
        return state

    def load_experiment(self, experiment_id: str) -> ExperimentState:
        """Load a persisted experiment by ID.

        Args:
            experiment_id: The unique identifier of the experiment.

        Returns:
            The loaded ``ExperimentState``.

        Raises:
            ValueError: If no state file exists for *experiment_id*.
        """
        path = self._state_path(experiment_id)
        if not path.exists():
            msg = f"Experiment {experiment_id!r} not found at {path}"
            raise ValueError(msg)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ExperimentState(**raw)

    def get_current_step(self, experiment_id: str) -> StepDefinition:
        """Return the ``StepDefinition`` for the experiment's current step.

        Args:
            experiment_id: The unique identifier of the experiment.

        Returns:
            The current ``StepDefinition``.

        Raises:
            ValueError: If the experiment is not found or the current step id
                does not match any step in ``merged_steps``.
        """
        state = self.load_experiment(experiment_id)
        for step in state.merged_steps:
            if step.id == state.current_step:
                return step
        msg = f"Step {state.current_step!r} not found in experiment {experiment_id!r}. Available steps: " + ", ".join(
            s.id for s in state.merged_steps
        )
        raise ValueError(msg)

    def complete_step(self, experiment_id: str, step_id: str, artefacts: dict[str, str]) -> dict[str, object]:
        """Attempt to complete *step_id* for the given experiment.

        Validates that *step_id* matches the current step, checks required
        artefacts are present, handles the special ``"iterate"`` step loop,
        and advances (or terminates) the experiment.

        Args:
            experiment_id: The unique identifier of the experiment.
            step_id: The id of the step being completed.
            artefacts: Key-value pairs produced during this step.

        Returns:
            A dict with at minimum a ``"success"`` key (``bool``). On
            failure the dict contains ``"missing_artefacts"`` or
            ``"blocked_on_human_input"`` fields.  On success it contains
            ``"next_step"`` (``str | None``) and ``"status"`` (``str``).

        Raises:
            ValueError: If *step_id* does not match the current step.
        """
        state = self.load_experiment(experiment_id)

        # Validate step matches current
        if step_id != state.current_step:
            msg = (
                f"Cannot complete step {step_id!r}: current step is "
                f"{state.current_step!r} for experiment {experiment_id!r}."
            )
            raise ValueError(msg)

        # Find the step definition
        current_def: StepDefinition | None = None
        for step in state.merged_steps:
            if step.id == step_id:
                current_def = step
                break

        if current_def is None:
            msg = f"Step {step_id!r} not found in experiment {experiment_id!r}."
            raise ValueError(msg)

        # Check required artefacts
        missing = [a for a in current_def.required_artefacts if a not in artefacts]
        if missing:
            # If human_input_required and the missing artefacts are human-provided
            if current_def.human_input_required:
                return {
                    "success": False,
                    "blocked_on_human_input": True,
                    "description": current_def.human_input_description
                    or f"Human input required for step {step_id!r}. Missing: {missing}",
                }
            return {"success": False, "missing_artefacts": missing}

        # Merge provided artefacts into state
        state.artefacts.update(artefacts)

        # Determine step index for advancement
        step_ids = [s.id for s in state.merged_steps]
        current_index = step_ids.index(step_id)

        # Special handling for "iterate" step
        if step_id == "iterate":
            state.iteration_count += 1
            criteria_passed = artefacts.get("criteria_passed", "").lower() == "true"

            if criteria_passed:
                state.status = "complete"
                state.current_step = step_id
                state.completed_steps.append(step_id)
                state.last_updated = self._now_iso()
                self._save(state)
                return {"success": True, "next_step": None, "status": state.status}

            if state.iteration_count >= state.max_iterations:
                state.status = "inconclusive"
                state.last_updated = self._now_iso()
                self._save(state)
                return {"success": True, "next_step": None, "status": state.status}

            # Loop back — keep current_step as "iterate"
            state.last_updated = self._now_iso()
            self._save(state)
            return {"success": True, "next_step": step_id, "status": state.status}

        # Standard step: mark complete and advance
        state.completed_steps.append(step_id)
        next_index = current_index + 1
        if next_index < len(step_ids):
            state.current_step = step_ids[next_index]
            next_step: str | None = state.current_step
        else:
            state.status = "complete"
            next_step = None

        state.last_updated = self._now_iso()
        self._save(state)
        return {"success": True, "next_step": next_step, "status": state.status}

    def list_experiments(self) -> list[ExperimentState]:
        """Return all persisted experiments.

        Returns:
            A list of ``ExperimentState`` objects, one per discovered
            ``state.json`` file. Returns an empty list if the experiments
            directory does not exist.
        """
        if not self._experiments_dir.exists():
            return []
        experiments: list[ExperimentState] = []
        for state_file in sorted(self._experiments_dir.glob("*/state.json")):
            raw = json.loads(state_file.read_text(encoding="utf-8"))
            experiments.append(ExperimentState(**raw))
        return experiments

    def get_experiment_summary(self, experiment_id: str) -> dict[str, object]:
        """Return a summary dict for the given experiment.

        Args:
            experiment_id: The unique identifier of the experiment.

        Returns:
            A dict containing: ``id``, ``base``, ``status``, ``context``,
            ``created``, ``last_updated``, ``completed_steps``,
            ``artefacts``, and ``iteration_count``.

        Raises:
            ValueError: If the experiment is not found.
        """
        state = self.load_experiment(experiment_id)
        return {
            "id": state.id,
            "base": state.base,
            "status": state.status,
            "context": state.context,
            "created": state.created,
            "last_updated": state.last_updated,
            "completed_steps": state.completed_steps,
            "artefacts": state.artefacts,
            "iteration_count": state.iteration_count,
        }
