# ADR-010: task_id is the canonical field name in SAM task file YAML frontmatter

**Date:** 2026-03-07
**Status:** Accepted

## Context

SAM task files store per-task metadata in YAML frontmatter. The field identifying a task within that frontmatter has been written inconsistently across task files — some use `task_id:`, others use `task:`.

This inconsistency surfaced as a bug in `implementation_manager.py`. The script has two parsing paths:

- `parse_task_from_frontmatter()` — high-level function that normalizes `task_id` → `task` before returning the parsed result. Code downstream of this function sees a consistent `task` key.
- `_find_task_section_in_file()` and `_try_claim_part()` — lower-level functions that read frontmatter directly using `fm.get("task")`, bypassing the normalization performed by `parse_task_from_frontmatter()`.

When a task file used `task_id:` as the field name, the lower-level functions found nothing and `claim-task` always returned task-not-found, regardless of whether the task existed.

The fix added a compatibility shim to both lower-level functions:

```python
# COMPAT(issue=#N, remove_when="all task files migrated to task_id:", added=2026-03-07)
task_id = fm.get("task") if "task" in fm else fm.get("task_id")
```

This shim resolves the immediate bug but introduces a dual-field dependency that must not persist indefinitely. The canonical field name must be declared so migration and shim removal have a clear target.

## Decision

`task_id:` is the canonical YAML frontmatter field name for task identity in SAM task files.

- All new task files must use `task_id:` as the field name.
- `task:` is a deprecated alias. It is accepted only via the compatibility shim documented in ADR-011.
- The compatibility shim handling `task:` must carry a `COMPAT:` annotation per ADR-011.
- The shim must be removed once all task files in the repository have been migrated to `task_id:`.
- `parse_task_from_frontmatter()` must be updated to read `task_id:` natively once the shim is removed, eliminating the internal normalization step that introduced the divergence.

## Consequences

**Positive:**

- Single canonical field name eliminates parsing ambiguity across all code paths.
- New task files and task-generating agents have an unambiguous field to write.
- The shim removal condition is concrete and observable: zero remaining `task:` fields in task files.

**Negative:**

- Existing task files using `task:` must be migrated before the compatibility shim can be removed. The migration scope is bounded to files matching `plan/tasks-*.md` and `plan/tasks-*/**.md`.
- Until migration is complete, two code paths must be maintained and tested.

**Migration path:**

1. Run a one-time migration script across all task files to rename `task:` → `task_id:` in YAML frontmatter.
2. Verify with `implementation_manager.py validate` that all task files parse correctly.
3. Remove the compatibility shim from `_find_task_section_in_file()` and `_try_claim_part()`.
4. Update `parse_task_from_frontmatter()` to read `task_id:` directly without internal normalization.
5. Close the tracking issue referenced in the `COMPAT:` annotation.
