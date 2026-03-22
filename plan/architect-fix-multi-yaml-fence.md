# Architecture Spec: Fix Multi-YAML Fence Bug in SAM Task File Pipeline

**Issue**: #320
**Date**: 2026-03-02
**Status**: READY FOR IMPLEMENTATION

---

## Executive Summary

The `swarm-task-planner` agent generates task files with YAML frontmatter wrapped in ` ```yaml ` fenced code blocks. The parser (`has_yaml_frontmatter` in `task_format.py`) requires `content.startswith("---\n")`, so fenced blocks fail detection and silently fall through to legacy markdown parsing, which returns empty task lists. This spec covers a three-part fix: agent template correction, parser self-healing with warnings, and format policy documentation.

---

## Question Resolutions

Resolutions for the open questions from [feature-context-fix-multi-yaml-fence.md](./feature-context-fix-multi-yaml-fence.md):

| # | Question | Resolution | Rationale |
|---|----------|------------|-----------|
| Q1 | Migrate existing affected files? | Option C: Create a separate backlog item | Keeps this fix focused on prevention and detection; migration is a distinct operation |
| Q2 | Auto-strip or raise error? | Option B: Auto-strip and warn to stderr | Self-healing avoids blocking in-flight work; the stderr warning surfaces the root cause for upstream correction |
| Q3 | Which scripts are designated writers? | Four scripts listed in Part 3 below | The swarm-task-planner agent creates initial files but SHOULD use raw frontmatter, not fenced blocks. The policy is format enforcement, not write authorization |
| Q4 | Widen legacy header regex? | Option C: Separate issue | Header regex changes have broader implications; fenced YAML detection is the priority |
| Q5 | Multi-task files with plan-level + per-task YAML? | Option C: Separate issue | This is a parser architecture question beyond the scope of fence detection |

---

## Part 1: Agent Template Fix

### Scope

Two template locations in each of two agent files (four total edits).

### Files Modified

| File | Template Locations |
|------|-------------------|
| `plugins/python3-development/agents/swarm-task-planner.md` | Lines ~212-220 (TASK file template), Lines ~249-265 (Task Structure Requirements) |
| `plugins/development-harness/agents/swarm-task-planner.md` | Lines ~212-219 (TASK file template), Lines ~248-264 (Task Structure Requirements) |

### Change Description

Remove the ` ```yaml ` / ` ``` ` wrapper from both template blocks in both files so the YAML frontmatter is shown as raw content starting with `---`.

**Current (broken)** -- the outer `````markdown` fence shows an inner ` ```yaml ` fence wrapping the `---` delimiters:

`````markdown
````markdown
```yaml
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
---
```
````
`````

**Target (correct)** -- the outer `````markdown` fence shows raw `---` delimiters without inner fencing:

`````markdown
````markdown
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
---
````
`````

### Constraints

- The `development-harness` variant uses `role:` instead of `agent:`. This field name difference MUST be preserved.
- All other YAML fields (`accuracy-risk`, `skills`, `parallelize-with`, `reason`, `handoff`) remain unchanged.
- The enclosing `````markdown` documentation fence stays; only the inner ` ```yaml ` / ` ``` ` lines are removed.

---

## Part 2: Format Validation in Parser

### 2.1 New Function: `detect_fenced_yaml`

**Module**: [task_format.py](../plugins/python3-development/skills/implementation-manager/scripts/task_format.py)

**Purpose**: Detect whether content contains YAML frontmatter wrapped in fenced code blocks and return the stripped content if so.

**Interface**:

```python
def detect_fenced_yaml(content: str) -> str | None:
    """Detect YAML frontmatter wrapped in fenced code blocks and strip the fences.

    Recognizes patterns where ``---`` delimited YAML is wrapped inside
    a fenced code block (e.g., ```yaml ... ``` or ``` ... ```).

    Args:
        content: Raw file content to check.

    Returns:
        The content with fence markers stripped if fenced YAML was detected,
        or None if no fenced YAML pattern was found.
    """
```

**Detection logic**:

1. Check if content starts with a line matching the regex pattern `^```(?:yaml|yml)?\s*\n` (backtick fence with optional yaml/yml language tag).
2. If match found, check if the content after the fence line starts with `---\n` (the YAML frontmatter delimiter).
3. If both conditions met, strip the opening fence line and strip the closing ` ``` ` line that terminates the fenced block.
4. Handle both single-task files (one fenced block wrapping one `---` block) and multi-task files where each task section has its own fenced block.
5. Return the stripped content, or `None` if the pattern was not detected.

