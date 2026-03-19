---
title: "Task Plan — Deduplicate Agents Phase 4"
slug: deduplicate-agents-phase4
version: "1.0"
generated: 2026-03-18
feature-context: plan/feature-context-deduplicate-agents-phase4.md
codebase-analysis: plan/codebase/AGENTS.md
architect-spec: plan/architect-deduplicate-agents-phase4.md
task-count: 7
tasks:
  - T1: Ecosystem-researcher v1.1 decision gate
  - T2: Delete 11 agent files from python3-development
  - T3: Update .claude/rules/local-workflow.md Agent File Locations tables
  - T4: Update plugins/python3-development/skills/orchestrate/SKILL.md
  - T5: Update plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
  - T6: Add forwarding note to plugins/python3-development/CLAUDE.md
  - T7: Validate both plugins pass skilllint and no stale namespace references remain
task_exports:
  enabled: false
  directory: "TASK"
---

# Task Plan: Deduplicate Agents Phase 4

Remove 10 duplicate agents from `plugins/python3-development/agents/` (plus the v1.1
versioned variant after decision gate) so `development-harness` becomes the sole provider
of shared workflow agents. Update all reference documents to use `@dh:` namespace. Leave
the 8 domain-specific Python agents untouched.

---

## Dependency Graph

```text
T1 (Decision Gate)
  |
T2 (Delete 11 agent files)          ← depends on T1
  |
  +-- T3 (local-workflow.md)         ─┐
  +-- T4 (orchestrate/SKILL.md)       ├── parallel (depend on T2, not each other)
  +-- T5 (python-development-orch)    ├── parallel
  +-- T6 (CLAUDE.md forwarding)       ┘
  |
T7 (Validation)                      ← depends on T3 + T4 + T5 + T6
```

T3, T4, T5, T6 have no shared output files and can execute concurrently after T2 completes.

---

## SYNC CHECKPOINT 1 — After T1

- Convergence point: T1 output (D1 decision record)
- Quality gate: D1 decision is explicit (Option A, B, or C) and recorded in T1 output
- Reflection: Does T2's deletion list need to change based on D1? (Option C keeps v1.1 renamed)
- Proceed to T2 only after T1 acceptance criteria are met

## SYNC CHECKPOINT 2 — After T2

- Convergence point: T2 output (agent files deleted)
- Quality gate: `ls -1 plugins/python3-development/agents/*.md | wc -l` returns expected count
- Quality gate: `ls -1 plugins/development-harness/agents/*.md | wc -l` returns 12 (unchanged)
- Proceed to T3/T4/T5/T6 in parallel only after T2 acceptance criteria are met

## SYNC CHECKPOINT 3 — After T3 + T4 + T5 + T6

- Convergence point: all four reference update tasks complete
- Quality gate: no task has status BLOCKED
- Proceed to T7 only after all four complete

---

## T1: Ecosystem-researcher v1.1 Decision Gate

**Status**: COMPLETE
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: medium
**Can parallelize with**: nothing — T2 depends on this decision

### Context

`plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md` is not a straight
duplicate of `plugins/development-harness/agents/ecosystem-researcher.md`. The v1.1 variant
has `WebSearch`, `WebFetch`, `Write`, `Edit` in its tool list and describes itself as a
"Python projects" researcher. The dh version intentionally uses MCP-only tools and BLOCKs
when no MCP server is available (this is a design constraint, not an omission).

This task records the explicit D1 decision so T2 knows whether to also delete the v1.1 file,
rename it, or merge its tools into dh before deletion. No file changes are made in this task.

Architecture spec (plan/architect-deduplicate-agents-phase4.md §Decision Point D1) defines
three options:

- **Option A**: Add WebSearch/WebFetch to dh ecosystem-researcher, update description,
  then delete v1.1.
- **Option B** (recommended): Delete v1.1 as-is. The BLOCK behavior is intentional.
  No capability is lost because direct-web fallback is an anti-pattern for this agent.
- **Option C**: Rename v1.1 to `python-ecosystem-researcher.md` and keep it as a
  python3-development-specific agent.

### Objective

Produce a written decision record (one of: Option A, B, or C) for the v1.1 file, with
rationale, so T2 can execute the correct deletion or rename action.

### Inputs

- `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md` — read frontmatter
  and body to confirm current tool list and framing
- `plugins/development-harness/agents/ecosystem-researcher.md` — read frontmatter and body
  to confirm dh canonical version
- Architecture spec § Decision Point D1:
  `plan/architect-deduplicate-agents-phase4.md` lines 65-116
- Feature context § Q1:
  `plan/feature-context-deduplicate-agents-phase4.md` lines 153-161

### Requirements

1. Read both agent files (v1.1 and dh) in full.
2. Confirm the tool set difference: v1.1 has `WebSearch`, `WebFetch`; dh uses `mcp__*`
   wildcards only and explicitly BLOCKs on missing MCP servers.
3. Confirm whether any skill file in `plugins/python3-development/skills/` or
   `.claude/rules/` references `ecosystem-researcher-v1.1-rt-ica` by name:
   ```bash
   grep -r "ecosystem-researcher-v1.1" /home/ubuntulinuxqa2/repos/claude_skills/plugins/ /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/ --include="*.md"
   ```
   If zero matches: v1.1 has no live references, deletion is safe regardless of option chosen.
4. Choose one of Option A / B / C. The architecture spec recommends Option B.
5. Write the decision record to `plan/D1-ecosystem-researcher-decision.md`.

### Constraints

- Do NOT edit any agent file in this task. This task is read-only plus decision record.
- Do NOT write Step 0 (dh edit for Option A) in this task — that is part of T2.
- If choosing Option A, flag that T2 must include a sub-step to update the dh agent
  BEFORE deleting v1.1 (the dh edit must use `plugin-creator:contextual-ai-documentation-optimizer`
  per MEMORY.md constraint).

### Expected Outputs

