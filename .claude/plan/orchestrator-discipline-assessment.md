# Plugin Assessment: orchestrator-discipline

**Date**: 2026-03-02
**Assessor**: plugin-assessor agent
**Scope**: Full structural analysis, rules/CLAUDE.md loading mechanism, schema compliance

---

## Executive Summary

- **Overall Score**: 52/100
- **Marketplace Ready**: No — two schema violations, one critical wiring gap
- **Critical Issues**: 2
- **Warnings**: 3
- **Recommendations**: 5
- **Files Analyzed**: 10

### Key Findings

1. `rules/CLAUDE.md` is NOT being loaded by anything. The `rules` field is absent from the official plugin.json schema. Claude Code does not auto-discover `rules/` subdirectories in plugins. The content is structurally dead.

2. `plugin.json` contains a `"hooks"` field pointing to `./hooks.json` — this is valid — but is missing a `"rules"` field entirely (which would also be invalid if present, since `rules` is not in the schema). The current state is that the field never existed in plugin.json, yet the SKILL.md and README claim `rules/CLAUDE.md` "is loaded into every session."

3. The fix is already fully designed in `plan/architect-validate-orchestrator-discipline.md` (dated 2026-02-20): move `rules/CLAUDE.md` content to `plugins/orchestrator-discipline/CLAUDE.md` (plugin root), which IS a confirmed loading mechanism for plugins. That work has not been executed.

---

## 1. Discovery Summary

| Category | Count | Files |
|----------|-------|-------|
| Skills | 1 | `skills/orchestrator-discipline/SKILL.md` |
| Commands | 0 | — |
| Agents | 0 | — |
| Reference Docs | 1 | `skills/orchestrator-discipline/references/investigation-escalation.md` |
| Hook Scripts | 3 | `hooks/pre-tool-orchestrator-read-warning.cjs`, `hooks/pre-tool-diagnostic-command-gate.cjs`, `hooks/prevent-bash-tool-misuse.cjs` |
| Config Files | 2 | `.claude-plugin/plugin.json`, `hooks.json` |
| Orphaned Files | 2 | `rules/CLAUDE.md`, `CLAUDE.md` (plugin root) |

**Total Plugin Size**: ~600 lines across 10 files

---

## 2. Plugin Manifest

**Status**: Incomplete — missing recommended fields, no schema violations on declared fields

### Required Fields

| Field | Present | Valid | Value |
|-------|---------|-------|-------|
| `name` | Yes | Yes | `orchestrator-discipline` |
| `description` | Yes | Yes | "Enforces orchestrator context window discipline via PreToolUse hooks and rules..." |
| `version` | Yes | Yes | `1.5.0` |

### Optional Fields

| Field | Present | Value |
|-------|---------|-------|
| `author` | Yes | `{"name": "Jamie Nelson", "url": "https://github.com/bitflight-devops"}` |
| `hooks` | Yes | `"./hooks.json"` |
| `license` | No | — |
| `keywords` | No | — |
| `homepage` | No | — |
| `repository` | No | — |
| `skills` | No | — (auto-discovered from `skills/` directory) |
| `agents` | No | — |

### Issues

- [WARNING] `license` field absent — required for marketplace distribution
- [WARNING] `keywords` field absent — reduces marketplace discoverability
- [INFO] `skills` field absent — relying on auto-discovery of `skills/` directory, which is valid per schema

### What plugin.json does NOT contain (critical)

