# Python3 Development Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A comprehensive Claude Code plugin providing opinionated Python development guidance, modern Python 3.11+ patterns, quality gates, and orchestration workflows for building production-ready Python applications.

## Features

- **Modern Python 3.11+ Standards**: Native type hints, PEP 723 inline metadata, structural pattern matching
- **Comprehensive Reference Library**: 50+ module guides, tool registry, mypy documentation
- **Quality Gates**: Automated linting, formatting, type checking, and test coverage requirements
- **Orchestration Workflows**: Test-driven development, feature addition, refactoring, debugging, code review
- **Configuration Templates**: Pre-configured pyproject.toml, ruff, mypy, pre-commit, and hatch setups
- **Command Templates**: Reference material for creating custom slash commands
- **Typer + Rich Integration**: CLI application patterns with proper exception handling and output formatting

## Installation

### Prerequisites

- **Claude Code**: Version 2.1+ (for skills and plugins support)
- **Python**: 3.11 or later
- **uv**: Python package and project manager (recommended)
- **Git**: For version control integration

### Install Plugin

```bash
# Method 1: Via Claude Code plugin system (if published to marketplace)
/plugin install python3-development

# Method 2: Manual installation from repository
git clone <repository-url> ~/.claude/plugins/python3-development
/plugin reload

# Method 3: Project-specific installation
git clone <repository-url> .claude/plugins/python3-development
/plugin reload
```

### External Dependencies

This plugin references external agents and commands that must be installed separately:

**Agents** (install to `~/.claude/agents/`):
- `@agent-python-cli-architect` - Python CLI development with Typer and Rich
- `@agent-python-pytest-architect` - Test suite creation and planning
- `@agent-python-code-reviewer` - Post-implementation code review
- `@agent-python-portable-script` - Standalone stdlib-only script creation

**Commands** (install to `~/.claude/commands/`):
- `/modernpython` - Python 3.11+ pattern enforcement and legacy code detection
- `/shebangpython` - PEP 723 inline script metadata validation

**System Tools** (install via package manager):
```bash
# Recommended: Install via uv
uv tool install ruff
uv tool install pytest
uv tool install pre-commit
uv tool install mypy

# Or via pip
pip install ruff pytest pre-commit mypy pyright
```

## Quick Start

### For Orchestrators (Main Claude Session)

When working on Python development tasks, the orchestrator must read the orchestration guide before delegating:

```text
# 1. Activate the skill and read orchestration guide
@python3-development

# Claude will:
# - Load Python development standards
# - Access reference documentation
# - Follow orchestration patterns for delegation

# 2. Example workflow for building a CLI tool
User: "Build a CSV processing CLI tool with progress bars"

Orchestrator:
- Reads orchestration guide first (mandatory)
- States workflow pattern: "Using FEATURE ADDITION workflow"
- Delegates to @agent-python-cli-architect for implementation
- Delegates to @agent-python-pytest-architect for tests
- Validates with quality gates
```

### For Agents (Sub-Agents)

Agents automatically receive skill guidance when delegated Python tasks:

```text
# Agent receives task from orchestrator
Task: Implement CSV processor with Typer CLI

# Agent follows skill guidance:
1. Modern Python 3.11+ patterns
2. Typer + Rich for CLI
3. Comprehensive type hints
4. Quality gates: ruff format → ruff check → pytest
5. PEP 723 metadata for scripts
```

### Direct Skill Invocation

```text
# Load skill for Python development tasks
Skill(command: "python3-development")

# Or use @ syntax
@python3-development
```

## Capabilities

| Type | Name | Description | Access |
|------|------|-------------|--------|
| **Skill** | python3-development | Comprehensive Python development orchestration and standards | Auto-activated or `@python3-development` |
| **Reference** | Modern Modules | 50+ library guides (httpx, attrs, typer, rich, prefect, etc.) | Via skill references |
| **Reference** | Tool Registry | Development tools catalog (ruff, mypy, pytest, pre-commit) | Via skill references |
| **Reference** | Mypy Docs | Type safety patterns (generics, protocols, TypedDict, narrowing) | Via skill references |
| **Reference** | Orchestration Guide | Workflow patterns (TDD, feature addition, refactoring, debugging) | Via skill references |
| **Templates** | Command Templates | Reference material for creating slash commands | `commands/` directory |
| **Templates** | Configuration Files | pyproject.toml, pre-commit, editorconfig, markdownlint | `assets/` directory |
| **Examples** | Typer Examples | Exception handling, Rich console wrapping solutions | `assets/typer_examples/` |

## Usage

### Skills

The python3-development skill provides comprehensive Python development guidance and automatically activates when working with Python projects. See [docs/skills.md](./docs/skills.md) for detailed documentation.

**Key Features**:
- Modern Python 3.11+ patterns (native generics, PEP 723, structural pattern matching)
- Orchestration workflows (TDD, feature addition, refactoring, debugging, code review)
- Quality gates (formatting, linting, type checking, testing)
- Reference documentation (50+ modules, tool registry, mypy patterns)

**Activation Triggers**:
1. Working within any Python project
2. Python script writing or editing
3. Building CI scripts or tools
4. Running Python scripts or tests
5. Writing tests for Python code
6. Python linting or pre-commit errors
7. Code review tasks

### Command Templates

The `commands/` directory contains **reference material** for creating custom slash commands, not deployed commands themselves. See [docs/commands.md](./docs/commands.md) for details on using these templates.

**Available Templates**:
- Command structure template
- Testing workflow patterns
- Development workflow patterns
- Command patterns configuration

**Note**: Actual slash commands (like `/modernpython` and `/shebangpython`) must be installed separately to `~/.claude/commands/`.

## Configuration

### Quality Gates

All Python code must pass these gates before completion:

1. **Format**: `uv run ruff format <files>`
2. **Lint**: `uv run ruff check <files>`
3. **Type Check**: `uv run mypy <files>` or `uv run pyright <files>`
4. **Test**: `uv run pytest` (>80% coverage required)

**Preferred Method** (if pre-commit configured):
```bash
# Runs all checks in correct order
uv run pre-commit run --files <files>
```

### Linting Discovery Protocol

The skill implements automatic tool detection:

1. Check for `.pre-commit-config.yaml` - use configured toolchain
2. Check CI configuration (`.gitlab-ci.yml`, `.github/workflows/`) - match CI tools
3. Fallback to `pyproject.toml` dev dependencies

This ensures local validation matches CI requirements.

### Standard Project Structure

```text
project-root/
├── pyproject.toml
├── packages/
│   └── package_name/      # Hyphens → underscores
│       ├── __init__.py
│       └── ...
├── tests/
├── scripts/
└── README.md
```

### Configuration Templates

Copy templates from skill assets to new projects:

```bash
# Version management
cp ~/.claude/skills/python3-development/assets/version.py packages/mypackage/

# Pre-commit hooks
cp ~/.claude/skills/python3-development/assets/example.pre-commit-config.yaml .pre-commit-config.yaml
uv run pre-commit install

# Editor configuration
cp ~/.claude/skills/python3-development/assets/.editorconfig .
cp ~/.claude/skills/python3-development/assets/.markdownlint.json .
```

## Examples

### Example 1: Building a CLI Tool

**Scenario**: Create a CSV processing tool with progress bars and error handling

**Orchestrator Workflow**:
```text
1. Read orchestration guide (mandatory)
   Read("~/.claude/skills/python3-development/references/python-development-orchestration.md")

2. State workflow pattern
   "Using FEATURE ADDITION workflow with agents:
    @agent-python-cli-architect → @agent-python-pytest-architect → @agent-python-code-reviewer"

3. Delegate implementation (focused scope)
   Task(
     agent="agent-python-cli-architect",
     prompt="Create CSV processor with Typer CLI and Rich progress bars.
             Scope: packages/csv_tool/processor.py only.
             Success criteria: Process CSV files with progress indication."
   )

4. Delegate testing (focused scope)
   Task(
     agent="agent-python-pytest-architect",
     prompt="Create test suite for CSV processor.
             Scope: tests/test_processor.py only.
             Success criteria: >80% coverage, test edge cases."
   )

5. Validate quality gates
   - Run: uv run pre-commit run --files packages/csv_tool/processor.py tests/test_processor.py
   - Verify: All checks pass (format, lint, type check)
   - Test: uv run pytest --cov

6. Code review
   Task(
     agent="agent-python-code-reviewer",
     prompt="Review CSV processor implementation for patterns and quality."
   )
```

**Result**: Production-ready CLI tool following all standards

---

### Example 2: Type-Safe Data Structures

**Scenario**: Create type-safe configuration loader with validation

**Code**:
```python
from typing import TypedDict
from pathlib import Path
import tomllib

class DatabaseConfig(TypedDict):
    host: str
    port: int
    name: str

class AppConfig(TypedDict):
    database: DatabaseConfig
    debug: bool

def load_config(path: Path) -> AppConfig:
    """Load and validate application configuration.

    Args:
        path: Path to TOML configuration file

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If configuration file doesn't exist
    """
    with path.open("rb") as f:
        data = tomllib.load(f)

    # Type narrowing with validation
    if not isinstance(data.get("database"), dict):
        raise ValueError("Missing or invalid database configuration")

    config: AppConfig = {
        "database": {
            "host": data["database"]["host"],
            "port": int(data["database"]["port"]),
            "name": data["database"]["name"],
        },
        "debug": bool(data.get("debug", False)),
    }

    return config
```

**Benefits**:
- Type-safe dictionary access (mypy validates keys and value types)
- Clear structure documentation via TypedDict
- Explicit validation with meaningful errors

