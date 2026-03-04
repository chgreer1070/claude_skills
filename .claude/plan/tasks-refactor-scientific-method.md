# Refactoring Tasks: Scientific Method Plugin

**Plugin**: plugins/scientific-method
**Assessment Score**: 82/100
**Design File**: .claude/plan/scientific-method/refactor-design-scientific-method.md
**Created**: 2026-03-04T00:00:00Z

## Summary

- Total Tasks: 6
- Refactoring Tasks: 4
- Verification Tasks: 2
- Parallelization Groups: 2 (Group A: Tasks 1-4 all independent, Group B: V1, V2 sequential)

---

## Task 1: Remove Navigation Links from investigation-workflow.md

**Status**: ❌ NOT STARTED
**Dependencies**: None
**Priority**: 2
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer

**Target**: plugins/scientific-method/shared/investigation-workflow.md
**Issue Type**: STRUCTURE_FIX

**Acceptance Criteria**:

1. Lines 388-393 (the `## Navigation` section and its preceding `---` separator) are removed from the file
2. No links traversing outside `plugins/scientific-method/` remain anywhere in the file (specifically no `../../../.claude/knowledge/` paths)
3. File ends cleanly — the final line is content, not a dangling separator or empty navigation header

**Required Inputs**:

- Design spec section: "Structure Fixes > Navigation Links Removal"
- Source files: plugins/scientific-method/shared/investigation-workflow.md

**Expected Outputs**:

- plugins/scientific-method/shared/investigation-workflow.md (modified — navigation section removed)

**Can Parallelize With**: Task 2, Task 3, Task 4
**Reason**: Each task targets a different file; no shared write state between Tasks 1, 2, 3, and 4

**Verification Steps**:

1. Run `grep -n "\.claude/knowledge" plugins/scientific-method/shared/investigation-workflow.md` — must return no matches
2. Run `grep -n "## Navigation" plugins/scientific-method/shared/investigation-workflow.md` — must return no matches
3. Read the final 5 lines of the file and confirm the file ends on content, not a bare `---` separator or empty section header

---

## Task 2: Add tools Field to retrospective-analyst.md

**Status**: ❌ NOT STARTED
**Dependencies**: None
**Priority**: 3
**Complexity**: Low
**Agent**: subagent-refactorer

**Target**: plugins/scientific-method/agents/retrospective-analyst.md
**Issue Type**: AGENT_OPTIMIZE

**Acceptance Criteria**:

1. YAML frontmatter contains `tools: [Read, Write]` on the line immediately after the `description` field
2. No other frontmatter fields are added, removed, or reordered — only the `tools` field is inserted
3. Plugin validator `FrontmatterValidator` passes on the file after the change

**Required Inputs**:

- Design spec section: "Agent Optimizations > retrospective-analyst Tools Field"
- Source files: plugins/scientific-method/agents/retrospective-analyst.md

**Expected Outputs**:

- plugins/scientific-method/agents/retrospective-analyst.md (modified — `tools` field added to frontmatter)

**Can Parallelize With**: Task 1, Task 3, Task 4
**Reason**: Each task targets a different file; no shared write state between Tasks 1, 2, 3, and 4

**Verification Steps**:

1. Run `grep -n "^tools:" plugins/scientific-method/agents/retrospective-analyst.md` — must return exactly one match with value `[Read, Write]`
2. Read the full frontmatter block (between `---` delimiters) and confirm field order is: `name`, `description`, `tools`
3. Run `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/scientific-method --verbose` and confirm no new FrontmatterValidator errors appear for `retrospective-analyst.md`

---

## Task 3: Sync README Version to 1.2.0

**Status**: ❌ NOT STARTED
**Dependencies**: None
**Priority**: 3
**Complexity**: Low
**Agent**: contextual-ai-documentation-optimizer

**Target**: plugins/scientific-method/README.md
**Issue Type**: DOC_IMPROVE

**Acceptance Criteria**:

1. The version string in README.md reads `1.2.0` (was `1.1.0`)
2. The version in `plugin.json` (`1.2.0`) matches the version in `README.md` exactly
3. No other content in README.md is modified — only the version string is updated

**Required Inputs**:

- Design spec section: "Documentation Improvements > README Version Sync"
- Source files: plugins/scientific-method/README.md, plugins/scientific-method/plugin.json

**Expected Outputs**:

- plugins/scientific-method/README.md (modified — version string updated from `1.1.0` to `1.2.0`)

**Can Parallelize With**: Task 1, Task 2, Task 4
**Reason**: Each task targets a different file; no shared write state between Tasks 1, 2, 3, and 4

