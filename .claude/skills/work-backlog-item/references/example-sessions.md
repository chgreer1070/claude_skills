# Example Sessions

## Quick mode (one-file fix)

<eg>
> /work-backlog-item --quick gitlab-skill: Remove hardcoded URL

Found: "gitlab-skill: Remove hardcoded URL" (P1)
Quick mode — skipping grooming, RT-ICA, and SAM planning.

Composing quick plan...

plan/quick/gitlab-skill-remove-hardcoded-url.md created.
  Steps: 2 tasks
  Done when: URL replaced in plugins/gitlab-skill/skills/gitlab-skill/SKILL.md

To execute: /implement-feature plan/quick/gitlab-skill-remove-hardcoded-url.md
To close:   /work-backlog-item close gitlab-skill: Remove hardcoded URL
</eg>

## Progress report

<eg>
> /work-backlog-item progress

Backlog Health — 2026-02-26

Active Milestone: #5 v1.1 — Quality Gates
  Closed:      8 items
  Open:        5 items
  Progress:    [########..] 61%

Overall Backlog:
  P0:    1 items (1 in milestone)
  P1:    22 items (8 in milestone, 5 groomed but unassigned)
  P2:    40 items
  Ideas: 12 items

Next recommended action:
  /work-backlog-item SAM: Error Recovery  — SAM: Error Recovery (P1, groomed, in active milestone)
</eg>

## Resume a stopped implementation

<eg>
> /work-backlog-item resume Error Recovery

Resume: SAM: Error Recovery / Rollback Procedures
Plan:   plan/tasks-2-error-recovery.md

Progress: 5/12 tasks (41%)

Last completed:  Add retry logic to execute_task in executor.py
Next to do:      Write unit tests for retry behaviour

To continue: /implement-feature error-recovery
To close:    /work-backlog-item close Error Recovery
</eg>

## Closing a completed item (by title)

<eg>
> /work-backlog-item close validator UX

Found: "plugin-validator UX and coverage gaps" (P1)
Plan: plan/tasks-2-validator-ux-coverage.md
Checklist: 12/12 tasks complete

Extracting acceptance criteria from item file...
  Found 3 criteria.

Spawning acceptance criteria verification agent...

Acceptance Criteria Verification:

  [PASS] plugin_validator.py reports unique file counts — verified at plugins/plugin-creator/scripts/plugin_validator.py:187
  [PASS] hook validation included in report — verified at plugins/plugin-creator/scripts/plugin_validator.py:203
  [PASS] test suite passes — confirmed via git log (commit 4a2f1b3)

Overall: PASS (3/3 criteria met)

Backlog item "plugin-validator UX and coverage gaps" closed.
- Checklist: 12/12 tasks complete
- Acceptance criteria: PASS (3/3)
- Status written to per-item file
</eg>

## Resolving a no-longer-applicable item

<eg>
> /work-backlog-item resolve commitlint verify last flag

Found: "commitlint: Verify --last flag and exit codes against primary sources" (P1)
Why is this item no longer applicable?
> REFUTED by fact-check: --last flag is verified in commitlint source cli.ts. No fix needed.

Backlog item resolved.
  Resolved: 2026-02-21
  Status: RESOLVED — REFUTED by fact-check: --last flag verified against commitlint
          source cli.ts and official docs. No fix needed.
</eg>

## Issue-first workflow and setup-github examples

See [github-integration.md](./github-integration.md) for GitHub Issue creation flow and setup-github session examples.
