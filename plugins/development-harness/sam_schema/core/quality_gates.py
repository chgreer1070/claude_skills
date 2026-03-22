"""Quality gate plan generator for the complete-implementation workflow.

Produces a YAML string for a 6-task quality-gate plan (QG prefix) that is
passed to ``sam_create`` by the ``complete-implementation`` skill.

The function is pure — no file I/O, no MCP calls, no side effects.
"""

from __future__ import annotations

import io
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

# Ordered quality-gate phase definitions.
# Each entry maps directly to a SAM Task field set.
_PHASE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "id": "T1",
        "title": "Code Review",
        "agent": "code-reviewer",
        "dependencies": [],
        "complexity": "medium",
        "phase": 1,
    },
    {
        "id": "T2",
        "title": "Feature Verification",
        "agent": "feature-verifier",
        "dependencies": ["T1"],
        "complexity": "medium",
        "phase": 2,
    },
    {
        "id": "T3",
        "title": "Integration Check",
        "agent": "integration-checker",
        "dependencies": ["T2"],
        "complexity": "medium",
        "phase": 3,
    },
    {
        "id": "T4",
        "title": "Documentation Drift Audit",
        "agent": "doc-drift-auditor",
        "dependencies": ["T3"],
        "complexity": "low",
        "phase": 4,
    },
    {
        "id": "T5",
        "title": "Documentation Update",
        "agent": "service-docs-maintainer",
        "dependencies": ["T4"],
        "complexity": "low",
        "phase": 5,
    },
    {
        "id": "T6",
        "title": "Context Refinement",
        "agent": "context-refinement",
        "dependencies": ["T5"],
        "complexity": "medium",
        "phase": 6,
    },
]


def _make_yaml() -> YAML:
    """Return a ruamel.yaml instance configured for plain YAML output.

    Returns:
        Configured ``YAML`` instance.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096  # prevent line-wrapping in long body strings
    return yaml


def _phase_body(phase: int, impl_plan_address: str) -> str:
    """Build the task body markdown for a quality-gate phase.

    Args:
        phase: Phase number (1-6).
        impl_plan_address: Address of the implementation plan, e.g. ``P003``.

    Returns:
        Markdown string cross-referencing the implementation plan.
    """
    titles = {
        1: "Code Review",
        2: "Feature Verification",
        3: "Integration Check",
        4: "Documentation Drift Audit",
        5: "Documentation Update",
        6: "Context Refinement",
    }
    title = titles.get(phase, f"Phase {phase}")
    return (
        f"## Quality Gate Phase {phase}: {title}\n\n"
        f"Implementation plan: `{impl_plan_address}`\n\n"
        f"Run this phase as instructed by the `{title.lower()}` agent.\n"
        f"Mark this task complete after the phase agent finishes.\n"
    )


def build_quality_gate_plan(
    slug: str, issue: str | None, impl_plan_address: str, phase_4_drift_found: bool | None = None
) -> str:
    """Generate YAML for a 6-task quality-gate plan.

    The returned string is intended to be passed directly to ``sam_create``
    as the ``tasks_yaml`` argument. No file I/O is performed.

    Args:
        slug: Feature slug used as the plan ``feature`` identifier,
            e.g. ``"my-feature"``.
        issue: GitHub issue number (as a string) to embed in the plan, or
            ``None`` to omit the field.
        impl_plan_address: Address of the implementation plan this QG plan
            is gating, e.g. ``"P003"``. Embedded in each task body.
        phase_4_drift_found: Reserved for future use. When ``False``, callers
            may later mark T5 as SKIPPED via ``sam_state``. This parameter
            does not affect the generated YAML — T5 is always emitted with
            status ``not-started``.

    Returns:
        YAML string containing plan-level metadata and 6 task definitions.
        The string is valid YAML parseable by ``ruamel.yaml`` and validates
        against the ``Plan`` model.
    """
    plan_data: dict[str, Any] = {
        "feature": slug,
        "version": "1.0",
        "goal": f"Quality gate verification for implementation plan {impl_plan_address}",
        "tasks": [],
    }

    if issue is not None:
        plan_data["issue"] = issue

    tasks: list[dict[str, Any]] = []
    for defn in _PHASE_DEFINITIONS:
        body_text = _phase_body(defn["phase"], impl_plan_address)
        task: dict[str, Any] = {
            "id": defn["id"],
            "title": defn["title"],
            "status": "not-started",
            "agent": defn["agent"],
            "dependencies": list(defn["dependencies"]),
            "priority": 1,
            "complexity": defn["complexity"],
            "body": LiteralScalarString(body_text),
        }
        tasks.append(task)

    plan_data["tasks"] = tasks

    yaml = _make_yaml()
    stream = io.StringIO()
    yaml.dump(plan_data, stream)
    return stream.getvalue()
