"""Tests for backlog.py GH-first Phase 1 changes.

Tests use pytest-mock (mocker fixture) to mock PyGithub — no live API calls.
Import uses importlib because backlog.py lives under .claude/ (not a Python package).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Load backlog.py as a module via importlib (dot in .claude/ breaks normal import)
# ---------------------------------------------------------------------------
_SCRIPT = Path(__file__).parent.parent / "scripts" / "backlog.py"
_spec = importlib.util.spec_from_file_location("backlog", _SCRIPT)
assert _spec is not None, f"Cannot find spec for {_SCRIPT}"
assert _spec.loader is not None, f"Cannot find loader for {_SCRIPT}"
_mod = importlib.util.module_from_spec(_spec)
sys.modules["backlog"] = _mod
_spec.loader.exec_module(_mod)

app = _mod.app
runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_backlog_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect BACKLOG_DIR to a temp directory for every test.

    Tests: Test isolation for backlog directory.
    How: Patches BACKLOG_DIR to a fresh tmp_path per test.
    Why: Prevents tests from reading/writing real backlog files.
    """
    monkeypatch.setattr(_mod, "BACKLOG_DIR", tmp_path / ".claude" / "backlog")
    (tmp_path / ".claude" / "backlog").mkdir(parents=True, exist_ok=True)


def _make_mock_issue(mocker: MockerFixture, number: int = 999, title: str = "feat: Test item") -> object:
    """Create a mock GitHub Issue with standard attributes.

    Args:
        mocker: pytest-mock fixture for creating mocks.
        number: Issue number.
        title: Issue title.

    Returns:
        Mock object mimicking a PyGithub Issue.
    """
    issue = mocker.Mock()
    issue.number = number
    issue.title = title
    issue.body = "## Story\n\nTest\n\n## Description\n\nTest description"
    issue.state = "open"
    issue.pull_request = None
    label_mock = mocker.Mock()
    label_mock.name = "status:in-progress"
    issue.labels = [label_mock]
    issue.milestone = None
    return issue


# ─── T1: add GH-first ───


class TestAddGhFirst:
    """T1: Verify add creates GitHub Issue before writing local file.

    Tests the GH-first flow for the `add` command: issue creation happens
    before the local cache file is written. Covers online, offline, and
    --no-create-issue scenarios.
    """

    def test_add_creates_gh_issue_first(self, mocker: MockerFixture) -> None:
        """Verify add creates GH Issue first, then writes local cache with issue number.

        Tests: GH-first add command.
        How: Mock _try_get_github to return a repo, mock create_issue_for_item to return 42.
        Why: Core GH-first guarantee — issue must exist before local file.
        """
        # Arrange
        mock_create = mocker.patch.object(_mod, "create_issue_for_item", return_value=42)
        mock_try_gh = mocker.patch.object(_mod, "_try_get_github", return_value=mocker.Mock())

        # Act
        result = runner.invoke(
            app, ["add", "--title", "Test GH-first", "--priority", "P1", "--description", "Testing GH-first add"]
        )

        # Assert
        assert result.exit_code == 0
        mock_try_gh.assert_called_once()
        mock_create.assert_called_once()
        assert "Issue: #42" in result.output

    def test_add_offline_fallback(self, mocker: MockerFixture) -> None:
        """Verify add creates local-only file when GitHub is unavailable.

        Tests: Graceful degradation for add command.
        How: Mock _try_get_github returning None (offline/no token).
        Why: Agents must work offline — local file created without issue number.
        """
        # Arrange
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = runner.invoke(
            app, ["add", "--title", "Offline test", "--priority", "P2", "--description", "Should work offline"]
        )

        # Assert
        assert result.exit_code == 0
        assert "WARNING: GitHub unavailable" in result.output
        assert "Backlog item created" in result.output
        assert "Issue: #" not in result.output

    def test_add_no_create_issue_flag(self, mocker: MockerFixture) -> None:
        """Verify --no-create-issue skips GitHub entirely.

        Tests: Local-only mode via CLI flag.
        How: Pass --no-create-issue and verify _try_get_github is never called.
        Why: Needed for testing/offline use — explicit opt-out of GH integration.
        """
        # Arrange
        mock_try_gh = mocker.patch.object(_mod, "_try_get_github")

        # Act
        result = runner.invoke(
            app, ["add", "--title", "Local only", "--priority", "P2", "--description", "No GH", "--no-create-issue"]
        )

        # Assert
        assert result.exit_code == 0
        mock_try_gh.assert_not_called()


