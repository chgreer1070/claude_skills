---
title: "Multi-Ecosystem Plugin Creator Architecture"
feature: multi-ecosystem-plugin-creator
status: DRAFT
date: 2026-03-06
---

# Multi-Ecosystem Plugin Creator Architecture

## Executive Summary

The `plugin-creator` plugin currently applies Claude Code-only semantics when validating, normalizing,
and scaffolding SKILL.md files. As the agentskills.io standard gains adopters (Claude Code, OpenCode,
AmpCode, Cursor, VS Code Copilot, Gemini CLI), plugin authors are writing SKILL.md files that contain
both Claude Code fields and OpenCode-specific fields — primarily the `mcp:` dict — in the same
frontmatter block.

Three failure modes exist today:

1. **FM009 colon-fix fires on `mcp:` sub-keys.** The unquoted-colon regex in `plugin_validator.py`
   matches any `key: value: more` line. An `mcp:` block with nested server configs (e.g.,
   `command: npx -y server`) can trigger FM009, which auto-rewrites the line with incorrect quoting.
2. **AI agents clobber unknown fields.** `skill-creator`, `agent-creator`, `subagent-refactorer`,
   and `plugin-assessor` only know Claude Code schema. When asked to clean up or optimize a
   multi-runtime SKILL.md, they flag or remove `mcp:` as unrecognized.
3. **No scaffolding guidance.** Authors creating a new skill targeting both runtimes have no
   reference for the correct `mcp:` structure or how to combine it with Claude Code fields.

The round-trip layer (`frontmatter_utils.py` using `ruamel.yaml` round-trip mode) is **not** a risk
vector. ruamel.yaml round-trip mode preserves all keys — known and unknown — verbatim, including
nested dicts. No changes to the YAML serialization layer are needed.

This architecture addresses all three failure modes through four targeted changes:

- A new **ecosystem registry** (`ecosystem_registry.py`) that declares known-good fields per vendor
- A **validator guard** that exempts ecosystem-owned fields from FM009 colon rewrites
- **AI-facing documentation updates** to four reference files
- **Agent prompt additions** to four agents that touch SKILL.md content

No new Python dependencies are required. The Pydantic `extra="allow"` layer remains unchanged.

## Architecture Overview

### Current Data Flow (Problem State)

```
Author writes SKILL.md with mcp: block
        │
        ▼
plugin_validator.py --fix
        │
        ├─ FM009 regex: matches "command: npx -y server" inside mcp: ──> REWRITES (data corruption)
        │
        ▼
normalize_frontmatter.py round-trip
        │
        └─ ruamel.yaml round-trip mode ──> mcp: dict preserved verbatim (safe, no change needed)

Author asks /skill-creator to optimize SKILL.md
        │
        ▼
skill-creator agent (Claude Code schema only)
        │
        └─ sees mcp: ──> flags as unknown, may remove or warn (AI-level data loss)
```

### Target Data Flow (After This Architecture)

```
Author writes SKILL.md with mcp: block
        │
        ▼
plugin_validator.py --fix
        │
        ├─ Ecosystem registry consulted: mcp: is an OpenCode-owned field
        ├─ FM009 guard: skip colon-fix for fields registered to any ecosystem
        └─ No rewrites to mcp: sub-structure

Author asks /skill-creator to optimize SKILL.md
        │
        ▼
skill-creator agent (loads agent-plugin-ecosystem skill)
        │
        ├─ agent-plugin-ecosystem skill now includes OpenCode mcp: schema
        └─ Agent treats mcp: as valid OpenCode field, preserves it

Author creates new multi-runtime skill
        │
        ▼
skill-creator / init_skill.py
        │
        └─ New documentation section: multi-runtime scaffold pattern with mcp: example
```

### Component Relationships

```
ecosystem_registry.py (new)
        │
        ├─── imported by ──> plugin_validator.py (FM009 guard)
        ├─── imported by ──> normalize_frontmatter.py (no-op: round-trip already safe, but
        │                    registry available for future ecosystem-specific normalization rules)
        └─── referenced by ──> agent-plugin-ecosystem/SKILL.md (human-readable version)

agent-plugin-ecosystem/SKILL.md (updated)
        │
        └─── loaded by ──> skill-creator, agent-creator, subagent-refactorer, plugin-assessor
                           (via their skills: field or explicit Skill() calls)

frontmatter-requirements.md (updated)
        │
        └─── scoped rule: applies to **/SKILL.md, **/agents/**/*.md, **/commands/**/*.md
             (all agents operating on these files see the update automatically)
```

## Key Finding: Round-Trip Safety Is Already Solved

**Observation from `plugins/plugin-creator/scripts/frontmatter_utils.py`:**

`RuamelYAMLHandler` initializes with `YAML(typ="rt")` — ruamel.yaml's round-trip mode. This mode
preserves all YAML keys, including nested dicts, regardless of whether they appear in any Pydantic
model. The `mcp:` dict (a nested YAML structure) will survive `load_frontmatter` / `dump_frontmatter`
round-trips intact.

`preserve_quotes = False` means unnecessary quotes are stripped — but this applies to scalar values,
not to the presence or absence of keys. Nested dict keys are not affected.

**Conclusion:** `normalize_frontmatter.py` is safe for multi-runtime SKILL.md files today. No changes
to `frontmatter_utils.py` or `normalize_frontmatter.py` are needed.

### The Actual Risk: FM009 Colon-Fix Regex

The FM009 regex in `plugin_validator.py` (`_fix_unquoted_colons()`) operates on raw frontmatter text
line-by-line, before YAML parsing. The pattern:

