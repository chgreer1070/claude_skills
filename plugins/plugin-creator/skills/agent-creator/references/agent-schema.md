# Agent Frontmatter Schema Reference

> **Canonical source**: Load `/plugin-creator:claude-subagent-reference` for the complete
> field specification (all 16 fields with descriptions, env vars, and examples).
>
> This file contains creation-specific additions not covered by that reference.

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> (accessed 2026-05-28)

---

## Creation-specific constraints

These points are not in the canonical reference but matter during authoring:

### YAML multiline indicator bug

Do NOT use YAML multiline indicators (`>-`, `|`, `|-`, `>`) for `description`. Claude Code's
indexer does not parse them correctly — the description displays as the literal `>-` characters
instead of the content.

```yaml
# WRONG — displays as ">-"
description: >-
  This agent reviews code for quality issues.

# CORRECT — single-line string
description: 'This agent reviews code for quality issues.'
```

### MCP tool name casing

MCP tools must be listed by their exact registered name, case-sensitive. Wildcards and wrong
case fail silently — the agent receives no MCP tools and hallucination ensues.

```yaml
# CORRECT
tools: Read, mcp__Ref__ref_read_url

# WRONG — wildcard fails silently
tools: Read, mcp__Ref__*

# WRONG — wrong case fails silently
tools: Read, mcp__ref__ref_read_url
```

Verified via controlled experiment 2026-03-22.

### Plugin agent field restrictions

`permissionMode`, `hooks`, and `mcpServers` are **silently ignored** when the agent file is
shipped inside a plugin (`plugins/*/agents/`). Copy the agent to `.claude/agents/` or
`~/.claude/agents/` to use these fields.

`isolation: worktree` is supported in plugin agents — it is the only `isolation` value.

For the full plugin agent integration rules (auto-discovery, `agents` key override-on-declare
risk, validation commands), see `/plugin-creator:claude-plugins-reference-2026`.

---

## Validation

```bash
# Validate single agent file
uvx skilllint@latest check path/to/agent.md

# Auto-fix common issues (YAML arrays → comma-separated strings, etc.)
uvx skilllint@latest check --fix path/to/agent.md

# Validate full plugin (when agent is inside a plugin)
claude plugin validate path/to/plugin/
```
