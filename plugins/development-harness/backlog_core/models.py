"""Constants, regex patterns, type maps, Pydantic models, and exceptions for the backlog MCP package.

This module is standalone — it has no imports from other mcp submodules.
All models use Pydantic BaseModel for natural integration with FastMCP 3.x.
"""

from __future__ import annotations

import functools
import os
import re
from pathlib import Path
from typing import TypedDict

import git
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------


def _resolve_repo_root(project_dir: str | None = None) -> Path:
    """Return the repository root path.

    Args:
        project_dir: Explicit project directory path, typically passed via
            ``--project-dir`` CLI argument when the server is installed as a
            plugin (where ``__file__`` points to the plugin cache, not the
            user's project).  When ``None``, falls back to ``Path.cwd()``
            which is correct for in-repo development.

    Returns:
        Resolved Path to the repository root.
    """
    if project_dir:
        return Path(project_dir).resolve()
    return Path.cwd()


_REPO_ROOT = _resolve_repo_root()
BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"


def init(project_dir: str | None = None, repo: str | None = None) -> None:
    """Re-initialise module-level path and repository constants.

    Call this once at server startup (before any tool runs) when the server is
    launched with ``--project-dir`` or a known ``repo`` slug.  Mutates module
    globals ``_REPO_ROOT``, ``BACKLOG_DIR``, and ``DEFAULT_REPO`` in-place.

    Args:
        project_dir: Absolute path to the user's project root, forwarded from
            the ``--project-dir`` CLI argument in ``server.py``.
        repo: Explicit ``owner/repo`` slug override.  When ``None``, calls
            :func:`discover_repo` to resolve the slug dynamically.
    """
    global _REPO_ROOT, BACKLOG_DIR, DEFAULT_REPO  # noqa: PLW0603
    _REPO_ROOT = _resolve_repo_root(project_dir)
    BACKLOG_DIR = _REPO_ROOT / ".claude" / "backlog"
    if repo is not None:
        DEFAULT_REPO = _validate_repo_slug(repo)
    else:
        discover_repo.cache_clear()
        DEFAULT_REPO = discover_repo()


# ---------------------------------------------------------------------------
# Repository discovery
# ---------------------------------------------------------------------------

#: Matches the canonical ``owner/repo`` slug format.
_REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

#: SSH SCP remote pattern: ``git@github.com:owner/repo.git``
_SSH_REMOTE_RE = re.compile(r"git@[^:]+:([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$")

#: HTTPS / proxy remote pattern: ``https://…/owner/repo[.git]``
_HTTPS_REMOTE_RE = re.compile(r"https?://[^/]+/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$")

#: SSH protocol remote pattern: ``ssh://git@github.com/owner/repo.git``
_SSH_PROTO_REMOTE_RE = re.compile(r"ssh://[^/]+/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?$")

#: Proxy remote pattern: ``http://local_proxy@127.0.0.1:{port}/git/{owner}/{repo}``
#: Matches any host/port proxy URL with a ``/git/`` path prefix.
_PROXY_REMOTE_RE = re.compile(r".*/git/([^/]+/[^/]+?)(?:\.git)?/?$")


class RepoDiscoveryError(Exception):
    """Raised when all repository discovery methods fail.

    Attributes:
        methods_tried: Names of the discovery methods attempted in order.
        message: User-facing actionable error message.
    """

    def __init__(self, methods_tried: list[str], details: list[str]) -> None:
        """Initialise with discovery context.

        Args:
            methods_tried: Method names tried in order.
            details: Per-method failure descriptions.
        """
        self.methods_tried = methods_tried
        detail_lines = "\n".join(f"  {i + 1}. {d}" for i, d in enumerate(details))
        message = (
            "Could not determine the GitHub repository.\n\n"
            f"Tried:\n{detail_lines}\n\n"
            "To fix, either:\n"
            "  - Set GITHUB_REPO=owner/repo in your environment\n"
            "  - Ensure you are in a git repository with a GitHub remote"
        )
        self.message = message
        super().__init__(message)


def _validate_repo_slug(slug: str) -> str:
    """Validate that *slug* matches ``owner/repo`` format.

    Args:
        slug: Candidate repository slug to validate.

    Returns:
        The validated slug, unchanged.

    Raises:
        RepoDiscoveryError: When the slug does not match the expected format.
    """
    if not _REPO_SLUG_RE.match(slug):
        raise RepoDiscoveryError(
            methods_tried=["validate"], details=[f"Slug '{slug}' does not match owner/repo format"]
        )
    return slug


def _discover_via_env() -> str | None:
    """Return the ``GITHUB_REPO`` environment variable value if set and valid.

    Returns:
        Validated ``owner/repo`` slug, or ``None`` when the variable is absent
        or empty.
    """
    value = os.environ.get("GITHUB_REPO", "").strip()
    if not value:
        return None
    return _validate_repo_slug(value)