---

### Example 3: Fixing Linting Errors

**Scenario**: Resolve ruff and mypy errors in existing code

**Workflow**:
```bash
# 1. Discover project tooling (automatic via skill)
test -f .pre-commit-config.yaml && echo "Using pre-commit"

# 2. Format first (fixes many issues automatically)
uv run ruff format packages/

# 3. Lint and fix auto-fixable issues
uv run ruff check --fix packages/

# 4. Fix remaining issues manually
uv run ruff check packages/
# Review output, fix issues at root cause

# 5. Type check
uv run mypy packages/
# Fix type errors with proper annotations

# 6. Verify all quality gates pass
uv run pre-commit run --all-files
```

**Linting Exception Conditions** (from CLAUDE.md):
Only ignore linting errors for:
1. Vendored code (third-party code copied without modification)
2. Educational examples of incorrect code
3. Code pinned to Python <3.11 for compatibility
4. Python derivative implementations (CircuitPython, MicroPython)

**Never suppress** without user approval: BLE001 (blind-except), D103 (missing-docstring), TRY300 (try-consider-else)

---

### Example 4: PEP 723 Inline Script Metadata

**Scenario**: Create standalone Python script with external dependencies

**Before** (requires manual dependency management):
```python
#!/usr/bin/env python3
# User must: pip install typer rich

import typer
from rich.console import Console

def main():
    console = Console()
    console.print("[green]Hello World![/green]")

if __name__ == "__main__":
    typer.run(main)
```

**After** (self-contained with PEP 723):
```python
#!/usr/bin/env -S uv --quiet run --active --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.9.0",
#     "rich>=13.0.0",
# ]
# ///

import typer
from rich.console import Console

def main():
    console = Console()
    console.print("[green]Hello World![/green]")

if __name__ == "__main__":
    typer.run(main)
```

**Benefits**:
- Single file contains all dependency information
- `uv` automatically installs dependencies on first run
- No manual environment setup required
- Script remains portable and self-documenting

**Validation**:
```bash
/shebangpython scripts/hello.py
# Validates shebang matches dependencies
# Adds/removes PEP 723 metadata as needed
```

## Troubleshooting

### Skill Not Activating

**Problem**: Skill doesn't load when working on Python code

**Solution**:
1. Verify installation: `/plugin list`
2. Check skill location: `ls ~/.claude/plugins/python3-development/skills/`
3. Reload plugins: `/plugin reload`
4. Manually activate: `@python3-development`

### Quality Gates Failing

**Problem**: Linting or type checking errors block progress

**Solution**:
1. Follow format-first workflow: `ruff format` before `ruff check`
2. Check project tooling: Read `.pre-commit-config.yaml` for configured tools
3. Review exception conditions: Only suppress errors for valid reasons (see CLAUDE.md)
4. Fix at root cause: Don't add `# noqa` or `# type: ignore` without understanding why

### Agent Context Exhaustion

**Problem**: Agent runs out of context during complex tasks

**Solution**:
1. **Read orchestration guide first** (mandatory): `Read("~/.claude/skills/python3-development/references/python-development-orchestration.md")`
2. Break task into focused delegations: One agent per concern (implement → test → review)
3. Provide bounded scope: "Scope: packages/module.py only"
4. Set clear success criteria: "Success: >80% coverage, all tests pass"
5. Use agent chaining: Multiple focused agents instead of one agent doing everything

### External Dependencies Missing

**Problem**: Plugin references agents or commands that don't exist

**Solution**:
1. Agents must be installed separately to `~/.claude/agents/`
2. Commands must be installed separately to `~/.claude/commands/`
3. System tools must be installed: `uv tool install ruff pytest mypy`
4. The plugin provides orchestration guidance; agents perform implementation

### Typer Exception Chains

**Problem**: Typer CLI shows nested exception traces

**Solution**: See `assets/nested-typer-exceptions/` for correct exception handling patterns:
- Use `raise SystemExit(1)` instead of `raise typer.Exit(1)` in nested functions
- Use Rich Console for output instead of Typer echo
- Never raise Typer exceptions from within try/except blocks

## Contributing

Contributions are welcome! Please ensure:

1. All Python code passes quality gates (ruff format, ruff check, mypy, pytest)
2. New modules added to `references/modern-modules/` follow template structure
3. Command templates in `commands/` are reference material (not deployed commands)
4. Documentation uses markdown links for file references: `[text](./path/to/file.md)`
5. Code examples use Python 3.11+ patterns (no legacy typing syntax)

## License

MIT License - See LICENSE file for details

## Credits

**Author**: [Author information from plugin.json]

**References**:
- Python Enhancement Proposals (PEPs): 585, 604, 695, 723
- Mypy documentation: Types, generics, protocols, type narrowing
- Ruff documentation: Linting and formatting standards
- Typer and Rich documentation: CLI application patterns
