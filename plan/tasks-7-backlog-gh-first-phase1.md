---
description: "Phase 1: Flip backlog add/list/update to GitHub-first with local cache fallback"
version: "1.0"
tasks:
  - "T1: Flip add to GH-first — create issue before writing local cache"
  - "T2: Add --from-github flag to list — query GH Issues with label filters"
  - "T3: Make update --plan GH-first — write plan ref to issue body then local"
  - "T4: Auto-migration — pull creates missing GH Issues for P0/P1 items"
  - "T5: Batch status fetch — optimize --with-status to avoid N+1 API calls"
  - "T6: Acceptance tests — verify GH-first flows and graceful degradation"
task_exports:
  enabled: false
  directory: "TASK"
---

# Task Plan: Backlog GH-First Phase 1

## Metadata

- **Feature slug**: backlog-gh-first-phase1
- **Issue**: #282
- **Total tasks**: 6
- **Estimated change**: ~200 lines modified in backlog.py, ~150 lines new test file
- **Primary file**: .claude/skills/backlog/scripts/backlog.py (1948 lines)

## Parallelization Map

```text
Group 1 (Core flip — independent changes to separate functions):
  T1 ──┐
       ├── can run concurrently (T1=add, T2=list, T3=update modify different functions)
  T2 ──┤
       │
  T3 ──┘

    ↓ Sync Checkpoint 1: verify add/list/update all work locally (no GH token set)

Group 2 (Integration — depends on Group 1):
  T4 ──┐
       ├── can run concurrently (T4=migration in pull, T5=batch fetch in list)
  T5 ──┘

    ↓ Sync Checkpoint 2: verify pull auto-migrates and list --with-status batches

Group 3 (Validation — depends on Group 1+2):
  T6 (sequential: write and run tests)

    ↓ Sync Checkpoint 3: all tests pass, pre-commit passes
```

---

## Sync Checkpoints

### Checkpoint 1: After Group 1

```bash
# Verify add works without GITHUB_TOKEN (graceful degradation)
GITHUB_TOKEN= uv run .claude/skills/backlog/scripts/backlog.py add \
  --title "Test local fallback" --priority P2 --description "test" --no-create-issue

# Verify list still works from local cache
uv run .claude/skills/backlog/scripts/backlog.py list --format json | head -5

# Verify update --plan writes to local
uv run .claude/skills/backlog/scripts/backlog.py update "Test local fallback" --plan "plan/test.md"

# Cleanup
rm .claude/backlog/p2-test-local-fallback.md
```

### Checkpoint 2: After Group 2

```bash
# Verify pull creates missing issues (dry-run)
uv run .claude/skills/backlog/scripts/backlog.py pull --dry-run -R Jamie-BitFlight/claude_skills

# Verify list --with-status uses batch fetch (observe single API call log)
uv run .claude/skills/backlog/scripts/backlog.py list --with-status -R Jamie-BitFlight/claude_skills
```

### Checkpoint 3: After Group 3

```bash
# Run tests
uv run pytest .claude/skills/backlog/tests/ -v

# Pre-commit on modified file
uv run prek run --files .claude/skills/backlog/scripts/backlog.py
```

---

## Tasks

### T1: Flip `add` to GH-first

**File**: `.claude/skills/backlog/scripts/backlog.py`
**Functions**: `_add_item_index_format()` (line 698), `add()` (line 761)

**Current behavior**: Creates local file first (line 731), then optionally creates GH Issue (line 733). The `--create-issue` flag defaults to True (line 770).

**Target behavior**: Try to create GH Issue first. If it succeeds, write local cache with issue number already embedded in frontmatter. If GH is unavailable, fall back to local-only (write local file without issue number, log warning).

**Changes**:

1. In `_add_item_index_format()`, reorder operations:
   - Build the item dict (title, description, etc.) — same as now
   - If `create_issue` is True, call `_try_get_github(repo)`:
     - If repository is available, call `create_issue_for_item()` to get issue_num
     - If repository is None (no token, network error), log warning and set issue_num = None
   - Build frontmatter with issue number already included (if available)
   - Write local cache file (one write, not write-then-update)

2. Remove the separate `_update_item_metadata()` call after issue creation (line 749) — the issue number is included in the initial write.

3. Add `set_synced=True` to the local write when GH issue was created (sets `last_synced` in frontmatter).

**Key constraint**: `_try_get_github()` (line 131) already handles graceful degradation — returns None on network error or missing token. Use this instead of `_get_github()` which raises on failure.

