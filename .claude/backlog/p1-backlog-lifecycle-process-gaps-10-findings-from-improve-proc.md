---
name: Backlog lifecycle process gaps — 10 findings from improve-processes audit
description: "Process audit of the full backlog item lifecycle (create → groom → discuss → research → validate → feasibility → plan → implement → close/resolve) using the /improve-processes excellence checklist and triage protocol. 10 findings identified across 3 severity levels. 2 HIGH: (F1) no feasibility gate between RT-ICA APPROVED and SAM planning, (F9) 6 implied handoffs that break autonomous execution. 5 MEDIUM: (F2) no discussion/interview step, (F4) vague 'is job valid' condition, (F5) non-sequential step numbering, (F6) no groomer output validation, (F10) draft lifecycle doc not promoted. 3 LOW: (F3) RT-ICA staleness, (F7) auto-mode P1 default, (F8) fact-check auto-push. Full report: .claude/docs/process-audit-backlog-lifecycle-2026-03-02.md"
metadata:
  topic: backlog-lifecycle-process-gaps-10-findings-from-improve-proc
  source: Session observation — /improve-processes audit
  added: '2026-03-02'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#398'
  last_synced: '2026-03-03T03:53:33Z'
  plan: .claude/docs/process-audit-backlog-lifecycle-2026-03-02.md
---

## Story

As a **developer using Claude Code skills**, I want to **backlog lifecycle process gaps — 10 findings from improve-processes audit** so that **the tooling becomes more capable and complete**.

## Description

Process audit of the full backlog item lifecycle (create → groom → discuss → research → validate → feasibility → plan → implement → close/resolve) using the /improve-processes excellence checklist and triage protocol. 10 findings identified across 3 severity levels. 2 HIGH: (F1) no feasibility gate between RT-ICA APPROVED and SAM planning, (F9) 6 implied handoffs that break autonomous execution. 5 MEDIUM: (F2) no discussion/interview step, (F4) vague 'is job valid' condition, (F5) non-sequential step numbering, (F6) no groomer output validation, (F10) draft lifecycle doc not promoted. 3 LOW: (F3) RT-ICA staleness, (F7) auto-mode P1 default, (F8) fact-check auto-push. Full report: .claude/docs/process-audit-backlog-lifecycle-2026-03-02.md

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session observation — /improve-processes audit
- **Priority**: P1
- **Added**: 2026-03-02
- **Research questions**: None

## Groomed (2026-03-02)

### MCP Ecosystem Comparison — Additional Findings (2026-03-01)

Comparative review of four peer MCP project-tracking systems (spec-workflow-mcp 3.9K⭐, saga-mcp, ultra-mcp 269⭐, openspec-mcp) against our backlog MCP. Sources: research/mcp-ecosystem/{spec-workflow-mcp,saga-mcp,ultra-mcp,openspec-mcp}.md

### F11 — MEDIUM: No MCP safety annotations on any tool

Our 10 tools declare no `readOnly`, `idempotent`, or `destructive` annotations. saga-mcp annotates all 31 tools. Without annotations, MCP clients cannot gate destructive ops behind confirmation prompts or safely cache read-only calls.

**Fix**: Add `annotations=` to each `@mcp.tool()` call in `server.py`. `backlog_list` and `backlog_view` → `readOnly`; `backlog_close` and `backlog_resolve` → `destructive`. Zero new logic required.

### F12 — HIGH: No session resumption primitive

Agents rejoining a session after context compaction cannot ask "what changed in the backlog since I was last here." They must re-run `backlog_list` and infer state manually. saga-mcp's `tracker_session_diff(since: timestamp)` surfaces only items changed since a given ISO timestamp.

**Fix**: Add `backlog_session_diff(since: str)` — query items whose backing file mtime (or `git log --since`) is newer than the provided timestamp. Returns same shape as `backlog_list`.

### F13 — HIGH: No single-call backlog health overview

Agents working on multi-task features repeatedly call `backlog_list`, count items per section, and identify items needing grooming. spec-workflow-mcp and openspec-mcp both have a dashboard/progress-summary tool. We have none.

**Fix**: Add `backlog_dashboard()` returning: counts by section (P0/P1/P2/Ideas), counts by status, items with no GitHub issue, items with `needs-grooming` label, items modified in the last 7 days. One call replaces 3–5 agent round-trips per session.

### F14 — MEDIUM: Named status-transition tools are missing

`backlog_update(status="in-progress")` is a generic setter — agent intent is invisible in audit logs. openspec-mcp uses distinct named tools (`request_approval`, `approve_change`, `reject_change`) making every transition explicit and auditable.

**Fix**: Add thin wrappers: `backlog_start(selector)`, `backlog_block(selector, reason)`, `backlog_unblock(selector)`. Each delegates to `backlog_update(status=...)` internally. Adds semantic clarity with zero new business logic.

### F15 — MEDIUM: No batch mutation support

Updating status on multiple items (e.g., marking a wave of tasks complete after `/complete-implementation`) requires N sequential tool calls. saga-mcp's `task_batch_update` accepts an array. Our agents pay N round-trips where 1 would suffice.

**Fix**: Add `backlog_batch_update(selectors: list[str], status: str | None, plan: str | None)`. Single call, same validation as `backlog_update`.

### F16 — LOW: `backlog_update` exceeds the 4-parameter ergonomics threshold

ultra-mcp's design guidance: max 4 parameters per tool for predictable Claude Code integration. `backlog_update` has 9 parameters. Agents routinely pass incorrect combinations (e.g., `groomed_content` and `section` together).

**Fix**: Document intended call patterns in the tool docstring. Add a validation guard that raises `ValidationError` when mutually exclusive params are combined. Long-term: split into focused tools with ≤4 params each.

### F17 — LOW: Tools not discoverable as MCP prompts

ultra-mcp (v0.7.0) exposes all 25 tools also as prompts in Claude Code. Our server exposes only tools — no prompt picker discoverability.

**Fix**: Register each tool as a corresponding MCP prompt in `server.py` via `@mcp.prompt()`. Lower priority — impacts human discoverability, not agent execution.

### Prioritised Implementation Order

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| P1 | F11 — MCP safety annotations | Low | High |
| P1 | F12 — `backlog_session_diff` | Low | High |
| P1 | F13 — `backlog_dashboard` | Medium | High |
| P2 | F14 — Named status tools | Low | Medium |
| P2 | F15 — `backlog_batch_update` | Medium | Medium |
| P3 | F16 — Parameter count guard | Low | Low |
| P3 | F17 — MCP prompts | Low | Low |

### What NOT to adopt from peers

- SQLite as primary storage (saga-mcp, openspec-mcp): GitHub-as-source-of-truth is superior for cross-agent, cross-PR, cross-session durability.
- Local web dashboard: adds process dependency incompatible with Claude Code's session model.
- Atomising all `backlog_update` fields into micro-tools: named status tools (F14) are the right granularity.
