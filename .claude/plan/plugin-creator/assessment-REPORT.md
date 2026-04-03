# Plugin Assessment: plugin-creator

Date: 2026-03-17

## Summary

48 issues found: 3 critical, 18 high, 18 medium, 9 low.

The hooks skills are the most severe gap — they document 13 of 21 current events, carry wrong
matcher flags for `SubagentStart`/`SubagentStop`/`SessionEnd`, use an obsolete tool name
(`Task` instead of `Agent`), and are missing two new handler types (`http`, `agent`). Secondary
gaps are a missing substitution variable (`${CLAUDE_SKILL_DIR}`) present in all skill authoring
references, one wrong `agents` field type in the plugin.json schema, and a missing security
restriction notice for plugin agents in the MCP reference file.

---

## Critical Issues (must fix first)

### C1 — `Task` matcher name obsolete; must be `Agent`

- **File**: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
- **What's wrong**: The PreToolUse/PostToolUse/PermissionRequest matcher table uses `Task` as
  the tool name for subagent operations. The Task tool was renamed to `Agent` in v2.1.63 (now complete). Any
  hook written with `matcher: "Task"` will silently fail to match subagent operations in current
  Claude Code.
- **What current docs say**: The official hooks.md tool-name examples use `Agent`, not `Task`.
  SOURCE: <https://code.claude.com/docs/en/hooks.md> (accessed 2026-03-17)
- **Recommended fix**: Replace every occurrence of `Task` in matcher examples and tables with
  `Agent` in `hooks-core-reference/SKILL.md`.

### C2 — `SubagentStart` and `SubagentStop` matcher support is wrong

- **Files**:
  - `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
  - `plugins/plugin-creator/skills/hook-creator/SKILL.md`
- **What's wrong**: Both files mark `SubagentStart` and `SubagentStop` as having no matcher
  support (column value = No). Current official docs show both events support matchers, filtering
  by agent type name.
- **What current docs say**: SubagentStart and SubagentStop appear in the same matcher-support
  group in the official event table. SOURCE: <https://code.claude.com/docs/en/hooks.md>
  (accessed 2026-03-17)
- **Recommended fix**:
  - In `hooks-core-reference/SKILL.md`: set matcher support to Yes for both events; add
    agent-type matcher example.
  - In `hook-creator/SKILL.md`: remove `SubagentStart` from the "Events without matchers" list.

### C3 — `hooks-patterns` frontmatter supported events claim is wrong

- **File**: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`
- **What's wrong**: The skill states "Supported events: `PreToolUse`, `PostToolUse`, `Stop`" for
  skill/agent frontmatter hooks. This is factually incorrect — it implies only these three events
  can be used in frontmatter.
- **What current docs say**: "All hook events are supported in skill and agent frontmatter. The
  following are the most common events for subagents: PreToolUse, PostToolUse, Stop."
  SOURCE: <https://code.claude.com/docs/en/hooks.md> (accessed 2026-03-17)
- **Recommended fix**: Change the statement to "All hook events are supported in skill and agent
  frontmatter."

---

## High Priority Issues

### H1 — Default command hook timeout is wrong

- **File**: `plugins/plugin-creator/skills/hook-creator/SKILL.md`
- **What's wrong**: Skill states the built-in default timeout for command hooks is 60 seconds.
- **What current docs say**: The default is 600 seconds (10 minutes) for command hooks; 30s for
  prompt; 60s for agent. SOURCE: <https://code.claude.com/docs/en/hooks.md> (accessed 2026-03-17)
- **Recommended fix**: Change 60s to 600s in the timeout reference table.

### H2 — `SessionEnd` matcher support is wrong

- **File**: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
- **What's wrong**: Skill marks `SessionEnd` as having no matcher (column value = No). Current
  docs show `SessionEnd` supports matchers filtering by session-end reason.
- **What current docs say**: `SessionEnd` reason values are `clear`, `logout`,
  `prompt_input_exit`, `bypass_permissions_disabled`, `other`. SOURCE:
  <https://code.claude.com/docs/en/hooks.md> (accessed 2026-03-17)