**Edge cases to handle**:

- Content starting with ` ```yaml\n---\n ` (standard case)
- Content starting with ` ```yml\n---\n ` (alternate language tag)
- Content starting with ` ```\n---\n ` (no language tag)
- Whitespace before the opening fence (strip leading whitespace before checking)
- Multiple fenced YAML blocks in a single file (multi-task embedded case as in `tasks-4-validate-orchestrator-discipline.md`)
- Fenced blocks that do NOT contain `---` delimiters (should return `None` -- these are regular code blocks, not frontmatter)

**Multi-task stripping strategy for embedded fenced blocks**:

For files where individual task sections each have their own ` ```yaml ` / ` ``` ` wrapper around `---` blocks (as seen in `tasks-4-validate-orchestrator-discipline.md`), use a regex substitution pattern to strip all fence pairs that immediately surround `---` delimiters. The regex pattern:

```text
^```(?:yaml|yml)?\s*\n(---\n[\s\S]*?\n---)\n```\s*$
```

This matches a fence-open line, captures the `---`-delimited block, and matches the fence-close line. Replace with just the captured group (the raw frontmatter).

### 2.2 Modified Function: `parse_task_content`

**Module**: [implementation_manager.py](../plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py)

**Current behavior** (lines 645-693): Calls `has_yaml_frontmatter(content)`. If true, attempts YAML parse. On `(ValueError, TypeError)`, silently falls through to legacy parsing. Returns empty list if legacy parsing also finds nothing.

**Modified behavior**:

```text
1. Call has_yaml_frontmatter(content).
2. If True:
   a. Try parse_task_from_frontmatter(content).
   b. On success: return [task].
   c. On (ValueError, TypeError): emit WARNING to stderr with exception message,
      then fall through to legacy parsing.
3. If False:
   a. Call detect_fenced_yaml(content).
   b. If detect_fenced_yaml returns stripped content (not None):
      i.   Emit WARNING to stderr:
           "Task file contains YAML frontmatter wrapped in code fences (```yaml).
            Stripping fences and re-parsing. Fix the generator to produce raw
            frontmatter starting with --- instead of fenced blocks."
      ii.  Recurse: return parse_task_content(stripped_content).
   c. If detect_fenced_yaml returns None:
      Continue to legacy markdown parsing (existing behavior).
4. Legacy markdown parsing (unchanged).
5. If legacy parsing returns empty list: no change (caller handles empty results).
```

**Interface change**: None. `parse_task_content(content: str) -> list[Task]` signature is unchanged.

**Warning output**: Use `sys.stderr.write()` or `warnings.warn()` -- NOT `logging` (the module does not currently use the logging module and adding it is out of scope). The warning MUST go to stderr so it is visible in CI/CD output and terminal but does not pollute stdout JSON output from `implementation_manager.py` CLI commands.

**Import addition**: Add `detect_fenced_yaml` to the import from `task_format`:

```python
from task_format import VALID_STATUSES, detect_fenced_yaml, has_yaml_frontmatter, normalize_status, parse_yaml_frontmatter
```

### 2.3 Export Update: `task_format.py`

Add `detect_fenced_yaml` to the `__all__` list in [task_format.py](../plugins/python3-development/skills/implementation-manager/scripts/task_format.py).

### 2.4 Silent Fallthrough Fix

**Current code** (implementation_manager.py lines 665-667):

```python
except (ValueError, TypeError):
    # Fall through to legacy parsing if YAML parsing fails
    pass
