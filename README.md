# Custom Claude Skills

[![Lint and Test](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/lint-and-test.yml/badge.svg)](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/lint-and-test.yml)
[![Security Scanning](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/security.yml/badge.svg)](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/security.yml)
[![Documentation Quality](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/docs.yml/badge.svg)](https://github.com/Jamie-BitFlight/claude_skills/actions/workflows/docs.yml)

This repository contains custom Agent Skills for Claude - modular packages that extend Claude's capabilities with specialized knowledge, workflows, and tools.

## Skills in This Repository

This collection provides **22 specialized skills** for development workflows:

### Development & Build Tools

- **python3-development** - Opinionated Python development workflow and best practices
- **uv** - Expert guidance for Astral's uv Python package and project manager
- **clang-format** - C/C++ code formatting with clang-format
- **hatchling** - Python build system guidance
- **pypi-readme-creator** - Create polished PyPI README files

### Code Quality & Linting

- **holistic-linting** - Multi-tool linting orchestration
- **pre-commit** - Pre-commit hook guidance and configuration
- **commitlint** - Commit message linting
- **conventional-commits** - Conventional commit format guidance

### Documentation

- **mkdocs** - MkDocs documentation site generator
- **pypi-readme-creator** - PyPI README creation and optimization

### AI & LLM Tools

- **fastmcp-creator** - Create FastMCP servers for Claude Desktop
- **litellm** - LiteLLM proxy and gateway guidance
- **llamafile** - Self-contained LLM executable guidance
- **prompt-optimization-claude-45** - Optimize prompts for Claude 4.5

### Development Workflows

- **agent-orchestration** - Task delegation and workflow patterns
- **verification-gate** - Quality gates and validation workflows
- **brainstorming-skill** - Structured brainstorming and ideation
- **story-based-framing** - Frame code changes as stories

### GitLab Integration

- **gitlab-skill** - GitLab API integration and workflows

### Patterns & Utilities

- **async-python-patterns** - Async Python best practices
- **toml-python** - TOML file handling in Python
- **xdg-base-directory** - XDG Base Directory specification
- **memory-bank-setup-skill** - Memory bank configuration

## Using These Skills in Claude Code

Install this skill collection:

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install development-skills@jamie-bitflight-skills
```

## Development Setup

### Prerequisites

- Python 3.11 or higher (tested with 3.12.3)
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

### Initial Setup

```bash
# Install uv if not already installed
pip install uv

# Install project dependencies
uv sync

# Install skills locally for development
./install.py
```

The `install.py` script discovers all skills (directories containing SKILL.md) and creates symlinks in `~/.claude/skills/`, making them immediately available in Claude Code.

### Pre-commit Hooks

This repository uses pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Run all checks
pre-commit run --all-files
```

## Creating New Skills

Use the skill-creator skill (from the official Anthropic skills) to create new skills in this repository:

```bash
# The skill-creator skill is already available in Claude Code
# Just ask Claude to create a new skill and it will use the skill-creator
```

After creating a new skill, run `./install.py` to make it available locally.

## About Agent Skills

Skills are self-contained directories, each containing:

- `SKILL.md` (required): YAML frontmatter + markdown instructions
- `scripts/` (optional): Executable Python/Bash code
- `references/` (optional): Documentation loaded into context as needed
- `assets/` (optional): Files used in output (templates, images, fonts)
- `commands/` (optional): Skill-specific commands

For more information, see the [official Agent Skills repository](https://github.com/anthropics/claude-skills).

## Contributing

Contributions are welcome! Please ensure:

1. New skills include proper `SKILL.md` with YAML frontmatter
2. Code passes all pre-commit checks (`pre-commit run --all-files`)
3. Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
4. Run `./install.py` after creating new skills

## References

- [Official Claude Skills Repository](https://github.com/anthropics/claude-skills)
- [Comfy Claude Prompt Library](https://github.com/Comfy-Org/comfy-claude-prompt-library)
