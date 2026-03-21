# Feature Context: Quality Gates Runner

## Problem

The `/work-milestone` workflow calls quality gate commands at two checkpoints — before merge and
before landing — but there is no standardised executor for those commands. Gate commands are
plain strings declared in `quality_gates.pre_merge` and `quality_gates.post_merge` of the
dispatch YAML. Currently there is nothing that:

- runs those strings via subprocess in a deterministic way
- captures exit code, stdout, and stderr per command
- returns a structured result that the caller can act on
- distinguishes fail-fast (abort on first failure) from run-all (collect all results)
- handles the "command not found" case with an actionable error rather than a raw OS error

## Outcome

A new module `dispatch_schema/gates.py` that exposes:

- `CommandResult` — Pydantic model capturing the outcome of one subprocess invocation
- `GateResult` — Pydantic model summarising a full gate run (list of CommandResults, aggregate pass/fail)
- `run_quality_gates()` — function that accepts a list of gate command strings and a mode flag,
  executes them, and returns a `GateResult`

The module fits inside the existing `dispatch_schema` package, follows the same Pydantic
BaseModel patterns already in `core/models.py`, and is re-exported from `dispatch_schema/__init__.py`.

`run_quality_gates` is **not** exposed as an MCP tool. It is a library function called by
`/work-milestone` in-process. MCP exposure would require a running server context and adds no
value for a synchronous gate check.

## Story

GitHub issue #922.

## Constraints

- Python 3.11+, stdlib `subprocess`, Pydantic BaseModel
- NEVER `shell=True` in subprocess calls
- Commands are split via `shlex.split` before passing to subprocess
- `shutil.which` is the command-not-found check mechanism
- No new top-level dependencies — gates.py uses only stdlib + pydantic (already a dep)
