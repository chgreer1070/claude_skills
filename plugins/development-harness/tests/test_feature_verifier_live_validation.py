"""Tests for the feature verifier live validation step (Step 8).

Verifies that check_live_validation() reads quality_gates.live_validation from
.dh/language-manifest.yaml and returns the correct LiveValidationOutcome for
each branch described in the feature-verifier agent Step 8 protocol.

Not marked pytest.mark.e2e — all tests run in the default suite with no
external services or API tokens required.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from live_validation_step import (
    GAP_MESSAGE_NO_LIVE_VALIDATION,
    MANIFEST_RELATIVE_PATH,
    LiveValidationResult,
    check_live_validation,
)
from manifest_schema import load_manifest

# Repo root resolved from this file's location
# plugins/development-harness/tests/ → development-harness/ → plugins/ → repo root
_REPO_ROOT = Path(__file__).parent.parent.parent.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_manifest(project_root: Path, quality_gates_yaml: str = "") -> None:
    """Write a minimal valid language manifest to .dh/language-manifest.yaml.

    Args:
        project_root: Directory that acts as the project root under test.
        quality_gates_yaml: Optional YAML block for the quality_gates section,
            e.g. ``"quality_gates:\\n  live_validation: 'echo ok'\\n"``.
            Omit to produce a manifest with no quality_gates section.
    """
    dh_dir = project_root / ".dh"
    dh_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = dh_dir / "language-manifest.yaml"
    manifest_path.write_text(
        dedent("""\
            name: test-manifest
            language: python
            version: "1.0"
            project_detection:
              markers:
                - pyproject.toml
            """)
        + quality_gates_yaml
    )


# ---------------------------------------------------------------------------
# 8 test functions — one per acceptance-criteria scenario
# ---------------------------------------------------------------------------


def test_command_exits_0_no_gap(tmp_path: Path) -> None:
    """When live_validation is a command that exits 0, result is PASS with no gap."""
    # Arrange
    _write_manifest(tmp_path, "quality_gates:\n  live_validation: 'echo ok'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.PASS
    assert outcome.gap_message is None
    assert outcome.exit_code == 0


def test_command_exits_nonzero_gaps_found(tmp_path: Path) -> None:
    """When live_validation command exits non-zero, result is GAPS_FOUND."""
    # Arrange — `false` reliably exits 1 on all POSIX systems
    _write_manifest(tmp_path, "quality_gates:\n  live_validation: 'false'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.GAPS_FOUND
    assert outcome.exit_code is not None
    assert outcome.exit_code != 0


def test_agent_browser_deferred_no_gap(tmp_path: Path) -> None:
    """When live_validation is 'agent-browser', result is DEFERRED_BROWSER with no gap."""
    # Arrange
    _write_manifest(tmp_path, "quality_gates:\n  live_validation: 'agent-browser'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.DEFERRED_BROWSER
    assert outcome.gap_message is None


def test_absent_live_validation_gaps_found(tmp_path: Path) -> None:
    """When live_validation key is absent from quality_gates, result is GAPS_FOUND."""
    # Arrange — quality_gates present but live_validation key omitted
    _write_manifest(tmp_path, "quality_gates:\n  lint: 'ruff check .'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.GAPS_FOUND
    assert outcome.gap_message is not None


def test_no_quality_gates_step_skipped(tmp_path: Path) -> None:
    """When the quality_gates section is absent, the live validation step is skipped."""
    # Arrange — no quality_gates key in manifest
    _write_manifest(tmp_path)

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.SKIPPED


def test_gap_message_exact_text(tmp_path: Path) -> None:
    """When live_validation is absent, gap_message matches the exact protocol text."""
    # Arrange
    _write_manifest(tmp_path, "quality_gates:\n  lint: 'ruff check .'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert — exact wording required by the feature verifier Step 8 protocol
    assert outcome.gap_message == GAP_MESSAGE_NO_LIVE_VALIDATION


def test_manifest_read_path_is_dh_language_manifest(tmp_path: Path) -> None:
    """check_live_validation reads the manifest from .dh/language-manifest.yaml."""
    # Assert the constant encodes the canonical path
    assert Path(".dh") / "language-manifest.yaml" == MANIFEST_RELATIVE_PATH

    # Arrange — write manifest at the canonical path
    canonical = tmp_path / MANIFEST_RELATIVE_PATH
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(
        dedent("""\
            name: test-manifest
            language: python
            version: "1.0"
            project_detection:
              markers:
                - pyproject.toml
            quality_gates:
              live_validation: 'echo ok'
            """)
    )

    # Act — function must find the manifest at this path and use it
    outcome = check_live_validation(tmp_path)

    # Assert — manifest was located and live_validation command ran successfully
    assert outcome.result == LiveValidationResult.PASS

    # Removing the file causes the step to skip, proving no alternative path is consulted
    canonical.unlink()
    outcome_after_removal = check_live_validation(tmp_path)
    assert outcome_after_removal.result == LiveValidationResult.SKIPPED


def test_claude_skill_sentinel_deferred_no_gap(tmp_path: Path) -> None:
    """When live_validation is 'claude-skill', result is DEFERRED_SKILL with no gap."""
    # Arrange
    _write_manifest(tmp_path, "quality_gates:\n  live_validation: 'claude-skill'\n")

    # Act
    outcome = check_live_validation(tmp_path)

    # Assert
    assert outcome.result == LiveValidationResult.DEFERRED_SKILL
    assert outcome.gap_message is None


def test_python3_manifest_has_live_validation() -> None:
    """python3 language manifest declares quality_gates.live_validation == 'claude-skill'."""
    # Arrange — resolve path to actual manifest (no fixture, real file)
    manifest_path = _REPO_ROOT / "plugins" / "python3-development" / "manifests" / "python3" / "language-manifest.yaml"

    # Act
    manifest = load_manifest(manifest_path)

    # Assert
    assert manifest.quality_gates is not None
    assert manifest.quality_gates.live_validation == "claude-skill"


def test_python3_cli_manifest_has_live_validation() -> None:
    """python3-cli language manifest declares quality_gates.live_validation == 'claude-skill'."""
    # Arrange — resolve path to actual manifest (no fixture, real file)
    manifest_path = (
        _REPO_ROOT / "plugins" / "python3-development" / "manifests" / "python3-cli" / "language-manifest.yaml"
    )

    # Act
    manifest = load_manifest(manifest_path)

    # Assert
    assert manifest.quality_gates is not None
    assert manifest.quality_gates.live_validation == "claude-skill"
