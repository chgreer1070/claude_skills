# Audit Report

**Workflow:** drift-audit
**Date:** {{date}}
**Scope:** {{scope}}

## STATUS

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: {{summary}}
ARTIFACTS:
  - {{artifact_paths}}
VALIDATION:
  - link-checker: {{link_checker_result}}
  - citation-check: {{citation_check_result}}
EVIDENCE:
  findings_total: {{findings_total}}
  findings_with_citations: {{findings_with_citations}}
  findings_without_citations: 0
```

## Findings

### Undocumented Features

Features present in code but absent from all documentation:

{{#each undocumented_features}}

- **{{name}}** — `{{file}}:{{line}}`
  > {{evidence_quote}}

{{/each}}

### Documented but Removed

Features referenced in documentation that no longer exist in the codebase:

{{#each documented_removed}}

- **{{name}}** — docs reference at `{{doc_file}}:{{line}}`, not found in code
  > {{evidence_quote}}

{{/each}}

### Stale Cross-References

Links or symbol references that have drifted from their targets:

{{#each stale_refs}}

- `{{source_file}}:{{line}}` references `{{target}}` ({{reason}})

{{/each}}

### Mismatched Signatures

Documented signatures that do not match the implementation:

{{#each mismatched}}

- **{{name}}** — documented as `{{documented_signature}}`, implemented as `{{actual_signature}}`
  > Code evidence: `{{code_file}}:{{code_line}}`

{{/each}}

## Evidence Checklist

- [ ] All findings have file:line citations
- [ ] No speculation ("likely", "probably") present in any finding
- [ ] Commit SHAs included where historical analysis was performed
- [ ] All cross-references in audit output itself resolve (link-checker PASS)
