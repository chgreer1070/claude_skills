#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["gitpython>=3.1.45"]
# ///
"""Repair destroyed Git symlinks and normalize absolute symlink targets.

When core.symlinks is false, Git stores symlinks (mode 120000) as plain files
whose content is the target path. This script:
1. Sets core.symlinks true (repo-local)
2. Finds mode 120000 paths in HEAD that are plain files on disk (destroyed)
3. Removes each and creates real symlinks from HEAD blob content
4. Finds existing symlinks with absolute targets that resolve inside the repo
5. Replaces them with portable relative symlinks

Uses HEAD (not index) so we find destroyed symlinks even when they have been
staged — staging overwrites the index with 100644, so index-based detection
would miss them. destroyed-symlinks compares HEAD to index; we must fix before
that hook runs.

Uses GitPython — no subprocess / shell-out to git.

Requires Windows Developer Mode or Administrator for symlink creation.
Run from repository root.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from git.objects import Blob

GIT_MODE_SYMLINK = 0o120000  # 40960 decimal; GitPython tree items use this


def _ensure_core_symlinks(repo: Repo) -> bool:
    """Set core.symlinks true.

    Returns:
        True if core.symlinks is now true, False on failure.
    """
    try:
        cfg = repo.config_reader()
        val = cfg.get_value("core", "symlinks", True)
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
        if not isinstance(item, Blob):
            continue
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


def _normalize_symlink_target(target: str, symlink_path: Path, repo_root: Path) -> str:
    r"""Normalize an absolute symlink target to a relative path when inside the repo.

    Relative targets are returned unchanged. Absolute targets that resolve to a
    path inside the repo root are converted to a relative path from the symlink's
    parent directory. Absolute targets outside the repo are returned unchanged so
    that external symlinks are preserved as-is.

    The computation uses ``os.path.relpath`` rather than ``Path.relative_to``
    because relpath handles ``..`` traversal correctly for paths that are not
    strict descendants of the symlink's parent.

    Args:
        target: Raw symlink target string read from the Git blob (may use
            ``\\`` separators on Windows — callers should normalise before
            passing if required, but the function also converts ``\\`` → ``/``
            on the returned value for consistency).
        symlink_path: Absolute path of the symlink file on disk (or where it
            will be created). Used as the base for the relative path
            calculation.
        repo_root: Absolute path to the repository root. Used to determine
            whether the target falls inside the repo.

    Returns:
        The (possibly rewritten) symlink target string. Always uses ``/``
        separators. Returns the original *target* unchanged when it is
        already relative or when the resolved target falls outside the repo.
    """
    # Normalise Windows-style separators in the incoming target
    normalised = target.replace("\\", "/")

    if not Path(normalised).is_absolute():
        return normalised

    # Absolute path: resolve relative to repo_root so we can check containment.
    # We do NOT call Path.resolve() here because the target may not exist on
    # disk (e.g. points to a file that hasn't been checked out yet).  Instead
    # we use Path() directly — absolute paths don't need resolution for the
    # containment check.
    abs_target = Path(normalised)
    repo_root_resolved = repo_root.resolve()

    try:
        abs_target.relative_to(repo_root_resolved)
    except ValueError:
        # Target prefix doesn't match the current repo root.  This happens
        # when a symlink was created on a different machine (different home
        # directory, different checkout path).  Recover by finding the repo
        # directory name in the absolute path and treating everything after
        # it as a repo-relative path.
        #
        # Example: target = /home/otheruser/repos/claude_skills/plugins/foo
        #          repo   = /home/user/claude_skills  (name = "claude_skills")
        #          After repo name: plugins/foo
        #          Verify: repo_root / plugins/foo exists → rewrite
        repo_name = repo_root_resolved.name
        parts = abs_target.parts
        found_suffix: str | None = None
        for i, part in enumerate(parts):
            if part == repo_name and i + 1 < len(parts):
                # Everything after the repo name directory is the in-repo path.
                candidate = str(Path(*parts[i + 1 :]))
                if (repo_root_resolved / candidate).exists():
                    found_suffix = candidate
                break  # Only match the first occurrence of the repo name.
        if found_suffix is None:
            # Repo name not found in path, or suffix doesn't exist — external.
            return normalised
        # Rewrite: the real target is repo_root / found_suffix.
        abs_target = repo_root_resolved / found_suffix

    # Target is inside the repo: compute relative path from symlink's parent.
    rel = os.path.relpath(str(abs_target), str(symlink_path.parent))
    return rel.replace("\\", "/")


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
    if not isinstance(blob, Blob):
        return False
    raw_target = _get_symlink_target_from_blob(repo, blob)
    target = _normalize_symlink_target(raw_target, path, repo_root)
    if target != raw_target:
        print(f"repair_symlinks: normalized absolute symlink to relative: {rel} -> {target}", file=sys.stderr)
    if path.is_dir():
        # Path was a symlink in HEAD but is now a directory on disk —
        # intentionally replaced, not a destroyed symlink.
        return True
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


def _find_absolute_symlinks(repo: Repo, repo_root: Path) -> list[Path]:
    """Find existing symlinks in HEAD that have absolute targets.

    Scans all mode 120000 entries in HEAD and returns those that are actual
    symlinks on disk whose target is an absolute path.

    Args:
        repo: The Git repository object.
        repo_root: Absolute path to the repository root.

    Returns:
        List of symlink paths on disk that have absolute targets.
    """
    absolute: list[Path] = []
    head_tree = repo.head.commit.tree
    for item in head_tree.traverse():
        if not isinstance(item, Blob):
            continue
        if item.mode != GIT_MODE_SYMLINK:
            continue
        path = repo_root / item.path
        if path.is_symlink():
            link_target = str(Path(path).readlink())
            if Path(link_target).is_absolute():
                absolute.append(path)
    return absolute


def _normalize_one(path: Path, repo_root: Path) -> bool:
    """Normalize a single existing symlink from absolute to relative.

    Reads the current symlink target, normalizes it via
    ``_normalize_symlink_target``, and recreates the symlink if the target
    changed. Stages the result so the index reflects the new target.

    Args:
        path: Absolute path of the symlink on disk.
        repo_root: Absolute path to the repository root.

    Returns:
        True if the symlink was normalized (or was already fine), False on
        failure.
    """
    raw_target = str(Path(path).readlink())
    target = _normalize_symlink_target(raw_target, path, repo_root)
    if target == raw_target:
        # Still absolute after normalization — genuinely external, skip.
        return True
    rel = path.relative_to(repo_root)
    print(f"repair_symlinks: normalized absolute symlink to relative: {rel} -> {target}", file=sys.stderr)
    path.unlink()
    try:
        path.symlink_to(target)
    except OSError:
        print(f"repair_symlinks: could not recreate symlink for {rel}", file=sys.stderr)
        return False
    return True


def main() -> int:
    """Repair destroyed Git symlinks and normalize absolute targets.

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

    # Phase 1: Repair destroyed symlinks (plain files that should be symlinks).
    destroyed = _find_destroyed_symlinks(repo, repo_root)
    for path in destroyed:
        if not _repair_one(repo, path, repo_root):
            return 1

    # Phase 2: Normalize existing symlinks with absolute targets.
    absolute = _find_absolute_symlinks(repo, repo_root)
    for path in absolute:
        if not _normalize_one(path, repo_root):
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
