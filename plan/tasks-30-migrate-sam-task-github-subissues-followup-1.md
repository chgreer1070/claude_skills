---
tasks:
  - task: "Fix _sub_issues_to_task_dicts using si.body directly instead of repo.get_issue(si.sub_issue.number).body"
    status: complete
    parent_task: "plan/tasks-2-migrate-sam-task-github-subissues.md"
---

# Task: Fix SubIssue body access in _sub_issues_to_task_dicts

## Parent Task
- Original: `plan/tasks-2-migrate-sam-task-github-subissues.md`
- Review Date: 2026-03-06

## Status
- [x] Complete

## Priority
High

## Resolution

**Determination**: `si.body` is safe and reliable. No code changes required.

**Evidence from PyGitHub source** (`.venv/lib/python3.11/site-packages/github/Issue.py`, verified 2026-03-07):

1. `SubIssue` extends `Issue` directly: `class SubIssue(Issue)` (line 822).
2. `SubIssue._useAttributes` calls `super()._useAttributes(attributes)` (line 856) — all `Issue` attributes including `body` are fully populated from the API response JSON.
3. `Issue.body` calls `self._completeIfNotSet(self._body)` (lines 196-198) — PyGitHub's lazy-completion mechanism triggers an additional API call to fetch the full issue if `body` was not included in the initial paginated response.
4. `get_sub_issues()` uses `PaginatedList(SubIssue, ...)` (lines 577-583) — each element is initialized via `_useAttributes` with the full sub-issue API response, which includes `body`.

**Conclusion**: The `_completeIfNotSet` mechanism ensures `si.body` always returns the body string, either from the initial paginated response or via a lazy-fetch API call. Using `repo.get_issue(si.number).body` as the spec suggested would be redundant (doubling API calls) without any reliability benefit.

**Action taken**: Added an explanatory comment to both `_sub_issues_to_task_dicts` in `operations.py` and `fetch_tasks_from_github` in `implementation_manager.py` documenting why `si.body` is safe, citing the verified PyGitHub source location and date.

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
- [x] Verify the actual PyGitHub `SubIssue` attributes by reading `.venv/lib/python3.11/site-packages/github/SubIssue.py` (or similar path) to understand what attributes are available. **Done**: Read `github/Issue.py` lines 822-861. There is no separate `SubIssue.py` — `SubIssue` is defined at the end of `Issue.py` as `class SubIssue(Issue)`.
- [x] If `si.body` is confirmed directly accessible AND reliable (not sometimes None from the API), document this in a comment and leave the code as-is. **Done**: Added detailed comments to both files explaining the lazy-completion mechanism.
- [x] Tests for `get_sam_tasks` remain passing (no mock changes needed — `si.body` interface unchanged).
- [x] `uv run prek run --files` passes on both modified files.

## Files Modified
- `.claude/skills/backlog/backlog_core/operations.py` — Added explanation comment to `_sub_issues_to_task_dicts` docstring
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — Expanded inline comment in `fetch_tasks_from_github`

## Verification Steps
1. Read `.venv/lib/python3.11/site-packages/github/Issue.py` to confirm `SubIssue` structure — Done.
2. Run `uv run pytest .claude/skills/backlog/tests/test_operations_sam.py -v` — all tests pass.
3. Run `uv run pytest tests/test_migrate_tasks_to_github.py -v` — all tests pass.
4. Run `uv run prek run --files .claude/skills/backlog/backlog_core/operations.py plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` — exits 0.

## References
- Original review: `plan/tasks-2-migrate-sam-task-github-subissues.md` T1 CoVe checks (lines 356-372)
- Related code: `.claude/skills/backlog/backlog_core/operations.py:1573`
- Related code: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:919`