- **Recommended fix**: Set matcher support to Yes for `SessionEnd`; document the reason-based
  matcher values in the event table.

### H3 — `inline-agent-hooks.md` missing plugin agent `mcpServers` restriction

- **File**: `plugins/plugin-creator/skills/hooks-guide/references/inline-agent-hooks.md`
- **What's wrong**: The reference documents `mcpServers` as a valid agent frontmatter field with
  no caveat about plugin agents. Plugin developers who follow this reference will add `mcpServers`
  to plugin agents and get silent no-op behavior — the field is stripped at runtime.
- **What current docs say**: "For security reasons, plugin subagents do not support the `hooks`,
  `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading
  agents from a plugin." SOURCE: <https://code.claude.com/docs/en/sub-agents.md>
  (accessed 2026-03-17)
- **Recommended fix**: Add a prominent warning immediately after the `mcpServers` field entry:
  field is silently stripped for plugin agents; only works in `.claude/agents/` or
  `~/.claude/agents/`.

### H4 — `agents` field typed as `string|array` in plugin.json schema table

- **File**: `plugins/plugin-creator/skills/plugin-creator/SKILL.md` (plugin.json schema table,
  line ~584)
- **What's wrong**: Schema table shows `agents` field type as `string|array`. A directory string
  is explicitly invalid and triggers `agents: Invalid input` error at runtime.
- **What current docs say**: `agents` MUST be an array of individual file paths. SOURCE:
  <https://code.claude.com/docs/en/plugins.md> (accessed 2026-03-17)
- **Recommended fix**: Change type column from `string|array` to `array` for the `agents` field.

### H5 — 9 new hook events missing across multiple skills (pervasive)

The following 9 events are in current official docs but absent from all hook skills:

| Missing Event | Blocking (exit 2)? |
|---|---|
| `TeammateIdle` | Yes — prevents teammate going idle |
| `TaskCompleted` | Yes — prevents task being marked complete |
| `InstructionsLoaded` | No |
| `ConfigChange` | Yes — except `policy_settings` changes |
| `WorktreeCreate` | Yes — any non-zero exit fails creation |
| `WorktreeRemove` | No — debug-logged only |
| `PostCompact` | No — stderr shown to user |
| `Elicitation` | Yes — denies MCP input elicitation |
| `ElicitationResult` | Yes — blocks elicitation response |

**Files affected**:

- `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md` — event table, output handling
  table, exit code 2 table (all missing these events)
- `plugins/plugin-creator/skills/hooks-io-api/SKILL.md` — exit code 2 table missing all 9 events
- `plugins/plugin-creator/skills/hook-creator/SKILL.md` — event selection flowchart missing all
  9 events
- `plugins/plugin-creator/skills/claude-plugins-reference-2026/SKILL.md` — hook events table
  missing `TeammateIdle`, `TaskCompleted`, `ConfigChange`, `WorktreeCreate`, `WorktreeRemove`
- `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md` — hook events
  table missing all 9

SOURCE: <https://code.claude.com/docs/en/hooks.md> (accessed 2026-03-17)

**Recommended fix**: Add all 9 events to the event tables in all affected files. Start with
`hooks-core-reference/SKILL.md` as the authoritative source, then propagate to the others.

### H6 — New hook handler types `type: "http"` and `type: "agent"` undocumented

- **Files**:
  - `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
  - `plugins/plugin-creator/skills/hook-creator/SKILL.md`
- **What's wrong**: Both skills only document `type: "command"` and `type: "prompt"`. Two new
  handler types are absent from all documentation.
- **What current docs say**: Current docs add `type: "http"` (HTTP hooks — POST to a URL) and
  `type: "agent"` (delegates to a subagent). SOURCE: <https://code.claude.com/docs/en/hooks.md>
  (accessed 2026-03-17)
- **Recommended fix**:
  - `hooks-core-reference/SKILL.md`: add both types with schema.
  - `hook-creator/SKILL.md`: add both to the type-selection flowchart.
  - `hooks-patterns/SKILL.md`: expand `type: "agent"` entry with full schema (currently listed
    without schema detail).

