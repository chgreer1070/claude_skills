---
task: T6
title: Update TASK_FILE_FORMAT.md — add divergence-notes optional field
status: complete
started: 2026-03-02T12:00:00Z
completed: 2026-03-02T00:00:00Z
agent: general-purpose
dependencies: []
priority: 1
complexity: low
accuracy-risk: low
parallelize-with: [T1]
reason: T6 and T1 write to different files with no overlap
handoff: >
  Report: line numbers of each addition in TASK_FILE_FORMAT.md, confirmation that
  divergence-notes appears in both the Optional Fields table and JSON schema,
  backward-compatibility validation result.
---

## Context

This task was planned as a standalone update. `TASK_FILE_FORMAT.md` is the schema
document that defines valid YAML frontmatter fields for task files. The `divergence-notes`
field needs to be added as an optional field so it is recognized as part of the schema,
enabling the `context-refinement` agent to quickly identify tasks that recorded divergences.

T6 has no dependencies — the schema change is self-contained and does not reference the
policy document.

Architecture spec source: [plan/architect-plan-artifact-lifecycle.md](../architect-plan-artifact-lifecycle.md),
section "Task File Format Extension".

## Objective

Add `divergence-notes` as an optional integer field to the Optional Fields table and the
JSON Schema `properties` block in `.claude/docs/TASK_FILE_FORMAT.md`.

## Required Inputs

- [.claude/docs/TASK_FILE_FORMAT.md](../../.claude/docs/TASK_FILE_FORMAT.md) — file to modify;
  read before editing

## Requirements

1. Add `divergence-notes` row to Optional Fields table (type: integer, description:
   "Count of divergence notes recorded during implementation", example: 2)
2. Add `divergence-notes` property to JSON Schema (type: integer, minimum: 0, default: 0)
3. Add commented `divergence-notes: 0` line to template section

## Constraints

- Read the file fully before editing to understand current structure
- Do not modify any existing field definitions
- The JSON schema addition must maintain valid JSON syntax
- Do not add `divergence-notes` to the Required Fields table

## Expected Outputs

- File modified: `.claude/docs/TASK_FILE_FORMAT.md`

## Acceptance Criteria

1. `divergence-notes` appears in the Optional Fields table with type `integer`
2. `divergence-notes` appears in the JSON schema with `"type": "integer"`, `"minimum": 0`, `"default": 0`
3. The template block contains a commented `divergence-notes` line
4. Backward-compatibility: `uv run implementation_manager.py validate . plugin-linter` exits 0
5. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0
