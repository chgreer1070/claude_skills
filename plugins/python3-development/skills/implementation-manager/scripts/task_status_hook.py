#!/usr/bin/env python3
"""Task Status Hook - Update task status and timestamps automatically.

This hook script handles multiple hook events:
- SubagentStop: Parse prompt for task info, set status to COMPLETE, add Completed timestamp
- PostToolUse (Write|Edit|Bash): Update LastActivity timestamp using context file

Supports two task file formats:
- YAML frontmatter: Detected via ``---`` delimiters, updated with update_yaml_field()
- Legacy markdown: ``**Status**: value`` lines updated via regex

Context File Mechanism:
- The /start-task command writes task context to .claude/context/active-task-{session_id}.json
- PostToolUse hooks read from this file to know which task is active
- SubagentStop parses the prompt directly (doesn't need context file)

Usage:
    Called automatically via hooks configuration.
    Receives JSON via stdin with hook context.

Exit Codes:
    0: Success
    2: Error (stderr message shown to Claude)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_format import (
    has_yaml_frontmatter,
    normalize_status,
    parse_yaml_frontmatter,
    update_yaml_field,
)

# Alphanumeric task ID pattern: "1", "1.1", "T1", "P0-T01", etc.
_TASK_ID_RE = r"[A-Za-z0-9]+(?:[-.][\dA-Za-z]+)*"


def parse_hook_input() -> dict[str, Any]:
    """Parse JSON input from stdin.

    Returns:
        Dictionary with hook input data.

    Raises:
        ValueError: If stdin is empty or invalid JSON.
    """
    stdin_data = sys.stdin.read()
    if not stdin_data.strip():
        raise ValueError("No input received on stdin")

    result: dict[str, Any] = json.loads(stdin_data)
    return result


def extract_task_info_from_args(args: str) -> tuple[Path | None, str | None]:
    """Extract task file path and task ID from command args.

    Args:
        args: Command arguments string.

    Returns:
        Tuple of (task_file_path, task_id) or (None, None) if not extractable.
    """
    if not args:
        return None, None

    # Parse the args string
    # Format: "<task-file-path> --task <task-id>"
    # or: "<task-file-path> <task-id>"

    parts = args.split()
    if not parts:
        return None, None

    task_file_path: Path | None = None
    task_id: str | None = None

    # First part should be the task file path
    if parts[0].endswith(".md"):
        task_file_path = Path(parts[0])

    # Look for --task flag or task ID pattern
    for i, part in enumerate(parts):
        if part == "--task" and i + 1 < len(parts):
            task_id = parts[i + 1]
            break
        # Match alphanumeric task ID pattern (e.g., "1.1", "T1", "P0-T01")
        if re.match(rf"^{_TASK_ID_RE}$", part) and i > 0:
            task_id = part
            break

    return task_file_path, task_id


def extract_task_info_from_prompt(prompt: str) -> tuple[Path | None, str | None]:
    """Extract task file path and task ID from sub-agent prompt.

    Args:
        prompt: The sub-agent's prompt string.

    Returns:
        Tuple of (task_file_path, task_id) or (None, None) if not extractable.
    """
    if not prompt:
        return None, None

    # Look for /start-task invocation pattern in the prompt
    # Pattern: /start-task <path> --task <id>
    match = re.search(
        rf"/start-task\s+([^\s]+\.md)(?:\s+--task\s+({_TASK_ID_RE}))?", prompt
    )
    if match:
        task_file = Path(match.group(1))
        task_id = match.group(2)
        return task_file, task_id

    return None, None


def get_context_file_path(cwd: Path, session_id: str) -> Path:
    """Get the path to the active task context file.

    Args:
        cwd: Current working directory.
        session_id: Session ID from hook input.

    Returns:
        Path to the context file.
    """
    context_dir = cwd / ".claude" / "context"
    return context_dir / f"active-task-{session_id}.json"


def read_task_context(cwd: Path, session_id: str) -> tuple[Path | None, str | None]:
    """Read task info from context file.

    Args:
        cwd: Current working directory.
        session_id: Session ID from hook input.

    Returns:
        Tuple of (task_file_path, task_id) or (None, None) if not found.
    """
    context_file = get_context_file_path(cwd, session_id)
    if not context_file.exists():
        return None, None

    try:
        context_data: dict[str, str] = json.loads(
            context_file.read_text(encoding="utf-8")
        )
        task_file = context_data.get("task_file_path")
        task_id = context_data.get("task_id")
        if task_file and task_id:
            return Path(task_file), task_id
    except (json.JSONDecodeError, KeyError):
        pass

    return None, None


def write_task_context(
    cwd: Path, session_id: str, task_file_path: Path, task_id: str
) -> None:
    """Write task info to context file.

    Args:
        cwd: Current working directory.
        session_id: Session ID from hook input.
        task_file_path: Path to the task file.
        task_id: Task ID being worked on.
    """
    context_file = get_context_file_path(cwd, session_id)
    context_file.parent.mkdir(parents=True, exist_ok=True)

    context_data = {"task_file_path": str(task_file_path), "task_id": task_id}
    context_file.write_text(json.dumps(context_data), encoding="utf-8")


def delete_task_context(cwd: Path, session_id: str) -> None:
    """Delete the task context file.

    Args:
        cwd: Current working directory.
        session_id: Session ID from hook input.
    """
    context_file = get_context_file_path(cwd, session_id)
    if context_file.exists():
        context_file.unlink()


def _find_yaml_task_file(directory: Path, task_id: str) -> Path | None:
    """Find an individual task file whose YAML frontmatter matches a task ID.

    Scans ``.md`` files in the given directory for one whose ``task`` frontmatter
    field equals *task_id*.

    Args:
        directory: Directory to search for task files.
        task_id: Task ID to match against the ``task`` frontmatter field.

    Returns:
        Path to the matching file, or None if no match found.
    """
    for md_file in sorted(directory.glob("*.md")):
        try:
            file_content = md_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if not has_yaml_frontmatter(file_content):
            continue
        try:
            frontmatter, _ = parse_yaml_frontmatter(file_content)
        except (ValueError, TypeError):
            continue
        if str(frontmatter.get("task", "")) == task_id:
            return md_file
    return None


def find_task_section(content: str, task_id: str) -> tuple[int, int] | None:
    """Find the start and end line indices for a task section.

    For YAML frontmatter files, checks the ``task`` field in frontmatter.
    For legacy markdown files, searches for ``## Task <id>:`` headers.

    Args:
        content: Full content of the task file.
        task_id: Task ID to find (e.g., "1.1", "T1", "P0-T01").

    Returns:
        Tuple of (start_line, end_line) indices, or None if not found.
    """
    # --- YAML frontmatter format ---
    if has_yaml_frontmatter(content):
        try:
            frontmatter, _ = parse_yaml_frontmatter(content)
        except (ValueError, TypeError):
            return None
        # For individual task files the entire file IS the task
        if str(frontmatter.get("task", "")) == task_id:
            lines = content.split("\n")
            return 0, len(lines)
        return None

    # --- Legacy markdown format ---
    lines = content.split("\n")
    task_pattern = rf"^##\s+Task\s+{re.escape(task_id)}:\s*"

    start_idx: int | None = None
    end_idx: int | None = None

    for i, line in enumerate(lines):
        if re.match(task_pattern, line):
            start_idx = i
            continue

        # If we found the start, look for the next task header or end of file
        if start_idx is not None and re.match(rf"^##\s+Task\s+{_TASK_ID_RE}:", line):
            end_idx = i
            break

    if start_idx is not None:
        # If no next task found, end at file end
        if end_idx is None:
            end_idx = len(lines)
        return start_idx, end_idx

    return None


_LEGACY_INSERT_AFTER_FIELDS: tuple[str, ...] = (
    "Status",
    "Dependencies",
    "Priority",
    "Complexity",
    "Agent",
)


def _update_legacy_timestamp(
    lines: list[str], start_idx: int, end_idx: int, field_name: str, timestamp: str
) -> str:
    """Add or update a timestamp field in a legacy markdown task section.

    Args:
        lines: All lines of the file.
        start_idx: Start line index of the task section.
        end_idx: End line index of the task section (exclusive).
        field_name: Bold-markdown field name (e.g., "Completed").
        timestamp: ISO timestamp string.

    Returns:
        Reconstructed file content with the field added or updated.
    """
    task_lines = lines[start_idx:end_idx]
    field_pattern = rf"^\*\*{field_name}\*\*:\s*"
    new_field_line = f"**{field_name}**: {timestamp}"

    # Check if field already exists
    for i, line in enumerate(task_lines):
        if re.match(field_pattern, line):
            task_lines[i] = new_field_line
            return "\n".join(lines[:start_idx] + task_lines + lines[end_idx:])

    # Insert new field after a known metadata line, or after the header
    insert_idx = 1
    for i, line in enumerate(task_lines):
        if any(re.match(rf"^\*\*{f}\*\*:", line) for f in _LEGACY_INSERT_AFTER_FIELDS):
            insert_idx = i + 1
            break

    task_lines.insert(insert_idx, new_field_line)
    return "\n".join(lines[:start_idx] + task_lines + lines[end_idx:])


def add_timestamp_to_task(
    content: str, task_id: str, field_name: str, timestamp: str
) -> str:
    """Add or update a timestamp field in a task section.

    For YAML frontmatter files, uses ``update_yaml_field`` to set the field in
    frontmatter.  For legacy markdown files, delegates to
    ``_update_legacy_timestamp``.

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        field_name: Field name (e.g., "started", "completed", "last_activity"
            for YAML; "Started", "Completed", "LastActivity" for legacy).
        timestamp: ISO timestamp string.

    Returns:
        Updated content with timestamp field added/updated.

    Raises:
        ValueError: If task section not found.
    """
    # --- YAML frontmatter format ---
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        yaml_field = _legacy_field_to_yaml(field_name)
        return update_yaml_field(content, yaml_field, timestamp)

    # --- Legacy markdown format ---
    section = find_task_section(content, task_id)
    if section is None:
        raise ValueError(f"Task {task_id} not found in file")

    start_idx, end_idx = section
    lines = content.split("\n")
    return _update_legacy_timestamp(lines, start_idx, end_idx, field_name, timestamp)


def _legacy_field_to_yaml(field_name: str) -> str:
    """Convert a legacy PascalCase field name to a YAML snake_case field name.

    Args:
        field_name: Legacy field name (e.g., "LastActivity", "Completed").

    Returns:
        YAML field name (e.g., "last_activity", "completed").
    """
    field_map: dict[str, str] = {
        "LastActivity": "last_activity",
        "Started": "started",
        "Completed": "completed",
        "Status": "status",
    }
    return field_map.get(field_name, field_name.lower())


def update_task_status(content: str, task_id: str, new_status: str) -> str:
    r"""Update the status field in a task section.

    For YAML frontmatter files, normalizes the status and uses
    ``update_yaml_field``.  For legacy markdown files, uses regex-based line
    replacement.

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        new_status: New status value. For YAML files this is normalized
            (e.g., "complete"); for legacy files the raw value is written
            (e.g., "\\u2705 COMPLETE").

    Returns:
        Updated content with status changed.

    Raises:
        ValueError: If task section not found.
    """
    # --- YAML frontmatter format ---
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        normalized = normalize_status(new_status)
        return update_yaml_field(content, "status", normalized)

    # --- Legacy markdown format ---
    section = find_task_section(content, task_id)
    if section is None:
        raise ValueError(f"Task {task_id} not found in file")

    start_idx, end_idx = section
    lines = content.split("\n")
    task_lines = lines[start_idx:end_idx]

    # Find and update status line
    status_pattern = r"^\*\*Status\*\*:\s*.*$"
    for i, line in enumerate(task_lines):
        if re.match(status_pattern, line):
            task_lines[i] = f"**Status**: {new_status}"
            break

    # Reconstruct content
    result_lines = lines[:start_idx] + task_lines + lines[end_idx:]
    return "\n".join(result_lines)


def get_iso_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO formatted timestamp string.
    """
    return datetime.now(UTC).isoformat(timespec="seconds")


