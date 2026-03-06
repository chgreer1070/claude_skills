---
description: "Multi-ecosystem plugin-creator: ecosystem registry, FM009 guard, AI doc updates"
version: "1.0"
feature: multi-ecosystem-plugin-creator
tasks:
  - T1: ecosystem-registry-module
  - T2: validator-fm009-guard
  - T3: agent-plugin-ecosystem-opencode-section
  - T4: frontmatter-requirements-preservation-rule
  - T5: skill-creator-multiruntime-and-callout
  - T6: subagent-refactorer-exclusion-list
  - T7: contextual-optimizer-passthrough-rule
  - T8: plugin-assessor-ecosystem-rule
  - T9: tests-ecosystem-registry-and-fm009
task_exports:
  enabled: false
  directory: "TASK"
---

# Task Plan: Multi-Ecosystem Plugin Creator

## Dependency Graph

```
T1 (ecosystem_registry.py)
    │
    ├── T2 (validator FM009 guard)
    │       │
    │       └── T9 (tests)
    │
T3 (agent-plugin-ecosystem SKILL.md)
    │
    └── T5 (skill-creator SKILL.md)
            │
            └── (parallel with T6, T7, T8)

T4 (frontmatter-requirements.md)
    │
    ├── T6 (subagent-refactorer.md)
    ├── T7 (contextual-optimizer.md)
    └── T8 (plugin-assessor.md) [also depends T3]
```

## Parallelization Summary

| Wave | Tasks | Can run concurrently |
|------|-------|---------------------|
| 1 | T1, T3, T4 | Yes — no shared files, no mutual dependencies |
| 2 | T2, T5, T6, T7, T8 | T2 after T1; T5 after T3; T6+T7 after T4; T8 after T3+T4 |
| 3 | T9 | After T1+T2 complete |

---

## SYNC CHECKPOINT 1 — After Wave 1

Convergence: T1 + T3 + T4 outputs

Quality gates:
- `plugins/plugin-creator/scripts/ecosystem_registry.py` exists and imports without error
- `get_ecosystem_owned_keys()` returns a frozenset containing `"mcp"`
- `agent-plugin-ecosystem/SKILL.md` contains "OpenCode SKILL.md Extensions" section with both stdio and http format examples
- `frontmatter-requirements.md` contains "Non-Claude Ecosystem Fields" section with `mcp:` documented
- `uv run prek run --files plugins/plugin-creator/scripts/ecosystem_registry.py` exits 0
- `uv run prek run --files plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` exits 0
- `uv run prek run --files plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` exits 0

Reflection questions:
- Does the ecosystem registry interface match the architecture spec signatures exactly?
- Does the SKILL.md OpenCode section cite oh-my-opencode with access date?
- Do any two Wave 1 outputs reference each other with paths that do not yet exist?

Proceed to Wave 2 only after all gates pass.

---

## SYNC CHECKPOINT 2 — After Wave 2

Convergence: T2 + T5 + T6 + T7 + T8 outputs

Quality gates:
- `plugin_validator.py` imports `ecosystem_registry` without error (run `python -c "import sys; sys.path.insert(0, 'plugins/plugin-creator/scripts'); import ecosystem_registry"` from repo root)
- `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix` on a fixture with `mcp:` block does not rewrite any `mcp:` sub-key lines
- `skill-creator/SKILL.md` contains both the preservation callout (before workflow) and the Step 5b multi-runtime scaffold section
- Each agent file (subagent-refactorer, contextual-optimizer, plugin-assessor) contains its ecosystem-preservation addition
- `uv run prek run --files plugins/plugin-creator/scripts/plugin_validator.py` exits 0
- `uv run prek run --files plugins/plugin-creator/skills/skill-creator/SKILL.md` exits 0
- `uv run prek run --files plugins/plugin-creator/agents/subagent-refactorer.md` exits 0
- `uv run prek run --files plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` exits 0
- `uv run prek run --files plugins/plugin-creator/agents/plugin-assessor.md` exits 0

Reflection questions:
- Does the FM009 state machine handle the `mcp: null` scalar edge case (no indented sub-keys)?
- Does the skill-creator SKILL.md callout appear before the numbered workflow steps?
- Do any agent prompt additions introduce colons in YAML frontmatter description fields?

Proceed to Wave 3 only after all gates pass.

---

## SYNC CHECKPOINT 3 — After Wave 3 (Final)

Convergence: T9 outputs

Quality gates:
- `uv run pytest plugins/plugin-creator/tests/test_ecosystem_registry.py -v` exits 0
- `uv run pytest plugins/plugin-creator/tests/test_frontmatter_fixes.py -v` exits 0 (or equivalent FM009 test file)
- All 7 parametrized FM009 test cases pass (listed in T9 acceptance criteria)
- Integration fixture test: `--fix` on `multi_runtime_skill.md` produces byte-identical `mcp:` block
- Regression test: existing Claude Code `--fix` behavior unchanged

Final reflection:
- Are there any PENDING markers remaining in any output file?
- Does `git diff --stat` show only expected files changed?
- Is every modified file under `plugins/plugin-creator/`?

---

## Tasks

---

### T1 — Ecosystem Registry Module