def _discover_via_git() -> str | None:
    """Parse the ``origin`` remote URL via GitPython to extract ``owner/repo``.

    Uses :class:`git.Repo` with ``search_parent_directories=True`` to locate
    the repository, then reads the ``origin`` remote URL and applies regex
    patterns for SSH SCP, SSH protocol, and HTTPS URL formats.

    Returns:
        Validated ``owner/repo`` slug, or ``None`` when no git repository is
        found, there is no ``origin`` remote, or the URL cannot be parsed.
    """
    try:
        repo = git.Repo(search_parent_directories=True)
        url = repo.remote().url
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, ValueError):
        return None
    for pattern in (_SSH_REMOTE_RE, _HTTPS_REMOTE_RE, _SSH_PROTO_REMOTE_RE, _PROXY_REMOTE_RE):
        match = pattern.match(url)
        if match:
            slug = match.group(1)
            if _REPO_SLUG_RE.match(slug):
                return slug
    return None


@functools.lru_cache(maxsize=1)
def discover_repo() -> str:
    """Discover the current repository's ``owner/repo`` slug.

    Resolution priority chain (first success wins):

    1. ``GITHUB_REPO`` environment variable — explicit override, highest priority.
    2. GitPython remote URL parsing — reads the ``origin`` remote URL from the
       git repository and parses owner/repo using regex patterns for SSH SCP,
       SSH protocol, and HTTPS URL formats.
    3. :class:`RepoDiscoveryError` — all methods exhausted, no fallback.

    The result is cached with :func:`functools.lru_cache` so discovery runs at
    most once per process.  Call ``discover_repo.cache_clear()`` in tests to
    reset between runs.

    Returns:
        Repository slug in ``owner/repo`` format.

    Raises:
        RepoDiscoveryError: When no discovery method succeeds.
    """
    methods_tried: list[str] = []
    details: list[str] = []

    # 1. Environment variable
    methods_tried.append("GITHUB_REPO environment variable")
    slug = _discover_via_env()
    if slug is not None:
        return slug
    details.append("GITHUB_REPO environment variable: not set or empty")

    # 2. GitPython remote URL parsing
    methods_tried.append("Git remote (origin) via GitPython")
    slug = _discover_via_git()
    if slug is not None:
        return slug
    details.append("Git remote (origin): no git repository found or URL could not be parsed")

    raise RepoDiscoveryError(methods_tried=methods_tried, details=details)


#: Populated at server startup by :func:`init`. Not set at import time to avoid
#: triggering git I/O during module import. Call :func:`discover_repo` directly
#: when a default is needed before ``init()`` has run.
DEFAULT_REPO: str = ""

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(r"^##\s+(P0|P1|P2|Ideas)")
GITHUB_ISSUE_URL_RE = re.compile(r"https?://github\.com/([^/]+/[^/]+)/issues/(\d+)")
COMMIT_PREFIX_RE = re.compile(r"^(feat|fix|refactor|docs|chore|perf|test|ci):\s*", re.IGNORECASE)
_COMMIT_PREFIX_RE = COMMIT_PREFIX_RE  # backwards-compat alias; import COMMIT_PREFIX_RE in new code

# ---------------------------------------------------------------------------
# Scalar constants
# ---------------------------------------------------------------------------

SKIP_STATUS = ("DONE", "RESOLVED", "COMPLETED", "CLOSED")

VALID_CLOSE_REASONS = ("duplicate", "out_of_scope", "superseded", "wontfix", "blocked")
GITHUB_ISSUE_TITLE_TRUNCATE = 80
MIN_FRONTMATTER_PARTS = 3
FUZZY_DUPLICATE_THRESHOLD = 0.80

# ---------------------------------------------------------------------------
# Dict mappings
# ---------------------------------------------------------------------------

TYPE_TO_LABEL: dict[str, str] = {
    "feature": "type:feature",
    "bug": "type:bug",
    "refactor": "type:refactor",
    "docs": "type:docs",
    "chore": "type:chore",
}

ROLE_MAP: dict[str, str] = {
    "Feature": "developer using Claude Code skills",
    "Bug": "developer relying on this plugin",
    "Refactor": "maintainer of the codebase",
    "Docs": "developer reading the documentation",
    "Chore": "maintainer of the project infrastructure",
}

BENEFIT_MAP: dict[str, str] = {
    "Feature": "the tooling becomes more capable and complete",
    "Bug": "the tool works correctly and reliably",
    "Refactor": "the code is cleaner and more maintainable",
    "Docs": "documentation is accurate and trustworthy",
    "Chore": "the project infrastructure stays healthy",
}

FIELD_TO_INDEX: dict[str, int] = {
    "description": 0,
    "suggested location": 1,
    "research first": 2,
    "decision needed": 3,
    "files": 4,
    "required work": 5,
}

PRIORITY_SECTIONS: dict[str, str] = {
    "P0": "## P0 - Must Have",
    "P1": "## P1 - Should Have",
    "P2": "## P2 - Could Have",
    "Idea": "## Ideas",
    "Ideas": "## Ideas",
}

# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------


class BacklogError(Exception):
    """General backlog operation error."""