**Verification Steps**:

1. Run `grep -n "1\.1\.0" plugins/scientific-method/README.md` — must return no matches
2. Run `grep -n "1\.2\.0" plugins/scientific-method/README.md` — must return at least one match
3. Run `grep "version" plugins/scientific-method/plugin.json` and confirm the value matches the version now in README.md

---

## Task 4: Fix experiment-protocol/SKILL.md (Markup Cleanup + Integration Note)

**Status**: ❌ NOT STARTED
**Dependencies**: None
**Priority**: 2
**Complexity**: Medium
**Agent**: contextual-ai-documentation-optimizer

**Target**: plugins/scientific-method/skills/experiment-protocol/SKILL.md
**Issue Type**: DOC_IMPROVE

**Acceptance Criteria**:

1. No `<eg>` or `</eg>` tags remain anywhere in the file — both Block 1 (lines 87-113) and Block 2 (lines 128-147) are cleaned; content inside those tags is preserved intact
2. A `## Downstream Integration` section is present in the file, positioned after the main workflow steps and before any closing section, containing a reference to `retrospective-analyst` and description of the iteration log handoff
3. File passes markdown linting (`uv run prek run --files plugins/scientific-method/skills/experiment-protocol/SKILL.md`) with no new errors

**Required Inputs**:

- Design spec section: "Documentation Improvements > experiment-protocol Non-Standard Markup" and "Documentation Improvements > experiment-protocol Downstream Integration Note"
- Source files: plugins/scientific-method/skills/experiment-protocol/SKILL.md

**Expected Outputs**:

- plugins/scientific-method/skills/experiment-protocol/SKILL.md (modified — `<eg>`/`</eg>` tags removed, `## Downstream Integration` section added)

**Can Parallelize With**: Task 1, Task 2, Task 3
**Reason**: Each task targets a different file; no shared write state between Tasks 1, 2, 3, and 4

**Verification Steps**:

1. Run `grep -n "<eg>\|</eg>" plugins/scientific-method/skills/experiment-protocol/SKILL.md` — must return no matches
2. Run `grep -n "retrospective-analyst" plugins/scientific-method/skills/experiment-protocol/SKILL.md` — must return at least one match inside the `## Downstream Integration` section
3. Run `uv run prek run --files plugins/scientific-method/skills/experiment-protocol/SKILL.md` and confirm exit code 0 with no new linting errors

---

## Task V1: Validate Plugin Structure

**Status**: ❌ NOT STARTED
**Dependencies**: Task 1, Task 2, Task 3, Task 4
**Priority**: 1
**Complexity**: Low
**Agent**: plugin-assessor (via plugin-creator:assessor skill)

**Target**: plugins/scientific-method (full plugin directory)
**Issue Type**: STRUCTURE_FIX

**Acceptance Criteria**:

1. `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/scientific-method --verbose` exits with code 0
2. No new validator errors are introduced compared to the pre-refactoring baseline (score was 82/100)
3. InternalLinkValidator confirms no links in `investigation-workflow.md` traverse outside `plugins/scientific-method/`

**Required Inputs**:

- Design spec section: "Dependency Map" and "Parallelization Opportunities"
- Source files: plugins/scientific-method (all files modified by Tasks 1-4)

**Expected Outputs**:

- Validator output logged (no file produced — this is a gate task)

**Can Parallelize With**: None
**Reason**: V1 must verify the completed state of Tasks 1, 2, 3, and 4 — all must be COMPLETE before validation runs

**Verification Steps**:

1. Run `uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/scientific-method --verbose` and confirm exit code 0
2. Confirm reported score is >= 82/100 (no regression from baseline)
3. Confirm InternalLinkValidator section in output shows 0 broken external links for `investigation-workflow.md`

---

## Task V2: Update Plugin Documentation

**Status**: ❌ NOT STARTED
**Dependencies**: Task V1
**Priority**: 2
**Complexity**: Low
**Agent**: plugin-docs-writer

**Target**: plugins/scientific-method/README.md
**Issue Type**: DOC_IMPROVE

**Acceptance Criteria**:

1. README.md reflects the current state of the plugin after all refactoring tasks complete — including the version sync from Task 3 and any structural changes from Tasks 1 and 4
2. No content in README.md contradicts the current plugin structure or references removed features
3. README.md passes markdown linting (`uv run prek run --files plugins/scientific-method/README.md`) with exit code 0

**Required Inputs**:

- Design spec section: Full design document — all sections
- Source files: plugins/scientific-method/README.md, plugins/scientific-method/plugin.json, plugins/scientific-method/skills/experiment-protocol/SKILL.md

