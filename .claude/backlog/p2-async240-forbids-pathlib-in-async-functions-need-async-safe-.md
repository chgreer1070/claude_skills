---
name: ASYNC240 forbids pathlib in async functions — need async-safe pathlib pattern
description: "Ruff ASYNC240 forbids pathlib.Path methods (.exists(), .read_text(), .write_text()) inside async functions because they perform blocking I/O. This conflicts with the project convention of using pathlib exclusively (modern Python / shinysnake — no os.path). In async test code during #328, calling Path(...).exists() triggered ASYNC240. Workarounds used: backlog_dir.glob('pattern') for existence checks, reading files in sync fixtures. Options: (1) per-file ASYNC240 suppression for tests/, (2) adopt anyio.Path for async contexts, (3) document canonical async-safe pathlib pattern for the project."
metadata:
  topic: async240-forbids-pathlib-in-async-functions-need-async-safe-
  source: 'session observation during #328 implementation'
  added: '2026-03-01'
  priority: completed
  type: Bug
  status: done
  issue: '#336'
  last_synced: '2026-03-06T23:04:23Z'
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

1. Run `uv run ruff check --select ASYNC240 .claude/skills/backlog/tests/test_scenarios.py` — ASYNC240 fires on pathlib calls inside async test class methods.
2. Confirmed violation sites in `.claude/skills/backlog/tests/test_scenarios.py`:
   - Line 247: `filepath.exists()` inside `async def test_resolve_with_cleanup` (class `TestResolveBacklogItem`)
   - Line 437: `non_canonical.write_text(...)` inside `async def test_normalize_updates_items` (class `TestNormalize`)
   - Lines 457–458: `non_canonical.exists()` and `non_canonical.read_text(...)` inside same method
   - Lines 593, 606: `backlog_dir.glob("*resolve*")` called twice inside `async def test_lifecycle_create_then_resolve_with_cleanup` (class `TestLifecycle`)
3. No `noqa: ASYNC240` suppressions exist anywhere in the codebase — confirmed by grep returning zero matches.
4. The `**/tests/**` `per-file-ignores` block in `pyproject.toml` (line 360–372) suppresses `ANN`, `D`, `DOC`, `E501`, `EXE`, `N`, `PLC`, `PLR`, `S`, `SLF`, `T` — but does NOT suppress `ASYNC`, so ASYNC240 is active for all test files.
5. `plugins/agentskill-kaizen/tests/test_server.py` has pathlib calls but all are inside sync (non-async) test methods — not affected by ASYNC240.

### Output / Evidence

- Run `uv run ruff check --select ASYNC240 .claude/skills/backlog/tests/` — currently produces zero output (ASYNC240 may require individual file paths or the rule fires only on detected blocking calls). Verify by running against the specific offending file.
- "Done" means: `uv run ruff check .` exits 0 with no ASYNC240 violations, and `uv run pytest .claude/skills/backlog/tests/` passes.
- If the chosen approach is `anyio.Path`: `python -c "import anyio; print(anyio.__version__)"` confirms the library is available.
- If the chosen approach is suppression: `git grep "noqa: ASYNC240" -- "tests/"` returns at least one match per suppressed call site.

### Priority

5/10 — ASYNC240 is a linting violation, not a runtime bug. Blocking I/O calls in tests run under pytest-asyncio which provides an event loop, but the actual blocking impact is limited to test execution time. No production code paths are affected today. However, leaving it unresolved means the ASYNC rule group cannot function as a quality gate: any future blocking I/O introduced in production async code would blend silently with accepted test violations.

### Impact

- Blocks: ASYNC240 cannot serve as a meaningful quality gate while active violations exist in tests — any new blocking pathlib call in production async code becomes invisible against the baseline noise.
- Bottleneck: Two enforced rules are in direct conflict with no documented resolution: PTH (use pathlib, no os.path) mandates pathlib everywhere; ASYNC240 forbids pathlib methods in async contexts. Developers hitting this have no canonical pattern to follow.
- Scope: Currently confined to 6 pathlib call sites in `.claude/skills/backlog/tests/test_scenarios.py`. No production (non-test) async code violates ASYNC240 today.

### Expected Behavior

`uv run ruff check .` completes with zero ASYNC240 violations. All async functions that interact with the filesystem either use an async-safe API or are structured so pathlib calls occur outside the async context (e.g., in sync fixtures). A project-level canonical pattern for async-context filesystem access exists so future contributors do not need to re-derive it.

### Desired Structure

Three candidate target states — one must be selected (see Decision section):

