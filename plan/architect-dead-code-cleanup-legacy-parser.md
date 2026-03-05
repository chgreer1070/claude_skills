---
title: "Architecture: Dead Code Cleanup — Legacy Parser and Fenced YAML Recovery"
slug: dead-code-cleanup-legacy-parser
status: ready
generated: 2026-03-05
sources:
  - plan/feature-context-dead-code-cleanup-legacy-parser.md
  - plan/codebase/dead-code-scope.md
---

# Architecture: Dead Code Cleanup — Legacy Parser and Fenced YAML Recovery

## Executive Summary

All task files now use the directory format with bare YAML frontmatter. The legacy markdown
parser, fenced YAML recovery path, and their supporting infrastructure are permanently
unreachable. This spec defines exact deletion boundaries for each dead code cluster across
three source files and one test file.

The single non-obvious constraint: `_legacy_field_to_yaml` is called from the **live** YAML
branch of `add_timestamp_to_task`, not from the dead legacy branch. Its field-name mapping
must be inlined into that call site before the function is deleted.

No new abstractions are introduced. This is a subtraction-only change.

---

## Scope

### Files Modified

| File | Nature of Change |
|---|---|
| `implementation_manager.py` | Delete parser classes, registry, `_parse_line`, dead branches in `parse_task_content` |
| `task_format.py` | Delete `detect_fenced_yaml`, `_FENCED_YAML_PATTERN`, remove from `__all__` |
| `task_status_hook.py` | Inline field map, delete `_legacy_field_to_yaml`, `_update_legacy_timestamp`, `_LEGACY_INSERT_AFTER_FIELDS`, dead branches in two functions |
| `test_task_format_fenced_yaml.py` | Delete entire file after extracting surviving tests |

### Files Not Modified

`task_format.py` functions `has_yaml_frontmatter`, `parse_yaml_frontmatter`,
`update_yaml_field`, `normalize_status`, `VALID_STATUSES`, `parse_task_from_frontmatter`
are live and untouched. `task_status_hook.py` functions `update_yaml_field`,
`find_task_section`, `get_iso_timestamp` are live and untouched.

---

## Decision 1: `implementation_manager.py` — FieldParser Cluster

### What to Delete

The entire FieldParser class hierarchy and its registry:

- Section header comment `# Field Parsers (OCP: ...)` at line 456
- `FieldParser` base class (lines 461–468)
- `StatusParser` (lines 471–483)
- `DependenciesParser` (lines 486–498)
- `AgentParser` (lines 501–519)
- `PriorityParser` (lines 521–537)
- `ComplexityParser` (lines 539–551)
- `StartedParser` (lines 554–566)
- `CompletedParser` (lines 569–581)
- `SkillsParser` (lines 584–598)
- `FIELD_PARSERS` registry (lines 600–610)
- `_create_empty_task_data` helper (lines 618–639) — only called from the legacy markdown
  loop that is being deleted
- `_parse_line` function (lines 642–655) — sole call site is the legacy loop

### Why

The entire call chain is: `FIELD_PARSERS` → `_parse_line` → legacy markdown loop in
`parse_task_content`. The codebase analysis confirmed no external files import any of these
symbols. With the legacy loop gone, all nine classes and the registry become unreferenced.
`_create_empty_task_data` is included because it is only called from the legacy loop to
initialize the dict that `_parse_line` populates.

### Boundary Condition

The section comment at line 456 (`# Task Parsing (SRP: ...)`) that precedes
`_create_empty_task_data` at line 613 is retained — it introduces the surviving YAML parsing
functions. Only the `# Field Parsers (OCP: ...)` section comment and its contents are removed.

---

## Decision 2: `implementation_manager.py` — `parse_task_content` Dead Branches

### What to Delete

Three dead code regions inside `parse_task_content` (function signature at line 658):

**Region A — Recursion guard** (lines 677–680):

```text
if _depth > 1:
    sys.stderr.write("WARNING: max recursion depth exceeded in parse_task_content\n")
    return []
```

