# Feature Context: Multi-Ecosystem Plugin Creator

## Document Metadata

- **Generated**: 2026-03-06
- **Input Type**: simple_description (with pre-researched technical facts)
- **Source**: Feature request provided directly with verified OpenCode technical facts
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

The `plugin-creator` plugin currently only understands Claude Code's schema for SKILL.md and agent
frontmatter. It needs to become multi-ecosystem aware so that:

1. When working on a plugin that contains OpenCode-compatible frontmatter fields (e.g., `mcp:` in
   SKILL.md), it does NOT treat those fields as invalid or strip them
2. It detects that the plugin targets multiple runtimes (Claude Code + OpenCode) and applies the
   correct schema per runtime
3. It knows the differences in how skills are handled per provider (Claude Code vs OpenCode)
4. When validating or editing skill/agent files, it preserves non-Claude frontmatter entries and
   considers the OpenCode schema

---

## Core Intent Analysis

### WHO (Target Users)

Plugin authors who are building skills that run on both Claude Code and OpenCode simultaneously.
They maintain a single SKILL.md file with both Claude Code fields (e.g., `hooks:`, `agent:`,
`user-invocable:`) and OpenCode fields (e.g., `mcp:`) in the same frontmatter block.

### WHAT (Desired Outcome)

The plugin-creator toolchain — specifically `plugin_validator.py`, `normalize_frontmatter.py`,
`frontmatter_core.py`, and the AI-facing skill documentation — treats non-Claude-Code frontmatter
fields in SKILL.md as valid when the file targets a multi-runtime plugin. The validator does not
flag, strip, or warn on `mcp:` fields. When the plugin-creator agent assists with editing, it
does not overwrite or remove OpenCode-specific fields.

### WHEN (Trigger Conditions)

- A plugin author creates or edits a SKILL.md that includes an `mcp:` block (OpenCode-style
  embedded MCP server config)
- A plugin author runs `plugin_validator.py --fix` and discovers it stripped their `mcp:` block
- The plugin-creator AI agent helps write or refactor a skill and deletes `mcp:` because it
  isn't in the known schema
- A plugin author wants to create a new skill explicitly targeting both Claude Code and OpenCode

### WHY (Problem Being Solved)

As the SKILL.md format becomes a cross-vendor open standard (agentskills.io adopters include
Claude Code, Cursor, VS Code Copilot, Gemini CLI, OpenCode, and others), plugin authors are
creating skills that span multiple runtimes. The plugin-creator currently has a Claude Code-only
worldview — its Pydantic models, fix routines, normalization pass, and AI-facing documentation
all assume only Claude Code semantics. A multi-runtime SKILL.md that includes `mcp:` frontmatter
currently risks data loss during auto-fix or normalization.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: `extra="allow"` on all three frontmatter models

- **Location**: `plugins/plugin-creator/scripts/frontmatter_core.py:83` (SkillFrontmatter),
  `frontmatter_core.py:125` (CommandFrontmatter), `frontmatter_core.py:169` (AgentFrontmatter)
- **Relevance**: All three Pydantic models already use `ConfigDict(extra="allow")`, meaning
  unknown fields (including `mcp:`) do NOT cause Pydantic validation errors. They are silently
  accepted at the model level.
- **Reusable**: The Pydantic layer already tolerates OpenCode fields — the risk is elsewhere
  (normalization round-trip, fix routines, AI agent behavior).

#### Pattern 2: `agent-plugin-ecosystem` skill — existing multi-vendor awareness

- **Location**: `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md`
- **Relevance**: This skill already documents Claude Code, Cursor, agentskills.io portable fields,
  and the AAIF. It lists OpenCode as an agentskills.io adopter (via the `agentskills/references/
  integration.md` reference). It is the existing extension point for adding OpenCode schema
  knowledge.
- **Reusable**: The skill's self-update protocol section and cross-vendor comparison table are
  exactly the right place to add OpenCode-specific facts.

#### Pattern 3: `normalize_frontmatter.py` round-trip via `frontmatter_utils`

- **Location**: `plugins/plugin-creator/scripts/normalize_frontmatter.py:49`
- **Relevance**: The normalizer round-trips every frontmatter block through `load_frontmatter` /
  `dump_frontmatter`. Whether `mcp:` (a nested YAML dict) survives this round-trip intact depends
  on `frontmatter_utils.py` — which was not read. This is the primary risk vector for silent data
  loss.
- **Reusable**: If `frontmatter_utils` uses ruamel.yaml's round-trip loader (not safe loader),
  nested structures are preserved. This needs verification.

#### Pattern 4: FM error codes FM001–FM010

