---
version: "1.0"
description: "Fix multi-YAML fence bug in SAM task file pipeline (Issue #320)"
issue: 320
tasks:
  - T1: Add detect_fenced_yaml to task_format.py
  - T2: Modify parse_task_content and fix silent fallthrough in implementation_manager.py
  - T3: Fix swarm-task-planner templates in both plugin locations
  - T4: Unit and integration tests for detect_fenced_yaml and parse_task_content
  - T5: Add Authorized Writers section and anti-pattern example to TASK_FILE_FORMAT.md
  - T6: End-to-end validation with real affected file
task_exports:
  enabled: false
  directory: TASK
---

## Context Manifest

This plan fixes the `swarm-task-planner` agent generating unparseable task files by wrapping YAML
frontmatter in fenced code blocks. The parser (`has_yaml_frontmatter`) requires
`content.startswith("---\n")`; fenced content silently falls through to legacy parsing returning
empty task lists.

Three-part fix: (1) agent template correction, (2) parser self-healing with stderr warnings,
(3) format policy documentation.

Primary sources:

- Architecture spec: `plan/architect-fix-multi-yaml-fence.md`
- Codebase analysis: `plan/codebase/task-file-parser.md`
- Parser source: `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
- Parser source: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- Format spec: `.claude/docs/TASK_FILE_FORMAT.md`
- Affected real file: `plan/tasks-4-validate-orchestrator-discipline.md`

### Same-File Merge Notes

The suggested task breakdown included separate tasks for unit tests (detect_fenced_yaml) and
integration tests (parse_task_content with fenced input). Both write to the same new test file.
They are merged into T4 to prevent edit conflicts.

The architecture spec's T1 and T2 (fix python3-development and development-harness templates
separately) are merged into T3 because they edit different files with no conflict and are
symmetrical edits of the same type. Merging reduces agent launch overhead.

---

## Priority 1 — Foundational (no dependencies, fully parallel)

Tasks T1, T3, and T5 have no dependencies and write to non-overlapping files. All three can
execute concurrently.

---

```yaml
---
task: T1
title: Add detect_fenced_yaml to task_format.py
status: not-started
agent: python-cli-architect
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
parallelize-with:
  - T3
  - T5
reason: T1, T3, T5 write to different files with no overlap
skills:
  - python3-development
handoff: >
  Report: function signature confirmed, __all__ updated, re import verified,
  test cases listed in acceptance criteria pass when run manually against the
  function in isolation.
---
```

### Context

`task_format.py` is the foundation module imported by `implementation_manager.py`,
`task_status_hook.py`, and `split_task_file.py`. It currently exports `has_yaml_frontmatter`,
`parse_yaml_frontmatter`, `normalize_status`, `update_yaml_field`, and `VALID_STATUSES`.

This task adds `detect_fenced_yaml` — a new function that strips fenced code block wrappers from
YAML frontmatter so the parser can recover from the output of the broken `swarm-task-planner`
template.

Architecture spec primary reference: `plan/architect-fix-multi-yaml-fence.md` sections 2.1, 2.3.
Codebase reference: `plan/codebase/task-file-parser.md` sections 1, 5, 6.

### Objective

Implement `detect_fenced_yaml(content: str) -> str | None` in `task_format.py` and add it to
`__all__`, so callers can detect and strip fenced YAML wrappers before passing content to the
existing YAML parsing path.

### Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — file to
  modify; read it before editing
- `plan/architect-fix-multi-yaml-fence.md` sections 2.1, 2.3 — exact interface and detection
  logic
- `plan/codebase/task-file-parser.md` section 6 — concrete example of fenced YAML input

### Requirements

1. Add `detect_fenced_yaml(content: str) -> str | None` to `task_format.py` with the exact
   docstring specified in the architecture spec (section 2.1).
2. Detection logic (from architecture spec 2.1):
   a. Strip leading whitespace from `content` before checking the opening fence.
   b. Check if the content (after leading whitespace strip) starts with a line matching
      `^```(?:yaml|yml)?\s*\n` (3-backtick fence, optional yaml/yml tag).
   c. If the opening fence matches, check if the next line starts with `---\n`.
   d. If both conditions are true, use the multiline regex substitution pattern from the
      architecture spec (section 2.1) to strip all fence pairs that immediately surround
      `---` delimiters:
      Pattern: `^```(?:yaml|yml)?\s*\n(---\n[\s\S]*?\n---)\n```\s*$`
      with `re.MULTILINE` flag.
   e. Return the stripped content if any substitution was made; return `None` otherwise.
