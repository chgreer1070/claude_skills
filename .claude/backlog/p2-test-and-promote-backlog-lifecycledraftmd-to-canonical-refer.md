---
name: Test and promote backlog-lifecycle.draft.md to canonical reference
description: 'backlog-lifecycle.draft.md (675 lines) documents the full item lifecycle, data flow, and state transitions. Contains 15+ [VERIFY] annotations and a 7-item testing checklist. Needs: run the testing checklist against live script behavior, resolve all [VERIFY] annotations, then promote from .draft.md to canonical docs/ reference. Link from work-backlog-item and groom-backlog-item skills.'
metadata:
  topic: test-and-promote-backlog-lifecycledraftmd-to-canonical-refer
  source: Workflow validation session 2026-02-27
  added: '2026-02-27'
  priority: P2
  type: Documentation
  status: open
  issue: '#286'
  groomed: '2026-03-01'
  last_synced: '2026-03-01T00:54:47Z'
  plan: plan/tasks-11-backlog-lifecycle-promotion.md
---

## Story

As a **developer**, I want **backlog-lifecycle** so that **backlog items are tracked in GitHub**.

## Description

backlog-lifecycle.draft.md (675 lines) documents the full item lifecycle, data flow, and state transitions. Contains 15+ [VERIFY] annotations and a 7-item testing checklist. Needs: run the testing checklist against live script behavior, resolve all [VERIFY] annotations, then promote from .draft.md to canonical docs/ reference. Link from work-backlog-item and groom-backlog-item skills.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Workflow validation session 2026-02-27
- **Priority**: P2
- **Added**: 2026-02-27
- **Research questions**: None

## Fact-Check

Claims checked: 3 | VERIFIED: 3 | REFUTED: 0 | INCONCLUSIVE: 0. File exists at .claude/docs/backlog-lifecycle.draft.md (674 lines). Contains 17 [VERIFY] annotations (confirmed via grep). Section 7 contains testing checklist with 7 subsections and ~20 individual test items. All claims verified against codebase (2026-03-01).

## RT-ICA

Goal: Validate backlog-lifecycle.draft.md against live script behavior, resolve all [VERIFY] annotations, rename from .draft.md to .md, add two-way cross-references between all backlog process files and the workflow document.
Conditions: 7 AVAILABLE, 0 DERIVABLE, 0 MISSING.
1. Draft file exists | AVAILABLE
2. 17 [VERIFY] annotations need resolution | AVAILABLE
3. 20+ test checklist items need execution | AVAILABLE
4. backlog.py runnable with test suite | AVAILABLE
5. Domain registry exists (.claude/skills/backlog-tools-administrator/references/domain-registry.md) | AVAILABLE
6. project_workflow.draft.md exists for cross-referencing | AVAILABLE
7. User wants .draft removed from filename before linking | AVAILABLE
Decision: APPROVED | Missing: None

## Groomed (2026-03-01)

### Priority

8/10 — Validates core backlog infrastructure. RT-ICA APPROVED with no missing conditions. Testing checklist is concrete and executable. File rename is straightforward. Cross-reference scope is well-defined (31 files in domain registry). Blocks downstream backlog operations credibility until verified.

### Impact

- Blocks: Canonical reference for backlog-item-groomer agent, work-backlog-item skill, groom-backlog-item skill
- Bottleneck: 17 [VERIFY] annotations prevent docs from being promoted to canonical status

### Scope

- Run 7-item testing checklist against live backlog.py
- Resolve 17 [VERIFY] annotations via script execution
- Rename backlog-lifecycle.draft.md to backlog-lifecycle.md
- Add two-way cross-references between all backlog process files and the lifecycle doc

### Output / Evidence

- .claude/docs/backlog-lifecycle.md — canonical, all [VERIFY] resolved
- Cross-references in: work-backlog-item/SKILL.md, groom-backlog-item/SKILL.md, backlog-tools-administrator/references/domain-registry.md, project_workflow.draft.md

### Dependencies

- Depends on: None (self-contained)
- Blocks: Canonical lifecycle reference in agent prompts, project_workflow.draft.md promotion

### Skills

- /backlog, /work-backlog-item, /groom-backlog-item, /backlog-tools-administrator

### Agents

- @backlog-item-groomer

### Prior Work

- .claude/skills/backlog/references/state-machine.md
- .claude/skills/backlog/references/item-schema.md
- .claude/skills/backlog-tools-administrator/references/domain-registry.md
- .claude/docs/backlog-item-groomed-schema.md

### Files

- .claude/docs/backlog-lifecycle.draft.md (target: rename to backlog-lifecycle.md)
- .claude/skills/backlog/scripts/backlog.py (test target)
- .claude/project_workflow.draft.md (cross-reference target)

### Decision

APPROVED — All conditions available. Proceed with testing checklist, annotation resolution, file rename, and cross-reference updates.