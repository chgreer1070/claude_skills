#!/usr/bin/env python3
"""Automatically sync plugin.json and marketplace.json based on git changes.

This script detects CRUD operations on plugins and their components during pre-commit,
then updates manifests and bumps versions accordingly.

CRUD Detection:
- Plugin created: New plugins/ directory with .claude-plugin/plugin.json
- Plugin deleted: Removed plugins/ directory
- Component created: New skill/agent/command/hook/mcp file
- Component deleted: Removed skill/agent/command/hook/mcp file

Version Bumping:
- New plugin: Bump marketplace minor version
- Deleted plugin: Bump marketplace major version
- New component in plugin: Bump plugin minor version
- Deleted component: Bump plugin major version
- Modified component: Bump plugin patch version
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Literal, TypedDict, cast

# Git status parsing constants
_EXPECTED_PARTS_COUNT = 2
_MIN_PLUGIN_PATH_PARTS = 2
_MIN_COMPONENT_PATH_PARTS = 3
_MIN_SKILL_PATH_PARTS = 4


class PluginPathInfo(TypedDict):
    """Parsed plugin path information."""

    plugin: str
    component_type: str | None
    component_path: str | None


class ComponentChange(TypedDict):
    """Component change information."""

    component_type: str
    component_path: str


class ComponentChanges(TypedDict):
    """Changes for a plugin's components."""

    added: list[ComponentChange]
    deleted: list[ComponentChange]
    modified: list[ComponentChange]


class MarketplaceChanges(TypedDict):
    """Changes for marketplace plugins."""

    added: set[str]
    deleted: set[str]
    modified: list[tuple[str, str]]