**Expected Outputs**:

- plugins/scientific-method/README.md (reviewed and updated if any content is stale post-refactoring)

**Can Parallelize With**: None
**Reason**: V2 depends on V1 passing — documentation update is the final step after structural validation confirms correctness

**Verification Steps**:

1. Run `grep -n "1\.1\.0" plugins/scientific-method/README.md` — must return no matches (version sync from Task 3 persisted)
2. Run `uv run prek run --files plugins/scientific-method/README.md` — must exit code 0
3. Read README.md and confirm no references to `../../../.claude/knowledge/` or other out-of-boundary paths appear in the document

---

## Context Manifest

### How This Currently Works: Plugin Structure

The `scientific-method` plugin lives at `plugins/scientific-method/` and follows the standard Claude Code plugin layout. The canonical version authority is `plugins/scientific-method/.claude-plugin/plugin.json`, which declares `"version": "1.2.0"`. The README at `plugins/scientific-method/README.md` line 5 still reads `**Version**: 1.1.0` — the mismatch this refactoring must fix.

The plugin contains three skills (`scientific-thinking`, `evidence-first-debugging`, `experiment-protocol`), one agent (`retrospective-analyst`), a `shared/` reference directory, a `hooks/` directory, and the `.claude-plugin/plugin.json` manifest. The `agents` field in plugin.json registers only `"./agents/retrospective-analyst.md"`.

### How This Currently Works: investigation-workflow.md

`plugins/scientific-method/shared/investigation-workflow.md` is 394 lines. The file was migrated from `.claude/knowledge/workflow-diagrams/investigation-workflow.md` during the plugin consolidation. The original location now contains a redirect stub pointing to the plugin path.

The file ends with this exact content at lines 387–394:

```markdown
Investigation slots into the full workflow:

- **Context** → Observation (gather facts)
- **Planning** → Hypothesis (form testable theory)
- **Execution** → Experiment (test theory)
- **Verification** → Conclusion (confirm findings)

---

## Navigation

- **Previous:** [Simple Task Workflow](../../../.claude/knowledge/workflow-diagrams/simple-task-workflow.md)
- **Next:** [RAG Retrieval Pattern](../../../.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md)
- **Back to:** [Index](../../../.claude/knowledge/workflow-diagrams/README.md)
```

The `---` separator on line 388 and the `## Navigation` section on lines 389–393 are the target for removal. The three linked paths (`../../../.claude/knowledge/workflow-diagrams/...`) traverse outside the plugin boundary and will be broken for any marketplace user who does not have that personal `.claude/knowledge/` directory.

The file is referenced internally by:

- `plugins/scientific-method/skills/scientific-thinking/SKILL.md` line 18: `[Investigation Workflow](../../shared/investigation-workflow.md)`
- `plugins/scientific-method/skills/scientific-thinking/references/shared-references.md` line 15: `[Investigation Workflow](../../../shared/investigation-workflow.md)`
- `plugins/scientific-method/README.md` line 111 (table row, no click-through concern)

The file is referenced externally (from outside the plugin) by:

- `.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md` line 366 — points INTO the plugin
- `.claude/knowledge/workflow-diagrams/simple-task-workflow.md` line 300 — points INTO the plugin
- `.claude/knowledge/workflow-diagrams/investigation-workflow.md` line 5 — redirect stub pointing INTO the plugin
- `.claude/knowledge/workflow-diagrams/README.md` lines 15 and 146 — points INTO the plugin

These external references point TO `investigation-workflow.md` — they are not affected by removing the Navigation section FROM `investigation-workflow.md`. The Navigation section points back out to those files; removing the outbound links from the plugin does not break any inbound links.

**Critical: the removal target is lines 388–393 (the `---` separator plus the `## Navigation` section). After removal, the file's last content line will be line 386: `- **Verification** → Conclusion (confirm findings)`.**

### How This Currently Works: retrospective-analyst.md

`plugins/scientific-method/agents/retrospective-analyst.md` has this exact frontmatter (lines 1–4):

```yaml
---
name: retrospective-analyst
description: Spawned after an investigation reaches resolved-verified status — analyzes the iteration log to produce a mermaid investigation timeline, result analysis (what worked, what did not, pattern observations), and a retrospective with lessons learned and rubric update recommendations. Use when an investigation is complete and the user wants structured analysis and visualization.
---
```

The agent body (lines 6–111) describes reading investigation inputs and writing three output files to `.claude/retrospectives/`: a timeline, a result analysis, and a retrospective. The `Read` tool is used to read the investigation input; the `Write` tool is used to produce all three output files. No other tools are used by the agent's described procedure.