- `plan/D1-ecosystem-researcher-decision.md` containing:
  - Chosen option (A, B, or C)
  - Rationale (2-4 sentences)
  - Explicit instruction for T2: what to do with `ecosystem-researcher-v1.1-rt-ica.md`
  - If Option A: note that T2 must update dh agent before deleting v1.1

### Acceptance Criteria

1. `plan/D1-ecosystem-researcher-decision.md` exists.
2. File contains exactly one of: `Decision: Option A`, `Decision: Option B`,
   `Decision: Option C`.
3. File contains a rationale section (at least 2 sentences).
4. File contains explicit T2 instruction: either `Delete ecosystem-researcher-v1.1-rt-ica.md`,
   `Rename to python-ecosystem-researcher.md`, or `Update dh then delete v1.1`.
5. The zero-references grep result is recorded in the decision file.

### Verification Steps

1. Read `plan/D1-ecosystem-researcher-decision.md` and confirm structure matches criteria.
2. Confirm grep command was run and result is recorded:
   ```bash
   grep -r "ecosystem-researcher-v1.1" /home/ubuntulinuxqa2/repos/claude_skills/plugins/ /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/ --include="*.md"
   ```
3. Confirm the chosen option is compatible with T2's deletion scope (Option B or A → delete;
   Option C → rename only, deletion list shrinks by 1).

### CoVe Checks

Key claims to verify:

- Claim: v1.1 has `WebSearch`, `WebFetch`; dh does not.
- Claim: No skill file references `ecosystem-researcher-v1.1-rt-ica` by name.
- Claim: dh version explicitly BLOCKs on missing MCP servers (by design, not omission).

Verification questions:

1. Does `tools:` in `ecosystem-researcher-v1.1-rt-ica.md` frontmatter contain `WebSearch`
   and `WebFetch`? (Read the file — do not rely on the spec.)
2. Does the dh `ecosystem-researcher.md` description contain "BLOCKs if none available"?
3. Does `grep -r "ecosystem-researcher-v1.1"` return zero results?

Evidence to collect: output of the grep command + direct read of both frontmatters.

Revision rule: if any check fails (e.g., a skill file does reference v1.1), update the
decision rationale to account for that reference before writing the decision file.

### Handoff

Return:
- Path to `plan/D1-ecosystem-researcher-decision.md`
- One-line summary of the chosen option and rationale
- Whether T2 requires a dh-edit sub-step (Option A only)

---

## T2: Delete 11 Agent Files from python3-development

**Status**: COMPLETE
**Dependencies**: T1
**Priority**: 2
**Complexity**: Low
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: low
**Can parallelize with**: nothing at this priority level

### Context

This task makes Phase 4's goal observable in the filesystem: the 10 shared workflow agents
are deleted from `plugins/python3-development/agents/`, leaving only the 8 domain-specific
Python agents. The dh copies in `plugins/development-harness/agents/` are untouched and
remain the canonical versions.

`plugin.json` does NOT declare an explicit agents array (confirmed in codebase analysis).
Auto-discovery handles deregistration — no json edits are required.

The v1.1 file (`ecosystem-researcher-v1.1-rt-ica.md`) handling depends on T1's D1 decision:
- Option B: delete it alongside the 10 shared agents (11 total deletions)
- Option C: rename it to `python-ecosystem-researcher.md` before the deletion run
- Option A: update dh agent first (per spec, using `plugin-creator:contextual-ai-documentation-optimizer`),
  then delete v1.1

Read `plan/D1-ecosystem-researcher-decision.md` (T1 output) before running any git rm.

### Objective

Delete exactly 10 shared workflow agents (plus v1.1 per D1 decision) from
`plugins/python3-development/agents/` so the directory contains only the 8 KEEP agents.

### Inputs

- `plan/D1-ecosystem-researcher-decision.md` (T1 output) — confirms v1.1 action
- Architecture spec deletion list: `plan/architect-deduplicate-agents-phase4.md` lines 29-41
- Current agent files (pre-deletion diff check per spec lines 321-330):
  ```bash
  for agent in feature-researcher codebase-analyzer context-gathering context-refinement \
    plan-validator feature-verifier integration-checker doc-drift-auditor swarm-task-planner \
    ecosystem-researcher; do
    diff /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/${agent}.md \
         /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/agents/${agent}.md \
      && echo "IDENTICAL: ${agent}" || echo "DIFFERS: ${agent}"
  done
  ```

### Requirements

1. Read `plan/D1-ecosystem-researcher-decision.md` and confirm which option was chosen.
2. Run pre-deletion diff check for all 10 shared agents (loop above). If any diff shows
   content present in the python3-development copy but NOT in the dh copy (beyond formatting),
   STOP and report — do not delete until dh is updated with that content.
3. If D1 = Option A: update `plugins/development-harness/agents/ecosystem-researcher.md`
   by adding `WebSearch`, `WebFetch` to `tools:` and updating description to reflect
   direct-web fallback. Delegate this edit to `plugin-creator:contextual-ai-documentation-optimizer`
   (MEMORY.md: never write agent body content directly as orchestrator).
4. Delete the 10 shared agents:
   ```bash
   cd /home/ubuntulinuxqa2/repos/claude_skills
   git rm plugins/python3-development/agents/feature-researcher.md \
          plugins/python3-development/agents/codebase-analyzer.md \
          plugins/python3-development/agents/context-gathering.md \
          plugins/python3-development/agents/context-refinement.md \
          plugins/python3-development/agents/plan-validator.md \
          plugins/python3-development/agents/feature-verifier.md \
          plugins/python3-development/agents/integration-checker.md \
          plugins/python3-development/agents/doc-drift-auditor.md \
          plugins/python3-development/agents/swarm-task-planner.md \
          plugins/python3-development/agents/ecosystem-researcher.md
   ```
5. Apply D1 decision to v1.1:
   - Option B: `git rm plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md`
   - Option C: `git mv plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md \
     plugins/python3-development/agents/python-ecosystem-researcher.md` then edit
     frontmatter `name:` field from `ecosystem-researcher` to `python-ecosystem-researcher`
   - Option A: `git rm plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md`
     (after dh edit in Requirement 3)
