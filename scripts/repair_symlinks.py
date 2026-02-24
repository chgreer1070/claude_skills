#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///
"""Repair destroyed Git symlinks on Windows.

When core.symlinks is false, Git stores symlinks (mode 120000) as plain files
whose content is the target path. This script:
1. Sets core.symlinks true (repo-local)
2. Finds mode 120000 files that are plain files on disk (destroyed)
3. Removes each and runs git checkout to restore as real symlinks

Requires Windows Developer Mode or Administrator for symlink creation.
Run from repository root.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import which

GIT_MODE_SYMLINK = "120000"
LSFILES_PARTS = 2


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command and return the result.

    Returns:
        CompletedProcess from git. Exits if git not in PATH.
    """
    git_path = which("git")
    if not git_path:
        print("repair_symlinks: git not found in PATH", file=sys.stderr)
        sys.exit(1)
    return subprocess.run([git_path, *args], cwd=cwd, capture_output=True, text=True, check=False)


def _ensure_core_symlinks(repo_root: Path) -> bool:
    """Set core.symlinks true. Return False on failure.

    Returns:
        True if core.symlinks is true, False on failure.
    """
    result = run_git(["config", "core.symlinks"], repo_root)
    current = result.stdout.strip() if result.returncode == 0 else ""
    if current == "true":
        return True
    run_git(["config", "core.symlinks", "true"], repo_root)
    if run_git(["config", "core.symlinks"], repo_root).stdout.strip() != "true":
        print("repair_symlinks: failed to set core.symlinks true", file=sys.stderr)
        return False
    return True


def _find_destroyed_symlinks(repo_root: Path) -> list[Path] | None:
    """Find mode 120000 files that are plain files on disk (destroyed). None if ls-files failed.

    Returns:
        List of destroyed symlink paths, or None if git ls-files failed.
    """
    result = run_git(["ls-files", "-s"], repo_root)
    if result.returncode != 0:
        return None

    destroyed: list[Path] = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) != LSFILES_PARTS:
            continue
        mode, path_str = parts[0].split()[0], parts[1]
        if mode != GIT_MODE_SYMLINK:
            continue
        path = repo_root / path_str
        if path.exists() and not path.is_symlink():
            destroyed.append(path)
    return destroyed


def _repair_one(path: Path, repo_root: Path) -> bool:
    """Repair a single destroyed symlink. Return False on failure.

    Returns:
        True if symlink was restored, False on failure.
    """
    rel = path.relative_to(repo_root)
    path.unlink()
    result = run_git(["checkout", "--", str(rel)], repo_root)
    if result.returncode == 0 and path.is_symlink():
        return True
    run_git(["checkout", "--", str(rel)], repo_root)
    print(
        f"repair_symlinks: could not create symlink for {rel} (enable Windows Developer Mode or run as Administrator)",
        file=sys.stderr,
    )
    return False


def main() -> int:
    """Repair destroyed Git symlinks. Exit 0 on success, 1 on failure.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    repo_root = Path.cwd()
    if not (repo_root / ".git").exists():
        print("repair_symlinks: not a git repository", file=sys.stderr)
        return 1

    if not _ensure_core_symlinks(repo_root):
        return 1

    symlink_paths = _find_destroyed_symlinks(repo_root)
    if symlink_paths is None:
        print("repair_symlinks: git ls-files failed", file=sys.stderr)
        return 1
    if not symlink_paths:
        return 0

    for path in symlink_paths:
        if not _repair_one(path, repo_root):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
