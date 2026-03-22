#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Kage-bunshin spawn — launch an independent claude -p session in an optional git worktree.

Spawns a ``claude -p`` CLI process with proper environment setup.
Prints a JSON record of the spawned process to stdout and exits immediately.
The caller is responsible for managing the PID.

Usage:
    spawn.py [--worktree] [--branch BRANCH] [--model MODEL]
             [--max-budget MAX_BUDGET] [--name NAME]
             [--no-session-persistence] [--output-dir DIR]
             PROMPT

Exit Codes:
    0: Process spawned successfully.
    1: Fatal error (claude not found, git worktree failed, etc.).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_MODEL = "sonnet"
_DEFAULT_OUTPUT_DIR = Path("/tmp/kage-bunshin")  # noqa: S108
_NAME_MAX_CHARS = 30
_SLUG_MAX_CHARS = 40
_LOCK_ITEM_MAX_CHARS = 100


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(text: str, max_length: int = _SLUG_MAX_CHARS) -> str:
    """Convert *text* to a URL-safe slug.

    Args:
        text: Input string to slugify.
        max_length: Maximum length of the resulting slug.

    Returns:
        Lowercase slug with non-alphanumeric characters replaced by hyphens,
        truncated to *max_length* characters with trailing hyphens stripped.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_length].rstrip("-")


def _auto_name(prompt: str) -> str:
    """Derive a session display name from the first chars of *prompt*.

    Args:
        prompt: The full prompt string.

    Returns:
        The first :data:`_NAME_MAX_CHARS` characters of *prompt*, stripped.
    """
    return prompt[:_NAME_MAX_CHARS].strip()


def _git_repo_root() -> Path:
    """Return the root of the current git repository.

    Returns:
        Absolute path to the repository root.

    Raises:
        SystemExit: If the current directory is not inside a git repository.
    """
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)  # noqa: S607
    if result.returncode != 0:
        print(f"error: not inside a git repository: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return Path(result.stdout.strip())


def _current_branch() -> str:
    """Return the name of the currently checked-out git branch.

    Returns:
        Branch name string.

    Raises:
        SystemExit: If git cannot determine the current branch.
    """
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)  # noqa: S607
    if result.returncode != 0:
        print(f"error: cannot determine current branch: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Worktree management
# ---------------------------------------------------------------------------


def _setup_worktree(name_slug: str, branch: str, repo_root: Path) -> Path:
    """Create (or reuse) a git worktree for the session.

    Args:
        name_slug: Slug used to name the worktree directory.
        branch: Branch name to create the worktree from.
        repo_root: Absolute path to the git repository root.

    Returns:
        Absolute path to the worktree directory.

    Raises:
        SystemExit: If ``git worktree add`` fails for a reason other than the
            worktree already existing.
    """
    worktree_path = repo_root / ".worktrees" / f"kb-{name_slug}"

    if not worktree_path.exists():
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            cwd=str(repo_root),
        )
        if result.returncode != 0:
            print(f"error: git worktree add failed: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"warning: worktree already exists, reusing: {worktree_path}", file=sys.stderr)

    return worktree_path


def _symlink_shared_artifact(source: Path, dest: Path) -> None:
    """Create a symlink at *dest* pointing to *source*, with collision checks.

    Args:
        source: Absolute path of the target the symlink should point to.
        dest: Path where the symlink should be created inside the worktree.
    """
    if not source.exists():
        return

    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and dest.resolve() == source.resolve():
            # Already correct — nothing to do.
            return
        print(f"warning: {dest} already exists and is not a symlink to {source}; skipping", file=sys.stderr)
        return

    dest.symlink_to(source)


def _write_lock_file(worktree: Path, session_id: str, prompt: str, model: str) -> Path | None:
    """Write a JSON lock file into the worktree's .claude directory.

    Args:
        worktree: Root path of the worktree.
        session_id: UUID4 string for this session.
        prompt: Full prompt string (truncated to :data:`_LOCK_ITEM_MAX_CHARS`).
        model: Model identifier for the session.

    Returns:
        Path to the written lock file, or ``None`` if the write failed.
    """
    claude_dir = worktree / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    lock_path = claude_dir / "kage-bunshin.lock"
    payload: dict[str, Any] = {
        "session_id": session_id,
        "parent_pid": os.getpid(),
        "spawned_at": datetime.now(UTC).isoformat(),
        "item": prompt[:_LOCK_ITEM_MAX_CHARS],
        "model": model,
    }
    try:
        lock_path.write_text(json.dumps(payload, indent=2))
    except OSError as exc:
        print(f"warning: could not write lock file: {exc}", file=sys.stderr)
        return None
    return lock_path


# ---------------------------------------------------------------------------
# Command building
# ---------------------------------------------------------------------------


def _build_command(
    model: str, max_budget: float | None, name: str | None, no_session_persistence: bool, prompt: str
) -> list[str]:
    """Assemble the ``claude -p`` command list.

    Args:
        model: Model identifier string.
        max_budget: Optional maximum USD budget.
        name: Optional session display name.
        no_session_persistence: Whether to pass ``--no-session-persistence``.
        prompt: The prompt text to send.

    Returns:
        List of strings suitable for passing to ``subprocess.Popen``.
    """
    cmd: list[str] = ["claude", "-p", "--model", model, "--permission-mode", "auto", "--output-format", "json"]
    if max_budget is not None:
        cmd += ["--max-budget-usd", str(max_budget)]
    if name:
        cmd += ["--name", name]
    if no_session_persistence:
        cmd.append("--no-session-persistence")
    cmd.append(prompt)
    return cmd


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed :class:`argparse.Namespace`.
    """
    parser = argparse.ArgumentParser(
        description="Spawn a kage-bunshin — an independent claude -p session in an optional isolated git worktree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("prompt", metavar="PROMPT", help="Prompt to send to the spawned session.")
    parser.add_argument(
        "--worktree", action="store_true", default=False, help="Create an isolated git worktree for the session."
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Branch to create the worktree from (default: current branch). Only used with --worktree.",
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_MODEL,
        help=f"Model for the spawned session's orchestrator (default: {_DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-budget", type=float, default=None, metavar="MAX_BUDGET", help="Maximum USD spend for the session."
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Session display name. Auto-generated from the first 30 chars of PROMPT if omitted.",
    )
    parser.add_argument(
        "--no-session-persistence", action="store_true", default=False, help="Do not save the session to disk."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Directory for result JSON and error logs (default: {_DEFAULT_OUTPUT_DIR}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Spawn a kage-bunshin and print a JSON process record to stdout.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Raises:
        SystemExit: On fatal errors (claude not found, git failures).
    """
    args = _parse_args(argv)

    # Verify claude is available before doing any setup work.
    if shutil.which("claude") is None:
        print("error: claude binary not found in PATH", file=sys.stderr)
        sys.exit(1)

    # Resolve display name and slug.
    display_name: str = args.name or _auto_name(args.prompt)
    name_slug = _slugify(display_name)

    # Ensure output directory exists.
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / f"{name_slug}-result.json"
    error_file = output_dir / f"{name_slug}-err.log"

    # Worktree setup.
    worktree_path: Path | None = None
    lock_file_path: Path | None = None
    session_id = str(uuid.uuid4())

    if args.worktree:
        repo_root = _git_repo_root()
        branch = args.branch or _current_branch()
        worktree_path = _setup_worktree(name_slug, branch, repo_root)

        # Symlink shared heavy artifacts into the worktree.
        for artifact_name in (".venv", "node_modules"):
            _symlink_shared_artifact(source=repo_root / artifact_name, dest=worktree_path / artifact_name)

        lock_file_path = _write_lock_file(worktree_path, session_id, args.prompt, args.model)

    # Build the command.
    cmd = _build_command(
        model=args.model,
        max_budget=args.max_budget,
        name=display_name if args.name else None,
        no_session_persistence=args.no_session_persistence,
        prompt=args.prompt,
    )

    # Spawn — do not wait.
    cwd = str(worktree_path) if worktree_path else str(Path.cwd())
    with result_file.open("w") as stdout_fh, error_file.open("w") as stderr_fh:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=stdout_fh, stderr=stderr_fh, stdin=subprocess.DEVNULL)

    # Emit the process record.
    record: dict[str, Any] = {
        "pid": proc.pid,
        "name": display_name,
        "worktree": str(worktree_path) if worktree_path else None,
        "result_file": str(result_file),
        "error_file": str(error_file),
        "model": args.model,
        "lock_file": str(lock_file_path) if lock_file_path else None,
    }
    print(json.dumps(record))


if __name__ == "__main__":
    main()
