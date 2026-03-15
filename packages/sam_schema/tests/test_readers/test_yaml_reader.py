"""Tests for sam_schema.readers.yaml_reader — PURE_YAML and DIRECTORY formats."""

from __future__ import annotations

import pathlib

import pytest
from sam_schema.readers.detect import FormatType
from sam_schema.readers.yaml_reader import read_yaml_plan

# Shared fixtures directory
_FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Single-file YAML
# ---------------------------------------------------------------------------


def test_read_yaml_plan_single_file_returns_three_tasks():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _plan_meta, task_dicts, _fmt = read_yaml_plan(path)
    assert len(task_dicts) == 3


def test_read_yaml_plan_single_file_returns_pure_yaml_format_type():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _, _, fmt = read_yaml_plan(path)
    assert fmt == FormatType.PURE_YAML


def test_read_yaml_plan_single_file_plan_meta_has_feature():
    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, _, _ = read_yaml_plan(path)
    assert plan_meta.get("feature") == "auth-system"


def test_read_yaml_plan_single_file_plan_meta_has_version():
    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, _, _ = read_yaml_plan(path)
    assert plan_meta.get("version") == "1.0"


def test_read_yaml_plan_single_file_task_dicts_are_plain_dicts():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _, task_dicts, _ = read_yaml_plan(path)
    for task in task_dicts:
        assert type(task) is dict, f"Expected plain dict, got {type(task)}"


def test_read_yaml_plan_single_file_first_task_has_correct_id():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _, task_dicts, _ = read_yaml_plan(path)
    assert task_dicts[0].get("id") == "T1"


def test_read_yaml_plan_single_file_first_task_has_correct_status():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _, task_dicts, _ = read_yaml_plan(path)
    assert task_dicts[0].get("status") == "complete"


def test_read_yaml_plan_single_file_second_task_has_dependency_list():
    path = _FIXTURES / "pure_yaml_single.yaml"
    _, task_dicts, _ = read_yaml_plan(path)
    deps = task_dicts[1].get("dependencies")
    assert isinstance(deps, list)
    assert "T1" in deps


def test_read_yaml_plan_single_file_tasks_list_removed_from_plan_meta():
    path = _FIXTURES / "pure_yaml_single.yaml"
    plan_meta, _, _ = read_yaml_plan(path)
    assert "tasks" not in plan_meta


# ---------------------------------------------------------------------------
# Directory format
# ---------------------------------------------------------------------------


def test_read_yaml_plan_directory_returns_three_tasks():
    path = _FIXTURES / "pure_yaml_directory"
    _, task_dicts, _ = read_yaml_plan(path)
    assert len(task_dicts) == 3


def test_read_yaml_plan_directory_returns_pure_yaml_format_type():
    path = _FIXTURES / "pure_yaml_directory"
    _, _, fmt = read_yaml_plan(path)
    assert fmt == FormatType.PURE_YAML


def test_read_yaml_plan_directory_plan_meta_has_feature_from_plan_yaml():
    path = _FIXTURES / "pure_yaml_directory"
    plan_meta, _, _ = read_yaml_plan(path)
    assert plan_meta.get("feature") == "logging-pipeline"


def test_read_yaml_plan_directory_tasks_have_ids():
    path = _FIXTURES / "pure_yaml_directory"
    _, task_dicts, _ = read_yaml_plan(path)
    task_ids = {t.get("id") for t in task_dicts}
    assert "T1" in task_ids


def test_read_yaml_plan_directory_no_plan_yaml_synthesizes_feature_from_dirname(tmp_path):
    task_dir = tmp_path / "tasks-99-my-feature"
    task_dir.mkdir()
    task_file = task_dir / "task-T1.yaml"
    task_file.write_text("id: T1\ntitle: A task\nstatus: not-started\n")
    plan_meta, task_dicts, _ = read_yaml_plan(task_dir)
    assert plan_meta.get("feature") == "my-feature"
    assert len(task_dicts) == 1


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_read_yaml_plan_nonexistent_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_yaml_plan(tmp_path / "nonexistent.yaml")


def test_read_yaml_plan_invalid_yaml_raises_value_error(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("feature: test\n  broken: yaml: indentation:\n    - nested\n  bad\n")
    with pytest.raises(ValueError, match="Failed to parse YAML"):
        read_yaml_plan(f)


def test_read_yaml_plan_non_mapping_top_level_raises_type_error(tmp_path):
    f = tmp_path / "list.yaml"
    f.write_text("- item1\n- item2\n")
    with pytest.raises(TypeError):
        read_yaml_plan(f)
