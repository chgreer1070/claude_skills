---
workflow: summarization
canonical_skill: summarizer
canonical_path: plugins/summarizer/skills/summarizer/SKILL.md
version: "1.0"
output_contract: summary-block-v1
---

# Summarization Workflow

## Purpose

Fidelity-enforced summarization of files, URLs, images, or multiple sources. The summarizer skill dispatches to type-specific strategies (file, URL, image, multi-source) and enforces fidelity rules throughout.

## Entrypoint Contract

### Required Inputs

- Source — file path, URL, image path, or list of sources (multi-source)
- Format — structured (default), bullets, tldr, json, table, outline

### Optional Inputs

- Focus area — specific sections or topics to prioritize
- Audience — who will read the summary

## Steps

1. **Load summarizer skill** — `Skill(command: "summarizer:summarizer")`
2. **Determine source type** — file, URL, image, or multi-source manifest
3. **Read source in full** — MUST read before summarizing (Fidelity Rule 1)
4. **Extract before abstracting** — identify key passages first (Fidelity Rule 2)
5. **Dispatch to strategy** — file-summarization, url-summarization, image-summarization, or multi-source-synthesis
6. **Validate fidelity** — check against all 7 fidelity rules before producing final output
7. **Output structured summary** — with YAML frontmatter, confidence, sources

## Fidelity Constraints

All summarization output MUST satisfy the rules in [../references/fidelity-rules.md](../references/fidelity-rules.md). Key rules:

- Rule 1 — Read before summarizing. Never guess from filename.
- Rule 2 — Extract before abstracting. Create audit trail.
- Rule 3 — Preserve counts and specifics exactly.
- Rule 4 — Distinguish absence from nonexistence.
- Rule 5 — No lossy re-summarization. Do not summarize a summary.
- Rule 6 — State confidence explicitly.
- Rule 7 — Use structured output format.

## Validation Gates

- HARD STOP — output contains "likely" or "probably" as causal language: reject, re-run
- HARD STOP — vague quantifier found ("many", "several", "some") where count was available: reject
- HARD STOP — confidence field absent from YAML frontmatter: add before finalizing
- SOFT STOP — source was not readable: state "Unable to read [source]: [reason]" and continue with available sources

## Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [1-2 sentences describing the source and what was found]
ARTIFACTS:
  - path/to/summary-output.md
VALIDATION:
  - fidelity-enforcer: PASS|FAIL
FIDELITY:
  sources_read: N
  sources_inaccessible: N
  confidence: high|medium|low
NOTES: [only if needed]
```

See [../references/output-contracts.md](../references/output-contracts.md) for the full summary-block-v1 specification.

## Adapter Notes

The summarizer skill's SubagentStop hook validates output against fidelity rules automatically. The adapter at [./adapters/summarizer-adapter.md](./adapters/summarizer-adapter.md) maps summarizer output to the summary-block-v1 STATUS format.
