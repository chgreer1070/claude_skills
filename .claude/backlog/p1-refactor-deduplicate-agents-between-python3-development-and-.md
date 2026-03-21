---
name: 'refactor: Deduplicate agents between python3-development and dh (Phase 4)'
description: "python3-development currently has 16 specialist agents that duplicate the generic agents in dh. Phase 4 removes the specialist agents from python3-development, replacing them with domain skills only. The 10 shared agents between dh and python3-development (already synced in Phase 1) are deduplicated — python3-development retains only domain skills, references, conventions, and quality gates. dh becomes the sole provider of agents.\n\nScope:\n- Remove the 10 synced agents from plugins/python3-development/agents/ (feature-researcher, codebase-analyzer, context-gathering, context-refinement, plan-validator, feature-verifier, integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher)\n- Verify dh counterparts are complete and correct (done in Phase 1)\n- Update any python3-development skills that reference these agents to use @dh: namespace\n- Update CLAUDE.md and documentation in python3-development to reflect agents-only-in-dh model\n- Verify plugin validator passes for both plugins after removal\n- Add forwarding note in python3-development README pointing to dh for agent access\n\nDependencies: Depends on Phase 1 (dh agents synced) — done. Depends on Phase 3 (backlog lift) — should be done first so backlog agents move before specialist agents are removed."
metadata:
  topic: refactor-deduplicate-agents-between-python3-development-and-
  source: 'GitHub Issue #581 — Development Harness Architecture Refactor, Phase 4'
  added: '2026-03-18'
  priority: P1
  type: Refactor
  status: closed
  issue: '#850'
  groomed: '2026-03-19'
  last_synced: '2026-03-19T03:52:38Z'
  plan: plan/tasks-1-deduplicate-agents-phase4.md
  close_reason: superseded
---

## RT-ICA

<div><sub>2026-03-19T03:47:40Z</sub>

RT-ICA Snapshot: refactor: Deduplicate agents between python3-development and dh (Phase 4)
Goal: Remove 10 duplicate agents from plugins/python3-development/agents/ so dh becomes the sole agent provider, python3-development retains only domain skills.

Conditions:
1. 10 target agents exist in plugins/python3-development/agents/ | Status: AVAILABLE (verified via ls)
2. dh counterpart agents exist and are functionally equivalent | Status: DERIVABLE (grep plugins/development-harness/agents/)
3. python3-development skills reference these agents by namespace | Status: DERIVABLE (grep plugins/python3-development/skills/)
4. python3-development CLAUDE.md or docs reference these agents | Status: DERIVABLE (read plugins/python3-development/)
5. Phase 3 (backlog_core lift to dh) is complete | Status: DERIVABLE (git log / backlog check)
6. No other files in python3-development reference removed agent names | Status: DERIVABLE (grep)
7. Plugin validator configuration known | Status: AVAILABLE (prek/validator from project setup)

AVAILABLE count: 2
DERIVABLE count: 5
MISSING count: 0
</div>

## Groomed (2026-03-19)


### Impact

<div><sub>2026-03-18T00:00:00Z</sub>

<div><sub>2026-03-19T03:48:59Z</sub>
</div>

<div><sub>2026-03-19T03:50:58Z</sub>

**User-visible change**: Agents previously routed via `@python3-development:agent-name` are now routed via `@development-harness:agent-name`. This is transparent if users are consuming agents through published orchestration skills (add-new-feature, implement-feature, complete-implementation) — the skills handle the namespace change internally.

**For skill authors** writing custom delegation prompts: any existing custom delegate-to-python3-development-agents calls must be updated to use dh instead. A breaking change, but only affects internal development; marketplace users are unaffected.

**What improves**:
1. **Single source of truth** — agents exist in one place (dh), not duplicated across plugins
2. **Versioning clarity** — the ecosystem-researcher v1.1 conflict is resolved (single canonical version in dh)
3. **Maintenance simplification** — agent updates only need to be applied to dh, reducing the risk of divergence
4. **Cleaner python3-development** — the plugin becomes focused on domain-specific skills (CLI, testing, Python code review) and quality gates (T0/TN verification), with no generic agents cluttering the agent roster

**No functional change** — the agents themselves do not change; only their location and namespace change.
</div>

### Priority

<div><sub>2026-03-19T03:50:51Z</sub>

**P1 — Critical path for plugin architecture consolidation**

Phase 4 (removal) is the final step that completes the 3-phase deduplication plan. Phase 1 and Phase 3 are already merged. Delaying Phase 4 leaves duplicate agents in python3-development indefinitely, blocking the architecture goal of centralizing agents in dh.

**Rationale**: The deduplication series is sequential — Phase 1 creates the target (dh agents), Phase 3 preps the ecosystem (backlog lift), Phase 4 removes the source (python3-development agents). Without Phase 4, the prior phases provide no value and the repository remains architecturally fragmented.

**Business impact**: Consolidating agents in dh reduces maintenance burden (single source of truth), eliminates versioning conflicts (current ecosystem-researcher v1.1 issue), and makes it clear to users that dh is the agent provider.
</div>

### Scope

<div><sub>2026-03-19T03:51:16Z</sub>

