# Alignment Review: #981 vs #986

**Date**: 2026-03-22
**Issues**: #981 "Consolidate backlog and plan directories under .dh/" vs #986 "Add dispatch orchestration MCP tools with background task support to backlog server"

---

## 1. Directory Structure Alignment

**Finding: No conflict — architectures are compatible, but #981's Acceptance Criteria introduces a significant design change not in the issue description.**

#986 explicitly states:
> "State backend: SQLite at `~/.dh/projects/{project-stub}/dispatch-state.db`... User-level, outside git, shared across all worktrees."
> "No dependency on #981: This path is independent of the in-repo `.dh/` consolidation."

#981's Acceptance Criteria define three tiers:

- **Tier 1** — in-repo `.dh/` (committed config/settings only)
- **Tier 2** — `~/.dh/projects/{slug}/` (persistent state: backlog cache, plan artifacts, SQLite)
- **Tier 3** — `~/.dh/projects/{slug}/` (ephemeral: context files, reports)

**Critical gap in #981**: The issue description says "consolidate under `.dh/`" (implying in-repo), but the Acceptance Criteria move backlog cache and plan artifacts to `~/.dh/projects/{slug}/` (user-level, outside git). This is a fundamentally different architecture than the description implies. The "Suggested target layout" in the Next Steps section shows `plan/` and `backlog/` as in-repo `.dh/` subdirectories — contradicting Tier 2 of the Acceptance Criteria.

**This internal contradiction in #981 needs resolution before implementation begins.** The two options are:

- **Option A** (matches description + Next Steps suggested layout): Move to in-repo `.dh/backlog/`, `.dh/plan/`, `.dh/context/`, `.dh/reports/`
- **Option B** (matches Acceptance Criteria Tier 2/3): Move to `~/.dh/projects/{slug}/` — outside git, shared across worktrees, backed by SQLite

These are not the same thing. Option A is a directory rename. Option B is a backend replacement (filesystem → SQLite with filesystem cache).

---

## 2. Path References — Do #981's Changes Break #986?

**Finding: No breaking conflict currently. Potential conflict if Option B is chosen for #981.**

#986 depends on these paths:

| Path | Used by #986 | #981 plans to change? |
|------|-------------|----------------------|
| `plan/milestone-{N}-dispatch.yaml` | `dispatch_spawn` reads via `dispatch_read` | Yes — `plan/` moves under `.dh/plan/` or `~/.dh/.../plan/` |
| `~/.dh/projects/{slug}/dispatch-state.db` | New SQLite state file | This is a new file — no conflict |
| `plugins/development-harness/backlog_core/server.py` | #986 adds new MCP tools here | #981 plans to modify this file (path constants) |
| `.claude/backlog/` | #986 does not read this directly | #981 moves this |

**The `plan/` path is the key dependency.** #986's `dispatch_read` tool reads `plan/milestone-{N}-dispatch.yaml`. If #981 moves `plan/` before #986 ships, the dispatch tools need to be updated at the same time. If #986 ships first using `plan/`, then #981 moves `plan/`, the `dispatch_read` constant needs updating as part of #981's migration.

This is manageable — it's a constant update, not an architectural conflict — but the sequencing must be explicit.

---

## 3. MCP Server Changes

**Finding: Additive conflict — both issues modify `server.py`. Must be coordinated.**

- **#981** plans to update `backlog_core/server.py` to replace hardcoded `.claude/backlog/` path constants. Scope: path constant updates + potentially new backend initialization logic.
- **#986** plans to add four new MCP tools to `backlog_core/server.py`: `dispatch_wave_start`, `dispatch_item_status`, `dispatch_wave_status`, `dispatch_spawn`.

Both changes are additive but they touch the same file. If #986 and #981 are implemented in separate branches simultaneously, the merge will conflict on `server.py`. This is a coordination requirement, not a design conflict.

**Recommendation**: Implement #986 first (adds new tools) then #981 (updates path constants). Or implement in the same branch. Do not parallelize across separate branches without a merge plan.

---

## 4. Naming — `.dh/` in-repo vs `~/.dh/` user-level

**Finding: The naming is intentional but the distinction is not documented in #981.**

#986's Design Notes explicitly distinguish:
> "This is under `~/.dh/` — our own namespace, not inside `~/.claude/`."

#981's description says "consolidate under `.dh/`" without qualifying whether that's in-repo or user-level. The Acceptance Criteria reveal both are used simultaneously:
- In-repo `.dh/` = config/settings (Tier 1)
- User-level `~/.dh/` = runtime state + cached artifacts (Tier 2/3)

