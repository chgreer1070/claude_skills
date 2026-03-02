---
name: Research Resources
description: ''
metadata:
  topic: research-resources
  source: Not specified
  added: '2026-02-23'
  priority: Ideas
  type: Feature
  status: open
  issue: '#264'
---

## Story

As a **developer using Claude Code skills**, I want to **research resources** so that **the tooling becomes more capable and complete**.

## Description

**Skill for research phase**: `/research-and-compare <methodology-name-or-url>` (moved to [stateless-agent-methodology](https://github.com/bitflight-devops/stateless-agent-methodology) repo)

- Produces structured comparison documents following SAM comparison template
- Includes overlap/divergence analysis, weakness discovery, implementation pairing
- Outputs to [`stateless-agent-methodology/.meta/v1_comparisons/`](https://github.com/bitflight-devops/stateless-agent-methodology/tree/main/.meta/v1_comparisons)

**Existing SAM comparisons** (start here before running new research):

- [SAM v1 comparisons](https://github.com/bitflight-devops/stateless-agent-methodology/tree/main/.meta/v1_comparisons)
  - sam-vs-get-shit-done.md
  - sam-vs-bmad-method.md
  - sam-vs-gastown.md
  - sam-vs-taskmaster.md
  - sam-vs-octocode.md
  - sam-vs-superclaude.md
  - sam-vs-ralph-loop-orchestrator.md
  - sam-vs-cc-sessions.md
  - sam-vs-v-model.md
  - sam-infrastructure-layer.md

**Workflow for SAM gap items**:

1. Check existing comparisons for relevant findings
2. If more research needed: `/research-and-compare <framework>` (in stateless-agent-methodology repo) for specific topics
3. Synthesize findings into SAM framework update
4. Mark backlog item complete

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Not specified
- **Priority**: Ideas
- **Added**: 2026-02-23
- **Research questions**: None