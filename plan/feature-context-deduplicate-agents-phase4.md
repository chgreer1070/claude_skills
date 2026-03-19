# Feature Context: Deduplicate Agents Phase 4

## Document Metadata

- **Generated**: 2026-03-18
- **Input Type**: simple_description
- **Source**: Feature request — remove 10 duplicate agents from python3-development, make development-harness the sole provider
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Remove 10 duplicate agents from `plugins/python3-development/agents/` so development-harness (dh) becomes the sole agent provider. Python3-development retains only domain-specific agents.

Agents to DELETE from `plugins/python3-development/agents/`:
- `feature-researcher.md`, `codebase-analyzer.md`, `context-gathering.md`, `context-refinement.md`, `plan-validator.md`, `feature-verifier.md`, `integration-checker.md`, `doc-drift-auditor.md`, `swarm-task-planner.md`, `ecosystem-researcher.md`
- `ecosystem-researcher-v1.1-rt-ica.md` (needs reconciliation)

References to update after deletion:
- `plugins/python3-development/skills/orchestrate/SKILL.md`
- `plugins/python3-development/references/python-development-orchestration.md`
- `.claude/rules/local-workflow.md`
- `plugins/python3-development/README.md` or `CLAUDE.md`
- `plugins/python3-development/plugin.json` if it has an explicit agent list

Background: Phase 1 (dh agents synced via COPY-THEN-PATCH, commit 29387b59) — DONE. Phase 3 (backlog skills moved to dh, commit 5e3231ce) — DONE. 9 domain-specific agents remain in python3-development after deletion.

---

## Core Intent Analysis

### WHO (Target Users)

Maintainers of the claude_skills plugin repository who need to locate, update, and reason about agents. Specifically anyone reading `local-workflow.md`, orchestrating the SAM workflow, or onboarding to how the two plugins relate.

### WHAT (Desired Outcome)

After this change:

- The 10 listed agents exist only under `plugins/development-harness/agents/`
- `plugins/python3-development/agents/` contains only agents that are genuinely Python-specific (currently: `python-cli-architect`, `python-cli-design-spec`, `python-pytest-architect`, `python-code-reviewer`, `code-reviewer`, `semantic-code-search`, `t0-baseline-capture`, `tn-verification-gate`, `python-cli-architect`)
- All documentation that previously listed both plugin locations for the same agent now points exclusively to `@dh:` namespace for the shared agents
- No broken references remain — documentation consumers can follow every agent citation to a real file

### WHEN (Trigger Conditions)

This change is triggered because Phase 1 completed the sync: the dh copies are confirmed authoritative. Keeping both copies active means:
- Fixes to a shared agent must be applied in two places
- Documentation lists both plugins in "Agent File Locations" tables, implying both are valid sources, which is no longer true
- Users invoking `@python3-development:feature-researcher` get the stale copy; the live version is `@dh:feature-researcher`

### WHY (Problem Being Solved)

**Dual-source maintenance burden**: When the same agent body exists in two plugin directories, any improvement must be applied twice. History shows this leads to silent divergence — one copy gets updated, the other does not.

**Discoverability confusion**: `local-workflow.md` currently shows "Agent File Locations" tables with both `python3-development` and `development-harness` columns for the same agents. A reader cannot tell which is authoritative. New contributors will invoke the wrong namespace.

**Single source of truth**: The Phase 1 decision established dh as the owner of shared workflow agents. The file deletions make that decision observable in the filesystem, not just documented in a commit message.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Phase 1 COPY-THEN-PATCH commit

- **Location**: Commit `29387b59` (referenced in feature request background)
- **Relevance**: Established the canonical copies in dh. The dh agents are already live and in use — the python3-development copies are now the stale duplicates, not the other way around.
- **Reusable**: Commit message convention "COPY-THEN-PATCH" confirms intent: dh was the destination.

#### Pattern 2: local-workflow.md Agent File Locations tables

- **Location**: `.claude/rules/local-workflow.md` (Agent File Locations section, multiple tables)
- **Relevance**: These tables explicitly list both `python3-development` and `development-harness` columns for shared agents. After deletion, the `python3-development` column cells for the 10 agents will have no corresponding file and must be updated to show `@dh:` namespace only.
- **Reusable**: The table structure already knows which agents are shared — it is the authoritative list of what needs updating in docs.

#### Pattern 3: ecosystem-researcher-v1.1-rt-ica.md divergence

