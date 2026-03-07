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

> **Resolution note**: The failure scenario below was investigated and disproved. See ## Resolution above.

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

---

## Context Manifest

_Added by context-refinement agent on 2026-03-07_

This follow-up task required investigating the PyGitHub `SubIssue` API to determine whether
`si.body` was safe to use directly, as both `operations.py` and `implementation_manager.py`
did. The original spec (from the parent task's Context Manifest) claimed `si.body` could not
be relied on and directed implementors to use `repo.get_issue(si.sub_issue.number).body`
instead. That claim was incorrect on two counts.

### Discovered During Implementation

_Session Date: 2026-03-07_

During implementation, we discovered that the original spec's guidance about PyGitHub's
`SubIssue.body` was factually wrong. The spec said `SubIssue.body` could not be relied on
directly from `get_sub_issues()` and advised using `repo.get_issue(si.sub_issue.number).body`
as the correct alternative. Investigation of the actual PyGitHub source at
`.venv/lib/python3.11/site-packages/github/Issue.py` revealed the opposite is true.

**Key Discoveries:**

1. **SubIssue class location**: `SubIssue` is not in a separate file. It is defined at line
   822 of `Issue.py` as `class SubIssue(Issue)`. There is no `github/SubIssue.py`. Future
   investigations into PyGitHub sub-issue behavior must look in `Issue.py`.

2. **`si.body` is always safe**: `Issue.body` (inherited by `SubIssue`) calls
   `self._completeIfNotSet(self._body)` (lines 196-198). This is PyGitHub's lazy-completion
   mechanism: if `body` was not populated in the initial API response, PyGitHub
   automatically issues an additional API call to fetch the full issue object. `si.body` can
   never return `None` due to the API response being incomplete — it either succeeds or
   raises an exception.

3. **The spec's suggested alternative was incorrect**: The spec directed use of
   `repo.get_issue(si.sub_issue.number).body`. `SubIssue` has no `sub_issue` attribute.
   Its attributes beyond those inherited from `Issue` are only `parent_issue` and
   `priority_position` (lines 822-861). The correct equivalent would have been
   `repo.get_issue(si.number).body`, but this is redundant — it doubles API calls with no
   reliability benefit over `si.body`.

4. **Both files correct as-is**: `operations.py` and `implementation_manager.py` both used
   `si.body` correctly from the start. The fix was documentation only — adding explanatory
   comments citing the PyGitHub source to prevent future false-positive code reviews.

#### Updated Technical Details

- `SubIssue` class: `github/Issue.py` line 822, `class SubIssue(Issue)`
- `SubIssue._useAttributes`: line 856, calls `super()._useAttributes(attributes)` — all
  `Issue` fields including `body` are populated from the API response JSON
- `Issue.body` lazy-completion: lines 196-198, `_completeIfNotSet(self._body)`
- `get_sub_issues()`: lines 577-583, uses `PaginatedList(SubIssue, ...)` — each element
  initialized with the full sub-issue API response

#### Gotchas for Future Developers

- Do not trust spec comments that claim PyGitHub attributes are unreliable without verifying
  against the installed source. The lazy-completion pattern means attribute access is always
  safe — the library handles partial responses transparently.
- If you need to investigate `SubIssue`, look in `Issue.py`, not a separate file.
- Adding `repo.get_issue(si.number).body` instead of `si.body` does NOT improve reliability;
  it only doubles API calls.

### Design Refinements

The original spec claimed `si.body` was unreliable and directed use of
`repo.get_issue(si.sub_issue.number).body`. Investigation showed:

- Original (spec): `"SubIssue inherits from Issue but .body cannot be relied on directly
  from the SubIssue object returned by get_sub_issues()"`
- Actual: `si.body` is fully reliable due to PyGitHub's `_completeIfNotSet` lazy-completion
  mechanism
- Original (spec): `"Use repo.get_issue(si.sub_issue.number).body"` — incorrect; `SubIssue`
  has no `sub_issue` attribute
- Actual: The correct attribute to use would be `si.number`, but `si.body` already works and
  is preferred

Classification: **design-refinement** — the spec described incorrect PyGitHub behavior. The
implementation (using `si.body`) was correct from the start. No intent divergence: the goal
of reliably reading sub-issue bodies was achieved; only the spec's stated mechanism was wrong.
