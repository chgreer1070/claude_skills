# Documentation Sync Report

**Workflow:** documentation-sync
**Date:** {{date}}
**Target Skill:** {{target_skill_path}}
**Upstream Source:** {{upstream_url}}

## STATUS

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: {{summary}}
ARTIFACTS:
  - {{sync_script_path}}
  - {{target_skill_path}}/SKILL.md (updated)
VALIDATION:
  - link-checker: {{link_checker_result}}
  - frontmatter-validator: {{frontmatter_result}}
```

## Sync Configuration

| Field | Value |
|---|---|
| Source URL | {{upstream_url}} |
| Destination | {{destination_path}} |
| Cooldown period | {{cooldown_hours}} hours |
| Transformation rules | {{transformation_rules}} |

## Files Updated

{{#each updated_files}}

- `{{path}}` — {{bytes}} bytes, {{lines}} lines

{{/each}}

## Files Removed

{{#each removed_files}}

- `{{path}}` — removed (no longer in upstream source)

{{/each}}

## How to Re-Run

```bash
uv run {{sync_script_path}} --force
```

Omit `--force` to respect the cooldown period. The script will exit early if run within {{cooldown_hours}} hours of the last sync.

## Next Steps

- [ ] Run drift-audit to verify local docs now match the canonical source
- [ ] Commit updated reference files