```yaml
task: T1
title: "Create ecosystem_registry.py — stdlib-only frontmatter field registry"
status: not-started
agent: python-cli-architect
dependencies: []
priority: 1
complexity: low
accuracy-risk: medium
skills: ["python3-development"]
parallelize-with: [T3, T4]
reason: "New file with no shared output. T3 and T4 write to different files entirely."
handoff: "Report: file path created, output of `get_ecosystem_owned_keys()` and `get_ecosystem_for_key('mcp')` when called, prek lint exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `ecosystem_registry.py`.

The `plugin-creator` plugin validator (`plugins/plugin-creator/scripts/plugin_validator.py`) currently rewrites any frontmatter line matching `key: value-with-colon` (FM009 fix). This breaks `mcp:` blocks from the OpenCode ecosystem by rewriting sub-keys like `command: npx -y server`. The fix requires a registry that lists which top-level frontmatter keys belong to non-Claude-Code ecosystems, so the validator can skip them.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, sections "Component 1 — Ecosystem Registry" and "Decision Log D5".

#### Objective

Create `plugins/plugin-creator/scripts/ecosystem_registry.py` as a stdlib-only Python module that declares OpenCode's frontmatter key ownership and exposes two public functions matching the architecture spec's interface contract exactly.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — Component 1 section (interface contract, data schema, OpenCode mcp: field specification)
- `plugins/plugin-creator/scripts/frontmatter_core.py` — read to confirm `sys.path` import pattern used by sibling modules (do not modify)
- `plugins/plugin-creator/scripts/normalize_frontmatter.py` — read lines 1–60 to confirm the `sys.path.insert` pattern for local module imports (do not modify)

#### Requirements

1. Create `plugins/plugin-creator/scripts/ecosystem_registry.py` as a standalone stdlib-only Python module (no third-party imports).
2. Implement `EcosystemSpec` as a `dataclass` (or `TypedDict`) with fields: `display_name: str`, `source_url: str`, `verified_date: str`, `skill_frontmatter_keys: frozenset[str]`, `agent_frontmatter_keys: frozenset[str]`, `notes: str`.
3. Define module-level `_REGISTRY: dict[str, EcosystemSpec]` containing exactly one entry: key `"opencode"` with `skill_frontmatter_keys=frozenset({"mcp"})`, `agent_frontmatter_keys=frozenset()`, `source_url="https://github.com/sst/opencode"`, `verified_date="2026-03-06"`.
4. Implement `get_ecosystem_owned_keys() -> frozenset[str]` that returns the union of all `skill_frontmatter_keys` across all registry entries.
5. Implement `get_ecosystem_for_key(key: str) -> str | None` that returns the ecosystem name (dict key) if `key` is in that ecosystem's `skill_frontmatter_keys` or `agent_frontmatter_keys`, else `None`.
6. Add a module-level docstring citing the source URL and verified date for the OpenCode `mcp:` field specification.
7. AmpCode note: include a comment in `notes` that AmpCode's compatibility with inline `mcp:` frontmatter is unverified; do not assert AmpCode = OpenCode.

#### Constraints

- No third-party imports. stdlib only (`dataclasses`, `typing`, etc.).
- Do not modify any existing file in `plugins/plugin-creator/scripts/`.
- Do not add a `__main__` block or CLI interface.
- `_REGISTRY` is a private module-level constant; do not expose it directly.
- Function signatures must match the architecture spec exactly — no extra parameters, no renamed functions.

#### Expected Outputs

- `plugins/plugin-creator/scripts/ecosystem_registry.py` (new file)

#### Acceptance Criteria

1. `from ecosystem_registry import get_ecosystem_owned_keys, get_ecosystem_for_key` succeeds after `sys.path.insert(0, "plugins/plugin-creator/scripts")`.
2. `get_ecosystem_owned_keys()` returns a `frozenset` containing exactly `"mcp"` for the current registry.
3. `get_ecosystem_for_key("mcp")` returns `"opencode"`.
4. `get_ecosystem_for_key("description")` returns `None`.
5. `get_ecosystem_for_key("unknown-field-xyz")` returns `None`.
6. `get_ecosystem_owned_keys()` returns a `frozenset` (immutable — calling code cannot accidentally mutate it).
7. `uv run prek run --files plugins/plugin-creator/scripts/ecosystem_registry.py` exits 0.

#### Verification Steps

1. Run: `python -c "import sys; sys.path.insert(0, 'plugins/plugin-creator/scripts'); from ecosystem_registry import get_ecosystem_owned_keys, get_ecosystem_for_key; print(get_ecosystem_owned_keys()); print(get_ecosystem_for_key('mcp')); print(get_ecosystem_for_key('description'))"` from repo root. Expected output: `frozenset({'mcp'})`, `opencode`, `None`.
2. Run: `python -c "import sys; sys.path.insert(0, 'plugins/plugin-creator/scripts'); from ecosystem_registry import get_ecosystem_owned_keys; k = get_ecosystem_owned_keys(); k.add('test')"` — expect `AttributeError: 'frozenset' object has no attribute 'add'` (confirms immutability).
3. Run: `uv run prek run --files plugins/plugin-creator/scripts/ecosystem_registry.py` from repo root. Expect exit 0.

#### CoVe Checks

Key claims to verify:
- The `sys.path.insert` pattern used by sibling modules is the correct way to make `ecosystem_registry.py` importable from `plugin_validator.py`.
- `frozenset` is the correct return type (not `set`) to satisfy the "immutable" requirement.

Verification questions:
1. Does `normalize_frontmatter.py` use `sys.path.insert(0, ...)` to import `frontmatter_utils`? Read lines 1–20 of `plugins/plugin-creator/scripts/normalize_frontmatter.py` to confirm.
2. Does `plugin_validator.py` already use `sys.path.insert` for local imports? Grep for `sys.path` in `plugins/plugin-creator/scripts/plugin_validator.py`.

Evidence to collect:
- Exact `sys.path.insert` lines from both files (line numbers).

Revision rule:
If the import pattern differs from `sys.path.insert(0, script_dir)`, use the pattern actually present in the sibling modules.

---

### T2 — Validator FM009 Guard

```yaml
task: T2
title: "Add ecosystem-aware state machine to _fix_unquoted_colons() in plugin_validator.py"
status: not-started
agent: python-cli-architect
dependencies: [T1]
priority: 2
complexity: medium
accuracy-risk: high
skills: ["python3-development"]
parallelize-with: []
reason: "Sole writer of plugin_validator.py changes. T1 must complete first (provides the import)."
handoff: "Report: exact line range modified in plugin_validator.py, state machine logic summary, output of --fix on multi-runtime fixture (confirm mcp: block unchanged), prek exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugin_validator.py` changes.

`_fix_unquoted_colons()` is at `plugin_validator.py:140-180`. It iterates frontmatter text line-by-line using `unquoted_colon_re = re.compile(r'^(\s*([\w-]+):\s+)([^\'"\[\{|>].+:.*)$')`. This regex fires on any indented `key: value-with-colon` line — including `command: npx -y @scope/server` inside an `mcp:` block. The fix rewrites `mcp:` sub-key values with unnecessary quotes, constituting silent data mutation.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, sections "Component 2 — Validator Changes" (Changes 1, 2, 3).

Codebase state: `plugins/plugin-creator/scripts/plugin_validator.py` is 5,095 lines. The FM009 fix is at lines 140–180. `ecosystem_registry.py` will exist at `plugins/plugin-creator/scripts/ecosystem_registry.py` after T1 completes.

#### Objective

Modify `_fix_unquoted_colons()` to skip FM009 rewrites for all lines that are indented under a top-level frontmatter key registered in `ecosystem_registry.get_ecosystem_owned_keys()`, and add the module-level import of `get_ecosystem_owned_keys` from `ecosystem_registry`.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — Component 2 section (pseudocode, edge cases, change contracts)
- `plugins/plugin-creator/scripts/plugin_validator.py` lines 1–200 — read to locate exact import block and `_fix_unquoted_colons()` function body (do not read entire 5,095-line file)
- `plugins/plugin-creator/scripts/ecosystem_registry.py` — read the completed T1 output to confirm exact function name and module name

