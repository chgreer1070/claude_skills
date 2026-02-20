#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "ruamel.yaml>=0.18.0",
#     "python-frontmatter>=1.1.0",
#     "pydantic>=2.0.0",
# ]
# ///
"""Validate and fix YAML frontmatter in Claude Code capability files.

Validates frontmatter in:
- SKILL.md files (skills)
- Agent .md files

Note: Commands in plugins are deprecated. For user-level commands
(~/.claude/commands/), use the validate/fix commands directly on the file.

Checks against official schema with field type validation.
Reports issues with specific line numbers and suggestions.
Auto-fixes common issues like YAML arrays that should be comma-separated strings.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

import typer
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from ruamel.yaml import YAMLError

# Make sibling module importable without package install
sys.path.insert(0, str(Path(__file__).parent))
from frontmatter_utils import RuamelYAMLHandler
from rich.console import Console
from rich.measure import Measurement
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from rich.table import Table

console = Console()
error_console = Console(stderr=True)

# Shared YAML handler backed by ruamel.yaml round-trip mode
_yaml_handler = RuamelYAMLHandler()

# Constants
MIN_QUOTED_STRING_LENGTH = 2
RECOMMENDED_DESCRIPTION_LENGTH = 1024
MAX_SKILL_NAME_LENGTH = 40


def _get_table_width(table: Table) -> int:
    """Get natural width of table using temporary wide console.

    Source: python3-development skill - tool-library-registry.md

    Returns:
        The natural width of the table in characters.
    """
    temp_console = Console(width=99999)
    measurement = Measurement.get(temp_console, temp_console.options, table)
    return int(measurement.maximum)


app = typer.Typer(
    name="validate-frontmatter",
    help="Validate YAML frontmatter in Claude Code capability files",
    rich_markup_mode="rich",
)


class FileType(StrEnum):
    """Type of capability file."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"
    UNKNOWN = "unknown"


@dataclass
class ValidationIssue:
    """A validation issue found in frontmatter."""

    field: str
    severity: str  # "error" or "warning"
    message: str
    suggestion: str | None = None


class SkillFrontmatter(BaseModel):
    """Pydantic model for skill frontmatter validation.

    Source: .claude/skills/claude-skills-overview-2026/SKILL.md lines 52-67
    """

    model_config = ConfigDict(extra="allow")

    name: str | None = Field(None, max_length=64, pattern=r"^[a-z][a-z0-9-]*$")
    description: str | None = None
    argument_hint: str | None = Field(None, alias="argument-hint")
    allowed_tools: str | None = Field(None, alias="allowed-tools")
    model: str | None = None
    skills: str | None = None
    context: Literal["fork"] | None = None
    agent: str | None = None
    user_invocable: bool | None = Field(None, alias="user-invocable")
    disable_model_invocation: bool | None = Field(
        None, alias="disable-model-invocation"
    )
    hooks: dict[str, Any] | None = None

    @field_validator("skills", "allowed_tools", mode="before")
    @classmethod
    def normalize_comma_separated(cls, v: object) -> str | None:
        """Convert YAML arrays to comma-separated strings.

        Returns:
            Normalized comma-separated string or None.
        """
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v if isinstance(v, str) else None

    @field_validator("description", mode="before")
    @classmethod
    def normalize_single_line(cls, v: object) -> str | None:
        """Collapse multiline descriptions to single line.

        Returns:
            Normalized single-line string or None.
        """
        if isinstance(v, str) and "\n" in v:
            return " ".join(v.split())
        return v if isinstance(v, str) else None

    @field_validator("description", mode="after")
    @classmethod
    def validate_no_colons(cls, v: str | None) -> str | None:
        """Reject descriptions containing colons except in URLs.

        Returns:
            Validated description or None.

        Raises:
            ValueError: If description contains colons outside URLs.
        """
        if not v:
            return v

        # Allow colons in URLs
        temp = v.replace("http://", "").replace("https://", "")

        if ":" in temp:
            msg = (
                "Description cannot contain colons (:) except in URLs. "
                "They trigger YAML quoting. Use alternatives: "
                "semicolons (;), em dashes (—), or rephrase."
            )
            raise ValueError(msg)
        return v