**Region B — Fenced YAML recovery block** (lines 694–703, inside the `else` branch of
`has_yaml_frontmatter`):

```text
else:
    stripped = detect_fenced_yaml(content)
    if stripped is not None:
        sys.stderr.write("WARNING: Task file contains YAML frontmatter wrapped ...")
        return parse_task_content(stripped, _depth=_depth + 1)
```

**Region C — Legacy markdown loop** (lines 705–727):

```text
# Legacy markdown path: multiple tasks with ## Task headers
tasks: list[Task] = []
task_header_pattern = re.compile(...)
current_task: TaskData | None = None

for line in content.split("\n"):
    ...

if current_task:
    tasks.append(_create_task_from_dict(current_task))

return tasks
```

### What to Retain

The YAML frontmatter branch (lines 682–693) is the live path:

```text
if has_yaml_frontmatter(content):
    try:
        task = parse_task_from_frontmatter(content)
    except (ValueError, TypeError) as exc:
        sys.stderr.write(...)
    else:
        return [task]
```

The YAML parse failure warning (the `except` branch) is retained — it fires when a file has
valid `---` delimiters but malformed YAML content. This is a live defensive path.

### Signature Change

Remove the `_depth: int = 0` parameter from `parse_task_content`'s signature. After deletion,
the function is no longer recursive and carries no recursion state.

### Docstring Update

The docstring currently describes three format detection modes and fenced YAML recovery.
After deletion, the docstring describes only: YAML frontmatter format (single task per file
with `---` delimited metadata). All references to "legacy markdown", "automatic format
detection", and "fenced YAML recovery" are removed.

### `else` Collapse

Region B lives inside an `else` branch attached to `if has_yaml_frontmatter(content)`. After
removing Region B, the `else` clause becomes empty and is deleted entirely. The `if` block
stands alone with no `else`.

### `detect_fenced_yaml` Import

`implementation_manager.py` line 41 imports `detect_fenced_yaml` from `task_format`. After
Region B is deleted, this import has no remaining call site and is removed from the import
statement.

---

## Decision 3: `task_format.py` — `detect_fenced_yaml` and `_FENCED_YAML_PATTERN`

### What to Delete

- `_FENCED_YAML_PATTERN` compiled regex (lines 109–111)
- `detect_fenced_yaml` function (lines 114–137)
- `"detect_fenced_yaml"` entry in `__all__` (line 68)

### Why

`detect_fenced_yaml` has exactly one production call site: `implementation_manager.py:696`,
which is inside Region B (Decision 2). Deleting Region B leaves `detect_fenced_yaml` with
zero production callers. `_FENCED_YAML_PATTERN` is only used by `detect_fenced_yaml`.

The `__all__` list is a declaration of public API. Removing a function from `__all__` without
removing the function body would leave a symbol that is exported but has no callers. Both the
body and the `__all__` entry are deleted together.

### What is Not Affected

`has_yaml_frontmatter` and all other entries in `__all__` are untouched. The `_FRONTMATTER_DELIMITER`
constant and the frontmatter parsing block that follows `detect_fenced_yaml` are untouched.

---

## Decision 4: `task_status_hook.py` — `_legacy_field_to_yaml` Inline-Then-Delete

### The Constraint

`_legacy_field_to_yaml` is called from the **live** YAML branch of `add_timestamp_to_task`
at line 344:

```python
yaml_field = _legacy_field_to_yaml(field_name)
return update_yaml_field(content, yaml_field, timestamp)
```

Its sole purpose is to map PascalCase caller-provided field names to YAML snake_case keys:

```python
field_map = {
    "LastActivity": "last_activity",
    "Started": "started",
    "Completed": "completed",
    "Status": "status",
}
return field_map.get(field_name, field_name.lower())
```

### What to Do

The field mapping is inlined directly at the call site in `add_timestamp_to_task`'s YAML
branch. The local dict replaces the function call. After inlining, `_legacy_field_to_yaml`
has zero callers and is deleted.

