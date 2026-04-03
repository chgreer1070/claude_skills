"""Task format detection and field resolution utilities.

Provides helpers for detecting YAML frontmatter format and resolving
backward-compatible task ID field names.
"""

from __future__ import annotations

from typing import Any

_FRONTMATTER_DELIMITER = "---\n"


def has_yaml_frontmatter(content: str) -> bool:
    r"""Return True if content begins with a valid YAML frontmatter block.

    A valid frontmatter block starts with ``---\\n`` on line 1 and has a
    matching closing ``---\\n`` delimiter.  Content that starts with a fenced
    code block or has any characters before the first ``---`` is NOT
    considered frontmatter.

    Args:
        content: Raw file content to inspect.

    Returns:
        True if content has a valid opening and closing frontmatter delimiter,
        False otherwise.
    """
    if not content or not content.startswith(_FRONTMATTER_DELIMITER):
        return False
    closing_idx = content.find("\n---\n", len(_FRONTMATTER_DELIMITER))
    return closing_idx != -1


def resolve_task_id(fm: dict[str, Any]) -> str | None:
    """Resolve the task ID from a parsed YAML frontmatter dict.

    Supports both ``task:`` (preferred, newer format) and ``task_id:``
    (older format) field names for backward compatibility.

    Args:
        fm: Parsed YAML frontmatter as a plain dict.

    Returns:
        The task ID string if present, or None if neither key is set.
    """
    raw = fm.get("task") if "task" in fm else fm.get("task_id")
    return str(raw) if raw is not None else None
