---
name: Create a broad simplify skill that reviews all changed file types, not just code
description: 'The built-in /simplify skill only reviews source code (redundant state, copy-paste, N+1 queries, JSX nesting). It skips markdown, YAML, skill files, agent definitions, and plan artifacts. Sessions that produce only planning artifacts, documentation, or skill edits get no quality review. A custom /simplify-all (or replacement) skill should also check for: duplicate content across markdown files, stale cross-references and broken links, inconsistent formatting, invalid documentation claims, redundant instructions across skills/agents, and plan artifact quality (missing sections, incomplete acceptance criteria).'
metadata:
  topic: create-a-broad-simplify-skill-that-reviews-all-changed-file-
  source: 'GitHub Issue #977'
  added: '2026-03-22'
  priority: P2
  type: Feature
  status: needs-grooming
  issue: '#977'
  last_synced: '2026-03-22T15:08:46Z'
---

## Story

As a **developer using Claude Code skills**, I want to **create a broad simplify skill that reviews all changed file types, not just code** so that **the tooling becomes more capable and complete**.

## Description

The built-in /simplify skill only reviews source code (redundant state, copy-paste, N+1 queries, JSX nesting). It skips markdown, YAML, skill files, agent definitions, and plan artifacts. Sessions that produce only planning artifacts, documentation, or skill edits get no quality review. A custom /simplify-all (or replacement) skill should also check for: duplicate content across markdown files, stale cross-references and broken links, inconsistent formatting, invalid documentation claims, redundant instructions across skills/agents, and plan artifact quality (missing sections, incomplete acceptance criteria).

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session observation 2026-03-21 — /simplify ran on a planning-only session and found nothing to review
- **Priority**: P2
- **Added**: 2026-03-22
- **Research questions**: None