6. Verify remaining agent count matches expected.
7. Do NOT commit in this task — leave changes staged or unstaged for T7 to validate and commit.

### Constraints

- Do NOT delete agents from the KEEP list:
  `python-cli-architect.md`, `python-pytest-architect.md`, `python-cli-design-spec.md`,
  `python-code-reviewer.md`, `code-reviewer.md`, `semantic-code-search.md`,
  `t0-baseline-capture.md`, `tn-verification-gate.md`
- Do NOT touch `plugins/development-harness/agents/` except for the Option A dh edit.
- If pre-deletion diff finds a divergence (python3-dev has content not in dh), STOP and
  report the specific file and content before proceeding.
- Do NOT commit in this task.

### Expected Outputs

- 10 (or 11) agent files removed from `plugins/python3-development/agents/` via `git rm`
- `plugins/python3-development/agents/` contains exactly 8 files (Option B/A) or 9 files
  (Option C with renamed python-ecosystem-researcher.md)
- `plugins/development-harness/agents/` count unchanged at 12 (or 12 for B/C, 12 for A
  since it already existed)
- Pre-deletion diff results recorded in task handoff

### Acceptance Criteria

1. `ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/*.md | wc -l`
   returns `8` (Option B or A) or `9` (Option C).
2. `ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/agents/*.md | wc -l`
   returns `12`.
3. None of the KEEP agents are missing from `plugins/python3-development/agents/`.
4. Pre-deletion diff showed no divergence, OR any divergence was resolved before deletion.
5. D1 decision (from T1) was applied correctly to the v1.1 file.

### Verification Steps

1. Run the agent count check:
   ```bash
   ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/*.md
   ```
   Confirm: only the 8 KEEP agents (plus `python-ecosystem-researcher.md` if Option C).

2. Run the dh count check:
   ```bash
   ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/agents/*.md | wc -l
   ```
   Confirm: `12`.

3. Confirm KEEP agents exist:
   ```bash
   for f in python-cli-architect python-pytest-architect python-cli-design-spec \
     python-code-reviewer code-reviewer semantic-code-search t0-baseline-capture \
     tn-verification-gate; do
     ls /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/${f}.md \
       && echo "OK: ${f}" || echo "MISSING: ${f}"
   done
   ```
   All 8 must print `OK`.

### Handoff

Return:
- Pre-deletion diff results (IDENTICAL or DIFFERS per agent, list all 10)
- Final agent count in `plugins/python3-development/agents/`
- Which D1 option was applied and confirmation of v1.1 action taken
- STATUS: DONE or BLOCKED (with reason if blocked)

---

## T3: Update .claude/rules/local-workflow.md — Agent File Locations Tables

**Status**: NOT STARTED
**Dependencies**: T2
**Priority**: 3
**Complexity**: Medium
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: medium
**Can parallelize with**: T4, T5, T6

### Context

`.claude/rules/local-workflow.md` contains two "Agent File Locations" tables — one in the
Phase 1 Planning section and one in the Phase 3 Quality Gates section. Both currently show
a `python3-development` column alongside a `development-harness` column for shared agents.

After T2 deletes the 10 agents from python3-development, those column cells become dead
references. The architecture spec (§Step 2) resolves this: remove the `python3-development`
column entries for the deleted agents, making the tables single-source-of-truth pointing
only to dh for shared agents.

KEEP agents (`python-cli-design-spec`, `t0-baseline-capture`, `tn-verification-gate`,
`code-reviewer`) still exist in python3-development — their rows are UNCHANGED.

The codebase analysis (plan/codebase/AGENTS.md §Update locations in local-workflow.md)
identifies the specific lines to change:

- Phase 1 table (~lines 54-63): remove python3-development column cells for the 10 shared agents
- Phase 3 table (~lines 269-276): remove python3-development column cells for the shared agents
- Data flow diagram: update any `python3-development:{deleted-agent}` inline references to `dh:`

This task also checks the data flow diagram in local-workflow.md for agent namespace
references and updates any that reference deleted agents.

### Objective

Update `.claude/rules/local-workflow.md` so the Agent File Locations tables show only
`development-harness` paths for the 10 deleted shared agents, leaving KEEP agent rows unchanged.

### Inputs

- `/home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md` — the file to edit
- Architecture spec §Step 2: `plan/architect-deduplicate-agents-phase4.md` lines 179-213
- Codebase analysis §Update locations: `plan/codebase/AGENTS.md` lines 98-127
- KEEP agents list (must NOT have their table rows modified):
  `python-cli-design-spec`, `t0-baseline-capture`, `tn-verification-gate`, `code-reviewer`,
  `python-cli-architect`, `python-pytest-architect`, `python-code-reviewer`

### Requirements

1. Read `/home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md` in full.
2. Identify all Agent File Locations tables (search for `| Agent |` headers).
3. For each table row where the agent is one of the 10 deleted agents (feature-researcher,
   codebase-analyzer, context-gathering, context-refinement, plan-validator, feature-verifier,
   integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher):
   - Remove the `python3-development` column cell (replace cell content with `—` or remove
     the column). Follow the existing table style.
4. Do NOT modify rows for KEEP agents (python-cli-architect, python-pytest-architect,
   python-cli-design-spec, python-code-reviewer, code-reviewer, t0-baseline-capture,
   tn-verification-gate).
5. Search the data flow diagram and any prose sections for `python3-development:{deleted-agent}`
   namespace references:
   ```bash
   grep -n "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md
   ```
   For each match found, update the namespace from `python3-development:` to `dh:`.
6. Verify the file still renders as valid Markdown (tables have consistent column counts,
   no broken pipe characters).

### Constraints

- Do NOT remove entire table rows for shared agents — only remove or blank the
  `python3-development` column cell within those rows.
- Do NOT change any reference to agents in the KEEP list.
- Do NOT modify the file's overall structure (sections, headings, data flow diagram prose).
- Preserve all existing `dh:` and `development-harness` path references exactly.

### Expected Outputs

- Modified `/home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md`
- Phase 1 and Phase 3 Agent File Locations tables updated
- Data flow diagram updated if any `python3-development:{deleted-agent}` references existed

