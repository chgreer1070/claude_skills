#!/usr/bin/env python3
"""Get GitLab CI/CD context for dynamic injection."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Configuration constants
PREVIEW_LINES = 50  # Number of lines to show from .gitlab-ci.yml


def run_glab(*args: str) -> str | None:
    """Run glab command and return output.

    Args:
        *args: Command-line arguments to pass to glab.

    Returns:
        Command stdout if successful, None if command failed or glab not found.
    """
    # Verify glab is available in PATH (security: S607 partial path mitigation)
    glab_path = shutil.which("glab")
    if not glab_path:
        return None

    try:
        result = subprocess.run(
            [glab_path, *args], capture_output=True, text=True, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def get_pipeline_status() -> str:
    """Get current pipeline status.

    Returns:
        Pipeline status output from glab, or error message if unavailable.
    """
    status = run_glab("ci", "status", "--compact")
    return status or "Not in GitLab project or glab not installed"


def get_recent_pipelines() -> str:
    """Get recent pipeline runs.

    Returns:
        Recent pipeline list output from glab, or error message if unavailable.
    """
    pipelines = run_glab("ci", "list", "-n", "5")
    return pipelines or "Pipeline history unavailable"


def get_ci_validation() -> str:
    """Check CI configuration validation.

    Returns:
        Validation status message indicating if .gitlab-ci.yml is valid.
    """
    result = run_glab("ci", "lint", "--quiet")
    if result is not None:
        return "✓ .gitlab-ci.yml is valid"

    # Check if it's a validation error or missing glab
    gitlab_ci = Path(".gitlab-ci.yml")
    if not gitlab_ci.exists():
        return "No .gitlab-ci.yml in current directory"

    return "✗ CI config has errors or glab not available"


def get_gitlab_ci_preview() -> str:
    """Get first N lines of .gitlab-ci.yml.

    Returns:
        Markdown-formatted preview of .gitlab-ci.yml, or error message if unavailable.
    """
    gitlab_ci = Path(".gitlab-ci.yml")
    if not gitlab_ci.exists():
        return "No .gitlab-ci.yml in current directory"

    try:
        lines = gitlab_ci.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return f"Error reading .gitlab-ci.yml: {e}"
    else:
        if len(lines) > PREVIEW_LINES:
            preview = "\n".join(lines[:PREVIEW_LINES])
            preview += f"\n\n... ({len(lines) - PREVIEW_LINES} more lines)"
        else:
            preview = "\n".join(lines[:PREVIEW_LINES])
        return f"```yaml\n{preview}\n```"


def main() -> None:
    """Print GitLab context information."""
    print(f"**Pipeline status:**\n{get_pipeline_status()}\n")
    print(f"**Recent pipeline runs:**\n{get_recent_pipelines()}\n")
    print(f"**CI configuration validation:**\n{get_ci_validation()}\n")
    print(f"**Current .gitlab-ci.yml (first 50 lines):**\n{get_gitlab_ci_preview()}")


if __name__ == "__main__":
    main()