The `tools` field is absent from the frontmatter. The fix inserts `tools: [Read, Write]` on the line immediately after `description:`. The field order after the fix must be: `name`, `description`, `tools`.

The agent is registered in `plugins/scientific-method/.claude-plugin/plugin.json` under the `agents` array as `"./agents/retrospective-analyst.md"`. The plugin validator `FrontmatterValidator` checks agent frontmatter — adding the `tools` field is a known-valid schema addition (confirmed in official docs).

### How This Currently Works: experiment-protocol/SKILL.md

`plugins/scientific-method/skills/experiment-protocol/SKILL.md` is 233 lines. It has YAML frontmatter (lines 1–5) with fields `name`, `description`, and `user-invocable: true`.

Two `<eg>...</eg>` wrapper blocks exist in the file:

**Block 1** (lines 87–113): Wraps two example fixtures — a correct fixture (neutral input only) and a wrong fixture (criteria embedded). The block opens with `<eg>` on line 87 (preceded by a blank line after the Step 2 instruction paragraph) and closes with `</eg>` on line 113 (followed by a blank line before Step 3). The content between the tags — two bold headings (`**Correct fixture — neutral input only:**` and `**Wrong fixture — criteria embedded:**`) plus their markdown code fences — is preserved intact. Only the `<eg>` and `</eg>` tag lines are removed.

**Block 2** (lines 128–147): Wraps two rubric criterion examples. Opens with `<eg>` on line 128 (after the rubric criterion format block) and closes with `</eg>` on line 147 (before the Step 4 section). Content preserved intact.

No existing `## Downstream Integration` section is present in the file. The file ends at line 233 with a verification checklist. The `## Downstream Integration` section must be inserted after the last workflow step section and before the verification checklist at the end, or appended after the checklist. The design spec places it "after the main workflow steps and before any closing section" — the final `## Verification Before Declaring Complete` section (line 222) is the closing section, so the new section goes between `## Anti-Patterns` content and `## Verification Before Declaring Complete`.

The `retrospective-analyst` agent is not mentioned anywhere in `experiment-protocol/SKILL.md` currently. The iteration log format is documented in Step 6 of the skill (lines 168–190). The skill produces an iteration log file at `.claude/agents/tests/{experiment-name}-log.md` or `.claude/skills/tests/{experiment-name}-log.md`.

### External Dependency Check

Searching all `**/*.md` files in `plugins/` for `scientific-method` references (excluding the plugin itself) found two files:

- `plugins/plugin-creator/skills/claude-skills-overview-2026/SKILL.md` line 149: references `/scientific-method:scientific-thinking` skill by activation syntax
- `plugins/plugin-creator/skills/skill-creator/SKILL.md` line 114: references `/scientific-method:scientific-thinking` skill by activation syntax

Both are read-only activation syntax references (`/scientific-method:scientific-thinking`) — they do not reference specific files within the plugin. None of the 4 target files (`investigation-workflow.md`, `retrospective-analyst.md`, `README.md`, `experiment-protocol/SKILL.md`) are referenced by path from any other plugin. The refactoring changes are fully contained within `plugins/scientific-method/`.

The `.claude/knowledge/workflow-diagrams/` files (`rag-retrieval-pattern.md`, `simple-task-workflow.md`, `README.md`) link TO `investigation-workflow.md` — those links are inbound and are unaffected by removing the Navigation section inside the plugin file.

### Technical Reference Details

#### File Locations and Exact Edit Targets

- `plugins/scientific-method/shared/investigation-workflow.md` — 394 lines total; remove lines 388–393 (the `---` separator and `## Navigation` section with its 3 links)
- `plugins/scientific-method/agents/retrospective-analyst.md` — 111 lines total; insert `tools: [Read, Write]` after line 3 (the `description:` field line)
- `plugins/scientific-method/README.md` — 171 lines total; line 5 contains `**Version**: 1.1.0` — change to `1.2.0`
- `plugins/scientific-method/skills/experiment-protocol/SKILL.md` — 233 lines total; remove `<eg>` tag on line 87 and `</eg>` tag on line 113; remove `<eg>` tag on line 128 and `</eg>` tag on line 147; add `## Downstream Integration` section before `## Verification Before Declaring Complete`

#### Exact Strings for Edit Operations

**Task 1 — investigation-workflow.md removal target** (exact string to match):

```markdown
---

## Navigation

- **Previous:** [Simple Task Workflow](../../../.claude/knowledge/workflow-diagrams/simple-task-workflow.md)
- **Next:** [RAG Retrieval Pattern](../../../.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md)
- **Back to:** [Index](../../../.claude/knowledge/workflow-diagrams/README.md)
```

Replace with empty string (delete entirely, including the trailing newline so the file ends on the preceding content line).

**Task 2 — retrospective-analyst.md frontmatter insertion** (exact old string):

```yaml
---
name: retrospective-analyst
description: Spawned after an investigation reaches resolved-verified status — analyzes the iteration log to produce a mermaid investigation timeline, result analysis (what worked, what did not, pattern observations), and a retrospective with lessons learned and rubric update recommendations. Use when an investigation is complete and the user wants structured analysis and visualization.
---
```

Replace with:

```yaml
---
name: retrospective-analyst
description: Spawned after an investigation reaches resolved-verified status — analyzes the iteration log to produce a mermaid investigation timeline, result analysis (what worked, what did not, pattern observations), and a retrospective with lessons learned and rubric update recommendations. Use when an investigation is complete and the user wants structured analysis and visualization.
tools: [Read, Write]
---
```

**Task 3 — README.md version string** (exact old string):

```text
**Version**: 1.1.0 | **Author**: [Jamie Nelson](https://github.com/bitflight-devops)
```

Replace with:

```text
**Version**: 1.2.0 | **Author**: [Jamie Nelson](https://github.com/bitflight-devops)
```

**Task 4 — experiment-protocol/SKILL.md, Block 1 removal** — the `<eg>` tag on its own line between the Step 2 instruction and the `**Correct fixture` heading; the `</eg>` tag on its own line after the wrong fixture code fence.

**Task 4 — experiment-protocol/SKILL.md, Block 2 removal** — the `<eg>` tag on its own line before `## Criterion 1`; the `</eg>` tag on its own line after the Criterion 2 code fence.

**Task 4 — Downstream Integration section insertion** — insert before `## Verification Before Declaring Complete` (the section starting at line 222):

```markdown
## Downstream Integration

The iteration log produced by this skill is the primary input to the `retrospective-analyst`
agent. When an investigation reaches `status: resolved-verified`, the `SubagentStop` hook
notifies the user to invoke `retrospective-analyst`. That agent reads:

- The complete investigation output (all 14 sections of the Unified Investigation Template)
- The iteration log written during experiment-protocol sessions

This produces three structured artefacts in `.claude/retrospectives/`: an investigation timeline,
a result analysis, and a retrospective with lessons learned.
```

#### Version Authority

- Canonical version: `plugins/scientific-method/.claude-plugin/plugin.json` field `"version": "1.2.0"`
- README target: line 5, change `1.1.0` to `1.2.0`

#### Plugin Validator Location

```text
uv run plugins/plugin-creator/scripts/plugin_validator.py plugins/scientific-method --verbose
```

#### Linting Command

```bash
uv run prek run --files <file>
```

Applied per-file after each edit. All four modified files must pass with exit code 0.

#### Parallelization Constraint

Fix 4 and Fix 5 from the design spec are combined into Task 4 in the task file — both target `experiment-protocol/SKILL.md`. A single agent handles both the `<eg>` tag removal and the `## Downstream Integration` insertion in one edit pass to avoid concurrent write conflicts.

Tasks 1, 2, 3, and 4 target four different files with no shared write state and can execute concurrently.

---

## Dependency Summary

### Group A — Independent (run in parallel)

Tasks 1, 2, 3, and 4 all target different files and share no state. All four can execute concurrently.

```text
Task 1: investigation-workflow.md  — STRUCTURE_FIX
Task 2: retrospective-analyst.md   — AGENT_OPTIMIZE
Task 3: README.md                  — DOC_IMPROVE (version sync)
Task 4: experiment-protocol/SKILL.md — DOC_IMPROVE (markup + integration note)
```

### Group B — Sequential (run after Group A completes)

```text
Task V1: plugin validator gate (requires Tasks 1, 2, 3, 4 all COMPLETE)
Task V2: documentation review (requires V1 COMPLETE)
```

---

## Success Metrics

- **Quantitative target**: Score >= 82/100 (no regression; targeted improvement to 87-90/100)
- **InternalLinkValidator**: 0 broken cross-repo links
- **FrontmatterValidator**: retrospective-analyst.md passes with `tools` field present
- **Markdown linting**: All modified files pass `uv run prek run --files`
- **Version consistency**: README.md and plugin.json agree on `1.2.0`
- **Markup cleanliness**: 0 `<eg>`/`</eg>` tags remain in experiment-protocol/SKILL.md
- **Integration coverage**: retrospective-analyst referenced in experiment-protocol/SKILL.md downstream section