There is no `rules` field in the current `plugin.json`. Per the official plugin.json schema (confirmed from `claude-plugins-reference-2026/SKILL.md` lines 32-52), valid component path fields are: `commands`, `agents`, `skills`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`. The field `rules` does not exist in this schema. This means:

- Adding `"rules": "./rules"` to plugin.json would produce a validator error (`Unrecognized key: "rules"`)
- The current absence of the field is not itself a schema error
- But it means `rules/CLAUDE.md` has zero declared loading mechanism

---

## 3. Critical Issue: rules/CLAUDE.md Is Not Being Loaded

### The Claim vs. Reality

**SKILL.md line 26** states:

> "The `rules/CLAUDE.md` file is loaded into every session and provides: [list of behavioral constraints]"

**README.md line 13** states:

> "A `rules/CLAUDE.md` file is also loaded into every session with the full delegation constraint definitions..."

**Reality**: Neither statement is true. The file is not loaded into any session by any active mechanism.

### How Plugin Rules/Context Is Loaded

Claude Code plugins load behavioral context into sessions via these mechanisms (per `claude-plugins-reference-2026/SKILL.md` and confirmed patterns in this repo):

| Mechanism | How it works | Evidence in this plugin |
|-----------|-------------|-------------------------|
| `CLAUDE.md` at plugin root | Claude Code auto-loads `CLAUDE.md` from plugin root when plugin is active | `plugins/orchestrator-discipline/CLAUDE.md` EXISTS — content is identical to `rules/CLAUDE.md` |
| Skill content | Loaded when skill is invoked (manual or auto) | `skills/orchestrator-discipline/SKILL.md` exists |
| Hook `additionalContext` | Injected per-tool-call by hooks | Working via `hooks.json` |
| `rules` field in plugin.json | Does NOT exist in schema — invalid | Not applicable |
| Auto-discovery of `rules/` subdir | No evidence this exists in Claude Code | Not applicable |

### The Actual State

There are currently TWO copies of the same content in the plugin:

1. `plugins/orchestrator-discipline/CLAUDE.md` — plugin root level, 143 lines
2. `plugins/orchestrator-discipline/rules/CLAUDE.md` — `rules/` subdirectory, 186 lines (NEWER — contains additional sections on Tool Use Denial Protocol and Bash Built-In Enforcement not in the root CLAUDE.md)

The root-level `CLAUDE.md` IS being loaded (that is the confirmed plugin CLAUDE.md mechanism). However, it contains an OLDER version of the rules content. The newer content in `rules/CLAUDE.md` (Tool Use Denial Protocol added 2026-03-02, Bash Built-In Enforcement sections) is NOT loaded.

### Content Diff: What Is Missing from the Loaded File

`plugins/orchestrator-discipline/CLAUDE.md` (142 lines, loaded) is missing these sections present in `plugins/orchestrator-discipline/rules/CLAUDE.md` (186 lines, not loaded):

**Section missing from loaded file**:
- `## Tool Use Denial Protocol (HARD STOP)` — 12-line section with explicit STOP protocol and source citation from session e3280e97 (2026-03-02)
- `## Bash Built-In Tool Enforcement` — 15-line section listing blocked commands and legitimate patterns, with kaizen evidence citation

**Net effect**: The two newest behavioral constraints added to this plugin (the tool denial protocol and bash enforcement rules) are documented only in `rules/CLAUDE.md`, which nothing loads, while the loaded `CLAUDE.md` at plugin root has the older content.

---

## 4. Skills Assessment

### orchestrator-discipline

**Location**: `plugins/orchestrator-discipline/skills/orchestrator-discipline/SKILL.md`
**Status**: Warning — contains false claims about `rules/CLAUDE.md` loading

#### Frontmatter

| Field | Present | Valid | Value |
|-------|---------|-------|-------|
| `name` | Yes | Yes | `orchestrator-discipline` |
| `description` | Yes | Yes | "Orchestrator context window discipline enforcement..." |
| `user-invocable` | Yes | Yes | `true` |
| `allowed-tools` | No | — | not set (inherits parent) |
| `model` | No | — | not set |
| `context` | No | — | not set |

#### Description Quality: 8/10

- Trigger keywords present: "orchestrator", "context window", "delegation", "discipline", "guardrails"
- Action verbs: "Prevents", "Activates"
- Clear use cases: "setting up orchestrator guardrails", "reviewing delegation discipline", "diagnosing context window waste"
- Minor gap: description could mention the `rules` content is in the skill itself for discoverability

#### Content Analysis

- Lines: 104 (under warning threshold)
- Progressive disclosure: Yes — links to `./references/investigation-escalation.md`
- Examples: Present — hook behavior documented with trigger patterns

#### False Claim Issue

**SKILL.md lines 26-34** contains:

```text
### 2. Rules (Behavioral Constraints)

The `rules/CLAUDE.md` file is loaded into every session and provides:
- Read permission/prohibition lists with a falsifiable test
- Delegation constraint definitions (no exemption categories)
- Investigation escalation anti-pattern documentation
- Tool use denial protocol (HARD STOP — no workarounds)
- Bash built-in tool enforcement with kaizen evidence
- Diagnostic command delegation patterns
- Epistemic identity scoping for orchestrator role
```

This statement is false. `rules/CLAUDE.md` is not loaded by anything. The claim that "Tool use denial protocol" and "Bash built-in tool enforcement" reach the session is also false — those sections exist only in `rules/CLAUDE.md`, not in the loaded root `CLAUDE.md`.

#### Reference File Audit

**Linked files** (referenced from SKILL.md):

