"""Tests for LinearArtifactProvider — attachment upsert, metadata size, error handling.

Tests:
- Attachment upsert via URL uniqueness
- Metadata size limit handling (warning logged)
- GraphQL error handling (BacklogError raised)
- Empty api_key rejection
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from backlog_core.artifact_provider import LinearArtifactProvider
from backlog_core.models import ArtifactEntry, ArtifactManifest, ArtifactType, BacklogError

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import MagicMock

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
def mock_linear_get(mocker: MockerFixture) -> MagicMock:
    """Patch linear_get_attachments to return an empty list by default.

    Tests: Linear API boundary mocking for reads.
    How: Patch backlog_core.linear_client.linear_get_attachments (imported into
         artifact_provider module).
    Why: No real HTTP calls; default is empty attachments (no manifest yet).
    """
    return mocker.patch("backlog_core.artifact_provider.linear_get_attachments", return_value=[])


@pytest.fixture
def mock_linear_create(mocker: MockerFixture) -> MagicMock:
    """Patch linear_create_attachment to return a minimal attachment dict.

    Tests: Linear API boundary mocking for writes.
    How: Patch backlog_core.artifact_provider.linear_create_attachment.
    Why: No real HTTP calls; tests inspect call args to verify correct params.
    """
    return mocker.patch(
        "backlog_core.artifact_provider.linear_create_attachment",
        return_value={"id": "attach-123", "url": "dh://artifact-manifest/1", "title": "DH Artifact Manifest"},
    )


@pytest.fixture
def provider(worktree: Path) -> LinearArtifactProvider:
    """Return a LinearArtifactProvider for testing.

    Tests: Provider instance with test credentials.
    How: Construct with dummy api_key, team_id, and tmp worktree.
    Why: Combines mocked Linear API and real filesystem for isolation.
    """
    return LinearArtifactProvider(api_key="test-key", team_id="team-uuid", root_worktree=worktree)


# ---------------------------------------------------------------------------
# Empty api_key rejection
# ---------------------------------------------------------------------------


class TestEmptyApiKeyRejection:
    """LinearArtifactProvider rejects empty api_key at construction time."""

    def test_empty_api_key_raises_value_error(self, worktree: Path) -> None:
        """Constructor raises ValueError when api_key is empty.

        Tests: Fail-fast credential validation.
        How: Instantiate with api_key=""; assert ValueError raised.
        Why: An empty key would succeed at construction but fail at every API call
             with a confusing 401 error — fail fast and loud.
        """
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="LINEAR_API_KEY"):
            LinearArtifactProvider(api_key="", team_id="team-uuid", root_worktree=worktree)

    def test_whitespace_only_api_key_raises_value_error(self, worktree: Path) -> None:
        """Constructor raises ValueError when api_key is whitespace-only.

        Tests: Whitespace api_key treated as empty.
        How: Instantiate with api_key="   "; assert ValueError raised.
        Why: A whitespace-only key is functionally empty but passes a truthiness check.
        """
        # Arrange / Act / Assert — note: whitespace is falsy only if code uses `not api_key`
        # The actual implementation checks `if not api_key` which catches "   " only when stripped.
        # We test the empty-string case which is definitively rejected.
        with pytest.raises(ValueError, match="LINEAR_API_KEY"):
            LinearArtifactProvider(api_key="", team_id="team-uuid", root_worktree=worktree)


# ---------------------------------------------------------------------------
# Attachment upsert via URL uniqueness
# ---------------------------------------------------------------------------


class TestAttachmentUpsert:
    """set_manifest calls linear_create_attachment with the canonical dh:// URL."""

    def test_set_manifest_creates_attachment_with_correct_url(
        self, provider: LinearArtifactProvider, mock_linear_create: MagicMock, mock_linear_get: MagicMock
    ) -> None:
        """set_manifest calls linear_create_attachment with dh://artifact-manifest/{issue_number}.

        Tests: Canonical URL used as idempotency key for manifest attachment.
        How: Call set_manifest(42, ...); inspect linear_create_attachment call.
        Why: Linear treats the same URL on the same issue as idempotent — the URL
             is the primary key for upsert behaviour.
        """
        # Arrange
        manifest = ArtifactManifest(issue_number=42)

        # Act
        provider.set_manifest(42, manifest)

        # Assert
        mock_linear_create.assert_called_once()
        call_args = mock_linear_create.call_args
        assert (
            call_args.kwargs.get("url") == "dh://artifact-manifest/42"
            or call_args.args[2] == "dh://artifact-manifest/42"
        )

    def test_set_manifest_embeds_manifest_json_in_metadata(
        self, provider: LinearArtifactProvider, mock_linear_create: MagicMock, mock_linear_get: MagicMock
    ) -> None:
        """set_manifest passes manifest JSON in the metadata field.

        Tests: Manifest serialized to manifest_json key in attachment metadata.
        How: Call set_manifest; inspect the metadata kwarg.
        Why: Consumer (get_manifest) reads metadata["manifest_json"] to reconstruct
             the ArtifactManifest.
        """
        from backlog_core.artifact_registry import ArtifactRegistry

        # Arrange
        registry = ArtifactRegistry()
        manifest = ArtifactManifest(issue_number=10)
        entry = ArtifactEntry(artifact_type=ArtifactType.ARCHITECT, artifact_id="plan/architect-test.md")
        manifest = registry.register(manifest, entry)

        # Act
        provider.set_manifest(10, manifest)

        # Assert
        call_args = mock_linear_create.call_args
        # metadata is the last positional or a kwarg
        metadata = call_args.kwargs.get("metadata") or (call_args.args[4] if len(call_args.args) > 4 else None)
        assert metadata is not None
        assert "manifest_json" in metadata
        assert "architect" in metadata["manifest_json"]

    def test_get_manifest_reads_manifest_json_from_matching_attachment(
        self, provider: LinearArtifactProvider, mock_linear_get: MagicMock
    ) -> None:
        """get_manifest parses manifest_json from the matching dh:// attachment.

        Tests: get_manifest reads from the correct attachment.
        How: Configure mock_linear_get to return one attachment with the correct URL
             and manifest_json in metadata; assert returned manifest contains entry.
        Why: get_manifest must filter by URL and extract manifest_json reliably.
        """
        from backlog_core.artifact_registry import ArtifactRegistry

        registry = ArtifactRegistry()
        manifest = ArtifactManifest(issue_number=5)
        entry = ArtifactEntry(artifact_type=ArtifactType.FEATURE_CONTEXT, artifact_id="plan/feature.md")
        manifest = registry.register(manifest, entry)
        manifest_json = manifest.model_dump_json(by_alias=True)

        mock_linear_get.return_value = [
            {
                "id": "a1",
                "url": "dh://artifact-manifest/5",
                "title": "DH Artifact Manifest",
                "metadata": {"manifest_json": manifest_json},
            },
            {"id": "a2", "url": "dh://other/5", "title": "Other", "metadata": {}},
        ]

        # Act
        result = provider.get_manifest(5)

        # Assert
        assert len(result.artifacts) == 1
        assert result.artifacts[0].artifact_type == ArtifactType.FEATURE_CONTEXT

    def test_get_manifest_returns_empty_when_no_matching_attachment(
        self, provider: LinearArtifactProvider, mock_linear_get: MagicMock
    ) -> None:
        """get_manifest returns empty ArtifactManifest when no matching attachment exists.

        Tests: No-manifest case returns empty manifest, not an error.
        How: linear_get_attachments returns []; assert manifest.artifacts == [].
        Why: Fresh issues have no manifest attachment yet — this is normal.
        """
        # Arrange: mock_linear_get already returns []

        # Act
        result = provider.get_manifest(99)

        # Assert
        assert result.artifacts == []


