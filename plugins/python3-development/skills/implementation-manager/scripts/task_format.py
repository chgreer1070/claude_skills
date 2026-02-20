"""Shared YAML frontmatter utilities for task file parsing and manipulation.

Provides common functions for detecting, parsing, and updating YAML frontmatter
in task files. Used by both implementation_manager.py and task_status_hook.py.

Source references:
    - STATUS_MAP: migrate_task_format.py lines 59-71
    - normalize_status: migrate_task_format.py lines 74-109
    - TASK_ID_PATTERN: TASK_FILE_FORMAT.md line 272 (JSON schema)
    - VALID_STATUSES: TASK_FILE_FORMAT.md line 283
    - VALID_COMPLEXITIES: TASK_FILE_FORMAT.md line 310
"""

from __future__ import annotations

import re
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

_yaml = YAML(typ="safe")

# =============================================================================
# Constants
# =============================================================================

STATUS_MAP: dict[str, str] = {
    "NOT STARTED": "not-started",
    "IN PROGRESS": "in-progress",
    "COMPLETE": "complete",
    "BLOCKED": "blocked",
    # Emoji variations
    ":x:": "not-started",
    ":cross_mark:": "not-started",
    ":white_check_mark:": "complete",
    ":heavy_check_mark:": "complete",
    ":arrows_counterclockwise:": "in-progress",
    ":repeat:": "in-progress",
}

TASK_ID_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z]?\d+(\.\d+)?$")

VALID_STATUSES: frozenset[str] = frozenset({
    "not-started",
    "in-progress",
    "complete",
    "blocked",
})

VALID_COMPLEXITIES: frozenset[str] = frozenset({"low", "medium", "high"})

_FRONTMATTER_DELIMITER = "---\n"


# =============================================================================
# Frontmatter Detection and Parsing
# =============================================================================


def has_yaml_frontmatter(content: str) -> bool:
    """Detect if content uses YAML frontmatter format.

    Checks for opening ``---`` delimiter followed by YAML content and a
    closing ``---`` delimiter.

    Args:
        content: File content to check.

    Returns:
        True if content contains valid YAML frontmatter delimiters.
    """
    if not content or not content.startswith(_FRONTMATTER_DELIMITER):
        return False

    # Must have a closing delimiter after the opening one
    closing_idx = content.find("\n---\n", len(_FRONTMATTER_DELIMITER))
    if closing_idx == -1:
        # Check for closing delimiter at end of file (no trailing newline after ---)
        closing_idx = content.find("\n---", len(_FRONTMATTER_DELIMITER))
        if closing_idx == -1:
            return False
        remaining = content[closing_idx + len("\n---") :]
        if remaining and remaining != "\n":
            return False

    return True


