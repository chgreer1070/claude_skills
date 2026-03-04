"""Composable pure-function validators for the experiment-registry MCP server.

All functions are side-effect-free: no file writes, no state mutation, no network calls.
Every public function returns a list of error dicts (empty list means no errors).
Each error dict contains at minimum 'code' and 'message' keys.

Artefact values are treated as file paths per architecture decision D1 -- validators
resolve paths against the experiment directory and read file content from disk.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from models import ExperimentState, StepDefinition, ValidationRule

# ---------------------------------------------------------------------------
# Error code constants
# ---------------------------------------------------------------------------

EMPTY_ARTEFACT = "EMPTY_ARTEFACT"
FILE_NOT_FOUND = "FILE_NOT_FOUND"
FROZEN_ARTEFACT_MODIFIED = "FROZEN_ARTEFACT_MODIFIED"
MISSING_RUBRIC_SCORES = "MISSING_RUBRIC_SCORES"
INCOMPLETE_RUBRIC_SCORES = "INCOMPLETE_RUBRIC_SCORES"
UNKNOWN_RUBRIC_CRITERIA = "UNKNOWN_RUBRIC_CRITERIA"
CONTENT_VALIDATION_FAILED = "CONTENT_VALIDATION_FAILED"
MISSING_ITERATION_OUTPUT = "MISSING_ITERATION_OUTPUT"
TERMINAL_STATE = "TERMINAL_STATE"


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------


def _eval_non_empty(content: str, params: dict[str, Any]) -> str | None:
    """Return error message if content is empty after stripping whitespace.

    Args:
        content: File content to validate.
        params: Unused for this rule type.

    Returns:
        None if content is non-empty, error message string otherwise.
    """
    if not content.strip():
        return "Artefact content is empty"
    return None


def _eval_required_sections(content: str, params: dict[str, Any]) -> str | None:
    """Return error message if any required section header is absent.

    Args:
        content: File content to validate.
        params: Must contain 'sections' key with list of required section strings.

    Returns:
        None if all sections present, error message listing missing sections otherwise.
    """
    sections: list[str] = params.get("sections", [])
    missing = [s for s in sections if s not in content]
    if missing:
        return f"Missing required section(s): {', '.join(missing)}"
    return None


def _eval_no_forbidden_content(content: str, params: dict[str, Any]) -> str | None:
    """Return error message if any forbidden pattern appears in content.

    Args:
        content: File content to validate.
        params: Must contain 'patterns' key with list of forbidden pattern strings.

    Returns:
        None if no forbidden patterns found, error message listing found patterns.
    """
    patterns: list[str] = params.get("patterns", [])
    found = [p for p in patterns if p.lower() in content.lower()]
    if found:
        return f"Forbidden content found: {', '.join(found)}"
    return None


def _eval_min_criteria_count(content: str, params: dict[str, Any]) -> str | None:
    """Return error message if criterion count falls below minimum.

    Counts lines matching the checklist item pattern '- [ ]' or '- [x]'.

    Args:
        content: File content to validate.
        params: Must contain 'min' key with the minimum required criterion count.

    Returns:
        None if criterion count meets minimum, error message otherwise.
    """
    min_count: int = params.get("min", 1)
    # Match checkbox list items: '- [ ] ...' or '- [x] ...'
    criterion_pattern = re.compile(r"^- \[[ x]\]", re.MULTILINE)
    matches = criterion_pattern.findall(content)
    count = len(matches)
    if count < min_count:
        return f"Rubric must contain at least {min_count} criterion/criteria (found {count})"
    return None


_RULE_EVALUATORS: dict[str, Callable[[str, dict[str, Any]], str | None]] = {
    "non_empty": _eval_non_empty,
    "required_sections": _eval_required_sections,
    "no_forbidden_content": _eval_no_forbidden_content,
    "min_criteria_count": _eval_min_criteria_count,
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _resolve_artefact_path(value: str, experiment_dir: Path) -> Path:
    """Resolve an artefact value as a file path relative to experiment directory.

    Args:
        value: The artefact value string (relative or absolute path).
        experiment_dir: The experiment's directory.

    Returns:
        Resolved absolute Path.
    """
    p = Path(value)
    if p.is_absolute():
        return p
    return experiment_dir / p


def _has_file_extension(key: str) -> bool:
    """Return True if key contains a '.' indicating a file path (per D1 convention).

    Args:
        key: Artefact key name.

    Returns:
        True if key appears to be a file path.
    """
    return "." in key


def _apply_rule(content: str, rule: ValidationRule, artefact_key: str) -> dict[str, Any] | None:
    """Apply a single ValidationRule to content, returning an error dict or None.

    Args:
        content: File content to validate.
        rule: The validation rule to apply.
        artefact_key: The artefact key (for error context).

    Returns:
        Error dict if validation fails, None if it passes.
    """
    evaluator = _RULE_EVALUATORS.get(rule.type)
    if evaluator is None:
        # Unknown rule type — skip silently (forward compatibility)
        return None

    error_message = evaluator(content, rule.params)
    if error_message is None:
        return None

    code = EMPTY_ARTEFACT if rule.type == "non_empty" else CONTENT_VALIDATION_FAILED
    return {"code": code, "artefact": artefact_key, "rule": rule.type, "message": error_message}


def _extract_rubric_criteria_from_markdown(rubric_content: str) -> list[str]:
    """Extract criterion names from rubric.md content.

    Handles two formats:
    - Markdown headings: '## criterion name' or '### criterion name'
    - Bold list items: '- **criterion_name**:'

    Args:
        rubric_content: Content of rubric.md file.

    Returns:
        List of criterion name strings (stripped).
    """
    criteria: list[str] = []

    # Match '## heading' or '### heading'
    heading_pattern = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
    for match in heading_pattern.finditer(rubric_content):
        name = match.group(1).strip()
        if name:
            criteria.append(name)

    # Match '- **criterion_name**:' if no headings found
    if not criteria:
        bold_pattern = re.compile(r"^- \*\*([^*]+)\*\*:", re.MULTILINE)
        for match in bold_pattern.finditer(rubric_content):
            name = match.group(1).strip()
            if name:
                criteria.append(name)

    return criteria


def _get_rubric_criteria(state: ExperimentState, experiment_dir: Path) -> list[str]:
    """Discover rubric criteria from structured templates or rubric.md file.

    Prefers rubric_templates from registered type. Falls back to parsing rubric.md.

    Args:
        state: Current experiment state.
        experiment_dir: The experiment's base directory.

    Returns:
        List of criterion name strings.
    """
    # Collect rubric_templates from all merged steps' parent type
    # rubric_templates live on ExperimentType, not StepDefinition.
    # State doesn't carry ExperimentType directly, but a rubric_templates-derived
    # list would be passed via the state's merged steps context. Since ExperimentState
    # doesn't directly expose rubric_templates, we fall back to rubric.md parsing,
    # unless artefacts already contain a parsed rubric key.
    #
    # The architecture spec (D3) says: "If the experiment type has rubric_templates
    # (from registry JSON), criterion names are [t.name for t in rubric_templates]"
    # but ExperimentState has no rubric_templates field — those live on ExperimentType.
    # The state_manager must pass rubric criteria separately or we parse rubric.md.
    # Since T2 is a pure validator and state_manager integration is T4, we use rubric.md.
    #
    # When rubric_templates are available (injected in future or via state extension),
    # the caller can pass them via a wrapper. For now, always parse rubric.md.

    rubric_path_str = state.artefacts.get("rubric.md", "")
    if not rubric_path_str:
        return []

    rubric_path = _resolve_artefact_path(rubric_path_str, experiment_dir)
    if not rubric_path.exists() or not rubric_path.is_file():
        return []

    try:
        rubric_content = rubric_path.read_text(encoding="utf-8")
    except OSError:
        return []

    return _extract_rubric_criteria_from_markdown(rubric_content)


# ---------------------------------------------------------------------------
# Public validation functions
# ---------------------------------------------------------------------------


def validate_terminal_state(state: ExperimentState) -> list[dict[str, Any]]:
    """Check that experiment is not already in a terminal state.

    Args:
        state: Current experiment state.

    Returns:
        List with one TERMINAL_STATE error dict if status is complete or inconclusive,
        empty list otherwise.
    """
    if state.status in {"complete", "inconclusive"}:
        return [
            {
                "code": TERMINAL_STATE,
                "status": state.status,
                "message": (
                    f"Experiment '{state.id}' is already in terminal state '{state.status}'. "
                    "No further steps can be completed."
                ),
            }
        ]
    return []


def validate_file_existence(artefacts: dict[str, str], experiment_dir: Path) -> list[dict[str, Any]]:
    """Check that artefact file paths resolve to existing files on disk.

    Keys without a '.' (no file extension) are treated as inline values per
    architecture decision D1 and are skipped.

    Args:
        artefacts: Mapping of artefact key to file path string.
        experiment_dir: The experiment's base directory for relative path resolution.

    Returns:
        List of FILE_NOT_FOUND error dicts for each missing file.
    """
    errors: list[dict[str, Any]] = []

    for key, value in artefacts.items():
        if not _has_file_extension(key):
            # Inline value, not a file path — skip
            continue

        path = _resolve_artefact_path(value, experiment_dir)
        if not path.exists() or not path.is_file():
            errors.append({
                "code": FILE_NOT_FOUND,
                "artefact": key,
                "path": str(path),
                "message": (
                    f"Artefact '{key}' references path '{path}' which does not exist or is not a regular file."
                ),
            })

    return errors


def validate_artefact_content(
    step_def: StepDefinition, artefacts: dict[str, str], experiment_dir: Path
) -> list[dict[str, Any]]:
    """Apply all validation rules from step definition to artefact file content.

    For each required artefact in the step definition, reads file content and
    applies all validation rules. Collects all errors across all artefacts
    without short-circuiting.

    Args:
        step_def: The step definition containing validation_rules to apply.
        artefacts: Mapping of artefact key to file path string.
        experiment_dir: The experiment's base directory for path resolution.

    Returns:
        List of error dicts for all validation failures across all artefacts.
    """
    errors: list[dict[str, Any]] = []

    if not step_def.validation_rules:
        return errors

    for key in step_def.required_artefacts:
        if key not in artefacts:
            # Missing artefact key — handled by the required-artefacts check
            # in state_manager, not by content validation
            continue

        if not _has_file_extension(key):
            # Inline value — skip file content validation
            continue

        value = artefacts[key]
        path = _resolve_artefact_path(value, experiment_dir)

        if not path.exists() or not path.is_file():
            # File existence errors are reported by validate_file_existence;
            # skip content validation for files that don't exist
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append({
                "code": CONTENT_VALIDATION_FAILED,
                "artefact": key,
                "rule": "file_read",
                "message": f"Could not read artefact '{key}': {exc}",
            })
            continue

        for rule in step_def.validation_rules:
            error = _apply_rule(content, rule, key)
            if error is not None:
                errors.append(error)

    return errors


def validate_freeze_integrity(state: ExperimentState, experiment_dir: Path) -> list[dict[str, Any]]:
    """Check that previously frozen artefact files have not been modified.

    Re-hashes each file in state.artefact_integrity and compares against
    the stored SHA-256 digest. Detects modifications made between complete_step calls.

    Args:
        state: Current experiment state with artefact_integrity records.
        experiment_dir: The experiment's base directory for path resolution.

    Returns:
        List of FROZEN_ARTEFACT_MODIFIED error dicts for each tampered artefact.
    """
    errors: list[dict[str, Any]] = []

    for key, integrity in state.artefact_integrity.items():
        # Resolve path: use stored artefact value if available, otherwise key itself
        artefact_value = state.artefacts.get(key, key)
        path = _resolve_artefact_path(artefact_value, experiment_dir)

        if not path.exists() or not path.is_file():
            errors.append({
                "code": FROZEN_ARTEFACT_MODIFIED,
                "artefact": key,
                "expected_hash": integrity.sha256,
                "actual_hash": None,
                "message": (
                    f"Frozen artefact '{key}' at path '{path}' no longer exists. Frozen artefacts must not be deleted."
                ),
            })
            continue

        try:
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            errors.append({
                "code": FROZEN_ARTEFACT_MODIFIED,
                "artefact": key,
                "expected_hash": integrity.sha256,
                "actual_hash": None,
                "message": f"Could not read frozen artefact '{key}' for integrity check: {exc}",
            })
            continue

        if actual_hash != integrity.sha256:
            errors.append({
                "code": FROZEN_ARTEFACT_MODIFIED,
                "artefact": key,
                "expected_hash": integrity.sha256,
                "actual_hash": actual_hash,
                "frozen_by_step": integrity.frozen_by_step,
                "message": (
                    f"Frozen artefact '{key}' was modified after being frozen by step "
                    f"'{integrity.frozen_by_step}'. Frozen artefacts must not be changed."
                ),
            })

    return errors


def validate_rubric_scores(
    rubric_scores: dict[str, bool] | None, state: ExperimentState, experiment_dir: Path | None = None
) -> list[dict[str, Any]]:
    """Validate that rubric scores are provided and complete for iterate steps.

    Called only when the current step is 'iterate'. Verifies:
    1. rubric_scores is not None and not empty.
    2. Every known criterion has a corresponding score entry.
    3. No extra keys in rubric_scores that are not known criteria.

    Criterion discovery uses rubric.md parsing (ad-hoc experiments).

    Args:
        rubric_scores: Mapping of criterion name to pass/fail boolean, or None.
        state: Current experiment state.
        experiment_dir: Experiment directory for resolving rubric.md path.
            Required when state has no structured rubric_templates.

    Returns:
        List of rubric-related error dicts.
    """
    if state.current_step != "iterate":
        return []

    if rubric_scores is None:
        return [
            {
                "code": MISSING_RUBRIC_SCORES,
                "message": (
                    "The 'iterate' step requires 'rubric_scores' (dict[str, bool]) to be provided. "
                    "The 'criteria_passed' string artefact is no longer accepted."
                ),
            }
        ]

    if not rubric_scores:
        return [
            {
                "code": MISSING_RUBRIC_SCORES,
                "message": "rubric_scores must not be empty. Provide a score for each criterion.",
            }
        ]

    # Discover expected criteria
    known_criteria: list[str] = []
    if experiment_dir is not None:
        known_criteria = _get_rubric_criteria(state, experiment_dir)

    errors: list[dict[str, Any]] = []

    if known_criteria:
        # Check completeness: every known criterion must have a score
        missing_criteria = [c for c in known_criteria if c not in rubric_scores]
        if missing_criteria:
            errors.append({
                "code": INCOMPLETE_RUBRIC_SCORES,
                "missing_criteria": missing_criteria,
                "message": (
                    f"rubric_scores is missing entries for: {', '.join(missing_criteria)}. "
                    "Every rubric criterion must be scored."
                ),
            })

        # Check for unknown criteria: extra keys not in known_criteria
        unknown_criteria = [c for c in rubric_scores if c not in known_criteria]
        if unknown_criteria:
            errors.append({
                "code": UNKNOWN_RUBRIC_CRITERIA,
                "unknown_criteria": unknown_criteria,
                "message": (
                    f"rubric_scores contains unknown criteria: {', '.join(unknown_criteria)}. "
                    "These do not match any criterion in the experiment's rubric."
                ),
            })

    return errors


def validate_iteration_output(state: ExperimentState, artefacts: dict[str, str]) -> list[dict[str, Any]]:
    """Check that per-iteration output file is provided for iterate steps.

    Requires 'output-iterN.md' where N = iteration_count + 1 (the iteration
    being completed). Called only for the 'iterate' step.

    Args:
        state: Current experiment state (iteration_count before increment).
        artefacts: Artefacts submitted for this step.

    Returns:
        List with one MISSING_ITERATION_OUTPUT error if the required key is absent,
        empty list otherwise.
    """
    if state.current_step != "iterate":
        return []

    # iteration_count is incremented during the step; validation runs before increment.
    # After baseline (iter0), first iterate call has iteration_count=0, so expected = iter1.
    expected_key = f"output-iter{state.iteration_count + 1}.md"

    if expected_key not in artefacts:
        return [
            {
                "code": MISSING_ITERATION_OUTPUT,
                "expected": expected_key,
                "message": (
                    f"Iteration output '{expected_key}' is required but was not provided. "
                    "Each iteration must capture its output for retrospective analysis."
                ),
            }
        ]

    return []
