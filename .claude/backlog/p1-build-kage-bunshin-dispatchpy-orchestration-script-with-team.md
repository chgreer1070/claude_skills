---
name: Add dispatch orchestration MCP tools with background task support to backlog server
description: "The kage-bunshin spawn.py script handles per-item process launching (worktree creation, .venv symlinking, lock file, claude -p spawn). What is missing is the orchestration layer that reads a dispatch plan, iterates waves, spawns kage-bunshins, tracks state, and collects results.\n\nThis orchestration belongs in the backlog MCP server — not a standalone script. The backlog MCP already has four dispatch DATA tools (dispatch_read, dispatch_validate, dispatch_stale_check, dispatch_conflicts). The missing piece is dispatch EXECUTION and STATE tools.\n\n## What is missing\n\n### New MCP tools on the backlog server\n\n1. `dispatch_wave_start(milestone, wave_num)` — record that a wave has started, which items are in-progress, their PIDs. Writes state to an in-memory or file-backed store.\n\n2. `dispatch_item_status(milestone, issue, status, result, error, cost)` — record item completion or failure. Called by the orchestrator after each kage-bunshin PID exits. Statuses: in-progress, complete, failed, skipped.\n\n3. `dispatch_wave_status(milestone, wave_num)` — query current wave state. Returns items in-progress, completed, failed, elapsed time per item. Any MCP client can call this to monitor progress.\n\n4. `dispatch_spawn(milestone, wave_num, max_concurrent, model, phase)` with `task=True` — the actual orchestration loop as a FastMCP background task. Reads the dispatch plan, spawns kage-bunshins (calling spawn.py per item), manages PIDs with concurrency throttle (max_concurrent, default 3), calls dispatch_item_status on each completion, reports progress via FastMCP Progress API. Phase parameter selects groom (no worktree) or work (with worktree).\n\n### FastMCP background task capabilities (verified from docs)\n\n- `@mcp.tool(task=True)` enables background execution — clients can invoke and poll\n- Progress reporting: `await progress.set_total(n)`, `await progress.increment()`, `await progress.set_message(\"Processing item #42\")`\n- In-memory backend (default): zero config, ephemeral, sufficient for single-machine use\n- Redis backend (production): `FASTMCP_DOCKET_URL=redis://localhost:6379` for persistence and horizontal scaling\n- Worker concurrency: `FASTMCP_DOCKET_CONCURRENCY=N`\n- Constraint: task tools must be async, defined at server startup\n\n### Team size control\n\n`max_concurrent` parameter on `dispatch_spawn` (default: 3). Controls how many kage-bunshin sessions run simultaneously per wave. Without this, a 10-item wave spawns 10 sessions — each costing ~$0.13+ for context loading alone (observed: haiku context load = $0.13).\n\n### Architecture\n\n```\ndispatch_spawn (MCP background task)\n  ├── reads plan/milestone-{N}-dispatch.yaml via dispatch_read\n  ├── for each wave:\n  │   ├── dispatch_wave_start(milestone, wave_num)\n  │   ├── for each item (throttled to max_concurrent):\n  │   │   ├── calls spawn.py (creates worktree, launches claude -p)\n  │   │   ├── waits for PID exit\n  │   │   ├── reads result JSON\n  │   │   └── dispatch_item_status(milestone, issue, status, result)\n  │   └── progress.set_message(\"Wave {N}: {completed}/{total} items\")\n  └── returns structured summary\n\nspawn.py (process launcher — already exists)\n  ├── creates worktree (if --worktree)\n  ├── symlinks .venv, node_modules\n  ├── writes lock file\n  ├── launches claude -p\n  └── returns PID + file paths as JSON\n```\n\nspawn.py stays as-is — it handles process-level concerns. The MCP server handles orchestration, state tracking, and progress reporting."
metadata:
  topic: build-kage-bunshin-dispatchpy-orchestration-script-with-team
  source: Session observation — kage-bunshin architecture design session 2026-03-22
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: open
  issue: '#986'
  last_synced: '2026-03-22T12:45:56Z'
  groomed: '2026-03-22'
  plan: plan/P986-dispatch-orchestration-mcp-tools.yaml
---

## Groomed (2026-03-22)





### Design Notes

<div><sub>2026-03-22T12:22:31Z</sub>
<details><summary>struck: 2026-03-22T12:45:56Z — Use ~/.dh/projects/ not ~/.claude/projects/ — .dh is our namespace, .claude belongs to Claude Code</summary>

