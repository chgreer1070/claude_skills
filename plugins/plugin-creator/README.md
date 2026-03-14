<p align="center">
  <img src="./assets/hero.png" alt="Plugin Creator & Refactoring Toolkit" width="800" />
</p>

# Plugin Creator & Refactoring Toolkit

Complete plugin development toolkit for creating, refactoring, and validating Claude Code plugins. Combines plugin creation, systematic refactoring workflows, and comprehensive validation tools.

## Overview

This plugin provides end-to-end capabilities for plugin development:

**Plugin Creation:**

- Step-by-step guidance for creating new plugins
- Frontmatter validation and auto-fixing
- Structure scaffolding and template generation

**Plugin Refactoring:**

- Analyze plugin structure and identify issues
- Create detailed refactoring plans
- Execute tasks via specialized agents
- Validate refactoring completeness

**Validation Tools:**

- Comprehensive frontmatter schema validation
- Skill structure and quality checks
- Internal link validation
- Line count enforcement

## Skill Name Field

**`name:` is required** per the [Agent Skills open standard](https://agentskills.io/specification).

```yaml
---
name: my-skill
description: Does something useful
user-invocable: true
---
```

### Bug History (Resolved)

**Discovered:** 2026-01-29 (Claude Code v2.1.23) — **Resolved:** 2026-02-20

A bug caused plugin skills with an explicit `name:` field to not appear as slash commands. As a workaround, validators automatically removed `name:` from plugin skill frontmatter. That workaround has been reversed. The `skilllint` CLI now automatically **adds** the `name:` field when absent, deriving it from the directory name.

## When to Use

Use this plugin when:

- Creating new plugins, skills, commands, or agents
- Validating frontmatter in SKILL.md or agent files
- A skill exceeds the validator token threshold and needs splitting
- Skills cover multiple distinct domains
- Agent descriptions have weak triggers
- Plugin structure needs reorganization
- Systematically improving plugin quality

## Quick Start

### Creating Plugins

```bash
# Generate new plugin structure
uv run ./scripts/create_plugin.py

# Validate frontmatter
uvx skilllint@latest check ./skills/my-skill/SKILL.md

# Auto-fix common frontmatter issues
uvx skilllint@latest check --fix ./skills/my-skill/SKILL.md
```

### Refactoring Plugins

```bash
# Check skill complexity via token metrics
uvx skilllint@latest check --verbose ./plugins/my-plugin
```

## Skills

### Creation Skills

| Skill                           | Purpose                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `plugin-creator`                | Step-by-step guidance for creating Claude Code plugins                                         |
| `skill-creator`                 | Official Anthropic guide for creating effective skills (modified from upstream)                |
| `agent-creator`                 | Create high-quality Claude Code agents from scratch or by adapting existing agents             |
| `write-frontmatter-description` | Write or rewrite frontmatter description fields for skills and agents following best practices |

### Reference Skills

| Skill                           | Purpose                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| `claude-skills-overview-2026`   | Complete reference for Claude Code skills system (January 2026)  |
| `claude-plugins-reference-2026` | Complete reference for Claude Code plugins system (January 2026) |
| `hooks-guide`                   | Cross-platform hooks reference — Claude Code, GitHub Copilot, Cursor, Windsurf, Amp |

### Refactoring Skills

| Skill                 | Purpose                                                   |
| --------------------- | --------------------------------------------------------- |
| `assessor`            | Analyze plugin and create refactoring task files          |
| `implement-refactor`  | Execute refactoring tasks with parallel orchestration     |
| `ensure-complete`     | Validate refactoring and create follow-up tasks if needed |
| `refactor-plugin`     | Complete plugin refactoring workflow                      |
| `refactor-skill`      | Split oversized skills into smaller focused skills        |
| `start-refactor-task` | Execute individual refactoring tasks                      |
| `feature-discovery`   | Research feature requests and identify gaps               |

## Agents

| Agent                | Purpose                                       | Triggers                                                |
| -------------------- | --------------------------------------------- | ------------------------------------------------------- |
| `refactor-planner`   | Analyze plugins and create refactoring plans  | "plan a refactoring", "analyze plugin for refactoring"  |
| `refactor-executor`  | Execute refactoring tasks from plans          | "execute refactoring tasks", "run the refactoring plan" |
| `refactor-validator` | Validate refactoring completeness and quality | "validate refactoring", "verify refactoring complete"   |

## Scripts

### Validation Scripts

| Script                        | Purpose                                       | Usage                                              |
| ----------------------------- | --------------------------------------------- | -------------------------------------------------- |
| `skilllint`               | Comprehensive schema validation with auto-fix | `uvx skilllint@latest check SKILL.md`                |
| `validate-task-file.sh`       | Validate refactoring task file format         | `./validate-task-file.sh tasks.md`                 |

### Utility Scripts

| Script                 | Purpose                                   | Usage                                        |
| ---------------------- | ----------------------------------------- | -------------------------------------------- |
| `create_plugin.py`     | Interactive plugin scaffolding            | `uv run create_plugin.py`                    |
| `fix_tool_formats.py`  | Fix tool field formatting issues          | `uv run fix_tool_formats.py`                 |

### Script Usage Examples

```bash
# Validate frontmatter (comprehensive)
uvx skilllint@latest check ./skills/my-skill/SKILL.md

# Validate all frontmatter in a directory
uvx skilllint@latest check ./plugins/my-plugin

# Auto-fix frontmatter issues
uvx skilllint@latest check --check ./skills/my-skill/SKILL.md
uvx skilllint@latest check --fix ./skills/my-skill/SKILL.md

# Batch fix entire plugin
uvx skilllint@latest check --fix ./plugins/my-plugin

```

## Validation Capabilities

### Frontmatter Validation (skilllint)

**Checks:**

- YAML syntax validity
- No forbidden multiline indicators (`>-`, `|-`)
- Required fields present (`name`, `description` for agents)
- Field types match schema (string, bool, object)
- Field values within constraints (length, pattern, valid values)
- Enumeration validation (model, permissionMode)

**Auto-fixes:**

- YAML arrays → comma-separated strings (tools, skills, etc.)
- Multiline descriptions → single-line strings
- Unquoted colons in descriptions — adds quotes to prevent YAML parsing failures

**Supports:**

- Skills (SKILL.md)
- Agents (.md in agents/ directories)
- Commands (.md in commands/ directories)

## Refactoring Workflow

```text
┌─────────────────────────────────────────────────────────────────┐
│                    REFACTORING WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Invoke @"plugin-creator:refactor-planner (agent)"              │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 1:        │                                            │
│  │ Assessment      │──▶ Plugin Assessment Report                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 2:        │                                            │
│  │ Design          │──▶ refactor-design-{slug}.md               │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 3:        │                                            │
│  │ Task Planning   │──▶ tasks-refactor-{slug}.md                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  Invoke @"plugin-creator:refactor-executor (agent)"             │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 4:        │                                            │
│  │ Execution       │──▶ Parallel agent execution                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  Invoke @"plugin-creator:refactor-validator (agent)"            │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 5:        │                                            │
│  │ Validation      │──▶ Validation Report                       │
│  └────────┬────────┘                                            │
│           │                                                      │
│     ┌─────┴─────┐                                               │
│     │           │                                               │
│     ▼           ▼                                               │
│  [Issues]    [No Issues]                                        │
│     │           │                                               │
│     ▼           ▼                                               │
│  Follow-up   COMPLETE                                           │
│  Tasks                                                          │
│     │                                                           │
│     └─────────▶ Recurse                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quality Standards

### Skill Size Limits

Complexity is measured by token count (via `skilllint`). Token thresholds replace line-count heuristics.

- **Warning**: TOKEN_WARNING_THRESHOLD tokens - consider splitting
- **Critical**: TOKEN_ERROR_THRESHOLD tokens - must split

### Skill Split Requirements

When splitting skills:

- No content loss (100% migration)
- Cross-references between new skills
- Original skill becomes facade/meta-skill
- Backwards compatibility maintained

### Frontmatter Requirements

**Skills:**

- `name`: Optional (uses directory name if omitted)
- `description`: Optional (uses first paragraph if omitted)
- Valid tool/model values if specified

**Agents:**

- `name`: Required (lowercase, hyphens)
- `description`: Required (trigger keywords)
- `model`: One of sonnet/opus/haiku/inherit
- `tools`: Comma-separated string (not array)

## Plugin System Fundamentals

### Plugin Caching and File Resolution

Claude Code copies plugins to a cache directory rather than using them in-place for security and verification.

**How it works:**

- Marketplace plugins: The `source` path is copied recursively
- Plugins with `.claude-plugin/plugin.json`: The directory containing `.claude-plugin/` is copied recursively

**Path traversal limitations:**

- Plugins cannot reference files outside their directory (`../shared-utils` will fail)
- External files are not copied to the cache

**Solutions for external dependencies:**

1. **Use symlinks:** Create symlinks within your plugin directory (symlinks are followed during copy)

   ```bash
   ln -s /path/to/shared-utils ./shared-utils
   ```

2. **Restructure marketplace:** Set source to parent directory that contains all required files

### Installation Scopes

When installing a plugin, choose a scope that determines availability:

| Scope     | Settings file                 | Use case                                                 |
| --------- | ----------------------------- | -------------------------------------------------------- |
| `user`    | `~/.claude/settings.json`     | Personal plugins available across all projects (default) |
| `project` | `.claude/settings.json`       | Team plugins shared via version control                  |
| `local`   | `.claude/settings.local.json` | Project-specific plugins, gitignored                     |
| `managed` | `managed-settings.json`       | Managed plugins (read-only, update only)                 |

**Examples:**

```bash
# Install to user scope (default)
claude plugin install plugin-creator@jamie-bitflight-skills

# Install to project scope (shared with team)
claude plugin install plugin-creator@jamie-bitflight-skills --scope project

# Install to local scope (gitignored)
claude plugin install plugin-creator@jamie-bitflight-skills --scope local
```

### Environment Variables

**`${CLAUDE_PLUGIN_ROOT}`:** Absolute path to your plugin directory. Use in hooks, MCP servers, and scripts.

**`${CLAUDE_PROJECT_DIR}`:** Project root directory (where Claude Code was started).

**Example:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
      }]
    }]
  }
}
```

### CLI Commands Reference

**Install plugin:**

```bash
claude plugin install <plugin> [--scope user|project|local]
```

**Uninstall plugin:**

```bash
claude plugin uninstall <plugin> [--scope user|project|local]
# Aliases: remove, rm
```

**Enable/disable plugin:**

```bash
claude plugin enable <plugin> [--scope user|project|local]
claude plugin disable <plugin> [--scope user|project|local]
```

**Update plugin:**

```bash
claude plugin update <plugin> [--scope user|project|local|managed]
```

**Validate plugin:**

```bash
claude plugin validate <plugin-directory>
/plugin validate <plugin-directory>  # In session
```

### Testing Without Installation

```bash
# Load plugin for current session only
claude --plugin-dir ./plugins/plugin-creator

# Load multiple plugins
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two
```

## Installation

```bash
# From marketplace (user scope - default)
/plugin install plugin-creator@jamie-bitflight-skills

# Install to project scope (shared with team)
claude plugin install plugin-creator@jamie-bitflight-skills --scope project

# For development (session only)
claude --plugin-dir ./plugins/plugin-creator
```

## Example Sessions

### Creating a New Plugin

```bash
# Generate plugin structure interactively
uv run ./scripts/create_plugin.py

# Validate the generated frontmatter
uvx skilllint@latest check ./my-new-plugin

# Validate plugin manifest
claude plugin validate ./my-new-plugin
```

### Refactoring an Existing Plugin

```bash
# 1. Check skill complexity
uvx skilllint@latest check --verbose ./plugins/python3-development

# Output shows skills over token thresholds

# 2. Invoke @"plugin-creator:refactor-planner (agent)"
Use @"plugin-creator:refactor-planner (agent)" to analyze ./plugins/python3-development

# Assessment runs, creates plan files

# 4. Review plan at .claude/plan/refactor-design-python3-development.md

# 5. Invoke @"plugin-creator:refactor-executor (agent)" when ready
Use @"plugin-creator:refactor-executor (agent)" to execute the python3-development refactoring plan

# Tasks execute in parallel where possible

# 6. Invoke @"plugin-creator:refactor-validator (agent)"
Use @"plugin-creator:refactor-validator (agent)" to validate the python3-development refactoring

# If issues found, follow-up tasks created and cycle repeats
```

### Validating and Fixing Frontmatter

```bash
# Check a single file
uvx skilllint@latest check ./skills/my-skill/SKILL.md

# Validate all skills in a plugin
uvx skilllint@latest check ./plugins/my-plugin

# Validate only (no fixes)
uvx skilllint@latest check --check ./skills/my-skill/SKILL.md

# Apply fixes
uvx skilllint@latest check --fix ./skills/my-skill/SKILL.md

# Batch fix entire plugin
uvx skilllint@latest check --fix ./plugins/my-plugin
```

## Plugin Component Reference

### plugin.json Component Fields

| Field          | Type           | Description                                         | Example                                  |
| -------------- | -------------- | --------------------------------------------------- | ---------------------------------------- |
| `commands`     | string\|array  | Additional command files/directories                | `"./custom/cmd.md"` or `["./cmd1.md"]`   |
| `agents`       | string\|array  | Additional agent files or directories               | `"./custom/agents/"` or `["./agent.md"]` |
| `skills`       | string\|array  | Additional skill directories                        | `"./custom/skills/"`                     |
| `hooks`        | string\|object | Hook config path or inline config                   | `"./hooks.json"`                         |
| `mcpServers`   | string\|object | MCP config path or inline config                    | `"./mcp-config.json"`                    |
| `outputStyles` | string\|array  | Additional output style files/directories           | `"./styles/"`                            |
| `lspServers`   | string\|object | Language Server Protocol config (code intelligence) | `"./.lsp.json"`                          |

**Path behavior:**

- Custom paths supplement default directories (don't replace them)
- All paths must be relative and start with `./`
- Multiple paths can be specified as arrays

### LSP Servers

Plugins can provide Language Server Protocol (LSP) servers for real-time code intelligence:

- **Instant diagnostics:** Claude sees errors and warnings immediately after edits
- **Code navigation:** go to definition, find references, hover information
- **Language awareness:** type information and documentation for code symbols

**Configuration format:**

```json
{
  "lspServers": {
    "python": {
      "command": "pyright-langserver",
      "args": ["--stdio"],
      "extensionToLanguage": {
        ".py": "python"
      }
    }
  }
}
```

**Note:** LSP servers require separate binary installation. LSP plugins configure Claude Code's connection to a language server but don't include the server itself.

**Available LSP plugins:**

| Plugin           | Language server  | Install command                                                                            |
| ---------------- | ---------------- | ------------------------------------------------------------------------------------------ |
| `pyright-lsp`    | Pyright (Python) | `pip install pyright` or `npm install -g pyright`                                          |
| `typescript-lsp` | TypeScript LS    | `npm install -g typescript-language-server typescript`                                     |
| `rust-lsp`       | rust-analyzer    | See [rust-analyzer installation](https://rust-analyzer.github.io/manual.html#installation) |

## Related Plugins

- **holistic-linting** - Code quality and linting workflows
- **prompt-optimization-claude-45** - Optimize AI-facing documentation
- **python3-development** - Python development best practices

## Version

2.5.0 - Added official Anthropic skill-creator skill (modified from upstream)

## Author

Jamie Nelson (<https://github.com/bitflight-devops>)

## Attributions

- **skill-creator skill**: Modified version of the official Anthropic skill-creator from [anthropics/skills](https://github.com/anthropics/skills/tree/69c0b1a0674149f27b61b2635f935524b6add202/skills/skill-creator). Licensed under Apache License 2.0 (see `skills/skill-creator/LICENSE.txt`).

## License

MIT License (excluding skill-creator which retains Apache License 2.0)

---

> **The Ancient Woe**
>
> *The master craftsman who spends all day building tools to build other tools, never actually finishing the grand cathedral he was hired to construct.*

> **The Bard's Decree**
>
> *"I need a forge that births other forges! A master mold to cast my iron servants, that I may finally rest whilst they hammer the steel into shape!"*
