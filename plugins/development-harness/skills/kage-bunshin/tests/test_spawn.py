"""Tests for kage-bunshin spawn.py — bidirectional session manager."""

from __future__ import annotations

import json
import os
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
    # _slugify truncates to _NAME_MAX_CHARS (30) and strips trailing hyphens.
    long_text = "a" * 100
    result = _spawn._slugify(long_text)
    assert len(result) <= _spawn._NAME_MAX_CHARS


def test_slugify_with_trailing_hyphens_strips_them():
    # Input that would produce trailing hyphens after truncation.
    text = "hello" + "-" * 25
    result = _spawn._slugify(text)
    assert not result.endswith("-")


def test_slugify_with_empty_string_returns_empty():
    result = _spawn._slugify("")
    assert result == ""


# ---------------------------------------------------------------------------
# _repo_slug
# ---------------------------------------------------------------------------


def test_repo_slug_replaces_slashes_with_hyphens():
    result = _spawn._repo_slug(Path("/home/user/repos/claude_skills"))
    assert result == "-home-user-repos-claude_skills"


def test_repo_slug_leading_hyphen_is_intentional():
    result = _spawn._repo_slug(Path("/foo/bar"))
    assert result.startswith("-")


# ---------------------------------------------------------------------------
# _dh_state_home
# ---------------------------------------------------------------------------


def test_dh_state_home_returns_default_when_env_unset():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DH_STATE_HOME", None)
        result = _spawn._dh_state_home()
    assert result == Path.home() / ".dh"


def test_dh_state_home_respects_env_override(tmp_path):
    with patch.dict(os.environ, {"DH_STATE_HOME": str(tmp_path)}):
        result = _spawn._dh_state_home()
    assert result == tmp_path


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def test_load_registry_returns_empty_dict_when_file_absent(tmp_path):
    result = _spawn._load_registry(tmp_path)
    assert result == {}


def test_save_and_load_registry_round_trips(tmp_path):
    registry = {"mysession": {"name": "mysession", "model": "sonnet"}}
    _spawn._save_registry(tmp_path, registry)
    loaded = _spawn._load_registry(tmp_path)
    assert loaded == registry


def test_save_registry_writes_atomically(tmp_path):
    registry = {"a": {"name": "a"}}
    _spawn._save_registry(tmp_path, registry)
    rp = _spawn._registry_path(tmp_path)
    assert rp.exists()
    # No .tmp file should remain.
    assert not rp.with_suffix(".tmp").exists()


