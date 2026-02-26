---
milestone: N
title: "Milestone title"
version: "vN"
date-opened: YYYY-MM-DD
date-closed: YYYY-MM-DD
status: archived
items-completed: 0
items-carried-forward: 0
items-resolved: 0
items-unverified: 0
---

# Milestone vN: {Title} — Completion Archive

<!-- Written by: complete-milestone skill. Do not edit manually. -->
<!-- SOURCE: Adapted from GSD milestone-archive.md pattern (accessed 2026-02-26) -->

## Summary

**Date range**: {YYYY-MM-DD} → {YYYY-MM-DD}
**Items completed**: N (AC verified PASS)
**Items carried forward**: N (work continues in next milestone)
**Items resolved**: N (closed without full implementation)
**Items unverified**: N (closed without AC verification — see Pre-flight section)

## Definition of Done

<!-- The milestone-level success criteria written at create-milestone time. -->
<!-- If none were defined at creation, write "Not specified at creation time." -->

- <!-- criterion 1 -->
- <!-- criterion 2 -->

**Met**: YES | NO | PARTIAL

## Pre-flight Audit Results

<!-- Output of the pre-flight audit gate from complete-milestone Step 0. -->
<!-- Lists items closed via verify path vs items closed without AC verification. -->

Items closed via `/work-backlog-item close` (AC verified):

- <!-- #N Title — PASS -->

Items closed without AC verification:

- <!-- #N Title — not run through verify path -->

## Items Completed

<!-- Items that reached status:done with AC verified PASS. -->

| Issue | Title | Acceptance Criteria | Verified |
|---|---|---|---|
| #N | {title} | {count} criteria | PASS |

## Items Carried Forward

<!-- Items assigned to this milestone but not completed — moved to next milestone. -->

| Issue | Title | Status at close | Reason |
|---|---|---|---|
| #N | {title} | in-progress | {reason} |

## Items Resolved

<!-- Items closed without full implementation — obsolete, superseded, or out-of-scope. -->

| Issue | Title | Resolution |
|---|---|---|
| #N | {title} | {reason} |

## Requirements Coverage

<!-- For each milestone goal (definition of done criterion above), which items addressed it? -->
<!-- Gap: goal stated but no item completed against it. -->

- {criterion}: covered by #N, #M — MET
- {criterion}: no items completed — GAP

## Decisions Made

<!-- Key decisions made during this milestone that affect future planning. -->
<!-- Each decision should include: what was decided, why, and any deferred work. -->

1. **{decision}** — {rationale}. Deferred: {what was not done}.

## Next Milestone Goals

<!-- Recommended focus for the next milestone, based on carried-forward items and open gaps. -->

- {goal 1}
- {goal 2}

## Archive Location

**Milestone GitHub URL**: <https://github.com/Jamie-BitFlight/claude_skills/milestone/N>
**Archive file**: `.claude/milestones/vN-completion.md`
