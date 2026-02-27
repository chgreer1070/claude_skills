---
name: 'backlog.py: plan field N/A blocks work-backlog-item Step 2'
description: "When per-item files have plan: N/A (set on completed items), work-backlog-item Step 2 treats it as a valid plan path and stops with 'This item already has a plan at N/A'. Currently all 22 items with plan: N/A are status: done so they're filtered out, but this is a latent bug. Fix: either strip N/A values during parsing in backlog.py, or add a guard in Step 2 to ignore non-path plan values."
metadata:
  topic: backlogpy-plan-field-na-blocks-work-backlog-item-step-2
  source: Workflow validation session 2026-02-27
  added: '2026-02-27'
  priority: P2
  type: Bug
  status: open
  issue: '#285'
---