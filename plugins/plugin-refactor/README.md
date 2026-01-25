# Plugin Refactor

A comprehensive toolkit for refactoring Claude Code plugins. Analyzes plugin structure, identifies oversized skills, creates refactoring plans, and orchestrates parallel execution of refactoring tasks.

## Overview

The plugin-refactor toolkit helps you systematically improve plugin quality by:

1. **Assessing** plugin structure and identifying issues
2. **Planning** refactoring with detailed task specifications
3. **Executing** tasks via specialized agents
4. **Validating** that refactoring achieved its goals

## When to Use

Use this plugin when:

- A skill exceeds 500 lines and needs splitting
- Skills cover multiple distinct domains
- Agent descriptions have weak triggers
- Plugin structure needs reorganization
- You want to improve plugin quality systematically

## Quick Start

```bash
# Start a complete refactoring workflow
/plugin-refactor:refactor ./plugins/my-plugin

# Quick check of skill line counts
/plugin-refactor:count-lines ./plugins/my-plugin
```

## Commands

| Command                        | Purpose                             | Example                                                   |
| ------------------------------ | ----------------------------------- | --------------------------------------------------------- |
| `/plugin-refactor:refactor`    | Start complete refactoring workflow | `/plugin-refactor:refactor ./plugins/python3-development` |
| `/plugin-refactor:count-lines` | Quick line count check              | `/plugin-refactor:count-lines ./plugins/my-plugin`        |

## Skills

| Skill                 | Purpose                                                   |
| --------------------- | --------------------------------------------------------- |
| `assessor`            | Analyze plugin and create refactoring task files          |
| `implement-refactor`  | Execute refactoring tasks with parallel orchestration     |
| `ensure-complete`     | Validate refactoring and create follow-up tasks if needed |
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

Utility scripts for validation and analysis:

| Script                        | Purpose                                           |
| ----------------------------- | ------------------------------------------------- |
| `validate-skill-structure.sh` | Validate skill directory structure and content    |
| `validate-task-file.sh`       | Validate refactoring task file format             |
| `count-skill-lines.sh`        | Count lines in skills and identify oversized ones |

### Usage

```bash
# Validate a skill
./scripts/validate-skill-structure.sh ./skills/my-skill

# Validate a task file
./scripts/validate-task-file.sh .claude/plan/tasks-refactor-my-plugin.md

# Count skill lines
./scripts/count-skill-lines.sh ./plugins/my-plugin
```

## Refactoring Workflow

```text
┌─────────────────────────────────────────────────────────────────┐
│                    REFACTORING WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /plugin-refactor:refactor <plugin-path>                         │
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
│  /plugin-refactor:implement-refactor {slug}                      │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ Phase 4:        │                                            │
│  │ Execution       │──▶ Parallel agent execution                │
│  └────────┬────────┘                                            │
│           │                                                      │
│           ▼                                                      │
│  /plugin-refactor:ensure-complete                                │
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

## Task Types

The refactoring system handles these issue types:

| Type             | Description                         | Handler                          |
| ---------------- | ----------------------------------- | -------------------------------- |
| `SKILL_SPLIT`    | Skills >500 lines or multi-domain   | `refactor-skill` skill           |
| `AGENT_OPTIMIZE` | Weak agent triggers or instructions | `subagent-refactorer` agent      |
| `DOC_IMPROVE`    | Poor descriptions or documentation  | `claude-context-optimizer` agent |
| `ORPHAN_RESOLVE` | Unreferenced files                  | Context optimizer or manual      |
| `STRUCTURE_FIX`  | Broken links or structure issues    | Direct implementation            |

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

### Validation Checks

- All tasks have acceptance criteria (minimum 3)
- All tasks have verification steps
- Dependencies correctly mapped
- No circular dependencies
- Parallelization opportunities identified

## Installation

```bash
# From marketplace
/plugin install plugin-refactor@jamie-bitflight-skills

# For development
claude --plugin-dir ./plugins/plugin-refactor
```

## Example Session

```bash
# 1. Check skill sizes first
/plugin-refactor:count-lines ./plugins/python3-development

# Output shows skills over 500 lines

# 2. Start refactoring workflow
/plugin-refactor:refactor ./plugins/python3-development

# Assessment runs, creates plan files

# 3. Review plan at .claude/plan/refactor-design-python3-development.md

# 4. Execute when ready
/plugin-refactor:implement-refactor python3-development

# Tasks execute in parallel where possible

# 5. Validation runs automatically
# If issues found, follow-up tasks created and cycle repeats
```

## Related Plugins

- **plugin-dev** - Create new plugins from scratch
- **holistic-linting** - Code quality and linting workflows
- **prompt-optimization-claude-45** - Optimize AI-facing documentation

## Version

1.1.0 - Added agents, commands, and validation scripts

## Author

Jamie Hoover (<https://github.com/bitflight-devops>)

## License

MIT License
