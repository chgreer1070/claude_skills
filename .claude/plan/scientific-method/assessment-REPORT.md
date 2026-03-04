# Plugin Assessment Report — scientific-method

**Assessment date**: 2026-03-04
**Assessor**: code-reviewer sub-agent (full content inspection)
**Plugin path**: `plugins/scientific-method`
**Plugin version**: 1.2.0 (plugin.json) / 1.1.0 (README — mismatch, see Manifest Validation)

---

## Executive Summary

- **Overall Score**: 82/100
- **Marketplace Ready**: With Changes
- **Critical Issues**: 0
- **Important Issues**: 1 (cross-repo links in shared file — portability defect)
- **Low Issues**: 4 (version mismatch, missing agent tools field, missing downstream docs, non-standard markup)
- **Skills needing refactoring**: `experiment-protocol` (1,971 tokens — largest skill; no references/ directory; no downstream integration docs)
- **Agents needing optimization**: `retrospective-analyst` (missing `tools` field in frontmatter)
- **Orphaned files**: 1 (`README.md` — not auto-loaded by runtime, not referenced from plugin.json or any skill)

**Score breakdown**:

| Category | Max | Score | Notes |
|----------|-----|-------|-------|
| Manifest validity | 15 | 13 | Version mismatch README vs plugin.json |
| Skills quality | 30 | 25 | experiment-protocol lacks references/ and downstream docs |
| Agent quality | 15 | 13 | retrospective-analyst missing tools field; otherwise high quality |
| Hooks quality | 10 | 9 | Valid; timeout may be tight for large investigation outputs |
| Cross-reference integrity | 15 | 13 | 3 cross-repo links in investigation-workflow.md break on marketplace install |
| Structure | 15 | 9 | shared/ unrecognized by schema; README orphaned; PD warnings across all skills |

---

## Plugin Structure

Complete file tree (15 files total):

```text
plugins/scientific-method/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   └── retrospective-analyst.md            (110 lines)
├── hooks/
│   └── hooks.json
├── shared/
│   ├── causality-check.md                  (53 lines)
│   ├── evidence-rules.md                   (59 lines)
│   ├── investigation-template.md           (205 lines)
│   ├── investigation-workflow.md           (393 lines)
│   └── extensions/
│       ├── debugging-extensions.md         (41 lines)
│       └── performance-extensions.md       (47 lines)
├── skills/
│   ├── evidence-first-debugging/
│   │   ├── SKILL.md                        (98 lines / 948 tokens)
│   │   └── references/
│   │       └── shared-references.md
│   ├── experiment-protocol/
│   │   └── SKILL.md                        (232 lines / 1,971 tokens)
│   └── scientific-thinking/
│       ├── SKILL.md                        (94 lines / 832 tokens)
│       └── references/
│           └── shared-references.md
└── README.md                               (human-facing; not auto-loaded)
```

Recognized by plugin schema: `.claude-plugin/`, `agents/`, `hooks/`, `skills/`
Not recognized by plugin schema: `shared/` (no schema field), `README.md`

---

## Manifest Validation

**File**: `plugins/scientific-method/.claude-plugin/plugin.json`

Schema compliance: PASS. Required fields present: `name`, `description`, `version`, `author`, `agents`.

```json
{
  "name": "scientific-method",
  "description": "...",
  "version": "1.2.0",
  "author": { "name": "Jamie Nelson", "url": "https://github.com/bitflight-devops" },
  "agents": ["./agents/retrospective-analyst.md"]
}
```

Issues:

1. **Version mismatch** (Low): `plugin.json` declares `1.2.0`. `README.md` shows `1.1.0`. The README was not updated when the plugin version was bumped. The canonical version source is `plugin.json`.

2. **`shared/` not declared** (Note): The `shared/` directory contains canonical reference files that all three skills depend on. It is not listed in `plugin.json` — this is not a schema violation (no `shared` field exists in the schema), but means the manifest is not a complete inventory of plugin contents. A future schema version adding a `shared` field would require back-filling.

3. **`skills` array absent** (Note): Plugin.json does not declare a `skills` array. Skill discovery works by directory scan. This is valid per the schema.

---

## Skills Analysis

