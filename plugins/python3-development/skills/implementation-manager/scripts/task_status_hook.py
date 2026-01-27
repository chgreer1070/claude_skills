#!/usr/bin/env python3
"""Task Status Hook - Update task status and timestamps automatically.

This hook script handles multiple hook events:
- SubagentStop: Parse prompt for task info, set status to COMPLETE, add Completed timestamp
- PostToolUse (Write|Edit|Bash): Update LastActivity timestamp using context file

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
        # Match task ID pattern (e.g., "1.1", "2", "3.2")
        if re.match(r"^\d+(?:\.\d+)?$", part) and i > 0:
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
        r"/start-task\s+([^\s]+\.md)(?:\s+--task\s+(\d+(?:\.\d+)?))?", prompt
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


def find_task_section(content: str, task_id: str) -> tuple[int, int] | None:
    """Find the start and end line indices for a task section.

    Args:
        content: Full content of the task file.
        task_id: Task ID to find (e.g., "1.1", "2").

    Returns:
        Tuple of (start_line, end_line) indices, or None if not found.
    """
    lines = content.split("\n")
    task_pattern = rf"^##\s+Task\s+{re.escape(task_id)}:\s*"

    start_idx: int | None = None
    end_idx: int | None = None

    for i, line in enumerate(lines):
        if re.match(task_pattern, line):
            start_idx = i
            continue

        # If we found the start, look for the next task header or end of file
        if start_idx is not None and re.match(r"^##\s+Task\s+[\d.]+:", line):
            end_idx = i
            break

    if start_idx is not None:
        # If no next task found, end at file end
        if end_idx is None:
            end_idx = len(lines)
        return start_idx, end_idx

    return None


def add_timestamp_to_task(
    content: str, task_id: str, field_name: str, timestamp: str
) -> str:
    """Add or update a timestamp field in a task section.

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        field_name: Field name (e.g., "Started", "Completed", "LastActivity").
        timestamp: ISO timestamp string.

    Returns:
        Updated content with timestamp field added/updated.

    Raises:
        ValueError: If task section not found.
    """
    section = find_task_section(content, task_id)
    if section is None:
        raise ValueError(f"Task {task_id} not found in file")

    start_idx, end_idx = section
    lines = content.split("\n")
    task_lines = lines[start_idx:end_idx]

    # Check if field already exists
    field_pattern = rf"^\*\*{field_name}\*\*:\s*"
    field_exists = False
    field_idx: int | None = None

    for i, line in enumerate(task_lines):
        if re.match(field_pattern, line):
            field_exists = True
            field_idx = i
            break

    new_field_line = f"**{field_name}**: {timestamp}"

    if field_exists and field_idx is not None:
        # Update existing field
        task_lines[field_idx] = new_field_line
    else:
        # Insert new field after Status line (or after header if no Status)
        insert_idx = 1  # Default: after header
        for i, line in enumerate(task_lines):
            if re.match(r"^\*\*Status\*\*:", line):
                insert_idx = i + 1
                break
            if re.match(r"^\*\*Dependencies\*\*:", line):
                insert_idx = i + 1
                break
            if re.match(r"^\*\*Priority\*\*:", line):
                insert_idx = i + 1
                break
            if re.match(r"^\*\*Complexity\*\*:", line):
                insert_idx = i + 1
                break
            if re.match(r"^\*\*Agent\*\*:", line):
                insert_idx = i + 1
                break

        task_lines.insert(insert_idx, new_field_line)

    # Reconstruct content
    result_lines = lines[:start_idx] + task_lines + lines[end_idx:]
    return "\n".join(result_lines)


def update_task_status(content: str, task_id: str, new_status: str) -> str:
    """Update the status field in a task section.

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        new_status: New status value (e.g., "🔄 IN PROGRESS", "✅ COMPLETE").

    Returns:
        Updated content with status changed.

    Raises:
        ValueError: If task section not found.
    """
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

    if not full_path.exists():
        print(f"Task file not found: {full_path}", file=sys.stderr)
        sys.exit(2)

    content = full_path.read_text(encoding="utf-8")
    timestamp = get_iso_timestamp()

    try:
        # Update status to COMPLETE
        updated_content = update_task_status(content, task_id, "✅ COMPLETE")
        # Add Completed timestamp
        updated_content = add_timestamp_to_task(
            updated_content, task_id, "Completed", timestamp
        )
        full_path.write_text(updated_content, encoding="utf-8")
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

    if not full_path.exists():
        # Task file doesn't exist, exit silently
        sys.exit(0)

    content = full_path.read_text(encoding="utf-8")
    timestamp = get_iso_timestamp()

    try:
        updated_content = add_timestamp_to_task(
            content, task_id, "LastActivity", timestamp
        )
        full_path.write_text(updated_content, encoding="utf-8")
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
