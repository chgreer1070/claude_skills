"""Shared test configuration for development-harness tests.

Adds the plugin root to sys.path so ``from backlog_core.parsing import ...``
resolves correctly regardless of pytest invocation directory.

Shared fixtures for scenario integration tests:
- ``backlog_dir``: Redirects BACKLOG_DIR to tmp_path for test isolation
- ``mock_github``: Patches all github.py functions at operations.py boundary
- ``write_test_item``: Factory for creating per-item files with valid frontmatter
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure backlog_core package is importable when running tests from repo root.
# The package lives at plugins/development-harness/ (not installed as editable
# from root), so we add its parent directory to sys.path explicitly.
_plugin_dir = Path(__file__).parent.parent
if str(_plugin_dir) not in sys.path:
    sys.path.insert(0, str(_plugin_dir))


# ---------------------------------------------------------------------------
# Shared fixtures for backlog scenario integration tests
# ---------------------------------------------------------------------------


@pytest.fixture
def backlog_dir(tmp_path, monkeypatch):
    """Redirect BACKLOG_DIR to a temp directory for test isolation.

    Patches BACKLOG_DIR in all three modules that import it at module level:
    models, operations, and parsing. Returns the directory path so tests can
    inspect created files.
    """
    bd = tmp_path / ".claude" / "backlog"
    bd.mkdir(parents=True)
    monkeypatch.setattr("backlog_core.models.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.operations.BACKLOG_DIR", bd)
    monkeypatch.setattr("backlog_core.parsing.BACKLOG_DIR", bd)
    return bd


@pytest.fixture
def mock_github(monkeypatch):
    """Patch all github.py functions imported by operations.py.

    Returns dict of ``{function_name: MagicMock}`` for per-test configuration.
    Override return values in individual tests like::

        mock_github["create_issue_for_item"].return_value = 99
    """
    from backlog_core.models import IssueLocalFields

    mocks: dict[str, MagicMock] = {}
    defaults: dict[str, object] = {
        "try_get_github": None,
        "get_github": MagicMock(),
        "create_issue_for_item": 42,
        "close_github_issue": None,
        "resolve_github_issue": None,
        "check_open_prs_for_issue": [],
        "batch_fetch_statuses": {},
        "apply_status_in_progress": None,
        "apply_status_verified": None,
        "fetch_open_issues_by_title": {},
        "view_enrich_from_github": False,
        "sync_groomed_to_github_issue": True,
        "fetch_github_issue_body": "issue body from github",
        "issue_to_local_fields": IssueLocalFields(
            title="Test", body="body", priority="P1", item_type="Feature", status="open"
        ),
    }
    for name, default in defaults.items():
        mock = MagicMock(return_value=default)
        monkeypatch.setattr(f"backlog_core.operations.{name}", mock)
        mocks[name] = mock
    return mocks


@pytest.fixture
def write_test_item(backlog_dir):
    """Factory: create per-item file with valid frontmatter in test backlog_dir.

    Usage::

        filepath = write_test_item("My Title", priority="P0", issue="#42")

    Returns the Path to the created file.
    """

    def _write(
        title: str,
        priority: str = "P1",
        issue: str = "",
        description: str = "Test item",
        status: str = "open",
        type_val: str = "Feature",
    ) -> Path:
        from backlog_core.parsing import build_backlog_frontmatter, title_to_slug

        slug = title_to_slug(title)
        filepath = backlog_dir / f"{priority.lower()}-{slug}.md"
        fm = build_backlog_frontmatter(
            title, description, "test", "2026-01-01", priority, type_val, status, issue, "", ""
        )
        filepath.write_text(fm, encoding="utf-8")
        return filepath

    return _write
