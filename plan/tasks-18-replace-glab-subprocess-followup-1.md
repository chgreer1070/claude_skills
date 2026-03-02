---
tasks:
  - task: "Remove glab subprocess fallback from get_gitlab_context.py (Gap #1 from #368)"
    status: pending
    parent_task: "plan/tasks-17-replace-glab-subprocess.md"
---

# Task: Remove glab subprocess fallback from get_gitlab_context.py

## Parent Task

- Original: `plan/tasks-17-replace-glab-subprocess.md`
- Review Date: 2026-03-02

## Status

- [ ] Pending

## Priority

Medium

## Description

`plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py` contains the same
subprocess/glab pattern that was removed from `fetch_gitlab_mr.py` in commit 2996746.
The architecture spec for #368 explicitly identified this file as "Gap #1" and deferred it
as out of scope. Now that the pattern is established, this follow-up completes the remediation.

The file at `plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py`
(lines 6-7, 24, 29) imports and uses `shutil` and `subprocess` to invoke the `glab` CLI
binary for token resolution. The same S607 (subprocess call with partial executable path)
ruff violation exists there.

The reference implementation to match is now `fetch_gitlab_mr.py` lines 89-99 (post-#368):

```python
def _resolve_token() -> str | None:
    """Resolve GitLab API token from environment variables.

    Checks in order:
    1. GITLAB_TOKEN environment variable
    2. GITLAB_PRIVATE_TOKEN environment variable

    Returns:
        Token string, or None if no token found.
    """
    return os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN") or None
```

## Acceptance Criteria

- [ ] `import shutil` does not appear in `get_gitlab_context.py`
- [ ] `import subprocess` does not appear in `get_gitlab_context.py`
- [ ] `_resolve_token()` (or equivalent function) body is a single `return` expression
      using `os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN") or None`
- [ ] Error message in the caller of `_resolve_token()` names both `GITLAB_TOKEN` and
      `GITLAB_PRIVATE_TOKEN` (not "configure glab")
- [ ] `uv run ruff check plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py --select S607`
      exits 0 with no output
- [ ] `uv run prek run --files plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py`
      exits 0
- [ ] No `# noqa: S607` suppression added
- [ ] `fetch_gitlab_mr.py` is not modified (only `get_gitlab_context.py` changes)

## Files to Modify

- `plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py:6-7,24-29` -
  delete `import shutil`, `import subprocess`, and the subprocess block in `_resolve_token()`
  (or equivalent function); replace with single-expression env-var return

## Verification Steps

1. Confirm no shutil/subprocess references remain:
   ```bash
   grep -n "shutil\|subprocess" plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py
   ```
   Must produce no output.

2. Run S607-targeted lint check:
   ```bash
   uv run ruff check plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py --select S607
   ```
   Must exit 0 with no output.

3. Run full linting gate:
   ```bash
   uv run prek run --files plugins/gitlab-skill/skills/gitlab-skill/scripts/get_gitlab_context.py
   ```
   Must exit 0.

4. Confirm `fetch_gitlab_mr.py` is unchanged:
   ```bash
   git diff .claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py
   ```
   Must produce no output.

## References

- Original review: code-reviewer agent review of commit 2996746
- Architecture spec that deferred this file: `plan/architect-replace-glab-subprocess.md`
  (Gap #1 section)
- Parent task: `plan/tasks-17-replace-glab-subprocess.md`
- Completed reference implementation: `.claude/skills/create-merge-request-changelog/scripts/fetch_gitlab_mr.py`
  commit 2996746
- Related closed issue: #368
