---
name: Circuit breaker hook for agent failure loops
description: 'Add a PostToolUseFailure hook that tracks consecutive tool failures. After 3 failures: inject try a different approach guidance. After 5 lifetime trips: escalate to stop and rethink. Catches agent failure loops that our blocker reporting misses. Pattern sourced from Citadel circuit-breaker.js.'
metadata:
  topic: circuit-breaker-hook-for-agent-failure-loops
  source: Citadel assessment .claude/reports/citadel-assessment-20260320.md
  added: '2026-03-21'
  priority: P1
  type: Feature
  status: open
  issue: '#929'
  last_synced: '2026-03-21T01:07:11Z'
---