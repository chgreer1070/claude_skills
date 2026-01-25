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
- Command .md files
- Agent .md files

Checks against official schema with field type validation.
Reports issues with specific line numbers and suggestions.
Auto-fixes common issues like YAML arrays that should be comma-separated strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
error_console = Console(stderr=True)

# Preview length for dry-run output
PREVIEW_MAX_CHARS = 2000

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
        valid_values=["sonnet", "opus", "haiku", "inherit"],  # per lines 64-71
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
    FieldSpec("color", str, False, "Terminal output color"),  # per lines 252-264
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


def fix_array_to_comma_string(content: str) -> tuple[str, list[str]]:
    """Convert YAML arrays to comma-separated strings for specified fields.

    Returns:
        Tuple of (fixed_content, list_of_fixes_applied).
    """
    fixes: list[str] = []

    # Parse to find array fields
    frontmatter, _start_line, _end_line = extract_frontmatter(content)
    if frontmatter is None:
        return content, fixes

    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError:
        return content, fixes

    if not isinstance(data, dict):
        return content, fixes

    # Check each comma-separated field
    fields_to_fix: dict[str, str] = {}
    for field_name in COMMA_SEPARATED_FIELDS:
        if field_name in data and isinstance(data[field_name], list):
            # Convert list to comma-separated string
            items = [str(item).strip() for item in data[field_name]]
            fields_to_fix[field_name] = ", ".join(items)
            fixes.append(
                f"Converted {field_name} from YAML array to comma-separated string"
            )

    if not fields_to_fix:
        return content, fixes

    # Apply fixes by regenerating frontmatter
    for field_name, new_value in fields_to_fix.items():
        data[field_name] = new_value

    # Rebuild file with fixed frontmatter
    # Find the end of frontmatter in original content
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return content, fixes

    body = content[end_match.end() + 3 :]

    # Generate new YAML frontmatter
    new_frontmatter = yaml.dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False, width=1000
    )

    return f"---\n{new_frontmatter}---\n{body}", fixes


def fix_multiline_description(content: str) -> tuple[str, list[str]]:
    """Convert YAML multiline indicators to single-line quoted strings.

    Returns:
        Tuple of (fixed_content, list_of_fixes_applied).
    """
    fixes: list[str] = []

    # Pattern to detect description with multiline indicators
    multiline_patterns = [
        (r"(description:\s*)>\-\n((?:\s+.+\n)+)", "folded-strip"),
        (r"(description:\s*)\|\-\n((?:\s+.+\n)+)", "literal-strip"),
        (r"(description:\s*)>\n((?:\s+.+\n)+)", "folded"),
        (r"(description:\s*)\|\n((?:\s+.+\n)+)", "literal"),
    ]

    for pattern, indicator_type in multiline_patterns:
        match = re.search(pattern, content)
        if match:
            prefix = match.group(1)
            multiline_content = match.group(2)
            # Join the lines and clean up
            lines = [line.strip() for line in multiline_content.strip().split("\n")]
            single_line = " ".join(lines)
            # Quote it properly
            quoted = f'"{single_line}"' if "'" in single_line else f"'{single_line}'"
            content = (
                content[: match.start()]
                + prefix
                + quoted
                + "\n"
                + content[match.end() :]
            )
            fixes.append(
                f"Converted description from {indicator_type} multiline to single-line string"
            )
            break

    return content, fixes


def apply_fixes(content: str) -> tuple[str, list[str]]:
    """Apply all automatic fixes to frontmatter.

    Returns:
        Tuple of (fixed_content, list_of_all_fixes_applied).
    """
    all_fixes: list[str] = []

    # Apply fixes in order
    content, fixes = fix_array_to_comma_string(content)
    all_fixes.extend(fixes)

    content, fixes = fix_multiline_description(content)
    all_fixes.extend(fixes)

    return content, all_fixes


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

    # Check for unknown fields
    known_fields = {spec.name for spec in schema}
    issues.extend(
        ValidationIssue(
            field=field_name,
            severity="warning",
            message="Unknown field (not in official schema)",
            suggestion="Check spelling or remove if not needed",
        )
        for field_name in data
        if field_name not in known_fields
    )

    return issues


