"""Integration tests for lazy migration backend detection.

Tests verify the resolution order for ``create_task_backend()``:

    TASKBACKEND env var > taskbackend.toml > default "local"

And verify that ``create_task_backend(name=...)`` routes correctly to the
appropriate backend, simulating what backend_ref detection in a plan YAML
would produce.

No asyncio — all tests are synchronous. asyncio_mode = "auto" in pyproject.toml.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import sam_schema.core.task_config as task_config_module
from sam_schema.core.backends.local_yaml import LocalYamlTaskProvider
from sam_schema.core.backends.memory import InMemoryTaskProvider
from sam_schema.core.task_config import create_task_backend, reset_task_config

if TYPE_CHECKING:
    from collections.abc import Generator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_config() -> Generator[None, None, None]:
    """Clear _active_config before and after each test.

    Ensures that the module-level TaskConfig singleton does not leak between
    tests. reset_task_config() sets _active_config = None so the next
    get_task_config() call raises RuntimeError rather than returning a stale
    config from a previous test.

    Yields:
        None (setup/teardown only).
    """
    reset_task_config()
    yield
    reset_task_config()


# ---------------------------------------------------------------------------
# TestLazyMigration
# ---------------------------------------------------------------------------


class TestLazyMigration:
    """Tests for backend_ref detection and migration routing."""

    def test_plan_without_backend_ref_uses_local(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan YAML without backend_ref routes through LocalYamlTaskProvider.

        When no TASKBACKEND env var is set and no taskbackend.toml is found,
        create_task_backend() returns the default LocalYamlTaskProvider. This is
        the "plan without backend_ref" path — the plan has not been migrated to a
        remote backend.

        Arrange: clear TASKBACKEND env var; mock toml loader to return None.
        Act: call create_task_backend() with no arguments.
        Assert: returned backend is a LocalYamlTaskProvider instance.
        """
        # Arrange
        monkeypatch.delenv("TASKBACKEND", raising=False)
        monkeypatch.setattr(task_config_module, "_load_backend_toml_name", lambda: None)

        # Act
        backend = create_task_backend()

        # Assert
        assert isinstance(backend, LocalYamlTaskProvider)

    def test_plan_with_backend_ref_routes_to_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan YAML with backend_ref field routes through the specified backend.

        When a plan YAML contains backend_ref (e.g., ``"memory://..."``), the
        detection logic extracts the backend name and calls
        ``create_task_backend(name)``.  This test verifies that passing
        ``name="memory"`` — as backend_ref detection would do — returns an
        InMemoryTaskProvider instead of the default local backend.

        Arrange: clear TASKBACKEND env var; mock toml loader to return None.
        Act: call create_task_backend(name="memory").
        Assert: returned backend is an InMemoryTaskProvider instance.
        """
        # Arrange
        monkeypatch.delenv("TASKBACKEND", raising=False)
        monkeypatch.setattr(task_config_module, "_load_backend_toml_name", lambda: None)

        # Act — simulates backend_ref detection resolving to "memory"
        backend = create_task_backend(name="memory")

        # Assert
        assert isinstance(backend, InMemoryTaskProvider)

    def test_taskbackend_toml_overrides_default(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """taskbackend.toml in project root selects the backend.

        When ``taskbackend.toml`` is present at the project root (resolved via
        ``dh_paths.git_project_root()``), its ``[backend] name`` overrides the
        default ``"local"`` backend.  The factory reads the TOML and instantiates
        the configured backend.

        Arrange: write taskbackend.toml with name="memory" to tmp_path;
                 mock dh_paths.git_project_root() to return tmp_path;
                 redirect Path.home() to an empty directory (no ~/.dh/ toml);
                 clear TASKBACKEND env var.
        Act: call create_task_backend() with no arguments.
        Assert: returned backend is InMemoryTaskProvider.
        """
        # Arrange — write TOML to the mocked project root
        (tmp_path / "taskbackend.toml").write_text('[backend]\nname = "memory"\n', encoding="utf-8")

        monkeypatch.delenv("TASKBACKEND", raising=False)

        mock_dh = MagicMock()
        mock_dh.git_project_root.return_value = tmp_path
        monkeypatch.setattr(task_config_module, "_dh_paths", mock_dh)

        # Redirect Path.home() so ~/.dh/taskbackend.toml is never found,
        # ensuring only the project-root TOML influences the result.
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Act
        backend = create_task_backend()

        # Assert
        assert isinstance(backend, InMemoryTaskProvider)

    def test_env_var_overrides_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """TASKBACKEND env var takes precedence over taskbackend.toml.

        When ``TASKBACKEND="memory"`` is set and ``taskbackend.toml`` declares
        ``name="local"``, the env var wins.  Resolution order:
        env var > taskbackend.toml > default ``"local"``.

        Arrange: write taskbackend.toml with name="local" to tmp_path;
                 set TASKBACKEND="memory" via monkeypatch;
                 mock dh_paths.git_project_root() to return tmp_path;
                 redirect Path.home() to an empty directory.
        Act: call create_task_backend() with no arguments.
        Assert: returned backend is InMemoryTaskProvider (env var wins over toml).
        """
        # Arrange — toml says "local", env var says "memory"
        (tmp_path / "taskbackend.toml").write_text('[backend]\nname = "local"\n', encoding="utf-8")

        monkeypatch.setenv("TASKBACKEND", "memory")

        mock_dh = MagicMock()
        mock_dh.git_project_root.return_value = tmp_path
        monkeypatch.setattr(task_config_module, "_dh_paths", mock_dh)

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Act
        backend = create_task_backend()

        # Assert — TASKBACKEND env var overrides taskbackend.toml
        assert isinstance(backend, InMemoryTaskProvider)

    def test_mixed_plans_different_backends(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Plans in the same directory can use different backends via backend_ref.

        When a project has plans at different migration stages, each plan routes
        through the backend indicated by its backend_ref field.  Plans without
        backend_ref use the local default; plans with a backend_ref (e.g.
        ``"memory://..."``) route to the named backend.

        Arrange: clear TASKBACKEND env var; mock toml loader to return None.
        Act: call create_task_backend() without a name (plan without backend_ref)
             and create_task_backend("memory") (plan with backend_ref).
        Assert: first call returns LocalYamlTaskProvider;
                second call returns InMemoryTaskProvider;
                the two instances are distinct objects.
        """
        # Arrange
        monkeypatch.delenv("TASKBACKEND", raising=False)
        monkeypatch.setattr(task_config_module, "_load_backend_toml_name", lambda: None)

        # Act — two plans in the same directory routed to different backends
        local_backend = create_task_backend()  # plan without backend_ref → default local
        memory_backend = create_task_backend(name="memory")  # plan with backend_ref → memory

        # Assert — each plan gets the correct backend
        assert isinstance(local_backend, LocalYamlTaskProvider)
        assert isinstance(memory_backend, InMemoryTaskProvider)
        assert local_backend is not memory_backend