def parse_yaml_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and markdown body from content.

    Splits content on ``---`` delimiters and parses the YAML section
    between them.

    Args:
        content: File content with YAML frontmatter.

    Returns:
        Tuple of (frontmatter_dict, body_content).

    Raises:
        ValueError: If frontmatter format is invalid or YAML parsing fails.
        TypeError: If parsed YAML is not a mapping.
    """
    parts = content.split("---\n", 2)
    if len(parts) < 3:  # noqa: PLR2004
        msg = (
            "Invalid frontmatter format: expected opening and closing '---' delimiters"
        )
        raise ValueError(msg)

    # parts[0] should be empty (content before first ---)
    if parts[0].strip():
        msg = "Invalid frontmatter format: content found before opening '---'"
        raise ValueError(msg)

    raw_yaml = parts[1]
    body = parts[2]

    try:
        parsed = _yaml.load(raw_yaml)
    except YAMLError as exc:
        msg = f"YAML parsing failed: {exc}"
        raise ValueError(msg) from exc
    if not isinstance(parsed, dict):
        msg = f"Frontmatter must be a YAML mapping, got {type(parsed).__name__}"
        raise TypeError(msg)

    frontmatter: dict[str, Any] = parsed
    return frontmatter, body


# =============================================================================
# Field Update
# =============================================================================


def update_yaml_field(content: str, field: str, value: str | int | list[str]) -> str:
    """Update a single field in YAML frontmatter without re-serializing.

    Uses regex-based line replacement to preserve YAML formatting, field
    ordering, and body content.

    Args:
        content: File content with YAML frontmatter.
        field: YAML field name to update or add.
        value: New value for the field.

    Returns:
        Updated content with the field changed or added.

    Raises:
        ValueError: If content does not contain valid YAML frontmatter.
    """
    if not has_yaml_frontmatter(content):
        msg = "Content does not contain YAML frontmatter"
        raise ValueError(msg)

    lines = content.split("\n")

    # Find frontmatter boundaries (line indices)
    open_idx: int | None = None
    close_idx: int | None = None

    for i, line in enumerate(lines):
        if line == "---":
            if open_idx is None:
                open_idx = i
            else:
                close_idx = i
                break

    if open_idx is None or close_idx is None:
        msg = "Could not locate frontmatter delimiters"
        raise ValueError(msg)

    formatted_value = _format_yaml_value(field, value)

    # Search for existing field within frontmatter
    field_pattern = re.compile(rf"^{re.escape(field)}\s*:")
    field_line_idx: int | None = None

    for i in range(open_idx + 1, close_idx):
        if field_pattern.match(lines[i]):
            field_line_idx = i
            break

    if field_line_idx is not None:
        # Replace existing field line (handle multi-line list values)
        end_of_field = field_line_idx + 1
        if isinstance(value, list):
            # Remove continuation lines (indented lines that are part of the list)
            while end_of_field < close_idx and lines[end_of_field].startswith("  - "):
                end_of_field += 1
        lines[field_line_idx:end_of_field] = [formatted_value]
    else:
        # Insert new field before closing ---
        lines.insert(close_idx, formatted_value)

    return "\n".join(lines)


def _format_yaml_value(field: str, value: str | int | list[str]) -> str:
    """Format a field-value pair as a YAML line.

    Args:
        field: YAML field name.
        value: Value to format.

    Returns:
        Formatted YAML line string.
    """
    match value:
        case list():
            if not value:
                return f"{field}: []"
            items = "\n".join(f"  - {item}" for item in value)
            return f"{field}:\n{items}"
        case int():
            return f"{field}: {value}"
        case str():
            # Quote strings that contain special YAML characters
            if any(ch in value for ch in (":", "#", "[", "]", "{", "}")):
                escaped = value.replace('"', '\\"')
                return f'{field}: "{escaped}"'
            return f"{field}: {value}"


# =============================================================================
# Status Normalization
# =============================================================================


def normalize_status(old_status: str) -> str:
    """Convert any old-format status string to the new hyphenated lowercase format.

    Strips emoji characters, checks against STATUS_MAP, and falls back to
    ``not-started`` for unrecognized values.

    Args:
        old_status: Status from old markdown format or emoji format.

    Returns:
        Normalized status in new format (one of VALID_STATUSES).
    """
    status_clean = old_status.strip()

    # Remove common Unicode emoji characters
    status_clean = (
        status_clean
        .replace("\u2705", "")  # check mark
        .replace("\u274c", "")  # cross mark
        .replace("\U0001f504", "")  # counterclockwise arrows
    )
    status_clean = status_clean.strip()

    status_upper = status_clean.upper()

    # Check for exact matches first
    if status_upper in STATUS_MAP:
        return STATUS_MAP[status_upper]

    # Check for emoji name patterns in original text
    status_lower = old_status.lower().strip()
    for pattern, new_status in STATUS_MAP.items():
        if pattern in status_lower:
            return new_status

    # Check if cleaned text matches after removing emojis
    for old_pattern, new_status in STATUS_MAP.items():
        if old_pattern.upper() in status_upper:
            return new_status

    # Default to not-started if unclear
    return "not-started"
