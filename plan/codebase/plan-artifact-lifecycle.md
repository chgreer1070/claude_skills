# Plan Artifact Lifecycle

**Analysis Date:** 2026-03-02
**Repository:** claude_skills

---

## Artifact Types and Structures

### 1. Feature Context (`plan/feature-context-{slug}.md`)

**Created by:** `feature-researcher` agent (Phase 1 of `/add-new-feature`)

**Observed files:**

- `plan/feature-context-plugin-linter.md` — 481 lines
- `plan/feature-context-sam-task-skills-context.md` — (60+ lines sampled)
- `plan/feature-context-process-quality-discipline.md` — (50+ lines sampled)
- `plan/feature-context-validate-orchestrator-discipline.md` — (40+ lines sampled)

**Structure (from `feature-context-plugin-linter.md`):**

```markdown
## Document Metadata
- Generated: {date}
- Input Type: {complex_requirement_document|simple_description|existing_document}
- Source: {description}
- Status: DISCOVERY_COMPLETE

## Original Request
## Core Intent Analysis
  ### WHO (Target Users)
  ### WHAT (Desired Outcome)
  ### WHEN (Trigger Conditions)
  ### WHY (Problem Being Solved)
## Codebase Research
  ### Similar Patterns Found
  ### Existing Infrastructure
  ### Code References
## Use Scenarios
## Gap Analysis
## Questions Requiring Resolution
## Goals (Pending Resolution)
## Next Steps
## Risk Assessment
## Technical Complexity Assessment
## Dependencies on External Systems
## Backward Compatibility Concerns
## Related Work
## Success Criteria
## Open Research Questions
```

**Lifecycle:** Write-once at planning time. No update mechanism exists. The `context-refinement` agent (`plugins/python3-development/agents/context-refinement.md`) appends only to the task file's Context Manifest — it does not update the feature-context file.

**Freshness indicator:** `Generated:` date in metadata block. No version field. No mechanism to check or enforce freshness.

---

### 2. Architecture Spec (`plan/architect-{slug}.md`)

**Created by:** `python-cli-design-spec` agent (Phase 3 of `/add-new-feature`)

**Observed files:**

- `plan/architect-plugin-linter.md` — (80+ lines sampled, substantially longer)
- `plan/architect-sam-task-skills-context.md` — referenced but not read
- `plan/architect-process-quality-discipline.md` — referenced by task files

**Structure (from `architect-plugin-linter.md`):**

```markdown
## Executive Summary
## Document Purpose and Boundaries
  **This document specifies:** (interfaces, contracts, schemas, validators, data flow)
  **This document does NOT specify:** (implementation code, test code, CLI implementations)
## Architecture Overview
  ### System Context (C4 Mermaid diagram)
  ### Container Diagram (C4 Mermaid diagram)
## Technology Stack
## [Feature-specific sections: models, validators, error codes, etc.]
## Testing Strategy
## Performance Requirements
## Configuration Requirements
## File Locations
## References
```

**Lifecycle:** Write-once at planning time. The `context-refinement` agent (`plugins/python3-development/agents/context-refinement.md:121`) may recommend architecture spec updates in its `RECOMMENDED DOCUMENTATION UPDATES` output block, but it does not modify the file directly. It notes: "Should architecture.md be updated to reflect this? (Note it for the orchestrator)". The orchestrator must act on this recommendation manually.

**Referenced by:** Task file Context Manifests link to architect specs (e.g., `plan/tasks-15-fix-multi-yaml-fence/T1.md:285` references `plan/architect-fix-multi-yaml-fence.md`). The `feature-verifier` agent (`plugins/python3-development/agents/feature-verifier.md:56`) reads the architecture spec from `plan/architect-{slug}.md` during verification.

**Freshness indicator:** None. No `last_updated` field, no version. No mechanism prevents architecture spec from diverging from implementation after tasks complete.

---

### 3. Task Plan

**Two formats exist simultaneously:**

**Format A — Single monolithic file (`plan/tasks-{N}-{slug}.md`):**