def test_get_session_raises_system_exit_when_missing(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        _spawn._get_session(tmp_path, "nonexistent")
    assert exc_info.value.code == 1


def test_get_session_returns_entry_when_present(tmp_path):
    registry = {"mysess": {"name": "mysess", "model": "haiku"}}
    _spawn._save_registry(tmp_path, registry)
    result = _spawn._get_session(tmp_path, "mysess")
    assert result["model"] == "haiku"


# ---------------------------------------------------------------------------
# tmux helpers
# ---------------------------------------------------------------------------


def test_tmux_session_name_prefixes_with_kb():
    assert _spawn._tmux_session_name("myname") == "kb-myname"


def test_tmux_alive_returns_false_when_session_absent():
    # Use an implausible session name that won't exist.
    result = _spawn._tmux_alive("kage-bunshin-test-nonexistent-xyzzy-99999")
    assert result is False


# ---------------------------------------------------------------------------
# _make_user_message
# ---------------------------------------------------------------------------


def test_make_user_message_produces_valid_stream_json():
    raw = _spawn._make_user_message("hello there")
    parsed = json.loads(raw)
    assert parsed["type"] == "user"
    assert parsed["message"]["role"] == "user"
    assert parsed["message"]["content"] == "hello there"


# ---------------------------------------------------------------------------
# _format_age
# ---------------------------------------------------------------------------


def test_format_age_seconds():
    assert _spawn._format_age(45) == "45s"


def test_format_age_minutes():
    assert _spawn._format_age(120) == "2m"


def test_format_age_hours():
    assert _spawn._format_age(7200) == "2h"


def test_format_age_days():
    assert _spawn._format_age(172800) == "2d"


# ---------------------------------------------------------------------------
# _parse_jsonl_events
# ---------------------------------------------------------------------------


def test_parse_jsonl_events_returns_empty_list_when_file_absent(tmp_path):
    result = _spawn._parse_jsonl_events(tmp_path / "nonexistent.jsonl")
    assert result == []


def test_parse_jsonl_events_parses_valid_lines(tmp_path):
    output = tmp_path / "out.jsonl"
    output.write_text('{"type":"assistant","message":{"content":"hi"}}\n{"type":"result","cost_usd":0.01}\n')
    events = _spawn._parse_jsonl_events(output)
    assert len(events) == 2
    assert events[0]["type"] == "assistant"
    assert events[1]["type"] == "result"


def test_parse_jsonl_events_skips_malformed_lines(tmp_path):
    output = tmp_path / "out.jsonl"
    output.write_text('{"type":"result"}\nNOT JSON\n{"type":"assistant"}\n')
    events = _spawn._parse_jsonl_events(output)
    assert len(events) == 2


# ---------------------------------------------------------------------------
# _extract_assistant_text
# ---------------------------------------------------------------------------


def test_extract_assistant_text_returns_none_when_no_assistant_event():
    events = [{"type": "result", "cost_usd": 0.01}]
    assert _spawn._extract_assistant_text(events) is None


def test_extract_assistant_text_extracts_string_content():
    events = [{"type": "assistant", "message": {"content": "Hello!"}}]
    result = _spawn._extract_assistant_text(events)
    assert result == "Hello!"


def test_extract_assistant_text_extracts_list_content():
    events = [
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Part one. "}, {"type": "text", "text": "Part two."}]},
        }
    ]
    result = _spawn._extract_assistant_text(events)
    assert result == "Part one. Part two."


def test_extract_assistant_text_returns_last_assistant_message():
    events = [
        {"type": "assistant", "message": {"content": "First"}},
        {"type": "assistant", "message": {"content": "Second"}},
    ]
    result = _spawn._extract_assistant_text(events)
    assert result == "Second"


# ---------------------------------------------------------------------------
# Argument parser — subcommands
# ---------------------------------------------------------------------------


def test_build_parser_spawn_subcommand_parses_prompt():
    parser = _spawn._build_parser()
    args = parser.parse_args(["spawn", "my prompt"])
    assert args.prompt == ["my prompt"]
    assert args.model == "sonnet"
    assert args.worktree is False
    assert args.max_budget is None
    assert args.name is None


def test_build_parser_spawn_with_all_flags():
    parser = _spawn._build_parser()
    args = parser.parse_args([
        "spawn",
        "--name",
        "sess",
        "--worktree",
        "--model",
        "opus",
        "--max-budget",
        "3.0",
        "prompt",
    ])
    assert args.name == "sess"
    assert args.worktree is True
    assert args.model == "opus"
    assert args.max_budget == pytest.approx(3.0)


def test_build_parser_send_requires_name():
    parser = _spawn._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["send", "message"])


def test_build_parser_send_with_name_and_message():
    parser = _spawn._build_parser()
    args = parser.parse_args(["send", "--name", "mysess", "hello"])
    assert args.name == "mysess"
    assert args.message == ["hello"]


def test_build_parser_read_defaults():
    parser = _spawn._build_parser()
    args = parser.parse_args(["read", "--name", "s"])
    assert args.wait == pytest.approx(0.0)
    assert args.follow is False


def test_build_parser_read_follow_flag():
    parser = _spawn._build_parser()
    args = parser.parse_args(["read", "--name", "s", "--follow"])
    assert args.follow is True


def test_build_parser_read_wait_option():
    parser = _spawn._build_parser()
    args = parser.parse_args(["read", "--name", "s", "--wait", "10"])
    assert args.wait == pytest.approx(10.0)


def test_build_parser_kill_requires_name():
    parser = _spawn._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["kill"])


def test_build_parser_list_has_no_required_args():
    parser = _spawn._build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_build_parser_status_requires_name():
    parser = _spawn._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["status"])


