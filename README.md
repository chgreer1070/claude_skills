# Claude Skills Collection

> AI reflects what's expressed, not what's true.

Professional development workflow extensions for Claude Code. Make Claude more thorough, accurate, and productive across Python, shell, Perl, CI/CD, and AI tooling.

## What Problem Does This Solve?

| Without plugins | With plugins |
| --- | --- |
| Claude gives generic Python advice | Claude applies Python 3.11+, Typer, Rich, httpx conventions specific to your stack |
| Claude says "done" before linters pass | Holistic-linting enforces root-cause fixes before any task completes |
| Claude speculates and hallucinates | Hallucination-detector blocks completion on ungrounded claims |
| Claude jumps to solutions without investigating | Verification-gate forces evidence gathering before action |
| Session transcripts disappear with no learning | Agentskill-kaizen mines transcripts for anti-patterns and generates skill patches |
| Commit messages are inconsistent | Conventional-commits enforces feat/fix/chore format for semantic versioning |

## Quick Start

```bash
# Add the marketplace (one-time setup)
/plugin marketplace add Jamie-BitFlight/claude_skills

# Install a plugin
/plugin install plugin-name@jamie-bitflight-skills
```

### Verify Installation

Start a new session and ask Claude to perform a task the plugin handles (for example, write a Python function after installing `python3-development`). Claude should automatically apply the plugin's conventions rather than generic defaults.

## Available Plugins

### Full-Featured Development Systems

Comprehensive frameworks with multiple skills, commands, and specialized agents.

| Plugin | What It Does |
| --- | --- |
| [python3-development](./plugins/python3-development) | Transform Claude into a Python 3.11+ expert with 15+ commands, TDD workflows, modern library selection (Typer, Rich, httpx), and SAM methodology for feature development |
| [bash-development](./plugins/bash-development) | Write robust Bash 5.1+ scripts with modern patterns, error handling, POSIX portability, and specialized agents for development and auditing |
| [perl-development](./plugins/perl-development) | Build production-quality Perl 5.30+ scripts with modern practices, CPAN ecosystem integration, comprehensive testing, and CLI architecture |
| [plugin-creator](./plugins/plugin-creator) | Complete toolkit for creating, refactoring, and validating Claude Code plugins with 6 specialized agents and systematic workflows |
| [uv](./plugins/uv) | Expert guidance for Astral's uv — the fast Python package manager that replaces pip, poetry, pyenv, and virtualenv with modern lockfiles |
| [clang-format](./plugins/clang-format) | Configure clang-format to match your existing C/C++ code style by analyzing patterns and showing impact before changes |
| [holistic-linting](./plugins/holistic-linting) | Automatic code quality enforcement — Claude won't say "done" until code passes all configured linters with root-cause fixing |
| [summarizer](./plugins/summarizer) | Faithful information summarization with anti-hallucination methodology, structured output templates, and autonomous agents |
| [agentskill-kaizen](./plugins/agentskill-kaizen) | Analyze Claude Code session transcripts to find inefficiencies, anti-patterns, and repeated mistakes with DuckDB process-mining and live sentiment dashboard |
| [dasel](./plugins/dasel) | Query, transform, and convert structured data files (JSON, YAML, TOML, XML, CSV) using dasel v3 with enterprise XML support and exploration agents |
| [development-harness](./plugins/development-harness) | Language-agnostic development process harness implementing the SAM 7-stage pipeline with planning, verification, and testing methodology |
| [the-rewrite-room](./plugins/the-rewrite-room) | Documentation workflow router — routes tasks like drift audits, doc sync, prompt optimization, and summarization to canonical workflows with validation |

### Lightweight Knowledge Clip-Ins

Focused plugins that teach Claude specific conventions or tools without heavy workflows.

#### Python and Package Management

| Plugin | What It Does |
| --- | --- |
| [litellm](./plugins/litellm) | Call any LLM API (OpenAI/Anthropic/local) from Python with unified interface and retry logic |
| [llamafile](./plugins/llamafile) | Run local GGUF models with OpenAI-compatible API for offline/air-gapped inference |
| [xdg-base-directory](./plugins/xdg-base-directory) | Store config and data files in correct XDG-compliant directories using platformdirs |

#### Git and CI/CD

| Plugin | What It Does |
| --- | --- |
| [conventional-commits](./plugins/conventional-commits) | Write consistent commit messages (feat/fix/chore) for semantic versioning and changelog generation |
| [commitlint](./plugins/commitlint) | Configure and validate commit messages against commitlint rules for CI/CD enforcement |
| [gitlab-skill](./plugins/gitlab-skill) | Write GitLab CI pipelines and GLFM documentation with local testing before pushing |

#### AI and LLM Tools

| Plugin | What It Does |
| --- | --- |
| [fastmcp-creator](./plugins/fastmcp-creator) | Build production-ready Model Context Protocol (MCP) servers with FastMCP framework and agent-centric design patterns |
| [prompt-optimization-claude-45](./plugins/prompt-optimization-claude-45) | Optimize CLAUDE.md and skills using Anthropic's best practices — transforms negative rules into positive patterns |

#### Better Claude Behavior

| Plugin | What It Does |
| --- | --- |
| [agent-orchestration](./plugins/agent-orchestration) | Makes Claude more thorough on complex tasks by investigating root causes and verifying work actually functions |
| [verification-gate](./plugins/verification-gate) | Forces Claude to investigate before acting, preventing correct diagnosis with wrong implementation |
| [hallucination-detector](https://github.com/bitflight-devops/hallucination-detector) | Blocks task completion when Claude speculates or makes ungrounded claims, forcing evidence-first rewrites |
| [brainstorming-skill](./plugins/brainstorming-skill) | Significantly improves brainstorming with 30+ research-validated prompt patterns across 14 categories |
| [orchestrator-discipline](./plugins/orchestrator-discipline) | Prevents orchestrator context window bloat via PreToolUse hooks — blocks file reads without edits, diagnostic commands that should be delegated |

## How Plugins Work

Plugins contain:

- **Skills** — Knowledge and workflows that guide Claude's behavior
- **Commands** — Slash commands you can invoke directly (like `/lint` or `/modernpython`)
- **Agents** — Specialized sub-agents for complex tasks (like code review or architecture design)
- **Hooks** — Automation that runs at specific lifecycle events

Once installed, plugins work automatically. Claude knows when to apply them based on your project context.

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

## Local Development

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

## Workshops

The `workshops/` directory contains hands-on workshop materials for teaching AI-assisted development in specific domains:

- **[Embedded Engineers (Claude)](./workshops/ai-agents-skills-for-embedded-engineers-claude.md)** — 1-hour workshop covering skills, agents, and orchestration for firmware development with MISRA-C, FreeRTOS, and Zigbee patterns
- **[Embedded Engineers (Cursor)](./workshops/ai-agents-skills-for-embedded-engineers-cursor.md)** — Equivalent workshop adapted for Cursor with custom agents and embedded skills

## Troubleshooting

**Plugin commands not found after install?**

Restart Claude Code to reload commands. Verify the plugin installed:

```bash
/plugin list
```

**Plugin not influencing Claude's behavior?**

Check that the plugin is enabled and not scoped to a different project:

```bash
/plugin list --all
```

**Want to test a plugin before committing to it?**

Use `--scope local` when installing. This keeps the plugin active only in your current project and gitignored.

**Something broken after an update?**

Reinstall the specific plugin:

```bash
/plugin install plugin-name@jamie-bitflight-skills
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

MIT License — see individual plugins for specifics.
