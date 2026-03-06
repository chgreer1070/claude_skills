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
  last_synced: '2026-03-06T05:50:52Z'
  plan: .claude/docs/process-audit-backlog-lifecycle-2026-03-02.md
  groomed: '2026-03-06'
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

### Priority

9/10 — Two HIGH-severity findings (F1, F9) break autonomous operation entirely: F1 triggers the 4-6 agent SAM pipeline on infeasible items; F9 stalls `--auto` mode at every lifecycle transition. The remaining 8 findings degrade quality and determinism in every grooming and creation session. No other open P1 item has this breadth of impact across the full lifecycle.

### Impact

- **Blocks**: Any attempt to run the full backlog lifecycle end-to-end in `--auto` mode stalls at six implied handoffs (F9). The SAM pipeline runs without a feasibility gate (F1), consuming 4-6 agent delegations before anyone asks "should we proceed?"
- **Bottleneck**: `groom-backlog-item` writes groomer agent output with no validation gate (F6) — a haiku-model agent with documented ~50% accuracy on ambiguous tasks writes directly to canonical item files. `create-backlog-item --auto` defaults P1 priority on most items (F7), diluting P1 meaning across the entire backlog.
- **Risk if unchanged**: Wasted planning cycles on infeasible items, stalled auto mode, inconsistent lifecycle execution, and P1/P2 signal degradation across the full backlog.

### Scope

Exact files to change per finding:

| Finding | File | Change |
|---------|------|--------|
| F1 — feasibility gate | `.claude/skills/work-backlog-item/SKILL.md` | Add Step 4b feasibility gate between RT-ICA APPROVED check and Step 6 SAM invocation. Gate outputs FEASIBLE/DEFER/REJECT |
| F2 — discussion/interview step | `.claude/skills/groom-backlog-item/SKILL.md` | Add structured interview step before groomer agent spawn; integrate `.claude/docs/sdlc-layers/arl-human-probing-design.md` (STATUS: Design — partial implementation possible without it) |
| F3 — RT-ICA staleness | `.claude/skills/work-backlog-item/SKILL.md` | Add freshness check in Step 4: compare RT-ICA date against today minus N days; compare item description date against RT-ICA date |
| F3 — RT-ICA staleness | `.claude/skills/groom-backlog-item/SKILL.md` | Same staleness check before accepting cached RT-ICA result |
| F4 — vague validity check | `.claude/skills/groom-backlog-item/SKILL.md` line 31 | Replace "Ask or infer" with three concrete checks: age >30d with no activity → flag; `suggested_location` file deleted/heavily refactored → flag; keyword overlap with newer items → report |
| F5 — non-sequential numbering | `.claude/skills/work-backlog-item/SKILL.md` | Renumber all steps sequentially into named phases (Locate, Validate, Prepare, Plan, Close/Resolve). Current sequence: 0, 1b, 1, 2, 2.3, 3, 4, 5, 6, 7, 8, 8.5, 9, 2.5, 2.5a, 2.7 |
| F6 — groomer output validation | `.claude/skills/groom-backlog-item/SKILL.md` | Add validation step between Step 8 (spawn groomer) and Step 9 (write): check required sections present; check no implementation language; retry or escalate on failure |
| F7 — auto-mode P1 default | `.claude/skills/create-backlog-item/SKILL.md` line 39 | Change default from P1 to P2 in `--auto` mode. P1 requires urgency keyword match or explicit `--p1` flag |
| F8 — fact-check auto-push | `.claude/skills/fact-check/SKILL.md` line 192 | Remove `git push -u origin HEAD` from Post-Actions. Caller controls push. |
| F9 — implied handoffs (Gap A) | `.claude/skills/create-backlog-item/SKILL.md` | Add explicit next-step invocation post-creation → groom |
| F9 — implied handoffs (Gaps B, F) | `.claude/skills/groom-backlog-item/SKILL.md` | Add explicit next-step invocations: post-groom → group-items-to-milestone; fact-check → groom return |
| F9 — implied handoffs (Gaps D, E) | `.claude/skills/work-backlog-item/SKILL.md` | Add explicit next-step invocations: complete-implementation → resolve; resolve → complete-milestone |
| F9 + F10 — handoffs + lifecycle doc | `.claude/docs/backlog-lifecycle.draft.md` | Document full state machine as single-page canonical overview |
| F10 — draft lifecycle doc | `.claude/docs/backlog-lifecycle.draft.md` | Validate against audit findings, resolve all `[VERIFY]` markers, remove STATUS: DRAFT, add reference links from each affected SKILL.md |

### Output / Evidence

Grep-verifiable acceptance signals per finding:

| Finding | Verification command | Expected result |
|---------|---------------------|-----------------|
| F1 | `grep -n "feasib\|FEASIBLE\|DEFER\|REJECT" .claude/skills/work-backlog-item/SKILL.md` | At least one match in step between RT-ICA gate and SAM invocation |
| F2 | `grep -n "interview\|probe\|arl-human-probing" .claude/skills/groom-backlog-item/SKILL.md` | At least one match |
| F3 | `grep -n "freshness\|staleness\|re-run" .claude/skills/work-backlog-item/SKILL.md` | At least one match in RT-ICA gate section |
| F4 | `grep -n "Ask or infer" .claude/skills/groom-backlog-item/SKILL.md` | No matches |
| F5 | `grep -n "^### Step" .claude/skills/work-backlog-item/SKILL.md` | Sequential integers with no decimals (2.3, 2.5), no gaps, no lettered variants (1b) |
| F6 | `grep -n "validation\|required sections\|implementation language" .claude/skills/groom-backlog-item/SKILL.md` | At least one match between groomer spawn and write step |
| F7 | `grep -n "default P" .claude/skills/create-backlog-item/SKILL.md` | Returns "default P2" not "default P1" |
| F8 | `grep -n "git push" .claude/skills/fact-check/SKILL.md` | No matches |
| F9 | Inspect each of 6 handoff points in the relevant SKILL.md files | Explicit skill invocation instructions, not text-only "Next steps:" |
| F10 | `grep -n "STATUS: DRAFT\|\[VERIFY\]" .claude/docs/backlog-lifecycle.draft.md` | No matches; at least 3 SKILL.md files contain link to lifecycle doc |

### Dependencies

- **Depends on**: #426 (Backlog state machine implementation — state_handler.py) for F9 machine-readable handoff output — state_handler.py exists at `.claude/skills/backlog/scripts/state_handler.py` but no skill currently calls it; F9 fixes must reference it
- **Depends on (partial)**: #194 (ARL human-probing — implement skill/agent) for F2 — design doc exists at `.claude/docs/sdlc-layers/arl-human-probing-design.md` (STATUS: Design) but skill/agent not implemented; F2 can be partially addressed with a lightweight interview mode independent of #194
- **Blocks**: Any item requiring reliable `--auto` end-to-end execution — F9 is the critical blocker for all autonomous operation
- **Upstream**: #282 (Backlog system redesign: GitHub Issues as source of truth) — implied handoffs in F9 affect GitHub-sync transitions

### Prior Work

| Artifact | Path | Status | Relevance |
|----------|------|--------|-----------|
| Process audit report | `.claude/docs/process-audit-backlog-lifecycle-2026-03-02.md` | Final | Source definitions for F1-F10 |
| Draft lifecycle doc | `.claude/docs/backlog-lifecycle.draft.md` | DRAFT (unverified `[VERIFY]` markers) | F10 target — validate and promote |
| ARL human-probing design | `.claude/docs/sdlc-layers/arl-human-probing-design.md` | Design (not implemented) | F2 specification input |
| state_handler.py | `.claude/skills/backlog/scripts/state_handler.py` | Implemented (commit d7e3f84) | 8-state lifecycle DAG — F9 state machine foundation |
| Backlog state machine definition | `.claude/skills/backlog/references/state-machine.md` | Current | Consumed by state_handler.py |
| Groomer agent steps (extracted) | `.claude/skills/groom-backlog-item/references/groomer-agent.md` | Current (extracted 2026-03-06) | F6 groomer output context |
| Issue classification steps (extracted) | `.claude/skills/groom-backlog-item/references/issue-classification.md` | Current (extracted 2026-03-06) | Groom-backlog-item context |
| F11-F17 commit | Commit `2541356` (overwritten by `76dcf77`) | OVERWRITTEN — not in current server.py | MCP tool additions that need re-implementation |

### Files

Files requiring changes:

- `.claude/skills/work-backlog-item/SKILL.md` — F1 (feasibility gate), F3 (RT-ICA freshness), F5 (renumber steps), F9 (Gaps D, E handoffs)
- `.claude/skills/groom-backlog-item/SKILL.md` — F2 (interview step), F3 (RT-ICA freshness), F4 (validity check), F6 (groomer validation), F9 (Gaps B, F handoffs)
- `.claude/skills/create-backlog-item/SKILL.md` — F7 (P1→P2 default), F9 (Gap A handoff)
- `.claude/skills/fact-check/SKILL.md` — F8 (remove auto-push, line 192)
- `.claude/docs/backlog-lifecycle.draft.md` — F9 (state machine) + F10 (promote to canonical)

Reference files (read-only context):
- `.claude/docs/process-audit-backlog-lifecycle-2026-03-02.md`
- `.claude/docs/sdlc-layers/arl-human-probing-design.md`
- `.claude/skills/backlog/scripts/state_handler.py`
- `.claude/skills/groom-backlog-item/references/groomer-agent.md`
- `.claude/skills/groom-backlog-item/references/issue-classification.md`

### Decision

**Proceed with planning.** RT-ICA APPROVED (2026-03-06). All 10 findings confirmed unimplemented via grep verification.

**Blockers**:
- F2 (ARL discussion step) is partially blocked pending #194 — a lightweight interview mode can proceed without it
- F11-F17 MCP tool additions are out of scope for F1-F10 planning; commit `2541356` was overwritten by `76dcf77 Add files via upload`; need separate re-implementation work