#### Requirements

1. Add `from ecosystem_registry import get_ecosystem_owned_keys` at the top of `plugin_validator.py`, adjacent to the existing `sys.path.insert` block for sibling module imports. Do not add a try/except fallback.
2. At the start of `_fix_unquoted_colons()`, call `ecosystem_keys = get_ecosystem_owned_keys()`.
3. Implement a state machine tracking `current_ecosystem_block: str | None = None` as a local variable:
   - When a zero-indentation line matches `^[\w-]+:\s*` and the key is in `ecosystem_keys`, set `current_ecosystem_block = key`.
   - When a zero-indentation line matches `^[\w-]+:\s*` and the key is NOT in `ecosystem_keys`, set `current_ecosystem_block = None`.
   - When processing any line where `current_ecosystem_block is not None`, skip the FM009 regex check and rewrite for that line.
4. Handle the `mcp: null` scalar edge case: a zero-indentation line like `mcp: null` sets `current_ecosystem_block = "mcp"` and the line itself is not rewritten; subsequent non-indented lines reset the state.
5. Ensure the `list_of_fixed_field_names` returned by the function does NOT include any field name from a skipped ecosystem block line.
6. Preserve all existing FM009 behavior for lines where `current_ecosystem_block is None`.

#### Constraints

- Do not modify any other function in `plugin_validator.py`.
- Do not add a try/except around the `ecosystem_registry` import.
- Do not change the function signature of `_fix_unquoted_colons()`.
- Do not add new error codes or modify the `ErrorCode` enum.
- No new third-party imports.

#### Expected Outputs

- `plugins/plugin-creator/scripts/plugin_validator.py` (modified — import block and `_fix_unquoted_colons()` body only)

#### Acceptance Criteria

1. `python -c "import sys; sys.path.insert(0, 'plugins/plugin-creator/scripts'); import plugin_validator"` succeeds without `ImportError`.
2. Running `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix <fixture>` on a SKILL.md containing an `mcp:` block with `command: npx -y server` does not rewrite the `command:` line.
3. Running `--fix` on a SKILL.md containing `description: Fix: something broke` (no `mcp:`) still rewrites the description value and reports FM009.
4. Running `--fix` on a SKILL.md containing both `description: Fix: something` and a `mcp:` block fixes only `description:` and leaves `mcp:` sub-keys unchanged.
5. Running `--fix` on a SKILL.md with `mcp: null` (scalar) does not error and does not rewrite the `mcp:` line.
6. Running `--fix` on any existing SKILL.md that previously produced FM009 output continues to produce identical FM009 output (no regression).
7. `uv run prek run --files plugins/plugin-creator/scripts/plugin_validator.py` exits 0.

#### Verification Steps

1. Create a temporary file `/tmp/test_multiruntime.md` with content:
   ```
   ---
   name: test-skill
   description: "Test skill"
   mcp:
     my-server:
       command: npx -y @scope/server
       args:
         - /tmp/workspace
     remote:
       url: https://api.example.com/mcp
   ---
   Body content.
   ```
   Run: `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix /tmp/test_multiruntime.md`
   Check: `grep "command:" /tmp/test_multiruntime.md` outputs `    command: npx -y @scope/server` (no added quotes).
   Check: `grep "url:" /tmp/test_multiruntime.md` outputs `    url: https://api.example.com/mcp` (no added quotes).

2. Create `/tmp/test_claude_only.md`:
   ```
   ---
   description: Fix: something broke
   user-invocable: true
   ---
   Body.
   ```
   Run: `uv run plugins/plugin-creator/scripts/plugin_validator.py --fix /tmp/test_claude_only.md`
   Check: `grep "description:" /tmp/test_claude_only.md` shows the value is now quoted. FM009 appears in validator output.

3. Run: `uv run prek run --files plugins/plugin-creator/scripts/plugin_validator.py`. Expect exit 0.

#### CoVe Checks

Key claims to verify:
- `_fix_unquoted_colons()` currently returns `tuple[str, list[str]]` — the state machine must not break this return type.
- The import location (after `sys.path.insert`) is correct and will resolve `ecosystem_registry` from `plugins/plugin-creator/scripts/`.
- A zero-indentation line detection pattern distinguishes top-level keys from continuation lines reliably.

Verification questions:
1. What is the exact current return type and return statement of `_fix_unquoted_colons()`? Read `plugin_validator.py` lines 140–180.
2. Where exactly does the existing `sys.path.insert` for sibling modules occur in `plugin_validator.py`? (Line number.)
3. Does the existing regex `^(\s*([\w-]+):\s+)([^'"\[\{|>].+:.*)$` match a zero-indentation line? (Confirm by checking whether `\s*` can match empty string — it can, so the pattern fires on top-level keys too. The state machine must therefore check indentation separately, not rely on the regex.)

Evidence to collect:
- Exact text of `_fix_unquoted_colons()` lines 140–180.
- Exact `sys.path.insert` block location.

Revision rule:
If the return type or existing logic differs from what the architecture spec assumes, implement the state machine to match the actual code structure, not the pseudocode.

---

### T3 — agent-plugin-ecosystem OpenCode Section

```yaml
task: T3
title: "Add OpenCode SKILL.md Extensions section to agent-plugin-ecosystem/SKILL.md"
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 1
complexity: medium
accuracy-risk: medium
skills: ["development-harness:clear-cove-task-design"]
parallelize-with: [T1, T4]
reason: "Sole writer of agent-plugin-ecosystem/SKILL.md. T1 and T4 write to different files."
handoff: "Report: section heading added, line range inserted, prek exit code, citation text used."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md`.

`agent-plugin-ecosystem/SKILL.md` currently mentions OpenCode only in passing as an agentskills.io adopter (line 36). It has no `mcp:` field documentation and no multi-runtime section. Agents that load this skill (`skill-creator`, `agent-creator`, `subagent-refactorer`, `plugin-assessor`) currently have no guidance on OpenCode fields.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "3a. agent-plugin-ecosystem skill — OpenCode section".

#### Objective

