"""Tests for GitLabArtifactProvider — snippet creation, multi-file ops, linking, recovery.

Tests:
- Snippet creation with visibility: private
- Multi-file snippet operations
- Snippet-issue linking via notes
- Recovery mechanism (missing note, scan by name)
- Empty private_token rejection
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from backlog_core.artifact_provider import GitLabArtifactProvider
from backlog_core.models import ArtifactManifest, BacklogError

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    """Provide a temporary directory as the root worktree.

    Tests: Filesystem root for provider under test.
    How: Create plan/ inside tmp_path.
    Why: Provider validates artifact paths against this root.
    """
    (tmp_path / "plan").mkdir()
    return tmp_path


@pytest.fixture
def mock_gitlab_list_notes(mocker: MockerFixture) -> MagicMock:
    """Patch gitlab_list_issue_notes to return no notes by default.

    Tests: GitLab notes API boundary mocking.
    How: Patch backlog_core.artifact_provider.gitlab_list_issue_notes.
    Why: No real HTTP calls; default is empty notes (no snippet linked yet).
    """
    return mocker.patch("backlog_core.artifact_provider.gitlab_list_issue_notes", return_value=[])


@pytest.fixture
def mock_gitlab_create_snippet(mocker: MockerFixture) -> MagicMock:
    """Patch gitlab_create_snippet to return a minimal snippet dict.

    Tests: GitLab snippet creation API mocking.
    How: Patch backlog_core.artifact_provider.gitlab_create_snippet.
    Why: No real HTTP calls; tests inspect call args to verify correct params.
    """
    return mocker.patch(
        "backlog_core.artifact_provider.gitlab_create_snippet",
        return_value={"id": 42, "title": "dh-artifact-manifest-issue-1", "web_url": "https://gitlab.com/..."},
    )


@pytest.fixture
def mock_gitlab_update_snippet(mocker: MockerFixture) -> MagicMock:
    """Patch gitlab_update_snippet to return a minimal snippet dict.

    Tests: GitLab snippet update API mocking.
    How: Patch backlog_core.artifact_provider.gitlab_update_snippet.
    Why: No real HTTP calls; tests inspect call args for correct file actions.
    """
    return mocker.patch(
        "backlog_core.artifact_provider.gitlab_update_snippet",
        return_value={"id": 42, "title": "dh-artifact-manifest-issue-1"},
    )


@pytest.fixture
def mock_gitlab_get_snippet(mocker: MockerFixture) -> MagicMock:
    """Patch gitlab_get_snippet to return a snippet with manifest.json content.

    Tests: GitLab snippet retrieval mocking.
    How: Patch backlog_core.artifact_provider.gitlab_get_snippet.
    Why: get_manifest reads manifest.json from the snippet; mock controls content.
    """
    return mocker.patch(
        "backlog_core.artifact_provider.gitlab_get_snippet",
        return_value={
            "id": 42,
            "title": "dh-artifact-manifest-issue-1",
            "web_url": "https://gitlab.com/...",
            "files_content": {"manifest.json": '{"artifacts": [], "issue_number": 1, "last-updated": ""}'},
        },
    )


@pytest.fixture
def mock_gitlab_create_note(mocker: MockerFixture) -> MagicMock:
    """Patch gitlab_create_issue_note to return a minimal note dict.

    Tests: GitLab note creation API mocking.
    How: Patch backlog_core.artifact_provider.gitlab_create_issue_note.
    Why: _get_or_create_snippet posts a sentinel note; this records call args.
    """
    return mocker.patch(
        "backlog_core.artifact_provider.gitlab_create_issue_note",
        return_value={"id": 7, "body": "<!-- artifact-snippet:42 -->"},
    )


@pytest.fixture
def provider(worktree: Path) -> GitLabArtifactProvider:
    """Return a GitLabArtifactProvider for testing.

    Tests: Provider instance with test credentials.
    How: Construct with project_id=1, private_token="test-token", tmp worktree.
    Why: Combines mocked GitLab API and real filesystem for isolation.
    """
    return GitLabArtifactProvider(project_id=1, private_token="test-token", root_worktree=worktree)


# ---------------------------------------------------------------------------
# Empty private_token rejection
# ---------------------------------------------------------------------------


class TestEmptyPrivateTokenRejection:
    """GitLabArtifactProvider rejects empty private_token at construction time."""

    def test_empty_private_token_raises_value_error(self, worktree: Path) -> None:
        """Constructor raises ValueError when private_token is empty.

        Tests: Fail-fast credential validation.
        How: Instantiate with private_token=""; assert ValueError raised.
        Why: An empty token would succeed at construction but fail at every API call
             with a confusing 401 error — fail fast and loud.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="GITLAB_TOKEN"):
            GitLabArtifactProvider(project_id=1, private_token="", root_worktree=worktree)