def display_results(
    path: Path, file_type: FileType, issues: list[ValidationIssue]
) -> bool:
    """Display validation results.

    Returns:
        True if no errors found, False otherwise.
    """
    console.print(f"[cyan]File:[/cyan] {path}")
    console.print(f"[cyan]Type:[/cyan] {file_type.value}")
    console.print()

    if not issues:
        console.print(
            Panel("[green]All validations passed![/green]", border_style="green")
        )
        return True

    table = Table(title="Validation Issues")
    table.add_column("Field", style="cyan")
    table.add_column("Severity")
    table.add_column("Message", style="white")
    table.add_column("Suggestion", style="dim")

    has_errors = False
    for issue in issues:
        severity_style = (
            "[red]ERROR[/red]" if issue.severity == "error" else "[yellow]WARN[/yellow]"
        )
        table.add_row(
            issue.field, severity_style, issue.message, issue.suggestion or ""
        )
        if issue.severity == "error":
            has_errors = True

    console.print(table)

    if has_errors:
        console.print()
        console.print(
            Panel("[red]Validation failed - fix errors above[/red]", border_style="red")
        )
    else:
        console.print()
        console.print(
            Panel(
                "[yellow]Validation passed with warnings[/yellow]",
                border_style="yellow",
            )
        )

    return not has_errors


@app.command()
def validate(
    path: Annotated[Path, typer.Argument(help="Path to .md file with frontmatter")],
    file_type: Annotated[
        FileType | None,
        typer.Option(
            "--type", "-t", help="Force file type (auto-detected if not specified)"
        ),
    ] = None,
) -> None:
    """Validate YAML frontmatter in a Claude Code capability file.

    Checks:
    - YAML syntax validity
    - No forbidden multiline indicators (>- or |-)
    - Required fields present
    - Field types match schema
    - Field values within constraints (length, pattern, valid values)

    Examples:
        uv run validate_frontmatter.py skills/my-skill/SKILL.md
        uv run validate_frontmatter.py commands/my-command.md --type command
    """
    if not path.exists():
        error_console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    content = path.read_text()

    # Extract frontmatter
    frontmatter, _start_line, _end_line = extract_frontmatter(content)
    if frontmatter is None:
        error_console.print(f"[red]No YAML frontmatter found in:[/red] {path}")
        error_console.print("File must start with '---' delimiter")
        raise typer.Exit(1)

    # Detect or use specified file type
    detected_type = file_type or detect_file_type(path)
    if detected_type == FileType.UNKNOWN:
        error_console.print(
            "[yellow]Warning:[/yellow] Could not detect file type, using skill schema"
        )
        detected_type = FileType.SKILL

    # Get schema and validate
    schema = get_schema(detected_type)
    issues = validate_frontmatter(frontmatter, schema, detected_type)

    # Display results
    success = display_results(path, detected_type, issues)

    if not success:
        raise typer.Exit(1)


@app.command()
def batch(
    directory: Annotated[
        Path, typer.Argument(help="Directory to search for capability files")
    ],
    recursive: Annotated[
        bool, typer.Option("--recursive", "-r", help="Search recursively")
    ] = True,
) -> None:
    """Validate all capability files in a directory.

    Finds and validates:
    - SKILL.md files
    - Files in commands/ directories
    - Files in agents/ directories
    """
    if not directory.exists():
        error_console.print(f"[red]Directory not found:[/red] {directory}")
        raise typer.Exit(1)

    # Find all capability files
    patterns = ["**/SKILL.md", "**/commands/*.md", "**/agents/*.md"]
    files: list[Path] = []

    for pattern in patterns:
        if recursive:
            files.extend(directory.glob(pattern))
        else:
            files.extend(directory.glob(pattern.replace("**/", "")))

    if not files:
        console.print("[yellow]No capability files found[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Found {len(files)} capability files[/cyan]")
    console.print()

    total_errors = 0
    total_warnings = 0

    for file_path in sorted(files):
        content = file_path.read_text()
        frontmatter, _, _ = extract_frontmatter(content)

        if frontmatter is None:
            console.print(f"[yellow]SKIP[/yellow] {file_path} - no frontmatter")
            continue

        detected_type = detect_file_type(file_path)
        schema = get_schema(detected_type)
        issues = validate_frontmatter(frontmatter, schema, detected_type)

        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")

        if errors > 0:
            console.print(
                f"[red]FAIL[/red] {file_path} - {errors} errors, {warnings} warnings"
            )
            total_errors += errors
        elif warnings > 0:
            console.print(f"[yellow]WARN[/yellow] {file_path} - {warnings} warnings")
            total_warnings += warnings
        else:
            console.print(f"[green]PASS[/green] {file_path}")

    console.print()
    console.print(
        f"[cyan]Summary:[/cyan] {len(files)} files, {total_errors} errors, {total_warnings} warnings"
    )

    if total_errors > 0:
        raise typer.Exit(1)