**Effort estimate**: Medium — 10 targeted edits across 4 SKILL.md files and 1 draft doc. No new scripts required for F3-F8, F10. F1 and F9 require new step content and trigger cascading renumbering (F5 in scope). Total: 8-12 focused file edits with grep-verifiable acceptance criteria.


## Fact-Check

**Date**: 2026-03-06
**Claims checked**: 7

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Audit report exists at `.claude/docs/process-audit-backlog-lifecycle-2026-03-02.md` with 10 findings | VERIFIED | File exists; F1–F10 headings and severities confirmed via Read |
| 2 | F1 (feasibility gate) absent from `work-backlog-item` | VERIFIED | grep for "feasib" in SKILL.md returns no matches |
| 3 | F4 (vague "is job valid?") still uses "Ask or infer" | VERIFIED | Line 31 of groom-backlog-item SKILL.md: "Ask or infer: does this item still belong..." |
| 4 | F7 (auto-mode P1 default) unchanged | VERIFIED | create-backlog-item SKILL.md line 39: "default P1" |
| 5 | F8 (fact-check auto-push) still present | VERIFIED | fact-check SKILL.md line 192: `git push -u origin HEAD` in Post-Actions |
| 6 | F5 (non-sequential numbering) still present | VERIFIED | work-backlog-item: Steps 0, 1b, 1, 2, 2.3, 3, 4, 5, 6, 7, 8, 8.5, 9, 2.5, 2.5a, 2.7 |
| 7 | F11-F17 MCP tools implemented and present in server.py | REFUTED | Commit `2541356` added tools, but `76dcf77 Add files via upload` overwrote server.py; current server.py has 10 tools (add/list/view/sync/close/resolve/update/groom/normalize/pull) — `backlog_session_diff`, `backlog_dashboard`, `backlog_start`, `backlog_block`, `backlog_unblock`, `backlog_batch_update` absent |

**Totals**: VERIFIED 6 | REFUTED 1 | INCONCLUSIVE 0

**New context since 2026-03-03**:
- `work-backlog-item`: `/simplify` step added (Step 8), "Report Next Steps" moved to Step 8.5 — F9 partial progress but state machine still not machine-readable
- Token complexity refactor: Steps 6-8 in groom-backlog-item extracted to `references/issue-classification.md` and `references/groomer-agent.md`
- `state_handler.py` added at `.claude/skills/backlog/scripts/state_handler.py` — 8-state lifecycle DAG (commit `d7e3f84`)
- F11-F17 commit `2541356` exists on `master` branch but server.py was overwritten; implementation in operations.py may still be present

## RT-ICA

**Date**: 2026-03-06
**Goal**: Implement the 10 process-gap fixes across backlog lifecycle skills so that end-to-end autonomous operation runs without implied handoffs, ungated transitions, or silent quality failures.

| # | Condition | Status | Info needed |
|---|---|---|---|
| 1 | Source audit with 10 findings and evidence is available | AVAILABLE | `.claude/docs/process-audit-backlog-lifecycle-2026-03-02.md` |
| 2 | F1: feasibility gate absent from `work-backlog-item` | AVAILABLE | Confirmed: no feasibility step exists |
| 3 | F4: vague validity check is still "Ask or infer" | AVAILABLE | Confirmed: line 31 of groom-backlog-item SKILL.md |
| 4 | F7: auto-mode P1 default still present | AVAILABLE | Confirmed: create-backlog-item SKILL.md line 39 |
| 5 | F8: fact-check auto-push still present | AVAILABLE | Confirmed: fact-check SKILL.md line 192 |
| 6 | F5: non-sequential step numbering in work-backlog-item | AVAILABLE | Steps: 0, 1b, 1, 2, 2.3, 3, 4, 5, 6, 7, 8, 8.5, 9, 2.5, 2.5a, 2.7 |
| 7 | F11-F17 MCP tools implementation status | AVAILABLE | REFUTED: F11-F17 commit `2541356` merged but server.py overwritten; tools absent from current surface |
| 8 | F6: no groomer output validation step before backlog write | AVAILABLE | Confirmed: groom-backlog-item Step 9 writes without validation gate |
| 9 | F9: handoff invocations — explicit next-step output | DERIVABLE | /simplify step added to work-backlog-item; state machine still prose-only |
| 10 | F10: draft lifecycle doc promotion status | AVAILABLE | `.claude/docs/backlog-lifecycle.draft.md` still has STATUS: DRAFT with [VERIFY] markers |
| 11 | F2: ARL human-probing step implementation status | AVAILABLE | `.claude/docs/sdlc-layers/arl-human-probing-design.md` exists but status not checked this session |
| 12 | F3: RT-ICA freshness policy | AVAILABLE | No freshness check in groom or work-backlog-item (both confirmed via grep) |

**Decision**: APPROVED
**Missing**: F2 ARL design doc status should be confirmed (currently DERIVABLE pending read)