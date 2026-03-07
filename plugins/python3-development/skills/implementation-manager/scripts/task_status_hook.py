#!/usr/bin/env python3
"""Task Status Hook - Update task status and timestamps automatically.

This hook script handles multiple hook events:
- SubagentStop: Parse prompt for task info, set status to COMPLETE, add Completed timestamp
- PostToolUse (Write|Edit|Bash): Update LastActivity timestamp using context file

Task files use YAML frontmatter format (detected via ``---`` delimiters),
updated with update_yaml_field().

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

from task_format import has_yaml_frontmatter, normalize_status, parse_yaml_frontmatter, update_yaml_field

# Conditionally add backlog_core to sys.path for GitHub sync.
# The hook script lives at:
#   plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py
# parents[5] resolves to the repo root (e.g. /home/user/claude_skills).
_BACKLOG_CORE_HOOK = Path(__file__).resolve().parents[5] / ".claude" / "skills" / "backlog" / "backlog_core"
if _BACKLOG_CORE_HOOK.exists():
    sys.path.insert(0, str(_BACKLOG_CORE_HOOK.parent))

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
    # Pattern 1: /start-task <path> --task <id>  (literal slash-command)
    match = re.search(rf"/start-task\s+([^\s]+\.md)(?:\s+--task\s+({_TASK_ID_RE}))?", prompt)
    if match:
        task_file = Path(match.group(1))
        task_id = match.group(2)
        return task_file, task_id

    # Pattern 2: Skill(skill="start-task", args="<path> --task <id>")
    # The orchestrator invokes start-task via the Skill tool, not as a literal command.
    skill_match = re.search(
        rf'Skill\(\s*skill\s*=\s*["\']start-task["\']\s*,\s*args\s*=\s*["\']'
        rf"([^\s\"']+\.md)(?:\s+--task\s+({_TASK_ID_RE}))?"
        rf'["\']',
        prompt,
    )
    if skill_match:
        task_file = Path(skill_match.group(1))
        task_id = skill_match.group(2)
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
        context_data: dict[str, str] = json.loads(context_file.read_text(encoding="utf-8"))
        task_file = context_data.get("task_file_path")
        task_id = context_data.get("task_id")
        if task_file and task_id:
            return Path(task_file), task_id
    except (json.JSONDecodeError, KeyError):
        pass

    return None, None


def write_task_context(cwd: Path, session_id: str, task_file_path: Path, task_id: str) -> None:
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


def add_timestamp_to_task(content: str, task_id: str, field_name: str, timestamp: str) -> str:
    """Add or update a timestamp field in a task section.

    Uses ``update_yaml_field`` to set the field in YAML frontmatter,
    converting PascalCase field names (e.g., "LastActivity") to snake_case
    YAML keys (e.g., "last_activity").

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        field_name: PascalCase field name (e.g., "Started", "Completed",
            "LastActivity").
        timestamp: ISO timestamp string.

    Returns:
        Updated content with timestamp field added/updated.

    Raises:
        ValueError: If task section not found or file is not YAML frontmatter format.
    """
    # --- YAML frontmatter format ---
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        field_map: dict[str, str] = {
            "LastActivity": "last_activity",
            "Started": "started",
            "Completed": "completed",
            "Status": "status",
        }
        yaml_field = field_map.get(field_name, field_name.lower())
        return update_yaml_field(content, yaml_field, timestamp)

    raise ValueError(f"Task {task_id} not found in file")


def update_task_status(content: str, task_id: str, new_status: str) -> str:
    """Update the status field in a task section.

    Normalizes the status value and uses ``update_yaml_field`` to write it
    to the YAML frontmatter.

    Args:
        content: Full content of the task file.
        task_id: Task ID to update.
        new_status: New status value; normalized by ``normalize_status``
            before writing (e.g., "complete").

    Returns:
        Updated content with status changed.

    Raises:
        ValueError: If task section not found or file is not YAML frontmatter format.
    """
    # --- YAML frontmatter format ---
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        normalized = normalize_status(new_status)
        return update_yaml_field(content, "status", normalized)

    raise ValueError(f"Task {task_id} not found in file")


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


def _fallback_to_context_file(hook_input: dict[str, Any]) -> tuple[Path | None, str | None]:
    """Read task info from the active-task context file as a fallback.

    When prompt parsing fails (e.g. Skill() syntax not matched), the context
    file written by /start-task step 4 provides the task_file_path and task_id.

    Returns:
        Tuple of (task_file_path, task_id) or (None, None) if context file not found.
    """
    cwd = Path(hook_input.get("cwd", "."))
    session_id = hook_input.get("session_id", "")
    if session_id:
        return read_task_context(cwd, session_id)
    return None, None


def get_parent_issue_number(hook_input: dict[str, Any]) -> int | None:
    """Read parent_issue_number from the active-task context file.

    Returns the integer issue number, or None if the field is absent or the
    context file does not exist. Never raises — all failures return None.

    Args:
        hook_input: Parsed hook input from stdin.

    Returns:
        Parent issue number as int, or None if not found.
    """
    cwd = Path(hook_input.get("cwd", "."))
    session_id = hook_input.get("session_id", "")
    if not session_id:
        return None
    context_file = get_context_file_path(cwd, session_id)
    if not context_file.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(context_file.read_text(encoding="utf-8"))
        if "parent_issue_number" in data:
            return int(data["parent_issue_number"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        pass
    return None


def sync_completion_to_github(task_file_path: Path, task_id: str, parent_issue_number: int | None) -> None:
    """Sync task completion status to GitHub sub-issue.

    Reads github_issue field from the task YAML frontmatter. If absent, logs
    a warning to stderr and returns without making any GitHub API call.
    Wraps all GitHub operations in try/except — failure logs a warning to stderr
    and returns without raising. This function is always called after the local
    write succeeds; GitHub failure does not affect hook exit code.

    Args:
        task_file_path: Resolved path to the task YAML file.
        task_id: Task ID being completed.
        parent_issue_number: Optional parent story issue number from context file.
    """
    try:
        # Read github_issue from task YAML frontmatter
        github_issue: int | None = None
        if task_file_path.is_file():
            try:
                file_content = task_file_path.read_text(encoding="utf-8")
                if has_yaml_frontmatter(file_content):
                    frontmatter, _ = parse_yaml_frontmatter(file_content)
                    raw = frontmatter.get("github_issue")
                    if raw is not None:
                        github_issue = int(raw)
            except (ValueError, TypeError, OSError):
                pass

        if github_issue is None:
            print(f"[hook] No github_issue field in {task_file_path} — skipping GitHub sync", file=sys.stderr)
            return

        if not _BACKLOG_CORE_HOOK.exists():
            print("[hook] backlog_core not found — skipping GitHub sync", file=sys.stderr)
            return

        # Conditional import — only after path guard
        import backlog_core.github as _bc_github  # noqa: PLC0415

        try:
            repo = _bc_github.get_github()
        except Exception as e:  # noqa: BLE001
            print(f"[hook] GitHub unavailable — skipping GitHub sync: {e}", file=sys.stderr)
            return

        try:
            _bc_github.update_task_status(repo, github_issue, "complete")
        except Exception as e:  # noqa: BLE001
            print(f"[hook] GitHub sync update_task_status failed: {e}", file=sys.stderr)
            return

        print(f"[hook] Synced task {task_id} completion to GitHub issue #{github_issue}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"[hook] GitHub sync failed: {e}", file=sys.stderr)


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

    # Fallback: read from context file written by /start-task step 4
    if task_file_path is None or task_id is None:
        task_file_path, task_id = _fallback_to_context_file(hook_input)

    if task_file_path is None or task_id is None:
        # Not a /start-task sub-agent, exit silently
        sys.exit(0)

    # Resolve path relative to cwd
    cwd = Path(hook_input.get("cwd", "."))
    full_path = cwd / task_file_path if not task_file_path.is_absolute() else task_file_path

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
        updated_content = add_timestamp_to_task(updated_content, task_id, "Completed", timestamp)
        resolved_path.write_text(updated_content, encoding="utf-8")
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)

    # Clean up context file
    session_id = hook_input.get("session_id", "")
    if session_id:
        delete_task_context(cwd, session_id)

    # Step 5: sync_completion_to_github — best-effort, never changes exit code
    sync_completion_to_github(resolved_path, task_id, get_parent_issue_number(hook_input))


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
    full_path = cwd / task_file_path if not task_file_path.is_absolute() else task_file_path

    resolved = _resolve_task_file(full_path, task_id)
    if resolved is None:
        # Task file doesn't exist, exit silently
        sys.exit(0)

    resolved_path, content = resolved

    # Guard: skip silently if task is already complete
    if has_yaml_frontmatter(content):
        try:
            frontmatter, _ = parse_yaml_frontmatter(content)
            current_status = normalize_status(str(frontmatter.get("status", "")))
            if current_status == "complete":
                return
        except (ValueError, TypeError):
            pass

    timestamp = get_iso_timestamp()

    try:
        updated_content = add_timestamp_to_task(content, task_id, "LastActivity", timestamp)
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