# ─── T2: list --from-github ───


class TestListFromGithub:
    """T2: Verify list --from-github refreshes cache from GH.

    Tests the --from-github flag on the list command: queries GitHub Issues
    and rebuilds local cache before displaying results. Default list (no flag)
    must remain local-only with zero API calls.
    """

    def test_list_default_no_api_calls(self, mocker: MockerFixture) -> None:
        """Verify default list reads only local files — zero API calls.

        Tests: Cache-first read design.
        How: Invoke list without --from-github, verify _try_get_github never called.
        Why: Agents calling list frequently must not trigger API calls.
        """
        # Arrange
        mock_try_gh = mocker.patch.object(_mod, "_try_get_github")

        # Act
        result = runner.invoke(app, ["list", "--format", "json"])

        # Assert
        assert result.exit_code == 0
        mock_try_gh.assert_not_called()

    def test_list_from_github_refreshes_cache(self, mocker: MockerFixture) -> None:
        """Verify --from-github queries GH, calls _pull_single_issue per issue.

        Tests: GH-first list with cache refresh.
        How: Mock repo.get_issues to return one mock issue, verify _pull_single_issue called.
        Why: --from-github must fetch fresh data from GH and update local cache.
        """
        # Arrange
        mock_repo = mocker.Mock()
        mocker.patch.object(_mod, "_try_get_github", return_value=mock_repo)
        mock_pull = mocker.patch.object(_mod, "_pull_single_issue", return_value=Path("/tmp/test.md"))
        mock_issue = _make_mock_issue(mocker)
        mock_repo.get_issues.return_value = [mock_issue]
        mock_repo.get_label.return_value = mocker.Mock()

        # Act
        result = runner.invoke(app, ["list", "--from-github", "--format", "json"])

        # Assert
        assert result.exit_code == 0
        mock_repo.get_issues.assert_called_once()
        mock_pull.assert_called_once_with(mock_repo, 999)

    def test_list_from_github_offline_fallback(self, mocker: MockerFixture) -> None:
        """Verify --from-github falls back to local cache when GH unavailable.

        Tests: Graceful degradation for list --from-github.
        How: Mock _try_get_github returning None.
        Why: Offline agents must see local cache, not crash.
        """
        # Arrange
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = runner.invoke(app, ["list", "--from-github", "--format", "json"])

        # Assert
        assert result.exit_code == 0
        assert "WARNING: GitHub unavailable" in result.output


# ─── T3: update --plan GH-first ───


