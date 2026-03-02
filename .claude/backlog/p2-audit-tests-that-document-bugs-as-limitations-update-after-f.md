---
name: Audit tests that document bugs as 'limitations' — update after fixes
description: "During backlog MCP scenario testing (#328), a prior bugfix to _parse_frontmatter (preserving nested metadata dicts) caused test_parse_frontmatter_nested_meta_produces_empty_meta_dict to fail. The test explicitly asserted the buggy behavior (meta == {}) with a comment calling it a 'documented limitation'. This pattern — tests that enshrine bugs as expected behavior — can mask regressions and block fixes. Action: audit existing test suite for similar patterns where tests document current behavior as intentional limitations rather than testing correct behavior. Check for comments containing 'limitation', 'known issue', 'current behavior', 'workaround' that may be masking bugs."
metadata:
  topic: audit-tests-that-document-bugs-as-limitations-update-after-f
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: open
  issue: '#335'
  last_synced: '2026-03-02T01:40:35Z'
  groomed: '2026-03-02'
  plan: plan/tasks-16-audit-tests-limitation-patterns.md
---

## Story

As a **developer**, I want **During backlog MCP scenario testing (#328), a prior bugfix to _parse_frontmat...** so that **backlog items are tracked in GitHub**.

## Description

During backlog MCP scenario testing (#328), a prior bugfix to _parse_frontmatter (preserving nested metadata dicts) caused test_parse_frontmatter_nested_meta_produces_empty_meta_dict to fail. The test explicitly asserted the buggy behavior (meta == {}) with a comment calling it a 'documented limitation'. This pattern — tests that enshrine bugs as expected behavior — can mask regressions and block fixes. Action: audit existing test suite for similar patterns where tests document current behavior as intentional limitations rather than testing correct behavior. Check for comments containing 'limitation', 'known issue', 'current behavior', 'workaround' that may be masking bugs.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: session observation during #328 implementation
- **Priority**: P2
- **Added**: 2026-03-01
- **Research questions**: None

## Fact-Check

Claims checked: 4
VERIFIED: 4 | REFUTED: 0 | INCONCLUSIVE: 0

- VERIFIED: test_parse_frontmatter_nested_meta_produces_empty_meta_dict existed with 'documented limitation' comment asserting meta == {} (git show 0e0611f diff)
- VERIFIED: _parse_frontmatter bug fix to preserve nested metadata dicts was implemented (commit 7a01ea5)
- VERIFIED: Fix broke the documentation-as-limitation test, triggering this audit item (commit 04ef112 comment)
- VERIFIED: 31 test files exist; current scan finds 4 files with limitation/workaround patterns (2 are benign — valid scope documentation)

## RT-ICA

Goal: Identify and update all tests in the project that assert incorrect/buggy behavior under the guise of 'documented limitations', ensuring tests reflect correct behavior.

Conditions:
1. List of all test files in project | Status: AVAILABLE | 31 files identified
2. Search patterns (limitation, known issue, current behavior, workaround, documented) | Status: AVAILABLE
3. Reference instance (test_parse_frontmatter_nested_meta_produces_empty_meta_dict — fixed in commit 0e0611f) | Status: AVAILABLE
4. Understanding of correct behavior for each flagged test | Status: DERIVABLE per case
5. Test suite must remain green after changes | Status: AVAILABLE (pytest via uv run pytest)

Decision: APPROVED
Missing: None

## Groomed (2026-03-02)

### Reproducibility

1. Run `uv run pytest .claude/skills/backlog/tests/test_backlog_core_parsing.py::TestParseFrontmatter -v`
2. Observe that tests pass (the bug fix is in place)
3. Search the test suite with patterns: "limitation", "known issue", "current behavior", "workaround", "documented"
4. Identify tests with assertion comments suggesting buggy behavior is "expected"

### Output / Evidence

- Reference test: `.claude/skills/backlog/tests/test_backlog_core_parsing.py::TestParseFrontmatter::test_parse_frontmatter_nested_meta_preserves_metadata` (lines 300-310)
- Fixed parsing function: `.claude/skills/backlog/backlog_core/parsing.py`
- Previous instance fixed in commit `0e0611f` — test was asserting `meta == {}` with "documented limitation" comment
- Current scan (4 flagged files): plugin-creator/tests/test_frontmatter_validator.py:548, test_hook_validator.py:75, test_token_counting.py:206 — all appear benign

### Priority

6/10 — Prevents future bugs from being masked by test assertions; reduces confusion during bug fix cycles.

### Impact

- **Blocks**: Developers fixing bugs encounter test failures that assert buggy behavior, causing confusion about fix correctness
- **Risk**: Regressions masked — tests pass while bugs exist, fail when bugs are fixed

### Scope

31 test files across:
- `.claude/skills/backlog/tests/` (7 files)
- `plugins/plugin-creator/tests/` (20 files)
- `plugins/agentskill-kaizen/tests/` (2 files)
- `plugins/summarizer/tests/` (1 file)
- `.claude/skills/gh/tests/` (1 file)

### Dependencies

- Depends on: None
- Blocks: Any future bug fixes that might be masked by tests documenting bugs as limitations

### Skills

- /python3-development:python3-test-design
- /python3-development:python3-review

### Agents

- @python3-development:python-pytest-architect

### Prior Work

- commit `0e0611f` — fixed the original instance (test_parse_frontmatter_nested_meta_produces_empty_meta_dict → test_parse_frontmatter_nested_meta_preserves_metadata)
- commit `7a01ea5` — the _parse_frontmatter bug fix that triggered this audit

### Files

- `.claude/skills/backlog/tests/test_backlog_core_parsing.py` (reference: fixed test at line 300)
- `plugins/plugin-creator/tests/test_frontmatter_validator.py` (line 548 — benign)
- `plugins/plugin-creator/tests/test_hook_validator.py` (line 75 — benign)
- `plugins/plugin-creator/tests/test_token_counting.py` (line 206 — benign)

### Issue Classification

**Type**: defect
**Rationale**: Tests asserting incorrect behavior with "documented limitation" comments are a quality defect — they normalize bugs and prevent fixes from being detected clearly.
**Analysis Method**: 5-whys
**Scenario Target**: _parse_frontmatter bug fix → test asserting buggy behavior failed → revealed anti-pattern → audit prevents future instances

### Root-Cause Analysis

**Method**: 5-whys
**Classification**: defect

#### Evidence Chain

1. test_parse_frontmatter_nested_meta_produces_empty_meta_dict asserted `meta == {}` — because _parse_frontmatter stringified nested YAML dicts (the actual bug)
2. Test was written against known-buggy behavior and labeled "documented limitation" instead of using pytest.mark.xfail or a TODO comment with issue reference
3. No convention existed for marking tests written during known-buggy states
4. When bug was fixed, test failed — creating confusion about whether the fix was correct
5. Audit item created to find remaining instances across all 31 test files

**Root Cause**: No agreed practice for tests written against known-buggy behavior. Correct convention is pytest.mark.xfail (designed for this case) or TODO with issue reference — not asserting wrong values as "expected".