# ---------------------------------------------------------------------------
# Snippet creation with visibility: private
# ---------------------------------------------------------------------------


class TestSnippetCreatedPrivate:
    """Snippets are always created with visibility=private."""

    def test_snippet_created_with_private_visibility(
        self,
        provider: GitLabArtifactProvider,
        mock_gitlab_list_notes: MagicMock,
        mock_gitlab_create_snippet: MagicMock,
        mock_gitlab_update_snippet: MagicMock,
        mock_gitlab_create_note: MagicMock,
    ) -> None:
        """set_manifest creates a private snippet when none exists yet.

        Tests: Snippet visibility=private enforcement.
        How: Call set_manifest with an empty manifest (no notes → no snippet);
             inspect the gitlab_create_snippet call.
        Why: DH manifests contain issue metadata and must not be publicly visible.
        """
        # Arrange
        manifest = ArtifactManifest(issue_number=1)

        # Act
        provider.set_manifest(1, manifest)

        # Assert
        mock_gitlab_create_snippet.assert_called_once()
        call_kwargs = mock_gitlab_create_snippet.call_args.kwargs
        visibility = call_kwargs.get("visibility") or mock_gitlab_create_snippet.call_args.args[5]
        assert visibility == "private"


# ---------------------------------------------------------------------------
# Multi-file snippet operations
# ---------------------------------------------------------------------------


class TestMultiFileSnippetOperations:
    """store_artifact_content stores files with sanitized names in the snippet."""

    def test_store_artifact_content_sanitizes_path(
        self,
        provider: GitLabArtifactProvider,
        mock_gitlab_list_notes: MagicMock,
        mock_gitlab_create_snippet: MagicMock,
        mock_gitlab_update_snippet: MagicMock,
        mock_gitlab_create_note: MagicMock,
    ) -> None:
        """store_artifact_content replaces / with -- and appends .txt.

        Tests: Path sanitization for GitLab snippet filenames.
        How: Call store_artifact_content with plan/architect-foo.md; inspect
             gitlab_update_snippet file_path.
        Why: GitLab snippet files may not contain / in the filename; the -- encoding
             and .txt suffix are the canonical representation.
        """
        # Arrange — snippet already exists; update returns error triggering create action
        mock_gitlab_list_notes.return_value = [{"id": 99, "body": "<!-- artifact-snippet:42 -->"}]
        mock_gitlab_get_snippet_local = MagicMock(
            return_value={"id": 42, "title": "t", "web_url": "u", "files_content": {}}
        )

        # Override update to succeed
        mock_gitlab_update_snippet.return_value = {"id": 42}

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("backlog_core.artifact_provider.gitlab_get_snippet", mock_gitlab_get_snippet_local)
            provider.store_artifact_content(1, "architect", "plan/architect-foo.md", "# content")

        # Assert
        mock_gitlab_update_snippet.assert_called()
        call_args = mock_gitlab_update_snippet.call_args
        files = call_args.kwargs.get("files") or call_args.args[4]
        file_paths = [f.get("file_path") for f in files]
        assert "plan--architect-foo.md.txt" in file_paths

    def test_read_artifact_content_from_remote_returns_none_when_no_snippet(
        self, provider: GitLabArtifactProvider, mock_gitlab_list_notes: MagicMock
    ) -> None:
        """read_artifact_content_from_remote returns None when no snippet is linked.

        Tests: No-snippet case returns None, not an error.
        How: Notes list returns no sentinel; assert read_artifact_content_from_remote returns None.
        Why: Returning None allows callers to fall back to local filesystem lookup.
        """
        # Arrange: mock_gitlab_list_notes returns []

        # Act
        result = provider.read_artifact_content_from_remote(1, "architect", "plan/architect-foo.md")

        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# Snippet-issue linking via notes
# ---------------------------------------------------------------------------