### H7 — `${CLAUDE_SKILL_DIR}` substitution variable absent from all reference files

- **Files affected**:
  - `plugins/plugin-creator/skills/claude-skills-overview-2026/SKILL.md` (substitutions table)
  - `plugins/plugin-creator/skills/skill-creator/SKILL.md` (Step 5 guidance, lines ~552–555)
  - `plugins/plugin-creator/skills/skill-creator/references/claude-code-skills-official.md`
    (substitutions table, lines ~103–108)
  - `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
    (substitution variable table, lines ~33–37)
- **What's wrong**: `${CLAUDE_SKILL_DIR}` is completely absent from every substitution reference.
  This is the most pervasive gap — it affects every skill author who needs to reference files
  relative to the skill itself.
- **What current docs say**: "The directory containing the skill's SKILL.md file. For plugin
  skills, this is the skill's subdirectory within the plugin, not the plugin root."
  SOURCE: <https://code.claude.com/docs/en/skills.md> (accessed 2026-03-17)
- **Recommended fix**: Add `${CLAUDE_SKILL_DIR}` row to substitution tables in all four files.

### H8 — Agent SDK / headless mode has no reference file in plugin-creator

- **What's wrong**: There is no dedicated reference for the Agent SDK CLI (`claude -p`). The only
  mentions are incidental (one example in
  `plugins/plugin-creator/skills/skill-creator/references/evaluation-and-optimization.md`
  line 52). Critically, the docs state user-invocable skills are unavailable in `-p` mode —
  plugin authors creating user-invocable skills have no warning of this.
- **What current docs say**: "User-invoked skills like `/commit` and built-in commands are only
  available in interactive mode. In `-p` mode, describe the task you want to accomplish instead."
  Also documents: `--output-format json/stream-json`, `--json-schema` for typed output,
  `--continue`/`--resume` for multi-turn. SOURCE: <https://code.claude.com/docs/en/headless.md>
  (accessed 2026-03-17)
- **Affected skills**: `skill-creator` (testing guidance), `agent-creator` (non-interactive
  testing), `audit-skill-completeness` (checklist should verify headless compatibility).
- **Recommended fix**: Create
  `plugins/plugin-creator/skills/skill-creator/references/agent-sdk-headless.md` and link from
  `skill-creator/SKILL.md`. Add a note to `skill-creator/SKILL.md` that user-invocable skills
  are unavailable in `-p` mode.

### H9 — `stale model names in skill-creator`

- **File**: `plugins/plugin-creator/skills/skill-creator/SKILL.md` (Step 5 guidance, line ~521)
- **What's wrong**: Guidance lists `claude-opus-4-5-20251101`, `claude-sonnet-4-20250514` as
  model ID examples. These are dated model versions that will not match current runtimes.
- **What current docs say**: Alias forms (`opus`, `sonnet`, `haiku`) are the stable reference
  forms. SOURCE: <https://code.claude.com/docs/en/skills.md> (accessed 2026-03-17)
- **Recommended fix**: Remove specific dated model IDs from examples; keep alias forms only.

### H10 — `claude-skills-overview-2026` stale model IDs and missing `${CLAUDE_SKILL_DIR}`

- **File**: `plugins/plugin-creator/skills/claude-skills-overview-2026/SKILL.md`
- **What's wrong**:
  1. Frontmatter table examples show `claude-opus-4-5-20251101`, `claude-sonnet-4-20250514` —
     dated model IDs.
  2. Substitutions table omits `${CLAUDE_SKILL_DIR}` (see H7).
  3. Hooks field in frontmatter table lists events as `PreToolUse`, `PostToolUse`, `Stop` only —
     may be stale (see H5 re: all events supported).
- **Recommended fix**: Remove dated model IDs; add `${CLAUDE_SKILL_DIR}` (covered in H7 fix).

### H11 — `plugin-creator/SKILL.md` bundled skills list is incomplete

- **File**: `plugins/plugin-creator/skills/plugin-creator/SKILL.md` (research phase, line ~306)
- **What's wrong**: The bundled skills list does not include `/claude-api` or `/loop`. This
  partial list affects research quality during plugin creation workflows.
- **What current docs say**: Current `skills.md` lists 5 bundled skills: `/simplify`, `/batch`,
  `/debug`, `/loop`, `/claude-api`. SOURCE: <https://code.claude.com/docs/en/skills.md>
  (accessed 2026-03-17)
- **Recommended fix**: Add `/loop` and `/claude-api` to the bundled skills list in the research
  phase section.

### H12 — `claude-code-skills-official.md` missing two bundled skills

- **File**: `plugins/plugin-creator/skills/skill-creator/references/claude-code-skills-official.md`
  (bundled skills table, lines ~223–229)
- **What's wrong**: Lists only 3 bundled skills (`/simplify`, `/batch`, `/debug`). Missing
  `/loop` and `/claude-api`.
- **Recommended fix**: Add both missing bundled skills to the table.

### H13 — `subagent-refactorer` body references non-existent `Opus 4.1`

- **File**: `plugins/plugin-creator/agents/subagent-refactorer.md`
- **What's wrong**: Agent body states "You refactor agents specifically for Claude models
  (Sonnet 4.5 and Opus 4.1)". `Opus 4.1` does not exist. The same file also cites
  `claude-opus-4-6` elsewhere in the body, creating an internal contradiction.
- **Recommended fix**: Update mandate section to reference current model family (Opus 4.5/4.6);
  remove hardcoded pricing annotation (`$5/$25 per million tokens — Nov 24, 2025`).

### H14 — `advanced-features.md` hook events table missing 9 new events

- **File**: `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
  (hook events table, lines ~147–160)