class TestUpdatePlanGhFirst:
    """T3: Verify update --plan writes to GH Issue then local.

    Tests the GH-first flow for plan updates: plan reference is posted as a
    comment on the linked GitHub Issue, then the local cache file is updated.
    """

    def test_update_plan_posts_gh_comment(self, mocker: MockerFixture) -> None:
        """Verify update --plan posts plan comment on GH Issue and updates local.

        Tests: GH-first plan update.
        How: Create local item with issue #99, mock GH, verify create_comment called.
        Why: Plan references must be visible on GH Issue for team visibility.
        """
        # Arrange
        backlog_dir = _mod.BACKLOG_DIR
        item_file = backlog_dir / "p1-test-plan-item.md"
        item_file.write_text(
            "---\nname: Test plan item\ndescription: Test\nmetadata:\n  issue: '#99'\n  priority: P1\n"
            "  status: open\n  source: test\n  added: '2026-01-01'\n  type: Feature\n  topic: test-plan-item\n---\n",
            encoding="utf-8",
        )
        mock_repo = mocker.Mock()
        mocker.patch.object(_mod, "_try_get_github", return_value=mock_repo)
        mock_issue = _make_mock_issue(mocker, 99)
        mock_repo.get_issue.return_value = mock_issue

        # Act
        result = runner.invoke(app, ["update", "Test plan", "--plan", "plan/tasks-1-test.md", "-R", "test/repo"])

        # Assert
        assert result.exit_code == 0
        mock_issue.create_comment.assert_called_once_with("**Plan**: plan/tasks-1-test.md")

    def test_update_plan_offline_still_updates_local(self, mocker: MockerFixture) -> None:
        """Verify update --plan writes local file even when GH is unavailable.

        Tests: Offline fallback for plan update.
        How: Mock _try_get_github returning None, verify local file contains plan path.
        Why: Local cache must always be updated regardless of GH availability.
        """
        # Arrange
        backlog_dir = _mod.BACKLOG_DIR
        item_file = backlog_dir / "p1-offline-plan.md"
        item_file.write_text(
            "---\nname: Offline plan test\ndescription: Test\nmetadata:\n  priority: P1\n  status: open\n"
            "  source: test\n  added: '2026-01-01'\n  type: Feature\n  topic: offline-plan-test\n---\n",
            encoding="utf-8",
        )
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = runner.invoke(app, ["update", "Offline plan", "--plan", "plan/test.md", "-R", "test/repo"])

        # Assert
        assert result.exit_code == 0
        assert "plan/test.md" in item_file.read_text()


# ─── T4: pull auto-migration ───


class TestPullAutoMigration:
    """T4: Verify pull creates missing GH Issues for P0/P1 items.

    Tests the auto-migration behavior in the pull command: P0/P1 items without
    GitHub Issues get them created automatically. P2/Ideas are skipped.
    """

    def test_pull_auto_migrates_p0_p1(self, mocker: MockerFixture) -> None:
        """Verify pull creates GH Issues for P0/P1 items missing them.

        Tests: Auto-migration in pull command.
        How: Create P1 item without issue, mock GH, verify _sync_create_missing_issues called.
        Why: P0/P1 items must be on GitHub for team visibility and tracking.
        """
        # Arrange
        backlog_dir = _mod.BACKLOG_DIR
        (backlog_dir / "p1-unmigrated.md").write_text(
            "---\nname: Unmigrated P1\ndescription: Needs migration\nmetadata:\n  priority: P1\n  status: open\n"
            "  source: test\n  added: '2026-01-01'\n  type: Feature\n  topic: unmigrated-p1\n---\n",
            encoding="utf-8",
        )
        mock_sync = mocker.patch.object(_mod, "_sync_create_missing_issues")
        mocker.patch.object(_mod, "_get_github", return_value=mocker.Mock())
        mocker.patch.object(_mod, "_pull_item", return_value=False)

        # Act
        runner.invoke(app, ["pull", "-R", "test/repo"])

        # Assert
        mock_sync.assert_called_once()

    def test_pull_skips_p2_ideas(self, mocker: MockerFixture) -> None:
        """Verify pull does NOT auto-migrate P2/Ideas items.

        Tests: Auto-migration scope restriction.
        How: Create P2 item without issue, verify _sync_create_missing_issues NOT called.
        Why: P2/Ideas stay local-only unless explicitly synced.
        """
        # Arrange
        backlog_dir = _mod.BACKLOG_DIR
        (backlog_dir / "p2-no-migrate.md").write_text(
            "---\nname: P2 no migrate\ndescription: Stay local\nmetadata:\n  priority: P2\n  status: open\n"
            "  source: test\n  added: '2026-01-01'\n  type: Feature\n  topic: p2-no-migrate\n---\n",
            encoding="utf-8",
        )
        mock_sync = mocker.patch.object(_mod, "_sync_create_missing_issues")
        mocker.patch.object(_mod, "_get_github", return_value=mocker.Mock())

        # Act
        runner.invoke(app, ["pull", "-R", "test/repo"])

        # Assert
        mock_sync.assert_not_called()


