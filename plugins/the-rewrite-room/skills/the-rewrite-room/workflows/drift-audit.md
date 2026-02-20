---
workflow: drift-audit
canonical_agent: doc-drift-auditor
canonical_path: plugins/development-harness/agents/doc-drift-auditor.md
version: "1.0"
output_contract: audit-block-v1
---

# Drift Audit Workflow

## Purpose

Evidence-based comparison of documentation versus code using git forensics.

Detects:

- Implemented features not mentioned in any documentation
- Features documented as existing that are no longer in the codebase
- Stale cross-references pointing to renamed or deleted symbols
- Documentation whose language does not match the actual implementation

## Entrypoint Contract

### Required Inputs

- Source — at minimum one code file AND one documentation file, or a git diff showing both
- Scope — explicit list of file paths OR inferred from changed files in branch

### Optional Inputs

- Commit range (for git-forensics historical analysis)
- Specific symbols to check (function names, class names, API endpoints)

## Steps

1. **Identify scope** — list changed code files and their paired documentation files
2. **Delegate to doc-drift-auditor agent** — provide file paths and commit range; do NOT summarize file contents
3. **Collect findings** — agent returns evidence-based report with file:line citations
4. **Run link-checker validator** — verify cross-references in documentation files still resolve
5. **Chain to formatting-validation** — if any markdown files were modified

## Validation Gates

- HARD STOP — any claim without file:line citation: reject, request re-run
- HARD STOP — agent output contains "likely" or "probably": trigger hallucination check
- SOFT STOP — broken cross-reference found: flag in report, do not block completion

## Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [1-2 sentences, factual — no speculation]
ARTIFACTS:
  - path/to/audit-report.md
VALIDATION:
  - link-checker: PASS|FAIL
  - citation-check: PASS|FAIL
NOTES: [only if needed]
```

See [../references/output-contracts.md](../references/output-contracts.md) for the full audit-block-v1 specification.

## Evidence Requirements

Every finding MUST include:

- File path (relative to repo root)
- Line number(s)
- Commit SHA (when historical analysis is performed)
- Quoted text from source confirming the finding

## Adapter Notes

The `doc-drift-auditor` agent in `plugins/development-harness/agents/doc-drift-auditor.md` already produces evidence-based output in the development-harness subagent-contract format. The adapter at [./adapters/doc-drift-auditor-adapter.md](./adapters/doc-drift-auditor-adapter.md) normalizes this to the audit-block-v1 STATUS block format.
