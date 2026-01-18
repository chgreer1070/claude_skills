# Skills Reference

This plugin provides one comprehensive skill for Python development orchestration and standards.

## python3-development

**Location**: `skills/python3-development/SKILL.md`

**Version**: 1.2.0

**Last Updated**: 2026-01-14

**Python Compatibility**: 3.11+

**Description**: Comprehensive orchestration guide for Python development using specialized agents and modern Python 3.11-3.14 patterns. Provides workflow patterns for test-driven development, feature addition, refactoring, debugging, and code review.

**User Invocable**: Yes (default)

**Model**: Inherits from session

**Context**: Inline (default)

### When to Use

The skill automatically activates when:

1. Working within any Python project
2. Python CLI applications with Typer and Rich are mentioned
3. Tasked with Python script writing or editing
4. Building CI scripts or tools
5. Creating portable Python scripts with stdlib only
6. Planning out a Python package design
7. Running any Python script or test
8. Writing tests (unit, integration, e2e, validation) for Python code
9. Reviewing Python code against best practices or for code smells
10. Python command fails to run or errors
11. Pre-commit or linting errors occur in Python files
12. Writing or editing Python code in a git repository

### Activation

**Automatic**: Claude activates this skill when working on Python development tasks

**Manual**:
```text
@python3-development
```

**Programmatic**:
```text
Skill(command: "python3-development")
```

### What This Skill Provides

#### For Orchestrators (Main Claude Session)

**Orchestration Patterns**:
- Test-Driven Development (TDD) workflow
- Feature addition workflow
- Refactoring workflow
- Debugging workflow
- Code review workflow

**Pre-Delegation Protocol** (MANDATORY):
1. Read orchestration guide BEFORE any delegation
2. Identify workflow pattern (TDD, feature addition, refactoring, etc.)
3. Plan agent chain (never single-agent for complex tasks)
4. Define scope boundaries for each agent
5. Set measurable success criteria

**Agent Selection Guidance**:
| Task Type | Agent |
|-----------|-------|
| Python CLI implementation | `@agent-python-cli-architect` |
| Test suite creation | `@agent-python-pytest-architect` |
| Code review | `@agent-python-code-reviewer` |
| Stdlib-only scripts | `@agent-python-portable-script` |
| Architecture design | `@agent-spec-architect` |
| Task breakdown | `@agent-spec-planner` |
| Requirements gathering | `@agent-spec-analyst` |

**Key Principle**: Orchestrators coordinate workflows and delegate to specialized agents rather than implementing code directly.

#### For All Roles (Orchestrators and Agents)

**Modern Python Standards**:
- Python 3.11+ native type hints (no `typing.List`, `typing.Dict`)
- PEP 723 inline script metadata for executable scripts
- Structural pattern matching (`match/case`)
- Native generics syntax (Python 3.12+)
- Type safety with mypy comprehensive patterns

**Quality Gates**:
1. Format: `ruff format` (always first)
2. Lint: `ruff check` (after formatting)
3. Type Check: `mypy` or `pyright` (detect which project uses)
4. Test: `pytest` with >80% coverage (>95% for critical code)

**Reference Documentation**:
- 50+ modern Python module guides
- Tool and library registry
- Mypy type patterns (generics, protocols, TypedDict, narrowing)
- API specifications
- Exception handling patterns
- Working configurations (pyproject.toml, ruff, mypy, pytest)

**Configuration Templates**:
- `version.py` - Dual-mode version management
- `.pre-commit-config.yaml` - Git hooks configuration
- `.editorconfig` - Editor formatting settings
- `.markdownlint.json` - Markdown linting rules
- `hatch_build.py` - Build hook for binary/asset handling

### Key Concepts

#### Linting Discovery Protocol

The skill implements automatic tool detection to ensure local validation matches CI requirements:

1. **Check for pre-commit**: If `.pre-commit-config.yaml` exists, use configured toolchain
2. **Check CI config**: Read `.gitlab-ci.yml` or `.github/workflows/` for required tools
3. **Fallback to pyproject.toml**: Use dev dependencies if no CI config found

**Tool Detection**: Automatically detects whether project uses `pre-commit` or `prek` (Rust-based replacement)

#### Format-First Workflow

**Rule**: Always format before linting

**Reason**: Formatting automatically fixes many linting issues (whitespace, line length, quotes)

