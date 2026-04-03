"""Tests for auto-registration of plan artifacts in backlog_update (T8).

Covers:
- _auto_register_plan_artifact registers task-plan artifact when item has issue
- _auto_register_plan_artifact is skipped when item has no issue number
- Registration failure does not block the call (best-effort, warns)
- Item with issue="#123" format is parsed correctly
- Item with malformed issue string logs warning and skips
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backlog_core.models import ArtifactManifest, ArtifactType, BacklogItem, Output
from backlog_core.operations import _auto_register_plan_artifact

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_item(issue: str = "", file_path: str = "") -> BacklogItem:
    """Return a minimal BacklogItem for testing."""
    return BacklogItem(title="Test Feature", issue=issue, file_path=file_path)


def _empty_manifest(issue_number: int = 42) -> ArtifactManifest:
    """Return an empty ArtifactManifest."""
    return ArtifactManifest(issue_number=issue_number)


# ---------------------------------------------------------------------------
# Tests: _auto_register_plan_artifact
# ---------------------------------------------------------------------------


class TestAutoRegisterPlanArtifact:
    """Tests for the _auto_register_plan_artifact helper."""

    def test_auto_register_plan_artifact_with_issue_registers_task_plan(self) -> None:
        """When item has a linked issue, the plan is registered as task-plan artifact."""
        item = _make_item(issue="#42")
        out = Output()

        with (
            patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls,
            patch("backlog_core.operations.ArtifactRegistry") as mock_registry_cls,
        ):
            mock_provider = MagicMock()
            mock_provider.get_manifest.return_value = _empty_manifest(issue_number=42)
            mock_provider_cls.return_value = mock_provider

            mock_registry = MagicMock()
            updated_manifest = _empty_manifest(issue_number=42)
            mock_registry.register.return_value = updated_manifest
            mock_registry_cls.return_value = mock_registry

            _auto_register_plan_artifact(item, "plan/tasks-1-foo.yaml", repo="owner/repo", output=out)

        # Provider was constructed with the correct repo
        mock_provider_cls.assert_called_once_with(repo="owner/repo")
        # Manifest was fetched for issue 42
        mock_provider.get_manifest.assert_called_once_with(42)
        # Register was called with a task-plan entry pointing at the plan path
        mock_registry.register.assert_called_once()
        call_args = mock_registry.register.call_args
        entry = call_args[0][1]  # second positional arg is the ArtifactEntry
        assert entry.artifact_type == ArtifactType.TASK_PLAN
        assert entry.path == "plan/tasks-1-foo.yaml"
        # Updated manifest was persisted
        mock_provider.set_manifest.assert_called_once_with(42, updated_manifest)
        # Info message was emitted
        assert any("Artifact registered" in m for m in out.messages)
        assert out.warnings == []

    def test_auto_register_plan_artifact_without_issue_skips_silently(self) -> None:
        """When item has no issue number, registration is skipped entirely."""
        item = _make_item(issue="")
        out = Output()

        with (
            patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls,
            patch("backlog_core.operations.ArtifactRegistry") as mock_registry_cls,
        ):
            _auto_register_plan_artifact(item, "plan/tasks-1-foo.yaml", repo="owner/repo", output=out)

            mock_provider_cls.assert_not_called()
            mock_registry_cls.assert_not_called()

        assert out.warnings == []
        assert out.messages == []

    def test_auto_register_plan_artifact_registration_failure_does_not_raise(self) -> None:
        """Registration failure logs a warning but does not propagate the exception."""
        item = _make_item(issue="#99")
        out = Output()

        with patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls:
            mock_provider = MagicMock()
            mock_provider.get_manifest.side_effect = RuntimeError("GitHub unavailable")
            mock_provider_cls.return_value = mock_provider

            # Must not raise
            _auto_register_plan_artifact(item, "plan/tasks-1-bar.yaml", repo="owner/repo", output=out)

        assert any("WARNING" in w and "Artifact registration failed" in w for w in out.warnings)

    def test_auto_register_plan_artifact_malformed_issue_string_warns_and_skips(self) -> None:
        """Item with unparseable issue string logs a warning and does not call the provider."""
        item = _make_item(issue="not-a-number")
        out = Output()

        with patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls:
            _auto_register_plan_artifact(item, "plan/tasks-1-foo.yaml", repo="owner/repo", output=out)
            mock_provider_cls.assert_not_called()

        assert any("WARNING" in w and "Could not parse issue number" in w for w in out.warnings)

    def test_auto_register_plan_artifact_issue_without_hash_prefix(self) -> None:
        """Issue string without '#' prefix (bare number) is still parsed correctly."""
        item = _make_item(issue="123")
        out = Output()

        with (
            patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls,
            patch("backlog_core.operations.ArtifactRegistry") as mock_registry_cls,
        ):
            mock_provider = MagicMock()
            mock_provider.get_manifest.return_value = _empty_manifest(issue_number=123)
            mock_provider_cls.return_value = mock_provider

            mock_registry = MagicMock()
            mock_registry.register.return_value = _empty_manifest(issue_number=123)
            mock_registry_cls.return_value = mock_registry

            _auto_register_plan_artifact(item, "plan/tasks-1-baz.yaml", repo="owner/repo", output=out)

        mock_provider.get_manifest.assert_called_once_with(123)
        assert out.warnings == []

    def test_auto_register_plan_artifact_set_manifest_failure_warns(self) -> None:
        """set_manifest failure logs a warning but does not propagate."""
        item = _make_item(issue="#7")
        out = Output()

        with (
            patch("backlog_core.operations.GitHubArtifactProvider") as mock_provider_cls,
            patch("backlog_core.operations.ArtifactRegistry") as mock_registry_cls,
        ):
            mock_provider = MagicMock()
            mock_provider.get_manifest.return_value = _empty_manifest(issue_number=7)
            mock_provider.set_manifest.side_effect = OSError("network timeout")
            mock_provider_cls.return_value = mock_provider

            mock_registry = MagicMock()
            mock_registry.register.return_value = _empty_manifest(issue_number=7)
            mock_registry_cls.return_value = mock_registry

            # Must not raise
            _auto_register_plan_artifact(item, "plan/tasks-1-qux.yaml", repo="owner/repo", output=out)

        assert any("WARNING" in w for w in out.warnings)