Add a new "OpenCode SKILL.md Extensions" section and update the "Writing for the Correct Target" flowchart and the URL watchlist to cover OpenCode, so agents loading this skill know to treat `mcp:` as valid OpenCode frontmatter.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — section 3a (required additions, flowchart additions, self-update protocol)
- `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — read in full to locate: existing "Cross-Vendor Standardization Status" section, "Writing for the Correct Target" flowchart, and URL watchlist

#### Requirements

1. Add a new `## OpenCode SKILL.md Extensions` section positioned between "Cross-Vendor Standardization Status" and "Writing for the Correct Target" flowchart.
2. The new section must contain:
   a. The `mcp:` key described as an OpenCode-specific top-level SKILL.md frontmatter key (not in the portable field list).
   b. Both sub-formats (stdio: `command`/`args`/`env`; http: `url`/`headers`) with minimal valid YAML examples matching the architecture spec's verified schema.
   c. AmpCode note: AmpCode uses `mcp.json` sidecar; inline `mcp:` compatibility unverified — do not assert AmpCode = OpenCode.
   d. Preservation rule: "When editing a SKILL.md that contains an `mcp:` block, treat it as owned by the OpenCode runtime and preserve it verbatim. Do not remove, reformat, or flag it."
   e. Source citation: `SOURCE: https://github.com/sst/opencode (accessed 2026-03-06)` inline in the section.
3. Update the "Writing for the Correct Target" Mermaid flowchart to add two new branches:
   - `Q1 -->|OpenCode only| OC[Use mcp: frontmatter key or mcp.json sidecar<br>stdio: command/args/env<br>http: url/headers]`
   - `Q1 -->|Multiple ecosystems| Multi[Use agentskills.io portable fields + ecosystem-specific extensions<br>mcp: for OpenCode — preserved by plugin_validator.py]`
4. Add `https://github.com/sst/opencode` to the monitored URLs list in the self-update protocol section (if such a list exists).
5. Do NOT add `mcp:` to the portable fields list. It is OpenCode-specific only.

#### Constraints

- Do not remove any existing content.
- Do not alter the portable field list (only add OpenCode to a dedicated section).
- All code fences must have language specifiers (`yaml`, `mermaid`, etc.).
- No colons in YAML frontmatter `description` field of this skill file.
- Mermaid node labels: use `<br>` not `\n` for line breaks; use `=` not `:` for assignments inside node labels.

#### Expected Outputs

- `plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` (modified)

#### Acceptance Criteria

1. `## OpenCode SKILL.md Extensions` section exists in the file between "Cross-Vendor Standardization Status" and "Writing for the Correct Target" sections.
2. The section contains both stdio and http `mcp:` format YAML examples.
3. The section contains the preservation rule for `mcp:` blocks.
4. The section contains `SOURCE: https://github.com/sst/opencode (accessed 2026-03-06)`.
5. The AmpCode note states compatibility is unverified and does not assert it matches OpenCode.
6. The Mermaid flowchart contains branches for "OpenCode only" and "Multiple ecosystems".
7. `uv run prek run --files plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` exits 0.

#### Verification Steps

1. Run: `grep -n "OpenCode SKILL.md Extensions" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — must return exactly one match.
2. Run: `grep -n "mcp:" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — must return at least 3 lines (section heading reference + stdio example + http example).
3. Run: `grep -n "sst/opencode" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — must return at least 1 line (citation).
4. Run: `uv run prek run --files plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — expect exit 0.

#### CoVe Checks

Key claims to verify:
- The section heading "Cross-Vendor Standardization Status" actually exists in the current file (to confirm insertion point).
- The "Writing for the Correct Target" Mermaid flowchart exists and uses the `Q1` node label referenced in the architecture spec.

Verification questions:
1. Run `grep -n "Cross-Vendor Standardization" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — does it exist?
2. Run `grep -n "Writing for the Correct Target" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — does it exist?
3. Run `grep -n "Q1" plugins/plugin-creator/skills/agent-plugin-ecosystem/SKILL.md` — is `Q1` the actual node name in the Mermaid flowchart?

Evidence to collect:
- Line numbers for the existing section headings and Q1 node.

Revision rule:
If the actual section headings or flowchart node names differ from the architecture spec, insert the new content at the correct adjacent location and use the actual Q1 node name.

---

### T4 — frontmatter-requirements.md Preservation Rule

```yaml
task: T4
title: "Add Non-Claude Ecosystem Fields section to frontmatter-requirements.md"
status: not-started
agent: service-docs-maintainer
dependencies: []
priority: 1
complexity: low
accuracy-risk: low
skills: []
parallelize-with: [T1, T3]
reason: "Sole writer of frontmatter-requirements.md. T1 and T3 write to different files."
handoff: "Report: section added (line range), prek exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md`.

`frontmatter-requirements.md` is a scoped rule file (`paths:` covers `**/SKILL.md`, `**/agents/**/*.md`, `**/commands/**/*.md`). It is injected into every agent session that touches these file types. Currently it documents only Claude Code schema rules. Adding the preservation rule here means ALL agents operating on skill/agent/command files receive it automatically — without requiring changes to each agent's individual prompt.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "3c. frontmatter-requirements.md scoped rule".

#### Objective

Append a "Non-Claude Ecosystem Fields" section to `frontmatter-requirements.md` documenting that `mcp:` is a valid OpenCode field and must be preserved verbatim by any agent editing a SKILL.md.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — section 3c (exact content to add)
- `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` — read in full to locate end of file and confirm current content

#### Requirements

1. Append a new `## Non-Claude Ecosystem Fields` section at the end of `frontmatter-requirements.md`.
2. The section must state:
   - SKILL.md frontmatter may contain fields owned by other ecosystems (e.g., `mcp:` for OpenCode). These fields are valid.
   - `mcp:` — OpenCode MCP server configuration. Contains stdio (`command`/`args`/`env`) or http (`url`/`headers`) sub-structures. Treat as opaque.
   - When editing a SKILL.md that contains `mcp:`, preserve the block verbatim. The plugin validator will not flag `mcp:` as an error.
3. Do not add a colon in any YAML frontmatter `description` field of this file (if it has frontmatter).

#### Constraints

- Append only — do not remove or alter existing content.
- All code fences must have language specifiers.
- Surround all code fences with blank lines (MD031).

#### Expected Outputs

- `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` (modified)

#### Acceptance Criteria

1. `## Non-Claude Ecosystem Fields` heading exists at the end of the file.
2. The section contains the word `opaque` (confirming agents are told not to parse `mcp:` contents).
3. The section states `plugin validator will not flag mcp: as an error` (or equivalent phrasing).
4. `uv run prek run --files plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` exits 0.

#### Verification Steps

