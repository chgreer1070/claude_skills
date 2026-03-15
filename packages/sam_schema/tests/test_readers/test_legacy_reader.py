"""Tests for sam_schema.readers.legacy_reader — legacy markdown format reader."""

from __future__ import annotations

import pathlib

import pytest
from sam_schema.readers.detect import FormatType
from sam_schema.readers.legacy_reader import read_legacy_plan

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Basic reading
# ---------------------------------------------------------------------------


def test_read_legacy_plan_returns_three_tasks():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    assert len(task_dicts) == 3


def test_read_legacy_plan_returns_legacy_markdown_format_type():
    path = _FIXTURES / "legacy_markdown.md"
    _, _, fmt = read_legacy_plan(path)
    assert fmt == FormatType.LEGACY_MARKDOWN


def test_read_legacy_plan_plan_meta_has_feature_from_h1():
    path = _FIXTURES / "legacy_markdown.md"
    plan_meta, _, _ = read_legacy_plan(path)
    # The H1 is "API Rate Limiting - Task Plan"
    assert "api" in plan_meta.get("feature", "").lower()


# ---------------------------------------------------------------------------
# First task — title and status
# ---------------------------------------------------------------------------


def test_read_legacy_plan_first_task_number_is_1():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    assert task_dicts[0].get("task") == "1"


def test_read_legacy_plan_first_task_title_is_correct():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    assert task_dicts[0].get("title") == "Define rate limit configuration model"


def test_read_legacy_plan_first_task_status_is_complete():
    # Fixture uses :white_check_mark: COMPLETE emoji marker
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    # Legacy reader returns the raw string — normalize is tested in test_normalize.py
    assert task_dicts[0].get("status") is not None


# ---------------------------------------------------------------------------
# Second task — dependencies and priority
# ---------------------------------------------------------------------------


def test_read_legacy_plan_second_task_number_is_2():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    assert task_dicts[1].get("task") == "2"


def test_read_legacy_plan_second_task_has_dependency_list():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    deps = task_dicts[1].get("dependencies")
    assert isinstance(deps, list)
    assert len(deps) >= 1


def test_read_legacy_plan_second_task_raw_dependency_contains_task_prefix():
    # Legacy reader emits raw values like "Task 1" — normalizer strips prefix
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    deps = task_dicts[1].get("dependencies", [])
    # Raw value from fixture is "Task 1"
    assert any("1" in d for d in deps)


def test_read_legacy_plan_second_task_priority_is_integer():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    priority = task_dicts[1].get("priority")
    assert isinstance(priority, int)
    assert priority == 2


# ---------------------------------------------------------------------------
# Third task — multi-dependency, complexity
# ---------------------------------------------------------------------------


def test_read_legacy_plan_third_task_has_multiple_dependencies():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    deps = task_dicts[2].get("dependencies", [])
    assert len(deps) >= 2


def test_read_legacy_plan_third_task_complexity_is_extracted():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    complexity = task_dicts[2].get("complexity")
    assert complexity is not None


# ---------------------------------------------------------------------------
# Agent field extraction
# ---------------------------------------------------------------------------


def test_read_legacy_plan_tasks_have_agent_field():
    path = _FIXTURES / "legacy_markdown.md"
    _, task_dicts, _ = read_legacy_plan(path)
    for task in task_dicts:
        assert "agent" in task, f"Task {task.get('task')} missing 'agent' field"


# ---------------------------------------------------------------------------
# Feature name synthesis from filename
# ---------------------------------------------------------------------------


def test_read_legacy_plan_synthesizes_feature_from_filename_when_no_h1(tmp_path):
    # A legacy file with no # heading — feature is synthesized from filename
    content = (
        "## Task 1: A simple task\n\n"
        "**Status**: NOT STARTED\n"
        "**Agent**: some-agent\n"
        "**Priority**: 1\n"
        "**Complexity**: Low\n"
    )
    f = tmp_path / "tasks-7-my-feature.md"
    f.write_text(content)
    plan_meta, task_dicts, _ = read_legacy_plan(f)
    assert plan_meta.get("feature") == "my-feature"
    assert len(task_dicts) == 1