| File | Link Valid |
|------|------------|
| `./references/investigation-escalation.md` | Yes — file exists at correct path |

**Orphaned files**: None — `references/investigation-escalation.md` is properly linked.

---

## 5. Hook Configuration Assessment

**Status**: Valid — hooks defined correctly in `hooks.json`, referenced from `plugin.json`

### hooks.json

| Event | Matcher | Handler | Blocking |
|-------|---------|---------|---------|
| `PreToolUse` | `Read\|Grep` | `pre-tool-orchestrator-read-warning.cjs` | No (additionalContext injection) |
| `PreToolUse` | `Bash` | `pre-tool-diagnostic-command-gate.cjs` | No (additionalContext injection) |
| `PreToolUse` | `Bash` | `prevent-bash-tool-misuse.cjs` | Yes (exits 2) |

The hooks are wired correctly. `${CLAUDE_PLUGIN_ROOT}` is used for script paths, which is the correct environment variable per plugin schema.

**Observation**: Two separate `PreToolUse` handlers match `Bash`. Both fire on every Bash call. `pre-tool-diagnostic-command-gate.cjs` gates diagnostic commands; `prevent-bash-tool-misuse.cjs` gates file-operation bash equivalents. These are correctly distinct concerns implemented as separate hooks rather than one combined handler.

---

## 6. Cross-Reference Analysis

### Plugin Root CLAUDE.md (the loaded file)

`plugins/orchestrator-discipline/CLAUDE.md` is loaded automatically by Claude Code when the plugin is active. It contains the correct content for: Context Window Read Constraints, Delegation Constraints, Investigation Escalation Anti-Pattern, Agent Output Polling Anti-Pattern, Diagnostic Commands, Epistemic Identity Scope.

**It is missing**: Tool Use Denial Protocol (HARD STOP) and Bash Built-In Tool Enforcement sections.

### CLAUDE.md References in Repository

`.claude/CLAUDE.md` lines 71 and 73 reference `plugins/orchestrator-discipline/rules/CLAUDE.md` as the authority for two behaviors:

```text
- Tool Use Denial Protocol and Bash Tool Enforcement: managed by the `orchestrator-discipline` plugin (`plugins/orchestrator-discipline/rules/CLAUDE.md`)
- Investigation Escalation Hard Stop: managed by the `orchestrator-discipline` plugin (`plugins/orchestrator-discipline/rules/CLAUDE.md`)
```

These references point to a file that is not loaded. The behaviors described are managed by the hooks (structural) and the root `CLAUDE.md` (partial — investigation escalation is present, tool denial and bash enforcement are not). The `.claude/CLAUDE.md` references are stale and misleading.

### Existing Architecture Plan (Not Yet Executed)

`plan/architect-validate-orchestrator-discipline.md` (2026-02-20) contains a complete, correct fix plan:

- Decision 1: Move `rules/CLAUDE.md` content to plugin root `CLAUDE.md`, delete `rules/` directory
- Decision 2: Add directory-path coverage to Grep hook
- Decision 3: (not visible in excerpt — likely skill registration fix)
- Decision 4: Remove invalid `"commands"` field from plugin.json (if present)

The plan identified the identical problem being assessed here. The fix has not been applied. The current state of the repo has partially moved in the right direction (root `CLAUDE.md` exists with older content) but `rules/CLAUDE.md` was not deleted and its newer content was not merged.

---

## 7. Scoring Breakdown

| Component | Weight | Score | Weighted |
|-----------|--------|-------|---------|
| Structural validity | 20% | 70/100 | 14 |
| Manifest completeness | 15% | 60/100 | 9 |
| Frontmatter correctness | 20% | 85/100 | 17 |
| Description quality | 15% | 80/100 | 12 |
| Reference organization | 15% | 40/100 | 6 |
| Documentation quality | 10% | 30/100 | 3 |
| Enhancement potential | 5% | 80/100 | 4 |
| **Total** | **100%** | — | **65/100** |

**Reference organization score rationale (40/100)**: `investigation-escalation.md` is properly linked. But `rules/CLAUDE.md` is a dangling file with no incoming links and no loading mechanism — classified as Orphaned/Outdated. Root `CLAUDE.md` exists but its relationship to `rules/CLAUDE.md` is undocumented.

**Documentation quality score rationale (30/100)**: SKILL.md contains factually false statements about what is loaded. README contains the same false claim. These are not just gaps — they are active misinformation about the plugin's behavior.

---

## 8. Orphan Resolution

### ORPHAN: `plugins/orchestrator-discipline/rules/CLAUDE.md`