- **Location**: `plugins/plugin-creator/scripts/plugin_validator.py:257–267`
- **Relevance**: The 10 frontmatter error codes cover YAML syntax, missing required fields, type
  mismatches, multiline indicators, and colon quoting. None report or flag unknown fields. There
  is no "FM011: unrecognized field" code.
- **Reusable**: The error code registry is extensible — adding ecosystem-aware codes (e.g.,
  "FM011: OpenCode `mcp:` field requires stdio or http sub-keys") would fit the existing pattern.

#### Pattern 5: `agentskills/references/integration.md` — existing OpenCode mention

- **Location**: `plugins/plugin-creator/skills/agentskills/references/integration.md:133`
- **Relevance**: OpenCode is already listed as an agentskills.io adopter in the existing
  reference material, confirming OpenCode is a known ecosystem in this codebase.
- **Reusable**: Source citation exists; schema details just need to be added alongside it.

### Existing Infrastructure

- **Pydantic schema layer** (`frontmatter_core.py`): tolerates unknown fields via `extra="allow"`.
  No changes needed here unless runtime-specific validation modes are added.
- **Error code registry** (`plugin_validator.py:ErrorCode enum`): extensible by adding new enum
  values and corresponding validation logic.
- **`agent-plugin-ecosystem` skill**: the canonical location for multi-vendor knowledge. Already
  has self-update protocol.
- **`skill-creator` skill**: teaches authors what frontmatter fields are valid. Currently teaches
  only Claude Code fields.

### Code References

- `plugins/plugin-creator/scripts/frontmatter_core.py:77–95` — `SkillFrontmatter` model with
  known Claude Code fields; `extra="allow"` at line 83
- `plugins/plugin-creator/scripts/frontmatter_core.py:218` — `_MODEL_REGISTRY` dict — extension
  point for adding runtime-specific models
- `plugins/plugin-creator/scripts/plugin_validator.py:257–267` — FM error code enum definition
- `plugins/plugin-creator/scripts/normalize_frontmatter.py:49` — round-trip import; risk vector
  for `mcp:` field survival
- `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md:36–47` — existing cross-vendor
  portable field list (does not mention `mcp:`)
- `plugins/plugin-creator/skills/agentskills/references/integration.md:133` — OpenCode listed
  as adopter

---

## Use Scenarios

### Scenario 1: Author runs `--fix` on a multi-runtime SKILL.md

**Actor**: Plugin author targeting Claude Code + OpenCode
**Trigger**: Runs `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix skills/my-skill/SKILL.md` after editing the skill
**Goal**: Fix legitimate Claude Code validation issues (e.g., unquoted colon in description) without losing the `mcp:` block
**Expected Outcome**: The `mcp:` block is preserved verbatim; only the reported issues are fixed; no data loss

### Scenario 2: AI agent helps refactor a SKILL.md

**Actor**: Plugin author using `/skill-creator` or the plugin-assessor agent
**Trigger**: Asks the AI to "clean up" or "optimize" their multi-runtime skill file
**Goal**: Improve description wording or reorganize content without losing OpenCode config
**Expected Outcome**: The agent recognizes `mcp:` as a valid OpenCode field, does not flag it as unknown, and preserves it in the output

### Scenario 3: Author creates a new skill targeting both runtimes

**Actor**: Plugin author starting fresh
**Trigger**: Uses `/skill-creator` to scaffold a new skill and wants it to work on both Claude Code and OpenCode
**Goal**: Get a scaffold that includes both Claude Code fields and the correct `mcp:` structure
**Expected Outcome**: The skill-creator skill knows the OpenCode `mcp:` field format and can scaffold it alongside Claude Code fields, or at minimum doesn't warn about it

### Scenario 4: Validator runs in CI on a multi-runtime plugin

