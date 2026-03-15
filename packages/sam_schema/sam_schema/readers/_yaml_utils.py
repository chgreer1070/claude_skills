"""Shared YAML loading and coercion utilities for SAM readers.

All readers that use ruamel.yaml import from here to avoid copy-pasting the
same YAML instance creation and CommentedMap coercion logic.
"""

from __future__ import annotations

from typing import Any

from ruamel.yaml import YAML


def make_yaml() -> YAML:
    """Create a ruamel.yaml instance in round-trip mode with ``preserve_quotes``.

    Reader modules use this factory to get a consistent YAML parser that
    preserves comments, field order, and string quoting style.

    Returns:
        Configured ``YAML`` instance ready for ``yaml.load()``.
    """
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    return yaml


def load_yaml(content: str) -> Any:  # noqa: ANN401
    """Parse YAML text using ruamel.yaml round-trip mode.

    Args:
        content: Raw YAML text to parse.

    Returns:
        Parsed YAML structure (dict or list).

    Raises:
        ValueError: If the content cannot be parsed as valid YAML.
    """
    yaml = make_yaml()
    try:
        return yaml.load(content)
    except Exception as exc:
        msg = f"Failed to parse YAML: {exc}"
        raise ValueError(msg) from exc


def coerce_to_plain(obj: Any) -> Any:  # noqa: ANN401
    """Recursively coerce ruamel.yaml comment-map/seq objects to plain Python types.

    ruamel.yaml round-trip mode returns ``CommentedMap`` and ``CommentedSeq``
    instead of plain ``dict``/``list``. Downstream normalizers work with plain
    Python types only.

    Args:
        obj: Any value from a ruamel.yaml parse result.

    Returns:
        Plain Python ``dict``, ``list``, or scalar (unchanged).
    """
    if hasattr(obj, "items"):  # dict-like (CommentedMap)
        return {str(k): coerce_to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [coerce_to_plain(item) for item in obj]
    return obj