- **What's wrong**: Table is missing `TeammateIdle`, `TaskCompleted`, `ConfigChange`,
  `WorktreeCreate`, `WorktreeRemove`, `Elicitation`, `ElicitationResult`, `InstructionsLoaded`,
  `PostCompact` (see H5). Also shows `Setup` with no matcher but `hooks-core-reference` says it
  has matchers — inconsistency. Shows `SubagentStop` as having a matcher while `hooks-core-reference`
  says No — additional inconsistency.
- **Recommended fix**: Add the 9 missing events; resolve `Setup` and `SubagentStop` matcher
  inconsistencies after the `Setup` event status is verified (see M1).

### H15 — `claude-plugins-reference-2026` missing 5 new hook events

- **File**: `plugins/plugin-creator/skills/claude-plugins-reference-2026/SKILL.md`
  (hook events table, lines ~225–240)
- **What's wrong**: Hook events table is missing `TeammateIdle`, `TaskCompleted`, `ConfigChange`,
  `WorktreeCreate`, `WorktreeRemove`. Also documents a `Setup` event that is absent from the
  auto-generated `hooks-guide/references/claude-code.md` (see M1).
- **Recommended fix**: Add the 5 missing events. Resolve `Setup` status before deciding whether
  to retain or remove it.

### H16 — `hooks-io-api` exit code 2 table missing 9 new events

- **File**: `plugins/plugin-creator/skills/hooks-io-api/SKILL.md`
- **What's wrong**: The exit code 2 behavior table does not cover any of the 9 new events
  (see H5), leaving hook authors without guidance on which new events can block operations.
- **Recommended fix**: Add all 9 new events to the exit code 2 table with their blocking
  behavior per the table in H5.

### H17 — `skill-creator/SKILL.md` missing user-invocable + headless constraint note

- **File**: `plugins/plugin-creator/skills/skill-creator/SKILL.md`
- **What's wrong**: No mention that user-invocable skills (`user-invocable: true`) are
  unavailable when Claude Code is run with `-p`. Plugin authors building user-invocable skills
  have no warning.
- **Recommended fix**: Add a note to the `user-invocable` field documentation and the testing
  section (covered more broadly in H8 — creating the headless reference file).

### H18 — `plugin-lifecycle/SKILL.md` domain prerequisites reference wrong field count

