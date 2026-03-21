# Feature Context: Gates Subprocess Timeout

## Document Metadata

- **Generated**: 2026-03-21
- **Input Type**: simple_description
- **Source**: Bug fix request — subprocess.run in gates.py has no timeout, follow-up from code review of Issue #938
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Add subprocess timeout to the `run_quality_gates()` function in
`plugins/development-harness/dispatch_schema/gates.py`. The `subprocess.run` call at line 75
has no timeout parameter, so a hung gate command blocks indefinitely with no recovery path.

Expected behavior when a gate command exceeds the timeout (default 300s):

1. `subprocess.run` raises `subprocess.TimeoutExpired`
2. Exception caught in `run_quality_gates()`
3. `CommandResult` constructed with `exit_code=124` (Unix timeout convention) and
   `stderr="command timed out after {timeout}s"`
4. Mode logic applies — `FAIL_FAST` breaks, `RUN_ALL` continues

Source: GitHub Issue #951, code review of Issue #938.

---

## Core Intent Analysis

### WHO (Target Users)

Agents and CI pipelines that invoke `run_quality_gates()` to execute shell-based quality checks
(lint, type-check, test). These callers have no mechanism today to recover from a hung
subprocess — the process hangs the entire caller indefinitely.

### WHAT (Desired Outcome)

A gate command that exceeds a configurable time limit (default 300 seconds) produces a
`CommandResult` with `exit_code=124` and a human-readable `stderr` message instead of blocking
forever. The `GateResult` aggregation and mode logic (`FAIL_FAST` / `RUN_ALL`) treat the
timeout result the same as any other failed command result.

### WHEN (Trigger Conditions)

- A gate command hangs (e.g., a test runner waiting for a lock, a network call with no timeout
  of its own, or a subprocess that deadlocks on stdin).
- Under normal conditions the timeout is never reached and behavior is unchanged.

### WHY (Problem Being Solved)

Without a timeout, a single hung gate command blocks the entire development workflow — no
results are returned, no failure is recorded, and the caller cannot proceed or recover. The
fix gives the caller a deterministic failure record (`exit_code=124`) and allows the workflow
to continue or stop based on the configured mode.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Command-not-found handled as CommandResult (exit_code=127)

- **Location**: `plugins/development-harness/dispatch_schema/gates.py:71-72`
- **Relevance**: Establishes the pattern for converting a non-subprocess error condition into
  a `CommandResult` with a conventional exit code and a descriptive `stderr` string, without
  raising an exception. The timeout fix follows this exact pattern with `exit_code=124`.
- **Reusable**: The `CommandResult(command=command, exit_code=127, stdout="", stderr=f"...")`
  constructor call is the template for the `exit_code=124` timeout result.

#### Pattern 2: Existing subprocess.run call site

- **Location**: `plugins/development-harness/dispatch_schema/gates.py:75`
- **Relevance**: The `subprocess.run(resolved_tokens, capture_output=True, text=True, cwd=cwd, check=False)` call is the single site where `timeout=` must be added. Adding the keyword argument here and catching `subprocess.TimeoutExpired` in the enclosing `else` block (or a wrapping `try/except`) is the complete change surface.
- **Reusable**: The surrounding `else` branch structure at lines 73-78 contains all subprocess
  interaction logic for one command — the `try/except TimeoutExpired` wraps this block.

#### Pattern 3: Test mock structure for subprocess.run

- **Location**: `plugins/development-harness/tests/test_dispatch_schema/test_gates.py`
- **Relevance**: All existing unit tests mock `dispatch_schema.gates.subprocess.run` via
  `mocker.patch("dispatch_schema.gates.subprocess.run", ...)`. The new timeout test uses
  `side_effect=subprocess.TimeoutExpired(cmd=..., timeout=300.0)` on the same mock target.
  The `_clear_resolve_executable_cache` autouse fixture ensures `shutil.which` cache does not
  interfere with new tests.
- **Reusable**: `_make_completed_process` helper, `mocker.patch` target string, class-based
  test organization, and the AAA comment structure are all directly reusable.

### Existing Infrastructure

- `CommandResult` model (imported from `dispatch_schema.core.models`) accepts `exit_code`,
  `stdout`, `stderr`, and derives `passed` from `exit_code == 0`. No model changes are needed.
