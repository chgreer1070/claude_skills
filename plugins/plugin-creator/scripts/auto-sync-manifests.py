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
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Literal, TypedDict, cast

# Prettier formatting
_NPX_PATH: str | None = shutil.which("npx")

# Git status parsing constants
_MIN_PLUGIN_PATH_PARTS = 2
_MIN_COMPONENT_PATH_PARTS = 3
_MIN_SKILL_PATH_PARTS = 4

# Resolve git binary once at module load
_GIT_PATH: str | None = shutil.which("git")


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

    Raises:
        FileNotFoundError: If git binary is not found in PATH.
    """
    if _GIT_PATH is None:
        msg = "git executable not found in PATH"
        raise FileNotFoundError(msg)

    result = subprocess.run(
        [_GIT_PATH, *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0 and result.stderr:
        sys.stderr.write(f"git {' '.join(args)}: {result.stderr.strip()}\n")
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

    min_fields = 2
    rename_fields = 3

    for line in output.split("\n"):
        if not line.strip():
            continue

        # Split all tab-separated fields:
        #   A/D/M produce 2 fields: [operation, filepath]
        #   R{score} produces 3 fields: [operation, old_path, new_path]
        parts = line.split("\t")
        if len(parts) < min_fields:
            continue

        operation = parts[0]

        match operation:
            case "A":
                status["added"].append(parts[1])
            case "D":
                status["deleted"].append(parts[1])
            case "M":
                status["modified"].append(parts[1])
            case op if op.startswith("R") and len(parts) == rename_fields:
                status["deleted"].append(parts[1])
                status["added"].append(parts[2])

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

        match component_dir:
            case "skills" if len(parts) >= _MIN_SKILL_PATH_PARTS:
                result["component_type"] = "skill"
                result["component_path"] = "/".join(parts[2:])
            case "agents" if filepath.endswith(".md"):
                result["component_type"] = "agent"
                result["component_path"] = "/".join(parts[2:])
            case "commands" if filepath.endswith(".md"):
                result["component_type"] = "command"
                result["component_path"] = "/".join(parts[2:])
            case "hooks" if filepath.endswith(".json"):
                result["component_type"] = "hook"
                result["component_path"] = "/".join(parts[2:])
            case "mcp":
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
        sys.stderr.write(
            f"Warning: malformed version '{current}', defaulting to 0.1.0\n"
        )
        return "0.1.0"

    match bump_type:
        case "major":
            return f"{major + 1}.0.0"
        case "minor":
            return f"{major}.{minor + 1}.0"
        case "patch":
            return f"{major}.{minor}.{patch + 1}"


def _get_staged_files() -> set[str]:
    """Return the set of currently staged file paths.

    Calls ``git diff --cached --name-only`` once and returns a set for O(1)
    membership tests, avoiding repeated subprocess invocations.

    Returns:
        Set of staged file paths (strings).
    """
    staged_output = run_git_command(["diff", "--cached", "--name-only"])
    return set(staged_output.splitlines()) if staged_output else set()


def _is_file_staged(filepath: str | Path, staged_files: set[str]) -> bool:
    """Check whether a file path appears in the staged files set.

    Uses exact matching to prevent false positives
    (e.g. ``plugin.json.bak`` matching ``plugin.json``).

    Args:
        filepath: Path to check.
        staged_files: Pre-fetched set from ``_get_staged_files()``.

    Returns:
        True if the exact path appears in the staged files set.
    """
    return str(filepath) in staged_files


def _find_prettierrc() -> Path | None:
    """Locate ``.prettierrc`` by walking up from the current directory.

    Returns:
        Absolute path to ``.prettierrc`` if found, else None.
    """
    current = Path.cwd().resolve()
    for parent in (current, *current.parents):
        candidate = parent / ".prettierrc"
        if candidate.is_file():
            return candidate
    return None


# Resolve prettier config once at module load.
_PRETTIERRC_PATH: Path | None = _find_prettierrc()


def _format_json(data: object) -> str:
    """Serialize data to JSON, formatted by prettier if available.

    Writes ``json.dumps(indent=2)`` output.  If ``npx`` is available, runs
    ``prettier --write`` to match the project's prettier configuration.
    The ``--config`` flag is passed explicitly so that temp files outside
    the repository still receive the project's formatting rules.

    Args:
        data: JSON-serialisable Python object.

    Returns:
        A prettier-formatted JSON string with trailing newline.
    """
    content = json.dumps(data, indent=2) + "\n"
    if not _NPX_PATH:
        return content
    with tempfile.NamedTemporaryFile(
        encoding="utf-8", mode="w", suffix=".json", delete=False
    ) as f:
        f.write(content)
        tmp_path = f.name
    try:
        cmd = [_NPX_PATH, "prettier", "--write"]
        if _PRETTIERRC_PATH:
            cmd.extend(["--config", str(_PRETTIERRC_PATH)])
        cmd.append(tmp_path)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            sys.stderr.write(
                f"Warning: prettier formatting failed: {result.stderr.strip()}\n"
            )
            return content
        return Path(tmp_path).read_text(encoding="utf-8")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


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


def update_plugin_json(
    plugin_name: str, changes: ComponentChanges, staged_files: set[str]
) -> tuple[bool, str]:
    """Update plugin.json based on component changes.

    Args:
        plugin_name: Name of the plugin
        changes: {
            'added': [{'component_type': 'skill', 'component_path': 'skills/foo'}],
            'deleted': [{'component_type': 'agent', 'component_path': 'agents/bar.md'}],
            'modified': [...],
        }
        staged_files: Pre-fetched set of staged file paths from ``_get_staged_files()``.

    Returns:
        (updated: bool, new_version: str)
    """
    plugin_json_path = Path(f"plugins/{plugin_name}/.claude-plugin/plugin.json")

    if not plugin_json_path.exists():
        return False, "0.0.0"

    # Check if plugin.json is already staged using exact line matching
    if _is_file_staged(plugin_json_path, staged_files):
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
        existing_content = plugin_json_path.read_text(encoding="utf-8")

        data["version"] = new_version
        new_content = _format_json(data)

        # Skip write when the formatted output already matches the file.
        # The primary double-bump defence is the _is_file_staged guard
        # above — this check provides an additional safety net.
        if new_content == existing_content:
            return False, current_version

        plugin_json_path.write_text(new_content, encoding="utf-8")

        return True, new_version

    return False, current_version


def _update_marketplace_plugins(
    data: dict[str, dict[str, str] | list[dict[str, str]]],
    plugin_changes: MarketplaceChanges,
) -> bool:
    """Add and remove plugins in the marketplace data structure.

    Args:
        data: Marketplace JSON data dictionary (mutated in place).
        plugin_changes: Changes describing added/deleted plugins.

    Returns:
        True if the plugins list was modified.
    """
    modified = False

    for plugin_name in plugin_changes["added"]:
        plugin_entry = {"name": plugin_name, "source": f"./plugins/{plugin_name}"}

        if "plugins" not in data:
            data["plugins"] = []

        plugins_list = cast("list[dict[str, str]]", data["plugins"])

        if not any(p["name"] == plugin_name for p in plugins_list):
            plugins_list.append(plugin_entry)
            modified = True

    for plugin_name in plugin_changes["deleted"]:
        if "plugins" in data:
            plugins_list = cast("list[dict[str, str]]", data["plugins"])
            data["plugins"] = [p for p in plugins_list if p["name"] != plugin_name]
            modified = True

    return modified


def update_marketplace_json(
    plugin_changes: MarketplaceChanges, staged_files: set[str]
) -> bool:
    """Update marketplace.json based on plugin changes.

    Args:
        plugin_changes: {
            'added': ['plugin-name'],
            'deleted': ['plugin-name'],
            'modified': [('plugin-name', 'new-version')],
        }
        staged_files: Pre-fetched set of staged file paths from ``_get_staged_files()``.

    Returns:
        updated: bool
    """
    marketplace_json_path = Path(".claude-plugin/marketplace.json")

    if not marketplace_json_path.exists():
        print("Warning: marketplace.json not found")
        return False

    # Check if marketplace.json is already staged using exact line matching
    if _is_file_staged(marketplace_json_path, staged_files):
        return False

    with marketplace_json_path.open(encoding="utf-8") as f:
        data: dict[str, dict[str, str] | list[dict[str, str]]] = json.load(f)

    metadata = cast("dict[str, str]", data.get("metadata", {}))
    current_version = metadata.get("version", "0.0.0")
    bump_type: Literal["major", "minor", "patch"] = "patch"

    # Determine bump type
    if plugin_changes["deleted"]:
        bump_type = "major"  # Breaking change
    elif plugin_changes["added"]:
        bump_type = "minor"  # New plugins

    # Add and remove plugins
    modified = _update_marketplace_plugins(data, plugin_changes)

    # Bump marketplace version if any changes
    if modified or plugin_changes["modified"]:
        existing_content = marketplace_json_path.read_text(encoding="utf-8")
        new_version = bump_version(current_version, bump_type)

        if "metadata" not in data:
            data["metadata"] = {}

        metadata = cast("dict[str, str]", data["metadata"])
        metadata["version"] = new_version

        new_content = _format_json(data)

        if new_content == existing_content:
            return False

        marketplace_json_path.write_text(new_content, encoding="utf-8")

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

                match operation:
                    case "added" | "deleted" | "modified":
                        plugin_component_changes[plugin_name][operation].append(
                            component_change
                        )

    return plugin_component_changes, marketplace_changes


def _git_stage_file(filepath: str) -> None:
    """Stage a file with git add, logging warnings on failure.

    Args:
        filepath: Relative path to stage.
    """
    if not _GIT_PATH:
        return
    result = subprocess.run(
        [_GIT_PATH, "add", filepath], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        sys.stderr.write(
            f"Warning: git add {filepath} failed: {result.stderr.strip()}\n"
        )


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    status = get_git_status()
    staged_files = _get_staged_files()

    # Track changes by plugin
    plugin_component_changes, marketplace_changes = _process_file_changes(status)

    # Update plugin.json files
    plugins_updated = False
    marketplace_updated = False
    for plugin_name, changes in plugin_component_changes.items():
        updated, new_version = update_plugin_json(plugin_name, changes, staged_files)

        if updated:
            plugins_updated = True
            plugin_json_path = f"plugins/{plugin_name}/.claude-plugin/plugin.json"

            # Stage the updated file
            _git_stage_file(plugin_json_path)

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
        marketplace_updated = update_marketplace_json(marketplace_changes, staged_files)

        if marketplace_updated:
            _git_stage_file(".claude-plugin/marketplace.json")

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
