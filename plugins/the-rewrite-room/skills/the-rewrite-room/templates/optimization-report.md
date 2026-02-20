# Prompt Optimization Report

**Workflow:** prompt-optimization
**Date:** {{date}}
**Target:** {{target_path}}
**Scope:** {{scope}}

## STATUS

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: {{summary}}
ARTIFACTS:
  - {{target_path}}
VALIDATION:
  - frontmatter-validator: {{frontmatter_result}}
  - prompt-structure-validator: {{structure_result}}
DIFF:
  tokens_before: {{tokens_before}}
  tokens_after: {{tokens_after}}
  delta: {{token_delta}}
  prohibitions_converted: {{prohibitions_converted}}
  sections_added: {{sections_added}}
```

## RT-ICA Pre-Check

{{rt_ica_assessment}}

## Changes Applied

### Structural Changes

{{#each structural_changes}}

- {{description}}

{{/each}}

### Prohibition Conversions

{{#each prohibition_conversions}}

**Before:**

```text
{{before}}
```

**After:**

```text
{{after}}
```

{{/each}}

### Sections Added

{{#each sections_added}}

- `{{section_name}}` — {{reason}}

{{/each}}

## CoVe Verification

{{cove_verification_result}}

## Token Impact

| Metric | Before | After | Delta |
|---|---|---|---|
| Estimated tokens | {{tokens_before}} | {{tokens_after}} | {{token_delta}} |
| Prohibition patterns | {{prohibitions_before}} | {{prohibitions_after}} | {{prohibitions_delta}} |
| Required sections | {{sections_before}} | {{sections_after}} | {{sections_delta}} |
