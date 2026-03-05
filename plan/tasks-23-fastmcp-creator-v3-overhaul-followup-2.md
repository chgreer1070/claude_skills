---
tasks:
  - task: "Restore or remove accessing_online_resources.md — listed as preserved file but does not exist"
    status: pending
    parent_task: "plan/tasks-1-fastmcp-creator-v3-overhaul.md"
---

# Task: Resolve Missing accessing_online_resources.md Reference File

## Parent Task
- Original: `plan/tasks-1-fastmcp-creator-v3-overhaul.md`
- Review Date: 2026-03-05

## Status
- [ ] Pending

## Priority
Medium

## Description

The task spec at `plan/tasks-1-fastmcp-creator-v3-overhaul.md` lists
`plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md` as a
file to **preserve** (not touch):

```text
plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md
```

However, the file does not exist in the repository. A glob search for the file returns no results.
Two possibilities:

1. The file was accidentally deleted during the overhaul (Task T4.1 deleted the five old reference
   files, and this file may have been collateral damage).
2. The file never existed and the task spec listed it erroneously.

The `python3-development` skill's SKILL.md references an `accessing_online_resources.md` at
`./references/accessing_online_resources.md` — this suggests the file is a real, shared resource
that should exist for the fastmcp-creator plugin as well.

The SKILL.md for fastmcp-creator does NOT currently link to this file, so there is no broken
link in the published skill. However, if the file was intentionally preserved and was deleted
by mistake, it should be restored.

## Acceptance Criteria
- [ ] Determine whether `accessing_online_resources.md` existed before the overhaul by checking
      git history: `git log --diff-filter=D -- plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md`
- [ ] If it was deleted: restore it from git history and add a link from SKILL.md's "Related Skills"
      or "Reference Files" section
- [ ] If it never existed: remove the reference from the task spec Context Manifest (or document
      the finding as a task spec error — no code change needed)
- [ ] If restored: `uv run prek run --files plugins/fastmcp-creator/skills/fastmcp-creator/SKILL.md`
      passes with zero errors

## Files to Modify
- Depends on finding above:
  - If restore: create `plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md`
    from git history and update `plugins/fastmcp-creator/skills/fastmcp-creator/SKILL.md` to link it
  - If never existed: no file changes needed; annotate task spec

## Verification Steps
1. `git log --diff-filter=D -- plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md`
2. If output is non-empty: `git show <commit>:plugins/fastmcp-creator/skills/fastmcp-creator/references/accessing_online_resources.md`
   to retrieve content for restoration
3. If restored: verify SKILL.md link resolves with Glob tool

## References
- Original review: `plan/tasks-23-fastmcp-creator-v3-overhaul-followup-2.md`
- Task spec preserved file list: `plan/tasks-1-fastmcp-creator-v3-overhaul.md` lines 190-199
- Analog file in another plugin: `plugins/python3-development/skills/python3-development/references/accessing_online_resources.md` (may be the canonical source)
