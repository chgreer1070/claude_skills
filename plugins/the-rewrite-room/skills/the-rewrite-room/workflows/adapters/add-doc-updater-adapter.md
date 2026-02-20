---
adapter: add-doc-updater-adapter
wraps: plugins/plugin-creator/skills/add-doc-updater/SKILL.md
normalizes_to: status-block-v1
version: "1.0"
---

# add-doc-updater Adapter

## Wrapped Component

`plugins/plugin-creator/skills/add-doc-updater/SKILL.md`

This skill orchestrates a 5-phase workflow that ends with the sync script integrated into the target skill's SKILL.md.

## Native Output Contract

The `add-doc-updater` skill does not produce a STATUS block. It produces:

1. A Python sync script at a path inside the target skill's `scripts/` directory
2. A reference to that script added to the target SKILL.md execution protocol
3. Phase completion output via sub-agent STATUS/BLOCKED blocks

## Adapter Transformation

When the `add-doc-updater` skill completes all 5 phases, the rewrite-room wraps the result as:

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: Documentation sync pipeline added to {skill-name}. Sync script created at {script-path}.
ARTIFACTS:
  - {skill-path}/scripts/{sync-script-name}.py
  - {skill-path}/SKILL.md (updated with execution protocol)
VALIDATION:
  - link-checker: PASS|FAIL
  - frontmatter-validator: PASS|FAIL
NOTES: Run `uv run {script-path} --force` to trigger immediate sync.
```

## Validators Added by Adapter

- `link-checker` — verifies sync script reference in SKILL.md resolves
- `frontmatter-validator` — re-validates SKILL.md frontmatter after modification

## BLOCKED Mapping

If any phase of `add-doc-updater` returns BLOCKED, the adapter propagates BLOCKED with the original NOTES content.
