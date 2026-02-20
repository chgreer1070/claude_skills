# Agent Orchestration Reference

This document describes patterns for orchestrating Claude Code sub-agents effectively.

## Core Principles

Effective orchestration rests on three principles: delegation fidelity, context isolation, and output contracts.

**Delegation fidelity** means the orchestrator passes file paths and outcomes to agents — never pre-summarized content. Agents verify source files directly. Pre-summarized input bypasses Chain of Verification and introduces stale data.

**Context isolation** means each agent gets a fresh context window. The orchestrator's context is shared across the entire session and should not be consumed by investigative reads that produce no edits.

**Output contracts** mean every agent returns a STATUS block with ARTIFACTS, VALIDATION, and NOTES. The orchestrator relays these verbatim to the user — it does not re-interpret or re-summarize agent output.

## Agent Selection

Select agents by task type, not task size.

For read-only retrieval tasks with no reasoning required, the Explore agent (Haiku) is appropriate. For retrieval with reasoning, use the Plan agent. For implementation, use general-purpose agents or specialist agents when one exists for the task domain.

The following agents are available for documentation and authoring tasks:

- `@doc-drift-auditor` — evidence-based comparison of docs vs. code
- `@contextual-ai-documentation-optimizer` — AI-facing documentation optimization
- `@file-summarizer` — file content summarization with fidelity enforcement
- `@url-summarizer` — URL content summarization
- `@image-summarizer` — image description via multimodal capabilities
- `@service-docs-maintainer` — post-implementation documentation sync

## Delegation Template

Every Task tool invocation MUST follow this template:

```text
Task: [agent-name]
Goal: [what outcome is needed — not what steps to take]
Scope: [files, directories, or git range]
Constraints: [hard requirements — format, validators, output path]
Definition of Done: [how to know the task is complete]
```

Deviating from this template produces under-specified delegations that agents complete incorrectly.

## Output Contract Enforcement

The orchestrator MUST verify agent output before relaying to the user:

1. STATUS field is DONE, BLOCKED, or FAILED (no other values)
2. ARTIFACTS lists every file written
3. VALIDATION lists every validator run with PASS or FAIL result
4. If STATUS is DONE but any validator is FAIL — re-run or escalate

If the agent returns BLOCKED, the orchestrator must resolve the blocker and re-delegate. It MUST NOT attempt to complete the blocked task itself.

## Anti-Patterns

The following patterns have been validated as failure modes in production orchestration sessions:

**Investigation escalation**: The orchestrator reads one file, findings justify reading another, leading to self-implementation after 10+ reads. Trigger: 3 consecutive Read calls on source files without an intervening Edit, Write, or Task delegation.

**Pre-gathering for agents**: The orchestrator reads files to "save the agent time" then passes summaries instead of paths. This bypasses Chain of Verification and introduces stale data.

**Polling loops**: The orchestrator sends repeated status-check messages to idle teammates. Team agents send completion messages automatically — polling burns turns and accumulates context.

**Delegation bypass**: "This change is small enough to do myself." There is no size threshold below which delegation is optional. The orchestrator delegates; agents implement.

## Context Window Discipline

The orchestrator's context window is shared across the entire session. Agents get fresh context per task.

Files the orchestrator MUST NOT read unless it will Edit or Write them in the same turn:

- Source code files (`.py`, `.js`, `.ts`)
- Configuration files (`.toml`, `.yaml`, `.yml`, `.json`)
- Test files
- Diagnostic command output

Before every Read or Grep on a source or config file, apply the falsifiable test: "Will I Edit or Write this file in this turn?" If NO — pass the path to an agent instead.

## Session Examples

A session that wasted 17,300 tokens on 14 investigative reads producing zero edits has been documented. In that session, the orchestrator read 7 Python files, 4 YAML configs, and 3 test files while "planning" an implementation — then delegated the same files to an agent anyway. The investigation added zero value.

SOURCE: session-orchestrator-antipatterns-2026-02-19.md (session 73e28879)

## Quality Gates

Every implementation task MUST pass these gates before STATUS DONE:

- Format: `uv run ruff format .`
- Lint: `uv run ruff check .`
- Type check: `uv run basedpyright` or `uv run mypy src/`
- Tests: `uv run pytest` (>80% coverage minimum)

Skipping quality gates produces technical debt that compounds across sessions. The gates exist because the agent will attempt to skip them given the opportunity.
