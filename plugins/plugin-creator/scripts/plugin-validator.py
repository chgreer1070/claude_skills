#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.0.0",
#     "tiktoken>=0.8.0",
#     "pyyaml>=6.0",
#     "pydantic>=2.0.0",
# ]
# ///
"""Plugin validator for Claude Code plugins, skills, agents, and commands.

This tool provides comprehensive validation for Claude Code capability files:
- Frontmatter schema validation
- Skill structure and quality checks
- Token-based complexity measurement
- Internal link validation
- Progressive disclosure structure

Consolidates and replaces:
- validate_frontmatter.py (frontmatter validation)
- validate-skill-structure.sh (quality checks)
- count-skill-lines.sh (complexity measurement)

Uses token-based metrics instead of line counts for more accurate complexity assessment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

# Constants - Token-based complexity thresholds
TOKEN_WARNING_THRESHOLD = 4000  # ~500 lines equivalent
TOKEN_ERROR_THRESHOLD = 6400  # ~800 lines equivalent

# Description requirements
MIN_DESCRIPTION_LENGTH = 20
RECOMMENDED_DESCRIPTION_LENGTH = 1024

# Name format
NAME_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
MAX_SKILL_NAME_LENGTH = 40

# Trigger phrase requirements
REQUIRED_TRIGGER_PHRASES = ["use when", "use this", "trigger", "activate"]

# Documentation base URL
ERROR_CODE_BASE_URL = "https://github.com/yourusername/claude_skills/blob/main/plugins/plugin-creator/docs/validation-errors.md"


# Error code constants - Frontmatter errors (FM001-FM010)
FM001 = "FM001"  # YAML syntax error
FM002 = "FM002"  # Missing frontmatter delimiters
FM003 = "FM003"  # Missing required field
FM004 = "FM004"  # Invalid field type
FM005 = "FM005"  # Invalid field value
FM006 = "FM006"  # Forbidden multiline indicator
FM007 = "FM007"  # Tools/skills not comma-separated string
FM008 = "FM008"  # Name format violation
FM009 = "FM009"  # Description has unescaped colons
FM010 = "FM010"  # Unknown frontmatter field

# Error code constants - Skill structure errors (SK001-SK007)
SK001 = "SK001"  # Name field missing (when required)
SK002 = "SK002"  # Name format invalid
SK003 = "SK003"  # Description too short
SK004 = "SK004"  # Description missing trigger phrases
SK005 = "SK005"  # Skill name exceeds max length
SK006 = "SK006"  # Body content missing
SK007 = "SK007"  # Frontmatter not closed properly

# Error code constants - Link validation errors (LK001-LK002)
LK001 = "LK001"  # Broken internal link
LK002 = "LK002"  # Invalid link format

# Error code constants - Progressive disclosure errors (PD001-PD003)
PD001 = "PD001"  # Missing references directory
PD002 = "PD002"  # Missing examples directory
PD003 = "PD003"  # Missing scripts directory

# Error code constants - Plugin structure errors (PL001-PL005)
PL001 = "PL001"  # plugin.json missing
PL002 = "PL002"  # plugin.json invalid JSON
PL003 = "PL003"  # plugin.json missing required field
PL004 = "PL004"  # plugin.json path format invalid
PL005 = "PL005"  # plugin.json referenced file not found


class FileType(StrEnum):
    """Type of capability file."""

    SKILL = "skill"
    AGENT = "agent"
    COMMAND = "command"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"

    @staticmethod
    def detect_file_type(path: Path) -> FileType:
        """Detect file type from path structure.

        Args:
            path: Path to the file or directory to detect

        Returns:
            FileType enum value
        """
        if path.is_file():
            if path.name == "SKILL.md":
                return FileType.SKILL
            if path.name == "plugin.json" or path.parent.name == ".claude-plugin":
                return FileType.PLUGIN
            if "agents" in path.parts:
                return FileType.AGENT
            if "commands" in path.parts:
                return FileType.COMMAND
        else:
            # Directory paths
            if (path / "SKILL.md").exists():
                return FileType.SKILL
            if (path / ".claude-plugin" / "plugin.json").exists():
                return FileType.PLUGIN

        return FileType.UNKNOWN


@dataclass(frozen=True)
class ValidationIssue:
    """A validation issue with context and remediation guidance.

    This represents a single validation problem found in a capability file.
    Issues include error code, severity, context, and actionable suggestions.
    """

    field: str
    severity: Literal["error", "warning", "info"]
    message: str
    code: str
    line: int | None = None
    suggestion: str | None = None
    docs_url: str | None = None

    def format(self) -> str:
        """Format issue for display.

        Returns:
            Formatted string with emoji, field, location, and message
        """
        severity_icon = {"error": "✗", "warning": "⚠", "info": "i"}[self.severity]

        location = f":{self.line}" if self.line else ""
        code_display = f"[{self.code}]" if self.code else ""

        formatted = (
            f"  {severity_icon} {self.field}{location}: {self.message} {code_display}"
        )

        if self.suggestion:
            formatted += f"\n    → {self.suggestion}"

        if self.docs_url:
            formatted += f"\n    → Documentation: {self.docs_url}"

        return formatted


@dataclass(frozen=True)
class ComplexityMetrics:
    """Token-based complexity metrics for skill files.

    Uses tiktoken to measure actual token counts that Claude processes,
    providing more accurate complexity assessment than line counts.
    """

    total_tokens: int
    frontmatter_tokens: int
    body_tokens: int
    encoding: str = "cl100k_base"

    @property
    def status(self) -> Literal["ok", "warning", "error"]:
        """Determine status from thresholds.

        Returns:
            Status level based on body_tokens:
            - "ok": Under warning threshold
            - "warning": Over warning threshold but under error threshold
            - "error": Over error threshold
        """
        if self.body_tokens > TOKEN_ERROR_THRESHOLD:
            return "error"
        if self.body_tokens > TOKEN_WARNING_THRESHOLD:
            return "warning"
        return "ok"

    @property
    def message(self) -> str:
        """Human-readable status message.

        Returns:
            Formatted message with token count and threshold context
        """
        if self.status == "error":
            return f"CRITICAL: {self.body_tokens} tokens (>{TOKEN_ERROR_THRESHOLD})"
        if self.status == "warning":
            return f"WARNING: {self.body_tokens} tokens (>{TOKEN_WARNING_THRESHOLD})"
        return f"OK: {self.body_tokens} tokens"


@dataclass(frozen=True)
class ValidationResult:
    """Result from a validation check.

    Aggregates all validation issues found during validation,
    categorized by severity level.
    """

    passed: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    info: list[ValidationIssue]


def generate_docs_url(error_code: str) -> str:
    """Generate documentation URL for an error code.

    Args:
        error_code: The error code (e.g., "FM001", "SK003")

    Returns:
        Full URL to documentation for this error code
    """
    return f"{ERROR_CODE_BASE_URL}#{error_code.lower()}"


def main() -> None:
    """Entry point for plugin validator CLI.

    To be implemented in subsequent tasks.
    """
    raise NotImplementedError("CLI implementation pending in Task T3")


if __name__ == "__main__":
    main()
