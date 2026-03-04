# Audit: plugin-creator Skill Knowledge

Sources consulted:
- `/root/.claude/skills/plugin-creator/SKILL.md` (loaded via `Skill(skill="plugin-creator")`)
- `/root/.claude/skills/plugin-creator/references/advanced-features.md`

---

## Q1: What is a plugin?

**GIVEN**: The skill defines a plugin as a directory containing a required `.claude-plugin/` metadata directory (which holds only `plugin.json`) plus optional components at the plugin root: agents, skills, hooks, MCP server definitions, scripts, LICENSE, and README. Claude Code copies plugins to a cache directory rather than using them in-place.

Directory structure from the skill:

```text
my-plugin/
├── .claude-plugin/           # REQUIRED: metadata directory
│   └── plugin.json          # REQUIRED: only file in .claude-plugin/
├── agents/                   # Optional: agent definitions (.md)
├── skills/                   # Optional: skill directories
│   └── my-skill/
│       ├── SKILL.md
│       └── references/      # Optional: detailed reference docs
├── hooks/                    # Optional: hook configurations
│   └── hooks.json
├── .mcp.json                # Optional: MCP server definitions
├── scripts/                 # Optional: helper scripts
├── LICENSE
└── README.md
```

**WHEN**: Presented in "Phase 3: Implementation" under "Manual Implementation Structure" and in "Plugin Runtime Mechanics". Caching behavior is in `references/advanced-features.md` under "Plugin Caching Behavior".

**THEN**: Create a plugin directory matching this structure. Ensure `.claude-plugin/` contains only `plugin.json` and all other components live at the plugin root, not inside `.claude-plugin/`. Use `${CLAUDE_PLUGIN_ROOT}` for all internal path references to account for the cache copy location.

---

## Q2: What are the capabilities of a plugin?

**GIVEN**: The skill documents these plugin capabilities:

- **Skills** — `SKILL.md` files delivering instructions to Claude when invoked
- **Agents** — `.md` agent definition files for specialized sub-agent types
- **Hooks** — Event handlers responding to Claude Code events (PreToolUse, PostToolUse, PostToolUseFailure, Stop, UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, Setup, PreCompact); three hook types: `command`, `prompt`, `agent`
- **MCP servers** — External tool integration via Model Context Protocol
- **LSP servers** — Language Server Protocol servers providing diagnostics, go-to-definition, find-references, and type information
- **Dynamic context injection** — `!`command`` syntax runs shell commands before skill content is sent to Claude, replacing the placeholder with output
- **String substitutions** — `$ARGUMENTS`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_PLUGIN_ROOT}`
- **Subagent isolation** — `context: fork` frontmatter runs a skill in an isolated subagent
- **Visual output** — Bundled scripts in any language generating HTML output opened in browser
- **Extended thinking** — Including "ultrathink" anywhere in skill content enables extended thinking mode
- **Output styles** — `outputStyles` field in plugin.json

**WHEN**: Distributed across the SKILL.md "Plugin Runtime Mechanics", "Phase 3: Implementation", plugin.json schema table, and `references/advanced-features.md` (one section per feature).

**THEN**: Select which capabilities the plugin needs based on its purpose, then implement each component following the documented patterns for that capability.

---

## Q3: Who is the user of a plugin?

**GIVEN**: The skill does not define a named user persona. It implicitly distinguishes two audiences:

1. **Plugin consumers** — people or agents in a Claude Code session who invoke skills, receive hook enforcement, and use MCP tools. The skill states: "A `CLAUDE.md` inside a plugin directory informs Claude when it is doing development work inside that plugin directory. It has zero effect on plugin users because Claude runs in the user's project directory, not the plugin source directory."

2. **Plugin developers** — who work inside the plugin source directory during development and read the plugin's internal `CLAUDE.md`.

The RT-ICA prerequisite check requires "Target users | Requires: Who will use this | Why: Shapes UX decisions" before building begins.

**WHEN**: The consumer/developer distinction appears in "Plugin Runtime Mechanics". The target users requirement appears in "Phase 0: RT-ICA Prerequisite Check".

**THEN**: Identify target users before building. Content that must reach plugin consumers must go into SKILL.md, hooks, or agent definitions — not into `CLAUDE.md` inside the plugin directory.

---

## Q4: What systems or tools can load these plugins?

**GIVEN**: The skill names **Claude Code** as the system that loads plugins. All official documentation URLs use `code.claude.com`. Distribution is via the Claude Code plugin marketplace (`https://code.claude.com/docs/en/plugin-marketplaces`). No other system is mentioned as able to load these plugins.

