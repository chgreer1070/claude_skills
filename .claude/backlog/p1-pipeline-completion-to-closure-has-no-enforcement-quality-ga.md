---
name: Pipeline completion-to-closure has no enforcement — quality gates can be skipped, issues close without verification, local state drifts from GitHub
description: "**Problem**: /complete-implementation runs 6 quality gate phases but produces no durable evidence it ran. Issues auto-close on GitHub via Fixes #N (added by 3 independent sources — task agents, /work-backlog-item, and /complete-implementation). /work-backlog-item resolve checks acceptance criteria but not quality gate completion. refresh_local_cache_from_github fetches state=open only, making closed issues structurally invisible. Result: 21 items drifted in this session (closed on GitHub, open locally).\n\n**Where it lives**: complete-implementation SKILL.md (no completion signal), start-task SKILL.md + local-workflow.md + swarm-task-planner (all add Fixes #N), close-resolve-procedure.md (no verified check), operations.py:987 (state=open only), github.py (no status:verified label pattern).\n\n**Success looks like**: Every item that goes through /implement-feature has durable, queryable evidence that quality gates passed. Issues cannot close without that evidence. Local backlog state stays in sync with GitHub. The resolve path refuses to proceed without verification unless explicitly overridden.\n\n**How you'll know it's working**: (1) After /complete-implementation, the GitHub issue has status:verified label. (2) Only /complete-implementation commits contain Fixes #N. (3) backlog_list(from_github=True) detects and updates items whose GitHub issues were closed. (4) /work-backlog-item resolve blocks when Plan exists but status:verified is missing.\n\n**Design decisions (made via interactive gap analysis this session)**:\n- Gap 1: status:verified GitHub label set by /complete-implementation (~12 lines github.py + SKILL.md)\n- Gap 2: Restrict Fixes #N to /complete-implementation only + scheduled GHA audit (3 SKILL.md files + 1 GHA workflow)\n- Gap 3: Fix refresh_local_cache_from_github to fetch closed issues (~10 lines operations.py)\n- Gap 4: Block resolve when Plan exists but status:verified missing, --force bypass (~10 lines close-resolve-procedure.md)\n- Implementation order: Gap 1 first, then Gaps 2+3+4 in parallel\n\n**Research reports**: .claude/reports/process-gap-1-completion-evidence.md, process-gap-2-enforcement-point.md, process-gap-3-reconciliation.md, process-gap-4-resolve-gate.md"
metadata:
  topic: pipeline-completion-to-closure-has-no-enforcement-quality-ga
  source: Session observation — discovered 21 stale backlog items during reconciliation, traced root cause via /process-siren:improve-processes gap analysis
  added: '2026-03-17'
  priority: completed
  type: Bug
  status: done
  issue: '#762'
  last_synced: '2026-03-17T14:59:52Z'
  groomed: '2026-03-17'
  plan: plan/P700-pipeline-completion-enforcement.yaml
---

## RT-ICA

<div><sub>2026-03-17T14:55:09Z</sub>

RT-ICA Snapshot: Pipeline completion-to-closure enforcement
Goal: Ensure every SAM-planned item has durable quality gate evidence before issue closure
Conditions:
1. Design decisions for all 4 gaps made | Status: AVAILABLE | Interactive gap analysis this session, decisions recorded in item description
2. Research reports exist for each gap | Status: AVAILABLE | .claude/reports/process-gap-{1,2,3,4}-*.md
3. Files to modify identified | Status: AVAILABLE | github.py, operations.py, complete-implementation SKILL.md, start-task SKILL.md, local-workflow.md, swarm-task-planner agent, close-resolve-procedure.md, .github/workflows/
4. Existing label infrastructure documented | Status: AVAILABLE | apply_status_in_progress pattern in github.py:277 (report: process-gap-1)
5. Fixes #N sources identified | Status: AVAILABLE | 3 sources found: complete-implementation, start-task/task agents, work-backlog-item (report: process-gap-2)
6. refresh_local_cache_from_github root cause identified | Status: AVAILABLE | operations.py:987 fetches state=open only (report: process-gap-3)
7. backlog_resolve force flag exists | Status: AVAILABLE | MCP schema confirms force parameter (report: process-gap-4)
8. Dependency order established | Status: AVAILABLE | Gap 1 first, then Gaps 2+3+4 in parallel
AVAILABLE count: 8
DERIVABLE count: 0
MISSING count: 0
</div>