```markdown
## Task 1.1: Title

**Status**: NOT STARTED | IN PROGRESS | COMPLETE | BLOCKED
**Dependencies**: Task N.N | None
**Priority**: 1-5
**Complexity**: Low | Medium | High
**Agent**: agent-name
**Skills**: skill1, skill2  (comma-separated list)
**Started**: {ISO timestamp}
**Completed**: {ISO timestamp}
**LastActivity**: {ISO timestamp}

[Free-text body: Context, Objective, Requirements, Constraints, ...]
```

Examples: `plan/tasks-13-sam-task-skills-context.md`, `plan/tasks-10-validate-agent-browser.md`

**Format B — YAML frontmatter per-task file in directory (`plan/tasks-{slug}/` or `plan/tasks-{N}-{slug}/`):**

```yaml
---
task: T1
title: "Title"
status: not-started | in-progress | complete | blocked
agent: agent-name
dependencies: []
priority: 1
complexity: medium
accuracy-risk: low | medium | high   # Non-standard field accepted by parser
parallelize-with: [T3, T5]
reason: "..."
handoff: "..."
skills:
  - python3-development
started: 2026-03-02T00:00:00Z
completed: 2026-03-02T00:05:00Z
---

## Context Manifest
...

## Context
...
```

Examples: `plan/tasks-1-plugin-linter/` (25 files), `plan/tasks-15-process-quality-discipline/` (7 files), `plan/tasks-15-fix-multi-yaml-fence/` (6 files)

**Migration state:** Per `TASK_FILE_FORMAT.md:454-479`, Phase 4 (Adoption) is "in progress". `plan/tasks-1-plugin-linter.md.pre-migration-backup` confirms the original monolithic file was migrated to the directory format.

---

### 4. Context Manifest (embedded in task file)

**Created by:** `context-gathering` agent (Phase 6 of `/add-new-feature`)

**Location:** Inserted as a `## Context Manifest` section inside the task file (not a separate file).

**Structure (from `plan/tasks-15-fix-multi-yaml-fence/T1.md:10-273`):**

```markdown
## Context Manifest

_Generated by context-gathering agent on YYYY-MM-DD_

### How This Currently Works: [Description]

[Narrative paragraphs with code paths, function references, architectural decisions]

### Key Architecture Decisions

[Decision rationale blocks, Q&A format]

### Task Dependencies and Execution Order

[ASCII dependency graph with SYNC CHECKPOINTs]

### Files Each Task Reads and Modifies

[Per-task file lists with line ranges]

### Technical Reference Details

[Code signatures, exact function bodies, data structures]

### Pre-Existing Issues Noted (not in scope)

[Numbered list of known issues excluded from this work]
```

**Update mechanism:** `context-refinement` agent appends a `### Discovered During Implementation` subsection to the existing Context Manifest. It does NOT replace or edit the original content — only appends. Format from `plugins/python3-development/agents/context-refinement.md:56-85`:

```markdown
### Discovered During Implementation

_Session Date: YYYY-MM-DD_

[NARRATIVE explanation]

**Key Discoveries:**
1. **[Name]**: [Explanation]

#### Updated Technical Details
- [new signatures, endpoints, patterns]

#### Gotchas for Future Developers
- [specific pitfalls]
```

---

### 5. Codebase Analysis (`plan/codebase/{FOCUS}.md`)

**Created by:** `codebase-analyzer` agent (Phase 2, optional)

**Observed files in `plan/codebase/`:**

- `TESTING.md`
- `cross-references-backlog.md`
- `orchestrator-discipline-patterns.md`
- `plugin-mcp-patterns.md`
- `plugin-validator-architecture.md`
- `sam-pipeline-quality.md`
- `task-file-parser.md`
- (this file: `plan-artifact-lifecycle.md`)

**Lifecycle:** Write-once. No update mechanism. Referenced by task Context Manifests (e.g., `plan/tasks-15-fix-multi-yaml-fence/T1.md:286` references `plan/codebase/task-file-parser.md`). Multiple features can reference the same codebase analysis file from different feature cycles; the file is not updated between them.

---

### 6. Taxonomy Validation File (`plan/taxonomy-validation-{slug}.md`)