class CommandFrontmatter(BaseModel):
    """Pydantic model for command frontmatter validation."""

    model_config = ConfigDict(extra="allow")

    description: str
    argument_hint: str | None = Field(None, alias="argument-hint")
    allowed_tools: str | None = Field(None, alias="allowed-tools")
    model: str | None = None
    context: Literal["fork"] | None = None
    agent: str | None = None
    hooks: dict[str, Any] | None = None

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def normalize_comma_separated(cls, v: object) -> str | None:
        """Convert YAML arrays to comma-separated strings.

        Returns:
            Normalized comma-separated string or None.
        """
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v if isinstance(v, str) else None

    @field_validator("description", mode="before")
    @classmethod
    def normalize_single_line(cls, v: object) -> str | None:
        """Collapse multiline descriptions to single line.

        Returns:
            Normalized single-line string or None.
        """
        if isinstance(v, str) and "\n" in v:
            return " ".join(v.split())
        return v if isinstance(v, str) else None

    @field_validator("description", mode="after")
    @classmethod
    def validate_no_colons(cls, v: str) -> str:
        """Reject descriptions containing colons except in URLs.

        Returns:
            Validated description.

        Raises:
            ValueError: If description contains colons outside URLs.
        """
        # Allow colons in URLs
        temp = v.replace("http://", "").replace("https://", "")

        if ":" in temp:
            msg = (
                "Description cannot contain colons (:) except in URLs. "
                "They trigger YAML quoting. Use alternatives: "
                "semicolons (;), em dashes (—), or rephrase."
            )
            raise ValueError(msg)
        return v


class AgentFrontmatter(BaseModel):
    """Pydantic model for agent frontmatter validation.

    Source: .claude/skills/agent-creator/references/agent-schema.md

    Note: Field names use camelCase to match the official agent schema.
    Ruff N815 warnings suppressed for these fields as they match external spec.
    """

    model_config = ConfigDict(extra="allow")

    name: str = Field(max_length=64, pattern=r"^[a-z][a-z0-9-]*$")
    description: str
    tools: str | None = None
    disallowedTools: str | None = None  # noqa: N815
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    permissionMode: (  # noqa: N815
        Literal["default", "acceptEdits", "dontAsk", "bypassPermissions", "plan"] | None
    ) = None
    skills: str | None = None
    hooks: dict[str, Any] | None = None
    color: str | None = None

    @field_validator("skills", "tools", "disallowedTools", mode="before")
    @classmethod
    def normalize_comma_separated(cls, v: object) -> str | None:
        """Convert YAML arrays to comma-separated strings.

        Returns:
            Normalized comma-separated string or None.
        """
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return v if isinstance(v, str) else None

    @field_validator("description", mode="before")
    @classmethod
    def normalize_single_line(cls, v: object) -> str | None:
        """Collapse multiline descriptions to single line.

        Returns:
            Normalized single-line string or None.
        """
        if isinstance(v, str) and "\n" in v:
            return " ".join(v.split())
        return v if isinstance(v, str) else None

    @field_validator("description", mode="after")
    @classmethod
    def validate_no_colons(cls, v: str) -> str:
        """Reject descriptions containing colons except in URLs.

        Returns:
            Validated description.

        Raises:
            ValueError: If description contains colons outside URLs.
        """
        # Allow colons in URLs
        temp = v.replace("http://", "").replace("https://", "")

        if ":" in temp:
            msg = (
                "Description cannot contain colons (:) except in URLs. "
                "They trigger YAML quoting. Use alternatives: "
                "semicolons (;), em dashes (—), or rephrase."
            )
            raise ValueError(msg)
        return v


def detect_file_type(path: Path) -> FileType:
    """Detect the type of capability file based on path.

    Returns:
        FileType enum indicating the detected file type.
    """
    if path.name == "SKILL.md":
        return FileType.SKILL
    if "commands" in path.parts:
        return FileType.COMMAND
    if "agents" in path.parts:
        return FileType.AGENT
    return FileType.UNKNOWN


