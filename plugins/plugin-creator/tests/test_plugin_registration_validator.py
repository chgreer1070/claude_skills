"""Unit tests for PluginRegistrationValidator.

Tests:
- Graceful pass when .claude-plugin/plugin.json is absent (TestNoPluginJson)
- PL002 error for malformed plugin.json (TestInvalidJson)
- PR001 warning for unregistered skill (TestUnregisteredSkill)
- PR001 warning for unregistered agent (TestUnregisteredAgent)
- PR001 warning for unregistered command (TestUnregisteredCommand)
- PR002 error when registered path does not exist (TestMissingRegisteredFile)
- No errors when all capabilities registered and files exist (TestFullyRegistered)
- Empty plugin with no capabilities passes (TestEmptyPlugin)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path to import plugin_validator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from plugin_validator import PluginRegistrationValidator

# ---------------------------------------------------------------------------
# Helper factory functions
# ---------------------------------------------------------------------------


def _make_plugin(
    tmp_path: Path,
    plugin_name: str = "test-plugin",
    plugin_json_content: str | None = None,
) -> Path:
    """Create a plugin directory with .claude-plugin/plugin.json.

    Args:
        tmp_path: Pytest temporary directory
        plugin_name: Name of the plugin directory
        plugin_json_content: Raw JSON string for plugin.json; if None, a
            minimal valid JSON is written

    Returns:
        Path to the plugin root directory
    """
    plugin_dir = tmp_path / plugin_name
    plugin_dir.mkdir()
    claude_plugin = plugin_dir / ".claude-plugin"
    claude_plugin.mkdir()

    if plugin_json_content is not None:
        (claude_plugin / "plugin.json").write_text(plugin_json_content)
    else:
        default_config = {
            "name": plugin_name,
            "skills": [],
            "agents": [],
            "commands": [],
        }
        (claude_plugin / "plugin.json").write_text(json.dumps(default_config, indent=2))

    return plugin_dir


def _add_skill(plugin_dir: Path, skill_name: str) -> Path:
    """Create a skill directory with SKILL.md inside the plugin.

    Args:
        plugin_dir: Plugin root directory
        skill_name: Skill directory name

    Returns:
        Path to the new SKILL.md
    """
    skill_dir = plugin_dir / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(f"---\ndescription: {skill_name}\n---\n\n# {skill_name}\n")
    return skill_md


def _add_agent(plugin_dir: Path, agent_name: str) -> Path:
    """Create an agent .md file inside the plugin.

    Args:
        plugin_dir: Plugin root directory
        agent_name: Agent file stem (without .md extension)

    Returns:
        Path to the new agent .md file
    """
    agents_dir = plugin_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    agent_md = agents_dir / f"{agent_name}.md"
    agent_md.write_text(
        f"---\nname: {agent_name}\ndescription: Test agent\n---\n\n# {agent_name}\n"
    )
    return agent_md


def _add_command(plugin_dir: Path, command_name: str) -> Path:
    """Create a command .md file inside the plugin.

    Args:
        plugin_dir: Plugin root directory
        command_name: Command file stem (without .md extension)

    Returns:
        Path to the new command .md file
    """
    commands_dir = plugin_dir / "commands"
    commands_dir.mkdir(exist_ok=True)
    command_md = commands_dir / f"{command_name}.md"
    command_md.write_text(
        f"---\ndescription: {command_name} command\n---\n\n# {command_name}\n"
    )
    return command_md


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestNoPluginJson:
    """Test validator passes gracefully when plugin.json is absent."""

    def test_no_plugin_json_passes(self, tmp_path: Path) -> None:
        """Test validation passes when .claude-plugin/plugin.json does not exist.

        Tests: Missing plugin.json handling
        How: Create plugin dir without plugin.json, validate
        Why: Validator skips gracefully; not all directories are plugins
        """
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        # No .claude-plugin directory or plugin.json

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_claude_plugin_dir_exists_but_no_plugin_json_passes(
        self, tmp_path: Path
    ) -> None:
        """Test validation passes when .claude-plugin/ exists but plugin.json absent.

        Tests: plugin.json presence check
        How: Create .claude-plugin/ directory without plugin.json, validate
        Why: Validator checks file existence before attempting JSON load
        """
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        (plugin_dir / ".claude-plugin").mkdir()
        # plugin.json deliberately absent

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is True
        assert len(result.errors) == 0

    def test_validates_from_skill_file_path(self, tmp_path: Path) -> None:
        """Test validator can be called with a file path inside the plugin.

        Tests: _find_plugin_dir traversal from file path
        How: Pass skill file path instead of plugin dir, verify graceful result
        Why: validate(path) accepts both file and directory paths
        """
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        skill_dir = plugin_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\ndescription: Test\n---\n\n# Test\n")
        # No plugin.json -- passes gracefully

        validator = PluginRegistrationValidator()
        result = validator.validate(skill_md)

        assert result.passed is True


class TestInvalidJson:
    """Test PL002 error for malformed plugin.json."""

    def test_invalid_json_syntax_produces_pl002(self, tmp_path: Path) -> None:
        """Test PL002 error reported for malformed JSON in plugin.json.

        Tests: JSON parse error detection (PL002)
        How: Write invalid JSON to plugin.json, validate
        Why: Malformed JSON prevents capability discovery and must be flagged
        """
        plugin_dir = _make_plugin(
            tmp_path, plugin_json_content='{"name": "test", INVALID}'
        )

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is False
        pl002_errors = [e for e in result.errors if e.code == "PL002"]
        assert len(pl002_errors) >= 1

    def test_completely_empty_plugin_json_produces_pl002(self, tmp_path: Path) -> None:
        """Test PL002 error for completely empty plugin.json.

        Tests: Empty file handling (PL002)
        How: Write empty string to plugin.json, validate
        Why: Empty file is invalid JSON
        """
        plugin_dir = _make_plugin(tmp_path, plugin_json_content="")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is False
        pl002_errors = [e for e in result.errors if e.code == "PL002"]
        assert len(pl002_errors) >= 1

    def test_invalid_json_pl002_has_suggestion(self, tmp_path: Path) -> None:
        """Test PL002 error includes a suggestion for resolving the issue.

        Tests: Suggestion field populated for PL002
        How: Write invalid JSON, validate, check suggestion
        Why: Actionable suggestions help users fix validation errors
        """
        plugin_dir = _make_plugin(
            tmp_path, plugin_json_content="{not valid json at all"
        )

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pl002_errors = [e for e in result.errors if e.code == "PL002"]
        assert len(pl002_errors) >= 1
        assert all(e.suggestion is not None for e in pl002_errors)

    def test_can_fix_returns_false(self) -> None:
        """Test can_fix() returns False for PluginRegistrationValidator.

        Tests: Auto-fix capability
        How: Call can_fix(), assert False
        Why: Registration issues require manual plugin.json edits
        """
        validator = PluginRegistrationValidator()
        assert validator.can_fix() is False

    def test_fix_raises_not_implemented(self, tmp_path: Path) -> None:
        """Test fix() raises NotImplementedError.

        Tests: Auto-fix raises correctly
        How: Call fix() on plugin dir, expect NotImplementedError
        Why: Registration fixes require manual plugin.json edits
        """
        plugin_dir = _make_plugin(tmp_path)

        validator = PluginRegistrationValidator()
        with pytest.raises(NotImplementedError):
            validator.fix(plugin_dir)


class TestUnregisteredSkill:
    """Test PR001 warning when skill directory exists but is not in plugin.json."""

    def test_unregistered_skill_produces_pr001(self, tmp_path: Path) -> None:
        """Test PR001 warning for skill existing without registration.

        Tests: Unregistered skill detection (PR001)
        How: Create skill directory, leave plugin.json skills array empty
        Why: Unregistered capabilities rely on default discovery which may be fragile
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_skill(plugin_dir, "my-skill")
        # skills array in plugin.json is empty (default from _make_plugin)

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        # PR001 is a warning, not an error -- result should still pass
        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 1

    def test_unregistered_skill_warning_mentions_skill_name(
        self, tmp_path: Path
    ) -> None:
        """Test PR001 warning message references the unregistered skill name.

        Tests: PR001 warning message content
        How: Create named skill, check PR001 warning message
        Why: Warning should identify which skill needs registration
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_skill(plugin_dir, "unregistered-skill")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 1
        assert any("unregistered-skill" in w.message for w in pr001_warnings)

    def test_registered_skill_no_pr001(self, tmp_path: Path) -> None:
        """Test no PR001 warning when skill is registered in plugin.json.

        Tests: Registered skill accepted without warning
        How: Create skill, register it in plugin.json skills array, validate
        Why: Registered capabilities should not generate PR001 warnings
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/my-skill/"],
            }),
        )
        _add_skill(plugin_dir, "my-skill")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0

    def test_multiple_unregistered_skills_all_reported(self, tmp_path: Path) -> None:
        """Test all unregistered skills produce individual PR001 warnings.

        Tests: Multiple unregistered skills
        How: Create two skills, leave both unregistered, validate
        Why: All unregistered capabilities must be reported
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_skill(plugin_dir, "skill-one")
        _add_skill(plugin_dir, "skill-two")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 2


class TestUnregisteredAgent:
    """Test PR001 warning when agent file exists but is not in plugin.json."""

    def test_unregistered_agent_produces_pr001(self, tmp_path: Path) -> None:
        """Test PR001 warning for agent existing without registration.

        Tests: Unregistered agent detection (PR001)
        How: Create agent file, leave plugin.json agents array empty, validate
        Why: Unregistered agents must be flagged for explicit registration
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_agent(plugin_dir, "my-agent")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 1

    def test_unregistered_agent_warning_mentions_agent_name(
        self, tmp_path: Path
    ) -> None:
        """Test PR001 warning message references the unregistered agent name.

        Tests: PR001 warning message for agent
        How: Create named agent, validate, check warning message
        Why: Warning must identify which agent needs registration
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_agent(plugin_dir, "unregistered-agent")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 1
        assert any("unregistered-agent" in w.message for w in pr001_warnings)

    def test_registered_agent_no_pr001(self, tmp_path: Path) -> None:
        """Test no PR001 warning when agent is registered in plugin.json.

        Tests: Registered agent accepted without warning
        How: Create agent, register it in plugin.json, validate
        Why: Registered agents should not generate PR001 warnings
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "agents": ["./agents/my-agent.md"],
            }),
        )
        _add_agent(plugin_dir, "my-agent")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0