**Observed:** `plan/taxonomy-validation-process-quality-discipline.md`

**This is a non-standard artifact type** — exists for exactly one feature (process-quality-discipline). Not part of the documented workflow in `local-workflow.md`. No agent creates it systematically.

---

## Creation Patterns

### Which Agent Creates Each Artifact

| Artifact | Creating Agent | Phase | Skill |
|----------|---------------|-------|-------|
| `feature-context-{slug}.md` | `feature-researcher` | 1 | `/add-new-feature` |
| `plan/codebase/{FOCUS}.md` | `codebase-analyzer` | 2 (optional) | `/add-new-feature` |
| `architect-{slug}.md` | `python-cli-design-spec` | 3 | `/add-new-feature` |
| `tasks-{N}-{slug}.md` | `swarm-task-planner` | 4 | `/add-new-feature` |
| Context Manifest (in task file) | `context-gathering` | 6 | `/add-new-feature` |
| `tasks-{slug}/T*.md` (directory) | `swarm-task-planner` | 4 | `/add-new-feature` (newer) |

The `plan-validator` agent (Phase 5) does NOT create a file — it returns READY or BLOCKED and the workflow halts or proceeds. Its output exists only in the agent's return value, not as a durable artifact.

---

## Update Patterns

### Which Artifacts Are Ever Updated

**Task files — actively updated during execution:**

- `**Status**` field: Updated by `/start-task` skill (to IN PROGRESS / `in-progress`) and by `task_status_hook.py` SubagentStop event (to COMPLETE / `complete`).
- `**Started**` timestamp: Written by `/start-task` skill (`local-workflow.md:200-205`).
- `**Completed**` timestamp: Written by `task_status_hook.py` on SubagentStop (`local-workflow.md:200-205`).
- `**LastActivity**` timestamp: Written by `task_status_hook.py` on every Write/Edit/Bash PostToolUse event (`local-workflow.md:197`).
- Context Manifest: Appended (not replaced) by `context-refinement` agent at end of `/complete-implementation` Phase 6, if discoveries were made.

**All other artifacts — write-once:**

| Artifact | Written Once At | Never Updated |
|----------|----------------|---------------|
| `feature-context-{slug}.md` | Phase 1 | After creation |
| `plan/codebase/{FOCUS}.md` | Phase 2 | After creation |
| `architect-{slug}.md` | Phase 3 | After creation (see note) |
| Context Manifest initial section | Phase 6 | After initial write |

**Note on architect spec updates:** `context-refinement` recommends updates in its DONE response (`context-refinement.md:166-168`) but the agent is explicitly prohibited from modifying architecture.md directly. The recommendation surface is text output only, not a file write. No automated mechanism triggers an architect spec update.

---

## Lifecycle Markers

### Timestamps

Task files (legacy markdown format) use bold-field timestamps:

```text
**Started**: 2026-03-01T23:30:00Z
**Completed**: 2026-03-01T14:19:27Z
**LastActivity**: (written by hook)
```

Task files (YAML frontmatter format) use YAML timestamps per ISO 8601:

```yaml
created: 2026-02-02T15:00:00Z
started: 2026-02-02T15:15:00Z
completed: 2026-02-02T15:30:00Z
```

**Observed inconsistency:** In `plan/tasks-13-sam-task-skills-context.md:60-65`, Task 2.1 has `**Started**: 2026-03-01T23:30:00Z` and `**Completed**: 2026-03-01T14:19:27Z` — the Completed timestamp is earlier than Started. This is a real artifact in the repository showing that timestamp accuracy is not enforced.

### Versioning

No versioning exists for any plan artifact type. The only version-like field is `accuracy-risk` (low/medium/high) in newer YAML-format task files (observed in `plan/tasks-15-fix-multi-yaml-fence/T1.md:8`). This is not defined in the official schema (`TASK_FILE_FORMAT.md`) but is tolerated because `implementation_manager.py` ignores unknown YAML fields.

### Freshness Indicators