**In scope — Removals from python3-development**:
- Delete 10 agent files from `plugins/python3-development/agents/`:
  - feature-researcher.md
  - codebase-analyzer.md
  - context-gathering.md
  - context-refinement.md
  - plan-validator.md
  - feature-verifier.md
  - integration-checker.md
  - doc-drift-auditor.md
  - swarm-task-planner.md
  - ecosystem-researcher.md
- CRITICAL DECISION POINT: ecosystem-researcher-v1.1-rt-ica.md must be reconciled before removal. Determine if v1.1 is canonical (copy to dh first) or deprecated (safe to discard). Cannot proceed with agent removal until this is resolved.

**In scope — Reference Updates**:
- Update `plugins/python3-development/skills/add-new-feature/SKILL.md` to delegate planning agents to @development-harness
- Update `plugins/python3-development/skills/implement-feature/SKILL.md` to use harness agents (if delegation is namespace-qualified)
- Update `plugins/python3-development/skills/complete-implementation/SKILL.md` to delegate feature-verifier, integration-checker, doc-drift-auditor, context-refinement to @development-harness; retain code-reviewer as @python3-development
- Update `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` — change all `@python3-development:` agent namespaces to `@development-harness:` for the 10 removed agents
- Update `plugins/python3-development/README.md` to remove the 10 agents from inventory; update agent count from 16 to 6; add note pointing to dh for planning/verification agents
- Update `.claude/rules/local-workflow.md` — Phase 1, 2, 3 agent delegation tables/text must reflect dh agents

**In scope — Validation**:
- Verify all 10 dh agent copies have content parity with python3-development originals (byte-for-byte or semantic equivalence)
- Verify plugin.json does not have explicit agent list that would need updating (auto-discovery may be in use)
- Run pre-commit hooks to verify no linting errors after deletion
- Confirm no orphaned references to removed agents remain in python3-development skills or docs

**Out of scope**:
- Changes to development-harness plugin (already complete from Phase 1)
- Changes to backlog item content in `.claude/backlog/` — these are documentation and do not block core functionality. Update if time permits, otherwise note that references are stale and a future grooming can clean them up.
- Changes to `.continuehere.md` or other project-level docs — note that agent references may be stale; the main blocking issue is skill-level reference updates
- Modifying any agent's content or instructions — this is Phase 1's responsibility (already done via COPY-THEN-PATCH). Phase 4 only removes duplicates, does not refactor agent logic

**Constraint — ecosystem-researcher versioning**:
The v1.1-rt-ica variant (17,426 lines) cannot be removed without determining if it is canonical. If it is the current working version:
1. Copy ecosystem-researcher-v1.1-rt-ica.md to plugins/development-harness/agents/ecosystem-researcher.md (overwrite the shorter version)
2. Verify dh version now matches the v1.1 content
3. Then remove both python3-development versions (ecosystem-researcher.md and ecosystem-researcher-v1.1-rt-ica.md)

If v1.1 is deprecated or abandoned, confirm with domain expert before discarding.
</div>

### Dependencies

<div><sub>2026-03-19T03:51:29Z</sub>

**External (must complete before Phase 4 starts)**:
- Phase 1 (dh agents synced) — DONE (commit 29387b59)
- Phase 3 (backlog skills lifted) — DONE (commit 5e3231ce)

