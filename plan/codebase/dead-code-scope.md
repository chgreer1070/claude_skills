# Dead Code Scope Analysis

**Analysis Date:** 2026-03-05
**Scope:** `plugins/python3-development/skills/implementation-manager/scripts/`

---

## Q1: Does `detect_fenced_yaml` have callers outside the dead fenced-YAML recovery path?

**Answer: No. Its only production caller is the dead fenced-YAML recovery branch in `parse_task_content`.**

### Production callers

`implementation_manager.py:696` — the single production call site:

```python
# implementation_manager.py lines 694–703 (inside the else branch of has_yaml_frontmatter)
stripped = detect_fenced_yaml(content)
if stripped is not None:
    sys.stderr.write("WARNING: ...")
    return parse_task_content(stripped, _depth=_depth + 1)
```

This call is reachable only when `has_yaml_frontmatter(content)` returns `False` (line 683).
That is, `detect_fenced_yaml` is called exclusively from the fenced-YAML recovery path,
which the feature context identifies as dead.

### Test callers

`test_task_format_fenced_yaml.py:30` imports `detect_fenced_yaml` directly:

```python
from task_format import detect_fenced_yaml
```

The `TestDetectFencedYaml` class (lines 60–283) exercises it in 11 unit tests.
These tests exist solely to verify the fenced-YAML recovery path.

### Import chain

`implementation_manager.py:41` imports it:

```python
from task_format import (
    VALID_STATUSES,
    detect_fenced_yaml,
    has_yaml_frontmatter,
    normalize_status,
    parse_yaml_frontmatter,
)
```

No other file in the repository imports or calls `detect_fenced_yaml` outside `scripts/`.

### `__all__` exposure

`task_format.py:68` lists `"detect_fenced_yaml"` in `__all__`. This is a declaration, not a
call site. No file outside `scripts/` imports it.

**Conclusion:** `detect_fenced_yaml` is exclusively used by the dead fenced-YAML recovery path
and its tests. Both the function in `task_format.py` and its import in `implementation_manager.py`
are safe to remove when the recovery path is deleted.

---

## Q2: Are the 8 `FieldParser` subclasses exclusively used by the dead legacy markdown loop?

**Answer: Yes. All 8 subclasses are used exclusively via `FIELD_PARSERS` → `_parse_line` → the legacy markdown loop.**

### Class definitions and registry

`implementation_manager.py:461–610`:

| Class | Line | Field parsed |
|---|---|---|
| `FieldParser` | 461 | Base class |
| `StatusParser` | 471 | `**Status**` |
| `DependenciesParser` | 486 | `**Dependencies**` |
| `AgentParser` | 501 | `**Agent**` |
| `PriorityParser` | 521 | `**Priority**` |
| `ComplexityParser` | 539 | `**Complexity**` |
| `StartedParser` | 554 | `**Started**` |
| `CompletedParser` | 569 | `**Completed**` |
| `SkillsParser` | 584 | `**Skills**` |

All 8 instances are collected into the `FIELD_PARSERS` registry at `implementation_manager.py:601–610`.

### Call chain

```
FIELD_PARSERS (line 601)
  -> _parse_line (line 642–655): iterates FIELD_PARSERS, applies first match
       -> called from legacy markdown loop (line 722):
            elif current_task:
                _parse_line(line, current_task)
```

The legacy markdown loop runs at `implementation_manager.py:715–725`:

```python
for line in content.split("\n"):
    header_match = task_header_pattern.match(line)
    if header_match:
        ...
    elif current_task:
        _parse_line(line, current_task)
```

`_parse_line` has exactly one call site (line 722). `FIELD_PARSERS` has exactly one consumer
(`_parse_line`, line 651).

### External references

No file outside `implementation_manager.py` imports `FieldParser`, `FIELD_PARSERS`, or any
of the 8 subclasses. The grep of the full repo found references only in:

- `implementation_manager.py` (definitions and usages)
- `plan/codebase/task-file-parser.md` (documentation mentioning the OCP pattern)
- `.claude/backlog/p2-dead-code-cleanup-*.md` (backlog item describing what to delete)
- `plan/feature-context-dead-code-cleanup-legacy-parser.md` (feature context)

None of those are callers.

**Conclusion:** All 8 `FieldParser` subclasses, the `FIELD_PARSERS` registry, and `_parse_line`
are exclusively used by the dead legacy markdown loop. All are safe to delete together.

---