def _resolve_task_file(full_path: Path, task_id: str) -> tuple[Path, str] | None:
    """Resolve a task file path, handling both file and directory targets.

    When *full_path* is a directory, searches for an individual ``.md`` file
    whose YAML ``task`` field matches *task_id*.  When it is a file, returns
    the path and its content directly.

    Args:
        full_path: Path that may be a file or directory.
        task_id: Task ID to locate.

    Returns:
        Tuple of (resolved_path, file_content), or None if not found.
    """
    if full_path.is_dir():
        resolved = _find_yaml_task_file(full_path, task_id)
        if resolved is None:
            return None
        return resolved, resolved.read_text(encoding="utf-8")
    if full_path.is_file():
        return full_path, full_path.read_text(encoding="utf-8")
    return None


def handle_subagent_stop(hook_input: dict[str, Any]) -> None:
    """Handle SubagentStop event - mark task COMPLETE with timestamp.

    Parses the sub-agent's prompt to find the /start-task invocation
    and extracts task file path and task ID.

    Args:
        hook_input: Parsed hook input from stdin.
    """
    # Get the sub-agent's prompt which contains /start-task invocation
    prompt = hook_input.get("prompt", "")
    if not prompt:
        # Try tool_input for backwards compatibility
        tool_input = hook_input.get("tool_input", {})
        prompt = tool_input.get("prompt", "")

    task_file_path, task_id = extract_task_info_from_prompt(prompt)

    if task_file_path is None or task_id is None:
        # Not a /start-task sub-agent, exit silently
        sys.exit(0)

    # Resolve path relative to cwd
    cwd = Path(hook_input.get("cwd", "."))
    full_path = (
        cwd / task_file_path if not task_file_path.is_absolute() else task_file_path
    )

    resolved = _resolve_task_file(full_path, task_id)
    if resolved is None:
        print(f"Task file not found: {full_path}", file=sys.stderr)
        sys.exit(2)

    resolved_path, content = resolved
    timestamp = get_iso_timestamp()

    try:
        # Update status to COMPLETE (normalize_status handles YAML normalization)
        updated_content = update_task_status(content, task_id, "\u2705 COMPLETE")
        # Add Completed timestamp
        updated_content = add_timestamp_to_task(
            updated_content, task_id, "Completed", timestamp
        )
        resolved_path.write_text(updated_content, encoding="utf-8")
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    # Clean up context file
    session_id = hook_input.get("session_id", "")
    if session_id:
        delete_task_context(cwd, session_id)


