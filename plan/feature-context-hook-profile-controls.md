# Feature Context: Hook Runtime Profile Controls

**Source**: GitHub Issue #577
**Research reference**: `./research/agent-frameworks/everything-claude-code.md` (ECC_HOOK_PROFILE pattern)

---

## Problem Statement

`task_status_hook.py` executes unconditionally on every matching hook event. There is no mechanism to:

1. **Disable individual hooks** without editing SKILL.md frontmatter directly
2. **Reduce hook frequency** (e.g., skip PostToolUse LastActivity updates that fire on every Write/Edit/Bash call)
3. **Set a profile level** that adjusts hook behavior to match the session's needs

The only current control is binary: the hook is declared in SKILL.md frontmatter, or it is not. Users who want to reduce hook overhead during rapid iteration, or add stricter validation during critical work, must manually edit two separate SKILL.md files (`start-task/SKILL.md` and `implement-feature/SKILL.md`), then revert those edits afterward.

---

## Current Behavior (Observed)

### Hook declarations

**`start-task/SKILL.md`** declares a PostToolUse hook with matcher `Write|Edit|Bash`:

```yaml
hooks:
  PostToolUse:
  - matcher: Write|Edit|Bash
    hooks:
    - type: command
      command: python3 "${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py"
```

**`implement-feature/SKILL.md`** declares a SubagentStop hook (no matcher, fires on all SubagentStop events):

```yaml
hooks:
  SubagentStop:
  - hooks:
    - type: command
      command: python3 "${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py"
```

Both invoke the same script: `task_status_hook.py`.

### Script dispatch logic

`task_status_hook.py` reads `hook_event_name` from stdin JSON and dispatches:

- `SubagentStop` -> `handle_subagent_stop()`: marks task COMPLETE, adds Completed timestamp, deletes context file, syncs to GitHub
- `PostToolUse` (Write|Edit|Bash) -> `handle_activity_update()`: reads context file, updates `last-activity` timestamp via `sam_update_plan_fields`

There is no environment variable check, no profile branching, and no early-exit path based on configuration. Every invocation runs the full handler for its event type.

### Execution frequency

The PostToolUse hook fires on **every** Write, Edit, or Bash tool call during task execution. For a typical task with 30-50 tool calls, this means 30-50 invocations of `task_status_hook.py`, each performing:
1. stdin JSON parse
2. Context file read
3. sam_schema task lookup (to check if already COMPLETE)
4. Timestamp update via `sam_update_plan_fields` (file read + write)

The SubagentStop hook fires once per delegated task (low frequency, high importance).

---

## Desired Outcome

Two environment variables control hook behavior at runtime, without any SKILL.md edits:

### `CLAUDE_SKILLS_HOOK_PROFILE`

Three levels:

| Profile | PostToolUse (LastActivity) | SubagentStop (Completion) | Additional validation |
|---------|---------------------------|---------------------------|----------------------|
| `minimal` | Skipped (exit 0 immediately) | Runs normally | None |
| `standard` | Runs normally (current behavior) | Runs normally | None |
| `strict` | Runs normally | Runs normally | Additional checks run (e.g., verify task was claimed before completing, validate acceptance criteria fields exist) |

Default when unset: `standard` (preserves current behavior exactly).

### `CLAUDE_SKILLS_DISABLED_HOOKS`

Comma-separated list of hook IDs that exit immediately with code 0 when matched. Hook IDs correspond to the handler functions:

- `task-status:post-tool-use` — disables the PostToolUse/LastActivity handler
- `task-status:subagent-stop` — disables the SubagentStop/completion handler

This provides granular per-handler disablement independent of profile level.

### What "done" looks like

- Setting `CLAUDE_SKILLS_HOOK_PROFILE=minimal` before running `/implement-feature` eliminates all PostToolUse file I/O during task execution, reducing hook overhead to near zero for rapid iteration sessions
- Setting `CLAUDE_SKILLS_HOOK_PROFILE=strict` adds validation guardrails for critical implementations
- Setting `CLAUDE_SKILLS_DISABLED_HOOKS=task-status:subagent-stop` disables automatic completion marking (useful when debugging task status issues)
- Unsetting both variables produces identical behavior to the current codebase — zero behavioral change for existing users
- No SKILL.md files are modified; all control is via environment variables read by the script at runtime

---

## Environment Constraints

1. **Exit code 0 required for disabled/skipped hooks** — Claude Code hooks treat non-zero exit as an error. Disabled or profile-skipped hooks must exit 0, not error.
2. **stdin must still be consumed** — even when skipping, the script receives JSON on stdin. Failing to read stdin may cause pipe errors in the parent process.
3. **No SKILL.md changes** — the feature is entirely within `task_status_hook.py`. The hook declarations in SKILL.md frontmatter remain unchanged.
4. **sam_schema dependency** — the script imports from `sam_schema` at module level. Profile/disable checks should run before sam_schema operations but after stdin parsing (to know the event name).
5. **Backward compatibility** — when neither env var is set, behavior must be identical to the current implementation. No new defaults that change existing behavior.

---

## ECC Pattern Reference

The Everything Claude Code (ECC) framework implements an analogous pattern:

```bash
export ECC_HOOK_PROFILE=standard    # or: minimal, strict
export ECC_DISABLED_HOOKS="pre:bash:tmux-reminder,post:edit:typecheck"
```

ECC uses colon-separated hook IDs (`pre:bash:tmux-reminder`). The proposed `CLAUDE_SKILLS_DISABLED_HOOKS` follows the same convention adapted to this repo's hook structure: `task-status:post-tool-use` identifies the script (`task-status`) and the handler (`post-tool-use`).

SOURCE: `./research/agent-frameworks/everything-claude-code.md` lines 159-160, 281-284 (accessed 2026-03-21)

---

## Questions for Resolution

1. **Strict profile scope**: What specific validation checks should `strict` mode add? Candidates: verify task was claimed via `sam_claim` before marking complete, verify acceptance criteria fields are non-empty, verify dependencies are all COMPLETE before allowing completion. The feature request mentions "additional validation checks" without specifying which ones.

2. **Logging on skip**: When a hook is skipped (minimal profile or disabled), should it print a stderr message (e.g., `[hook] Skipped: PostToolUse (profile=minimal)`) or exit completely silently? Stderr messages are visible to Claude but do not affect hook success/failure.

3. **Hook ID namespace**: The proposed IDs (`task-status:post-tool-use`, `task-status:subagent-stop`) assume a `script:handler` convention. If other hook scripts are added in the future, should the namespace be formalized now (e.g., documented in a reference file), or is the convention sufficient as an implicit standard?
