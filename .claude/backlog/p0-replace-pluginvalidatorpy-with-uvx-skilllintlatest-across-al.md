---
name: Replace plugin_validator.py with uvx skilllint@latest across all invocation sites
description: 'The repository uses `uv run plugins/plugin-creator/scripts/plugin_validator.py` in ~46 files (~150+ occurrences) across pre-commit hooks, CI workflows, agent files, SKILL.md files, rules, and documentation. The `skilllint` CLI (`uvx skilllint@latest`) is the replacement and is already available on PyPI. All invocation sites need to be updated to use `uvx skilllint@latest` instead. A full audit of affected files has been written to `.claude/reports/skilllint-migration-audit.md`. Success looks like: `plugin_validator.py` is no longer referenced in any invocation context (pre-commit, CI, agent/skill instructions, rules, docs), all hooks and workflows use `uvx skilllint@latest`, and the pre-commit hook id is updated consistently across all files that reference it by id.'
metadata:
  topic: replace-pluginvalidatorpy-with-uvx-skilllintlatest-across-al
  source: Session observation
  added: '2026-03-13'
  priority: P0
  type: Refactor
  status: open
  issue: '#684'
  last_synced: '2026-03-13T19:11:28Z'
  groomed: '2026-03-13'
  plan: plan/tasks-37-replace-pluginvalidatorpy-with-uvx-skilllint.md
---

## Fact-Check

<div><sub>2026-03-13T19:10:33Z</sub>

Verified 2026-03-13 against codebase and PyPI:

- `uvx skilllint@latest` available on PyPI: VERIFIED
- Audit file at `.claude/reports/skilllint-migration-audit.md`: VERIFIED
- Scope claim of "~46 files / ~150+ occurrences" in original description: REFUTED — audit summary footer repeats this number but the per-category tables enumerate far more actionable sites; independent grep `grep -r "plugin_validator" . --include="*.md" --include="*.yaml" --include="*.yml" | wc -l` returns 1,988 occurrences across 395 files (historical/archive files included). Actionable (non-archive) files: ~46 files per the audit summary table, but each file contains multiple occurrences. The 395/1,988 figures include out-of-scope archive/plan/research files explicitly listed in the audit as out-of-scope.
</div>

## RT-ICA

<div><sub>2026-03-13T19:10:45Z</sub>

Decision: APPROVED (pre-computed by orchestrator, 2026-03-13)

Goal: Replace all `uv run plugins/plugin-creator/scripts/plugin_validator.py` invocations with `uvx skilllint@latest` across pre-commit hooks, CI workflows, agent files, skill files, rules, and documentation.

Conditions verified:
- Replacement CLI (`uvx skilllint@latest`) available on PyPI: AVAILABLE — verified
- Full audit of affected files exists: AVAILABLE — `.claude/reports/skilllint-migration-audit.md`
- CLI flag/subcommand compatibility: DERIVABLE — audit notes pre-migration check (`uvx skilllint@latest --help`) is required before applying changes; flags listed in audit mapping table
- Pre-commit hook id ripple: AVAILABLE — audit §Special Cases documents 4 additional files that reference `plugin-validator` by id

No MISSING conditions. Classification: procedural migration with enumerated steps.
</div>

## Groomed (2026-03-13)

### Groomed

<div><sub>2026-03-13T19:11:28Z</sub>

### Reproducibility

1. From the repository root, run:

```bash
grep -r "plugin_validator" . \
  --include="*.md" --include="*.yaml" --include="*.yml" \
  --exclude-dir=".git" \
  | grep -v "\.claude/archive\|\.claude/audits\|\.claude/backlog\|\.claude/plan\|plan/\|research/\|plugins/plugin-creator/planning/" \
  | wc -l
```

A non-zero result confirms actionable references remain. The same command scoped to a single category:

```bash
grep -r "plugin_validator" .pre-commit-config.yaml .github/workflows/ .claude/rules/ CONTRIBUTING.md plugins/plugin-creator/
```

2. Run the pre-commit hook to observe it still calls the local script:

```bash
uv run prek run plugin-validator --all-files 2>&1 | head -5
```

### Output / Evidence

Done looks like all of the following:

```bash
# Zero actionable occurrences remain (archive/plan dirs excluded)
grep -r "plugin_validator" . \
  --include="*.md" --include="*.yaml" --include="*.yml" \
  --exclude-dir=".git" \
  | grep -v "\.claude/archive\|\.claude/audits\|\.claude/backlog\|\.claude/plan\|plan/\|research/\|plugins/plugin-creator/planning/" \
  | wc -l
# Expected output: 0
```