- Feature context files: `Generated:` date in Document Metadata section (string, not machine-parsed).
- Codebase analysis files: `**Analysis Date:**` in header (string, not machine-parsed).
- Context Manifest: `_Generated by context-gathering agent on YYYY-MM-DD_` (string, not machine-parsed).
- No automated stale detection. No mechanism prevents using a 6-month-old feature-context file.

---

## Human Touch Points

### Where Human Decisions Are Captured

**Phase 1 (feature-context):** Human-supplied intent is captured verbatim in `## Original Request` section. Unresolved questions are listed in `## Questions Requiring Resolution` with `Resolution: _pending_`. There is no mechanism to record when or how these questions were resolved — the answers do not flow back into the artifact.

**Phase 5 (plan-validator BLOCKED):** When the plan-validator returns BLOCKED, the workflow stops. The human must intervene. This decision point has no artifact — it exists only as a gating condition in `/add-new-feature:81` ("If it returns BLOCKED, do not proceed"). There is no document capturing what the human changed and why.

**Feature slug:** The human-chosen or workflow-generated slug becomes the permanent name for all artifacts. No mechanism links artifacts from the same feature together except the naming convention `{slug}`.

### How Human Decisions Are Referenced Later

- Architecture specs reference feature-context files by path: `./plan/feature-context-{slug}.md`
- Task files reference architect specs in their headers: `**Architecture Spec**: [architect-{slug}.md](./architect-{slug}.md)`
- Context Manifests reference architecture specs inline (e.g., `Architecture spec: plan/architect-process-quality-discipline.md, sections...`)
- The `feature-verifier` agent reads the architect spec at `plan/architect-{slug}.md` and task file to derive the feature goals it verifies against.

---

## Divergence Evidence

Comparison of stated design in plan artifacts against observable facts:

### Divergence 1: `skills:` Field in Task Schema

**Feature-context-sam-task-skills-context.md:18** states: "There is no `skills` field. The `TASK_FILE_FORMAT.md` JSON schema defines `task`, `title`, `status`, `agent`, `dependencies`, `priority`, `complexity`, timestamps, `blocked-by`, and `parallelize-with`."

**Current state of TASK_FILE_FORMAT.md** (read directly): The `skills` field IS now present in the JSON schema properties block, the Optional Fields table, the template, and the Field Mapping table. This was the feature that `tasks-13-sam-task-skills-context.md` was tracking, and it shows COMPLETE.

**Verdict:** Feature-context file accurately described the pre-implementation state. After implementation, the feature-context description diverged from reality. The feature-context file was not updated.

### Divergence 2: `accuracy-risk` Field in Task Files

**TASK_FILE_FORMAT.md** (the schema document) does not define `accuracy-risk` as a valid field in either the Optional Fields table or the JSON schema properties block.

**Observed in `plan/tasks-15-fix-multi-yaml-fence/T1.md:8`:** `accuracy-risk: medium`

**Observed in `plan/tasks-15-process-quality-discipline/T1-schema-foundation-task-file-format-md-and-backlog.md:11`:** `accuracy-risk: medium`

**Verdict:** Task files use a field not defined in the schema. This is tolerated because the parser ignores unknown fields, but it represents schema drift — the schema doc does not reflect all fields in active use.

### Divergence 3: `reason` and `handoff` Fields in Task Files

**TASK_FILE_FORMAT.md** does not define `reason` or `handoff` as valid YAML frontmatter fields.

**Observed in `plan/tasks-15-fix-multi-yaml-fence/T1.md:12-16`:**

```yaml
reason: T1, T3, T5 write to different files with no overlap
handoff: >
  Report: function signature confirmed, __all__ updated...
```

**Observed in `plan/tasks-15-process-quality-discipline/T1-schema-foundation-task-file-format-md-and-backlog.md:14-15`:**

```yaml
handoff: "Report: lines added to each file..."
```

**Verdict:** Multiple undocumented YAML fields are in active use across new task files. The `handoff` field appears in both the YAML frontmatter AND as a `## Handoff` markdown section in the same task file (T1.md:414), creating a duplication with different content.

### Divergence 4: `@python-cli-architect` Agent Reference in Task Files

**Observed in `plan/tasks-1-plugin-linter/1-filetype-enum-extension.md:6`:** `agent: "@python-cli-architect"`