# ---------------------------------------------------------------------------
# cmd_spawn — integration with subprocess mocked
# ---------------------------------------------------------------------------


def _make_spawn_args(
    tmp_path: Path,
    name: str = "testsess",
    prompt: str = "hello world",
    model: str = "sonnet",
    worktree: bool = False,
    max_budget: float | None = None,
) -> MagicMock:
    """Build a mock Namespace for cmd_spawn."""
    ns = MagicMock()
    ns.name = name
    ns.prompt = [prompt]
    ns.model = model
    ns.worktree = worktree
    ns.max_budget = max_budget
    return ns


def test_cmd_spawn_exits_1_when_claude_not_in_path(tmp_path):
    args = _make_spawn_args(tmp_path)
    with (
        patch("shutil.which", return_value=None),
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        pytest.raises(SystemExit) as exc_info,
    ):
        _spawn.cmd_spawn(args)
    assert exc_info.value.code == 1


def test_cmd_spawn_exits_1_when_tmux_not_in_path(tmp_path):
    args = _make_spawn_args(tmp_path)

    def fake_which(name: str) -> str | None:
        return "/usr/bin/claude" if name == "claude" else None

    with (
        patch("shutil.which", side_effect=fake_which),
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        pytest.raises(SystemExit) as exc_info,
    ):
        _spawn.cmd_spawn(args)
    assert exc_info.value.code == 1


def test_cmd_spawn_creates_fifo_and_registry_entry(tmp_path, capsys):
    args = _make_spawn_args(tmp_path)

    fake_run_result = MagicMock()
    fake_run_result.returncode = 0
    fake_run_result.stderr = ""

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch("subprocess.run", return_value=fake_run_result),
        patch("subprocess.Popen"),
        patch.object(_spawn, "_write_to_fifo"),
    ):
        _spawn.cmd_spawn(args)

    # Registry entry written.
    registry = _spawn._load_registry(tmp_path)
    assert "testsess" in registry
    entry = registry["testsess"]
    assert entry["model"] == "sonnet"
    assert entry["worktree"] is False
    assert "fifo_path" in entry
    assert "output_path" in entry

    # JSON record printed to stdout.
    captured = capsys.readouterr()
    record = json.loads(captured.out)
    assert record["name"] == "testsess"
    assert record["model"] == "sonnet"
    assert "tmux_session" in record


def test_cmd_spawn_exits_1_when_tmux_fails(tmp_path):
    args = _make_spawn_args(tmp_path)

    fake_run_result = MagicMock()
    fake_run_result.returncode = 1
    fake_run_result.stderr = "duplicate session"

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch("subprocess.run", return_value=fake_run_result),
        pytest.raises(SystemExit) as exc_info,
    ):
        _spawn.cmd_spawn(args)
    assert exc_info.value.code == 1


def test_cmd_spawn_includes_worktree_flag_in_claude_cmd(tmp_path, capsys):
    args = _make_spawn_args(tmp_path, worktree=True)

    fake_run_result = MagicMock()
    fake_run_result.returncode = 0
    fake_run_result.stderr = ""

    captured_shell_cmd: list[str] = []

    def fake_run(cmd, **kwargs):
        if "new-session" in cmd:
            captured_shell_cmd.append(cmd[-1])  # last arg is the shell_cmd
        return fake_run_result

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch("subprocess.run", side_effect=fake_run),
        patch("subprocess.Popen"),
        patch.object(_spawn, "_write_to_fifo"),
    ):
        _spawn.cmd_spawn(args)

    assert captured_shell_cmd, "tmux new-session was not called"
    shell_cmd = captured_shell_cmd[0]
    assert "--worktree" in shell_cmd


# ---------------------------------------------------------------------------
# cmd_send
# ---------------------------------------------------------------------------


def test_cmd_send_exits_1_when_session_not_found(tmp_path):
    ns = MagicMock()
    ns.name = "nosuchsession"
    ns.message = ["hi"]
    with patch.object(_spawn, "_session_state_dir", return_value=tmp_path), pytest.raises(SystemExit) as exc_info:
        _spawn.cmd_send(ns)
    assert exc_info.value.code == 1


