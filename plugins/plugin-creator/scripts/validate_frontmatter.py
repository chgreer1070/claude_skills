#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.0.0",
#     "pyyaml>=6.0",
#     "types-PyYAML>=6.0",
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
from typing import TYPE_CHECKING, Annotated

import typer
import yaml
from rich.console import Console
from rich.measure import Measurement
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from rich.table import Table

console = Console()
error_console = Console(stderr=True)

# Constants
MIN_QUOTED_STRING_LENGTH = 2


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
class FieldSpec:
    """Specification for a frontmatter field."""

    name: str
    field_type: type | tuple[type, ...]
    required: bool
    description: str
    valid_values: list[str] | None = None
    max_length: int | None = None
    pattern: str | None = None


@dataclass
class ValidationIssue:
    """A validation issue found in frontmatter."""

    field: str
    severity: str  # "error" or "warning"
    message: str
    suggestion: str | None = None


# Schema definitions verified against local reference skills
# Source: .claude/skills/claude-skills-overview-2026/SKILL.md lines 52-67

SKILL_SCHEMA: list[FieldSpec] = [
    FieldSpec(
        "name",
        str,
        False,  # Optional - uses directory name if omitted
        "Display name (lowercase, hyphens, max 64)",
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
    ),
    FieldSpec(
        "description",
        str,
        False,  # "Recommended" per docs, not required - uses first paragraph if omitted
        "When to use; Claude uses for auto-invocation",
        max_length=1024,
    ),
    FieldSpec("argument-hint", str, False, "Autocomplete hint"),
    FieldSpec(
        "allowed-tools",
        str,
        False,
        "Tools without permission prompts (comma-separated)",
    ),
    FieldSpec(
        "model",
        str,
        False,
        "Model when skill is active",
        # No valid_values restriction - accepts any model ID per docs
    ),
    FieldSpec("context", str, False, "Context behavior", valid_values=["fork"]),
    FieldSpec("agent", str, False, "Subagent type when context: fork"),
    FieldSpec("user-invocable", bool, False, "Show in / menu"),
    FieldSpec("disable-model-invocation", bool, False, "Prevent Claude auto-loading"),
    FieldSpec("hooks", dict, False, "Hooks scoped to skill lifecycle"),
]

COMMAND_SCHEMA: list[FieldSpec] = [
    FieldSpec("description", str, True, "Shown in /help menu", max_length=1024),
    FieldSpec("argument-hint", str, False, "Shows in autocomplete"),
    FieldSpec("allowed-tools", str, False, "Tool allowlist (comma-separated)"),
    FieldSpec("model", str, False, "Override model"),
    FieldSpec("context", str, False, "Context behavior", valid_values=["fork"]),
    FieldSpec("agent", str, False, "Agent type when context: fork"),
    FieldSpec("hooks", dict, False, "Scoped hooks"),
]

# Source: .claude/skills/agent-creator/references/agent-schema.md

AGENT_SCHEMA: list[FieldSpec] = [
    FieldSpec(
        "name",
        str,
        True,  # Required per agent-schema.md lines 9-20
        "Unique identifier",
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
    ),
    FieldSpec(
        "description",
        str,
        True,  # Required per agent-schema.md lines 22-40
        "Delegation trigger keywords",
        max_length=1024,
    ),
    FieldSpec("tools", str, False, "Tool allowlist (comma-separated)"),
    FieldSpec("disallowedTools", str, False, "Tool denylist (comma-separated)"),
    FieldSpec(
        "model",
        str,
        False,
        "Model to use",
        valid_values=["sonnet", "opus", "haiku", "inherit"],
    ),
    FieldSpec(
        "permissionMode",
        str,
        False,
        "Permission behavior",
        valid_values=["default", "acceptEdits", "dontAsk", "bypassPermissions", "plan"],
    ),
    FieldSpec("skills", str, False, "Skills to load (comma-separated)"),
    FieldSpec("hooks", dict, False, "Scoped hooks"),
    FieldSpec("color", str, False, "UI color metadata"),
]

# Fields that must be comma-separated strings (not YAML arrays)
# Per official docs: https://code.claude.com/docs/en/skills.md
COMMA_SEPARATED_FIELDS = {"allowed-tools", "tools", "disallowedTools", "skills"}


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


def get_schema(file_type: FileType) -> list[FieldSpec]:
    """Get the schema for a file type.

    Returns:
        List of FieldSpec defining the expected frontmatter fields.
    """
    match file_type:
        case FileType.SKILL:
            return SKILL_SCHEMA
        case FileType.COMMAND:
            return COMMAND_SCHEMA
        case FileType.AGENT:
            return AGENT_SCHEMA
        case _:
            return []


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