def handle_activity_update(hook_input: dict[str, Any]) -> None:
    """Handle PostToolUse event - update LastActivity timestamp.

    Reads task info from context file and updates the LastActivity field.

    Args:
        hook_input: Parsed hook input from stdin.
    """
    cwd = Path(hook_input.get("cwd", "."))
    session_id = hook_input.get("session_id", "")

    if not session_id:
        # No session ID, can't find context file
        sys.exit(0)

    task_file_path, task_id = read_task_context(cwd, session_id)

    if task_file_path is None or task_id is None:
        # No active task context, exit silently
        sys.exit(0)

    # Resolve path relative to cwd
    full_path = (
        cwd / task_file_path if not task_file_path.is_absolute() else task_file_path
    )

    resolved = _resolve_task_file(full_path, task_id)
    if resolved is None:
        # Task file doesn't exist, exit silently
        sys.exit(0)

    resolved_path, content = resolved
    timestamp = get_iso_timestamp()

    try:
        updated_content = add_timestamp_to_task(
            content, task_id, "LastActivity", timestamp
        )
        resolved_path.write_text(updated_content, encoding="utf-8")
    except ValueError:
        # Task section not found, exit silently
        sys.exit(0)


def main() -> None:
    """Main entry point for the hook script."""
    try:
        hook_input = parse_hook_input()
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Failed to parse hook input: {e}", file=sys.stderr)
        sys.exit(2)

    event_name = hook_input.get("hook_event_name", "")

    if event_name == "SubagentStop":
        handle_subagent_stop(hook_input)
    elif event_name == "PostToolUse":
        # Update LastActivity for Write/Edit/Bash operations
        tool_name = hook_input.get("tool_name", "")
        if tool_name in {"Write", "Edit", "Bash"}:
            handle_activity_update(hook_input)
    # Unknown event or non-matching tool, exit silently
    sys.exit(0)


if __name__ == "__main__":
    main()