## Q3: Does `update_task_status` have a parallel legacy fallback separate from `add_timestamp_to_task`? What does the live vs dead split look like?

**Answer: Yes. Both `update_task_status` and `add_timestamp_to_task` contain independent
YAML (live) and legacy-markdown (dead) branches.**

### `update_task_status` — `task_status_hook.py:375–421`

```python
def update_task_status(content: str, task_id: str, new_status: str) -> str:
    # --- YAML frontmatter format --- (LIVE)
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        normalized = normalize_status(new_status)
        return update_yaml_field(content, "status", normalized)

    # --- Legacy markdown format --- (DEAD)
    section = find_task_section(content, task_id)
    if section is None:
        raise ValueError(f"Task {task_id} not found in file")
    start_idx, end_idx = section
    lines = content.split("\n")
    task_lines = lines[start_idx:end_idx]
    # Find and update status line via regex
    status_pattern = r"^\*\*Status\*\*:\s*.*$"
    for i, line in enumerate(task_lines):
        if re.match(status_pattern, line):
            task_lines[i] = f"**Status**: {new_status}"
            break
    result_lines = lines[:start_idx] + task_lines + lines[end_idx:]
    return "\n".join(result_lines)
```

The legacy branch (lines 403–421) is inline regex logic. It does **not** call
`_update_legacy_timestamp` or `_legacy_field_to_yaml`. It is self-contained dead code.

### `add_timestamp_to_task` — `task_status_hook.py:319–354`

```python
def add_timestamp_to_task(content: str, task_id: str, field_name: str, timestamp: str) -> str:
    # --- YAML frontmatter format --- (LIVE)
    if has_yaml_frontmatter(content):
        section = find_task_section(content, task_id)
        if section is None:
            raise ValueError(f"Task {task_id} not found in file")
        yaml_field = _legacy_field_to_yaml(field_name)   # <-- calls dead helper
        return update_yaml_field(content, yaml_field, timestamp)

    # --- Legacy markdown format --- (DEAD)
    section = find_task_section(content, task_id)
    if section is None:
        raise ValueError(f"Task {task_id} not found in file")
    start_idx, end_idx = section
    lines = content.split("\n")
    return _update_legacy_timestamp(lines, start_idx, end_idx, field_name, timestamp)
```

**Notable:** `_legacy_field_to_yaml` is called from the **YAML (live) branch** of
`add_timestamp_to_task` (line 344), not from the legacy branch. Its purpose is to
convert a PascalCase field name (e.g., `"LastActivity"`) to a snake_case YAML key
(`"last_activity"`). This call is live.

### Live vs dead split summary

| Code | Location | Status | Notes |
|---|---|---|---|
| YAML branch of `update_task_status` | lines 396–401 | **Live** | Uses `update_yaml_field` |
| Legacy branch of `update_task_status` | lines 403–421 | **Dead** | Inline regex, no helper calls |
| YAML branch of `add_timestamp_to_task` | lines 339–345 | **Live** | Calls `_legacy_field_to_yaml` (live use) |
| Legacy branch of `add_timestamp_to_task` | lines 347–354 | **Dead** | Calls `_update_legacy_timestamp` |
| `_legacy_field_to_yaml` body | lines 357–372 | **Live** (called from YAML branch) | See Q4 |
| `_update_legacy_timestamp` | lines 285–316 | **Dead** | Called only from legacy branch |

---

## Q4: Are there callers of `_update_legacy_timestamp` or `_legacy_field_to_yaml` beyond `add_timestamp_to_task`?

### `_update_legacy_timestamp`

**Answer: No. Its only caller is the legacy markdown branch of `add_timestamp_to_task` (line 354).**

`task_status_hook.py:354`:
```python
return _update_legacy_timestamp(lines, start_idx, end_idx, field_name, timestamp)
```

The repo-wide grep found zero other references to `_update_legacy_timestamp` outside
`task_status_hook.py`. Within `task_status_hook.py`, it appears at:
- Line 285: definition
- Line 324: docstring reference (`_update_legacy_timestamp`)
- Line 354: the sole call site (inside the dead legacy branch of `add_timestamp_to_task`)

### `_legacy_field_to_yaml`

**Answer: Its only caller is `add_timestamp_to_task` (line 344) — from the YAML (live) branch.**

`task_status_hook.py:344`:
```python
yaml_field = _legacy_field_to_yaml(field_name)
return update_yaml_field(content, yaml_field, timestamp)
```

