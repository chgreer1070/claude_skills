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

import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Literal, Protocol

import typer
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

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

# Claude CLI timeout (Architecture line 1267)
CLAUDE_TIMEOUT = 30  # seconds


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
# VALIDATOR PROTOCOL (Architecture lines 162-176)
# ============================================================================


class Validator(Protocol):
    """Protocol for all validators.

    Defines the interface that all validator classes must implement to be
    compatible with the validation framework. Validators check specific aspects
    of plugin structure and can optionally provide auto-fixing capabilities.
    """

    def validate(self, path: Path) -> ValidationResult:
        """Run validation check on path.

        Args:
            path: Path to file or directory to validate

        Returns:
            ValidationResult with passed status and any issues found
        """
        ...

    def can_fix(self) -> bool:
        """Whether this validator supports auto-fixing.

        Returns:
            True if validator can automatically fix issues, False otherwise
        """
        ...

    def fix(self, path: Path) -> list[str]:
        """Auto-fix issues in the file or directory.

        Args:
            path: Path to file or directory to fix

        Returns:
            List of human-readable descriptions of fixes applied
        """
        ...


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


def extract_frontmatter(content: str) -> tuple[str | None, int, int]:
    """Extract YAML frontmatter from content.

    Args:
        content: File content potentially containing YAML frontmatter

    Returns:
        Tuple of (frontmatter_text, start_line, end_line) or (None, 0, 0)
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


# ============================================================================
# PROGRESSIVE DISCLOSURE VALIDATOR
# ============================================================================


class ProgressiveDisclosureValidator:
    """Validates presence of progressive disclosure directories.

    Checks for references/, examples/, and scripts/ directories that help
    organize additional content for on-demand exploration. Missing directories
    are reported as INFO (not errors) since they're optional organizational aids.

    Architecture lines 1170-1186, Task T7 lines 815-876
    """

    # Directory names to check for progressive disclosure
    DISCLOSURE_DIRS: ClassVar[list[str]] = ["references", "examples", "scripts"]

    def validate(self, path: Path) -> ValidationResult:
        """Validate progressive disclosure structure in skill directory.

        Args:
            path: Path to skill directory (should contain SKILL.md)

        Returns:
            ValidationResult with info messages for missing directories
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Only validate skill directories (must contain SKILL.md)
        if path.is_file():
            path = path.parent

        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            # Not a skill directory - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Check each progressive disclosure directory
        for dir_name in self.DISCLOSURE_DIRS:
            dir_path = path / dir_name
            if not dir_path.exists():
                # Directory missing - report as INFO
                code = self._get_error_code(dir_name)
                info.append(
                    ValidationIssue(
                        field="progressive-disclosure",
                        severity="info",
                        message=f"No {dir_name}/ directory found (consider adding for documentation)",
                        code=code,
                        docs_url=generate_docs_url(code),
                        suggestion=f"Create {dir_name}/ directory to organize additional content",
                    )
                )
            else:
                # Directory exists - count files recursively
                sum(1 for _ in dir_path.rglob("*") if _.is_file())
                # No info message needed when directory exists
                # (only report missing directories)

        # Always pass - info messages don't fail validation
        return ValidationResult(
            passed=True, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (creating directories requires content creation decisions)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix progressive disclosure issues (not supported).

        Args:
            path: Path to directory to fix

        Raises:
            NotImplementedError: Progressive disclosure validation cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Progressive disclosure validation cannot be auto-fixed. "
            "Creating directories requires human decisions about content organization."
        )

    def _get_error_code(self, dir_name: str) -> str:
        """Get error code for missing directory.

        Args:
            dir_name: Directory name (references, examples, scripts)

        Returns:
            Error code (PD001, PD002, PD003)
        """
        match dir_name:
            case "references":
                return PD001
            case "examples":
                return PD002
            case "scripts":
                return PD003
            case _:
                return PD001  # Default fallback


# ============================================================================
# INTERNAL LINK VALIDATOR
# ============================================================================


