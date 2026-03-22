"""DH path constants and resolution.

All path functions return absolute Path objects. Call ensure_dirs() to
create the directory tree before writing files.

Three-tier layout
-----------------
Tier 1 — in-repo project config:
    {project_root}/.dh/              (committed, shared across developers)

Tier 2 — persistent per-project state:
    ~/.dh/projects/{slug}/backlog/
    ~/.dh/projects/{slug}/plan/
    ~/.dh/projects/{slug}/milestones/
    ~/.dh/projects/{slug}/research/

Tier 3 — ephemeral per-session state:
    ~/.dh/projects/{slug}/context/
    ~/.dh/projects/{slug}/reports/

Environment override
--------------------
Set DH_STATE_HOME to relocate all DH state (useful for tests and CI):
    DH_STATE_HOME=/tmp/test-dh uv run ...
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Module-level cache: maps cwd (as str) -> resolved project root Path.
# git_project_root() populates this on first call per cwd.
_root_cache: dict[str, Path] = {}


def git_project_root(cwd: Path | None = None) -> Path:
    """Resolve the main worktree root via git.

    Uses ``git rev-parse --path-format=absolute --git-common-dir`` which
    returns the common git dir (identical to .git/ for main worktrees; the
    shared ``../.git/`` parent for linked worktrees).  The project root is
    the parent of that directory.

    Args:
        cwd: Directory from which to run git.  Defaults to ``Path.cwd()``.

    Returns:
        Absolute path to the project root (main worktree root).

    Raises:
        FileNotFoundError: If the ``git`` binary is not found.
        subprocess.CalledProcessError: If the directory is not inside a
            git repository.
    """
    resolved_cwd = str(cwd or Path.cwd())
    if resolved_cwd in _root_cache:
        return _root_cache[resolved_cwd]

    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=True,
        cwd=resolved_cwd,
    )
    # Strip trailing whitespace / newline from git output.
    git_common_dir = Path(result.stdout.strip())
    # .git/ (or bare common dir) → parent is the project root.
    project_root = git_common_dir.parent
    _root_cache[resolved_cwd] = project_root
    return project_root


def compute_slug(project_root: Path) -> str:
    """Compute project slug from absolute path.

    Algorithm: replace every ``/`` in ``str(project_root)`` with ``-``.
    The leading ``-`` is intentional — it makes slugs visually distinct
    from ordinary directory names and prevents collision with numeric ids.

    Args:
        project_root: Absolute path to the project root.

    Returns:
        Slug string, e.g. ``-home-user-repos-claude_skills``.

    Examples:
        >>> from pathlib import Path
        >>> compute_slug(Path("/home/user/repos/claude_skills"))
        '-home-user-repos-claude_skills'
    """
    return str(project_root).replace("/", "-")


# ---------------------------------------------------------------------------
# Tier 1 — in-repo project config
# ---------------------------------------------------------------------------


def project_dh_dir(project_root: Path | None = None) -> Path:
    """Return ``{project_root}/.dh/`` — committed project config directory.

    Args:
        project_root: Explicit project root.  If ``None``, auto-detected
            via :func:`git_project_root`.

    Returns:
        Absolute path to the in-repo ``.dh/`` directory.
    """
    root = project_root if project_root is not None else git_project_root()
    return root / ".dh"


# ---------------------------------------------------------------------------
# State home — overridable via DH_STATE_HOME
# ---------------------------------------------------------------------------


def _dh_user_root() -> Path:
    """Return the base DH state directory.

    Reads ``DH_STATE_HOME`` environment variable.  If set, returns that
    path; otherwise returns ``~/.dh/``.

    Returns:
        Absolute Path to the DH state home.
    """
    env_override = os.environ.get("DH_STATE_HOME", "")
    if env_override:
        return Path(env_override)
    return Path.home() / ".dh"


# Module-level alias kept for consumers that import the constant directly.
# Re-computed on each access through the function so DH_STATE_HOME overrides
# set after import take effect (important for tests using monkeypatch).
def _get_dh_user_root() -> Path:
    return _dh_user_root()


# ---------------------------------------------------------------------------
# Tier 2 + Tier 3 — per-project state
# ---------------------------------------------------------------------------


def state_root(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/`` — per-project state directory.

    Args:
        project_root: Explicit project root.  If ``None``, auto-detected
            via :func:`git_project_root`.

    Returns:
        Absolute path to the per-project state root.
    """
    root = project_root if project_root is not None else git_project_root()
    slug = compute_slug(root)
    return _dh_user_root() / "projects" / slug


def backlog_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/backlog/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the backlog directory.
    """
    return state_root(project_root) / "backlog"


def plan_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/plan/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the plan directory.
    """
    return state_root(project_root) / "plan"


def milestones_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/milestones/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the milestones directory.
    """
    return state_root(project_root) / "milestones"


def research_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/research/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the research directory.
    """
    return state_root(project_root) / "research"


def context_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/context/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the context (ephemeral session files) directory.
    """
    return state_root(project_root) / "context"


def reports_dir(project_root: Path | None = None) -> Path:
    """Return ``~/.dh/projects/{slug}/reports/``.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        Absolute path to the reports directory.
    """
    return state_root(project_root) / "reports"


# ---------------------------------------------------------------------------
# Directory initialisation
# ---------------------------------------------------------------------------


def ensure_dirs(project_root: Path | None = None) -> Path:
    """Create all Tier 2 and Tier 3 directories if they do not exist.

    Also creates the Tier 1 ``.dh/`` directory and ``.dh/.gitkeep``
    inside the repo.  Idempotent — safe to call multiple times.

    Args:
        project_root: Explicit project root.  Defaults to git auto-detect.

    Returns:
        The resolved :func:`state_root` path.
    """
    root = project_root if project_root is not None else git_project_root()

    # Tier 1 — in-repo config dir
    dh_dir = project_dh_dir(root)
    dh_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = dh_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

    # Tier 2 — persistent state
    for make_dir in (backlog_dir, plan_dir, milestones_dir, research_dir):
        make_dir(root).mkdir(parents=True, exist_ok=True)

    # plan/codebase sub-directory
    (plan_dir(root) / "codebase").mkdir(parents=True, exist_ok=True)

    # Tier 3 — ephemeral state
    for make_dir in (context_dir, reports_dir):
        make_dir(root).mkdir(parents=True, exist_ok=True)

    return state_root(root)


# ---------------------------------------------------------------------------
# Legacy path mapping (migration support)
# ---------------------------------------------------------------------------

LEGACY_PATH_MAP: dict[str, str] = {
    ".claude/backlog": "backlog_dir",
    "plan": "plan_dir",
    ".claude/context": "context_dir",
    ".claude/reports": "reports_dir",
    ".claude/reports/": "reports_dir",
    "plan/": "plan_dir",
    ".claude/backlog/": "backlog_dir",
    ".claude/context/": "context_dir",
}
"""Maps old repo-relative path prefixes to new dh_paths function names.

Used by the migration tool and automated reference-update scripts to
translate legacy path strings to their ``dh_paths`` equivalents.

Example entries::

    ".claude/backlog"  -> "backlog_dir"
    "plan"             -> "plan_dir"
    ".claude/context"  -> "context_dir"
    ".claude/reports"  -> "reports_dir"
"""