```
^(\s*([\w-]+):\s+)([^'"\[\{|>].+:.*)$
```

This matches **any indented line** with a colon in its value — not only the top-level `description:`
field. An `mcp:` block like:

```yaml
mcp:
  my-server:
    command: npx -y @modelcontextprotocol/server-filesystem
    args: /tmp
```

contains the line `    command: npx -y @modelcontextprotocol/server-filesystem`. That line matches the
FM009 pattern because it is indented, has `command:` as key, and `npx -y @modelcontextprotocol/server-filesystem`
as a value that contains no special YAML characters at its start. The fix routine would rewrite it
to `    command: 'npx -y @modelcontextprotocol/server-filesystem'` — a quote-wrapped value that is
still valid YAML, but an unnecessary mutation that marks the file as changed and confuses diff history.

More critically: the http-style `mcp:` format uses a `url:` key whose value is typically `https://...`,
a colon-containing value. FM009 would attempt to quote this, potentially producing malformed YAML if
the value already contains quotes or special characters.

**This is the primary code change target.** The FM009 fix routine must skip lines that belong to
ecosystem-owned field blocks.

## Decision Log

### D1 — Multi-Runtime Detection Mechanism

**Options considered:**

- A) Explicit `ecosystems:` or `targets:` field in SKILL.md frontmatter
- B) Heuristic: detect presence of known ecosystem-specific fields (e.g., if `mcp:` present, infer OpenCode)
- C) Option C from feature context: no detection at all — always preserve unknown fields

**Decision: Option B (heuristic inference) as the primary path, with no new frontmatter field.**

**Rationale:**

- Option A adds a required field that authors must remember to set. The failure mode is: author forgets
  `targets:`, validator behaves as Claude Code-only, FM009 fires on `mcp:` anyway. The field solves
  nothing if the heuristic already works.
- Option C (always preserve) is the correct long-term default — the Pydantic `extra="allow"` layer
  already does this. The remaining gap is the FM009 text-level rewrite, which needs ecosystem awareness
  regardless of whether there is a declaration field.
- Option B combined with the ecosystem registry gives the validator enough information: if a field key
  matches a key registered to any known ecosystem, skip the colon-fix transformation for that field's
  entire block.

**Concrete detection rule:** Before the FM009 fix loop, parse the YAML (already done in Step 3 of
`FrontmatterValidator.validate()`). Collect the set of top-level keys. For each top-level key, consult
the ecosystem registry. If the key is registered to any ecosystem other than Claude Code, mark it as
an ecosystem-owned key. Lines inside ecosystem-owned blocks are skipped by the FM009 fix routine.

**No new SKILL.md frontmatter field is introduced.**

---

### D2 — OpenCode `mcp:` Validation Depth

**Options considered:**

- A) Preserve only — no validation of `mcp:` contents
- B) Validate `mcp:` structure against known OpenCode schema (stdio requires `command`/`args`, http requires `url`)
- C) Warn that `mcp:` is an OpenCode field but do not validate its contents

**Decision: Option A (preserve only) for this feature. Option C (informational annotation) added to
error code registry as a future extension point.**

**Rationale:**

- The primary user value is non-destruction. A validator that recognizes and preserves `mcp:` without
  touching it delivers the critical use case (Scenario 1 and Scenario 4 from the feature context).
- OpenCode schema validation requires maintaining a second Pydantic model and keeping it in sync with
  the oh-my-opencode source. That is ongoing maintenance cost with unclear benefit — plugin authors
  will discover OpenCode validation errors when they actually test in OpenCode, not from this validator.
