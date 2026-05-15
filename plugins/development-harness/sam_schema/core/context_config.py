"""ContextConfig — dependency injection container for the active ContextBackend.

Provides the module-level singleton pattern (get_context_config / set_context_config /
reset_context_config) and the factory function create_context_backend, following the
pattern established in task_config.py.

Resolution order for backend selection:
    1. ``CONTEXTBACKEND`` environment variable
    2. ``[backend] name`` in ``contextbackend.toml`` (project root or ``~/.dh/``)
    3. Default: ``"local"``
"""

from __future__ import annotations

import contextlib
import importlib
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

    from sam_schema.core.context_backend import ContextBackend

_dh_paths: types.ModuleType | None = None
with contextlib.suppress(ImportError):
    import dh_paths as _dh_paths  # optional — only present inside the plugin

__all__ = [
    "ContextConfig",
    "create_context_backend",
    "get_context_config",
    "reset_context_config",
    "set_context_config",
]

_VALID_BACKENDS: tuple[str, ...] = ("beads", "local", "github", "memory")
_BACKEND_TOML_FILENAME = "contextbackend.toml"


# ---------------------------------------------------------------------------
# ContextConfig dataclass
# ---------------------------------------------------------------------------


@dataclass
class ContextConfig:
    """Container for the active ContextBackend instance.

    This dataclass replaces direct imports from server.py in the MCP server.
    Pass a ContextConfig to server tools so they can work against any conforming
    backend implementation.

    Attributes:
        backend: The active ContextBackend implementation.
    """

    backend: ContextBackend


# ---------------------------------------------------------------------------
# Module-level config accessor
# ---------------------------------------------------------------------------

_active_config: ContextConfig | None = None


def get_context_config() -> ContextConfig:
    """Return the active ContextConfig.

    Unlike backlog_core which auto-initialises, this function requires
    an explicit :func:`set_context_config` call first. This prevents the server
    module from silently falling back to a default backend when misconfigured.

    Returns:
        The active ContextConfig instance.

    Raises:
        RuntimeError: When no config has been set via :func:`set_context_config`.
    """
    if _active_config is None:
        msg = "ContextConfig not set. Call set_context_config() first."
        raise RuntimeError(msg)
    return _active_config


def set_context_config(config: ContextConfig) -> None:
    """Register the active ContextConfig.

    Args:
        config: ContextConfig instance wrapping the chosen backend implementation.
    """
    global _active_config  # noqa: PLW0603
    _active_config = config


def reset_context_config() -> None:
    """Clear the cached ContextConfig singleton.

    Intended for test teardown — call this between tests to force the next
    ``get_context_config()`` call to raise rather than returning a stale config.
    """
    global _active_config  # noqa: PLW0603
    _active_config = None


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------


def _load_backend_toml_name() -> str | None:
    """Read backend name from contextbackend.toml if present.

    Searches the project root (via dh_paths) then ``~/.dh/``. Missing files
    are silently ignored. A present file that lacks the ``backend.name`` key
    is also ignored.

    Returns:
        Backend name string from ``[backend] name = "..."`` if found,
        otherwise ``None``.
    """
    search_paths: list[Path] = []

    if _dh_paths is not None:
        with contextlib.suppress(FileNotFoundError, RuntimeError):
            project_root = _dh_paths.git_project_root()
            search_paths.append(project_root / _BACKEND_TOML_FILENAME)

    search_paths.append(Path.home() / ".dh" / _BACKEND_TOML_FILENAME)

    for candidate in search_paths:
        if candidate.is_file():
            try:
                data = tomllib.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError):
                continue
            name = data.get("backend", {}).get("name")
            if isinstance(name, str) and name:
                return name

    return None


def create_context_backend(name: str | None = None) -> ContextBackend:
    """Instantiate and return a ContextBackend by name.

    Resolution order when *name* is ``None``:

    1. ``CONTEXTBACKEND`` environment variable.
    2. ``[backend] name`` in ``contextbackend.toml`` (project root or ``~/.dh/``).
    3. Default: ``"local"``.

    Args:
        name: Backend identifier to instantiate. Pass ``None`` to trigger
            automatic resolution.

    Returns:
        Configured ContextBackend instance.

    Raises:
        ValueError: When *name* (or the resolved name) is not a recognised
            backend identifier. The message lists all valid options.
        NotImplementedError: When the resolved name is ``"github"`` (pending T02
            GitHubContextBackend implementation).
    """
    resolved = name or os.environ.get("CONTEXTBACKEND") or _load_backend_toml_name() or "local"

    if resolved == "local":
        mod = importlib.import_module("sam_schema.core.backends.local_context_backend")
        return mod.LocalContextBackend()  # type: ignore[return-value]

    if resolved == "memory":
        mod = importlib.import_module("sam_schema.core.backends.memory_context_backend")
        return mod.InMemoryContextBackend()  # type: ignore[return-value]

    if resolved == "beads":
        # importlib.import_module defers resolution to runtime: avoids circular imports
        # and handles the case where the beads backend module is created in T08.
        mod = importlib.import_module("sam_schema.core.backends.beads")
        return mod.BeadsContextBackend()  # type: ignore[return-value]

    if resolved == "github":
        msg = "GitHub context backend is implemented in T02. Use 'local' or 'memory' instead."
        raise NotImplementedError(msg)

    msg = f"Unknown backend {resolved!r}. Valid options: {', '.join(sorted(_VALID_BACKENDS))}"
    raise ValueError(msg)