**Sequence**:
```bash
1. uv run ruff format <files>  # Fix formatting
2. uv run ruff check <files>   # Lint after formatting
3. uv run mypy <files>         # Type check
4. uv run pytest               # Test
```

#### Type Safety Requirements

**Requirement**: All Python code MUST be comprehensively typed using Python 3.11+ native type hints

**Mypy Patterns Available**:
- Generics (TypeVar, Generic, native syntax)
- Protocols (structural subtyping)
- TypedDict (typed dictionaries)
- Type narrowing (isinstance, type guards, TypeIs)
- Additional features (attrs, dataclasses, Self type)

**Decision Matrix**:
| Use Case | Pattern |
|----------|---------|
| Type-safe container classes | Generics |
| Duck typing with type safety | Protocols |
| Fixed-schema dictionaries | TypedDict |
| Union type refinement | Type narrowing |
| Data classes | attrs (default), dataclasses (stdlib-only), pydantic (external data only) |

#### Rich Console Integration

**Emoji Usage**: Always use Rich emoji tokens, never literal Unicode:
```python
# Correct
console.print(":white_check_mark: Task completed")

# Incorrect
console.print("✅ Task completed")
```

**Width Handling**: Use `get_rendered_width()` helper for Panel and Table:
```python
panel = Panel(long_content)
panel_width = get_rendered_width(panel)
console.width = panel_width
console.print(panel, crop=False, overflow="ignore")
```

See `assets/typer_examples/` for complete working examples.

#### Exception Handling

**Principle**: Catch exceptions only when you have a specific recovery action

**Pattern**:
```python
# Good - specific recovery action
try:
    return db.query(User, id)
except ConnectionError:
    logger.warning("DB unavailable, using cache")
    return cache.get(f"user:{id}")

# Bad - no recovery action, just re-raising
try:
    return db.query(User, id)
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

**Typer Exception Chains**: See `assets/nested-typer-exceptions/` for correct exception handling in CLI applications.

#### Script Dependency Trade-offs

**Default Recommendation**: Use Typer + Rich with PEP 723 unless portability prevents network access

**Scripts with Dependencies** (PEP 723):
- Benefits: Less complexity, better UX, well-tested libraries
- Trade-off: Requires network on first run

**Stdlib-only Scripts**:
- Benefits: Maximum portability, no network required
- Trade-offs: More complexity, more code, basic UX

### Reference Files

The skill includes extensive reference documentation in the `references/` subdirectory:

**Core Documentation**:
- `python-development-orchestration.md` - Detailed workflow patterns (MANDATORY reading for orchestrators)
- `user-project-conventions.md` - Extracted conventions from production projects
- `modern-modules.md` - 50+ library guides with usage patterns
- `tool-library-registry.md` - Development tools catalog
- `api_reference.md` - API specifications and integration guides

**Specialized Guides**:
- `PEP723.md` - Inline script metadata specification
- `exception-handling.md` - Exception patterns for CLI applications

**Mypy Documentation** (`references/mypy-docs/`):
- `generics.rst` - Generic types and type variables
- `protocols.rst` - Structural subtyping
- `typed_dict.rst` - TypedDict patterns
- `type_narrowing.rst` - Type refinement techniques
- `additional_features.rst` - attrs, dataclasses, Self type

**Module-Specific Guides** (`references/modern-modules/`):
- `httpx.md` - Modern HTTP client
- `typer.md` - CLI framework
- `rich.md` - Terminal output formatting
- `attrs.md` - Data classes
- `pytest.md` - Testing framework
- 12+ additional module guides

**Usage Examples** (`assets/`):
- `typer_examples/console_no_wrap_example.py` - Plain text wrapping solutions
- `typer_examples/console_containers_no_wrap.py` - Panel/Table width handling
- `nested-typer-exceptions/` - Exception handling patterns
- Configuration templates (`.editorconfig`, `.markdownlint.json`, etc.)

### External Dependencies

This skill provides orchestration guidance. Implementation requires external agents and commands:

**Required Agents** (install separately to `~/.claude/agents/`):
- `@agent-python-cli-architect`
- `@agent-python-pytest-architect`
- `@agent-python-code-reviewer`
- `@agent-python-portable-script`
- `@agent-spec-architect`
- `@agent-spec-planner`
- `@agent-spec-analyst`

**Required Commands** (install separately to `~/.claude/commands/`):
- `/modernpython` - Python 3.11+ pattern enforcement
- `/shebangpython` - PEP 723 validation

**System Tools** (install via package manager):
- `uv` - Python package manager (required)
- `ruff` - Linter and formatter
- `mypy` or `pyright` - Type checker
- `pytest` - Testing framework
- `pre-commit` or `prek` - Git hook framework

### Orchestration Example

**Workflow**: Building a CLI tool with TDD approach

```text
# Orchestrator reads guide (MANDATORY first step)
Read("~/.claude/skills/python3-development/references/python-development-orchestration.md")

