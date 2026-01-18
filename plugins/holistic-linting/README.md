# Holistic Linting

Comprehensive linting and formatting verification for code quality. Provides automatic linting workflows for orchestrators (delegate to concurrent agents) and sub-agents (lint touched files before task completion). Includes systematic resolution through root-cause analysis rather than error suppression.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install holistic-linting@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /path/to/holistic-linting
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [holistic-linting](./skills/holistic-linting/SKILL.md) | Ensures code quality through comprehensive linting and formatting. Provides automatic workflows for orchestrators and sub-agents. Prevents claiming "production ready" without verification. |
| Command | [lint](./commands/lint.md) | Run linting and formatting on files or discover project linters. Usage: /lint [path\|init] [--force] |
| Agent | [linting-root-cause-resolver](./agents/linting-root-cause-resolver.md) | Resolves linting errors by investigating root causes using linter-specific research methods (ruff rule, mypy docs, basedpyright docs). |
| Agent | [post-linting-architecture-reviewer](./agents/post-linting-architecture-reviewer.md) | Performs architectural review after linting resolution by examining artifacts and validating against codebase patterns. |

## Quick Start

**Orchestrator workflow** (delegate to agents):

```text
# After making code changes, delegate immediately without running linters
Task(agent="linting-root-cause-resolver", prompt="Format, lint, and resolve any issues in src/auth.py")

# After agent completes, delegate architectural review
Task(agent="post-linting-architecture-reviewer", prompt="Review linting resolution for src/auth.py")

# Read review report to determine if additional work needed
Read(".claude/reports/architectural-review-[timestamp].md")
```

**Sub-agent workflow** (lint before task completion):

```text
# Before marking task complete
1. Format: uv run ruff format modified_file.py
2. Lint: uv run ruff check modified_file.py && uv run mypy modified_file.py
3. Resolve issues following holistic-linting skill workflows
4. Verify: Re-run linters to confirm clean
```

**Discover project linters:**

```bash
/lint init
```

This scans configuration files (pyproject.toml, .pre-commit-config.yaml, package.json) and generates a LINTERS section in CLAUDE.md documenting all formatters and linters.

## Features

- **Automatic linting workflows** - Different behavior for orchestrators vs sub-agents
- **Systematic resolution** - Root-cause analysis using linter-specific documentation
- **Concurrent resolution** - Launch parallel agents for multiple files
- **Rules knowledge base** - Comprehensive documentation for ruff (933 rules), mypy, and bandit
- **Linter discovery** - Automatically detect and document project linters
- **Architectural review** - Post-resolution validation of fix quality

## License

MIT
