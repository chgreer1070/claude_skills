# ADR-011: COMPAT annotation standard for compatibility shims

**Date:** 2026-03-07
**Status:** Accepted

## Context

Compatibility shims, field-name fallbacks, and temporary workarounds are regularly introduced during bug fixes. Without a tracking convention, these accumulate silently — they are never removed because there is no recorded condition under which removal is safe, no issue to follow up on, and no CI gate to surface their presence.

The `claim-task` fix on 2026-03-07 is a concrete example. A field-name fallback was added to `_find_task_section_in_file()` and `_try_claim_part()` in `implementation_manager.py` to handle task files that use `task:` instead of the canonical `task_id:`. The shim resolves the immediate bug but has no documented removal condition, no linked issue, and no enforcement mechanism. Without intervention, it will persist indefinitely.

This pattern repeats across any codebase with active development. The cost is accumulated dead code, increased cognitive load when reading compatibility branches, and reduced confidence in whether any given shim is still necessary.

## Decision

Every compatibility shim added to the codebase must carry a structured `COMPAT:` annotation on the line immediately before the compatibility code. The annotation format is:

```python
# COMPAT(issue=#N, remove_when="<observable condition>", added=YYYY-MM-DD)
```

**Field definitions:**

- `issue` — GitHub issue number that tracks the removal work. Required. The issue must exist before the shim is merged.
- `remove_when` — A concrete, observable condition that makes the shim safe to remove. Must be verifiable without judgment (e.g., "all task files migrated to task_id:", "users on version < 2.0 reach < 1% of traffic"). Dates are not acceptable — they are not observable conditions. Required.
- `added` — ISO date (YYYY-MM-DD) the shim was introduced. Required.

**Placement rule:** The annotation must appear on the line immediately before the compatibility code, with no blank lines between annotation and code.

**Example — correct:**

```python
# COMPAT(issue=#42, remove_when="all task files migrated to task_id:", added=2026-03-07)
task_id = fm.get("task") if "task" in fm else fm.get("task_id")
```

**Example — incorrect (missing fields):**

```python
# COMPAT: temporary fallback for old field name
task_id = fm.get("task") if "task" in fm else fm.get("task_id")
```

**Enforcement via pre-commit hook:**

A pre-commit hook script at `scripts/check_compat_annotations.py` scans all Python files for `COMPAT` comments and fails if any are malformed (missing one or more of `issue=`, `remove_when=`, `added=`).

The hook also scans for any bare `fm.get("task")` pattern that lacks the `task_id` fallback, as a regression guard specific to ADR-010. This guard may be generalized to other known deprecated patterns as they are identified.

The hook runs on every commit that touches a `.py` file. CI runs the same check on pull requests.

## Consequences

**Positive:**

- Every shim is traceable to a GitHub issue, ensuring removal work enters the backlog.
- The `remove_when` condition gives any future reader a concrete way to evaluate whether the shim is still necessary.
- CI enforcement means malformed annotations fail fast at commit time, not during code review.
- The pattern is low-overhead: one line per shim.

**Negative:**

- A GitHub issue must exist before the shim can be merged. For hotfixes, this adds one step to the fix workflow.
- The pre-commit hook must be wired before this standard is enforced. Until it is wired, the annotation format is a convention, not a constraint.
- `remove_when` requires the author to think through the removal condition at shim-introduction time, which takes slightly more effort than writing an unstructured comment.

**Dependencies:**

- `scripts/check_compat_annotations.py` must be created and added to `.pre-commit-config.yaml`.
- The hook must be included in the `prek` configuration so it runs via `uv run prek run`.