3. Handle all edge cases from architecture spec section 2.1:
   - ` ```yaml\n---\n` (standard)
   - ` ```yml\n---\n` (alternate tag)
   - ` ```\n---\n` (no tag)
   - Leading whitespace before fence
   - Multiple fenced blocks (multi-task file)
   - Fenced block without `---` inside (return `None`)
   - Four-backtick fence — regex must NOT match 4+ backtick fences (use `^```(?!`)`)
4. Add `detect_fenced_yaml` to the `__all__` list in `task_format.py`.
5. Confirm `import re` is already present; do not add a duplicate import.

### Constraints

- Do not modify `has_yaml_frontmatter`, `parse_yaml_frontmatter`, or any existing function.
- Do not add new external dependencies; `re` is already imported.
- Do not add a `logging` import; this module does not use logging.
- The function must be pure (no side effects, no I/O, no stderr writes); callers emit warnings.
- Four-backtick fences (documentation fences) must return `None` — they are not generated output.

### Expected Outputs

- Modified file: `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
  - New function `detect_fenced_yaml` added
  - `__all__` updated to include `"detect_fenced_yaml"`

### Acceptance Criteria

1. `detect_fenced_yaml` exists in `task_format.py` and is listed in `__all__`.
2. Called with ` ```yaml\n---\ntask: T1\ntitle: X\nstatus: not-started\n---\n``` `, it returns
   `---\ntask: T1\ntitle: X\nstatus: not-started\n---\n` (fence lines stripped).
3. Called with `---\ntask: T1\ntitle: X\nstatus: not-started\n---\n` (raw frontmatter), it
   returns `None`.
4. Called with ` ```yaml\nkey: value\n``` ` (fence without `---` inside), it returns `None`.
5. Called with ` ````yaml\n---\ntask: T1\n---\n```` ` (4-backtick fence), it returns `None`.
6. Called with content containing 3 separate ` ```yaml\n---...---\n``` ` blocks (multi-task),
   it returns content with all three fence pairs stripped.
7. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
   exits 0 with no linting errors.

### Verification Steps

1. Read `task_format.py` after edit to confirm `detect_fenced_yaml` is present and `__all__`
   is updated.
2. Run the following inline test to verify basic detection:

```bash
uv run python3 -c "
import sys
sys.path.insert(0, 'plugins/python3-development/skills/implementation-manager/scripts')
from task_format import detect_fenced_yaml

# Case 1: standard fenced YAML
result = detect_fenced_yaml('\`\`\`yaml\n---\ntask: T1\ntitle: X\nstatus: not-started\n---\n\`\`\`\n')
assert result is not None, 'Expected stripped content, got None'
assert result.startswith('---\n'), f'Expected --- start, got: {result[:20]!r}'
print('PASS: standard fenced YAML stripped')

# Case 2: raw frontmatter returns None
result2 = detect_fenced_yaml('---\ntask: T1\ntitle: X\nstatus: not-started\n---\n')
assert result2 is None, f'Expected None for raw frontmatter, got: {result2!r}'
print('PASS: raw frontmatter returns None')

# Case 3: fenced block without --- returns None
result3 = detect_fenced_yaml('\`\`\`yaml\nkey: value\n\`\`\`\n')
assert result3 is None, f'Expected None for no --- inside fence, got: {result3!r}'
print('PASS: fenced block without --- returns None')

print('All inline checks passed')
"
```

3. Run linting:

```bash
uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/task_format.py
```

### CoVe Checks

Key claims to verify:

- The regex pattern `^` \`\`\`` (?:yaml|yml)?\s*\n` with `re.MULTILINE` matches only 3-backtick fences.
- Four-backtick fences produce a different match — confirm the negative lookahead `(?!`)` works.

Verification questions:

1. Does `re.match(r"^```(?:yaml|yml)?\s*\n", "````yaml\n---\n")` return `None` in Python?
2. Does the multiline substitution preserve content between `---` delimiters exactly?

Evidence to collect:

- Run both regex patterns via `uv run python3 -c` and observe match results before writing code.

Revision rule: If the regex matches 4-backtick fences or strips content between delimiters, revise
the pattern and document what changed.

### Handoff

Return:

- Confirmation that `detect_fenced_yaml` is in `task_format.py` and in `__all__`
- Output of inline verification commands (pass/fail)
- Linting exit code
- Any edge cases not covered by the specified logic

---

## Priority 2 — Depends on T1

Tasks T2 and T3 can start once T1 is complete. T2 and T3 are independent of each other and can
run concurrently.

---

```yaml
---
task: T2
title: Modify parse_task_content and fix silent fallthrough in implementation_manager.py
status: not-started
agent: python-cli-architect
dependencies:
  - T1
priority: 2
complexity: medium
accuracy-risk: medium
parallelize-with:
  - T3
reason: T2 and T3 write to different files (implementation_manager.py vs agent template files)
skills:
  - python3-development
handoff: >
  Report: modified function shown (relevant lines), import line verified, stderr warning
  format matches spec exactly, recursion depth guard present, linting passes.
---
```

### Context

`parse_task_content` in `implementation_manager.py` (lines 645-693) currently has two problems:
(1) it silently swallows `(ValueError, TypeError)` when YAML parsing fails, falling through to
legacy parsing with no warning; (2) it has no path for fenced YAML content, returning an empty
list when the swarm-task-planner generates fenced output.

This task wires in `detect_fenced_yaml` (added by T1) and replaces the silent exception swallow
with stderr warnings.

Architecture spec primary reference: `plan/architect-fix-multi-yaml-fence.md` sections 2.2, 2.4,
2.5, 2.6.
Codebase reference: `plan/codebase/task-file-parser.md` section 1 (routing), section 5 (gaps).

### Objective

Modify `parse_task_content` in `implementation_manager.py` to: call `detect_fenced_yaml` when
`has_yaml_frontmatter` returns `False`, emit stderr warnings on fenced YAML detection and on YAML
parse failure, and add a recursion depth guard, so fenced task files are auto-recovered instead
of silently returning empty lists.

### Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
  — file to modify; read lines 645-693 before editing
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — confirm
  `detect_fenced_yaml` was added by T1 before importing it
- `plan/architect-fix-multi-yaml-fence.md` sections 2.2, 2.4, 2.5, 2.6 — exact pseudocode,
  warning message formats, and recursion safety requirements

### Requirements

1. Add `detect_fenced_yaml` to the import from `task_format` at the top of
   `implementation_manager.py`. The import line after this change must be:

```python
from task_format import VALID_STATUSES, detect_fenced_yaml, has_yaml_frontmatter, normalize_status, parse_yaml_frontmatter
```

2. Modify `parse_task_content` to accept an optional `_depth: int = 0` parameter (not exposed
   in the public interface — callers always use the default).
3. Add recursion guard: if `_depth > 1`, emit a warning to `sys.stderr` and return `[]`.
4. Implement the modified control flow from architecture spec section 2.2:

```text
1. Call has_yaml_frontmatter(content).
2. If True:
   a. Try parse_task_from_frontmatter(content).
   b. On success: return [task].
   c. On (ValueError, TypeError): emit WARNING to stderr, then fall through.
3. If False:
   a. Call detect_fenced_yaml(content).
   b. If returns stripped content (not None):
      i.  Emit WARNING to stderr (fenced YAML detected).
      ii. Recurse: return parse_task_content(stripped_content, _depth=_depth+1).
   c. If returns None: continue to legacy markdown parsing.
4. Legacy markdown parsing (unchanged).
```

5. Warning for YAML parse failure (replaces silent `pass` at current lines 665-667):

```text
WARNING: YAML frontmatter detected but parsing failed: {exception_message}. Falling through to legacy markdown parsing.
```

6. Warning for fenced YAML detection:

```text
WARNING: Task file contains YAML frontmatter wrapped in code fences (```yaml). Stripping fences and re-parsing. Fix the generator to produce raw frontmatter starting with --- instead of fenced blocks.
```

7. All warnings must use `sys.stderr.write(f"WARNING: ...\n")`. Do not use `print()`,
   `logging`, or `warnings.warn()`.
8. Confirm `import sys` is already in the file; do not add a duplicate import.

### Constraints

- The public signature `parse_task_content(content: str) -> list[Task]` must remain unchanged
  for external callers; `_depth` is an internal parameter.
- Do not modify `_parse_task_directory`, `parse_task_file`, or any other function.
- Do not add new external dependencies.
- Legacy markdown parsing (the `## Task` header loop) must remain unchanged.
- Warning text must match the exact format in the architecture spec (section 2.2 and 2.4) so
  tests can assert on the exact message.

### Expected Outputs

- Modified file: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
  - Import line updated to include `detect_fenced_yaml`
  - `parse_task_content` modified with recursion guard, fenced detection, and stderr warnings

### Acceptance Criteria

1. The import line for `task_format` in `implementation_manager.py` includes `detect_fenced_yaml`.
2. `parse_task_content` called with fenced YAML content emits a WARNING to stderr and returns
   a non-empty list of `Task` objects with correct field values.
3. `parse_task_content` called with content that has valid `---` delimiters but invalid YAML
   inside emits a WARNING containing "YAML frontmatter detected but parsing failed" to stderr
   and falls through to legacy parsing.
4. `parse_task_content` called with raw `---` frontmatter (no fences) returns `[Task]` with no
   warnings emitted (unchanged regression behavior).
5. `parse_task_content` called with legacy `## Task` markdown returns tasks with no warnings
   emitted (unchanged regression behavior).
6. The `_depth > 1` guard causes `parse_task_content` to return `[]` and emit a recursion
   depth warning when called with `_depth=2`.
7. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
   exits 0.

### Verification Steps

1. Read `implementation_manager.py` lines 640-700 after edit to confirm the modified control
   flow matches the spec pseudocode.
2. Run the inline import test to confirm `detect_fenced_yaml` is importable:

```bash
uv run python3 -c "
import sys
sys.path.insert(0, 'plugins/python3-development/skills/implementation-manager/scripts')
from implementation_manager import parse_task_content
print('Import OK')
"
```

3. Run the fenced YAML recovery test:

```bash
uv run python3 -c "
import sys, io
sys.path.insert(0, 'plugins/python3-development/skills/implementation-manager/scripts')
from implementation_manager import parse_task_content

fenced_content = '\`\`\`yaml\n---\ntask: T1\ntitle: Example Task\nstatus: not-started\nagent: python-cli-architect\n---\n\`\`\`\n\n## Context\nTest task body.\n'

# Capture stderr
old_stderr = sys.stderr
sys.stderr = buf = io.StringIO()
tasks = parse_task_content(fenced_content)
sys.stderr = old_stderr

stderr_out = buf.getvalue()
assert len(tasks) == 1, f'Expected 1 task, got {len(tasks)}'
assert tasks[0].id == 'T1', f'Expected T1, got {tasks[0].id!r}'
assert 'WARNING' in stderr_out, f'Expected WARNING in stderr, got: {stderr_out!r}'
print(f'PASS: fenced YAML recovered, task={tasks[0].id}, warning emitted')
print(f'stderr: {stderr_out.strip()}')
"
```

4. Run linting:

```bash
uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py
```

### CoVe Checks

Key claims to verify:

- `sys.stderr` is already imported in `implementation_manager.py` (confirmed by reading file
  before editing).
- The recursion call `parse_task_content(stripped_content, _depth=_depth+1)` is valid Python
  given the signature change.

Verification questions:

1. Does `implementation_manager.py` already import `sys`? Read the imports section before adding.
2. After the signature change, are there any other call sites of `parse_task_content` in the
   file that pass positional arguments that would break?

Evidence to collect:

- Read `implementation_manager.py` imports block and all call sites of `parse_task_content`
  before making changes.

Revision rule: If `sys` is not imported, add it. If other call sites exist with positional args,
update them or verify the default `_depth=0` is safe.

### Handoff

Return:

- Output of inline verification commands (pass/fail for each)
- The modified `parse_task_content` function signature and first 30 lines (to confirm control flow)
- Linting exit code
- Any call sites of `parse_task_content` found and how they were handled

---

```yaml
---
task: T3
title: Fix swarm-task-planner templates in both plugin locations
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 2
complexity: low
accuracy-risk: low
parallelize-with:
  - T2
reason: T3 writes to agent template files; T2 writes to implementation_manager.py; no overlap
skills: []
handoff: >
  Report: exact lines changed in each file, before/after diff for both template locations
  in both files, linting passes for both files.
---
```

### Context

Two swarm-task-planner agent files each contain two template locations that show YAML frontmatter
wrapped in fenced code blocks. When an LLM reads these templates and generates a task file, it
reproduces the fenced structure. The parser then silently fails to parse the file.

Files to edit:

- `plugins/python3-development/agents/swarm-task-planner.md` lines ~212-220 (TASK file
  template) and lines ~249-265 (Task Structure Requirements)
- `plugins/development-harness/agents/swarm-task-planner.md` lines ~212-219 (TASK file
  template) and lines ~248-264 (Task Structure Requirements)

Architecture spec primary reference: `plan/architect-fix-multi-yaml-fence.md` Part 1.

### Objective

Remove the ` ```yaml ` / ` ``` ` wrapper from both template blocks in both agent files so the
YAML frontmatter is shown as raw content starting with `---`, and the agent no longer instructs
LLMs to generate fenced output.

### Required Inputs

- `plugins/python3-development/agents/swarm-task-planner.md` — read before editing; locate both
  template blocks (around lines 212-220 and 249-265)
- `plugins/development-harness/agents/swarm-task-planner.md` — read before editing; locate both
  template blocks (around lines 212-219 and 248-264)
- `plan/architect-fix-multi-yaml-fence.md` Part 1 — exact before/after examples and constraints

### Requirements

1. In `plugins/python3-development/agents/swarm-task-planner.md`:
   - Template location 1 (TASK file template, ~lines 212-220): Remove the ` ```yaml ` line
     before `---` and the closing ` ``` ` line after the final `---`. The `````markdown` outer
     fence must stay.
   - Template location 2 (Task Structure Requirements, ~lines 249-265): Same edit — remove
     inner ` ```yaml ` / ` ``` ` lines, keep outer `````markdown` fence.

2. In `plugins/development-harness/agents/swarm-task-planner.md`:
   - Template location 1 (~lines 212-219): Same edit as above.
   - Template location 2 (~lines 248-264): Same edit as above. Confirm this file uses `role:`
     instead of `agent:` and preserve that difference.

3. After editing, each template block must look like this pattern (raw frontmatter inside the
   outer markdown fence, no inner code fence):

```text
````markdown
---
task: [Task ID]
title: [Descriptive Name]
status: not-started
...
---
````
```

### Constraints

- The `development-harness` variant uses `role:` instead of `agent:` in the YAML fields. Do
  NOT change this field name.
- All other YAML fields (`accuracy-risk`, `skills`, `parallelize-with`, `reason`, `handoff`,
  etc.) must remain unchanged.
- The enclosing `````markdown` documentation fence (4 backticks) must stay in place; only the
  inner ` ```yaml ` / ` ``` ` lines (3 backticks) are removed.
- Do not change any instructional prose, section headings, or other content in either file.

### Expected Outputs