- **File**: `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md` (line ~37)
- **What's wrong**: States "all 14 frontmatter fields" — current docs list 10 fields for skills.
- **Recommended fix**: Change "14" to "10". Alternatively remove the count and reference the
  skill directly.

---

## Medium Priority Issues

### M1 — `Setup` event conflict between two reference files

- **Files**:
  - `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md` (lists `Setup`)
  - `plugins/plugin-creator/skills/hooks-guide/references/claude-code.md` (does NOT list `Setup`)
- **What's wrong**: `hooks-core-reference` documents a `Setup` event that fires on `--init`,
  `--init-only`, `--maintenance` flags. The auto-generated `claude-code.md` (sourced 2026-03-01)
  does not list it. One of these is wrong — they cannot both be correct.
- **Recommended fix**: Fetch current `https://code.claude.com/docs/en/hooks.md` and confirm
  whether `Setup` is present. If present: add to `claude-code.md`. If absent: remove from
  `hooks-core-reference/SKILL.md` and `claude-plugins-reference-2026/SKILL.md`.

### M2 — `model` field missing full-model-ID option in two reference files

- **Files**:
  - `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md`
  - `plugins/plugin-creator/skills/hooks-guide/references/inline-agent-hooks.md`
- **What's wrong**: Both list `model` options as `sonnet`, `opus`, `haiku`, `inherit`. The
  full-model-ID option is absent.
- **What current docs say**: "model: sonnet, opus, haiku, a full model ID (for example,
  claude-opus-4-6), or inherit. Defaults to inherit." SOURCE:
  <https://code.claude.com/docs/en/sub-agents.md> (accessed 2026-03-17)
- **Recommended fix**: Add the full-model-ID option with example (`claude-opus-4-6`) to the
  model field documentation in both files.

### M3 — `SubagentStop` input schema incomplete in `hooks-io-api`

- **File**: `plugins/plugin-creator/skills/hooks-io-api/SKILL.md`
- **What's wrong**: `SubagentStop` input schema is documented as
  `{ "agent_id": "def456", "agent_transcript_path": "...", "stop_hook_active": false }`.
  Two fields are missing.
- **What current docs say**: Current docs add `last_assistant_message` (final response text) and
  `agent_type` (used for matcher filtering). SOURCE: <https://code.claude.com/docs/en/hooks.md>
  (accessed 2026-03-17)
- **Recommended fix**: Add both fields to the SubagentStop input schema section.

### M4 — New output schemas missing in `hooks-io-api` for new events

- **File**: `plugins/plugin-creator/skills/hooks-io-api/SKILL.md`
- **What's wrong**: No output schema documentation for:
  - `WorktreeCreate` output (hook prints absolute path to created worktree to stdout)
  - `Elicitation` output (`action`, `content` fields)
  - `ElicitationResult` output
- **Recommended fix**: Add output schema sections for these three events.

### M5 — `once`, `statusMessage`, and `async` hook fields undocumented

- **File**: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
- **What's wrong**: Three valid common hook fields are absent from all documentation:
  - `once: true` — runs only once per session, then removed (skills only, not agents)
  - `statusMessage` — custom spinner message while hook runs
  - `async: true` — run command hook in background without blocking
- **Recommended fix**: Add all three to the common hook fields section.
  Also add `once` to the configuration docs in `hook-creator/SKILL.md`.

### M6 — `once` field missing in `hook-creator`

- **File**: `plugins/plugin-creator/skills/hook-creator/SKILL.md`
- **What's wrong**: `once` field is not documented (companion to M5).
- **Recommended fix**: Add `once` to the hook configuration section.

### M7 — `settings.json` plugin default-settings feature undocumented in schema

- **File**: `plugins/plugin-creator/skills/claude-plugins-reference-2026/SKILL.md`
- **What's wrong**: Current `plugins.md` documents "Ship default settings with your plugin" via
  a `settings.json` at plugin root supporting the `agent` key. The `claude-plugins-reference-2026`
  schema section has no entry for this. It appears only as a brief blockquote annotation in
  `plugin-creator/SKILL.md`.