# ─── T5: batch status fetch ───


class TestBatchStatusFetch:
    """T5: Verify --with-status uses batch fetch instead of N+1 queries.

    Tests the _batch_fetch_statuses function that replaces per-item
    get_issue() calls with a single get_issues(state="open") call.
    """

    def test_list_with_status_uses_batch(self, mocker: MockerFixture) -> None:
        """Verify list --with-status calls _batch_fetch_statuses once.

        Tests: Batch status fetch integration.
        How: Create item with issue #100, mock batch fetch, verify single call and output.
        Why: N+1 queries are slow and risk rate limiting — batch is mandatory.
        """
        # Arrange
        backlog_dir = _mod.BACKLOG_DIR
        (backlog_dir / "p1-batch-test.md").write_text(
            "---\nname: Batch test\ndescription: Test\nmetadata:\n  issue: '#100'\n  priority: P1\n  status: open\n"
            "  source: test\n  added: '2026-01-01'\n  type: Feature\n  topic: batch-test\n---\n",
            encoding="utf-8",
        )
        mock_batch = mocker.patch.object(
            _mod, "_batch_fetch_statuses", return_value={100: {"status": "status:in-progress", "milestone": "v1.0"}}
        )

        # Act
        result = runner.invoke(app, ["list", "--with-status", "--format", "json", "-R", "test/repo"])

        # Assert
        assert result.exit_code == 0
        mock_batch.assert_called_once()
        data = json.loads(result.output)
        items_100 = [it for it in data if it.get("issue") == "#100"]
        assert len(items_100) == 1
        assert items_100[0]["status"] == "status:in-progress"

    def test_batch_fetch_offline_returns_empty(self, mocker: MockerFixture) -> None:
        """Verify _batch_fetch_statuses returns empty dict when GH unavailable.

        Tests: Batch fetch graceful degradation.
        How: Mock _try_get_github returning None, call _batch_fetch_statuses directly.
        Why: Offline agents must get empty status, not crash.
        """
        # Arrange
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = _mod._batch_fetch_statuses([{"_issue": "#100"}], "test/repo")

        # Assert
        assert result == {}


# ─── Graceful degradation ───


class TestGracefulDegradation:
    """Cross-cutting: all commands degrade gracefully when GH is unavailable.

    Verifies that every GH-first command completes successfully with exit
    code 0 when _try_get_github returns None (no token, network error).
    """

    def test_add_degrades(self, mocker: MockerFixture) -> None:
        """Verify add completes successfully when GH unavailable.

        Tests: Add command graceful degradation.
        How: Mock _try_get_github returning None, invoke add.
        Why: Agents must always be able to create backlog items.
        """
        # Arrange
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = runner.invoke(app, ["add", "--title", "Degrade test", "--priority", "P1", "--description", "test"])

        # Assert
        assert result.exit_code == 0

    def test_list_from_github_degrades(self, mocker: MockerFixture) -> None:
        """Verify list --from-github completes successfully when GH unavailable.

        Tests: List --from-github graceful degradation.
        How: Mock _try_get_github returning None, invoke list --from-github.
        Why: Agents must fall back to local cache, not crash.
        """
        # Arrange
        mocker.patch.object(_mod, "_try_get_github", return_value=None)

        # Act
        result = runner.invoke(app, ["list", "--from-github", "--format", "json"])

        # Assert
        assert result.exit_code == 0

    def test_list_with_status_degrades(self, mocker: MockerFixture) -> None:
        """Verify list --with-status completes successfully when batch fetch empty.

        Tests: List --with-status graceful degradation.
        How: Mock _batch_fetch_statuses returning empty dict.
        Why: Status display must work even without GH data.
        """
        # Arrange
        mocker.patch.object(_mod, "_batch_fetch_statuses", return_value={})

        # Act
        result = runner.invoke(app, ["list", "--with-status", "--format", "json"])

        # Assert
        assert result.exit_code == 0
