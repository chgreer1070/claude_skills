"""ContextBackend Protocol — implementation-agnostic abstraction for session context storage.

This module defines the ContextBackend Protocol. All backend implementations
(LocalContextBackend, GitHubContextBackend, InMemoryContextBackend) must satisfy
this Protocol. The MCP server depends on this interface; storage-specific
implementations live in ``sam_schema.core.backends``.

All protocol methods are synchronous. The MCP layer wraps calls in
``asyncio.to_thread()`` when needed — matching the pattern established in
``task_backend.py`` and ``backlog_core.backend_protocol``.

Dependency direction (must remain acyclic):
    context_backend imports from: models (TYPE_CHECKING only)
    context_backend is imported by: context_config, server
    context_backend does NOT import from: backends, server, context_config
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Protocol, runtime_checkable

if TYPE_CHECKING:
    from sam_schema.core.models import ActiveTaskContext

__all__ = ["ContextBackend"]


@runtime_checkable
class ContextBackend(Protocol):
    """Protocol defining the backend contract for session-to-task context storage.

    All methods are synchronous. The MCP layer wraps calls in
    ``asyncio.to_thread()`` when needed.

    Method groups:
    - **Active task**: get_active_task, set_active_task, clear_active_task, list_active_tasks
    """

    def get_active_task(self, session_id: str) -> ActiveTaskContext | None:
        """Retrieve the active task context for a session.

        Args:
            session_id: Claude Code session identifier. Used as file/dict key.

        Returns:
            ActiveTaskContext if a context exists for this session, otherwise None.
        """
        ...

    def set_active_task(
        self, session_id: str, plan: str, task: str, plan_dir: str, parent_issue_number: str | int | None = None
    ) -> ActiveTaskContext:
        """Store the active task context for a session.

        Args:
            session_id: Claude Code session identifier.
            plan: Plan address (e.g., 'P1' or slug).
            task: Task ID within the plan (e.g., 'T3').
            plan_dir: Plan directory path sentinel or absolute path.
            parent_issue_number: Optional GitHub issue number for the parent story.

        Returns:
            The stored ActiveTaskContext instance.
        """
        ...

    def clear_active_task(self, session_id: str) -> bool:
        """Remove the active task context for a session.

        Args:
            session_id: Claude Code session identifier.

        Returns:
            True if context existed and was removed, False if no context found.
        """
        ...

    def list_active_tasks(self) -> list[ActiveTaskContext]:
        """Return all stored active task contexts.

        Returns:
            List of all ActiveTaskContext instances currently stored.
        """
        ...
