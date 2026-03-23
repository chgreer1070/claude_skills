---
name: python3-development
description: Use when building Python 3.11+ CLI apps (Typer/Rich), writing pytest test suites, fixing ruff linting or ty/mypy type errors, configuring pyproject.toml, creating portable scripts, or reviewing Python code. Activates on all Python implementation tasks — routes to specialist agents for CLI architecture, test design, packaging, and code review. Authoritative reference for modern Python 3.11-3.14 patterns and TDD workflows.
---

# Opinionated Python Development Skill

Python development guide for modern Python 3.11-3.14 patterns.

## Domain-Specific Skill Routing

### Testing

Load `/python3-development:comprehensive-test-review` when reviewing test quality or performing test audits (full checklist).

Load `/python3-development:analyze-test-failures` when analyzing failing tests or debugging test failures (balanced investigation).

Load `/python3-development:test-failure-mindset` when resetting approach to test failures (tests-as-spec mindset).

### CLI and UI libraries

Load `/python3-development:typer-and-rich` when building CLIs with Typer and Rich together (integration, width handling, examples).

Load `/python3-development:typer` when working on Typer-only CLI patterns (commands, arguments, Typer features).

Load `/python3-development:rich` when working on Rich output (tables, panels, progress, trees).

Load `/python3-development:textual` when building terminal UIs with Textual.

### Development workflows

Load `/python3-development:create-feature-task` when creating a structured feature task with tracking and phases.

Load `/python3-development:use-command-template` when creating a new Claude Code skill from the template workflow.

### Code quality

Load `/python3-development:modernpython` when applying modern Python 3.11+ patterns or modernizing legacy code (PEP-grounded).

Load `/python3-development:shebangpython` when validating shebangs or PEP 723 inline script metadata.

Load `/python3-development:stinkysnake` when running progressive quality improvement (static analysis, typing, modernization plan, TDD loop).

### Extended tool matrix

Load `/python3-development:specialist-skill-routing` when the task involves uv, Hatchling, ty, pre-commit, packaging, or other specialists not listed above (full trigger map inside that skill).

## Skill Architecture

### Bundled Resources (Included in This Skill)

**Reference Documentation:**

- [Python 3 Standards](./references/python3-standards.md) — Unified Python 3.11+ standards, knowledge graph, process graph, and how to amend them (consult when enforcing plugin-wide rules)
- [User Project Conventions](./references/user-project-conventions.md) — Conventions from production projects; consult when starting or matching an existing project style
- [Modern Python Modules](./references/modern-modules.md) - 50+ library guides with usage patterns and best practices
- [Tool & Library Registry](./references/tool-library-registry.md) - Development tools catalog for linting, testing, and build automation
- [API Reference](./references/api_reference.md) - API specifications and integration guides
- [Python Development Orchestration](./references/python-development-orchestration.md) - Detailed workflow patterns for TDD, feature addition, refactoring, and code review

**Specialist Skills** (routing commands — see **Domain-Specific Skill Routing**):

- Testing: comprehensive-test-review, analyze-test-failures, test-failure-mindset
- CLI/UI: typer-and-rich, typer, rich, textual
- Workflows: create-feature-task, use-command-template
- Quality: modernpython, shebangpython, stinkysnake
- More: specialist-skill-routing (uv, Hatchling, ty, packaging, …)

**Scripts and Assets:**

- Example scripts demonstrating patterns
- Configuration templates and boilerplate

**System Tools** (install via package manager or uv):

- `uv` - Python package and project manager (required)
- `ruff` - Linter and formatter
- `ty` - Primary static type checker (Astral); default for new work — see `/python3-development:ty`
- `mypy` - Static type checker; use when the project already configures it — do not force migration away from mypy
- `pyright` / `basedpyright` - Use when the project already standardizes on them
- `pytest` - Testing framework
- `pre-commit` - Git hook framework
- `mutmut` - Mutation testing (for critical code)
- `bandit` - Security scanner (for critical code)

