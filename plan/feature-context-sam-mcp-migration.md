# Feature Context: Replace uv run sam CLI with SAM MCP Tool Calls

## Problem Statement

The workflow skills (implement-feature, start-task, complete-implementation, implementation-manager) and their associated agents (code-reviewer, context-gathering, swarm-task-planner, context-refinement) instruct the orchestrator to run `uv run sam` CLI commands via Bash and pass the output to agents. This creates two inefficiencies:

1. **Context waste** — CLI output is captured by the orchestrator, consuming context window tokens that could be used for other work.
2. **Unnecessary intermediary** — The orchestrator acts as a middleman between agents and SAM data. Agents with MCP access can call SAM tools directly.

## Desired Outcome

- Agents call `mcp__plugin_dh_sam__*` MCP tools directly instead of relying on orchestrator-fetched CLI output
- Agent frontmatter `tools:` fields include the specific SAM MCP tools each agent needs
- Skill instructions tell agents to use MCP tools as primary interface
- CLI (`uv run sam`) becomes fallback-only for when MCP is unavailable
- Documentation reflects MCP-first approach

## CLI-to-MCP Mapping

Verified from `plugins/development-harness/docs/TASK_FILE_FORMAT.md` lines 55-62:

| CLI Command | MCP Tool |
|---|---|
| `uv run sam list` | `mcp__plugin_dh_sam__sam_list` |
| `uv run sam create` | `mcp__plugin_dh_sam__sam_create` |
| `uv run sam read` | `mcp__plugin_dh_sam__sam_read` |
| `uv run sam update` | `mcp__plugin_dh_sam__sam_update` |
| `uv run sam claim` | `mcp__plugin_dh_sam__sam_claim` |
| `uv run sam state` | `mcp__plugin_dh_sam__sam_state` |
| `uv run sam ready` | `mcp__plugin_dh_sam__sam_ready` |
| `uv run sam status` | `mcp__plugin_dh_sam__sam_status` |

## Constraints

1. `implementation-manager/SKILL.md` line 13 uses `!` backtick command substitution at skill load time. MCP tools cannot be called at load time — this must remain CLI with a comment.
2. CLI is retained as fallback, not removed.
3. Each agent gets only the specific MCP tools it uses, not all 8.

## Source

GitHub Issue #967. User observation during #933 implementation — agents should use MCP directly, not orchestrator-fetched CLI output.