@app.command()
def fix(
    path: Annotated[Path, typer.Argument(help="Path to .md file with frontmatter")],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Show what would be fixed without writing"
        ),
    ] = False,
) -> None:
    """Auto-fix common frontmatter issues.

    Fixes:
    - YAML arrays converted to comma-separated strings (allowed-tools, tools, etc.)
    - Multiline description indicators converted to single-line quoted strings

    Examples:
        uv run validate_frontmatter.py fix skills/my-skill/SKILL.md
        uv run validate_frontmatter.py fix agents/my-agent.md --dry-run
    """
    if not path.exists():
        error_console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    content = path.read_text()

    # Apply all fixes
    fixed_content, fixes = apply_fixes(content)

    if not fixes:
        console.print(f"[green]No fixes needed for:[/green] {path}")
        raise typer.Exit(0)

    console.print(f"[cyan]File:[/cyan] {path}")
    console.print("[cyan]Fixes applied:[/cyan]")
    for fix_desc in fixes:
        console.print(f"  [green]✓[/green] {fix_desc}")

    if dry_run:
        console.print()
        console.print("[yellow]Dry run - no changes written[/yellow]")
        console.print()
        console.print("[dim]Fixed content would be:[/dim]")
        console.print(
            Panel(
                fixed_content[:PREVIEW_MAX_CHARS]
                + ("..." if len(fixed_content) > PREVIEW_MAX_CHARS else "")
            )
        )
    else:
        path.write_text(fixed_content)
        console.print()
        console.print(
            Panel("[green]File updated successfully![/green]", border_style="green")
        )


@app.command()
def fix_batch(
    directory: Annotated[
        Path, typer.Argument(help="Directory to search for capability files")
    ],
    recursive: Annotated[
        bool, typer.Option("--recursive", "-r", help="Search recursively")
    ] = True,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Show what would be fixed without writing"
        ),
    ] = False,
) -> None:
    """Auto-fix all capability files in a directory.

    Finds and fixes:
    - SKILL.md files
    - Files in commands/ directories
    - Files in agents/ directories
    """
    if not directory.exists():
        error_console.print(f"[red]Directory not found:[/red] {directory}")
        raise typer.Exit(1)

    # Find all capability files
    patterns = ["**/SKILL.md", "**/commands/*.md", "**/agents/*.md"]
    files: list[Path] = []

    for pattern in patterns:
        if recursive:
            files.extend(directory.glob(pattern))
        else:
            files.extend(directory.glob(pattern.replace("**/", "")))

    if not files:
        console.print("[yellow]No capability files found[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Found {len(files)} capability files[/cyan]")
    console.print()

    total_fixed = 0
    total_fixes = 0

    for file_path in sorted(files):
        content = file_path.read_text()
        fixed_content, fixes = apply_fixes(content)

        if fixes:
            total_fixed += 1
            total_fixes += len(fixes)
            console.print(f"[green]FIX[/green] {file_path} - {len(fixes)} fixes")
            for fix_desc in fixes:
                console.print(f"      [dim]{fix_desc}[/dim]")
            if not dry_run:
                file_path.write_text(fixed_content)
        else:
            console.print(f"[dim]OK[/dim] {file_path}")

    console.print()
    if dry_run:
        console.print(
            f"[yellow]Dry run:[/yellow] {total_fixed} files would be fixed with {total_fixes} total fixes"
        )
    else:
        console.print(
            f"[green]Summary:[/green] {total_fixed} files fixed with {total_fixes} total fixes"
        )


if __name__ == "__main__":
    app()
