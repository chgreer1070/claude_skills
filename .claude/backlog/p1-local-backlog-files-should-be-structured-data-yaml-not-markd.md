---
name: Local backlog files should be structured data (YAML) not markdown documents
description: Local backlog files (.claude/backlog/*.md) are currently markdown documents. They should be structured data (YAML or JSON) acting as a sync cache for GitHub Issues, not a document format. GitHub is canonical — local files are write caches that push upstream ASAP. The structured format would make parsing reliable, eliminate markdown formatting issues, and align with the principle that local structure mirrors issue structure.
metadata:
  topic: local-backlog-files-should-be-structured-data-yaml-not-markd
  source: 'User vision statement 2026-03-21 — divergence #2 from canonical issue lifecycle'
  added: '2026-03-21'
  priority: P1
  type: Refactor
  status: needs-grooming
  issue: '#964'
  last_synced: '2026-03-21T15:34:17Z'
---

## Story

As a **maintainer of the codebase**, I want to **local backlog files should be structured data (yaml) not markdown documents** so that **the code is cleaner and more maintainable**.

## Description

Local backlog files (.claude/backlog/*.md) are currently markdown documents. They should be structured data (YAML or JSON) acting as a sync cache for GitHub Issues, not a document format. GitHub is canonical — local files are write caches that push upstream ASAP. The structured format would make parsing reliable, eliminate markdown formatting issues, and align with the principle that local structure mirrors issue structure.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User vision statement 2026-03-21 — divergence #2 from canonical issue lifecycle
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None
