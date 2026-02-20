---
workflow: documentation-sync
canonical_skill: add-doc-updater
canonical_path: plugins/plugin-creator/skills/add-doc-updater/SKILL.md
version: "1.0"
output_contract: status-block-v1
---

# Documentation Sync Workflow

## Purpose

Outbound sync pipeline — downloads upstream external documentation into a skill's `references/` directory. Creates a Python sync script with cooldown enforcement that can be re-run to keep documentation current.

This workflow is directional: EXTERNAL SOURCE → LOCAL SKILL. It does not audit internal docs against code (that is drift-audit).

## Entrypoint Contract

### Required Inputs

- Target skill path — which skill receives the documentation
- Upstream source URL — where to download documentation from

### Optional Inputs

- Cooldown period (default: 24 hours)
- Transformation rules (strip Hugo shortcodes, transform links)

## Steps

1. **Activate add-doc-updater skill** — `Skill(command: "plugin-creator:add-doc-updater")`
2. **Provide target and source** — skill creates a 5-phase implementation workflow
3. **Delegate to @python-cli-architect** — creates the sync script using PEP 723
4. **Delegate to @python-code-reviewer** — quality review of sync script
5. **Run prek quality gates** — format, lint, execute-bit check
6. **Validate integration** — confirm sync script is referenced in SKILL.md execution protocol
7. **Chain to drift-audit** — after sync, verify local docs now match the canonical source

## Validation Gates

- HARD STOP — sync script not PEP 723 compliant: fix before proceeding
- HARD STOP — sync script lacks cooldown enforcement: add before proceeding
- SOFT STOP — Hugo shortcodes not removed from downloaded content: flag for manual review

## Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [what was synced and where]
ARTIFACTS:
  - path/to/sync-script.py
  - path/to/references/synced-docs.md
VALIDATION:
  - link-checker: PASS|FAIL
  - frontmatter-validator: PASS|FAIL
NOTES: [only if needed]
```

## Adapter Notes

The `add-doc-updater` skill in `plugins/plugin-creator/skills/add-doc-updater/SKILL.md` orchestrates this workflow. The adapter at [./adapters/add-doc-updater-adapter.md](./adapters/add-doc-updater-adapter.md) maps its phase completion output to the status-block-v1 format.