- `GateRunMode.FAIL_FAST` / `GateRunMode.RUN_ALL` branch at `gates.py:82-83` already handles
  any `CommandResult` with `passed=False` — timeout results flow through this logic unchanged.
- `pytest-mock` (`MockerFixture`) is the established mocking tool in the test file — no
  new test dependencies are needed.

### Code References

- `plugins/development-harness/dispatch_schema/gates.py:38-85` — `run_quality_gates()` full
  function, docstring, and subprocess call site
- `plugins/development-harness/dispatch_schema/gates.py:75` — the specific `subprocess.run`
  call missing `timeout=`
- `plugins/development-harness/dispatch_schema/gates.py:71-72` — `exit_code=127` precedent
  for converting a non-subprocess failure into a `CommandResult`
- `plugins/development-harness/dispatch_schema/gates.py:82-83` — mode logic that applies to
  any `CommandResult.passed=False`, including the new timeout result
- `plugins/development-harness/tests/test_dispatch_schema/test_gates.py:34-42` — autouse
  cache-clear fixture all new tests inherit
- `plugins/development-harness/tests/test_dispatch_schema/test_gates.py:50-54` — `_make_completed_process` helper
- `plugins/development-harness/tests/test_dispatch_schema/test_gates.py:568-651` — `TestSubprocessInvocationContract` class — the most relevant existing test class for a new timeout test class

---

## Use Scenarios

### Scenario 1: Hung test runner in FAIL_FAST mode

**Actor**: CI pipeline running quality gates via `run_quality_gates(["uv run pytest", "ruff check ."])`
**Trigger**: `uv run pytest` hangs because a test acquires a lock and never releases it
**Goal**: The pipeline receives a failure result and stops — it does not hang indefinitely
**Expected Outcome**: After 300 seconds, `run_quality_gates` returns a `GateResult` with
`passed=False`, one `CommandResult` with `exit_code=124` and `stderr="command timed out after 300.0s"`,
and `mode=FAIL_FAST`. The second command (`ruff check .`) is never executed.

### Scenario 2: One command times out in RUN_ALL mode

**Actor**: Developer running all gates to get a full diagnostic picture
**Trigger**: One gate command hangs; developer is using `RUN_ALL` to see all results
**Goal**: The timeout is recorded as a failure for that command; remaining commands still execute
**Expected Outcome**: The timed-out command produces `CommandResult(exit_code=124, passed=False)`.
Subsequent commands execute normally. `GateResult.passed=False` because at least one result
failed.

### Scenario 3: All gates pass within timeout (normal operation)

**Actor**: Any caller of `run_quality_gates()`
**Trigger**: Normal gate execution where all commands complete in under 300 seconds
**Goal**: No behavior change from today
**Expected Outcome**: All `CommandResult` values are populated from `subprocess.CompletedProcess`
as before. The `timeout=300.0` parameter is passed to `subprocess.run` but never triggers.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | `run_quality_gates()` signature does not expose a `timeout` parameter to callers — the 300s default is baked in | Callers with shorter or longer gate budgets cannot customize without modifying source |
| 2 | Behavior | When `subprocess.TimeoutExpired` is raised, the process may still be running in the background — no explicit `kill()` is specified | Zombie subprocesses could accumulate if many timeouts occur; OS will eventually clean up but timing is non-deterministic |
| 3 | Scope | The `OSError` propagation note in the existing docstring (lines 50-52) describes a current intentional design decision — timeout handling must not disturb that contract | Verified: `TimeoutExpired` is a separate exception type from `OSError` so there is no conflict, but the docstring update must preserve the `OSError` note |

---

## Questions Requiring Resolution

### Q1: Should `timeout` be a parameter or a baked-in constant?

- **Category**: Scope
- **Gap**: The request specifies `default 300s` but does not state whether callers should be
  able to override this per-call.
- **Question**: Should `run_quality_gates()` accept a `timeout: float = 300.0` keyword
  argument, or should 300.0 be a module-level constant not exposed in the signature?
- **Options**:
  - A) Add `timeout: float = 300.0` to the function signature — callers can override per call
  - B) Define `_DEFAULT_GATE_TIMEOUT = 300.0` as a module constant — not user-configurable at call time
