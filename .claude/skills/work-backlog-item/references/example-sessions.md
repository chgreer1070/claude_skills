# Example Sessions

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

## Resolving a completed item (by title)

```text
> /work-backlog-item resolve validator UX

Found: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Spawning acceptance criteria verification agent...

Verdict: PASS
Evidence: Sub-issues 1-4 implemented in plugins/plugin-creator/scripts/plugin_validator.py
          commit 4a2f1b3 — "fix(validator): report unique files, add hook validation"

Summarize what was done:
> Implemented all 4 sub-issues: unique file reporting, hook validation, coverage gaps filled.

Backlog item "plugin-validator UX and coverage gaps" resolved.
- Summary: Implemented all 4 sub-issues: unique file reporting, hook validation, coverage gaps filled.
- Checklist: 12/12 tasks complete
- Acceptance criteria: PASS
- GitHub Issue #131 closed with evidence trail
```

## Resolving a completed item (by issue number)

```text
> /work-backlog-item resolve #131

Fetching GitHub Issue #131...
  Title: plugin-validator UX and coverage gaps
  State: open

Found per-item file match: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Spawning acceptance criteria verification agent...

Verdict: PASS
Evidence: commit 4a2f1b3 — "fix(validator): report unique files, add hook validation"

Summarize what was done:
> All validator sub-issues implemented and tested.

Backlog item "plugin-validator UX and coverage gaps" resolved.
- Summary: All validator sub-issues implemented and tested.
- GitHub Issue #131 closed with evidence trail
```

## Closing (dismissing) an item

```text
> /work-backlog-item close commitlint verify last flag

Found: "commitlint: Verify --last flag and exit codes against primary sources" (P1)
Why is this item being dismissed?
> out_of_scope
Any additional comment?
> REFUTED by fact-check: --last flag verified against commitlint source cli.ts. No fix needed.

Backlog item closed.
  Closed: 2026-02-21
  Reason: out_of_scope
  Comment: REFUTED by fact-check: --last flag verified against commitlint
           source cli.ts and official docs. No fix needed.
```

## GitHub Issue creation flow and setup-github examples

See [github-integration.md](./github-integration.md) for the GitHub Issue creation flow and setup-github session examples.
