---
name: 'SAM: Replace validate-task-file.sh with Python validator'
description: "The bash validator at `plugins/plugin-creator/scripts/validate-task-file.sh` validates a different schema (`tasks-refactor-*.md`) and doesn't understand YAML frontmatter. Replace with Python validator that uses the shared `task_format.py` module.\n**File**: `plugins/plugin-creator/scripts/validate-task-file.sh`"
metadata:
  topic: sam-replace-validate-task-filesh-with-python-validator
  source: Task format standardization plan (2026-02-13)
  added: '2026-02-13'
  priority: P2
  type: Feature
  status: open
  issue: '#106'
---

## Story

As a **developer using Claude Code skills**, I want to **sam: replace validate-task-file.sh with python validator** so that **the tooling becomes more capable and complete**.

## Description

The bash validator at `plugins/plugin-creator/scripts/validate-task-file.sh` validates a different schema (`tasks-refactor-*.md`) and doesn't understand YAML frontmatter. Replace with Python validator that uses the shared `task_format.py` module.
**File**: `plugins/plugin-creator/scripts/validate-task-file.sh`

## Context

- **Source**: Task format standardization plan (2026-02-13)
- **Priority**: P2
- **Added**: 2026-02-13
- **Research questions**: None