### Acceptance Criteria

1. No cell in the Agent File Locations tables contains a `python3-development/agents/` path
   for any of the 10 deleted agents.
2. Rows for `python-cli-architect`, `python-pytest-architect`, `python-cli-design-spec`,
   `python-code-reviewer`, `code-reviewer`, `t0-baseline-capture`, `tn-verification-gate`
   are unchanged.
3. The grep for `python3-development:{deleted-agent}` in the file returns zero matches
   (excluding the historical backlog section if one exists):
   ```bash
   grep -c "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md
   ```
   Expected: `0`
4. Markdown tables have consistent column counts (no orphaned pipe characters).
5. The file is not truncated — character count is within 10% of original (table restructure
   shrinks content slightly; wholesale deletion would be much larger).

### Verification Steps

1. Run the grep check for stale namespace references:
   ```bash
   grep -n "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md
   ```
   Confirm: zero matches.

2. Read the Phase 1 and Phase 3 Agent File Locations tables (search for `| Agent |` header)
   and visually confirm: shared agent rows show only dh path; KEEP agent rows unchanged.

3. Run prek lint on the file:
   ```bash
   uv run prek run --files /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/local-workflow.md
   ```
   Confirm: exits 0 (no pre-commit issues).

### CoVe Checks

Key claims to verify:

- Claim: The Agent File Locations tables use a two-column format with `python3-development`
  and `development-harness` columns — not a different table structure.
- Claim: KEEP agents (`t0-baseline-capture`, `tn-verification-gate`, `code-reviewer`) have
  rows in these tables that should remain with `python3-development` paths.

Verification questions:

1. After reading the file, what are the exact column headers of the Agent File Locations
   tables? (Do they say `python3-development` and `development-harness`, or something else?)
2. Do `t0-baseline-capture` and `tn-verification-gate` rows show `—` in the dh column
   (meaning they are python3-development-only)? If so, their rows must be kept intact.

Evidence to collect: direct read of the relevant table sections in local-workflow.md.

Revision rule: if table format differs from the two-column assumption, adapt the edit
approach to match the actual structure before making changes.

### Handoff

Return:
- Number of table cells modified (cells where python3-development path was removed)
- Number of prose/diagram namespace references updated
- Confirmation that KEEP agent rows are unchanged
- Output of the stale-reference grep (should be zero lines)

---

## T4: Update plugins/python3-development/skills/orchestrate/SKILL.md

**Status**: NOT STARTED
**Dependencies**: T2
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: low
**Can parallelize with**: T3, T5, T6

### Context

`plugins/python3-development/skills/orchestrate/SKILL.md` references `swarm-task-planner`
as a delegation target. After T2 deletes that agent from python3-development, any reference
using `python3-development:swarm-task-planner` resolves to a missing agent.

Per the architecture spec (§Step 3), the codebase analysis confirms that `orchestrate/SKILL.md`
also references `python-cli-architect`, `python-pytest-architect`, `python-code-reviewer`,
and `python-cli-design-spec` — these are ALL KEEP agents and must NOT be changed.

Only the `swarm-task-planner` reference crosses the namespace boundary after Phase 4.

### Objective

Update `plugins/python3-development/skills/orchestrate/SKILL.md` to replace
`python3-development:swarm-task-planner` with `dh:swarm-task-planner`. Leave all other
agent references unchanged.

### Inputs

- `/home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md`
  — the file to edit
- Architecture spec §Step 3: `plan/architect-deduplicate-agents-phase4.md` lines 214-231
- Codebase analysis §orchestrate/SKILL.md: `plan/codebase/AGENTS.md` lines 251-266

### Requirements

1. Read the full file to locate all references to `swarm-task-planner`.
2. Search specifically for namespace-prefixed forms:
   ```bash
   grep -n "swarm-task-planner" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md
   ```
3. For each match: if the reference uses `python3-development:swarm-task-planner`, update
   it to `dh:swarm-task-planner`.
4. For each match: if the reference uses `swarm-task-planner` without a namespace prefix
   (e.g., in descriptive text), update to clarify it is now `@dh:swarm-task-planner` if
   the context is a delegation instruction, or leave as-is if it is narrative prose.
5. Confirm all references to `python-cli-architect`, `python-pytest-architect`,
   `python-code-reviewer`, `python-cli-design-spec` are NOT changed.
6. Run prek lint on the file.

### Constraints

- Do NOT change any reference to the KEEP agents:
  `python-cli-architect`, `python-pytest-architect`, `python-code-reviewer`,
  `python-cli-design-spec`, `python-code-reviewer`, `stdlib-scripting`.
- Do NOT restructure sections or alter the file's overall format.
- If `swarm-task-planner` appears zero times in the file (grep returns nothing), the task
  is DONE — no edit needed. Report this as the handoff result.

### Expected Outputs

- Modified `/home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md`
  with `swarm-task-planner` references updated to use `dh:` namespace.
- If zero references found, no file modification (report as clean).

### Acceptance Criteria

1. Grep for `python3-development:swarm-task-planner` in the file returns zero matches:
   ```bash
   grep -c "python3-development:swarm-task-planner" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md
   ```
   Expected: `0`
2. Grep for `dh:swarm-task-planner` returns a count matching the number of swarm-task-planner
   delegation references in the original file (at least 1, unless the file had zero).
3. References to KEEP agents (`python3-development:python-cli-architect`, etc.) are unchanged.
4. `uv run prek run --files` exits 0.

### Verification Steps

1. Run the stale-reference check:
   ```bash
   grep -c "python3-development:swarm-task-planner" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md
   ```
   Expected: `0`.

2. Run the KEEP-agents check to confirm no unintended changes:
   ```bash
   grep -n "python-cli-architect\|python-pytest-architect\|python-code-reviewer\|python-cli-design-spec" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md
   ```
   All results should still show `python3-development:` prefix (not `dh:`).

3. Run prek lint:
   ```bash
   uv run prek run --files /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/orchestrate/SKILL.md
   ```
   Confirm: exits 0.