class TestSnippetIssueLinking:
    """The snippet sentinel note is posted on the issue after creation."""

    def test_sentinel_note_posted_after_snippet_creation(
        self,
        provider: GitLabArtifactProvider,
        mock_gitlab_list_notes: MagicMock,
        mock_gitlab_create_snippet: MagicMock,
        mock_gitlab_update_snippet: MagicMock,
        mock_gitlab_create_note: MagicMock,
    ) -> None:
        """_get_or_create_snippet posts a sentinel note linking snippet to issue.

        Tests: Sentinel note body contains <!-- artifact-snippet:{id} -->.
        How: Call set_manifest on a fresh issue; inspect gitlab_create_issue_note call.
        Why: The sentinel note is the discovery mechanism — future calls scan notes
             to find the snippet ID without storing it elsewhere.
        """
        # Arrange
        manifest = ArtifactManifest(issue_number=1)

        # Act
        provider.set_manifest(1, manifest)

        # Assert
        mock_gitlab_create_note.assert_called_once()
        note_body = mock_gitlab_create_note.call_args.kwargs.get("body") or mock_gitlab_create_note.call_args.args[4]
        assert note_body == "<!-- artifact-snippet:42 -->"

    def test_sentinel_note_not_posted_when_snippet_already_linked(
        self,
        provider: GitLabArtifactProvider,
        mock_gitlab_list_notes: MagicMock,
        mock_gitlab_update_snippet: MagicMock,
        mock_gitlab_create_note: MagicMock,
        mock_gitlab_get_snippet: MagicMock,
    ) -> None:
        """No new sentinel note when the snippet already exists.

        Tests: Idempotent snippet linkage.
        How: Return a note with a sentinel from list_notes; call set_manifest;
             assert create_note NOT called.
        Why: Creating duplicate sentinel notes would cause the wrong snippet ID to
             be discovered on subsequent calls (first match wins).
        """
        # Arrange — snippet 42 already linked via existing note
        mock_gitlab_list_notes.return_value = [{"id": 1, "body": "<!-- artifact-snippet:42 -->"}]
        manifest = ArtifactManifest(issue_number=1)

        # Act
        provider.set_manifest(1, manifest)

        # Assert — no new note created
        mock_gitlab_create_note.assert_not_called()


# ---------------------------------------------------------------------------
# Recovery mechanism
# ---------------------------------------------------------------------------


class TestRecoveryMechanism:
    """_get_snippet_id_from_notes scans notes each time when no cache entry exists."""

    def test_get_manifest_returns_empty_when_no_notes(
        self, provider: GitLabArtifactProvider, mock_gitlab_list_notes: MagicMock
    ) -> None:
        """get_manifest returns empty manifest when no sentinel note exists.

        Tests: No-snippet recovery path returns empty manifest.
        How: Notes list returns []; assert get_manifest returns ArtifactManifest with no artifacts.
        Why: Fresh issues have no snippet — this is not an error condition.
        """
        # Arrange: mock_gitlab_list_notes returns []

        # Act
        result = provider.get_manifest(1)

        # Assert
        assert result.artifacts == []

    def test_snippet_cache_prevents_repeated_note_scans(
        self, provider: GitLabArtifactProvider, mock_gitlab_list_notes: MagicMock, mock_gitlab_get_snippet: MagicMock
    ) -> None:
        """_snippet_cache prevents repeated list_notes calls for the same issue.

        Tests: In-memory caching of snippet IDs per issue.
        How: Call get_manifest twice for the same issue; assert list_notes called once.
        Why: Each list_notes call costs an API round-trip; caching avoids redundancy.
        """
        # Arrange
        mock_gitlab_list_notes.return_value = [{"id": 1, "body": "<!-- artifact-snippet:42 -->"}]

        # Act — call twice
        provider.get_manifest(1)
        provider.get_manifest(1)

        # Assert — notes scanned only once (second served from cache)
        mock_gitlab_list_notes.assert_called_once()

    def test_api_error_in_list_notes_propagates(
        self, provider: GitLabArtifactProvider, mock_gitlab_list_notes: MagicMock
    ) -> None:
        """BacklogError from gitlab_list_issue_notes propagates from get_manifest.

        Tests: API error propagation from note scan.
        How: Configure list_notes to raise BacklogError; call get_manifest.
        Why: API failures must propagate — silently returning an empty manifest would
             hide a configuration or network problem.
        """
        # Arrange
        mock_gitlab_list_notes.side_effect = BacklogError("GITLAB_TOKEN is invalid or missing")

        # Act / Assert
        with pytest.raises(BacklogError, match="GITLAB_TOKEN"):
            provider.get_manifest(1)
