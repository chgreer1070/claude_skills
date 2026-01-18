# Holistic Linting Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Comprehensive code quality enforcement through systematic linting workflows for Python projects. Prevents claiming "production ready" code without verification by embedding format-lint-resolve cycles into Claude's development workflow.

## Features

- **Automatic Quality Gates** - Ensures formatting and linting before task completion
- **Root Cause Resolution** - Investigates linting errors systematically instead of suppressing symptoms
- **Orchestrator-Agent Workflow** - Separates task delegation from execution for clean context management
- **Linting Rules Knowledge Base** - 933+ documented rules for Ruff, MyPy, and Bandit
- **Project Configuration Discovery** - Scans and documents project linters in CLAUDE.md
- **Concurrent Resolution** - Parallel agents for multi-file linting tasks
- **Architectural Review** - Post-resolution validation of design implications
- **Python 3.11+ Integration** - Coordinates with python3-development skill for modern patterns

## Installation

### Prerequisites

- Claude Code 2.1+
- Python 3.11+ projects with linting tools (ruff, mypy, pyright, bandit)
- UV or similar Python package manager

### Install Plugin

```bash
# Method 1: Using cc plugin install (when published to marketplace)
cc plugin install holistic-linting

# Method 2: Manual installation
git clone <repository-url> ~/.claude/plugins/holistic-linting
cc plugin reload
```

## Quick Start

### Step 1: Discover Project Linters

```bash
/lint init
```

This scans your project for linting configuration and generates the `## LINTERS` section in `CLAUDE.md`.

### Step 2: Let Claude Enforce Quality Automatically

When Claude Code completes implementation work, the holistic-linting skill automatically:

1. **Orchestrators** - Delegate to linting-root-cause-resolver agent for formatting, linting, and resolution
2. **Sub-Agents** - Format and lint touched files before completing tasks

No manual intervention required - quality enforcement is embedded in the workflow.

### Step 3: Manual Linting (Optional)

```bash
/lint path/to/file.py              # Lint specific file
/lint src/                         # Lint directory
/lint file1.py file2.py file3.py   # Lint multiple files
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | holistic-linting | Automatic linting workflow guidance for orchestrators and sub-agents | Auto-activated |
| Command | /lint | Manual linting invocation and project linter discovery | `/lint [path\|init]` |
| Agent | linting-root-cause-resolver | Systematic investigation and resolution of linting errors | Auto-delegated |
| Agent | post-linting-architecture-reviewer | Architectural validation after linting resolution | Auto-delegated |

## Usage

### Skills

The holistic-linting skill provides different behaviors based on Claude's role:

- **Orchestrators** - Delegate immediately to linting agents without running linters themselves
- **Sub-Agents** - Format and lint touched files before task completion

See [Skills Reference](./docs/skills.md) for detailed activation patterns and workflows.

### Commands

The `/lint` command provides manual control:

- `/lint init` - Discover and document project linters in CLAUDE.md
- `/lint <path>` - Format, lint, and resolve issues in specified files

See [Commands Reference](./docs/commands.md) for complete usage.

### Agents

Two specialized agents handle systematic resolution:

- **linting-root-cause-resolver** - Researches rules, traces code flow, implements elegant fixes
- **post-linting-architecture-reviewer** - Validates resolution quality and architectural implications

See [Agents Reference](./docs/agents.md) for delegation patterns and output artifacts.

## Configuration

### Project Setup

Create `## LINTERS` section in your project's `CLAUDE.md`:

```bash
/lint init
```

This generates configuration like:

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

See [Configuration Reference](./docs/configuration.md) for advanced setup.

## Examples

### Example 1: Automatic Linting During Development

```text
User: "Add JWT authentication to the API"

Claude (Orchestrator):
1. [Implements JWT middleware in auth.py]
2. [Holistic-linting skill activates automatically]
3. Delegates: Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in auth.py")
4. [Agent formats, lints, resolves 5 issues at root cause]
5. [Agent produces resolution report]
6. [Orchestrator reads report confirming clean resolution]
7. "JWT authentication implemented and verified ✓"
```

### Example 2: Manual Linting Multiple Files

```bash
/lint src/auth.py src/models.py tests/test_auth.py
```

Output:
- Formats all 3 files
- Runs ruff, mypy, pyright on each
- Launches concurrent resolution agents for files with errors
- Verifies all issues resolved

### Example 3: Discovering Project Linters

```bash
/lint init
```

Output:
- Scans `.pre-commit-config.yaml`, `pyproject.toml`, `package.json`
- Identifies 6 formatters and 5 linters
- Appends structured configuration to `CLAUDE.md`

See [Usage Examples](./docs/examples.md) for more workflows.

## Troubleshooting

### "I don't know which linters this project uses"

**Solution**: Run `/lint init` to scan and document project linters in `CLAUDE.md`.

### "Linting errors but I don't understand the rule"

**Solution**: The linting-root-cause-resolver agent automatically researches rules using:
- `ruff rule {CODE}` for Ruff issues
- Local mypy documentation cache for MyPy errors
- Basedpyright online docs for Pyright issues

### "Multiple files with linting errors"

**Solution**: The skill launches concurrent linting-root-cause-resolver agents (one per file) automatically.

### "Linter not found (command not available)"

**Solution**: Check linter installation. Use `uv run <tool>` for Python tools to ensure virtual environment activation.

### "False positive linting error"

**Solution**: Configure the rule in `pyproject.toml` rather than using `# noqa` or `# type: ignore` comments.

## Contributing

Contributions welcome! Please:

1. Follow the existing skill/command/agent structure
2. Add reference documentation for new linter rules
3. Update SKILL.md with workflow changes
4. Test with real projects before submitting

## Credits

Created for systematic code quality enforcement in Claude Code workflows.

## Related Documentation

- [Skills Reference](./docs/skills.md) - Detailed skill behavior and activation
- [Commands Reference](./docs/commands.md) - Complete /lint command documentation
- [Agents Reference](./docs/agents.md) - Agent delegation patterns and artifacts
- [Configuration](./docs/configuration.md) - Setup and customization
- [Examples](./docs/examples.md) - Real-world usage workflows