class InternalLinkValidator:
    """Validates internal markdown links in SKILL.md files.

    Checks that links starting with ./ point to existing files and warns if
    relative links are missing the ./ prefix for clarity.

    Architecture lines 1188-1256, Task T8 lines 897-982
    """

    # Regex pattern for extracting markdown links (Architecture line 1219)
    LINK_PATTERN: ClassVar[str] = r"\[([^\]]+)\]\(([^)]+)\)"

    def validate(self, path: Path) -> ValidationResult:
        """Validate internal markdown links in SKILL.md.

        Args:
            path: Path to SKILL.md file

        Returns:
            ValidationResult with errors for broken links, warnings for missing ./ prefix
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Only validate SKILL.md files
        if path.name != "SKILL.md":
            # Not a skill file - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Extract all markdown links
        matches = re.finditer(self.LINK_PATTERN, content)

        # Process each link
        for match in matches:
            link_text = match.group(1)
            link_url = match.group(2)

            # Filter to relative file links only
            if self._should_ignore_link(link_url):
                continue

            # Check for missing ./ prefix (warning)
            if not link_url.startswith("./") and not link_url.startswith("../"):
                warnings.append(
                    ValidationIssue(
                        field="internal-links",
                        severity="warning",
                        message=f"Link missing ./ prefix: [{link_text}]({link_url})",
                        code=LK002,
                        docs_url=generate_docs_url(LK002),
                        suggestion=f"Use relative path: [{link_text}](./{link_url})",
                    )
                )
                # Continue validation even with missing prefix

            # Resolve link path relative to SKILL.md directory
            skill_dir = path.parent
            link_path = (skill_dir / link_url).resolve()

            # Check if linked file exists (error)
            if not link_path.exists():
                errors.append(
                    ValidationIssue(
                        field="internal-links",
                        severity="error",
                        message=f"Broken link: [{link_text}]({link_url}) (file not found)",
                        code=LK001,
                        docs_url=generate_docs_url(LK001),
                        suggestion=f"Create missing file or fix link path: {link_url}",
                    )
                )

        # Pass if no errors (warnings don't fail validation)
        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (broken links require file creation or manual correction)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix internal link issues (not supported).

        Args:
            path: Path to file to fix

        Raises:
            NotImplementedError: Internal link validation cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Internal link validation cannot be auto-fixed. "
            "Broken links require creating missing files or correcting link paths manually."
        )

    def _should_ignore_link(self, url: str) -> bool:
        """Check if link should be ignored during validation.

        Args:
            url: Link URL to check

        Returns:
            True if link should be ignored (external, anchor, absolute)
        """
        # Ignore external links
        if url.startswith(("http://", "https://", "ftp://")):
            return True

        # Ignore anchor links
        if url.startswith("#"):
            return True

        # Ignore absolute paths
        return bool(url.startswith("/"))


# ============================================================================
# PYDANTIC FRONTMATTER MODELS (from validate_frontmatter.py)
# ============================================================================


class SkillFrontmatter(BaseModel):
    """Pydantic model for skill frontmatter validation.

    Source: validate_frontmatter.py lines 95-166
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
    """Pydantic model for command frontmatter validation.

    Source: validate_frontmatter.py lines 168-227
    """

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

    Source: validate_frontmatter.py lines 229-297

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


# ============================================================================
# FRONTMATTER VALIDATOR
# ============================================================================


