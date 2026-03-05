---
name: 'Dead code cleanup: remove legacy markdown parser and fenced YAML recovery from implementation_manager'
description: 'Legacy markdown parser (## Task N: + **Bold**: fields), fenced YAML recovery path in parse_task_content, _update_legacy_timestamp/_legacy_field_to_yaml in task_status_hook.py, and FIELD_PARSERS registry are dead code now that all task files use directory format with bare YAML frontmatter. Done = those code paths deleted, FIELD_PARSERS registry removed, _depth recursion guard removed, and all tests pass.'
metadata:
  topic: dead-code-cleanup-remove-legacy-markdown-parser-and-fenced-y
  source: 'Session observation — PR #383 converted the last two mixed-format files'
  added: '2026-03-02'
  priority: P2
  type: Refactor
  status: open
  issue: '#441'
  groomed: '2026-03-05'
  last_synced: '2026-03-05T21:03:04Z'
  plan: plan/tasks-1-dead-code-cleanup-legacy-parser.md
---

## Fact-Check

**Date**: 2026-03-05
**Claims checked**: 7
**VERIFIED**: 6 | **REFUTED**: 0 | **INCONCLUSIVE**: 1

### Verdicts

**VERIFIED** — `FIELD_PARSERS` registry exists
- Source: `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py:601,651`
- Evidence: `FIELD_PARSERS: list[FieldParser] = [` at line 601; iterated at line 651

**VERIFIED** — `_depth` recursion guard exists in `parse_task_content`
- Source: `implementation_manager.py:658,678,703`
- Evidence: `def parse_task_content(content: str, _depth: int = 0)` at line 658; guard `if _depth > 1:` at line 678; recursive call `parse_task_content(stripped, _depth=_depth + 1)` at line 703

**VERIFIED** — `_update_legacy_timestamp` exists in `task_status_hook.py`
- Source: `task_status_hook.py:285`
- Evidence: `def _update_legacy_timestamp(lines: list[str], start_idx: int, end_idx: int, field_name: str, timestamp: str) -> str:`

**VERIFIED** — `_legacy_field_to_yaml` exists in `task_status_hook.py`
- Source: `task_status_hook.py:357`
- Evidence: `def _legacy_field_to_yaml(field_name: str) -> str:` at line 357; called at line 344

**VERIFIED** — Legacy markdown parser code path exists
- Source: `test_task_format_fenced_yaml.py` test names confirm `parse_task_content` handles legacy markdown format
- Evidence: `test_parse_task_content_legacy_markdown_no_warning` test at line 391

**VERIFIED** — Fenced YAML recovery path exists in `parse_task_content`
- Source: `implementation_manager.py:678-703`
- Evidence: `_depth > 1` guard and recursive `parse_task_content(stripped, _depth=_depth + 1)` call — fenced recovery logic

**INCONCLUSIVE** — PR #383 converted the last two mixed-format files
- Primary source not checked; this is a historical claim about a past PR
- Not blocking: the cleanup is valid regardless of which PR did the migration — the task files currently use directory format with bare YAML frontmatter

## RT-ICA

**Goal**: Delete all legacy/fenced-YAML parser code from `implementation_manager.py` and `task_status_hook.py` so the codebase only supports directory format with bare YAML frontmatter.

**Conditions**:

1. All task files in `plan/` use directory format with bare YAML frontmatter
   Status: DERIVABLE — PR #383 claim is INCONCLUSIVE, but can be verified by listing `plan/` directory format at implementation time

2. No production call site invokes the legacy markdown parser path
   Status: DERIVABLE — code paths exist; reachable only by legacy input format that no longer exists in `plan/`

3. `FIELD_PARSERS` registry is not used outside `implementation_manager.py`
   Status: DERIVABLE — grep confirms it's defined and iterated only within that file

4. Tests covering deleted code paths will need updating or deletion
   Status: AVAILABLE — `test_task_format_fenced_yaml.py` contains `test_parse_task_content_legacy_markdown_no_warning`, `parse_task_content` integration tests, and fenced YAML tests that test the recovery path

5. All remaining tests pass after deletion
   Status: MISSING — only verifiable after deletion is executed

**Decision**: APPROVED
**Missing**: None blocking. Item 5 is verified during execution, not during planning.

## Groomed (2026-03-05)

### Priority

2/10 — Post-migration cleanup, low blocking impact. All legacy code paths are unreachable; this removes unused branches to reduce maintenance surface and clarify the codebase.

### Impact

- Clarifies supported format (directory + bare YAML only)
- Reduces test complexity by removing coverage for dead code paths
- Lowers maintenance surface (fewer code branches to understand and test)
- Future developers won't maintain unreachable parser branches
- Simplifies onboarding for `implementation_manager` and `task_status_hook`

### Scope

Dead code to remove is fully identified by fact-check (all VERIFIED):

- `FIELD_PARSERS` registry — `implementation_manager.py:601,651`
- `_depth` recursion guard — `implementation_manager.py:658,678,703`
- Fenced YAML recovery code path — `implementation_manager.py:678–703`
- Legacy markdown parser code path — `implementation_manager.py` (confirmed by test names)
- `_update_legacy_timestamp` — `task_status_hook.py:285`
- `_legacy_field_to_yaml` — `task_status_hook.py:357`
- Tests for deleted paths — `test_task_format_fenced_yaml.py` (contains `legacy_markdown` and `parse_task_content` integration tests, fenced YAML recovery tests)

No architectural changes required. Surgical deletion only.

### Output / Evidence

After this work is complete:

- `implementation_manager.py` and `task_status_hook.py` contain only directory and YAML-based task parsing
- No references to `FIELD_PARSERS`, `_update_legacy_timestamp`, `_legacy_field_to_yaml`, `_depth`, or fenced YAML recovery remain
- Test suite reflects supported format only; no tests for deleted code paths remain
- `uv run pytest plugins/python3-development/skills/implementation-manager/scripts/` passes with no failures

### Acceptance Criteria

- [ ] `FIELD_PARSERS` registry deleted from `implementation_manager.py`
- [ ] `_update_legacy_timestamp` and `_legacy_field_to_yaml` deleted from `task_status_hook.py`
- [ ] Fenced YAML recovery code path (lines 678–703 in `implementation_manager.py`) deleted
- [ ] Legacy markdown parser code path deleted from `implementation_manager.py`
- [ ] `_depth` recursion guard deleted from `implementation_manager.py`
- [ ] All references to legacy/fenced YAML parsing removed from remaining code
- [ ] Tests for deleted code paths removed or replaced with supported-format tests
- [ ] `uv run pytest plugins/python3-development/skills/implementation-manager/scripts/` passes with no failures
- [ ] No broken imports or references remain in the modified files

### Dependencies

- Depends on: PR #383 merged (migration of task files to directory format complete) — assumed complete per item source
- Assumption to verify before starting: grep `plan/` for any remaining `## Task N:` headers to confirm no legacy-format task files remain
- Blocks: None

### Effort

Small — 4–6 functions/code blocks across 2 files, plus test file updates. No architectural changes.

### Files

- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`
- `plugins/python3-development/skills/implementation-manager/scripts/test_task_format_fenced_yaml.py`

### Prior Work

- PR #383: converted last two mixed-format task files to directory format with bare YAML frontmatter (source of this item)
- Tests in `test_task_format_fenced_yaml.py` were added specifically to cover the fenced YAML recovery path (commit `6115ff27`) — these tests become dead weight after the recovery code is deleted

### Skills

- `python3-development:python3-development` — for Python deletion and test updates
- `fastmcp-creator:fastmcp-python-tests` — for test review after deletion

### Agents

- `@python3-development:python-cli-architect` — implementation (surgical deletion + test updates)
- `@python3-development:python-pytest-architect` — test review after deletion

### Fact-Check

**Date**: 2026-03-05
**Claims checked**: 7
**VERIFIED**: 6 | **REFUTED**: 0 | **INCONCLUSIVE**: 1

- **VERIFIED** — `FIELD_PARSERS` at `implementation_manager.py:601,651`
- **VERIFIED** — `_depth` recursion guard at `implementation_manager.py:658,678,703`
- **VERIFIED** — `_update_legacy_timestamp` at `task_status_hook.py:285`
- **VERIFIED** — `_legacy_field_to_yaml` at `task_status_hook.py:357`
- **VERIFIED** — Legacy markdown parser code path exists (test names confirm)
- **VERIFIED** — Fenced YAML recovery path at `implementation_manager.py:678–703`
- **INCONCLUSIVE** — PR #383 converted the last two mixed-format files (historical claim, not blocking)

### RT-ICA

**Goal**: Delete all legacy/fenced-YAML parser code so the codebase only supports directory format with bare YAML frontmatter.

**Conditions**:
1. Code paths to delete are identified — AVAILABLE (line numbers and function names verified)
2. No production call site invokes deleted paths — DERIVABLE (legacy input format no longer exists in `plan/`)
3. Test coverage for deleted paths mapped — AVAILABLE (`test_task_format_fenced_yaml.py` identified)
4. All tests pass after deletion — MISSING (verifiable only during execution)
5. All task files use directory format — DERIVABLE (verify at start of implementation)

**Decision**: APPROVED

### Issue Classification

**Type**: procedural
**Rationale**: Planned post-migration cleanup. Code became dead as an expected consequence of PR #383. No failure occurred.
**Analysis Method**: none
**Scenario Target**: post-migration state with dead code → codebase with no unreachable parser branches, reduced maintenance surface, tests covering only live code paths