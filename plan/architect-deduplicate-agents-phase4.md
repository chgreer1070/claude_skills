---
title: Architecture Spec — Deduplicate Agents Phase 4
slug: deduplicate-agents-phase4
status: READY
generated: 2026-03-18
feature-context: plan/feature-context-deduplicate-agents-phase4.md
codebase-analysis: plan/codebase/AGENTS.md
---

# Architecture Spec: Deduplicate Agents Phase 4

## Scope Statement

Delete 10 duplicate agents from `plugins/python3-development/agents/` and handle the v1.1
versioned variant. Update all references that previously pointed to the
`python3-development:` namespace for these agents to use `dh:` instead. Leave the 8
domain-specific Python agents in `plugins/python3-development/agents/` untouched.

This spec covers HOW to execute the change, not WHY (see feature-context for that).

---

## Authoritative Agent Classification

### Delete from `plugins/python3-development/agents/` (11 files)

These exist in both plugins. `development-harness` is the canonical source after Phase 1.

```text
feature-researcher.md
codebase-analyzer.md
context-gathering.md
context-refinement.md
plan-validator.md
feature-verifier.md
integration-checker.md
doc-drift-auditor.md
swarm-task-planner.md
ecosystem-researcher.md
ecosystem-researcher-v1.1-rt-ica.md   ← see Decision Point D1 below
```

### Keep in `plugins/python3-development/agents/` (8 files)

Domain-specific — NOT present in dh:

```text
python-cli-architect.md
python-pytest-architect.md
python-cli-design-spec.md
python-code-reviewer.md
code-reviewer.md
semantic-code-search.md
t0-baseline-capture.md
tn-verification-gate.md
```

### plugin.json

`plugins/python3-development/plugin.json` does not exist — the plugin uses auto-discovery.
No json edits are required. Deleting agent `.md` files is sufficient to deregister them.

---

## Decision Point D1: ecosystem-researcher-v1.1-rt-ica.md

### Observed difference

`plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md`:

```yaml
tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch,
       mcp__Ref__ref_search_documentation, mcp__Ref__ref_read_url,
       mcp__exa__get_code_context_exa, mcp__sequential_thinking__sequentialthinking
model: haiku
color: purple
```

`plugins/development-harness/agents/ecosystem-researcher.md`:

```yaml
tools: Read, Grep, Glob, mcp__ref__*, mcp__exa__*, mcp__context7__*, mcp__firecrawl__*
model: haiku
color: blue
description: "...Requires MCP research servers (Ref, exa, context7, or firecrawl) — BLOCKs if none available."
```

### Key capability difference