def test_cmd_send_exits_1_when_tmux_dead(tmp_path):
    registry = {
        "sess": {
            "name": "sess",
            "model": "sonnet",
            "fifo_path": str(tmp_path / "sess-input.fifo"),
            "output_path": str(tmp_path / "sess-output.jsonl"),
            "error_path": str(tmp_path / "sess-err.log"),
            "tmux_session": "kb-sess",
        }
    }
    _spawn._save_registry(tmp_path, registry)

    ns = MagicMock()
    ns.name = "sess"
    ns.message = ["hello"]

    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_tmux_alive", return_value=False),
        pytest.raises(SystemExit) as exc_info,
    ):
        _spawn.cmd_send(ns)
    assert exc_info.value.code == 1


def test_cmd_send_writes_stream_json_to_fifo(tmp_path, capsys):
    fifo_path = tmp_path / "sess-input.fifo"
    registry = {
        "sess": {
            "name": "sess",
            "model": "sonnet",
            "fifo_path": str(fifo_path),
            "output_path": str(tmp_path / "sess-output.jsonl"),
            "error_path": str(tmp_path / "sess-err.log"),
            "tmux_session": "kb-sess",
        }
    }
    _spawn._save_registry(tmp_path, registry)
    fifo_path.touch()  # Simulate an existing fifo for the exists() check.

    ns = MagicMock()
    ns.name = "sess"
    ns.message = ["do the thing"]

    written: list[str] = []

    def fake_write(path: Path, line: str, **_kwargs: object) -> None:
        written.append(line)

    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_tmux_alive", return_value=True),
        patch.object(_spawn, "_write_to_fifo", side_effect=fake_write),
    ):
        _spawn.cmd_send(ns)

    assert len(written) == 1
    parsed = json.loads(written[0])
    assert parsed["type"] == "user"
    assert parsed["message"]["content"] == "do the thing"


# ---------------------------------------------------------------------------
# cmd_kill
# ---------------------------------------------------------------------------


def test_cmd_kill_removes_registry_entry(tmp_path):
    fifo_path = tmp_path / "sess-input.fifo"
    registry = {"sess": {"name": "sess", "fifo_path": str(fifo_path), "tmux_session": "kb-sess"}}
    _spawn._save_registry(tmp_path, registry)
    # Create a real FIFO for the unlink test.
    os.mkfifo(fifo_path)

    ns = MagicMock()
    ns.name = "sess"

    with patch.object(_spawn, "_session_state_dir", return_value=tmp_path), patch.object(_spawn, "_tmux_kill"):
        _spawn.cmd_kill(ns)

    assert "sess" not in _spawn._load_registry(tmp_path)
    assert not fifo_path.exists()


def test_cmd_kill_exits_1_when_session_not_found(tmp_path):
    ns = MagicMock()
    ns.name = "ghost"
    with patch.object(_spawn, "_session_state_dir", return_value=tmp_path), pytest.raises(SystemExit) as exc_info:
        _spawn.cmd_kill(ns)
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------


def test_cmd_list_prints_no_sessions_when_registry_empty(tmp_path, capsys):
    ns = MagicMock()
    with patch.object(_spawn, "_session_state_dir", return_value=tmp_path):
        _spawn.cmd_list(ns)
    captured = capsys.readouterr()
    assert "No sessions" in captured.out


def test_cmd_list_shows_alive_and_dead_sessions(tmp_path, capsys):
    registry = {
        "alive-sess": {
            "name": "alive-sess",
            "model": "sonnet",
            "spawned_at": "2026-01-01T00:00:00+00:00",
            "worktree": False,
            "tmux_session": "kb-alive-sess",
        },
        "dead-sess": {
            "name": "dead-sess",
            "model": "haiku",
            "spawned_at": "2026-01-01T00:00:00+00:00",
            "worktree": True,
            "tmux_session": "kb-dead-sess",
        },
    }
    _spawn._save_registry(tmp_path, registry)

    def fake_alive(name: str) -> bool:
        return name == "alive-sess"

    ns = MagicMock()
    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_tmux_alive", side_effect=fake_alive),
    ):
        _spawn.cmd_list(ns)

    captured = capsys.readouterr()
    assert "alive-sess" in captured.out
    assert "dead-sess" in captured.out
    assert "alive" in captured.out
    assert "dead" in captured.out


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------


