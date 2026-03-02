# saga-mcp

**Research Date**: 2026-03-02
**Source URL**: <https://github.com/spranab/saga-mcp>
**GitHub Repository**: <https://github.com/spranab/saga-mcp>
**npm Package**: <https://www.npmjs.com/package/saga-mcp>
**Version at Research**: v1.5.3
**License**: MIT

---

## Overview

saga-mcp is a Jira-like project tracker MCP server for AI agents. It provides a SQLite-backed, per-project-scoped database with full hierarchy (Projects > Epics > Tasks > Subtasks), activity logging, task dependencies, and a dashboard tool — all accessible through 31 MCP tools. It enables LLMs to maintain structured project state across sessions without relying on scattered markdown files.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| AI agents lose task state between sessions | Persistent SQLite database per project stores all entities and activity across sessions |
| No structured task hierarchy for agents | Full 4-level hierarchy: Projects > Epics > Tasks > Subtasks with cascade deletes |
| Task ordering and blocking is implicit | Explicit `task_dependencies` table with auto-block/unblock when dependency status changes |
| Context loss in long agent conversations | `tracker_session_diff` tool surfaces only what changed since a given timestamp |
| Repeated boilerplate task setup | Templates with `{variable}` substitution allow reusable task sets across projects |
| No searchable decision trail for agents | Typed notes system (decision, context, blocker, technical, etc.) with full-text search |
| No audit trail for LLM mutations | Immutable activity log records every create/update/delete with old and new values |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| GitHub Stars | 11 | 2026-03-02 |
| npm Downloads/month | 830 | 2026-03-02 |
| Forks | 2 | 2026-03-02 |
| Contributors | 1 | 2026-03-02 |
| Latest Release | v1.5.3 | 2026-03-02 |
| Open Issues | 2 | 2026-03-02 |
| Repository Created | 2026-02-21 | 2026-03-02 |

---

## Key Features

### Task Hierarchy and Dependencies

- 4-level hierarchy: Projects > Epics > Tasks > Subtasks enforced by SQLite foreign keys with CASCADE deletes
- Task dependency graph via `task_dependencies` junction table — any task can declare `depends_on: [id, ...]`
- Automatic block/unblock: when a dependency task status changes to `done`, downstream tasks are re-evaluated and auto-unblocked to `todo` if all deps are met
- Status enum for tasks: `todo | in_progress | review | done | blocked`
- Priority enum: `low | medium | high | critical` on both epics and tasks

### MCP Tool Surface (31 tools)

- All 31 tools carry MCP safety annotations: `readOnly`, `idempotent`, `destructive`
- Tool groups: Getting Started (2), Projects (3), Epics (3), Tasks (5), Subtasks (3), Comments (2), Templates (4), Notes (4), Intelligence (3), Import/Export (2)
- Batch operations: `subtask_create` and `task_batch_update` accept arrays to reduce tool call round-trips
- `tracker_dashboard` returns a full project overview with a natural language summary in a single call

### Session Continuity

- `tracker_session_diff` accepts a timestamp and returns only entities modified since then — designed to be called at the start of each agent session
- Activity log records every mutation with entity type, entity ID, field name, old value, new value, and summary string
- Comments thread persists across sessions on each task: `comment_add` / `comment_list`

### Notes System

- Eight typed note categories: `general | decision | context | meeting | technical | blocker | progress | release`
- `note_save` uses upsert semantics — same note can be updated idempotently
- `note_search` provides full-text search across all notes in the project

### Templates

- Templates store task definitions with `{variable}` placeholders in titles
- `template_apply` performs variable substitution at create time: `{ "feature": "user auth" }` → "Design user auth API"
- Templates are stored in the database and listed/deleted via dedicated tools

### Import/Export and Source References

- `tracker_export` serializes the full project hierarchy including task dependencies and comments to nested JSON
- `tracker_import` restores from that JSON format — enables project backup and migration
- Tasks carry a `source_ref` field for linking a task to a specific code location (file path, line, symbol)

### Storage Architecture

- Single `.tracker.db` SQLite file per project — path specified via `DB_PATH` environment variable
- Schema auto-created on first use: no migration step, no external database, no API keys
- `estimated_hours` and `actual_hours` fields on tasks; actual hours computed from activity log timestamps
- Tags stored as JSON arrays in TEXT columns; metadata as JSON objects for extensibility

---

## Technical Architecture

saga-mcp is a TypeScript Node.js MCP server using the `stdio` transport. It depends on two packages: `@modelcontextprotocol/sdk ^1.26.0` for the MCP protocol implementation and `better-sqlite3 ^12.6.0` for synchronous SQLite access.

```text
Client (Claude Code / Claude Desktop)
    |
    | stdio (MCP protocol)
    v
saga-mcp (Node.js process)
    |-- src/index.ts         -- MCP server init, tool registration
    |-- src/schema.ts        -- SCHEMA_SQL constant, all CREATE TABLE statements
    |-- src/db.ts            -- Database initialization, connection management
    |-- src/types.ts         -- TypeScript type definitions
    |-- src/tools/
    |   |-- projects.ts      -- project_create, project_list, project_update
    |   |-- epics.ts         -- epic_create, epic_list, epic_update
    |   |-- tasks.ts         -- task_create, task_list, task_get, task_update, task_batch_update
    |   |-- subtasks.ts      -- subtask_create, subtask_update, subtask_delete
    |   |-- comments.ts      -- comment_add, comment_list
    |   |-- templates.ts     -- template_create, template_list, template_apply, template_delete
    |   |-- notes.ts         -- note_save, note_list, note_search, note_delete
    |   |-- activity.ts      -- activity_log, tracker_session_diff
    |   |-- dashboard.ts     -- tracker_dashboard
    |   |-- search.ts        -- tracker_search
    |   `-- export-import.ts -- tracker_export, tracker_import
    `-- src/helpers/         -- shared utilities
```

