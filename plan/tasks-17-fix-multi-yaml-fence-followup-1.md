---
task: T1
title: Handle mixed plan-level YAML + fenced per-task YAML in parse_task_content
status: pending
parent_task: plan/tasks-15-fix-multi-yaml-fence/T6.md
priority: 2
complexity: medium
---

# Task: Handle Mixed Plan-Level YAML + Fenced Per-Task YAML

## Parent Task

- Original: `plan/tasks-15-fix-multi-yaml-fence/T6.md`
- Review Date: 2026-03-02

## Status

- [ ] Pending

## Priority

High

## Description

The `parse_task_content` function in `implementation_manager.py` does not handle the case where
a file contains **both** plan-level YAML frontmatter (starting the file with `---`) **and**
per-task YAML frontmatter wrapped in fenced code blocks within the body.

**Current behavior on `plan/tasks-4-validate-orchestrator-discipline.md`**:

1. `has_yaml_frontmatter(content)` returns `True` — because the file starts with `---\n`
   (the plan-level description frontmatter)
2. `parse_task_from_frontmatter(content)` is called on the entire file
3. It raises `ValueError: Missing required YAML frontmatter fields: task, title, status`
   (because the plan-level YAML is feature metadata, not a task)
4. Falls through to legacy parsing
5. Legacy parser looks for `## Task` headers — finds none (tasks use `### T1:` format)
6. Returns empty list `[]`

**The fenced per-task YAML blocks in the body are never reached** because
`detect_fenced_yaml` is only called when `has_yaml_frontmatter` returns `False`. When a file
starts with `---` (any YAML frontmatter), the fenced-detection path is short-circuited.

**Architecture spec claim** (Compatibility table, `plan/architect-fix-multi-yaml-fence.md`):

> Mixed: plan-level YAML + fenced per-task YAML | Silent failure | Auto-stripped per-task fences, parsed with warning

This claim is NOT met by the current implementation.

**T6 acceptance criterion (not met)**:

> The JSON output contains at least one task (non-empty tasks array)

The actual output is `"total_tasks": 0`.

The regression test was adjusted to accept 0 tasks with the comment
"The fixture's top-level frontmatter is a feature-level description, so parse_task_content
returns 0 tasks." This softens the acceptance criterion but does not fix the structural gap.

**Root cause**: `parse_task_content` dispatches exclusively on `has_yaml_frontmatter(content)`.
When this returns `True`, it attempts to parse the entire file as a single-task frontmatter.
The function has no logic to:
1. Detect that the YAML frontmatter does not contain task fields
2. Fall to body scanning for fenced per-task blocks
3. Strip those fenced blocks and treat each as a separate task

**Required behavior for the mixed case**:

After `parse_task_from_frontmatter` raises `ValueError`, if the fallthrough legacy parsing
also returns an empty list, the implementation SHOULD apply `detect_fenced_yaml` to the
body content (the part after the plan-level `---` block) as a recovery path.

## Acceptance Criteria

- [ ] `parse_task_content` called with `plan/tasks-4-validate-orchestrator-discipline.md`
      content returns at least one `Task` object (non-empty list)
- [ ] The returned tasks have correct `id` values (`T1`, `T2`, `T3`, `T4`)
- [ ] Stderr contains WARNING about fenced YAML detection
- [ ] All 18 existing tests in `test_task_format_fenced_yaml.py` continue to pass
- [ ] `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
      exits 0
- [ ] `uv run python3 plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py status . validate-orchestrator-discipline`
      exits 0 with `"total_tasks": 4` in JSON output

## Files to Modify

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:651-720`
  — `parse_task_content` function: add body-level fenced YAML detection after legacy parsing
  returns empty list
- `plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py:491-529`
  — `TestRegressionFixture.test_parse_task_content_real_world_regression`: update assertion
  to require `len(result) >= 1` instead of accepting empty list

## Implementation Approach

After legacy parsing returns `tasks = []`:

```python
# If legacy parsing also returned nothing AND we previously detected plan-level YAML,
# attempt to extract and strip fenced blocks from the body content.
if not tasks and has_yaml_frontmatter(content):
    # Extract body after the plan-level frontmatter
    parts = content.split("---\n", 2)
    if len(parts) >= 3:
        body = parts[2]
        stripped_body = detect_fenced_yaml(body)
        if stripped_body is not None:
            sys.stderr.write(
                "WARNING: Plan-level YAML file contains fenced per-task YAML in body. "
                "Stripping fences and re-parsing body.\n"
            )
            tasks = parse_task_content(stripped_body, _depth=_depth + 1)
```

Note: The recursion depth guard (`_depth > 1`) must still apply. The body re-parse uses
`_depth + 1`, so it can only happen once (depth 0 → body re-parse at depth 1 → guard at
depth 2).

## Verification Steps

1. Run the implementation manager against the real file:

```bash
uv run python3 plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  status . validate-orchestrator-discipline 2>/tmp/im_stderr.txt
cat /tmp/im_stderr.txt
```

Expected: JSON output with `"total_tasks": 4`, stderr contains `WARNING`.

2. Run all existing tests to verify no regressions:

```bash
uv run pytest plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py -v
```

Expected: all 18 tests pass.

3. Run linting:

```bash
uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py
```

## References

- Original review: `plan/tasks-15-fix-multi-yaml-fence`
- T6 acceptance criteria: `plan/tasks-15-fix-multi-yaml-fence/T6.md:66-73`
- Architecture spec compatibility table: `plan/architect-fix-multi-yaml-fence.md:293-308`
- Related code: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:651-720`
- Real-world fixture: `plan/tasks-4-validate-orchestrator-discipline.md`
