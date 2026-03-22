"""Unit tests for dh_paths module.

Tests cover:
- compute_slug(): slug format for various path inputs
- git_project_root(): subprocess mock for main repo and worktree scenarios
- All *_dir() functions: correct absolute paths given a known project_root
- ensure_dirs(): idempotent directory creation
- DH_STATE_HOME override: env var changes base directory
- Cache behaviour: repeated calls with same cwd return cached results
- LEGACY_PATH_MAP: expected keys present
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import dh_paths
import pytest
from dh_paths import (
    LEGACY_PATH_MAP,
    backlog_dir,
    compute_slug,
    context_dir,
    ensure_dirs,
    git_project_root,
    milestones_dir,
    plan_dir,
    project_dh_dir,
    reports_dir,
    research_dir,
    state_root,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_git_run_mock(common_dir: Path):
    """Return a mock for subprocess.run that simulates git rev-parse output."""

    def _side_effect(args, **kwargs):
        result = MagicMock()
        result.stdout = str(common_dir) + "\n"
        result.returncode = 0
        return result

    return _side_effect


# ---------------------------------------------------------------------------
# compute_slug
# ---------------------------------------------------------------------------


class TestComputeSlug:
    def test_compute_slug_simple_path_returns_dash_prefixed_slug(self):
        # Arrange
        path = Path("/home/user/repos/project")

        # Act
        slug = compute_slug(path)

        # Assert
        assert slug == "-home-user-repos-project"

    def test_compute_slug_nested_path_replaces_all_slashes(self):
        # Arrange
        path = Path("/home/ubuntulinuxqa2/repos/claude_skills")

        # Act
        slug = compute_slug(path)

        # Assert
        assert slug == "-home-ubuntulinuxqa2-repos-claude_skills"

    def test_compute_slug_path_with_underscores_preserves_underscores(self):
        # Arrange
        path = Path("/home/user/my_project")

        # Act
        slug = compute_slug(path)

        # Assert
        assert slug == "-home-user-my_project"

    def test_compute_slug_short_path_produces_minimal_slug(self):
        # Arrange
        path = Path("/project")

        # Act
        slug = compute_slug(path)

        # Assert
        assert slug == "-project"

    def test_compute_slug_leading_dash_is_always_present(self):
        # Arrange
        path = Path("/anything")

        # Act
        slug = compute_slug(path)

        # Assert
        assert slug.startswith("-")

    def test_compute_slug_no_forward_slashes_in_result(self):
        # Arrange
        path = Path("/home/user/deep/nested/directory/structure")

        # Act
        slug = compute_slug(path)

        # Assert
        assert "/" not in slug


# ---------------------------------------------------------------------------
# git_project_root
# ---------------------------------------------------------------------------


class TestGitProjectRoot:
    def setup_method(self):
        # Clear the module-level cache before each test to avoid interference.
        dh_paths._root_cache.clear()

    def test_git_project_root_main_repo_returns_parent_of_git_dir(self, tmp_path):
        # Arrange
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            # Act
            result = git_project_root(cwd=tmp_path)

        # Assert
        assert result == tmp_path

    def test_git_project_root_worktree_returns_common_dir_parent(self, tmp_path):
        # Arrange — simulate a linked worktree where common dir is in the main repo
        main_repo = tmp_path / "main-repo"
        main_repo.mkdir()
        common_git_dir = main_repo / ".git"
        common_git_dir.mkdir()
        worktree_dir = tmp_path / "worktree"
        worktree_dir.mkdir()

        with patch("subprocess.run", side_effect=_make_git_run_mock(common_git_dir)):
            # Act
            result = git_project_root(cwd=worktree_dir)

        # Assert — slug resolves to the main repo root, not the worktree root
        assert result == main_repo

    def test_git_project_root_not_a_git_repo_raises_called_process_error(self, tmp_path):
        # Arrange
        def _fail(*args, **kwargs):
            raise subprocess.CalledProcessError(128, "git")

        with patch("subprocess.run", side_effect=_fail), pytest.raises(subprocess.CalledProcessError):
            # Act / Assert
            git_project_root(cwd=tmp_path)

    def test_git_project_root_uses_list_args_not_shell(self, tmp_path):
        # Arrange
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        captured: list[list[str]] = []

        def _capture(args, **kwargs):
            captured.append(args)
            m = MagicMock()
            m.stdout = str(fake_git_dir) + "\n"
            return m

        with patch("subprocess.run", side_effect=_capture):
            git_project_root(cwd=tmp_path)

        # Assert — args is a list (no shell=True path)
        assert isinstance(captured[0], list)
        assert captured[0][0] == "git"
        assert "--git-common-dir" in captured[0]

    def test_git_project_root_caches_result_for_same_cwd(self, tmp_path):
        # Arrange
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        call_count = {"n": 0}

        def _counting_mock(args, **kwargs):
            call_count["n"] += 1
            m = MagicMock()
            m.stdout = str(fake_git_dir) + "\n"
            return m

        with patch("subprocess.run", side_effect=_counting_mock):
            git_project_root(cwd=tmp_path)
            git_project_root(cwd=tmp_path)

        # Assert — subprocess only called once; second call uses cache
        assert call_count["n"] == 1

    def test_git_project_root_different_cwds_each_resolved_independently(self, tmp_path):
        # Arrange
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        git_a = dir_a / ".git"
        git_b = dir_b / ".git"
        git_a.mkdir()
        git_b.mkdir()
        call_count = {"n": 0}

        def _tracking(args, **kwargs):
            call_count["n"] += 1
            cwd_used = str(kwargs.get("cwd", ""))
            git_dir = git_a if "dir_a" in cwd_used or str(dir_a) in cwd_used else git_b
            m = MagicMock()
            m.stdout = str(git_dir) + "\n"
            return m

        with patch("subprocess.run", side_effect=_tracking):
            result_a = git_project_root(cwd=dir_a)
            result_b = git_project_root(cwd=dir_b)

        # Assert — two distinct roots resolved
        assert result_a != result_b
        assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# Path functions — given an explicit project_root
# ---------------------------------------------------------------------------


class TestPathFunctions:
    """Verify each *_dir() function returns the expected subpath.

    All tests pass an explicit project_root to avoid subprocess calls.
    """

    def test_project_dh_dir_returns_dh_under_project_root(self, tmp_path):
        result = project_dh_dir(project_root=tmp_path)
        assert result == tmp_path / ".dh"

    def test_state_root_returns_path_under_dh_user_root_with_slug(self, tmp_path, monkeypatch):
        # Arrange
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        # Act
        result = state_root(project_root=project)

        # Assert
        expected_slug = compute_slug(project)
        assert result == tmp_path / "dh" / "projects" / expected_slug

    def test_backlog_dir_returns_backlog_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = backlog_dir(project_root=project)

        assert result == state_root(project_root=project) / "backlog"

    def test_plan_dir_returns_plan_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = plan_dir(project_root=project)

        assert result == state_root(project_root=project) / "plan"

    def test_milestones_dir_returns_milestones_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = milestones_dir(project_root=project)

        assert result == state_root(project_root=project) / "milestones"

    def test_research_dir_returns_research_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = research_dir(project_root=project)

        assert result == state_root(project_root=project) / "research"

    def test_context_dir_returns_context_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = context_dir(project_root=project)

        assert result == state_root(project_root=project) / "context"

    def test_reports_dir_returns_reports_under_state_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        result = reports_dir(project_root=project)

        assert result == state_root(project_root=project) / "reports"

    def test_all_dir_functions_return_absolute_paths(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))
        project = Path("/home/user/repo")

        for fn in (backlog_dir, plan_dir, milestones_dir, research_dir, context_dir, reports_dir):
            result = fn(project_root=project)
            assert result.is_absolute(), f"{fn.__name__} returned non-absolute path: {result}"


# ---------------------------------------------------------------------------
# DH_STATE_HOME environment variable override
# ---------------------------------------------------------------------------


class TestDHStateHomeOverride:
    def test_state_root_uses_dh_state_home_when_set(self, tmp_path, monkeypatch):
        # Arrange
        custom_home = tmp_path / "custom-dh"
        monkeypatch.setenv("DH_STATE_HOME", str(custom_home))
        project = Path("/home/user/project")

        # Act
        result = state_root(project_root=project)

        # Assert — base is custom_home, not ~/.dh
        assert str(result).startswith(str(custom_home))

    def test_state_root_uses_home_dh_when_dh_state_home_not_set(self, tmp_path, monkeypatch):
        # Arrange
        monkeypatch.delenv("DH_STATE_HOME", raising=False)
        project = Path("/home/user/project")

        # Act
        result = state_root(project_root=project)

        # Assert — base is ~/.dh
        assert str(result).startswith(str(Path.home() / ".dh"))

    def test_backlog_dir_respects_dh_state_home_override(self, tmp_path, monkeypatch):
        # Arrange
        custom_home = tmp_path / "env-override"
        monkeypatch.setenv("DH_STATE_HOME", str(custom_home))
        project = Path("/home/user/project")

        # Act
        result = backlog_dir(project_root=project)

        # Assert
        assert str(result).startswith(str(custom_home))
        assert result.name == "backlog"

    def test_plan_dir_respects_dh_state_home_override(self, tmp_path, monkeypatch):
        # Arrange
        custom_home = tmp_path / "env-override"
        monkeypatch.setenv("DH_STATE_HOME", str(custom_home))
        project = Path("/home/user/project")

        # Act
        result = plan_dir(project_root=project)

        # Assert
        assert str(result).startswith(str(custom_home))
        assert result.name == "plan"

    def test_context_dir_respects_dh_state_home_override(self, tmp_path, monkeypatch):
        # Arrange
        custom_home = tmp_path / "env-override"
        monkeypatch.setenv("DH_STATE_HOME", str(custom_home))
        project = Path("/home/user/project")

        # Act
        result = context_dir(project_root=project)

        # Assert
        assert str(result).startswith(str(custom_home))
        assert result.name == "context"

    def test_two_different_env_values_produce_different_roots(self, tmp_path, monkeypatch):
        # Arrange
        project = Path("/home/user/project")

        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "home-a"))
        root_a = state_root(project_root=project)

        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "home-b"))
        root_b = state_root(project_root=project)

        # Assert
        assert root_a != root_b


# ---------------------------------------------------------------------------
# ensure_dirs
# ---------------------------------------------------------------------------


class TestEnsureDirs:
    def test_ensure_dirs_creates_all_expected_directories(self, tmp_path, monkeypatch):
        # Arrange
        dh_paths._root_cache.clear()
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            # Act
            returned = ensure_dirs(project_root=tmp_path)

        # Assert — all tier-2 and tier-3 dirs exist
        expected_dirs = [
            returned / "backlog",
            returned / "plan",
            returned / "plan" / "codebase",
            returned / "milestones",
            returned / "research",
            returned / "context",
            returned / "reports",
        ]
        for d in expected_dirs:
            assert d.is_dir(), f"Expected directory not created: {d}"

    def test_ensure_dirs_creates_tier1_dh_dir_with_gitkeep(self, tmp_path, monkeypatch):
        # Arrange
        dh_paths._root_cache.clear()
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            ensure_dirs(project_root=tmp_path)

        # Assert
        assert (tmp_path / ".dh").is_dir()
        assert (tmp_path / ".dh" / ".gitkeep").exists()

    def test_ensure_dirs_is_idempotent_called_twice_no_error(self, tmp_path, monkeypatch):
        # Arrange
        dh_paths._root_cache.clear()
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            # Act — calling twice must not raise
            ensure_dirs(project_root=tmp_path)
            ensure_dirs(project_root=tmp_path)

        # Assert — directories still exist
        assert (tmp_path / ".dh").is_dir()

    def test_ensure_dirs_returns_state_root_path(self, tmp_path, monkeypatch):
        # Arrange
        dh_paths._root_cache.clear()
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            # Act
            result = ensure_dirs(project_root=tmp_path)

        # Assert — returned path matches state_root()
        expected = state_root(project_root=tmp_path)
        assert result == expected

    def test_ensure_dirs_does_not_delete_existing_files(self, tmp_path, monkeypatch):
        # Arrange
        dh_paths._root_cache.clear()
        fake_git_dir = tmp_path / ".git"
        fake_git_dir.mkdir()
        monkeypatch.setenv("DH_STATE_HOME", str(tmp_path / "dh"))

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            state = ensure_dirs(project_root=tmp_path)

        sentinel = state / "backlog" / "sentinel.txt"
        sentinel.write_text("keep me")

        with patch("subprocess.run", side_effect=_make_git_run_mock(fake_git_dir)):
            ensure_dirs(project_root=tmp_path)

        # Assert — sentinel file untouched
        assert sentinel.exists()
        assert sentinel.read_text() == "keep me"


# ---------------------------------------------------------------------------
# LEGACY_PATH_MAP
# ---------------------------------------------------------------------------


class TestLegacyPathMap:
    def test_legacy_path_map_contains_backlog_key(self):
        assert ".claude/backlog" in LEGACY_PATH_MAP

    def test_legacy_path_map_contains_plan_key(self):
        assert "plan" in LEGACY_PATH_MAP

    def test_legacy_path_map_contains_context_key(self):
        assert ".claude/context" in LEGACY_PATH_MAP

    def test_legacy_path_map_contains_reports_key(self):
        assert ".claude/reports" in LEGACY_PATH_MAP

    def test_legacy_path_map_backlog_maps_to_backlog_dir(self):
        assert LEGACY_PATH_MAP[".claude/backlog"] == "backlog_dir"

    def test_legacy_path_map_plan_maps_to_plan_dir(self):
        assert LEGACY_PATH_MAP["plan"] == "plan_dir"

    def test_legacy_path_map_context_maps_to_context_dir(self):
        assert LEGACY_PATH_MAP[".claude/context"] == "context_dir"

    def test_legacy_path_map_reports_maps_to_reports_dir(self):
        assert LEGACY_PATH_MAP[".claude/reports"] == "reports_dir"

    def test_legacy_path_map_all_values_are_callable_function_names(self):
        for value in LEGACY_PATH_MAP.values():
            assert hasattr(dh_paths, value), f"dh_paths has no attribute '{value}'"
            assert callable(getattr(dh_paths, value)), f"dh_paths.{value} is not callable"
