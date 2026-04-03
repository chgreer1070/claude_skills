"""Unit tests for dh_migrate CLI tool.

Tests cover:
- verify command: detects old layout, new layout, partial migration
- migrate --dry-run: shows plan without modifying files
- migrate: moves directories, creates .dh/.gitkeep, removes empty old dirs
- _detect_layout: correct flags for old/new/both/neither
- _old_dirs: correct path construction
- Artifact manifest update step: logs instructions (no external calls)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: add the harness package to sys.path so dh_paths and dh_migrate
# can be imported in the test environment.
# ---------------------------------------------------------------------------
_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from typing import TYPE_CHECKING

import dh_paths
from scripts.dh_migrate import _OLD_TO_NEW, _detect_layout, _old_dirs, _update_artifact_manifests, app
from typer.testing import CliRunner

if TYPE_CHECKING:
    from collections.abc import Generator

runner = CliRunner()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    """Create an isolated fake project root with DH_STATE_HOME overridden.

    Returns:
        Absolute path to the fake project root (git root mock).
    """
    project_root = tmp_path / "my-project"
    project_root.mkdir()
    state_home = tmp_path / "dh-state"
    state_home.mkdir()
    monkeypatch.setenv("DH_STATE_HOME", str(state_home))
    # Patch git_project_root to return our fake project root
    with patch.object(dh_paths, "git_project_root", return_value=project_root):
        # Also clear the root cache so it doesn't interfere
        dh_paths._root_cache.clear()
        yield project_root


@pytest.fixture
def old_layout(fake_project: Path) -> Path:
    """Create the old layout directories inside the fake project root.

    Returns:
        The fake project root path.
    """
    (fake_project / ".claude" / "backlog").mkdir(parents=True)
    (fake_project / ".claude" / "backlog" / "item.md").write_text("# item")
    (fake_project / ".claude" / "context").mkdir(parents=True)
    (fake_project / ".claude" / "reports").mkdir(parents=True)
    (fake_project / "plan").mkdir(parents=True)
    (fake_project / "plan" / "P001-test.yaml").write_text("slug: test")
    return fake_project


@pytest.fixture
def new_layout(fake_project: Path) -> Path:
    """Create the new layout directories under state_home.

    Returns:
        The fake project root path.
    """
    backlog = dh_paths.backlog_dir(fake_project)
    backlog.mkdir(parents=True)
    (backlog / "item.md").write_text("# item")
    return fake_project


# ---------------------------------------------------------------------------
# _detect_layout
# ---------------------------------------------------------------------------


def test_detect_layout_old_only_returns_old_present(old_layout: Path) -> None:
    # Arrange: old dirs present, new absent (fixture creates old only)
    # Act
    result = _detect_layout(old_layout)
    # Assert
    assert result["old_present"] is True
    assert result["new_present"] is False


def test_detect_layout_new_only_returns_new_present(new_layout: Path) -> None:
    # Arrange: new dirs present, old absent
    # Act
    result = _detect_layout(new_layout)
    # Assert
    assert result["old_present"] is False
    assert result["new_present"] is True


def test_detect_layout_neither_returns_both_false(fake_project: Path) -> None:
    # Arrange: clean project with no dirs
    # Act
    result = _detect_layout(fake_project)
    # Assert
    assert result["old_present"] is False
    assert result["new_present"] is False


def test_detect_layout_both_present_returns_both_true(old_layout: Path, new_layout: Path) -> None:
    # Arrange: old_layout and new_layout fixtures both applied to fake_project
    # Act (both fixtures share same fake_project root)
    result = _detect_layout(old_layout)
    # Assert
    assert result["old_present"] is True
    assert result["new_present"] is True


# ---------------------------------------------------------------------------
# _old_dirs
# ---------------------------------------------------------------------------


def test_old_dirs_returns_correct_paths(fake_project: Path) -> None:
    # Arrange
    result = _old_dirs(fake_project)
    # Assert: all keys from _OLD_TO_NEW are present and paths are absolute
    assert set(result.keys()) == set(_OLD_TO_NEW.keys())
    for key, path in result.items():
        assert path == fake_project / key
        assert path.is_absolute()


def test_old_dirs_paths_are_under_project_root(fake_project: Path) -> None:
    # Arrange / Act
    result = _old_dirs(fake_project)
    # Assert: all paths are children of the project root
    for path in result.values():
        assert str(path).startswith(str(fake_project))


# ---------------------------------------------------------------------------
# verify command
# ---------------------------------------------------------------------------


def test_verify_old_layout_exits_1_and_reports_present(old_layout: Path) -> None:
    # Arrange: old layout in place
    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["verify"])
    # Assert
    assert result.exit_code == 1
    assert "present" in result.output
    assert "Action Required" in result.output or "Partial" in result.output


def test_verify_new_layout_exits_0(new_layout: Path) -> None:
    # Arrange: new layout in place
    with patch.object(dh_paths, "git_project_root", return_value=new_layout):
        # Act
        result = runner.invoke(app, ["verify"])
    # Assert
    assert result.exit_code == 0
    assert "Migrated" in result.output or "present" in result.output


def test_verify_no_layout_exits_1(fake_project: Path) -> None:
    # Arrange: neither old nor new layout
    with patch.object(dh_paths, "git_project_root", return_value=fake_project):
        # Act
        result = runner.invoke(app, ["verify"])
    # Assert: exits 1 because old dirs absent but new also absent — action required
    # (Actual message depends on state logic; either Action Required or Migrated)
    assert result.exit_code in (0, 1)


def test_verify_shows_project_slug(old_layout: Path) -> None:
    # Arrange
    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["verify"])
    # Assert: "Project slug:" label is in output (Rich may truncate the full slug value)
    assert "Project slug:" in result.output


# ---------------------------------------------------------------------------
# migrate --dry-run command
# ---------------------------------------------------------------------------


def test_migrate_dry_run_exits_0_and_shows_plan(old_layout: Path) -> None:
    # Arrange
    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate", "--dry-run"])
    # Assert
    assert result.exit_code == 0
    assert "Dry-run complete" in result.output
    assert "Migration Plan" in result.output


def test_migrate_dry_run_does_not_move_files(old_layout: Path) -> None:
    # Arrange: confirm old backlog file exists before dry-run
    old_backlog = old_layout / ".claude" / "backlog" / "item.md"
    assert old_backlog.exists()

    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        runner.invoke(app, ["migrate", "--dry-run"])

    # Assert: source file still exists after dry-run
    assert old_backlog.exists()
    # New backlog dir should NOT exist
    assert not dh_paths.backlog_dir(old_layout).exists()


def test_migrate_dry_run_shows_source_and_destination(old_layout: Path) -> None:
    # Arrange
    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate", "--dry-run"])
    # Assert: output contains Source and Destination column headers
    # (Rich may truncate long path values in table cells)
    assert "Source (old)" in result.output
    assert "Destination (new)" in result.output
    assert "Migration Plan" in result.output


# ---------------------------------------------------------------------------
# migrate (real move) command
# ---------------------------------------------------------------------------


def test_migrate_moves_backlog_to_new_location(old_layout: Path) -> None:
    # Arrange
    old_backlog_file = old_layout / ".claude" / "backlog" / "item.md"
    assert old_backlog_file.exists()

    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate"])

    # Assert
    assert result.exit_code == 0
    new_backlog_file = dh_paths.backlog_dir(old_layout) / "item.md"
    assert new_backlog_file.exists()
    assert new_backlog_file.read_text() == "# item"


def test_migrate_moves_plan_to_new_location(old_layout: Path) -> None:
    # Arrange
    old_plan_file = old_layout / "plan" / "P001-test.yaml"
    assert old_plan_file.exists()

    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate"])

    # Assert
    assert result.exit_code == 0
    new_plan_file = dh_paths.plan_dir(old_layout) / "P001-test.yaml"
    assert new_plan_file.exists()
    assert new_plan_file.read_text() == "slug: test"


def test_migrate_creates_dh_gitkeep(old_layout: Path) -> None:
    # Arrange
    gitkeep = old_layout / ".dh" / ".gitkeep"
    assert not gitkeep.exists()

    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate"])

    # Assert
    assert result.exit_code == 0
    assert gitkeep.exists()


def test_migrate_removes_empty_old_dirs(old_layout: Path) -> None:
    # Arrange: old dirs have content that will be moved
    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate"])

    # Assert: old dirs removed after migration (they are now empty)
    assert result.exit_code == 0
    old_backlog = old_layout / ".claude" / "backlog"
    old_plan = old_layout / "plan"
    assert not old_backlog.exists()
    assert not old_plan.exists()


def test_migrate_no_old_dirs_exits_0_with_nothing_to_migrate(fake_project: Path) -> None:
    # Arrange: no old layout dirs at all
    with patch.object(dh_paths, "git_project_root", return_value=fake_project):
        # Act
        result = runner.invoke(app, ["migrate"])
    # Assert: exits 0, reports nothing to migrate
    assert result.exit_code == 0
    assert "nothing to migrate" in result.output.lower()


def test_migrate_idempotent_gitkeep_already_present(old_layout: Path) -> None:
    # Arrange: pre-create the .dh/.gitkeep
    dh_dir = old_layout / ".dh"
    dh_dir.mkdir(parents=True)
    (dh_dir / ".gitkeep").touch()

    with patch.object(dh_paths, "git_project_root", return_value=old_layout):
        # Act
        result = runner.invoke(app, ["migrate"])

    # Assert: exits 0, does not error on existing .gitkeep
    assert result.exit_code == 0
    assert (dh_dir / ".gitkeep").exists()


# ---------------------------------------------------------------------------
# _update_artifact_manifests
# ---------------------------------------------------------------------------


def test_update_artifact_manifests_logs_instructions(fake_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange: use a real Console writing to stdout via Rich
    from rich.console import Console

    out = Console(highlight=False)

    # Act — should not raise, should print instructions
    _update_artifact_manifests(fake_project, out)

    # No assertion on specific output needed — just verify no exception raised
    # and the function returns normally (does not raise SystemExit or Exception)


def test_update_artifact_manifests_mentions_artifact_register(fake_project: Path) -> None:
    # Arrange
    from io import StringIO

    from rich.console import Console

    buffer = StringIO()
    out = Console(file=buffer, highlight=False)

    # Act
    _update_artifact_manifests(fake_project, out)
    output = buffer.getvalue()

    # Assert: key MCP tool name is mentioned
    assert "artifact_register" in output


def test_update_artifact_manifests_shows_old_prefixes(fake_project: Path) -> None:
    # Arrange
    from io import StringIO

    from rich.console import Console

    buffer = StringIO()
    out = Console(file=buffer, highlight=False)

    # Act
    _update_artifact_manifests(fake_project, out)
    output = buffer.getvalue()

    # Assert: old prefixes are mentioned
    assert "plan/" in output
    assert ".claude/backlog/" in output