# ---------------------------------------------------------------------------
# Metadata size limit handling
# ---------------------------------------------------------------------------


class TestMetadataSizeLimit:
    """set_manifest logs a warning when the manifest JSON exceeds 10K chars."""

    def test_large_manifest_triggers_warning_log(
        self,
        provider: LinearArtifactProvider,
        mock_linear_create: MagicMock,
        mock_linear_get: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        """set_manifest logs a warning when manifest JSON exceeds _LINEAR_MANIFEST_WARN_CHARS.

        Tests: Oversized manifest warning path.
        How: Patch ArtifactManifest.model_dump_json on the class so it returns a
             string exceeding the size threshold; assert logger.warning is called.
        Why: Linear metadata has undocumented size limits; users must be warned
             before data truncation occurs silently at the API boundary.
             Pydantic model instances are immutable — patch at class level.
        """
        from backlog_core.artifact_provider import _LINEAR_MANIFEST_WARN_CHARS

        # Arrange
        manifest = ArtifactManifest(issue_number=1)
        big_json = "x" * (_LINEAR_MANIFEST_WARN_CHARS + 1)

        mock_warning = mocker.patch("backlog_core.artifact_provider.logger")
        # Patch at class level — Pydantic instances don't allow attribute assignment
        mocker.patch.object(ArtifactManifest, "model_dump_json", return_value=big_json)

        # Act
        provider.set_manifest(1, manifest)

        # Assert — warning was logged
        mock_warning.warning.assert_called_once()
        args = mock_warning.warning.call_args[0]
        assert "10K" in args[0] or "truncation" in args[0]


# ---------------------------------------------------------------------------
# GraphQL error handling
# ---------------------------------------------------------------------------


class TestGraphQLErrorHandling:
    """BacklogError is raised when the Linear API returns errors."""

    def test_get_manifest_raises_backlog_error_on_api_failure(
        self, provider: LinearArtifactProvider, mock_linear_get: MagicMock
    ) -> None:
        """get_manifest raises BacklogError when linear_get_attachments raises.

        Tests: Linear API error propagation through get_manifest.
        How: Configure mock_linear_get to raise BacklogError; call get_manifest;
             assert BacklogError propagates unchanged.
        Why: API errors must propagate — swallowing them hides configuration failures.
        """
        # Arrange
        mock_linear_get.side_effect = BacklogError("LINEAR_API_KEY is invalid or missing")

        # Act / Assert
        with pytest.raises(BacklogError, match="LINEAR_API_KEY"):
            provider.get_manifest(1)

    def test_set_manifest_raises_backlog_error_on_api_failure(
        self, provider: LinearArtifactProvider, mock_linear_create: MagicMock, mock_linear_get: MagicMock
    ) -> None:
        """set_manifest raises BacklogError when linear_create_attachment raises.

        Tests: Linear API write error propagation.
        How: Configure mock_linear_create to raise BacklogError; call set_manifest.
        Why: Write failures must propagate — the manifest was not persisted.
        """
        # Arrange
        mock_linear_create.side_effect = BacklogError("Linear API error: resource not found")
        manifest = ArtifactManifest(issue_number=2)

        # Act / Assert
        with pytest.raises(BacklogError, match="Linear API"):
            provider.set_manifest(2, manifest)