**State backend**: SQLite (not Redis, not in-memory). A shared SQLite database at `.claude/dispatch-state.db` stores wave and item status. Reasons: (1) persistent across MCP server restarts, (2) no external infrastructure dependency, (3) sufficient for single-machine concurrency of 3-10 kage-bunshin sessions, (4) queryable from any process (spawn.py, monitoring scripts, other MCP tools). FastMCP's built-in task backends (in-memory or Redis) are for the task execution queue only — dispatch state tracking uses SQLite directly via the stdlib `sqlite3` module.
</details>
</div>

<div><sub>2026-03-22T12:25:31Z</sub>
<details><summary>struck: 2026-03-22T12:45:56Z — Use ~/.dh/projects/ not ~/.claude/projects/ — .dh is our namespace, .claude belongs to Claude Code</summary>

**State backend**: SQLite (not Redis, not in-memory). Dispatch state database stored at `.dh/dispatch-state.db` — aligned with #981 (Consolidate backlog and plan directories under .dh/). All development-harness project state is moving under `.dh/` per that item. The `.dh/` directory will contain backlog cache, plan artifacts, reports, context files, and now dispatch state. Uses stdlib `sqlite3` module — no external dependency. Sufficient for single-machine concurrency of 3-10 kage-bunshin sessions. Queryable from any process (spawn.py, monitoring scripts, other MCP tools). FastMCP's built-in task backends (in-memory or Redis) are for the task execution queue only — dispatch state tracking uses SQLite directly.

**Dependency**: This item should be sequenced after #981 lands, or at minimum use `.dh/` as the target path so the state file doesn't need to be moved later. If #981 hasn't landed yet, the MCP server should create `.dh/` on first use.
</details>
</div>

<div><sub>2026-03-22T12:33:12Z</sub>
<details><summary>struck: 2026-03-22T12:45:56Z — Use ~/.dh/projects/ not ~/.claude/projects/ — .dh is our namespace, .claude belongs to Claude Code</summary>

**State backend**: SQLite at `~/.dh/projects/{project-stub}/dispatch-state.db`. This is user-level, outside the git repo, and shared across all worktrees of the same project. Reasons: (1) worktrees each get their own in-repo directories — an in-repo DB would be invisible to spawned kage-bunshin sessions in other worktrees, (2) dispatch state is session-ephemeral coordination data, not project artifacts — it does not belong alongside backlog items and plans in `.dh/`, (3) no `.gitignore` maintenance needed. The `{project-stub}` is a unique identifier derived from the repo (e.g., repo name or path hash). Uses stdlib `sqlite3` — no external dependency. The MCP server creates `~/.dh/projects/{project-stub}/` on first use via `mkdir -p`.

**Dependency on #981**: None — this path is independent of the in-repo `.dh/` consolidation. The in-repo `.dh/` holds backlog cache and plan artifacts (project data). The user-level `~/.dh/` holds runtime state (dispatch coordination). These are orthogonal.
</details>
</div>

<div><sub>2026-03-22T12:45:13Z</sub>
<details><summary>struck: 2026-03-22T12:45:56Z — Use ~/.dh/projects/ not ~/.claude/projects/ — .dh is our namespace, .claude belongs to Claude Code</summary>

**State backend**: SQLite at `~/.claude/projects/{project-stub}/dispatch-state.db`. Follows the Claude Code convention for per-project user-level data. The `{project-stub}` is derived the same way Claude Code derives its project directory names: absolute path of the repo root with `/` replaced by `-` (e.g., `/home/user/repos/claude_skills` → `-home-user-repos-claude_skills`). This directory already exists for every project that has had a Claude Code session. Uses stdlib `sqlite3` — no external dependency for the DB itself. Shared across all worktrees of the same project (user-level, outside git). The MCP server creates the file on first `dispatch_wave_start` call.

**No dependency on #981**: This path is independent of the in-repo `.dh/` consolidation. Runtime coordination state and project artifacts are orthogonal.
</details>
</div>

<div><sub>2026-03-22T12:45:56Z</sub>

**State backend**: SQLite at `~/.dh/projects/{project-stub}/dispatch-state.db`. The `{project-stub}` follows the Claude Code naming convention: absolute path of the repo root with `/` replaced by `-` (e.g., `/home/user/repos/claude_skills` → `-home-user-repos-claude_skills`). This is under `~/.dh/` — our own namespace, not inside `~/.claude/`. User-level, outside git, shared across all worktrees of the same project. Uses stdlib `sqlite3` — no external dependency. The MCP server creates `~/.dh/projects/{project-stub}/` on first `dispatch_wave_start` call.

**No dependency on #981**: This path is independent of the in-repo `.dh/` consolidation. Runtime coordination state and project artifacts are orthogonal.
</div>