class FrontmatterValidator:
    """Validates and auto-fixes YAML frontmatter in capability files.

    Implements Validator protocol for frontmatter validation of skills, agents,
    and commands. Preserves exact behavior from validate_frontmatter.py.

    Source: validate_frontmatter.py lines 95-607
    """

    def validate(self, path: Path) -> ValidationResult:  # noqa: PLR0914, PLR0912, PLR0915, C901
        """Validate frontmatter in file.

        Args:
            path: Path to file with YAML frontmatter

        Returns:
            ValidationResult with errors, warnings, and info issues

        Note:
            Complexity preserved from validate_frontmatter.py for behavioral parity.
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Extract frontmatter
        frontmatter_text, _start_line, _end_line = self._extract_frontmatter(content)
        if frontmatter_text is None:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message="No YAML frontmatter found",
                    code=FM003,
                    docs_url=generate_docs_url(FM003),
                    suggestion="File must start with '---' delimiter",
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Detect file type
        file_type = FileType.detect_file_type(path)
        if file_type == FileType.UNKNOWN:
            file_type = FileType.SKILL

        # Check for forbidden multiline indicators
        if re.search(r"description:\s*[|>][-+]?\s*\n", frontmatter_text):
            errors.append(
                ValidationIssue(
                    field="description",
                    severity="error",
                    message="Uses forbidden multiline YAML syntax (|, >, |-, >-)",
                    code=FM004,
                    docs_url=generate_docs_url(FM004),
                    suggestion="Use single-line string",
                )
            )

        # Parse YAML
        try:
            data = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            errors.append(
                ValidationIssue(
                    field="(yaml)",
                    severity="error",
                    message=f"Invalid YAML syntax: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        if not isinstance(data, dict):
            errors.append(
                ValidationIssue(
                    field="(yaml)",
                    severity="error",
                    message="Frontmatter must be a YAML mapping",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Select Pydantic model based on file type
        model_class = self._get_model_class(file_type)
        if not model_class:
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Validate with Pydantic
        try:
            validated = model_class.model_validate(data)

            # Add warning for long descriptions
            if (
                hasattr(validated, "description")
                and validated.description
                and len(validated.description) > RECOMMENDED_DESCRIPTION_LENGTH
            ):
                warnings.append(
                    ValidationIssue(
                        field="description",
                        severity="warning",
                        message=f"Exceeds recommended length of {RECOMMENDED_DESCRIPTION_LENGTH} characters (got {len(validated.description)})",
                        code=SK004,
                        docs_url=generate_docs_url(SK004),
                        suggestion=f"Front-load critical information in first {RECOMMENDED_DESCRIPTION_LENGTH} characters",
                    )
                )

        except ValidationError as e:
            # Convert Pydantic errors to ValidationIssue
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                msg = error["msg"]
                code = FM005  # Default to type mismatch

                # Determine specific error code
                if "Field required" in msg:
                    code = FM001
                    msg = f"Missing required field: {field}"
                elif "String should match pattern" in msg:
                    code = FM010
                    msg = "Must use lowercase letters, numbers, and hyphens only"
                    suggestion = "Use format: lowercase-with-hyphens"
                elif "String should have at most" in msg:
                    code = FM005
                    max_len = error.get("ctx", {}).get("max_length", "unknown")
                    msg = f"Exceeds maximum length of {max_len} characters"
                    suggestion = f"Shorten to {max_len} characters or less"
                elif "Input should be" in msg and "literal" in msg.lower():
                    code = FM006
                    valid_values = error.get("ctx", {}).get("expected", "")
                    msg = f"Invalid value. Must be one of: {valid_values}"
                    suggestion = None
                elif isinstance(error.get("input"), list):
                    # Tools or skills field is YAML array
                    if "tools" in field.lower():
                        code = FM007
                        msg = "Tools field is YAML array (should be comma-separated string)"
                    elif "skills" in field.lower():
                        code = FM008
                        msg = "Skills field is YAML array (should be comma-separated string)"
                    suggestion = "Use format: 'tool1, tool2, tool3'"
                elif "colon" in msg.lower():
                    code = FM009
                    suggestion = "Quote the description or remove colons"
                else:
                    code = FM005
                    suggestion = None

                errors.append(
                    ValidationIssue(
                        field=field,
                        severity="error",
                        message=msg,
                        code=code,
                        docs_url=generate_docs_url(code),
                        suggestion=suggestion,
                    )
                )

        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            True (frontmatter validator supports auto-fixing)
        """
        return True

    def fix(self, path: Path) -> list[str]:
        """Auto-fix frontmatter issues in file.

        Fixes FM004, FM007, FM008, FM009 only. Does not fix schema violations.

        Args:
            path: Path to file to fix

        Returns:
            List of human-readable descriptions of fixes applied
        """
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return []

        # Detect file type
        file_type = FileType.detect_file_type(path)
        if file_type == FileType.UNKNOWN:
            file_type = FileType.SKILL

        # Apply fixes
        fixed_content, fixes = self._apply_fixes(content, file_type)

        if not fixes:
            return []

        # Write fixed content
        try:
            path.write_text(fixed_content, encoding="utf-8")
        except OSError:
            return []

        return fixes

    def _extract_frontmatter(self, content: str) -> tuple[str | None, int, int]:
        """Extract YAML frontmatter from content.

        Returns:
            Tuple of (frontmatter_text, start_line, end_line) or (None, 0, 0)

        Deprecated:
            Use module-level extract_frontmatter() function instead.
        """
        return extract_frontmatter(content)

    def _get_model_class(
        self, file_type: FileType
    ) -> type[SkillFrontmatter | CommandFrontmatter | AgentFrontmatter] | None:
        """Get Pydantic model class for file type.

        Returns:
            Pydantic model class or None if unknown type.
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

    def _apply_fixes(self, content: str, file_type: FileType) -> tuple[str, list[str]]:  # noqa: PLR0911, PLR0912, C901
        """Apply auto-fixes to content.

        Args:
            content: File content with frontmatter
            file_type: Type of capability file

        Returns:
            Tuple of (fixed_content, list_of_fixes_applied)

        Note:
            Complexity preserved from validate_frontmatter.py for behavioral parity.
        """
        frontmatter_text, _, _ = self._extract_frontmatter(content)
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
        model_class = self._get_model_class(file_type)
        if not model_class:
            return content, []

        try:
            validated = model_class.model_validate(original_data)
            normalized_dict = validated.model_dump(
                by_alias=True, exclude_none=True, mode="python"
            )
        except ValidationError:
            return content, []

        # Track fixes
        fixes = []

        # CRITICAL BUG WORKAROUND: Remove 'name' field from skills
        # Source: validate_frontmatter.py lines 560-573
        if file_type == FileType.SKILL and "name" in normalized_dict:
            del normalized_dict["name"]
            fixes.append(
                "Removed 'name' field (Claude Code bug: plugin skills with 'name' don't appear as slash commands)"
            )

        # Compare to detect changes
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


# ============================================================================
# NAME FORMAT VALIDATOR
# ============================================================================


class NameFormatValidator:
    """Validates skill/agent/command name format.

    Checks for:
    - Lowercase characters only (no uppercase)
    - Hyphens only (no underscores)
    - No leading/trailing hyphens
    - No consecutive hyphens

    Architecture lines 1074-1090, Task T4 lines 518-593
    """

    def validate(self, path: Path) -> ValidationResult:
        """Validate name format in frontmatter.

        Args:
            path: Path to file with YAML frontmatter

        Returns:
            ValidationResult with errors for invalid name format
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Extract frontmatter
        frontmatter_text, _start_line, _end_line = extract_frontmatter(content)
        if frontmatter_text is None:
            # No frontmatter - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Parse YAML
        try:
            data = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            # Invalid YAML - not our concern (FrontmatterValidator handles this)
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        if not isinstance(data, dict):
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Extract name field
        name = data.get("name")
        if not name or not isinstance(name, str):
            # No name field or not a string - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Check for uppercase characters
        if any(c.isupper() for c in name):
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name contains uppercase characters",
                    code=SK001,
                    docs_url=generate_docs_url(SK001),
                    suggestion="Use lowercase only (e.g., 'test-skill' not 'Test-Skill')",
                )
            )

        # Check for underscores
        if "_" in name:
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name contains underscores (use hyphens instead)",
                    code=SK002,
                    docs_url=generate_docs_url(SK002),
                    suggestion=f"Replace underscores with hyphens: '{name.replace('_', '-')}'",
                )
            )

        # Check for leading hyphens
        if name.startswith("-"):
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name has leading hyphen",
                    code=SK003,
                    docs_url=generate_docs_url(SK003),
                    suggestion=f"Remove leading hyphen: '{name.lstrip('-')}'",
                )
            )

        # Check for trailing hyphens
        if name.endswith("-"):
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name has trailing hyphen",
                    code=SK003,
                    docs_url=generate_docs_url(SK003),
                    suggestion=f"Remove trailing hyphen: '{name.rstrip('-')}'",
                )
            )

        # Check for consecutive hyphens
        if "--" in name:
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name has consecutive hyphens",
                    code=SK003,
                    docs_url=generate_docs_url(SK003),
                    suggestion="Use single hyphens only (e.g., 'test-skill' not 'test--skill')",
                )
            )

        # Validate against full pattern
        if not re.match(NAME_PATTERN, name) and not errors:
            # If we didn't catch specific issues above, add generic pattern error
            errors.append(
                ValidationIssue(
                    field="name",
                    severity="error",
                    message="Name format invalid",
                    code=SK003,
                    docs_url=generate_docs_url(SK003),
                    suggestion="Use lowercase letters, numbers, and hyphens only (e.g., 'my-skill-name')",
                )
            )

        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (name changes require human decision on correct name)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix name format issues (not supported).

        Args:
            path: Path to file to fix

        Raises:
            NotImplementedError: Name format issues cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Name format validation cannot be auto-fixed. "
            "Renaming requires human decision on correct name."
        )