- **Location**: `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md:1-8`
- **Relevance**: This file has a different tool set from both the plain `ecosystem-researcher.md` in python3-development and the dh counterpart. Key differences observed:
  - `ecosystem-researcher-v1.1-rt-ica.md`: `tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch, mcp__Ref__ref_search_documentation, mcp__Ref__ref_read_url, mcp__exa__get_code_context_exa, mcp__sequential_thinking__sequentialthinking` — includes `WebSearch`, `WebFetch`, `Write`, `Edit`
  - `plugins/python3-development/agents/ecosystem-researcher.md` (lines 1-8): identical frontmatter to dh counterpart — `tools: Read, Grep, Glob, mcp__ref__*, mcp__exa__*, mcp__context7__*, mcp__firecrawl__*` — MCP-only, no direct web tools
  - Role description in v1.1: "ecosystem researcher for **Python projects**" — Python-scoped framing not present in dh version
- **Reusable**: If the v1.1 improvements (WebSearch/WebFetch fallback when MCP servers unavailable, Python-specific framing) are valuable, they need to be assessed against the dh counterpart before the v1.1 file is deleted.

#### Pattern 4: Remaining domain-specific agents in python3-development

- **Location**: `plugins/python3-development/agents/` — files not in the deletion list
- **Relevance**: After deletion, the surviving agents are: `python-cli-architect.md`, `python-cli-design-spec.md`, `python-pytest-architect.md`, `python-code-reviewer.md`, `code-reviewer.md`, `semantic-code-search.md`, `t0-baseline-capture.md`, `tn-verification-gate.md`
- **Reusable**: Confirms that python3-development keeps 8–9 agents that are genuinely Python-specific. The deletion list is coherent — it removes only the non-language-specific workflow agents.

### Code References

- `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md:1-8` — v1.1 frontmatter showing divergent tool set
- `plugins/python3-development/agents/ecosystem-researcher.md:1-8` — identical to dh counterpart
- `plugins/development-harness/agents/ecosystem-researcher.md:1-8` — MCP-only tools, confirmed dh canonical copy
- `plugins/development-harness/CLAUDE.md:178` — lists `@dh:ecosystem-researcher` as live agent

---

## Use Scenarios

### Scenario 1: Contributor invokes a shared agent

**Actor**: Plugin contributor running a SAM workflow
**Trigger**: Needs to invoke `feature-researcher` during planning
**Goal**: Find the right namespace (`@dh:feature-researcher` vs `@python3-development:feature-researcher`)
**Expected Outcome**: After this change, only `@dh:feature-researcher` resolves. Contributor cannot accidentally invoke the stale python3-development copy.

### Scenario 2: Maintainer patches a shared agent

**Actor**: Plugin maintainer improving `context-gathering` agent body
**Trigger**: Bug found or improvement needed in context gathering behavior
**Goal**: Apply fix once, have it take effect everywhere
**Expected Outcome**: After this change, only one file exists (`plugins/development-harness/agents/context-gathering.md`). One edit is sufficient. No risk of the python3-development copy silently remaining stale.

### Scenario 3: New contributor reads local-workflow.md

**Actor**: Developer onboarding to the SAM workflow
**Trigger**: Following the "Agent File Locations" tables in `local-workflow.md`
**Goal**: Understand where to find each agent
**Expected Outcome**: After this change, the table shows `development-harness` as the sole location for shared agents. No ambiguity about which plugin owns them.

### Scenario 4: ecosystem-researcher v1.1 assessment

**Actor**: Maintainer deciding what to do with `ecosystem-researcher-v1.1-rt-ica.md`
**Trigger**: This file is not a straight duplicate — it has WebSearch/WebFetch and Python-specific framing not present in dh counterpart
**Goal**: Either preserve the v1.1 improvements by merging them into dh, or confirm the v1.1 is superseded/deprecated
**Expected Outcome**: A clear decision is recorded. If improvements are merged to dh before deletion, no capability is lost. If deprecated, a rationale is documented.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `ecosystem-researcher-v1.1-rt-ica.md` has a different tool set and Python-specific framing not present in the dh counterpart — it is not a straight duplicate | If deleted without review, the WebSearch/WebFetch fallback capability and Python framing may be lost |
| 2 | Integration | `plugin.json` for python3-development could not be found at expected path — unclear if it has an explicit agents list that would need updating | If plugin.json has `"agents": [...]` entries, deleting files without updating it breaks plugin registration |
| 3 | Behavior | References in `plugins/python3-development/skills/orchestrate/SKILL.md` and `references/python-development-orchestration.md` may invoke shared agents by python3-development namespace — these would break silently after deletion | Orchestration workflows that hard-code `python3-development:feature-researcher` etc. would fail with no agent found |
| 4 | Scope | Whether `context-refinement` is in dh was not separately verified — the dh agents/ listing shows it exists, but the body content has not been compared | If dh `context-refinement` is missing content from the python3-development copy, deletion causes capability regression |
| 5 | Integration | `.claude/rules/local-workflow.md` has "Agent File Locations" tables — the exact table format after update is unspecified | Doc update approach (remove python3-dev column? replace with dh-only rows? add forwarding note?) is not decided |