**Actor**: CI pipeline (pre-commit hook via `plugin-validator` hook in `.pre-commit-config.yaml`)
**Trigger**: Author commits a SKILL.md containing `mcp:`
**Goal**: Validation passes without false-positive errors for the `mcp:` field
**Expected Outcome**: No error emitted for `mcp:`. If OpenCode schema validation is desired, it validates the sub-structure correctly (stdio vs http configs).

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | `normalize_frontmatter.py` round-trip through `frontmatter_utils` — unknown whether `mcp:` (nested dict) survives intact | Silent data loss if normalizer strips nested unknown keys |
| 2 | Behavior | `--fix` mode in `plugin_validator.py` — unclear if fix routines preserve fields not in the known schema | Data loss for `mcp:` during auto-fix operations |
| 3 | Scope | No definition of what "multi-runtime detection" means — heuristic (presence of `mcp:` field?) or explicit declaration (e.g., `targets: [claude-code, opencode]` frontmatter key)? | Determines how the validator knows to apply OpenCode schema rules |
| 4 | Scope | Should the validator validate OpenCode `mcp:` field structure (stdio/http sub-keys), or only preserve it without validating? | Determines depth of implementation |
| 5 | Integration | `agent-plugin-ecosystem` skill needs OpenCode section — but how much? Full schema, or just `mcp:` field? | Scope of AI-facing documentation update |
| 6 | User | Who is the primary user — plugin authors at this repository, or downstream users installing the plugin-creator plugin? | Determines whether changes are to the local scripts only, or to the installable plugin |
| 7 | Scope | Does OpenCode support agent frontmatter with extra fields, or is this SKILL.md only? | Whether `AgentFrontmatter` model also needs ecosystem awareness |
| 8 | Behavior | `skill-creator` SKILL.md teaches frontmatter fields to AI agents — currently Claude Code only. Should it teach the multi-runtime pattern? | AI agents creating skills won't know to add `mcp:` even if the validator accepts it |
| 9 | Integration | Are there other OpenCode-specific fields beyond `mcp:` that might appear in SKILL.md frontmatter? (The research provided only covers `mcp:`) | Incomplete schema coverage if other fields exist |
| 10 | Scope | `mcp.json` sidecar file — should plugin-creator know about this alternative format? Does it need to validate `mcp.json` files? | Determines whether file-discovery logic needs updating |

---

## Questions Requiring Resolution

### Q1: Multi-runtime detection mechanism

- **Category**: Scope
- **Gap**: Gap 3 — no definition of how the validator detects that a skill targets multiple runtimes
- **Question**: Should multi-runtime targeting be signaled by an explicit frontmatter field (e.g., `targets: opencode, claude-code`), or should the validator infer it from the presence of ecosystem-specific fields (e.g., if `mcp:` is present, assume OpenCode targeting)?
- **Options**:
  - A) Explicit declaration field in frontmatter
  - B) Heuristic inference from known ecosystem-specific fields
  - C) No detection needed — just always preserve unknown fields without attempting ecosystem-specific validation
- **Why It Matters**: Determines whether a new frontmatter field is introduced, whether the validator has conditional logic paths, and what the skill-creator scaffold looks like
- **Resolution**: _pending_

---

### Q2: OpenCode validation depth

- **Category**: Scope
- **Gap**: Gap 4 — should the validator validate `mcp:` sub-structure or only preserve it?
- **Question**: When a SKILL.md contains `mcp:`, should `plugin_validator.py` validate the `mcp:` block against the OpenCode schema (stdio: requires `command`/`args`; http: requires `url`), or should it only preserve the field and skip validation of its contents?
- **Options**:
  - A) Preserve only — no validation of `mcp:` contents
  - B) Validate `mcp:` structure against known OpenCode schema
  - C) Warn that `mcp:` is an OpenCode field but do not validate its contents
- **Why It Matters**: Determines whether a new Pydantic model for OpenCode SKILL.md frontmatter is needed, and the scope of the implementation
- **Resolution**: _pending_

---

### Q3: Normalization and fix safety

- **Category**: Behavior
- **Gap**: Gaps 1 and 2 — unknown whether `mcp:` survives round-trip and fix operations today
- **Question**: Have you observed `mcp:` being stripped by `--fix` or `normalize_frontmatter.py` on an actual multi-runtime SKILL.md, or is this a preventive/anticipated concern? If observed: what was the exact command and what was lost?
- **Why It Matters**: If the round-trip already preserves `mcp:` (because `frontmatter_utils` uses ruamel.yaml round-trip mode which retains unknown keys), the fix may be documentation-only. If it does strip, a concrete fix is needed.
- **Resolution**: _pending_

---

### Q4: Scope — SKILL.md only or also agents?