# ============================================================================
# DESCRIPTION VALIDATOR
# ============================================================================


class DescriptionValidator:
    """Validates description field quality.

    Checks:
    - Minimum length (20 characters)
    - Presence of trigger phrases to help users know when to use the skill/agent/command

    Both checks produce warnings, not errors, since description quality is subjective.

    Architecture lines 1092-1113, Task T5 lines 602-672
    """

    def validate(self, path: Path) -> ValidationResult:  # noqa: PLR0911
        """Validate description field in frontmatter.

        Args:
            path: Path to file with YAML frontmatter

        Returns:
            ValidationResult with warnings for description quality issues

        Note:
            Multiple early returns are necessary to handle various skip conditions gracefully.
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Extract frontmatter
        frontmatter_text, _start_line, _end_line = extract_frontmatter(content)
        if frontmatter_text is None:
            # No frontmatter - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Parse YAML
        try:
            data = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            # Invalid YAML - not our concern (FrontmatterValidator handles this)
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        if not isinstance(data, dict):
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Extract description field
        description = data.get("description")
        if not description:
            # No description field - skip validation (pass with no warnings)
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        if not isinstance(description, str):
            # Description is not a string - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Check minimum length
        if len(description) < MIN_DESCRIPTION_LENGTH:
            warnings.append(
                ValidationIssue(
                    field="description",
                    severity="warning",
                    message=f"Description too short (minimum {MIN_DESCRIPTION_LENGTH} characters, got {len(description)})",
                    code=SK004,
                    docs_url=generate_docs_url(SK004),
                    suggestion="Add more detail to help users understand when to use this capability",
                )
            )

        # Check for trigger phrases (case-insensitive)
        description_lower = description.lower()
        has_trigger = any(
            phrase in description_lower for phrase in REQUIRED_TRIGGER_PHRASES
        )

        if not has_trigger:
            warnings.append(
                ValidationIssue(
                    field="description",
                    severity="warning",
                    message="Description missing trigger phrases",
                    code=SK005,
                    docs_url=generate_docs_url(SK005),
                    suggestion=f"Include at least one trigger phrase: {', '.join(REQUIRED_TRIGGER_PHRASES)}",
                )
            )

        # Pass if no errors (warnings don't fail validation)
        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (description quality requires human-written content)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix description issues (not supported).

        Args:
            path: Path to file to fix

        Raises:
            NotImplementedError: Description quality cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Description validation cannot be auto-fixed. "
            "Writing quality descriptions requires human judgment."
        )


# ============================================================================
# COMPLEXITY VALIDATOR (TOKEN-BASED)
# ============================================================================


class ComplexityValidator:
    """Validates skill complexity using token counting.

    Measures skill complexity by counting tokens in body content (excluding
    frontmatter) using tiktoken. Provides more accurate complexity measurement
    than line counting since it reflects actual Claude processing cost.

    Architecture lines 1115-1168, Task T6 lines 685-797
    """

    def validate(self, path: Path) -> ValidationResult:
        """Validate skill complexity using token counting.

        Args:
            path: Path to SKILL.md file

        Returns:
            ValidationResult with warnings/errors based on token thresholds

        Note:
            Multiple early returns are necessary to handle various skip conditions gracefully.
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Only validate SKILL.md files
        if path.name != "SKILL.md":
            # Not a skill file - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Read file
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                ValidationIssue(
                    field="(file)",
                    severity="error",
                    message=f"Could not read file: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Split frontmatter and body
        frontmatter_text, _start_line, _end_line = extract_frontmatter(content)

        # Calculate body content (everything after frontmatter)
        # Note: re module already imported at module level (line 27)
        if frontmatter_text is not None:
            # Find end of frontmatter
            end_match = re.search(r"\n---\s*\n", content[3:])
            body = content[end_match.end() + 3 :] if end_match else content
        else:
            # No frontmatter - entire file is body
            body = content

        # Count tokens using tiktoken (lazy-loaded for performance)
        body_tokens = self._count_tokens(body, errors, warnings, info)
        if body_tokens is None:
            # Token counting failed - errors list already populated
            return ValidationResult(
                passed=False, errors=errors, warnings=warnings, info=info
            )

        # Check against thresholds
        if body_tokens > TOKEN_ERROR_THRESHOLD:
            # CRITICAL: Must split skill
            errors.append(
                ValidationIssue(
                    field="complexity",
                    severity="error",
                    message=f"Skill body exceeds token limit ({body_tokens} tokens > {TOKEN_ERROR_THRESHOLD} threshold)",
                    code=SK007,
                    docs_url=generate_docs_url(SK007),
                    suggestion="Split skill into multiple smaller skills to reduce complexity and context window usage",
                )
            )
        elif body_tokens > TOKEN_WARNING_THRESHOLD:
            # WARNING: Consider splitting
            warnings.append(
                ValidationIssue(
                    field="complexity",
                    severity="warning",
                    message=f"Skill body is large ({body_tokens} tokens > {TOKEN_WARNING_THRESHOLD} threshold)",
                    code=SK006,
                    docs_url=generate_docs_url(SK006),
                    suggestion="Consider splitting into multiple focused skills for better maintainability",
                )
            )

        # Pass if no errors (warnings don't fail validation)
        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (complexity requires content restructuring)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix complexity issues (not supported).

        Args:
            path: Path to file to fix

        Raises:
            NotImplementedError: Complexity issues cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Complexity validation cannot be auto-fixed. "
            "Reducing complexity requires content restructuring and splitting skills."
        )

    def _count_tokens(
        self,
        text: str,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue],
        info: list[ValidationIssue],
    ) -> int | None:
        """Count tokens in text using tiktoken (lazy-loaded).

        Args:
            text: Text content to count tokens in
            errors: List to append errors to if token counting fails
            warnings: Warnings list (unused but required for signature consistency)
            info: Info list (unused but required for signature consistency)

        Returns:
            Token count, or None if tiktoken unavailable or counting failed
        """
        # Lazy-load tiktoken for performance (only imported when validation runs)
        try:
            import tiktoken  # noqa: PLC0415
        except ImportError as e:
            errors.append(
                ValidationIssue(
                    field="(dependencies)",
                    severity="error",
                    message=f"tiktoken library not available: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                    suggestion="Install tiktoken: pip install tiktoken>=0.8.0",
                )
            )
            return None

        # Count tokens using cl100k_base (GPT-4/Claude compatible)
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except (ValueError, KeyError) as e:
            # ValueError: Invalid encoding name
            # KeyError: Encoding data not found
            errors.append(
                ValidationIssue(
                    field="(token-counting)",
                    severity="error",
                    message=f"Token counting failed: {e}",
                    code=FM002,
                    docs_url=generate_docs_url(FM002),
                )
            )
            return None


# ============================================================================
# PLUGIN STRUCTURE VALIDATOR (CLAUDE CLI INTEGRATION)
# ============================================================================


class PluginStructureValidator:
    """Validates plugin structure using claude CLI.

    Integrates with external `claude plugin validate` CLI command for
    plugin.json validation. Gracefully handles cases where claude CLI
    is not available by skipping validation.

    Architecture lines 1258-1286, Task T9 lines 1034-1124
    """

    def validate(self, path: Path) -> ValidationResult:
        """Validate plugin structure using claude CLI.

        Args:
            path: Path to plugin directory or file within plugin

        Returns:
            ValidationResult with errors from claude CLI or info if skipped
        """
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        info: list[ValidationIssue] = []

        # Find plugin directory (contains .claude-plugin/plugin.json)
        plugin_dir = self._find_plugin_directory(path)
        if plugin_dir is None:
            # Not a plugin directory - skip validation
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Check if claude CLI is available and get full path
        claude_path = self._get_claude_path()
        if claude_path is None:
            # Claude not available - skip with info message
            info.append(
                ValidationIssue(
                    field="(plugin-structure)",
                    severity="info",
                    message="Claude CLI not available, skipping plugin structure validation",
                    code=PL001,
                    docs_url=generate_docs_url(PL001),
                    suggestion="Install Claude Code to enable plugin validation",
                )
            )
            return ValidationResult(
                passed=True, errors=errors, warnings=warnings, info=info
            )

        # Run claude plugin validate
        try:
            result = subprocess.run(
                [claude_path, "plugin", "validate", str(plugin_dir)],
                capture_output=True,
                text=True,
                timeout=CLAUDE_TIMEOUT,
                check=False,
            )

            # Parse output for errors
            if result.returncode != 0:
                # Validation failed - parse errors from output
                self._parse_claude_errors(
                    result.stdout, result.stderr, errors, warnings, info
                )

        except subprocess.TimeoutExpired:
            errors.append(
                ValidationIssue(
                    field="(plugin-validation)",
                    severity="error",
                    message=f"Claude plugin validation timed out after {CLAUDE_TIMEOUT} seconds",
                    code=PL002,
                    docs_url=generate_docs_url(PL002),
                )
            )
        except FileNotFoundError:
            # Claude CLI not found (should be caught by _is_claude_available)
            info.append(
                ValidationIssue(
                    field="(plugin-structure)",
                    severity="info",
                    message="Claude CLI not found in PATH",
                    code=PL001,
                    docs_url=generate_docs_url(PL001),
                    suggestion="Install Claude Code to enable plugin validation",
                )
            )
        except OSError as e:
            # Other subprocess errors
            errors.append(
                ValidationIssue(
                    field="(plugin-validation)",
                    severity="error",
                    message=f"Failed to run claude plugin validate: {e}",
                    code=PL002,
                    docs_url=generate_docs_url(PL002),
                )
            )

        # Pass if no errors (warnings/info don't fail validation)
        passed = len(errors) == 0
        return ValidationResult(
            passed=passed, errors=errors, warnings=warnings, info=info
        )

    def can_fix(self) -> bool:
        """Check if validator supports auto-fixing.

        Returns:
            False (plugin structure issues require manual structural changes)
        """
        return False

    def fix(self, path: Path) -> list[str]:
        """Auto-fix plugin structure issues (not supported).

        Args:
            path: Path to plugin directory to fix

        Raises:
            NotImplementedError: Plugin structure validation cannot be auto-fixed

        Returns:
            Never returns (always raises)
        """
        raise NotImplementedError(
            "Plugin structure validation cannot be auto-fixed. "
            "Structural issues require manual changes to plugin.json and component files."
        )

    def _get_claude_path(self) -> str | None:
        """Get full path to claude CLI if available.

        Returns:
            Full path to claude executable, or None if not found
        """
        return shutil.which("claude")

    def _find_plugin_directory(self, path: Path) -> Path | None:
        """Find plugin directory containing .claude-plugin/plugin.json.

        Args:
            path: Path to file or directory within plugin

        Returns:
            Path to plugin directory, or None if not found
        """
        # If path is a file, start from parent directory
        search_path = path.parent if path.is_file() else path

        # Search up the directory tree for .claude-plugin/plugin.json
        for parent in [search_path, *search_path.parents]:
            plugin_json = parent / ".claude-plugin" / "plugin.json"
            if plugin_json.exists():
                return parent

        return None

    def _parse_claude_errors(
        self,
        stdout: str,
        stderr: str,
        errors: list[ValidationIssue],
        warnings: list[ValidationIssue],
        info: list[ValidationIssue],
    ) -> None:
        """Parse claude CLI output for validation errors.

        Args:
            stdout: Standard output from claude CLI
            stderr: Standard error from claude CLI
            errors: List to append error issues to
            warnings: List to append warning issues to
            info: List to append info issues to
        """
        # Combine stdout and stderr for parsing
        output = stdout + "\n" + stderr

        # Map claude CLI error patterns to error codes
        error_patterns = {
            PL001: r"missing.*plugin\.json|plugin\.json.*not found",
            PL002: r"invalid.*json|json.*syntax|parse.*error",
            PL003: r"missing.*required.*field.*name|name.*required",
            PL004: r"path.*must.*start.*with.*\./|invalid.*path.*format",
            PL005: r"file.*does not exist|referenced.*file.*not found|missing.*file",
        }

        # Check for each error pattern
        for code, pattern in error_patterns.items():
            if re.search(pattern, output, re.IGNORECASE):
                errors.append(
                    ValidationIssue(
                        field="plugin.json",
                        severity="error",
                        message=self._get_error_message(code, output),
                        code=code,
                        docs_url=generate_docs_url(code),
                        suggestion=self._get_error_suggestion(code),
                    )
                )

        # If no specific error pattern matched but validation failed, add generic error
        if not errors:
            errors.append(
                ValidationIssue(
                    field="plugin.json",
                    severity="error",
                    message="Plugin validation failed (see claude CLI output for details)",
                    code=PL002,
                    docs_url=generate_docs_url(PL002),
                )
            )

    def _get_error_message(self, code: str, output: str) -> str:  # noqa: PLR0911
        """Get human-readable error message for code.

        Args:
            code: Error code (PL001-PL005)
            output: CLI output containing error details

        Returns:
            Human-readable error message
        """
        # Extract first line containing relevant error text
        lines = output.split("\n")
        for text_line in lines:
            stripped_line = text_line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                continue
            if any(
                keyword in stripped_line.lower()
                for keyword in ["error", "missing", "invalid", "required", "not found"]
            ):
                return stripped_line[:200]  # Truncate long messages

        # Fallback to generic messages
        match code:
            case "PL001":
                return "Missing plugin.json file in .claude-plugin/ directory"
            case "PL002":
                return "Invalid JSON syntax in plugin.json"
            case "PL003":
                return "Missing required field 'name' in plugin.json"
            case "PL004":
                return "Component path does not start with './'"
            case "PL005":
                return "Referenced component file does not exist"
            case _:
                return "Plugin structure validation failed"

    def _get_error_suggestion(self, code: str) -> str:
        """Get suggestion for fixing error.

        Args:
            code: Error code (PL001-PL005)

        Returns:
            Human-readable suggestion for fixing the error
        """
        match code:
            case "PL001":
                return "Create .claude-plugin/plugin.json with required fields"
            case "PL002":
                return "Validate JSON syntax: python3 -m json.tool .claude-plugin/plugin.json"
            case "PL003":
                return 'Add \'name\' field to plugin.json: {"name": "plugin-name"}'
            case "PL004":
                return "Ensure all component paths start with './' (e.g., './skills/skill-name/')"
            case "PL005":
                return "Verify all referenced files exist at specified paths"
            case _:
                return "Run 'claude plugin validate' for detailed error information"