| Skill | Lines | Tokens | Validator Status | Description Quality | References Dir | Orphans | Refactor Needed |
|-------|-------|--------|-----------------|---------------------|---------------|---------|-----------------|
| scientific-thinking | 94 | 832 | PASS (PD002, PD003 info) | High | Yes | None | No |
| evidence-first-debugging | 98 | 948 | PASS (PD002, PD003 info) | High | Yes | None | No |
| experiment-protocol | 232 | 1,971 | PASS (PD001, PD002, PD003 info) | High | No | None | Medium |

### scientific-thinking

- Frontmatter: PASS. Fields: `name`, `description`, `user-invocable`.
- Activation triggers: Specific keyword list provided.
- Scope boundary: Explicitly stated with out-of-scope examples.
- Mermaid workflow: Present and correct. Includes status branch and `retrospective-analyst` notification.
- Companion skill cross-reference: Documents `evidence-first-debugging` relationship. Not a broken link.
- References index (`references/shared-references.md`): Present. Links `investigation-template.md` and `investigation-workflow.md` — both resolve.
- PD002/PD003 (info only): No `examples/` or `scripts/` directories.
- Defects: None.

### evidence-first-debugging

- Frontmatter: PASS. Fields: `name`, `description`, `user-invocable`.
- Five non-negotiable rules: Concrete, specific, with prescribed formats.
- Domain extension loading: Mermaid flowchart shows conditional extension selection. Correct.
- References index (`references/shared-references.md`): Present. Links all five shared files including both extensions — all resolve.
- Internal links in SKILL.md: All 5 shared file links resolve.
- Output checklist: Present and complete (8 items).
- PD002/PD003 (info only): No `examples/` or `scripts/` directories.
- Defects: None.

### experiment-protocol

- Frontmatter: PASS. Fields: `name`, `description`, `user-invocable`.
- Self-contained: Does not reference `shared/` files. This is intentional — the skill governs experiment design, not investigation template output.
- Downstream integration undocumented: The iteration log produced by this skill feeds `retrospective-analyst`. The agent expects "the complete investigation output (all 14 sections of the Unified Investigation Template)" plus the iteration log. `experiment-protocol/SKILL.md` does not mention `retrospective-analyst`, the investigation template, or the downstream workflow. Users of this skill cannot discover the connection without reading `scientific-thinking/SKILL.md` or the README.
- Non-standard markup: Uses `<eg>...</eg>` XML tags to wrap examples (lines 87–113, 128–147). Not a recognized Claude Code or markdown convention. The validator did not flag it. May be treated as literal text in some rendering contexts.
- Missing `references/` directory: PD001 informational warning. The 232-line / 1,971-token SKILL.md is the largest in the plugin and a candidate for progressive disclosure restructuring.
- No internal links: Correct — the skill is self-contained by design.
- PD001/PD002/PD003 (info only): No `references/`, `examples/`, or `scripts/` directories.
- Defects: 2 (undocumented downstream integration; non-standard markup).

---

## Agents Analysis

### retrospective-analyst

**File**: `plugins/scientific-method/agents/retrospective-analyst.md` (110 lines)

- Frontmatter fields present: `name`, `description`
- Frontmatter fields missing: `tools`, `model`, `color`
- Description quality: High. States trigger condition (`resolved-verified` status), what is produced (3 named artefact files with exact paths), when to use.
- Scope boundary: Explicit — "You do NOT suggest code changes — your scope is process analysis only."
- Input specification: Clearly declares inputs (full investigation output + iteration log).
- Output artefacts: Three files with exact naming conventions and directory (`.claude/retrospectives/`).
- Derivation constraint: Explicit — "Derive all content from the investigation input — do not invent events."
- File write operations: The agent writes 3 files. The `tools` field is absent. Without it the agent runs with default tool permissions rather than a declared, auditable set.
- Trigger clarity: HIGH. The hooks.json `SubagentStop` prompt explicitly notifies users when to invoke it.
- Defects: 1 (missing `tools` field).

---

## Hooks Analysis

**File**: `plugins/scientific-method/hooks/hooks.json`

Structure: Valid JSON. Registered under `SubagentStop`. Single hook, `type: "prompt"`.

Assessment:

1. **Purpose**: Informational status-check. Reads investigation output for `status: resolved-verified`. Explicitly designed to never block or fail output. Correct fail-open behavior.

2. **Status detection**: Checks for `status: resolved-verified` in section 14 of the Unified Investigation Template. Precise match. Fallback on no-status-found returns `{"ok": true}` silently — prevents false positives from non-investigation sub-agents.