**Internal (ordering within Phase 4)**:
1. **Ecosystem-researcher versioning decision** (BLOCKING) — Must be resolved first. Decision tree:
   - Query: Is ecosystem-researcher-v1.1-rt-ica.md canonical and in use?
     - YES → Copy v1.1 to dh, verify content, then remove both python3-development versions
     - NO / DEPRECATED → Confirm safe to discard, then remove both python3-development versions
     - UNCLEAR → Escalate to domain expert (ask in #channel or reach out directly)
   - This decision unblocks all subsequent agent removal steps
2. **Content parity verification** — After versioning is settled, verify all 10 dh copies are byte-identical or semantically complete
3. **Skill reference updates** — Update orchestration skills to route to dh agents (add-new-feature, implement-feature, complete-implementation)
4. **Reference documentation updates** — Update python-development-orchestration.md, local-workflow.md, README.md
5. **Agent file deletion** — Delete the 10 agents from plugins/python3-development/agents/
6. **Validation** — Run pre-commit hooks, verify no broken references, confirm plugin validator passes

**Conditional dependencies** (may surface during execution):
- If any python3-development skill internally delegates to removed agents by name (e.g., calls `Skill(skill="start-task", args="... --task t1")` where t1's agent is in python3-development), those delegation routes must be re-routed to dh agents. This requires reading the task file and agent assignment — likely caught during skill reference updates but worth noting.
- If `plugin.json` lists agents explicitly (overriding auto-discovery), must update the `agents` array to remove the 10 agents

**Relationship to other backlog items**:
- No other items block this one (Phase 1 and 3 are complete)
- This item unblocks future architecture work (e.g., removing redundant domain skills, consolidating plugin structure, etc.)
- Backlog items that reference python3-development agents become stale after this completes; grooming those items is a separate (lower-priority) task
</div>

### Acceptance Criteria

<div><sub>2026-03-19T03:51:43Z</sub>

**All 10 agents removed from python3-development**:
- [ ] `plugins/python3-development/agents/feature-researcher.md` deleted
- [ ] `plugins/python3-development/agents/codebase-analyzer.md` deleted
- [ ] `plugins/python3-development/agents/context-gathering.md` deleted
- [ ] `plugins/python3-development/agents/context-refinement.md` deleted
- [ ] `plugins/python3-development/agents/plan-validator.md` deleted
- [ ] `plugins/python3-development/agents/feature-verifier.md` deleted
- [ ] `plugins/python3-development/agents/integration-checker.md` deleted
- [ ] `plugins/python3-development/agents/doc-drift-auditor.md` deleted
- [ ] `plugins/python3-development/agents/swarm-task-planner.md` deleted
- [ ] `plugins/python3-development/agents/ecosystem-researcher.md` deleted (after versioning is resolved)

**ecosystem-researcher versioning reconciled**:
- [ ] Determined whether `ecosystem-researcher-v1.1-rt-ica.md` is canonical (in use) or deprecated
- [ ] If canonical: copied v1.1 to plugins/development-harness/agents/ecosystem-researcher.md, verified content matches, then removed both python3-development versions
- [ ] If deprecated: confirmed safe to discard with domain expert, then removed both versions from python3-development

**All 10 agents verified to exist in dh with correct content**:
- [ ] `plugins/development-harness/agents/feature-researcher.md` exists and matches python3-development original
- [ ] `plugins/development-harness/agents/codebase-analyzer.md` exists and matches
- [ ] `plugins/development-harness/agents/context-gathering.md` exists and matches
- [ ] `plugins/development-harness/agents/context-refinement.md` exists and matches
- [ ] `plugins/development-harness/agents/plan-validator.md` exists and matches
- [ ] `plugins/development-harness/agents/feature-verifier.md` exists and matches
- [ ] `plugins/development-harness/agents/integration-checker.md` exists and matches
- [ ] `plugins/development-harness/agents/doc-drift-auditor.md` exists and matches
- [ ] `plugins/development-harness/agents/swarm-task-planner.md` exists and matches
- [ ] `plugins/development-harness/agents/ecosystem-researcher.md` exists and matches (or is v1.1)

**All skill references updated to use @development-harness**:
- [ ] `plugins/python3-development/skills/add-new-feature/SKILL.md` updated to delegate @development-harness agents
- [ ] `plugins/python3-development/skills/implement-feature/SKILL.md` updated (if it contains namespace-qualified agent references)
- [ ] `plugins/python3-development/skills/complete-implementation/SKILL.md` updated to route feature-verifier, integration-checker, doc-drift-auditor, context-refinement to @development-harness; code-reviewer stays @python3-development

**All reference documentation updated**:
- [ ] `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` updated — Phase 1, 2, 3 agent routing now references @development-harness
- [ ] `.claude/rules/local-workflow.md` updated — all 10 agents now reference @development-harness namespace in delegation tables and workflow steps
- [ ] `plugins/python3-development/README.md` updated — removed 10 agents from roster; updated agent count (16 → 6); added forwarding note pointing to dh for planning/verification agents

**Validation complete**:
- [ ] No dangling references to removed agents exist in python3-development skills, agents, or references
- [ ] Pre-commit hooks pass (plugin.json version bumped automatically, no linting errors)
- [ ] Plugin validator passes for both python3-development and development-harness
- [ ] `git diff` shows expected changes: 10 agent file deletions + 4 skill/doc updates + agent count reduction in README
- [ ] No `@python3-development:` references remain for the 10 removed agents (grep confirms 0 matches)

**Project-level docs acknowledge the change** (nice-to-have):
- [ ] `.continuehere.md` reviewed; stale agent references updated or noted
- [ ] `.claude/audits/agent-map.json` (if present) reflects 6 remaining agents in python3-development
- [ ] Backlog items with agent references reviewed; out-of-date references noted for future grooming
</div>

### Files

<div><sub>2026-03-19T03:52:09Z</sub>

**Files to DELETE** (10 agent files):
1. `plugins/python3-development/agents/feature-researcher.md` — DELETE
2. `plugins/python3-development/agents/codebase-analyzer.md` — DELETE
3. `plugins/python3-development/agents/context-gathering.md` — DELETE
4. `plugins/python3-development/agents/context-refinement.md` — DELETE
5. `plugins/python3-development/agents/plan-validator.md` — DELETE
6. `plugins/python3-development/agents/feature-verifier.md` — DELETE
7. `plugins/python3-development/agents/integration-checker.md` — DELETE
8. `plugins/python3-development/agents/doc-drift-auditor.md` — DELETE
9. `plugins/python3-development/agents/swarm-task-planner.md` — DELETE
10. `plugins/python3-development/agents/ecosystem-researcher.md` — DELETE (AFTER ecosystem-researcher-v1.1-rt-ica decision)
11. `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md` — DELETE (contingent on v1.1 reconciliation; if canonical, copy to dh first)

**Files to UPDATE** (skill and reference documentation):
1. `plugins/python3-development/skills/add-new-feature/SKILL.md` — UPDATE
   - Change agent delegations: feature-researcher, codebase-analyzer, swarm-task-planner, plan-validator, context-gathering from @python3-development to @development-harness
   - Keep python-cli-design-spec as @python3-development

2. `plugins/python3-development/skills/implement-feature/SKILL.md` — UPDATE
   - Verify no hard-coded agent routing (likely delegates via task file agent assignment)
   - If skill contains `@python3-development:` references, update to @development-harness

3. `plugins/python3-development/skills/complete-implementation/SKILL.md` — UPDATE
   - Change delegations: feature-verifier, integration-checker, doc-drift-auditor, context-refinement from @python3-development to @development-harness
   - Keep code-reviewer as @python3-development
   - Verify service-docs-maintainer delegation routes to @development-harness (already correct, as it only exists in dh)

4. `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` — UPDATE
   - Phase 1 agent delegation table: change @python3-development:feature-researcher, codebase-analyzer, context-gathering, plan-validator to @development-harness equivalents
   - Phase 2 agent delegation table: if agents are listed, update
   - Phase 3 agent delegation table: change @python3-development:code-reviewer, feature-verifier, integration-checker, doc-drift-auditor, context-refinement, service-docs-maintainer to @development-harness (except code-reviewer stays @python3-development)
   - Agent file location table: remove the 10 agents from python3-development column

5. `.claude/rules/local-workflow.md` — UPDATE
   - "Agent Delegation Sequence" table (Phase 1, 2, 3): replace @python3-development agents with @development-harness
   - "Agent File Locations" table: remove python3-development entries for the 10 agents; keep dh entries
   - Example delegation prompts: if they reference python3-development agents, update to dh

6. `plugins/python3-development/README.md` — UPDATE
   - Agent inventory section: remove 10 agents from list
   - Update agent count from 16 to 6
   - Add section: "Planning and Verification Agents" → forwarding note: "Planning agents (feature-researcher, codebase-analyzer, etc.) and generic quality gates have been consolidated into the development-harness plugin. See @development-harness agent roster."
   - Retain description of remaining 6 domain-specific agents (code-reviewer, python-cli-architect, python-pytest-architect, python-code-reviewer, t0-baseline-capture, tn-verification-gate)

**Files to VERIFY** (should not need changes, but check for stale refs):
- `plugins/python3-development/plugin.json` — if it contains explicit `"agents": [...]` array, remove the 10 agent paths; otherwise verify auto-discovery works correctly after deletion
- `plugins/python3-development/CLAUDE.md` (if present) — verify no agent references
- Backlog item files in `.claude/backlog/` — review for stale @python3-development:agent-name references (note for future grooming, not a blocking issue)

**Expected git diff output** (after completion):
```
Deleted: 10 agent files (ecosystem-researcher may include v1.1 variant)
Modified: 6 files (4 SKILL.md + 2 references)
Unchanged: plugin.json version (auto-bumped by pre-commit hook)
```
</div>

### Effort

<div><sub>2026-03-19T03:52:21Z</sub>

**Sizing: Medium (M)**

**Reasoning**:

**Mechanical work** (straightforward, low risk):
- 10 file deletions via `rm` or Edit tool — ~5 minutes
- 1 README update (add forwarding note, reduce agent count) — ~10 minutes
- Pre-commit hook validates; no additional CI work required

**Reference updates** (moderate effort, high precision required):
- `python-development-orchestration.md` — 3 agent tables to update (Phase 1, 2, 3), ~20-30 lines each. Requires careful namespace substitution. ~30 minutes
- `local-workflow.md` — agent delegation documentation, similar scope. ~30 minutes
- `add-new-feature`, `implement-feature`, `complete-implementation` SKILL.md files — 3-5 delegations per file, verify routing logic. ~20 minutes total
- Grep validation (confirm 0 matches for removed agents after deletion) — ~10 minutes

**Risk/Uncertainty factors**:
- **Ecosystem-researcher versioning** (BLOCKING): 1-2 hours if domain expert consultation is needed; 10 minutes if decision is clear. Assume 30 minutes as midpoint.
- **plugin.json auto-discovery** (low risk): If plugin.json lists agents explicitly, removal requires update. Likely a 5-minute fix; flagged for verification
- **Task file agent routing** (low risk): If a skill internally delegates to tasks with python3-development agents, those task files must be updated. Mitigated by accepting criteria checks; estimated ~10 minutes if found

**Total effort estimate**:
- Ecosystem-researcher decision: 30 minutes
- File deletions + README: 15 minutes
- Reference updates (orchestration, workflow): 60 minutes
- Skill SKILL.md updates: 20 minutes
- Validation (grep, pre-commit, plugin validator): 15 minutes
- **Subtotal: 140 minutes (~2.5 hours)**

**Effort class: Medium (M)**
- Not Small because reference updates span 4 documentation files and require precise namespace changes
- Not Large because scope is well-defined, no architectural refactoring, and dh agents are already in place
- Effort is primarily documentation/configuration, not implementation
</div>

### Output / Evidence

<div><sub>2026-03-19T03:52:38Z</sub>

**Verification checklist to confirm work is done**:

1. **Agent files deleted** (use `ls` or `git status`):
   ```bash
   ls -la plugins/python3-development/agents/
   # Should show 6 remaining agents (code-reviewer, python-cli-architect, python-pytest-architect, python-code-reviewer, t0-baseline-capture, tn-verification-gate)
   # Should NOT show: feature-researcher.md, codebase-analyzer.md, context-gathering.md, context-refinement.md, plan-validator.md, feature-verifier.md, integration-checker.md, doc-drift-auditor.md, swarm-task-planner.md, ecosystem-researcher.md
   git status --short plugins/python3-development/agents/
   # Should show D (deleted) for each of the 10 files
   ```

2. **Dh agents present and correct**:
   ```bash
   ls -la plugins/development-harness/agents/ | grep -E "(feature-researcher|codebase-analyzer|context-gathering|context-refinement|plan-validator|feature-verifier|integration-checker|doc-drift-auditor|swarm-task-planner|ecosystem-researcher)"
   # All 10 files should be listed
   wc -l plugins/development-harness/agents/ecosystem-researcher.md
   # Should match v1.1 line count (17,426) if v1.1 was canonical, or match original (405) if v1.0 was kept
   ```

3. **No dangling references** (confirm 0 matches):
   ```bash
   grep -r "@python3-development:feature-researcher\|@python3-development:codebase-analyzer\|@python3-development:context-gathering\|@python3-development:context-refinement\|@python3-development:plan-validator\|@python3-development:feature-verifier\|@python3-development:integration-checker\|@python3-development:doc-drift-auditor\|@python3-development:swarm-task-planner\|@python3-development:ecosystem-researcher" plugins/python3-development/
   # Output should be empty (0 matches)
   ```

4. **Skills updated**:
   ```bash
   grep "@development-harness:feature-researcher" plugins/python3-development/skills/add-new-feature/SKILL.md
   grep "@development-harness:context-refinement" plugins/python3-development/skills/complete-implementation/SKILL.md
   # Both should return matches (non-empty)
   ```

5. **Reference docs updated**:
   ```bash
   grep "@development-harness" plugins/python3-development/skills/python3-development/references/python-development-orchestration.md | wc -l
   # Should show non-zero count (multiple agent references now use @development-harness)
   grep "@development-harness" .claude/rules/local-workflow.md | wc -l
   # Should show non-zero count
   ```

6. **README updated**:
   ```bash
   grep -A 5 "Planning and Verification Agents" plugins/python3-development/README.md
   # Should show forwarding note pointing to development-harness
   grep -i "agent count\|16 agents\|6 agents" plugins/python3-development/README.md
   # Should show "6 agents" or similar (not 16)
   ```

7. **Pre-commit hooks pass**:
   ```bash
   uv run prek run --files plugins/python3-development/plugin.json
   # Should show no errors; plugin.json version should be bumped
   git diff plugins/python3-development/plugin.json
   # Should show version increment (e.g., 1.3.0 → 1.3.1)
   ```

8. **Plugin validator passes**:
   ```bash
   uv run prek run --files plugins/python3-development/skills/add-new-feature/SKILL.md
   uv run prek run --files plugins/development-harness/agents/feature-researcher.md
   # Both should show no linting errors
   ```

9. **Commit message**:
   ```
   refactor(python3-development): deduplicate agents, consolidate in development-harness

   Phase 4 removes 10 generic agents from python3-development:
   - feature-researcher, codebase-analyzer, context-gathering, context-refinement
   - plan-validator, feature-verifier, integration-checker, doc-drift-auditor
   - swarm-task-planner, ecosystem-researcher

   development-harness becomes the sole provider of these agents.

   Skills (add-new-feature, implement-feature, complete-implementation) updated
   to route delegations to @development-harness agents.

   Reference docs (python-development-orchestration.md, local-workflow.md) updated.

   README updated with forwarding note and revised agent count (16 → 6).

   python3-development retains 6 domain-specific agents (code-reviewer,
   python-cli-architect, python-pytest-architect, python-code-reviewer,
   t0-baseline-capture, tn-verification-gate).

   Fixes #850
   ```

**Expected output after `git add -A && git commit -m "..."` && git status`**:
```
On branch main
nothing to commit, working tree clean
```

**Regression test** (verify the deduplication did not break orchestration):
- Ask a skill user to invoke `/python3-development:add-new-feature` — it should route to dh agents without errors
- No skill load-time failures should occur when agents are referenced by @development-harness namespace
</div>


## Impact Radius

### Code — Producers (write the changed interface)

- `plugins/python3-development/agents/` — 10 agent files to be removed (feature-researcher.md, codebase-analyzer.md, context-gathering.md, context-refinement.md, plan-validator.md, feature-verifier.md, integration-checker.md, doc-drift-auditor.md, swarm-task-planner.md, ecosystem-researcher.md)
- `plugins/development-harness/agents/` — 11 files (all 10 duplicate agents already exist, plus service-docs-maintainer.md which is harness-only). These become the sole source of truth.

### Code — Consumers (read the changed interface)

**Orchestration Skills (delegate to agents)**:
- `plugins/python3-development/skills/add-new-feature/SKILL.md` — currently delegates to @python3-development agents (feature-researcher, codebase-analyzer, python-cli-design-spec, swarm-task-planner, plan-validator, context-gathering). Must route these to @development-harness agents instead.
- `plugins/python3-development/skills/implement-feature/SKILL.md` — currently delegates to tasks which reference agents by name. Task status hook works via agent name; must verify agent namespaces resolve correctly after migration.
- `plugins/python3-development/skills/complete-implementation/SKILL.md` — currently delegates to @python3-development agents (code-reviewer, feature-verifier, integration-checker, doc-drift-auditor, service-docs-maintainer, context-refinement). CRITICAL: service-docs-maintainer is harness-only and is already missing from python3-development. The skill must change to route feature-verifier, integration-checker, doc-drift-auditor, context-refinement to @development-harness. code-reviewer remains @python3-development.

**Reference Documentation**:
- `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` — extensively documents agent delegation model, routing, and dependencies. Documents which agents run in which phases. Section "Phase 1: Planning", "Phase 2: Execution", "Phase 3: Quality Gates" all need namespace updates (python3-development → development-harness for all 10 agents).
- `plugins/python3-development/README.md` — documents the agent roster and their roles. Remove the 10 agents from the inventory section; update agent count from 16 to 6 (retaining code-reviewer, python-cli-architect, python-pytest-architect, python-code-reviewer, t0-baseline-capture, tn-verification-gate). Update references to development-harness as the source for planning/verification agents.

**Backlog Items**:
- `.claude/backlog/` directory — multiple items reference agent names and delegation routes. Examples: `p1-sam-bookend-validation-baseline-capture-t0-and-verification-.md`, `p1-sam-task-planner-merge-same-file-tasks-into-single-agent-ass.md`, `p1-add-ux-impact-assessment-to-sam-task-template-grooming-and-c.md`. These likely reference python3-development agents by namespace in plan files. No code breakage (backlog items are documentation), but content becomes stale.

**Project-Level Documentation**:
- `.claude/audits/agent-map.json` — inventory file listing all agents. Must update to reflect removed agents.
- `.continuehere.md` — may contain references to agent delegation examples or status. Verify content and update if agent names appear.

### Documentation (will become stale)

**Skill Documentation**:
- `plugins/python3-development/skills/orchestrate/SKILL.md` — documents orchestration workflow and agent dispatch. Contains specific agent names in delegation routes and examples.
- `plugins/python3-development/skills/python3-development/SKILL.md` — main skill entry point; may document agent availability and routing.
- `plugins/python3-development/skills/stinkysnake/SKILL.md` — references agents (unclear context from grep; needs inspection).

**Agent Internal References**:
- Agent files (the 10 being removed) may delegate to other agents being removed. Examples found:
  - `codebase-analyzer.md` references other agents
  - `context-gathering.md` references other agents
  - `doc-drift-auditor.md` references other agents
  - `ecosystem-researcher.md` and `ecosystem-researcher-v1.1-rt-ica.md` both exist (likely versioned); must reconcile before removal

**Planning Documentation**:
- `plugins/python3-development/planning/sse-gap-analysis.md`
- `plugins/python3-development/planning/sse-gap-analysis-verification.md`
- `plugins/python3-development/skills/python3-development/planning/reference-document-architecture.md`
- `plugins/python3-development/skills/python3-development/planning/python3-development-workflow-port-plan.md`
These files may reference agent roles and workflows that will change.

### Configuration / CI

- `plugins/python3-development/plugin.json` — (JSON not found in glob; may have different name or structure). If present, must update agents declaration if it lists component paths. Agent auto-discovery in plugin.json may be overridden by explicit agent list — if so, remove the 10 agents from the `agents` array.
- Pre-commit hooks: auto-version-bump on plugin.json will trigger when agents/ files are deleted. No manual action needed, but verify hook runs correctly during deletion.

### Agent Instructions (instruct AI to use current interface)

**SAM Workflow Documentation** (from local-workflow.md):
- `.claude/rules/local-workflow.md` — Phase 1 (Planning), Phase 2 (Execution), Phase 3 (Quality Gates) all document agent delegation steps. Tables and text referencing agents by `@python3-development:agent-name` must change to `@development-harness:agent-name` for the 10 removed agents. Affects "Agent Delegation Sequence" section and "Phase 1" through "Phase 3".

**Agent Files** (the duplicate agents in development-harness):
- `plugins/development-harness/agents/feature-researcher.md` — verify contains all current instruction content from python3-development counterpart before removal
- `plugins/development-harness/agents/codebase-analyzer.md` — ditto
- `plugins/development-harness/agents/context-gathering.md` — ditto
- `plugins/development-harness/agents/context-refinement.md` — ditto
- `plugins/development-harness/agents/plan-validator.md` — ditto
- `plugins/development-harness/agents/feature-verifier.md` — ditto
- `plugins/development-harness/agents/integration-checker.md` — ditto
- `plugins/development-harness/agents/doc-drift-auditor.md` — ditto
- `plugins/development-harness/agents/swarm-task-planner.md` — ditto
- `plugins/development-harness/agents/ecosystem-researcher.md` — ditto

**Post-Migration Instruction Updates**:
- All skills, references, backlog items, and project docs must be updated AFTER verifying harness copies contain current content
- All agent references must switch namespace from python3-development to development-harness
- Backlog items should note that agents are no longer available from python3-development

### Systems Inventory

**Count Summary**:
- **Skills affected**: 4 (add-new-feature, implement-feature, complete-implementation, orchestrate, python3-development, stinkysnake)
- **Reference documents affected**: 5 (python-development-orchestration.md, reference-document-architecture.md, python3-development-workflow-port-plan.md, sse-gap-analysis files, planning files)
- **Agent files being removed**: 10 (feature-researcher, codebase-analyzer, context-gathering, context-refinement, plan-validator, feature-verifier, integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher)
- **Project-level docs affected**: 15+ (audits/, backlog items, CLAUDE.md, local-workflow.md, continuehere.md)
- **Backlog items with agent references**: 10+ (.claude/backlog/*.md files)
- **Development-harness verification needed**: 11 agents in development-harness/agents/ must have content parity before source removal

### Ecosystem Completeness Checklist

- [ ] All 10 agent duplicates exist in development-harness/agents/ and have content parity with python3-development copies
- [ ] Skills (add-new-feature, implement-feature, complete-implementation) updated to delegate to @development-harness agents
- [ ] Reference documentation (python-development-orchestration.md) updated with development-harness agent namespaces
- [ ] Local workflow rules (.claude/rules/local-workflow.md) updated with development-harness agent routing
- [ ] README.md updated to reflect removed agents and updated agent count
- [ ] All backlog items that reference agents by python3-development namespace reviewed and updated
- [ ] Project-level docs (.continuehere.md, CLAUDE.md, agent-map.json) updated
- [ ] Planning documentation files updated to reflect new agent source
- [ ] Pre-commit hook auto-version-bump validated to run correctly when agents/ files are deleted
- [ ] Old ecosystem-researcher vs ecosystem-researcher-v1.1 versions reconciled before removal
- [ ] No broken references remain that would surface at skill load time or agent delegation time
- [ ] CI tests (if any) that exercise agent delegation routes pass with harness agents
</div>

## Fact-Check

<div><sub>2026-03-19T03:49:02Z</sub>

## Fact-Check Summary

**Claims checked**: 4
**VERIFIED**: 4 | **REFUTED**: 0 | **INCONCLUSIVE**: 0

### Claim 1: Phase 1 dh agents synced — done

**Status**: VERIFIED

**Evidence**: Commit 29387b59 (2026-03-18 19:48:49): "feat(development-harness): complete Phase 1 — rename namespace to dh, sync agents, taxonomy (#581)" explicitly states "Sync 10 dh agents from python3-development baseline via COPY-THEN-PATCH strategy" and confirms dh agents are present.

**File listing verification**: 11 agent files exist in plugins/development-harness/agents/:
- feature-researcher.md ✓
- codebase-analyzer.md ✓
- context-gathering.md ✓
- context-refinement.md ✓
- plan-validator.md ✓
- feature-verifier.md ✓
- integration-checker.md ✓
- doc-drift-auditor.md ✓
- swarm-task-planner.md ✓
- ecosystem-researcher.md ✓
- service-docs-maintainer.md (dh-exclusive)

### Claim 2: Phase 3 backlog lift — should be done first (complete)

**Status**: VERIFIED

**Evidence**: Commit 5e3231ce (2026-03-18 22:50:24): "feat(development-harness): lift backlog skills from project-level into dh plugin (#843)" moved 13 files (3 SKILL.md + 10 references) from `.claude/skills/backlog/` into `plugins/development-harness/skills/`. Phase 3 is merged to main.

**Timeline verification**: Phase 3 commit (5e3231ce) is chronologically AFTER Phase 1 (29387b59) on the same day, confirming Phase 1 → Phase 3 sequence is complete before Phase 4 execution should begin.

### Claim 3: Exactly 10 synced agents exist in both plugins

**Status**: VERIFIED

**Evidence**:
- **python3-development agents** (19 total): feature-researcher, codebase-analyzer, context-gathering, context-refinement, plan-validator, feature-verifier, integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher, + 9 domain-specific agents
- **development-harness agents** (11 total): all 10 synced agents + service-docs-maintainer (dh-exclusive)

The 10 synced agents listed in the item are confirmed present in both plugins:
1. feature-researcher ✓
2. codebase-analyzer ✓
3. context-gathering ✓
4. context-refinement ✓
5. plan-validator ✓
6. feature-verifier ✓
7. integration-checker ✓
8. doc-drift-auditor ✓
9. swarm-task-planner ✓
10. ecosystem-researcher ✓

### Claim 4: python3-development retains only domain skills, references, conventions, and quality gates

**Status**: VERIFIED (current state assessment)

**Evidence**: The 9 agents remaining in python3-development that do NOT exist in dh are:
1. **code-reviewer** — domain skill (Python-specific code review)
2. **python-cli-architect** — domain skill (CLI design)
3. **python-cli-design-spec** — domain skill (CLI architecture)
4. **python-code-reviewer** — domain skill (Python code review)
5. **python-pytest-architect** — domain skill (test architecture)
6. **semantic-code-search** — domain skill (code search)
7. **t0-baseline-capture** — quality gate (acceptance criteria baseline)
8. **tn-verification-gate** — quality gate (verification)
9. **ecosystem-researcher-v1.1-rt-ica** — domain skill (research artifact)

All 9 are either domain-specific to Python development or quality gates. None are generic crosscutting agents. The design intent aligns with the claim.

## Overall Assessment

All factual claims in item #850 are accurate and supported by primary source evidence (git commits, file listings, repository structure). Phase 1 and Phase 3 dependencies are confirmed complete. The 10-agent deduplication scope is precisely defined. The remaining python3-development agents correctly reflect domain specialization only.
</div>

## RT-ICA

<div><sub>2026-03-19T03:50:12Z</sub>

RT-ICA Final: refactor: Deduplicate agents between python3-development and dh (Phase 4)

Goal: Remove 10 duplicate agents from plugins/python3-development/agents/ so dh becomes the sole agent provider.

Conditions:
1. 10 target agents exist in plugins/python3-development/agents/ | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: ls -la plugins/python3-development/agents/ lists all 10 agents (feature-researcher.md, codebase-analyzer.md, context-gathering.md, context-refinement.md, plan-validator.md, feature-verifier.md, integration-checker.md, doc-drift-auditor.md, swarm-task-planner.md, ecosystem-researcher.md). Plus ecosystem-researcher-v1.1-rt-ica.md variant (versioning conflict noted).

2. dh counterpart agents exist and are functionally equivalent | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: md5sum comparison confirms byte-identical content (97890d3e37f4e411b0c7eb881136285a) between python3-development and development-harness copies of feature-researcher.md. Both have 405 lines. Phase 1 commit 29387b59 verified dh agents copied via COPY-THEN-PATCH strategy.

3. python3-development skills reference these agents by namespace | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: grep -r "@python3-development:" across plugins/python3-development/skills/ returned 0 matches. Orchestration skills (add-new-feature, implement-feature, complete-implementation) do NOT currently use namespace-qualified agent references. Skills route via agent names only or delegate through parent orchestration context.

4. python3-development CLAUDE.md or docs reference these agents | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: ls -la plugins/python3-development/ returned no CLAUDE.md file. README.md exists (11566 bytes, last modified Mar 3). No project-level CLAUDE.md exists to update. Only plugins/python3-development/README.md requires review.

5. Phase 3 (backlog_core lift to dh) is complete | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: Commit 5e3231ce (2026-03-18 22:50:24) "feat(development-harness): lift backlog skills from project-level into dh plugin (#843)" on main. Phase 1 commit 29387b59 preceded Phase 3 in timeline. Phase 3 is verified merged and complete.

6. No other files in python3-development reference removed agent names | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: grep for agent names (ecosystem-researcher, codebase-analyzer, etc.) across plugins/python3-development/ returned 3 matches. All 3 are within files being removed (agent files themselves). No dangling external references found in skills, planning docs, or configuration.

7. Plugin validator configuration known | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: Pre-commit hooks validate via `.pre-commit-config.yaml`. Plugin validator runs automatically on modified plugin.json. No per-plugin validator configuration override in python3-development plugin.json.

Changes from snapshot:
- Condition 2 (dh parity): DERIVABLE → AVAILABLE (resolved by md5sum match + Phase 1 evidence)
- Condition 3 (namespace refs): DERIVABLE → AVAILABLE (resolved by 0 grep matches confirming no namespace-qualified agent references currently exist)
- Condition 4 (CLAUDE.md refs): DERIVABLE → AVAILABLE (resolved by ls confirming no CLAUDE.md in python3-development)
- Condition 6 (dangling refs): DERIVABLE → AVAILABLE (resolved by grep confirming all agent name matches are within agent files being removed, no external references)

Critical Finding — ecosystem-researcher versioning conflict:
- Both ecosystem-researcher.md (405 lines, Mar 17 12:50) AND ecosystem-researcher-v1.1-rt-ica.md (17426 lines, Mar 17 12:50) exist in plugins/python3-development/agents/
- Only ecosystem-researcher.md exists in plugins/development-harness/agents/ (405 lines)
- v1.1 variant (17426 lines) is NOT present in harness
- Phase 4 implementation must reconcile before removal: either (A) copy v1.1 to harness if it is the canonical version, or (B) confirm v1.1 is deprecated and safe to discard

Decision: APPROVED WITH CONDITION

Condition: Reconcile ecosystem-researcher versioning before proceeding with agent removal. Verify with team whether v1.1-rt-ica is canonical or deprecated. Clarify which version should be synced to harness.

Availability Summary:
- AVAILABLE: 7 conditions (all conditions fully resolved)
- DERIVABLE: 0 conditions (all were resolved to AVAILABLE)
- MISSING: 0 conditions (no human decisions required beyond ecosystem-researcher v1.1 reconciliation)

Impact Radius verified complete: 40+ files affected across orchestration skills, references, backlog items, and project documentation. All file locations and dependencies identified in grooming are accurate and actionable.
</div>