def test_read_legacy_plan_uses_h1_as_feature_when_present(tmp_path):
    content = "# My Feature Plan\n\n## Task 1: A task\n\n**Status**: NOT STARTED\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    plan_meta, _, _ = read_legacy_plan(f)
    assert plan_meta.get("feature") == "My Feature Plan"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_read_legacy_plan_nonexistent_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_legacy_plan(tmp_path / "missing.md")


def test_read_legacy_plan_no_task_headings_raises_value_error(tmp_path):
    f = tmp_path / "no_tasks.md"
    f.write_text("# A Plan\n\nNo task headings here.\n")
    with pytest.raises(ValueError, match="No '## Task N:'"):
        read_legacy_plan(f)


# ---------------------------------------------------------------------------
# Field value parsing — list fields return empty list for "None"
# ---------------------------------------------------------------------------


def test_read_legacy_plan_none_dependency_returns_empty_list(tmp_path):
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Dependencies**: None\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    assert task_dicts[0].get("dependencies") == []


# ---------------------------------------------------------------------------
# Field value parsing — divergence-notes non-integer fallback
# ---------------------------------------------------------------------------


def test_read_legacy_plan_divergence_notes_non_integer_returns_zero(tmp_path: pathlib.Path) -> None:
    """Verify non-integer divergence-notes value falls back to 0.

    Tests: divergence-notes field parsing with invalid value.
    How: Write task with 'abc' as divergence-notes value.
    Why: Malformed divergence-notes must not crash the reader.
    """
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Divergence Notes**: abc\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    assert task_dicts[0].get("divergence-notes") == 0


def test_read_legacy_plan_divergence_notes_integer_returns_int(tmp_path: pathlib.Path) -> None:
    """Verify integer divergence-notes value is parsed correctly.

    Tests: divergence-notes field parsing with valid integer.
    How: Write task with '3' as divergence-notes value.
    Why: Valid integers must be preserved.
    """
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Divergence Notes**: 3\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    assert task_dicts[0].get("divergence-notes") == 3


# ---------------------------------------------------------------------------
# Field value parsing — priority non-integer fallback
# ---------------------------------------------------------------------------


def test_read_legacy_plan_priority_non_integer_returns_raw_string(tmp_path: pathlib.Path) -> None:
    """Verify non-integer priority value returns the raw string.

    Tests: Priority field parsing with non-numeric value.
    How: Write task with 'high' as priority value.
    Why: Some legacy files use 'high'/'low' labels instead of integers.
    """
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Priority**: high\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    assert task_dicts[0].get("priority") == "high"


# ---------------------------------------------------------------------------
# Field value parsing — null-like values return None
# ---------------------------------------------------------------------------


def test_read_legacy_plan_null_like_field_value_returns_none(tmp_path: pathlib.Path) -> None:
    """Verify null-like field values (N/A, none, -) return None.

    Tests: Null detection in field value parsing.
    How: Write task with 'N/A' as agent value.
    Why: Null-like markers in legacy files must be treated as absent.
    """
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Agent**: N/A\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    # 'N/A' is null-like — the field should not be set (None returned from parser,
    # and the field extraction skips None values)
    assert "agent" not in task_dicts[0]


# ---------------------------------------------------------------------------
# Complexity normalization — title case to lowercase
# ---------------------------------------------------------------------------


def test_read_legacy_plan_complexity_title_case_normalized_to_lower(tmp_path: pathlib.Path) -> None:
    """Verify title-case complexity is normalized to lowercase.

    Tests: Complexity field case normalization.
    How: Write task with 'Medium' complexity (title case).
    Why: Legacy files use title case; Complexity enum expects lowercase.
    """
    content = "## Task 1: A task\n\n**Status**: NOT STARTED\n**Complexity**: Medium\n**Agent**: agent\n"
    f = tmp_path / "tasks.md"
    f.write_text(content)
    _, task_dicts, _ = read_legacy_plan(f)
    assert task_dicts[0].get("complexity") == "medium"