- Modified file: `plugins/python3-development/agents/swarm-task-planner.md`
  - Both template locations updated (inner ` ```yaml ` fence removed)
- Modified file: `plugins/development-harness/agents/swarm-task-planner.md`
  - Both template locations updated (inner ` ```yaml ` fence removed, `role:` preserved)

### Acceptance Criteria

1. Neither `plugins/python3-development/agents/swarm-task-planner.md` nor
   `plugins/development-harness/agents/swarm-task-planner.md` contains the string
   ` ```yaml\n---` (fenced YAML opening) after the edit.
2. Both files still contain `````markdown` outer documentation fences around their template
   blocks (the 4-backtick fences are not removed).
3. `plugins/development-harness/agents/swarm-task-planner.md` still contains `role:` in the
   YAML template fields (not changed to `agent:`).
4. `uv run prek run --files plugins/python3-development/agents/swarm-task-planner.md` exits 0.
5. `uv run prek run --files plugins/development-harness/agents/swarm-task-planner.md` exits 0.

### Verification Steps

1. After editing, grep for the fenced YAML opening pattern in both files:

```bash
grep -n '```yaml' plugins/python3-development/agents/swarm-task-planner.md
grep -n '```yaml' plugins/development-harness/agents/swarm-task-planner.md
```

Expected: only matches that are themselves inside documentation code fences (i.e., the
anti-pattern example if one exists, not template content). Zero matches at the template
locations confirms the fix.

2. Confirm `role:` still present in development-harness template:

```bash
grep -n 'role:' plugins/development-harness/agents/swarm-task-planner.md
```

Expected: `role:` appears in the YAML template block.

3. Run linting on both files:

```bash
uv run prek run --files plugins/python3-development/agents/swarm-task-planner.md
uv run prek run --files plugins/development-harness/agents/swarm-task-planner.md
```

### Handoff

Return:

- Lines changed in each file (before/after for each template location)
- Output of grep verification commands
- Linting exit codes for both files

---

## Priority 3 — Depends on T1 and T2

T4 (tests) depends on both T1 (detect_fenced_yaml exists) and T2 (parse_task_content modified).
T5 (documentation) has no code dependencies and can execute concurrently with T4 once Priority 1
tasks are complete, but is listed at Priority 3 because it documents behavior added in T1-T2.

---

```yaml
---
task: T4
title: Unit and integration tests for detect_fenced_yaml and parse_task_content
status: not-started
agent: python-pytest-architect
dependencies:
  - T1
  - T2
priority: 3
complexity: high
accuracy-risk: medium
parallelize-with:
  - T5
reason: >
  T4 creates a new test file; T5 edits TASK_FILE_FORMAT.md. No file overlap.
skills:
  - python3-development
handoff: >
  Report: test file path, number of tests created, pytest exit code,
  stderr capture approach used, any test cases that required deviation from spec.
---
```

### Context

This task was merged from two originally planned tasks: (1) unit tests for `detect_fenced_yaml`
and (2) integration tests for `parse_task_content` with fenced input. Both would write to the
same new test file, so they are combined here to avoid edit conflicts.

No existing test files are present under
`plugins/python3-development/skills/implementation-manager/scripts/`. Create a new test file
following the project's Python testing conventions (pytest, `uv run pytest`).

Architecture spec primary reference: `plan/architect-fix-multi-yaml-fence.md` section "Testing
Strategy" with all 17 test cases specified.

### Objective

Create a pytest test file covering all 17 test cases from the architecture spec: 11 unit tests
for `detect_fenced_yaml` and 6 integration tests for `parse_task_content` with fenced, raw, and
legacy inputs, with stderr capture for warning assertions.

### Required Inputs

- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py` — import
  source for `detect_fenced_yaml` (must exist after T1)
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
  — import source for `parse_task_content` (must be modified after T2)
- `plan/architect-fix-multi-yaml-fence.md` section "Testing Strategy" — all 17 test cases with
  inputs and expected outputs
- `plan/tasks-4-validate-orchestrator-discipline.md` lines 265-279 — regression fixture
  (real-world fenced YAML content)

### Requirements

#### Unit tests for detect_fenced_yaml

Create test cases for all 11 cases from the architecture spec:

1. Standard fenced YAML (` ```yaml\n---\ntask: T1\n---\n``` `) returns stripped content.
2. Fenced with `yml` tag (` ```yml\n---\ntask: T1\n---\n``` `) returns stripped content.
3. Fenced without language tag (` ```\n---\ntask: T1\n---\n``` `) returns stripped content.
4. Leading whitespace before fence — returns stripped content after leading whitespace handling.
5. No fence, raw frontmatter (`---\ntask: T1\n---\n`) returns `None`.
6. Legacy markdown (`## Task T1: Title\n**Status**: ...`) returns `None`.
7. Fenced block without `---` inside (` ```yaml\nkey: value\n``` `) returns `None`.
8. Multiple fenced blocks (multi-task) — all three blocks stripped, returns combined content.
9. Four-backtick fence (` ````yaml\n---\ntask: T1\n---\n```` `) returns `None`.
10. Empty content (`""`) returns `None`.
11. Fence with trailing content after close — stripped content preserves trailing content.