- **Recommended fix**: Add `settings.json` plugin configuration to the plugin.json schema
  section.

### M8 — `advanced-features.md` `SubagentStop` matcher inconsistency

- **File**: `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
- **What's wrong**: Shows `SubagentStop` with "Yes" for matcher, while `hooks-core-reference`
  says "No". This is an internal contradiction between two files in the same plugin.
- **Recommended fix**: Align with the resolution from C2 — `SubagentStop` should be Yes for
  matcher support per current official docs.

### M9 — `advanced-features.md` `Setup` event matcher inconsistency

- **File**: `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
- **What's wrong**: Shows `Setup` with "No" for matcher while `hooks-core-reference` says it has
  matchers (`init`, `maintenance`).
- **Recommended fix**: Resolve after M1 (verify `Setup` status against live docs).

### M10 — `argumentHint` and `alwaysLoadSkills` fields in `agent-schema.md` unverified

- **File**: `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md`
- **What's wrong**: Two fields are documented locally but absent from the official supported
  frontmatter fields table: `argumentHint` and `alwaysLoadSkills`. Their status is unknown —
  they may be skilllint extensions, removed fields, or simply undocumented upstream.
- **Recommended fix**: Verify against current `https://code.claude.com/docs/en/sub-agents.md`.
  If absent from official docs: remove or annotate as "local extension, not supported by Claude
  Code runtime."

### M11 — `claude-code-skills-official.md` missing `${CLAUDE_SKILL_DIR}` (companion to H7)

- **File**: `plugins/plugin-creator/skills/skill-creator/references/claude-code-skills-official.md`
  (substitutions table, lines ~103–108)
- **What's wrong**: `${CLAUDE_SKILL_DIR}` is absent from the substitutions table. Source access
  date is 2026-03-01 — the variable appears to have been added to docs after that date.
- **Recommended fix**: Add `${CLAUDE_SKILL_DIR}` row to the substitutions table (covered in H7).

### M12 — `hooks-core-reference` missing `PermissionRequest` event in `advanced-features.md`

- **File**: `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
  (hook events table, lines ~147–160)
- **What's wrong**: No `PermissionRequest` event entry in the hook events table.
- **Recommended fix**: Add `PermissionRequest` to the table.

### M13 — `claude-plugins-reference-2026` hook events table has `Setup` event not in generated reference

- **File**: `plugins/plugin-creator/skills/claude-plugins-reference-2026/SKILL.md`
  (hook events table, line ~235)
- **What's wrong**: Lists `Setup` event which is absent from the auto-generated
  `hooks-guide/references/claude-code.md`. Contingent on M1 resolution.
- **Recommended fix**: Resolve after M1; remove if `Setup` is no longer in official docs.

### M14 — `subagent-refactorer` hardcoded pricing annotation will go stale

- **File**: `plugins/plugin-creator/agents/subagent-refactorer.md`
- **What's wrong**: Body contains `"Opus 4.5 now $5/$25 per million tokens — Nov 24, 2025"`.
  Pricing changes frequently; this annotation is already a maintenance liability.
- **Recommended fix**: Remove the hardcoded pricing/version annotation. Reference current model
  aliases only.

### M15 — `agent-creator` skill has no agent teams guidance

- **File**: `plugins/plugin-creator/skills/agent-creator/SKILL.md`
- **What's wrong**: The skill creates subagents but has no guidance on designing agents for team
  workflows, when to use agent teams vs subagents, or how to configure team-aware hooks
  (`TeammateIdle`, `TaskCompleted`).
- **Recommended fix**: Add a "Creating agents for team workflows" section with a link to the
  agent-teams resource at
  `plugins/plugin-creator/skills/claude-skills-overview-2026/resources/agent-teams.md`.

### M16 — `advanced-features.md` has no agent teams section

- **File**: `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
- **What's wrong**: Covers scheduled tasks and extended thinking but has no section on designing
  plugins that leverage agent teams (hooks for team quality gates, `TeammateIdle`/`TaskCompleted`
  patterns).
