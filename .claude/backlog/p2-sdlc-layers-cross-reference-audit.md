---
name: 'SDLC layers: Cross-reference audit'
description: 'Verify all cross-references in SDLC layer docs resolve. Paths in layer-0, layer-1, layer-2, and ARL docs may point to files that moved or were renamed. Success: no broken links; all `[text](path)` resolve.'
metadata:
  topic: sdlc-layers-cross-reference-audit
  source: Session observation — SDLC layer implementation (2026-02-23)
  added: '2026-02-23'
  priority: P2
  type: Chore
  status: open
  issue: '#250'
---

## Story

As a **maintainer of the project infrastructure**, I want to **sdlc layers: cross-reference audit** so that **the project infrastructure stays healthy**.

## Description

Verify all cross-references in SDLC layer docs resolve. Paths in layer-0, layer-1, layer-2, and ARL docs may point to files that moved or were renamed. Success: no broken links; all `[text](path)` resolve.

## Suggested Location

`.claude/docs/sdlc-layers/` and `plugins/development-harness/docs/layer-2/`

## Context

- **Source**: Session observation — SDLC layer implementation (2026-02-23)
- **Priority**: P2
- **Added**: 2026-02-23
- **Research questions**: None