1. Run: `grep -n "Non-Claude Ecosystem Fields" plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` — must return exactly one match.
2. Run: `grep -n "opaque" plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` — must return at least one line.
3. Run: `uv run prek run --files plugins/plugin-creator/.claude/rules/frontmatter-requirements.md` — expect exit 0.

---

### T5 — skill-creator SKILL.md Multi-Runtime and Callout

```yaml
task: T5
title: "Add preservation callout and Step 5b multi-runtime scaffold to skill-creator/SKILL.md"
status: not-started
agent: service-docs-maintainer
dependencies: [T3]
priority: 2
complexity: medium
accuracy-risk: low
skills: []
parallelize-with: [T6, T7, T8]
reason: >
  Merged from two planned changes to the same file to avoid edit conflicts:
  (1) preservation callout before the 10-step workflow, and
  (2) Step 5b multi-runtime scaffold section.
  T3 must complete first so the link to agent-plugin-ecosystem is stable.
handoff: "Report: location of callout (before which step heading), location of Step 5b (after Step 5 heading), prek exit code."
```

#### Context

This task was merged from two planned changes that both target `plugins/plugin-creator/skills/skill-creator/SKILL.md`, to prevent edit conflicts:

- **Preservation callout**: an early "Before You Begin" or "Non-Destructive Editing" notice warning agents not to remove unrecognized frontmatter keys from existing SKILL.md files.
- **Step 5b multi-runtime scaffold**: a new subsection at the end of Step 5 (frontmatter fields) showing the combined Claude Code + OpenCode `mcp:` frontmatter template.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, sections "3b. skill-creator skill" and "4a. skill-creator skill — preservation instruction".

#### Objective

Add both the preservation callout (before the numbered workflow) and the Step 5b multi-runtime scaffold section to `skill-creator/SKILL.md` in a single edit pass, so the file is updated atomically.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — sections 3b and 4a (exact content requirements for both additions)
- `plugins/plugin-creator/skills/skill-creator/SKILL.md` — read in full to locate Step 1 heading, Step 5 heading, and end of Step 5 content

#### Requirements

### Preservation callout (before numbered workflow)

1. Insert a callout block before the heading of Step 1 (or before any `## Step 1` heading), titled **"Non-Destructive Editing"** or equivalent.
2. Callout content: when editing an existing SKILL.md that contains `mcp:` or other unrecognized top-level frontmatter keys, treat those keys as owned by another runtime ecosystem. Do not remove, move, or question them. Preserve verbatim.
3. Reference: if the author wants multi-runtime targeting for a new skill, see Step 5b below.

### Step 5b multi-runtime scaffold (end of Step 5)

4. Insert a new subsection `### Step 5b — Multi-Runtime Skills (Claude Code + OpenCode)` immediately after the existing Step 5 content (before Step 6 heading).
5. The subsection must contain:
   a. **When to use**: single SKILL.md targeting both Claude Code and OpenCode; Claude Code reads its fields, OpenCode reads `mcp:`.
   b. **Scaffold template** as a `yaml` code fence:
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
   c. **Validator behavior**: `plugin_validator.py --fix` will not modify the `mcp:` block.
   d. **Portability link**: "For the full cross-vendor portability picture, use the `/agent-plugin-ecosystem` skill."

#### Constraints

