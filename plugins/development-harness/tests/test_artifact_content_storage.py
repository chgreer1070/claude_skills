"""Tests for artifact content storage and retrieval via GitHub issue comments.

Covers:
- _build_artifact_content_comment: structure, truncation
- _extract_content_from_comment: happy path, malformed input
- GitHubArtifactProvider.store_artifact_content: create new, update existing
- GitHubArtifactProvider.read_artifact_content_from_github: found, not found
- artifact_register MCP tool: with content (tier 1), auto-read local file (tier 2), no content/no file (tier 3)
- artifact_read MCP tool: GitHub-first, filesystem fallback, neither available
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from backlog_core.artifact_provider import (
    _GITHUB_COMMENT_MAX_CHARS,
    GitHubArtifactProvider,
    _build_artifact_content_comment,
    _extract_content_from_comment,
)
from backlog_core.models import ArtifactEntry, ArtifactManifest, ArtifactStatus, ArtifactType
from backlog_core.server import mcp
from fastmcp.client import Client

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _call(tool_name: str, params: dict | None = None) -> dict:
    """Call a tool through the in-memory FastMCP transport and parse the result."""
    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, params or {})
    return json.loads(result.content[0].text)


def _make_comment_mock(body: str) -> MagicMock:
    """Build a MagicMock resembling a PyGithub IssueComment."""
    comment = MagicMock()
    comment.body = body
    return comment


def _make_issue_mock(comments: list[MagicMock] | None = None) -> MagicMock:
    """Build a MagicMock resembling a PyGithub Issue."""
    issue = MagicMock()
    issue.get_comments.return_value = comments or []
    issue.create_comment = MagicMock()
    return issue


def _make_repo_mock(issue: MagicMock) -> MagicMock:
    """Build a MagicMock resembling a PyGithub Repository."""
    repo = MagicMock()
    repo.get_issue.return_value = issue
    return repo


# ---------------------------------------------------------------------------
# _build_artifact_content_comment
# ---------------------------------------------------------------------------


def test_build_artifact_content_comment_contains_opening_tag() -> None:
    # Arrange
    artifact_type = "research"
    path = "plan/research-foo.md"
    content = "Some content"

    # Act
    result = _build_artifact_content_comment(artifact_type, path, content)

    # Assert
    assert "<!-- artifact-content:type=research:path=plan/research-foo.md -->" in result


def test_build_artifact_content_comment_contains_closing_tag() -> None:
    # Arrange / Act
    result = _build_artifact_content_comment("research", "plan/foo.md", "content")

    # Assert
    assert "<!-- /artifact-content -->" in result


def test_build_artifact_content_comment_contains_details_block() -> None:
    # Arrange / Act
    result = _build_artifact_content_comment("architect", "plan/arch.md", "# Architecture")

    # Assert
    assert "<details>" in result
    assert "</details>" in result
    assert "<summary>" in result


def test_build_artifact_content_comment_embeds_content() -> None:
    # Arrange
    content = "This is the artifact body text."

    # Act
    result = _build_artifact_content_comment("feature-context", "plan/fc.md", content)

    # Assert
    assert content in result


def test_build_artifact_content_comment_truncates_oversized_content() -> None:
    # Arrange — content large enough to exceed the GitHub limit
    oversized = "x" * (_GITHUB_COMMENT_MAX_CHARS + 1000)

    # Act
    result = _build_artifact_content_comment("research", "plan/big.md", oversized)

    # Assert — result must be within the limit
    assert len(result) <= _GITHUB_COMMENT_MAX_CHARS
    assert "WARNING: content truncated" in result


def test_build_artifact_content_comment_does_not_truncate_within_limit() -> None:
    # Arrange — content well within limit
    content = "Small content"

    # Act
    result = _build_artifact_content_comment("research", "plan/small.md", content)

    # Assert — no truncation warning
    assert "WARNING" not in result
    assert content in result


# ---------------------------------------------------------------------------
# _extract_content_from_comment
# ---------------------------------------------------------------------------


def test_extract_content_from_comment_returns_inner_content() -> None:
    # Arrange
    comment_body = (
        "<!-- artifact-content:type=research:path=plan/foo.md -->\n"
        "<details>\n"
        "<summary>Artifact: research — plan/foo.md</summary>\n\n"
        "# Research findings\n\nSome text here.\n\n"
        "</details>\n"
        "<!-- /artifact-content -->"
    )

    # Act
    result = _extract_content_from_comment(comment_body)

    # Assert
    assert "# Research findings" in result
    assert "Some text here." in result


def test_extract_content_from_comment_strips_surrounding_whitespace() -> None:
    # Arrange
    comment_body = (
        "<!-- artifact-content:type=research:path=plan/foo.md -->\n"
        "<details>\n"
        "<summary>summary</summary>\n\n"
        "  actual content  \n\n"
        "</details>\n"
        "<!-- /artifact-content -->"
    )

    # Act
    result = _extract_content_from_comment(comment_body)

    # Assert
    assert result == "actual content"


def test_extract_content_from_comment_returns_full_body_when_malformed() -> None:
    # Arrange — no </summary> or </details> tags
    malformed = "<!-- artifact-content:type=x:path=y -->\nsome raw text\n<!-- /artifact-content -->"

    # Act
    result = _extract_content_from_comment(malformed)

    # Assert — returns the full body rather than raising
    assert result == malformed


# ---------------------------------------------------------------------------
# GitHubArtifactProvider.store_artifact_content
# ---------------------------------------------------------------------------


def test_store_artifact_content_creates_new_comment_when_none_exists(tmp_path: Path) -> None:
    # Arrange
    issue = _make_issue_mock(comments=[])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        provider.store_artifact_content(42, "research", "plan/foo.md", "# Content")

    # Assert
    issue.create_comment.assert_called_once()
    body = issue.create_comment.call_args[0][0]
    assert "artifact-content:type=research:path=plan/foo.md" in body
    assert "# Content" in body


def test_store_artifact_content_updates_existing_comment_in_place(tmp_path: Path) -> None:
    # Arrange — existing comment matches type+path
    existing_body = (
        "<!-- artifact-content:type=research:path=plan/foo.md -->\n"
        "<details>\n<summary>Artifact: research — plan/foo.md</summary>\n\n"
        "old content\n\n</details>\n<!-- /artifact-content -->"
    )
    existing_comment = _make_comment_mock(existing_body)
    issue = _make_issue_mock(comments=[existing_comment])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        provider.store_artifact_content(42, "research", "plan/foo.md", "new content")

    # Assert — edit called on the existing comment, not create_comment
    existing_comment.edit.assert_called_once()
    issue.create_comment.assert_not_called()
    new_body = existing_comment.edit.call_args[0][0]
    assert "new content" in new_body


def test_store_artifact_content_does_not_update_comment_with_different_path(tmp_path: Path) -> None:
    # Arrange — comment has same type but different path
    existing_body = (
        "<!-- artifact-content:type=research:path=plan/other.md -->\n"
        "<details>\n<summary>summary</summary>\n\nold\n\n</details>\n<!-- /artifact-content -->"
    )
    existing_comment = _make_comment_mock(existing_body)
    issue = _make_issue_mock(comments=[existing_comment])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        provider.store_artifact_content(42, "research", "plan/foo.md", "new content")

    # Assert — different path means new comment is created
    issue.create_comment.assert_called_once()
    existing_comment.edit.assert_not_called()


# ---------------------------------------------------------------------------
# GitHubArtifactProvider.read_artifact_content_from_github
# ---------------------------------------------------------------------------


def test_read_artifact_content_from_github_returns_content_when_found(tmp_path: Path) -> None:
    # Arrange
    stored_content = "# Research findings\n\nImportant data."
    comment_body = _build_artifact_content_comment("research", "plan/foo.md", stored_content)
    issue = _make_issue_mock(comments=[_make_comment_mock(comment_body)])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        result = provider.read_artifact_content_from_github(42, "research", "plan/foo.md")

    # Assert
    assert result is not None
    assert "# Research findings" in result
    assert "Important data." in result


def test_read_artifact_content_from_github_returns_none_when_not_found(tmp_path: Path) -> None:
    # Arrange — no matching comment
    issue = _make_issue_mock(comments=[])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        result = provider.read_artifact_content_from_github(42, "research", "plan/foo.md")

    # Assert
    assert result is None


def test_read_artifact_content_from_github_ignores_wrong_type(tmp_path: Path) -> None:
    # Arrange — comment exists but for a different type
    comment_body = _build_artifact_content_comment("architect", "plan/foo.md", "some content")
    issue = _make_issue_mock(comments=[_make_comment_mock(comment_body)])
    repo = _make_repo_mock(issue)
    provider = GitHubArtifactProvider(repo="owner/repo", root_worktree=tmp_path)

    with patch("backlog_core.artifact_provider.get_github", return_value=repo):
        # Act
        result = provider.read_artifact_content_from_github(42, "research", "plan/foo.md")

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# artifact_register MCP tool — content parameter
# ---------------------------------------------------------------------------


async def test_artifact_register_without_content_and_no_local_file_registers_manifest_only() -> None:
    # Arrange — no explicit content and no local file (tier 3: manifest-only)
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest
    mock_provider.set_manifest.return_value = None
    mock_provider.read_local_artifact_content.return_value = None  # no local file

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.register.return_value = mock_manifest.model_copy(
            update={"artifacts": [ArtifactEntry(artifact_type=ArtifactType.RESEARCH, path="plan/r.md")]}
        )
        # Act
        result = await _call(
            "artifact_register", {"issue_number": 42, "artifact_type": "research", "path": "plan/r.md"}
        )

    # Assert
    assert result.get("error") is None
    assert result["registered"] is True
    assert result["content_stored"] is False
    mock_provider.store_artifact_content.assert_not_called()
    # A warning must be emitted so callers can detect the missing content
    assert any("no local file" in w.lower() or "manifest entry" in w.lower() for w in result.get("warnings", []))


async def test_artifact_register_with_content_stores_to_github() -> None:
    # Arrange
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest
    mock_provider.set_manifest.return_value = None
    mock_provider.store_artifact_content.return_value = None

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.register.return_value = mock_manifest.model_copy(
            update={"artifacts": [ArtifactEntry(artifact_type=ArtifactType.RESEARCH, path="plan/r.md")]}
        )
        # Act
        result = await _call(
            "artifact_register",
            {"issue_number": 42, "artifact_type": "research", "path": "plan/r.md", "content": "# Research content"},
        )

    # Assert
    assert result.get("error") is None
    assert result["registered"] is True
    assert result["content_stored"] is True
    mock_provider.store_artifact_content.assert_called_once_with(42, "research", "plan/r.md", "# Research content")


async def test_artifact_register_without_content_reads_local_file_and_uploads() -> None:
    # Arrange — no explicit content but local file exists (tier 2: auto-read from filesystem)
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest
    mock_provider.set_manifest.return_value = None
    mock_provider.read_local_artifact_content.return_value = "# File content read automatically"
    mock_provider.store_artifact_content.return_value = None

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.register.return_value = mock_manifest.model_copy(
            update={"artifacts": [ArtifactEntry(artifact_type=ArtifactType.RESEARCH, path="plan/r.md")]}
        )
        # Act
        result = await _call(
            "artifact_register", {"issue_number": 42, "artifact_type": "research", "path": "plan/r.md"}
        )

    # Assert
    assert result.get("error") is None
    assert result["registered"] is True
    assert result["content_stored"] is True
    mock_provider.read_local_artifact_content.assert_called_once_with("plan/r.md")
    mock_provider.store_artifact_content.assert_called_once_with(
        42, "research", "plan/r.md", "# File content read automatically"
    )


async def test_artifact_register_with_invalid_type_returns_error() -> None:
    # Arrange / Act
    result = await _call(
        "artifact_register", {"issue_number": 42, "artifact_type": "not-a-real-type", "path": "plan/foo.md"}
    )

    # Assert
    assert "error" in result


# ---------------------------------------------------------------------------
# artifact_read MCP tool — GitHub-first, filesystem fallback
# ---------------------------------------------------------------------------


async def test_artifact_read_returns_github_content_when_available() -> None:
    # Arrange
    entry = ArtifactEntry(artifact_type=ArtifactType.RESEARCH, path="plan/r.md", status=ArtifactStatus.CURRENT)
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[entry])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest
    mock_provider.read_artifact_content_from_github.return_value = "# From GitHub"

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.get_by_type.return_value = [entry]
        # Act
        result = await _call("artifact_read", {"issue_number": 42, "artifact_type": "research"})

    # Assert
    assert result.get("error") is None
    assert result["content"] == "# From GitHub"
    mock_provider.read_artifact_content.assert_not_called()


async def test_artifact_read_falls_back_to_filesystem_when_github_returns_none(tmp_path: Path) -> None:
    # Arrange
    entry = ArtifactEntry(artifact_type=ArtifactType.RESEARCH, path="plan/r.md", status=ArtifactStatus.CURRENT)
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[entry])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest
    mock_provider.read_artifact_content_from_github.return_value = None
    mock_provider.read_artifact_content.return_value = "# From filesystem"

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.get_by_type.return_value = [entry]
        # Act
        result = await _call("artifact_read", {"issue_number": 42, "artifact_type": "research"})

    # Assert
    assert result.get("error") is None
    assert result["content"] == "# From filesystem"
    mock_provider.read_artifact_content.assert_called_once_with("plan/r.md")


async def test_artifact_read_returns_error_when_type_not_found() -> None:
    # Arrange
    mock_manifest = ArtifactManifest(issue_number=42, artifacts=[])
    mock_provider = MagicMock()
    mock_provider.get_manifest.return_value = mock_manifest

    with (
        patch("backlog_core.server._get_artifact_provider", return_value=mock_provider),
        patch("backlog_core.server._artifact_registry") as mock_registry,
    ):
        mock_registry.get_by_type.return_value = []
        # Act
        result = await _call("artifact_read", {"issue_number": 42, "artifact_type": "research"})

    # Assert
    assert "error" in result


async def test_artifact_read_returns_error_for_invalid_type() -> None:
    # Arrange / Act
    result = await _call("artifact_read", {"issue_number": 42, "artifact_type": "not-real"})

    # Assert
    assert "error" in result
