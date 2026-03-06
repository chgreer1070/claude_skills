---
name: ASYNC240 forbids pathlib in async functions — need async-safe pathlib pattern
description: "Ruff ASYNC240 forbids pathlib.Path methods (.exists(), .read_text(), .write_text()) inside async functions because they perform blocking I/O. This conflicts with the project convention of using pathlib exclusively (modern Python / shinysnake — no os.path). In async test code during #328, calling Path(...).exists() triggered ASYNC240. Workarounds used: backlog_dir.glob('pattern') for existence checks, reading files in sync fixtures. Options: (1) per-file ASYNC240 suppression for tests/, (2) adopt anyio.Path for async contexts, (3) document canonical async-safe pathlib pattern for the project."
metadata:
  topic: async240-forbids-pathlib-in-async-functions-need-async-safe-
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: P2
  type: Bug
  status: needs-grooming
  issue: '#336'
  last_synced: '2026-03-06T23:01:34Z'
  groomed: '2026-03-06'
---

## Story

As a **developer relying on this plugin**, I want to **async240 forbids pathlib in async functions — need async-safe pathlib pattern** so that **the tool works correctly and reliably**.

## Description

Ruff ASYNC240 forbids pathlib.Path methods (.exists(), .read_text(), .write_text()) inside async functions because they perform blocking I/O. This conflicts with the project convention of using pathlib exclusively (modern Python / shinysnake — no os.path). In async test code during #328, calling Path(...).exists() triggered ASYNC240. Workarounds used: backlog_dir.glob('pattern') for existence checks, reading files in sync fixtures. Options: (1) per-file ASYNC240 suppression for tests/, (2) adopt anyio.Path for async contexts, (3) document canonical async-safe pathlib pattern for the project.

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: session observation during #328 implementation
- **Priority**: P2
- **Added**: 2026-03-01
- **Research questions**: None

## Fact-Check

**Date**: 2026-03-06
**Claims checked**: 2

