# JSONL Schema Reference

Complete record type schemas for Claude Code session transcripts.

## Common Fields (All Records)

Every record with session context carries:

```json
{
  "type": "...",
  "uuid": "<message-uuid>",
  "parentUuid": "<parent-uuid | null>",
  "timestamp": "2026-01-30T16:39:40.005Z",
  "sessionId": "<session-uuid>",
  "cwd": "/home/user/repos/project",
  "version": "2.1.25",
  "gitBranch": "main",
  "isSidechain": false,
  "userType": "external",
  "slug": "squishy-discovering-breeze"
}
```

Subagent-specific additions:

```json
{
  "agentId": "a0ec468",
  "isSidechain": true,
  "agentName": "external-researcher",
  "teamName": "kaizen-scoping"
}
```

## Record Type: `user`

Human input or tool result.

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "<string> | [{type, text}] | [{type: tool_result, tool_use_id, content, is_error}]"
  },
  "toolUseResult": true,
  "sourceToolAssistantUUID": "...",
  "uuid": "...",
  "parentUuid": "..."
}
```

Tool result content structure:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01...",
  "content": [{"type": "text", "text": "..."}],
  "is_error": false
}
```

## Record Type: `assistant`

LLM response turn.

```json
{
  "type": "assistant",
  "requestId": "req_011CYEpNE8U6bRtNVbuJBjaW",
  "message": {
    "id": "msg_018oRhgn7XnKrXg9DKBiKsvS",
    "model": "claude-sonnet-4-6",
    "role": "assistant",
    "type": "message",
    "stop_reason": "tool_use | end_turn | stop_sequence | null",
    "content": [
      {"type": "text", "text": "..."},
      {
        "type": "tool_use",
        "id": "toolu_01...",
        "name": "Bash",
        "input": {"command": "..."},
        "caller": {"type": "direct"}
      }
    ],
    "usage": {
      "input_tokens": 1234,
      "output_tokens": 567,
      "cache_creation_input_tokens": 49394,
      "cache_read_input_tokens": 0,
      "service_tier": "standard"
    }
  },
  "error": "billing_error"
}
```

## Record Type: `progress`

Two subtypes via `data.type`:

### `hook_progress`

```json
{
  "type": "progress",
  "data": {
    "type": "hook_progress",
    "hookEvent": "SessionStart",
    "hookName": "SessionStart:startup",
    "command": "node \"/path/to/hook.js\""
  },
  "parentToolUseID": "...",
  "toolUseID": "..."
}
```

### `agent_progress`

```json
{
  "type": "progress",
  "data": {
    "type": "agent_progress",
    "message": {
      "type": "user | assistant",
      "timestamp": "...",
      "message": {}
    }
  }
}
```

## Record Type: `system`

Metadata events discriminated by `subtype`:

### `stop_hook_summary`

```json
{
  "type": "system",
  "subtype": "stop_hook_summary",
  "hookCount": 3,
  "hookInfos": [{"command": "node ..."}],
  "hookErrors": [],
  "preventedContinuation": false,
  "stopReason": "",
  "hasOutput": true,
  "level": "suggestion",
  "toolUseID": "..."
}
```

### `turn_duration`

```json
{
  "type": "system",
  "subtype": "turn_duration",
  "durationMs": 12500,
  "isMeta": true
}
```

### `api_error`

```json
{
  "type": "system",
  "subtype": "api_error",
  "level": "error",
  "cause": {"code": "ConnectionRefused", "path": "https://api.anthropic.com/...", "errno": 0},
  "retryInMs": 595.8,
  "retryAttempt": 1,
  "maxRetries": 10
}
```

### `compact_boundary`

```json
{
  "type": "system",
  "subtype": "compact_boundary",
  "content": "Conversation compacted",
  "logicalParentUuid": "...",
  "isMeta": false
}
```

### `local_command`

```json
{
  "type": "system",
  "subtype": "local_command",
  "content": "<command-name>/clear</command-name>\n<command-message>clear</command-message>",
  "level": "info"
}
```

## Record Type: `file-history-snapshot`

```json
{
  "type": "file-history-snapshot",
  "messageId": "...",
  "snapshot": {
    "messageId": "...",
    "trackedFileBackups": {
      ".claude/skills/rt-ica/SKILL.md": {
        "backupFileName": "fce4cdb71d269c08@v1",
        "version": 1,
        "backupTime": "2026-01-27T18:04:22.616Z"
      }
    },
    "timestamp": "..."
  },
  "isSnapshotUpdate": false
}
```

## Record Type: `queue-operation`

```json
{
  "type": "queue-operation",
  "operation": "enqueue | dequeue",
  "timestamp": "...",
  "sessionId": "...",
  "content": "[string or json payload]"
}
```

## Record Type: `summary`

```json
{
  "type": "summary",
  "summary": "Credit balance insufficient error loop",
  "leafUuid": "..."
}
```

## Tool Call Schema

Tool use blocks appear inside `assistant.message.content[]`:

```json
{
  "type": "tool_use",
  "id": "toolu_01...",
  "name": "Bash",
  "input": {"command": "git status", "description": "Show working tree status"},
  "caller": {"type": "direct"}
}
```

Tool inputs by tool name:

- **Bash** — `{"command": "...", "description": "..."}`
- **Read** — `{"file_path": "...", "limit": N, "offset": N}`
- **Edit** — `{"file_path": "...", "old_string": "...", "new_string": "..."}`
- **Write** — `{"file_path": "...", "content": "..."}`
- **Grep** — `{"pattern": "...", "path": "...", "output_mode": "content|files_with_matches"}`
- **Glob** — `{"pattern": "...", "path": "..."}`
- **Task** — `{"description": "...", "subagent_type": "...", "prompt": "...", "run_in_background": true, "team_name": "...", "name": "...", "model": "..."}`
- **Skill** — `{"skill": "...", "args": "..."}`

## Subagent Relationship Model

<eg>
Main session JSONL (orchestrator)
└── Task tool_use (id: toolu_01X)
     └── tool_result → "agentId: abc1234"
          └── Subagent at: {session-uuid}/subagents/agent-abc1234.jsonl
               └── Records with isSidechain: true, agentId: abc1234
</eg>

Async agent flow:

1. Orchestrator calls `Task` with `run_in_background: true`
2. Tool result contains agentId and output_file path
3. Orchestrator polls with `TaskOutput`
4. Full output stored in `{session-dir}/tool-results/{task-tool-use-id}.txt`

SOURCE: Empirical analysis of 720 JSONL files from claude-skills project (2026-02-18)
