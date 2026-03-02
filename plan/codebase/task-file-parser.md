# SAM Task File Parser — Patterns and Architecture

**Analysis Date:** 2026-03-02
**Files Analyzed:**
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`
- `plugins/python3-development/scripts/split_task_file.py`
- `plugins/python3-development/agents/swarm-task-planner.md`
- `plugins/development-harness/agents/swarm-task-planner.md`
- `.claude/docs/TASK_FILE_FORMAT.md`

---

## 1. Format Detection and Routing

The parser uses a two-path dispatch controlled by `has_yaml_frontmatter()` in `task_format.py:66`.

### Detection Logic

`has_yaml_frontmatter()` (`task_format.py:66-92`) applies two checks in sequence:

1. Content must start with the exact string `"---\n"` (the constant `_FRONTMATTER_DELIMITER = "---\n"` at `task_format.py:48`).
2. There must be a closing `"\n---\n"` delimiter somewhere after the opening one, OR a `"\n---"` followed by nothing or a single newline (end-of-file case).

```python
def has_yaml_frontmatter(content: str) -> bool:
    if not content or not content.startswith(_FRONTMATTER_DELIMITER):
        return False
    closing_idx = content.find("\n---\n", len(_FRONTMATTER_DELIMITER))
    if closing_idx == -1:
        closing_idx = content.find("\n---", len(_FRONTMATTER_DELIMITER))
        if closing_idx == -1:
            return False
        remaining = content[closing_idx + len("\n---"):]
        if remaining and remaining != "\n":
            return False
    return True
```

**Critical boundary**: the check is `content.startswith("---\n")`. A file whose YAML block is wrapped in a fenced code block (i.e., starting with ` ```yaml ` or ```` ``` ```` followed by `---`) returns `False` from this function and falls through to legacy markdown parsing. See Section 6 for implications.

### Routing in `parse_task_content()`

`implementation_manager.py:645-693`:

```python
def parse_task_content(content: str) -> list[Task]:
    if has_yaml_frontmatter(content):
        try:
            task = parse_task_from_frontmatter(content)
        except (ValueError, TypeError):
            # Fall through to legacy parsing if YAML parsing fails
            pass
        else:
            return [task]

    # Legacy markdown path: multiple tasks with ## Task headers
    tasks: list[Task] = []
    task_header_pattern = re.compile(r"^#{2,3}\s+Task:?\s+([A-Za-z0-9.]+)[:\s-]+(.+)$")
    ...
```

The silent fallback on `(ValueError, TypeError)` means a file that starts with `---\n` but has invalid YAML will silently reparse as legacy markdown. No warning is emitted. The caller has no way to distinguish "parsed as YAML" from "fell back to legacy."

### Directory vs. Single-File Routing

`parse_task_file()` (`implementation_manager.py:696-719`) dispatches on path type before calling `parse_task_content()`:

```python
def parse_task_file(file_path: Path) -> list[Task]:
    if file_path.is_dir():
        return _parse_task_directory(file_path)
    content = file_path.read_text(encoding="utf-8")
    return parse_task_content(content)
```

`_parse_task_directory()` (`implementation_manager.py:722-748`) globs `*.md` files, parses each with `parse_task_content()`, and sorts results using natural-order key `_task_sort_key()`.

---

## 2. YAML Frontmatter Parsing Path

### `parse_yaml_frontmatter()` — `task_format.py:95-134`

Splits on `"---\n"` with `maxsplit=2`, producing three parts:

```python
parts = content.split("---\n", 2)
# parts[0] = "" (before opening delimiter)
# parts[1] = raw YAML content
# parts[2] = markdown body
```

Validates that `parts[0]` is empty (no content before first `---`). Parses `parts[1]` with `ruamel.yaml` in safe mode. Raises `ValueError` if YAML is invalid or `TypeError` if parsed value is not a dict.

### `parse_task_from_frontmatter()` — `implementation_manager.py:376-440`

Maps YAML keys to `Task` fields:

| YAML field | Task attribute | Default if absent |
|---|---|---|
| `task` (required) | `id` | raises `ValueError` |
| `title` (required) | `name` | raises `ValueError` |
| `status` (required) | `status` | raises `ValueError` |
| `agent` | `agent` | `None` |
| `dependencies` | `dependencies` | `[]` |
| `priority` | `priority` | `TaskPriority.MEDIUM` |
| `complexity` | `complexity` | `"medium"` (capitalized to `"Medium"`) |
| `started` | `started` | `None` |
| `completed` | `completed` | `None` |
| `skills` | `skills` | `[]` |

Agent values of `"none"`, `"n/a"`, `"-"`, or `""` are coerced to `None` (`implementation_manager.py:418-419`).

`_coerce_timestamp()` (`implementation_manager.py:320-334`) handles ISO timestamps that `ruamel.yaml` (safe mode) auto-parses into `datetime` objects — it calls `str()` on them.

---

## 3. Legacy Markdown Parsing Path

### `_create_empty_task_data()` — `implementation_manager.py:605-626`

Provides null defaults for all fields before any lines are parsed:

```python
return TaskData(
    id=task_id,
    name=task_name,
    status=TaskStatus.NOT_STARTED,
    dependencies=[],
    agent=None,
    priority=TaskPriority.CRITICAL,   # Note: default is CRITICAL (1), not MEDIUM (3)
    complexity="Medium",
    started=None,
    completed=None,
    skills=[],
)
```

**Note**: The YAML path defaults `priority` to `TaskPriority.MEDIUM` (`implementation_manager.py:422`), but the legacy path defaults to `TaskPriority.CRITICAL`. This is an inconsistency between the two parsing paths.

### Field Parsers (OCP Registry Pattern)

`FIELD_PARSERS` (`implementation_manager.py:588-597`) is a list of `FieldParser` instances. Each has a compiled `pattern` and a `parse()` method. `_parse_line()` iterates the registry and applies the first match.

Registered parsers and their patterns:

| Parser class | Pattern | File:line |
|---|---|---|
| `StatusParser` | `^\*\*Status\*\*:\s*(.+)$` | `implementation_manager.py:461` |
| `DependenciesParser` | `^\*\*Dependencies\*\*:\s*(.+)$` | `implementation_manager.py:473` |
| `AgentParser` | `^\*\*Agent\*\*:\s*(.+)$` | `implementation_manager.py:488` |
| `PriorityParser` | `^\*\*Priority\*\*:\s*(\d+)` | `implementation_manager.py:508` |
| `ComplexityParser` | `^\*\*Complexity\*\*:\s*(\w+)` | `implementation_manager.py:526` |
| `StartedParser` | `^\*\*Started\*\*:\s*(.+)$` | `implementation_manager.py:541` |
| `CompletedParser` | `^\*\*Completed\*\*:\s*(.+)$` | `implementation_manager.py:556` |
| `SkillsParser` | `^\*\*Skills\*\*:\s*(.+)$` | `implementation_manager.py:571` |

### Task Header Pattern

The legacy task header regex at `implementation_manager.py:678`:

```python
task_header_pattern = re.compile(r"^#{2,3}\s+Task:?\s+([A-Za-z0-9.]+)[:\s-]+(.+)$")
```

Accepts `## Task 1.1: Title`, `### Task T1: Title`, `## Task T15 - Title`, `## Task: T1 Title`. Does not accept `# Task` (h1) or `#### Task` (h4+).

---

## 4. `split_task_file.py` and its Relationship to `implementation_manager.py`

`split_task_file.py` imports directly from `implementation_manager`:

```python
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "implementation-manager" / "scripts"))
from implementation_manager import Task, parse_task_file
from task_format import has_yaml_frontmatter
```

This creates a hard import dependency: `split_task_file.py` relies on `implementation_manager.py` for all parsing and uses `has_yaml_frontmatter` only to dispatch between body-extraction strategies.

### `parse_tasks_with_body()` — `split_task_file.py:212-234`

The entry point for split operations:

```python
def parse_tasks_with_body(file_path: Path) -> list[TaskWithBody]:
    content = file_path.read_text(encoding="utf-8")
    tasks = parse_task_file(file_path)           # delegate to implementation_manager
    if not tasks:
        return []
    if has_yaml_frontmatter(content):
        return _parse_yaml_multidoc_bodies(content, tasks)
    return _parse_legacy_bodies(content, tasks)
```

The metadata and the body are extracted by separate code paths. `implementation_manager.parse_task_file()` provides `Task` objects (metadata only). The body content is re-extracted by `split_task_file.py`'s own functions.

### `_parse_yaml_multidoc_bodies()` — `split_task_file.py:151-192`

Splits on `(?:^|\n)---\n` and heuristically classifies each resulting section as YAML metadata or body content. The heuristic `_looks_like_yaml_frontmatter()` (`split_task_file.py:195-209`) checks whether at least 2 of the first 5 lines match `^[a-z_-]+\s*:`. This is a weak heuristic: a markdown body section that happens to start with 2+ colon lines would be misclassified as YAML.

Body sections are collected into a list and then paired with tasks by index position. If the count of extracted bodies does not match the count of parsed tasks, later tasks silently receive empty string bodies.

---

## 5. Validation at Format Boundaries

### What exists

- `parse_task_from_frontmatter()` validates that `task`, `title`, and `status` are present (`implementation_manager.py:406-409`).
- `parse_yaml_frontmatter()` validates that `parts[0]` is empty and that parsed YAML is a `dict`.
- The `validate` CLI command (`implementation_manager.py:1082-1141`) checks: missing `agent`, non-standard status, unknown dependency IDs, duplicate task IDs.
- `TaskPriority(int(raw_priority))` raises `ValueError` on invalid priority at parse time.

### What is missing

1. **No schema validation against `TASK_FILE_FORMAT.md`'s JSON schema.** The spec at `.claude/docs/TASK_FILE_FORMAT.md:596-619` includes `jsonschema` validation code as a design proposal, but `implementation_manager.py` does not import or use `jsonschema`. The `validate` command is a post-hoc structural check, not schema enforcement.

2. **No detection of fenced-YAML input.** If `swarm-task-planner` produces output with ` ```yaml\n---\n...\n---\n``` ` wrapping (see Section 6), `has_yaml_frontmatter()` returns `False`, the file silently falls to legacy markdown parsing, and `parse_task_content()` returns zero tasks (no `## Task` headers match). The caller receives an empty list with no error.

3. **No warning when YAML parse fails and falls back to legacy.** The silent `except (ValueError, TypeError): pass` in `parse_task_content()` (`implementation_manager.py:665-667`) discards the exception.

4. **`last_activity` / `LastActivity` is written but never parsed back.** `task_status_hook.py` writes a `last_activity` YAML field and a `**LastActivity**` legacy field, but neither `task_format.py` nor `implementation_manager.py` read these fields. `Task` has no `last_activity` attribute. The field is write-only from the parser's perspective.

5. **`blocked-by` and `parallelize-with` fields in the schema are not parsed.** `TASK_FILE_FORMAT.md:148-149` defines these optional fields. `parse_task_from_frontmatter()` ignores them. `Task` has no attributes for them. They are accepted without error (extra keys are silently dropped by `parse_yaml_frontmatter`).

6. **`accuracy-risk` field written by `swarm-task-planner` is not parsed.** Both agent templates include `accuracy-risk` in YAML frontmatter (`swarm-task-planner.md:258`). The parser ignores it.

---

## 6. Fenced YAML: The Generator/Parser Mismatch

### How the planner template instructs output

Both `swarm-task-planner` agent templates (`plugins/python3-development/agents/swarm-task-planner.md:249-265` and `plugins/development-harness/agents/swarm-task-planner.md:248-264`) contain this task structure example:

````markdown
````markdown
```yaml
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
...
---
```
````
````

The template wraps the `---` frontmatter block in a ` ```yaml ` fenced code block inside a markdown code fence. This is documentation showing the expected output format in a triple-backtick block.

### The failure path

If a model generates a task file that literally starts with:

```text
```yaml
---
task: T1
...
---
```
```

Then:

1. `has_yaml_frontmatter()` checks `content.startswith("---\n")` → `False` (content starts with ` ```yaml\n `)
2. `parse_task_content()` falls to the legacy markdown path
3. Legacy `task_header_pattern` looks for `## Task` headers → none found
4. Returns `[]` (empty list) silently

The implementation manager reports zero tasks; `get_ready_tasks()` returns empty; no agent is dispatched. The feature appears to have no tasks.

### Why this matters

The `swarm-task-planner` templates show this fenced format as the example in the "Task Structure Requirements" and "Task Prompt Export Mode" sections. An LLM reading these templates for guidance may reproduce the fence in actual output files. The parser has no recovery path for this input.

---

## 7. `get_ready_tasks()` Logic

`implementation_manager.py:949-978`:

```python
def get_ready_tasks(tasks: list[Task]) -> list[Task]:
    status_by_id: dict[str, TaskStatus] = {task.id: task.status for task in tasks}
    ready: list[Task] = []
    for task in tasks:
        if task.status != TaskStatus.NOT_STARTED:
            continue
        deps_satisfied = all(
            status_by_id.get(dep_id) == TaskStatus.COMPLETE
            for dep_id in task.dependencies
        )
        if deps_satisfied:
            ready.append(task)
    return ready
```

A task is ready when:
- `status == NOT_STARTED`
- All dependency IDs are present in `status_by_id` with value `COMPLETE`

**Edge case**: If a dependency ID is not in `status_by_id` (i.e., the dependency references a non-existent task ID), `status_by_id.get(dep_id)` returns `None`, which is not `== TaskStatus.COMPLETE`, so `deps_satisfied` becomes `False`. The task is blocked forever, silently. The `validate` command will report this as an error, but `get_ready_tasks()` does not.

