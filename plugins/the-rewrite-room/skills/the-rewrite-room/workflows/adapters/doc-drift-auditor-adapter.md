---
adapter: doc-drift-auditor-adapter
wraps: plugins/development-harness/agents/doc-drift-auditor.md
normalizes_to: audit-block-v1
version: "1.0"
---

# doc-drift-auditor Adapter

## Wrapped Component

`plugins/development-harness/agents/doc-drift-auditor.md`

This agent produces a development-harness subagent-contract STATUS block with ARTIFACTS listing and RISKS section. Output path is `.claude/reports/DOCUMENTATION_DRIFT_AUDIT.md` by convention.

## Native Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
ARTIFACTS:
  - .claude/reports/DOCUMENTATION_DRIFT_AUDIT.md
RISKS:
  - [risk description]
```

## Adapter Transformation

The adapter maps the native output to `audit-block-v1`:

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [extracted from first paragraph of DOCUMENTATION_DRIFT_AUDIT.md]
ARTIFACTS:
  - .claude/reports/DOCUMENTATION_DRIFT_AUDIT.md
VALIDATION:
  - link-checker: PASS|FAIL
  - citation-check: PASS|FAIL (all findings have file:line evidence)
NOTES: [RISKS content from native output, if any]
```

## Citation Check Rule

The adapter performs a post-hoc citation check: reads the DOCUMENTATION_DRIFT_AUDIT.md and verifies that every finding includes at minimum one `file:line` reference. If any finding lacks a citation, `citation-check` is set to FAIL and the STATUS is escalated to FAILED.

## Validators Added by Adapter

- `link-checker` — runs after audit to verify all cross-references in audit artifact resolve
- `citation-check` — reads audit output and confirms file:line evidence is present for every finding

## BLOCKED Mapping

If the agent returns BLOCKED, the adapter preserves the BLOCKED status and routes the NOTES content to the NOTES field of the normalized block.