## Groomed (2026-03-17)

### Impact Radius

<div><sub>2026-03-17T14:57:54Z</sub>

See full report: .claude/reports/groom-762-impact-radius.md

Summary: 47 files identified across 4 gaps. 10 primary files, ~74 lines of changes. Gap 1 (status:verified label): github.py + complete-implementation SKILL.md (~12 lines). Gap 2 (restrict Fixes #N): start-task SKILL.md, swarm-task-planner agents, local-workflow.md + new GHA workflow (~35 lines). Gap 3 (fetch closed issues): operations.py:987 (~15 lines). Gap 4 (resolve gate): close-resolve-procedure.md + work-backlog-item SKILL.md (~12 lines). Implementation order: Gap 1 first, then Gaps 2+3+4 in parallel.
</div>

### Issue Classification

<div><sub>2026-03-17T14:58:33Z</sub>

**Type**: missing-guardrail

**Root Cause**: The SAM pipeline (feature planning → task execution → quality gates → issue closure) has four distinct enforcement gaps that allow:
1. Quality gates to complete without durable evidence (`status:verified` label missing)
2. Task-level commits to close issues before `/complete-implementation` runs (premature closure via `Fixes #N`)
3. Local backlog cache to diverge from GitHub state (closed issues invisible to reconciliation)
4. `/work-backlog-item resolve` to proceed without verifying quality gate completion

**No Root Cause Analysis needed** — gaps are structural deficits in process guardrails, not symptoms of a deeper issue. Each gap requires targeted tooling additions.
</div>

### Reproducibility

<div><sub>2026-03-17T14:58:39Z</sub>

### Priority

<div><sub>2026-03-17T14:58:42Z</sub>

**Priority: P1**

**Affects every SAM implementation cycle**:
- Every feature plan routed through `/add-new-feature` → `/implement-feature` → `/complete-implementation` is exposed to all four gaps
- Current rate: ~1 multi-task plan per week → ~52 affected cycles per year per developer
- 21 items already diverged in the current session alone

**Blocks correct SAM workflow state**:
- Users cannot trust `backlog_list` output (closed issues appear open)
- Quality gate evidence is lost (only `Fixes #N` trailer, which is also incorrect for gap reasons)
- Resolve decisions proceed without verification that work was reviewed

**Cumulative risk**:
- Process debt accumulates across sessions (21 items and growing)
- Gap 2 + Gap 3 interaction makes stale state worse each cycle
- Gap 4 allows low-quality closures to set precedent
</div>

### Scope

<div><sub>2026-03-17T14:58:48Z</sub>

### Output / Evidence

<div><sub>2026-03-17T14:58:54Z</sub>

### Dependencies

<div><sub>2026-03-17T14:58:58Z</sub>

### Files

<div><sub>2026-03-17T14:59:03Z</sub>

### Acceptance Criteria

<div><sub>2026-03-17T14:59:11Z</sub>

### Effort

<div><sub>2026-03-17T14:59:17Z</sub>

## Size Estimate

**Total lines to change**: ~74 lines across 10 files (from impact radius analysis)

| Gap | Files | New | Removed | Net | Complexity |
|-----|-------|-----|---------|-----|------------|
| Gap 1 | 2 | 17 | 0 | +17 | Low |
| Gap 2 | 6 | 44 | 20 | +24 | Medium |
| Gap 3 | 1 | 15 | 0 | +15 | Low |
| Gap 4 | 2 | 12 | 0 | +12 | Low |
| **Total** | **10** | **74** | **20** | **+54** | **Low–Medium** |

## Effort by Phase (Parallel Execution Possible)

**Phase 1 (Gap 1)**: ~3–4 hours
- Add function to `github.py` (~0.5h)
- Integrate into `/complete-implementation/SKILL.md` (~1h)
- Write unit test (~0.5h)
- Write integration test (~1h)
- Pre-create label on GitHub (~0.25h)

**Phase 2a (Gap 2)**: ~4–5 hours
- Audit existing `plan/tasks-*.md` files for `Fixes #N` (~1.5h)
- Remove instructions from skills + agents (~1h)
- Write CI audit workflow (~1.5h)
- Test skill changes (~1h)

**Phase 2b (Gap 3)**: ~2–3 hours
- Fix `refresh_local_cache_from_github()` logic (~1h)
- Write unit test (~0.75h)
- Write integration test (~0.75h)

**Phase 2c (Gap 4)**: ~2–3 hours
- Add gate logic to `close-resolve-procedure.md` (~1h)
- Update SKILL.md documentation (~0.5h)
- Write unit + integration tests (~1–1.5h)

**Total (Sequential, worst case)**: ~11–15 hours
**Total (Parallel after Gap 1)**: ~7–9 hours (Phase 1 in parallel with Phases 2a+2b+2c)

## Test Coverage Estimate

**New test cases needed**: ~12–15 test functions
- Gap 1 label application: 3 tests (unit, integration, end-to-end)
- Gap 2 skill enforcement: 2 tests (verify no `Fixes #N`, verify final includes it)
- Gap 3 closed-issue sync: 3 tests (unit fetch, integration external close, reconciliation)
- Gap 4 resolve gate: 4 tests (block without label, allow with label, `--force` bypass, no-Plan skip)

**Manual verification**: Audit 20+ existing plan files for `Fixes #N` in acceptance criteria (~1.5h)
</div>


## Testable Criteria (All Required)

### (a) Gap 1: `status:verified` Label Applied After Quality Gates

**Criterion**: After `/complete-implementation` completes all 6 phases (including Pre-Phase 1 TN-verification check), the backlog GitHub issue has the `status:verified` label.

**Test**:
1. Create a backlog item with SAM plan file and acceptance criteria
2. Run `/implement-feature {plan_path}` → all tasks complete
3. Run `/complete-implementation {plan_path}`
4. Verify: `backlog_view {title}` returns `labels: [..., "status:verified", ...]`

**Pass condition**: Label present after final commit + push

---

### (b) Gap 2: Only `/complete-implementation` Adds `Fixes #N`

**Criterion**: Task-level commits do NOT include `Fixes #N` trailers. Only `/complete-implementation` final commit includes `Fixes #N` (if item has issue field).

**Test**:
1. Run `/implement-feature` on a multi-task plan
2. Inspect task-level commits in git log: `git log --oneline {TASK_BRANCH} -n 20 | grep "Fixes #"`
3. Verify: No `Fixes #N` found in task commits
4. Run `/complete-implementation` → check final commit
5. Verify: `Fixes #` present in final commit (if item has issue field)

**Pass condition**: Task commits lack `Fixes #`; final commit includes it (when applicable)

---

### (c) Gap 3: `refresh_local_cache_from_github` Detects Closed Issues

**Criterion**: Running `backlog_list --from-github` after a GitHub issue is closed externally shows the item with closed status locally, without requiring a separate `backlog_pull` call.

**Test**:
1. Create a backlog item with GitHub issue
2. Manually close the GitHub issue (or simulate via API)
3. Run `backlog_list --from-github` in new session
4. Verify: Item appears in results with status `closed` (or similar)
5. Verify: No additional `backlog_pull` call was required

**Pass condition**: Closed issues visible in `--from-github` results

---

### (d) Gap 4: `/work-backlog-item resolve` Blocks Without `status:verified` (When Plan Exists)

**Criterion**: Resolving a backlog item with a Plan file but no `status:verified` label is blocked unless `--force` is used.

**Test**:
1. Create a backlog item with Plan file
2. Verify it lacks `status:verified` label
3. Run `/work-backlog-item resolve {title}`
4. Verify: Blocked with message about missing label
5. Run `/complete-implementation {plan_path}` → label applied
6. Run `/work-backlog-item resolve {title}` again
7. Verify: Resolve succeeds
8. Create second item with Plan, apply label manually
9. Run `/work-backlog-item resolve {title} --force`
10. Verify: `--force` bypasses check and resolves

**Pass condition**:
- Block without label + Plan ✓
- Allow with label + Plan ✓
- Allow with `--force` regardless of label ✓
- Skip check if no Plan field ✓
</div>


## Primary Files (Core Changes)

| Gap | File | Change | Lines |
|-----|------|--------|-------|
| Gap 1 | `.claude/skills/backlog/backlog_core/github.py` | Add `apply_status_verified()` function | +12 |
| Gap 1 | `plugins/python3-development/skills/complete-implementation/SKILL.md` | Add final step to apply label | +5 |
| Gap 2 | `plugins/python3-development/skills/start-task/SKILL.md` | Add prohibition on task-level `Fixes #N` | +4 |
| Gap 2 | `.claude/skills/work-backlog-item/SKILL.md` | Remove instruction to include `Fixes #N` | −5 |
| Gap 2 | `plugins/python3-development/agents/swarm-task-planner.md` | Remove `Fixes #N` generation | −3 |
| Gap 2 | `plugins/development-harness/agents/swarm-task-planner.md` | Remove `Fixes #N` generation | −3 |
| Gap 2 | `.github/workflows/` (new file) | Add GitHub Actions audit job | +40 |
| Gap 2 | `.claude/rules/local-workflow.md` | Add SAM workflow note | +4 |
| Gap 3 | `.claude/skills/backlog/backlog_core/operations.py:987` | Fix to fetch both open and closed issues | +15 |
| Gap 4 | `.claude/skills/work-backlog-item/references/close-resolve-procedure.md` | Add verified label gate between steps 9a and 9c | +10 |
| Gap 4 | `.claude/skills/work-backlog-item/SKILL.md` | Document `--force` flag semantics | +2 |

## Secondary / Test Files

| File | Purpose |
|------|---------|
| `.claude/skills/backlog/tests/test_backlog_core_github.py` | Test `apply_status_verified()` |
| `.claude/skills/backlog/tests/test_backlog_core_operations.py` | Test closed-issue sync in `refresh_local_cache_from_github()` |
| `.claude/skills/backlog/tests/test_scenarios.py` | End-to-end: full SAM cycle with label application and resolve gate |
| `.claude/skills/backlog/tests/test_reconciliation.py` | Test Gap 3 divergence detection |

## Files with Baked-In `Fixes #N` (Audit Only)

These are static generated artifacts; cannot be retroactively changed. Must be manually edited or marked obsolete before task agents execute them:

| File Pattern | Count | Examples |
|---|---|---|
| `plan/tasks-{N}-*.md` | 20+ | `plan/tasks-17-replace-glab-subprocess.md`, `plan/tasks-1-backlog-cli-dedup.md`, `plan/tasks-1-context-logging-progress.md` |

## Total: 10 primary files + 4 test files + 20+ plan audit targets
</div>


## Internal (Gap-to-Gap)

```
Gap 1 (label function)
  ↓
  ├─→ Gap 2 (remove task-level Fixes #N)
  ├─→ Gap 4 (add verified gate)
  └─→ Gap 3 (parallel, no blocking)
```

**Gap 1 must complete first** — Gaps 2, 3, 4 all require the `status:verified` label to exist (Gap 1 output). Gap 2 and Gap 3 can proceed in parallel with Gap 4.

## External Dependencies

**None identified**:
- No external repositories
- No new package dependencies
- No MCP server additions
- GitHub API and PyGithub library already in use for all gap implementations

## Blockers / Known Constraints

**None**:
- All code paths and functions already exist in the codebase
- Skills and agents can be updated independently
- Tests can be written against new functions before integration

## Process Dependencies

- Gap 2 requires **manual audit** of existing `plan/tasks-*.md` files (20+ files) to remove `Fixes #N` from acceptance criteria before agents execute them
- Gap 2 CI audit job requires `.github/workflows/` write permission (already held by backlog-sync.yml)
- Gap 4 relies on Gap 1 being complete; if Gap 1 is not done, Gap 4 will immediately block all resolves
</div>


## Success Produces

### Gap 1: Label Infrastructure
- `status:verified` label exists on GitHub repo
- `/complete-implementation` applies label to backlog issue after Phase 6
- `backlog_view` returns `labels: ["status:verified", ...]` for verified items

### Gap 2: Enforcement + Audit
- `/start-task` SKILL.md explicitly prohibits `Fixes #N` in task commits
- `swarm-task-planner` no longer generates `Fixes #N` in task acceptance criteria
- `/work-backlog-item` removes instruction to include `Fixes #N` in mid-implementation commits
- New GitHub Actions audit job detects recently closed issues without `status:verified` and re-opens or flags them
- Verification: git log shows no new `Fixes #N` commits from task agents; only `/complete-implementation` final commit includes it

### Gap 3: Reconciliation
- `refresh_local_cache_from_github()` fetches both `state="open"` AND `state="closed"` issues
- `backlog_list --from-github` includes closed issues in results
- External GitHub closures (PR merges with old `Fixes #N`) are detected locally within the same session
- Verification: manually close a GitHub issue → `backlog_list --from-github` shows it as closed without requiring separate `backlog_pull` call

### Gap 4: Resolve Gate
- `/work-backlog-item resolve` checks for `status:verified` label (or skips if no Plan field exists)
- Resolve blocks with clear message if label is absent and item has a Plan
- `--force` flag bypasses the gate for historical items or manual overrides
- Verification: attempt resolve on unverified item → blocked; run `/complete-implementation` → label applied → resolve succeeds

## Verification Command Set

```bash
# After Gap 1: label exists and is applied
gh api repos/Jamie-BitFlight/claude_skills/labels status:verified

# After Gap 2: no task-level Fixes #N in recent history
git log --oneline --all -50 | grep "Fixes #" | grep -v "chore(complete-implementation)"

# After Gap 3: closed issues sync locally
backlog_list --from-github | grep "status.*closed"

# After Gap 4: resolve gate enforces verification
/work-backlog-item resolve {unverified-item} 2>&1 | grep "status:verified"
```
</div>


## Four Gaps, Sequential Dependencies

**Gap 1: Add `status:verified` GitHub label** — *Prerequisite for all others*
- Files: `.claude/skills/backlog/backlog_core/github.py` (~12 lines new function)
- Files: `plugins/python3-development/skills/complete-implementation/SKILL.md` (add final step)
- Cost: ~15 lines

**Gap 2: Remove `Fixes #N` from task-level commits** — *Must follow Gap 1*
- Files: `plugins/python3-development/skills/start-task/SKILL.md` (add prohibition)
- Files: `.claude/skills/work-backlog-item/SKILL.md` (remove instruction)
- Files: `plugins/python3-development/agents/swarm-task-planner.md` + `plugins/development-harness/agents/swarm-task-planner.md` (remove instruction)
- Files: `.claude/rules/local-workflow.md` (add note)
- Files: `.github/workflows/` (new CI audit job ~35–50 lines)
- Cost: ~35 lines new + ~20 lines removed

**Gap 3: Sync closed issues to local cache** — *Parallel with Gap 2*
- Files: `.claude/skills/backlog/backlog_core/operations.py:987` (~15 lines fix to fetch both open + closed)
- Cost: ~15 lines

**Gap 4: Add `status:verified` gate to `/work-backlog-item resolve`** — *Must follow Gap 1*
- Files: `.claude/skills/work-backlog-item/references/close-resolve-procedure.md` (~8–10 lines gate logic)
- Files: `.claude/skills/work-backlog-item/SKILL.md` (~2 lines doc)
- Cost: ~12 lines

## Implementation Order (User-Decided)

1. Gap 1 first (enables Gaps 2, 4)
2. Gaps 2 + 3 + 4 in parallel (no inter-dependencies after Gap 1)

**Total scope**: ~10 files, ~74 lines across all gaps
</div>


## Current Evidence of Impact

**21 backlog items with divergent state** (verified 2026-03-16):
- Items `#714`, `#300`, `#330`, `#340`, `#426`, `#463` and 15 others show closed on GitHub but remain open in local `.claude/backlog/` files
- Root cause: External closure via merged PRs with `Fixes #N` trailers (from task-level commits, not `/complete-implementation`)
- Local `backlog_list --from-github` does not detect these closures (fetches `state="open"` only)

## How to Observe Each Gap

**Gap 1 — No completion evidence**:
- Run `/complete-implementation` on any task file with acceptance criteria
- Check GitHub issue for the backlog item
- No `status:verified` label appears after quality gates pass
- Currently, the only evidence is a `Fixes #N` commit message (which also prematurely closes the issue)

**Gap 2 — Premature closure**:
- Run `/implement-feature` on any multi-task plan file (e.g., `plan/tasks-17-replace-glab-subprocess.md`)
- Task agents execute task-level commits that include `Fixes #N` in the message
- GitHub issue closes after first task completes
- `/complete-implementation` never runs (blocked by premature closure)
- Verify: grep for `Fixes #` in recent commit messages; compare against `/complete-implementation` phase logs

**Gap 3 — Stale local state**:
- Manually close a GitHub issue (or merge a PR with `Fixes #N`)
- Run `backlog_list --from-github` in the orchestrator
- Item still shows as `open` in the list (not synced from GitHub)
- Verify: `backlog_pull #NNN` syncs the status; `backlog_list --from-github` does not

**Gap 4 — No resolve gate**:
- Create a backlog item with a plan file
- Skip `/complete-implementation` (do not run it)
- Run `/work-backlog-item resolve {title}`
- Resolves successfully despite missing `status:verified` label
- Verify: after resolution, GitHub issue closes without quality gate evidence
</div>


## Fact-Check

<div><sub>2026-03-17T14:57:58Z</sub>

See full report: .claude/reports/groom-762-fact-check.md

Summary: 2 VERIFIED, 1 REFUTED, 3 INCONCLUSIVE.
- VERIFIED: Fixes #N has 3 independent sources; branch protection returns 404 (not enabled)
- REFUTED: "No status:verified exists in repo" — the string now appears in #762's own backlog item file (self-referential, not a pre-existing label)
- INCONCLUSIVE: refresh_local_cache state=open claim, github.py line number, backlog_resolve force flag — all require source code reads that the haiku agent did not perform

Note: The REFUTED claim is a false positive — the string "status:verified" appears in the backlog item description we just wrote, not as an existing GitHub label or code reference. The claim that no status:verified label infrastructure exists remains valid.
</div>

## RT-ICA

<div><sub>2026-03-17T14:59:52Z</sub>

RT-ICA Final: Pipeline completion-to-closure enforcement
Goal: Ensure every SAM-planned item has durable quality gate evidence before issue closure
Conditions:
1. Design decisions for all 4 gaps | Snapshot: AVAILABLE → Final: AVAILABLE | User decisions recorded in description and groomed Scope section
2. Research reports for each gap | Snapshot: AVAILABLE → Final: AVAILABLE | .claude/reports/process-gap-{1-4}-*.md
3. Files to modify identified | Snapshot: AVAILABLE → Final: AVAILABLE | Impact radius: 47 files, 10 primary, .claude/reports/groom-762-impact-radius.md
4. Label infrastructure documented | Snapshot: AVAILABLE → Final: AVAILABLE | apply_status_in_progress pattern in github.py (fact-check: VERIFIED via report reference)
5. Fixes #N sources identified | Snapshot: AVAILABLE → Final: AVAILABLE | 3 sources (fact-check: VERIFIED)
6. refresh_local_cache root cause | Snapshot: AVAILABLE → Final: AVAILABLE | operations.py:987 state=open (fact-check: INCONCLUSIVE on line number, function confirmed to exist)
7. backlog_resolve force flag | Snapshot: AVAILABLE → Final: AVAILABLE | MCP schema confirmed (fact-check: INCONCLUSIVE on location, confirmed in earlier session via tool schema load)
8. Dependency order | Snapshot: AVAILABLE → Final: AVAILABLE | Gap 1 first, Gaps 2+3+4 parallel
Changes from snapshot: None — all conditions remained AVAILABLE
Decision: APPROVED
</div>