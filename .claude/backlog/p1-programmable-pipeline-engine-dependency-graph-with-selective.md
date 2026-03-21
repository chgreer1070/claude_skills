---
name: Programmable pipeline engine — dependency graph with selective step injection
description: 'Convert the static workflow architecture diagram (.claude/docs/workflow-architecture-diagram.md from Issue #933) into a programmable pipeline engine. The pipeline should be: (1) a queryable dependency graph with typed edges between nodes, (2) a workflow analysis tool for reasoning about bottlenecks, missing edges, and redundant steps, (3) capable of selective step injection — depending on project type (Python CLI, FastAPI, TypeScript) and required validation harnesses, different steps get injected into the pipeline, (4) able to select validation harnesses that verify design intent was achieved for a specific project when executing plans. This builds on the SDLC layers concept (.claude/docs/sdlc-layers/) where Layer 1 is language and Layer 2 is stack profile. The pipeline engine would be Layer 0 — the execution infrastructure that composes Layer 1+2 steps into a project-specific pipeline.'
metadata:
  topic: programmable-pipeline-engine-dependency-graph-with-selective
  source: 'User vision statement during #933 implementation — pipeline is infrastructure, not documentation'
  added: '2026-03-21'
  priority: P1
  type: Feature
  status: needs-grooming
  issue: '#962'
  last_synced: '2026-03-21T15:59:55Z'
---

## Story

As a **developer using Claude Code skills**, I want to **programmable pipeline engine — dependency graph with selective step injection** so that **the tooling becomes more capable and complete**.

## Description

Convert the static workflow architecture diagram (.claude/docs/workflow-architecture-diagram.md from Issue #933) into a programmable pipeline engine. The pipeline should be: (1) a queryable dependency graph with typed edges between nodes, (2) a workflow analysis tool for reasoning about bottlenecks, missing edges, and redundant steps, (3) capable of selective step injection — depending on project type (Python CLI, FastAPI, TypeScript) and required validation harnesses, different steps get injected into the pipeline, (4) able to select validation harnesses that verify design intent was achieved for a specific project when executing plans. This builds on the SDLC layers concept (.claude/docs/sdlc-layers/) where Layer 1 is language and Layer 2 is stack profile. The pipeline engine would be Layer 0 — the execution infrastructure that composes Layer 1+2 steps into a project-specific pipeline.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User vision statement during #933 implementation — pipeline is infrastructure, not documentation
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None
