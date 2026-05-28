# Fork Mode (Experimental)

SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Fork the current conversation (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/env-vars.md> — `CLAUDE_CODE_FORK_SUBAGENT` entry (accessed 2026-05-28)

**Status**: Experimental. Requires Claude Code v2.1.117 or later.
**Enable**: `CLAUDE_CODE_FORK_SUBAGENT=1`

---

## What a fork is

A fork is a subagent that inherits the **entire conversation so far** instead of starting fresh. It sees the same system prompt, tools, model, and message history as the main session.

- Fork's own tool calls stay out of your conversation
- Only its final result comes back to the main context
- Your main context window stays clean

Use a fork when a named subagent would need too much background context to be useful, or when you want to try several approaches in parallel from the same starting point.

---

## Enabling fork mode

```bash
export CLAUDE_CODE_FORK_SUBAGENT=1
```

Or in `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_FORK_SUBAGENT": "1"
  }
}
```

Works in interactive mode, non-interactive mode (`-p`), and the Agent SDK.

---

## What changes when fork mode is enabled

Three behaviors change:

1. **general-purpose becomes a fork**: Claude spawns a fork whenever it would otherwise use the `general-purpose` built-in subagent. Named subagents (Explore, Plan, custom agents) spawn as before.
2. **All subagent spawns run in the background**: Both forks and named subagents run in the background regardless of the `background` frontmatter field. Forks still surface permission prompts in your terminal; named subagents auto-deny anything that would prompt.
3. **`/fork` command spawns a fork**: Instead of acting as an alias for `/branch`, `/fork` spawns a fork with the directive you provide.

---

## /fork command

```text
/fork draft unit tests for the parser changes so far
```

Claude Code names the fork from the first words of the directive. The fork appears in a panel below your prompt and runs in the background while you continue working. When it finishes, its result arrives as a message in your main conversation.

---

## Observe and steer running forks

Running forks appear in a panel below the prompt input, with one row for the main session and one for each fork.

| Key | Action |
|:----|:-------|
| `↑` / `↓` | Move between rows |
| `Enter` | Open the selected fork's transcript; send follow-up messages |
| `x` | Dismiss a finished fork or stop a running one |
| `Esc` | Return focus to the prompt input |

---

## Forks vs named subagents

| | Fork | Named subagent |
|:-|:-----|:---------------|
| Context | Full conversation history inherited | Fresh context with the delegation prompt |
| System prompt and tools | Same as main session | From the subagent's definition file |
| Model | Same as main session | From the subagent's `model` field |
| Permissions | Prompts surface in your terminal | Auto-denied when running in background |
| Prompt cache | **Shared with main session** (cheaper) | Separate cache |

Because a fork's system prompt and tool definitions are identical to the parent, its first request reuses the parent's prompt cache — making forking cheaper than spawning a fresh subagent for tasks needing the same context.

When Claude spawns a fork through the Agent tool, it can pass `isolation: "worktree"` so the fork's file edits go to a separate git worktree instead of your checkout.

---

## Limitations

- A fork cannot spawn further forks
- To keep spawns synchronous, set `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` alongside fork mode
