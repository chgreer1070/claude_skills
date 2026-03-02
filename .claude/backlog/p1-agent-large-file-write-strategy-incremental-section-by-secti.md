---
name: 'Agent Large File Write Strategy: Incremental Section-by-Section Writing'
description: Sub-agents writing large files (>30K chars) via single Write calls timeout or get stuck. Need a strategy where agents write the file structure/skeleton first, then fill in content section-by-section using Edit calls. Observed during task planner writing 57,800 char task plan that stalled. The pattern should be documented as agent guidance and possibly enforced via hooks or delegation instructions.
metadata:
  topic: agent-large-file-write-strategy-incremental-section-by-secti
  source: Session observation
  added: '2026-03-01'
  priority: P1
  type: Feature
  status: open
  issue: '#367'
  last_synced: '2026-03-02T04:50:43Z'
  groomed: '2026-03-02'
---

## Fact-Check

**Claims checked**: 2
**VERIFIED**: 2 | **REFUTED**: 0 | **INCONCLUSIVE**: 0

1. **Sub-agents writing large files (>30K chars) via single Write calls timeout or get stuck** — VERIFIED. First-hand session observation documented in commit 8beddfb (2026-03-01). The task planner agent stalled during a single Write call for a large task plan file.
2. **Observed during task planner writing 57,800 char task plan** — VERIFIED. Commit 8beddfb created during the same session, adding a 330-line context manifest to tasks-14-console-forwarding-mcp-server-plugin.md. The backlog item was created as a direct response to the observed stall.

## RT-ICA

**Goal**: Prevent sub-agent stalls when writing large files by establishing an incremental write strategy (skeleton + Edit fills).

**Conditions**:
1. Understanding of Write tool timeout/stall behavior for large content | Status: AVAILABLE | Evidence: Direct observation in session (commit 8beddfb)
2. Knowledge of Edit tool as incremental content insertion mechanism | Status: AVAILABLE | Evidence: Edit tool is a core Claude Code tool, well-documented
3. Delegation instruction injection point (where to document the strategy) | Status: DERIVABLE | Basis: CLAUDE.md rules, agent prompts, delegation-format.md — need to determine best location
4. Hook enforcement mechanism (optional) | Status: DERIVABLE | Basis: prek hooks, SubagentStop/PostToolUse hook patterns already exist in the codebase
5. Threshold for 'large file' definition | Status: DERIVABLE | Basis: Observed at 57,800 chars; need to determine safe threshold (e.g., 20K, 30K)
6. Agent file write patterns across existing agents | Status: DERIVABLE | Basis: Can be surveyed from agents/ directory

**Decision**: APPROVED
**Missing**: None
**Assumptions to confirm**: Exact character threshold for triggering incremental writes; best location for guidance (CLAUDE.md rule vs agent-level instruction vs hook)

## Groomed (2026-03-02)

### Priority

9/10 — Prevents sub-agent stalls during critical planning tasks; directly blocks SAM execution with large output files (57.8K chars observed); no current workaround documented.

### Impact

- Blocks: Sub-agents writing task plans, architecture docs, feature specifications that exceed ~30K chars
- Bottleneck: `swarm-task-planner` agent and any delegated agent that must produce large consolidated files

### Benefits

- Enables sub-agents to complete large-file writes without stalling
- Establishes reusable pattern for incremental file generation across agent ecosystem
- Reduces risk of silent Write timeouts during critical workflow stages (planning, synthesis)

### Expected Behavior

When a sub-agent must write a file larger than a safe threshold (e.g., 20K–30K chars):

1. Agent writes the file structure/skeleton first (TOC, section headers, minimal metadata)
2. Agent then fills content incrementally using Edit calls (section-by-section, subsection-by-subsection)
3. Agent completes the file without stalling or exceeding tool timeout limits

### Desired Structure

A documented pattern adopted across the agent ecosystem consisting of:

1. Canonical guidance document describing the incremental write strategy (skeleton-first, Edit-fill pattern)
2. Character threshold definition (safe limit for single Write calls, trigger point for incremental strategy)
3. Injection point(s) for the guidance:
   - CLAUDE.md or a new `.claude/rules/agent-file-writing-strategy.md` rule
   - Delegation instructions in agent prompts (how sub-agents read the pattern)
   - Optional: hook enforcement (PreToolUse hook to warn on large-content Write calls)
4. Agent-specific implementation examples (e.g., updated `swarm-task-planner` prompt showing the pattern in action)

### Acceptance Criteria

1. Guidance document exists and describes the skeleton-first, Edit-fill pattern with concrete examples
2. Document specifies character threshold (derivable from session: 57.8K failed; safe threshold to be determined via testing, estimated 20K–30K)
3. Guidance is linked from or embedded in:
   - At least one of: CLAUDE.md (new agent-file-writing rule), delegation-format.md, or new dedicated rule file
   - Swarm-task-planner agent frontmatter (whenToUse or skill loading reference)
4. At least one existing large-output agent (e.g., swarm-task-planner) has been updated to demonstrate the pattern
5. Guidance is testable: create a minimal test case (agent writing >30K chars) and verify completion without stall

### Resources

| Type | Item |
|------|------|
| Prior work | Commit 8beddfb (session observation: task planner stall at 57.8K chars) |
| Agent | swarm-task-planner (plugins/python3-development/agents/swarm-task-planner.md, plugins/development-harness/agents/swarm-task-planner.md) |
| Rule reference | delegation-format.md (.claude/rules/delegation-format.md) |
| Rule reference | CLAUDE.md (.claude/CLAUDE.md — agent-facing project instructions) |
| Hook reference | claude-code.md (plugins/plugin-creator/skills/hooks-guide/references/claude-code.md — PreToolUse/PostToolUse events) |

### Dependencies

- Depends on: None — this is a standalone guardrail item
- Blocks: Any future agent-writing-large-files tasks (e.g., if new agents generate comprehensive documentation)

### Effort

Small — Guidance writing + updating 1–2 agent prompts + minimal testing. Estimated 2–4 hours.

- Guidance writing: 1 hour (document pattern, examples, threshold)
- Agent prompt updates: 1 hour (swarm-task-planner + 1 other agent)
- Testing/validation: 1 hour (write >30K test case, verify completion)