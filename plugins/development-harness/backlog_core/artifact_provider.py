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

Parse/render helpers are consolidated in :mod:`backlog_core.artifact_registry`.
This module imports them from there.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .artifact_registry import parse_manifest_section, render_manifest_section, replace_manifest_in_body
from .github import _graphql_request, get_github

if TYPE_CHECKING:
    from .models import ArtifactManifest

# Re-export so callers that imported these from artifact_provider continue to work.
__all__ = [
    "ArtifactBackend",
    "GitHubArtifactProvider",
    "parse_manifest_section",
    "render_manifest_section",
    "replace_manifest_in_body",
]

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