class TestUnregisteredCommand:
    """Test PR001 warning when command file exists but is not in plugin.json."""

    def test_unregistered_command_produces_pr001(self, tmp_path: Path) -> None:
        """Test PR001 warning for command existing without registration.

        Tests: Unregistered command detection (PR001)
        How: Create command file, leave plugin.json commands array empty, validate
        Why: Unregistered commands must be flagged
        """
        plugin_dir = _make_plugin(tmp_path)
        _add_command(plugin_dir, "my-command")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) >= 1

    def test_registered_command_no_pr001(self, tmp_path: Path) -> None:
        """Test no PR001 warning when command is registered in plugin.json.

        Tests: Registered command accepted without warning
        How: Create command, register it in plugin.json, validate
        Why: Registered commands should not generate PR001 warnings
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "commands": ["./commands/my-command.md"],
            }),
        )
        _add_command(plugin_dir, "my-command")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0

    def test_readme_and_claude_md_not_treated_as_commands(self, tmp_path: Path) -> None:
        """Test CLAUDE.md and README.md in commands/ are not flagged as unregistered.

        Tests: CLAUDE.md and README.md exclusion from command discovery
        How: Create CLAUDE.md and README.md in commands/ dir, validate
        Why: _find_actual_capabilities excludes these filenames explicitly
        """
        plugin_dir = _make_plugin(tmp_path)
        commands_dir = plugin_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "CLAUDE.md").write_text("# Claude instructions\n")
        (commands_dir / "README.md").write_text("# Commands readme\n")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        # CLAUDE.md and README.md must not produce PR001 warnings
        assert len(pr001_warnings) == 0


class TestMissingRegisteredFile:
    """Test PR002 error when plugin.json lists paths that do not exist."""

    def test_registered_skill_not_on_disk_produces_pr002(self, tmp_path: Path) -> None:
        """Test PR002 error when registered skill SKILL.md does not exist on disk.

        Tests: Missing registered skill detection (PR002)
        How: Register skill in plugin.json without creating SKILL.md, validate
        Why: Registered paths that do not exist are broken configurations (PR002)
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/phantom-skill/"],
            }),
        )
        # Do NOT create the skills/phantom-skill/SKILL.md

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is False
        pr002_errors = [e for e in result.errors if e.code == "PR002"]
        assert len(pr002_errors) >= 1

    def test_registered_agent_not_on_disk_produces_pr002(self, tmp_path: Path) -> None:
        """Test PR002 error when registered agent .md does not exist on disk.

        Tests: Missing registered agent detection (PR002)
        How: Register agent path in plugin.json without creating file, validate
        Why: Registered agent paths that do not exist are broken configurations (PR002)
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "agents": ["./agents/phantom-agent.md"],
            }),
        )
        # Do NOT create agents/phantom-agent.md

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is False
        pr002_errors = [e for e in result.errors if e.code == "PR002"]
        assert len(pr002_errors) >= 1

    def test_registered_command_not_on_disk_produces_pr002(
        self, tmp_path: Path
    ) -> None:
        """Test PR002 error when registered command .md does not exist on disk.

        Tests: Missing registered command detection (PR002)
        How: Register command path in plugin.json without creating file, validate
        Why: Registered command paths that do not exist are broken (PR002)
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "commands": ["./commands/phantom-cmd.md"],
            }),
        )
        # Do NOT create commands/phantom-cmd.md

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is False
        pr002_errors = [e for e in result.errors if e.code == "PR002"]
        assert len(pr002_errors) >= 1

    def test_pr002_error_has_suggestion(self, tmp_path: Path) -> None:
        """Test PR002 error includes a suggestion for resolving the issue.

        Tests: Suggestion field populated for PR002
        How: Register non-existent skill, validate, check suggestion
        Why: Actionable suggestions help users remove or create the referenced path
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/ghost-skill/"],
            }),
        )

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr002_errors = [e for e in result.errors if e.code == "PR002"]
        assert len(pr002_errors) >= 1
        assert all(e.suggestion is not None for e in pr002_errors)


class TestFullyRegistered:
    """Test no errors or PR001 warnings when all capabilities are registered and exist."""

    def test_fully_registered_plugin_passes(self, tmp_path: Path) -> None:
        """Test plugin with all capabilities registered passes with no errors.

        Tests: Happy path -- all capabilities registered and present
        How: Create skill, agent, command; register all in plugin.json; validate
        Why: Correctly configured plugin must produce zero errors or PR001 warnings
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/my-skill/"],
                "agents": ["./agents/my-agent.md"],
                "commands": ["./commands/my-cmd.md"],
            }),
        )
        _add_skill(plugin_dir, "my-skill")
        _add_agent(plugin_dir, "my-agent")
        _add_command(plugin_dir, "my-cmd")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is True
        assert len(result.errors) == 0
        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0

    def test_fully_registered_plugin_from_skill_file(self, tmp_path: Path) -> None:
        """Test validation via file path inside plugin finds plugin.json.

        Tests: _find_plugin_dir traversal for file path input
        How: Call validate() with a SKILL.md path, assert passes
        Why: validate() must handle file inputs by traversing up to plugin root
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/my-skill/"],
            }),
        )
        skill_md = _add_skill(plugin_dir, "my-skill")

        validator = PluginRegistrationValidator()
        result = validator.validate(skill_md)

        assert result.passed is True
        assert len(result.errors) == 0
        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0

    def test_mixed_registered_and_unregistered_separates_correctly(
        self, tmp_path: Path
    ) -> None:
        """Test only the unregistered skill generates PR001, registered one does not.

        Tests: Partial registration -- mix of registered and unregistered
        How: Register one skill, leave another unregistered, validate
        Why: Each skill must be evaluated independently
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": ["./skills/alpha-skill/"],
            }),
        )
        _add_skill(plugin_dir, "alpha-skill")
        _add_skill(plugin_dir, "beta-skill")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        # Only the unregistered skill should produce PR001
        assert len(pr001_warnings) >= 1
        assert any("beta-skill" in w.message for w in pr001_warnings)
        # The registered skill must not generate a PR001 warning
        assert not any("alpha-skill" in w.message for w in pr001_warnings)