def run_git_command(args: list[str]) -> str:
    """Run git command and return output.

    Args:
        args: List of git command arguments (e.g., ['status', '--short'])

    Returns:
        Git command stdout output stripped of whitespace
    """
    result = subprocess.run(
        ["/usr/bin/git", *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def get_git_status() -> dict[str, list[str]]:
    """Get staged file changes categorized by operation.

    Returns:
        {
            'added': ['path/to/new/file'],
            'deleted': ['path/to/deleted/file'],
            'modified': ['path/to/changed/file'],
        }
    """
    status: dict[str, list[str]] = {"added": [], "deleted": [], "modified": []}

    # Get staged changes
    output = run_git_command(["diff", "--cached", "--name-status"])

    for line in output.split("\n"):
        if not line.strip():
            continue

        parts = line.split("\t", 1)
        if len(parts) != _EXPECTED_PARTS_COUNT:
            continue

        operation, filepath = parts

        if operation == "A":
            status["added"].append(filepath)
        elif operation == "D":
            status["deleted"].append(filepath)
        elif operation == "M":
            status["modified"].append(filepath)
        elif operation.startswith("R"):  # Renamed
            # For renames, treat as delete old + add new
            old_new = filepath.split("\t")
            if len(old_new) == _EXPECTED_PARTS_COUNT:
                status["deleted"].append(old_new[0])
                status["added"].append(old_new[1])

    return status


def parse_plugin_path(filepath: str) -> PluginPathInfo | None:
    """Parse file path to extract plugin name and component type.

    Args:
        filepath: Relative file path from repository root

    Returns:
        {
            'plugin': 'plugin-name',
            'component_type': 'skill' | 'agent' | 'command' | 'hook' | 'mcp' | None,
            'component_path': 'skills/skill-name/SKILL.md',
        }
    """
    parts = Path(filepath).parts

    if not parts or parts[0] != "plugins":
        return None

    if len(parts) < _MIN_PLUGIN_PATH_PARTS:
        return None

    plugin_name = parts[1]
    result: PluginPathInfo = {
        "plugin": plugin_name,
        "component_type": None,
        "component_path": None,
    }

    # Check if this is a component file
    if len(parts) >= _MIN_COMPONENT_PATH_PARTS:
        component_dir = parts[2]

        if component_dir == "skills" and len(parts) >= _MIN_SKILL_PATH_PARTS:
            result["component_type"] = "skill"
            result["component_path"] = "/".join(parts[2:])
        elif component_dir == "agents" and filepath.endswith(".md"):
            result["component_type"] = "agent"
            result["component_path"] = "/".join(parts[2:])
        elif component_dir == "commands" and filepath.endswith(".md"):
            result["component_type"] = "command"
            result["component_path"] = "/".join(parts[2:])
        elif component_dir == "hooks" and filepath.endswith(".json"):
            result["component_type"] = "hook"
            result["component_path"] = "/".join(parts[2:])
        elif component_dir == "mcp" or "mcp" in filepath:
            result["component_type"] = "mcp"
            result["component_path"] = "/".join(parts[2:])

    return result


def bump_version(current: str, bump_type: Literal["major", "minor", "patch"]) -> str:
    """Bump semantic version.

    Args:
        current: Current version string (e.g., "1.2.3")
        bump_type: Type of version bump

    Returns:
        New version string after bumping
    """
    try:
        major, minor, patch = map(int, current.split("."))
    except (ValueError, AttributeError):
        return "0.1.0"

    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return current


def _update_component_arrays(
    data: dict[str, list[str] | str], changes: ComponentChanges
) -> bool:
    """Update component arrays in plugin.json.

    Args:
        data: Plugin.json data dictionary
        changes: Component changes to apply

    Returns:
        True if modifications were made
    """
    modified = False

    # Add new components
    for component in changes["added"]:
        comp_type = component["component_type"]
        comp_path = component["component_path"]

        if comp_type in {"skill", "agent", "command"}:
            field_name = f"{comp_type}s"

            if field_name not in data:
                data[field_name] = []

            # Normalize path to start with ./
            relative_path = f"./{comp_path}"

            field_value = data[field_name]
            if isinstance(field_value, list):
                if relative_path not in field_value:
                    field_value.append(relative_path)
                    modified = True
            elif isinstance(field_value, str):
                # Convert string to array
                data[field_name] = [field_value, relative_path]
                modified = True

    # Remove deleted components
    for component in changes["deleted"]:
        comp_type = component["component_type"]
        comp_path = component["component_path"]

        if comp_type in {"skill", "agent", "command"}:
            field_name = f"{comp_type}s"

            if field_name in data:
                field_value = data[field_name]
                if isinstance(field_value, list):
                    relative_path = f"./{comp_path}"

                    if relative_path in field_value:
                        field_value.remove(relative_path)
                        modified = True

    return modified


def update_plugin_json(plugin_name: str, changes: ComponentChanges) -> tuple[bool, str]:
    """Update plugin.json based on component changes.

    Args:
        plugin_name: Name of the plugin
        changes: {
            'added': [{'component_type': 'skill', 'component_path': 'skills/foo'}],
            'deleted': [{'component_type': 'agent', 'component_path': 'agents/bar.md'}],
            'modified': [...],
        }

    Returns:
        (updated: bool, new_version: str)
    """
    plugin_json_path = Path(f"plugins/{plugin_name}/.claude-plugin/plugin.json")

    if not plugin_json_path.exists():
        return False, "0.0.0"

    with plugin_json_path.open(encoding="utf-8") as f:
        data: dict[str, list[str] | str] = json.load(f)

    current_version = cast("str", data.get("version", "0.0.0"))
    bump_type: Literal["major", "minor", "patch"] = "patch"
    modified = False

    # Determine bump type based on changes
    if changes["deleted"]:
        bump_type = "major"  # Breaking change
    elif changes["added"]:
        bump_type = "minor"  # New feature

    # Update component arrays
    modified = _update_component_arrays(data, changes)

    # Bump version if changes were made
    if modified or changes["modified"]:
        new_version = bump_version(current_version, bump_type)
        data["version"] = new_version

        # Write updated plugin.json
        with plugin_json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        return True, new_version

    return False, current_version


def update_marketplace_json(plugin_changes: MarketplaceChanges) -> bool:
    """Update marketplace.json based on plugin changes.

    Args:
        plugin_changes: {
            'added': ['plugin-name'],
            'deleted': ['plugin-name'],
            'modified': [('plugin-name', 'new-version')],
        }

    Returns:
        updated: bool
    """
    marketplace_json_path = Path(".claude-plugin/marketplace.json")

    if not marketplace_json_path.exists():
        print("Warning: marketplace.json not found")
        return False

    with marketplace_json_path.open(encoding="utf-8") as f:
        data: dict[str, dict[str, str] | list[dict[str, str]]] = json.load(f)

    metadata = cast("dict[str, str]", data.get("metadata", {}))
    current_version = metadata.get("version", "0.0.0")
    bump_type: Literal["major", "minor", "patch"] = "patch"
    modified = False

    # Determine bump type
    if plugin_changes["deleted"]:
        bump_type = "major"  # Breaking change
    elif plugin_changes["added"]:
        bump_type = "minor"  # New plugins

    # Add new plugins
    for plugin_name in plugin_changes["added"]:
        plugin_entry = {"name": plugin_name, "source": f"./plugins/{plugin_name}"}

        if "plugins" not in data:
            data["plugins"] = []

        plugins_list = cast("list[dict[str, str]]", data["plugins"])

        # Check if already exists
        if not any(p["name"] == plugin_name for p in plugins_list):
            plugins_list.append(plugin_entry)
            modified = True

    # Remove deleted plugins
    for plugin_name in plugin_changes["deleted"]:
        if "plugins" in data:
            plugins_list = cast("list[dict[str, str]]", data["plugins"])
            data["plugins"] = [p for p in plugins_list if p["name"] != plugin_name]
            modified = True

    # Bump marketplace version if any changes
    if modified or plugin_changes["modified"]:
        new_version = bump_version(current_version, bump_type)

        if "metadata" not in data:
            data["metadata"] = {}

        metadata = cast("dict[str, str]", data["metadata"])
        metadata["version"] = new_version

        # Write updated marketplace.json
        with marketplace_json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        return True

    return False


def _process_file_changes(
    status: dict[str, list[str]],
) -> tuple[dict[str, ComponentChanges], MarketplaceChanges]:
    """Process changed files and categorize them.

    Args:
        status: Git status dictionary

    Returns:
        (plugin_component_changes, marketplace_changes)
    """
    plugin_component_changes: dict[str, ComponentChanges] = defaultdict(
        lambda: {"added": [], "deleted": [], "modified": []}
    )

    marketplace_changes: MarketplaceChanges = {
        "added": set(),
        "deleted": set(),
        "modified": [],
    }

    # Parse all changed files
    for operation in ["added", "deleted", "modified"]:
        for filepath in status[operation]:
            parsed = parse_plugin_path(filepath)

            if not parsed:
                continue

            plugin_name = parsed["plugin"]

            # Check if this is a new/deleted plugin
            if filepath.endswith(".claude-plugin/plugin.json"):
                if operation == "added":
                    marketplace_changes["added"].add(plugin_name)
                elif operation == "deleted":
                    marketplace_changes["deleted"].add(plugin_name)
                continue

            # Track component changes
            if parsed["component_type"] and parsed["component_path"]:
                component_change: ComponentChange = {
                    "component_type": parsed["component_type"],
                    "component_path": parsed["component_path"],
                }

                if operation == "added":
                    plugin_component_changes[plugin_name]["added"].append(
                        component_change
                    )
                elif operation == "deleted":
                    plugin_component_changes[plugin_name]["deleted"].append(
                        component_change
                    )
                elif operation == "modified":
                    plugin_component_changes[plugin_name]["modified"].append(
                        component_change
                    )

    return plugin_component_changes, marketplace_changes


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    status = get_git_status()

    # Track changes by plugin
    plugin_component_changes, marketplace_changes = _process_file_changes(status)

    # Update plugin.json files
    plugins_updated = False
    marketplace_updated = False
    for plugin_name, changes in plugin_component_changes.items():
        updated, new_version = update_plugin_json(plugin_name, changes)

        if updated:
            plugins_updated = True
            plugin_json_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"

            # Stage the updated file
            subprocess.run(["/usr/bin/git", "add", plugin_json_path], check=False)

            # Track for marketplace update
            marketplace_changes["modified"].append((plugin_name, new_version))

            # Report changes
            added_count = len(changes["added"])
            deleted_count = len(changes["deleted"])
            modified_count = len(changes["modified"])

            changes_desc = []
            if added_count:
                changes_desc.append(f"+{added_count}")
            if deleted_count:
                changes_desc.append(f"-{deleted_count}")
            if modified_count:
                changes_desc.append(f"~{modified_count}")

            print(
                f"Updated {plugin_name} -> {new_version} ({', '.join(changes_desc)} components)"
            )

    # Update marketplace.json
    if (
        marketplace_changes["added"]
        or marketplace_changes["deleted"]
        or marketplace_changes["modified"]
    ):
        marketplace_updated = update_marketplace_json(marketplace_changes)

        if marketplace_updated:
            subprocess.run(
                ["/usr/bin/git", "add", ".claude-plugin/marketplace.json"], check=False
            )

            with Path(".claude-plugin/marketplace.json").open(encoding="utf-8") as f:
                data = json.load(f)
                new_version = data["metadata"]["version"]

            print(f"Updated marketplace -> {new_version}")

            if marketplace_changes["added"]:
                print(f"   - Added plugins: {', '.join(marketplace_changes['added'])}")
            if marketplace_changes["deleted"]:
                print(
                    f"   - Removed plugins: {', '.join(marketplace_changes['deleted'])}"
                )

    if not plugins_updated and not marketplace_updated:
        print("Info: No manifest updates needed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