def test_cmd_status_shows_alive_true(tmp_path, capsys):
    output_path = tmp_path / "sess-output.jsonl"
    output_path.write_text("")
    registry = {
        "sess": {
            "name": "sess",
            "model": "sonnet",
            "spawned_at": "2026-01-01T00:00:00+00:00",
            "worktree": False,
            "tmux_session": "kb-sess",
            "output_path": str(output_path),
        }
    }
    _spawn._save_registry(tmp_path, registry)

    ns = MagicMock()
    ns.name = "sess"

    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_tmux_alive", return_value=True),
    ):
        _spawn.cmd_status(ns)

    captured = capsys.readouterr()
    status = json.loads(captured.out)
    assert status["alive"] is True
    assert status["model"] == "sonnet"


def test_cmd_status_extracts_cost_from_result_event(tmp_path, capsys):
    output_path = tmp_path / "sess-output.jsonl"
    output_path.write_text('{"type":"result","cost_usd":0.05,"num_turns":3}\n')

    registry = {
        "sess": {
            "name": "sess",
            "model": "sonnet",
            "spawned_at": "2026-01-01T00:00:00+00:00",
            "worktree": False,
            "tmux_session": "kb-sess",
            "output_path": str(output_path),
        }
    }
    _spawn._save_registry(tmp_path, registry)

    ns = MagicMock()
    ns.name = "sess"

    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_tmux_alive", return_value=False),
    ):
        _spawn.cmd_status(ns)

    captured = capsys.readouterr()
    status = json.loads(captured.out)
    assert status["cost_usd"] == pytest.approx(0.05)
    assert status["turns"] == 3


# ---------------------------------------------------------------------------
# cmd_read
# ---------------------------------------------------------------------------


def test_cmd_read_prints_latest_assistant_text(tmp_path, capsys):
    output_path = tmp_path / "sess-output.jsonl"
    output_path.write_text('{"type":"assistant","message":{"content":"The answer is 42."}}\n')
    registry = {"sess": {"name": "sess", "output_path": str(output_path), "tmux_session": "kb-sess"}}
    _spawn._save_registry(tmp_path, registry)

    ns = MagicMock()
    ns.name = "sess"
    ns.wait = 0.0
    ns.follow = False

    with patch.object(_spawn, "_session_state_dir", return_value=tmp_path):
        _spawn.cmd_read(ns)

    captured = capsys.readouterr()
    assert "The answer is 42." in captured.out


def test_cmd_read_with_wait_polls_until_content_appears(tmp_path, capsys):
    output_path = tmp_path / "sess-output.jsonl"

    call_count = 0

    def fake_parse(path: Path) -> list[dict]:
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            return [{"type": "assistant", "message": {"content": "Delayed reply."}}]
        return []

    registry = {"sess": {"name": "sess", "output_path": str(output_path), "tmux_session": "kb-sess"}}
    _spawn._save_registry(tmp_path, registry)

    ns = MagicMock()
    ns.name = "sess"
    ns.wait = 10.0
    ns.follow = False

    with (
        patch.object(_spawn, "_session_state_dir", return_value=tmp_path),
        patch.object(_spawn, "_parse_jsonl_events", side_effect=fake_parse),
        patch("time.sleep"),
    ):
        _spawn.cmd_read(ns)

    captured = capsys.readouterr()
    assert "Delayed reply." in captured.out


# ---------------------------------------------------------------------------
# _write_to_fifo — error path
# ---------------------------------------------------------------------------


def test_write_to_fifo_exits_when_no_reader(tmp_path):
    fifo_path = tmp_path / "test.fifo"
    os.mkfifo(fifo_path)
    # No reader — all retries should exhaust and _die should be called.
    with pytest.raises(SystemExit) as exc_info:
        _spawn._write_to_fifo(fifo_path, '{"type":"user"}', retries=2, delay=0.01)
    assert exc_info.value.code == 1
