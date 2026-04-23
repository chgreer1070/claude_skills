# Hook Events — Complete Reference

All events available for hooks in Claude Code plugins.

SOURCE: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) lines 211-265 (accessed 2026-04-23)

---

## Tool Lifecycle Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `PreToolUse` | Before Claude uses any tool | Can block tool execution |
| `PostToolUse` | After Claude successfully uses any tool | `matcher` field filters by tool name |
| `PostToolUseFailure` | After a tool execution fails | |

## Permission Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `PermissionRequest` | When a permission dialog is shown | Can approve/deny |
| `PermissionDenied` | After a permission dialog is denied | Can return `{"retry": true}` to re-prompt |

## User Interaction Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `UserPromptSubmit` | When user submits a prompt | |
| `UserPromptExpansion` | When a user-typed slash command expands into a full prompt | Can block expansion |

## Session Lifecycle Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `SessionStart` | At the beginning of a session | |
| `SessionEnd` | At the end of a session | |
| `Stop` | When Claude attempts to stop | Can block stop |

## Subagent Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `SubagentStart` | When a subagent is started | |
| `SubagentStop` | When a subagent attempts to stop | Can block stop |

## Task Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `TaskCreated` | When a task is created via TaskCreate | |
| `TaskCompleted` | When a task is marked completed | |
| `TeammateIdle` | When an agent team teammate is about to go idle | |

## Context and Configuration Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `InstructionsLoaded` | When `CLAUDE.md` or `.claude/rules/*.md` is loaded | |
| `ConfigChange` | When a configuration file changes during a session | |
| `CwdChanged` | When the working directory changes | |
| `FileChanged` | When a watched file changes | `matcher` field specifies filenames to watch |

## Compaction Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `PreCompact` | Before context compaction | |
| `PostCompact` | After context compaction | |

## Worktree Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `WorktreeCreate` | When a worktree is created via `--worktree` or agent `isolation: "worktree"` | |
| `WorktreeRemove` | When a worktree is removed | |

## Notification Event

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `Notification` | When Claude Code sends a notification | |

## MCP Elicitation Events

| Event | When it fires | Notes |
| ----- | ------------- | ----- |
| `Elicitation` | When an MCP server requests user input | |
| `ElicitationResult` | After a user responds to an MCP elicitation | |

---

## Hook Types

| Type | Description |
| ---- | ----------- |
| `command` | Execute a shell command or script. Receives event JSON via stdin. |
| `prompt` | Evaluate a prompt with an LLM. Uses `$ARGUMENTS` placeholder for event context. |
| `agent` | Run an agentic verifier with full tool access for complex verification tasks. |
| `http` | Send event JSON as an HTTP POST to a URL (webhook integration). |

SOURCE: [Plugins Reference](https://code.claude.com/docs/en/plugins-reference.md) line 254 (accessed 2026-04-23)

---

## Matcher Field

The `matcher` field on a hook group filters which tool calls or files trigger the hook.

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
        }
      ]
    }
  ],
  "FileChanged": [
    {
      "matcher": "*.ts",
      "hooks": [
        {
          "type": "command",
          "command": "${CLAUDE_PLUGIN_ROOT}/scripts/typecheck.sh"
        }
      ]
    }
  ]
}
```

For `FileChanged`, `matcher` specifies filename patterns to watch. For tool hooks, it filters by tool name using pipe-separated alternatives.
