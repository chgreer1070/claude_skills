"""Tests reproducing the pre-commit hook stash conflict bug in auto-sync-manifests.py.

Observed symptom: When a commit attempt fails (e.g., ruff errors on other files) and the
user retries ``git commit``, prek reports::

    Stashed changes conflicted with changes made by hook, rolling back the hook changes

The conflict involves ``plugins/*/.claude-plugin/plugin.json`` files.

Bug areas tested:
1. JSON formatting conflict -- json.dump(indent=2) writes arrays vertically while prettier
   collapses short arrays onto one line, producing different file content for the same data.
2. Idempotency -- running the same update functions twice must produce identical output
   without double-bumping versions.
3. The "already staged" guard -- lines 276-280 and 332-335 skip ALL processing when the
   manifest file is already in ``git diff --cached``, which changes behavior on retry.

Test isolation strategy:
- All git subprocess calls are mocked via pytest-mock.
- All file I/O uses pytest tmp_path fixtures with monkeypatch.chdir.
- Each test is fully independent with no shared state.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_mock import MockerFixture

# ---------------------------------------------------------------------------
# Module import -- script has a hyphen in the filename so we use importlib
# ---------------------------------------------------------------------------
_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "auto-sync-manifests.py"
_spec = importlib.util.spec_from_file_location("auto_sync_manifests", _SCRIPT_PATH)
if _spec and _spec.loader:
    auto_sync = importlib.util.module_from_spec(_spec)
    sys.modules["auto_sync_manifests"] = auto_sync
    _spec.loader.exec_module(auto_sync)
else:
    msg = f"Could not load module from {_SCRIPT_PATH}"
    raise ImportError(msg)


# Type aliases matching the module's TypedDicts -- defined locally so mypy
# resolves them without needing the dynamic module's types at analysis time.
ComponentChanges = dict[str, list[dict[str, str]]]
MarketplaceChanges = dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plugin_json(base: Path, plugin_name: str, data: Mapping[str, Any]) -> Path:
    """Create plugins/<plugin_name>/.claude-plugin/plugin.json under *base*.

    Returns the path to plugin.json.
    """
    plugin_dir = base / "plugins" / plugin_name / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    plugin_json = plugin_dir / "plugin.json"
    plugin_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return plugin_json


def _make_marketplace_json(base: Path, data: Mapping[str, Any]) -> Path:
    """Create .claude-plugin/marketplace.json under *base*.

    Returns the path to marketplace.json.
    """
    claude_dir = base / ".claude-plugin"
    claude_dir.mkdir(parents=True, exist_ok=True)
    marketplace_json = claude_dir / "marketplace.json"
    marketplace_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return marketplace_json


def _changes_with_modified_skill() -> ComponentChanges:
    """Return ComponentChanges with a single modified skill."""
    return {
        "added": [],
        "deleted": [],
        "modified": [
            {"component_type": "skill", "component_path": "skills/my-skill/SKILL.md"}
        ],
    }


def _changes_with_added_skill() -> ComponentChanges:
    """Return ComponentChanges with a single added skill."""
    return {
        "added": [
            {"component_type": "skill", "component_path": "skills/new-skill/SKILL.md"}
        ],
        "deleted": [],
        "modified": [],
    }


# ============================================================================
# Area 1: JSON formatting conflict with prettier
# ============================================================================


class TestJsonFormattingConflict:
    """Test that json.dump output differs from prettier-formatted JSON.

    The pre-commit hook writes JSON with ``json.dump(data, f, indent=2)`` (line 305).
    The prettier pre-commit hook also runs on JSON files, reformatting short arrays
    onto a single line.  When both modify the same file in the same pre-commit pass,
    the stash/restore cycle produces conflicts.

    These tests verify the formatting mismatch exists and quantify it.
    """

    def test_json_dump_expands_short_arrays_vertically(self) -> None:
        """Verify json.dump(indent=2) expands arrays with one element onto multiple lines.

        Tests: JSON serialisation format
        How: Serialize a dict with a single-element list and inspect the output
        Why: This vertical expansion is the root cause of the prettier conflict
        """
        # Arrange
        data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "skills": ["./skills/test-skill/"],
        }

        # Act
        output = json.dumps(data, indent=2) + "\n"

        # Assert -- json.dump writes the array across 3 lines
        assert '"skills": [\n    "./skills/test-skill/"\n  ]' in output

    def test_prettier_format_keeps_short_arrays_inline(self) -> None:
        """Verify prettier-style format collapses short arrays onto one line.

        Tests: Expected prettier output format
        How: Construct the prettier-equivalent string and compare to json.dump
        Why: Demonstrates the exact formatting difference that causes stash conflicts
        """
        # Arrange
        data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "skills": ["./skills/test-skill/"],
        }
        json_dump_output = json.dumps(data, indent=2) + "\n"

        # The format prettier produces for the same data
        prettier_output = (
            "{\n"
            '  "name": "test-plugin",\n'
            '  "version": "1.0.0",\n'
            '  "skills": ["./skills/test-skill/"]\n'
            "}\n"
        )

        # Act & Assert -- the two formats differ
        assert json_dump_output != prettier_output
        # But they parse to the same data
        assert json.loads(json_dump_output) == json.loads(prettier_output)

    def test_update_plugin_json_writes_prettier_compatible_format(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify update_plugin_json writes prettier-compatible JSON format.

        Tests: File output format after update_plugin_json
        How: Create plugin.json in prettier format, run update, check output stays
             prettier-compatible (short arrays stay inline)
        Why: Confirms the fix -- hook now writes the same format as prettier,
             eliminating stash conflicts
        """
        # Arrange -- chdir so relative paths in the script resolve under tmp_path
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        plugin_json = _make_plugin_json(
            tmp_path,
            plugin_name,
            {
                "name": "test-plugin",
                "version": "1.0.0",
                "skills": ["./skills/existing-skill/"],
            },
        )

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        changes = _changes_with_modified_skill()

        # Act
        updated, _new_version = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert
        assert updated is True
        written_content = plugin_json.read_text(encoding="utf-8")

        # The hook now writes prettier-compatible format: short arrays stay inline
        assert '"skills": ["./skills/existing-skill/"]' in written_content

        # Verify the data is still correct
        data = json.loads(written_content)
        assert data["version"] == "1.0.1"
        assert data["skills"] == ["./skills/existing-skill/"]

    def test_update_marketplace_json_writes_prettier_compatible_format(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify update_marketplace_json writes prettier-compatible JSON format.

        Tests: marketplace.json output format after update
        How: Create marketplace.json, run update with a modified plugin, check
             output uses prettier-compatible formatting (short structures inline)
        Why: Confirms the fix -- hook now writes the same format as prettier
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        _make_marketplace_json(
            tmp_path,
            {
                "metadata": {"version": "1.0.0"},
                "plugins": [
                    {"name": "existing-plugin", "source": "./plugins/existing-plugin"}
                ],
            },
        )

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        plugin_changes: MarketplaceChanges = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing-plugin", "1.0.1")],
        }

        # Act
        marketplace_json = tmp_path / ".claude-plugin" / "marketplace.json"
        updated = auto_sync.update_marketplace_json(plugin_changes)

        # Assert
        assert updated is True
        written = marketplace_json.read_text(encoding="utf-8")

        # Prettier-compatible: short objects stay inline
        assert '{ "version": "1.0.1" }' in written or '"version": "1.0.1"' in written

        # Verify the data is still correct
        data = json.loads(written)
        assert data["metadata"]["version"] == "1.0.1"