3. **Notification message**: Clear user-facing language directing to `retrospective-analyst`.

4. **Timeout** (Low): `"timeout": 15` seconds. The prompt processes `SubagentStop` output that may contain a full 14-section investigation template (potentially thousands of tokens). 15 seconds may be insufficient on slower inference endpoints. Recommended: 30 seconds.

5. **Nesting structure**: Matches observed schema pattern for this hook type. No structural issues.

Overall: PASS with one low-severity timeout note.

---

## Cross-Reference Integrity

All links verified by filesystem check (18 total links across all skill and reference files).

### Links in `skills/scientific-thinking/SKILL.md`

| Link | Resolved path | Status |
|------|--------------|--------|
| `./references/shared-references.md` | `skills/scientific-thinking/references/shared-references.md` | RESOLVES |
| `../../shared/investigation-template.md` | `shared/investigation-template.md` | RESOLVES |
| `../../shared/investigation-workflow.md` | `shared/investigation-workflow.md` | RESOLVES |

### Links in `skills/evidence-first-debugging/SKILL.md`

| Link | Resolved path | Status |
|------|--------------|--------|
| `./references/shared-references.md` | `skills/evidence-first-debugging/references/shared-references.md` | RESOLVES |
| `../../shared/investigation-template.md` | `shared/investigation-template.md` | RESOLVES |
| `../../shared/evidence-rules.md` | `shared/evidence-rules.md` | RESOLVES |
| `../../shared/causality-check.md` | `shared/causality-check.md` | RESOLVES |
| `../../shared/extensions/debugging-extensions.md` | `shared/extensions/debugging-extensions.md` | RESOLVES |
| `../../shared/extensions/performance-extensions.md` | `shared/extensions/performance-extensions.md` | RESOLVES |

### Links in `shared/investigation-template.md`

| Link | Resolved path | Status |
|------|--------------|--------|
| `./causality-check.md` | `shared/causality-check.md` | RESOLVES |

### Links in `shared/investigation-workflow.md` — Navigation section (lines 391–393)

| Link | Resolved path | Status |
|------|--------------|--------|
| `../../../.claude/knowledge/workflow-diagrams/simple-task-workflow.md` | `.claude/knowledge/workflow-diagrams/simple-task-workflow.md` | RESOLVES locally — BREAKS on marketplace install |
| `../../../.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md` | `.claude/knowledge/workflow-diagrams/rag-retrieval-pattern.md` | RESOLVES locally — BREAKS on marketplace install |
| `../../../.claude/knowledge/workflow-diagrams/README.md` | `.claude/knowledge/workflow-diagrams/README.md` | RESOLVES locally — BREAKS on marketplace install |

These three links resolve in the plugin author's environment because `investigation-workflow.md` was migrated from `.claude/skills/` with its original Navigation section preserved. A marketplace user will not have `.claude/knowledge/workflow-diagrams/` — the links will be broken. This is the only portability defect in the plugin.

### Links in `skills/scientific-thinking/references/shared-references.md`

| Link | Resolved path | Status |
|------|--------------|--------|
| `../../../shared/investigation-template.md` | `shared/investigation-template.md` | RESOLVES |
| `../../../shared/investigation-workflow.md` | `shared/investigation-workflow.md` | RESOLVES |

### Links in `skills/evidence-first-debugging/references/shared-references.md`

| Link | Resolved path | Status |
|------|--------------|--------|
| `../../../shared/investigation-template.md` | `shared/investigation-template.md` | RESOLVES |
| `../../../shared/evidence-rules.md` | `shared/evidence-rules.md` | RESOLVES |
| `../../../shared/causality-check.md` | `shared/causality-check.md` | RESOLVES |
| `../../../shared/extensions/debugging-extensions.md` | `shared/extensions/debugging-extensions.md` | RESOLVES |
| `../../../shared/extensions/performance-extensions.md` | `shared/extensions/performance-extensions.md` | RESOLVES |

**Summary**: 18 links verified. Within-plugin broken links: 0. Cross-repo portability defects: 3 (all in `investigation-workflow.md` Navigation section).

---

## Orphaned Files

| File | Status | Classification |
|------|--------|---------------|
| `README.md` | Confirmed orphan | Human-facing documentation; not auto-loaded at runtime; not referenced from `plugin.json` or any SKILL.md. Exists for marketplace/GitHub browsing only. Version number stale (1.1.0 vs plugin.json 1.2.0). |

