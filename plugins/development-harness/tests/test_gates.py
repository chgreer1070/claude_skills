"""Tests for dispatch_schema.gates.run_quality_gates.

Unit tests mock subprocess.run and shutil.which via pytest-mock.
Integration tests (marked integration) run real commands in a tmp directory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from dispatch_schema import GateResult, GateRunMode, run_quality_gates

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_completed(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    """Return a mock CompletedProcess with the given fields."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ---------------------------------------------------------------------------
# Unit tests — FAIL_FAST mode
# ---------------------------------------------------------------------------


def test_run_quality_gates_all_pass_fail_fast_returns_passed_true(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/echo")
    mocker.patch("subprocess.run", return_value=_make_completed(0, stdout="ok"))

    # Act
    result = run_quality_gates(["echo hello", "echo world"], mode=GateRunMode.FAIL_FAST)

    # Assert
    assert isinstance(result, GateResult)
    assert result.passed is True
    assert len(result.results) == 2
    assert result.mode == GateRunMode.FAIL_FAST
    assert all(r.passed for r in result.results)


def test_run_quality_gates_first_fails_fail_fast_stops_after_first(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/false")
    mocker.patch("subprocess.run", return_value=_make_completed(1, stderr="error"))

    # Act
    result = run_quality_gates(["false", "echo should_not_run"], mode=GateRunMode.FAIL_FAST)

    # Assert
    assert result.passed is False
    assert len(result.results) == 1
    assert result.results[0].passed is False
    assert result.results[0].exit_code == 1


def test_run_quality_gates_second_fails_fail_fast_stops_after_second(mocker):
    # Arrange
    which_mock = mocker.patch("shutil.which", return_value="/usr/bin/cmd")
    run_mock = mocker.patch(
        "subprocess.run", side_effect=[_make_completed(0), _make_completed(2, stderr="lint errors")]
    )

    # Act
    result = run_quality_gates(["cmd pass", "cmd fail", "cmd skip"], mode=GateRunMode.FAIL_FAST)

    # Assert
    assert result.passed is False
    assert len(result.results) == 2
    assert result.results[0].passed is True
    assert result.results[1].passed is False
    assert run_mock.call_count == 2
    _ = which_mock  # used


def test_run_quality_gates_command_not_found_produces_exit_127_fail_fast(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value=None)
    run_mock = mocker.patch("subprocess.run")

    # Act
    result = run_quality_gates(["nonexistent-tool --check"], mode=GateRunMode.FAIL_FAST)

    # Assert
    assert result.passed is False
    assert len(result.results) == 1
    cmd_result = result.results[0]
    assert cmd_result.exit_code == 127
    assert cmd_result.passed is False
    assert "nonexistent-tool" in cmd_result.stderr
    assert cmd_result.stdout == ""
    run_mock.assert_not_called()


def test_run_quality_gates_empty_commands_returns_passed_true_fail_fast():
    # Arrange / Act
    result = run_quality_gates([], mode=GateRunMode.FAIL_FAST)

    # Assert
    assert result.passed is True
    assert result.results == []
    assert result.mode == GateRunMode.FAIL_FAST


# ---------------------------------------------------------------------------
# Unit tests — RUN_ALL mode
# ---------------------------------------------------------------------------


def test_run_quality_gates_all_pass_run_all_returns_passed_true(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/echo")
    mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    result = run_quality_gates(["echo a", "echo b", "echo c"], mode=GateRunMode.RUN_ALL)

    # Assert
    assert result.passed is True
    assert len(result.results) == 3
    assert result.mode == GateRunMode.RUN_ALL


def test_run_quality_gates_first_fails_run_all_executes_all_commands(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/cmd")
    run_mock = mocker.patch("subprocess.run", side_effect=[_make_completed(1), _make_completed(0), _make_completed(0)])

    # Act
    result = run_quality_gates(["cmd a", "cmd b", "cmd c"], mode=GateRunMode.RUN_ALL)

    # Assert
    assert result.passed is False
    assert len(result.results) == 3
    assert run_mock.call_count == 3


def test_run_quality_gates_command_not_found_run_all_continues_to_next(mocker):
    # Arrange
    mocker.patch("shutil.which", side_effect=[None, "/usr/bin/echo"])
    mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    result = run_quality_gates(["bad-tool", "echo ok"], mode=GateRunMode.RUN_ALL)

    # Assert
    assert result.passed is False
    assert len(result.results) == 2
    assert result.results[0].exit_code == 127
    assert result.results[0].passed is False
    assert result.results[1].passed is True


def test_run_quality_gates_empty_commands_returns_passed_true_run_all():
    # Arrange / Act
    result = run_quality_gates([], mode=GateRunMode.RUN_ALL)

    # Assert
    assert result.passed is True
    assert result.results == []
    assert result.mode == GateRunMode.RUN_ALL


# ---------------------------------------------------------------------------
# Unit tests — model invariants
# ---------------------------------------------------------------------------


def test_run_quality_gates_command_field_matches_original_string(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/ruff")
    mocker.patch("subprocess.run", return_value=_make_completed(0, stdout="All clear"))
    original_cmd = "ruff check . --select E,W"

    # Act
    result = run_quality_gates([original_cmd])

    # Assert
    assert result.results[0].command == original_cmd


def test_run_quality_gates_stdout_stderr_captured(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/mypy")
    mocker.patch("subprocess.run", return_value=_make_completed(1, stdout="Found 3 errors", stderr="type error detail"))

    # Act
    result = run_quality_gates(["mypy src/"], mode=GateRunMode.RUN_ALL)

    # Assert
    cmd_result = result.results[0]
    assert cmd_result.stdout == "Found 3 errors"
    assert cmd_result.stderr == "type error detail"


def test_run_quality_gates_default_mode_is_fail_fast(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/echo")
    mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act — no mode kwarg
    result = run_quality_gates(["echo hi"])

    # Assert
    assert result.mode == GateRunMode.FAIL_FAST


def test_run_quality_gates_resolved_path_used_as_argv0(mocker):
    # Arrange
    which_mock = mocker.patch("shutil.which", return_value="/usr/local/bin/ruff")
    run_mock = mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    run_quality_gates(["ruff check ."])

    # Assert
    which_mock.assert_called_once_with("ruff")
    call_args = run_mock.call_args[0][0]
    assert call_args[0] == "/usr/local/bin/ruff"
    assert call_args[1] == "check"
    assert call_args[2] == "."


def test_run_quality_gates_cwd_passed_to_subprocess(mocker, tmp_path):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/echo")
    run_mock = mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    run_quality_gates(["echo hi"], cwd=tmp_path)

    # Assert
    _, kwargs = run_mock.call_args
    assert kwargs["cwd"] == tmp_path


def test_run_quality_gates_no_shell_true(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/echo")
    run_mock = mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    run_quality_gates(["echo hi"])

    # Assert — shell kwarg must not be True
    _, kwargs = run_mock.call_args
    assert kwargs.get("shell") is not True


def test_run_quality_gates_shlex_handles_quoted_args(mocker):
    # Arrange
    mocker.patch("shutil.which", return_value="/usr/bin/pytest")
    run_mock = mocker.patch("subprocess.run", return_value=_make_completed(0))

    # Act
    run_quality_gates(['pytest tests/ -k "not slow"'])

    # Assert — quoted arg must be a single token, not split on the space
    call_args = run_mock.call_args[0][0]
    assert call_args == ["/usr/bin/pytest", "tests/", "-k", "not slow"]


# ---------------------------------------------------------------------------
# Integration tests — real subprocess (marked integration)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_run_quality_gates_integration_real_echo_passes(tmp_path: Path):
    # Arrange / Act
    result = run_quality_gates(["echo hello"], cwd=tmp_path)

    # Assert
    assert result.passed is True
    assert result.results[0].exit_code == 0
    assert "hello" in result.results[0].stdout


@pytest.mark.integration
def test_run_quality_gates_integration_false_fails(tmp_path: Path):
    # Arrange / Act
    result = run_quality_gates(["false"], cwd=tmp_path)

    # Assert
    assert result.passed is False
    assert result.results[0].exit_code != 0


@pytest.mark.integration
def test_run_quality_gates_integration_command_not_found(tmp_path: Path):
    # Arrange / Act
    result = run_quality_gates(["zzz-definitely-not-a-real-command-xyz"], cwd=tmp_path)

    # Assert
    assert result.passed is False
    assert result.results[0].exit_code == 127