### Implementation Contract for the Inline

The inlined mapping must be semantically identical to the function body:

- The four explicit mappings (`LastActivity`, `Started`, `Completed`, `Status`) map to their
  snake_case equivalents
- The fallback `field_name.lower()` is preserved for unmapped field names
- The result is assigned to `yaml_field` and passed to `update_yaml_field` exactly as before

The calling convention of `add_timestamp_to_task` does not change. Its signature, its
`task_id` parameter, and its `update_yaml_field` delegation are all unchanged.

### Why Not Rename

The function's name (`_legacy_field_to_yaml`) is misleading — it implies legacy-format
handling, but it serves the live YAML branch. Inlining removes the misleading name and makes
the field mapping visible at the site where it is used, without introducing a new function
with a corrected name. The mapping is small enough (4 entries + fallback) that inlining is
the cleaner outcome.

---

## Decision 5: `task_status_hook.py` — `_update_legacy_timestamp` and `_LEGACY_INSERT_AFTER_FIELDS`

### What to Delete

- `_LEGACY_INSERT_AFTER_FIELDS` constant (line 282)
- `_update_legacy_timestamp` function (lines 285–316)
- Legacy markdown fallback block in `add_timestamp_to_task` (lines 347–354):

  ```python
  # --- Legacy markdown format ---
  section = find_task_section(content, task_id)
  if section is None:
      raise ValueError(f"Task {task_id} not found in file")

  start_idx, end_idx = section
  lines = content.split("\n")
  return _update_legacy_timestamp(lines, start_idx, end_idx, field_name, timestamp)
  ```

### Why

`_update_legacy_timestamp` is only called from this legacy fallback block (line 354).
`_LEGACY_INSERT_AFTER_FIELDS` is only used by `_update_legacy_timestamp` (line 311).
The fallback block is only reachable when `has_yaml_frontmatter(content)` returns `False`,
which does not occur in production (all current task files use YAML frontmatter).

Deleting the fallback block makes `add_timestamp_to_task` a single-path function: it always
takes the YAML branch. The `if has_yaml_frontmatter(content):` guard becomes the function's
only path and its `if` can either be retained as a defensive check or removed entirely.

### Guard Retention Decision

The `if has_yaml_frontmatter(content):` guard in `add_timestamp_to_task` is **retained** as
a defensive assertion. Its body becomes unconditional logic, and the `else` (legacy fallback)
is deleted. Retaining the guard preserves an early-error signal if a non-frontmatter file is
ever passed to the function. The guard does not need to be converted to an `assert` — a clear
docstring note is sufficient.

### Docstring Update

`add_timestamp_to_task`'s docstring currently describes both YAML and legacy markdown paths.
After deletion, the docstring describes only the YAML path. The references to
`_update_legacy_timestamp` and "legacy markdown files" are removed. The `field_name`
parameter description is updated: it accepts YAML snake_case field names directly
(`"started"`, `"completed"`, `"last_activity"`) now that the PascalCase-to-snake_case
conversion is inlined.

---

## Decision 6: `task_status_hook.py` — `update_task_status` Dead Legacy Branch

### What to Delete

The legacy markdown fallback block in `update_task_status` (lines 403–421):

```python
# --- Legacy markdown format ---
section = find_task_section(content, task_id)
if section is None:
    raise ValueError(f"Task {task_id} not found in file")

start_idx, end_idx = section
lines = content.split("\n")
task_lines = lines[start_idx:end_idx]

# Find and update status line
status_pattern = r"^\*\*Status\*\*:\s*.*$"
for i, line in enumerate(task_lines):
    if re.match(status_pattern, line):
        task_lines[i] = f"**Status**: {new_status}"
        break

# Reconstruct content
result_lines = lines[:start_idx] + task_lines + lines[end_idx:]
return "\n".join(result_lines)
```

### Why