### Handoff

Return:
- Number of `swarm-task-planner` references found and updated
- Confirmation that KEEP agent references are unchanged
- Output of stale-reference grep (should be `0`)
- Prek lint result (pass/fail)

---

## T5: Update python-development-orchestration.md

**Status**: NOT STARTED
**Dependencies**: T2
**Priority**: 3
**Complexity**: Medium
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: medium
**Can parallelize with**: T3, T4, T6

### Context

`plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`
is the most heavily impacted document in this refactoring. The codebase analysis
(plan/codebase/AGENTS.md §Reference Patterns) identified 50+ agent references across 5+
workflow scenarios. Many of these reference agents that remain valid (`python-cli-architect`,
`python-pytest-architect`, `python-code-reviewer`, `python-cli-design-spec`) — these must
NOT be changed.

The specific agents that cross the namespace boundary after Phase 4 are limited to
`swarm-task-planner` (and potentially `feature-researcher`, `codebase-analyzer` if they
appear in this document). The architecture spec (§Step 4) clarifies: only references using
`python3-development:{deleted-agent}` namespace must be updated. The domain-specific
agents keep their `python3-development:` prefix.

Deleted agents that may appear in this document: `feature-researcher`, `codebase-analyzer`,
`context-gathering`, `context-refinement`, `plan-validator`, `feature-verifier`,
`integration-checker`, `doc-drift-auditor`, `swarm-task-planner`, `ecosystem-researcher`.

### Objective

Update all `python3-development:{deleted-agent}` namespace references in
`python-development-orchestration.md` to `dh:{agent-name}`. Leave references to KEEP agents
unchanged.

### Inputs

- `/home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`
  — the file to edit
- Architecture spec §Step 4: `plan/architect-deduplicate-agents-phase4.md` lines 232-252
- Codebase analysis §python-development-orchestration.md: `plan/codebase/AGENTS.md` lines
  131-178, 279-293

### Requirements

1. Read the full file.
2. Run a targeted grep to find all occurrences of the deleted agent names with the
   `python3-development:` namespace:
   ```bash
   grep -n "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
   ```
3. For each match: replace `python3-development:{deleted-agent}` with `dh:{deleted-agent}`.
4. Also check for bare (non-namespace-prefixed) agent name references in delegation
   instructions that may imply the python3-development namespace. If the context is a
   `subagent_type=` string or `@python3-development:` prefix, update it. If the reference
   is purely in prose describing the agent's role (no namespace), leave it unchanged.
5. Run the stale-reference grep after edits to confirm zero matches remain.
6. Confirm KEEP agent references are unchanged by running:
   ```bash
   grep -n "python3-development:\(python-cli-architect\|python-pytest-architect\|python-code-reviewer\|python-cli-design-spec\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
   ```
   All results should remain as `python3-development:` (not changed to `dh:`).

### Constraints

- Do NOT change references to KEEP agents: `python-cli-architect`, `python-pytest-architect`,
  `python-code-reviewer`, `python-cli-design-spec`.
- Do NOT rewrite workflow scenario prose, Mermaid diagrams, or section structure beyond
  the namespace substitutions.
- Do NOT change references to skills (e.g., `/python3-development:add-new-feature`) —
  these are skill namespace references, not agent namespace references.
