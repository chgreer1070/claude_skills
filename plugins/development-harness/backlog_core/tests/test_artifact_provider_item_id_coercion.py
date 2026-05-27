"""Regression tests for numeric-string item_id coercion in artifact_provider.

Bug: ``artifact_read`` and ``artifact_list`` fail with
``GitHubGistArtifactProvider requires an integer item ID, got '2459'``
when a numeric string is passed instead of an integer.

The MCP tool schema declares ``item_id: Union[str, int]`` to handle both
GitHub integer IDs and beads nanoid strings (e.g. ``'bd-a3f8'``).  But
``_require_int_item_id`` currently raises on ANY string — including strings
that are valid integer representations like ``'2459'``.

The expected post-fix behaviour:
- A numeric-only string such as ``'2459'`` is coerced to ``int(2459)`` and
  returned without raising.
- A non-numeric beads string such as ``'bd-a3f8'`` still raises ``TypeError``
  because it cannot route to a GitHub/GitLab provider.
- A plain integer ``2459`` is returned unchanged.

These tests are RED (failing) before the fix is applied.
"""

from __future__ import annotations

import pytest

from backlog_core.artifact_provider import _require_int_item_id


class TestRequireIntItemIdCoercion:
    """_require_int_item_id coerces numeric strings and rejects beads strings."""

    def test_numeric_string_is_coerced_to_int(self) -> None:
        """A numeric string like '2459' must be coerced to int(2459), not raise.

        This is the root-cause reproduction of the reported bug.  Agents pass
        item_id as a string when the MCP tool schema allows str|int; the helper
        must accept numeric strings instead of raising TypeError.
        """
        # Arrange
        item_id_string = "2459"

        # Act
        result = _require_int_item_id("GitHubGistArtifactProvider", item_id_string)

        # Assert
        assert result == 2459
        assert isinstance(result, int)

    def test_beads_string_still_raises_type_error(self) -> None:
        """A beads nanoid string like 'bd-a3f8' must still raise TypeError.

        The discriminator between GitHub and beads providers depends on this
        rejection — a beads ID cannot be coerced to int and must not silently
        succeed for GitHub providers.
        """
        # Arrange / Act / Assert
        with pytest.raises(TypeError, match="requires an integer item ID"):
            _require_int_item_id("GitHubGistArtifactProvider", "bd-a3f8")

    def test_plain_integer_passes_through_unchanged(self) -> None:
        """A plain int like 2459 must be returned as-is without modification.

        This is the existing happy-path contract; the coercion fix must not
        alter it.
        """
        # Arrange
        item_id_int = 2459

        # Act
        result = _require_int_item_id("GitHubGistArtifactProvider", item_id_int)

        # Assert
        assert result == 2459
        assert isinstance(result, int)

    def test_gitlab_provider_name_in_error_message(self) -> None:
        """The cls_name parameter appears in the TypeError message for GitLab too.

        Verifies that the error message is correctly attributed regardless of
        which provider is calling the helper.
        """
        with pytest.raises(TypeError, match="GitLabArtifactProvider requires an integer item ID"):
            _require_int_item_id("GitLabArtifactProvider", "bd-a3f8")
