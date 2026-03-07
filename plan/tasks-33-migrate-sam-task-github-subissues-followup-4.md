---
tasks:
  - task: "T5 SKILL.md update incomplete: start-task does not document writing github_issue update to in-progress"
    status: pending
    parent_task: "plan/tasks-2-migrate-sam-task-github-subissues.md"
---

# Task: Complete T5 — start-task SKILL.md missing in-progress GitHub sync step

## Parent Task
- Original: `plan/tasks-2-migrate-sam-task-github-subissues.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
Medium

## Description

The task spec (Context Manifest lines 113-116 and 192-194) requires two updates to start-task SKILL.md:

1. Step 5 of start-task must write `parent_issue_number` to the active-task context file.
2. If `parent_issue_number` is known and `github_issue` is set in the task YAML, call `backlog_core.github.update_task_status(repo, github_issue, "in-progress")` after writing the context file.

The start-task SKILL.md does document `parent_issue_number` in the context file (confirmed at line 126 via grep). However, the second requirement — calling `update_task_status` to mark the sub-issue as `"in-progress"` at task start — is mentioned only as a conditional note (line 132-133: "If `parent_issue_number` is known and `github_issue` field is set in the task YAML, call...").

This is documentation only; the actual implementation of this sync on task start is not present in `task_status_hook.py`. The hook currently syncs GitHub only on `SubagentStop` (task completion). The spec explicitly requires in-progress syncing to happen from start-task, not the hook. Without this, GitHub sub-issues stay at `not-started` throughout execution, providing no live status visibility.

Additionally, the SKILL.md update for `implement-feature` documents `backlog_get_ready_sam_tasks` (confirmed at line 56), but does not document whether the orchestrator should prefer the MCP tool over `implementation_manager.py --github` for ready-task queries. The spec (Context Manifest line 103-107) says T2 provides `get_ready_sam_tasks` as the MCP-preferred query path — this preference is not clearly stated in either SKILL.md.

## Acceptance Criteria
- [ ] `start-task` SKILL.md step 6 (or a new step) explicitly instructs: if `github_issue` is in the task YAML frontmatter and `parent_issue_number` is known, call `update_task_status(repo, github_issue, "in-progress")` via `backlog_core.github` (best-effort, warn and continue on failure)
- [ ] Both copies of start-task SKILL.md are updated identically: `.claude/skills/start-task/SKILL.md` and `plugins/python3-development/skills/development/start-task/SKILL.md`
- [ ] `implement-feature` SKILL.md documents the MCP-preferred query path: use `backlog_get_ready_sam_tasks(parent_issue_number=N)` when parent issue is known; fall back to `implementation_manager.py ready-tasks` for local-only scenarios
- [ ] Both copies of implement-feature SKILL.md are updated identically

## Files to Modify
- `.claude/skills/start-task/SKILL.md` - add in-progress GitHub sync step after context file write
- `plugins/python3-development/skills/development/start-task/SKILL.md` - mirror of above
- `.claude/skills/implement-feature/SKILL.md` - clarify MCP-preferred vs CLI query preference
- `plugins/python3-development/skills/development/implement-feature/SKILL.md` - mirror of above

## Verification Steps
1. Read `.claude/skills/start-task/SKILL.md` — confirm step for in-progress GitHub sync is present
2. Diff the two copies of start-task SKILL.md — confirm they are identical
3. Diff the two copies of implement-feature SKILL.md — confirm they are identical
4. Read `plugins/python3-development/skills/development/start-task/SKILL.md` — confirm in-progress sync step present

## References
- Original review: `plan/tasks-2-migrate-sam-task-github-subissues.md` T5 task
- Related code: `.claude/skills/start-task/SKILL.md:126-133`