**TASK_FILE_FORMAT.md:137:** `agent` field description is "Agent responsible for task", example: `"python-cli-architect"`.

**`plan-validator.md:145-156`** (Dimension 4, Agent Capability Match table): Uses agent names without `@` prefix.

**Verdict:** The `@` prefix convention used in some task files is not defined in the schema. The planner that generated `tasks-1-plugin-linter` used `@python-cli-architect` while newer task files omit it.

### Divergence 5: `issue-classification` and Related Fields

**Feature-context-process-quality-discipline.md** (the planning document) described these fields as not yet existing.

**Current state of TASK_FILE_FORMAT.md:** `issue-classification`, `scenario-target`, `analysis-method` are all present in the Optional Fields table and JSON schema (as seen in the full TASK_FILE_FORMAT.md read). The feature that added them (`tasks-15-process-quality-discipline`) shows `status: complete` on T1.

**Verdict:** Consistent with Divergence 1 pattern — feature-context files describe pre-implementation state, and after implementation they diverge from current reality. This is expected behavior given the write-once lifecycle, but it means feature-context files cannot be used as current-state documentation.

---

## complete-implementation Workflow: What It Checks

The six-phase quality gate (`/complete-implementation` SKILL.md) runs after all tasks are COMPLETE:

**Phase 1 — code-reviewer:** Reviews implemented changes. May create follow-up task files at `plan/tasks-{N}-{slug}-followup-{k}.md`. These new task files re-enter the full lifecycle as new plan artifacts.

**Phase 2 — feature-verifier:** Reads architecture spec (`plan/architect-{slug}.md`) and task file. Derives feature goals from architecture spec. Verifies actual codebase implementation against those goals using three-level checks (exists, substantive, wired). If `issue-classification` is present in task metadata, applies proportional verification (`feature-verifier.md:187-224`).

**Phase 3 — integration-checker:** Checks integration points.

**Phase 4 — doc-drift-auditor:** Compares documentation against implementation. Writes `DOCUMENTATION_DRIFT_AUDIT.md` to `.claude/reports/`. Does NOT check plan artifact freshness — it checks project documentation (`CLAUDE.md`, `architecture.md`, plan files) against source code, not whether plan artifacts are stale relative to each other.

**Phase 5 — service-docs-maintainer:** Updates documentation if Phase 4 found drift.

**Phase 6 — context-refinement:** The ONLY phase that updates a plan artifact. Appends `### Discovered During Implementation` to the task file's Context Manifest if significant discoveries were made. Decision criteria from `context-refinement.md:89-109`:

- YES: Undocumented module interactions, incorrect assumptions, missing config requirements, hidden dependencies, complex error cases, performance constraints, security requirements, shared utilities that should be reused, patterns that conflicted with architecture.md.
- NO: Minor typos, implied-but-not-explicit things, standard debugging, temporary workarounds, implementation choices, personal preferences.

**What complete-implementation does NOT check:**

- Whether feature-context files are stale.
- Whether architecture specs diverged from implementation.
- Whether codebase analysis files are outdated.
- Whether multiple features have modified the same files (cross-feature drift).
- Timestamps or freshness of plan artifacts.

---

## Summary: Lifecycle Phases per Artifact

| Artifact | Created | Updated During Execution | Updated Post-Execution | Deleted |
|----------|---------|--------------------------|------------------------|---------|
| `feature-context-{slug}.md` | Phase 1 | Never | Never | Never |
| `plan/codebase/{FOCUS}.md` | Phase 2 | Never | Never | Never |
| `architect-{slug}.md` | Phase 3 | Never | Recommended only, never automated | Never |
| `tasks-{N}-{slug}.md` (monolithic) | Phase 4 | Status, timestamps | Context Manifest append | Never |
| `tasks-{slug}/T*.md` (per-task) | Phase 4 | Status, timestamps | Context Manifest append | Never |
| `.claude/context/active-task-{sid}.json` | `/start-task` | LastActivity hook | Deleted by SubagentStop hook | Yes, on task complete |

---

_Lifecycle analysis: 2026-03-02_
