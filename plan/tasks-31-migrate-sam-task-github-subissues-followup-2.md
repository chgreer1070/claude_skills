---
tasks:
  - task: "Fix _write_sam_task_cache missing synced_at and count fields; cache format diverges from spec"
    status: pending
    parent_task: "plan/tasks-2-migrate-sam-task-github-subissues.md"
---

# Task: Fix _write_sam_task_cache cache format to match spec

## Parent Task
- Original: `plan/tasks-2-migrate-sam-task-github-subissues.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
Medium

## Description

The spec (Context Manifest lines 196-214) documents the required cache file format:

```json
{
  "feature_slug": "my-feature",
  "parent_issue_number": 480,
  "synced_at": "2026-03-06T12:00:00+00:00",
  "tasks": [...]
}
```

But `_write_sam_task_cache` in `operations.py` (lines 1558-1570) writes:

```python
payload = {"tasks": tasks, "count": len(tasks), "parent_issue_number": parent_issue_number}
```

Two divergences from spec:
1. **Missing `synced_at` field** — the spec requires it; the reader in `get_sam_tasks` offline fallback path (lines 1682-1690) reads `cached.get("count", len(cached_tasks))` which handles the missing `count`, but `synced_at` is missing entirely. The `_load_tasks_from_cache` in `implementation_manager.py` does not use `synced_at`, but the field is part of the documented format contract.
2. **Missing `feature_slug` field** — the spec includes it in the format. Without it, readers that scan for a matching cache by feature slug (rather than parent issue number) cannot confirm the slug.

Additionally, `_write_sam_task_cache` writes the full task dicts (from `_sub_issues_to_task_dicts`) verbatim into the cache. These dicts include all SamTask fields plus `issue_number` and `issue_url`. The spec's example cache shows a minimal format (`task_id`, `status`, `agent`, `priority`, `skills`, `dependencies`). The reader in `_load_tasks_from_cache` in `implementation_manager.py` (lines 856-876) reads `raw["task_id"]`, `raw.get("status")`, `raw.get("priority")`, `raw.get("agent")`, `raw.get("skills")`, `raw.get("dependencies")` — all present in the full dict — so this does not cause a functional bug, but the extra fields (`issue_number`, `issue_url`, SamTask internal fields) are not filtered out.

The `feature_slug` in the cache is also used by `get_sam_tasks` offline path when scanning multiple cache files (line 1678) to match `parent_issue_number`. The current implementation correctly matches on `parent_issue_number`, so the offline fallback works. But `feature_slug` being absent means a reader relying on that field would get an empty string.

## Acceptance Criteria
- [ ] `_write_sam_task_cache` includes `synced_at` (ISO timestamp) in the payload
- [ ] `_write_sam_task_cache` includes `feature_slug` in the payload (derive from `_extract_feature_slug(tasks)`)
- [ ] The cache format matches the documented spec example exactly (same top-level keys)
- [ ] The `test_get_sam_tasks_writes_cache` test asserts `synced_at` and `feature_slug` are present in written cache
- [ ] `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` exits 0

## Files to Modify
- `.claude/skills/backlog/backlog_core/operations.py:1558-1570` - add `synced_at` and `feature_slug` to payload
- `.claude/skills/backlog/tests/test_operations_sam.py:329-338` - assert `synced_at` and `feature_slug` in cache

## Verification Steps
1. Read `operations.py` lines 1558-1570 after fix — confirm `synced_at` and `feature_slug` present
2. Run `uv run pytest .claude/skills/backlog/tests/test_operations_sam.py::TestGetSamTasks::test_get_sam_tasks_writes_cache -v` - passes
3. Run `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` - exits 0

## References
- Original review: `plan/tasks-2-migrate-sam-task-github-subissues.md` T1 requirement 10 (cache write format)
- Related code: `.claude/skills/backlog/backlog_core/operations.py:1558`
- Spec format: Context Manifest lines 196-214