def check_multiline_indicators(frontmatter: str) -> list[ValidationIssue]:
    """Check for forbidden YAML multiline indicators.

    Returns:
        List of ValidationIssue for any forbidden indicators found.
    """
    issues = []

    # These break Claude Code's YAML parser
    forbidden_patterns = [
        (r":\s*>\-", ">-"),
        (r":\s*\|\-", "|-"),
        (r":\s*>\|", ">|"),
        (r":\s*\|>", "|>"),
    ]

    for pattern, indicator in forbidden_patterns:
        if re.search(pattern, frontmatter):
            issues.append(
                ValidationIssue(
                    field="(yaml)",
                    severity="error",
                    message=f"Contains YAML multiline indicator '{indicator}' which breaks parsing",
                    suggestion="Use single-line strings in quotes instead",
                )
            )

    return issues


def validate_field(field_spec: FieldSpec, value: object) -> list[ValidationIssue]:
    """Validate a single field against its spec.

    Returns:
        List of ValidationIssue for any issues found with the field value.
    """
    issues = []

    # Type check
    if not isinstance(value, field_spec.field_type):
        expected = (
            field_spec.field_type.__name__
            if isinstance(field_spec.field_type, type)
            else " or ".join(t.__name__ for t in field_spec.field_type)
        )
        issues.append(
            ValidationIssue(
                field=field_spec.name,
                severity="error",
                message=f"Expected type {expected}, got {type(value).__name__}",
            )
        )
        return issues  # Skip further checks if type is wrong

    # String-specific checks
    if isinstance(value, str):
        if field_spec.max_length and len(value) > field_spec.max_length:
            issues.append(
                ValidationIssue(
                    field=field_spec.name,
                    severity="error",
                    message=f"Exceeds max length {field_spec.max_length} (got {len(value)})",
                    suggestion=f"Shorten to {field_spec.max_length} characters or less",
                )
            )

        if field_spec.pattern and not re.match(field_spec.pattern, value):
            issues.append(
                ValidationIssue(
                    field=field_spec.name,
                    severity="error",
                    message=f"Does not match required pattern: {field_spec.pattern}",
                    suggestion="Use lowercase letters, numbers, and hyphens only",
                )
            )

        if field_spec.valid_values and value not in field_spec.valid_values:
            issues.append(
                ValidationIssue(
                    field=field_spec.name,
                    severity="warning",
                    message=f"Value '{value}' not in known values: {field_spec.valid_values}",
                    suggestion="Check if this is intentional",
                )
            )

    return issues