def validate_skill_directory_name(skill_dir_name: str) -> list[ValidationIssue]:
    """Validate skill directory name format.

    Skill directory names must match the pattern used by init_skill.py:
    - Lowercase letters, digits, and hyphens only
    - Cannot start or end with hyphen
    - Max 40 characters

    Source: init_skill.py lines 212-238

    Args:
        skill_dir_name: Directory name to validate

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    if not skill_dir_name:
        issues.append(
            ValidationIssue(
                field="directory",
                severity="error",
                message="Skill directory name cannot be empty",
            )
        )
        return issues

    # Check length
    if len(skill_dir_name) > MAX_SKILL_NAME_LENGTH:
        issues.append(
            ValidationIssue(
                field="directory",
                severity="error",
                message=f"Directory name exceeds maximum length of {MAX_SKILL_NAME_LENGTH} characters (got {len(skill_dir_name)})",
                suggestion=f"Shorten directory name to {MAX_SKILL_NAME_LENGTH} characters or less",
            )
        )

    # Check pattern: lowercase, digits, hyphens; no leading/trailing hyphen
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    if not re.match(pattern, skill_dir_name):
        # Provide specific error messages for common violations
        violations = []
        if re.search(r"[A-Z]", skill_dir_name):
            violations.append("contains uppercase letters")
        if re.search(r"[^a-z0-9-]", skill_dir_name):
            violations.append(
                "contains invalid characters (only lowercase, digits, hyphens allowed)"
            )
        if skill_dir_name.startswith("-"):
            violations.append("starts with hyphen")
        if skill_dir_name.endswith("-"):
            violations.append("ends with hyphen")
        if "--" in skill_dir_name:
            violations.append("contains consecutive hyphens")
        if "_" in skill_dir_name:
            violations.append("contains underscores (use hyphens instead)")

        violation_msg = "; ".join(violations) if violations else "invalid format"

        issues.append(
            ValidationIssue(
                field="directory",
                severity="error",
                message=f"Directory name {violation_msg}",
                suggestion="Use lowercase-hyphen-case (e.g., 'my-skill-name')",
            )
        )

    return issues


def get_model_class(
    file_type: FileType,
) -> type[SkillFrontmatter | CommandFrontmatter | AgentFrontmatter] | None:
    """Get the Pydantic model class for a file type.

    Returns:
        Pydantic model class for validation or None if unknown type.
    """
    match file_type:
        case FileType.SKILL:
            return SkillFrontmatter
        case FileType.COMMAND:
            return CommandFrontmatter
        case FileType.AGENT:
            return AgentFrontmatter
        case _:
            return None


def extract_frontmatter(content: str) -> tuple[str | None, int, int]:
    """Extract YAML frontmatter from content.

    Returns:
        Tuple of (frontmatter_text, start_line, end_line) or (None, 0, 0) if not found.
    """
    if not content.startswith("---"):
        return None, 0, 0

    # Find closing delimiter
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return None, 0, 0

    frontmatter = content[4 : end_match.start() + 3]
    start_line = 1
    end_line = frontmatter.count("\n") + 2

    return frontmatter, start_line, end_line


def validate_and_normalize(
    frontmatter_text: str, file_type: FileType
) -> tuple[dict[str, Any], list[ValidationIssue]]:
    """Parse, validate, and normalize frontmatter using Pydantic.

    Returns:
        Tuple of (normalized_dict, validation_issues)
    """
    issues = []

    # Check raw text for forbidden multiline indicators
    if re.search(r"description:\s*[|>][-+]?\s*\n", frontmatter_text):
        issues.append(
            ValidationIssue(
                field="description",
                severity="error",
                message="Uses forbidden multiline YAML syntax (|, >, |-, >-)",
                suggestion="Use single-line string",
            )
        )

    # Parse YAML
    try:
        data = _yaml_handler.load(frontmatter_text)
    except YAMLError as e:
        issues.append(
            ValidationIssue(
                field="(yaml)", severity="error", message=f"Invalid YAML syntax: {e}"
            )
        )
        return {}, issues

    if not isinstance(data, dict):
        issues.append(
            ValidationIssue(
                field="(yaml)",
                severity="error",
                message="Frontmatter must be a YAML mapping",
            )
        )
        return {}, issues

    # Select Pydantic model based on file type
    model_class = get_model_class(file_type)

    if not model_class:
        return data, issues

    # Validate and normalize with Pydantic
    try:
        validated = model_class.model_validate(data)
        normalized_dict = validated.model_dump(
            by_alias=True, exclude_none=True, mode="python"
        )

        # Add warning for long descriptions (not an error)
        if (
            validated.description
            and len(validated.description) > RECOMMENDED_DESCRIPTION_LENGTH
        ):
            issues.append(
                ValidationIssue(
                    field="description",
                    severity="warning",
                    message=f"Exceeds recommended length of {RECOMMENDED_DESCRIPTION_LENGTH} characters (got {len(validated.description)})",
                    suggestion=f"Front-load critical information in first {RECOMMENDED_DESCRIPTION_LENGTH} characters - Claude Code may truncate in some contexts",
                )
            )

        return normalized_dict, issues
    except ValidationError as e:
        # Convert Pydantic errors to ValidationIssue
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]

            # Make error messages more user-friendly
            if "String should match pattern" in msg:
                msg = "Must use lowercase letters, numbers, and hyphens only"
                suggestion = "Use format: lowercase-with-hyphens"
            elif "String should have at most" in msg:
                max_len = error.get("ctx", {}).get("max_length", "unknown")
                msg = f"Exceeds maximum length of {max_len} characters"
                suggestion = f"Shorten to {max_len} characters or less"
            elif "Input should be" in msg and "literal" in msg.lower():
                valid_values = error.get("ctx", {}).get("expected", "")
                msg = f"Invalid value. Must be one of: {valid_values}"
                suggestion = None
            else:
                suggestion = None

            issues.append(
                ValidationIssue(
                    field=field, severity="error", message=msg, suggestion=suggestion
                )
            )
        return data, issues
    else:
        return normalized_dict, issues


_SKILL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


def _fix_skill_name(
    normalized_dict: dict[str, Any], file_path: Path, fixes: list[str]
) -> dict[str, Any]:
    """Add or correct the 'name' field to match the skill's parent directory name.

    The 'name' field must equal the directory name containing SKILL.md.
    If absent, it is derived from the directory name.
    If present but wrong, it is corrected.
    If the directory name does not match the required pattern, no change is made.

    Args:
        normalized_dict: Current frontmatter key/value pairs.
        file_path: Path to the SKILL.md file.
        fixes: Mutable list of fix descriptions to append to.

    Returns:
        Updated normalized_dict (may be a new dict if name was inserted).
    """
    dir_name = file_path.parent.name
    if not _SKILL_NAME_PATTERN.match(dir_name):
        return normalized_dict
    current_name = normalized_dict.get("name")
    if current_name is None:
        fixes.append(f"Added 'name' field '{dir_name}' derived from directory name")
        return {"name": dir_name, **normalized_dict}
    if current_name != dir_name:
        fixes.append(
            f"Corrected 'name' field from '{current_name}' to '{dir_name}' to match directory name"
        )
        normalized_dict["name"] = dir_name
    return normalized_dict


def apply_fixes(
    content: str, file_type: FileType, file_path: Path | None = None
) -> tuple[str, list[str]]:
    """Parse, normalize via Pydantic, and regenerate frontmatter.

    Args:
        content: File content to fix
        file_type: Detected type of the file
        file_path: Optional path to the file, used to derive skill name from directory

    Returns:
        Tuple of (fixed_content, list_of_fixes_applied)
    """
    frontmatter_text, _, _ = extract_frontmatter(content)
    if frontmatter_text is None:
        return content, []

    # Find body content
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return content, []
    body = content[end_match.end() + 3 :]

    # Parse YAML
    try:
        original_data = _yaml_handler.load(frontmatter_text)
    except YAMLError:
        return content, []

    if not isinstance(original_data, dict):
        return content, []

    # Validate and normalize
    normalized_dict, _ = validate_and_normalize(frontmatter_text, file_type)

    # Track what was fixed
    fixes = []

    # Restore 'name' field for skills and ensure it matches the directory name.
    # The Claude Code bug (2026-01-29) that caused plugin skills with a 'name' field
    # to not appear as slash commands has been resolved. Skills should now include the
    # 'name' field whose value matches the parent directory name.
    if file_type == FileType.SKILL and file_path is not None:
        normalized_dict = _fix_skill_name(normalized_dict, file_path, fixes)

    # Compare to detect what changed
    for key, value in normalized_dict.items():
        if key in original_data and original_data[key] != value:
            if isinstance(original_data[key], list) and isinstance(value, str):
                fixes.append(
                    f"Converted {key} from YAML array to comma-separated string"
                )
            elif (
                isinstance(original_data[key], str)
                and "\n" in original_data[key]
                and "\n" not in str(value)
            ):
                fixes.append(f"Normalized {key} to single line")

    # Check for multiline indicators
    has_multiline_indicators = bool(re.search(r":\s*[|>][-+]?", frontmatter_text))
    if has_multiline_indicators:
        fixes.append("Removed YAML multiline indicators")

    # Only proceed if there were changes
    if not fixes:
        return content, []

    # Regenerate frontmatter with ruamel.yaml via shared handler
    new_frontmatter = _yaml_handler.export(normalized_dict)

    return f"---\n{new_frontmatter}\n---\n{body}", fixes


def get_git_remote_url(repo_path: Path) -> str | None:
    """Extract repository URL from git remote.

    Returns:
        HTTPS URL of git remote origin, or None if not a git repo.
    """
    git_path = shutil.which("git")
    if not git_path:
        return None

    try:
        result = subprocess.run(
            [git_path, "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    remote_url = result.stdout.strip()

    # Convert SSH to HTTPS
    if remote_url.startswith("git@github.com:"):
        # git@github.com:user/repo.git -> https://github.com/user/repo
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")

    return remote_url.removesuffix(".git")


def get_git_author() -> dict[str, str] | None:
    """Extract author info from git config.

    Returns:
        Dict with 'name' and optionally 'email', or None if not available.
    """
    git_path = shutil.which("git")
    if not git_path:
        return None

    try:
        name_result = subprocess.run(
            [git_path, "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    name = name_result.stdout.strip()

    try:
        email_result = subprocess.run(
            [git_path, "config", "user.email"],
            capture_output=True,
            text=True,
            check=False,  # Email might not be set
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"name": name}

    email = email_result.stdout.strip() if email_result.returncode == 0 else None

    author: dict[str, str] = {"name": name}
    if email:
        author["email"] = email

    return author


def generate_plugin_metadata(plugin_dir: Path) -> dict[str, Any]:
    """Generate plugin.json metadata from git and file structure.

    Returns:
        Dict with repository, homepage, author fields populated from git.
    """
    metadata: dict[str, Any] = {}

    # Try to find git root
    current = plugin_dir
    while current != current.parent:
        if (current / ".git").exists():
            repo_url = get_git_remote_url(current)
            if repo_url:
                metadata["repository"] = repo_url

                # Generate homepage from repo + plugin path
                relative_path = plugin_dir.relative_to(current)
                metadata["homepage"] = f"{repo_url}/tree/main/{relative_path}"
            break
        current = current.parent

    # Get author from git config
    author = get_git_author()
    if author:
        metadata["author"] = author

    return metadata


def _find_actual_capabilities(
    plugin_dir: Path,
) -> tuple[set[Path], set[Path], set[Path]]:
    """Find all actual capability files in plugin directory.

    Returns:
        Tuple of (actual_skills, actual_agents, actual_commands).
    """
    actual_skills = {
        d.relative_to(plugin_dir)
        for d in (plugin_dir / "skills").glob("*/")
        if d.is_dir() and (d / "SKILL.md").exists()
    }
    actual_agents = {
        f.relative_to(plugin_dir)
        for f in (plugin_dir / "agents").glob("*.md")
        if f.name not in {"CLAUDE.md", "README.md"}
    }
    actual_commands = {
        f.relative_to(plugin_dir)
        for f in (plugin_dir / "commands").glob("*.md")
        if f.name not in {"CLAUDE.md", "README.md"}
    }
    return actual_skills, actual_agents, actual_commands


def _parse_registered_paths(
    plugin_config: dict[str, Any], plugin_dir: Path, field: str
) -> set[Path]:
    """Parse registered paths from plugin.json field.

    Args:
        plugin_config: Loaded plugin.json content.
        plugin_dir: Plugin directory path.
        field: Field name (skills, agents, commands).

    Returns:
        Set of registered paths.
    """
    registered: set[Path] = set()

    if field not in plugin_config:
        return registered

    value = plugin_config[field]

    if isinstance(value, str):
        value_path = plugin_dir / value.lstrip("./")
        if value_path.is_dir():
            # Directory - find all .md files
            registered.update(
                f.relative_to(plugin_dir)
                for f in value_path.glob("*.md")
                if f.name not in {"CLAUDE.md", "README.md"}
            )
        else:
            registered.add(Path(value.lstrip("./")))
    elif isinstance(value, list):
        registered.update(Path(item.lstrip("./")) for item in value)

    return registered


def _check_orphaned_files(
    actual: set[Path], registered: set[Path], capability_type: str, field: str
) -> list[ValidationIssue]:
    """Check for orphaned files (exist but not registered).

    Args:
        actual: Set of actual capability files.
        registered: Set of registered capability files.
        capability_type: Type name (Skill, Agent, Command).
        field: Field name for suggestion.

    Returns:
        List of validation issues.
    """
    orphaned = actual - registered
    if not orphaned:
        return []

    return [
        ValidationIssue(
            field="plugin.json",
            severity="warning",
            message=f"{capability_type} '{item}' exists but not explicitly registered (relying on default discovery)",
            suggestion=f"Add './{item}' to plugin.json {field} array for explicit registration",
        )
        for item in orphaned
    ]


def _check_broken_references(
    registered: set[Path],
    plugin_dir: Path,
    capability_type: str,
    is_skill: bool = False,
) -> list[ValidationIssue]:
    """Check for broken references (registered but don't exist).

    Args:
        registered: Set of registered paths.
        plugin_dir: Plugin directory path.
        capability_type: Type name (skill, agent, command).
        is_skill: Whether this is a skill (needs /SKILL.md suffix).

    Returns:
        List of validation issues.
    """
    issues: list[ValidationIssue] = []

    for item in registered:
        item_path = plugin_dir / item
        if is_skill:
            item_path /= "SKILL.md"

        if not item_path.exists():
            suffix = "/SKILL.md" if is_skill else ""
            issues.append(
                ValidationIssue(
                    field="plugin.json",
                    severity="error",
                    message=f"Registered {capability_type} '{item}' does not exist",
                    suggestion=f"Remove from plugin.json or create {item}{suffix}",
                )
            )

    return issues


def validate_plugin_registration(plugin_dir: Path) -> list[ValidationIssue]:
    """Validate that capability files match plugin.json registration.

    Checks:
    - All capability files are registered in plugin.json (or use default discovery)
    - All registered paths exist
    - No broken references

    Returns:
        List of ValidationIssue for registration problems.
    """
    issues: list[ValidationIssue] = []

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        # No plugin.json - this might be a user-level directory, not a plugin
        return issues

    try:
        with plugin_json_path.open() as f:
            plugin_config = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(
            ValidationIssue(
                field="plugin.json",
                severity="error",
                message=f"Invalid JSON: {e}",
                suggestion="Fix JSON syntax errors",
            )
        )
        return issues

    # Find all actual capability files
    actual_skills, actual_agents, actual_commands = _find_actual_capabilities(
        plugin_dir
    )

    # Parse registered paths from plugin.json
    registered_skills = _parse_registered_paths(plugin_config, plugin_dir, "skills")
    registered_agents = _parse_registered_paths(plugin_config, plugin_dir, "agents")
    registered_commands = _parse_registered_paths(plugin_config, plugin_dir, "commands")

    # Check for orphaned files
    issues.extend(
        _check_orphaned_files(actual_skills, registered_skills, "Skill", "skills")
    )
    issues.extend(
        _check_orphaned_files(actual_agents, registered_agents, "Agent", "agents")
    )
    issues.extend(
        _check_orphaned_files(
            actual_commands, registered_commands, "Command", "commands"
        )
    )

    # Check for broken references
    issues.extend(
        _check_broken_references(registered_skills, plugin_dir, "skill", is_skill=True)
    )
    issues.extend(_check_broken_references(registered_agents, plugin_dir, "agent"))
    issues.extend(_check_broken_references(registered_commands, plugin_dir, "command"))

    return issues


def validate_plugin_metadata(plugin_dir: Path) -> list[ValidationIssue]:
    """Validate plugin.json metadata against git information.

    Returns:
        List of ValidationIssue for metadata suggestions.
    """
    issues: list[ValidationIssue] = []

    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        return issues

    try:
        with plugin_json_path.open() as f:
            plugin_config = json.load(f)
    except json.JSONDecodeError:
        return issues

    # Generate metadata from git
    git_metadata = generate_plugin_metadata(plugin_dir)

    if not git_metadata:
        # Not in a git repo or git not available
        return issues

    # Check for missing metadata
    missing_fields = []
    suggested_values = {}

    if "repository" not in plugin_config and "repository" in git_metadata:
        missing_fields.append("repository")
        suggested_values["repository"] = git_metadata["repository"]

    if "homepage" not in plugin_config and "homepage" in git_metadata:
        missing_fields.append("homepage")
        suggested_values["homepage"] = git_metadata["homepage"]

    if "author" not in plugin_config and "author" in git_metadata:
        missing_fields.append("author")
        suggested_values["author"] = git_metadata["author"]

    if missing_fields:
        suggestion_json = json.dumps(suggested_values, indent=2)
        issues.append(
            ValidationIssue(
                field="plugin.json",
                severity="info",
                message=f"Plugin metadata could be auto-populated from git: {', '.join(missing_fields)}",
                suggestion=f"Add to plugin.json:\n{suggestion_json}",
            )
        )

    # Check for mismatched metadata
    if (
        "repository" in plugin_config
        and "repository" in git_metadata
        and plugin_config["repository"] != git_metadata["repository"]
    ):
        issues.append(
            ValidationIssue(
                field="plugin.json",
                severity="warning",
                message=f"Repository URL mismatch: plugin.json has '{plugin_config['repository']}', git has '{git_metadata['repository']}'",
                suggestion=f"Update repository to: {git_metadata['repository']}",
            )
        )

    return issues


def find_capability_files(path: Path) -> list[Path]:
    """Find all capability files in path.

    Searches recursively for:
    - Files named SKILL.md
    - Files directly in agents/ directories (not subdirectories)
    - Files directly in commands/ directories (not subdirectories)

    Excludes:
    - CLAUDE.md (documentation)
    - README.md (documentation)

    Returns:
        List of paths to capability files.
    """
    if path.is_file():
        # Skip documentation files even when passed directly
        if path.name in {"CLAUDE.md", "README.md"}:
            return []
        return [path]

    files: list[Path] = []

    # Find SKILL.md files
    files.extend(path.glob("**/SKILL.md"))

    # If path is directly an agents/ or commands/ directory, scan it
    if path.name in {"agents", "commands"}:
        for pattern in ["*.md", "*.mdc"]:
            for file in path.glob(pattern):
                # Skip documentation files
                if file.name in {"CLAUDE.md", "README.md"}:
                    continue
                files.append(file)
    else:
        # Find files directly in agents/ and commands/ directories
        # (not in subdirectories like references/, assets/, etc.)
        for pattern in [
            "**/agents/*.md",
            "**/agents/*.mdc",
            "**/commands/*.md",
            "**/commands/*.mdc",
        ]:
            for file in path.glob(pattern):
                # Skip documentation files
                if file.name in {"CLAUDE.md", "README.md"}:
                    continue
                files.append(file)

    return sorted(files)


def process_file(
    file_path: Path, check_only: bool
) -> tuple[bool, list[str], list[ValidationIssue]]:
    """Process a single file (validate and optionally fix).

    Returns:
        Tuple of (success, fixes_applied, remaining_issues).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        return (
            False,
            [],
            [
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                )
            ],
        )

    # Extract frontmatter
    frontmatter, _, _ = extract_frontmatter(content)
    if frontmatter is None:
        return (
            False,
            [],
            [
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message="No YAML frontmatter found",
                    suggestion="File must start with '---' delimiter",
                )
            ],
        )

    # Detect file type first
    detected_type = detect_file_type(file_path)
    if detected_type == FileType.UNKNOWN:
        detected_type = FileType.SKILL

    # Auto-fix if not check-only
    fixes: list[str] = []
    if not check_only:
        fixed_content, fixes = apply_fixes(content, detected_type, file_path)
        if fixes:
            try:
                file_path.write_text(fixed_content, encoding="utf-8")
                content = fixed_content
                # Re-extract frontmatter after fixes
                frontmatter, _, _ = extract_frontmatter(content)
            except OSError as e:
                return (
                    False,
                    fixes,
                    [
                        ValidationIssue(
                            field="(file)",
                            severity="error",
                            message=f"Could not write fixed file: {e}",
                        )
                    ],
                )

    # Validate using Pydantic
    normalized_data, issues = validate_and_normalize(frontmatter or "", detected_type)

    # Validate skill directory name and name-field consistency if this is a SKILL.md file
    if detected_type == FileType.SKILL and file_path.name == "SKILL.md":
        # Get parent directory name (skill directory)
        skill_dir_name = file_path.parent.name
        dir_issues = validate_skill_directory_name(skill_dir_name)
        issues.extend(dir_issues)

        # Check that 'name' field matches the directory name when both are present
        skill_name_in_fm = normalized_data.get("name")
        if skill_name_in_fm and skill_name_in_fm != skill_dir_name:
            issues.append(
                ValidationIssue(
                    field="name",
                    severity="warning",
                    message=(
                        f"'name' field value '{skill_name_in_fm}' does not match "
                        f"directory name '{skill_dir_name}'"
                    ),
                    suggestion=(
                        f"Set name: {skill_dir_name} to match the directory, "
                        "or remove the 'name' field to use the directory name automatically"
                    ),
                )
            )

    success = not any(issue.severity == "error" for issue in issues)
    return success, fixes, issues


