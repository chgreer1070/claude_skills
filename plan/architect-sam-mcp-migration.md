# Architecture Spec: SAM MCP Migration

## Overview

This is a documentation-only refactor. No Python code changes. All modifications are to markdown files (agent prompts, skill instructions, workflow documentation).

## Change Categories

### Category 1: Agent Frontmatter Updates

Add SAM MCP tools to each agent's `tools:` field in YAML frontmatter. Each agent gets only the tools it actually uses.

| Agent | Tools to Add |
|---|---|
| `code-reviewer.md` | `mcp__plugin_dh_sam__sam_create` |
| `context-gathering.md` | `mcp__plugin_dh_sam__sam_read, mcp__plugin_dh_sam__sam_update` |
| `swarm-task-planner.md` | `mcp__plugin_dh_sam__sam_create` |
| `context-refinement.md` | `mcp__plugin_dh_sam__sam_read, mcp__plugin_dh_sam__sam_update` |

### Category 2: Agent Body Instruction Rewrites

Replace `uv run sam <cmd>` patterns in agent body text with MCP tool call instructions. Pattern:

**Before:**
```text
uv run sam read P{N} --format json
```

**After:**
```text
mcp__plugin_dh_sam__sam_read(address="P{N}")
```

Keep CLI as documented fallback when MCP is unavailable.

### Category 3: Skill Instruction Rewrites

Replace `uv run sam` patterns in SKILL.md files with MCP tool call instructions. Skills are read by the orchestrator which always has MCP access.

**Exception:** `implementation-manager/SKILL.md` line 13 uses `!` backtick command substitution for load-time execution. This must remain CLI.

### Category 4: Documentation Updates

Update workflow documentation to show MCP as primary interface, CLI as fallback. Three files:
- `.claude/rules/local-workflow.md`
- `plugins/development-harness/docs/workflow-architecture-diagram.md`
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md`

## Edit Pattern

For each file, the edit pattern is:

1. **Frontmatter** (agents only): Append SAM MCP tools to the `tools:` comma-separated list
2. **Body text**: Replace `uv run sam <cmd> <args>` with `mcp__plugin_dh_sam__sam_<cmd>(<params>)` syntax
3. **Fallback note**: Add a brief note that CLI (`uv run sam`) is available as fallback when MCP is unavailable

## No Python Changes

The SAM MCP server already implements all tools. The `sam` CLI already exists. This refactor only changes which interface the documentation directs agents to use.