Files in `shared/` are not orphaned — all are referenced by at least one skill SKILL.md or references index.

`shared/investigation-workflow.md` is referenced only by `scientific-thinking/SKILL.md` and its references index. It is not referenced by `evidence-first-debugging` or `experiment-protocol`. Given it contains the full visual workflow for the scientific method, this may be a discoverability gap rather than an orphan.

**Confirmed orphan count**: 1

---

## Refactoring Recommendations

### STRUCTURE_FIX: Remove cross-repo navigation links from investigation-workflow.md

- **Target file**: `plugins/scientific-method/shared/investigation-workflow.md` (lines 389–393)
- **Issue type**: Portability defect — 3 links resolve only in plugin author's environment
- **Severity**: Important
- **Description**: The Navigation section at the bottom of `investigation-workflow.md` links to `../../../.claude/knowledge/workflow-diagrams/` files. These are personal `.claude/` directory files not shipped with the plugin. Any marketplace installation will produce broken links at these three locations.
- **Fix**: Remove lines 389–393 (the entire "Navigation" block) from `shared/investigation-workflow.md`. The navigation content has no value inside the plugin — the skill files themselves provide context for how the workflow document fits into the overall methodology.
- **Recommended agent**: `plugin-creator:subagent-refactorer`
- **Expected outcome**: `investigation-workflow.md` becomes fully portable. No links outside the plugin directory. Validator InternalLinkValidator will confirm no broken links.

---

### DOC_IMPROVE: Fix README version mismatch

- **Target file**: `plugins/scientific-method/README.md`
- **Issue type**: Stale documentation
- **Severity**: Low
- **Description**: `README.md` line 3 shows `**Version**: 1.1.0`. `plugin.json` shows `1.2.0`. README was not updated when the plugin version was bumped to 1.2.0.
- **Fix**: Update line 3 of `README.md` from `**Version**: 1.1.0` to `**Version**: 1.2.0`.
- **Recommended agent**: `plugin-creator:contextual-ai-documentation-optimizer`
- **Expected outcome**: README version matches plugin.json.

---

### AGENT_OPTIMIZE: Add `tools` field to retrospective-analyst frontmatter

- **Target file**: `plugins/scientific-method/agents/retrospective-analyst.md`
- **Issue type**: Missing frontmatter field
- **Severity**: Low
- **Description**: The agent writes 3 files to `.claude/retrospectives/` and reads investigation inputs. No `tools` field is declared in the YAML frontmatter. Without it the agent runs with default (unrestricted) tool permissions. Declaring `tools` documents intent and constrains scope to what the agent actually needs.
- **Fix**: Add `tools: [Read, Write]` to the YAML frontmatter block.
- **Recommended agent**: `plugin-creator:subagent-refactorer`
- **Expected outcome**: Agent frontmatter explicitly declares its required tools. Unexpected tool use is prevented.

---

### DOC_IMPROVE: Document downstream integration in experiment-protocol

- **Target file**: `plugins/scientific-method/skills/experiment-protocol/SKILL.md`
- **Issue type**: Discoverability gap — implicit workflow connection
- **Severity**: Low
- **Description**: `experiment-protocol` produces an iteration log that feeds `retrospective-analyst`. The agent expects the full investigation output (14-section template) plus the iteration log. Nothing in `experiment-protocol/SKILL.md` mentions this downstream connection. Users who invoke `/scientific-method:experiment-protocol` cannot discover `retrospective-analyst` exists without reading `scientific-thinking/SKILL.md` or the README.
- **Fix**: Add a "Downstream Integration" section near the end of SKILL.md documenting that the iteration log is consumed by `retrospective-analyst`, and that the `SubagentStop` hook will notify the user when an investigation completes.
- **Recommended agent**: `plugin-creator:contextual-ai-documentation-optimizer`
- **Expected outcome**: Users of `experiment-protocol` can discover the full workflow: experiment design → iteration log → `retrospective-analyst` → structured retrospective artefacts.

---

### DOC_IMPROVE: Replace non-standard `<eg>` markup in experiment-protocol