#### Integration tests for parse_task_content

Create test cases for all 6 integration cases from the architecture spec:

12. Fenced single task — returns `[Task]` with correct fields; WARNING on stderr.
13. Fenced multi-task file (plan-level YAML + fenced per-task blocks) — tasks parsed, warnings
    on stderr.
14. Existing raw YAML (regression) — returns `[Task]` with no warnings.
15. Existing legacy markdown (regression) — returns tasks with correct fields, no warnings.
16. YAML parse failure — WARNING containing "YAML frontmatter detected but parsing failed" on
    stderr, falls through to legacy.
17. Fenced with missing required field — warning from fence stripping, then warning from YAML
    parse failure, then legacy (or empty list).

#### Real-world regression fixture

18. Use content from `plan/tasks-4-validate-orchestrator-discipline.md` lines 265-279 as a
    fixture. Verify that `parse_task_content` applied to that content returns at least one
    `Task` object (non-empty list) and emits a WARNING to stderr.

#### stderr capture

All tests that assert on warnings must capture `sys.stderr` using `capsys` (pytest built-in).
Assert that the captured stderr contains the word "WARNING".

### Constraints

- Test file must be named `test_task_format_fenced_yaml.py` and placed at:
  `plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py`
- Use `sys.path.insert` at the top of the test file to make the scripts directory importable.
- Do not import from paths outside the scripts directory — all imports must come from
  `task_format` and `implementation_manager` modules.
- Do not create a `conftest.py` unless required by the test setup; keep it simple.
- All test functions must be named `test_*` (pytest convention).
- Tests must be runnable via `uv run pytest` from the repo root.

### Expected Outputs

- New file:
  `plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py`
  - 17+ test functions (11 unit + 6 integration + 1 regression fixture test)
  - All tests pass with `uv run pytest` against the modified codebase

### Acceptance Criteria

1. Test file exists at the specified path and contains at least 17 test functions.
2. `uv run pytest plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py -v`
   exits 0 with all tests passing.
3. Tests for cases 12, 13, 16, 17, and 18 capture stderr and assert `"WARNING"` in the output.
4. Tests for cases 14 and 15 (regression) assert that stderr is empty (no spurious warnings
   on clean input).
5. The real-world regression fixture (case 18) reads actual content from
   `plan/tasks-4-validate-orchestrator-discipline.md` and exercises the parser — it does not
   use hardcoded content that diverges from the real file.
6. `uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py`
   exits 0.

### Verification Steps

1. Run all tests:

```bash
uv run pytest plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py -v
```

Expected: all tests pass, exit code 0.

2. Count test functions:

```bash
uv run pytest plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py --collect-only -q
```

Expected: at least 17 test items collected.

3. Confirm real-world fixture reads the actual file:

```bash
grep -n 'tasks-4-validate' plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py
```

Expected: the path `plan/tasks-4-validate-orchestrator-discipline.md` appears in the test source.

4. Run linting:

```bash
uv run prek run --files plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py
```

### CoVe Checks

Key claims to verify:

- `plan/tasks-4-validate-orchestrator-discipline.md` lines 265-279 contain fenced YAML that
  exercises the parser (read the file before using it as a fixture).
- `capsys` is the correct pytest mechanism for capturing `sys.stderr.write()` output (not just
  `logging` output).

Verification questions:

1. Does `capsys.readouterr().err` capture `sys.stderr.write("WARNING: ...")` output in pytest?
2. Does `plan/tasks-4-validate-orchestrator-discipline.md` lines 265-279 actually contain a
   fenced YAML block with `---` delimiters?

Evidence to collect:

- Read `plan/tasks-4-validate-orchestrator-discipline.md` lines 260-285 before writing the
  fixture to confirm the content and line numbers.
- Run one small test case manually with `uv run python3 -c` to confirm `capsys` captures
  `sys.stderr.write()`.

Revision rule: If `capsys` does not capture `sys.stderr.write()` output in the test environment,
use `monkeypatch.setattr(sys, "stderr", io.StringIO())` as an alternative and document the change.

### Handoff

Return:

- Path to test file
- Count of test functions
- `pytest -v` output (pass/fail per test)
- Confirmation that real-world fixture reads the actual plan file
- Any test cases that could not be implemented as specified and why

---

```yaml
---
task: T5
title: Add Authorized Writers section and anti-pattern to TASK_FILE_FORMAT.md
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 3
complexity: low
accuracy-risk: low
parallelize-with:
  - T4
reason: T5 writes to TASK_FILE_FORMAT.md; T4 writes to a new test file. No file overlap.
skills: []
handoff: >
  Report: section heading and line number where content was inserted, linting exit code,
  confirmation that anti-pattern example uses correct backtick nesting.
---
```

### Context

`TASK_FILE_FORMAT.md` at `.claude/docs/TASK_FILE_FORMAT.md` is the canonical format
specification for SAM task files. It does not currently document (1) which scripts are
authorized to write task files, or (2) the fenced YAML anti-pattern that causes silent parser
failure.