- **Why It Matters**: Option A changes the public API of `run_quality_gates()`. Option B is
  a smaller change but limits flexibility. The acceptance criteria as written do not include
  a new parameter, suggesting Option B — but this should be confirmed.
- **Resolution**: Option A was chosen. See ADR-001 in `plan/architect-gates-subprocess-timeout.md`. Implemented as `timeout: float = 300.0` keyword-only parameter.

### Q2: Should the timed-out subprocess be explicitly killed?

- **Category**: Behavior
- **Gap**: `subprocess.TimeoutExpired` is raised after the timeout elapses, but the child
  process continues running unless explicitly terminated. The request does not specify kill behavior.
- **Question**: After catching `subprocess.TimeoutExpired`, should the implementation call
  `.kill()` / `.wait()` on the process to clean up, or is recording the result and moving on
  sufficient?
- **Options**:
  - A) No kill — record `CommandResult(exit_code=124)` and continue; OS cleans up eventually
  - B) Kill the process after timeout — `process.kill(); process.wait()` before constructing `CommandResult`
- **Why It Matters**: Without kill, hung subprocesses accumulate. With kill, the code needs
  access to the `Popen` object, which requires refactoring from `subprocess.run` to
  `subprocess.Popen`. Option A is the minimal change; Option B is safer in long-running
  environments.
- **Resolution**: Option A (no kill) was chosen. See ADR-002 in `plan/architect-gates-subprocess-timeout.md`. Python docs confirm `subprocess.run` sends SIGKILL before raising `TimeoutExpired` — no `Popen` refactoring needed. Validated in implementation.

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. The `subprocess.run` call at `gates.py:75` includes a timeout so hung commands do not
   block indefinitely.
2. `subprocess.TimeoutExpired` is caught and converted to a `CommandResult` with
   `exit_code=124` and a descriptive `stderr` message, following the established `exit_code=127`
   pattern for non-subprocess failures.
3. Mode logic (`FAIL_FAST` / `RUN_ALL`) applies to the timeout result without special casing.
4. The 8 existing test classes in `test_gates.py` continue to pass without modification.
5. A new test class verifies the timeout path: mocks `subprocess.run` to raise
   `subprocess.TimeoutExpired`, asserts `exit_code=124` and `passed=False`.
6. The `run_quality_gates()` docstring documents the timeout behavior and `exit_code=124`
   convention.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Q1 and Q2 above
2. Finalize Goals section (particularly whether `timeout` appears in the function signature)
3. Proceed to RT-ICA assessment
4. Delegate implementation to `python3-development:python-cli-architect` and tests to
   `python3-development:python-pytest-architect`

---

## Post-Implementation Annotations

Added by context-refinement agent on 2026-03-21

### Design Refinements

1. **Q1 resolved as Option A (timeout as function parameter)**: The architect chose to expose `timeout: float = 300.0` as a keyword-only parameter rather than a module-level constant. This is a scope expansion relative to the minimal interpretation of the original request (which did not specify a public API change), but aligns with the feature's goal of giving callers control over gate budgets.
   - Original: "Resolution: _pending_" — feature context left this open
   - Actual: `timeout: float = 300.0` keyword-only parameter added to `run_quality_gates()` signature
   - Recorded in: `plan/architect-gates-subprocess-timeout.md`, ADR-001

2. **Q2 resolved as Option A (no explicit kill)**: Python's `subprocess.run` kills the child process before raising `TimeoutExpired`, making explicit `Popen`/`kill()`/`wait()` refactoring unnecessary.
   - Original: "Resolution: _pending_" — feature context left this open
   - Actual: Simple `except subprocess.TimeoutExpired` block, no process cleanup code
   - Recorded in: `plan/architect-gates-subprocess-timeout.md`, ADR-002

3. **Test method count 6, not implied by AC4**: AC4 said "new test class verifies timeout behavior" without specifying method count. The implementation added 6 test methods covering exit_code, stderr format, passed=False, FAIL_FAST mode, RUN_ALL mode, and custom timeout forwarding.
   - Original: AC4 — "New test class verifies timeout behavior"
   - Actual: `TestSubprocessTimeoutContract` with 6 methods; total test count 38
