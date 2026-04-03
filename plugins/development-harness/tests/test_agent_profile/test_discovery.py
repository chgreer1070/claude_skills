"""Unit tests for agent_profile.discovery module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from agent_profile.discovery import find_agent, scan_all_agents
from agent_profile.models import AgentEntry

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# scan_all_agents
# ---------------------------------------------------------------------------


class TestScanAllAgents:
    def test_finds_agents_in_single_plugin(self, single_plugin_root: Path) -> None:
        agents = scan_all_agents(single_plugin_root)
        names = [a.name for a in agents]
        assert "list-skills-agent" in names
        assert "csv-skills-agent" in names
        assert "no-skills-agent" in names

    def test_finds_agents_across_multiple_plugins(self, multi_plugin_root: Path) -> None:
        agents = scan_all_agents(multi_plugin_root)
        plugins = {a.plugin for a in agents}
        assert "alpha" in plugins
        assert "beta" in plugins

    def test_returns_agent_entry_objects(self, single_plugin_root: Path) -> None:
        agents = scan_all_agents(single_plugin_root)
        for agent in agents:
            assert isinstance(agent, AgentEntry)
            assert agent.path.exists()
            assert agent.path.suffix == ".md"

    def test_sorted_by_plugin_then_name(self, multi_plugin_root: Path) -> None:
        agents = scan_all_agents(multi_plugin_root)
        keys = [(a.plugin, a.name) for a in agents]
        assert keys == sorted(keys)

    def test_subdirectory_agent_produces_colon_name(self, single_plugin_root: Path) -> None:
        agents = scan_all_agents(single_plugin_root)
        names = [a.name for a in agents]
        assert "testing:unit-tester" in names

    def test_empty_plugins_root_returns_empty_list(self, tmp_path: Path) -> None:
        plugins_root = tmp_path / "plugins"
        plugins_root.mkdir()
        agents = scan_all_agents(plugins_root)
        assert agents == []

    def test_plugin_without_agents_dir_is_skipped(self, tmp_path: Path) -> None:
        plugins_root = tmp_path / "plugins"
        (plugins_root / "no-agents-plugin").mkdir(parents=True)
        agents = scan_all_agents(plugins_root)
        assert agents == []

    def test_plugin_field_matches_directory_name(self, single_plugin_root: Path) -> None:
        agents = scan_all_agents(single_plugin_root)
        for agent in agents:
            assert agent.plugin == "test-plugin"


# ---------------------------------------------------------------------------
# find_agent — bare name
# ---------------------------------------------------------------------------


class TestFindAgentBare:
    def test_finds_unique_bare_name(self, single_plugin_root: Path) -> None:
        agent = find_agent("list-skills-agent", single_plugin_root)
        assert agent.name == "list-skills-agent"
        assert agent.plugin == "test-plugin"

    def test_raises_file_not_found_for_missing_agent(self, single_plugin_root: Path) -> None:
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            find_agent("nonexistent", single_plugin_root)

    def test_raises_value_error_for_ambiguous_bare_name(self, multi_plugin_root: Path) -> None:
        with pytest.raises(ValueError, match="shared-name"):
            find_agent("shared-name", multi_plugin_root)

    def test_error_message_lists_plugin_locations(self, multi_plugin_root: Path) -> None:
        with pytest.raises(ValueError, match="shared-name") as exc_info:
            find_agent("shared-name", multi_plugin_root)
        msg = str(exc_info.value)
        assert "alpha" in msg
        assert "beta" in msg


# ---------------------------------------------------------------------------
# find_agent — plugin-qualified name
# ---------------------------------------------------------------------------


class TestFindAgentPluginQualified:
    def test_finds_by_plugin_qualified_name(self, multi_plugin_root: Path) -> None:
        agent = find_agent("alpha:alpha-agent", multi_plugin_root)
        assert agent.name == "alpha-agent"
        assert agent.plugin == "alpha"

    def test_finds_agent_in_other_plugin_when_qualified(self, multi_plugin_root: Path) -> None:
        agent = find_agent("beta:beta-agent", multi_plugin_root)
        assert agent.name == "beta-agent"
        assert agent.plugin == "beta"

    def test_raises_file_not_found_for_missing_qualified_agent(self, multi_plugin_root: Path) -> None:
        with pytest.raises(FileNotFoundError):
            find_agent("alpha:nonexistent-agent", multi_plugin_root)

    def test_finds_subdirectory_agent_with_plugin_qualified_name(self, single_plugin_root: Path) -> None:
        agent = find_agent("test-plugin:testing:unit-tester", single_plugin_root)
        assert agent.name == "testing:unit-tester"
        assert agent.plugin == "test-plugin"

    def test_path_points_to_existing_file(self, multi_plugin_root: Path) -> None:
        agent = find_agent("alpha:alpha-agent", multi_plugin_root)
        assert agent.path.is_file()
