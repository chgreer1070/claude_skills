"""Tests for the FM009 state-machine guard in plugin_validator.py.

Tests the ecosystem-aware _fix_unquoted_colons() function and the
full --fix CLI integration path, verifying that:
- mcp: blocks are never rewritten by the FM009 fix
- Claude Code-only fields still receive FM009 fixes
- Integration via subprocess produces byte-identical mcp: blocks
- Regression: existing FM009 behavior for Claude Code-only files unchanged
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from plugin_validator import _fix_unquoted_colons

# Path to the plugin_validator script for subprocess-based integration tests
_VALIDATOR_SCRIPT = Path(__file__).parent.parent / "scripts" / "plugin_validator.py"

# Path to the fixtures directory
_FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFM009Guard:
    """Tests for the FM009 state-machine guard in _fix_unquoted_colons().

    Scope: White-box unit tests that call _fix_unquoted_colons() directly,
    verifying per-line behaviour for eight distinct input shapes.

    Strategy: AAA pattern; each case constructs a minimal frontmatter string,
    calls the function, and asserts on the returned (text, fixes, fields) tuple.
    The state machine must pass mcp: sub-keys through unchanged and still
    rewrite Claude Code fields containing unquoted colons.
    """

    @pytest.mark.parametrize(
        ("case_id", "frontmatter", "check_not_rewritten", "check_fm009_fires"),
        [
            pytest.param(
                "mcp_stdio_command",
                (
                    "name: test-skill\n"
                    "description: A test skill\n"
                    "mcp:\n"
                    "  my-server:\n"
                    "    command: npx -y @scope/server-package\n"
                    "    args:\n"
                    "      - /tmp/workspace\n"
                ),
                "    command: npx -y @scope/server-package\n",
                False,
                id="case1_mcp_stdio_command_not_rewritten",
            ),
            pytest.param(
                "mcp_http_url",
                ("name: test-skill\ndescription: A test skill\nmcp:\n  remote:\n    url: https://example.com/mcp\n"),
                "    url: https://example.com/mcp\n",
                False,
                id="case2_mcp_http_url_not_rewritten",
            ),
            pytest.param(
                "description_with_colon_no_mcp",
                ("description: Fix: something broke\nuser-invocable: true\n"),
                None,
                True,
                id="case3_description_colon_fixed",
            ),
            pytest.param(
                "mixed_description_and_mcp",
                ("description: Fix: something broke\nmcp:\n  server:\n    command: npx -y server-package\n"),
                "    command: npx -y server-package\n",
                True,
                id="case4_mixed_only_description_fixed",
            ),
            pytest.param(
                "mcp_null_scalar", "mcp: null\n", "mcp: null\n", False, id="case5_mcp_null_scalar_no_crash_no_rewrite"
            ),
            pytest.param(
                "claude_only_no_ecosystem",
                ("description: Check: everything looks fine\nuser-invocable: true\ntools: Read, Write\n"),
                None,
                True,
                id="case6_claude_only_fm009_fires",
            ),
            pytest.param(
                "mcp_block_many_indented_lines",
                (
                    "name: test-skill\n"
                    "description: Normal description\n"
                    "mcp:\n"
                    "  server-a:\n"
                    "    command: npx -y pkgA\n"
                    "    args:\n"
                    "      - --flag: value\n"
                    "  server-b:\n"
                    "    url: https://api.host.com/mcp\n"
                    "    headers:\n"
                    "      Authorization: Bearer secret-token\n"
                    "user-invocable: true\n"
                ),
                "    command: npx -y pkgA\n",
                False,
                id="case7_mcp_block_four_plus_indented_lines_all_skipped",
            ),
            pytest.param(
                "mcp_scalar_null_followed_by_claude_field",
                "mcp: null\nsome-other-key:\n  description: Fix: colon here\n",
                None,
                True,
                id="case8_mcp_scalar_null_fm009_fires_for_subsequent_fields",
            ),
        ],
    )
    def test_fm009_guard(
        self, case_id: str, frontmatter: str, check_not_rewritten: str | None, check_fm009_fires: bool
    ) -> None:
        """FM009 state-machine guard produces correct per-case output.

        Tests: _fix_unquoted_colons() state machine for 7 input shapes
        How: Call the function with a crafted frontmatter string; inspect the
             returned (fixed_text, fixes, fixed_fields) tuple to verify that
             mcp: sub-key lines are passed through unchanged and that Claude
             Code fields with unquoted colons are still fixed.
        Why: The state machine is the core correctness guarantee that prevents
             silent mutation of OpenCode configuration while preserving full
             FM009 fix behaviour for Claude Code-only fields.
        """
        # Arrange
        # (frontmatter is prepared by parametrize)

        # Act
        fixed_text, _fixes, fixed_fields = _fix_unquoted_colons(frontmatter)

        # Assert — line that must NOT be rewritten
        if check_not_rewritten is not None:
            assert check_not_rewritten in fixed_text, (
                f"[{case_id}] Expected line {check_not_rewritten!r} to be "
                f"preserved verbatim in output, but it was absent or modified.\n"
                f"Output:\n{fixed_text}"
            )

        # Assert — FM009 fired (or did not fire)
        if check_fm009_fires:
            assert len(fixed_fields) > 0, (
                f"[{case_id}] Expected FM009 to produce fixed_fields, but got empty list. Output:\n{fixed_text}"
            )
        else:
            assert fixed_fields == [], (
                f"[{case_id}] Expected no FM009 fixes, but got fixed_fields={fixed_fields!r}. Output:\n{fixed_text}"
            )


class TestFM009MixedFieldIsolation:
    """Targeted tests verifying that only Claude Code fields are rewritten in mixed input.

    Scope: Case 4 expanded — confirms the mcp: block is byte-identical in
    output when a mixed frontmatter contains both a Claude Code colon field
    and a multi-line mcp: block.
    """

    def test_only_description_fixed_in_mixed_frontmatter(self) -> None:
        """Only the description field is modified when frontmatter mixes Claude Code and mcp: fields.

        Tests: Isolation between Claude Code and ecosystem-owned sections
        How: Feed mixed frontmatter; check description is quoted, mcp: lines untouched
        Why: Silent mutation of any mcp: sub-key would corrupt OpenCode server
             configuration in a multi-runtime SKILL.md.
        """
        # Arrange
        frontmatter = (
            "description: Fix: something broke\n"
            "mcp:\n"
            "  server:\n"
            "    command: npx -y server-package\n"
            "    url: https://remote.example.com/mcp\n"
        )

        # Act
        fixed_text, _fixes, fixed_fields = _fix_unquoted_colons(frontmatter)

        # Assert — description was fixed
        assert '"Fix: something broke"' in fixed_text
        assert "description" in fixed_fields

        # Assert — mcp: lines untouched
        assert "    command: npx -y server-package\n" in fixed_text
        assert "    url: https://remote.example.com/mcp\n" in fixed_text

        # Assert — mcp fields not in fixed_fields
        assert "command" not in fixed_fields
        assert "url" not in fixed_fields


class TestFM009IntegrationFixture:
    """Integration tests that invoke plugin_validator.py via subprocess.

    Scope: End-to-end test using the full CLI path (uv run) so that
    PEP 723 dependency resolution is exercised, not just direct import.

    Strategy: Run --fix on a pre-constructed fixture file written to a
    tmp_path copy, then read the output file and assert byte-level
    correctness of the mcp: block.
    """

    def test_fix_on_multi_runtime_skill_preserves_mcp_block(self, tmp_path: Path) -> None:
        """Running --fix on a multi-runtime fixture produces a byte-identical mcp: block.

        Tests: Full CLI --fix pipeline leaves mcp: block unchanged
        How: Copy fixture to tmp_path, run validator --fix as subprocess,
             read result and assert the mcp: block is byte-identical to input.
        Why: The subprocess path is the actual user-facing path; direct import
             tests would miss any regression introduced by argument parsing or
             the Typer command wrapper that processes --fix.
        """
        # Arrange
        fixture_src = _FIXTURES_DIR / "multi_runtime_skill.md"
        target = tmp_path / "multi_runtime_skill.md"
        target.write_text(fixture_src.read_text())

        original_content = fixture_src.read_text()

        # Extract the mcp: block from original for byte comparison.
        # The block starts at "mcp:\n" and ends before the closing "---".
        mcp_block_start = original_content.index("mcp:\n")
        mcp_block_end = original_content.index("\n---\n", mcp_block_start)
        original_mcp_block = original_content[mcp_block_start:mcp_block_end]

        # Act
        result = subprocess.run(
            ["uv", "run", "--quiet", str(_VALIDATOR_SCRIPT), "--fix", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )

        # Assert — exit code 0
        assert result.returncode == 0, (
            f"plugin_validator.py --fix exited {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Assert — mcp: block in output file is byte-identical to original
        fixed_content = target.read_text()
        mcp_block_start_out = fixed_content.index("mcp:\n")
        mcp_block_end_out = fixed_content.index("\n---\n", mcp_block_start_out)
        output_mcp_block = fixed_content[mcp_block_start_out:mcp_block_end_out]

        assert output_mcp_block == original_mcp_block, (
            f"mcp: block was mutated by --fix.\nOriginal:\n{original_mcp_block}\nAfter --fix:\n{output_mcp_block}"
        )

        # Assert — FM009 was not reported for mcp: block
        assert "mcp" not in result.stdout.lower().split("fm009")[1:], (
            "FM009 should not reference any mcp: field.\nstdout:\n" + result.stdout
        )


class TestFM009Regression:
    """Regression tests ensuring pre-existing FM009 behaviour is unchanged.

    Scope: Verifies that adding the ecosystem guard did not break FM009
    fixes for Claude Code-only SKILL.md files.

    Strategy: Run --fix on a synthetic Claude-only fixture that has a
    known FM009 violation; assert the description is quoted afterwards.
    """

    def test_fix_still_applies_fm009_to_claude_only_skill(self, tmp_path: Path) -> None:
        """Running --fix on a Claude-only skill still quotes the colon-containing description.

        Tests: FM009 regression — existing Claude Code fix behaviour unchanged
        How: Copy claude_only_skill.md fixture to tmp_path, run --fix,
             assert description value is now quoted in the output file.
        Why: The state-machine guard must not suppress FM009 for fields that
             are Claude Code-owned; regression here would silently allow
             invalid YAML to persist in production SKILL.md files.
        """
        # Arrange
        # The validator classifies files by name — only SKILL.md files receive
        # full frontmatter validation including FM009 fixes.  Copy the fixture
        # to a SKILL.md path so the validator applies the fix.
        fixture_src = _FIXTURES_DIR / "claude_only_skill.md"
        target = tmp_path / "SKILL.md"
        target.write_text(fixture_src.read_text())

        # Act
        result = subprocess.run(
            ["uv", "run", "--quiet", str(_VALIDATOR_SCRIPT), "--fix", str(target)],
            capture_output=True,
            text=True,
            check=False,
        )

        # Assert — exit code 0
        assert result.returncode == 0, (
            f"plugin_validator.py --fix exited {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Assert — description value is now quoted in the output file
        fixed_content = target.read_text()
        assert '"Fix: something broke in the pipeline"' in fixed_content, (
            f"Expected description value to be quoted after --fix.\nFixed content:\n{fixed_content}"
        )

    def test_unit_fix_still_applies_fm009_to_claude_only_frontmatter(self) -> None:
        """_fix_unquoted_colons() still quotes description colon values in Claude-only frontmatter.

        Tests: Unit-level FM009 regression for Claude Code-only input
        How: Call _fix_unquoted_colons() directly with a frontmatter string
             that has no mcp: key; assert description is quoted and fm009 fires.
        Why: Confirms the state machine does not globally suppress FM009 —
             only ecosystem-owned keys bypass the fix.
        """
        # Arrange
        frontmatter = "description: Fix: something broke in the pipeline\nuser-invocable: true\n"

        # Act
        fixed_text, fixes, fixed_fields = _fix_unquoted_colons(frontmatter)

        # Assert
        assert '"Fix: something broke in the pipeline"' in fixed_text
        assert "description" in fixed_fields
        assert len(fixes) > 0