- If a deleted agent name appears in prose without a namespace prefix (e.g., "the
  feature-researcher agent"), leave it unchanged — only namespace-qualified delegation
  references require updating.

### Expected Outputs

- Modified `python-development-orchestration.md` with all `python3-development:{deleted-agent}`
  namespace references replaced by `dh:{deleted-agent}`.

### Acceptance Criteria

1. Grep for `python3-development:{deleted-agents}` returns zero matches:
   ```bash
   grep -c "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
   ```
   Expected: `0`
2. Grep for KEEP agents still returns `python3-development:` prefix (not changed to `dh:`):
   ```bash
   grep "dh:\(python-cli-architect\|python-pytest-architect\|python-code-reviewer\|python-cli-design-spec\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
   ```
   Expected: zero matches (KEEP agents must NOT have been updated to dh:).
3. `uv run prek run --files` exits 0.

### Verification Steps

1. Run the stale-reference grep (Requirement 5 command). Confirm: `0`.

2. Run the KEEP-agents check (Requirement 6 command). Confirm: results all show
   `python3-development:` prefix.

3. Run prek lint:
   ```bash
   uv run prek run --files /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
   ```

### CoVe Checks

Key claims to verify:

- Claim: The file references `python3-development:swarm-task-planner` and potentially other
  deleted agent namespaces (not just agent names in prose).
- Claim: Mermaid diagram node labels in this file use `subagent_type=` strings that may
  embed agent namespaces.

Verification questions:

1. Does the grep in Requirement 2 return any matches? (Run it — do not assume based on the
   codebase analysis table which showed only `swarm-task-planner` at lines 60 and 103.)
2. Are there `subagent_type="python3-development:{deleted-agent}"` patterns in Mermaid node
   labels (which require `=` not `:` in the label — per delegation-format.md constraints)?

Evidence to collect: direct grep output from Requirement 2.

Revision rule: if grep returns matches for agents other than `swarm-task-planner`, update
all of them. Do not limit the fix to only `swarm-task-planner`.

### Handoff

Return:
- Number of namespace references updated (list each: `agent-name: N occurrences`)
- Output of post-edit stale-reference grep (should be `0`)
- Output of KEEP-agents check (should show `python3-development:` prefixes unchanged)
- Prek lint result

---

## T6: Add Forwarding Note to plugins/python3-development/CLAUDE.md

**Status**: NOT STARTED
**Dependencies**: T2
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: low
**Can parallelize with**: T3, T4, T5

### Context

A developer reading `plugins/python3-development/` after Phase 4 will notice that 10 agents
are missing with no explanation. The architecture spec (§Step 5) specifies adding a
forwarding note to the plugin's developer-facing document (`CLAUDE.md` or `README.md`).

The note should explain: the agents were moved to development-harness in Phase 4, which
plugin to use to invoke them, and which agents remain in python3-development.

The architecture spec provides the exact content to add (lines 259-275). Before editing,
the target file must be confirmed to exist.

### Objective

Add a Phase 4 Agent Consolidation forwarding note near the top of
`plugins/python3-development/CLAUDE.md` (or equivalent developer-facing file if CLAUDE.md
does not exist).

### Inputs

- Architecture spec §Step 5: `plan/architect-deduplicate-agents-phase4.md` lines 254-281
  (includes exact content to add)
- Target file: `plugins/python3-development/CLAUDE.md` — verify existence first:
  ```bash
  ls /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/CLAUDE.md
  ls /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/README.md
  ```
  Use whichever exists. If neither exists, create `CLAUDE.md` with only the forwarding
  note section (do not invent other content).

### Requirements

1. Confirm which developer-facing document exists (`CLAUDE.md` or `README.md`).
2. If neither exists: create `plugins/python3-development/CLAUDE.md` with the forwarding
   note as the sole content.
3. If the file exists: read it in full, then insert the following section near the top
   (after the first `# heading` or before the first `## heading`, whichever comes first):
   ```markdown
   ## Agent Consolidation (Phase 4, 2026-03-18)

   Shared workflow agents (feature-researcher, codebase-analyzer, context-gathering,
   context-refinement, plan-validator, feature-verifier, integration-checker,
   doc-drift-auditor, swarm-task-planner, ecosystem-researcher) were moved to the
   `development-harness` plugin in Phase 4. They no longer exist in this plugin.

   Use `@dh:{agent-name}` to invoke these agents.

   Agents remaining in this plugin are Python-domain-specific:
   python-cli-architect, python-pytest-architect, python-cli-design-spec,
   python-code-reviewer, code-reviewer, semantic-code-search,
   t0-baseline-capture, tn-verification-gate.
   ```
4. Do not modify any other section of the file.
5. Run prek lint on the modified file.

### Constraints

- Insert the forwarding note as a new `## Agent Consolidation` section — do not replace
  or remove any existing content.
- Do not add any content beyond what the architecture spec specifies in the forwarding note.
- If the file is very large (>100 lines), position the note after the first `## ` heading
  that is not the title, so it is visible early in the file without disrupting the intro.

### Expected Outputs

- Modified `plugins/python3-development/CLAUDE.md` (or `README.md`) with the
  `## Agent Consolidation (Phase 4, 2026-03-18)` section present near the top.

### Acceptance Criteria

1. The forwarding note section exists in the target file:
   ```bash
   grep -c "Agent Consolidation (Phase 4, 2026-03-18)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/CLAUDE.md
   ```
   Expected: `1` (or `README.md` if CLAUDE.md not used).
2. The note lists all 10 deleted agent names.
3. The note contains `@dh:{agent-name}` usage instruction.
4. The note lists all 8 KEEP agents.
5. `uv run prek run --files` exits 0 on the modified file.

### Verification Steps

1. Grep for the section heading to confirm it was inserted:
   ```bash
   grep -n "Agent Consolidation" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/CLAUDE.md
   ```

2. Read the section and confirm all 10 deleted agents and all 8 KEEP agents are listed.

3. Run prek lint:
   ```bash
   uv run prek run --files /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/CLAUDE.md
   ```

### Handoff

Return:
- Which file was modified (CLAUDE.md or README.md)
- Whether the file was created new or edited
- Confirmation that the forwarding note section is present with correct content
- Prek lint result

---

## T7: Validate Both Plugins and Confirm No Stale References

**Status**: NOT STARTED
**Dependencies**: T3, T4, T5, T6
**Priority**: 4
**Complexity**: Low
**Agent**: general-purpose
**Skills**: []
**Accuracy Risk**: low
**Can parallelize with**: nothing — this is the final gate

### Context

T7 is the final quality gate. It runs after T3, T4, T5, and T6 have all completed.
It verifies the complete state of both plugins and the reference files, then stages
and commits all changes in a single logical commit.

The architecture spec §Validation Design defines the exact checks (lines 319-381).
This task is purely verification + commit — no new edits should be needed. If any check
fails, T7 is BLOCKED and the relevant prior task (T3/T4/T5/T6) must fix the issue.

### Objective

Verify all Phase 4 changes are consistent and correct, then commit all staged changes
with the canonical commit message from the architecture spec.

### Inputs

- All files modified by T2/T3/T4/T5/T6 (staged in git)
- Architecture spec §Validation Design: `plan/architect-deduplicate-agents-phase4.md`
  lines 319-381
- `plan/D1-ecosystem-researcher-decision.md` (T1 output) — for commit message D1 clause

### Requirements

1. Run the agent inventory count checks:
   ```bash
   ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/*.md | wc -l
   # Expected: 8 (Option B/A) or 9 (Option C)

   ls -1 /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/agents/*.md | wc -l
   # Expected: 12
   ```

2. Run the stale namespace reference grep across all updated files (excluding backlog):
   ```bash
   grep -r "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
     /home/ubuntulinuxqa2/repos/claude_skills/plugins/ \
     /home/ubuntulinuxqa2/repos/claude_skills/.claude/rules/ \
     --include="*.md" \
     --exclude-dir=backlog \
     --exclude-dir=agents
   ```
   Expected: zero matches.

3. Run plugin validator on both plugins:
   ```bash
   uvx skilllint@latest check /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development
   uvx skilllint@latest check /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness
   ```
   Both must exit 0. If either fails with errors introduced by this change (not pre-existing),
   T7 is BLOCKED — identify which task introduced the error and report it.

4. Confirm the 8 KEEP agents still exist:
   ```bash
   for f in python-cli-architect python-pytest-architect python-cli-design-spec \
     python-code-reviewer code-reviewer semantic-code-search t0-baseline-capture \
     tn-verification-gate; do
     ls /home/ubuntulinuxqa2/repos/claude_skills/plugins/python3-development/agents/${f}.md \
       && echo "OK: ${f}" || echo "MISSING: ${f}"
   done
   ```
   All 8 must print `OK`.

5. Confirm dh agent files for the 10 deleted agents still exist (no accidental dh deletion):
   ```bash
   for f in feature-researcher codebase-analyzer context-gathering context-refinement \
     plan-validator feature-verifier integration-checker doc-drift-auditor \
     swarm-task-planner ecosystem-researcher; do
     ls /home/ubuntulinuxqa2/repos/claude_skills/plugins/development-harness/agents/${f}.md \
       && echo "OK: ${f}" || echo "MISSING FROM DH: ${f}"
   done
   ```
   All 10 must print `OK`.

6. Read `plan/D1-ecosystem-researcher-decision.md` to extract the D1 decision clause for
   the commit message.

7. Stage all modified/deleted files and commit with the canonical message:
   ```bash
   cd /home/ubuntulinuxqa2/repos/claude_skills
   git add -A plugins/python3-development/agents/ \
             .claude/rules/local-workflow.md \
             plugins/python3-development/skills/orchestrate/SKILL.md \
             plugins/python3-development/skills/python3-development/references/python-development-orchestration.md \
             plugins/python3-development/CLAUDE.md \
             plan/D1-ecosystem-researcher-decision.md
   git commit -m "refactor(agents): remove 10 shared agents from python3-development (Phase 4)

   dh is now the sole provider of: feature-researcher, codebase-analyzer,
   context-gathering, context-refinement, plan-validator, feature-verifier,
   integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher.

   Phase 1 (commit 29387b59) established dh as canonical. Phase 4 makes that
   observable in the filesystem by removing the stale python3-development copies.

   ecosystem-researcher-v1.1-rt-ica.md: [INSERT D1 DECISION CLAUSE FROM plan/D1-ecosystem-researcher-decision.md]"
   ```
   Replace `[INSERT D1 DECISION CLAUSE ...]` with the actual decision from T1 output.

### Constraints

- Do NOT make any new edits to reference files in this task. If a check fails, report
  which prior task needs to fix it and set status to BLOCKED.
- Do NOT commit if any validation check returns non-zero or unexpected results.
- Do NOT include `Fixes #N`, `Closes #N`, or `Resolves #N` in the commit message.
- Pre-existing skilllint errors that existed before Phase 4 do NOT block this task —
  only new errors introduced by Phase 4 changes are blockers.

### Expected Outputs

- All Phase 4 changes committed with the canonical commit message.
- `git log --oneline -1` shows the refactor(agents) commit.

### Acceptance Criteria

1. Agent inventory check passes: python3-development has 8 (or 9) agents; dh has 12.
2. Stale namespace grep returns zero matches.
3. `uvx skilllint@latest check plugins/python3-development` exits 0 (or fails only on
   pre-existing errors not caused by Phase 4 changes).
4. `uvx skilllint@latest check plugins/development-harness` exits 0 (or pre-existing only).
5. All 8 KEEP agents exist in python3-development.
6. All 10 deleted agents still exist in dh.
7. `git log --oneline -1` shows `refactor(agents): remove 10 shared agents`.

### Verification Steps

1. Run all five requirement checks (Requirements 1-5) and record outputs.
2. Run `git status` to confirm all Phase 4 modified files are staged.
3. Run `git log --oneline -1` after commit to confirm commit is present.
4. Run `git show --stat HEAD` to confirm the correct files are in the commit.

### Handoff

Return:
- Results of each validation check (pass/fail with output)
- Confirmation of commit hash (`git log --oneline -1` output)
- Any pre-existing skilllint errors noted (not caused by Phase 4)
- STATUS: DONE (all checks pass + committed) or BLOCKED (with failing check identified
  and which task must fix it)

---

## Context Manifest

Generated by context-gathering agent on 2026-03-19

### How This Currently Works: Phase 4 Agent Consolidation

When developers read the claude_skills repository, they encounter two plugins with overlapping agent definitions: `plugins/python3-development/agents/` and `plugins/development-harness/agents/`. Phase 1 (commit 29387b59) established development-harness as the canonical source by copying and patching shared workflow agents there. The python3-development copies remained — creating a dual-source maintenance burden where fixes must be applied in two places and documentation is ambiguous about which namespace is authoritative.

The Phase 4 consolidation removes the 10 stale copies from python3-development and updates all references to use the dh namespace. This makes the single-source-of-truth decision observable in the filesystem, not just documented in a commit message.

### Authoritative Agent Lists

**Agents to DELETE from plugins/python3-development/agents/ (11 files total):**

These exist in BOTH plugins. development-harness is canonical after Phase 1:

```
plugins/python3-development/agents/feature-researcher.md
plugins/python3-development/agents/codebase-analyzer.md
plugins/python3-development/agents/context-gathering.md
plugins/python3-development/agents/context-refinement.md
plugins/python3-development/agents/plan-validator.md
plugins/python3-development/agents/feature-verifier.md
plugins/python3-development/agents/integration-checker.md
plugins/python3-development/agents/doc-drift-auditor.md
plugins/python3-development/agents/swarm-task-planner.md
plugins/python3-development/agents/ecosystem-researcher.md
plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md (per T1 decision)
```

**Agents to KEEP in plugins/python3-development/agents/ (8 files):**

Domain-specific Python agents NOT present in development-harness:

```
plugins/python3-development/agents/python-cli-architect.md
plugins/python3-development/agents/python-pytest-architect.md
plugins/python3-development/agents/python-cli-design-spec.md
plugins/python3-development/agents/python-code-reviewer.md
plugins/python3-development/agents/code-reviewer.md
plugins/python3-development/agents/semantic-code-search.md
plugins/python3-development/agents/t0-baseline-capture.md
plugins/python3-development/agents/tn-verification-gate.md
```

### Files Requiring Reference Updates (Post-T2 Deletions)

After T2 deletes the agent files, these files must be updated to replace `python3-development:{deleted-agent}` namespace with `dh:{deleted-agent}`:

**1. `.claude/rules/local-workflow.md`**
- Phase 1 Agent File Locations table (lines ~54-63): Remove python3-development column cells for 10 deleted agents
- Phase 3 Agent File Locations table (lines ~269-276): Remove python3-development column cells for deleted agents
- Data flow diagram: Update any `python3-development:{deleted-agent}` to `dh:{deleted-agent}`
- KEEP agent rows retain their python3-development column (python-cli-design-spec, t0-baseline-capture, tn-verification-gate, code-reviewer)

**2. `plugins/python3-development/skills/orchestrate/SKILL.md`**
- Update only `swarm-task-planner` references from `python3-development:` to `dh:` namespace
- KEEP agents (python-cli-architect, python-pytest-architect, python-code-reviewer, python-cli-design-spec) remain unchanged in python3-development: namespace

**3. `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`**
- Most heavily impacted (50+ lines across 5+ workflow scenarios)
- Update namespace for all 10 deleted agents: `python3-development:{agent}` → `dh:{agent}`
- Keep KEEP agent references unchanged (python-cli-architect, python-pytest-architect, python-code-reviewer, python-cli-design-spec)
- Mermaid diagrams may use `subagent_type=` patterns with agent namespaces

**4. `plugins/python3-development/CLAUDE.md` (or README.md if CLAUDE.md doesn't exist)**
- Add section: `## Agent Consolidation (Phase 4, 2026-03-18)`
- List all 10 deleted agents with notation they moved to development-harness
- Provide `@dh:{agent-name}` usage instruction
- List all 8 KEEP agents as remaining Python-domain-specific agents

### Decision Point D1: ecosystem-researcher-v1.1-rt-ica.md

This file is NOT a straight duplicate:

**v1.1 variant** (`ecosystem-researcher-v1.1-rt-ica.md`):
- Tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch, mcp__Ref__ref_search_documentation, mcp__Ref__ref_read_url, mcp__exa__get_code_context_exa, mcp__sequential_thinking__sequentialthinking
- Color: purple
- Framing: Python-projects researcher
- Capability: WebSearch/WebFetch fallback when MCP servers unavailable

**dh canonical version** (`plugins/development-harness/agents/ecosystem-researcher.md`):
- Tools: Read, Grep, Glob, mcp__ref__*, mcp__exa__*, mcp__context7__*, mcp__firecrawl__* (wildcard MCP patterns)
- Color: blue
- Framing: General ecosystem researcher
- Constraint: Explicitly BLOCKs when no MCP server available (intentional design)

**T1 Decision Gate must choose one option:**

- **Option A**: Merge v1.1 tools (WebSearch, WebFetch) into dh before deleting v1.1
- **Option B (recommended)**: Delete v1.1 as-is. BLOCK behavior is intentional. Direct-web fallback is an anti-pattern
- **Option C**: Rename v1.1 to `python-ecosystem-researcher.md` and keep as python3-development-specific agent

Zero files reference `ecosystem-researcher-v1.1-rt-ica` by name (verified via grep), so chosen option has zero reference-update impact.

### plugin.json Configuration

`plugins/python3-development/plugin.json` does not exist or has no explicit `agents` array. Auto-discovery handles agent registration. File deletion alone is sufficient — no json updates required.

### Validation Commands (T7 Checklist)

After all deletions and reference updates, run:

**1. Agent count verification:**
```bash
ls -1 plugins/python3-development/agents/*.md | wc -l
# Expected: 8 (Option B/A) or 9 (Option C)

ls -1 plugins/development-harness/agents/*.md | wc -l
# Expected: 12
```

**2. Stale namespace references (must return zero):**
```bash
grep -r "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
  plugins/ .claude/rules/ --include="*.md" --exclude-dir=backlog --exclude-dir=agents
```

**3. Plugin validation (both must exit 0):**
```bash
uvx skilllint@latest check plugins/python3-development
uvx skilllint@latest check plugins/development-harness
```

**4. Confirm KEEP agents exist (all 8 must print OK):**
```bash
for f in python-cli-architect python-pytest-architect python-cli-design-spec \
  python-code-reviewer code-reviewer semantic-code-search t0-baseline-capture \
  tn-verification-gate; do
  ls plugins/python3-development/agents/${f}.md && echo "OK: ${f}" || echo "MISSING: ${f}"
done
```

**5. Confirm dh agents exist (all 10 must print OK):**
```bash
for f in feature-researcher codebase-analyzer context-gathering context-refinement \
  plan-validator feature-verifier integration-checker doc-drift-auditor \
  swarm-task-planner ecosystem-researcher; do
  ls plugins/development-harness/agents/${f}.md && echo "OK: ${f}" || echo "MISSING FROM DH: ${f}"
done
```

**6. Pre-deletion diff verification (no python3-dev content missing from dh):**
```bash
for agent in feature-researcher codebase-analyzer context-gathering context-refinement \
  plan-validator feature-verifier integration-checker doc-drift-auditor \
  swarm-task-planner ecosystem-researcher; do
  diff plugins/python3-development/agents/${agent}.md \
       plugins/development-harness/agents/${agent}.md \
    && echo "IDENTICAL: ${agent}" || echo "DIFFERS: ${agent}"
done
```

### Execution Sequence

```
T1 (Decision Gate)
  ↓ produces plan/D1-ecosystem-researcher-decision.md
T2 (Delete 11 files per D1)
  ↓ depends on T1 outcome for v1.1 handling
T3/T4/T5/T6 (Parallel reference updates to 4 files)
  ├─ T3: .claude/rules/local-workflow.md
  ├─ T4: plugins/python3-development/skills/orchestrate/SKILL.md
  ├─ T5: plugins/python3-development/skills/python3-development/references/python-development-orchestration.md
  └─ T6: plugins/python3-development/CLAUDE.md (or README.md)
T7 (Validation + commit)
  ↓ depends on T3+T4+T5+T6 all complete
```

### Sync Checkpoints

- **After T1**: D1 decision is explicit and recorded in plan/D1-ecosystem-researcher-decision.md
- **After T2**: Agent file counts match expected (8 in p3d, 12 in dh)
- **After T3/T4/T5/T6**: All reference updates complete, no file has conflicting edits
- **T7**: All validation checks pass before committing
