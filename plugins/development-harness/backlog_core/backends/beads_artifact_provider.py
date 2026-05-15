"""Beads CLI artifact provider stub — full implementation added in T09.

This module satisfies the deferred-import registration wired in T02 via
``backlog_core.artifact_provider.create_artifact_provider``.  The
:class:`BeadsArtifactProvider` class will route artifact manifest storage to
the ``bd`` CLI subprocess once T09 lands.

Instantiating :class:`BeadsArtifactProvider` before T09 lands will raise
:exc:`NotImplementedError` on every method call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from backlog_core.models import ArtifactManifest


class BeadsArtifactProvider:
    """Routes artifact manifest storage to the ``bd`` CLI subprocess.

    .. note::
        Stub registered in T02.  Full implementation added in T09.
        All method calls on this stub raise :exc:`NotImplementedError`.

    Args:
        root_worktree: Absolute path to the DH state root directory.
    """

    def __init__(self, root_worktree: Path | None = None) -> None:
        """Initialise stub with the DH state root path.

        Args:
            root_worktree: Absolute path to the DH state root directory.
        """
        self._root_worktree = root_worktree

    def get_manifest(self, issue_number: int) -> ArtifactManifest:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.get_manifest not yet implemented (T09)")

    def set_manifest(self, issue_number: int, manifest: ArtifactManifest) -> None:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.set_manifest not yet implemented (T09)")

    def read_artifact_content(self, path: str) -> str:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.read_artifact_content not yet implemented (T09)")

    def store_artifact_content(self, issue_number: int, artifact_type: str, path: str, content: str) -> None:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.store_artifact_content not yet implemented (T09)")

    def read_artifact_content_from_remote(self, issue_number: int, artifact_type: str, path: str) -> str | None:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.read_artifact_content_from_remote not yet implemented (T09)")

    def read_local_artifact_content(self, path: str) -> str | None:
        """Not yet implemented — see T09."""
        raise NotImplementedError("BeadsArtifactProvider.read_local_artifact_content not yet implemented (T09)")