| Claim | Verdict | Source |
|-------|---------|--------|
| Ruff ASYNC240 forbids pathlib.Path methods in async functions (blocking I/O) | VERIFIED | [Ruff docs: ASYNC240](https://docs.astral.sh/ruff/rules/blocking-path-method-in-async-function/) (2026-03-06) |
| anyio.Path provides async-safe .exists(), .read_text(), .write_text() alternatives | VERIFIED | [anyio File I/O docs](https://anyio.readthedocs.io/en/stable/fileio.html) (2026-03-06) |

No refuted or inconclusive claims.

## RT-ICA

**Goal**: Establish a canonical async-safe pathlib pattern so async code complies with both ASYNC240 and the project's pathlib-only convention.

| # | Condition | Status | Info |
|---|-----------|--------|------|
| 1 | ASYNC240 rule exists and forbids pathlib in async | AVAILABLE | Verified via Ruff docs |
| 2 | anyio.Path is a viable async alternative | AVAILABLE | Verified via anyio docs |
| 3 | Project convention requires pathlib-only (no os.path) | AVAILABLE | Observable in codebase |
| 4 | Scope of affected async code in repo | DERIVABLE | Searchable via grep |
| 5 | anyio already in project dependencies | DERIVABLE | Check pyproject.toml |

**Decision**: APPROVED
**Missing**: None

## Groomed (2026-03-06)

### Issue Classification

**Type**: missing-guardrail
**Scenario-target**: Async functions using pathlib.Path methods trigger ASYNC240 lint errors; no project-level pattern or utility exists to handle this.
**Analysis method**: None (missing-guardrail type does not require RCA)

### Reproducibility

1. Run `uv run ruff check .claude/skills/backlog/tests/test_scenarios.py` — ASYNC240 fires on pathlib calls inside async test methods.
2. Specific instances confirmed in codebase:
   - `test_scenarios.py` line 437: `non_canonical.write_text(...)` inside `async def test_normalize_updates_items`
   - `test_scenarios.py` lines 593, 606: `backlog_dir.glob("*resolve*")` inside `async def test_stale_item_discovery`
   - `test_scenarios.py` line 247: `filepath.exists()` inside `async def test_resolve_with_cleanup`
3. No `noqa: ASYNC240` suppressions exist anywhere in the codebase — confirmed by grep returning zero matches.
4. The `**/tests/**` `per-file-ignores` block in `pyproject.toml` does NOT suppress the `ASYNC` rule group, so ASYNC240 is active for all test files.

### Output / Evidence

- Run `uv run ruff check --select ASYNC240 .claude/skills/backlog/tests/` — currently produces zero output (ASYNC240 may require individual file paths or the rule fires only on detected blocking calls). Verify by running against the specific offending file.
- "Done" means: `uv run ruff check .` exits 0 with no ASYNC240 violations, and `uv run pytest .claude/skills/backlog/tests/` passes.
- If the chosen approach is `anyio.Path`: `python -c "import anyio; print(anyio.__version__)"` confirms the library is available.
- If the chosen approach is suppression: `git grep "noqa: ASYNC240" -- "tests/"` returns at least one match per suppressed call site.

### Priority

5/10 — ASYNC240 is a linting violation, not a runtime bug: the blocking I/O calls in tests run under pytest-asyncio which uses an event loop but the blocking impact is limited to test duration. No production code paths are affected. However, leaving it unresolved means the ASYNC rule group cannot be trusted as a quality gate, and future blocking I/O in production async code would blend silently with accepted test violations.

### Impact

- Blocks: ASYNC240 cannot serve as a meaningful quality gate while active violations exist in tests — any new blocking pathlib call in production async code would be indistinguishable from accepted test-scope violations.
- Bottleneck: The project convention mandates `pathlib` exclusively (PTH rule group enforced) while ASYNC240 forbids it in async contexts — these two rules are in direct conflict with no documented resolution.
- Scope: Violations are currently confined to `.claude/skills/backlog/tests/test_scenarios.py` (3 call sites: `.write_text()`, two `.glob()` calls, `.exists()`). No production async code violates ASYNC240 today.

### Expected Behavior

`uv run ruff check .` completes with zero ASYNC240 violations. All async functions that interact with the filesystem either use an async-safe API or are structured so pathlib calls occur outside the async context (e.g., in sync fixtures). The project has a documented, canonical pattern for async-context filesystem access that future contributors can follow.

### Desired Structure

One of three target states (decision required — see Decision section):

**Option A — anyio.Path adoption** (recommended for production async code):
- `anyio` added to `backlog-core` dependencies in `.claude/skills/backlog/pyproject.toml`
- Async functions that do filesystem I/O import and use `anyio.Path` instead of `pathlib.Path`
- A note in the project's coding conventions documents when to use `anyio.Path` vs `pathlib.Path`

**Option B — Suppress ASYNC240 for tests/**:
- `"ASYNC240"` added to the `**/tests/**` entry in `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`
- `"ASYNC240"` also added to `**/scripts/test_*.py` if needed
- A comment explains why: "pathlib blocking I/O acceptable in test context under pytest-asyncio"

**Option C — Refactor to sync fixtures**:
- Pathlib calls in async test methods moved to sync helper functions or sync pytest fixtures
- Async test methods call only `await`-based operations; filesystem assertions happen after `await` in sync helpers
- No new dependencies, no suppressions

In all cases: `uv run ruff check .` produces zero ASYNC240 violations and `uv run pytest` passes.

### Acceptance Criteria

1. `uv run ruff check --select ASYNC240 .` exits 0 with no output.
2. `uv run pytest .claude/skills/backlog/tests/` passes with no failures.
3. `uv run ruff check .` (full ruleset) exits 0 — no regressions introduced.
4. If Option A chosen: `uv run python -c "from anyio import Path; print('ok')"` succeeds within the backlog-core environment.
5. If Option B chosen: `git grep "ASYNC240" pyproject.toml` returns a match in the `per-file-ignores` section with an explanatory comment.
6. If Option C chosen: no `async def` test methods in `test_scenarios.py` contain direct `pathlib.Path` method calls (`.exists()`, `.read_text()`, `.write_text()`, `.glob()`, `.mkdir()`).
7. A project-level note (CONTRIBUTING.md or rule file) records which option was chosen and why, so future contributors know the canonical pattern.