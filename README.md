# Claude Skills Collection

Professional development workflow extensions for Claude Code. Make Claude more thorough, accurate, and productive across Python, shell, Perl, CI/CD, and AI tooling.

## Quick Start

```bash
# Add the marketplace (one-time setup)
/plugin marketplace add Jamie-BitFlight/claude_skills

# Install a plugin
/plugin install plugin-name@jamie-bitflight-skills
```

## Available Plugins

### Python Development

| Plugin                                                   | What It Does                                                                         |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [python3-development](./plugins/python3-development)     | Better Python code with modern patterns, proper testing, and clean project structure |
| [uv](./plugins/uv)                                       | Fast, modern Python project setup with uv instead of pip                             |
| [async-python-patterns](./plugins/async-python-patterns) | Write async Python code that actually works                                          |
| [hatchling](./plugins/hatchling)                         | Set up Python packages with modern pyproject.toml                                    |
| [pypi-readme-creator](./plugins/pypi-readme-creator)     | READMEs that render correctly on PyPI                                                |
| [toml-python](./plugins/toml-python)                     | Edit TOML files without breaking comments and formatting                             |

### Shell & Systems Programming

| Plugin                                             | What It Does                                                          |
| -------------------------------------------------- | --------------------------------------------------------------------- |
| [bash-development](./plugins/bash-development)     | Modern Bash 5.1+ scripting with testing, linting, and POSIX fallbacks |
| [perl-development](./plugins/perl-development)     | Perl 5.30+ development with CPAN ecosystem and modern testing         |
| [xdg-base-directory](./plugins/xdg-base-directory) | Store config and data files in the right places                       |

### Code Quality & Linting

| Plugin                                         | What It Does                                                |
| ---------------------------------------------- | ----------------------------------------------------------- |
| [holistic-linting](./plugins/holistic-linting) | Claude checks and fixes lint errors before saying "done"    |
| [pre-commit](./plugins/pre-commit)             | Set up pre-commit hooks that actually catch issues          |
| [clang-format](./plugins/clang-format)         | Configure C/C++ formatting that matches your codebase style |

### Git & CI/CD

| Plugin                                                 | What It Does                                               |
| ------------------------------------------------------ | ---------------------------------------------------------- |
| [conventional-commits](./plugins/conventional-commits) | Consistent commit messages that work with semantic release |
| [commitlint](./plugins/commitlint)                     | Validate commit messages in CI                             |
| [gitlab-skill](./plugins/gitlab-skill)                 | Better GitLab CI pipelines and documentation               |

### AI & LLM Tools

| Plugin                                                                   | What It Does                                      |
| ------------------------------------------------------------------------ | ------------------------------------------------- |
| [fastmcp-creator](./plugins/fastmcp-creator)                             | Build MCP servers that Claude can use             |
| [litellm](./plugins/litellm)                                             | Call any LLM API with one library                 |
| [llamafile](./plugins/llamafile)                                         | Run LLMs locally without cloud APIs               |
| [prompt-optimization-claude-45](./plugins/prompt-optimization-claude-45) | Write better CLAUDE.md and skill files            |
| [hallucination-detector](./plugins/hallucination-detector)               | Stop Claude from speculating instead of verifying |

### Documentation

| Plugin                     | What It Does                                    |
| -------------------------- | ----------------------------------------------- |
| [mkdocs](./plugins/mkdocs) | Create documentation sites with MkDocs Material |

### Better Claude Behavior

| Plugin                                               | What It Does                                             |
| ---------------------------------------------------- | -------------------------------------------------------- |
| [agent-orchestration](./plugins/agent-orchestration) | Claude handles complex, multi-step tasks more thoroughly |
| [brainstorming-skill](./plugins/brainstorming-skill) | Structured brainstorming with proven prompt patterns     |
| [story-based-framing](./plugins/story-based-framing) | Better pattern recognition through narrative structure   |
| [verification-gate](./plugins/verification-gate)     | Claude verifies work before claiming "done"              |

### Plugin & Skill Development

| Plugin                                     | What It Does                                       |
| ------------------------------------------ | -------------------------------------------------- |
| [plugin-creator](./plugins/plugin-creator) | Create, refactor, and validate Claude Code plugins |

