#!/usr/bin/env python3
"""Get task context for implementation manager dynamic injection."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_available_features() -> dict[str, Any]:
    """Get list of features with task files.

    Returns:
        Dictionary containing features array, count, and optional message.
    """
    if not Path("plan").exists():
        return {
            "features": [],
            "count": 0,
            "message": "Not in a project with task files (no plan/ directory)",
        }

    try:
        # Run implementation_manager.py list-features
        script_path = Path(__file__).parent / "implementation_manager.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "list-features", "."],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            parsed: dict[str, Any] = json.loads(result.stdout)
        else:
            return {
                "features": [],
                "count": 0,
                "message": f"Failed to list features: {result.stderr}",
            }
    except (OSError, json.JSONDecodeError, ValueError) as e:
        return {
            "features": [],
            "count": 0,
            "message": f"Error running implementation_manager.py: {e}",
        }
    else:
        return parsed


def get_active_task() -> str:
    """Get active task context if any.

    Returns:
        JSON content of active task file, or message if no active task.
    """
    context_dir = Path(".claude/context")
    if not context_dir.exists():
        return "No active task"

    # Find active-task-*.json files
    task_files = list(context_dir.glob("active-task-*.json"))
    if not task_files:
        return "No active task"

    # Return first match
    try:
        return task_files[0].read_text(encoding="utf-8")
    except OSError as e:
        return f"Error reading task context: {e}"


def main() -> None:
    """Print task context information."""
    features = get_available_features()
    print(f"**Available features:**\n```json\n{json.dumps(features, indent=2)}\n```\n")

    active_task = get_active_task()
    print(f"**Active task context:**\n{active_task}")


if __name__ == "__main__":
    main()