This call is inside the `if has_yaml_frontmatter(content):` block, making it a live call path.
The function converts PascalCase field names (`"LastActivity"`, `"Started"`, `"Completed"`,
`"Status"`) to their YAML snake_case equivalents (`"last_activity"`, `"started"`, etc.).

The repo-wide grep found zero other callers of `_legacy_field_to_yaml` outside
`task_status_hook.py`.

**Important implication:** `_legacy_field_to_yaml` cannot be deleted without first
inlining its mapping into `add_timestamp_to_task`'s YAML branch, or replacing it with
a direct parameter that already uses the YAML field name. The function name is misleading:
despite the `_legacy_` prefix, it serves the live YAML code path.

---

## Q5: Any files outside `scripts/` that import or call the dead code symbols?

**Answer: No files outside `scripts/` import or call any of these symbols.**

Grep results for each symbol, filtered to source files (excluding plan docs and backlog items):

| Symbol | Files with source-code references |
|---|---|
| `detect_fenced_yaml` | `scripts/task_format.py` (definition), `scripts/implementation_manager.py` (import + call), `scripts/test_task_format_fenced_yaml.py` (import + 11 test calls) |
| `FIELD_PARSERS` | `scripts/implementation_manager.py` only (definition at line 601, use at line 651) |
| `FieldParser` | `scripts/implementation_manager.py` only (base class + 8 subclasses) |
| `_update_legacy_timestamp` | `scripts/task_status_hook.py` only (definition + 1 call site) |
| `_legacy_field_to_yaml` | `scripts/task_status_hook.py` only (definition + 1 call site) |

No other `.py`, `.ts`, `.js`, or shell files in the repository reference these symbols.

---

## Summary Table

| Symbol | File | Dead? | Only caller | Safe to delete? |
|---|---|---|---|---|
| `detect_fenced_yaml` | `task_format.py:114` | Yes | `implementation_manager.py:696` (dead path) | Yes — with its import and tests |
| `_FENCED_YAML_PATTERN` | `task_format.py:109` | Yes | `detect_fenced_yaml` | Yes |
| `FieldParser` (base) | `implementation_manager.py:461` | Yes | `FIELD_PARSERS` | Yes |
| `StatusParser` | `implementation_manager.py:471` | Yes | `FIELD_PARSERS` | Yes |
| `DependenciesParser` | `implementation_manager.py:486` | Yes | `FIELD_PARSERS` | Yes |
| `AgentParser` | `implementation_manager.py:501` | Yes | `FIELD_PARSERS` | Yes |
| `PriorityParser` | `implementation_manager.py:521` | Yes | `FIELD_PARSERS` | Yes |
| `ComplexityParser` | `implementation_manager.py:539` | Yes | `FIELD_PARSERS` | Yes |
| `StartedParser` | `implementation_manager.py:554` | Yes | `FIELD_PARSERS` | Yes |
| `CompletedParser` | `implementation_manager.py:569` | Yes | `FIELD_PARSERS` | Yes |
| `SkillsParser` | `implementation_manager.py:584` | Yes | `FIELD_PARSERS` | Yes |
| `FIELD_PARSERS` | `implementation_manager.py:601` | Yes | `_parse_line` | Yes |
| `_parse_line` | `implementation_manager.py:642` | Yes | legacy loop (line 722) | Yes |
| `_LEGACY_INSERT_AFTER_FIELDS` | `task_status_hook.py:282` | Yes | `_update_legacy_timestamp` | Yes |
| `_update_legacy_timestamp` | `task_status_hook.py:285` | Yes | `add_timestamp_to_task` legacy branch (line 354) | Yes |
| `_legacy_field_to_yaml` | `task_status_hook.py:357` | **No** | `add_timestamp_to_task` YAML branch (line 344) | **No — live caller** |
| Legacy branch of `update_task_status` | `task_status_hook.py:403–421` | Yes | None (unreachable) | Yes — inline dead block |
| Legacy branch of `add_timestamp_to_task` | `task_status_hook.py:347–354` | Yes | None (unreachable) | Yes — inline dead block |
| `find_task_section` legacy branch | `task_status_hook.py:256–278` | Yes | Still called by YAML branch too (line 341, 348) | No — YAML branch uses it |

---

*Analysis sourced from direct file reads and repo-wide grep. All line numbers reference the
current state of files in `plugins/python3-development/skills/implementation-manager/scripts/`.*
