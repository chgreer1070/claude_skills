---
name: gates.py subprocess timeout not applied
description: The subprocess.run call in dispatch_schema/gates.py has no timeout parameter. A hung gate command blocks indefinitely with no recovery. The simplify review fix T01 was supposed to add timeout=300.0 default and convert TimeoutExpired to CommandResult(exit_code=124) but did not complete this change. Follow-up from code review of issue 938.
metadata:
  topic: gatespy-subprocess-timeout-not-applied
  source: 'Code review of Issue #938 — simplify review fixes'
  added: '2026-03-21'
  priority: P1
  type: Bug
  status: open
  issue: '#951'
  last_synced: '2026-03-21T12:21:42Z'
  groomed: '2026-03-21'
  plan: plan/tasks-698-gates-subprocess-timeout.md
---

## RT-ICA

<div><sub>2026-03-21T12:16:29Z</sub>

RT-ICA Snapshot: gates.py subprocess timeout not applied
Goal: Add timeout to subprocess.run in gates.py so hung gate commands fail with exit_code=124 instead of blocking indefinitely.
Conditions:
1. Bug location identified (gates.py:75 subprocess.run call) | Status: AVAILABLE
2. Expected fix behavior defined (timeout=300.0 default, TimeoutExpired → CommandResult(exit_code=124)) | Status: AVAILABLE
3. CommandResult dataclass structure | Status: DERIVABLE
4. Callers of run_gate_commands function | Status: DERIVABLE
5. Whether subprocess.TimeoutExpired import exists | Status: DERIVABLE
AVAILABLE count: 2
DERIVABLE count: 3
MISSING count: 0
</div>

## Fact-Check

<div><sub>2026-03-21T12:18:53Z</sub>

## Fact-Check Summary

**Claims checked**: 3 | **VERIFIED**: 3 | **REFUTED**: 0 | **INCONCLUSIVE**: 0

1. subprocess.run has no timeout parameter — **VERIFIED** (line 75: `subprocess.run(resolved_tokens, capture_output=True, text=True, cwd=cwd, check=False)`)
2. Hung gate blocks indefinitely — **VERIFIED** (no TimeoutExpired handling in file or dispatch_schema/ directory, no signal/watchdog recovery)
3. Fix approach (timeout=300.0, TimeoutExpired → CommandResult(exit_code=124)) — **VERIFIED** (CommandResult accepts arbitrary exit_code int, already handles exit_code=127 for missing commands; subprocess.TimeoutExpired is built-in)

Full report: `.claude/reports/factcheck-gates-timeout-951.md`
</div>

## Groomed (2026-03-21)

### Impact Radius

<div><sub>2026-03-21T12:19:00Z</sub>

### Issue Classification

<div><sub>2026-03-21T12:21:21Z</sub>

**Type**: defect
**Root Cause (5-Whys)**:
1. Why does a hung gate block indefinitely? — subprocess.run has no timeout parameter
2. Why was timeout not included? — Original implementation did not account for non-terminating commands
3. Why was it not caught in review? — The code review for #938 identified it but the fix was not completed
**Classification**: Missing parameter — straightforward defect with known fix
</div>

### Reproducibility

<div><sub>2026-03-21T12:21:31Z</sub>

Create a gate command that hangs (e.g., infinite loop). When `run_quality_gates()` is invoked with this command, the subprocess never times out, the gate result never returns, and the entire dispatch plan stalls. Developers cannot recover without manual intervention (kill subprocess, restart orchestrator).
</div>

### Priority

<div><sub>2026-03-21T12:21:34Z</sub>

P1 — Critical Blocking Issue. Quality gates are the final validation step. A hanging gate blocks feature implementation workflow, dispatch plan execution, and CI/CD pipeline (timeout occurs at job level, not gate level — wastes resources and masks the real problem).
</div>

### Files

<div><sub>2026-03-21T12:21:38Z</sub>

- `plugins/development-harness/dispatch_schema/gates.py` — add timeout parameter to subprocess.run and TimeoutExpired exception handling
- `plugins/development-harness/dispatch_schema/test_dispatch_schema/test_gates.py` — add timeout behavior test
</div>

### Dependencies

<div><sub>2026-03-21T12:21:42Z</sub>

None — `subprocess` is stdlib, `CommandResult` is already in scope. No external libraries required.
</div>


## Impact Radius

### Code — Producers
- `plugins/development-harness/dispatch_schema/gates.py::run_quality_gates()` — contains the subprocess.run call at line 75; needs timeout parameter added and TimeoutExpired exception handling

### Code — Consumers
- `plugins/development-harness/dispatch_schema/__init__.py` — public API export of run_quality_gates
- `plugins/development-harness/dispatch_schema/test_dispatch_schema/test_gates.py` — 8 test cases exercising run_quality_gates; needs new test for timeout behavior

### Documentation
- None identified.

### Configuration / CI
- None identified.

### Agent Instructions
- None identified.

### Systems Inventory
- `gates.py` — producer — contains the bug
- `__init__.py` — re-exporter — no code change needed
- `test_gates.py` — test consumer — needs timeout test added

### Ecosystem Completeness Checklist
- [x] Every code producer updated or verified compatible
- [x] Every code consumer migrated to new interface (no interface change, just added timeout)
- [x] Every stale document updated (none identified)
- [x] Every agent instruction updated (none identified)
- [ ] Test for timeout behavior added
- [x] CI/config files updated and validated (none affected)

Full report: `.claude/reports/impact-gates-timeout-951.md`
</div>

## RT-ICA

<div><sub>2026-03-21T12:21:18Z</sub>

RT-ICA Final: gates.py subprocess timeout not applied
Goal: Add timeout to subprocess.run in gates.py so hung gate commands fail with exit_code=124 instead of blocking indefinitely.
Conditions:
1. Bug location (gates.py:75 subprocess.run call) | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: Grep output line 75
2. Fix behavior (timeout=300.0, TimeoutExpired → CommandResult(exit_code=124)) | Snapshot: AVAILABLE → Final: AVAILABLE | Citation: Fact-check report — CommandResult supports exit_code int, exit_code=127 pattern exists
3. CommandResult dataclass structure | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: Fact-checker verified CommandResult accepts arbitrary exit_code
4. Callers of run_quality_gates | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: Impact-analyst found test_gates.py (8 tests) + __init__.py re-export
5. subprocess.TimeoutExpired import | Snapshot: DERIVABLE → Final: AVAILABLE | Citation: Fact-checker confirmed subprocess.TimeoutExpired is built-in, no new import needed
Changes from snapshot:
- Conditions 3, 4, 5: DERIVABLE → AVAILABLE (resolved by fact-checker and impact-analyst agents)
Decision: APPROVED
</div>