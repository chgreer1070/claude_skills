---
name: 'github_project_setup.py: add GitHub Projects V2 status field updates'
description: The `milestone start` and `milestone close` commands transition `status:*` labels on issues but do not update the GitHub Projects V2 `Status` field (the kanban column). These are separate systems — labels are on the issue, the V2 status is a project-level field. Add `project update-status` subcommand to `github_project_setup.py` that uses the GraphQL API to set the `Status` field on project items. This unlocks the full kanban board view in GitHub Projects.
metadata:
  topic: githubprojectsetuppy-add-github-projects-v2-status-field-upd
  source: 'PR #149 follow-up — start-milestone automation (2026-02-22)'
  added: '2026-02-22'
  priority: P2
  type: Feature
  status: open
  issue: '#236'
  groomed: '2026-02-28'
  last_synced: '2026-02-28T05:39:37Z'
  plan: plan/tasks-8-project-v2-status-updates.md
---

## Story

As a **developer**, I want **The `milestone start` and `milestone close` commands transition `status:*` la...** so that **backlog items are tracked in GitHub**.

## Description

The `milestone start` and `milestone close` commands transition `status:*` labels on issues but do not update the GitHub Projects V2 `Status` field (the kanban column). These are separate systems — labels are on the issue, the V2 status is a project-level field. Add `project update-status` subcommand to `github_project_setup.py` that uses the GraphQL API to set the `Status` field on project items. This unlocks the full kanban board view in GitHub Projects.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: PR #149 follow-up — start-milestone automation (2026-02-22)
- **Priority**: P2
- **Added**: 2026-02-22
- **Research questions**: None

**Suggested location**: `.claude/skills/gh/scripts/github_project_setup.py` — add `project_app` Typer sub-app with `project update-status --project-number N --issue-number N --status "In Progress"` command

**Research first**: Projects V2 GraphQL API — `updateProjectV2ItemFieldValue` mutation. Field ID discovery via `projectV2Fields` query. Reference: `.claude/skills/gh/references/projects-v2.md`.

## Fact-Check

Fact-Check Summary: GitHub Projects V2 status field updates
Claims checked: 4

VERIFIED (4):
1. github_project_setup.py exists at .claude/skills/gh/scripts/github_project_setup.py — confirmed
2. milestone start/close commands exist — confirmed (label transitions implemented)
3. Projects V2 Status field NOT updated by milestone commands — confirmed (gap exists)
4. GraphQL API reference at .claude/skills/gh/references/projects-v2.md — confirmed
   Prior work: .claude/scripts/sync_issues_to_project.py has updateProjectV2ItemFieldValue mutation pattern

All claims verified. No refuted claims.

## RT-ICA

RT-ICA: github_project_setup.py Projects V2 status updates
Goal: Add project update-status subcommand to github_project_setup.py using GraphQL API
Decision: APPROVED

Conditions:
1. Script exists and has Typer structure | AVAILABLE
2. GraphQL mutation pattern available | AVAILABLE (sync_issues_to_project.py)
3. Field ID discovery documented | AVAILABLE (projects-v2.md)
4. Status field values known | DERIVABLE (sync_issues_to_project.py STATUS_OPTIONS)
5. Milestone integration points identified | AVAILABLE (milestone_start, milestone_close functions)

Missing: None
Assumptions to confirm: Exact Status field values in target project

## Groomed (2026-02-28)

### Priority

8/10 — Core kanban synchronization for milestone automation. Blocks full project board visibility.

### Impact

- Blocks: Teams cannot see true project status in kanban board when milestones are started/closed
- Bottleneck: Milestone automation incomplete — labels update but board state does not

### Benefits

- Kanban board reflects actual work state matching milestone transitions
- Full project visibility without manual status column updates
- Automation loop closes: label changes propagate to project field changes

### Acceptance Criteria

1. project update-status subcommand exists in github_project_setup.py
2. Uses GraphQL updateProjectV2ItemFieldValue mutation
3. Field ID and option ID discovery via projectV2Fields query
4. Accepts valid status values (Backlog, Grooming, In Progress, In Review, Done)
5. --dry-run flag shows changes without applying
6. milestone_start and milestone_close call update_status after label transitions

### Resources

| Type | Item |
|------|------|
| Script | .claude/skills/gh/scripts/github_project_setup.py |
| Reference | .claude/skills/gh/references/projects-v2.md |
| Prior work | .claude/scripts/sync_issues_to_project.py (GraphQL mutation pattern) |

### Dependencies

- Depends on: None
- Blocks: Full kanban board synchronization

### Blockers

None — RT-ICA APPROVED

### Effort

Medium — 40-60 minutes. Typer sub-app structure exists, GraphQL mutation template available.