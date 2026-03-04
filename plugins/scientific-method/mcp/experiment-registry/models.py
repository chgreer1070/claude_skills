"""Pydantic models for the experiment-registry MCP server.

These models correspond to the JSON registry schemas in the registry/ directory
and the persisted state for running experiments.
"""

from __future__ import annotations

import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationRule(BaseModel):
    """Machine-evaluable rule for validating artefact content."""

    type: Literal["required_sections", "non_empty", "no_forbidden_content", "min_criteria_count"]
    params: dict[str, Any] = Field(default_factory=dict)


class StepDefinition(BaseModel):
    """A single step in the experiment workflow."""

    id: str
    name: str
    required_artefacts: list[str] = Field(default_factory=list)
    validation: str = ""
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool = False
    human_input_description: str = ""
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    frozen_artefacts: list[str] = Field(default_factory=list)


class RubricTemplate(BaseModel):
    """Reusable rubric criterion template."""

    name: str
    observable: str
    pass_: str = Field(alias="pass")
    fail: str

    model_config = {"populate_by_name": True}


class StepExtension(BaseModel):
    """Extensions to a core step for a domain-specific experiment type."""

    additional_artefacts: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)
    human_input_required: bool | None = None
    human_input_description: str = ""
    additional_validation_rules: list[ValidationRule] = Field(default_factory=list)
    additional_frozen_artefacts: list[str] = Field(default_factory=list)


class ExperimentType(BaseModel):
    """Registered experiment type definition (core or domain)."""

    name: str
    description: str
    extends: str | None = None
    steps: list[StepDefinition] = Field(default_factory=list)
    step_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    rubric_templates: list[RubricTemplate] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)


class ArtefactIntegrity(BaseModel):
    """Content hash and freeze metadata for a frozen artefact."""

    sha256: str
    frozen_at: str
    frozen_by_step: str


class ExperimentState(BaseModel):
    """Persisted state for a running experiment."""

    id: str
    base: str
    extensions: list[str] = Field(default_factory=list)
    inline_extensions: dict[str, StepExtension] = Field(default_factory=dict)
    merged_steps: list[StepDefinition] = Field(default_factory=list)
    current_step: str = ""
    completed_steps: list[str] = Field(default_factory=list)
    artefacts: dict[str, str] = Field(default_factory=dict)
    context: str = ""
    iteration_count: int = 0
    max_iterations: int = 10
    status: str = "in_progress"
    created: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    last_updated: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    artefact_integrity: dict[str, ArtefactIntegrity] = Field(default_factory=dict)
