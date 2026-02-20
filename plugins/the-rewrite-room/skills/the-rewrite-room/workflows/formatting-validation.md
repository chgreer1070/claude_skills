---
workflow: formatting-validation
canonical_skill: plugin-creator-lint
canonical_path: plugins/plugin-creator/skills/lint/SKILL.md
canonical_skill_secondary: holistic-linting
canonical_path_secondary: plugins/holistic-linting/skills/holistic-linting/SKILL.md
version: "1.0"
output_contract: status-block-v1
---

# Formatting Validation Workflow

## Purpose

Validates markdown formatting, YAML frontmatter schema, GLFM syntax, plugin structure, and token complexity for documentation files and Claude Code plugin components.

Two validators cover complementary domains:

- `plugin-creator:lint` — SKILL.md frontmatter, agent definitions, plugin structure, token complexity, broken internal links
- `holistic-linting` — code file formatting (ruff, mypy, bandit) for companion Python scripts

## Entrypoint Contract

### Required Inputs

- Target — file path (SKILL.md, agent .md, plugin directory, or markdown file)

### Optional Inputs

- `--fix` flag — auto-fix frontmatter issues (passed to plugin_validator.py)
- GITLAB_TOKEN — required for GLFM validation via GitLab API

## Steps

1. **Determine target type** — SKILL.md, agent definition, plugin directory, or markdown
2. **Run plugin-creator:lint** — `Skill(command: "plugin-creator:lint")` with target path as argument
3. **For GLFM content** — run `uv run plugins/gitlab-skill/skills/gitlab-skill/scripts/validate_glfm.py --file {target}`
4. **For Python scripts in plugin** — activate holistic-linting skill for ruff/mypy checks
5. **Collect and aggregate results** — report per-validator pass/fail
6. **Run link-checker** — verify all markdown cross-references resolve

## Validation Gates

- HARD STOP — frontmatter colon in description (not URL): fix before proceeding
- HARD STOP — `allowed-tools` is YAML array format: fix before proceeding
- HARD STOP — `name` field present in SKILL.md frontmatter: remove (skills do not use `name`)
- SOFT STOP — token complexity exceeds TOKEN_WARNING_THRESHOLD: flag, do not block
- HARD STOP — token complexity exceeds TOKEN_ERROR_THRESHOLD: split skill before proceeding

## Output Contract

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [N files checked, N issues found]
ARTIFACTS:
  - (no artifact files — validation is in-place reporting)
VALIDATION:
  - frontmatter-validator: PASS|FAIL
  - plugin-structure-validator: PASS|FAIL
  - link-checker: PASS|FAIL
  - glfm-validator: PASS|FAIL (if applicable)
NOTES: [list any issues found with file:line references]
```

## GLFM Validation Notes

GLFM validation requires `GITLAB_TOKEN` environment variable. If not present, the glfm-validator step is skipped and noted in NOTES. Alert block syntax, collapsible sections, and table alignment must be verified via the GitLab markdown API — local markdown renderers do not enforce GLFM rules.