**WHEN**: Referenced throughout via official docs URLs (`code.claude.com/docs/en/plugins-reference.md`, `code.claude.com/docs/en/skills.md`) and the phrase "Claude Code" in "Plugin Runtime Mechanics".

**THEN**: Target Claude Code as the sole runtime. Distribute via the Claude Code plugin marketplace.

---

## Q5: Where is data stored in plugins?

**GIVEN**: The skill identifies these storage locations:

1. **Plugin cache directory** — Claude Code copies the plugin here at install/load time. `${CLAUDE_PLUGIN_ROOT}` always resolves to the cached location. External files outside the plugin directory are not copied (symlinks are followed during copy).

2. **Plugin root** — Source files at development time: `plugin.json`, skill directories, agent files, hooks, `.mcp.json`, scripts.

3. **Work artifact directory** — `.claude/plan/{plugin-name}/` for orchestration artifacts created during plugin development:

```text
.claude/plan/{plugin-name}/
├── PROJECT.md
├── REQUIREMENTS.md
├── STATE.md
├── discuss-CONTEXT.md
├── research-FINDINGS.md
├── design-PLAN.md
├── validation-REPORT.md
└── SUMMARY.md
```

4. **MCP server data** — The MCP example shows `"DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"`, placing data inside the plugin's cached directory.

5. **Session logs** — `${CLAUDE_SESSION_ID}` can be used in log paths (e.g., `logs/${CLAUDE_SESSION_ID}.log`).

**WHEN**: Plugin caching is in `references/advanced-features.md` under "Plugin Caching Behavior". Artifact storage is in "Artifact System". MCP data path example is in "MCP Server Integration".

**THEN**: Use `${CLAUDE_PLUGIN_ROOT}` in all hook command paths, MCP server commands, args, and env values to ensure correct resolution from the cache location.

---

## Q6: What environment variables are available in plugins?

**GIVEN**: The skill documents these variables available in skill content and plugin configuration:

| Variable | Description |
|---|---|
| `$ARGUMENTS` | Text passed when invoking the skill |
| `${CLAUDE_SESSION_ID}` | Current session ID (for logging, correlating output) |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory (the cached copy) |

MCP server configuration supports an `env` block for arbitrary environment variables passed to MCP server processes (shown with `"DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"`).

Hooks use `${CLAUDE_PLUGIN_ROOT}` in command paths: `"${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"`. The skill notes: "Always use `${CLAUDE_PLUGIN_ROOT}` for script paths — it resolves to the correct cached location."

**WHEN**: String substitutions documented in `references/advanced-features.md` under "String Substitutions". MCP env block under "MCP Server Integration". Hook path usage under "Hook Configuration".

**THEN**: Use `${CLAUDE_PLUGIN_ROOT}` in all hook and MCP path references. Use `$ARGUMENTS` in SKILL.md to receive user input. Use `${CLAUDE_SESSION_ID}` for per-session log file naming or correlation.

---

## Q7: How many ways can an MCP server be made available to an agent?

**GIVEN**: The skill documents **two ways** to define MCP servers in a plugin:

1. **Separate `.mcp.json` file** at the plugin root
2. **Inline in `plugin.json`** via the `mcpServers` field

