# Work Route — Example Sessions

## Issue-first planning (`#N`)

```text
> /work-backlog-item #131

Loading GitHub Issue #131...
  Title:     plugin-validator: UX and coverage gaps
  Labels:    priority:p1, status:needs-grooming
  Milestone: v1.1 — Quality Gates
  State:     open

Matched per-item file for additional context: ✓
No groomed content in item file. Running groom-backlog-item first...

[groomed content written to item file]

RT-ICA: APPROVED — all conditions available.
Setting status:in-progress on issue #131...
  ✓ status:needs-grooming → status:in-progress

Composing feature request...
Invoking /add-new-feature...

[SAM phases run]

Updated per-item file with Plan: plan/tasks-2-validator-ux-coverage.md

Next steps:
- To execute:      /implement-feature validator-ux-coverage
- To close when done: /work-backlog-item close plugin-validator UX and coverage gaps
```

## Planning (with title substring)

```text
> /work-backlog-item Error Recovery

Found: "SAM: Error Recovery / Rollback Procedures" (P1)
No groomed content in item file. Running groom-backlog-item first...

[groomed content written to item file]

RT-ICA: APPROVED — all conditions available.
Composing feature request...
Invoking /add-new-feature...

[SAM phases run]

Updated per-item file with Plan: plan/tasks-2-error-recovery.md

Next steps:
- To execute:      /implement-feature error-recovery
- To check status: /implementation-manager status . error-recovery
- To close when done: /work-backlog-item close error-recovery
```
