"""Registry loader for the experiment-registry MCP server.

Discovers JSON registry files, parses them as Pydantic models, and merges
core + domain + inline extensions into fully resolved step definitions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import ExperimentType, RubricTemplate, StepDefinition, StepExtension


class RegistryLoader:
    """Discovers and loads experiment type definitions from registry JSON files.

    Args:
        registry_dir: Path to the directory containing registry JSON files.
            Defaults to the ``registry/`` subdirectory next to this module.
            The ``examples/`` subdirectory is excluded from discovery.
    """

    def __init__(self, registry_dir: Path | None = None) -> None:
        """Initialise the loader and discover all registry files.

        Args:
            registry_dir: Path to the directory containing registry JSON files.
                Defaults to the ``registry/`` subdirectory next to this module.
        """
        self._registry_dir: Path = registry_dir or (Path(__file__).parent / "registry")
        self._types: dict[str, ExperimentType] = {}
        self._load_all()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Discover and parse all JSON files in the registry directory.

        Excludes the ``examples/`` subdirectory so that sample files do not
        appear as valid experiment types.
        """
        examples_dir = self._registry_dir / "examples"
        for json_file in sorted(self._registry_dir.glob("*.json")):
            if json_file.parent == examples_dir:
                continue
            self._load_file(json_file)

    def _load_file(self, path: Path) -> None:
        """Parse a single JSON registry file and store the resulting type.

        Args:
            path: Absolute path to the JSON file.

        Raises:
            ValueError: If the JSON is malformed or missing required fields.
        """
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

        steps = [StepDefinition(**s) for s in raw.get("steps", [])]

        raw_extensions = raw.get("step_extensions", {})
        step_extensions: dict[str, StepExtension] = {
            step_id: StepExtension(**ext) for step_id, ext in raw_extensions.items()
        }

        rubric_templates = [RubricTemplate(**t) for t in raw.get("rubric_templates", [])]

        experiment_type = ExperimentType(
            name=raw["name"],
            description=raw["description"],
            extends=raw.get("extends"),
            steps=steps,
            step_extensions=step_extensions,
            rubric_templates=rubric_templates,
            anti_patterns=raw.get("anti_patterns", []),
        )
        self._types[experiment_type.name] = experiment_type

    @staticmethod
    def _apply_extension(step: StepDefinition, ext: StepExtension) -> StepDefinition:
        """Return a new StepDefinition with the extension merged in.

        Merge rules:
        - ``additional_artefacts`` are appended to ``required_artefacts``.
        - ``checklist`` items are appended to the existing checklist.
        - ``human_input_required`` overrides the base value when not ``None``.
        - ``human_input_description`` overrides when non-empty.
        - ``additional_validation_rules`` are appended to ``validation_rules``.
        - ``additional_frozen_artefacts`` are appended to ``frozen_artefacts``
          with deduplication (order-preserving).

        Args:
            step: The base step definition.
            ext: The extension to apply.

        Returns:
            A new ``StepDefinition`` with merged fields.
        """
        merged_artefacts = list(step.required_artefacts) + list(ext.additional_artefacts)
        merged_checklist = list(step.checklist) + list(ext.checklist)
        merged_validation_rules = list(step.validation_rules) + list(ext.additional_validation_rules)
        # Deduplicate frozen_artefacts while preserving insertion order
        merged_frozen_artefacts = list(
            dict.fromkeys(list(step.frozen_artefacts) + list(ext.additional_frozen_artefacts))
        )

        human_input_required = step.human_input_required
        if ext.human_input_required is not None:
            human_input_required = ext.human_input_required

        human_input_description = step.human_input_description
        if ext.human_input_description:
            human_input_description = ext.human_input_description

        return StepDefinition(
            id=step.id,
            name=step.name,
            required_artefacts=merged_artefacts,
            validation=step.validation,
            checklist=merged_checklist,
            human_input_required=human_input_required,
            human_input_description=human_input_description,
            validation_rules=merged_validation_rules,
            frozen_artefacts=merged_frozen_artefacts,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_types(self) -> list[ExperimentType]:
        """Return all loaded experiment types.

        Returns:
            A list of ``ExperimentType`` objects in discovery order.
        """
        return list(self._types.values())

    def get_type(self, name: str) -> ExperimentType:
        """Return a single experiment type by name.

        Args:
            name: The ``name`` field of the experiment type (e.g.
                ``"ai_agent_testing"``).

        Returns:
            The matching ``ExperimentType``.

        Raises:
            ValueError: If no type with the given name has been loaded.
        """
        if name not in self._types:
            available = ", ".join(sorted(self._types))
            msg = f"Unknown experiment type {name!r}. Available: {available}"
            raise ValueError(msg)
        return self._types[name]

    def merge_type(
        self, base_name: str, inline_extensions: dict[str, StepExtension] | None = None
    ) -> list[StepDefinition]:
        """Produce fully resolved step definitions for a given experiment type.

        Resolution order:
        1. Load ``experiment_core`` steps as the base.
        2. If ``base_name`` is not ``"experiment_core"``, load the named
           domain type and apply its ``step_extensions`` on top.
        3. Apply any ``inline_extensions`` last.

        Args:
            base_name: Name of the experiment type to resolve (e.g.
                ``"ai_agent_testing"``).  ``"experiment_core"`` is always
                valid and returns unmodified core steps.
            inline_extensions: Optional additional extensions keyed by step id,
                applied after domain extensions.

        Returns:
            A list of fully merged ``StepDefinition`` objects in core step
            order.

        Raises:
            ValueError: If ``experiment_core`` or ``base_name`` is not found.
        """
        core = self.get_type("experiment_core")
        steps: list[StepDefinition] = list(core.steps)

        if base_name != "experiment_core":
            domain = self.get_type(base_name)
            steps = [
                self._apply_extension(step, domain.step_extensions[step.id])
                if step.id in domain.step_extensions
                else step
                for step in steps
            ]

        if inline_extensions:
            steps = [
                self._apply_extension(step, inline_extensions[step.id]) if step.id in inline_extensions else step
                for step in steps
            ]

        return steps
