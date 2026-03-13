---
feature: replace-pluginvalidatorpy-with-uvx-skilllint
title: "Replace plugin_validator.py with uvx skilllint@latest check across all invocation sites"
github_issue: 684
parent_issue_number: 684
description: |
  Migrate all ~46 actionable files from `uv run plugins/plugin-creator/scripts/plugin_validator.py`
  to `uvx skilllint@latest check`. The audit is at `.claude/reports/skilllint-migration-audit.md`.

  CLI surface verified 2026-03-13:
  - No subcommands (validate/batch/fix/fix-batch eliminated — use positional PATHS)
  - `--fix` flag preserved
  - `--check` flag preserved
  - `--verbose` / `-v` preserved
  - `--no-color` preserved
  - `--tokens-only` preserved
  - `--filter-type` exists with values: skills, agents, commands
  - `--all-files` does NOT exist — prek integration must use a different invocation
  - Exit code: 0 = clean, non-zero = errors (preserved)

context_manifest:
  audit_report: .claude/reports/skilllint-migration-audit.md
  old_invocation: "uv run plugins/plugin-creator/scripts/plugin_validator.py"
  new_invocation: "uvx skilllint@latest check"
  old_hook_id: plugin-validator
  new_hook_id: skilllint
  verified_cli: true
---

# Task 1.1: Update pre-commit hook

**Status**: NOT STARTED
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update `.pre-commit-config.yaml` to use `uvx skilllint@latest check` and change the hook id from `plugin-validator` to `skilllint`.

## Acceptance Criteria

- [ ] `.pre-commit-config.yaml` line ~128: `- id: plugin-validator` → `- id: skilllint`
- [ ] `.pre-commit-config.yaml` line ~130: `entry: uv run -q --no-sync plugins/plugin-creator/scripts/plugin_validator.py --fix` → `entry: uvx skilllint@latest check --fix`
- [ ] Run `uv run prek run --all-files` and confirm no error about missing hook id

## Verification

```bash
grep "plugin.validator\|plugin_validator" .pre-commit-config.yaml | wc -l
# Expected: 0
grep "skilllint" .pre-commit-config.yaml
# Expected: shows the new hook definition
```

---

# Task 1.2: Update CI workflows

**Status**: NOT STARTED
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: Task 1.1

## Description