class TestEmptyPlugin:
    """Test plugin with no skills, agents, or commands and empty arrays passes."""

    def test_empty_plugin_passes(self, tmp_path: Path) -> None:
        """Test plugin with no capabilities and empty plugin.json arrays passes.

        Tests: Empty plugin happy path
        How: Create plugin with no skills/agents/commands directories, validate
        Why: A plugin under construction should not generate spurious errors
        """
        plugin_dir = _make_plugin(
            tmp_path,
            plugin_json_content=json.dumps({
                "name": "test-plugin",
                "skills": [],
                "agents": [],
                "commands": [],
            }),
        )
        # No skills/, agents/, or commands/ directories created

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is True
        assert len(result.errors) == 0
        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0

    def test_plugin_with_minimal_plugin_json_passes(self, tmp_path: Path) -> None:
        """Test plugin with only name field in plugin.json passes.

        Tests: Minimal plugin.json (no capability arrays)
        How: Write plugin.json with only name field, no capability arrays, validate
        Why: Capability arrays are optional; their absence should not cause errors
        """
        plugin_dir = _make_plugin(
            tmp_path, plugin_json_content=json.dumps({"name": "test-plugin"})
        )
        # No directories created

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        assert result.passed is True
        assert len(result.errors) == 0

    @pytest.mark.parametrize(
        ("capability_type", "file_name"),
        [("agents", "CLAUDE.md"), ("agents", "README.md")],
    )
    def test_excluded_filenames_not_flagged_as_unregistered(
        self, tmp_path: Path, capability_type: str, file_name: str
    ) -> None:
        """Test CLAUDE.md and README.md in agents/ are excluded from registration checks.

        Tests: Filename exclusion in _find_actual_capabilities
        How: Create excluded filename in agents/, verify no PR001 warning
        Why: CLAUDE.md and README.md are documentation, not agent files
        """
        plugin_dir = _make_plugin(tmp_path)
        cap_dir = plugin_dir / capability_type
        cap_dir.mkdir()
        (cap_dir / file_name).write_text("# Documentation\n")

        validator = PluginRegistrationValidator()
        result = validator.validate(plugin_dir)

        pr001_warnings = [w for w in result.warnings if w.code == "PR001"]
        assert len(pr001_warnings) == 0