Database schema tables (from `src/schema.ts`):

- `projects` — id, name, description, status (`active|on_hold|completed|archived`), tags (JSON), metadata (JSON)
- `epics` — id, project_id (FK), name, description, status, priority, sort_order, tags, metadata
- `tasks` — id, epic_id (FK), title, description, status, priority, sort_order, assigned_to, estimated_hours, actual_hours, due_date, source_ref, tags, metadata
- `subtasks` — id, task_id (FK), title, status (`todo|in_progress|done`), sort_order
- `task_dependencies` — junction table: task_id + depends_on_task_id (composite PK)
- `comments` — id, task_id (FK), author, content, created_at
- `notes` — id, project_id (FK), type (8 variants), title, content, created_at, updated_at
- `templates` — id, name, description, tasks (JSON array), created_at
- `activity_log` — id, entity_type, entity_id, action, field_name, old_value, new_value, summary, created_at

---

## Installation & Usage

### With Claude Code (`.mcp.json`)

```json
{
  "mcpServers": {
    "saga": {
      "command": "npx",
      "args": ["-y", "saga-mcp"],
      "env": {
        "DB_PATH": "/absolute/path/to/your/project/.tracker.db"
      }
    }
  }
}
```

### With Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "saga": {
      "command": "npx",
      "args": ["-y", "saga-mcp"],
      "env": {
        "DB_PATH": "/absolute/path/to/your/project/.tracker.db"
      }
    }
  }
}
```

### Global install and manual start

```bash
npm install -g saga-mcp
DB_PATH=./my-project/.tracker.db saga-mcp
```

### Development setup

```bash
git clone https://github.com/spranab/saga-mcp.git
cd saga-mcp
npm install
npm run build
DB_PATH=./test.db npm start
```

### Example agent tool calls

```javascript
// Initialize and create project
tracker_init({ project_name: "E-Commerce API", project_description: "REST API" })

// Create epic with tasks and dependencies
epic_create({ project_id: 1, name: "Authentication", priority: "high" })
task_create({ epic_id: 1, title: "Design auth schema", priority: "critical" })
task_create({ epic_id: 1, title: "Implement JWT", priority: "high", depends_on: [1] })

// Session resume — get only what changed since last session
tracker_session_diff({ since: "2026-03-01T09:00:00" })

// Full project overview in one call
tracker_dashboard({})
```

---

## Relevance to Claude Code Development

### Applications

- Drop-in task tracker for Claude Code sessions that need to manage multi-task projects without external services — the `.tracker.db` file lives in the project directory alongside source code
- `tracker_session_diff` directly solves the session-continuity problem: agents can resume work without replaying the entire conversation history
- The activity log provides an audit trail for agent mutations, supporting post-hoc debugging of what an agent changed and when

### Patterns Worth Adopting

- MCP safety annotations (`readOnly`, `idempotent`, `destructive`) on every tool are a strong pattern — they allow MCP clients to gate destructive operations behind confirmation prompts and to cache read-only calls safely
- Typed notes system (8 categories) is more structured than free-form markdown files and maps well to the kinds of context agents need to persist: decisions, blockers, context for next session
- `tracker_session_diff` (timestamp-based change surface) is a reusable pattern for any stateful MCP server that needs to support session resumption without full state replay
- Batch operation tools (`task_batch_update`, `subtask_create` with array input) reduce tool call round-trips — a latency and token-cost optimization worth applying in other MCP servers

### Integration Opportunities

- Can be added to any Claude Code project via `.mcp.json` to give the agent a persistent task backlog separate from the repository's backlog system
- Complements the repository's own `/backlog` skill: saga-mcp tracks in-session task breakdowns; the backlog skill manages longer-lived GitHub Issues
- The import/export JSON format could be used to seed a saga-mcp database from the repository's existing plan task files (`plan/tasks-*.md`) via a conversion script
- Source references (`source_ref` field on tasks) enable linking tracker tasks directly to specific files and line ranges — useful for agents doing targeted code modifications

---

## References

- [saga-mcp GitHub Repository](https://github.com/spranab/saga-mcp) (accessed 2026-03-02)
- [saga-mcp npm Package](https://www.npmjs.com/package/saga-mcp) (accessed 2026-03-02)
- [npm Downloads API — saga-mcp last month](https://api.npmjs.org/downloads/point/last-month/saga-mcp) (accessed 2026-03-02)
- [saga-mcp v1.5.3 Release Notes](https://github.com/spranab/saga-mcp/releases/tag/v1.5.3) (accessed 2026-03-02)
- [MCP SDK — @modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/typescript-sdk) (accessed 2026-03-02)
- [better-sqlite3 npm Package](https://www.npmjs.com/package/better-sqlite3) (accessed 2026-03-02)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-03-02 |
| Version at Verification | v1.5.3 |
| Next Review Recommended | 2026-06-02 |