- **Recommended fix**: Add an "Agent Teams in Plugins" section (parallel to the existing
  "Scheduled Tasks in Plugins" section).

### M17 — `hooks-guide/SKILL.md` stale source domain URL

- **File**: `plugins/plugin-creator/skills/hooks-guide/SKILL.md`
- **What's wrong**: Sources cite `https://docs.anthropic.com/en/docs/claude-code/hooks.md`
  (old domain). Canonical URL has changed.
- **What current docs say**: Canonical URL is `https://code.claude.com/docs/en/hooks.md`.
- **Recommended fix**: Update source URL to current domain.

### M18 — `hooks-io-api` stale source URL reference

- **File**: `plugins/plugin-creator/skills/hooks-io-api/SKILL.md`
- **What's wrong**: Sources cite `https://code.claude.com/docs/en/hooks-guide.md` — this URL
  appears to be a different page from the main hooks reference; may be a stale reference to an
  old page.
- **Recommended fix**: Verify the URL; if stale, update to `https://code.claude.com/docs/en/hooks.md`.

---

## Low Priority Issues

### L1 — `SessionEnd` missing `bypass_permissions_disabled` reason value

- **Files**:
  - `plugins/plugin-creator/skills/hooks-io-api/SKILL.md`
  - `plugins/plugin-creator/skills/plugin-creator/references/advanced-features.md`
- **What's wrong**: Both document `SessionEnd` reason values as `clear`, `logout`,
  `prompt_input_exit`, `other`. Current docs add `bypass_permissions_disabled`.
- **Recommended fix**: Add `bypass_permissions_disabled` to the reason values list in both files.

### L2 — `agent-teams.md` resource: `Shift+Up` navigation key undocumented

- **File**: `plugins/plugin-creator/skills/claude-skills-overview-2026/resources/agent-teams.md`
  (line ~115)
- **What's wrong**: Documents "Shift+Up/Down to select" in in-process mode. Current official
  docs only describe `Shift+Down` to cycle forward. `Shift+Up` is not in the official docs.
- **Recommended fix**: Remove `Shift+Up` reference or mark as unverified.

### L3 — `agent-teams.md` "Delegate Mode" (Shift+Tab) unverified

- **File**: `plugins/plugin-creator/skills/claude-skills-overview-2026/resources/agent-teams.md`
  (line ~111)
- **What's wrong**: "Delegate Mode" (Shift+Tab) is mentioned but cannot be verified in current
  official docs — may be experimental/unpublished.
- **Recommended fix**: Add `(unverified — not in current published docs)` annotation.

### L4 — `plugin-lifecycle/SKILL.md` "14 frontmatter fields" count is wrong

- **File**: `plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md` (line ~37)
- **What's wrong**: States "all 14 frontmatter fields" — current docs list 10 fields for skills.
- **Recommended fix**: Change "14" to "10" or remove the count and reference the skill directly.
  (Companion to H18 — same file, same fix.)

### L5 — MCP elicitation hooks pattern not covered anywhere

- **Files**: `plugins/plugin-creator/skills/hooks-patterns/SKILL.md`
- **What's wrong**: After `Elicitation` and `ElicitationResult` events are added (H5), there is
  no pattern example for using them to respond to MCP server input requests.
- **Recommended fix**: After H5 is fixed, add an MCP elicitation pattern example to
  `hooks-patterns/SKILL.md`.

### L6 — Plugin `.mcp.json` alternative to inline `plugin.json` undocumented

- **File**: `plugins/plugin-creator/skills/hooks-core-reference/SKILL.md`
- **What's wrong**: Current MCP docs add `.mcp.json` at plugin root as an alternative to inline
  `plugin.json` for MCP server configuration. Only the `plugin.json` approach is documented.
- **Recommended fix**: Add a note that `.mcp.json` at plugin root is also a valid location for
  plugin MCP server configuration.

### L7 — `argumentHint` and `alwaysLoadSkills` fields need verification (companion to M10)