- `uv run prek run --all-files` completes without error, and the output shows `uvx skilllint@latest` in the hook command line, not `plugin_validator.py`
- `.github/workflows/code-quality.yml` CI job passes using `uvx skilllint@latest`
- Pre-commit hook id in `.pre-commit-config.yaml` and all referencing files agree on the same id (`skilllint`)

### Priority

10/10 — P0. The local script is the enforced validation gate for every plugin commit (pre-commit hook), every CI run (code-quality.yml), and every agent that validates plugin files. Until this migration completes, improvements shipped in `skilllint` are invisible to this repository. Every session where an agent calls the old script path is a latent breakage risk if the script is later removed.

### Impact

- Blocks: All skilllint improvements (token threshold changes, new validators, bug fixes) from taking effect in CI, pre-commit, agent files, and skill instructions
- Bottleneck: Every agent that validates a plugin file calls `plugin_validator.py` via the local path; if the script is removed or renamed, all agent validation steps silently fail or error
- Maintenance: Any contributor updating `plugin_validator.py` logic must also update `skilllint` separately; the two diverge with each change

### Benefits

- All plugin validation uses the PyPI-published `skilllint` binary — version-pinned via `@latest` or explicit version tag
- Pre-commit, CI, agents, and skills all call the same command; one source of truth
- Contributors no longer need the local script path in mental model
- `uvx` handles installation — no `uv run --no-sync` or path resolution required

### Desired Structure

After migration:

- `.pre-commit-config.yaml` hook entry calls `uvx skilllint@latest --fix` with an id of `skilllint`
- `.github/workflows/code-quality.yml` calls `uvx skilllint@latest` (or `prek run skilllint`) with the updated hook id in the SKIP list
- All agent files (`agent-creator.md`, `hook-creator.md`, `plugin-assessor.md`, `refactor-validator.md`) reference `uvx skilllint@latest` in their validation steps
- All SKILL.md files reference `uvx skilllint@latest`
- All `.claude/rules/` files reference `uvx skilllint@latest`
- `CONTRIBUTING.md` examples use `uvx skilllint@latest`
- All reference files (`USAGE.md`, `ARCHITECTURE.md`, `ERROR_CODES.md`, etc.) reference `skilllint` as the tool name
- `plugins/plugin-creator/skills/lint/SKILL.md` line 10 uses `` !`uvx skilllint@latest <lint_target/>` ``

### Acceptance Criteria

1. `grep -r "plugin_validator" . --include="*.md" --include="*.yaml" --include="*.yml" --exclude-dir=".git" | grep -v "\.claude/archive\|\.claude/audits\|\.claude/backlog\|\.claude/plan\|plan/\|research/\|plugins/plugin-creator/planning/"` returns zero lines
2. `uv run prek run --all-files` exits 0 with no reference to `plugin_validator.py` in output
3. `.github/workflows/code-quality.yml` CI job passes on a branch containing a modified plugin file
4. Pre-commit hook id is identical across `.pre-commit-config.yaml`, `code-quality.yml` SKIP list, `references/USAGE.md`, `references/ARCHITECTURE.md`, and `scripts/CLAUDE.md`
5. `uvx skilllint@latest --help` was run before any file was changed and the subcommand/flag mapping table in the audit was confirmed or updated

### Resources

| Type | Item |
|------|------|
| Prior work | `.claude/reports/skilllint-migration-audit.md` (2026-03-13) — full per-file, per-line change list |
| Skill | `/plugin-creator:lint` — current lint skill (uses the path to be replaced at line 10) |
| Skill | `/plugin-creator:plugin-creator` — contains 8+ flowchart invocations to update |
| Skill | `/plugin-creator:skill-creator` — 1 invocation to update |
| Skill | `/plugin-creator:agent-creator` — 4 invocations to update |
| Agent | `@plugin-creator:refactor-validator` — calls validator in its validation step |

### Dependencies

- Depends on: `uvx skilllint@latest` available in CI runner environment (verify with `uvx skilllint@latest --version` in a CI step before migration commit is merged)
- Blocks: None (no other backlog items identified as waiting on this)

### Blockers

- Pre-migration prerequisite: run `uvx skilllint@latest --help` and confirm subcommand names and flag signatures match the mapping table in the audit file. If any subcommand differs, update the audit mapping before applying changes. This step must happen before the first file is edited.
- Hook id ripple: changing `id: plugin-validator` to `id: skilllint` in `.pre-commit-config.yaml` requires simultaneous updates to 4 additional files (see audit §Special Cases). These must be updated atomically in the same commit to avoid a broken SKIP list in CI.

### Effort

Medium — ~46 actionable files with enumerated line-level changes documented in the audit. The changes are mechanical substitutions (find/replace per file), but the pre-commit hook id ripple across 4 files and the SessionStart command substitution in `skills/lint/SKILL.md` require care. The pre-migration CLI verification step is the only non-mechanical gate.
</div>