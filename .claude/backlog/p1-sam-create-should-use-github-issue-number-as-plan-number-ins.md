---
name: sam create should use GitHub issue number as plan number instead of sequential assignment
description: 'sam create assigns plan numbers sequentially (P1, P2, ..., P699) but the issue number should BE the plan number. This was demonstrated when P698 collided — the gates timeout fix was issue #951 but got plan P698, which resolved to a completely different plan. If the plan number matched the issue number (P951), addressing would be unambiguous and the issue-to-plan relationship would be self-evident. sam create should accept --issue N and use that as the plan number.'
metadata:
  topic: sam-create-should-use-github-issue-number-as-plan-number-ins
  source: 'User vision statement 2026-03-21 — divergence #4 from canonical issue lifecycle, observed collision in this session'
  added: '2026-03-21'
  priority: completed
  type: Bug
  status: done
  issue: '#966'
  last_synced: '2026-03-21T16:17:29Z'
  groomed: '2026-03-21'
---

## Story

As a **developer relying on this plugin**, I want to **sam create should use github issue number as plan number instead of sequential assignment** so that **the tool works correctly and reliably**.

## Description

sam create assigns plan numbers sequentially (P1, P2, ..., P699) but the issue number should BE the plan number. This was demonstrated when P698 collided — the gates timeout fix was issue #951 but got plan P698, which resolved to a completely different plan. If the plan number matched the issue number (P951), addressing would be unambiguous and the issue-to-plan relationship would be self-evident. sam create should accept --issue N and use that as the plan number.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: User vision statement 2026-03-21 — divergence #4 from canonical issue lifecycle, observed collision in this session
- **Priority**: P1
- **Added**: 2026-03-21
- **Research questions**: None

## Groomed (2026-03-21)

### Progress

<div><sub>2026-03-21T16:17:29Z</sub>

2026-03-21: Fixed. sam create now uses --issue N as the plan number (P{N}-{slug}.yaml). Collision guard raises error if P{N} already exists. Sequential fallback preserved when --issue is omitted. 735 tests pass including 7 new tests.
</div>