**Acceptance criteria**:
- [ ] `add` with GITHUB_TOKEN creates GH Issue first, then writes local file with issue number
- [ ] `add` without GITHUB_TOKEN writes local file only, logs warning, does not raise
- [ ] `add --no-create-issue` skips GH entirely (still needed for testing/offline use)
- [ ] Local file written in single operation (no write-then-update)

---

### T2: Add `--from-github` flag to `list`

**File**: `.claude/skills/backlog/scripts/backlog.py`
**Functions**: `list_items()` (line 867), `_list_items_json()` (line 816), `_list_items_table()` (line 845)

**Current behavior**: `parse_backlog()` reads only local `.claude/backlog/*.md` files. No GH API call unless `--with-status` (which does N+1 queries per item).

**Target behavior**: New `--from-github` flag queries GH Issues with label filters and rebuilds local cache. Default behavior unchanged (local cache read).

**Changes**:

1. Add `--from-github` parameter to `list_items()`:
   ```python
   from_github: Annotated[bool, typer.Option("--from-github")] = False,
   ```

2. When `--from-github` is True:
   - Call `_try_get_github(repo)` — if None, fall back to local with warning
   - Use PyGithub to list open issues with label filter: `repo.get_issues(state='open', labels=[...])`
   - Filter by priority labels: `priority:p0`, `priority:p1`, `priority:p2`
   - For each issue: call `_pull_single_issue()` to create/update local cache
   - Then read from local cache as usual (cache is now fresh)

3. Add `--label` parameter (optional) for filtering:
   ```python
   label: Annotated[str | None, typer.Option("--label")] = None,
   ```
   When provided, pass to `repo.get_issues(labels=[label])`.

4. Default `list` (no flags) remains local-only — zero API calls, fast for agents.

**Acceptance criteria**:
- [ ] `list` (no flags) reads only local files — zero API calls
- [ ] `list --from-github` queries GH, updates local cache, displays results
- [ ] `list --from-github --label priority:p1` filters by label
- [ ] `list --from-github` with no GITHUB_TOKEN falls back to local with warning

---

### T3: Make `update --plan` GH-first

**File**: `.claude/skills/backlog/scripts/backlog.py`
**Functions**: `_apply_plan_to_item()` (line 1510), `update()` (line 1523)

**Current behavior**: `--plan` writes only to local file (line 1556). `--status in-progress` already writes to GH first (line 1564).

**Target behavior**: `--plan` also writes plan reference to GH Issue body (as a "Notes" section update), then updates local cache. GH write is best-effort — local always succeeds.

**Changes**:

1. Modify `_apply_plan_to_item()` to also update GH issue:
   - After local update, check if item has `_issue`
   - If yes, call `_try_get_github(repo)` and add/update a comment or body section:
     ```python
     gh_issue.create_comment(f"**Plan**: {plan}")
     ```
   - Use `_try_get_github()` for graceful degradation — if GH unavailable, local update still succeeds

2. Pass `repo` parameter to `_apply_plan_to_item()` (currently only takes `item` and `plan`).

**Acceptance criteria**:
- [ ] `update --plan` writes to local file AND posts plan comment on GH Issue
- [ ] `update --plan` without GITHUB_TOKEN writes local only, no error
- [ ] `update --plan` on item with no GH Issue writes local only

---

### T4: Auto-migration — `pull` creates missing GH Issues

**File**: `.claude/skills/backlog/scripts/backlog.py`
**Functions**: `pull()` (line 1913), `_sync_create_missing_issues()` (line 901)

**Current behavior**: `pull` only fetches existing GH Issues into local cache. `sync` creates missing issues as a separate command.

**Target behavior**: `pull` also creates missing GH Issues for P0/P1 items before fetching. This makes `pull` the single auto-migration command.

**Changes**:

1. In `pull()`, before fetching issue bodies, check for items without GH Issues:
   ```python
   items = parse_backlog()
   # Auto-migration: create missing GH Issues for P0/P1
   items_without_issues = [
       it for it in items
       if it.get("_section") in {"P0", "P1"} and not it.get("_skip") and not it.get("_issue")
   ]
   if items_without_issues:
       typer.echo(f"Auto-migrating {len(items_without_issues)} P0/P1 item(s) to GitHub Issues...")
       _sync_create_missing_issues(items, repo, dry_run)
       # Re-parse after migration to get updated issue numbers
       items = parse_backlog()
   ```

2. Add a log message: `[AUTO-MIGRATE] Creating GitHub Issue for: {title}`

3. Restrict auto-migration to P0/P1 only (P2/Ideas stay local-only unless explicitly synced).

**Acceptance criteria**:
- [ ] `pull` creates GH Issues for P0/P1 items missing them
- [ ] `pull --dry-run` reports what would be created without creating
- [ ] P2/Ideas items are NOT auto-migrated
- [ ] After migration, pull fetches the newly created issue bodies into local cache