Architecture spec primary reference: `plan/architect-fix-multi-yaml-fence.md` Part 3.

### Objective

Add a new `## Authorized Writers` section to `.claude/docs/TASK_FILE_FORMAT.md` after the
existing `## Format Specification` section, containing the designated writer scripts table,
the policy statement, and the fenced YAML anti-pattern example.

### Required Inputs

- `.claude/docs/TASK_FILE_FORMAT.md` — read before editing to locate `## Format Specification`
  section and confirm its line number
- `plan/architect-fix-multi-yaml-fence.md` Part 3 — exact table content, policy statement,
  and anti-pattern markdown to include

### Requirements

1. Read `.claude/docs/TASK_FILE_FORMAT.md` to find `## Format Specification` and the section
   that immediately follows it (`## Markdown Body Sections`).
2. Insert a new `## Authorized Writers` section between `## Format Specification` and
   `## Markdown Body Sections`.
3. The section must contain:

   a. The designated writers table with these four scripts:

   | Script | Purpose | Path |
   |--------|---------|------|
   | `implementation_manager.py` | Status field updates via `update_yaml_field` | `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py` |
   | `task_status_hook.py` | Timestamp and status updates from hooks | `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` |
   | `split_task_file.py` | Splits monolithic task files into per-task files | `plugins/python3-development/scripts/split_task_file.py` |
   | `migrate_task_format.py` | Converts legacy markdown to YAML frontmatter | `plugins/python3-development/scripts/migrate_task_format.py` |

   b. Policy statement: Task data files MUST contain raw YAML frontmatter starting with `---`.
      Agents generating task files SHOULD produce content matching this format directly. When
      the generator is an LLM agent (e.g., `swarm-task-planner`), the agent's template MUST
      show raw frontmatter without code fence wrappers.

   c. The anti-pattern example from the architecture spec Part 3, showing:
      - Section heading `### Anti-Pattern: Fenced YAML Frontmatter`
      - The "Wrong" example (fenced YAML block)
      - The "Correct" example (raw frontmatter)
      - Explanation: the `detect_fenced_yaml()` function auto-strips fences with a warning,
        but this is a fallback — the generator should produce correct output.

4. Use correct backtick nesting for code fences in the anti-pattern example:
   - The `Wrong` example must show ` ```yaml ` inside a code fence; use 4-backtick outer fence
     with 3-backtick inner fence.
   - The `Correct` example shows raw frontmatter; use a 3-backtick ` ```text ` or ` ```markdown `
     fence.

5. Surround the new section with blank lines (MD031 compliance).

### Constraints

- Do not modify any existing section in `TASK_FILE_FORMAT.md` outside the insertion point.
- Do not renumber or reorganize existing sections.
- Code fence language specifiers required on all code fences (e.g., ` ```text `, ` ```python `).
- The anti-pattern example must use 4-backtick outer fence + 3-backtick inner fence where
  nested fencing is needed (see `.claude/CLAUDE.md` File Reference Standards).

### Expected Outputs

- Modified file: `.claude/docs/TASK_FILE_FORMAT.md`
  - New `## Authorized Writers` section inserted between `## Format Specification` and
    `## Markdown Body Sections`

### Acceptance Criteria

1. `.claude/docs/TASK_FILE_FORMAT.md` contains a `## Authorized Writers` section.
2. The section appears after `## Format Specification` and before `## Markdown Body Sections`.
3. The table lists all four designated scripts with correct paths.
4. The anti-pattern example contains both a "Wrong" (fenced) and "Correct" (raw) block.
5. No code fence in the inserted content is missing a language specifier.
6. `uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md` exits 0.

### Verification Steps

1. Grep to confirm section order:

```bash
grep -n "^## " .claude/docs/TASK_FILE_FORMAT.md | head -20
```

Expected output includes `## Format Specification`, then `## Authorized Writers`, then
`## Markdown Body Sections` in that order.

2. Grep to confirm all four script names are present:

```bash
grep -c "implementation_manager.py\|task_status_hook.py\|split_task_file.py\|migrate_task_format.py" .claude/docs/TASK_FILE_FORMAT.md
```

Expected: 4 or more matches (each script name appears at least once).

3. Run linting:

```bash
uv run prek run --files .claude/docs/TASK_FILE_FORMAT.md
```

### Handoff

Return:

- Line numbers of inserted content (start and end)
- Output of grep verification commands
- Linting exit code

---

## Priority 4 — End-to-End Validation (depends on T2, T4, T3)

T6 requires that the parser changes (T2), tests (T4), and template fixes (T3) are all complete
before running end-to-end validation against the real affected file.

---

```yaml
---
task: T6
title: End-to-end validation with real affected file
status: not-started
agent: python-cli-architect
dependencies:
  - T2
  - T3
  - T4
priority: 4
complexity: low
accuracy-risk: low
parallelize-with: []
reason: T6 is the final convergence point; no parallel tasks remain.
skills:
  - python3-development
handoff: >
  Report: implementation_manager.py status output for the affected file before and after,
  task count parsed, any task with agent=None in the output, overall pass/fail.
---
```