- Do not remove or alter existing Step 5 content.
- Do not alter any other step content.
- All code fences must have language specifiers.
- Surround all code fences with blank lines (MD031).
- No colons in the YAML frontmatter `description` field of this skill file (the file's own frontmatter, not the scaffold example).

#### Expected Outputs

- `plugins/plugin-creator/skills/skill-creator/SKILL.md` (modified)

#### Acceptance Criteria

1. A preservation callout section exists before the first numbered step heading.
2. The callout instructs agents to treat unrecognized top-level keys as ecosystem-owned and preserve them.
3. `### Step 5b` heading exists in the file, positioned after Step 5 content and before Step 6 content.
4. Step 5b contains a `yaml` code fence with both `user-invocable: true` and `mcp:` frontmatter fields.
5. Step 5b mentions `plugin_validator.py --fix` and states the `mcp:` block will not be modified.
6. Step 5b contains a reference to `/agent-plugin-ecosystem` skill.
7. `uv run prek run --files plugins/plugin-creator/skills/skill-creator/SKILL.md` exits 0.

#### Verification Steps

1. Run: `grep -n "Non-Destructive\|Before You Begin" plugins/plugin-creator/skills/skill-creator/SKILL.md` — must return at least one line positioned before `## Step 1` (or equivalent first step heading).
2. Run: `grep -n "Step 5b" plugins/plugin-creator/skills/skill-creator/SKILL.md` — must return at least one line.
3. Run: `grep -n "mcp:" plugins/plugin-creator/skills/skill-creator/SKILL.md` — must return at least 2 lines (scaffold + prose reference).
4. Run: `uv run prek run --files plugins/plugin-creator/skills/skill-creator/SKILL.md` — expect exit 0.

---

### T6 — subagent-refactorer Exclusion List

```yaml
task: T6
title: "Add mcp: exclusion list to subagent-refactorer.md"
status: not-started
agent: service-docs-maintainer
dependencies: [T4]
priority: 2
complexity: low
accuracy-risk: low
skills: []
parallelize-with: [T5, T7, T8]
reason: "Sole writer of subagent-refactorer.md. T4 must complete first so the scoped rule exists before the agent prompt reinforces it."
handoff: "Report: location of insertion (section name), exact text added (first sentence), prek exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugins/plugin-creator/agents/subagent-refactorer.md`.

`subagent-refactorer` rewrites agent prompt files, focusing on the `description` field. It currently has no guidance on non-Claude fields. If it encounters a SKILL.md with `mcp:` frontmatter and is asked to "optimize" it, it may flag or remove `mcp:` as unrecognized.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "4b. subagent-refactorer agent".

#### Objective

Add an explicit exclusion list to `subagent-refactorer.md` stating which top-level frontmatter keys are outside its refactoring scope, specifically `mcp:` and any other unrecognized top-level key.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — section 4b (content to add, location)
- `plugins/plugin-creator/agents/subagent-refactorer.md` — read in full to locate the section covering which frontmatter fields the agent is allowed to modify

#### Requirements

1. In the section of `subagent-refactorer.md` that describes the agent's modification scope (e.g., "what this agent modifies" or the instruction block covering frontmatter fields), add an explicit exclusion block.
2. Exclusion block content:
   - Fields this agent must NOT modify, remove, or flag: `mcp:` and its entire sub-structure (OpenCode ecosystem-owned field); any other top-level key not listed in the Claude Code agent frontmatter schema.
   - Rule: when encountering an unrecognized top-level frontmatter key, treat it as an ecosystem field; exclude it from refactoring scope.
   - Scope: limited to `description`, `name`, and body content below the frontmatter block.
3. Do not alter the agent's frontmatter `description` field (it must remain single-line, no colons).

#### Constraints

- Add content only — do not remove or reorder existing instructions.
- No colons in any YAML frontmatter `description` field.
- All code fences must have language specifiers.

#### Expected Outputs

- `plugins/plugin-creator/agents/subagent-refactorer.md` (modified)

#### Acceptance Criteria

1. The file contains explicit text stating `mcp:` is out of scope for the refactoring operation.
2. The text states the agent's scope is limited to `description`, `name`, and body content.
3. The text instructs the agent to treat unrecognized top-level keys as ecosystem fields.
4. `uv run prek run --files plugins/plugin-creator/agents/subagent-refactorer.md` exits 0.

#### Verification Steps

1. Run: `grep -n "mcp:" plugins/plugin-creator/agents/subagent-refactorer.md` — must return at least one line.
2. Run: `grep -n "ecosystem" plugins/plugin-creator/agents/subagent-refactorer.md` — must return at least one line.
3. Run: `uv run prek run --files plugins/plugin-creator/agents/subagent-refactorer.md` — expect exit 0.

---

### T7 — contextual-optimizer Pass-Through Rule

```yaml
task: T7
title: "Add mcp: pass-through rule to contextual-ai-documentation-optimizer.md"
status: not-started
agent: service-docs-maintainer
dependencies: [T4]
priority: 2
complexity: low
accuracy-risk: low
skills: []
parallelize-with: [T5, T6, T8]
reason: "Sole writer of contextual-ai-documentation-optimizer.md. T4 must complete first."
handoff: "Report: location of insertion (section name), prek exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md`.

`contextual-ai-documentation-optimizer` rewrites SKILL.md and CLAUDE.md body content. It touches the `description` field indirectly. If given a multi-runtime SKILL.md with `mcp:` frontmatter, it may reformat or remove `mcp:` while optimizing the surrounding content.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "4c. contextual-ai-documentation-optimizer agent".

#### Objective

Add a pass-through rule to the agent's optimization scope definition: `mcp:` and its sub-structure must reach the output file unchanged; only `description` and `name` fields are in scope for frontmatter optimization.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — section 4c (content to add, location)
- `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` — read in full to locate the section describing the agent's optimization scope or allowed frontmatter mutations

#### Requirements

1. In the section of the agent file that defines optimization scope, add a pass-through rule block.
2. Pass-through rule content:
   - Scope of frontmatter optimization: `description` field rewrites and `name` field corrections only.
   - Out of scope: any top-level frontmatter key not in the Claude Code SKILL.md schema. Specifically: `mcp:` and its sub-structure must pass through to the output file unchanged.
   - Rule: do not reformat, reorder, or comment on these fields. They belong to other runtime ecosystems.

#### Constraints

- Add content only — do not remove or reorder existing instructions.
- No colons in the YAML frontmatter `description` field.

#### Expected Outputs

- `plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` (modified)

#### Acceptance Criteria

1. The file contains text stating `mcp:` is out of scope for frontmatter optimization.
2. The text states only `description` and `name` are in scope for frontmatter changes.
3. `uv run prek run --files plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` exits 0.

#### Verification Steps

1. Run: `grep -n "mcp:" plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` — must return at least one line.
2. Run: `grep -n "pass.through\|pass through\|ecosystem" plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` — must return at least one line.
3. Run: `uv run prek run --files plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md` — expect exit 0.

---

### T8 — plugin-assessor Ecosystem Assessment Rule

```yaml
task: T8
title: "Add ecosystem field assessment rule to plugin-assessor.md"
status: not-started
agent: service-docs-maintainer
dependencies: [T3, T4]
priority: 2
complexity: low
accuracy-risk: low
skills: []
parallelize-with: [T5, T6, T7]
reason: "Sole writer of plugin-assessor.md. Depends on T3 (OpenCode section in agent-plugin-ecosystem) so the assessor can reference it, and T4 (scoped rule) as the baseline."
handoff: "Report: location of insertion (section name), prek exit code."
```

#### Context

This task was not merged from multiple candidates — it is the sole writer of `plugins/plugin-creator/agents/plugin-assessor.md`.

`plugin-assessor` audits plugins for structure and frontmatter schema compliance (read-only). It currently has no guidance on ecosystem fields. If it encounters `mcp:` it may report it as an unknown field or schema violation.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "4d. plugin-assessor agent".

#### Objective

Add an assessment rule to `plugin-assessor.md` stating that recognized ecosystem fields (specifically `mcp:` for OpenCode) are valid and must be reported as ecosystem-owned, not as schema violations.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — section 4d (content to add, expected assessment output phrasing)
- `plugins/plugin-creator/agents/plugin-assessor.md` — read in full to locate the section covering frontmatter assessment criteria

#### Requirements

1. In the section of `plugin-assessor.md` covering frontmatter assessment, add an ecosystem field assessment rule.
2. Rule content:
   - When assessing a SKILL.md that contains `mcp:` or other unrecognized top-level frontmatter keys: report the key as present with a note that it belongs to another ecosystem.
   - Do NOT report it as a schema violation, unknown field error, or recommendation for removal.
   - If the key matches a known ecosystem field, name the ecosystem (e.g., "OpenCode").
   - The expected assessment output for a multi-runtime SKILL.md: "Frontmatter contains `mcp:` (OpenCode ecosystem field) — valid for multi-runtime targeting."
3. Add a reference to the `agent-plugin-ecosystem` skill as the source of ecosystem field documentation.

#### Constraints

- Add content only — do not remove or alter existing assessment criteria.
- No colons in the YAML frontmatter `description` field.

#### Expected Outputs

- `plugins/plugin-creator/agents/plugin-assessor.md` (modified)

#### Acceptance Criteria

1. The file instructs the assessor NOT to flag `mcp:` as a schema violation.
2. The file instructs the assessor to name the owning ecosystem when the field is recognized.
3. The file references `agent-plugin-ecosystem` skill (or its activation syntax `/agent-plugin-ecosystem`).
4. `uv run prek run --files plugins/plugin-creator/agents/plugin-assessor.md` exits 0.

#### Verification Steps

1. Run: `grep -n "mcp:" plugins/plugin-creator/agents/plugin-assessor.md` — must return at least one line.
2. Run: `grep -n "OpenCode\|ecosystem" plugins/plugin-creator/agents/plugin-assessor.md` — must return at least two lines.
3. Run: `grep -n "agent-plugin-ecosystem" plugins/plugin-creator/agents/plugin-assessor.md` — must return at least one line.
4. Run: `uv run prek run --files plugins/plugin-creator/agents/plugin-assessor.md` — expect exit 0.

---

### T9 — Tests for ecosystem_registry and FM009 Guard

```yaml
task: T9
title: "Write pytest tests for ecosystem_registry.py and the FM009 state machine guard"
status: not-started
agent: python-pytest-architect
dependencies: [T1, T2]
priority: 3
complexity: medium
accuracy-risk: medium
skills: ["fastmcp-python-tests", "python3-development"]
parallelize-with: []
reason: "Requires T1 (ecosystem_registry.py) and T2 (modified plugin_validator.py) to exist before tests can be written against them."
handoff: "Report: test files created or modified, total test count, pytest exit code, names of any skipped tests with reason."
```

#### Context

This task was not merged from multiple candidates. It writes to new or extended test files only, not to any production file.

The architecture spec defines 5 unit tests for `ecosystem_registry.py` and 7 parametrized test cases for the FM009 guard, plus 1 integration fixture test and 1 regression test. An existing test file for frontmatter fixes may exist at `plugins/plugin-creator/tests/test_frontmatter_fixes.py` — check before creating a new file.

Architecture spec: `plan/architect-multi-ecosystem-plugin-creator.md`, section "Testing Strategy".

#### Objective

Create `plugins/plugin-creator/tests/test_ecosystem_registry.py` and create or extend the FM009 test file with all test cases specified in the architecture spec, such that `uv run pytest plugins/plugin-creator/tests/ -v` exits 0.

#### Required Inputs

- `plan/architect-multi-ecosystem-plugin-creator.md` — "Testing Strategy" section (all test cases, fixture YAML)
- `plugins/plugin-creator/scripts/ecosystem_registry.py` — completed T1 output (import and call to verify)
- `plugins/plugin-creator/scripts/plugin_validator.py` lines 140–200 — read to understand `_fix_unquoted_colons()` signature and return type for white-box tests
- `plugins/plugin-creator/tests/` — glob to check whether this directory and any existing test files exist

#### Requirements

### ecosystem_registry tests (`test_ecosystem_registry.py`)

1. `test_get_ecosystem_owned_keys_contains_mcp` — asserts `"mcp" in get_ecosystem_owned_keys()`.
2. `test_get_ecosystem_owned_keys_is_frozenset` — asserts `isinstance(get_ecosystem_owned_keys(), frozenset)`.
3. `test_get_ecosystem_for_key_mcp_returns_opencode` — asserts `get_ecosystem_for_key("mcp") == "opencode"`.
4. `test_get_ecosystem_for_key_description_returns_none` — asserts `get_ecosystem_for_key("description") is None`.
5. `test_get_ecosystem_for_key_unknown_returns_none` — asserts `get_ecosystem_for_key("unknown-field-xyz") is None`.

### FM009 guard tests (extend or create `test_frontmatter_fixes.py`)

6. Parametrized test `test_fm009_guard` covering 7 cases from the architecture spec:
   - Case 1: `mcp:` with stdio `command: npx -y server` — `command:` line not rewritten; FM009 not in output.
   - Case 2: `mcp:` with http `url: https://example.com/mcp` — `url:` line not rewritten; FM009 not in output.
   - Case 3: `description: Fix: something broke` (no `mcp:`) — description value quoted; FM009 reported.
   - Case 4: Both `description: Fix: something` and `mcp:` — only `description:` fixed; `mcp:` block untouched.
   - Case 5: `mcp: null` (scalar) — line not rewritten; no error.
   - Case 6: Only Claude Code fields, no ecosystem fields — behavior identical to pre-change (FM009 fires on colon-containing description values).
   - Case 7: `mcp:` block with 4+ indented lines — all indented lines skipped; state exits on next top-level key.

### Integration fixture test

7. Create `plugins/plugin-creator/tests/fixtures/multi_runtime_skill.md` with the full YAML fixture from the architecture spec testing section.
8. Integration test: run `plugin_validator.py --fix` on the fixture (via `subprocess.run`) and assert: exit code 0, `mcp:` block in output file is byte-identical to input, no FM009 in stdout.

### Regression test

9. Run `plugin_validator.py --fix` on an existing SKILL.md that is expected to trigger FM009 on its `description:` field (use a synthetic fixture — do not modify a real production file). Assert the fix still applies correctly.

#### Constraints

- Do not modify any production source file (`plugin_validator.py`, `ecosystem_registry.py`, etc.).
- If `plugins/plugin-creator/tests/` does not exist, create it with `__init__.py`.
- If `test_frontmatter_fixes.py` already exists, extend it — do not create a duplicate file.
- Tests must use `pytest` (not `unittest`).
- All imports must resolve via `sys.path.insert` for the `scripts/` directory (same pattern as production code).
- No network calls in tests.

#### Expected Outputs

- `plugins/plugin-creator/tests/__init__.py` (create if absent)
- `plugins/plugin-creator/tests/test_ecosystem_registry.py` (new)
- `plugins/plugin-creator/tests/test_frontmatter_fixes.py` (new or extended)
- `plugins/plugin-creator/tests/fixtures/multi_runtime_skill.md` (new)
- `plugins/plugin-creator/tests/fixtures/claude_only_skill.md` (new — regression fixture)

#### Acceptance Criteria

1. `uv run pytest plugins/plugin-creator/tests/test_ecosystem_registry.py -v` exits 0 with 5 tests collected and passed.
2. All 7 parametrized FM009 guard test cases pass.
3. Integration fixture test passes: byte-identical `mcp:` block after `--fix`.
4. Regression test passes: existing FM009 behavior unchanged for Claude Code-only SKILL.md.
5. `uv run pytest plugins/plugin-creator/tests/ -v` exits 0 with no failures or errors.

#### Verification Steps

1. Run: `uv run pytest plugins/plugin-creator/tests/test_ecosystem_registry.py -v` — expect 5 passed, 0 failed.
2. Run: `uv run pytest plugins/plugin-creator/tests/test_frontmatter_fixes.py -v` — expect all FM009 cases passed.
3. Run: `uv run pytest plugins/plugin-creator/tests/ -v` — expect 0 failures.
4. Run: `uv run prek run --files plugins/plugin-creator/tests/test_ecosystem_registry.py plugins/plugin-creator/tests/test_frontmatter_fixes.py` — expect exit 0.

#### CoVe Checks

Key claims to verify:
- `_fix_unquoted_colons()` is a module-level function (not a method on a class) — calling it directly in tests requires correct import.
- The integration test must invoke `plugin_validator.py` as a subprocess (PEP 723 script, not importable as a plain module without the PEP 723 runner).

Verification questions:
1. Is `_fix_unquoted_colons()` a standalone function or a method on `FrontmatterValidator`? Check `plugin_validator.py` lines 130–145.
2. Does `plugin_validator.py` use PEP 723 inline metadata at the top (lines 1–15)? If yes, tests that invoke fix behavior must use `subprocess.run(["uv", "run", "...plugin_validator.py", "--fix", ...])` rather than direct import.

Evidence to collect:
- Location of `_fix_unquoted_colons()` definition (standalone vs method).
- Lines 1–15 of `plugin_validator.py` to confirm PEP 723 header.

Revision rule:
If `_fix_unquoted_colons()` is a method, use the class in unit tests. If PEP 723 is confirmed, use subprocess for all integration tests that invoke the script as a whole.

---

## Context Manifest

### Discovered During Implementation

_Session Date: 2026-03-06_

During implementation, several concrete facts emerged that the original architecture spec anticipated
at an abstracted level but did not fully resolve. These are recorded here to save future implementors
from re-discovering them.

**Key Discoveries:**

1. **Pydantic layer confirmed safe — only FM009 regex was the real risk**: The feature context
   flagged `normalize_frontmatter.py` as a potential risk vector (Gap 1) with the qualifier "needs
   verification." Implementation confirmed that `ruamel.yaml` round-trip mode preserves all keys
   including nested dicts verbatim — the architect spec correctly called this out, but implementation
   confirmed it empirically. The Pydantic `extra="allow"` layer was likewise confirmed safe. The
   only code path that could corrupt `mcp:` blocks was `_fix_unquoted_colons()` in
   `plugin_validator.py`. Future work on this codebase does not need to re-examine the round-trip
   layer or the Pydantic models for ecosystem field safety.

2. **`ruamel.yaml` round-trip preserves nested dicts without serialization changes**: Confirmed
   that `RuamelYAMLHandler` with `YAML(typ="rt")` retains all keys — including multi-level nested
   dicts like an `mcp:` block with `stdio` or `http` sub-configs — without any code changes to
   `frontmatter_utils.py` or `normalize_frontmatter.py`. No serialization changes are needed even
   if additional ecosystem keys with complex sub-structures are added to the registry in future.

3. **FM009 function is line-by-line — state machine approach is correct**: `_fix_unquoted_colons()`
   iterates line by line over raw frontmatter text before YAML parsing. The state machine tracking
   `current_ecosystem_block` via indentation detection is the right pattern and maps cleanly onto
   the existing loop structure. The function is a method on `FrontmatterValidator` (not a standalone
   function), so unit tests must instantiate the class rather than calling the function directly.

4. **`ecosystem_registry.py` uses `frozenset` return types**: The registry exposes
   `get_ecosystem_owned_keys() -> frozenset[str]` and `EcosystemSpec.skill_frontmatter_keys:
   frozenset[str]`. The immutable return type prevents callers from accidentally mutating the
   registry state. Future additions to the registry must maintain `frozenset` types for all
   key collections.

5. **Subprocess test pattern required — fixture must use `SKILL.md` filename**: The integration
   regression test that runs `plugin_validator.py --fix` via `subprocess.run` must copy the fixture
   content into a file named `SKILL.md` (not an arbitrary `.md` name). The validator applies FM009
   only to files matching its file-type detection rules, which require the filename `SKILL.md`.
   Tests that used a different fixture filename would bypass the FM009 code path entirely, producing
   a false pass. All future subprocess-based validator tests should use `SKILL.md` as the target
   filename.

6. **Code review found 3 follow-up issues**: After T9 completed, the code reviewer (Phase 1 of
   `/complete-implementation`) identified three issues requiring follow-up. These were decomposed
   into three follow-up task files:
   - `plan/tasks-2-multi-ecosystem-plugin-creator-followup-1.md` — flawed integration test
     assertion (the byte-identity check used string comparison after reading the file, not a binary
     diff, which would miss encoding differences)
   - `plan/tasks-2-multi-ecosystem-plugin-creator-followup-2.md` — `mcp:` scalar state-machine
     edge case: when `mcp: null` appears on a single line with no indented sub-keys, the state
     machine must not enter the ecosystem block for the following non-indented line
   - `plan/tasks-2-multi-ecosystem-plugin-creator-followup-3.md` — `agent_frontmatter_keys`
     inconsistency: the `EcosystemSpec` dataclass defines `agent_frontmatter_keys` but
     `get_ecosystem_owned_keys()` only unions `skill_frontmatter_keys`, silently ignoring the
     agent keys field

#### Updated Technical Details

- `_fix_unquoted_colons()` is a method on `FrontmatterValidator`, not a standalone function.
  Direct unit tests must call `FrontmatterValidator(...)._fix_unquoted_colons(text)` or use
  the class's public `validate()` entrypoint for integration-style tests.
- `plugin_validator.py` uses PEP 723 inline metadata at the top. All integration tests invoking
  it must use `subprocess.run(["uv", "run", "plugins/plugin-creator/scripts/plugin_validator.py",
  "--fix", fixture_path])`.
- `EcosystemSpec` was implemented as a `dataclass` (not `TypedDict`). Both work, but
  `dataclass` was chosen for immutability enforcement via `frozen=True`.
- Fixture files for subprocess tests must be named `SKILL.md` — the validator's file-type
  detection gates FM009 on this filename.

#### Gotchas for Future Developers

- Running `plugin_validator.py --fix` on a file named anything other than `SKILL.md` silently
  skips FM009. This is by design (FM009 applies only to skill frontmatter files), but it makes
  test fixtures named `multi_runtime.md` produce false passes.
- The `mcp: null` scalar edge case is the hardest state-machine case: the state machine enters
  the ecosystem block on that line but there are no subsequent indented lines to skip. The next
  top-level line must correctly reset `current_ecosystem_block = None`. Tests must cover this
  case explicitly.
- `get_ecosystem_owned_keys()` currently only unions `skill_frontmatter_keys`. If agent-level
  ecosystem fields are ever needed (e.g., a future OpenCode agent field), `agent_frontmatter_keys`
  must also be included in the union. This is a latent inconsistency documented in followup-3.
