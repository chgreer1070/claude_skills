# Hooks for Subagents

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Define hooks for subagents (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/hooks.md> § SubagentStart (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/hooks.md> § SubagentStop (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/hooks.md> § Hooks in skills and agents (accessed 2026-05-28)

Two ways to configure hooks for subagents:

1. **In the subagent's frontmatter** — run only while that subagent is active
2. **In `settings.json`** — run in the main session when subagents start or stop

---

## Hooks in subagent frontmatter

Hooks defined in frontmatter are scoped to the component's lifecycle and cleaned up when the subagent finishes. All hook events are supported.

> **Fires in two contexts**: when the agent is spawned as a subagent through the Agent tool or @-mention, AND when the agent runs as the main session via `--agent` or the `agent` setting. In the main-session case they run alongside hooks from `settings.json`.

> **Plugin restriction**: The `hooks` frontmatter field is **silently ignored** for plugin-shipped agents. Copy the agent file to `.claude/agents/` or `~/.claude/agents/` to use hooks.

> **Stop hooks auto-convert**: `Stop` hooks in frontmatter are automatically converted to `SubagentStop` events at runtime when the agent runs as a subagent.

```yaml
---
name: code-reviewer
description: Review code changes with automatic linting
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

### PreToolUse with exit code 2 blocking

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Conditional rules with hooks (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/hooks.md> § Exit code 2 behavior per event (accessed 2026-05-28)

`PreToolUse` with exit code 2 blocks the tool call and feeds stderr to Claude as an error. Useful for enforcing constraints the `tools` allowlist cannot express (e.g., allow Bash but only SELECT queries):

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
```

The hook receives JSON on stdin with the field `tool_input.command`. Returning exit code 2 blocks the call. Stderr text is shown to Claude as the reason.

---

## Project-level hooks for subagent lifecycle

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Project-level hooks for subagent events (accessed 2026-05-28)

Configure in `settings.json` using the `SubagentStart` and `SubagentStop` events. These run in the **main session** when subagents start or stop.

| Event | Matcher input | When it fires |
|:------|:-------------|:--------------|
| `SubagentStart` | Agent type name | When a subagent begins execution |
| `SubagentStop` | Agent type name | When a subagent completes |

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [
          { "type": "command", "command": "./scripts/setup-db-connection.sh" }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          { "type": "command", "command": "./scripts/cleanup-db-connection.sh" }
        ]
      }
    ]
  }
}
```

---

## SubagentStart input schema

SOURCE: <https://code.claude.com/docs/en/hooks.md> § SubagentStart input (accessed 2026-05-28)

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/my-project",
  "hook_event_name": "SubagentStart",
  "agent_id": "agent-abc123",
  "agent_type": "Explore"
}
```

`SubagentStart` hooks **cannot block** subagent creation (exit code 2 shows stderr to user only). They can return `additionalContext` in `hookSpecificOutput` to inject context into the subagent:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "Follow security guidelines for this task"
  }
}
```

Matcher values: `general-purpose`, `Explore`, `Plan`, or any custom agent `name` field value.

---

## SubagentStop input schema

SOURCE: <https://code.claude.com/docs/en/hooks.md> § SubagentStop input (accessed 2026-05-28)

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/my-project",
  "permission_mode": "default",
  "hook_event_name": "SubagentStop",
  "stop_hook_active": false,
  "agent_id": "def456",
  "agent_type": "Explore",
  "agent_transcript_path": "~/.claude/projects/.../abc123/subagents/agent-def456.jsonl",
  "last_assistant_message": "Analysis complete. Found 3 potential issues...",
  "background_tasks": [],
  "session_crons": []
}
```

`agent_transcript_path` is the subagent's own transcript stored in a nested `subagents/` folder. `last_assistant_message` contains the final response text without parsing the transcript file.

`SubagentStop` uses the same decision control as `Stop` hooks: returning `decision: "block"` with a `reason` keeps the subagent running and delivers `reason` to it as its next instruction.

```json
{
  "decision": "block",
  "reason": "Tests are still failing — fix them before stopping"
}
```

To inject context into the **parent session** after a subagent returns, use a `PostToolUse` hook on the `Agent` tool instead.

---

## Hook types supported in subagent frontmatter

SOURCE: <https://code.claude.com/docs/en/hooks.md> § Prompt-based hooks (accessed 2026-05-28)

All five hook types are supported in subagent frontmatter: `command`, `http`, `mcp_tool`, `prompt`, and `agent`.

The `once: true` field on individual hook handlers is **only honored for hooks declared in skill/agent frontmatter** (ignored in settings files).