Update `.github/workflows/code-quality.yml`:
- Line ~180: Update comment from `plugin_validator.py` to `skilllint`
- Line ~209: `run: uv run prek run plugin-validator --all-files` → use `uvx skilllint@latest check` directly (since `--all-files` doesn't exist, use `uvx skilllint@latest check plugins/` or keep prek with new hook id `skilllint`)
- Line ~270: Update `SKIP: ...,plugin-validator,...` to `SKIP: ...,skilllint,...`

**Note on line 209**: Since prek uses hook ids, if the hook id changed to `skilllint` in Task 1.1, then `uv run prek run skilllint --all-files` is the correct form. Verify the prek hook run syntax.

## Acceptance Criteria

- [ ] No `plugin-validator` or `plugin_validator` references remain in `.github/workflows/code-quality.yml`
- [ ] CI uses either `uvx skilllint@latest check` directly or `uv run prek run skilllint --all-files`

## Verification

```bash
grep "plugin.validator\|plugin_validator" .github/workflows/code-quality.yml | wc -l
# Expected: 0
```

---

# Task 1.3: Update project rules

**Status**: NOT STARTED
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 3 files in `.claude/rules/`:

1. `.claude/rules/delegation-format.md` line ~73: `Q{Run: uv run plugin_validator.py path<br>Exit code?}` → `Q{Run: uvx skilllint@latest check path<br>Exit code?}`
2. `.claude/rules/uv-run-fallback.md` line ~9: `uv run plugins/plugin-creator/scripts/plugin_validator.py <path>` → `uvx skilllint@latest check <path>`
3. `.claude/rules/language-conventions.md` line ~52: update `plugin-validator \`NameFormatValidator\`` → `skilllint \`NameFormatValidator\``

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in `.claude/rules/*.md`

## Verification

```bash
grep -r "plugin_validator\|plugin-validator" .claude/rules/ | wc -l
# Expected: 0
```

---

# Task 1.4: Update CONTRIBUTING.md

**Status**: NOT STARTED
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 4 invocations in `CONTRIBUTING.md` lines ~216–223.

Old pattern: `uv run plugins/plugin-creator/scripts/plugin_validator.py <subcommand> <path>`
New pattern: `uvx skilllint@latest check <path>` (no subcommands — positional paths only)

Note: `validate` and `fix` subcommands no longer exist. Map them:
- `validate <path>` → `uvx skilllint@latest check <path>` (default = validate)
- `fix <path>` → `uvx skilllint@latest check --fix <path>`
- `fix <path> --dry-run` → `uvx skilllint@latest check --check <path>` (check = no changes)
- `batch <dir>` → `uvx skilllint@latest check <dir>`

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in `CONTRIBUTING.md`
- [ ] All examples use correct `uvx skilllint@latest check` CLI surface (no subcommands)

## Verification

```bash
grep "plugin_validator\|plugin-validator" CONTRIBUTING.md | wc -l
# Expected: 0
```

---

# Task 2.1: Update plugins/plugin-creator/CLAUDE.md

**Status**: NOT STARTED
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose
**Dependencies**: None

## Description

Update `plugins/plugin-creator/CLAUDE.md` — the largest single file with ~15+ occurrences across lines 36–456.

Key changes:
- Lines 36–39: Replace invocation patterns in quick reference table
- Line 99–100: Update table row tool name
- Lines 132, 147: Update descriptive mentions
- Lines 153–166: Replace all `uv run plugins/plugin-creator/scripts/plugin_validator.py` invocations
- Line 173: Update `TOKEN_WARNING_THRESHOLD` source reference to `skilllint`
- Line 282, 331: Replace invocations
- Line 377: Update auto-adds reference
- Lines 456, 458: Update validation notes

Also update subcommand mapping per the verified CLI surface (no subcommands, positional args only).

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in `plugins/plugin-creator/CLAUDE.md`
- [ ] All invocations use correct `uvx skilllint@latest check` CLI surface

## Verification

```bash
grep "plugin_validator\|plugin-validator" plugins/plugin-creator/CLAUDE.md | wc -l
# Expected: 0
```

---

# Task 2.2: Update plugins/plugin-creator/scripts/CLAUDE.md

**Status**: NOT STARTED
**Priority**: 2
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update `plugins/plugin-creator/scripts/CLAUDE.md`:
- Line ~22: `### plugin_validator.py` section header → `### skilllint`
- Lines ~30–45: Six `uv run plugins/plugin-creator/scripts/plugin_validator.py` invocations → `uvx skilllint@latest check`
- Line ~116: Table row with `plugin-validator` and `plugin_validator.py` → update both

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in `plugins/plugin-creator/scripts/CLAUDE.md`

## Verification

```bash
grep "plugin_validator\|plugin-validator" plugins/plugin-creator/scripts/CLAUDE.md | wc -l
# Expected: 0
```

---

# Task 2.3: Update agent files

**Status**: NOT STARTED
**Priority**: 2
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 4 agent files:

1. `plugins/plugin-creator/agents/agent-creator.md` lines 165–189: Replace all `plugin_validator.py` and `plugin-validator` references
2. `plugins/plugin-creator/agents/hook-creator.md` line 298: Replace invocation
3. `plugins/plugin-creator/agents/plugin-assessor.md` line 24: Replace invocation
4. `plugins/plugin-creator/agents/refactor-validator.md` lines 3, 37–38, 60: Replace all references

Also update frontmatter description of `refactor-validator.md` (line 3).

Note: The Mermaid flowchart in `agent-creator.md` references the validator by name in node labels — update those to `skilllint`.

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in any of the 4 agent files

## Verification

```bash
grep -l "plugin_validator\|plugin-validator" plugins/plugin-creator/agents/ | wc -l
# Expected: 0
```

---

# Task 3.1: Update SKILL.md files (plugin-creator, lint, skill-creator)

**Status**: NOT STARTED
**Priority**: 3
**Complexity**: Medium
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 3 SKILL.md files:

1. `plugins/plugin-creator/skills/lint/SKILL.md` line 10:
   - Old: `` !`${CLAUDE_PLUGIN_ROOT}/scripts/plugin_validator.py <lint_target/>` ``
   - New: `` !`uvx skilllint@latest check <lint_target/>` ``

2. `plugins/plugin-creator/skills/plugin-creator/SKILL.md` lines 66–561:
   - 8+ Mermaid flowchart nodes with `uv run plugins/plugin-creator/scripts/plugin_validator.py PATH`
   - Body references at lines 254, 547
   - All → `uvx skilllint@latest check PATH`

3. `plugins/plugin-creator/skills/skill-creator/SKILL.md` line 327:
   - Replace invocation

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in the 3 files

## Verification

```bash
grep "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/skills/lint/SKILL.md \
  plugins/plugin-creator/skills/plugin-creator/SKILL.md \
  plugins/plugin-creator/skills/skill-creator/SKILL.md | wc -l
# Expected: 0
```

---

# Task 3.2: Update remaining SKILL.md files

**Status**: NOT STARTED
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 10 remaining SKILL.md files with single-to-few occurrences each:

1. `plugins/plugin-creator/skills/agent-creator/SKILL.md` lines 272, 278, 296, 302, 880
2. `plugins/plugin-creator/skills/agentskills/SKILL.md` line 98
3. `plugins/plugin-creator/skills/assessor/SKILL.md` line 248
4. `plugins/plugin-creator/skills/optimize-claude-md/SKILL.md` lines 42, 210
5. `plugins/plugin-creator/skills/refactor-skill/SKILL.md` lines 30, 48, 237, 407
6. `plugins/plugin-creator/skills/audit-skill-lifecycle/SKILL.md` line 253
7. `plugins/plugin-creator/skills/start-refactor-task/SKILL.md` line 202
8. `plugins/plugin-creator/skills/write-frontmatter-description/SKILL.md` lines 21, 24
9. `plugins/plugin-creator/skills/plugin-lifecycle/references/phase-skill-mapping.md` line 24

Note on subcommand mapping:
- `plugin_validator.py validate <path>` → `uvx skilllint@latest check <path>`
- `plugin_validator.py fix <path>` → `uvx skilllint@latest check --fix <path>`
- `plugin_validator.py --check <file>` → `uvx skilllint@latest check --check <file>`

## Acceptance Criteria

- [ ] Zero `plugin_validator` references across all 10 files listed

## Verification

```bash
grep -r "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/skills/agent-creator/SKILL.md \
  plugins/plugin-creator/skills/agentskills/SKILL.md \
  plugins/plugin-creator/skills/assessor/SKILL.md \
  plugins/plugin-creator/skills/optimize-claude-md/SKILL.md \
  plugins/plugin-creator/skills/refactor-skill/SKILL.md \
  plugins/plugin-creator/skills/audit-skill-lifecycle/SKILL.md \
  plugins/plugin-creator/skills/start-refactor-task/SKILL.md \
  plugins/plugin-creator/skills/write-frontmatter-description/SKILL.md | wc -l
# Expected: 0
```

---

# Task 4.1: Update reference files — USAGE.md and ARCHITECTURE.md

**Status**: NOT STARTED
**Priority**: 4
**Complexity**: High
**Agent**: general-purpose
**Dependencies**: None

## Description

Two large reference files with many occurrences:

### USAGE.md (`plugins/plugin-creator/references/USAGE.md`)

Entirely a usage reference for `plugin_validator.py` with 30+ invocations across ~700 lines. Changes:
- Update title/header from `plugin_validator.py` to `skilllint`
- Replace all `uv run plugins/plugin-creator/scripts/plugin_validator.py` with `uvx skilllint@latest check`
- Remove subcommand names (`validate`, `batch`, `fix`, `fix-batch`) — use positional args and flags instead
- Update source citation on line 709 (link to PyPI: `https://pypi.org/project/skilllint`)
- Update prek invocation on line 507: `pre-commit run plugin-validator --all-files` → `pre-commit run skilllint --all-files`

### ARCHITECTURE.md (`plugins/plugin-creator/references/ARCHITECTURE.md`)

- Line 3: Update document title
- Line 9: Update file reference
- Line 109: Update `TOKEN_WARNING_THRESHOLD` source reference
- Line 379: `name="plugin-validator"` — update to `name="skilllint"` if this is the Typer app name in skilllint
- Lines 521–524: Update hook id and entry
- Line 875: Update table row
- Line 885: Update link to `https://pypi.org/project/skilllint`

## Acceptance Criteria

- [ ] Zero `plugin_validator` references in `USAGE.md`
- [ ] Zero `plugin_validator` references in `ARCHITECTURE.md`
- [ ] All invocations use the correct positional-arg CLI surface (no subcommands)
- [ ] Source citations updated to PyPI URL

## Verification

```bash
grep "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/references/USAGE.md \
  plugins/plugin-creator/references/ARCHITECTURE.md | wc -l
# Expected: 0
```

---

# Task 4.2: Update reference files — ERROR_CODES and rules

**Status**: NOT STARTED
**Priority**: 4
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 6 files:

1. `plugins/plugin-creator/references/ERROR_CODES.md` lines 3, 439, 469, 784, 811
2. `plugins/plugin-creator/docs/ERROR_CODES.md` lines 3, 622, 652, 1080, 1152
3. `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` lines 34, 39
4. `plugins/plugin-creator/.claude/rules/plugin-json.md` lines 35, 47
5. `plugins/plugin-creator/skills/hooks-guide/references/best-practices.md` lines 500–501
6. `plugins/plugin-creator/skills/plugin-lifecycle/references/error-handling.md` line 12

For ERROR_CODES.md files:
- Update tool name in title/intro
- Update `TOKEN_WARNING_THRESHOLD` / `TOKEN_ERROR_THRESHOLD` source reference to `skilllint`
- Replace invocation on line 784 / 1080
- Update link on line 811 → `https://pypi.org/project/skilllint`

## Acceptance Criteria

- [ ] Zero `plugin_validator` references across all 6 files

## Verification

```bash
grep "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/references/ERROR_CODES.md \
  plugins/plugin-creator/docs/ERROR_CODES.md \
  plugins/plugin-creator/.claude/rules/frontmatter-requirements.md \
  plugins/plugin-creator/.claude/rules/plugin-json.md \
  plugins/plugin-creator/skills/hooks-guide/references/best-practices.md \
  plugins/plugin-creator/skills/plugin-lifecycle/references/error-handling.md | wc -l
# Expected: 0
```

---

# Task 4.3: Update remaining reference files

**Status**: NOT STARTED
**Priority**: 4
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 9 remaining reference files:

1. `plugins/plugin-creator/skills/plugin-lifecycle/references/example-sessions.md` line 96
2. `plugins/plugin-creator/skills/skill-creator/references/agent-plugin-ecosystem.md` line 113
3. `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md` lines 13, 482–555, 573
4. `plugins/plugin-creator/skills/agentskills/references/best-practices.md` lines 142, 473
5. `plugins/plugin-creator/skills/agentskills/references/specification.md` lines 208, 251
6. `plugins/plugin-creator/skills/audit-agent-lifecycle/references/agent-lifecycle-audit.md` line 195
7. `plugins/plugin-creator/skills/audit-skill-lifecycle/references/skill-lifecycle-audit.md` line 163
8. `plugins/plugin-creator/skills/plugin-creator/references/workflow-diagram.md` lines 160, 211, 249, 327
9. `plugins/plugin-creator/references/USAGE.md` line 507 (prek hook id reference — if not covered in Task 4.1)

For `agent-schema.md`:
- Line 13: Update link from `./../../scripts/plugin_validator.py` → `https://pypi.org/project/skilllint`
- Lines 482–555: Six invocations → `uvx skilllint@latest check`
- Line 573: Update SOURCE citation → PyPI URL

## Acceptance Criteria

- [ ] Zero `plugin_validator` references across all 9 files

## Verification

```bash
grep -r "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/skills/plugin-lifecycle/references/ \
  plugins/plugin-creator/skills/skill-creator/references/ \
  plugins/plugin-creator/skills/agent-creator/references/ \
  plugins/plugin-creator/skills/agentskills/references/ \
  plugins/plugin-creator/skills/audit-agent-lifecycle/references/ \
  plugins/plugin-creator/skills/audit-skill-lifecycle/references/ \
  plugins/plugin-creator/skills/plugin-creator/references/ | wc -l
# Expected: 0
```

---

# Task 5.1: Update README files and example files

**Status**: NOT STARTED
**Priority**: 5
**Complexity**: Medium
**Agent**: general-purpose
**Dependencies**: None

## Description

Update 4 files:

### `plugins/plugin-creator/README.md`

Lines 49, 72–82, 130, 144–161, 160 (section title), 246, 413, 423, 449–461.
- Update section title `### Frontmatter Validation (plugin_validator.py)` → `### Frontmatter Validation (skilllint)`
- Replace all invocations with `uvx skilllint@latest check`
- Update tool name in prose descriptions

### `plugins/plugin-creator/scripts/README.md`

Lines 132, 147–162, 156.
- Update `## plugin_validator.py` section header → `## skilllint`
- Replace all invocations
- Fix path typo on line 156 (`uv run plugins/plugin_validator.py` → `uvx skilllint@latest check`)

### Example files

- `plugins/plugin-creator/examples/agents/example-agent.md` lines 49, 52–53
- `plugins/plugin-creator/examples/skills/example-skill/SKILL.md` line 46

Note: In examples, `validate <path>` → `uvx skilllint@latest check <path>` and `fix <path>` → `uvx skilllint@latest check --fix <path>`.

## Acceptance Criteria

- [ ] Zero `plugin_validator` references across all 4 files

## Verification

```bash
grep "plugin_validator\|plugin-validator" \
  plugins/plugin-creator/README.md \
  plugins/plugin-creator/scripts/README.md \
  plugins/plugin-creator/examples/agents/example-agent.md \
  plugins/plugin-creator/examples/skills/example-skill/SKILL.md | wc -l
# Expected: 0
```

---

# Task 6.1: Final verification

**Status**: NOT STARTED
**Priority**: 6
**Complexity**: Low
**Agent**: general-purpose
**Dependencies**: Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 2.1, Task 2.2, Task 2.3, Task 3.1, Task 3.2, Task 4.1, Task 4.2, Task 4.3, Task 5.1

## Description

Run the complete verification suite to confirm zero actionable references remain and the pre-commit hook works correctly.

## Acceptance Criteria

- [ ] Zero actionable `plugin_validator` references (excluding archive/plan/research/backlog)
- [ ] `uv run prek run --all-files` completes without errors
- [ ] Pre-commit hook invocation shows `uvx skilllint@latest check` in output

## Verification

```bash
# 1. Count remaining actionable references
grep -r "plugin_validator\|plugin-validator" . \
  --include="*.md" --include="*.yaml" --include="*.yml" \
  --exclude-dir=".git" \
  | grep -v "\.claude/archive\|\.claude/audits\|\.claude/backlog\|\.claude/plan\|plan/\|research/\|plugins/plugin-creator/planning/" \
  | grep -v "skilllint-migration-audit.md" \
  | wc -l
# Expected: 0

# 2. Run pre-commit hooks
uv run prek run --all-files 2>&1 | grep -i "skilllint\|plugin.validator" | head -10

# 3. Confirm hook id in pre-commit config
grep "id:" .pre-commit-config.yaml | grep -v "plugin.validator"
```

## Commit

After verification passes:
```bash
git add -A
git commit -m "refactor(migration): replace plugin_validator.py with uvx skilllint@latest check

Migrated all ~46 actionable files from local script invocation to
the published CLI package. No subcommand syntax (validate/batch/fix)
retained — all converted to positional args with --fix/--check flags.

Fixes #684"
```