# ============================================================================
# REPORTER PROTOCOL (Architecture lines 206-272)
# ============================================================================


class Reporter(Protocol):
    """Protocol for result reporters.

    Defines interface for formatting and displaying validation results to users.
    Different implementations support various output formats (Rich terminal,
    plain text for CI, summary).
    """

    def report(
        self, results: list[tuple[Path, ValidationResult]], verbose: bool = False
    ) -> None:
        """Display validation results.

        Args:
            results: List of (file_path, ValidationResult) tuples from validation
            verbose: Whether to show additional detail like info messages
        """
        ...

    def summarize(
        self, total_files: int, passed: int, failed: int, warnings: int
    ) -> None:
        """Display summary statistics.

        Args:
            total_files: Total number of files validated
            passed: Number of files that passed validation
            failed: Number of files that failed validation
            warnings: Number of files with warnings (passed but with issues)
        """
        ...


# ============================================================================
# CONSOLE REPORTER (Rich-based)
# ============================================================================


class ConsoleReporter:
    """Rich-based terminal reporter with colored output.

    Uses Rich library for formatted terminal output with colors, tables, and
    styled text. Implements Rich table best practices from python3-development
    skill for proper width handling and no-wrap display.

    Architecture lines 239-252
    """

    def __init__(self, no_color: bool = False) -> None:
        """Initialize console reporter.

        Args:
            no_color: Disable color output for non-TTY environments
        """
        # Lazy import Rich to avoid startup cost when not needed
        from rich.console import Console  # noqa: PLC0415

        self.console = Console(force_terminal=not no_color, no_color=no_color)
        self.no_color = no_color

    def report(
        self, results: list[tuple[Path, ValidationResult]], verbose: bool = False
    ) -> None:
        """Display validation results with Rich formatting.

        Args:
            results: List of (file_path, ValidationResult) tuples from validation
            verbose: Whether to show info messages in addition to errors/warnings
        """
        for file_path, result in results:
            # Collect all issues to display
            issues_to_show = [*result.errors, *result.warnings]
            if verbose:
                issues_to_show.extend(result.info)

            if not issues_to_show:
                # File passed with no issues
                self.console.print(
                    f":white_check_mark: [green]{file_path}[/green] - PASSED"
                )
                continue

            # File has issues - show them
            self.console.print(f"\n[bold]{file_path}[/bold]")

            for issue in issues_to_show:
                # Format issue with severity icon, code, field, message
                severity_icons = {
                    "error": ":cross_mark:",
                    "warning": ":warning:",
                    "info": ":information:",
                }
                severity_colors = {"error": "red", "warning": "yellow", "info": "blue"}

                icon = severity_icons.get(issue.severity, "")
                color = severity_colors.get(issue.severity, "white")
                location = f":{issue.line}" if issue.line else ""

                # Main message line
                self.console.print(
                    f"  {icon} [{color}][{issue.code}][/{color}] "
                    f"{issue.field}{location}: {issue.message}"
                )

                # Suggestion line (if present)
                if issue.suggestion:
                    self.console.print(f"    [dim]→[/dim] {issue.suggestion}")

                # Docs URL line (if present)
                if issue.docs_url:
                    self.console.print(
                        f"    [dim]→[/dim] [link]{issue.docs_url}[/link]"
                    )

    def summarize(
        self, total_files: int, passed: int, failed: int, warnings: int
    ) -> None:
        """Display summary statistics with Rich formatting.

        Args:
            total_files: Total number of files validated
            passed: Number of files that passed validation
            failed: Number of files that failed validation
            warnings: Number of files with warnings (passed but with issues)
        """
        from rich.panel import Panel  # noqa: PLC0415

        # Determine overall status
        if failed == 0:
            status_icon = ":white_check_mark:"
            status_text = "PASSED"
            status_color = "green"
        else:
            status_icon = ":cross_mark:"
            status_text = "FAILED"
            status_color = "red"

        # Build summary text
        summary_lines = [
            f"{status_icon} [bold {status_color}]{status_text}[/bold {status_color}]",
            "",
            f"Total files: {total_files}",
            f"[green]Passed: {passed}[/green]",
            f"[red]Failed: {failed}[/red]",
        ]

        if warnings > 0:
            summary_lines.append(f"[yellow]Warnings: {warnings}[/yellow]")

        summary = "\n".join(summary_lines)

        # Display in panel
        self.console.print(
            Panel(
                summary,
                title="Validation Summary",
                border_style=status_color,
                expand=False,
            )
        )


# ============================================================================
# CI REPORTER (Plain text)
# ============================================================================


class CIReporter:
    """Plain text reporter for CI environments.

    Outputs validation results without ANSI color codes or Rich formatting.
    Uses standard file:line:code:message format for compatibility with CI
    tools and log parsers.

    Architecture lines 239-252
    """

    def report(
        self, results: list[tuple[Path, ValidationResult]], verbose: bool = False
    ) -> None:
        """Display validation results in plain text.

        Args:
            results: List of (file_path, ValidationResult) tuples from validation
            verbose: Whether to show info messages in addition to errors/warnings
        """
        for file_path, result in results:
            # Collect all issues to display
            issues_to_show = [*result.errors, *result.warnings]
            if verbose:
                issues_to_show.extend(result.info)

            if not issues_to_show:
                # File passed with no issues
                print(f"✓ {file_path} - PASSED")
                continue

            # File has issues - show them
            print(f"\n{file_path}")

            for issue in issues_to_show:
                # Format: file:line [CODE] field: message
                severity_prefixes = {
                    "error": "✗ ERROR",
                    "warning": "⚠ WARN",
                    "info": "i INFO",
                }
                prefix = severity_prefixes.get(issue.severity, "")
                location = f":{issue.line}" if issue.line else ""

                # Main message line
                print(
                    f"  {prefix} [{issue.code}] {issue.field}{location}: {issue.message}"
                )

                # Suggestion line (if present)
                if issue.suggestion:
                    print(f"    → {issue.suggestion}")

                # Docs URL line (if present)
                if issue.docs_url:
                    print(f"    → {issue.docs_url}")

    def summarize(
        self, total_files: int, passed: int, failed: int, warnings: int
    ) -> None:
        """Display summary statistics in plain text.

        Args:
            total_files: Total number of files validated
            passed: Number of files that passed validation
            failed: Number of files that failed validation
            warnings: Number of files with warnings (passed but with issues)
        """
        # Determine overall status
        status = "✓ PASSED" if failed == 0 else "✗ FAILED"

        # Display summary
        print("\n" + "=" * 60)
        print(f"{status}")
        print(f"Total files: {total_files}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        if warnings > 0:
            print(f"Warnings: {warnings}")
        print("=" * 60)


# ============================================================================
# SUMMARY REPORTER (One-line status)
# ============================================================================


class SummaryReporter:
    """Single-line summary reporter for quick status checks.

    Outputs minimal validation summary in a single line format. Useful for
    scripts, pre-commit hooks, or quick status checks.

    Architecture lines 239-252
    """

    def report(
        self, results: list[tuple[Path, ValidationResult]], verbose: bool = False
    ) -> None:
        """Display nothing (summary-only reporter).

        Args:
            results: List of (file_path, ValidationResult) tuples from validation
            verbose: Whether to show info messages (ignored for summary reporter)
        """
        # Summary reporter only shows final summary, not per-file results

    def summarize(
        self, total_files: int, passed: int, failed: int, warnings: int
    ) -> None:
        """Display single-line summary.

        Args:
            total_files: Total number of files validated
            passed: Number of files that passed validation
            failed: Number of files that failed validation
            warnings: Number of files with warnings (passed but with issues)
        """
        # Determine overall status
        if failed == 0:
            status_icon = "✓"
            status = f"{passed}/{total_files} files passed"
        else:
            status_icon = "✗"
            status = f"{failed}/{total_files} files failed"

        # Add warnings if present
        if warnings > 0:
            status += f" ({warnings} with warnings)"

        print(f"{status_icon} {status}")


# ============================================================================
# CLI LAYER (Architecture lines 87-129)
# ============================================================================


def main(  # noqa: PLR0912, C901
    path: Path = typer.Argument(
        ..., help="Path to plugin, skill, agent, or command file to validate"
    ),
    check: bool = typer.Option(False, "--check", help="Validate only, don't auto-fix"),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix issues where possible"),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed validation output including info messages",
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable color output for CI environments"
    ),
) -> None:
    """Validate Claude Code plugins, skills, agents, and commands.

    Validates frontmatter schema, plugin structure, skill complexity, internal links,
    and progressive disclosure. Optionally auto-fixes issues.

    Examples:
        # Validate single file
        ./plugin-validator.py path/to/SKILL.md

        # Validate entire plugin
        ./plugin-validator.py plugins/my-plugin

        # Auto-fix issues
        ./plugin-validator.py --fix path/to/SKILL.md

        # Validate for CI (no color)
        ./plugin-validator.py --no-color plugins/my-plugin

    Exit Codes:
        0: Success (all checks passed)
        1: Validation errors found
        2: Usage error (invalid arguments)
        130: Interrupted by user (Ctrl+C)

    Note:
        Complexity warnings suppressed (PLR0912, C901) for CLI entry point.
        Branching complexity is inherent to argument validation and workflow routing.
    """
    try:
        # Validate arguments
        if not path.exists():
            typer.echo(f"Error: Path does not exist: {path}", err=True)
            raise typer.Exit(2) from None

        if check and fix:
            typer.echo("Error: Cannot use both --check and --fix flags", err=True)
            raise typer.Exit(2) from None

        # Detect file type
        file_type = FileType.detect_file_type(path)

        # Initialize validators based on file type
        validators: list[Validator] = []

        if file_type in {FileType.SKILL, FileType.AGENT, FileType.COMMAND}:
            # Capability files: validate frontmatter, name, description
            validators.extend([
                FrontmatterValidator(),
                NameFormatValidator(),
                DescriptionValidator(),
            ])

            # Skill-specific validators
            if file_type == FileType.SKILL:
                validators.extend([
                    ComplexityValidator(),
                    InternalLinkValidator(),
                    ProgressiveDisclosureValidator(),
                ])

        elif file_type == FileType.PLUGIN:
            # Plugin directories: validate structure
            validators.append(PluginStructureValidator())

        else:
            # Unknown type
            typer.echo(f"Error: Cannot determine file type for: {path}", err=True)
            typer.echo(
                "Expected: SKILL.md, agent .md, command .md, or plugin directory",
                err=True,
            )
            raise typer.Exit(2) from None

        # Run validation
        results: list[tuple[Path, ValidationResult]] = []
        for validator in validators:
            result = validator.validate(path)
            results.append((path, result))

        # Apply fixes if requested and validator supports it
        if fix:
            fixes_applied: list[str] = []
            for validator in validators:
                if validator.can_fix():
                    try:
                        validator_fixes = validator.fix(path)
                        fixes_applied.extend(validator_fixes)
                    except NotImplementedError:
                        pass  # Validator doesn't support fixing

            # Re-validate after fixes
            if fixes_applied:
                results = []
                for validator in validators:
                    result = validator.validate(path)
                    results.append((path, result))

        # Select reporter based on --no-color flag
        reporter: Reporter
        reporter = CIReporter() if no_color else ConsoleReporter(no_color=no_color)

        # Report results
        reporter.report(results, verbose=verbose)

        # Calculate summary statistics
        total_files = len(results)
        passed = sum(1 for _, r in results if r.passed)
        failed = sum(1 for _, r in results if not r.passed)
        warnings = sum(1 for _, r in results if r.warnings and r.passed)

        # Display summary
        reporter.summarize(total_files, passed, failed, warnings)

        # Exit with appropriate code
        if failed > 0:
            raise typer.Exit(1) from None
        raise typer.Exit(0) from None

    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(130) from None


# Create Typer app
app = typer.Typer(
    name="plugin-validator",
    help="Validate Claude Code plugins and skills",
    add_completion=False,
)
app.command()(main)


if __name__ == "__main__":
    app()
