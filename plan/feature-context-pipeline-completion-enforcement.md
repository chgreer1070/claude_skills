# Feature Context: Pipeline Completion-to-Closure Enforcement

**Date**: 2026-03-17
**Backlog Item**: [#762](https://github.com/Jamie-BitFlight/claude_skills/issues/762)
**Research Sources**: [Gap 1](./../.claude/reports/process-gap-1-completion-evidence.md), [Gap 2](./../.claude/reports/process-gap-2-enforcement-point.md), [Gap 3](./../.claude/reports/process-gap-3-reconciliation.md), [Gap 4](./../.claude/reports/process-gap-4-resolve-gate.md), [Impact Radius](./../.claude/reports/groom-762-impact-radius.md), [Fact-Check](./../.claude/reports/groom-762-fact-check.md)

---

## 1. Problem Space

The SAM pipeline (`/add-new-feature` -> `/implement-feature` -> `/complete-implementation` -> `/work-backlog-item resolve`) has four structural gaps in the completion-to-closure chain. These gaps allow quality gates to be bypassed, issues to close without verification, and local state to diverge from GitHub.

### Gap 1: No Durable Completion Evidence

`/complete-implementation` runs 6 quality gate phases (code review, feature verification, integration check, doc drift audit, service docs, context refinement) but produces no durable, queryable signal that it ran. The closest artifact is `plan/TN-verification-{slug}.yaml`, but that is created by `tn-verification-gate` *before* `/complete-implementation` runs and only covers structured acceptance criteria -- not the 6 quality phases themselves.

No `status:verified` or `status:quality-gates-passed` GitHub label exists. No `Plan.quality_gates_completed` field exists in `sam_schema`. The `resolve_github_issue()` function closes issues and writes a structured comment, but nothing in the pipeline records that quality gates actually passed.

SOURCE: [Gap 1 report](./../.claude/reports/process-gap-1-completion-evidence.md) sections 1.1-1.6

### Gap 2: Premature Issue Closure via Task-Level `Fixes #N`

GitHub issues auto-close when a commit containing `Fixes #N` merges to the default branch. Three independent sources add this trailer:

1. `/complete-implementation` Final Step (line 300 of SKILL.md) -- the intended and correct location
2. `/work-backlog-item` (SKILL.md lines 343, 366) -- instructs agents to include `Fixes #N` in any commit during implementation
3. `swarm-task-planner` -- bakes `Fixes #N` directly into per-task acceptance criteria in generated plan files (observed in `plan/tasks-17-replace-glab-subprocess.md` lines 107, 110, 329, 341, 352, 358, 385, 395 and others)

Sources 2 and 3 cause task-level commits to close GitHub issues *before* `/complete-implementation` has a chance to run. This means quality gates are structurally bypassed for any multi-task plan.

Additionally, no branch protection exists on `main` (confirmed: `gh api repos/.../branches/main/protection` returns 404). Direct pushes bypass all CI checks.

SOURCE: [Gap 2 report](./../.claude/reports/process-gap-2-enforcement-point.md) sections 1-4, [Fact-Check](./../.claude/reports/groom-762-fact-check.md) Claims 1, 6

### Gap 3: Closed GitHub Issues Invisible to Local Reconciliation

`refresh_local_cache_from_github()` in `operations.py` (line 987) fetches `state="open"` issues only:

```python
issues = repo_obj.get_issues(state="open", labels=label_objs or GithubObject.NotSet)
```

When a GitHub issue is closed externally (via merged PR with `Fixes #N`, manual close, or stale-bot), the local `.claude/backlog/` file is never updated. `backlog_list --from-github` does not detect these closures. `backlog_pull` *does* sync status from GitHub when called explicitly, but it is never called automatically.

**21 items drifted in the session that discovered this issue** -- closed on GitHub, open locally. Items included `#714`, `#300`, `#330`, `#340`, `#426`, `#463` and 15 others. Root cause: external closure via merged PRs with `Fixes #N` trailers from task-level commits, combined with `refresh_local_cache_from_github` never fetching closed issues.

SOURCE: [Gap 3 report](./../.claude/reports/process-gap-3-reconciliation.md) sections 1-4

### Gap 4: No Verification Gate on `/work-backlog-item resolve`

The resolve path in `close-resolve-procedure.md` runs three gates before calling `backlog_resolve`:

- Step 9c: Plan checklist validation (if plan exists)
- Step 9d: Acceptance criteria verification
- Step 9e: Open PR check

None of these verify that `/complete-implementation` actually ran. An item with a plan file can be resolved without quality gates ever executing. The `backlog_view` tool already returns `labels` in its response (zero additional API calls needed), but no step checks for a verification label.

The `backlog_resolve` MCP tool already has a `force: bool` parameter (currently used to bypass the open PR check). This parameter can be extended to also bypass a verification gate.

SOURCE: [Gap 4 report](./../.claude/reports/process-gap-4-resolve-gate.md) sections 1-5

---

## 2. Stakeholders

### Users (Human Operators)

- Cannot trust `backlog_list` output -- closed issues appear open (21 items drifted)
- Quality gate evidence is lost -- no way to verify whether code review, integration check, or doc drift audit ran for a resolved item
- Resolve decisions proceed without verification that work was reviewed
- Must manually run `backlog_pull` to detect closed issues

### Agents (AI Sub-agents)

- `swarm-task-planner` currently generates `Fixes #N` in task acceptance criteria, causing premature closure
- Task agents executing `/start-task` include `Fixes #N` in commits when instructed by plan files
- `/complete-implementation` agents run quality gates but produce no queryable record
- `/work-backlog-item` agents resolve items without checking for quality gate completion

### CI System (GitHub Actions)

- `code-quality.yml` runs lint, typecheck, and test jobs but has no label-checking job
- `backlog-sync.yml` is push-only (local -> GitHub); no pull or reconciliation step
- No scheduled workflow detects premature issue closure
- No branch protection on `main` -- CI checks are advisory only

### Backlog System (MCP Server + CLI)

- `refresh_local_cache_from_github()` structurally cannot detect closed issues
- `backlog_sync` pushes local state to GitHub but never pulls closure state back
- `backlog_pull` can sync individual items but is never invoked automatically
- State machine supports terminal states (`done`, `resolved`, `closed`) but has no automated transition for "GitHub closed this issue externally"

---

## 3. Desired Outcome

Four user-approved design decisions (made via interactive gap analysis, session 2026-03-16):

**Decision 1 (Gap 1)**: `/complete-implementation` applies a `status:verified` GitHub label to the backlog issue after all 6 quality gate phases pass. This is the durable, queryable completion signal. Pattern: copy from `apply_status_in_progress()` in `github.py` lines 277-293 (~12 lines).

**Decision 2 (Gap 2)**: Restrict `Fixes #N` to `/complete-implementation` Final Step only. Remove the instruction from `/work-backlog-item` SKILL.md (lines 343, 366). Add explicit prohibition to `/start-task` SKILL.md. Remove `Fixes #N` generation from `swarm-task-planner` agent (both `python3-development` and `development-harness` variants). Add a scheduled GitHub Actions workflow to audit recently closed issues that lack `status:verified` and re-open or flag them.

**Decision 3 (Gap 3)**: Fix `refresh_local_cache_from_github()` to fetch both `state="open"` and `state="closed"` issues (~10-15 lines in `operations.py`). This makes `backlog_list --from-github` detect externally closed issues without requiring a separate `backlog_pull` call.

**Decision 4 (Gap 4)**: Add a `status:verified` gate to `/work-backlog-item resolve` between steps 9a and 9c in `close-resolve-procedure.md` (~8-10 lines). The gate checks `result["labels"]` from the already-loaded `backlog_view` response (zero additional API calls). Items without a `**Plan**:` field skip the check (covers docs-only, research, manual, and `--quick` items). The existing `--force` parameter on `backlog_resolve` bypasses the gate for historical items or explicit overrides.

---

## 4. Constraints

### Implementation Order

Gap 1 must complete first. Gaps 2, 3, and 4 depend on the `status:verified` label existing:

- Gap 4 checks for the label -- deploying Gap 4 before Gap 1 would block all resolves
- Gap 2's CI audit workflow checks for the label on closed issues
- Gap 3 is independent of the label but logically follows Gap 1 (detecting closed issues is meaningful only when the closure should have been preceded by verification)

After Gap 1, Gaps 2, 3, and 4 can proceed in parallel.

### Backward Compatibility

- **Historical items**: All currently closed issues lack `status:verified` (the label does not exist yet). The Gap 4 gate must not retroactively block resolution of items created before the label is defined. The `--force` bypass and the "no Plan field -> skip check" conditional handle this.
- **In-flight plan files**: 20+ existing `plan/tasks-*.md` files have `Fixes #N` baked into acceptance criteria. These are static generated artifacts that cannot be retroactively changed by modifying `swarm-task-planner`. Each active plan must be manually audited and edited before task agents execute them.
- **Non-SAM items**: Items resolved via `--quick` mode, documentation-only changes, research items, and manually merged PRs never pass through `/complete-implementation`. The Gap 4 gate skips the check when no `**Plan**:` field exists, matching the existing Step 9c conditional.

### No New External Dependencies

All implementations use existing infrastructure:
- GitHub API via PyGithub (already in use for label operations, issue state management)
- GitHub Actions (existing `code-quality.yml` and `backlog-sync.yml` patterns)
- `sam_schema` models (existing `Task` and `Plan` classes)
- MCP tool schema (`backlog_resolve` already has `force` parameter)

---

## 5. Open Questions

### Branch Protection

No branch protection exists on `main`. Any CI-based enforcement (label check job in `code-quality.yml`) can be bypassed by pushing directly to `main`. The gap reports document this constraint but do not resolve it. Enabling branch protection with `quality-gate` as a required status check would close this bypass, but that is a repository settings change outside the scope of code changes.

**Decision needed**: Should branch protection be enabled as part of this feature, or deferred?

### Fact-Check Inconclusive Items

Three claims from the backlog item description were marked INCONCLUSIVE by the fact-check report because the haiku-based agent did not read the Python source files:

1. `refresh_local_cache_from_github` fetches `state="open"` only (line 987 unverified)
2. `apply_status_in_progress` is a 12-line template at `github.py:277` (line number unverified)
3. `backlog_resolve` has a `force` flag (function location unverified)

These claims were verified in the original gap analysis sessions via direct source code observation. The fact-check's INCONCLUSIVE status reflects the checker's limitations, not actual uncertainty. However, exact line numbers should be re-confirmed at implementation time since the codebase may have changed.

### Audit Workflow Trigger

The Gap 2 CI audit workflow could trigger on schedule (e.g., daily cron), on PR merge, or on push to main. The gap reports suggest a daily schedule but do not commit to a specific trigger. Trade-off: scheduled runs have detection lag (up to 24 hours); PR-merge triggers are more timely but add CI cost to every merge.

### `--force` User Exposure

The `force` parameter exists in the MCP tool schema but is not mentioned as a user-facing argument in `/work-backlog-item` SKILL.md or its `argument-hint` frontmatter. Exposing it requires documenting the syntax for users.

---

## 6. Related Systems

SOURCE: [Impact Radius report](./../.claude/reports/groom-762-impact-radius.md)

### Primary Files (10 files, ~74 lines of changes)

**Backlog core infrastructure**:
- `.claude/skills/backlog/backlog_core/github.py` -- label operations; add `apply_status_verified()`
- `.claude/skills/backlog/backlog_core/operations.py` -- `refresh_local_cache_from_github()` line 987; fix `state="open"` limitation

**Skills**:
- `plugins/python3-development/skills/complete-implementation/SKILL.md` -- add final step to apply `status:verified` label
- `plugins/python3-development/skills/start-task/SKILL.md` -- add prohibition on task-level `Fixes #N`
- `.claude/skills/work-backlog-item/SKILL.md` -- remove `Fixes #N` instruction (lines 343, 366); document `--force` flag
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md` -- add verified label gate between steps 9a and 9c

**Agents**:
- `plugins/python3-development/agents/swarm-task-planner.md` -- remove `Fixes #N` generation in task acceptance criteria
- `plugins/development-harness/agents/swarm-task-planner.md` -- same removal

**Documentation**:
- `.claude/rules/local-workflow.md` -- add note that `Fixes #N` belongs only in `/complete-implementation` final commit

**CI**:
- `.github/workflows/` -- new audit workflow file (~35-50 lines)

### Secondary Files (test + audit targets)

**Test files** (4 files, ~12-15 new test functions):
- `.claude/skills/backlog/tests/test_backlog_core_github.py`
- `.claude/skills/backlog/tests/test_backlog_core_operations.py`
- `.claude/skills/backlog/tests/test_scenarios.py`
- `.claude/skills/backlog/tests/test_reconciliation.py`

**Plan files requiring manual audit** (20+ files):
- `plan/tasks-{N}-*.md` files with baked-in `Fixes #N` in acceptance criteria
- Examples: `plan/tasks-17-replace-glab-subprocess.md`, `plan/tasks-1-backlog-cli-dedup.md`, `plan/tasks-1-context-logging-progress.md`

### Broader Impact Radius

47 files total across all gaps (from impact radius report):
- 6 core backlog infrastructure files
- 8 skill files (SKILL.md + references)
- 2 agent files
- 5 documentation files
- 8 test files
- 4 GitHub workflow files
- 14+ plan/feature files (static, audit-only)

---

## References

1. [Gap 1 -- Completion Evidence](./../.claude/reports/process-gap-1-completion-evidence.md) (2026-03-16)
2. [Gap 2 -- Enforcement Point](./../.claude/reports/process-gap-2-enforcement-point.md) (2026-03-16)
3. [Gap 3 -- Reconciliation](./../.claude/reports/process-gap-3-reconciliation.md) (2026-03-16)
4. [Gap 4 -- Resolve Gate](./../.claude/reports/process-gap-4-resolve-gate.md) (2026-03-16)
5. [Impact Radius](./../.claude/reports/groom-762-impact-radius.md) (2026-03-17)
6. [Fact-Check](./../.claude/reports/groom-762-fact-check.md) (2026-03-17)
7. [Backlog Item #762](./../.claude/backlog/p1-pipeline-completion-to-closure-has-no-enforcement-quality-ga.md)
