---
name: python3-development
description: Python 3.11+ development with CLI apps (Typer/Rich), testing (pytest), linting (ruff/mypy), and TDD workflows. Use when building Python CLIs, writing tests, fixing linting errors, configuring pyproject.toml, creating portable scripts, or reviewing Python code for best practices.
version: 1.2.0
last_updated: '2026-01-14'
python_compatibility: 3.11+
---

# Opinionated Python Development Skill

Python development guide for modern Python 3.11-3.14 patterns.

## Skill Architecture

### Bundled Resources (Included in This Skill)

**Reference Documentation:**

- [User Project Conventions](./references/user-project-conventions.md) - Extracted conventions from user's production projects (MANDATORY for new projects)
- [Modern Python Modules](./references/modern-modules.md) - 50+ library guides with usage patterns and best practices
- [Tool & Library Registry](./references/tool-library-registry.md) - Development tools catalog for linting, testing, and build automation
- [API Reference](./references/api_reference.md) - API specifications and integration guides
- [Python Development Orchestration](./references/python-development-orchestration.md) - Detailed workflow patterns for TDD, feature addition, refactoring, and code review

**Command Templates and Guides** (`commands/`):

- Reference material for creating slash commands (NOT the actual slash commands)
- Command templates and patterns for development
- Testing and development workflow guides
- See `../../commands/` directory for details

**Scripts and Assets:**

- Example scripts demonstrating patterns
- Configuration templates and boilerplate

**System Tools** (install via package manager or uv):

- `uv` - Python package and project manager (required)
- `ruff` - Linter and formatter
- `pyright` - Type checker (Microsoft)
- `mypy` - Static type checker
- `pytest` - Testing framework
- `pre-commit` - Git hook framework
- `mutmut` - Mutation testing (for critical code)
- `bandit` - Security scanner (for critical code)

**Installation Notes:**

- Use the `uv` skill for comprehensive uv documentation and package management guidance

## Core Concepts

### Python Development Standards

This skill provides modern Python 3.11+ standards, quality gates, and reference documentation for Python development.

**Note on command templates**:

This plugin includes **command templates** under `./commands/` as reference material. For actual invocation, prefer **skills** (e.g., `modernpython`, `shebangpython`).

**Reference Documentation**:

- Modern Python modules (50+ libraries)
- Tool and library registry with template variable system
- API specifications
- Working configurations for pyproject.toml, ruff, mypy, pytest

**Docstring Standard**: Google style (Args/Returns/Raises sections). See [User Project Conventions](./references/user-project-conventions.md) for ruff pydocstyle configuration (`convention = "google"`).

**CRITICAL: Pyproject.toml Template Variables**:

All pyproject.toml examples use explicit template variables (e.g., `{{project_name_from_directory_or_git_remote}}`) instead of generic placeholders. The model MUST replace ALL template variables with actual values before creating files. See [Tool & Library Registry sections 18-19](./references/tool-library-registry.md#18-pyprojecttoml-template-variable-reference) for:

- Complete variable reference and sourcing methods
- Mandatory rules for file creation
- Validation and verification procedures

### Script Dependency Trade-offs

Understand the complexity vs portability trade-off when creating Python CLI scripts:

**Scripts with dependencies (Typer + Rich via PEP 723)**:

- **Benefits**:
  - Less development complexity - Leverage well-tested libraries for argument parsing, formatting, validation
  - Less code to write - Typer handles CLI boilerplate, Rich handles output formatting
  - Better UX - Colors, progress bars, structured output built-in
  - Just as simple to execute - PEP 723 makes it a single-file executable; uv handles dependencies automatically
- **Trade-off**: Requires network access on first run (to fetch packages)

**stdlib-only scripts**:

- **Benefits**:
  - Maximum portability - Runs on ANY Python installation without network access
  - Best for: Air-gapped systems, restricted corporate environments, embedded systems
- **Trade-offs**:
  - More development complexity - Build everything from scratch (manual argparse, manual tree formatting, manual color codes)
  - More code to write and test - Everything must be implemented manually
  - Basic UX - Limited formatting without external libraries

**Default recommendation:** Use Typer + Rich with PEP 723 unless you have specific portability requirements that prevent network access.

**See:**

- [Typer and Rich CLI Examples](./assets/typer_examples/index.md) for Rich width handling solutions

### Rich Panel and Table Width Handling

For Rich table and panel width patterns, activate the `/python3-development:python-cli-architect` skill.

**Executable Examples**: See [./assets/typer_examples/](./assets/typer_examples/index.md) for complete working scripts:

- `console_no_wrap_example.py` - Plain text wrapping solutions
- `console_containers_no_wrap.py` - Panel/Table width handling with `get_rendered_width()`

### Rich Emoji Usage

**Instruction**: In Rich console output, always use Rich emoji tokens instead of literal Unicode emojis.

**Use Rich emoji tokens**: `:white_check_mark: :cross_mark: :magnifying_glass:`

**Why**: Cross-platform compatibility, consistent rendering, markdown-safe alignment

**Example:**

```python
from rich.console import Console

console = Console()

# Correct - Rich emoji tokens
console.print(":white_check_mark: Task completed")
console.print(":cross_mark: Task failed")
console.print(":sparkles: New feature")
console.print(":rocket: Performance improvement")
```

**Benefits**:

- Rich emoji tokens work consistently across all terminals and fonts
- Avoid markdown table alignment issues (emoji width calculation problems)
- Enable proper width measurement in `get_rendered_width()`
- Ensure cross-platform compatibility (Windows, Linux, macOS)

**See**: [Rich Emoji Documentation](https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-emoji) for complete emoji token reference.

### Python Exception Handling

Catch exceptions only when you have a specific recovery action. Let all other errors propagate to the caller.

**Reason**: Fail-fast principle surfaces issues early rather than hiding them behind generic error messages.

**Pattern**:

```python
def get_user(id):
    return db.query(User, id)  # Errors surface naturally

def get_user_with_handling(id):
    try:
        return db.query(User, id)
    except ConnectionError:
        logger.warning("DB unavailable, using cache")
        return cache.get(f"user:{id}")  # Specific recovery action
```

When adding try/except, answer: "What specific error do I expect, and what is my recovery action?"

**See**: [Exception Handling in Python CLI Applications](./references/exception-handling.md) for comprehensive patterns including Typer exception chain prevention.

### Type Safety with Mypy

**REQUIREMENT**: All Python code MUST be comprehensively typed using Python 3.11+ native type hints.

**Python Version**: Python 3.11+ is required unless explicitly documented otherwise. Older versions are rare, documented exceptions.

**The model MUST read the official mypy documentation examples before implementing type patterns.**

For comprehensive type safety guidance including Generics, Protocols, TypedDict, Type Narrowing, attrs/dataclasses/pydantic comparison, and mypy configuration, see [Type Safety with Mypy Reference](./references/type-safety-mypy.md).

## Command Usage

### /python3-development:modernpython

**Purpose**: Comprehensive reference guide for Python 3.11+ patterns with official PEP citations

**When to use**:

- As reference guide when writing new code
- Learning modern Python 3.11-3.14 features and patterns
- Understanding official PEPs (585, 604, 695, etc.)
- Identifying legacy patterns to avoid
- Finding modern alternatives for old code

**Note**: This is a reference document to READ, not an automated validation tool. Use it to guide your implementation choices.

**Usage**:

```text
/python3-development:modernpython
→ Loads comprehensive reference guide
→ Provides Python 3.11+ pattern examples
→ Includes PEP citations with research tool guidance (prefer MCP tools: Ref/exa over WebFetch)
→ Shows legacy patterns to avoid
→ Shows modern alternatives to use
→ Framework-specific guides (Typer, Rich, pytest)

Research tool preference for PEP documentation:
1. mcp__Ref__ref_search_documentation(query="PEP {number} Python enhancement proposal")
2. mcp__exa__get_code_context_exa(query="PEP {number} implementation examples")
3. WebFetch as fallback

> [Web resource access, definitive guide for getting accurate data for high quality results](./references/accessing_online_resources.md)
```

**With file path argument**:

```text
/python3-development:modernpython src/mymodule.py
→ Loads guide for reference while working on specified file
→ Use guide to manually identify and refactor legacy patterns
```

### /python3-development:shebangpython

**Purpose**: Validate correct shebang for ALL Python scripts based on their dependencies and execution context

**When to use**:

- Creating any standalone executable Python script
- Validating script shebang correctness
- Ensuring scripts have proper execution configuration

**Required for**: ALL executable Python scripts (validates shebang matches script type)

**What it validates**:

- **Stdlib-only scripts**: `#!/usr/bin/env python3` (no PEP 723 needed - nothing to declare)
- **Scripts with dependencies**: `#!/usr/bin/env -S uv --quiet run --active --script` + PEP 723 metadata declaring those dependencies
- **Package executables**: `#!/usr/bin/env python3` (dependencies via package manager)
- **Library modules**: No shebang (not directly executable)

**See**: [PEP 723 Reference](./references/PEP723.md) for details on inline script metadata

**Pattern**:

```text
/python3-development:shebangpython scripts/deploy.py
→ Analyzes imports to determine dependency type
→ **Corrects shebang** to match script type (edits file if wrong)
→ **Adds PEP 723 metadata** if external dependencies detected (edits file)
→ **Removes PEP 723 metadata** if stdlib-only (edits file)
→ Sets execute bit if needed
→ Provides detailed verification report
```

## Quality Gates

For the mandatory quality gate sequence (linting, type checking, tests, full-file review, shebang validation), activate the `/python3-development:python-cli-architect` skill.

## Standard Project Structure

For project directory layout, Hatchling configuration, and package naming rules, activate the `/python3-development:python-cli-architect` skill.

## Integration

### Reference Example (Bundled)

**Complete working example** (bundled): [python-cli-demo.py](./assets/python-cli-demo.py)

This reference implementation demonstrates all recommended patterns:

- PEP 723 metadata with correct shebang
- Typer + Rich integration
- Modern Python 3.11+ (StrEnum, Protocol, TypeVar, Generics)
- Annotated syntax for CLI params
- Async processing
- Comprehensive docstrings

This file is bundled with this plugin to keep the workflow self-contained. Use it as reference when creating CLI tools.

### Using Asset Templates

When creating new Python projects, copy standard configuration files from the skill's assets directory to ensure consistency with established conventions:

**Reason**: Templates implement proven patterns and save setup time.

**Asset Directory Location (in plugin)**: `./assets/`

**Available Templates**:

1. **version.py** - Dual-mode version management (hatch-vcs + importlib.metadata fallback)

   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/python3-development/assets/version.py" "packages/{package_name}/version.py"
   ```

2. **hatch_build.py** - Build hook for binary/asset handling (only if needed)

   ```bash
   mkdir -p scripts/
   cp "${CLAUDE_PLUGIN_ROOT}/skills/python3-development/assets/hatch_build.py" "scripts/hatch_build.py"
   ```

3. **.markdownlint.json** - Markdown linting configuration

   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/python3-development/assets/.markdownlint.json" "."
   ```

4. **.pre-commit-config.yaml** - Standard git hooks configuration

   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/python3-development/assets/example.pre-commit-config.yaml" ".pre-commit-config.yaml"

   # Install hooks using pre-commit or prek (whichever is available)
   # Both tools use the same configuration file and have identical interfaces
   uv run pre-commit install  # or: uv run prek install
   ```

5. **.editorconfig** - Editor formatting settings
   ```bash
   cp "${CLAUDE_PLUGIN_ROOT}/skills/python3-development/assets/.editorconfig" "."
   ```

These templates implement the patterns documented in [User Project Conventions](./references/user-project-conventions.md) and ensure all projects follow the same standards for version management, linting, formatting, and build configuration.

## Detailed Documentation

### Reference Documentation

**PEP 723 Specification**: [PEP 723 - Inline Script Metadata](./references/PEP723.md) - User-friendly guide to PEP 723 inline script metadata with examples and migration patterns

**Exception Handling**: [Exception Handling in Python CLI Applications with Typer](./references/exception-handling.md) - Critical guidance on preventing exception chain explosion in Typer applications with correct patterns for graceful error handling

**Typer and Rich Examples**: [Typer and Rich CLI Examples](./assets/typer_examples/index.md) - Executable examples demonstrating solutions to common problems with Rich Console text wrapping in CI/non-TTY environments and Panel/Table content wrapping

**Module Reference**: [Modern Python Modules](./references/modern-modules.md) - Comprehensive guide to 50+ modern Python libraries with deep-dive documentation for each module including usage patterns and best practices

**Tool Registry**: [Tool & Library Registry](./references/tool-library-registry.md) - Catalog of development tools, their purposes, and usage patterns for linting, testing, and build automation

**API Documentation**: [API Reference](./references/api_reference.md) - API specifications, integration guides, and programmatic interface documentation

#### Navigating Large References

To find specific modules in modern-modules.md:

```bash
grep -i "^### " references/modern-modules.md
```

To search for tools by category in tool-library-registry.md:

```bash
grep -A 5 "^## " references/tool-library-registry.md
```

To locate workflow patterns in python-development-orchestration.md:

```bash
grep -i "^## " references/python-development-orchestration.md
```

### External Commands

These skills are bundled with this plugin and available as slash commands:

- [/python3-development:modernpython](../modernpython/SKILL.md) - Python 3.11+ patterns and PEP references
- [/python3-development:shebangpython](../shebangpython/SKILL.md) - PEP 723 validation and shebang standards

## Summary

- Modern Python 3.11+ standards and patterns
- Quality gates: ruff, pyright, mypy, pytest (>80% coverage)
- Command standards: /python3-development:modernpython, /python3-development:shebangpython
- Reference documentation for 50+ modern Python modules
- Tool and library registry