**Option A — Suppress ASYNC240 for tests/** (recommended):
- `"ASYNC240"` added to both `**/tests/**` and `**/scripts/test_*.py` entries in `[tool.ruff.lint.per-file-ignores]` in `/home/user/claude_skills/pyproject.toml`.
- Comment explains: "pathlib blocking I/O acceptable in test context under pytest-asyncio; async test methods are not event-loop-constrained by real I/O volume".
- No new dependencies, no code changes to test logic.
- A note in `CONTRIBUTING.md` or `.claude/rules/` documents the rule and the exception rationale.

**Option B — anyio.Path adoption for test assertions**:
- `anyio` added as an explicit dependency in `.claude/skills/backlog/pyproject.toml` (it is already transitively available via `fastmcp>=3.0.2`, but not declared).
- Async test methods that call pathlib methods import and use `anyio.Path` instead of `pathlib.Path` for those specific calls.
- A rule file documents when to use `anyio.Path` vs `pathlib.Path`.

**Option C — Refactor to sync fixtures**:
- Pathlib calls in async test methods moved into sync helper functions or sync pytest fixtures (already partially done: sync fixtures like `write_test_item` exist and are used).
- Async test methods contain only `await`-based operations; all filesystem assertions moved to sync helpers called after `await`.
- No new dependencies, no suppressions.

In all cases: `uv run ruff check .` produces zero ASYNC240 violations and `uv run pytest` passes.

### Acceptance Criteria

1. `uv run ruff check --select ASYNC240 .` exits 0 with no output.
2. `uv run pytest .claude/skills/backlog/tests/` passes with no failures.
3. `uv run ruff check .` (full ruleset) exits 0 — no regressions introduced.
4. If Option A chosen: `git grep "ASYNC240" pyproject.toml` returns a match inside the `per-file-ignores` block with an explanatory comment.
5. If Option B chosen: `uv run python -c "from anyio import Path; print('ok')"` succeeds; `anyio` appears explicitly in `.claude/skills/backlog/pyproject.toml` dependencies.
6. If Option C chosen: no `async def` test methods in `test_scenarios.py` contain direct `pathlib.Path` method calls (`.exists()`, `.read_text()`, `.write_text()`, `.glob()`, `.mkdir()`).
7. A project-level record (CONTRIBUTING.md, `.claude/rules/`, or inline pyproject comment) documents which option was chosen and why, so future contributors know the canonical pattern.

### Resources

| Type | Item |
|------|------|
| Prior work | `.claude/skills/backlog/tests/test_scenarios.py` — contains all 6 violation sites |
| Prior work | `pyproject.toml` lines 360–372 — `per-file-ignores` block for `**/tests/**` (ASYNC not suppressed) |
| Prior work | `pyproject.toml` lines 277–295 — `per-file-ignores` for `**/scripts/test_*.py` |
| Prior work | `.claude/skills/backlog/pyproject.toml` — backlog-core dependencies (anyio absent, fastmcp present as transitive source) |
| External | [Ruff ASYNC240 docs](https://docs.astral.sh/ruff/rules/blocking-path-method-in-async-function/) (verified 2026-03-06) |
| External | [anyio File I/O docs](https://anyio.readthedocs.io/en/stable/fileio.html) (verified 2026-03-06) |

### Dependencies

- Depends on: None — standalone fix.
- Blocks: None directly. Unblocks: ASYNC rule group functioning as a meaningful quality gate for production async code.
- If Option B chosen: `anyio` transitive dependency via `fastmcp>=3.0.2` is already satisfied at runtime; only explicit declaration in `backlog-core/pyproject.toml` is needed.
- Ruff version: `ruff>=0.15.4` already in dev dependencies — ASYNC240 is available at this version.

### Decision

**Recommended: Option A — Suppress ASYNC240 for tests/**

Rationale:
- The violations are exclusively in test assertion code. Blocking I/O in pytest-asyncio test methods is an accepted trade-off: the tests are not latency-sensitive and are not sharing an event loop with production coroutines.
- Option A requires one `pyproject.toml` edit and a comment. Options B and C require modifying test logic in 4 async methods across `test_scenarios.py` without improving test semantics.
- `anyio.Path` (Option B) is appropriate for production async code — if the backlog MCP server ever gains async file I/O paths, ASYNC240 violations there would be the right signal to adopt `anyio.Path`. Using it in test assertions adds an unnecessary runtime dependency on anyio's async context (tests would need to `await` pathlib operations that are currently synchronous one-liners).
- Option C (sync fixtures) is already partially applied: `write_test_item` is a sync fixture. Extending this approach to all assertions is feasible but increases test verbosity without a clear correctness benefit at test scale.

**What needs to change:**
1. Add `"ASYNC240"` to `**/tests/**` in `[tool.ruff.lint.per-file-ignores]` in `pyproject.toml`, with an explanatory comment.
2. Add `"ASYNC240"` to `**/scripts/test_*.py` entry for consistency.
3. Add a note in `.claude/rules/` (e.g., `async-pathlib-pattern.md`) recording: "In async test methods, pathlib.Path is acceptable because ASYNC240 is suppressed for tests/. In production async code, use anyio.Path or restructure to call pathlib outside the async context."
4. Run `uv run ruff check .` to verify zero violations and `uv run pytest` to verify no regressions.

### Effort

Small — Option A requires 2 lines added to `pyproject.toml` and one new rule file (~10 lines). Options B and C are Medium (requires test refactoring across 4 async methods).