**The confusion risk**: A developer reading #981's title ("under .dh/") would assume in-repo. The Acceptance Criteria reveal a more complex picture. This needs to be explicitly documented in the issue and any resulting design doc or CLAUDE.md update. The namespace (`~/.dh/` vs in-repo `.dh/`) must be unambiguous in all implementation artifacts.

---

## 5. Sequencing

**Finding: #986 CAN be implemented independently. One forward-compatibility consideration.**

#986's Design Notes explicitly state "No dependency on #981."

The correct implementation order is:

1. **#986 first** (or in parallel, in its own branch): Adds dispatch execution MCP tools to `server.py`. Uses current `plan/` paths. Uses `~/.dh/projects/{slug}/dispatch-state.db` for state.
2. **#981 second**: Migrates `plan/` to new location. Must include updating `dispatch_read` constant (and any other path references #986 introduced) as part of the migration sweep.

If #981 ships first (unlikely given it's still in design-decision-pending state per Outstanding Questions), #986 must use the new paths from the start.

**The outstanding questions in #981 must be resolved before #981 implementation begins.** The issue explicitly lists them as unresolved design decisions requiring human input.

---

## 6. General Coherence of #981 Grooming

**Findings:**

**What is solid:**
- Impact Radius analysis is thorough and accurate (verified against actual files — `plan/` has 391 files, `.claude/backlog/` has 332 items)
- The five-category breakdown (producers, consumers, tests, docs, config) is complete
- Hard Dependencies list is correct
- Acceptance Criteria are detailed

**What is broken or missing:**

1. **Internal contradiction on destination**: The issue description + "Suggested target layout" says in-repo `.dh/` with `backlog/`, `plan/`, `context/`, `reports/` subdirectories. But Acceptance Criteria Tier 2/3 say `~/.dh/projects/{slug}/` for backlog cache, plan, context, and reports. These cannot both be correct. **This is the single most important gap — it must be resolved before any plan is created.**

2. **`dispatch-state.db` placement**: The suggested target layout in Next Steps shows `dispatch-state.db` inside the in-repo `.dh/`. But #986 and #981's own Acceptance Criteria Tier 2 both put it in `~/.dh/projects/{slug}/`. The Next Steps layout is stale — it predates the Acceptance Criteria design.

3. **Outstanding Questions still open**: The Acceptance Criteria section says "all design decisions resolved (2026-03-22)" under Dependencies, but the Outstanding Questions section lists 5 open items including target layout, scope expansion, and migration strategy. This is contradictory. Either the questions were resolved (and the Outstanding Questions section should be updated) or they were not (and the Dependencies assertion is wrong).

4. **No plan attached**: `plan: ""` — the issue is groomed but has no SAM task plan. The Acceptance Criteria span a significant scope (50+ files, Python rewrites, SQLite backend). Implementation cannot start without a task plan.

5. **`dispatch-state.db` in-repo reference is an error**: The "Suggested target layout" shows `dispatch-state.db` inside in-repo `.dh/`. A SQLite database used across worktrees must NOT be in-repo (git conflicts, gitignore required). The Acceptance Criteria and #986 both correctly place it in `~/.dh/`. The Next Steps layout must be corrected.

**What is useful but needs update:**
- "This Item Is Blocked By: Nothing — all design decisions resolved" — this is contradicted by Outstanding Questions. Fix the status of Outstanding Questions or correct this claim.

---

## Summary of Action Items

| # | Finding | Action Required | Blocking? |
|---|---------|----------------|-----------|
| 1 | #981 internal contradiction: in-repo `.dh/` vs `~/.dh/` for backlog/plan artifacts | Resolve design decision before creating task plan | Yes for #981 |
| 2 | `plan/` path used by #986 will move in #981 | Update dispatch path constants as part of #981 migration sweep | No — handled in #981 |
| 3 | Both issues modify `server.py` | Do not implement in parallel branches; sequence or coordinate merge | Yes for parallel work |
| 4 | `dispatch-state.db` in Next Steps layout is in-repo (wrong) | Correct suggested layout to show `~/.dh/projects/{slug}/` | Editorial fix to #981 |
| 5 | Outstanding Questions still open despite "resolved" claim | Either answer all 5 questions or remove the "resolved" claim | Yes for #981 |
| 6 | #981 has no task plan | Create SAM task plan before starting implementation | Yes for #981 |
| 7 | #986 can implement now, independently | No blocker — proceed | — |