class ItemNotFoundError(BacklogError):
    """Raised when a backlog item cannot be found by the given selector."""

    def __init__(self, selector: str) -> None:
        """Initialize with the selector that failed to match."""
        self.selector = selector
        super().__init__(f"No item found for: {selector}")


class DuplicateItemError(BacklogError):
    """Raised when a fuzzy duplicate is detected during item creation."""

    def __init__(self, duplicates: list[tuple[str, float, str]]) -> None:
        """Initialize with list of (title, similarity_ratio, file_path) tuples."""
        self.duplicates = duplicates
        titles = ", ".join(f'"{t}" ({int(r * 100)}%)' for t, r, _ in duplicates)
        super().__init__(f"Similar backlog items found: {titles}")


class GitHubUnavailableError(BacklogError):
    """Raised when GITHUB_TOKEN is missing or the GitHub API is unreachable."""


class ValidationError(BacklogError):
    """Raised on input validation failure."""


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Entry(BaseModel):
    """A single timestamped content block within a backlog item section."""

    id: str = ""
    content: str = ""
    struck: bool = False
    struck_reason: str = ""
    struck_at: str = ""
    raw: str = ""


class BacklogItem(BaseModel):
    """Parsed backlog item from a per-item file.

    Replaces the untyped ``dict`` that was previously passed between functions.
    All fields default to empty/falsy values so items can be constructed
    incrementally during parsing.
    """

    title: str = ""
    description: str = ""
    source: str = "Not specified"
    added: str = ""
    priority: str = ""
    item_type: str = "Feature"
    issue: str = ""
    plan: str = ""
    research_first: str = ""
    files: str = ""
    suggested_location: str = ""

    type_: str = ""
    topic: str = ""

    section: str = ""
    file_path: str = ""
    skip: bool = False
    status: str = ""
    groomed: str = ""
    last_synced: str = ""
    raw_body: str = ""


class Output(BaseModel):
    """Structured output collector replacing direct typer.echo() calls.

    Functions that need to communicate status messages take an optional
    ``output: Output | None = None`` parameter. The CLI wrapper prints
    messages; the MCP server returns them in the response dict.
    """

    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def info(self, msg: str) -> None:
        """Record an informational message."""
        self.messages.append(msg)

    def warn(self, msg: str) -> None:
        """Record a warning message."""
        self.warnings.append(msg)

    def error(self, msg: str) -> None:
        """Record an error message."""
        self.errors.append(msg)

    def to_dict(self) -> dict[str, list[str]]:
        """Return all collected messages as a dict (alias for model_dump)."""
        return self.model_dump()


class SamTasksResult(TypedDict):
    """Return type for ``get_sam_tasks``."""

    tasks: list[dict[str, object]]
    count: int
    parent_issue_number: int
    messages: list[str]
    warnings: list[str]
    errors: list[str]


class IssueStatus(BaseModel):
    """GitHub issue status and milestone from batch fetch."""

    status: str = ""
    milestone: str = ""


class PullRequestRef(BaseModel):
    """Reference to an open pull request."""

    number: int
    title: str
    url: str


class ViewItemResult(BaseModel):
    """Result of viewing a single backlog item, optionally enriched with GitHub data."""

    title: str = ""
    priority: str = ""
    description: str = ""
    source: str = ""
    added: str = ""
    plan: str = ""
    issue: str = ""
    file_path: str = ""
    groomed: bool = False
    status: str = ""
    number: int | None = None
    state: str = ""
    body: str = ""
    labels: list[str] = Field(default_factory=list)
    milestone: str = ""
    sections: dict[str, dict[str, object]] = Field(default_factory=dict)


class IssueLocalFields(BaseModel):
    """Backlog-relevant fields extracted from a PyGithub Issue object."""

    title: str = ""
    body: str = ""
    priority: str = "P1"
    item_type: str = "Feature"
    status: str = "open"
    updated_at: str = ""
    milestone: str = ""


class SamTask(BaseModel):
    """SAM task metadata stored in the ``<!-- sam:task ... -->`` block of a GitHub issue body.

    Title format: ``[{feature}/{task_id}] {task_type}: {description}``
    Body block:   invisible HTML comment containing YAML fields below.
    """

    task_id: str = ""
    """Feature-scoped sequential ID, e.g. "T1", "T2"."""

    feature: str = ""
    """Feature slug, e.g. "uv-skill-update"."""

    task_type: str = ""
    """Execution category: "research" | "implement" | "review" | "fix" | "docs"."""

    status: str = "not-started"
    """Execution state: "not-started" | "in-progress" | "complete" | "blocked"."""

    agent: str = ""
    """Agent name to execute the task, e.g. "context-gathering"."""

    priority: int = 2
    """Execution priority 1-5 (1 = highest)."""

    skills: list[str] = Field(default_factory=list)
    """Skill names the executing agent should load."""

    dependencies: list[str] = Field(default_factory=list)
    """Feature-scoped task IDs this task depends on, e.g. ["T1", "T2"].
    Cross-feature deps use GitHub issue numbers: ["#479"]."""