- **File**: `plugins/plugin-creator/skills/agent-creator/references/agent-schema.md`
- Addressed in M10. Listed here for completeness — resolution depends on doc verification.

### L8 — `claude-skills-overview-2026` hook field events may be incomplete

- **File**: `plugins/plugin-creator/skills/claude-skills-overview-2026/SKILL.md`
- **What's wrong**: The `hooks` field in the frontmatter table lists only `PreToolUse`,
  `PostToolUse`, `Stop` as available events — may be stale (see C3, all events are supported).
- **Recommended fix**: After C3 is resolved, update this table to reflect all events are
  supported.

### L9 — `audit-skill-completeness` checklist has no headless compatibility check

- **File**: `plugins/plugin-creator/skills/audit-skill-completeness/references/skill-completeness-checklist.md`
  (lines ~153, 185)
- **What's wrong**: Checklist verifies `disable-model-invocation` and `user-invocable` fields
  but has no item checking whether user-invocable skills are tested for `-p`/headless
  incompatibility.
- **Recommended fix**: Add a checklist item: "If `user-invocable: true`, verify the skill
  includes a note that it is unavailable in `-p`/Agent SDK mode."

---

## Recommended Fix Order

Source: `.claude/reports/plugin-creator-audit-summary.md` (2026-03-17), Recommended Fix Order section.

1. **`hooks-core-reference/SKILL.md`** — highest blast radius; most other hook skills are
   derived from or cross-referenced with it. Fix `Task` → `Agent` (C1), fix `SubagentStart` and
   `SubagentStop` matcher flags (C2), fix `SessionEnd` matcher (H2), add 9 new events (H5), add
   `type: "http"` and `type: "agent"` handler types (H6), add `once`/`statusMessage`/`async`
   fields (M5), resolve `Setup` event status (M1).

2. **`hooks-patterns/SKILL.md` + `hook-creator/SKILL.md`** — immediately actionable, high user
   impact. Fix frontmatter events claim (C3), fix command hook timeout 60s → 600s (H1), add 9
   missing events to flowchart (H5), add HTTP and agent hook types (H6), fix `SubagentStart` in
   no-matcher list (C2), add `once` field (M6).

3. **`hooks-guide/references/inline-agent-hooks.md`** — single sentence addition; prevents
   silent runtime failures for plugin authors. Add `mcpServers` plugin restriction note (H3).

4. **`${CLAUDE_SKILL_DIR}` across 4 files** — affects every skill author; simple additions.
   Fix in `claude-skills-overview-2026/SKILL.md`, `skill-creator/SKILL.md`,
   `skill-creator/references/claude-code-skills-official.md`,
   `plugin-creator/references/advanced-features.md` (H7).

5. **`plugin-creator/SKILL.md`** — fix `agents` field type `string|array` → `array` (H4).

6. **`agents/subagent-refactorer.md`** — fix stale model reference `Opus 4.1` → `Opus 4.5/4.6`
   and remove pricing annotation (H13, M14).

7. **All remaining MEDIUM issues** in order: M1 (`Setup` verification), M2 (model full-ID),
   M3 (SubagentStop schema), M4 (new event output schemas), M7 (settings.json schema), M8/M9
   (advanced-features.md inconsistencies), M10 (unverified schema fields), M11–M16 (remaining
   per-file fixes), M17–M18 (URL updates).

8. **All LOW issues** in order: L1–L9.

---

## Source Reports

- [./../../reports/audit-agents-subagents.md](./../../reports/audit-agents-subagents.md) — Agent
  frontmatter audit (8 agents)
- [./../../reports/audit-skills-plugins.md](./../../reports/audit-skills-plugins.md) — Skills
  and plugins docs audit (15+ skills, reference files)
- [./../../reports/audit-teams-headless-scheduled.md](./../../reports/audit-teams-headless-scheduled.md)
  — Agent teams, headless mode, and scheduled tasks audit
- [./../../reports/audit-hooks-mcp.md](./../../reports/audit-hooks-mcp.md) — Hooks and MCP
  references audit
