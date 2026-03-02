---
name: add-new-feature
argument-hint: <feature description or existing doc path>
user-invocable: true
description: "SAM-style feature initiation workflow: discovery -> codebase analysis -> architecture spec -> task decomposition -> validation -> context manifest. Use when a user asks to add a feature, plan a feature, or convert an idea into executable task files."
metadata:
  version: "1.0.0"
  last_updated: "2026-02-28"
  source: python3-development plugin (local adaptation)
---
# Add New Feature (SAM Workflow)

You MUST convert the user's request into **durable SAM artifacts** under the repo:

- `plan/feature-context-{slug}.md` (discovery)
- `plan/codebase/{FOCUS}.md` (optional, analysis)
- `plan/architect-{slug}.md` (architecture/design spec)
- `plan/tasks-{N}-{slug}.md` (executable task plan with Agents, deps, and verification)

<feature_request>
$ARGUMENTS
</feature_request>

---

## Orchestrator Discipline

You are an orchestrator. You coordinate work across specialized agents. Prefer delegating discovery and analysis.

---

## Phase 1: Discovery (feature-researcher)

**WHAT / WHY only.** The feature-researcher produces problem space and desired outcome — not implementation approach. Output describes what is wanted and why; it does not prescribe how to build it.

Delegate to `feature-researcher` to produce `plan/feature-context-{slug}.md` and questions for resolution.

---

## Phase 2: Codebase Analysis (codebase-analyzer)

**WHAT exists today only.** The codebase-analyzer maps existing patterns, conventions, and constraints — not proposed designs. Output describes what is there; it does not prescribe what to add or change.

If helpful, delegate to `codebase-analyzer` for one or more focus areas:

- patterns
- architecture
- testing
- conventions

Outputs go to `plan/codebase/`.

---

## Phase 3: Architecture Spec (python-cli-design-spec)

**HOW begins here.** This is the first phase where implementation approach, design decisions, and code structure are determined — informed by the discovery and analysis from Phases 1–2.

Delegate to `python-cli-design-spec` to write `plan/architect-{slug}.md` based on:

- the feature context doc
- codebase analysis docs (if created)
- existing repo constraints (`CLAUDE.md`, `pyproject.toml`, etc.)

---

## Phase 4: Task Decomposition (swarm-task-planner)

Delegate to `swarm-task-planner` to:

- create `plan/tasks-{N}-{slug}.md`
- ensure every task has:
  - **Status**, **Dependencies**, **Priority**, **Complexity**, **Agent**
  - Acceptance Criteria (3+)
  - Verification Steps (3+)

---

## Phase 5: Plan Validation Gate (plan-validator)

Delegate to `plan-validator`. If it returns `BLOCKED`, do not proceed.

---

## Phase 6: Context Manifest (context-gathering)

Delegate to `context-gathering` with the task file path. It must insert a `## Context Manifest` into the task file.

---

## Success Outcome

When all phases complete, provide the user:

- the feature slug
- the task file path
- next step: run the `implement-feature` skill with the slug or task file path
