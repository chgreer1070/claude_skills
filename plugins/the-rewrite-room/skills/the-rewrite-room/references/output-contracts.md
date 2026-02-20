# Output Contracts

Every workflow in the-rewrite-room terminates with a STATUS block. This file defines all STATUS block variants and their required fields.

## Base Contract — status-block-v1

Used by: documentation-sync, authoring, formatting-validation, research-utilities

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [1-2 sentences, factual — no speculation, no vague quantifiers]
ARTIFACTS:
  - path/to/output-file.md
VALIDATION:
  - validator-name: PASS|FAIL
NOTES: [only if needed — issues, caveats, follow-up tasks]
```

Field rules:

- `STATUS` — exactly one of DONE, BLOCKED, FAILED. No other values.
- `SUMMARY` — factual observation of what occurred. No "likely", "probably", "I think".
- `ARTIFACTS` — list every file written. If no file was written, write `- (none — in-place output)`.
- `VALIDATION` — list every validator run with PASS or FAIL. Omit validators that were skipped with a note in NOTES.
- `NOTES` — optional. Include only when BLOCKED (state the blocker), FAILED (state what failed and why), or when follow-up tasks are needed.

## Audit Contract — audit-block-v1

Used by: drift-audit

Extends status-block-v1 with evidence requirements.

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [factual — N findings: M undocumented, K stale refs, J documented-but-removed]
ARTIFACTS:
  - path/to/audit-report.md
VALIDATION:
  - link-checker: PASS|FAIL
  - citation-check: PASS|FAIL
EVIDENCE:
  findings_total: N
  findings_with_citations: N
  findings_without_citations: 0
NOTES: [only if needed]
```

Additional constraint: `citation-check` is FAIL if ANY finding lacks a file:line citation. `findings_without_citations` MUST be 0 for STATUS DONE.

## Summary Contract — summary-block-v1

Used by: summarization

Extends status-block-v1 with fidelity reporting.

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [factual — what source was read, what was found]
ARTIFACTS:
  - path/to/summary-output.md
VALIDATION:
  - fidelity-enforcer: PASS|FAIL
FIDELITY:
  sources_read: N
  sources_inaccessible: N
  confidence: high|medium|low
  confidence_notes: [reason if not high — omit if high]
NOTES: [only if needed]
```

Additional constraint: `fidelity-enforcer` is FAIL if output contains vague quantifiers where counts were available, if confidence field is absent, or if any required section (What Was Found, What Was NOT Found, Uncertain, Sources) is missing.

## Optimization Contract — optimization-block-v1

Used by: prompt-optimization

Extends status-block-v1 with diff reporting.

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [factual — what was optimized, key structural changes made]
ARTIFACTS:
  - path/to/optimized-file.md
VALIDATION:
  - frontmatter-validator: PASS|FAIL
  - prompt-structure-validator: PASS|FAIL
DIFF:
  tokens_before: N
  tokens_after: N
  delta: +N | -N
  prohibitions_converted: N
  sections_added: N
NOTES: [only if needed]
```

Additional constraint: If `tokens_after > tokens_before`, NOTES MUST include "Token count increased by N — review before committing."

## Status Value Semantics

| Status | Meaning | When to Use |
|---|---|---|
| DONE | All validators PASS; artifact meets contract | Everything completed successfully |
| BLOCKED | Cannot proceed; user action required | Missing input, permission needed, ambiguous intent |
| FAILED | Validator returned non-zero; artifact produced but failed quality check | Output exists but does not meet the contract |

BLOCKED and FAILED are distinct:

- BLOCKED means the workflow did not complete — the artifact may not exist
- FAILED means the workflow completed but the output failed validation — the artifact exists but should not be trusted without fixing the issue noted in NOTES
