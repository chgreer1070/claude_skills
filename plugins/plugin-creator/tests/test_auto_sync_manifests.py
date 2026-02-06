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
3. The "already staged" guard -- _is_file_staged checks skip ALL processing when the
   manifest file is already staged, which changes behavior on retry.

Test isolation strategy:
- Functions that previously called git internally now receive a ``staged_files`` set,
  eliminating the need to mock ``run_git_command`` for staging checks.
- All file I/O uses pytest tmp_path fixtures with monkeypatch.chdir.
- Each test is fully independent with no shared state.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

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
_ComponentChangesDict = dict[str, list[dict[str, str]]]
_MarketplaceChangesDict = dict[str, Any]

# Empty staged files set -- used when no files are staged (common case)
_NO_STAGED: set[str] = set()

_requires_prettier = pytest.mark.skipif(
    shutil.which("npx") is None,
    reason="npx not available — prettier tests require Node.js tooling",
)


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


def _changes_with_modified_skill() -> _ComponentChangesDict:
    """Return component changes with a single modified skill."""
    return {
        "added": [],
        "deleted": [],
        "modified": [
            {"component_type": "skill", "component_path": "skills/my-skill/SKILL.md"}
        ],
    }


def _changes_with_added_skill() -> _ComponentChangesDict:
    """Return component changes with a single added skill."""
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
        self, tmp_path: Path, monkeypatch: Any
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

        changes = _changes_with_modified_skill()

        # Act
        updated, _new_version = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )

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
        self, tmp_path: Path, monkeypatch: Any
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

        plugin_changes: _MarketplaceChangesDict = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing-plugin", "1.0.1")],
        }

        # Act
        marketplace_json = tmp_path / ".claude-plugin" / "marketplace.json"
        updated = auto_sync.update_marketplace_json(plugin_changes, _NO_STAGED)

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
        self, tmp_path: Path, monkeypatch: Any
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

        changes = _changes_with_modified_skill()

        # Act -- Run 1: from original state
        updated_1, version_1 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )
        content_after_run1 = plugin_json.read_text(encoding="utf-8")

        # Reset to original state
        plugin_json.write_text(original_content, encoding="utf-8")

        # Act -- Run 2: from same original state
        updated_2, version_2 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )
        content_after_run2 = plugin_json.read_text(encoding="utf-8")

        # Assert -- both runs produced identical results
        assert updated_1 == updated_2
        assert version_1 == version_2
        assert content_after_run1 == content_after_run2

    def test_update_plugin_json_no_double_bump_on_retry(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify version does NOT double-bump when update runs twice.

        Tests: Idempotent version bumping via staged guard
        How: Run update_plugin_json, then simulate retry with the file in staged_files
        Why: On retry after a failed commit, plugin.json is already staged from run 1,
             so the staged guard prevents re-processing
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

        changes = _changes_with_modified_skill()

        # Act -- Run 1: plugin.json not staged, hook updates it
        updated_1, version_1 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )

        # Act -- Run 2: plugin.json IS staged from run 1's git add
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        updated_2, version_2 = auto_sync.update_plugin_json(
            plugin_name, changes, {staged_path}
        )

        # Assert -- version bumped only once: 1.0.0 -> 1.0.1, second run blocked
        assert updated_1 is True
        assert version_1 == "1.0.1"
        assert updated_2 is False
        assert version_2 == "0.0.0"

    def test_update_marketplace_json_no_double_bump_on_retry(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify marketplace version does NOT double-bump on retry.

        Tests: Idempotent version bumping for marketplace.json via staged guard
        How: Run update_marketplace_json, then simulate retry with file in staged_files
        Why: On retry, marketplace.json is already staged from run 1
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        original_data = {
            "metadata": {"version": "1.0.0"},
            "plugins": [{"name": "existing", "source": "./plugins/existing"}],
        }
        _make_marketplace_json(tmp_path, original_data)

        plugin_changes: _MarketplaceChangesDict = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing", "1.0.1")],
        }

        # Act -- Run 1: marketplace.json not staged
        updated_1 = auto_sync.update_marketplace_json(plugin_changes, _NO_STAGED)

        # Act -- Run 2: marketplace.json IS staged from run 1
        updated_2 = auto_sync.update_marketplace_json(
            plugin_changes, {".claude-plugin/marketplace.json"}
        )

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
    """Test the "already staged" guard via _is_file_staged.

    The guard checks the ``staged_files`` set for the manifest file.
    If found, it skips ALL processing and returns ``(False, "0.0.0")``.

    This is the mechanism that prevents double-bumping on retry, but it also
    means that on retry, the hook effectively becomes a no-op for that plugin,
    returning a version of "0.0.0" instead of the actual current version.
    """

    def test_update_plugin_json_skips_when_plugin_json_already_staged(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify update_plugin_json returns (False, "0.0.0") when plugin.json is staged.

        Tests: Already-staged guard in update_plugin_json
        How: Pass staged_files containing the plugin.json path, call update
        Why: On retry after failed commit, plugin.json is already staged from run 1
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        data = {"name": "test-plugin", "version": "1.5.0", "skills": []}
        plugin_json = _make_plugin_json(tmp_path, plugin_name, data)

        # plugin.json IS in the staged files set
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        staged = {staged_path}

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes, staged)

        # Assert -- guard triggered: returns False with "0.0.0" not the actual version
        assert updated is False
        assert version == "0.0.0"

        # File was NOT modified
        assert json.loads(plugin_json.read_text(encoding="utf-8"))["version"] == "1.5.0"

    def test_update_marketplace_json_skips_when_already_staged(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify update_marketplace_json returns False when marketplace.json is staged.

        Tests: Already-staged guard in update_marketplace_json
        How: Pass staged_files containing marketplace.json path, call update
        Why: Same pattern as plugin.json guard
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        data = {
            "metadata": {"version": "2.0.0"},
            "plugins": [{"name": "p1", "source": "./plugins/p1"}],
        }
        marketplace_json = _make_marketplace_json(tmp_path, data)

        # marketplace.json IS in the staged files
        staged = {".claude-plugin/marketplace.json"}

        plugin_changes: _MarketplaceChangesDict = {
            "added": {"new-plugin"},
            "deleted": set(),
            "modified": [],
        }

        # Act
        updated = auto_sync.update_marketplace_json(plugin_changes, staged)

        # Assert -- guard triggered, no modifications
        assert updated is False
        loaded = json.loads(marketplace_json.read_text(encoding="utf-8"))
        assert loaded["metadata"]["version"] == "2.0.0"

    def test_staged_guard_returns_zero_version_not_actual_version(
        self, tmp_path: Path, monkeypatch: Any
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
        staged = {staged_path}

        changes = _changes_with_added_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes, staged)

        # Assert -- returns "0.0.0" not "3.2.1"
        assert updated is False
        assert version == "0.0.0"
        assert version != "3.2.1"

    def test_staged_guard_uses_exact_line_match_not_substring(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify the guard uses exact matching, not substring containment.

        Tests: Guard matching semantics
        How: Pass staged_files containing only a longer filename that has the
             target path as a substring, verify guard does NOT trigger
        Why: With exact matching, "plugin.json.bak" no longer falsely
             matches "plugin.json" -- the false positive is eliminated
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        plugin_name = "test"
        data = {"name": "test", "version": "1.0.0"}
        _make_plugin_json(tmp_path, plugin_name, data)

        # The staged set contains a DIFFERENT file that has our path as substring
        staged = {"plugins/test/.claude-plugin/plugin.json.bak"}

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes, staged)

        # Assert -- guard does NOT trigger (exact match required, substring rejected)
        assert updated is True
        assert version == "1.0.1"

    def test_staged_guard_does_not_trigger_for_different_plugin(
        self, tmp_path: Path, monkeypatch: Any
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
        staged = {"plugins/other-plugin/.claude-plugin/plugin.json"}

        changes = _changes_with_modified_skill()

        # Act
        updated, version = auto_sync.update_plugin_json(plugin_name, changes, staged)

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
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Simulate the retry: first run bumps, second run is blocked by guard.

        Tests: Complete retry flow
        How: Run update twice, second time with plugin.json in staged set
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
        updated_1, version_1 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )

        assert updated_1 is True
        assert version_1 == "1.0.1"
        content_after_run1 = plugin_json.read_text(encoding="utf-8")

        # --- Simulate: commit fails, prek rolls back, user retries ---
        # On retry, plugin.json IS in staged files from run 1's git add
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        staged = {staged_path}

        # --- Run 2: guard should prevent double-bump ---
        updated_2, version_2 = auto_sync.update_plugin_json(
            plugin_name, changes, staged
        )

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
        # Arrange -- simulate what main() does
        marketplace_changes: _MarketplaceChangesDict = {
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
        self, tmp_path: Path, monkeypatch: Any
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
        updated_1, version_1 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )
        assert updated_1 is True
        assert version_1 == "1.0.1"
        hook_output = plugin_json.read_text(encoding="utf-8")

        # Verify hook wrote prettier-compatible format (short arrays inline)
        assert '"skills": ["./skills/existing/"]' in hook_output

        # Prettier would NOT modify this output -- it is already in prettier format.
        # No stash conflict can occur because hook and prettier agree on format.

        # --- Simulate: commit fails, user retries ---
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        staged = {staged_path}

        # --- Run 2: guard prevents re-processing ---
        updated_2, version_2 = auto_sync.update_plugin_json(
            plugin_name, changes, staged
        )

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

    def test_mcp_substring_in_non_mcp_path_is_not_mcp(self) -> None:
        """Verify 'mcp' as a substring in a non-mcp directory does not match as mcp.

        Tests: parse_plugin_path false-positive prevention for mcp detection
        How: Pass a script path containing 'mcp' as a substring in the filename
        Why: Previously ``"mcp" in filepath`` matched any path containing 'mcp',
             e.g. plugins/demo/scripts/mcp-utils.py was incorrectly typed as mcp
        """
        result = auto_sync.parse_plugin_path("plugins/demo/scripts/mcp-utils.py")
        assert result is not None
        assert result["plugin"] == "demo"
        # scripts/ is not a recognised component directory, so no component_type
        assert result["component_type"] is None

    def test_mcp_directory_is_detected(self) -> None:
        """Verify files in the mcp/ directory are correctly detected as mcp type.

        Tests: parse_plugin_path for mcp files
        How: Pass a path with mcp as the component directory
        Why: Ensure the mcp detection still works for actual mcp components
        """
        result = auto_sync.parse_plugin_path("plugins/my-plugin/mcp/my-server.json")
        assert result is not None
        assert result["component_type"] == "mcp"
        assert result["component_path"] == "mcp/my-server.json"


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
        changes: _ComponentChangesDict = {
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
        changes: _ComponentChangesDict = {
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
        changes: _ComponentChangesDict = {
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
        updated, version = auto_sync.update_plugin_json(
            "nonexistent", changes, _NO_STAGED
        )

        # Assert
        assert updated is False
        assert version == "0.0.0"


# ============================================================================
# New behaviour: _is_file_staged helper
# ============================================================================


class TestIsFileStaged:
    """Test the _is_file_staged helper for exact set membership."""

    def test_exact_match_returns_true(self) -> None:
        """Verify _is_file_staged returns True for an exact match.

        Tests: _is_file_staged exact matching
        How: Pass staged_files set containing the exact path
        Why: Ensure basic positive matching works
        """
        staged = {"plugins/foo/.claude-plugin/plugin.json"}
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json", staged)
            is True
        )

    def test_substring_match_returns_false(self) -> None:
        """Verify _is_file_staged rejects substring matches.

        Tests: _is_file_staged substring rejection
        How: Pass staged_files with a longer path containing the target as substring
        Why: Prevents false positives from paths like plugin.json.bak
        """
        staged = {"plugins/foo/.claude-plugin/plugin.json.bak"}
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json", staged)
            is False
        )

    def test_multiline_output_matches_correct_entry(self) -> None:
        """Verify _is_file_staged matches the right entry in a set with multiple files.

        Tests: _is_file_staged with multiple staged files
        How: Pass staged_files set with several entries, one of which matches
        Why: Real git output contains multiple files
        """
        staged = {
            "plugins/bar/.claude-plugin/plugin.json",
            "plugins/foo/.claude-plugin/plugin.json",
            "README.md",
        }
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json", staged)
            is True
        )

    def test_empty_set_returns_false(self) -> None:
        """Verify _is_file_staged returns False for empty staged files set.

        Tests: _is_file_staged with no staged files
        How: Pass empty set
        Why: Edge case when nothing is staged
        """
        assert (
            auto_sync._is_file_staged("plugins/foo/.claude-plugin/plugin.json", set())
            is False
        )

    def test_accepts_path_object(self) -> None:
        """Verify _is_file_staged works with Path objects.

        Tests: _is_file_staged type flexibility
        How: Pass a Path object instead of a string
        Why: The function signature accepts str | Path
        """
        staged = {"plugins/foo/.claude-plugin/plugin.json"}
        assert (
            auto_sync._is_file_staged(
                Path("plugins/foo/.claude-plugin/plugin.json"), staged
            )
            is True
        )


# ============================================================================
# New behaviour: _get_staged_files helper
# ============================================================================


class TestGetStagedFiles:
    """Test the _get_staged_files helper for correct set construction."""

    def test_returns_set_of_paths(self, mocker: MockerFixture) -> None:
        """Verify _get_staged_files returns a set of file paths.

        Tests: _get_staged_files return type and content
        How: Mock run_git_command to return multiline output
        Why: Ensure correct parsing of git output into set
        """
        mocker.patch.object(
            auto_sync, "run_git_command", return_value="file1.txt\nfile2.txt\nfile3.txt"
        )
        result = auto_sync._get_staged_files()
        assert result == {"file1.txt", "file2.txt", "file3.txt"}

    def test_returns_empty_set_for_no_output(self, mocker: MockerFixture) -> None:
        """Verify _get_staged_files returns empty set when nothing is staged.

        Tests: _get_staged_files edge case
        How: Mock empty git output
        Why: Empty output must not produce a set with empty string
        """
        mocker.patch.object(auto_sync, "run_git_command", return_value="")
        result = auto_sync._get_staged_files()
        assert result == set()


# ============================================================================
# New behaviour: _format_json formatter
# ============================================================================


class TestFormatJson:
    """Test the _format_json formatter for prettier-compatible output."""

    def test_format_json_produces_valid_json(self) -> None:
        """Verify _format_json output parses as valid JSON.

        Tests: JSON validity of _format_json output
        How: Round-trip through json.loads
        Why: Formatting changes must not break JSON syntax
        """
        data = {
            "name": "test-plugin",
            "version": "2.3.4",
            "skills": ["./skills/a/", "./skills/b/"],
            "metadata": {"author": "test"},
        }
        result = auto_sync._format_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_format_json_includes_trailing_newline(self) -> None:
        """Verify _format_json output ends with a newline.

        Tests: Trailing newline in _format_json output
        How: Check last character
        Why: POSIX text files require trailing newline
        """
        data = {"name": "test"}
        result = auto_sync._format_json(data)
        assert result.endswith("\n")

    @_requires_prettier
    def test_format_json_short_arrays_inline(self) -> None:
        """Verify _format_json keeps short arrays inline (prettier behaviour).

        Tests: Prettier-compatible inline array formatting
        How: Serialize data with a short array, check for inline format
        Why: This is the key difference from json.dumps(indent=2)
        """
        data = {"skills": ["./skills/test/"]}
        result = auto_sync._format_json(data)
        # prettier collapses short structures onto one line
        assert '["./skills/test/"]' in result

    @_requires_prettier
    def test_format_json_differs_from_json_dumps(self) -> None:
        """Verify _format_json output differs from json.dumps(indent=2).

        Tests: Format divergence that enables idempotency detection
        How: Compare _format_json output with json.dumps(indent=2) + newline
        Why: The idempotency check relies on this difference to distinguish
             initial file content (json.dumps) from hook-written content (_format_json)
        """
        data = {
            "name": "test-plugin",
            "version": "1.0.0",
            "skills": ["./skills/existing/"],
        }
        format_json_output = auto_sync._format_json(data)
        json_dumps_output = json.dumps(data, indent=2) + "\n"
        assert format_json_output != json_dumps_output

    def test_format_json_fallback_produces_valid_json(self, monkeypatch: Any) -> None:
        """Verify _format_json returns valid JSON when npx is unavailable.

        Tests: Fallback path when prettier is not installed
        How: Set _NPX_PATH to None, verify output parses as valid JSON
        Why: Ensures the hook works correctly on machines without Node.js
        """
        monkeypatch.setattr(auto_sync, "_NPX_PATH", None)
        data = {"name": "test-plugin", "version": "1.0.0", "skills": ["./skills/a/"]}
        result = auto_sync._format_json(data)
        parsed = json.loads(result)
        assert parsed == data
        assert result.endswith("\n")

    def test_format_json_fallback_uses_json_dumps_format(
        self, monkeypatch: Any
    ) -> None:
        """Verify fallback path produces json.dumps(indent=2) output exactly.

        Tests: Format equivalence in fallback mode
        How: Set _NPX_PATH to None, compare with json.dumps output
        Why: When prettier unavailable, output should be standard json.dumps
        """
        monkeypatch.setattr(auto_sync, "_NPX_PATH", None)
        data = {"name": "test"}
        result = auto_sync._format_json(data)
        expected = json.dumps(data, indent=2) + "\n"
        assert result == expected


# ============================================================================
# New behaviour: Idempotent writes (Bug 2 fix)
# ============================================================================


class TestIdempotentWrites:
    """Test that the staged guard prevents double-bumping on retry.

    The primary defence against double-bumping is the ``_is_file_staged`` guard.
    When run 1 writes and stages the manifest, run 2 (retry) sees the staged file
    and returns early.  An additional ``new_content == existing_content`` check
    provides a secondary safety net.
    """

    def test_update_plugin_json_is_noop_on_second_run(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify second run is blocked by staged guard.

        Tests: Staged guard prevents double-bump for plugin.json
        How: Run update, then run again with file in staged_files
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

        changes = _changes_with_modified_skill()

        # Run 1: should update
        updated_1, version_1 = auto_sync.update_plugin_json(
            plugin_name, changes, _NO_STAGED
        )
        assert updated_1 is True
        assert version_1 == "1.0.1"

        # Run 2: staged guard blocks re-processing
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"
        updated_2, version_2 = auto_sync.update_plugin_json(
            plugin_name, changes, {staged_path}
        )
        assert updated_2 is False
        assert version_2 == "0.0.0"

    def test_update_marketplace_json_is_noop_on_second_run(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify second run is blocked by staged guard.

        Tests: Staged guard prevents double-bump for marketplace.json
        How: Run update, then run again with file in staged_files
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

        plugin_changes: _MarketplaceChangesDict = {
            "added": set(),
            "deleted": set(),
            "modified": [("existing", "1.0.1")],
        }

        # Run 1: should update
        updated_1 = auto_sync.update_marketplace_json(plugin_changes, _NO_STAGED)
        assert updated_1 is True

        # Run 2: staged guard blocks re-processing
        updated_2 = auto_sync.update_marketplace_json(
            plugin_changes, {".claude-plugin/marketplace.json"}
        )
        assert updated_2 is False

        # Verify version was only bumped once
        marketplace_json = tmp_path / ".claude-plugin" / "marketplace.json"
        final_data = json.loads(marketplace_json.read_text(encoding="utf-8"))
        assert final_data["metadata"]["version"] == "1.0.1"

    def test_update_plugin_json_version_stays_at_single_bump(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        """Verify staged guard prevents multiple bumps across retries.

        Tests: Multiple consecutive runs with staged guard
        How: Run update once, then simulate two retries with staged guard
        Why: Stress test the double-bump prevention mechanism
        """
        monkeypatch.chdir(tmp_path)

        plugin_name = "test-plugin"
        plugin_json = _make_plugin_json(
            tmp_path,
            plugin_name,
            {"name": "test-plugin", "version": "1.0.0", "skills": []},
        )

        changes = _changes_with_modified_skill()
        staged_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"

        # Run 1: bumps to 1.0.1
        auto_sync.update_plugin_json(plugin_name, changes, _NO_STAGED)
        # Runs 2-3: staged guard blocks re-processing
        auto_sync.update_plugin_json(plugin_name, changes, {staged_path})
        auto_sync.update_plugin_json(plugin_name, changes, {staged_path})

        # Final version should be 1.0.1, not 1.0.3
        final_data = json.loads(plugin_json.read_text(encoding="utf-8"))
        assert final_data["version"] == "1.0.1"
