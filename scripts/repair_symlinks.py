#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["gitpython>=3.1.45"]
# ///
"""Repair destroyed Git symlinks on Windows.

When core.symlinks is false, Git stores symlinks (mode 120000) as plain files
whose content is the target path. This script:
1. Sets core.symlinks true (repo-local)
2. Finds mode 120000 paths in HEAD that are plain files on disk (destroyed)
3. Removes each and creates real symlinks from HEAD blob content

Uses HEAD (not index) so we find destroyed symlinks even when they have been
staged — staging overwrites the index with 100644, so index-based detection
would miss them. destroyed-symlinks compares HEAD to index; we must fix before
that hook runs.

Uses GitPython — no subprocess / shell-out to git.

Requires Windows Developer Mode or Administrator for symlink creation.
Run from repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

if TYPE_CHECKING:
    from git.objects import Blob

GIT_MODE_SYMLINK = 0o120000  # 40960 decimal; GitPython tree items use this


def _ensure_core_symlinks(repo: Repo) -> bool:
    """Set core.symlinks true.

    Returns:
        True if core.symlinks is now true, False on failure.
    """
    try:
        cfg = repo.config_reader()
        val = cfg.get_value("core", "symlinks")
        if val in {"true", True}:
            return True
    except (OSError, KeyError):
        pass
    try:
        with repo.config_writer() as writer:
            writer.set_value("core", "symlinks", "true")
        val = repo.config_reader().get_value("core", "symlinks")
    except (OSError, KeyError):
        print("repair_symlinks: failed to set core.symlinks true", file=sys.stderr)
        return False
    else:
        return val in {"true", True}


def _find_destroyed_symlinks(repo: Repo, repo_root: Path) -> list[Path]:
    """Find mode 120000 paths in HEAD that are plain files on disk (destroyed).

    Uses HEAD (not index) because staging overwrites the index with 100644, so
    index-based detection would miss destroyed symlinks that have been staged.

    Returns:
        List of paths that are symlinks in HEAD but plain files on disk.
    """
    destroyed: list[Path] = []
    head_tree = repo.head.commit.tree
    for item in head_tree.traverse():
        if item.mode != GIT_MODE_SYMLINK:
            continue
        path = repo_root / item.path
        if path.exists() and not path.is_symlink():
            destroyed.append(path)
    return destroyed


def _get_symlink_target_from_blob(repo: Repo, blob: Blob) -> str:
    """Read symlink target from blob content.

    Returns:
        The symlink target path as stored in the blob.
    """
    stream = repo.odb.stream(blob.binsha)
    return stream.read().decode("utf-8", errors="replace").strip()


def _repair_one(repo: Repo, path: Path, repo_root: Path) -> bool:
    """Repair a single destroyed symlink.

    Returns:
        True on success, False on failure.
    """
    rel = path.relative_to(repo_root)
    rel_str = str(rel).replace("\\", "/")
    try:
        blob = repo.head.commit.tree / rel_str
    except KeyError:
        return False
    target = _get_symlink_target_from_blob(repo, blob)
    path.unlink()
    try:
        path.symlink_to(target)
    except OSError:
        print(
            f"repair_symlinks: could not create symlink for {rel} "
            "(enable Windows Developer Mode or run as Administrator)",
            file=sys.stderr,
        )
        return False
    if not path.is_symlink():
        return False
    # Stage the repaired symlink so index gets mode 120000; otherwise
    # destroyed-symlinks still fails (HEAD 120000 vs index 100644).
    repo.index.add([str(rel).replace("\\", "/")])
    repo.index.write()
    return True


def main() -> int:
    """Repair destroyed Git symlinks.

    Returns:
        0 on success, 1 on failure.
    """
    repo_root = Path.cwd()
    if not (repo_root / ".git").exists():
        print("repair_symlinks: not a git repository", file=sys.stderr)
        return 1

    try:
        repo = Repo(repo_root)
    except (InvalidGitRepositoryError, NoSuchPathError):
        print("repair_symlinks: not a git repository", file=sys.stderr)
        return 1

    if not _ensure_core_symlinks(repo):
        return 1

    symlink_paths = _find_destroyed_symlinks(repo, repo_root)
    if not symlink_paths:
        return 0

    for path in symlink_paths:
        if not _repair_one(repo, path, repo_root):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