---

## Questions Requiring Resolution

### Q1: ecosystem-researcher v1.1 — preserve or deprecate?

- **Category**: Scope
- **Gap**: `ecosystem-researcher-v1.1-rt-ica.md` uses `WebSearch`, `WebFetch`, `Write`, `Edit` tools and frames itself as "Python projects" researcher. The dh counterpart uses MCP-only tools and has no Python framing. These are functionally different agents.
- **Question**: Should the v1.1 improvements (WebSearch/WebFetch fallback, Python framing) be merged into the dh `ecosystem-researcher` before the v1.1 file is deleted? Or is the v1.1 considered superseded/deprecated and can be deleted as-is?
- **Options**:
  - A) Merge v1.1 tool set and Python framing into dh before deleting
  - B) Delete v1.1 as-is — the MCP-only dh version is intentionally the canonical form (tools limited by design, not by omission)
  - C) Keep v1.1 as a python3-development-specific agent under a new name (e.g., `python-ecosystem-researcher`) rather than deleting
- **Why It Matters**: If deleted without merge, any workflow relying on WebSearch fallback when MCP servers are unavailable will silently degrade to BLOCKED on the dh agent.
- **Resolution**: _pending_

### Q2: Does plugin.json have an explicit agents list?

- **Category**: Integration
- **Gap**: `plugins/python3-development/plugin.json` was not found at the expected path. Per CLAUDE.md memory: "Declaring a subset overrides auto-discovery entirely — unlisted components become invisible." If an explicit agents list exists, the file deletions alone are insufficient.
- **Question**: Does `plugins/python3-development/plugin.json` exist, and if so, does it declare an explicit `"agents"` array? If so, what entries need to be removed after deletion?
- **Options**:
  - A) plugin.json does not exist (or has no `"agents"` key) — file deletion is sufficient
  - B) plugin.json exists with explicit agents list — must remove the 10 deleted agent entries
- **Why It Matters**: Leaving deleted agents in plugin.json means users see agent names that resolve to missing files — confusing error rather than clean absence.
- **Resolution**: _pending_

### Q3: How should local-workflow.md Agent File Locations tables be updated?

- **Category**: Integration
- **Gap**: The tables currently have two columns — `python3-development` and `development-harness` — for 10+ agents. After deletion, the python3-development column cells for the 10 shared agents are dead references.
- **Question**: What is the desired post-deletion format for these tables?
- **Options**:
  - A) Remove the `python3-development` column entirely for shared agents — show only dh location
  - B) Replace python3-development cell content with a forwarding note: "→ see @dh:"
  - C) Add a preamble note above the table: "Shared agents moved to development-harness in Phase 4" and leave table rows pointing only to dh
- **Why It Matters**: The tables are read by contributors and orchestrators. Ambiguous or stale entries cause invocation of wrong namespace.
- **Resolution**: _pending_

### Q4: Have all 10 dh copies been verified as complete (not missing content from python3-dev versions)?

- **Category**: Behavior
- **Gap**: Phase 1 was described as "COPY-THEN-PATCH." This research verified that `ecosystem-researcher.md` in python3-development is identical to its dh counterpart. The other 9 agents were not individually compared.
- **Question**: Has a diff between each python3-development agent and its dh counterpart been performed to confirm dh is the superset? Or should that comparison be part of this phase's work?
- **Options**:
  - A) Comparison was done in Phase 1 — dh copies are confirmed authoritative, deletion can proceed
  - B) Comparison should be performed as part of Phase 4 before deleting any file
- **Why It Matters**: If any python3-development copy has content not present in its dh counterpart (e.g., a fix applied to one but not propagated to the other), deletion causes silent capability loss.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. The 10 named agents exist only in `plugins/development-harness/agents/` after this phase completes
2. `ecosystem-researcher-v1.1-rt-ica.md` is either merged into dh or explicitly deprecated with rationale recorded
3. All documentation references to the deleted agents by `python3-development:` namespace are updated to `dh:` namespace
4. `plugin.json` (if it exists with explicit agent list) is updated to remove deleted entries
5. No broken agent references remain in `local-workflow.md`, `orchestrate/SKILL.md`, or `python-development-orchestration.md`
6. A commit message or comment records which agents were deleted and why (single source of truth rationale)

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to architecture design (deletion is mechanical but reference updates need scoping)
4. Proceed to task planning — tasks are: (a) diff verification, (b) file deletions, (c) reference updates per file, (d) plugin.json update if needed