---

### T5: Batch status fetch for `--with-status`

**File**: `.claude/skills/backlog/scripts/backlog.py`
**Functions**: `_list_items_json()` (line 816), `_list_items_table()` (line 845), `_fetch_item_status()` (line 798)

**Current behavior**: `--with-status` calls `_get_github()` and `repository.get_issue()` for EACH item individually (N+1 queries). For 20+ items this is slow and risks rate limiting.

**Target behavior**: Single batch query fetches all open issues with status labels, builds a lookup map, then decorates items from the map.

**Changes**:

1. New helper function `_batch_fetch_statuses()`:
   ```python
   def _batch_fetch_statuses(items: list[dict], repo: str) -> dict[int, dict]:
       """Batch fetch status and milestone from GH for all items with issue numbers.

       Returns:
           Dict mapping issue_number -> {"status": str, "milestone": str}
       """
       repo_obj = _try_get_github(repo)
       if not repo_obj:
           return {}
       # Single API call: fetch all open issues
       all_issues = {
           issue.number: issue
           for issue in repo_obj.get_issues(state="open")
       }
       result = {}
       for item in items:
           num_str = item.get("_issue", "").lstrip("#")
           if not num_str.isdigit():
               continue
           num = int(num_str)
           if num in all_issues:
               gh_issue = all_issues[num]
               status_labels = [l.name for l in gh_issue.labels if l.name.startswith("status:")]
               result[num] = {
                   "status": status_labels[0] if status_labels else "",
                   "milestone": gh_issue.milestone.title if gh_issue.milestone else "",
               }
       return result
   ```

2. Replace per-item `_get_github()` + `get_issue()` calls in `_list_items_json()` and `_list_items_table()` with a single `_batch_fetch_statuses()` call.

**Acceptance criteria**:
- [ ] `list --with-status` makes at most 2 API calls (auth + list issues), not N+1
- [ ] Status and milestone data is identical to current per-item fetch
- [ ] Graceful degradation when GH unavailable (empty status, no crash)

---

### T6: Acceptance tests

**File**: `.claude/skills/backlog/tests/test_backlog_gh_first.py` (new)

Write tests using `unittest.mock` to mock PyGithub calls. No live API calls in tests.

**Test cases**:

1. **test_add_gh_first_success**: Mock `_try_get_github()` to return a mock repo. Verify `create_issue_for_item()` is called before `filepath.write_text()`. Verify local file contains issue number in frontmatter.

2. **test_add_gh_unavailable_fallback**: Mock `_try_get_github()` to return None. Verify local file is created without issue number. Verify no exception raised.

3. **test_list_from_github**: Mock `repo.get_issues()` to return mock issues. Verify `_pull_single_issue()` is called for each. Verify output matches expected format.

4. **test_list_default_no_api_calls**: Verify that `list` without `--from-github` never calls `_try_get_github()`.

5. **test_update_plan_gh_first**: Mock GH. Verify plan comment is posted to issue. Verify local file is updated.

6. **test_pull_auto_migration**: Mock GH. Create local items without issue numbers. Verify `pull` creates issues for P0/P1, skips P2/Ideas.

7. **test_batch_status_fetch**: Mock `repo.get_issues(state="open")`. Verify single call replaces N individual `get_issue()` calls.

8. **test_graceful_degradation_all_commands**: For each of add, list, update: mock `_try_get_github()` returning None. Verify command completes successfully with local-only fallback.

**Acceptance criteria**:
- [ ] All 8 test cases pass
- [ ] Tests use mocks only — no live API calls
- [ ] `uv run pytest .claude/skills/backlog/tests/ -v` exits 0
- [ ] Pre-commit passes on test file

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| GH API rate limiting during batch fetch | `_try_get_github()` with timeout; paginate `get_issues()` |
| Breaking existing `sync` command | `sync` still works — it calls same `_sync_create_missing_issues()` |
| `--from-github` slow for large repos | Only fetches open issues with label filters; local cache used for subsequent reads |
| Existing callers of `add` (create-backlog-item skill) | `--create-issue` flag kept; default behavior unchanged (True) |
| Offline agents breaking | `_try_get_github()` returns None — all commands fall back to local |

## Out of Scope (Phase 2/3)

- `push` command (full local→GH bidirectional sync)
- Offline queue-for-sync (writes queued locally, pushed when online)
- Dependent skill SKILL.md updates (create-backlog-item, work-backlog-item, groom-backlog-item)
- Authorization gate enforcement (`agent:actionable` label filtering)
