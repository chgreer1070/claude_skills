# Agent Teams vs Subagents

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> (accessed 2026-05-28)
SOURCE: <https://code.claude.com/docs/en/sub-agents.md> § Work with subagents > Common patterns > Run parallel research (accessed 2026-05-28)

**Status**: Experimental — disabled by default.
**Requires**: Claude Code v2.1.32+
**Enable**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

---

## When to use each

| | Subagents | Agent teams |
|:-|:----------|:------------|
| **Context** | Own context window; results return to caller | Own context window; fully independent |
| **Communication** | Report results back to main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only the result matters | Complex work requiring discussion and collaboration |
| **Token cost** | Lower | Higher — each teammate is a separate Claude instance |

**Use subagents** for quick focused tasks that report back.
**Use agent teams** when teammates need to share findings, challenge each other, and coordinate autonomously.

---

## Strongest use cases for agent teams

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § When to use agent teams (accessed 2026-05-28)

- **Research and review**: parallel investigation of different aspects, findings shared and challenged between teammates
- **New modules or features**: each teammate owns a separate piece without stepping on each other
- **Debugging with competing hypotheses**: teammates test different theories in parallel and converge faster
- **Cross-layer coordination**: changes spanning frontend, backend, and tests, each owned by a different teammate

Agent teams add coordination overhead and use significantly more tokens. They work best when teammates can operate independently. For sequential tasks, same-file edits, or work with many dependencies, a single session or subagents are more effective.

---

## Enabling agent teams

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Or in `settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## Architecture

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Architecture (accessed 2026-05-28)

| Component | Role |
|:----------|:-----|
| **Team lead** | The main Claude Code session; creates the team, spawns teammates, coordinates work |
| **Teammates** | Separate Claude Code instances, each with their own context window |
| **Task list** | Shared work items teammates claim and complete. Task claiming uses file locking to prevent race conditions |
| **Mailbox** | Messaging system for direct inter-agent communication |

Teams and tasks are stored locally:

- **Team config**: `~/.claude/teams/{team-name}/config.json` — do not edit by hand; overwritten on state updates
- **Task list**: `~/.claude/tasks/{team-name}/`

---

## Starting a team

Tell Claude to create an agent team and describe the structure you want:

```text
Create an agent team to explore this from different angles: one teammate on UX,
one on technical architecture, one playing devil's advocate.
```

Claude creates the team, spawns teammates, and coordinates work. The lead's terminal lists all teammates and their current work. Use `Shift+Down` to cycle through teammates and message them directly.

---

## Display modes

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Choose a display mode (accessed 2026-05-28)

| Mode | How to switch | Requirements |
|:-----|:-------------|:-------------|
| **In-process** (default) | `Shift+Down` to cycle teammates | Any terminal |
| **Split panes** | `teammateMode: "tmux"` in settings or `--teammate-mode tmux` | tmux or iTerm2 |

Default `"auto"`: uses split panes if already inside a tmux session, in-process otherwise.

---

## Using subagent definitions as teammates

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Use subagent definitions for teammates (accessed 2026-05-28)

Reference a subagent type by name when asking Claude to spawn a teammate:

```text
Spawn a teammate using the security-reviewer agent type to audit the auth module.
```

The teammate uses that definition's `tools` and `model`. The definition's body is appended to the teammate's system prompt as additional instructions (not replacing it). Team coordination tools (`SendMessage`, task management) are always available to teammates even when `tools` restricts other tools.

> **Note**: `skills` and `mcpServers` frontmatter fields are **not applied** when a subagent definition runs as a teammate. Teammates load skills and MCP servers from project and user settings, the same as a regular session.

---

## Team hooks

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Enforce quality gates with hooks (accessed 2026-05-28)

| Event | When it fires | Exit code 2 effect |
|:------|:-------------|:-------------------|
| `TeammateIdle` | Teammate about to go idle | Teammate receives stderr as feedback, keeps working |
| `TaskCreated` | Task being created via `TaskCreate` | Rolls back task creation |
| `TaskCompleted` | Task being marked complete | Prevents completion |

For `TeammateIdle` and `TaskCompleted`, return `{"continue": false, "stopReason": "..."}` to stop the teammate entirely (same as `Stop` hook behavior).

---

## Best practices

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Best practices (accessed 2026-05-28)

**Team size**: 3–5 teammates optimal. Token costs scale linearly — each teammate is a separate Claude instance. Beyond ~5 teammates, coordination overhead increases with diminishing returns.

**Tasks per teammate**: 5–6 tasks per teammate keeps everyone productive without excessive context switching.

**Avoid file conflicts**: break work so each teammate owns a different set of files.

**Give teammates enough context**: teammates load project context (CLAUDE.md, MCP servers, skills) automatically but don't inherit the lead's conversation history. Include task-specific details in the spawn prompt.

**Monitor and steer**: check in on teammates' progress, redirect approaches that aren't working, and synthesize findings as they come in.

---

## Cleaning up

```text
Clean up the team
```

The lead checks for active teammates and fails if any are still running — shut them down first. Always use the lead to clean up; teammates should not run cleanup.

---

## Known limitations

SOURCE: <https://code.claude.com/docs/en/agent-teams.md> § Limitations (accessed 2026-05-28)

- No session resumption with in-process teammates (`/resume` and `/rewind` do not restore in-process teammates)
- Task status can lag — teammates sometimes fail to mark tasks complete
- Shutdown can be slow — finishes current request/tool call first
- One team at a time per lead
- No nested teams — teammates cannot spawn their own teams
- Lead is fixed for the team's lifetime — no leadership transfer
- Permissions set at spawn — cannot set per-teammate modes before spawning
- Split panes require tmux or iTerm2 (not supported in VS Code integrated terminal, Windows Terminal, or Ghostty)