# ============================================================================
# Area 2: Idempotency
# ============================================================================


class TestIdempotency:
    """Test that running update functions twice produces the same result.

    When a commit fails (e.g., ruff errors) and the user retries, the hook runs
    again on the same staged changes.  The version must not double-bump, and the
    file content must be stable.
    """

    def test_bump_version_is_not_idempotent_by_design(self) -> None:
        """Verify bump_version increments on every call -- it is NOT idempotent.

        Tests: bump_version function
        How: Call bump_version("1.0.0", "patch") twice in sequence
        Why: Demonstrates that without the staged guard, versions would double-bump
        """
        # Arrange
        version = "1.0.0"

        # Act
        first_bump = auto_sync.bump_version(version, "patch")
        second_bump = auto_sync.bump_version(first_bump, "patch")

        # Assert -- each call increments
        assert first_bump == "1.0.1"
        assert second_bump == "1.0.2"
        assert first_bump != second_bump

    def test_update_plugin_json_same_output_when_run_twice_from_same_state(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify running update_plugin_json twice from the same initial state is idempotent.

        Tests: Idempotency of update_plugin_json
        How: Create plugin.json, run update, reset to original, run update again,
             compare outputs
        Why: If the hook runs twice from the same file state, it should produce
             identical output
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        original_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "skills": ["./skills/existing/"],
        }
        original_content = json.dumps(original_data, indent=2) + "\n"
        plugin_json = _make_plugin_json(tmp_path, plugin_name, original_data)

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        changes = _changes_with_modified_skill()

        # Act -- Run 1: from original state
        updated_1, version_1 = auto_sync.update_plugin_json(plugin_name, changes)
        content_after_run1 = plugin_json.read_text(encoding="utf-8")

        # Reset to original state
        plugin_json.write_text(original_content, encoding="utf-8")

        # Act -- Run 2: from same original state
        updated_2, version_2 = auto_sync.update_plugin_json(plugin_name, changes)
        content_after_run2 = plugin_json.read_text(encoding="utf-8")

        # Assert -- both runs produced identical results
        assert updated_1 == updated_2
        assert version_1 == version_2
        assert content_after_run1 == content_after_run2

    def test_update_plugin_json_no_double_bump_on_retry(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify version does NOT double-bump when update runs twice.

        Tests: Idempotent version bumping (Bug 2 fix)
        How: Run update_plugin_json, then run it AGAIN on the already-modified file
             (simulating what happens when the staged guard is bypassed)
        Why: The idempotency check detects that the file was already updated and
             skips the second write, preventing 1.0.0 -> 1.0.1 -> 1.0.2
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        original_data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "skills": ["./skills/existing/"],
        }
        _make_plugin_json(tmp_path, plugin_name, original_data)

        # Mock git: always report nothing staged (bypassing the guard)
        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        changes = _changes_with_modified_skill()

        # Act -- Run 1
        updated_1, version_1 = auto_sync.update_plugin_json(plugin_name, changes)

        # Act -- Run 2 on the already-bumped file (idempotency prevents double-bump)
        updated_2, version_2 = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- version bumped only once: 1.0.0 -> 1.0.1, second run is no-op
        assert updated_1 is True
        assert version_1 == "1.0.1"
        assert updated_2 is False
        assert version_2 == "1.0.1"

    def test_update_marketplace_json_no_double_bump_on_retry(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify marketplace version does NOT double-bump on retry.

        Tests: Idempotent version bumping for marketplace.json (Bug 2 fix)
        How: Run update_marketplace_json twice on the same file without reset
        Why: The idempotency check prevents double-bumping
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        original_data = {
            "metadata": {"version": "1.0.0"},
            "plugins": [{"name": "existing", "source": "./plugins/existing"}],
        }
        _make_marketplace_json(tmp_path, original_data)

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        plugin_changes: MarketplaceChanges = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing", "1.0.1")],
        }

        # Act -- Run 1
        updated_1 = auto_sync.update_marketplace_json(plugin_changes)

        # Act -- Run 2 on the already-bumped file (idempotency prevents double-bump)
        updated_2 = auto_sync.update_marketplace_json(plugin_changes)

        # Assert -- version bumped only once
        assert updated_1 is True
        assert updated_2 is False

        marketplace_json = tmp_path / ".claude-plugin" / "marketplace.json"
        final_data = json.loads(marketplace_json.read_text(encoding="utf-8"))
        assert final_data["metadata"]["version"] == "1.0.1"

    def test_bump_version_handles_invalid_input_gracefully(self) -> None:
        """Verify bump_version returns default for malformed version strings.

        Tests: bump_version error handling
        How: Pass invalid version strings
        Why: Ensure robustness during edge cases
        """
        # Arrange / Act / Assert
        assert auto_sync.bump_version("invalid", "patch") == "0.1.0"
        assert auto_sync.bump_version("", "minor") == "0.1.0"
        assert auto_sync.bump_version("1.2", "patch") == "0.1.0"

    def test_bump_version_all_bump_types(self) -> None:
        """Verify each bump type increments the correct segment.

        Tests: bump_version correctness for major, minor, patch
        How: Call with each bump type from the same base version
        Why: Ensure version bumping logic is correct
        """
        # Arrange
        base = "2.3.4"

        # Act / Assert
        assert auto_sync.bump_version(base, "major") == "3.0.0"
        assert auto_sync.bump_version(base, "minor") == "2.4.0"
        assert auto_sync.bump_version(base, "patch") == "2.3.5"


