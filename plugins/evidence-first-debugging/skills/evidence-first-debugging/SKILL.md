---
name: evidence-first-debugging
description: Use when debugging software, investigating incidents, diagnosing flaky tests, or analyzing performance regressions — enforces a structured output contract that separates facts, evidence, actions, and hypotheses to prevent correlation-causation pollution. Use when an agent might otherwise summarize or speculate instead of reporting observed evidence.
---

# Evidence-First Debugging Output Skill

## Activation

Load this skill when debugging any software issue, investigating an incident, diagnosing flaky tests or performance regressions, or troubleshooting with tool output. Once loaded, every debugging iteration MUST use the output contract below.

## Non-negotiable rules

1. Facts only in FACTS/OBSERVATIONS/RESULTS. No guesses, no causal language unless proven.
2. All hypotheses must be explicitly labeled HYPOTHESIS and include a falsifiable test.
3. Never claim "fixed" unless the failure is reproduced first (or its absence is justified) and then a verification step passes.
4. Every claim must be backed by an EVIDENCE item, or it must be labeled UNKNOWN.
5. If outputs are abbreviated, the agent must disclose abbreviation and provide a stable fingerprint (hash, counts, key lines) so later reasoning is grounded.

## Output contract

For each debugging iteration, the agent MUST output exactly this structure, in this order, with these headings:

### 0) CONTEXT (minimal)

- Goal:
- System/component:
- Baseline commit/build (if known):
- Time window (if relevant):

### 1) ISSUE STATEMENT (testable)

- Symptom:
- Expected:
- Actual:
- Repro status: (reproduced / not reproduced / unknown)
- Repro steps (exact commands or clicks):

### 2) FACTS (known true)

List only items that are directly known without inference.
Each bullet MUST end with an Evidence ID in brackets.

- Fact 1. [E1]
- Fact 2. [E2]

### 3) OBSERVATIONS (raw signals)

Include logs, error messages, metrics, screenshots descriptions, stack traces, tool outputs, etc.

Rules:

- Prefer verbatim snippets (key lines) over paraphrase.
- If truncated, say "TRUNCATED" and include: total lines, shown lines, and a fingerprint.

Format:

- O1: \<what was observed>
  - Snippet:
    - \<line 1>
    - \<line 2>
  - Truncation: (none | TRUNCATED: total=\<N>, shown=\<M>, method=\<head/tail/grep>)
  - Fingerprint: (\<sha256 if available> | \<counts + key tokens>)
  - Evidence: [E#]

### 4) ACTIONS TAKEN (exact, ordered)

Only what was actually done.
Each action MUST include:

- command/change
- location (file path, function, setting)
- intended purpose (what it was trying to test)
- Evidence ID

Format:

- A1: \<command or edit>
  - Location:
  - Intended purpose:
  - Evidence: [E#]

### 5) RESULTS (what changed, measured)

Report outcomes of actions, not interpretations.
Include before/after comparisons where possible.

- R1: \<measured result> [E#]
- R2: \<measured result> [E#]

### 6) CAUSALITY CHECK (gate)

For each action-result relationship, explicitly classify:

- Link L1:
  - Action: A#
  - Result: R#
  - Classification: (causal-supported | correlated-only | unrelated | unknown)
  - Reason (must reference evidence, not intuition):
  - What would falsify causality (test):

Rules:

- "causal-supported" requires:
  - controlled comparison or isolation, AND
  - reproducible effect, AND
  - plausible mechanism consistent with facts (mechanism can be a hypothesis but must be labeled).

### 7) HYPOTHESES (explicit, testable)

Each hypothesis MUST include:

- statement
- why it fits current facts (cite evidence)
- test plan
- expected outcomes that would confirm vs refute

Format:

- H1: \<hypothesis statement>
  - Fits because: [E#]
  - Test:
  - Confirm if:
  - Refute if:

### 8) NEXT STEP (single most valuable)

- Next step:
- Why this step (tie to hypotheses or uncertainty reduction):
- Expected observable outputs (what evidence will be produced):

### 9) STATUS (no hype)

Choose exactly one:

- status: unresolved
- status: mitigated (symptom reduced but root cause unproven)
- status: resolved-verified (verification evidence attached)
- status: unknown (insufficient evidence)

If status is resolved-verified, MUST include:

- Verification command/test:
- Verification output summary:
- Evidence IDs:

## Evidence ID rules

- Evidence IDs are sequential: E1, E2, E3...
- Evidence must be one of:
  - a command output snippet
  - a log excerpt
  - a diff summary (with file paths and key lines)
  - a test report
  - a metric snapshot
  - a screenshot description + source
- If the agent cannot show full output due to context limits, it must still provide:
  - truncation disclosure
  - stable fingerprint
  - the exact command used to generate the output

## Forbidden phrases (unless proven with evidence)

The agent MUST NOT write these in FACTS/RESULTS/STATUS unless verified:

- "fixed"
- "resolved" (unless resolved-verified)
- "root cause is"
- "definitely"
- "must be"

Allowed replacements:

- "hypothesis:"
- "evidence suggests:"
- "observed:"
- "unknown:"

## Minimal diff reporting standard (when code/config changes occur)

When the agent edits files, it MUST report:

- files changed
- high-level summary
- key hunks (only the relevant lines)
- how the change is linked to a hypothesis test

Format:

- Diff summary: \<N> files, \<N> insertions, \<N> deletions [E#]
- Key hunk:
  - file: path/to/file
  - before:
    - ...
  - after:
    - ...
  - why this hunk matters:

## Example mini-iteration (template)

### 0) CONTEXT (minimal)

- Goal:
- System/component:
- Baseline commit/build:
- Time window:

### 1) ISSUE STATEMENT (testable)

- Symptom:
- Expected:
- Actual:
- Repro status:
- Repro steps:

### 2) FACTS (known true)

- [E1]
- [E2]

### 3) OBSERVATIONS (raw signals)

- O1:
  - Snippet:
  - Truncation:
  - Fingerprint:
  - Evidence: [E1]

### 4) ACTIONS TAKEN (exact, ordered)

- A1:
  - Location:
  - Intended purpose:
  - Evidence: [E2]

### 5) RESULTS (what changed, measured)

- R1: [E3]

### 6) CAUSALITY CHECK (gate)

- Link L1:
  - Action: A1
  - Result: R1
  - Classification:
  - Reason:
  - What would falsify causality:

### 7) HYPOTHESES (explicit, testable)

- H1:
  - Fits because: [E1]
  - Test:
  - Confirm if:
  - Refute if:

### 8) NEXT STEP (single most valuable)

- Next step:
- Why this step:
- Expected observable outputs:

### 9) STATUS (no hype)

- status:
