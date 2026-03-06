# Plugin-Creator Plugin — Current State Analysis

**Analysis Date:** 2026-03-06
**Plugin:** `plugin-creator` (`plugins/plugin-creator/`)
**Version:** 2.3.0 (from `CLAUDE.md`)

---

## Table of Contents

1. [Validation Logic — How the Validator Works](#1-validation-logic)
2. [Schema Definitions — Where Frontmatter Schemas Live](#2-schema-definitions)
3. [Skill/Agent Editing Workflows — Who Reads and Modifies Frontmatter](#3-skill-agent-editing-workflows)
4. [Multi-Ecosystem Awareness — Non-Claude Frontmatter Handling](#4-multi-ecosystem-awareness)
5. [Error Code Reference](#5-error-code-reference)
6. [Key File Map](#6-key-file-map)

---

## 1. Validation Logic

### Entry Point

**Script:** `plugins/plugin-creator/scripts/plugin_validator.py` (5,095 lines)

Run via:

```bash
uv run plugins/plugin-creator/scripts/plugin_validator.py [--fix] [--check] [--verbose] <path>
```

The script is a PEP 723 standalone script with these declared dependencies (`plugin_validator.py:1-12`):

```
typer>=0.21.0, tiktoken>=0.8.0, ruamel.yaml>=0.18.0,
python-frontmatter>=1.1.0, pydantic>=2.0.0, gitpython>=3.1.45
```

### File Type Detection

`FileType.detect_file_type(path)` at `plugin_validator.py:581-610` classifies files by path structure:

| Condition | FileType |
|---|---|
| `path.name == "SKILL.md"` | `SKILL` |
| `"agents" in path.parts` | `AGENT` |
| `"commands" in path.parts` | `COMMAND` |
| `path.name == "plugin.json"` | `PLUGIN` |
| `path.name == "hooks.json"` | `HOOK_CONFIG` |
| `path.name == "CLAUDE.md"` | `CLAUDE_MD` |
| `"references" in path.parts and .md suffix` | `REFERENCE` |
| other `.md` | `MARKDOWN` |
| anything else | `UNKNOWN` |

`UNKNOWN` is **promoted to `SKILL`** at validation time (`plugin_validator.py:1876-1877`). This means any unrecognized `.md` file with frontmatter gets validated as a skill.

### Exempt Filenames

Files in `FRONTMATTER_EXEMPT_FILENAMES` (`plugin_validator.py:380-386`) are skipped entirely:

```python
FRONTMATTER_EXEMPT_FILENAMES: frozenset[str] = frozenset({
    "AGENT.md", "AGENTS.md", "GEMINI.md", "CLAUDE.md", "README.md",
})
```

### FrontmatterValidator Class

Defined at `plugin_validator.py:1809-2003`. Core `validate()` method (`plugin_validator.py:1827-1960`):

**Step 1 — Extract frontmatter.** Calls `extract_frontmatter()` from `frontmatter_core.py:230-251`. Returns error FM003 if no `---` delimiters found.

**Step 2 — Check for forbidden multiline indicators.** Regex scan at `plugin_validator.py:1880`:

```python
re.search(r"description:\s*[|>][-+]?\s*\n", frontmatter_text)
```

Reports FM004 (ERROR, auto-fixable).

**Step 3 — Parse YAML** with `ruamel.yaml` safe loader. Reports FM002 on `YAMLError`.

**Step 4 — Select Pydantic model.** Calls `_get_model_class(file_type)` which maps to `_MODEL_REGISTRY` in `frontmatter_core.py:218-222`:

```python
_MODEL_REGISTRY = {
    "skill":   SkillFrontmatter,
    "command": CommandFrontmatter,
    "agent":   AgentFrontmatter,
}
```

If `file_type` has no registered model (e.g., `REFERENCE`, `CLAUDE_MD`), validation returns `passed=True` immediately at `plugin_validator.py:1921-1922` — **no schema check performed**.

**Step 5 — Pydantic model_validate().** All three Pydantic models are configured with `extra="allow"` (`frontmatter_core.py:83, 125, 169`), meaning **unknown frontmatter fields pass silently**. Pydantic validates only the declared known fields.

**Step 6 — Post-validation checks:**
- `_check_list_valued_tool_fields()` at `plugin_validator.py:815-846`: fires FM007 (tools array) or FM008 (skills array) for any list-valued `tools`, `disallowedTools`, `allowed-tools`, or `skills` field.
- `_check_skill_name_and_directory()` at `plugin_validator.py:849-895`: for `SKILL.md` files, validates directory name (SK008) and warns when `name` field doesn't match directory name (FM010 warning).
- `hooks:` dict validation: delegates to `HookValidator` for script reference checks.

### Auto-Fix Capabilities

`FrontmatterValidator.fix()` at `plugin_validator.py:1970-2003` applies these mutations in-place:

| Code | What Gets Fixed |
|---|---|
| FM004 | Multiline `description:` with `>-`, `|-` → single-line quoted string |
| FM007 | `tools:` YAML list → comma-separated string |
| FM008 | `skills:` YAML list → comma-separated string |
| FM009 | Unquoted colons in description → double-quoted value |

The FM009 fix is implemented in `_fix_unquoted_colons()` at `plugin_validator.py:140-180` using this regex:

```python
unquoted_colon_re = re.compile(r'^(\s*([\w-]+):\s+)([^\'"\[\{|>].+:.*)$')
```

It matches **any** `key: value: more` line (not only `description`), quotes the value, and reports the field name. This means FM009 can fire on any field that has an unquoted colon in its value — not just `description`.

**Auto-fix for skill `name:` field** (`frontmatter_core.py:274-303`): `fix_skill_name_field()` adds or corrects the `name` field to match the skill's parent directory name. Runs when `FileType.SKILL` + `--fix` flag is active.

### Ignore Config Suppression

Per-plugin suppression via `.claude-plugin/validator.json` (`plugin_validator.py:461-481`):

```json
{
  "ignore": {
    "skills/python3-development": ["SK006"]
  }
}
```

Suppressed issues are **dropped entirely** (not downgraded) before reporting.

### Token Complexity Thresholds

Defined as module-level constants at `plugin_validator.py:193-194`:

```python
TOKEN_WARNING_THRESHOLD = 4400   # → SK006 WARNING
TOKEN_ERROR_THRESHOLD   = 8800   # → SK007 ERROR
```

Token counting uses `tiktoken` with `cl100k_base` encoding, applied to SKILL.md **body only** (frontmatter excluded).

---

## 2. Schema Definitions

### Pydantic Models (Ground Truth)

**File:** `plugins/plugin-creator/scripts/frontmatter_core.py`

Three models cover the three file types:

#### `SkillFrontmatter` (`frontmatter_core.py:77-119`)

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `name` | `str \| None` | max 64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$` | Optional for skills |
| `description` | `str \| None` | — | Optional |
| `argument-hint` | `str \| None` | alias `argument_hint` | — |
| `allowed-tools` | `str \| None` | alias `allowed_tools`, comma-sep | List auto-normalized |
| `model` | `str \| None` | — | No enum constraint on skills |
| `skills` | `str \| None` | comma-sep | List auto-normalized |
| `context` | `Literal["fork"] \| None` | — | — |
| `agent` | `str \| None` | — | — |
| `user-invocable` | `bool \| None` | alias `user_invocable` | — |
| `disable-model-invocation` | `bool \| None` | alias `disable_model_invocation` | — |
| `hooks` | `dict[str, Any] \| None` | — | — |

`model_config = ConfigDict(extra="allow")` — all unknown fields pass silently.

#### `AgentFrontmatter` (`frontmatter_core.py:160-208`)

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `name` | `str` | required, max 64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$` | Required for agents |
| `description` | `str` | required | Required for agents |
| `tools` | `str \| None` | comma-sep | List auto-normalized |
| `disallowedTools` | `str \| None` | comma-sep | camelCase per official spec |
| `model` | `Literal["sonnet", "opus", "haiku", "inherit"] \| None` | enum-validated | FM006 on invalid |
| `permissionMode` | `Literal["default", "acceptEdits", "dontAsk", "bypassPermissions", "plan"] \| None` | enum-validated | — |
| `maxTurns` | `int \| None` | — | — |
| `skills` | `str \| None` | comma-sep | List auto-normalized |
| `mcpServers` | `list[Any] \| dict[str, Any] \| None` | — | Two formats supported |
| `hooks` | `dict[str, Any] \| None` | — | — |
| `memory` | `Literal["user", "project", "local"] \| None` | enum-validated | — |
| `background` | `bool \| None` | — | — |
| `isolation` | `Literal["worktree"] \| None` | enum-validated | — |
| `color` | `str \| None` | — | No enum constraint |

`model_config = ConfigDict(extra="allow")` — all unknown fields pass silently.

#### `CommandFrontmatter` (`frontmatter_core.py:122-157`)

| Field | Type | Constraint | Notes |
|---|---|---|---|
| `description` | `str` | required | Required for commands |
| `argument-hint` | `str \| None` | alias `argument_hint` | — |
| `allowed-tools` | `str \| None` | alias `allowed_tools`, comma-sep | List auto-normalized |
| `model` | `str \| None` | — | No enum constraint |
| `context` | `Literal["fork"] \| None` | — | — |
| `agent` | `str \| None` | — | — |
| `hooks` | `dict[str, Any] \| None` | — | — |

`model_config = ConfigDict(extra="allow")` — all unknown fields pass silently.

### Name Pattern (All File Types)

```python
NAME_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"   # plugin_validator.py:219
MAX_SKILL_NAME_LENGTH = 40                       # frontmatter_core.py:58
```

Note: Pydantic's `Field(max_length=64)` is the enforced limit; `MAX_SKILL_NAME_LENGTH = 40` is used by `init_skill.py` during scaffolding.

### Human-Readable Schema Reference

**File:** `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md`

Complete agent field documentation with examples, valid enum values, and decision trees for `model: inherit` vs explicit model. Cited source: `code.claude.com/docs/en/sub-agents.md` (accessed 2026-03-01). This is the reference document consumed by agents — the Pydantic models are the enforcement mechanism.

### Validator Rules Rule File

**File:** `plugins/plugin-creator/.claude/rules/frontmatter-requirements.md`

Scoped to `**/SKILL.md`, `**/agents/**/*.md`, `**/commands/**/*.md`. States rules in plain English (comma-separated strings, no multiline indicators, required fields). References `plugin_validator.py` as source of truth.

---

## 3. Skill/Agent Editing Workflows

### Agents that Read, Modify, or Validate Frontmatter

#### `agent-creator` (`plugins/plugin-creator/agents/agent-creator.md`)

- **Purpose:** Creates new agent `.md` files including full frontmatter.
- **Frontmatter it writes:** All fields declared in `AgentFrontmatter` plus `color`.
- **Validation step (Phase 6):** Runs `plugin_validator.py {agent-path}` after writing; loops until exit 0. If plugin-scoped, also runs `claude plugin validate {plugin-path}`.
- **Skills loaded:** `claude-plugins-reference-2026, hooks-guide, claude-skills-overview-2026, agent-creator`
- **Tools:** `Read, Write, Edit, Grep, Glob, Bash`

#### `subagent-refactorer` (`plugins/plugin-creator/agents/subagent-refactorer.md`)

- **Purpose:** Rewrites existing agent prompt files. Touches `description` field specifically.
- **Loads `write-frontmatter-description` skill** — enforces single-line, no-colons, front-loaded description rules.
- **Tools:** `Read, Write, Edit, Grep, Glob, WebFetch, WebSearch, Skill, SlashCommand` + MCP tools
- **Focus:** Frontmatter quality (description reformatting), not schema addition.

#### `contextual-ai-documentation-optimizer` (`plugins/plugin-creator/agents/contextual-ai-documentation-optimizer.md`)

- **Purpose:** Rewrites SKILL.md, CLAUDE.md, and agent body content for Claude comprehension.
- **Used for:** `DOC_IMPROVE` and `ORPHAN_RESOLVE` task types in the refactor workflow.
- **Touches frontmatter:** Yes, indirectly — `description` field optimization.

#### `plugin-assessor` (`plugins/plugin-creator/agents/plugin-assessor.md`)

- **Purpose:** Audits plugins for structure and frontmatter schema compliance.
- **Loaded skills:** `claude-skills-overview-2026, claude-plugins-reference-2026, hooks-guide`
- **Does not write** — read-only analysis.

### Skills that Drive Frontmatter Creation

#### `skill-creator` (`plugins/plugin-creator/skills/skill-creator/SKILL.md`)

- **Step 4** mandates running `init_skill.py` to scaffold SKILL.md with frontmatter template.
- **Step 5** documents all frontmatter fields with canonical rules (no multiline, no colons).
- Directs users to `write-frontmatter-description` skill for description authoring.
- Directs to `plugin_validator.py` for post-write validation.

#### `write-frontmatter-description` (`plugins/plugin-creator/skills/write-frontmatter-description/SKILL.md`)

- **Purpose:** Rules for writing the `description` field only.
- **Rules enforced:** Single-line only, no colons (use em dashes), front-load critical info, max 1024 chars.
- **Validation step:** Instructs running `plugin_validator.py [file]` after writing.
- **Loaded by:** `subagent-refactorer` agent.

#### `lint` (`plugins/plugin-creator/skills/lint/SKILL.md`)

- **Purpose:** User-invocable wrapper. Executes `plugin_validator.py $ARGUMENTS` via dynamic context injection.
- **Usage:** `/lint <path>`
- **Loads:** `ERROR_CODES.md` via `@` reference for inline error documentation.

### Pre-Commit Hook Integration

`auto_sync_manifests.py` runs on `git commit` for any change under `^plugins/`. It syncs `plugin.json` component arrays and bumps semver but does **not** modify frontmatter.

`plugin_validator.py` runs as a pre-commit hook for files matching:

```
^plugins/.*(SKILL\.md|agents/.*\.md|commands/.*\.md|plugin\.json)$
```

This means frontmatter is validated automatically on every commit touching plugin skill, agent, or command files.

---

## 4. Multi-Ecosystem Awareness

### Current State: Claude-Only Frontmatter Validation

The validator is exclusively Claude Code schema-aware. There is **no handling of non-Claude frontmatter**. Specific observations:

**No ecosystem detection.** `FileType.detect_file_type()` (`plugin_validator.py:581-610`) classifies files by path pattern (`agents/`, `skills/`, `SKILL.md`) and filename. It has no concept of a GitHub Copilot agent file, Cursor rules file, or Windsurf memory file.

**`extra="allow"` is the only escape hatch.** All three Pydantic models (`SkillFrontmatter`, `CommandFrontmatter`, `AgentFrontmatter`) use `ConfigDict(extra="allow")` (`frontmatter_core.py:83, 125, 169`). This means non-Claude fields in a Claude frontmatter file will pass silently without error — but they receive no validation.

**`FRONTMATTER_EXEMPT_FILENAMES` is a partial workaround** (`plugin_validator.py:380-386`). The set includes `"GEMINI.md"` and `"AGENTS.md"` — both non-Claude AI assistant config filenames. Files with these names skip all frontmatter validation. However, this only covers exact filename matches; it does not cover non-Claude agent files named otherwise (e.g., a GitHub Copilot agent at `.github/agents/my-agent.md`).

**Hooks documentation covers GitHub Copilot.** The `hooks-guide` skill includes `references/github-copilot.md`, `references/common-schema.md`, and `references/platform-coverage.md`, documenting GitHub Copilot hooks (`preToolUse`, `sessionStart`, etc.). However, this cross-platform awareness exists **only in documentation** — the validator and Pydantic models have no corresponding logic to handle GitHub Copilot hook schemas.

**`_should_skip_claude_validate()` (`plugin_validator.py:435-450`)** skips `claude plugin validate` CLI calls when `CLAUDE_CODE_REMOTE=true` or `CLAUDECODE` env var is set. This is a runtime escape hatch for nested Claude sessions, not an ecosystem escape hatch.

**Per-plugin `.claude-plugin/validator.json` suppression** (`plugin_validator.py:461-481`) allows suppressing specific error codes per path prefix. This is the only mechanism by which non-standard frontmatter validation can be silenced. A plugin author could suppress all FM codes for files that use a non-Claude schema, but there is no built-in automation for this.

### Summary: No Existing Multi-Ecosystem Support

| Mechanism | Covers non-Claude schemas? |
|---|---|
| `extra="allow"` on Pydantic models | Passes unknown fields silently — no validation |
| `FRONTMATTER_EXEMPT_FILENAMES` | Only exact filenames: `GEMINI.md`, `AGENTS.md`, `AGENT.md`, `CLAUDE.md`, `README.md` |
| `validator.json` suppression config | Manual per-path code suppression — not ecosystem-aware |
| `FileType` classification | No concept of non-Claude tool ecosystems |
| Hooks documentation (hooks-guide) | Documents GitHub Copilot hooks — but no validator support |

---

## 5. Error Code Reference

Complete error code list defined in `ErrorCode(StrEnum)` at `plugin_validator.py:254-321`.

The `references/ERROR_CODES.md` documents 23 codes. The source code defines 29 codes (includes HK001-HK005, NR001-NR002, SL001, TC001, PR001-PR005 not yet in the reference doc).

| Code | Category | Severity | Auto-fix | Description |
|---|---|---|---|---|
| FM001 | Frontmatter | ERROR | No | Missing required field |
| FM002 | Frontmatter | ERROR | No | Invalid YAML syntax |
| FM003 | Frontmatter | ERROR | No | Frontmatter not closed |
| FM004 | Frontmatter | ERROR | **Yes** | Forbidden multiline indicator |
| FM005 | Frontmatter | ERROR | No | Field type mismatch |
| FM006 | Frontmatter | ERROR | No | Invalid field value (enum) |
| FM007 | Frontmatter | ERROR | **Yes** | Tools field is YAML array |
| FM008 | Frontmatter | ERROR | **Yes** | Skills field is YAML array |
| FM009 | Frontmatter | ERROR | **Yes** | Unquoted colons in value |
| FM010 | Frontmatter | ERROR | No | Invalid name pattern |
| SK001 | Name format | ERROR | No | Uppercase in name |
| SK002 | Name format | ERROR | No | Underscores in name |
| SK003 | Name format | ERROR | No | Invalid hyphens |
| SK004 | Description | WARNING | No | Description too short (<20 chars) |
| SK005 | Description | WARNING | No | Missing trigger phrases |
| SK006 | Complexity | WARNING | No | Token count > `TOKEN_WARNING_THRESHOLD` (4400) |
| SK007 | Complexity | ERROR | No | Token count > `TOKEN_ERROR_THRESHOLD` (8800) |
| SK008 | Name/Dir | ERROR | No | Skill directory name violates naming convention |
| SK009 | Registration | INFO | No | Plugin uses manual skill selection |
| LK001 | Links | ERROR | No | Broken internal link |
| LK002 | Links | WARNING | No | Missing `./` prefix |
| PD001-PD003 | Progressive Disclosure | INFO | No | Missing references/examples/scripts dirs |
| PL001-PL005 | Plugin structure | ERROR | No | plugin.json issues |
| HK001-HK005 | Hooks | ERROR/WARNING | No | hooks.json validation |
| NR001-NR002 | Namespace refs | ERROR | No | Namespace reference targets |
| PR001-PR005 | Plugin registration | WARNING/INFO | No | plugin.json registration completeness |
| TC001 | Token count | INFO | No | Token count info |
| SL001 | Symlink | ERROR | No | Symlink target trailing whitespace |

**Exit codes:** `0` = passed, `1` = errors found, `2` = usage error, `130` = Ctrl+C.

---

## 6. Key File Map

| File | Role |
|---|---|
| `scripts/plugin_validator.py` | Main validator script (5,095 lines). All validation logic, error codes, FrontmatterValidator, CLI. |
| `scripts/frontmatter_core.py` | Pydantic models for skill/agent/command frontmatter. Schema ground truth. |
| `scripts/frontmatter_utils.py` | `RuamelYAMLHandler` — shared YAML read/write with round-trip preservation. |
| `scripts/normalize_frontmatter.py` | Standalone normalization tool. |
| `references/ERROR_CODES.md` | Human-readable error code docs (23 codes documented, 29 in source). |
| `references/ARCHITECTURE.md` | Validator architecture design document. |
| `references/USAGE.md` | CLI usage examples. |
| `skills/agent-creator/references/agent-schema.md` | Agent frontmatter field reference with valid enum values, decision trees, examples. |
| `skills/skill-creator/SKILL.md` | 10-step skill creation workflow. Mandatory `init_skill.py` scaffolding. |
| `skills/write-frontmatter-description/SKILL.md` | Description-field writing rules — single-line, no colons, front-load. |
| `skills/lint/SKILL.md` | User-invocable `/lint <path>` wrapper for `plugin_validator.py`. |
| `agents/agent-creator.md` | Writes agent files; runs validator in Phase 6. |
| `agents/subagent-refactorer.md` | Rewrites agent prompts and descriptions; loads `write-frontmatter-description`. |
| `agents/contextual-ai-documentation-optimizer.md` | Optimizes SKILL.md and CLAUDE.md content. |
| `.claude/rules/frontmatter-requirements.md` | Scoped rule file (applies to `**/SKILL.md`, `**/agents/**/*.md`, `**/commands/**/*.md`). |
| `skills/hooks-guide/references/platform-coverage.md` | Registry of documented hook platforms: Claude Code, GitHub Copilot. |
| `skills/hooks-guide/references/common-schema.md` | Cross-platform hooks schema comparison (Claude Code vs GitHub Copilot). |

---

_Codebase analysis: 2026-03-06_
