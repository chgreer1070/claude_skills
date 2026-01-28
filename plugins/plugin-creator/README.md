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

## When to Use

Use this plugin when:

- Creating new plugins, skills, commands, or agents
- Validating frontmatter in SKILL.md or agent files
- A skill exceeds 500 lines and needs splitting
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
uv run ./scripts/validate_frontmatter.py validate ./skills/my-skill/SKILL.md

# Auto-fix common frontmatter issues
uv run ./scripts/validate_frontmatter.py fix ./skills/my-skill/SKILL.md
```

### Refactoring Plugins

```bash
# Quick check of skill line counts
/plugin-creator:count-lines ./plugins/my-plugin

# Validate skill structure
./scripts/validate-skill-structure.sh ./skills/my-skill
```

## Commands

| Command                       | Purpose                | Example                                           |
| ----------------------------- | ---------------------- | ------------------------------------------------- |
| `/plugin-creator:count-lines` | Quick line count check | `/plugin-creator:count-lines ./plugins/my-plugin` |

## Skills

### Creation Skills

| Skill            | Purpose                                                                            |
| ---------------- | ---------------------------------------------------------------------------------- |
| `plugin-creator` | Step-by-step guidance for creating Claude Code plugins                             |
| `agent-creator`  | Create high-quality Claude Code agents from scratch or by adapting existing agents |

### Reference Skills

| Skill                           | Purpose                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| `claude-skills-overview-2026`   | Complete reference for Claude Code skills system (January 2026)  |
| `claude-plugins-reference-2026` | Complete reference for Claude Code plugins system (January 2026) |
| `claude-hooks-reference-2026`   | Complete reference for Claude Code hooks system (January 2026)   |

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
| `validate_frontmatter.py`     | Comprehensive schema validation with auto-fix | `uv run validate_frontmatter.py validate SKILL.md` |
| `validate-skill-structure.sh` | Skill structure and quality validation        | `./validate-skill-structure.sh ./skills/my-skill`  |
| `validate-task-file.sh`       | Validate refactoring task file format         | `./validate-task-file.sh tasks.md`                 |

### Utility Scripts

| Script                 | Purpose                                   | Usage                                        |
| ---------------------- | ----------------------------------------- | -------------------------------------------- |
| `create_plugin.py`     | Interactive plugin scaffolding            | `uv run create_plugin.py`                    |
| `count-skill-lines.sh` | Count lines and identify oversized skills | `./count-skill-lines.sh ./plugins/my-plugin` |
| `fix-tool-formats.py`  | Fix tool field formatting issues          | `uv run fix-tool-formats.py`                 |

### Script Usage Examples

```bash
# Validate frontmatter (comprehensive)
uv run ./scripts/validate_frontmatter.py validate ./skills/my-skill/SKILL.md

# Validate all frontmatter in a directory
uv run ./scripts/validate_frontmatter.py batch ./plugins/my-plugin

# Auto-fix frontmatter issues
uv run ./scripts/validate_frontmatter.py fix ./skills/my-skill/SKILL.md --dry-run
uv run ./scripts/validate_frontmatter.py fix ./skills/my-skill/SKILL.md

# Batch fix all frontmatter
uv run ./scripts/validate_frontmatter.py fix-batch ./plugins/my-plugin

# Validate skill structure (line counts, links, directories)
./scripts/validate-skill-structure.sh ./skills/my-skill

# Count skill lines
./scripts/count-skill-lines.sh ./plugins/my-plugin
```

## Validation Capabilities

### Frontmatter Validation (`validate_frontmatter.py`)

**Checks:**

- YAML syntax validity
- No forbidden multiline indicators (`>-`, `|-`)
- Required fields present (`name`, `description` for agents)
- Field types match schema (string, bool, object)
- Field values within constraints (length, pattern, valid values)
- Enumeration validation (model, permissionMode)

**Auto-fixes:**

- YAML arrays → comma-separated strings (tools, skills, etc.)
- Multiline descriptions → single-line quoted strings
- Unquoted descriptions with colons

**Supports:**

- Skills (SKILL.md)
- Agents (.md in agents/ directories)
- Commands (.md in commands/ directories)

### Skill Structure Validation (`validate-skill-structure.sh`)

**Checks:**

- SKILL.md presence and frontmatter structure
- Name and description fields
- Name format (lowercase, hyphens)
- Description length (minimum 20 characters)
- Description trigger phrases
- Line count limits (warns >500, errors >800)
- Progressive disclosure structure (references/, examples/, scripts/)
- Internal markdown link validity

## Refactoring Workflow

```text
┌─────────────────────────────────────────────────────────────────┐
│                    REFACTORING WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Invoke refactor-planner agent                                   │
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
│  Invoke refactor-executor agent                                  │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 4:        │                                            │
│  │ Execution       │──▶ Parallel agent execution                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  Invoke refactor-validator agent                                 │
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

- **Recommended**: <500 lines (body content)
- **Warning**: 500-800 lines - consider splitting
- **Critical**: >800 lines - must split

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

## Installation

```bash
# From marketplace
/plugin install plugin-creator@jamie-bitflight-skills

# For development
claude --plugin-dir ./plugins/plugin-creator
```

## Example Sessions

### Creating a New Plugin

```bash
# Generate plugin structure interactively
uv run ./scripts/create_plugin.py

# Validate the generated frontmatter
uv run ./scripts/validate_frontmatter.py batch ./my-new-plugin

# Validate plugin manifest
claude plugin validate ./my-new-plugin
```

### Refactoring an Existing Plugin

```bash
# 1. Check skill sizes
/plugin-creator:count-lines ./plugins/python3-development

# Output shows skills over 500 lines

# 2. Validate skill structures
./scripts/validate-skill-structure.sh ./plugins/python3-development/skills/python3

# 3. Invoke refactor-planner agent
Use the refactor-planner agent to analyze ./plugins/python3-development

# Assessment runs, creates plan files

# 4. Review plan at .claude/plan/refactor-design-python3-development.md

# 5. Invoke refactor-executor when ready
Use the refactor-executor agent to execute the python3-development refactoring plan

# Tasks execute in parallel where possible

# 6. Invoke refactor-validator
Use the refactor-validator agent to validate the python3-development refactoring

# If issues found, follow-up tasks created and cycle repeats
```

### Validating and Fixing Frontmatter

```bash
# Check a single file
uv run ./scripts/validate_frontmatter.py validate ./skills/my-skill/SKILL.md

# Validate all skills in a plugin
uv run ./scripts/validate_frontmatter.py batch ./plugins/my-plugin

# Auto-fix issues (dry-run first)
uv run ./scripts/validate_frontmatter.py fix ./skills/my-skill/SKILL.md --dry-run

# Apply fixes
uv run ./scripts/validate_frontmatter.py fix ./skills/my-skill/SKILL.md

# Batch fix entire plugin
uv run ./scripts/validate_frontmatter.py fix-batch ./plugins/my-plugin
```

## Related Plugins

- **holistic-linting** - Code quality and linting workflows
- **prompt-optimization-claude-45** - Optimize AI-facing documentation
- **python3-development** - Python development best practices

## Version

2.3.0 - Added claude-plugins-reference-2026 and claude-hooks-reference-2026 reference skills

## Author

Jamie Hoover (<https://github.com/bitflight-devops>)

## License

MIT License
