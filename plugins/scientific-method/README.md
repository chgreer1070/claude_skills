# scientific-method

> Use when debugging, investigating root causes, designing experiments, or performing scientific analysis — enforces hypothesis-driven reasoning, evidence-first observation, causality validation, and structured output templates. Use when facing unknowns, repeated failures, or complex investigations requiring rigorous methodology.

**Version**: 1.1.0 | **Author**: [Jamie Nelson](https://github.com/bitflight-devops)

---

## Overview

The `scientific-method` plugin consolidates three investigation and debugging skills into a unified plugin with shared canonical reference files. It replaces the standalone `scientific-thinking`, `experiment-protocol`, and `evidence-first-debugging` skills with a coherent methodology built on a single source of truth.

**Architecture**: Three thin skill wrappers share a `shared/` reference directory. The shared files are the canonical methodology — each skill SKILL.md declares its responsibility scope and loads the relevant shared files.

---

## Installation

```bash
/plugin install scientific-method@jamie-bitflight-skills
```

Or load for the current session only:

```bash
claude --plugin-dir ./plugins/scientific-method
```

---

## Skills

### `/scientific-method:scientific-thinking`

**When to use**: Starting any investigation, debugging session, unknown root cause, or complex problem requiring structured reasoning.

Loads the unified investigation template and guides you through hypothesis formation, evidence collection, experiment design, causality validation, and conclusion.

**Invocation**:

```text
/scientific-method:scientific-thinking
```

Or Claude auto-invokes when you describe a debugging problem, investigation, or unknown failure.

---

### `/scientific-method:evidence-first-debugging`

**When to use**: Debugging a specific defect, error, or system misbehavior where evidence collection is the priority.

Focuses on the evidence-gathering and causality-check phases of the investigation template. Enforces observation-before-assumption discipline: raw signals only, verbatim snippets, disclosed truncation.

**Invocation**:

```text
/scientific-method:evidence-first-debugging
```

---

### `/scientific-method:experiment-protocol`

**When to use**: Designing and running controlled experiments — A/B tests, performance benchmarks, configuration comparisons, or any test requiring isolation of variables.

Produces a structured experiment plan with hypothesis, predictions, confound isolation, and result recording.

**Invocation**:

```text
/scientific-method:experiment-protocol
```

---

## Agent

### `retrospective-analyst`

Produces structured process-quality artefacts after an investigation reaches `resolved-verified` status:

- Mermaid `sequenceDiagram` timeline — one node per hypothesis and experiment, labelled PASS/FAIL/UNEXPECTED
- Result analysis — what worked, what did not, patterns observed across iterations
- Retrospective — lessons learned, anti-patterns encountered, rubric update recommendations

The SubagentStop hook in this plugin detects `resolved-verified` status in investigation output and
notifies you to invoke this agent. Pass the full investigation output (all 14 sections) as input.

---

## Hooks

This plugin registers a `SubagentStop` hook that monitors investigation output. When an investigation
sub-agent finishes with `status: resolved-verified` in section 14, the hook notifies you that the
`retrospective-analyst` agent is available to produce a timeline and retrospective.

The hook is informational — it never blocks or fails agent output.

---

## Shared Reference Files

All skills reference these canonical files in `shared/`:

| File | Purpose |
|------|---------|
| `shared/investigation-template.md` | 15-section unified investigation template (sections 0–14) |
| `shared/evidence-rules.md` | Rules for evidence collection — raw signals, truncation disclosure, verbatim snippets |
| `shared/causality-check.md` | Causality classification rules — causal-supported, correlated-only, unrelated, unknown |
| `shared/investigation-workflow.md` | Mermaid workflow diagram for the full investigation lifecycle |
| `shared/extensions/debugging-extensions.md` | Domain extensions for software debugging investigations |
| `shared/extensions/performance-extensions.md` | Domain extensions for performance analysis investigations |

---

## Investigation Template Overview

The unified investigation template covers 15 sections filled progressively:

**Before execution (sections 0–7)**:
- `0 CONTEXT` — goal, system, environment, baseline
- `1 ISSUE STATEMENT` — symptom, expected vs actual, repro status
- `2 OBSERVATIONS` — raw signals with evidence IDs and truncation disclosure
- `3 FACTS` — evidence-cited statements only
- `4 HYPOTHESES` — falsifiable H0/H1 with fact references
- `5 PREDICTIONS` — observable outcomes if H1 is correct
- `6 EXPERIMENT PLAN` — Path A/B tests with expected outcomes per hypothesis
- `7 CONFOUNDING VARIABLES` — isolation plan

**During and after execution (sections 8–14)**:
- `8 ACTIONS` — commands/changes with evidence
- `9 RESULTS` — observed outcomes with evidence
- `10 CAUSALITY CHECK` — causal/correlated/unrelated/unknown classification
- `11 CONCLUSION` — reject or fail-to-reject H0 with evidence citations
- `12 CHANGES` — diff summary with key hunks
- `13 VERIFICATION` — verification command and result
- `14 EVIDENCE LOG` — complete evidence inventory

---

## Key Principles

- **Observation over assumption**: Fill sections 2–3 from raw tool output, not interpretation
- **Falsifiable hypotheses**: Every H1 must state "If H1 is true, we would observe X"
- **Evidence-cited facts**: Every fact in section 3 cites an evidence ID from section 2
- **Causality requires falsification**: Classification in section 10 requires a falsification test, not intuition
- **Truncation disclosure**: Any truncated output discloses `total=<N>, shown=<M>, method=<head|tail|grep>`

---

## Migration from Previous Skills

| Old skill | New invocation |
|-----------|---------------|
| `/scientific-thinking` | `/scientific-method:scientific-thinking` |
| `/experiment-protocol` | `/scientific-method:experiment-protocol` |
| `/evidence-first-debugging:evidence-first-debugging` | `/scientific-method:evidence-first-debugging` |

Redirect stubs remain at the old locations for backward compatibility.

---

## Source

Consolidated from:
- `.claude/skills/scientific-thinking/` (personal skill)
- `.claude/skills/experiment-protocol/` (personal skill)
- `plugins/evidence-first-debugging/` (retired plugin, content absorbed)
- `.claude/knowledge/workflow-diagrams/investigation-workflow.md` (migrated to `shared/`)