# State workflow pattern
"I have read the orchestration guide. Using TDD workflow with agents:
 @agent-python-pytest-architect → @agent-python-cli-architect → @agent-python-code-reviewer"

# Step 1: Design tests first (focused scope)
Task(
  agent="agent-python-pytest-architect",
  prompt="Design test suite for CSV processor CLI.
          Scope: tests/test_csv_processor.py only.
          Success criteria: Comprehensive test cases covering edge cases."
)

# Step 2: Implement to pass tests (focused scope)
Task(
  agent="agent-python-cli-architect",
  prompt="Implement CSV processor to pass test suite.
          Scope: packages/csv_tool/processor.py only.
          Success criteria: All tests pass, >80% coverage."
)

# Step 3: Validate quality gates
- uv run ruff format packages/ tests/
- uv run ruff check packages/ tests/
- uv run mypy packages/
- uv run pytest --cov

# Step 4: Code review (focused scope)
Task(
  agent="agent-python-code-reviewer",
  prompt="Review CSV processor implementation for patterns and quality."
)
```

**Notice**:
- Orchestrator reads guide FIRST (mandatory)
- States workflow pattern explicitly
- Each delegation has focused scope
- Clear success criteria for each step
- Quality gates validated between steps

### Linting Exception Conditions

The skill enforces strict linting standards with explicit exception conditions.

**Acceptable Exceptions** (OK to ignore linting):
1. Vendored code (third-party code copied without modification)
2. Examples of what-not-to-do (intentionally incorrect for education)
3. Code pinned to historic Python version (<3.11)
4. Code for Python derivatives (CircuitPython, MicroPython)

**Unacceptable** (MUST fix or escalate):
- Any code that doesn't fall into the above categories
- Never add `# type: ignore` or `# noqa` without explicit user approval

**Rule Codes That MUST Always Be Fixed** (never suppress):
- BLE001 (blind-except) - Replace generic exceptions with specific types
- D103 (missing-docstring) - Add docstrings to public functions
- TRY300 (try-consider-else) - Restructure try/except/else properly

**Per-File Exceptions** (acceptable in pyproject.toml):
- Scripts: T201 (print), S (security), DOC, ANN401, PLR*
- Tests: S, D, E501, ANN, DOC, PLC, SLF, PLR, EXE, N, T
- Assets: PLC0415, DOC
- Typings: N, ANN, A

### Standard Project Structure

All Python projects follow this layout:

```text
project-root/
├── pyproject.toml
├── packages/
│   └── package_name/      # Hyphens in project name → underscores
│       ├── __init__.py
│       ├── version.py
│       └── ...
├── tests/
├── scripts/
├── sessions/              # Optional: cc-sessions framework
└── README.md
```

**Hatchling Configuration**:
```toml
[tool.hatchling.build.targets.wheel]
packages = ["packages/package_name"]
```

### Integration Points

**With Other Skills**:
- `uv` skill - Comprehensive uv package manager documentation
- `holistic-linting` skill - Project-wide linting and quality checks

**With External Agents**:
- Agents receive skill guidance automatically when delegated
- Agents follow same quality gates and standards
- Agents implement; orchestrator coordinates

**With Commands**:
- `/modernpython` - Reference guide for Python 3.11+ patterns
- `/shebangpython` - Validate and correct script shebangs

## Summary

The python3-development skill provides:

**For Orchestrators**:
1. Comprehensive orchestration guide (MUST read before delegating)
2. Agent selection criteria and decision trees
3. Workflow patterns (TDD, feature addition, refactoring, debugging, code review)
4. Pre-delegation protocol (mandatory checklist)
5. Multi-agent chaining patterns

**For All Roles**:
1. Modern Python 3.11+ standards and patterns
2. Quality gates (format, lint, type check, test)
3. Reference documentation (50+ modules, mypy patterns, tool registry)
4. Configuration templates
5. Linting discovery protocol
6. Exception handling patterns
7. Rich console integration