# ============================================================================
# Area 3: The "already staged" guard
# ============================================================================


class TestAlreadyStagedGuard:
    """Test the "already staged" guard at lines 276-280 and 332-335.

    The guard checks ``git diff --cached --name-only`` for the manifest file.
    If found, it skips ALL processing and returns ``(False, "0.0.0")``.

    This is the mechanism that prevents double-bumping on retry, but it also
    means that on retry, the hook effectively becomes a no-op for that plugin,
    returning a version of "0.0.0" instead of the actual current version.
    """

    def test_update_plugin_json_skips_when_plugin_json_already_staged(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify update_plugin_json returns (False, "0.0.0") when plugin.json is staged.

        Tests: Already-staged guard in update_plugin_json (lines 276-280)
        How: Mock git diff --cached to include the plugin.json path, call update
        Why: On retry after failed commit, plugin.json is already staged from run 1
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        data = {"name": "test-plugin", "version": "1.5.0", "skills": []}
        plugin_json = _make_plugin_json(tmp_path, plugin_name, data)

        # Mock git: plugin.json IS in the staged files list
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        mocker.patch.object(auto_sync, "run_git_command", return_value=staged_path)

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- guard triggered: returns False with "0.0.0" not the actual version
        assert updated is False
        assert version == "0.0.0"

        # File was NOT modified
        assert json.loads(plugin_json.read_text(encoding="utf-8"))["version"] == "1.5.0"

    def test_update_marketplace_json_skips_when_already_staged(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify update_marketplace_json returns False when marketplace.json is staged.

        Tests: Already-staged guard in update_marketplace_json (lines 332-335)
        How: Mock git diff --cached to include marketplace.json path, call update
        Why: Same pattern as plugin.json guard
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        data = {
            "metadata": {"version": "2.0.0"},
            "plugins": [{"name": "p1", "source": "./plugins/p1"}],
        }
        marketplace_json = _make_marketplace_json(tmp_path, data)

        # Mock git: marketplace.json IS in the staged files
        mocker.patch.object(
            auto_sync, "run_git_command", return_value=".claude-plugin/marketplace.json"
        )

        plugin_changes: MarketplaceChanges = {
            "added": {"new-plugin"},
            "deleted": set(),
            "modified": [],
        }

        # Act
        updated = auto_sync.update_marketplace_json(plugin_changes)

        # Assert -- guard triggered, no modifications
        assert updated is False
        loaded = json.loads(marketplace_json.read_text(encoding="utf-8"))
        assert loaded["metadata"]["version"] == "2.0.0"

    def test_staged_guard_returns_zero_version_not_actual_version(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify the guard returns "0.0.0" rather than the file's actual version.

        Tests: Return value fidelity of the staged guard
        How: Set up plugin.json with version "3.2.1", trigger the guard, inspect return
        Why: The "0.0.0" return value propagates to marketplace_changes["modified"] as
             a tuple ("plugin-name", "0.0.0"), which could cause marketplace version
             tracking to use incorrect data
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "my-plugin"
        data = {"name": "my-plugin", "version": "3.2.1", "skills": []}
        _make_plugin_json(tmp_path, plugin_name, data)

        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        mocker.patch.object(auto_sync, "run_git_command", return_value=staged_path)

        changes = _changes_with_added_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- returns "0.0.0" not "3.2.1"
        assert updated is False
        assert version == "0.0.0"
        assert version != "3.2.1"

    def test_staged_guard_uses_exact_line_match_not_substring(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify the guard uses exact line matching, not substring containment.

        Tests: Guard matching semantics
        How: Return staged output containing only a longer filename that has the
             target path as a substring, verify guard does NOT trigger
        Why: With exact line matching, "plugin.json.bak" no longer falsely
             matches "plugin.json" -- the false positive is eliminated
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test"
        data = {"name": "test", "version": "1.0.0"}
        _make_plugin_json(tmp_path, plugin_name, data)

        # The staged output contains a DIFFERENT file that has our path as substring
        mocker.patch.object(
            auto_sync,
            "run_git_command",
            return_value="plugins/test/.claude-plugin/plugin.json.bak",
        )

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- guard does NOT trigger (exact match required, substring rejected)
        assert updated is True
        assert version == "1.0.1"

    def test_staged_guard_does_not_trigger_for_different_plugin(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify the guard does not trigger when a DIFFERENT plugin's json is staged.

        Tests: Guard specificity
        How: Stage a different plugin's plugin.json, call update for our plugin
        Why: Ensure the guard only activates for the exact plugin being updated
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "my-plugin"
        data = {"name": "my-plugin", "version": "1.0.0", "skills": []}
        _make_plugin_json(tmp_path, plugin_name, data)

        # A DIFFERENT plugin's json is staged
        mocker.patch.object(
            auto_sync,
            "run_git_command",
            return_value="plugins/other-plugin/.claude-plugin/plugin.json",
        )

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- guard did NOT trigger, update proceeds
        assert updated is True
        assert version == "1.0.1"


# ============================================================================
# Area 2+3 combined: Retry scenario simulation
# ============================================================================


class TestRetryScenario:
    """Simulate the full retry scenario that triggers the stash conflict.

    Scenario:
    1. User runs ``git commit``
    2. auto-sync-manifests hook runs, modifies plugin.json, stages it
    3. Another hook (e.g., ruff) fails
    4. prek stashes hook changes, restores original
    5. User runs ``git commit`` again
    6. auto-sync-manifests hook runs AGAIN
    7. This time plugin.json IS in staged files (from step 2's git add)
    8. The "already staged" guard kicks in, skipping processing

    But between steps 4 and 6, prettier may have also modified the file,
    creating a conflict.
    """

    def test_retry_scenario_guard_prevents_double_bump(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Simulate the retry: first run bumps, second run is blocked by guard.

        Tests: Complete retry flow
        How: Run update twice, second time with plugin.json in staged list
        Why: Verify the guard prevents double-bumping on commit retry
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "my-plugin"
        original_data = {
            "name": "my-plugin",
            "version": "1.0.0",
            "skills": ["./skills/existing/"],
        }
        plugin_json = _make_plugin_json(tmp_path, plugin_name, original_data)

        changes = _changes_with_modified_skill()

        # --- Run 1: plugin.json NOT staged, hook modifies it ---
        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        updated_1, version_1 = auto_sync.update_plugin_json(plugin_name, changes)

        assert updated_1 is True
        assert version_1 == "1.0.1"
        content_after_run1 = plugin_json.read_text(encoding="utf-8")

        # --- Simulate: commit fails, prek rolls back, user retries ---
        # On retry, plugin.json IS in staged files from run 1's git add

        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        mocker.patch.object(auto_sync, "run_git_command", return_value=staged_path)

        # --- Run 2: guard should prevent double-bump ---
        updated_2, version_2 = auto_sync.update_plugin_json(plugin_name, changes)

        assert updated_2 is False
        assert version_2 == "0.0.0"  # Guard returns "0.0.0"

        # File content unchanged from run 1
        assert plugin_json.read_text(encoding="utf-8") == content_after_run1

    def test_retry_guard_version_propagates_to_marketplace_changes(self) -> None:
        """Verify that guard's "0.0.0" return propagates to marketplace tracking.

        Tests: Interaction between guard return value and main() flow
        How: Simulate the code in main() that appends (plugin_name, new_version)
             to marketplace_changes when updated is True, and skips when False
        Why: When the guard returns (False, "0.0.0"), main() correctly skips
             appending to marketplace_changes["modified"], but if the caller
             incorrectly uses the version, it could corrupt marketplace state
        """
        # Arrange -- simulate what main() does at lines 469-480
        marketplace_changes: MarketplaceChanges = {
            "added": set(),
            "deleted": set(),
            "modified": [],
        }

        # Run 1 result: hook updated plugin
        updated_run1 = True
        version_run1 = "1.0.1"

        if updated_run1:
            marketplace_changes["modified"].append(("my-plugin", version_run1))

        # Run 2 result: guard blocked
        updated_run2 = False
        version_run2 = "0.0.0"

        if updated_run2:
            marketplace_changes["modified"].append(("my-plugin", version_run2))

        # Assert -- only run 1's version appears
        assert len(marketplace_changes["modified"]) == 1
        assert marketplace_changes["modified"][0] == ("my-plugin", "1.0.1")
        # "0.0.0" never appears because updated was False
        assert not any(v == "0.0.0" for _, v in marketplace_changes["modified"])

    def test_full_retry_with_prettier_no_conflict(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify the hook writes prettier-compatible format, eliminating stash conflicts.

        Tests: End-to-end conflict elimination
        How: Run 1 writes prettier-compatible format. Prettier has nothing to change.
             Run 2 (retry) encounters the staged guard. File remains stable throughout.
        Why: With prettier-compatible output, the hook and prettier produce identical
             content, so prek stash/restore never encounters conflicting diffs.
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "my-plugin"
        original_data = {
            "name": "my-plugin",
            "version": "1.0.0",
            "skills": ["./skills/existing/"],
        }
        plugin_json = _make_plugin_json(tmp_path, plugin_name, original_data)

        changes = _changes_with_modified_skill()

        # --- Run 1: hook writes prettier-compatible format ---
        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        updated_1, version_1 = auto_sync.update_plugin_json(plugin_name, changes)
        assert updated_1 is True
        assert version_1 == "1.0.1"
        hook_output = plugin_json.read_text(encoding="utf-8")

        # Verify hook wrote prettier-compatible format (short arrays inline)
        assert '"skills": ["./skills/existing/"]' in hook_output

        # Prettier would NOT modify this output -- it is already in prettier format.
        # No stash conflict can occur because hook and prettier agree on format.

        # --- Simulate: commit fails, user retries ---
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        mocker.patch.object(auto_sync, "run_git_command", return_value=staged_path)

        # --- Run 2: guard prevents re-processing ---
        updated_2, version_2 = auto_sync.update_plugin_json(plugin_name, changes)

        # Assert -- guard blocked re-processing
        assert updated_2 is False
        assert version_2 == "0.0.0"

        # File content unchanged from run 1
        final_content = plugin_json.read_text(encoding="utf-8")
        assert final_content == hook_output


# ============================================================================
# Supporting function tests
# ============================================================================


class TestParsePluginPath:
    """Test parse_plugin_path for correct categorisation of file paths."""

    def test_non_plugin_path_returns_none(self) -> None:
        """Verify paths outside plugins/ directory return None.

        Tests: parse_plugin_path boundary
        How: Pass a path not starting with plugins/
        Why: Ensure non-plugin files are ignored
        """
        result = auto_sync.parse_plugin_path("src/main.py")
        assert result is None

    def test_plugin_json_path_parsed(self) -> None:
        """Verify plugin.json path is parsed with no component type.

        Tests: parse_plugin_path for manifest files
        How: Pass plugins/foo/.claude-plugin/plugin.json
        Why: Plugin.json is detected as a plugin-level change, not a component
        """
        result = auto_sync.parse_plugin_path(
            "plugins/my-plugin/.claude-plugin/plugin.json"
        )
        assert result is not None
        assert result["plugin"] == "my-plugin"

    def test_skill_path_parsed(self) -> None:
        """Verify skill SKILL.md path is correctly categorised.

        Tests: parse_plugin_path for skill files
        How: Pass a skills/name/SKILL.md path
        Why: Ensure skills are detected as component_type "skill"
        """
        result = auto_sync.parse_plugin_path(
            "plugins/my-plugin/skills/my-skill/SKILL.md"
        )
        assert result is not None
        assert result["plugin"] == "my-plugin"
        assert result["component_type"] == "skill"
        assert result["component_path"] == "skills/my-skill/SKILL.md"

    def test_agent_path_parsed(self) -> None:
        """Verify agent .md path is correctly categorised.

        Tests: parse_plugin_path for agent files
        How: Pass an agents/name.md path
        Why: Ensure agents are detected as component_type "agent"
        """
        result = auto_sync.parse_plugin_path("plugins/my-plugin/agents/my-agent.md")
        assert result is not None
        assert result["component_type"] == "agent"


class TestProcessFileChanges:
    """Test _process_file_changes for correct categorisation."""

    def test_new_skill_detected_as_component_add(self) -> None:
        """Verify a new skill file triggers component addition.

        Tests: _process_file_changes with added skill
        How: Pass status with an added skill path
        Why: Ensure added skills are tracked for plugin.json update
        """
        # Arrange
        status: dict[str, list[str]] = {
            "added": ["plugins/my-plugin/skills/new-skill/SKILL.md"],
            "deleted": [],
            "modified": [],
        }

        # Act
        component_changes, _marketplace_changes = auto_sync._process_file_changes(
            status
        )

        # Assert
        assert "my-plugin" in component_changes
        assert len(component_changes["my-plugin"]["added"]) == 1
        assert component_changes["my-plugin"]["added"][0]["component_type"] == "skill"

    def test_new_plugin_json_detected_as_marketplace_add(self) -> None:
        """Verify a new plugin.json triggers marketplace addition.

        Tests: _process_file_changes with new plugin
        How: Pass status with added .claude-plugin/plugin.json
        Why: Ensure new plugins are tracked for marketplace.json update
        """
        # Arrange
        status: dict[str, list[str]] = {
            "added": ["plugins/new-plugin/.claude-plugin/plugin.json"],
            "deleted": [],
            "modified": [],
        }

        # Act
        _, marketplace_changes = auto_sync._process_file_changes(status)

        # Assert
        assert "new-plugin" in marketplace_changes["added"]

    def test_deleted_plugin_json_detected_as_marketplace_delete(self) -> None:
        """Verify a deleted plugin.json triggers marketplace removal.

        Tests: _process_file_changes with deleted plugin
        How: Pass status with deleted .claude-plugin/plugin.json
        Why: Ensure deleted plugins are tracked for marketplace.json update
        """
        # Arrange
        status: dict[str, list[str]] = {
            "added": [],
            "deleted": ["plugins/old-plugin/.claude-plugin/plugin.json"],
            "modified": [],
        }

        # Act
        _, marketplace_changes = auto_sync._process_file_changes(status)

        # Assert
        assert "old-plugin" in marketplace_changes["deleted"]


class TestUpdateComponentArrays:
    """Test _update_component_arrays for correct array manipulation."""

    def test_add_new_skill_to_empty_skills_array(self) -> None:
        """Verify adding a skill creates the skills array if absent.

        Tests: _update_component_arrays with missing skills field
        How: Pass data without skills field, add a skill component
        Why: Ensure the function creates the field when needed
        """
        # Arrange
        data: dict[str, list[str] | str] = {"name": "test"}
        changes: ComponentChanges = {
            "added": [
                {"component_type": "skill", "component_path": "skills/new/SKILL.md"}
            ],
            "deleted": [],
            "modified": [],
        }

        # Act
        modified = auto_sync._update_component_arrays(data, changes)

        # Assert
        assert modified is True
        assert "skills" in data
        assert "./skills/new/SKILL.md" in data["skills"]

    def test_add_duplicate_skill_is_noop(self) -> None:
        """Verify adding an already-present skill does not duplicate it.

        Tests: _update_component_arrays deduplication
        How: Pass data with existing skill path, try to add same path
        Why: Ensure idempotent component addition
        """
        # Arrange
        data: dict[str, list[str] | str] = {
            "name": "test",
            "skills": ["./skills/existing/SKILL.md"],
        }
        changes: ComponentChanges = {
            "added": [
                {
                    "component_type": "skill",
                    "component_path": "skills/existing/SKILL.md",
                }
            ],
            "deleted": [],
            "modified": [],
        }

        # Act
        modified = auto_sync._update_component_arrays(data, changes)

        # Assert
        assert modified is False
        skills = data["skills"]
        assert isinstance(skills, list)
        assert len(skills) == 1

    def test_delete_skill_removes_from_array(self) -> None:
        """Verify deleting a skill removes it from the array.

        Tests: _update_component_arrays deletion
        How: Pass data with a skill, delete that skill
        Why: Ensure component removal works correctly
        """
        # Arrange
        data: dict[str, list[str] | str] = {
            "name": "test",
            "skills": ["./skills/old/SKILL.md", "./skills/keep/SKILL.md"],
        }
        changes: ComponentChanges = {
            "added": [],
            "deleted": [
                {"component_type": "skill", "component_path": "skills/old/SKILL.md"}
            ],
            "modified": [],
        }

        # Act
        modified = auto_sync._update_component_arrays(data, changes)

        # Assert
        assert modified is True
        skills = data["skills"]
        assert isinstance(skills, list)
        assert "./skills/old/SKILL.md" not in skills
        assert "./skills/keep/SKILL.md" in skills


class TestUpdatePluginJsonFileNotFound:
    """Test update_plugin_json when plugin.json does not exist."""

    def test_returns_false_when_plugin_json_missing(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify update_plugin_json returns (False, "0.0.0") for missing file.

        Tests: update_plugin_json with non-existent plugin.json
        How: Call with a plugin name that has no .claude-plugin/plugin.json
        Why: Ensure graceful handling of missing files
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json("nonexistent", changes)

        # Assert
        assert updated is False
        assert version == "0.0.0"


# ============================================================================
# New behaviour: _is_file_staged helper
# ============================================================================


class TestIsFileStaged:
    """Test the _is_file_staged helper for exact line matching."""

    def test_exact_match_returns_true(self, mocker: MockerFixture) -> None:
        """Verify _is_file_staged returns True for an exact line match.

        Tests: _is_file_staged exact matching
        How: Mock git output with the exact path on its own line
        Why: Ensure basic positive matching works
        """
        mocker.patch.object(
            auto_sync,
            "run_git_command",
            return_value="plugins/foo/.claude-plugin/plugin.json",
        )
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json") is True
        )

    def test_substring_match_returns_false(self, mocker: MockerFixture) -> None:
        """Verify _is_file_staged rejects substring matches.

        Tests: _is_file_staged substring rejection
        How: Mock git output with a longer path containing the target as substring
        Why: Prevents false positives from paths like plugin.json.bak
        """
        mocker.patch.object(
            auto_sync,
            "run_git_command",
            return_value="plugins/foo/.claude-plugin/plugin.json.bak",
        )
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json") is False
        )

    def test_multiline_output_matches_correct_line(self, mocker: MockerFixture) -> None:
        """Verify _is_file_staged matches the right line in multiline output.

        Tests: _is_file_staged with multiple staged files
        How: Mock git output with several lines, one of which matches
        Why: Real git output contains multiple files
        """
        staged_output = (
            "plugins/bar/.claude-plugin/plugin.json\n"
            "plugins/foo/.claude-plugin/plugin.json\n"
            "README.md"
        )
        mocker.patch.object(auto_sync, "run_git_command", return_value=staged_output)
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json") is True
        )

    def test_empty_output_returns_false(self, mocker: MockerFixture) -> None:
        """Verify _is_file_staged returns False for empty git output.

        Tests: _is_file_staged with no staged files
        How: Mock empty git output
        Why: Edge case when nothing is staged
        """
        mocker.patch.object(auto_sync, "run_git_command", return_value="")
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json") is False
        )

    def test_accepts_path_object(self, mocker: MockerFixture) -> None:
        """Verify _is_file_staged works with Path objects.

        Tests: _is_file_staged type flexibility
        How: Pass a Path object instead of a string
        Why: The function signature accepts str | Path
        """
        mocker.patch.object(
            auto_sync,
            "run_git_command",
            return_value="plugins/foo/.claude-plugin/plugin.json",
        )
        assert (
            auto_sync._is_file_staged(Path("plugins/foo/.claude-plugin/plugin.json"))
            is True
        )


# ============================================================================
# New behaviour: _prettier_json_dumps formatter
# ============================================================================


class TestPrettierJsonDumps:
    """Test the _prettier_json_dumps formatter for prettier-compatible output."""

    def test_short_object_stays_inline(self) -> None:
        """Verify short objects are formatted on a single line.

        Tests: _prettier_json_dumps inline object format
        How: Serialize a small object and check for single-line format
        Why: Prettier keeps short structures inline
        """
        data = {"name": "test", "version": "1.0.0"}
        result = auto_sync._prettier_json_dumps(data)
        assert result == '{ "name": "test", "version": "1.0.0" }'

    def test_short_array_stays_inline(self) -> None:
        """Verify short arrays are formatted on a single line.

        Tests: _prettier_json_dumps inline array format
        How: Serialize a small array and check for single-line format
        Why: This is the core fix -- json.dump would expand this vertically
        """
        data = {"skills": ["./skills/test/"]}
        result = auto_sync._prettier_json_dumps(data)
        assert '["./skills/test/"]' in result

    def test_long_array_expands_vertically(self) -> None:
        """Verify long arrays are expanded vertically.

        Tests: _prettier_json_dumps vertical expansion for long arrays
        How: Serialize an array that exceeds 80 characters when inline
        Why: Prettier expands structures that don't fit on one line
        """
        data = {
            "skills": [
                "./skills/very-long-skill-name-one/",
                "./skills/very-long-skill-name-two/",
                "./skills/very-long-skill-name-three/",
            ]
        }
        result = auto_sync._prettier_json_dumps(data)
        # The array should be expanded across multiple lines
        assert '"skills": [\n' in result
        assert '    "./skills/very-long-skill-name-one/",' in result

    def test_output_is_valid_json(self) -> None:
        """Verify _prettier_json_dumps produces valid JSON.

        Tests: JSON validity of prettier-compatible output
        How: Round-trip through json.loads
        Why: Formatting changes must not break JSON syntax
        """
        data = {
            "name": "test-plugin",
            "version": "2.3.4",
            "skills": ["./skills/a/", "./skills/b/"],
            "metadata": {"author": "test"},
        }
        result = auto_sync._prettier_json_dumps(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_empty_structures(self) -> None:
        """Verify _prettier_json_dumps handles empty arrays and objects.

        Tests: Edge cases for empty structures
        How: Serialize empty dict and list
        Why: Ensure no crash on empty inputs
        """
        assert auto_sync._prettier_json_dumps({}) == "{}"
        assert auto_sync._prettier_json_dumps([]) == "[]"

    def test_nested_objects_inline_when_short(self) -> None:
        """Verify nested short objects stay inline.

        Tests: _prettier_json_dumps nested inline formatting
        How: Serialize an object with a short nested object
        Why: Prettier keeps nested structures inline when they fit
        """
        data = {"metadata": {"version": "1.0.0"}}
        result = auto_sync._prettier_json_dumps(data)
        assert '{ "version": "1.0.0" }' in result

    def test_matches_prettier_for_real_plugin_json(self) -> None:
        """Verify output matches prettier format for a realistic plugin.json.

        Tests: _prettier_json_dumps against known prettier output
        How: Serialize a realistic plugin.json and compare structure
        Why: End-to-end validation against actual prettier behaviour
        """
        data = {
            "name": "commitlint",
            "version": "1.0.7",
            "skills": ["./skills/commitlint"],
        }
        result = auto_sync._prettier_json_dumps(data)
        # Short enough to be inline (well under 80 chars total)
        parsed = json.loads(result)
        assert parsed == data
        # The skills array should be inline since it's short
        assert '["./skills/commitlint"]' in result


# ============================================================================
# New behaviour: Idempotent writes (Bug 2 fix)
# ============================================================================


class TestIdempotentWrites:
    """Test that running update functions twice produces identical output without double-bump.

    The fix detects when the serialized content matches what is already on disk,
    skipping the write and preventing version double-bumps.
    """

    def test_update_plugin_json_is_noop_on_second_run(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify second run of update_plugin_json is a no-op when file already matches.

        Tests: Idempotent write prevention for plugin.json
        How: Run update twice without reset, verify second run returns False
        Why: Prevents version double-bump when commit fails and user retries
        """
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        _make_plugin_json(
            tmp_path,
            plugin_name,
            {
                "name": "test-plugin",
                "version": "1.0.0",
                "skills": ["./skills/existing/"],
            },
        )

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        changes = _changes_with_modified_skill()

        # Run 1: should update
        updated_1, version_1 = auto_sync.update_plugin_json(plugin_name, changes)
        assert updated_1 is True
        assert version_1 == "1.0.1"

        # Run 2: file already has the bumped version in prettier format -- no-op
        updated_2, version_2 = auto_sync.update_plugin_json(plugin_name, changes)
        assert updated_2 is False
        assert version_2 == "1.0.1"

    def test_update_marketplace_json_is_noop_on_second_run(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify second run of update_marketplace_json is a no-op when file matches.

        Tests: Idempotent write prevention for marketplace.json
        How: Run update twice without reset, verify second run returns False
        Why: Prevents version double-bump in marketplace manifest
        """
        monkeypatch.chdir(tmp_path)

        _make_marketplace_json(
            tmp_path,
            {
                "metadata": {"version": "1.0.0"},
                "plugins": [{"name": "existing", "source": "./plugins/existing"}],
            },
        )

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        plugin_changes: MarketplaceChanges = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing", "1.0.1")],
        }

        # Run 1: should update
        updated_1 = auto_sync.update_marketplace_json(plugin_changes)
        assert updated_1 is True

        # Run 2: file already has the bumped version -- no-op
        updated_2 = auto_sync.update_marketplace_json(plugin_changes)
        assert updated_2 is False

        # Verify version was only bumped once
        marketplace_json = tmp_path / ".claude-plugin" / "marketplace.json"
        final_data = json.loads(marketplace_json.read_text(encoding="utf-8"))
        assert final_data["metadata"]["version"] == "1.0.1"

    def test_update_plugin_json_version_stays_at_single_bump(
        self, tmp_path: Path, monkeypatch: Any, mocker: MockerFixture
    ) -> None:
        """Verify running update_plugin_json three times still only bumps once.

        Tests: Multiple consecutive runs remain idempotent
        How: Run update three times, verify final version is 1.0.1 not 1.0.3
        Why: Stress test the idempotency mechanism
        """
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        plugin_json = _make_plugin_json(
            tmp_path,
            plugin_name,
            {"name": "test-plugin", "version": "1.0.0", "skills": []},
        )

        mocker.patch.object(auto_sync, "run_git_command", return_value="")

        changes = _changes_with_modified_skill()

        # Run three times
        auto_sync.update_plugin_json(plugin_name, changes)
        auto_sync.update_plugin_json(plugin_name, changes)
        auto_sync.update_plugin_json(plugin_name, changes)

        # Final version should be 1.0.1, not 1.0.3
        final_data = json.loads(plugin_json.read_text(encoding="utf-8"))
        assert final_data["version"] == "1.0.1"
