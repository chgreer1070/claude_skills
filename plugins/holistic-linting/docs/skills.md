# Skills Reference

The holistic-linting plugin provides one comprehensive skill that modifies Claude's development workflow to include automatic quality enforcement.

---

## holistic-linting

**Location**: `skills/holistic-linting/SKILL.md`

**Description**: Ensures code quality through comprehensive linting and formatting. Provides automatic linting workflows for orchestrators (format → lint → resolve via concurrent agents) and sub-agents (lint touched files before task completion). Prevents claiming "production ready" code without verification.

**User Invocable**: Yes (auto-activated)

**Model**: Inherits from session

**Context**: Inline (not forked)

---

## When to Use

This skill applies to **all code editing tasks** in projects with linting configuration. Claude automatically activates it when:

- Completing Python implementation work
- Editing files in projects with `.pre-commit-config.yaml` or `pyproject.toml`
- Creating or modifying Python modules
- Refactoring existing code

No manual activation required - the skill embeds quality checks into Claude's natural workflow.

---

## Activation

### Automatic Activation

Claude activates this skill automatically based on context:

```text
[User requests Python implementation]
  → [Claude detects linting configuration in project]
  → [holistic-linting skill auto-activates]
  → [Workflow includes format-lint-resolve steps]
```

### Manual Activation

Force skill activation in a session:

```text
Skill(command: "holistic-linting")
```

---

## Behavior by Role

The skill provides different guidance based on whether Claude is an orchestrator or a sub-agent.

### For Orchestrators (Interactive Claude Code CLI)

**Philosophy**: Orchestrators delegate work. They do NOT run formatters or linters themselves.

**Workflow**:

1. Complete implementation work
2. **Delegate immediately** to linting-root-cause-resolver agent
3. Wait for agent to format, lint, and resolve issues
4. Read resolution reports from `.claude/reports/`
5. Optionally delegate to post-linting-architecture-reviewer for validation
6. Mark task complete only after reports confirm clean resolution

**What Orchestrators Do**:
- ✅ Delegate to linting agents with file paths
- ✅ Read resolution artifacts and reports
- ✅ Launch concurrent agents for multiple files
- ✅ Trust agent verification results

**What Orchestrators Do NOT Do**:
- ❌ Run `ruff format` before delegating
- ❌ Run `ruff check` or `mypy` to gather error messages
- ❌ Pre-gather linting data for agents
- ❌ Verify agent work by re-running linters

**Delegation Pattern**:

```text
Task(
  agent="linting-root-cause-resolver",
  prompt="Format, lint, and resolve any issues in <file_path>"
)
```

### For Sub-Agents (Task-Delegated Agents)

**Philosophy**: Sub-agents execute work directly. They format and lint their own changes.

**Workflow**:

1. Complete implementation work (Edit/Write operations)
2. **Format touched files** using project formatters
3. **Lint touched files** using project linters
4. **Resolve issues directly** by researching rules and implementing fixes
5. **Verify resolution** by re-running linters
6. Mark task complete only when linters report clean

**What Sub-Agents Do**:
- ✅ Run formatters on files they modified
- ✅ Run linters on files they modified
- ✅ Research linting rules using tool-specific methods
- ✅ Implement root-cause fixes following python3-development skill
- ✅ Re-run linters to verify resolution

**Execution Pattern**:

```bash
# Format first (auto-fixes trivial issues)
uv run ruff format touched_file.py

# Lint second (reports substantive issues)
uv run ruff check touched_file.py
uv run mypy touched_file.py

# Resolve issues...

# Verify
uv run ruff check touched_file.py  # Must be clean
uv run mypy touched_file.py        # Must be clean
```

---

## Linter-Specific Resolution Workflows

The skill documents systematic resolution procedures for each major linting tool:

### Ruff Resolution Workflow

**Trigger**: Ruff rule codes (E, F, W, B, S, I, UP, C90, N, etc.)

**Process**:
1. Research rule: `ruff rule {RULE_CODE}`
2. Read affected code
3. Check architectural context
4. Load python3-development skill
5. Implement elegant fix
6. Verify: `ruff check <file>`

### MyPy Resolution Workflow

**Trigger**: MyPy error codes (attr-defined, arg-type, return-value, etc.)

**Process**:
1. Research error code in local mypy documentation cache
2. Trace type flow through code
3. Check architectural context
4. Load python3-development skill
5. Fix annotation or implementation
6. Verify: `mypy <file>`

### Pyright/Basedpyright Resolution Workflow

**Trigger**: Pyright diagnostic rules (reportGeneralTypeIssues, reportOptionalMemberAccess, etc.)

**Process**:
1. Research rule using MCP Ref tool or basedpyright docs
2. Read affected code and understand type inference
3. Check architectural context
4. Load python3-development skill
5. Add type narrowing, annotations, or guards
6. Verify: `pyright <file>` or `basedpyright <file>`

---

## Integration with python3-development Skill

All resolution workflows integrate with the python3-development skill at the implementation stage. This ensures:

- Modern Python 3.11+ syntax (native generics, `|` union syntax)
- Idiomatic code patterns (comprehensions, exceptions, naming)
- Complete and accurate type annotations
- Consistency with project conventions

**Activation Pattern**:

```text
[Identify linting issue]
  → [Research rule documentation]
  → [Read code and architecture]
  → [Load python3-development skill]
  → [Implement elegant fix]
  → [Verify with linter]
```

---

## Reference Documentation

The skill includes extensive reference documentation for linting rules:

### Ruff Rules (933+ documented)

**Location**: `skills/holistic-linting/references/rules/ruff/`

**Coverage**:
- Pycodestyle (E/W) - Style and whitespace
- Pyflakes (F) - Logical errors
- Bugbear (B) - Common bugs
- Bandit (S) - Security issues
- Import sorting (I)
- Pyupgrade (UP) - Modern Python patterns
- 13+ additional rule families

Each rule documents:
- Design principle it enforces
- Violation conditions and examples
- Valid usage patterns
- Configuration options

### MyPy Error Codes

**Location**: `skills/holistic-linting/references/rules/mypy/`

**Coverage**:
- Attribute access errors
- Name resolution errors
- Function call type checking
- Assignment compatibility
- Collection type checking
- Operator usage
- Import resolution
- Abstract class enforcement

Each error code documents:
- Type safety principle
- When it's an error vs. valid pattern
- Code examples (error and corrected)
- Configuration options

### Bandit Security Checks (65+ documented)

**Location**: `skills/holistic-linting/references/rules/bandit/`

**Coverage**:
- Credentials and secrets
- Cryptography weaknesses
- SSL/TLS vulnerabilities
- Injection attacks
- Deserialization risks
- File permissions
- Unsafe functions

Each check documents:
- Security vulnerability it prevents
- Insecure patterns and secure alternatives
- Severity level (LOW, MEDIUM, HIGH)

---

## Project Configuration

The skill reads project linting configuration from the `## LINTERS` section in `CLAUDE.md`.

**Expected Format**:

```markdown
## LINTERS

git pre-commit hooks: enabled
pre-commit tool: pre-commit

### Formatters

- ruff format [*.py]
- prettier [*.{ts,tsx,json,md}]

### Static Checking and Linting

- ruff check [*.py]
- mypy [*.py]
- pyright [*.py]
```

**Generation**:

Use the `/lint init` command to automatically scan and document project linters.

---

## Scripts

The skill includes helper scripts in `skills/holistic-linting/scripts/`:

| Script | Purpose |
|--------|---------|
| `detect-hook-tool.py` | Detects whether project uses pre-commit or prek |
| `discover-linters.py` | Scans project for linting configuration |
| `install-agents.py` | Installs linting agents to user or project scope |
| `lint-orchestrator.py` | Runs project linters based on CLAUDE.md config |

---

## Hooks

The skill does not include hook configurations. For automatic PostToolUse linting, use the separate [claude-linting-hook](https://github.com/yourrepo/claude-linting-hook) plugin.

---

## Best Practices

### For Orchestrators

1. **Delegate immediately** - Don't run formatters or linters before delegating
2. **Trust agent verification** - Read reports instead of re-running linters
3. **Launch concurrent agents** - One agent per file for parallel resolution
4. **Read CLAUDE.md first** - Check `## LINTERS` section for project configuration

### For Sub-Agents

1. **Format before linting** - Auto-fix trivial issues first
2. **Research rules thoroughly** - Use tool-specific documentation methods
3. **Never suppress without understanding** - No `# noqa` or `# type: ignore` without root cause analysis
4. **Verify after fixes** - Always re-run linters to confirm resolution
5. **Load python3-development skill** - Ensure modern Python patterns

### For All Roles

1. **Read CLAUDE.md LINTERS section first** - Don't assume which linters are available
2. **Use scoped operations** - Lint only touched files, not `--all-files`
3. **Reference rules knowledge base** - Use documented patterns for investigation
4. **Document patterns discovered** - Add to `.claude/knowledge/` for reuse

---

## Common Anti-Patterns

### ❌ Orchestrator Pre-Gathering Linting Data

```text
# Don't do this:
Bash("ruff check src/auth.py")
# Read the output...
# Then delegate with the output
Task(agent="linting-root-cause-resolver", prompt="Fix these errors: [pasted errors]")
```

**Problem**: Wastes orchestrator context window, duplicates agent work, creates stale context.

### ✅ Correct: Delegate Immediately

```text
# Do this instead:
Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in src/auth.py")
```

### ❌ Suppressing Errors Without Investigation

```python
# Don't do this:
result = value.upper()  # type: ignore
```

**Problem**: Silences symptom instead of fixing root cause.

### ✅ Correct: Add Type Narrowing

```python
# Do this instead:
if value is None:
    raise ValueError("value cannot be None")
result = value.upper()  # Type checker knows value is str
```

---

## Related Skills

- **python3-development** - Modern Python patterns (Python 3.11+ syntax, typing, idioms)
- **uv** - Python package and project management

---

[← Back to README](../README.md)
