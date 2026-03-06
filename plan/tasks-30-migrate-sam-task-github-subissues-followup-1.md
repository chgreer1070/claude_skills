---
tasks:
  - task: "Fix _sub_issues_to_task_dicts using si.body directly instead of repo.get_issue(si.sub_issue.number).body"
    status: pending
    parent_task: "plan/tasks-2-migrate-sam-task-github-subissues.md"
---

# Task: Fix SubIssue body access in _sub_issues_to_task_dicts

## Parent Task
- Original: `plan/tasks-2-migrate-sam-task-github-subissues.md`
- Review Date: 2026-03-06

## Status
- [ ] Pending

## Priority
High

## Description

The task spec (Context Manifest, lines 217 and 356-372) explicitly documents:

> `SubIssue` inherits from `Issue` but `.body` cannot be relied on directly from the `SubIssue` object returned by `get_sub_issues()`. Use `repo.get_issue(si.sub_issue.number).body` to fetch the body.

However, `_sub_issues_to_task_dicts` in `operations.py` (line 1584) reads `si.body` directly:

```python
body = si.body or ""
```

And `fetch_tasks_from_github` in `implementation_manager.py` (line 922) also reads `si.body`:

```python
body = si.body or ""
```

Both violate the CoVe requirement from the spec. The comment at line 921 of `implementation_manager.py` even acknowledges the ambiguity:

```python
# SubIssue inherits from Issue — .body is directly accessible.
```

This contradicts the spec. If `SubIssue.body` returns `None` or empty string from the API (which the spec says can happen), `parse_sam_task_metadata(body)` will return `None` for every sub-issue, causing `get_sam_tasks` to return an empty task list even when sub-issues exist with valid SAM metadata. This would silently break the entire GitHub-backed task query path.

The correct fix is to call `repo.get_issue(si.sub_issue.number).body` (using the number attribute on `si.sub_issue`, not `si.number`) per the spec. This requires passing `repo` to `_sub_issues_to_task_dicts`. Verify the actual PyGitHub `SubIssue` attribute (`sub_issue.number` vs another attribute) against the installed source at `.venv/lib/python3.11/site-packages/github/Issue.py` before writing the fix.

## Acceptance Criteria
- [ ] `_sub_issues_to_task_dicts` in `operations.py` fetches body via `repo.get_issue(...)` not `si.body`
- [ ] `fetch_tasks_from_github` in `implementation_manager.py` fetches body via `repo.get_issue(...)` not `si.body`
- [ ] The correct attribute path on `SubIssue` is verified from installed PyGitHub source before fixing
- [ ] Tests for `get_sam_tasks` are updated to mock `repo.get_issue()` returning the correct body
- [ ] Tests for `fetch_tasks_from_github` are updated accordingly
- [ ] `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` exits 0
- [ ] `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` exits 0

## Files to Modify
- `.claude/skills/backlog/backlog_core/operations.py:1573-1590` - `_sub_issues_to_task_dicts` must accept `repo` and call `repo.get_issue()`
- `.claude/skills/backlog/backlog_core/operations.py:1697` - caller must pass `repo` to `_sub_issues_to_task_dicts`
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:919-923` - fix `si.body` access in `fetch_tasks_from_github`
- `.claude/skills/backlog/tests/test_operations_sam.py` - update mock setup to mock `repo.get_issue()` return value

## Verification Steps
1. Read `.venv/lib/python3.11/site-packages/github/Issue.py` to confirm the correct `SubIssue` attribute for fetching issue number
2. Run `uv run pytest .claude/skills/backlog/tests/test_operations_sam.py -v` - all tests pass
3. Run `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py` - exits 0

## References
- Original review: `plan/tasks-2-migrate-sam-task-github-subissues.md` T1 CoVe checks (lines 356-372)
- Related code: `.claude/skills/backlog/backlog_core/operations.py:1573`
- Related code: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:919`
