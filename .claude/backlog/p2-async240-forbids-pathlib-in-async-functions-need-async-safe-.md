---
name: ASYNC240 forbids pathlib in async functions — need async-safe pathlib pattern
description: "Ruff ASYNC240 forbids pathlib.Path methods (.exists(), .read_text(), .write_text()) inside async functions because they perform blocking I/O. This conflicts with the project convention of using pathlib exclusively (modern Python / shinysnake — no os.path). In async test code during #328, calling Path(...).exists() triggered ASYNC240. Workarounds used: backlog_dir.glob('pattern') for existence checks, reading files in sync fixtures. Options: (1) per-file ASYNC240 suppression for tests/, (2) adopt anyio.Path for async contexts, (3) document canonical async-safe pathlib pattern for the project."
metadata:
  topic: async240-forbids-pathlib-in-async-functions-need-async-safe-
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: needs-grooming
  issue: '#336'
  last_synced: '2026-03-03T03:53:38Z'
---

## Story

As a **developer relying on this plugin**, I want to **async240 forbids pathlib in async functions — need async-safe pathlib pattern** so that **the tool works correctly and reliably**.

## Description

Ruff ASYNC240 forbids pathlib.Path methods (.exists(), .read_text(), .write_text()) inside async functions because they perform blocking I/O. This conflicts with the project convention of using pathlib exclusively (modern Python / shinysnake — no os.path). In async test code during #328, calling Path(...).exists() triggered ASYNC240. Workarounds used: backlog_dir.glob('pattern') for existence checks, reading files in sync fixtures. Options: (1) per-file ASYNC240 suppression for tests/, (2) adopt anyio.Path for async contexts, (3) document canonical async-safe pathlib pattern for the project.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: session observation during #328 implementation
- **Priority**: P2
- **Added**: 2026-03-01
- **Research questions**: None