---

## 8. Hook Script Format Dispatch

`task_status_hook.py` mirrors the same `has_yaml_frontmatter()` dispatch pattern:

- `update_task_status()` (`task_status_hook.py:375-421`): detects format, uses `update_yaml_field()` for YAML, regex line replacement for legacy.
- `add_timestamp_to_task()` (`task_status_hook.py:319-354`): same dispatch.
- `find_task_section()` (`task_status_hook.py:231-278`): for YAML files, returns `(0, len(lines))` if the `task` field matches (the whole file is the task section); for legacy, scans for `## Task <id>:` headers.

The hook also handles directory-based task files through `_find_yaml_task_file()` (`task_status_hook.py:202-228`), which scans `.md` files in a directory for one whose `task` frontmatter field matches the target ID.

---

## 9. Module Dependency Graph

```text
split_task_file.py
  └─ imports: implementation_manager.Task, parse_task_file
  └─ imports: task_format.has_yaml_frontmatter

task_status_hook.py
  └─ imports: task_format.has_yaml_frontmatter
  └─ imports: task_format.normalize_status
  └─ imports: task_format.parse_yaml_frontmatter
  └─ imports: task_format.update_yaml_field

implementation_manager.py
  └─ imports: task_format.VALID_STATUSES
  └─ imports: task_format.has_yaml_frontmatter
  └─ imports: task_format.normalize_status
  └─ imports: task_format.parse_yaml_frontmatter

task_format.py
  └─ imports: ruamel.yaml (safe mode)
  └─ (no local imports)
```

`task_format.py` is the foundation. Nothing in the parsing stack imports `jsonschema`. The format spec's schema validation code (`.claude/docs/TASK_FILE_FORMAT.md:596-619`) was never implemented.

---

## 10. Where to Add New Code

**New YAML frontmatter field support**: Add attribute to `Task` dataclass (`implementation_manager.py:89-115`), add extraction in `parse_task_from_frontmatter()` (`implementation_manager.py:376-440`), add `TaskDict` key (`implementation_manager.py:179-195`).

**New legacy markdown field support**: Add a new `FieldParser` subclass following the `StatusParser` pattern (`implementation_manager.py:458-470`), register it in `FIELD_PARSERS` (`implementation_manager.py:588-597`). No other changes needed (OCP pattern).

**Fenced YAML detection/recovery**: Add a pre-processing step in `parse_task_content()` (`implementation_manager.py:645`) before `has_yaml_frontmatter()` is called. Strip leading ` ```yaml\n ` and trailing ` ``` ` if present.

**Schema validation**: Add a `validate_task_frontmatter()` function to `task_format.py` using `jsonschema` (already in spec at `.claude/docs/TASK_FILE_FORMAT.md:593-619`). Call from `parse_task_from_frontmatter()` before returning the `Task`.

**Warning on YAML fallback**: Replace the silent `except (ValueError, TypeError): pass` in `parse_task_content()` (`implementation_manager.py:665-667`) with a stderr warning before falling through.

---

## 11. Key Constants and Patterns

| Constant / Pattern | Location | Value |
|---|---|---|
| `_FRONTMATTER_DELIMITER` | `task_format.py:48` | `"---\n"` |
| `TASK_ID_PATTERN` | `task_format.py:42` | `r"^[A-Za-z]?\d+(\.\d+)?$"` |
| `VALID_STATUSES` | `task_format.py:44` | `{"not-started", "in-progress", "complete", "blocked"}` |
| `VALID_COMPLEXITIES` | `task_format.py:46` | `{"low", "medium", "high"}` |
| `STATUS_MAP` | `task_format.py:28-40` | Legacy → normalized mapping, includes emoji variants |
| Legacy task header regex | `implementation_manager.py:678` | `r"^#{2,3}\s+Task:?\s+([A-Za-z0-9.]+)[:\s-]+(.+)$"` |
| Hook task ID regex | `task_status_hook.py:38` | `r"[A-Za-z0-9]+(?:[-.][\dA-Za-z]+)*"` |
| Schema task ID pattern | `TASK_FILE_FORMAT.md:272` | `"^[A-Z]?\\d+(\\.\\d+)?$"` (uppercase prefix only) |

**Note**: The hook's task ID regex (`task_status_hook.py:38`) is broader than `TASK_ID_PATTERN` in `task_format.py:42`. The hook accepts `P0-T01` (hyphen-separated). The format spec's JSON schema (`TASK_FILE_FORMAT.md:272`) accepts only uppercase letter prefix. These three patterns are not aligned.

---

_Analysis date: 2026-03-02_