def normalize_dict(data: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    """Normalize parsed frontmatter dict to match schema requirements.

    Applies dict-level transformations without text manipulation:
    - Converts YAML arrays to comma-separated strings
    - Collapses multi-line descriptions to single line

    Args:
        data: Parsed frontmatter dictionary

    Returns:
        Tuple of (normalized_dict, list_of_normalizations_applied)
    """
    fixes: list[str] = []
    normalized = data.copy()

    # Fix 1: YAML arrays → comma-separated strings
    for field_name in COMMA_SEPARATED_FIELDS:
        field_value = normalized.get(field_name)
        if isinstance(field_value, list):
            items = [str(item).strip() for item in field_value]
            normalized[field_name] = ", ".join(items)
            fixes.append(
                f"Converted {field_name} from YAML array to comma-separated string"
            )

    # Fix 2: Multi-line descriptions → single line
    desc = normalized.get("description")
    if isinstance(desc, str) and "\n" in desc:
        normalized["description"] = " ".join(desc.split())
        fixes.append("Collapsed multi-line description to single line")

    return normalized, fixes


def apply_fixes(content: str) -> tuple[str, list[str]]:
    """Apply all automatic fixes to frontmatter.

    Architecture:
    1. Extract frontmatter text and body
    2. Parse frontmatter to dict
    3. Normalize dict (arrays → strings, multiline → single line)
    4. Dump dict back to YAML (PyYAML handles all quoting)
    5. Reconstruct file

    Returns:
        Tuple of (fixed_content, list_of_all_fixes_applied).
    """
    # Phase 1: Extract
    frontmatter_text, _, _ = extract_frontmatter(content)
    if frontmatter_text is None:
        return content, []

    # Find body content
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return content, []
    body = content[end_match.end() + 3 :]

    # Phase 2: Parse
    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return content, []

    if not isinstance(data, dict):
        return content, []

    # Phase 3: Normalize
    normalized, fixes = normalize_dict(data)

    if not fixes:
        return content, []

    # Phase 4: Dump (PyYAML handles all quoting)
    new_frontmatter = yaml.dump(
        normalized,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,  # Prevent line wrapping
    )

    # Phase 5: Reconstruct
    return f"---\n{new_frontmatter}---\n{body}", fixes


def validate_frontmatter(
    frontmatter: str, schema: list[FieldSpec], file_type: FileType
) -> list[ValidationIssue]:
    """Validate frontmatter against schema.

    Returns:
        List of ValidationIssue for all validation problems found.
    """
    issues = []

    # Check for multiline indicators first
    issues.extend(check_multiline_indicators(frontmatter))

    # Parse YAML
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as e:
        issues.append(
            ValidationIssue(
                field="(yaml)", severity="error", message=f"Invalid YAML syntax: {e}"
            )
        )
        return issues

    if not isinstance(data, dict):
        issues.append(
            ValidationIssue(
                field="(yaml)",
                severity="error",
                message="Frontmatter must be a YAML mapping",
            )
        )
        return issues

    # Check each field in schema
    for field_spec in schema:
        if field_spec.name in data:
            issues.extend(validate_field(field_spec, data[field_spec.name]))
        elif field_spec.required:
            issues.append(
                ValidationIssue(
                    field=field_spec.name,
                    severity="error",
                    message="Required field is missing",
                    suggestion=f"Add '{field_spec.name}:' to frontmatter",
                )
            )

    # Note: Unknown fields are allowed - Claude Code supports custom frontmatter fields

    return issues


def find_capability_files(path: Path) -> list[Path]:
    """Find all capability files in path.

    Searches recursively for:
    - Files named SKILL.md
    - Files directly in agents/ directories (not subdirectories)
    - Files directly in commands/ directories (not subdirectories)

    Returns:
        List of paths to capability files.
    """
    if path.is_file():
        return [path]

    files: list[Path] = []

    # Find SKILL.md files
    files.extend(path.glob("**/SKILL.md"))

    # Find files directly in agents/ and commands/ directories
    # (not in subdirectories like references/, assets/, etc.)
    for pattern in [
        "**/agents/*.md",
        "**/agents/*.mdc",
        "**/commands/*.md",
        "**/commands/*.mdc",
    ]:
        files.extend(path.glob(pattern))

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

    # Auto-fix if not check-only
    fixes: list[str] = []
    if not check_only:
        fixed_content, fixes = apply_fixes(content)
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

    # Validate
    detected_type = detect_file_type(file_path)
    if detected_type == FileType.UNKNOWN:
        detected_type = FileType.SKILL

    schema = get_schema(detected_type)
    issues = validate_frontmatter(frontmatter or "", schema, detected_type)

    success = not any(issue.severity == "error" for issue in issues)
    return success, fixes, issues


def display_check_results(
    files_with_errors: list[tuple[Path, list[ValidationIssue]]], total_files: int
) -> None:
    """Display results for check mode."""
    if files_with_errors:
        console.print(f"[red]Found issues in {len(files_with_errors)} files:[/red]\n")
        for file_path, issues in files_with_errors:
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in issues:
                severity_mark = (
                    "[red]ERROR[/red]"
                    if issue.severity == "error"
                    else "[yellow]WARN[/yellow]"
                )
                console.print(f"  {severity_mark} {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()
    else:
        console.print(f"[green]✓[/green] All {total_files} files valid")


def display_fix_results(
    files_with_errors: list[tuple[Path, list[ValidationIssue]]],
    total_fixed: int,
    total_fixes: int,
) -> None:
    """Display results for fix mode."""
    if total_fixes > 0:
        console.print(
            f"[green]✓[/green] Fixed {total_fixed} files ({total_fixes} issues)"
        )

    if files_with_errors:
        console.print(
            f"\n[red]✗[/red] {len(files_with_errors)} files have unfixable errors:\n"
        )
        for file_path, issues in files_with_errors:
            errors = [i for i in issues if i.severity == "error"]
            console.print(f"[cyan]{file_path}[/cyan]")
            for issue in errors:
                console.print(f"  [red]ERROR[/red] {issue.field}: {issue.message}")
                if issue.suggestion:
                    console.print(f"    [dim]{issue.suggestion}[/dim]")
            console.print()
    elif total_fixes == 0:
        console.print("[green]✓[/green] All files valid")


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
    files_with_errors: list[tuple[Path, list[ValidationIssue]]] = []

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

            if not success:
                files_with_errors.append((file_path, issues))

            progress.advance(task)

    # Show results based on mode
    if check:
        display_check_results(files_with_errors, len(files))
        if files_with_errors:
            raise typer.Exit(1)
    else:
        display_fix_results(files_with_errors, total_fixed, total_fixes)
        if files_with_errors:
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