def _display_issues_by_severity(
    files_with_issues: list[tuple[Path, list[ValidationIssue]]],
    severity: str,
    color: str,
    icon: str,
    label: str,
) -> None:
    """Display issues of a specific severity.

    Args:
        files_with_issues: List of (path, issues) tuples.
        severity: Severity level to filter.
        color: Rich color for display.
        icon: Icon character to display.
        label: Label for the severity (ERROR, WARN, INFO).
    """
    filtered = [
        (path, [i for i in issues if i.severity == severity])
        for path, issues in files_with_issues
    ]
    filtered = [(p, i) for p, i in filtered if i]

    if not filtered:
        return

    console.print(
        f"[{color}]{icon} Found {severity}s in {len(filtered)} files:[/{color}]\n"
    )
    for file_path, issues in filtered:
        console.print(f"[cyan]{file_path}[/cyan]")
        for issue in issues:
            console.print(
                f"  [{color}]{label}[/{color}] {issue.field}: {issue.message}"
            )
            if issue.suggestion:
                console.print(f"    [dim]{issue.suggestion}[/dim]")
        console.print()


def display_check_results(
    files_with_errors: list[tuple[Path, list[ValidationIssue]]], total_files: int
) -> int:
    """Display results for check mode.

    Returns:
        Exit code: 1 if errors found, 0 if only warnings or success.
    """
    # Display issues by severity
    _display_issues_by_severity(files_with_errors, "error", "red", "✗", "ERROR")
    _display_issues_by_severity(files_with_errors, "warning", "yellow", "⚠", "WARN")
    _display_issues_by_severity(files_with_errors, "info", "blue", "i", "INFO")

    # Check if we have any errors
    has_errors = any(
        any(i.severity == "error" for i in issues) for _, issues in files_with_errors
    )

    # Success message
    if not files_with_errors:
        console.print(f"[green]✓[/green] All {total_files} files valid")

    # Exit 1 only for errors, not warnings or info
    return 1 if has_errors else 0


