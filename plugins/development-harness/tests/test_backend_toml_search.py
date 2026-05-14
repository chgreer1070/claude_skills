"""Tests — .dh/ backend TOML search path additions.

Verifies that _load_backend_toml_name() in both backlog_core.backend_protocol
and sam_schema.core.task_config discovers backend TOML files placed in
{project_root}/.dh/ as expected after T05 and T06.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from unittest.mock import MagicMock

import backlog_core.backend_protocol as _bp
import pytest
import sam_schema.core.task_config as _tc
import tomlkit

if TYPE_CHECKING:
    from pathlib import Path


class _BackendSearchModule(Protocol):
    """Protocol matching both backlog_core.backend_protocol and sam_schema.core.task_config."""

    _dh_paths: object

    def _load_backend_toml_name(self) -> str | None: ...


def _write_toml(path: Path, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomlkit.dumps({"backend": {"name": name}}), encoding="utf-8")


def _make_dh_paths_mock(project_root: Path) -> MagicMock:
    mock = MagicMock()
    mock.git_project_root.return_value = project_root
    return mock


_BOTH_SIDES = pytest.mark.parametrize(
    ("module", "filename", "expected_name"),
    [
        pytest.param(_bp, "backend.toml", "local", id="backlog_core"),
        pytest.param(_tc, "taskbackend.toml", "memory", id="sam_schema"),
    ],
)

_BOTH_SIDES_ORDERING = pytest.mark.parametrize(
    ("module", "filename"),
    [pytest.param(_bp, "backend.toml", id="backlog_core"), pytest.param(_tc, "taskbackend.toml", id="sam_schema")],
)


@_BOTH_SIDES
def test_dh_subdir_discovered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: _BackendSearchModule, filename: str, expected_name: str
) -> None:
    """Backend name from {project_root}/.dh/<filename> is returned when no project-root entry exists."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_toml(project_root / ".dh" / filename, expected_name)
    monkeypatch.setenv("HOME", str(tmp_path / "fakehome"))
    monkeypatch.setattr(module, "_dh_paths", _make_dh_paths_mock(project_root))
    assert module._load_backend_toml_name() == expected_name


@_BOTH_SIDES_ORDERING
def test_project_root_wins_over_dh_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: _BackendSearchModule, filename: str
) -> None:
    """project_root/<filename> takes precedence over project_root/.dh/<filename>."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_toml(project_root / filename, "winner")
    _write_toml(project_root / ".dh" / filename, "loser")
    monkeypatch.setenv("HOME", str(tmp_path / "fakehome"))
    monkeypatch.setattr(module, "_dh_paths", _make_dh_paths_mock(project_root))
    assert module._load_backend_toml_name() == "winner"


@_BOTH_SIDES
def test_only_dh_subdir_present_is_picked_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: _BackendSearchModule, filename: str, expected_name: str
) -> None:
    """Only .dh/<filename> exists — new search-path entry is reachable."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_toml(project_root / ".dh" / filename, expected_name)
    monkeypatch.setenv("HOME", str(tmp_path / "fakehome"))
    monkeypatch.setattr(module, "_dh_paths", _make_dh_paths_mock(project_root))
    assert module._load_backend_toml_name() == expected_name


@_BOTH_SIDES_ORDERING
def test_returns_none_when_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: _BackendSearchModule, filename: str
) -> None:
    """Returns None when no backend TOML files exist in any search path."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "fakehome"))
    monkeypatch.setattr(module, "_dh_paths", _make_dh_paths_mock(project_root))
    assert module._load_backend_toml_name() is None
