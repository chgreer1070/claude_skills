---
tasks:
  - task: "Fix Task.name field populated from task_id not title in fetch_tasks_from_github and _load_tasks_from_cache"
    status: pending
    parent_task: "plan/tasks-2-migrate-sam-task-github-subissues.md"
---

# Task: Fix Task.name populated from task_id instead of title

## Parent Task
- Original: `plan/tasks-2-migrate-sam-task-github-subissues.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
Medium

## Description

In `fetch_tasks_from_github` (`implementation_manager.py` lines 931-944), `Task.name` is set to `sam.task_id` instead of a human-readable title:

```python
tasks.append(
    Task(
        id=sam.task_id,
        name=sam.task_id,   # BUG: should be a human-readable title
        ...
    )
)
```

Similarly, in `_load_tasks_from_cache` (lines 863-876), `Task.name` is also set from `raw.get("task_id", "")`.

The local-file path (`parse_task_file`) populates `Task.name` from the `title` field in the YAML frontmatter. The `status` command output includes `{"id": t.id, "name": t.name, "agent": t.agent}` in `ready_tasks`. When the orchestrator reads the `--github` path output, `Task.name` will be `"T1"` instead of `"Add SAM task operations to operations.py"`, breaking the human-readable display and any downstream parsing that distinguishes name from id.

The `SamTask` model does not have a `title` field — the title comes from the GitHub issue title (via `si.title`). The fix requires passing the issue title through. In `fetch_tasks_from_github`, `si.title` is accessible on the `SubIssue` object. In `_load_tasks_from_cache`, the cache payload written by `fetch_tasks_from_github` does not include a `title` field, so the title would need to be added to the cache payload.

The `_write_sam_task_cache` function (followup-2 addresses format) should also include `title` per task in the cache. The `_load_tasks_from_cache` can then read `raw.get("title", raw.get("task_id", ""))` as a fallback.

## Acceptance Criteria
- [ ] `fetch_tasks_from_github` sets `Task.name` from `si.title` (GitHub issue title) not from `sam.task_id`
- [ ] The cache payload written by `fetch_tasks_from_github` includes `title` per task entry
- [ ] `_load_tasks_from_cache` reads `Task.name` from `raw.get("title", raw.get("task_id", ""))` with fallback
- [ ] `status --github` output `ready_tasks[].name` contains the task title (e.g., "Add SAM task operations to operations.py"), not just the task ID ("T1")
- [ ] `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` exits 0

## Files to Modify
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:931-944` - set `name=si.title` in `fetch_tasks_from_github`
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:950-965` - add `"title": t.name` to cache payload per task entry
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:863-876` - read `name` from `raw.get("title", raw.get("task_id", ""))` in `_load_tasks_from_cache`
- `tests/test_implementation_manager/test_github_flag.py` - assert `name` field is not equal to `id` in ready_tasks output

## Verification Steps
1. Run `uv run pytest tests/test_implementation_manager/test_github_flag.py -v` - all pass
2. Run `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` - exits 0

## References
- Original review: `plan/tasks-2-migrate-sam-task-github-subissues.md` T3 task
- Related code: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:931`