From the plugin.json schema table: `mcpServers | string\|object | No | MCP config path or inline`

Example from `references/advanced-features.md`:

```json
{
  "mcpServers": {
    "plugin-database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    }
  }
}
```

No other mechanism for making MCP servers available is documented in the skill.

**WHEN**: Plugin.json schema table in "Phase 3: Implementation" and `references/advanced-features.md` under "MCP Server Integration".

**THEN**: Choose either a separate `.mcp.json` file or an inline `mcpServers` block in `plugin.json` to bundle an MCP server with the plugin.

---

## Q8: How are tools assigned to an agent?

**GIVEN**: Tools are assigned via the `allowed-tools` frontmatter field in SKILL.md — a **comma-separated string** (not an array). From the frontmatter table: "Tools without permission prompts".

Example:

```yaml
---
description: Generate interactive tree visualization of codebase
allowed-tools: Bash(python:*)
---
```

The skill also documents inherent tool access levels by subagent type, from `references/advanced-features.md`:

- `Explore` — Read-only tools (Haiku-based, verbatim retrieval only)
- `Plan` — Architecture and planning tasks with reasoning
- `general-purpose` — Full tool access with reasoning

**WHEN**: `allowed-tools` is in the SKILL.md Frontmatter table in "Phase 3: Implementation". The CRITICAL note states: "YAML frontmatter fields like `allowed-tools` MUST be comma-separated strings, NOT arrays." Subagent tool access levels are in `references/advanced-features.md` under "Running Skills in Subagents".

**THEN**: Add `allowed-tools: Tool1, Tool2` to SKILL.md frontmatter to grant those tools without permission prompts. For subagents, select the `agent` type matching the required tool access level.

---

## Q9: How are tools hidden from an agent?

**GIVEN**: The skill documents two invocation-control fields that affect skill visibility, but not a mechanism specifically described as "hiding tools":

- `user-invocable: false` — hides the skill from the `/` menu (user-facing discovery)
- `disable-model-invocation: true` — prevents Claude from auto-loading the skill

From `references/advanced-features.md` under "Skill Invocation Control":

| Frontmatter | User | Claude | Use Case |
|---|---|---|---|
| (default) | Yes | Yes | Most skills |
| `disable-model-invocation: true` | Yes | No | Workflows with side effects |
| `user-invocable: false` | No | Yes | Background knowledge only |

Subagent type selection implicitly restricts available tools: `Explore` provides only read-only tools.

**WHEN**: `user-invocable` and `disable-model-invocation` are in the SKILL.md frontmatter table and in `references/advanced-features.md` under "Skill Invocation Control".

**THEN**: NOT COVERED BY THIS SKILL — no explicit mechanism for hiding specific tools from an agent is documented. The available controls are skill-level invocation control and subagent type selection.

---

## Q10: How are tools denied from use from an agent?

**GIVEN**: The skill does not document an explicit tool-denial mechanism (no `denied-tools` or `blocked-tools` field). The `allowed-tools` field grants pre-approved tool use but does not document a deny list. Tools not listed in `allowed-tools` require permission prompts but are not explicitly denied.

The closest documented controls:

- **Subagent type `Explore`** — inherently read-only, write tools unavailable
- **`disable-model-invocation: true`** — prevents Claude from auto-loading the skill, preventing that skill's `allowed-tools` from applying
- **Omitting `allowed-tools`** — tools require permission prompts (friction, not denial)

**WHEN**: These controls appear in `references/advanced-features.md` under "Skill Invocation Control" and "Running Skills in Subagents".

**THEN**: NOT COVERED BY THIS SKILL — no explicit tool denial or blocklist mechanism is documented.

---

## Q11: What are the ways agents in a plugin are allowed to do tasks without permission requests but pre-approved within the scope of the plugin?

**GIVEN**: The skill documents two mechanisms for pre-approving actions without permission requests:

1. **`allowed-tools` frontmatter field in SKILL.md** — lists tools the skill may use without triggering permission prompts. From the frontmatter table: "Tools without permission prompts."

Example:

```yaml
---
allowed-tools: Bash(python:*)
---
```

2. **Hooks in `hooks.json`** — execute automatically on trigger events without user approval. The hook example shows a `command` hook running `${CLAUDE_PLUGIN_ROOT}/scripts/format.sh` automatically on every Write or Edit tool use, with no permission prompt.

From `references/advanced-features.md` under "Hook Configuration", hooks fire on events including PreToolUse, PostToolUse, PostToolUseFailure, Stop, UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, Setup, and PreCompact.

**WHEN**: `allowed-tools` is in the SKILL.md frontmatter table and the Visual Output example. Hook auto-execution is in `references/advanced-features.md` under "Hook Configuration".

**THEN**: Add specific tools to `allowed-tools` in SKILL.md for pre-approved tool use within that skill's scope. Configure `hooks.json` for pre-approved automated script or agent execution on tool and session events.

---

## Q12: How is the plugin namespace defined?

**GIVEN**: The skill addresses namespace in three ways:

1. **Plugin name** — the `name` field in `plugin.json`: "Kebab-case identifier, max 64 chars". This is the top-level namespace component.

2. **Skill namespacing** — Skills are referenced using the format `plugin-name:skill-name`. The skill uses this format throughout for agent delegation (e.g., `subagent_type="plugin-creator:plugin-assessor"`, `subagent_type="plugin-creator:contextual-ai-documentation-optimizer"`).

3. **Skills auto-discovery (Mode A) vs explicit allowlist (Mode B)** — from the task spec in "Phase 2: Design": "Do NOT add a skills field — skills under `./skills/` are auto-discovered by Claude Code (Mode A). Add a skills field only when explicitly opting into manual allowlist mode (Mode B)." This means the namespace derives from the plugin name and the skill directory name under `skills/`.

4. **Path behavior** — from `references/advanced-features.md` under "Path Behavior Rules": "Custom paths SUPPLEMENT default directories, they don't REPLACE them."

**WHEN**: Plugin `name` field is in the plugin.json schema table. Namespaced skill references (`plugin:skill`) appear throughout agent delegation examples. Mode A/Mode B is in the task spec in "Phase 2: Design". Path behavior is in `references/advanced-features.md`.

**THEN**: Set the `name` field in `plugin.json` using kebab-case. Skills are auto-namespaced as `{plugin-name}:{skill-directory-name}` from the `skills/` directory. Add an explicit `skills` field in `plugin.json` only when opting into allowlist mode (Mode B).

---

## Q13: What scripting languages should be preferred when the script is shipping with the plugin as a hook or as MCP or tooling?

**GIVEN**: The skill does not state an explicit language preference for hook scripts or MCP servers.

- **Hook example** — shows a shell script: `"${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"` with `.sh` extension.
- **MCP server example** — shows a binary `servers/db-server` with no language specified.
- **Visual output scripts** — `references/advanced-features.md` states: "Skills can bundle scripts in ANY language to generate visual output." The example uses Python (`visualize.py`).
- **Bundled validator tooling** — The "Tooling" section states: "Scripts use PEP 723 inline metadata — dependencies install automatically via `uv run`." This applies to the plugin creation tooling scripts (`create_plugin.py`, `plugin_validator.py`), not specifically to hooks or MCP servers.

**WHEN**: PEP 723/`uv run` reference is in the "Tooling" section. "ANY language" for visual output scripts is in `references/advanced-features.md` under "Visual Output — Bundled Scripts". Hook script example (`.sh`) is in "Hook Configuration" in `references/advanced-features.md`.

**THEN**: NOT COVERED BY THIS SKILL — no explicit language preference is stated for hook scripts or MCP servers. Visual output scripts may be in any language. The plugin's own bundled tooling scripts use Python with PEP 723 inline metadata via `uv run`. Hook examples show shell scripts.