### Context

`plan/tasks-4-validate-orchestrator-discipline.md` is the real-world file that triggered
Issue #320. It contains per-task YAML frontmatter wrapped in fenced code blocks, plus a
plan-level YAML header that is not a task. Before this fix, running
`implementation_manager.py status . validate-orchestrator-discipline` returns zero tasks.

This task verifies the complete fix (T1+T2+T3+T4+T5) against this real file.

### Objective

Confirm that `implementation_manager.py status` on `plan/tasks-4-validate-orchestrator-discipline.md`
returns a non-empty task list with correct agent assignments after all previous tasks complete.

### Required Inputs

- `plan/tasks-4-validate-orchestrator-discipline.md` — the real affected file (read-only)
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
  — modified by T2 (must be complete before this task starts)

### Requirements

1. Run `implementation_manager.py status . validate-orchestrator-discipline` and capture output.
2. Confirm the output contains a non-empty task list (at least one task parsed).
3. Confirm no task in the output has `agent: null` or `agent: None` (all tasks have an agent
   assignment from the fenced YAML metadata).
4. Confirm that stderr output contains the WARNING about fenced YAML (the auto-strip was
   triggered).
5. If any task still has `agent: None`, report which task ID and what the YAML frontmatter
   contains for that task's `agent:` field.

### Constraints

- This task is read-only with respect to `plan/tasks-4-validate-orchestrator-discipline.md` —
  do not modify the real plan file.
- Do not modify any source files; this is a verification-only task.

### Expected Outputs

- No files created or modified
- Verification report in handoff output

### Acceptance Criteria

1. `uv run python3 plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py status . validate-orchestrator-discipline`
   exits 0.
2. The JSON output contains at least one task (non-empty `tasks` array).
3. No task in the output has `agent` value of `null` or `None`.
4. stderr (captured separately) contains "WARNING" from the fenced YAML detection.

### Verification Steps

1. Run status with stderr captured separately:

```bash
uv run python3 plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py \
  status . validate-orchestrator-discipline 2>/tmp/im_stderr.txt
```

2. Check task count and agent fields:

```bash
uv run python3 -c "
import json, sys
data = json.load(sys.stdin)
tasks = data.get('tasks', [])
print(f'Task count: {len(tasks)}')
null_agents = [t for t in tasks if not t.get('agent')]
if null_agents:
    print(f'Tasks with null agent: {[t[\"id\"] for t in null_agents]}')
else:
    print('All tasks have agent assignments')
" < <(uv run python3 plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py status . validate-orchestrator-discipline 2>/dev/null)
```

3. Check stderr warning:

```bash
cat /tmp/im_stderr.txt
```

Expected: contains "WARNING: Task file contains YAML frontmatter wrapped in code fences".

### Handoff

Return:

- Task count from status output
- Whether any task has `agent: null`
- Content of stderr (the WARNING messages)
- Overall pass/fail for end-to-end validation

---

## Sync Checkpoints

### SYNC CHECKPOINT 1: Priority 1 complete

Convergence point: T1 + T3 + T5 outputs

Quality gates:

- T1: `detect_fenced_yaml` in `task_format.py`, in `__all__`, inline tests pass, linting 0
- T3: both template files grep-clean for ` ```yaml\n---` pattern, `role:` preserved, linting 0
- T5: `## Authorized Writers` section present between correct sections, linting 0

Reflection questions:

- Does T1's implementation of the 4-backtick exclusion need adjustment based on actual regex
  behavior?
- Did the template fix in T3 reveal a third template location not identified in the architecture
  spec?

Proceed to Priority 2 (T2) after checkpoint passes.

### SYNC CHECKPOINT 2: Priority 2 complete

Convergence point: T2 output (with T3 already complete)

Quality gates:

- T2: fenced YAML recovery test passes, stderr warning emitted, linting 0
- T2: import line includes `detect_fenced_yaml`
- T2: recursion depth guard present and tested

Reflection questions:

- Is the warning message format exactly as specified in the architecture spec? Tests in T4 will
  assert on exact text.

Proceed to Priority 3 (T4, T5 in parallel) after checkpoint passes.

### SYNC CHECKPOINT 3: Priority 3 complete

Convergence point: T4 + T5 outputs

Quality gates:

- T4: all 17+ tests pass, `pytest -v` exit 0, real-world fixture reads actual plan file
- T5: section order confirmed, all four script paths present, linting 0

Reflection questions:

- Do any test cases reveal behavior not covered by the architecture spec?
- Does T5 documentation accurately reflect what T1/T2 implemented?

Proceed to Priority 4 (T6) after checkpoint passes.

### SYNC CHECKPOINT 4: End-to-End (T6)

Convergence point: all previous tasks complete, T6 verification output

Quality gates:

- T6: task count > 0, no null agents, WARNING present in stderr

If T6 reveals tasks with null agents despite the fix, do not close the issue — investigate
which YAML field value is not being parsed and create a follow-up task.
