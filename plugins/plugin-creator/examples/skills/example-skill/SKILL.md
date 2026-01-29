---
description: Demonstrates all available skill frontmatter fields. Use when you need a reference for skill configuration, when learning about skill capabilities, or when creating new skills from scratch.
argument-hint: '[topic]'
allowed-tools: Read, Grep, Glob, WebFetch
model: sonnet
user-invocable: true
disable-model-invocation: false
hooks:
  PostToolUse:
  - matcher: Read
    hooks:
    - type: command
      command: echo 'File was read'
      timeout: 5
---

# Example Skill

This skill demonstrates all available frontmatter fields for Claude Code skills.

## Purpose

Use this as a reference when creating new skills. All fields shown above are valid skill frontmatter options.

## Field Descriptions

| Field                      | Type    | Purpose                          | Constraints                     | Default         |
| -------------------------- | ------- | -------------------------------- | ------------------------------- | --------------- |
| `name`                     | string  | Display name                     | kebab-case, lowercase           | directory name  |
| `description`              | string  | When to load this skill          | Must include trigger keywords   | first paragraph |
| `argument-hint`            | string  | Autocomplete hint for `/` menu   | Brief hint text                 | none            |
| `allowed-tools`            | string  | Tools without permission prompts | Comma-separated tool names      | none            |
| `model`                    | string  | Model when skill is active       | sonnet, opus, haiku, or inherit | inherit         |
| `user-invocable`           | boolean | Show in `/` menu                 | true or false                   | true            |
| `disable-model-invocation` | boolean | Prevent Claude auto-loading      | true or false                   | false           |
| `hooks`                    | object  | Scoped hooks for skill lifecycle | Valid hook configuration object | none            |

**Note:** The fields `context` and `agent` are deprecated and not documented in the official Skills reference as of January 2026.

## Validation

Validate your skill using:

```bash
# Frontmatter validation
uv run plugins/plugin-creator/scripts/validate_frontmatter.py validate ./path/to/skill/SKILL.md

# Structure validation (checks line count, links, references)
plugins/plugin-creator/scripts/validate-skill-structure.sh ./path/to/skill/

# Plugin validation (if skill is part of a plugin)
claude plugin validate ./path/to/plugin/
```

## Common Validation Errors

| Error                                  | Cause                         | Fix                              |
| -------------------------------------- | ----------------------------- | -------------------------------- |
| `allowed-tools must be string`         | Used YAML array format        | Change to comma-separated string |
| `model must be sonnet/opus/haiku`      | Invalid model name            | Use valid model identifier       |
| `YAML array detected`                  | Used `- Tool1` format         | Change to `Tool1, Tool2` format  |
| `Skill body exceeds 500 lines`         | Skill is too large            | Split into multiple skills       |
| `Internal link points to missing file` | Referenced file doesn't exist | Create file or fix path          |
| `Description too short`                | Less than 20 characters       | Add trigger keywords and context |

## Usage

This skill is for demonstration purposes only. When creating real skills, include only the fields you need.

## Skill Location

Skills can be located in:

- **User-level:** `~/.claude/skills/skill-name/SKILL.md` - Available across all projects
- **Project-level:** `.claude/skills/skill-name/SKILL.md` - Version controlled, team shared
- **Plugin:** `plugins/plugin-name/skills/skill-name/SKILL.md` - Bundled in a plugin

## Sources

- [Skills Reference](https://code.claude.com/docs/en/skills.md) (accessed 2026-01-28)
- [Skills Overview](./plugins/plugin-creator/skills/claude-skills-overview-2026/SKILL.md) - Complete reference
- [Plugin Creator Validation Scripts](./plugins/plugin-creator/scripts/README.md)