- A new informational error code `EC001` ("Field belongs to OpenCode ecosystem — validated by OpenCode
  runtime, not this validator") creates an extension point without committing to validation logic now.
  Implementation of `EC001` is deferred to a follow-up.

---

### D3 — `mcp.json` Sidecar File

**Decision: Out of scope for this feature.**

**Rationale:**

- `mcp.json` is a separate file type. `plugin_validator.py` and `normalize_frontmatter.py` process
  `.md` files with frontmatter — they do not open or inspect JSON sidecar files. Adding `mcp.json`
  awareness requires new file-discovery logic and a separate validation path.
- The frontmatter `mcp:` block covers the inline case. Authors who prefer the sidecar format are
  unaffected by the current failure modes (FM009 only fires on `.md` frontmatter).
- A backlog item should be created for `mcp.json` sidecar awareness in the plugin structure validator.

---

### D4 — Scope: SKILL.md Only vs. Also Agent Files

**Decision: SKILL.md only for the OpenCode `mcp:` field. Agent file protection is already provided
by `extra="allow"` and the FM009 guard applies uniformly to all file types.**

**Rationale:**

- The verified OpenCode schema places `mcp:` in SKILL.md frontmatter (or the `mcp.json` sidecar),
  not in agent frontmatter. No OpenCode agent frontmatter fields are currently known.
- The FM009 fix guard will be implemented as a general mechanism (ecosystem-owned keys are exempt)
  that applies to all frontmatter files, not just SKILL.md. This means if OpenCode or another
  ecosystem later adds fields to agent files, the guard already covers them.

---

### D5 — Ecosystem Registry Location

**Decision: New Python module `ecosystem_registry.py` as a standalone stdlib module in
`plugins/plugin-creator/scripts/`, imported by `plugin_validator.py`.**

**Rationale:**

- Placing ecosystem knowledge in a dedicated module separates concerns cleanly. `plugin_validator.py`
  is already 5,095 lines. Adding ecosystem schemas inline would make it harder to maintain.
- A standalone module with no external dependencies can be imported by both `plugin_validator.py`
  and any future tools (e.g., a scaffold generator, a documentation sync script) without circular
  imports.
- The module must be stdlib-only because `plugin_validator.py` is a PEP 723 script — its imports
  must resolve to the same Python environment. `ecosystem_registry.py` as a sidecar module (not
  a PEP 723 script itself) will be resolved via the `sys.path.insert(0, ...)` pattern already
  used by `normalize_frontmatter.py` to import `frontmatter_utils`.

## Component 1 — Ecosystem Registry

### File

`plugins/plugin-creator/scripts/ecosystem_registry.py` (new file, stdlib-only)

### Purpose

A single source of truth for which frontmatter fields belong to which ecosystem. Consumed by:

- `plugin_validator.py` — FM009 guard (which fields to skip during colon-fix)
- Future tooling — scaffolding, documentation sync, schema diff

### Interface Contract

The module exposes two public functions. Implementation agents must satisfy these signatures exactly.

```python
def get_ecosystem_owned_keys() -> frozenset[str]:
    """Return all top-level frontmatter keys claimed by any non-Claude-Code ecosystem.

    These keys must not be rewritten, stripped, or flagged by the Claude Code
    validator. Their sub-structure is owned by the respective ecosystem's runtime.

    Returns:
        Frozen set of top-level YAML key names (e.g., {"mcp"}).
    """
    ...

def get_ecosystem_for_key(key: str) -> str | None:
    """Return the ecosystem name that owns the given frontmatter key, or None.

    Args:
        key: A top-level frontmatter key name (without the colon).

    Returns:
        Ecosystem name string (e.g., "opencode") or None if key is Claude Code-native
        or unknown.
    """
    ...
```

### Data Schema

The registry is a module-level constant — a dict mapping ecosystem names to their field descriptors.
No external file reads, no JSON parsing, no network calls. All data is inline in the module.

```python
# Conceptual shape — implementation agent fills in the actual values
_REGISTRY: dict[str, EcosystemSpec] = {
    "opencode": EcosystemSpec(
        display_name="OpenCode",
        source_url="https://github.com/sst/opencode",
        verified_date="2026-03-06",
        skill_frontmatter_keys=frozenset({"mcp"}),
        agent_frontmatter_keys=frozenset(),
        notes="mcp: dict supports two sub-formats: stdio (command/args/env) and http (url/headers). "
              "Alternative: mcp.json sidecar file (not covered by this validator).",
    ),
}
```

### `EcosystemSpec` TypedDict or dataclass

```python
# Exact type — either TypedDict or dataclass, implementation agent decides
# Fields:
#   display_name: str             — human-readable ecosystem name
#   source_url: str               — URL of ecosystem source or docs
#   verified_date: str            — ISO date string of last verification
#   skill_frontmatter_keys: frozenset[str]  — top-level SKILL.md keys owned by this ecosystem
#   agent_frontmatter_keys: frozenset[str]  — top-level agent frontmatter keys owned by this ecosystem
#   notes: str                    — free-text notes for documentation purposes
```

### OpenCode `mcp:` Field Specification

The following is the verified schema for the OpenCode `mcp:` frontmatter field. This is the
authoritative reference for both the registry and the AI-facing documentation.

**Source:** `oh-my-opencode` repository, `/src/features/opencode-skill-loader/skill-mcp-config.ts`
(as provided in the feature request — implementation agent must cite this URL with access date in
the module's docstring and in `agent-plugin-ecosystem/SKILL.md`).

**Top-level key:** `mcp` (dict)

Each entry under `mcp:` is a named server config. Two sub-formats:

**stdio format** (local process):

```yaml
mcp:
  server-name:
    command: <executable>       # required — command to run
    args:                       # optional — list of arguments
      - arg1
      - arg2
    env:                        # optional — environment variable overrides
      KEY: value
```

**http/SSE format** (remote server):

```yaml
mcp:
  server-name:
    url: https://example.com/mcp    # required — SSE endpoint URL
    headers:                         # optional — HTTP headers dict
      Authorization: Bearer token
```

**AmpCode note:** AmpCode shares the same `mcp.json` sidecar format documented in oh-my-opencode.
Whether AmpCode also supports the inline `mcp:` frontmatter key is unverified. The registry should
note this uncertainty. Implementation agent: do not assert AmpCode supports inline `mcp:` unless
you can cite a primary source.

### What the Registry Does NOT Do

- Does not validate `mcp:` sub-structure contents (Decision D2 — preserve only)
- Does not track all fields from all ecosystems (only fields that create conflict with Claude Code validation)
- Does not replace the Pydantic models (those remain Claude Code-specific with `extra="allow"`)

## Component 2 — Validator Changes

### File

`plugins/plugin-creator/scripts/plugin_validator.py` (modify existing, 5,095 lines)

### Change 1: Import ecosystem registry

At the top of `plugin_validator.py`, alongside the existing `sys.path.insert` for `frontmatter_core`:

```python
# After the existing sys.path setup for frontmatter_core
from ecosystem_registry import get_ecosystem_owned_keys
```

The import is at module level, not inside a function. If `ecosystem_registry.py` is absent (e.g.,
running an older copy of the validator), this import will fail with `ImportError` — which is correct
fail-fast behavior. Do not add a try/except fallback that silently disables the feature.

### Change 2: FM009 fix guard in `_fix_unquoted_colons()`

**Location:** `plugin_validator.py:140-180` — `_fix_unquoted_colons()` function

**Current behavior:** The function iterates over frontmatter text line by line. For each line
matching `^(\s*([\w-]+):\s+)([^'"\[\{|>].+:.*)$`, it rewrites the value with quotes.

**Required change:** Before the line-by-line loop, determine which top-level keys are
ecosystem-owned. Track state: when processing a line that is indented under an ecosystem-owned
top-level key, skip the FM009 rewrite for that line.

**Contract for the implementation:**

```python
# Pseudocode — implementation agent writes the actual code

def _fix_unquoted_colons(frontmatter_text: str) -> tuple[str, list[str]]:
    """Fix unquoted colons in frontmatter field values.

    Skips lines that belong to blocks owned by non-Claude-Code ecosystems,
    as determined by ecosystem_registry.get_ecosystem_owned_keys().

    Args:
        frontmatter_text: Raw YAML frontmatter string (without --- delimiters).

    Returns:
        Tuple of (modified_text, list_of_fixed_field_names).
    """
    ecosystem_keys = get_ecosystem_owned_keys()  # e.g., frozenset({"mcp"})

    # State machine:
    # - current_ecosystem_block: str | None = None
    #   Set to key name when we are inside an ecosystem-owned block.
    #   Reset to None when we encounter a top-level key (zero-indentation line
    #   that is NOT indented) that is not in ecosystem_keys.
    #
    # - Indentation detection: a line with leading whitespace is a continuation
    #   of the current block. A line with no leading whitespace and matching
    #   r'^[\w-]+:\s*' starts a new top-level key.
    #
    # - When current_ecosystem_block is set, skip the FM009 rewrite for all lines.
    # - When current_ecosystem_block is None, apply the existing FM009 logic.
    ...
```

**Edge cases the implementation must handle:**

- Ecosystem-owned key with a YAML block scalar value (indented multi-line content starting with
  `|` or `>`). The state machine must remain in the ecosystem block for all indented continuation
  lines.
- Ecosystem key appearing as the first line of the frontmatter (no prior lines — state machine
  starts with `current_ecosystem_block = None` correctly).
- Frontmatter with only Claude Code keys — no ecosystem block encountered, function behaves
  exactly as before.
- An ecosystem-owned key whose value is a scalar on the same line (e.g., `mcp: null`) — the
  state machine enters and immediately exits the ecosystem block on the next non-indented line.

**Test contract** (for the test architect agent):

- Input: frontmatter with `mcp:` block containing `command: npx -y server`. Expected: `command:` line is not rewritten.
- Input: frontmatter with `description: Fix: something broke`. Expected: `description:` value is quoted (existing behavior unchanged).
- Input: frontmatter with only Claude Code fields, no `mcp:`. Expected: identical output to current behavior.
- Input: frontmatter with `mcp:` block containing `url: https://example.com/mcp`. Expected: `url:` line is not rewritten.
- Input: `mcp: null` (scalar). Expected: line not rewritten (ecosystem-owned key, even as scalar).

### Change 3: FM009 reporting — distinguish ecosystem-owned skips

**Current behavior:** FM009 is reported when any colon-fix is applied.

**Required change:** FM009 is NOT reported for lines that were skipped due to ecosystem ownership.
The fix routine already returns a list of fixed field names. If all matched lines were in ecosystem
blocks (zero fixes applied), FM009 must not be emitted. This is already the correct behavior if
the skip logic prevents the line from being added to the "fixed fields" list.

No change to the FM009 error code definition. No new error code for the skip (Decision D2 deferred
the EC001 informational code to a follow-up).

### Change 4: No changes to FrontmatterValidator.validate()

The validation path (Steps 1–6 documented in the codebase analysis) does not need modification.
The Pydantic `extra="allow"` already handles unknown fields. Post-validation checks
(`_check_list_valued_tool_fields`, `_check_skill_name_and_directory`) operate on known fields only
and do not touch `mcp:`. No new validation checks are added for `mcp:` contents.

### What Does NOT Change in the Validator

- `_MODEL_REGISTRY` — unchanged. `SkillFrontmatter` remains Claude Code-specific.
- `FileType.detect_file_type()` — unchanged. No ecosystem-based file type classification.
- `FRONTMATTER_EXEMPT_FILENAMES` — unchanged.
- Token counting, link validation, plugin structure validation — unchanged.
- `--fix` mode for FM004, FM007, FM008 — unchanged. These fixes operate on Claude Code-specific
  fields and do not interact with `mcp:`.
- `fix_skill_name_field()` in `frontmatter_core.py` — unchanged. Adds `name:` from directory; does
  not affect other fields.
- `validator.json` suppression config — unchanged and still available for edge cases not covered
  by the registry.

## Component 3 — AI-Facing Documentation Changes

### 3a. `agent-plugin-ecosystem` skill — OpenCode section

**File:** `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md`

**Current state:** The skill documents Claude Code and Cursor plugin bundle schemas, the
agentskills.io portable field list, and AAIF status. OpenCode is mentioned only in passing as
an agentskills.io adopter (line 36). The `mcp:` field is not mentioned anywhere.

**Required additions:**

Add a new section **"OpenCode SKILL.md Extensions"** between the existing "Cross-Vendor
Standardization Status" section and the "Writing for the Correct Target" flowchart. The section
must contain:

1. **OpenCode-specific frontmatter fields** — the `mcp:` key, its two sub-formats (stdio and http),
   with minimal but correct YAML examples matching the verified schema.

2. **AmpCode note** — AmpCode uses the `mcp.json` sidecar format; whether it supports inline `mcp:`
   frontmatter is unverified. Do not assert compatibility without a source.

3. **Preservation rule for agents** — explicit instruction: when editing a SKILL.md that contains
   an `mcp:` block, treat it as owned by the OpenCode runtime and preserve it verbatim. Do not
   remove, reformat, or flag it as an error.

4. **Source citation** — cite `oh-my-opencode` source file path and access date inline.

**Updated "Writing for the Correct Target" flowchart** — add a fourth branch for OpenCode targeting:

```
Q1 -->|OpenCode only| OC[Use mcp: frontmatter key or mcp.json sidecar<br>stdio: command/args/env<br>http: url/headers]
Q1 -->|Multiple ecosystems| Multi[Use agentskills.io portable fields + ecosystem-specific extensions<br>mcp: for OpenCode, preserved by plugin_validator.py]
```

**Updated portable fields list** — verify whether `mcp:` is portable across other agentskills.io
adopters or only OpenCode-specific. Based on current research, treat `mcp:` as OpenCode-specific,
not in the portable list.

**Self-update protocol** — add oh-my-opencode repository to the monitored URLs list:
`https://github.com/sst/opencode`

---

### 3b. `skill-creator` skill — multi-runtime scaffolding section

**File:** `plugins/plugin-creator/skills/skill-creator/SKILL.md`

**Current state:** Step 5 documents all known frontmatter fields for Claude Code. There is no
guidance on writing skills that target multiple runtimes.

**Required addition:** New subsection at the end of Step 5 (or as Step 5b) titled
**"Multi-Runtime Skills (Claude Code + OpenCode)"** containing:

1. **When to use this pattern** — the author wants a single SKILL.md that loads correctly in both
   Claude Code and OpenCode. Claude Code reads `name`, `description`, and Claude Code-specific
   fields. OpenCode reads `name`, `description`, and `mcp:`.

2. **Scaffold template** — a minimal working example of a multi-runtime SKILL.md frontmatter:

   ```yaml
   ---
   name: my-skill
   description: Does X when you need to Y — works in Claude Code and OpenCode
   user-invocable: true
   mcp:
     my-server:
       command: npx
       args:
         - -y
         - "@scope/server-package"
   ---
   ```

3. **Validator behavior** — `plugin_validator.py --fix` will not modify the `mcp:` block. Authors
   can run `--fix` normally without data loss.

4. **Portability note** — link to `agent-plugin-ecosystem` skill for the full cross-vendor
   portability picture.

---

### 3c. `frontmatter-requirements.md` scoped rule — add OpenCode preservation rule

**File:** `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md`

**Current state:** Documents required/optional fields and formatting rules for Claude Code schema.
No mention of non-Claude fields.

**Required addition:** New section **"Non-Claude Ecosystem Fields"** at the end of the file:

```markdown
## Non-Claude Ecosystem Fields

SKILL.md frontmatter may contain fields owned by other ecosystems (e.g., `mcp:` for OpenCode).
These fields are valid. Do not remove, flag, or reformat them.

- `mcp:` — OpenCode MCP server configuration. Contains stdio (`command`/`args`/`env`) or
  http (`url`/`headers`) sub-structures. Treat as opaque — do not apply Claude Code formatting
  rules to its contents.

When editing a SKILL.md that contains `mcp:`, preserve the block verbatim. The plugin validator
will not flag `mcp:` as an error.
```

**Why this file matters:** `frontmatter-requirements.md` is a scoped rule file with `paths:`
covering `**/SKILL.md`, `**/agents/**/*.md`, `**/commands/**/*.md`. It is injected into every
agent session that touches these file types. Updating it means ALL agents (not just explicitly
loaded ones) get the preservation rule without requiring changes to each agent's prompt.

---

### 3d. `agent-schema.md` — no change required

**File:** `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md`

This file documents agent frontmatter fields. No OpenCode-specific agent frontmatter fields are
currently verified. The `extra="allow"` protection already covers any future OpenCode agent fields.
No change needed at this time.

## Component 4 — Agent Prompt Changes

The `frontmatter-requirements.md` scoped rule (Component 3c) provides passive protection for all
agents. Four agents that actively write or restructure SKILL.md content also need an explicit
instruction block in their prompt bodies to reinforce the preservation rule during content
generation, not just during post-write validation.

### 4a. `skill-creator` skill — preservation instruction

**File:** `plugins/plugin-creator/skills/skill-creator/SKILL.md`

**Addition location:** Early in the skill body, before the 10-step workflow — a "Before You Begin"
or "Non-Destructive Editing" callout.

**Content to add:**

When editing an existing SKILL.md that contains an `mcp:` block or other unrecognized top-level
frontmatter keys: treat those keys as owned by another runtime ecosystem. Do not remove them.
Do not move them. Do not ask the author if they are correct. Preserve them verbatim in the output.

If scaffolding a new skill and the author has requested multi-runtime targeting, see the
multi-runtime scaffold section (Step 5b).

---

### 4b. `subagent-refactorer` agent — preservation instruction

**File:** `plugins/plugin-creator/agents/subagent-refactorer.md`

**Current behavior:** Rewrites agent prompt files, specifically targeting the `description` field.
Already loads `write-frontmatter-description` skill.

**Addition location:** In the section covering frontmatter fields that the agent is allowed to
modify. This agent focuses on `description` — add an explicit exclusion list.

**Content to add:**

Fields the `subagent-refactorer` must NOT modify, remove, or flag as invalid:
- `mcp:` and its entire sub-structure (OpenCode ecosystem-owned field)
- Any other top-level key not listed in the Claude Code agent frontmatter schema

When the agent encounters an unrecognized top-level frontmatter key, it must treat it as an
ecosystem field and exclude it from its refactoring scope. The refactoring scope is limited to
`description`, `name`, and the body content below the frontmatter block.

---

### 4c. `contextual-ai-documentation-optimizer` agent — preservation instruction

**File:** `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md`

**Current behavior:** Rewrites SKILL.md and CLAUDE.md body content for Claude comprehension.
Touches `description` field indirectly during frontmatter optimization.

**Addition location:** In the agent's instruction block covering what it is allowed to optimize.

**Content to add:**

Scope of frontmatter optimization: `description` field rewrites and `name` field corrections only.

Out of scope: Any top-level frontmatter key not present in the Claude Code SKILL.md schema.
Specifically: `mcp:` and its sub-structure must be passed through to the output file unchanged.
Do not reformat, reorder, or comment on these fields. They belong to other runtime ecosystems.

---

### 4d. `plugin-assessor` agent — assessment rule addition

**File:** `plugins/plugin-creator/agents/plugin-assessor.md`

**Current behavior:** Audits plugins for structure and frontmatter schema compliance. Read-only.

**Addition location:** In the section covering frontmatter assessment criteria.

**Content to add:**

When assessing a SKILL.md that contains `mcp:` or other unrecognized top-level frontmatter keys:

- Report the key as present with a note that it belongs to another ecosystem (e.g., "OpenCode")
- Do NOT report it as a schema violation, unknown field error, or recommendation for removal
- If the key matches a known ecosystem field (see `agent-plugin-ecosystem` skill), name the ecosystem

The assessment output for a multi-runtime SKILL.md should read: "Frontmatter contains
`mcp:` (OpenCode ecosystem field) — valid for multi-runtime targeting."

---

### Why `agent-creator` Does Not Need a Change

`agent-creator` writes agent frontmatter files, not SKILL.md files. Agent frontmatter does not
currently have any verified OpenCode-specific fields. The `extra="allow"` protection in
`AgentFrontmatter` covers unknown fields at the Pydantic level. The `frontmatter-requirements.md`
scoped rule covers the agent file paths (`**/agents/**/*.md`). No explicit addition to
`agent-creator` is needed.

## Component 5 — Scaffolding Guidance

### Decision: Documentation-Only Scaffolding (No `init_skill.py` Flag)

The feature context Scenario 3 describes an author creating a new skill targeting both runtimes.
The question is whether `init_skill.py` should grow an `--ecosystem` flag that adds an `mcp:`
block to the generated scaffold.

**Decision: Documentation-only. No changes to `init_skill.py`.**

**Rationale:**

- The `mcp:` block content is highly specific to the author's actual MCP server (name, command,
  args). A scaffold with placeholder values (`command: PLACEHOLDER`) is not more useful than a
  documented example the author can copy.
- `init_skill.py` currently scaffolds the minimal correct Claude Code frontmatter. Adding an
  `--ecosystem opencode` flag introduces a code path that must be maintained and tested. The ROI
  is low compared to a well-documented example in `skill-creator` SKILL.md.
- If multiple ecosystems eventually each need scaffold variations, a dedicated `--ecosystem` flag
  system is worth building. For a single field (`mcp:`), documentation is the correct approach.

**What authors get instead:** The multi-runtime scaffold section in `skill-creator` SKILL.md
(Component 3b) provides a copy-paste template with the correct YAML structure. The author runs
`init_skill.py` to get the base Claude Code scaffold, then manually adds the `mcp:` block from
the template.

### No Changes To

- `init_skill.py` — unchanged
- `create_plugin.py` — unchanged
- `auto_sync_manifests.py` — unchanged (does not process frontmatter content)
- `fix_tool_formats.py` — unchanged (targets `tools:` and `skills:` arrays, not `mcp:`)

## Integration Map

### New Files

| File | Type | Purpose |
|------|------|---------|
| `plugins/plugin-creator/scripts/ecosystem_registry.py` | Python module (stdlib-only) | Ecosystem-to-field registry; imported by validator |

### Modified Files

| File | Change Type | What Changes |
|------|-------------|--------------|
| `plugins/plugin-creator/scripts/plugin_validator.py` | Code change | Import `ecosystem_registry`; add state machine to `_fix_unquoted_colons()` to skip ecosystem-owned key blocks |
| `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` | Content addition | New "OpenCode SKILL.md Extensions" section; updated flowchart; updated URL watchlist |
| `plugins/plugin-creator/skills/skill-creator/SKILL.md` | Content addition | Multi-runtime scaffold section (Step 5b); preservation callout before workflow |
| `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` | Content addition | "Non-Claude Ecosystem Fields" section |
| `plugins/plugin-creator/agents/subagent-refactorer.md` | Content addition | Exclusion list: `mcp:` and unrecognized keys out of scope |
| `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` | Content addition | `mcp:` pass-through rule |
| `plugins/plugin-creator/agents/plugin-assessor.md` | Content addition | Assessment rule: ecosystem fields are valid, name the ecosystem |

### Unchanged Files

| File | Why Unchanged |
|------|---------------|
| `plugins/plugin-creator/scripts/frontmatter_core.py` | `extra="allow"` already handles unknown fields; no model changes needed |
| `plugins/plugin-creator/scripts/frontmatter_utils.py` | Round-trip already safe; no changes |
| `plugins/plugin-creator/scripts/normalize_frontmatter.py` | Round-trip already safe; no changes |
| `plugins/plugin-creator/scripts/init_skill.py` | Decision D5: documentation-only scaffolding |
| `plugins/plugin-creator/agents/agent-creator.md` | No OpenCode agent frontmatter fields; scoped rule covers it |
| `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md` | No verified OpenCode agent fields |
| `plugins/plugin-creator/skills/agentskills/references/integration.md` | OpenCode already listed as adopter; schema details go in `agent-plugin-ecosystem` |

### Implementation Order

Dependencies flow as follows. Implement in this order to avoid broken references:

```
1. ecosystem_registry.py (new)
        │
        ▼
2. plugin_validator.py FM009 guard (depends on ecosystem_registry.py)
        │
        ▼
3. agent-plugin-ecosystem/SKILL.md (independent — can be done in parallel with step 2)
   frontmatter-requirements.md (independent)
        │
        ▼
4. skill-creator/SKILL.md (references agent-plugin-ecosystem, so after step 3)
        │
        ▼
5. Agent prompt additions (subagent-refactorer, contextual-ai-documentation-optimizer,
   plugin-assessor) — can be done in parallel with step 4
```

Steps 1 and 2 are code changes (require implementation + tests).
Steps 3, 4, and 5 are documentation changes (require content writing, no code tests).

### Version Bump

The `auto_sync_manifests.py` pre-commit hook will bump `plugin-creator` version on commit:
- Adding `ecosystem_registry.py` (new script component) triggers a minor bump
- Modifying existing skills and agents triggers patch bumps per component
- The manifest hook handles this automatically; no manual version changes needed

## Testing Strategy

### Unit Tests: `ecosystem_registry.py`

Required coverage:

- `get_ecosystem_owned_keys()` returns a frozenset containing `"mcp"`
- `get_ecosystem_for_key("mcp")` returns `"opencode"`
- `get_ecosystem_for_key("description")` returns `None` (Claude Code-native field)
- `get_ecosystem_for_key("unknown-field")` returns `None` (unknown field)
- Return type is `frozenset[str]` (immutable, not accidentally mutated)

### Unit Tests: FM009 guard in `plugin_validator.py`

Required test cases (parametrized):

| Input frontmatter | Expected output behavior |
|-------------------|--------------------------|
| Contains `mcp:` with stdio `command: npx -y server` sub-key | `command:` line not rewritten; FM009 not reported |
| Contains `mcp:` with http `url: https://example.com/mcp` sub-key | `url:` line not rewritten; FM009 not reported |
| Contains `description: Fix: something broke` (no `mcp:`) | `description:` value quoted; FM009 reported |
| Contains both `description: Fix: something` and `mcp:` block | Only `description:` fixed; `mcp:` block untouched |
| Contains `mcp: null` (scalar, no sub-structure) | Line not rewritten; state machine handles scalar cleanly |
| Contains only Claude Code fields, no ecosystem fields | Behavior identical to current implementation |
| `mcp:` block with multi-line nested structure (4+ indented lines) | All indented lines skipped; state exits correctly on next top-level key |

### Integration Test: `--fix` on a multi-runtime SKILL.md

Create a fixture file containing:

```yaml
---
name: test-skill
description: "Test skill for multi-runtime validation"
user-invocable: true
mcp:
  my-server:
    command: npx -y @scope/server
    args:
      - /tmp/workspace
    env:
      API_KEY: test-value
  remote-server:
    url: https://api.example.com/mcp
    headers:
      Authorization: Bearer token
---
```

Run: `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix <fixture_path>`

Assertions:

- Exit code 0
- `mcp:` block in output is byte-for-byte identical to input (no rewrites)
- `name:`, `description:`, `user-invocable:` fields intact
- No FM009 in validator output

### Regression Test: Existing Claude Code SKILL.md Unaffected

Run `--fix` on an existing SKILL.md with no `mcp:` block that currently produces known FM009
output (e.g., a skill with `description: Fix: something`). Verify the fix still applies correctly
and output is identical to pre-change behavior.

### Scenario Walkthrough Tests (Manual Verification)

From the feature context — verify each use scenario:

- **Scenario 1** (author runs `--fix`): covered by integration test above
- **Scenario 2** (AI agent optimizes multi-runtime skill): load `skill-creator` skill, provide the
  fixture SKILL.md with `mcp:` block, ask the AI to "optimize the description". Verify `mcp:` block
  survives. This is an AI behavior test — execute manually in a Claude Code session.
- **Scenario 3** (author creates new multi-runtime skill): follow the scaffold template in
  `skill-creator` Step 5b, create a new skill with `mcp:`, run `plugin_validator.py`. Verify no
  errors on the `mcp:` block.
- **Scenario 4** (validator in CI): the pre-commit hook runs `plugin_validator.py` on SKILL.md.
  Covered by integration test; also verify `.pre-commit-config.yaml` hook pattern matches the
  fixture path.

### Test File Location

New test file: `plugins/plugin-creator/tests/test_ecosystem_registry.py`
New fixture file: `plugins/plugin-creator/tests/fixtures/multi_runtime_skill.md`
Extend existing test file (if present): `plugins/plugin-creator/tests/test_frontmatter_fixes.py`
or equivalent for FM009 tests.

If no existing test directory: create `plugins/plugin-creator/tests/` with `__init__.py`.

Implementation agent must run `uv run pytest plugins/plugin-creator/tests/` as the final quality gate.

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-06_

### Design Refinements

1. **`_fix_unquoted_colons()` is a method on `FrontmatterValidator`, not a standalone function**:
   The architecture spec pseudocode (Component 2, Change 2) presented the function as standalone.
   It is a method on the `FrontmatterValidator` class. Unit tests must instantiate the class.
   - Original: `def _fix_unquoted_colons(frontmatter_text: str) -> tuple[str, list[str]]:`
     shown as a module-level function
   - Actual: `FrontmatterValidator._fix_unquoted_colons(self, frontmatter_text)` — instance method
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

2. **Integration test fixture must use `SKILL.md` filename**: The testing strategy section
   described fixture files without a filename constraint. The validator's file-type detection
   gates FM009 application on the filename being `SKILL.md`. Fixtures with other names bypass
   FM009 and produce false passes.
   - Original: "Create a fixture file containing: [YAML]" (no filename constraint specified)
   - Actual: Fixture must be copied to a temp file named `SKILL.md` before invoking `--fix`
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

3. **`get_ecosystem_owned_keys()` does not union `agent_frontmatter_keys`**: The architecture
   spec defined `EcosystemSpec` with both `skill_frontmatter_keys` and `agent_frontmatter_keys`
   fields, implying both would be considered when building the owned-keys set. The implementation
   of `get_ecosystem_owned_keys()` unions only `skill_frontmatter_keys`. This is a latent
   inconsistency — if agent-level ecosystem fields are added to the registry, the FM009 guard
   will not protect them until this function is updated. Tracked in followup-3.
   - Original: Interface contract shows both field types in `EcosystemSpec`; function doc says
     "Return all top-level frontmatter keys claimed by any non-Claude-Code ecosystem"
   - Actual: Only `skill_frontmatter_keys` are unioned; `agent_frontmatter_keys` is unused
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

4. **`mcp: null` scalar edge case requires explicit state-machine handling**: The architecture
   spec listed this as an edge case to handle but did not detail the mechanism. Implementation
   revealed it is the hardest case: the state machine enters the ecosystem block on the `mcp:
   null` line but there are no indented continuation lines. The state must reset correctly on
   the next non-indented key. A code review finding (followup-2) identified a defect in the
   initial implementation of this edge case.
   - Original: "Ecosystem key whose value is a scalar on the same line — state machine enters
     and immediately exits the ecosystem block on the next non-indented line"
   - Actual: The "immediately exits" behavior requires an explicit non-indented line to trigger
     the reset; if `mcp: null` is the last line of frontmatter, the state does not reset (no
     further line to trigger it). This is harmless for single-entry frontmatter but required
     a test case to confirm no regression on multi-key files.
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest DN-followup-2

5. **`EcosystemSpec` implemented as frozen dataclass, not TypedDict**: The architecture spec
   left the choice to the implementation agent. A `frozen=True` dataclass was chosen to enforce
   immutability at the field level, consistent with the `frozenset` immutability requirement for
   key collections.
   - Original: "Exact type — either TypedDict or dataclass, implementation agent decides"
   - Actual: `@dataclass(frozen=True)` chosen for field-level immutability enforcement
   - Recorded in: `plan/tasks-1-multi-ecosystem-plugin-creator.md`, Context Manifest

## Out of Scope

The following are explicitly excluded from this feature. Each has a rationale and a suggested
follow-up path.

### `mcp.json` Sidecar File Support

`plugin_validator.py` and `normalize_frontmatter.py` do not process JSON sidecar files. The
frontmatter `mcp:` block covers the inline case. Authors using the sidecar format are unaffected
by the current failure modes.

Follow-up: Create a backlog item for `mcp.json` detection in the plugin structure validator.

### OpenCode `mcp:` Schema Validation (EC001)

The validator will preserve `mcp:` but will not validate its sub-structure against the OpenCode
schema. Authors discover OpenCode-specific errors by running in the OpenCode runtime.

Follow-up: After this feature ships, add `EC001` (informational: "mcp: block present, validated
by OpenCode runtime") as an informational code. Optionally add stdio/http sub-structure validation
behind a `--ecosystem opencode` flag.

### AmpCode Explicit Support

AmpCode's compatibility with inline `mcp:` frontmatter is unverified. The registry will include
a note about AmpCode + `mcp.json` sidecar but will not assert AmpCode = OpenCode for the inline
field.

Follow-up: Verify AmpCode inline `mcp:` support from primary source, then update the registry.

### Cursor or Other Ecosystems

No Cursor-specific SKILL.md frontmatter fields are currently known. Cursor's plugin bundle schema
is documented in `agent-plugin-ecosystem` for plugin.json, not SKILL.md frontmatter.

Follow-up: If Cursor adds ecosystem-specific SKILL.md fields, add them to the ecosystem registry.

### `init_skill.py` `--ecosystem` Flag

Decision D5 above. Documentation-only scaffolding covers the use case.

Follow-up: If demand grows beyond `mcp:` (multiple ecosystems, multiple fields), implement
`--ecosystem` scaffolding mode.

### GitHub Copilot, Windsurf, VS Code Copilot Frontmatter

The `hooks-guide` skill already documents GitHub Copilot hooks. No GitHub Copilot-specific
SKILL.md frontmatter fields are currently known. The `FRONTMATTER_EXEMPT_FILENAMES` set
already exempts `AGENTS.md` and `GEMINI.md`. No changes needed.

### Downstream User Distribution

The changes land in `plugins/plugin-creator/` in this repository. Downstream users who have
installed `plugin-creator` as a marketplace plugin will receive the updates on their next
`claude plugin update plugin-creator`. No separate distribution step is required — this is
standard plugin update behavior.
