"""Backend abstraction for artifact manifest storage.

Defines the ``ArtifactBackend`` protocol and the ``GitHubArtifactProvider``
implementation that stores manifest data in GitHub Issue bodies.

The manifest is stored as a markdown table delimited by HTML comment markers
inside the issue body, making it human-readable when browsing GitHub and
machine-parseable by the MCP tools.

Manifest section format in issue body::

    ## Artifact Manifest

    <!-- artifact-manifest:begin -->
    | Type | Path | Status | Agent | Created |
    |------|------|--------|-------|---------|
    | feature-context | plan/feature-context-foo.md | current | feature-researcher | 2026-03-21T10:00:00Z |
    <!-- artifact-manifest:end -->

Note on T3 dependency:
    The ``parse_manifest_section``, ``render_manifest_section``, and
    ``replace_manifest_in_body`` helpers are implemented here so that T2
    compiles and runs independently of T3.  Once T3 creates
    ``artifact_registry.py``, those helpers will be consolidated there and
    this module will import them via::

        from .artifact_registry import parse_manifest_section, render_manifest_section, replace_manifest_in_body
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from .github import _graphql_request, get_github
from .models import ArtifactEntry, ArtifactManifest, ArtifactStatus, ArtifactType

# ---------------------------------------------------------------------------
# Manifest section constants
# ---------------------------------------------------------------------------

_MANIFEST_BEGIN = "<!-- artifact-manifest:begin -->"
_MANIFEST_END = "<!-- artifact-manifest:end -->"

_MANIFEST_HEADER = "## Artifact Manifest"

#: Regex that matches the complete manifest section including delimiters.
_MANIFEST_SECTION_RE = re.compile(r"<!-- artifact-manifest:begin -->.*?<!-- artifact-manifest:end -->", re.DOTALL)

#: Number of columns in the markdown table (Type | Path | Status | Agent | Created).
_TABLE_COLUMN_COUNT = 5

# ---------------------------------------------------------------------------
# Manifest section parse / render helpers
# ---------------------------------------------------------------------------
# These helpers are intentionally placed here so that artifact_provider.py is
# self-contained until T3 (artifact_registry.py) is implemented.  T3 will
# extract them into artifact_registry.py and replace this implementation with
# a sibling-module import.


def _parse_table_row(row: str) -> ArtifactEntry | None:
    """Parse one markdown table row into an ArtifactEntry, or return None.

    Args:
        row: A single markdown table row string, e.g.
            ``"| feature-context | plan/fc.md | current | agent | 2026… |"``.

    Returns:
        Parsed ``ArtifactEntry``, or ``None`` when the row is a header,
        separator, or otherwise unparseable.
    """
    stripped = row.strip()
    if not stripped.startswith("|"):
        return None
    cells = [c.strip() for c in stripped.strip("|").split("|")]
    if len(cells) < _TABLE_COLUMN_COUNT:
        return None
    type_cell, path_cell, status_cell, agent_cell, created_cell = (cells[0], cells[1], cells[2], cells[3], cells[4])
    # Skip header row ("Type") and separator row ("---")
    if type_cell.lower() in {"type", "---", "------"} or type_cell.startswith("-"):
        return None
    try:
        artifact_type = ArtifactType(type_cell)
    except ValueError:
        return None
    try:
        status = ArtifactStatus(status_cell)
    except ValueError:
        status = ArtifactStatus.CURRENT
    return ArtifactEntry(
        artifact_type=artifact_type, path=path_cell, status=status, created_at=created_cell, agent=agent_cell
    )


def parse_manifest_section(issue_body: str, issue_number: int) -> ArtifactManifest:
    """Extract and parse the artifact manifest section from an issue body.

    Returns an empty ``ArtifactManifest`` when no manifest section is found —
    this is not an error condition; it simply means no artifacts have been
    registered yet.

    Args:
        issue_body: Full GitHub Issue body text.
        issue_number: Issue number for the returned manifest object.

    Returns:
        ``ArtifactManifest`` parsed from the delimited section, or an empty
        manifest when the section is absent.
    """
    match = _MANIFEST_SECTION_RE.search(issue_body)
    if not match:
        return ArtifactManifest(issue_number=issue_number)

    section = match.group(0)
    artifacts: list[ArtifactEntry] = []
    for line in section.splitlines():
        entry = _parse_table_row(line)
        if entry is not None:
            artifacts.append(entry)
    return ArtifactManifest(issue_number=issue_number, artifacts=artifacts)


def render_manifest_section(manifest: ArtifactManifest) -> str:
    """Render an ``ArtifactManifest`` as a delimited markdown section.

    Produces the complete section including the heading, HTML comment
    delimiters, and markdown table.

    Args:
        manifest: The manifest to render.

    Returns:
        Multi-line string with heading, begin delimiter, table, end delimiter.
    """
    header_row = "| Type | Path | Status | Agent | Created |"
    separator_row = "|------|------|--------|-------|---------|"
    rows = [header_row, separator_row]
    rows.extend(
        f"| {entry.artifact_type} | {entry.path} | {entry.status} | {entry.agent} | {entry.created_at} |"
        for entry in manifest.artifacts
    )
    table = "\n".join(rows)
    return f"{_MANIFEST_HEADER}\n\n{_MANIFEST_BEGIN}\n{table}\n{_MANIFEST_END}"


def replace_manifest_in_body(issue_body: str, rendered_section: str) -> str:
    """Replace the manifest section in an issue body, or append it if absent.

    Preserves all content outside the manifest section.  When no section
    exists the rendered section is appended with a preceding blank line.

    Args:
        issue_body: Current full issue body text.
        rendered_section: New manifest section produced by
            :func:`render_manifest_section`.

    Returns:
        Updated issue body with the manifest section inserted or replaced.
    """
    if _MANIFEST_SECTION_RE.search(issue_body):
        # Replace both the heading (if immediately before the begin delimiter)
        # and the delimited block in one pass.
        heading_and_section_re = re.compile(
            r"##\s+Artifact Manifest\s*\n\s*\n?" + re.escape(_MANIFEST_BEGIN) + r".*?" + re.escape(_MANIFEST_END),
            re.DOTALL,
        )
        if heading_and_section_re.search(issue_body):
            return heading_and_section_re.sub(rendered_section, issue_body)
        # Fallback: replace only the delimited block (heading may be elsewhere)
        return _MANIFEST_SECTION_RE.sub(
            f"{_MANIFEST_BEGIN}\n{_extract_table_from_rendered(rendered_section)}\n{_MANIFEST_END}", issue_body
        )
    return issue_body.rstrip() + "\n\n" + rendered_section + "\n"


def _extract_table_from_rendered(rendered: str) -> str:
    """Return just the table rows from a rendered section (without heading or delimiters).

    Args:
        rendered: Output of :func:`render_manifest_section`.

    Returns:
        Lines between the begin and end delimiters.
    """
    lines = rendered.splitlines()
    inside = False
    table_lines: list[str] = []
    for line in lines:
        if _MANIFEST_BEGIN in line:
            inside = True
            continue
        if _MANIFEST_END in line:
            break
        if inside:
            table_lines.append(line)
    return "\n".join(table_lines)


# ---------------------------------------------------------------------------
# ArtifactBackend Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ArtifactBackend(Protocol):
    """Protocol defining the storage contract for artifact manifest backends.

    Implementations store and retrieve ``ArtifactManifest`` objects from a
    backend (GitHub Issue body, database, local file, etc.) and serve
    artifact file content for MCP consumers.

    All methods are synchronous.  The MCP tool layer wraps calls in
    ``asyncio.to_thread()`` when needed.
    """

    def get_manifest(self, issue_number: int) -> ArtifactManifest:
        """Retrieve the artifact manifest for *issue_number*.

        Args:
            issue_number: GitHub Issue number (positive integer).

        Returns:
            ``ArtifactManifest`` for the issue.  Returns an empty manifest
            (no artifacts) when the issue has no manifest section — this is
            not an error.
        """
        ...

    def set_manifest(self, issue_number: int, manifest: ArtifactManifest) -> None:
        """Persist *manifest* for *issue_number*.

        Replaces any existing manifest section; creates one if absent.

        Args:
            issue_number: GitHub Issue number (positive integer).
            manifest: Updated manifest to persist.
        """
        ...

    def read_artifact_content(self, path: str) -> str:
        """Read artifact file content from the root worktree.

        Args:
            path: Repo-relative path to the artifact file (e.g.
                ``plan/architect-foo.md``).  Must start with ``plan/`` and
                must not escape the repository root.

        Returns:
            Raw UTF-8 file content.

        Raises:
            ValueError: When *path* fails the safety checks (path traversal
                or non-plan path).
            FileNotFoundError: When the file does not exist in the root
                worktree (cache miss — the artifact is registered but not yet
                committed or was deleted).
        """
        ...


# ---------------------------------------------------------------------------
# GitHubArtifactProvider
# ---------------------------------------------------------------------------


class GitHubArtifactProvider:
    """GitHub-backed implementation of :class:`ArtifactBackend`.

    Reads and writes the artifact manifest section inside GitHub Issue bodies
    using the existing PyGithub + GraphQL helpers from ``backlog_core.github``.
    No new credentials are required — the same ``GITHUB_TOKEN`` used by other
    backlog operations is reused.

    Artifact file content is served directly from the local ``root_worktree``
    filesystem path.  Worktree-isolated agents access content via the
    ``artifact_read`` MCP tool rather than the filesystem.

    Args:
        repo: GitHub repository slug in ``owner/name`` format.
        root_worktree: Absolute path to the root git worktree (the repository
            checkout that has all committed and uncommitted plan files).
            Defaults to ``Path.cwd()`` when not provided.

    Example::

        provider = GitHubArtifactProvider(repo="owner/myrepo", root_worktree=Path("/home/user/repos/myrepo"))
        manifest = provider.get_manifest(965)
        print(manifest.artifacts)
    """

    def __init__(self, repo: str, root_worktree: Path | None = None) -> None:
        """Initialise provider with GitHub repository slug and worktree path.

        Args:
            repo: ``owner/name`` repository slug.
            root_worktree: Absolute path to the root git worktree.  When
                ``None``, ``Path.cwd()`` is used (correct for in-repo
                development where the server runs from the project root).
        """
        self._repo = repo
        self._root_worktree = root_worktree or Path.cwd()

    # ------------------------------------------------------------------
    # ArtifactBackend implementation
    # ------------------------------------------------------------------

    def get_manifest(self, issue_number: int) -> ArtifactManifest:
        """Retrieve the artifact manifest from the GitHub Issue body.

        Fetches the issue body via PyGithub REST, then extracts and parses
        the ``<!-- artifact-manifest:begin/end -->`` section.  Returns an
        empty manifest when the section is absent.

        Args:
            issue_number: GitHub Issue number (positive integer).

        Returns:
            Parsed ``ArtifactManifest``.  Empty (no artifacts) when the
            issue body contains no manifest section.

        Raises:
            backlog_core.models.GitHubUnavailableError: When ``GITHUB_TOKEN``
                is not set.
            github.GithubException: On GitHub API failures.
        """
        repo_obj = get_github(self._repo)
        issue = repo_obj.get_issue(issue_number)
        body = issue.body or ""
        return parse_manifest_section(body, issue_number)

    def set_manifest(self, issue_number: int, manifest: ArtifactManifest) -> None:
        """Persist the manifest by updating the GitHub Issue body.

        Renders the manifest as a markdown table, then replaces the existing
        manifest section in the issue body (or appends it if absent) via a
        PyGithub ``issue.edit(body=...)`` call.

        Args:
            issue_number: GitHub Issue number (positive integer).
            manifest: Updated manifest to persist.

        Raises:
            backlog_core.models.GitHubUnavailableError: When ``GITHUB_TOKEN``
                is not set.
            github.GithubException: On GitHub API failures.
        """
        repo_obj = get_github(self._repo)
        issue = repo_obj.get_issue(issue_number)
        current_body = issue.body or ""

        # Stamp last_updated before rendering
        manifest = manifest.model_copy(update={"last_updated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")})
        rendered = render_manifest_section(manifest)
        new_body = replace_manifest_in_body(current_body, rendered)

        if new_body != current_body:
            issue.edit(body=new_body)

    def read_artifact_content(self, path: str) -> str:
        """Read artifact file content from the root worktree filesystem.

        Validates that *path*:

        1. Does not contain ``..`` components (path traversal prevention).
        2. Starts with ``plan/`` (only plan artifacts are accessible).
        3. When resolved, is under the repository root (double-check after
           ``Path.resolve()``).

        Args:
            path: Repo-relative path to the artifact file, e.g.
                ``plan/architect-foo.md``.

        Returns:
            Raw UTF-8 file content.

        Raises:
            ValueError: When *path* fails the safety checks.
            FileNotFoundError: When the resolved file does not exist.
        """
        self._validate_artifact_path(path)
        resolved = (self._root_worktree / path).resolve()
        return resolved.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Path safety helpers
    # ------------------------------------------------------------------

    def _validate_artifact_path(self, path: str) -> None:
        """Raise ``ValueError`` when *path* fails the safety checks.

        Two checks are applied:

        - The repo-relative path must start with ``plan/`` to prevent access
          to arbitrary files outside the plan directory.
        - After resolution the absolute path must be a descendant of
          ``self._root_worktree`` to prevent path traversal (``..``).

        Args:
            path: Repo-relative path string as provided by the caller.

        Raises:
            ValueError: When either safety check fails.
        """
        if not path.startswith("plan/"):
            raise ValueError(
                f"Artifact path must start with 'plan/' — got {path!r}. "
                "Only plan artifacts are accessible via artifact_read."
            )
        # Resolve the candidate path and check it stays under root_worktree.
        candidate = (self._root_worktree / path).resolve()
        try:
            candidate.relative_to(self._root_worktree.resolve())
        except ValueError:
            raise ValueError(f"Path traversal detected: {path!r} resolves outside the repository root.") from None


# ---------------------------------------------------------------------------
# GraphQL-backed variant (optional — used when issue.edit() is rate-limited)
# ---------------------------------------------------------------------------


def _build_update_issue_body_mutation() -> str:
    """Return the GraphQL mutation string for updating an issue body.

    Returns:
        GraphQL mutation string that accepts ``$id`` (node ID) and
        ``$body`` (new body text) variables.
    """
    return """
mutation UpdateIssueBody($id: ID!, $body: String!) {
  updateIssue(input: {id: $id, body: $body}) {
    issue {
      id
      number
    }
  }
}"""


def _update_issue_body_graphql(repo_obj: object, issue_node_id: str, new_body: str) -> None:
    """Update an issue body via GraphQL mutation.

    Provided as an alternative to ``issue.edit(body=...)`` for callers that
    already hold the issue node ID from a prior GraphQL query and want to
    avoid the extra REST round-trip.

    Args:
        repo_obj: PyGithub ``Repository`` object (provides requester access).
        issue_node_id: GitHub GraphQL node ID of the issue (e.g. ``"I_kwDO…"``).
        new_body: Full new body text for the issue.

    Raises:
        backlog_core.models.BacklogError: On GraphQL errors.
    """
    mutation = _build_update_issue_body_mutation()
    _graphql_request(repo_obj, mutation, {"id": issue_node_id, "body": new_body})  # type: ignore[arg-type]