```

**Required change**: Replace `pass` with a stderr warning that includes the exception message. The warning must state what happened (YAML frontmatter was detected but parsing failed) and what will happen next (falling through to legacy parsing).

**Warning format**:

```text
WARNING: YAML frontmatter detected but parsing failed: {exception_message}. Falling through to legacy markdown parsing.
```

### 2.5 Data Flow Diagram

```text
parse_task_content(content)
    |
    +-- has_yaml_frontmatter(content)?
    |   |
    |   +-- YES --> parse_task_from_frontmatter(content)
    |   |           |
    |   |           +-- Success --> return [task]
    |   |           |
    |   |           +-- ValueError/TypeError --> WARN to stderr --> fall through
    |   |
    |   +-- NO --> detect_fenced_yaml(content)?
    |              |
    |              +-- Returns stripped content --> WARN to stderr
    |              |                               --> parse_task_content(stripped)  [recurse]
    |              |
    |              +-- Returns None --> continue to legacy parsing
    |
    +-- Legacy markdown parsing (## Task headers)
    |   |
    |   +-- Returns tasks list (may be empty)
```

### 2.6 Recursion Safety

The recursion in step 3.b.ii has a natural termination: after `detect_fenced_yaml` strips the fences, the stripped content will either:

- Start with `---\n` (detected by `has_yaml_frontmatter`, takes path 2a)
- Not start with `---\n` and not match the fenced pattern again (takes path 3c to legacy parsing)

The function cannot recurse infinitely because `detect_fenced_yaml` only strips fence markers and does not add them. A second call to `detect_fenced_yaml` on already-stripped content returns `None`.

However, as a defensive measure, the implementation SHOULD add a `_depth` parameter defaulting to 0 and guard against `_depth > 1` (return empty list with a warning). This prevents infinite recursion if a pathological input somehow triggers repeated stripping.

---

## Part 3: Script-Only Writes Policy Documentation

### File Modified

[TASK_FILE_FORMAT.md](../plugins/development-harness/docs/TASK_FILE_FORMAT.md)

### Content to Add

Add a new section `## Authorized Writers` after the existing `## Format Specification` section (before `## Markdown Body Sections`). The section documents:

1. **Designated writer scripts**: The four scripts authorized to write task data files:

   | Script | Purpose | Path |
   |--------|---------|------|
   | `implementation_manager.py` | Status field updates via `update_yaml_field` | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` |
   | `task_status_hook.py` | Timestamp and status updates from hooks | `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` |
   | `split_task_file.py` | Splits monolithic task files into per-task files | `plugins/python3-development/scripts/split_task_file.py` |
   | `migrate_task_format.py` | Converts legacy markdown to YAML frontmatter | `plugins/python3-development/scripts/migrate_task_format.py` |

2. **Policy statement**: Task data files MUST contain raw YAML frontmatter starting with `---`. Agents generating task files SHOULD produce content matching this format directly. When the generator is an LLM agent (e.g., `swarm-task-planner`), the agent's template MUST show raw frontmatter without code fence wrappers.

3. **Anti-pattern example**: Show the fenced YAML pattern that causes parser failure, with an explanation of why it fails.

**Anti-pattern to document**:

`````markdown
### Anti-Pattern: Fenced YAML Frontmatter

Do NOT wrap YAML frontmatter in fenced code blocks. The parser requires content to start with `---` on the first line.

**Wrong** (parser cannot detect frontmatter):

````text
```yaml
---
task: T1
title: Example Task
status: not-started
---
```
````

**Correct** (parser detects and parses frontmatter):

```text
---
task: T1
title: Example Task
status: not-started
---
```

The `detect_fenced_yaml()` function in `task_format.py` will auto-strip fences and emit a warning, but this is a fallback -- the generator should produce correct output.
`````

---

## Compatibility and Migration

### Existing File Compatibility

| File Type | Before Fix | After Fix |
|-----------|-----------|-----------|
| Raw YAML frontmatter (starts with `---`) | Parsed correctly | Parsed correctly (no change) |
| Legacy markdown (`## Task` headers) | Parsed correctly | Parsed correctly (no change) |
| Fenced YAML (starts with ` ```yaml\n--- `) | Silent failure, empty task list | Auto-stripped, parsed with warning |
| Mixed: plan-level YAML + fenced per-task YAML | Silent failure | Auto-stripped per-task fences, parsed with warning |
| Directory of `.md` files | Each file parsed via `parse_task_content` | Each file benefits from fence detection |

### Consumer Compatibility

| Consumer | Import | Impact |
|----------|--------|--------|
| `implementation_manager.py` | `from task_format import has_yaml_frontmatter` | Adds import of `detect_fenced_yaml`; behavior change in `parse_task_content` |
| `task_status_hook.py` | `from task_format import has_yaml_frontmatter` | No change required. The hook calls `has_yaml_frontmatter` to decide update strategy. Fenced YAML files will still return `False` from `has_yaml_frontmatter`, but the hook only writes to files that already have valid frontmatter (it does not create task files). If the hook encounters a fenced file, it will use the legacy update path, which is acceptable because the hook only appends/updates fields |
| `split_task_file.py` | `from task_format import has_yaml_frontmatter` | No change required. The split script calls `parse_task_file` (which calls `parse_task_content`) for metadata extraction. The fence stripping in `parse_task_content` means fenced files will now produce `Task` objects instead of empty lists. The split script's body extraction (`_parse_yaml_multidoc_bodies`) calls `has_yaml_frontmatter` separately, which will still return `False` for fenced content. This means body extraction falls to `_parse_legacy_bodies`. This is an imperfect match but acceptable for now -- full fix is a separate concern |

### Behavioral Change Summary

| Behavior | Before | After |
|----------|--------|-------|
| Fenced YAML in `parse_task_content` | Silent empty list | Stripped, parsed, warning emitted |
| YAML parse failure in `parse_task_content` | Silent fallthrough | Warning emitted, then fallthrough |
| `has_yaml_frontmatter` | Unchanged | Unchanged (no modification) |
| `detect_fenced_yaml` | Does not exist | New function in `task_format.py` |

---

## Error Handling

### Error Scenarios

| Scenario | Detection | Response |
|----------|-----------|----------|
| Content starts with ` ```yaml\n---\n ` | `detect_fenced_yaml` returns stripped content | Warning to stderr, recurse with stripped content |
| Content starts with ` ```yaml\n ` but no `---` inside | `detect_fenced_yaml` returns `None` | Falls through to legacy parsing |
| Valid YAML frontmatter but missing required fields (`task`, `title`, `status`) | `parse_task_from_frontmatter` raises `ValueError` | Warning to stderr with field name, falls through to legacy |
| YAML syntax error inside frontmatter | `parse_yaml_frontmatter` raises `ValueError` (from `YAMLError`) | Warning to stderr with YAML error details, falls through to legacy |
| Completely empty content | `has_yaml_frontmatter` returns `False`, `detect_fenced_yaml` returns `None` | Returns empty list (legacy parsing finds nothing) |
| Malformed fence (e.g., ` ````yaml ` with 4 backticks) | `detect_fenced_yaml` regex does not match 4+ backticks | Falls through to legacy parsing (correct behavior -- 4-backtick fences are documentation, not generated output) |

### Warning Format

All warnings use a consistent format:

```text
WARNING: [description of what was detected]. [action being taken]. [remediation advice].
```

Warnings go to stderr via `sys.stderr.write(f"WARNING: ...\n")`.

---

## Testing Strategy

### Unit Tests for `detect_fenced_yaml`

**Test file**: New test file or added to existing test module for `task_format.py`.

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Standard fenced YAML | ` ```yaml\n---\ntask: T1\n---\n``` ` | Stripped content: `---\ntask: T1\n---\n` |
| Fenced with `yml` tag | ` ```yml\n---\ntask: T1\n---\n``` ` | Stripped content |
| Fenced without language tag | ` ```\n---\ntask: T1\n---\n``` ` | Stripped content |
| Leading whitespace before fence | `  ```yaml\n---\ntask: T1\n---\n``` ` | Stripped content (after leading whitespace handling) |
| No fence, raw frontmatter | `---\ntask: T1\n---\n` | `None` (not fenced) |
| Legacy markdown (no frontmatter) | `## Task T1: Title\n**Status**: ...` | `None` (not fenced) |
| Fenced block without `---` inside | ` ```yaml\nkey: value\n``` ` | `None` (fence present but no frontmatter delimiters) |
| Multiple fenced blocks (multi-task) | Content with 3 separate ` ```yaml\n---...---\n``` ` blocks | All three blocks stripped |
| Four-backtick fence (documentation) | ` ````yaml\n---\ntask: T1\n---\n```` ` | `None` (not a 3-backtick fence) |
| Empty content | `""` | `None` |
| Fence with trailing content after close | ` ```yaml\n---\ntask: T1\n---\n```\nMore text\n` | Stripped content preserves "More text" section |

### Integration Tests for `parse_task_content` with Fenced Input

| Test Case | Input | Expected Behavior |
|-----------|-------|-------------------|
| Fenced single task | Fenced YAML with complete task metadata | Returns `[Task]` with correct fields; warning on stderr |
| Fenced multi-task file | Plan-level YAML + fenced per-task YAML blocks | Stripped fences, tasks parsed; warnings on stderr |
| Existing raw YAML (regression) | Standard `---` delimited frontmatter | Returns `[Task]` with no warnings (unchanged behavior) |
| Existing legacy markdown (regression) | `## Task T1: Title` with `**Status**:` fields | Returns tasks with correct fields (unchanged behavior) |
| YAML parse failure with warning | Valid frontmatter delimiters, invalid YAML syntax | Warning on stderr, falls through to legacy |
| Fenced with missing required field | Fenced YAML without `task:` field | Warning from fence stripping, then warning from YAML parse failure, then legacy |

### Test for Warning Output

Tests MUST capture stderr and assert that warning messages are present. Use `capsys` (pytest) or redirect `sys.stderr` to a `StringIO` to capture warnings.

### Test File Location

Tests should be added alongside existing tests for the implementation manager scripts. Verify the current test file location:

```text
plugins/python3-development/skills/implementation-manager/scripts/
```

If no test file exists, create one following the project's test conventions.

### Regression Test Data

Use the actual content from [plan/tasks-4-validate-orchestrator-discipline.md](./tasks-4-validate-orchestrator-discipline.md) lines 265-279 as a regression test fixture. This real-world example exercises the fenced YAML pattern with additional fields (`accuracy-risk`, `parallelize-with`, `reason`, `handoff`) that the parser does not currently extract.

---

## Module Dependency Graph (After Change)

```text
split_task_file.py
  +-- imports: implementation_manager.Task, parse_task_file
  +-- imports: task_format.has_yaml_frontmatter

task_status_hook.py
  +-- imports: task_format.has_yaml_frontmatter
  +-- imports: task_format.normalize_status
  +-- imports: task_format.parse_yaml_frontmatter
  +-- imports: task_format.update_yaml_field

implementation_manager.py
  +-- imports: task_format.VALID_STATUSES
  +-- imports: task_format.detect_fenced_yaml       <-- NEW
  +-- imports: task_format.has_yaml_frontmatter
  +-- imports: task_format.normalize_status
  +-- imports: task_format.parse_yaml_frontmatter

task_format.py  (foundation module)
  +-- imports: ruamel.yaml (safe mode)
  +-- exports: detect_fenced_yaml                   <-- NEW
  +-- exports: has_yaml_frontmatter
  +-- exports: normalize_status
  +-- exports: parse_yaml_frontmatter
  +-- exports: update_yaml_field
```

No new external dependencies. `detect_fenced_yaml` uses `re` (already imported in `task_format.py`).

---

## Implementation Task Breakdown

| Task | Description | Files | Dependencies |
|------|-------------|-------|--------------|
| T1 | Remove ` ```yaml ` / ` ``` ` wrappers from both template locations in `python3-development` swarm-task-planner | `plugins/python3-development/agents/swarm-task-planner.md` | None |
| T2 | Remove ` ```yaml ` / ` ``` ` wrappers from both template locations in `development-harness` swarm-task-planner | `plugins/development-harness/agents/swarm-task-planner.md` | None |
| T3 | Implement `detect_fenced_yaml()` in `task_format.py` and add to `__all__` | `task_format.py` | None |
| T4 | Modify `parse_task_content()` to call `detect_fenced_yaml`, add stderr warnings, fix silent fallthrough | `implementation_manager.py` | T3 |
| T5 | Write unit tests for `detect_fenced_yaml` and integration tests for `parse_task_content` with fenced input | Test file(s) | T3, T4 |
| T6 | Add "Authorized Writers" section and anti-pattern example to `TASK_FILE_FORMAT.md` | `plugins/development-harness/docs/TASK_FILE_FORMAT.md` | None |

Tasks T1, T2, T3, and T6 can run in parallel. T4 depends on T3. T5 depends on T3 and T4.

---

## References

- [Feature context](./feature-context-fix-multi-yaml-fence.md) -- discovery research and gap analysis
- [Codebase analysis](./codebase/task-file-parser.md) -- parser architecture and code references
- [Task File Format spec](../plugins/development-harness/docs/TASK_FILE_FORMAT.md) -- format specification and schema
- [task_format.py](../plugins/python3-development/skills/implementation-manager/scripts/task_format.py) -- source: frontmatter detection and parsing
- [implementation_manager.py](../plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py) -- source: `parse_task_content` at line 645
- [swarm-task-planner (python3-development)](../plugins/python3-development/agents/swarm-task-planner.md) -- agent template with fenced YAML
- [swarm-task-planner (development-harness)](../plugins/development-harness/agents/swarm-task-planner.md) -- agent template with fenced YAML
- [tasks-4-validate-orchestrator-discipline.md](./tasks-4-validate-orchestrator-discipline.md) -- real-world affected file