def display_fix_results(
    files_with_errors: list[tuple[Path, list[ValidationIssue]]],
    total_fixed: int,
    total_fixes: int,
) -> int:
    """Display results for fix mode.

    Returns:
        Exit code: 1 if errors found, 0 if only warnings or success.
    """
    if total_fixes > 0:
        console.print(
            f"[green]✓[/green] Fixed {total_fixed} files ({total_fixes} issues)"
        )

    # Display issues by severity (with newline prefix for separation)
    has_issues = bool(files_with_errors)

    if has_issues:
        # Add newline before displaying remaining issues
        console.print()

    _display_issues_by_severity(files_with_errors, "error", "red", "✗", "ERROR")
    _display_issues_by_severity(files_with_errors, "warning", "yellow", "⚠", "WARN")
    _display_issues_by_severity(files_with_errors, "info", "blue", "i", "INFO")

    # Check if we have any errors
    has_errors = any(
        any(i.severity == "error" for i in issues) for _, issues in files_with_errors
    )

    # Success message
    if not has_issues and total_fixes == 0:
        console.print("[green]✓[/green] All files valid")

    # Exit 1 only for errors, not warnings or info
    return 1 if has_errors else 0


@app.command()
def main(
    path: Annotated[
        Path | None,
        typer.Argument(
            help="Path to file or directory (defaults to current directory)"
        ),
    ] = None,
    check: Annotated[
        bool, typer.Option("--check", help="Validate only, don't modify files")
    ] = False,
) -> None:
    """Validate and auto-fix YAML frontmatter in Claude Code files.

    Auto-detects whether path is a file or directory.

    Default behavior (without --check):
    - Silently fix files that can be auto-fixed
    - Show summary of fixes and remaining errors
    - Exit 0 if all files valid or auto-fixed
    - Exit 1 if unfixable errors remain

    With --check flag:
    - Don't modify files
    - Show all issues found
    - Exit 1 if any issues found

    Examples:
        uv run validate_frontmatter.py                           # Fix current directory
        uv run validate_frontmatter.py plugins/my-plugin         # Fix directory
        uv run validate_frontmatter.py path/to/file.md           # Fix single file
        uv run validate_frontmatter.py --check plugins/my-plugin # Validate only
    """
    target_path = path or Path.cwd()

    if not target_path.exists():
        error_console.print(f"[red]Path not found:[/red] {target_path}")
        raise typer.Exit(1)

    # Find all capability files
    files = find_capability_files(target_path)

    if not files:
        console.print("[yellow]No capability files found[/yellow]")
        raise typer.Exit(0)

    # Process files
    total_fixed = 0
    total_fixes = 0
    files_with_issues: list[tuple[Path, list[ValidationIssue]]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Processing {len(files)} files...", total=len(files))

        for file_path in files:
            success, fixes, issues = process_file(file_path, check)

            if fixes:
                total_fixed += 1
                total_fixes += len(fixes)

            # Collect files with errors OR warnings
            if not success or issues:
                files_with_issues.append((file_path, issues))

            progress.advance(task)

    # If processing a plugin directory, validate plugin.json cross-references
    if (
        target_path.is_dir()
        and (target_path / ".claude-plugin" / "plugin.json").exists()
    ):
        plugin_issues = validate_plugin_registration(target_path)
        plugin_issues.extend(validate_plugin_metadata(target_path))

        if plugin_issues:
            files_with_issues.append((
                target_path / ".claude-plugin" / "plugin.json",
                plugin_issues,
            ))

    # Show results based on mode
    if check:
        exit_code = display_check_results(files_with_issues, len(files))
        if exit_code != 0:
            raise typer.Exit(exit_code)
    else:
        exit_code = display_fix_results(files_with_issues, total_fixed, total_fixes)
        if exit_code != 0:
            raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