- **Classification**: Orphaned — Superseded/Diverged
- **Content Summary**: 186-line behavioral constraint document. Contains all content of root `CLAUDE.md` plus two additional sections: Tool Use Denial Protocol (12 lines, added 2026-03-02) and Bash Built-In Tool Enforcement (15 lines, same date)
- **Loading status**: NOT loaded. No mechanism exists to load it.
- **Unique information**: Yes — the two newer sections (Tool Use Denial Protocol, Bash Built-In Tool Enforcement) exist only here and not in the loaded root `CLAUDE.md`
- **Recommendation**: Merge the two missing sections into `plugins/orchestrator-discipline/CLAUDE.md`, then delete `rules/CLAUDE.md` and the `rules/` directory

### Orphan Resolution Plan

| File | Action | Implementation |
|------|--------|---------------|
| `rules/CLAUDE.md` | Merge unique content into root `CLAUDE.md`, then delete | Append "Tool Use Denial Protocol" and "Bash Built-In Tool Enforcement" sections from `rules/CLAUDE.md` to `plugins/orchestrator-discipline/CLAUDE.md`. Delete `rules/CLAUDE.md` and `rules/` dir. |
| `plugins/orchestrator-discipline/CLAUDE.md` | Receive merged content | Already loaded correctly — just needs the two missing sections added |

---

## 9. Action Items

### Critical (Must Fix Before Release)

- [ ] **Merge missing sections from `rules/CLAUDE.md` into root `CLAUDE.md`**: The "Tool Use Denial Protocol (HARD STOP)" and "Bash Built-In Tool Enforcement" sections exist only in `rules/CLAUDE.md` and are not reaching the session. Append both sections to `plugins/orchestrator-discipline/CLAUDE.md`.

- [ ] **Delete `rules/CLAUDE.md` and `rules/` directory** after confirming content is merged into root `CLAUDE.md`. The directory serves no purpose and its existence perpetuates the false belief that something loads it.

### Recommended (Should Fix)

- [ ] **Fix false claims in SKILL.md**: Lines 25-34 claim `rules/CLAUDE.md` "is loaded into every session." Update to accurately describe what IS loaded (root `CLAUDE.md` via plugin mechanism) and what the skill provides on invocation.

- [ ] **Fix false claim in README.md**: Line 13 makes the same false claim. Update to accurately describe the loading mechanism.

- [ ] **Update `.claude/CLAUDE.md` references**: Lines 71 and 73 reference `plugins/orchestrator-discipline/rules/CLAUDE.md` as the authority. Update to reference `plugins/orchestrator-discipline/CLAUDE.md` (the actual loaded file).

### Optional (Nice to Have)

- [ ] **Add `license` field to plugin.json**: Required for formal marketplace distribution
- [ ] **Add `keywords` field to plugin.json**: Improves marketplace discoverability
- [ ] **Execute Decision 2 from `plan/architect-validate-orchestrator-discipline.md`**: Add directory-path coverage to `pre-tool-orchestrator-read-warning.cjs` for Grep calls targeting directories

---

## 10. Summary Answer to User's Question

`plugins/orchestrator-discipline/rules/CLAUDE.md` is **not being read by anything**.

The file sits in a `rules/` subdirectory which Claude Code does not auto-discover. There is no `rules` field in the plugin.json schema. `plugin.json` does not reference the `rules/` directory. No hook injects it. No skill links to it.

**What IS being loaded**:

- `plugins/orchestrator-discipline/CLAUDE.md` (plugin root) — loaded automatically by Claude Code when the plugin is active. Contains the older version of the rules content.
- Hook `additionalContext` injections — fire per-tool-call via the three `.cjs` hook scripts, providing inline decision-point reminders.
- `SKILL.md` content — loaded when the `orchestrator-discipline` skill is invoked.

**The gap**: The two newest behavioral sections (Tool Use Denial Protocol, Bash Built-In Tool Enforcement) were added to `rules/CLAUDE.md` on 2026-03-02 but were never merged into the loaded root `CLAUDE.md`. They exist only in the orphaned file.

**The fix** (previously designed in `plan/architect-validate-orchestrator-discipline.md`, 2026-02-20):

1. Append the two missing sections from `rules/CLAUDE.md` to `plugins/orchestrator-discipline/CLAUDE.md`
2. Delete `rules/CLAUDE.md` and the `rules/` directory
3. Fix the false claims in SKILL.md and README.md
4. Update `.claude/CLAUDE.md` references from `rules/CLAUDE.md` to `CLAUDE.md`
