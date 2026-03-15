"""Tests for sam_schema.readers.frontmatter_reader — YAML frontmatter in markdown."""

from __future__ import annotations

import pathlib

import pytest
from sam_schema.readers.detect import FormatType
from sam_schema.readers.frontmatter_reader import read_frontmatter_plan

_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Single-task frontmatter file
# ---------------------------------------------------------------------------


def test_read_frontmatter_plan_single_returns_one_task():
    path = _FIXTURES / "yaml_frontmatter_single.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    assert len(task_dicts) == 1


def test_read_frontmatter_plan_single_returns_yaml_frontmatter_format_type():
    path = _FIXTURES / "yaml_frontmatter_single.md"
    _, _, fmt = read_frontmatter_plan(path)
    assert fmt == FormatType.YAML_FRONTMATTER


def test_read_frontmatter_plan_single_task_has_correct_id():
    path = _FIXTURES / "yaml_frontmatter_single.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    assert task_dicts[0].get("task") == "T1"


def test_read_frontmatter_plan_single_task_has_correct_title():
    path = _FIXTURES / "yaml_frontmatter_single.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    assert task_dicts[0].get("title") == "Implement database migration framework"


def test_read_frontmatter_plan_single_task_has_correct_status():
    path = _FIXTURES / "yaml_frontmatter_single.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    assert task_dicts[0].get("status") == "not-started"


# ---------------------------------------------------------------------------
# Multi-task frontmatter file
# ---------------------------------------------------------------------------


def test_read_frontmatter_plan_multi_returns_three_tasks():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    assert len(task_dicts) == 3


def test_read_frontmatter_plan_multi_returns_yaml_frontmatter_format_type():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, _, fmt = read_frontmatter_plan(path)
    assert fmt == FormatType.YAML_FRONTMATTER


def test_read_frontmatter_plan_multi_plan_meta_has_feature():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    plan_meta, _, _ = read_frontmatter_plan(path)
    assert plan_meta.get("feature") == "cache-layer"


def test_read_frontmatter_plan_multi_first_task_is_complete():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    first = next(t for t in task_dicts if t.get("task") == "T1")
    assert first.get("status") == "complete"


def test_read_frontmatter_plan_multi_second_task_is_in_progress():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    second = next(t for t in task_dicts if t.get("task") == "T2")
    assert second.get("status") == "in-progress"


def test_read_frontmatter_plan_multi_third_task_is_not_started():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    third = next(t for t in task_dicts if t.get("task") == "T3")
    assert third.get("status") == "not-started"


def test_read_frontmatter_plan_multi_second_task_has_dependency():
    path = _FIXTURES / "yaml_frontmatter_multi.md"
    _, task_dicts, _ = read_frontmatter_plan(path)
    second = next(t for t in task_dicts if t.get("task") == "T2")
    deps = second.get("dependencies", [])
    assert "T1" in deps


# ---------------------------------------------------------------------------
# Code fence edge case — --- inside ``` blocks must not split segments
# ---------------------------------------------------------------------------


def test_read_frontmatter_plan_code_fence_does_not_split_on_dashes_inside_fence(tmp_path):
    # A multi-task file where a task body has a --- inside a code block.
    # The reader must not split there and must return exactly 2 tasks.
    content = (
        "---\n"
        "feature: fence-test\n"
        "---\n"
        "\n"
        "\n"
        "task: T1\n"
        "title: Task with code fence\n"
        "status: not-started\n"
        "\n"
        "---\n"
        "\n"
        "### Notes\n"
        "\n"
        "```yaml\n"
        "key: value\n"
        "---\n"
        "another: thing\n"
        "```\n"
        "\n"
        "---\n"
        "\n"
        "\n"
        "task: T2\n"
        "title: Second task\n"
        "status: not-started\n"
        "\n"
        "---\n"
    )
    f = tmp_path / "fence_test.md"
    f.write_text(content)
    _, task_dicts, _ = read_frontmatter_plan(f)
    assert len(task_dicts) == 2
    assert task_dicts[0].get("task") == "T1"
    assert task_dicts[1].get("task") == "T2"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_read_frontmatter_plan_nonexistent_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_frontmatter_plan(tmp_path / "missing.md")


def test_read_frontmatter_plan_no_frontmatter_raises_value_error(tmp_path):
    f = tmp_path / "no_fm.md"
    f.write_text("# Just a heading\n\nSome body text.\n")
    with pytest.raises(ValueError, match="frontmatter"):
        read_frontmatter_plan(f)


def test_read_frontmatter_plan_no_closing_delimiter_raises_value_error(tmp_path: pathlib.Path) -> None:
    """Verify ValueError when frontmatter has no closing '---'.

    Tests: Missing closing delimiter detection.
    How: Write file with opening --- but no closing ---.
    Why: Unclosed frontmatter would produce garbage task data.
    """
    f = tmp_path / "unclosed.md"
    f.write_text("---\ntask: T1\ntitle: Unclosed\nstatus: not-started\n")
    with pytest.raises(ValueError, match="closing"):
        read_frontmatter_plan(f)


def test_read_frontmatter_plan_invalid_yaml_in_frontmatter_raises_value_error(tmp_path: pathlib.Path) -> None:
    """Verify ValueError when frontmatter contains invalid YAML.

    Tests: Invalid YAML detection in frontmatter block.
    How: Write file with syntactically broken YAML in frontmatter.
    Why: Corrupt YAML must be rejected, not silently ignored.
    """
    f = tmp_path / "bad_yaml.md"
    f.write_text("---\n  bad: yaml: indentation:\n    - nested\n  bad\n---\n\nBody.\n")
    with pytest.raises(ValueError, match="parse"):
        read_frontmatter_plan(f)


def test_read_frontmatter_plan_multi_with_no_task_blocks_raises_error(tmp_path: pathlib.Path) -> None:
    """Verify error when multi-task file body contains no valid task blocks.

    Tests: No task blocks detection in multi-task frontmatter file.
    How: Write a file with feature frontmatter but only plain key-value YAML
    in the body (no 'task:' or 'task_id:' fields).
    Why: A multi-task file with zero recognized tasks is a data loss scenario.
    """
    # The body must contain valid YAML dicts (not prose) but without task:/task_id: fields
    content = "---\nfeature: empty-feature\n---\n\n---\n\nkey: value\nother: data\n\n---\n"
    f = tmp_path / "no_tasks.md"
    f.write_text(content)
    with pytest.raises(ValueError, match="No task blocks"):
        read_frontmatter_plan(f)


def test_read_frontmatter_plan_single_task_with_task_id_key(tmp_path: pathlib.Path) -> None:
    """Verify single-task file with 'task_id' key works.

    Tests: Alternative task_id key in frontmatter.
    How: Write file using 'task_id' instead of 'task'.
    Why: Some generators use 'task_id' as the key name.
    """
    content = "---\ntask_id: T5\ntitle: Alt key\nstatus: not-started\n---\n\nBody.\n"
    f = tmp_path / "alt_key.md"
    f.write_text(content)
    _, task_dicts, fmt = read_frontmatter_plan(f)
    assert len(task_dicts) == 1
    assert task_dicts[0].get("task") == "T5"
    assert fmt == FormatType.YAML_FRONTMATTER