## Why Use These Plugins?

Claude Code plugins extend Claude's capabilities in specific domains. Instead of generic responses, Claude will:

- Follow modern language conventions (Python 3.11+, Bash 5.1+, Perl 5.30+)
- Use your preferred tools and libraries consistently
- Verify work thoroughly before claiming completion
- Apply systematic problem-solving approaches
- Produce production-ready code with proper testing and quality checks

## How Plugins Work

Plugins contain:

- **Skills** - Knowledge and workflows that guide Claude's behavior
- **Commands** - Slash commands you can invoke directly (like `/lint` or `/modernpython`)
- **Agents** - Specialized sub-agents for complex tasks (like code review or architecture design)
- **Hooks** - Automation that runs at specific lifecycle events

Once installed, plugins work automatically - Claude knows when to use them based on your project context.

## Plugin Structure

```text
plugins/plugin-name/
├── .claude-plugin/
│   └── plugin.json       # Plugin manifest
├── skills/               # What Claude learns
├── commands/             # Slash commands you can use
├── agents/               # Specialized sub-agents
└── README.md             # Documentation
```

## Featured Plugins

### For Python Developers

**[python3-development](./plugins/python3-development)** - Comprehensive Python 3.11+ development with modern patterns, testing workflows, and quality checks. Includes 15+ user-invocable commands and specialized agents for CLI architecture, code review, and test design.

**[holistic-linting](./plugins/holistic-linting)** - Automatic code quality enforcement. Claude won't say "done" until your code passes all configured linters. Includes rule references for ruff, mypy, and other common tools.

**[uv](./plugins/uv)** - Modern Python project setup using uv (the fast Rust-based package manager). Creates proper pyproject.toml, manages dependencies, and handles virtual environments correctly.

### For Better Claude Behavior

**[agent-orchestration](./plugins/agent-orchestration)** - Makes Claude more thorough with complex tasks. Investigates root causes instead of symptoms, verifies solutions actually work, and completes all steps before claiming "done".

**[verification-gate](./plugins/verification-gate)** - Prevents Claude from jumping to solutions. Forces reading files, verifying diagnoses, and checking that fixes target the actual problem system.

**[hallucination-detector](./plugins/hallucination-detector)** - Catches speculation and ungrounded claims. Blocks completion when Claude makes claims without evidence, forcing evidence-first rewrites.

### For Plugin Developers

**[plugin-creator](./plugins/plugin-creator)** - Complete toolkit for creating, refactoring, and validating Claude Code plugins. Includes frontmatter validation, structure checking, and systematic refactoring workflows.

## Local Development

For testing plugins during development:

```bash
# Option 1: Load specific plugins for this session
claude --plugin-dir ./plugins/python3-development --plugin-dir ./plugins/holistic-linting

# Option 2: Add local marketplace for persistent enable/disable
/plugin marketplace add ./.claude-plugin/marketplace.json

# Install plugins you need (--scope local keeps it gitignored)
/plugin install python3-development@jamie-bitflight-skills --scope local

# Disable when not needed
/plugin disable python3-development@jamie-bitflight-skills

# Re-enable when needed
/plugin enable python3-development@jamie-bitflight-skills
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines on adding, removing, or updating plugins.

Quick overview:

1. Fork the repository
2. Create your plugin using `/plugin-creator` or manually
3. Update `.claude-plugin/marketplace.json`
4. Validate with `claude plugin validate`
5. Test locally before submitting PR
6. Submit pull request with description

## Requirements

- Claude Code v2.0 or later
- Individual plugins may have additional requirements (see plugin READMEs)

## License

MIT License - see individual plugins for specifics.

## Marketplace Info

**Marketplace Name**: `jamie-bitflight-skills`
**Owner**: Jamie BitFlight (<jamie@bitflight.io>)
**Version**: 2.0.0

This marketplace provides professional development workflow extensions for Python engineers, DevOps practitioners, and AI agent developers. Covers modern Python toolchains, GitLab CI/CD automation, code quality enforcement, MCP server creation, and plugin/agent development patterns.
