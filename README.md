# Claude Skills Collection

> AI reflects what's expressed, not what's true.

Professional development workflow extensions for Claude Code. Make Claude more thorough, accurate, and productive across Python, shell, Perl, CI/CD, and AI tooling.

**What's Here**: 20 plugins ranging from comprehensive development frameworks (15+ commands, specialized agents, extensive reference docs) to focused knowledge clip-ins (single-skill convention guides). Whether you need a complete Python TDD workflow or just want Claude to write proper commit messages, there's a plugin for that.

## Quick Start

```bash
# Add the marketplace (one-time setup)
/plugin marketplace add Jamie-BitFlight/claude_skills

# Install a plugin
/plugin install plugin-name@jamie-bitflight-skills
```

## Available Plugins

### 🏗️ Full-Featured Development Systems

These are comprehensive frameworks with multiple skills, commands, and specialized agents.

| Plugin                                           | What It Does                                                                                                          |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| [python3-development](./plugins/python3-development) | Transform Claude into a Python 3.11+ expert with 15+ commands, TDD workflows, modern library selection (Typer, Rich, httpx), and SAM methodology for feature development |
| [bash-development](./plugins/bash-development)       | Write robust Bash 5.1+ scripts with modern patterns, error handling, POSIX portability, and specialized agents for development and auditing |
| [perl-development](./plugins/perl-development)       | Build production-quality Perl 5.30+ scripts with modern practices, CPAN ecosystem integration, comprehensive testing, and CLI architecture |
| [plugin-creator](./plugins/plugin-creator)           | Complete toolkit for creating, refactoring, and validating Claude Code plugins with 6 specialized agents and systematic workflows |
| [uv](./plugins/uv)                                   | Expert guidance for Astral's uv - the extremely fast Python package manager that replaces pip, poetry, pyenv, and virtualenv with modern lockfiles |
| [clang-format](./plugins/clang-format)               | Configure clang-format to match your existing C/C++ code style by analyzing patterns and showing impact before changes |
| [holistic-linting](./plugins/holistic-linting)       | Automatic code quality enforcement - Claude won't say "done" until code passes all configured linters with root-cause fixing |
| [summarizer](./plugins/summarizer)                   | Faithful information summarization with anti-hallucination methodology, structured output templates, and autonomous agents |

### 📦 Lightweight Knowledge Clip-Ins

These are focused plugins that teach Claude specific conventions or tools without heavy workflows.

#### Python & Package Management

| Plugin | What It Does |
| ------ | ------------ |
| [litellm](./plugins/litellm) | Call any LLM API (OpenAI/Anthropic/local) from Python with unified interface and retry logic |
| [llamafile](./plugins/llamafile) | Run local GGUF models with OpenAI-compatible API for offline/air-gapped inference |
| [xdg-base-directory](./plugins/xdg-base-directory) | Store config and data files in correct XDG-compliant directories using platformdirs |

#### Git & CI/CD

| Plugin | What It Does |
| ------ | ------------ |
| [conventional-commits](./plugins/conventional-commits) | Write consistent commit messages (feat/fix/chore) for semantic versioning and changelog generation |
| [commitlint](./plugins/commitlint) | Configure and validate commit messages against commitlint rules for CI/CD enforcement |
| [gitlab-skill](./plugins/gitlab-skill) | Write GitLab CI pipelines and GLFM documentation with local testing before pushing |

#### AI & LLM Tools

| Plugin | What It Does |
| ------ | ------------ |
| [fastmcp-creator](./plugins/fastmcp-creator) | Build production-ready Model Context Protocol (MCP) servers with FastMCP framework and agent-centric design patterns |
| [prompt-optimization-claude-45](./plugins/prompt-optimization-claude-45) | Optimize CLAUDE.md and skills using Anthropic's best practices - transforms negative rules into positive patterns |

#### Better Claude Behavior

| Plugin | What It Does |
| ------ | ------------ |
| [agent-orchestration](./plugins/agent-orchestration) | Makes Claude more thorough on complex tasks by investigating root causes and verifying work actually functions |
| [verification-gate](./plugins/verification-gate) | Forces Claude to investigate before acting, preventing correct diagnosis with wrong implementation |
| [hallucination-detector](./plugins/hallucination-detector) | Blocks task completion when Claude speculates or makes ungrounded claims, forcing evidence-first rewrites |
| [brainstorming-skill](./plugins/brainstorming-skill) | Significantly improves brainstorming with 30+ research-validated prompt patterns across 14 categories |

## Why Use These Plugins?

Claude Code plugins extend Claude's capabilities in specific domains. This collection includes:

**Full-Featured Development Systems** - Complete frameworks with commands, specialized agents, and comprehensive workflows:
- **python3-development**: 15+ commands, 17 agents, TDD methodology, extensive reference docs
- **bash/perl-development**: Complete scripting frameworks with testing, linting, and auditing agents
- **plugin-creator**: 6 agents for systematic plugin development workflows
- **holistic-linting**: Automatic quality enforcement with root-cause analysis
- **summarizer**: Anti-hallucination summarization with structured templates

**Lightweight Knowledge Clip-Ins** - Focused plugins that teach specific conventions or tools:
- Modern commit formats (conventional-commits, commitlint)
- LLM integration patterns (litellm, llamafile, fastmcp-creator)
- Directory standards (xdg-base-directory)
- Code formatting (clang-format)
- Behavior improvements (verification-gate, hallucination-detector, brainstorming-skill)

Once installed, plugins work automatically - Claude knows when to use them based on your project context. Instead of generic responses, Claude will:

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

**[python3-development](./plugins/python3-development)** - The most comprehensive plugin in this collection. Transform Claude into a Python 3.11+ expert with 15+ commands, 17 specialized agents, TDD workflows, modern library selection (Typer, Rich, httpx, pytest), and SAM methodology for complete feature development. Includes extensive reference documentation covering 50+ modern Python libraries.

**[holistic-linting](./plugins/holistic-linting)** - Automatic code quality enforcement with root-cause fixing. Claude discovers your project's linters (ruff, mypy, bandit), runs them before completing tasks, and resolves issues through systematic analysis rather than suppression comments.

**[uv](./plugins/uv)** - Expert guidance for Astral's uv - the extremely fast Python package manager that replaces pip, poetry, pyenv, and virtualenv. Creates modern projects with lockfiles, writes portable scripts with PEP 723 inline dependencies, and configures CI/CD using best practices.

### For Systems Programming

**[bash-development](./plugins/bash-development)** - Write production-ready Bash 5.1+ scripts with modern error handling, POSIX portability checking, integrated logging framework, ShellCheck-aware linting, and test framework guidance. Includes specialized agents for script development and code auditing.

**[perl-development](./plugins/perl-development)** - Build robust Perl 5.30+ applications with strict/warnings/autodie pragmas, CPAN ecosystem management, comprehensive testing with Test2::V0, and Perl::Critic linting. Includes agents for development, auditing, and CLI architecture.

### For Better Claude Behavior

**[agent-orchestration](./plugins/agent-orchestration)** - Scientific delegation framework that makes Claude investigate root causes before implementing fixes, think about full scope instead of single issues, and verify work actually functions before claiming completion.

**[verification-gate](./plugins/verification-gate)** - Pre-action verification checkpoints that prevent Claude from jumping to solutions. Validates hypothesis-action alignment and catches situations where correct diagnosis leads to wrong implementation (like running the wrong package manager).

**[hallucination-detector](./plugins/hallucination-detector)** - Stop-hook that blocks task completion on speculation patterns. Catches ungrounded causality, pseudo-quantification without methodology, and completeness overclaims - forcing evidence-first rewrites.

**[brainstorming-skill](./plugins/brainstorming-skill)** - Improves idea generation with 30+ research-validated prompt patterns (role-based perspectives, constraint exploration, analogical thinking, inversion techniques). Structured techniques generate more ideas with reasoning while working within your actual constraints.

### For Plugin & Tool Developers

**[plugin-creator](./plugins/plugin-creator)** - Complete toolkit with 14 skills and 6 specialized agents for creating, refactoring, and validating Claude Code plugins. Includes systematic refactoring workflows, frontmatter validation, internal link checking, and automated quality enforcement.

**[fastmcp-creator](./plugins/fastmcp-creator)** - Build production-ready Model Context Protocol (MCP) servers with FastMCP framework specialization, agent-centric design patterns, Pydantic validation, async operations, and deployment guidance. Covers both Python (FastMCP) and TypeScript implementations.

**[clang-format](./plugins/clang-format)** - Configure clang-format to match your existing C/C++ code style instead of forcing a style. Analyzes patterns, tests configuration hypotheses, measures impact (line changes vs whitespace), and shows diffs before applying changes.

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
**Plugin Count**: 20 plugins (8 full-featured systems, 12 lightweight clip-ins)

This marketplace provides professional development workflow extensions for Python engineers, DevOps practitioners, and AI agent developers. Includes comprehensive frameworks for Python 3.11+, Bash 5.1+, and Perl 5.30+ development with TDD workflows, specialized agents, and automated quality enforcement. Also covers GitLab CI/CD automation, commit message standards, LLM integration patterns, MCP server creation, and Claude behavior improvements for hallucination prevention and systematic problem-solving.