- **Category**: Scope
- **Gap**: Gap 7 — whether OpenCode agent frontmatter also needs ecosystem awareness
- **Question**: Is this feature request limited to SKILL.md files, or should it also apply to agent frontmatter files (agents/*.md)?
- **Options**:
  - A) SKILL.md only (where `mcp:` lives per the verified OpenCode schema)
  - B) Both SKILL.md and agent files
- **Why It Matters**: `AgentFrontmatter` in `frontmatter_core.py` already has `extra="allow"`, so there is no blocking issue — but AI-facing documentation and scaffolding may need updating for agents too
- **Resolution**: _pending_

---

### Q5: OpenCode beyond `mcp:` — complete field list?

- **Category**: Scope
- **Gap**: Gap 9 — the research provided covers `mcp:` only
- **Question**: Are there other OpenCode-specific SKILL.md frontmatter fields beyond `mcp:` that should be recognized? For example: lifecycle fields, provider-specific metadata, version constraints?
- **Why It Matters**: If additional OpenCode fields exist, the schema documentation and any new validation models need to cover them. A partial list leads to repeated work.
- **Resolution**: _pending_

---

### Q6: Who triggers this — author or downstream user?

- **Category**: User
- **Gap**: Gap 6 — scope of where changes need to land
- **Question**: Are the plugin authors affected by this issue working in this repository directly, or are they downstream users who have installed the `plugin-creator` plugin into their own projects?
- **Options**:
  - A) This repository only — changes to local scripts and AI-facing skills are sufficient
  - B) Downstream users — the installable plugin itself must be updated so all users of plugin-creator get multi-ecosystem awareness
- **Why It Matters**: Determines whether this is a documentation/skill update or a full plugin release
- **Resolution**: _pending_

---

### Q7: `mcp.json` sidecar — in scope?

- **Category**: Scope
- **Gap**: Gap 10 — the OpenCode research describes `mcp.json` as an alternative to `mcp:` frontmatter
- **Question**: Should plugin-creator learn about `mcp.json` sidecar files (detecting them, not stripping them, scaffolding them), or is this feature request limited to frontmatter `mcp:` fields only?
- **Why It Matters**: `mcp.json` is a separate file type that `normalize_frontmatter.py` and `plugin_validator.py` don't currently process — adding support requires different code paths than frontmatter changes
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. The plugin-creator validator does not strip or flag `mcp:` fields in SKILL.md frontmatter
2. `normalize_frontmatter.py` preserves `mcp:` and other OpenCode-specific frontmatter fields through round-trip normalization
3. `plugin_validator.py --fix` does not alter `mcp:` content
4. The `agent-plugin-ecosystem` skill documents the OpenCode `mcp:` field format with source citation
5. The `skill-creator` skill teaches the multi-runtime SKILL.md pattern so AI agents don't inadvertently remove OpenCode fields when editing
6. (Conditional on Q2) `plugin_validator.py` validates `mcp:` sub-structure against OpenCode schema
7. (Conditional on Q1) A detection mechanism identifies multi-runtime skills and applies runtime-appropriate validation

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-06_

### Design Refinements

1. **Gap 1 and Gap 2 resolved — no normalizer changes needed**: The feature context listed
   `normalize_frontmatter.py` round-trip survival of `mcp:` as a gap requiring verification
   (Gaps 1 and 2). Implementation confirmed `ruamel.yaml` round-trip mode preserves nested
   dicts verbatim. No changes to `frontmatter_utils.py` or `normalize_frontmatter.py` were
   made. Gap 1 and Gap 2 are closed as non-issues.
   - Original: "Unknown whether `mcp:` (nested dict) survives intact" (Gap 1); "unclear if fix
     routines preserve fields not in the known schema" (Gap 2)
   - Actual: Round-trip layer is safe. Only FM009 in `plugin_validator.py` was the live risk.
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

2. **Q1 resolved — heuristic detection (Option B) implemented**: The feature context listed
   multi-runtime detection mechanism as pending (Q1). Architecture spec chose Option B
   (heuristic inference from ecosystem-owned key presence). Implementation confirmed this via
   the state machine in `_fix_unquoted_colons()`.
   - Original: "Resolution: _pending_"
   - Actual: Option B implemented — ecosystem registry consulted before FM009 loop; no new
     frontmatter field introduced.
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

3. **Q2 resolved — preserve only (Option A) implemented**: OpenCode `mcp:` sub-structure is
   not validated. The validator preserves the block without inspecting its contents. EC001
   informational code deferred to follow-up per Decision D2.
   - Original: "Resolution: _pending_"
   - Actual: Option A (preserve only). No Pydantic model for OpenCode schema.
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

4. **Subprocess test fixture must be named `SKILL.md`**: Tests calling `plugin_validator.py
   --fix` via subprocess discovered that FM009 only fires on files detected as SKILL.md type
   by the validator's file-type detection. Fixtures with arbitrary `.md` names produce false
   passes. All integration tests use `SKILL.md` as the target filename.
   - Original: Architecture spec fixture example used `<fixture_path>` without naming constraint
   - Actual: Fixture must be named `SKILL.md`; test copies fixture content to a temp `SKILL.md`
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

5. **`_fix_unquoted_colons()` is a method, not a standalone function**: Unit tests for the
   FM009 guard must instantiate `FrontmatterValidator` rather than calling the function directly.
   - Original: Architecture spec pseudocode showed it as a standalone function
   - Actual: Method on `FrontmatterValidator` class
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest
