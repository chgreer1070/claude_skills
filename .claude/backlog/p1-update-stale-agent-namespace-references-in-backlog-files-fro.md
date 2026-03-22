---
name: Update stale agent namespace references in backlog files from python3-development to dh
description: 'Five backlog files contain routing references to agents that were moved from python3-development to development-harness as part of deduplicate-agents-phase4 (e.g., @python3-development:swarm-task-planner, context-gathering, codebase-analyzer, feature-verifier). Any agent acting on these items will attempt to invoke nonexistent agents. References should be updated to use @dh: namespace.'
metadata:
  topic: update-stale-agent-namespace-references-in-backlog-files-fro
  source: 'GitHub Issue #937'
  added: '2026-03-22'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#937'
  last_synced: '2026-03-22T15:08:54Z'
---

## Story

As a **developer using Claude Code skills**, I want to **update stale agent namespace references in backlog files from python3-development to dh** so that **the tooling becomes more capable and complete**.

## Description

Five backlog files contain routing references to agents that were moved from python3-development to development-harness as part of deduplicate-agents-phase4 (e.g., @python3-development:swarm-task-planner, context-gathering, codebase-analyzer, feature-verifier). Any agent acting on these items will attempt to invoke nonexistent agents. References should be updated to use @dh: namespace.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Agent task — auto-derived from deduplicate-agents-phase4 session context
- **Priority**: P1
- **Added**: 2026-03-20
- **Research questions**: None