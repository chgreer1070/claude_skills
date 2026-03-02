---
name: 'plugin-creator: Remove dead code and triplicated regex'
description: Contains triplicated regex patterns (same regex defined 3 times), a dead `skipped` list that is populated but never read, an unused `sum()` call, and HK005 warning is incorrectly treated as an error in certain code paths. Also has a `noqa BLE001` suppression that should be addressed per CLAUDE.md linting policy.
metadata:
  topic: plugin-creator-remove-dead-code-and-triplicated-regex
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P2
  type: Feature
  status: open
  issue: '#102'
---

## Story

As a **developer using Claude Code skills**, I want to **plugin-creator: remove dead code and triplicated regex** so that **the tooling becomes more capable and complete**.

## Description

Contains triplicated regex patterns (same regex defined 3 times), a dead `skipped` list that is populated but never read, an unused `sum()` call, and HK005 warning is incorrectly treated as an error in certain code paths. Also has a `noqa BLE001` suppression that should be addressed per CLAUDE.md linting policy.

## Files

`plugins/plugin-creator/` (scripts and skill files)

## Context

- **Source**: Plugin code review session 2026-02-21
- **Priority**: P2
- **Added**: 2026-02-21
- **Research questions**: None