This block is only reachable when `has_yaml_frontmatter(content)` returns `False`, which does
not occur in production. The block is self-contained inline regex — it calls no helpers that
need separate deletion. Removing it makes `update_task_status` single-path, parallel to
`add_timestamp_to_task` after Decision 5.

### Guard Retention Decision

Same principle as Decision 5: the `if has_yaml_frontmatter(content):` guard in
`update_task_status` is retained as a defensive check. The `else` and its body are deleted.

### `re` Import Check

After both legacy blocks in `task_status_hook.py` are deleted, verify whether `import re`
is still used elsewhere in the file. If `re` has no remaining call sites in
`task_status_hook.py` after deletion, the import is removed. If other functions use `re`,
the import is retained.

---

## Decision 7: `test_task_format_fenced_yaml.py` — Test Classification and File Disposition

### Classification of All Test Classes

**Delete — tests exclusively cover dead code paths:**

`TestDetectFencedYaml` (lines 60–283) — 11 tests
: Tests `detect_fenced_yaml` directly. The function is deleted (Decision 3). Every test in
  this class becomes a reference to a removed symbol and will fail at import.

`TestParseTaskContent.test_parse_task_content_fenced_single` (line 305)
: Tests the fenced YAML recovery path through `parse_task_content`. Deleted in Decision 2.

`TestParseTaskContent.test_parse_task_content_fenced_multi` (line 332)
: Same — tests multi-block fenced YAML recovery. Dead path.

`TestParseTaskContent.test_parse_task_content_legacy_markdown_no_warning` (line 391)
: Tests the legacy markdown loop in `parse_task_content`. Deleted in Decision 2.

`TestParseTaskContent.test_parse_task_content_fenced_missing_required_field` (line 448)
: Tests the dual-warning path (fence-stripping + missing field). The fence-stripping half is
  dead. The missing-field warning half is tested by the surviving YAML parse failure test.

`TestRegressionFixture.test_parse_task_content_real_world_regression` (line 492)
: Asserts that `parse_task_content` emits a WARNING for the tasks-4 fixture file. After
  deletion, the YAML parse failure warning still fires for that file (the fixture has
  file-level frontmatter that fails task-level field validation). The test's regression
  signal is preserved by the surviving `test_parse_task_content_yaml_parse_failure_warns`.
  However, the specific assertion here ("WARNING must appear") depends on the fixture file
  still triggering the YAML parse failure path — acceptable to delete and rely on the
  unit-level test for that coverage.

**Retain — tests cover live behavior:**

`TestParseTaskContent.test_parse_task_content_raw_yaml_no_warning` (line 367)
: Tests the live YAML frontmatter path through `parse_task_content`. This is the primary
  production path and must remain covered.

`TestParseTaskContent.test_parse_task_content_yaml_parse_failure_warns` (line 422)
: Tests the YAML parse failure warning — the `except` branch retained in Decision 2. This
  is a live defensive path that must remain covered.

`TestDeferredSkippedStatus` (entire class, lines 575–805)
: Tests DEFERRED/SKIPPED status parsing and `get_ready_tasks` behavior. These use
  `parse_task_content` with YAML frontmatter inputs (live path) and `get_ready_tasks`
  directly. None of these tests touch fenced YAML or legacy markdown. All are retained.

### File Disposition

The file is **not deleted wholesale**. The surviving tests are migrated to an appropriate
existing or new test file before any deletion occurs.

**Migration target**: The two surviving `TestParseTaskContent` tests belong in a file that
covers `parse_task_content` and core parsing behavior — either a new
`test_implementation_manager_parsing.py` or appended to any existing test file for
`implementation_manager`. The `TestDeferredSkippedStatus` class can move to the same
file or remain split.

**After migration**: `test_task_format_fenced_yaml.py` is deleted. No test in the suite
references `detect_fenced_yaml` or any removed symbol.

### Test File for `detect_fenced_yaml` Tests

The 11 `TestDetectFencedYaml` tests have no migration target — `detect_fenced_yaml` is
deleted. These tests are discarded without migration. Their coverage was for a recovery path
that no longer exists.

