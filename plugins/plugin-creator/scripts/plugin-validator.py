#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.21.0",
#     "rich>=13.0.0",
#     "tiktoken>=0.8.0",
# ]
# ///
"""Plugin validator for Claude Code plugins.

Validates:
- Frontmatter schema (skills, agents, commands)
- Plugin structure (plugin.json)
- Skill complexity (token-based)
- Internal links
- Progressive disclosure structure
- Plugin completeness

Token-based complexity measurement replaces line counting for accurate AI cost estimation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

# Error code base URL for documentation links
ERROR_CODE_BASE_URL = "https://github.com/jamie-bitflight/claude_skills/blob/main/plugins/plugin-creator/docs/ERROR_CODES.md"

# Token-based complexity thresholds (Architecture lines 1156-1157)
TOKEN_WARNING_THRESHOLD = 4000  # ~500 lines equivalent
TOKEN_ERROR_THRESHOLD = 6400  # ~800 lines equivalent

# Description requirements (Architecture lines 349-350)
MIN_DESCRIPTION_LENGTH = 20
RECOMMENDED_DESCRIPTION_LENGTH = 1024

# Name format (Architecture lines 352-354)
NAME_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
MAX_SKILL_NAME_LENGTH = 40

# Trigger phrase requirements (Architecture line 357)
REQUIRED_TRIGGER_PHRASES = ["use when", "use this", "trigger", "activate"]

# ============================================================================
# ERROR CODE CONSTANTS (Architecture lines 836-887)
# ============================================================================

# Frontmatter Errors (FM001-FM010)
FM001 = "FM001"  # Missing required field (name, description)
FM002 = "FM002"  # Invalid YAML syntax
FM003 = "FM003"  # Frontmatter not closed with `---`
FM004 = "FM004"  # Forbidden multiline indicator (`>-`, `|-`)
FM005 = "FM005"  # Field type mismatch (expected string/bool)
FM006 = "FM006"  # Invalid field value (model not in enum)
FM007 = "FM007"  # Tools field is YAML array (not CSV string)
FM008 = "FM008"  # Skills field is YAML array (not CSV string)
FM009 = "FM009"  # Unquoted description with colons
FM010 = "FM010"  # Name pattern invalid (not lowercase-hyphens)

# Skill Errors (SK001-SK007)
SK001 = "SK001"  # Name contains uppercase characters
SK002 = "SK002"  # Name contains underscores (use hyphens)
SK003 = "SK003"  # Name has leading/trailing/consecutive hyphens
SK004 = "SK004"  # Description too short (minimum 20 characters)
SK005 = "SK005"  # Description missing trigger phrases
SK006 = "SK006"  # Token count exceeds 4000 (consider splitting)
SK007 = "SK007"  # Token count exceeds 6400 (must split)

# Link Errors (LK001-LK002)
LK001 = "LK001"  # Broken internal link (file does not exist)
LK002 = "LK002"  # Link missing `./` prefix (not relative path)

# Progressive Disclosure Errors (PD001-PD003)
PD001 = "PD001"  # No `references/` directory found
PD002 = "PD002"  # No `examples/` directory found
PD003 = "PD003"  # No `scripts/` directory found

# Plugin Errors (PL001-PL005)
PL001 = "PL001"  # Missing `plugin.json` file
PL002 = "PL002"  # Invalid JSON syntax in `plugin.json`
PL003 = "PL003"  # Missing required field `name` in plugin.json
PL004 = "PL004"  # Component path does not start with `./`
PL005 = "PL005"  # Referenced component file does not exist


# ============================================================================
# DATA MODELS (Architecture lines 136-480)
# ============================================================================


class FileType(StrEnum):
    """Type of capability file (Architecture lines 369-392)."""

    SKILL = "skill"
    AGENT = "agent"
    COMMAND = "command"
    PLUGIN = "plugin"
    UNKNOWN = "unknown"

    @staticmethod
    def detect_file_type(path: Path) -> FileType:
        """Detect file type from path structure.

        Args:
            path: Path to file or directory to classify

        Returns:
            FileType enum value based on path structure
        """
        if path.name == "SKILL.md":
            return FileType.SKILL
        if path.name == "plugin.json" or (path / ".claude-plugin/plugin.json").exists():
            return FileType.PLUGIN
        if "agents" in path.parts:
            return FileType.AGENT
        if "commands" in path.parts:
            return FileType.COMMAND
        return FileType.UNKNOWN


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue (Architecture lines 152-160, 395-423)."""

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
            Formatted string with severity icon, code, field, message, and optional docs URL
        """
        severity_icon = {
            "error": ":cross_mark:",
            "warning": ":warning:",
            "info": ":information:",
        }[self.severity]

        location = f":{self.line}" if self.line else ""
        suggestion_line = f"\n    → {self.suggestion}" if self.suggestion else ""
        docs = f"\n    → {self.docs_url}" if self.docs_url else ""
        return f"  {severity_icon} [{self.code}] {self.field}{location}: {self.message}{suggestion_line}{docs}"


@dataclass(frozen=True)
class ValidationResult:
    """Result from a validation check (Architecture lines 143-149)."""

    passed: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    info: list[ValidationIssue]


@dataclass(frozen=True)
class ComplexityMetrics:
    """Token-based complexity metrics (Architecture lines 431-479)."""

    total_tokens: int
    frontmatter_tokens: int
    body_tokens: int
    encoding: str = "cl100k_base"

    @property
    def status(self) -> Literal["ok", "warning", "error"]:
        """Determine status from thresholds.

        Returns:
            Status based on TOKEN_WARNING_THRESHOLD and TOKEN_ERROR_THRESHOLD
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
            Status message with token count and threshold
        """
        if self.status == "error":
            return f"CRITICAL: {self.body_tokens} tokens (>{TOKEN_ERROR_THRESHOLD})"
        if self.status == "warning":
            return f"WARNING: {self.body_tokens} tokens (>{TOKEN_WARNING_THRESHOLD})"
        return f"OK: {self.body_tokens} tokens"


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def generate_docs_url(error_code: str) -> str:
    """Generate documentation URL for error code.

    Args:
        error_code: Error code like "FM001", "SK006", etc.

    Returns:
        Full URL to error code documentation with anchor
    """
    return f"{ERROR_CODE_BASE_URL}#{error_code.lower()}"