**Installation Notes:**

- Use the `uv` skill for comprehensive uv documentation and package management guidance

## Core Concepts

### Python Development Standards

This skill provides modern Python 3.11+ standards, quality gates, and reference documentation for Python development.

Consult [Python 3 Standards](./references/python3-standards.md) when applying shared rules for:
- Architecture Standards (Layered architecture, Separation of concerns)
- Python Standards (Native type hints, Google-style docstrings, Fail-fast error handling)
- CLI Standards (Typer/Rich)
- Service Integration Standards (Protocol classes)
- Testing Standards (pytest-mock, 80% coverage)

### Python Development Process Graph

The following flowchart illustrates exactly where and why each skill/agent is used in the Python development lifecycle:

```mermaid
flowchart TD
    %% Define Styles
    classDef trigger fill:#e1f5fe,stroke:#3b82f6,stroke-width:2px;
    classDef plan fill:#fff3e0,stroke:#ff9800,stroke-width:2px;
    classDef implement fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    classDef verify fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px;

    %% Nodes
    Start([Feature Request / Tech Debt]) ::: trigger

    subgraph Planning Phase
        DesignSpec[python-cli-design-spec<br/>Create Architecture & Interfaces] ::: plan
        StinkySnake[stinkysnake<br/>Analyze & Plan Refactoring] ::: plan
    end

    subgraph Test-Driven Phase
        TestArch[python-pytest-architect<br/>Write Failing Tests] ::: implement
    end

    subgraph Implementation Phase
        CliArch[python-cli-architect<br/>Implement Core Logic] ::: implement
        SnakePolish[snakepolish<br/>Iterative Implement & Test Loop] ::: implement
    end

    subgraph Verification Phase
        StaticAnalysis[Ruff + type checker<br/>ty default; mypy if configured] ::: verify
        Review[code-reviewer / python3-review<br/>Holistic Quality & Pattern Check] ::: verify
    end

    Done([Ready for Merge]) ::: trigger

    %% Edges
    Start -->|New Feature| DesignSpec
    Start -->|Refactor Legacy| StinkySnake

    DesignSpec --> TestArch
    StinkySnake --> TestArch

    TestArch -->|Tests Fail| CliArch
    TestArch -->|Tests Fail| SnakePolish

    CliArch --> StaticAnalysis
    SnakePolish --> StaticAnalysis

    StaticAnalysis -->|Pass| Review
    StaticAnalysis -->|Fail| CliArch

    Review -->|Issues Found| CliArch
    Review -->|Approved| Done
```

**Reference documentation**

- [Python 3 Standards](./references/python3-standards.md) — Same as above; load when the process graph or standards need detail.

**Docstring standard** Google style (Args/Returns/Raises sections). See [User Project Conventions](./references/user-project-conventions.md) for ruff pydocstyle configuration (`convention = "google"`).

**Pyproject.toml template variables**

All `pyproject.toml` examples use explicit template variables (e.g., `{{project_name_from_directory_or_git_remote}}`) instead of generic placeholders. Replace every template variable with actual values before writing files. See [Tool & Library Registry sections 18–19](./references/tool-library-registry.md#18-pyprojecttoml-template-variable-reference) for variable reference, sourcing methods, and verification steps.

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

**Complete working example** (bundled): Load `Skill(skill="python3-development:typer-and-rich")` to access `python-cli-demo.py` — a complete CLI demo demonstrating all recommended patterns.

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

**Exception Handling and Typer/Rich Examples**: Load `Skill(skill="python3-development:typer-and-rich")` — covers exception chain prevention, Typer exit patterns, Rich non-TTY display solutions, and working executable examples including `typer_examples/` scripts and `python-cli-demo.py`.

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
- Quality gates: ruff, ty (default type check), mypy/pyright when project uses them, pytest (>80% coverage)
- Command standards: /python3-development:modernpython, /python3-development:shebangpython
- Reference documentation for 50+ modern Python modules
- Tool and library registry
