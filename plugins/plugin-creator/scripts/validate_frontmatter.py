#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.0.0",
#     "pyyaml>=6.0",
#     "types-PyYAML>=6.0",
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

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

import typer
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from rich.console import Console
from rich.measure import Measurement
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from rich.table import Table

console = Console()
error_console = Console(stderr=True)

# Constants
MIN_QUOTED_STRING_LENGTH = 2
RECOMMENDED_DESCRIPTION_LENGTH = 1024


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
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
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


def apply_fixes(content: str, file_type: FileType) -> tuple[str, list[str]]:
    """Parse, normalize via Pydantic, and regenerate frontmatter.

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
        original_data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return content, []

    if not isinstance(original_data, dict):
        return content, []

    # Validate and normalize
    normalized_dict, _ = validate_and_normalize(frontmatter_text, file_type)

    # Track what was fixed
    fixes = []

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

    # Regenerate frontmatter with PyYAML
    new_frontmatter = yaml.dump(
        normalized_dict,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )

    return f"---\n{new_frontmatter}---\n{body}", fixes


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
        fixed_content, fixes = apply_fixes(content, detected_type)
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
    _, issues = validate_and_normalize(frontmatter or "", detected_type)

    success = not any(issue.severity == "error" for issue in issues)
    return success, fixes, issues


def display_check_results(
    files_with_errors: list[tuple[Path, list[ValidationIssue]]], total_files: int
) -> int:
    """Display results for check mode.

    Returns:
        Exit code: 1 if errors found, 0 if only warnings or success.
    """
    # Separate errors from warnings
    files_with_actual_errors = [
        (path, [i for i in issues if i.severity == "error"])
        for path, issues in files_with_errors
    ]
    files_with_actual_errors = [(p, i) for p, i in files_with_actual_errors if i]

    files_with_warnings = [
        (path, [i for i in issues if i.severity == "warning"])
        for path, issues in files_with_errors
    ]
    files_with_warnings = [(p, i) for p, i in files_with_warnings if i]

    # Display errors
    if files_with_actual_errors:
        console.print(
            f"[red]✗ Found errors in {len(files_with_actual_errors)} files:[/red]\n"
        )
        for file_path, issues in files_with_actual_errors:
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in issues:
                console.print(f"  [red]ERROR[/red] {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()

    # Display warnings
    if files_with_warnings:
        console.print(
            f"[yellow]⚠ Found warnings in {len(files_with_warnings)} files:[/yellow]\n"
        )
        for file_path, issues in files_with_warnings:
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in issues:
                console.print(f"  [yellow]WARN[/yellow] {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()

    # Success message
    if not files_with_actual_errors and not files_with_warnings:
        console.print(f"[green]✓[/green] All {total_files} files valid")

    # Exit 1 only for errors, not warnings
    return 1 if files_with_actual_errors else 0


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

    # Separate errors from warnings
    files_with_actual_errors = [
        (path, [i for i in issues if i.severity == "error"])
        for path, issues in files_with_errors
    ]
    files_with_actual_errors = [(p, i) for p, i in files_with_actual_errors if i]

    files_with_warnings = [
        (path, [i for i in issues if i.severity == "warning"])
        for path, issues in files_with_errors
    ]
    files_with_warnings = [(p, i) for p, i in files_with_warnings if i]

    # Display errors
    if files_with_actual_errors:
        console.print(
            f"\n[red]✗[/red] {len(files_with_actual_errors)} files have unfixable errors:\n"
        )
        for file_path, issues in files_with_actual_errors:
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in issues:
                console.print(f"  [red]ERROR[/red] {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()

    # Display warnings
    if files_with_warnings:
        console.print(
            f"\n[yellow]⚠[/yellow] {len(files_with_warnings)} files have warnings:\n"
        )
        for file_path, issues in files_with_warnings:
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in issues:
                console.print(f"  [yellow]WARN[/yellow] {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()

    # Success message
    if not files_with_actual_errors and not files_with_warnings and total_fixes == 0:
        console.print("[green]✓[/green] All files valid")

    # Exit 1 only for errors, not warnings
    return 1 if files_with_actual_errors else 0


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
