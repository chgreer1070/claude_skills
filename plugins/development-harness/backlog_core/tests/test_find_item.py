"""Tests for find_item selector resolution in backlog_core.parsing.

Regression guard for #1721 — find_item previously silently returned the first
match when a title substring matched multiple items.  The fix raises
AmbiguousSelectorError, forcing callers to supply a more specific selector.
"""

from __future__ import annotations

import pytest

from backlog_core.models import AmbiguousSelectorError, BacklogItem
from backlog_core.parsing import find_item


def _item(title: str, issue: str = "") -> BacklogItem:
    return BacklogItem(title=title, issue=issue)


class TestFindItemByIssueNumber:
    """Issue-number selectors (#N, bare N, GitHub URL) are unambiguous."""

    def test_finds_item_by_hash_prefix(self) -> None:
        items = [_item("Fix auth bug", "#42"), _item("Fix cache bug", "#43")]
        result = find_item(items, "#42")
        assert result is not None
        assert result.title == "Fix auth bug"

    def test_finds_item_by_bare_number(self) -> None:
        items = [_item("Fix auth bug", "#42"), _item("Fix cache bug", "#43")]
        result = find_item(items, "42")
        assert result is not None
        assert result.title == "Fix auth bug"

    def test_returns_none_when_issue_number_not_found(self) -> None:
        items = [_item("Fix auth bug", "#42")]
        assert find_item(items, "#99") is None

    def test_returns_none_when_list_is_empty(self) -> None:
        assert find_item([], "#1") is None


class TestFindItemByTitleSubstring:
    """Title-substring selectors must be unambiguous or raise."""

    def test_returns_single_matching_item(self) -> None:
        items = [_item("Fix authentication timeout"), _item("Refactor cache layer")]
        result = find_item(items, "authentication")
        assert result is not None
        assert result.title == "Fix authentication timeout"

    def test_title_match_is_case_insensitive(self) -> None:
        items = [_item("Fix Authentication Timeout"), _item("Refactor cache layer")]
        result = find_item(items, "AUTHENTICATION")
        assert result is not None
        assert result.title == "Fix Authentication Timeout"

    def test_returns_none_when_no_title_matches(self) -> None:
        items = [_item("Fix auth bug"), _item("Refactor cache")]
        assert find_item(items, "nonexistent-keyword") is None

    def test_raises_ambiguous_when_multiple_titles_match(self) -> None:
        items = [_item("Fix auth login bug", "#10"), _item("Fix auth signup bug", "#11")]
        with pytest.raises(AmbiguousSelectorError) as exc_info:
            find_item(items, "auth")
        err = exc_info.value
        assert err.selector == "auth"
        assert len(err.matches) == 2
        assert "2 items" in str(err)

    def test_ambiguous_error_lists_matched_titles_in_message(self) -> None:
        items = [_item("Fix auth login bug", "#10"), _item("Fix auth signup bug", "#11")]
        with pytest.raises(AmbiguousSelectorError) as exc_info:
            find_item(items, "auth")
        msg = str(exc_info.value)
        assert "Fix auth login bug" in msg
        assert "Fix auth signup bug" in msg

    def test_ambiguous_error_captures_all_matches(self) -> None:
        items = [_item(f"Feature {i} auth flow", f"#{i}") for i in range(5)]
        with pytest.raises(AmbiguousSelectorError) as exc_info:
            find_item(items, "auth")
        assert len(exc_info.value.matches) == 5

    def test_ambiguous_error_is_subclass_of_backlog_error(self) -> None:
        from backlog_core.models import BacklogError

        items = [_item("auth feature A"), _item("auth feature B")]
        with pytest.raises(AmbiguousSelectorError) as exc_info:
            find_item(items, "auth")
        assert isinstance(exc_info.value, BacklogError)


class TestFindItemSameIssueDedup:
    """Title-substring matches that share one issue number collapse instead of raising."""

    def test_same_issue_number_collapses_without_raising(self) -> None:
        """Two cache rows with the same issue number and different titles (prefix drift)
        must return the first match without raising AmbiguousSelectorError."""
        items = [
            _item("add-new-feature orchestrator must not read content", "#2437"),
            _item("refactor: add-new-feature orchestrator must not read content", "#2437"),
        ]
        result = find_item(items, "add-new-feature")
        assert result is not None
        assert result.title == "add-new-feature orchestrator must not read content"

    def test_different_issue_numbers_still_raises(self) -> None:
        """Two genuinely distinct issues that match a selector must still raise."""
        items = [_item("auth feature", "#10"), _item("auth feature", "#11")]
        with pytest.raises(AmbiguousSelectorError) as exc_info:
            find_item(items, "auth")
        assert len(exc_info.value.matches) == 2

    def test_untracked_row_in_match_set_raises(self) -> None:
        """One tracked item and one untracked item (empty issue) matching a selector
        must raise because the untracked row cannot be collapsed by issue number."""
        items = [_item("cache feature", "#42"), _item("cache feature untracked", "")]
        with pytest.raises(AmbiguousSelectorError):
            find_item(items, "cache")

    def test_all_untracked_rows_raise(self) -> None:
        """Multiple untracked items (empty issue) matching a selector must raise."""
        items = [_item("cache feature alpha", ""), _item("cache feature beta", "")]
        with pytest.raises(AmbiguousSelectorError):
            find_item(items, "cache")