- **Target file**: `plugins/scientific-method/skills/experiment-protocol/SKILL.md` (lines 87–113, 128–147)
- **Issue type**: Non-standard markup
- **Severity**: Low
- **Description**: The skill uses `<eg>` and `</eg>` XML-like tags to wrap examples. This is not a recognized Claude Code or markdown convention. Standard practice is a subsection heading (`#### Example`) or a `> **Example:**` blockquote. The tags may render as literal text in some contexts and do not receive semantic treatment.
- **Fix**: Replace `<eg>` / `</eg>` wrapper pairs with standard markdown. Use `#### Example — Correct fixture` / `#### Example — Wrong fixture` subsection headings to preserve the comparison structure.
- **Recommended agent**: `plugin-creator:contextual-ai-documentation-optimizer`
- **Expected outcome**: All examples use standard markdown. No non-standard XML tags remain in the skill file. Content is unchanged.

---

### STRUCTURE_FIX: Add references/ directory to experiment-protocol (optional)

- **Target**: `plugins/scientific-method/skills/experiment-protocol/`
- **Issue type**: Missing progressive disclosure structure — PD001 informational warning
- **Severity**: Low (deferred — no immediate functional impact)
- **Description**: `experiment-protocol` is the largest skill (232 lines / 1,971 tokens) and the only one without a `references/` directory. The two smaller skills both have a references index. For consistency and progressive disclosure, the detailed step-by-step sections (file locations, log entry format, anti-patterns) could be split into references files.
- **Fix**: Create `skills/experiment-protocol/references/` and extract detailed sections into reference documents, leaving SKILL.md as a thin orchestration document.
- **Recommended agent**: `plugin-creator:subagent-refactorer`
- **Expected outcome**: `experiment-protocol/SKILL.md` token count reduced. Detailed content preserved in references/ files. PD001 validator warning resolved. Structural consistency with other two skills.

---

## Validator Output

Full raw output from:

```bash
uv run plugins/plugin-creator/scripts/plugin_validator.py --show-progress --show-summary --verbose plugins/scientific-method
```

```text
plugins/scientific-method
  PASSED  SymlinkTargetValidator
  WARNING PluginStructureValidator
    INFO [PL001] (plugin-structure): Skipping claude plugin validate (nested CLI sessions not supported)

plugins/scientific-method/skills/evidence-first-debugging/SKILL.md
  PASSED  SymlinkTargetValidator
  PASSED  FrontmatterValidator
  PASSED  NameFormatValidator
  PASSED  DescriptionValidator
  PASSED  NamespaceReferenceValidator
  PASSED  ComplexityValidator
  PASSED  InternalLinkValidator
  WARNING ProgressiveDisclosureValidator
    INFO [PD002] progressive-disclosure: No examples/ directory found (consider adding for documentation)
    INFO [PD003] progressive-disclosure: No scripts/ directory found (consider adding for documentation)

plugins/scientific-method/skills/experiment-protocol/SKILL.md
  PASSED  SymlinkTargetValidator
  PASSED  FrontmatterValidator
  PASSED  NameFormatValidator
  PASSED  DescriptionValidator
  PASSED  NamespaceReferenceValidator
  PASSED  ComplexityValidator
  PASSED  InternalLinkValidator
  WARNING ProgressiveDisclosureValidator
    INFO [PD001] progressive-disclosure: No references/ directory found (consider adding for documentation)
    INFO [PD002] progressive-disclosure: No examples/ directory found (consider adding for documentation)
    INFO [PD003] progressive-disclosure: No scripts/ directory found (consider adding for documentation)

plugins/scientific-method/skills/scientific-thinking/SKILL.md
  PASSED  SymlinkTargetValidator
  PASSED  FrontmatterValidator
  PASSED  NameFormatValidator
  PASSED  DescriptionValidator
  PASSED  NamespaceReferenceValidator
  PASSED  ComplexityValidator
  PASSED  InternalLinkValidator
  WARNING ProgressiveDisclosureValidator
    INFO [PD002] progressive-disclosure: No examples/ directory found (consider adding for documentation)
    INFO [PD003] progressive-disclosure: No scripts/ directory found (consider adding for documentation)

Validation Summary: PASSED
Total files: 4 | Passed: 4 | Failed: 0
Exit code: 0
```

Token counts per skill (from `--tokens-only --filter-type=skills`):

```text
948    plugins/scientific-method/skills/evidence-first-debugging/SKILL.md
1971   plugins/scientific-method/skills/experiment-protocol/SKILL.md
832    plugins/scientific-method/skills/scientific-thinking/SKILL.md
```

No SK006 or SK007 token threshold warnings produced. All three skills pass ComplexityValidator at current token counts.
