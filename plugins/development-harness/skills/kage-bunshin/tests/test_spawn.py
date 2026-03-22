"""Tests for kage-bunshin spawn.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the scripts directory to sys.path so spawn can be imported directly.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import spawn as _spawn

# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


def test_slugify_with_plain_text_returns_lowercase_hyphenated():
    result = _spawn._slugify("Hello World")
    assert result == "hello-world"


def test_slugify_with_special_chars_replaces_with_hyphens():
    result = _spawn._slugify("Load /dh:work-backlog-item #42!")
    assert result == "load-dh-work-backlog-item-42"


def test_slugify_with_long_text_truncates_to_max_length():
    long_text = "a" * 100
    result = _spawn._slugify(long_text, max_length=40)
    assert len(result) == 40


def test_slugify_with_trailing_hyphens_strips_them():
    result = _spawn._slugify("hello---", max_length=10)
    assert not result.endswith("-")


def test_slugify_with_empty_string_returns_empty():
    result = _spawn._slugify("")
    assert result == ""


# ---------------------------------------------------------------------------
# _auto_name
# ---------------------------------------------------------------------------


def test_auto_name_with_short_prompt_returns_full_text():
    result = _spawn._auto_name("Short")
    assert result == "Short"


def test_auto_name_with_long_prompt_truncates_to_30_chars():
    prompt = "a" * 100
    result = _spawn._auto_name(prompt)
    assert len(result) == 30


def test_auto_name_strips_leading_trailing_whitespace():
    result = _spawn._auto_name("   spaces   ")
    assert result == "spaces"


# ---------------------------------------------------------------------------
# _parse_args
# ---------------------------------------------------------------------------


def test_parse_args_with_prompt_only_sets_defaults():
    ns = _spawn._parse_args(["my prompt"])
    assert ns.prompt == "my prompt"
    assert ns.model == "sonnet"
    assert ns.worktree is False
    assert ns.branch is None
    assert ns.max_budget is None
    assert ns.name is None
    assert ns.no_session_persistence is False
    assert ns.output_dir == Path("/tmp/kage-bunshin")


def test_parse_args_with_worktree_flag_sets_true():
    ns = _spawn._parse_args(["--worktree", "prompt"])
    assert ns.worktree is True


def test_parse_args_with_model_sets_model():
    ns = _spawn._parse_args(["--model", "opus", "prompt"])
    assert ns.model == "opus"


def test_parse_args_with_max_budget_parses_float():
    ns = _spawn._parse_args(["--max-budget", "2.50", "prompt"])
    assert ns.max_budget == pytest.approx(2.50)


def test_parse_args_with_name_sets_name():
    ns = _spawn._parse_args(["--name", "my-session", "prompt"])
    assert ns.name == "my-session"


def test_parse_args_with_no_session_persistence_sets_flag():
    ns = _spawn._parse_args(["--no-session-persistence", "prompt"])
    assert ns.no_session_persistence is True


def test_parse_args_with_output_dir_sets_path():
    ns = _spawn._parse_args(["--output-dir", "/custom/dir", "prompt"])
    assert ns.output_dir == Path("/custom/dir")


def test_parse_args_with_branch_sets_branch():
    ns = _spawn._parse_args(["--worktree", "--branch", "feature/x", "prompt"])
    assert ns.branch == "feature/x"


# ---------------------------------------------------------------------------
# _build_command
# ---------------------------------------------------------------------------


def test_build_command_minimal_returns_required_flags():
    cmd = _spawn._build_command(
        model="sonnet", max_budget=None, name=None, no_session_persistence=False, prompt="hello"
    )
    assert "claude" in cmd
    assert "-p" in cmd
    assert "--model" in cmd
    assert "sonnet" in cmd
    assert "--permission-mode" in cmd
    assert "auto" in cmd
    assert "--output-format" in cmd
    assert "json" in cmd
    assert cmd[-1] == "hello"


def test_build_command_with_max_budget_includes_flag():
    cmd = _spawn._build_command(model="sonnet", max_budget=1.5, name=None, no_session_persistence=False, prompt="p")
    assert "--max-budget-usd" in cmd
    assert "1.5" in cmd


def test_build_command_with_name_includes_flag():
    cmd = _spawn._build_command(
        model="sonnet", max_budget=None, name="my-name", no_session_persistence=False, prompt="p"
    )
    assert "--name" in cmd
    assert "my-name" in cmd


def test_build_command_with_no_session_persistence_includes_flag():
    cmd = _spawn._build_command(model="sonnet", max_budget=None, name=None, no_session_persistence=True, prompt="p")
    assert "--no-session-persistence" in cmd


def test_build_command_prompt_is_last_element():
    cmd = _spawn._build_command(
        model="sonnet", max_budget=5.0, name="n", no_session_persistence=True, prompt="my prompt"
    )
    assert cmd[-1] == "my prompt"


# ---------------------------------------------------------------------------
# _symlink_shared_artifact
# ---------------------------------------------------------------------------


def test_symlink_shared_artifact_with_nonexistent_source_skips(tmp_path):
    source = tmp_path / "nonexistent"
    dest = tmp_path / "link"
    _spawn._symlink_shared_artifact(source, dest)
    assert not dest.exists()


def test_symlink_shared_artifact_creates_symlink(tmp_path):
    source = tmp_path / "source_dir"
    source.mkdir()
    dest = tmp_path / "link"
    _spawn._symlink_shared_artifact(source, dest)
    assert dest.is_symlink()
    assert dest.resolve() == source.resolve()


def test_symlink_shared_artifact_with_correct_existing_symlink_skips(tmp_path):
    source = tmp_path / "source_dir"
    source.mkdir()
    dest = tmp_path / "link"
    dest.symlink_to(source)
    # Should not raise and should leave the symlink unchanged.
    _spawn._symlink_shared_artifact(source, dest)
    assert dest.resolve() == source.resolve()


def test_symlink_shared_artifact_with_wrong_symlink_skips_with_warning(tmp_path, capsys):
    source = tmp_path / "source_dir"
    source.mkdir()
    other = tmp_path / "other_dir"
    other.mkdir()
    dest = tmp_path / "link"
    dest.symlink_to(other)  # Points to wrong target.
    _spawn._symlink_shared_artifact(source, dest)
    captured = capsys.readouterr()
    assert "warning" in captured.err
    # Symlink must not be changed.
    assert dest.resolve() == other.resolve()


def test_symlink_shared_artifact_with_regular_dir_skips_with_warning(tmp_path, capsys):
    source = tmp_path / "source_dir"
    source.mkdir()
    dest = tmp_path / "existing_dir"
    dest.mkdir()
    _spawn._symlink_shared_artifact(source, dest)
    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert dest.is_dir()
    assert not dest.is_symlink()


# ---------------------------------------------------------------------------
# _write_lock_file
# ---------------------------------------------------------------------------


def test_write_lock_file_creates_file_with_correct_fields(tmp_path):
    lock = _spawn._write_lock_file(tmp_path, "abc-123", "Test prompt", "sonnet")
    assert lock is not None
    assert lock.exists()
    data = json.loads(lock.read_text())
    assert data["session_id"] == "abc-123"
    assert data["model"] == "sonnet"
    assert "spawned_at" in data
    assert "parent_pid" in data
    assert data["item"] == "Test prompt"


def test_write_lock_file_truncates_item_to_100_chars(tmp_path):
    long_prompt = "x" * 200
    lock = _spawn._write_lock_file(tmp_path, "sid", long_prompt, "sonnet")
    assert lock is not None
    data = json.loads(lock.read_text())
    assert len(data["item"]) == 100


def test_write_lock_file_creates_claude_dir_if_missing(tmp_path):
    worktree = tmp_path / "wt"
    worktree.mkdir()
    lock = _spawn._write_lock_file(worktree, "sid", "prompt", "sonnet")
    assert lock is not None
    assert (worktree / ".claude").is_dir()


# ---------------------------------------------------------------------------
# main — integration-level with subprocess mocked
# ---------------------------------------------------------------------------


def test_main_exits_1_when_claude_not_in_path(capsys):
    with patch("shutil.which", return_value=None), pytest.raises(SystemExit) as exc_info:
        _spawn.main(["some prompt"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "claude" in captured.err


def test_main_without_worktree_spawns_process_in_cwd(tmp_path):
    mock_proc = MagicMock()
    mock_proc.pid = 9999

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.Popen", return_value=mock_proc) as mock_popen,
        patch.object(_spawn, "_DEFAULT_OUTPUT_DIR", tmp_path),
    ):
        _spawn.main(["hello world", "--output-dir", str(tmp_path)])

    mock_popen.assert_called_once()
    call_kwargs = mock_popen.call_args
    assert call_kwargs.kwargs.get("stdin") == subprocess.DEVNULL


def test_main_without_worktree_prints_json_record(tmp_path, capsys):
    mock_proc = MagicMock()
    mock_proc.pid = 42

    with patch("shutil.which", return_value="/usr/bin/claude"), patch("subprocess.Popen", return_value=mock_proc):
        _spawn.main(["test prompt", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    record = json.loads(captured.out)
    assert record["pid"] == 42
    assert record["worktree"] is None
    assert record["model"] == "sonnet"
    assert "result_file" in record
    assert "error_file" in record


def test_main_with_name_uses_provided_name(tmp_path, capsys):
    mock_proc = MagicMock()
    mock_proc.pid = 7

    with patch("shutil.which", return_value="/usr/bin/claude"), patch("subprocess.Popen", return_value=mock_proc):
        _spawn.main(["prompt text", "--name", "my-session", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    record = json.loads(captured.out)
    assert record["name"] == "my-session"


def test_main_without_name_auto_derives_name(tmp_path, capsys):
    mock_proc = MagicMock()
    mock_proc.pid = 3

    with patch("shutil.which", return_value="/usr/bin/claude"), patch("subprocess.Popen", return_value=mock_proc):
        _spawn.main(["Load /dh:work-backlog-item #42. Execute.", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    record = json.loads(captured.out)
    # _auto_name takes first 30 chars: "Load /dh:work-backlog-item #42" (the "." is at index 30, excluded)
    assert record["name"] == "Load /dh:work-backlog-item #42"


def test_main_with_worktree_calls_git_worktree_add(tmp_path):
    mock_proc = MagicMock()
    mock_proc.pid = 5

    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    (fake_root / ".git").mkdir()

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if "rev-parse" in cmd and "--show-toplevel" in cmd:
            result.stdout = str(fake_root) + "\n"
        elif "rev-parse" in cmd and "--abbrev-ref" in cmd:
            result.stdout = "main\n"
        elif "worktree" in cmd and "add" in cmd:
            # Actually create the worktree dir so the code can proceed.
            worktree_path = Path(cmd[3])
            worktree_path.mkdir(parents=True, exist_ok=True)
            result.stdout = ""
        else:
            result.stdout = ""
        result.stderr = ""
        return result

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run", side_effect=fake_run),
        patch("subprocess.Popen", return_value=mock_proc),
    ):
        _spawn.main(["prompt", "--worktree", "--output-dir", str(tmp_path)])


def test_main_with_worktree_exits_1_on_git_failure(tmp_path, capsys):
    def fake_run(cmd, **kwargs):
        result = MagicMock()
        if "rev-parse" in cmd and "--show-toplevel" in cmd:
            result.returncode = 0
            result.stdout = str(tmp_path) + "\n"
            result.stderr = ""
        elif "rev-parse" in cmd and "--abbrev-ref" in cmd:
            result.returncode = 0
            result.stdout = "main\n"
            result.stderr = ""
        else:
            # git worktree add fails
            result.returncode = 1
            result.stdout = ""
            result.stderr = "fatal: not a valid ref"
        return result

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run", side_effect=fake_run),
        pytest.raises(SystemExit) as exc_info,
    ):
        _spawn.main(["prompt", "--worktree", "--output-dir", str(tmp_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err
