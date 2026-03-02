---
name: 'complete-implementation: route follow-up task files to backlog instead of orphaning'
description: "The complete-implementation skill's code-reviewer phase creates follow-up task files (plan/tasks-{N}-{slug}-followup-{k}.md) when it finds gaps. The workflow then expects to recurse with /implement-feature on them. Problem: when the orchestrator skips recursion (deferred scope, different priority, session timeout, or context compaction), these files are orphaned — no backlog item links to them, no one knows they exist. This has happened 3+ times in recent sessions. Fix: Add a routing step between 'code reviewer creates follow-up' and 'recurse with implement-feature'."
metadata:
  topic: complete-implementation-route-follow-up-task-files-to-backlo
  source: 'Observed during #368 implementation — follow-up for get_gitlab_context.py was orphaned until manually linked'
  added: '2026-03-02'
  priority: P1
  type: Feature
  status: in-progress
  issue: '#381'
  groomed: '2026-03-02'
  last_synced: '2026-03-02T04:11:53Z'
---

## Fact-Check

Claims checked: 3 | VERIFIED: 3 | REFUTED: 0 | INCONCLUSIVE: 0

1. VERIFIED: code-reviewer phase creates follow-up task files (plan/tasks-{N}-{slug}-followup-{k}.md) — Evidence: SKILL.md line 59, local-workflow.md line 241
2. VERIFIED: workflow expects to recurse with /implement-feature on them — Evidence: SKILL.md lines 62-65, local-workflow.md lines 243-244
3. VERIFIED: no routing to backlog exists when recursion is skipped — Evidence: SKILL.md Recursive Follow-up Handling section has no backlog logic

## RT-ICA

Goal: Ensure follow-up task files created by complete-implementation are routed to backlog items instead of being orphaned when recursion is skipped.

Conditions:
1. complete-implementation SKILL.md exists and contains Recursive Follow-up Handling section | Status: AVAILABLE | Source: .claude/skills/complete-implementation/SKILL.md lines 57-65
2. Backlog script supports search-by-title, create, and update --plan operations | Status: AVAILABLE | Source: backlog.py add/update/list commands verified
3. Follow-up file naming convention is documented | Status: AVAILABLE | Source: plan/tasks-{N}-{slug}-followup-{k}.md per SKILL.md line 59
4. create-backlog-item skill exists and can be invoked programmatically | Status: AVAILABLE | Source: .claude/skills/create-backlog-item/SKILL.md
5. Criteria for when to recurse vs. defer to backlog are defined | Status: DERIVABLE | Basis: issue description states 'same priority AND same session scope' — needs formalization in implementation

Decision: APPROVED
Missing: None
Assumptions to confirm: recursion criteria (condition 5) — exact definition of 'same session scope' needs formalization during architecture phase

## Groomed (2026-03-02)

### Reproducibility

1. Observe complete-implementation skill Phase 1 (code-reviewer) finishing review
2. Code reviewer identifies gaps and creates follow-up task file: `plan/tasks-{N}-{slug}-followup-{k}.md`
3. Complete-implementation skill expects to recurse (lines 62-65 of SKILL.md) via `/implement-feature` on the follow-up file
4. However, orchestrator skips recursion due to: session timeout/context compaction, different priority, or deferred scope decision
5. Result: Follow-up file exists but no backlog item references it — it is orphaned

### Output / Evidence

- Observable: no GitHub Issue or `.claude/backlog/` entry for the follow-up work
- Evidence: item description states "This has happened 3+ times in recent sessions" (session #368 with get_gitlab_context.py follow-up)
- Log: SKILL.md Recursive Follow-up Handling section (lines 57-65) has no fallback path for skipped recursion

### Priority

9/10 — Prevents permanent loss of necessary follow-up work; happens when orchestrator context management is constrained (common end-of-session condition). Data loss is irreversible without manual re-discovery.

### Impact

- Blocks: follow-up work exists but is invisible to the backlog tracking system
- Bottleneck: orchestrators cannot safely skip recursion without guaranteeing follow-up files are tracked
- Cost: manual re-linking required when discovered; risk that orphaned files are never discovered

### Expected Behavior

When complete-implementation's code-reviewer phase creates a follow-up task file:

1. The system searches the backlog for an existing item matching the follow-up's scope (by title keywords)
2. If found: follow-up file is attached to the existing item via `backlog update --plan <path>`
3. If not found: new backlog item is created via `create-backlog-item` with the follow-up file as its plan
4. Recursion decision: recurse via `implement-feature` only if priority AND session scope match; otherwise, link to backlog and stop
5. User is notified of the backlog routing decision

### Acceptance Criteria

1. Complete-implementation SKILL.md Recursive Follow-up Handling section includes routing step (search backlog, create/update item, decision gate)
2. Routing step successfully searches backlog by title keywords extracted from follow-up filename
3. When match found: `backlog update --plan {followup_path}` is called with the matching item title
4. When no match found: `create-backlog-item --auto {title}` is called with derived title and the followup file path
5. Recursion only proceeds when both: (a) priority of follow-up equals or exceeds priority of parent item, AND (b) session scope is unchanged
6. Complete-implementation skill document is updated with the new routing workflow
7. No follow-up files exist in `plan/tasks-*-followup-*.md` that lack corresponding backlog items

### Resources

| Type | Item |
|------|------|
| Skill | /backlog |
| Skill | /complete-implementation |
| Skill | /create-backlog-item |
| Skill | /implement-feature |
| Agent | @code-reviewer |
| Prior work | .claude/skills/backlog/scripts/backlog.py (add, update, list operations) |
| Prior work | .claude/rules/local-workflow.md — Recursive Follow-up section (lines 239-244) |
| Prior work | plugins/python3-development/agents/code-reviewer.md — Creates follow-up task files |

### Dependencies

- Depends on: None — this is an enhancement to existing complete-implementation workflow
- Blocks: N/A — improves guardrails without blocking other work

### Blockers

None. RT-ICA is APPROVED. All required conditions are available or derivable.

### Effort

Medium — backlog search logic, routing gate logic, priority comparison, session scope check, SKILL.md update, and E2E test case.
