"""SAM exception hierarchy for TaskBackend operations.

All TaskBackend Protocol methods raise exceptions from this module.
These replace the broad exception tuples in server.py with semantically
meaningful, typed errors that callers can catch narrowly.
"""

from __future__ import annotations

__all__ = [
    "DocumentNotFoundError",
    "PlanExistsError",
    "PlanNotFoundError",
    "SamError",
    "TaskNotFoundError",
    "TaskValidationError",
]


class SamError(Exception):
    """Base exception for all SAM operations."""


class PlanNotFoundError(SamError):
    """Raised when a plan_id does not resolve to a known plan."""

    def __init__(self, plan_id: str) -> None:
        """Initialize with the plan ID that could not be found.

        Args:
            plan_id: The plan identifier that was not found.
        """
        self.plan_id = plan_id
        super().__init__(f"Plan not found: {plan_id}")


class PlanExistsError(SamError):
    """Raised when attempting to create a plan that already exists."""

    def __init__(self, plan_id: str) -> None:
        """Initialize with the duplicate plan ID.

        Args:
            plan_id: The plan identifier that already exists.
        """
        self.plan_id = plan_id
        super().__init__(f"Plan already exists: {plan_id}")


class TaskNotFoundError(SamError):
    """Raised when a task_id does not resolve within a known plan."""

    def __init__(self, plan_id: str, task_id: str) -> None:
        """Initialize with the plan and task identifiers.

        Args:
            plan_id: The plan the task was expected to belong to.
            task_id: The task identifier that was not found.
        """
        self.plan_id = plan_id
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id} in plan {plan_id}")


class TaskValidationError(SamError):
    """Raised when a task definition fails validation."""

    def __init__(self, task_index: int, detail: str) -> None:
        """Initialize with the index of the invalid task and a description.

        Args:
            task_index: Zero-based index of the task in the input list.
            detail: Human-readable description of the validation failure.
        """
        self.task_index = task_index
        self.detail = detail
        super().__init__(f"Task at index {task_index} failed validation: {detail}")


class DocumentNotFoundError(SamError):
    """Raised when a document content_ref cannot be resolved."""

    def __init__(self, content_ref: str) -> None:
        """Initialize with the opaque content reference that failed.

        Args:
            content_ref: The backend-specific reference string that was not found.
        """
        self.content_ref = content_ref
        super().__init__(f"Document not found: {content_ref}")