---

## Docstring and Comment Cleanup

Beyond function-level docstrings already covered in each decision, the following locations
require updates:

**`_parse_task_directory` docstring** (`implementation_manager.py`):
The phrase "Files without YAML frontmatter are attempted with legacy parsing" becomes
inaccurate after Decision 2. Update the docstring to state that files without YAML
frontmatter are skipped (or emit a warning if that is the post-cleanup behavior).

**`parse_task_file` docstring** (`implementation_manager.py`):
Currently documents both file and directory handling. The file path (single-file content
routing through `parse_task_content`) becomes a narrower path post-cleanup. Review and
update if the description of the single-file path references multi-format detection.

**Section comment** (`implementation_manager.py` around line 613):
The `# Task Parsing (SRP: separated into focused functions)` comment references SRP.
Verify it still accurately describes the remaining functions after the FieldParser block
is removed from the same region.

---

## Architectural Constraints

### No New Abstractions

This change introduces zero new functions, classes, or modules. It is strictly subtractive.
If an implementation agent finds that inlining Decision 4's field map creates apparent
duplication (e.g., if the map is referenced in tests), the map stays inline — do not
extract it to a constant or helper.

### Behavior Preservation

The observable behavior of all live call sites is unchanged:

- `add_timestamp_to_task` produces the same output for YAML frontmatter files
- `update_task_status` produces the same output for YAML frontmatter files
- `parse_task_content` produces the same output for valid YAML frontmatter files
- `parse_task_content` still emits a WARNING and falls through on YAML parse failure

### Test Suite Must Pass After Each File Change

Changes to each file are independently verifiable. The implementation agent must run
`uv run pytest` after modifying each file (not only at the end) to catch import errors
from removed symbols before they compound across files.

The deletion order that minimizes broken-import windows:

1. `test_task_format_fenced_yaml.py` — migrate surviving tests first, then delete file
2. `task_format.py` — delete `detect_fenced_yaml` and `_FENCED_YAML_PATTERN`
3. `implementation_manager.py` — delete FieldParser cluster and dead branches (removes
   the now-broken `detect_fenced_yaml` import)
4. `task_status_hook.py` — inline field map, delete legacy functions and branches

This order ensures no test file references a symbol before the symbol's source is touched.

### No `shell=True`, No Regex Workarounds

The legacy markdown loop used hand-rolled regex (compiled inline, `task_header_pattern`).
After deletion, no new regex is introduced to replace it. If the YAML path ever needs
field-name handling beyond the inlined map in Decision 4, that is a separate feature
request with its own architecture pass.

---

## Quality Gates

The implementation agent confirms completion when all of the following pass:

- [ ] `uv run pytest` — full test suite passes with no failures
- [ ] `uv run ruff check plugins/python3-development/skills/implementation-manager/scripts/` — zero errors
- [ ] `uv run ruff format --check plugins/python3-development/skills/implementation-manager/scripts/` — no reformatting needed
- [ ] `grep -r "detect_fenced_yaml" plugins/python3-development/skills/implementation-manager/scripts/` — zero matches
- [ ] `grep -r "FIELD_PARSERS\|FieldParser\|_parse_line" plugins/python3-development/skills/implementation-manager/scripts/` — zero matches
- [ ] `grep -r "_update_legacy_timestamp\|_legacy_field_to_yaml\|_LEGACY_INSERT_AFTER_FIELDS" plugins/python3-development/skills/implementation-manager/scripts/` — zero matches
- [ ] `grep -r "_depth" plugins/python3-development/skills/implementation-manager/scripts/` — zero matches
- [ ] No `<!-- PENDING:` markers (not applicable — this is Python, not markdown; this gate is for spec completeness only)
- [ ] `parse_task_content` docstring contains no references to "legacy markdown", "fenced YAML", or "format detection"
- [ ] `add_timestamp_to_task` docstring contains no references to `_update_legacy_timestamp` or "legacy markdown"
