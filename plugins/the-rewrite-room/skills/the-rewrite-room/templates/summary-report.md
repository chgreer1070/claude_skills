---
source_type: "{{source_type}}"
source_path: "{{source_path}}"
summarized_at: "{{date}}"
method: "{{method}}"
word_count_source: {{word_count_source}}
word_count_summary: {{word_count_summary}}
compression_ratio: {{compression_ratio}}
confidence: "{{confidence}}"
confidence_notes: "{{confidence_notes}}"
---

# Summary Report

**Workflow:** summarization
**Source:** {{source_path}}
**Method:** {{method}}

## STATUS

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: {{status_summary}}
ARTIFACTS:
  - {{output_path}}
VALIDATION:
  - fidelity-enforcer: {{fidelity_result}}
FIDELITY:
  sources_read: {{sources_read}}
  sources_inaccessible: {{sources_inaccessible}}
  confidence: {{confidence}}
```

## Summary

{{summary_text}}

## What Was Found

{{what_was_found}}

## What Was NOT Found

{{what_was_not_found}}

## Uncertain

{{uncertain}}

## Sources

{{#each sources}}

- {{label}} — {{ref}} (accessed {{accessed_date}})

{{/each}}