v1.1 has `WebSearch` and `WebFetch` as direct fallback when MCP servers are unavailable.
The dh version explicitly BLOCKs when no MCP server is available — this is intentional
constraint, not an omission. The dh version also uses wildcard `mcp__*` patterns (more
permissive than v1.1's explicit enumeration).

### Options

**Option A** — Merge WebSearch/WebFetch fallback into dh before deleting v1.1.
Adds tools `WebSearch`, `WebFetch` to dh `ecosystem-researcher.md` tool list and updates
description to mention direct-web fallback. Removes the BLOCK-on-no-MCP constraint.

**Option B** (recommended default) — Delete v1.1 as-is.
The dh version's BLOCK behavior is the intended design: the agent requires MCP research
infrastructure. Using WebSearch/WebFetch without that infrastructure produces lower-quality
research. The explicit BLOCK surfaces the missing dependency rather than silently degrading.
The v1.1 Python-specific framing is not needed in a general ecosystem researcher.

**Option C** — Rename v1.1 to `python-ecosystem-researcher.md` and keep it as a
python3-development-specific agent. Use when Python project research needs direct web access.

**Recommended**: Option B. Record rationale in commit message. No file in either plugin
references `ecosystem-researcher-v1.1-rt-ica.md` directly (verified in codebase analysis),
so deletion has zero reference-update impact.

**This decision must be confirmed by the implementer before Step 1 executes.**
If Option A or C is chosen, Step 0 (pre-deletion merge/rename) is inserted before Step 1.

---

## Execution Sequence

Steps are ordered for safety. Steps 1 and 2 can be batched in one commit.
Steps 3–6 are per-file reference updates and can each be separate commits or
batched together. Step 7 (validation) is always last.

### Step 0 (conditional): Ecosystem-researcher v1.1 pre-deletion action

Execute ONLY if D1 resolves to Option A or C. Skip if Option B.

**Option A path**:
- Edit `plugins/development-harness/agents/ecosystem-researcher.md`:
  - Add `WebSearch`, `WebFetch` to `tools:` line
  - Update `description:` to remove "BLOCKs if none available" and add
    "Falls back to WebSearch/WebFetch when MCP servers unavailable"
- Delegate edit to `plugin-creator:contextual-ai-documentation-optimizer`
  (per MEMORY.md: never write agent body content directly as orchestrator)

**Option C path**:
- Rename `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md`
  to `plugins/python3-development/agents/python-ecosystem-researcher.md`
- Edit frontmatter `name:` field from `ecosystem-researcher` to
  `python-ecosystem-researcher`
- No reference updates needed (the v1.1 file has zero existing references)

### Step 1: Delete the 10 shared agents from python3-development

Delete these files from `plugins/python3-development/agents/`:

```text
feature-researcher.md
codebase-analyzer.md
context-gathering.md
context-refinement.md
plan-validator.md
feature-verifier.md
integration-checker.md
doc-drift-auditor.md
swarm-task-planner.md
ecosystem-researcher.md
```

If D1 → Option B: also delete `ecosystem-researcher-v1.1-rt-ica.md`.
If D1 → Option C: `ecosystem-researcher-v1.1-rt-ica.md` was renamed in Step 0 — do not delete.

**Parallel safety**: Step 1 deletions are independent of each other. All 10 (or 11)
deletions can execute in one `git rm` command. No ordering required within this step.

**Verification after Step 1**:

```bash
# Confirm deleted agents no longer exist in python3-development
ls plugins/python3-development/agents/
# Expected: 8 files (the KEEP list above, plus python-ecosystem-researcher.md if Option C)

# Confirm dh copies still exist
ls plugins/development-harness/agents/
# Expected: 12 files (unchanged)
```

### Step 2: Update `.claude/rules/local-workflow.md` — Agent File Locations tables

**What changes**: The "Agent File Locations" tables in Phase 1 and Phase 3 currently show
both `python3-development` and `development-harness` columns for the 10 shared agents.
After deletion, the `python3-development` column cells for those agents are dead references.

**Design decision for table format** (resolves Q3 from feature-context):
Remove the `python3-development` column entirely from the Agent File Locations tables.
The tables become single-column showing only `development-harness` paths for shared agents.
This is cleaner than a forwarding note and makes the single-source-of-truth observable.

For agents that exist ONLY in `python3-development` (the 8 KEEP agents), their rows remain
with `python3-development` as the only column.

**Specific locations to update** (from codebase analysis):

Phase 1 table (lines ~54-63 of local-workflow.md):
- Remove `python3-development` column cells for: `feature-researcher`, `codebase-analyzer`,
  `context-gathering`, `plan-validator`, `swarm-task-planner`, `context-gathering`
- Rows for `python-cli-design-spec`, `t0-baseline-capture`, `tn-verification-gate` retain
  their `python3-development` column (these are KEEP agents)

Phase 3 table (lines ~269-276 of local-workflow.md):
- Remove `python3-development` column cells for: `feature-verifier`, `integration-checker`,
  `doc-drift-auditor`, `context-refinement`
- Rows for `code-reviewer`, `t0-baseline-capture`, `tn-verification-gate` retain their
  `python3-development` column (these are KEEP agents)
- `service-docs-maintainer` row stays as dh-only (unchanged)

Data Flow Diagram (if it lists agent file paths):
- Any `python3-development:` references for the 10 deleted agents → update to `dh:`

**Delegate to**: `python3-development:python-cli-architect` (document editing task,
not agent content authoring — MEMORY.md rule applies to agent bodies, not workflow docs).

### Step 3: Update `plugins/python3-development/skills/orchestrate/SKILL.md`

**What changes**: This file references `python3-development:swarm-task-planner` in
delegation guidance. After deletion, this resolves to a missing agent.

**Specific change**:
- Any `subagent_type="python3-development:swarm-task-planner"` →
  `subagent_type="dh:swarm-task-planner"`

**Scope note**: The codebase analysis confirms `orchestrate/SKILL.md` references
`python-cli-architect`, `python-pytest-architect`, `python-code-reviewer`,
`python-cli-design-spec` — these are KEEP agents in python3-development, so those
references remain valid and must NOT be changed.

Only the `swarm-task-planner` reference crosses the namespace boundary.

**Delegate to**: `python3-development:python-cli-architect`

### Step 4: Update `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`

**What changes**: This document references `swarm-task-planner` as a workflow step.
Per the grep results, it uses `python3-development:swarm-task-planner` (and
`python3-development:feature-researcher`, `python3-development:codebase-analyzer`, etc.
for any shared-agent namespace references found in the document).

**Specific changes**:
For each of the 10 deleted agents, any reference using `python3-development:{agent-name}`
namespace must become `dh:{agent-name}`.

The domain-specific agents (`python-cli-architect`, `python-pytest-architect`,
`python-code-reviewer`, `python-cli-design-spec`) keep their `python3-development:` prefix.

**Scope clarification** (codebase analysis confusion):
The codebase analysis lists `python-cli-architect`, `python-pytest-architect`,
`python-code-reviewer`, `python-cli-design-spec` as "to remove" — this is wrong per the
authoritative classification. These agents remain. The implementer must update ONLY
namespace references for the 10 deleted agents. Do not touch references to KEEP agents.

**Delegate to**: `python3-development:python-cli-architect`

### Step 5: Add forwarding note to `plugins/python3-development/README.md` or `CLAUDE.md`

**What changes**: A human reading the python3-development plugin directory should
understand that shared workflow agents live in development-harness after Phase 4.

**Format**: Add a section near the top of the CLAUDE.md (developer-facing) stating:

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

**Note**: If neither `README.md` nor `CLAUDE.md` exists in `plugins/python3-development/`,
check `plugins/python3-development/SKILL.md` or the plugin root for the appropriate
developer-facing document. The implementer must verify the target file exists before editing.

**Delegate to**: `python3-development:python-cli-architect`

### Step 6: Verify backlog files and MEMORY.md (read-only audit)

The grep results show `python3-development:{shared-agent}` references appear in:
- `.claude/backlog/*.md` files (backlog items referencing the old namespace)
- `.claude/kaizen-data-analysis.md`
- `.continuehere.md`
- `plugins/plugin-creator/skills/agent-capability-analyzer/scripts/populate-agent-descriptions.mjs`

**Decision**: Backlog files and analysis notes are historical records — they document
what existed at the time they were written. Updating them to change agent namespaces
would falsify the historical record. **Do not update these files.**

The `populate-agent-descriptions.mjs` script is an exception: if it dynamically invokes
agents (not just documents them), the implementer must read it to determine if it needs
updating. If it only catalogs agent descriptions, leave it unchanged.

**Action**: The implementer reads `populate-agent-descriptions.mjs` to determine if it
invokes agents or only describes them. If it invokes, update namespace references for
deleted agents. If it describes only, no change needed.

---

## Reference Update Design Summary

| File | Change Type | Agents Affected | Notes |
|------|-------------|-----------------|-------|
| `.claude/rules/local-workflow.md` | Table restructure | 10 deleted agents | Remove p3d column for deleted agents |
| `plugins/python3-development/skills/orchestrate/SKILL.md` | Namespace update | swarm-task-planner only | KEEP agents unchanged |
| `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md` | Namespace update | All 10 deleted agents | KEEP agents unchanged |
| `plugins/python3-development/CLAUDE.md` (or README.md) | Forwarding note | N/A — informational | Verify target file exists |
| `.claude/backlog/*.md` | No change | — | Historical records |
| `plugins/plugin-creator/.../populate-agent-descriptions.mjs` | Conditional | 10 deleted agents | Depends on whether it invokes or describes |

---

## Validation Design

### Pre-deletion diff check (optional but recommended)

Before deleting, run a content diff between each python3-development agent and its dh
counterpart to confirm dh is the superset. This resolves Q4 from the feature-context.

```bash
# Example for one agent — repeat for all 10
diff plugins/python3-development/agents/feature-researcher.md \
     plugins/development-harness/agents/feature-researcher.md
```

If any diff shows python3-development has content NOT in dh (not merely formatting
differences), that content must be merged to dh before deletion proceeds.

### Post-deletion namespace check

After Steps 1-5 complete, verify no `python3-development:` namespace references remain
for the deleted agents:

```bash
# Check for stale python3-development: references for deleted agents
grep -r "python3-development:\(feature-researcher\|codebase-analyzer\|context-gathering\|context-refinement\|plan-validator\|feature-verifier\|integration-checker\|doc-drift-auditor\|swarm-task-planner\|ecosystem-researcher\)" \
  plugins/ .claude/rules/ \
  --include="*.md" \
  --exclude-dir=backlog \
  --exclude-dir=agents
```

Expected result: zero matches. Any match is a reference that was missed.

### Plugin validator run

Run the plugin validator on both plugins after all changes:

```bash
uvx skilllint@latest check plugins/python3-development
uvx skilllint@latest check plugins/development-harness
```

Both must pass with no errors introduced by this change.

### Agent file inventory check

```bash
# Confirm python3-development has exactly 8 agents (or 9 if Option C chosen)
ls -1 plugins/python3-development/agents/*.md | wc -l
# Expected: 8 (Option B) or 9 (Option C)

# Confirm development-harness agent count is unchanged at 12
ls -1 plugins/development-harness/agents/*.md | wc -l
# Expected: 12
```

### No broken agent references

```bash
# Confirm all @dh: references in updated files resolve to existing dh agents
# Manual verification: for each updated reference, confirm the target file exists
ls plugins/development-harness/agents/swarm-task-planner.md
ls plugins/development-harness/agents/feature-researcher.md
# ... repeat for each agent that now routes to dh
```

---

## Rollback Strategy

All changes are git-tracked. If any step produces an unexpected result:

```bash
# Rollback to pre-Phase-4 state entirely
git revert HEAD~N  # N = number of Phase 4 commits

# Or restore individual files
git checkout HEAD~1 -- plugins/python3-development/agents/feature-researcher.md
```

If changes are committed as a single commit (recommended), a single `git revert` restores
all deleted files and reference updates atomically.

**Recommended commit strategy**: One commit per logical step (deletion, each reference
file update), with clear commit messages. This enables targeted rollback of a single step
without undoing others.

**Commit message format**:

```text
refactor(agents): remove 10 shared agents from python3-development (Phase 4)

dh is now the sole provider of: feature-researcher, codebase-analyzer,
context-gathering, context-refinement, plan-validator, feature-verifier,
integration-checker, doc-drift-auditor, swarm-task-planner, ecosystem-researcher.

Phase 1 (commit 29387b59) established dh as canonical. Phase 4 makes that
observable in the filesystem by removing the stale python3-development copies.

ecosystem-researcher-v1.1-rt-ica.md: [deleted as deprecated / renamed to
python-ecosystem-researcher / merged into dh — choose per D1 decision]
```

---

## Implementation Order and Parallelism

```text
Step 0  (conditional)   — D1 decision determines if this runs
  |
Step 1  (file deletion) — Independent. All 10-11 deletes in one git rm.
  |
  +-- Step 2 (local-workflow.md)        ─┐
  +-- Step 3 (orchestrate/SKILL.md)      ├── Can run in parallel
  +-- Step 4 (python-development-orch)   ├── No inter-dependencies
  +-- Step 5 (CLAUDE.md forwarding note) ┘
  |
Step 6  (populate-agent-descriptions.mjs audit — conditional update)
  |
Step 7  (Validation: diff check, grep, plugin validator, inventory count)
```

Steps 2-5 have no dependency on each other — they touch different files. They can be
delegated to four parallel agent invocations if desired.

Step 7 must follow all other steps.

---

## Open Questions Resolved by This Spec

| Q# | Resolution |
|----|-----------|
| Q1 (ecosystem-researcher v1.1) | Decision Point D1 — implementer confirms Option before Step 1 |
| Q2 (plugin.json) | Resolved: plugin.json does not exist, auto-discovery applies, no update needed |
| Q3 (local-workflow.md format) | Resolved: remove python3-development column for deleted agents; keep column for KEEP agents |
| Q4 (dh copy completeness) | Pre-deletion diff check in Validation Design section covers this |

---

## Acceptance Criteria

- [ ] `plugins/python3-development/agents/` contains exactly 8 files (the KEEP list) after deletion
- [ ] `plugins/development-harness/agents/` count is unchanged (12 files)
- [ ] Zero `python3-development:{deleted-agent}` references remain in `plugins/` or `.claude/rules/`
  (excluding `backlog/` and historical analysis notes)
- [ ] `uvx skilllint@latest check plugins/python3-development` passes
- [ ] `uvx skilllint@latest check plugins/development-harness` passes
- [ ] `.claude/rules/local-workflow.md` Agent File Locations tables show only dh paths for the 10 deleted agents
- [ ] D1 decision is recorded in the deletion commit message
- [ ] `plugins/python3-development/CLAUDE.md` (or equivalent) has forwarding note for the moved agents
