# Audit: plugin-creator Skill Knowledge

Sources consulted:
- `/root/.claude/skills/plugin-creator/SKILL.md` (loaded via `Skill(skill="plugin-creator")`)
- `/root/.claude/skills/plugin-creator/references/advanced-features.md`

---

## Q1: What is a plugin?

**GIVEN**: A plugin is a deployable unit installed into Claude Code that delivers capabilities to users. It is a directory containing a `.claude-plugin/plugin.json` manifest and optional components (skills, agents, hooks, MCP servers, LSP servers, scripts). Claude Code copies the plugin to a cache directory rather than using it in-place.

The skill defines this structure:

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

**WHEN**: Presented in the "Implementation Phase" section under "Manual Implementation Structure" and in the "Plugin Runtime Mechanics" section. The caching behavior is documented in `references/advanced-features.md` under "Plugin Caching Behavior".

**THEN**: The reader creates a plugin directory matching this structure, ensuring `.claude-plugin/` contains only `plugin.json`, and places all other components at the plugin root.

---

## Q2: What are the capabilities of a plugin?

**GIVEN**: The skill lists these plugin capabilities:

- **Skills** — `SKILL.md` files that deliver instructions to Claude when invoked via `/skill-name`
- **Agents** — `.md` agent definition files for specialized sub-agent types
- **Hooks** — Event handlers responding to Claude Code events (PreToolUse, PostToolUse, PostToolUseFailure, Stop, UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, Setup, PreCompact)
- **MCP servers** — External tool integration via the Model Context Protocol
- **LSP servers** — Language Server Protocol servers for code intelligence (diagnostics, go-to-definition, find-references, type info)
- **Dynamic context injection** — `!`command`` syntax runs shell commands before skill content is sent to Claude
- **String substitutions** — `$ARGUMENTS`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_PLUGIN_ROOT}`
- **Subagent isolation** — `context: fork` runs a skill in an isolated subagent
- **Visual output** — Bundled scripts in any language generating HTML output
- **Extended thinking** — Including "ultrathink" in skill content enables extended thinking mode
- **Output styles** — `outputStyles` field in plugin.json

**WHEN**: Distributed across the main SKILL.md ("Plugin Runtime Mechanics", "Implementation Phase", plugin.json schema table) and `references/advanced-features.md` (each feature in its own section).

**THEN**: The reader selects which capabilities to include based on the plugin's purpose, then implements each component following the documented patterns.

---

## Q3: Who is the user of a plugin?

**GIVEN**: The skill does not explicitly define a "user" persona. The Discussion Phase section distinguishes between two audiences implicitly:

1. **Plugin consumers** — people or agents who invoke skills, receive hook enforcement, and use MCP tools in their Claude Code session. The "Plugin Runtime Mechanics" section states: "A `CLAUDE.md` inside a plugin directory informs Claude when it is doing development work inside that plugin directory. It has zero effect on plugin users because Claude runs in the user's project directory, not the plugin source directory."

2. **Plugin developers** — who work inside the plugin directory during development sessions and read the plugin's internal `CLAUDE.md`.

The RT-ICA prerequisite check includes "Target users | Requires: Who will use this | Why: Shapes UX decisions" as a required condition, indicating the plugin creator must define their target users before building.

**WHEN**: The consumer/developer distinction appears in "Plugin Runtime Mechanics". The target users requirement appears in "Phase 0: RT-ICA Prerequisite Check".

**THEN**: Before building, the reader identifies their target users. Content that must reach plugin consumers goes into SKILL.md, hooks, or agent definitions — not into `CLAUDE.md` inside the plugin directory.

---

## Q4: What systems or tools can load these plugins?

**GIVEN**: The skill names **Claude Code** as the system that loads plugins. Specific references:

- "This skill orchestrates specialized agents through a comprehensive plugin creation workflow" (implied Claude Code context)
- Plugin.json schema source: `https://code.claude.com/docs/en/plugins-reference.md`
- Skills source: `https://code.claude.com/docs/en/skills.md`
- Distribution via **Plugin Marketplaces**: `https://code.claude.com/docs/en/plugin-marketplaces`

The skill does not name any other system that loads plugins.

**WHEN**: Referenced throughout via official docs URLs and the phrase "Claude Code" in "Plugin Runtime Mechanics" and throughout the workflow phases.

**THEN**: The reader targets Claude Code as the sole runtime. Distribution is via the Claude Code plugin marketplace.

---

## Q5: Where is data stored in plugins?

**GIVEN**: The skill identifies several storage locations:

1. **Plugin cache directory** — Claude Code copies the plugin here; `${CLAUDE_PLUGIN_ROOT}` always resolves to this cached location. External files outside the plugin directory are NOT copied (symlinks are followed during copy).

2. **Plugin root** — Source files at development time: `plugin.json`, skill directories, agent files, hooks, `.mcp.json`, scripts.

3. **Work artifact directory** — `.claude/plan/{plugin-name}/` for orchestration artifacts during plugin creation:

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

4. **MCP server data** — Example shows `"DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"`, placing data inside the plugin's cached directory.

5. **Runtime context** — `${CLAUDE_SESSION_ID}` can be used in log paths (e.g., `logs/${CLAUDE_SESSION_ID}.log`).

**WHEN**: Plugin caching is documented in `references/advanced-features.md` under "Plugin Caching Behavior". Artifact storage is in the "Artifact System" section. MCP data path example is in "MCP Server Integration".

**THEN**: The reader uses `${CLAUDE_PLUGIN_ROOT}` for all paths to scripts and data files within hooks and MCP configs to ensure correct resolution from the cache location.

---

## Q6: What environment variables are available in plugins?

**GIVEN**: The skill documents these variables available in skill content and configuration:

| Variable | Description |
|---|---|
| `$ARGUMENTS` | Text passed when invoking the skill |
| `${CLAUDE_SESSION_ID}` | Current session ID (for logging, correlating output) |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory (the cached copy) |

Additionally, MCP server configuration supports an `env` block for passing arbitrary environment variables to MCP server processes (shown in the MCP integration example with `"DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"`).

The hook example also uses `${CLAUDE_PLUGIN_ROOT}` in command paths: `"${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"`.

**WHEN**: String substitutions are documented in `references/advanced-features.md` under "String Substitutions". MCP env block appears under "MCP Server Integration". Hook path usage appears under "Hook Configuration". The note "Always use `${CLAUDE_PLUGIN_ROOT}` for script paths — it resolves to the correct cached location" appears in "Hook Configuration".

**THEN**: The reader uses `${CLAUDE_PLUGIN_ROOT}` in all hook command paths and MCP server commands/args/env to ensure correct resolution from the cache. `$ARGUMENTS` is used in SKILL.md to receive user-supplied input. `${CLAUDE_SESSION_ID}` is used for per-session logging or correlation.

---

## Q7: How many ways can an MCP server be made available to an agent?

**GIVEN**: The skill documents **two ways** to define MCP servers in a plugin:

1. **Separate `.mcp.json` file** at plugin root
2. **Inline in `plugin.json`** via the `mcpServers` field

From the plugin.json schema table: `mcpServers | string\|object | No | MCP config path or inline`

The MCP example in `references/advanced-features.md` shows the inline/file config structure:

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

The skill does not document any other mechanism for making MCP servers available.

**WHEN**: Documented in the plugin.json schema table in "Implementation Phase" and in `references/advanced-features.md` under "MCP Server Integration".

**THEN**: The reader chooses either a separate `.mcp.json` file or an inline `mcpServers` block in `plugin.json` to bundle an MCP server with the plugin.

---

## Q8: How are tools assigned to an agent?

**GIVEN**: Tools are assigned to a skill (and thus to the session or subagent using it) via the `allowed-tools` frontmatter field in SKILL.md. The field is a **comma-separated string** (not an array).

From the SKILL.md frontmatter table:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `allowed-tools` | comma-separated string | none | Tools without permission prompts |

Example from the Visual Output section:

```yaml
---
description: Generate interactive tree visualization of codebase
allowed-tools: Bash(python:*)
---
```

The skill also notes that subagent types have inherent tool access levels:
- `Explore` — Read-only tools
- `Plan` — Architecture and planning tasks with reasoning
- `general-purpose` — Full tool access with reasoning

**WHEN**: `allowed-tools` is documented in the SKILL.md Frontmatter table in "Implementation Phase" and in the "SKILL.md Frontmatter" section. The CRITICAL note states: "YAML frontmatter fields like `allowed-tools` MUST be comma-separated strings, NOT arrays." Subagent tool access levels appear in `references/advanced-features.md` under "Running Skills in Subagents".

**THEN**: The reader adds `allowed-tools: Tool1, Tool2` to SKILL.md frontmatter to grant those tools without permission prompts. For subagents, the reader selects the appropriate `agent` type matching the required tool access level.

---

## Q9: How are tools hidden from an agent?

**GIVEN**: The skill does not document a mechanism specifically for hiding tools from an agent. The `user-invocable: false` frontmatter field hides a skill from the `/` menu (user-facing), and `disable-model-invocation: true` prevents Claude from auto-loading a skill — but neither explicitly hides MCP tools or built-in tools from an agent.

The subagent type selection implicitly restricts tools: using `Explore` gives read-only tools, preventing write tools from being available in that subagent context.

**WHEN**: `user-invocable` and `disable-model-invocation` are documented in the SKILL.md frontmatter table and in `references/advanced-features.md` under "Skill Invocation Control". Subagent tool restrictions appear under "Running Skills in Subagents".

**THEN**: NOT COVERED BY THIS SKILL (no explicit tool-hiding mechanism documented beyond subagent type selection and skill invocation control).

---

## Q10: How are tools denied from use from an agent?

**GIVEN**: The skill does not document an explicit tool-denial mechanism (e.g., a `denied-tools` or `blocked-tools` field). The `allowed-tools` field grants tools without permission prompts but does not document a deny list.

The closest documented controls are:

- **`disable-model-invocation: true`** — prevents Claude from auto-loading the skill (preventing skill-scoped `allowed-tools` from applying)
- **Subagent type selection** — `Explore` agent type is read-only, inherently denying write tools
- **No `allowed-tools` entry** — tools not listed require permission prompts (implicit friction, not explicit denial)

**WHEN**: These controls appear in `references/advanced-features.md` under "Skill Invocation Control" and "Running Skills in Subagents".

**THEN**: NOT COVERED BY THIS SKILL (no explicit tool denial/blocklist mechanism is documented).

---

## Q11: What are the ways agents in a plugin are allowed to do tasks without permission requests but pre-approved within the scope of the plugin?

**GIVEN**: The skill documents one explicit mechanism for pre-approving actions without permission requests:

**`allowed-tools` frontmatter field** in SKILL.md — lists tools the skill may use without triggering permission prompts. From the frontmatter table: "Tools without permission prompts".

Example showing Bash pre-approved for python execution:

```yaml
---
allowed-tools: Bash(python:*)
---
```

Hooks also execute automatically without permission requests when their trigger events fire — the `hooks.json` configuration pre-approves script execution on events like `PostToolUse`, `PreToolUse`, `SessionStart`, etc.

From the hook example: a `command` hook runs `${CLAUDE_PLUGIN_ROOT}/scripts/format.sh` automatically on every Write or Edit without user approval.

**WHEN**: `allowed-tools` is documented in the SKILL.md frontmatter table and the Visual Output example. Hook auto-execution is documented in `references/advanced-features.md` under "Hook Configuration".

**THEN**: The reader adds specific tools to `allowed-tools` in SKILL.md for pre-approved tool use within that skill's scope, and configures `hooks.json` for pre-approved automated script execution on tool/session events.

---

## Q12: How is the plugin namespace defined?

**GIVEN**: The skill addresses namespace in two ways:

1. **Plugin name** — defined by the `name` field in `plugin.json`: "Kebab-case identifier, max 64 chars". This is the top-level namespace identifier.

2. **Skill namespacing** — Skills are referenced as `plugin-name:skill-name`. The skill references this format throughout (e.g., `subagent_type="plugin-creator:plugin-assessor"`, `subagent_type="plugin-creator:contextual-ai-documentation-optimizer"`).

3. **Skills auto-discovery vs explicit listing** — The `plugin.json` task spec note states: "Do NOT add a skills field — skills under `./skills/` are auto-discovered by Claude Code (Mode A). Add a skills field only when explicitly opting into manual allowlist mode (Mode B)." This implies the namespace is determined by the plugin name and the skill directory name beneath `skills/`.

4. **Path behavior** — "Custom paths SUPPLEMENT default directories, they don't REPLACE them." Custom `skills` paths in plugin.json add to the `skills/` directory rather than replacing it.

**WHEN**: Plugin name field is in the plugin.json schema table. Namespaced skill references appear throughout the SKILL.md in agent delegation examples. The Mode A/Mode B note appears in the task spec example in "Phase 2: Design". Path behavior is documented in `references/advanced-features.md` under "Path Behavior Rules".

**THEN**: The reader sets the `name` field in `plugin.json` using kebab-case. Skills are auto-discovered from `skills/` using the format `{plugin-name}:{skill-directory-name}`. The `skills` field in plugin.json is added only when opting into explicit allowlist control.

---

## Q13: What scripting languages should be preferred when the script is shipping with the plugin as a hook or as MCP or tooling?

**GIVEN**: The skill states: "Scripts use PEP 723 inline metadata — dependencies install automatically via `uv run`." This appears in the "Tooling" section describing the bundled validator scripts (`create_plugin.py`, `plugin_validator.py`).

The Visual Output section states: "Skills can bundle scripts in ANY language to generate visual output." It shows a Python example (`visualize.py`).

The CLAUDE.md project instructions (in scope as project context) state: "All Python via `uv`, `uv run`, `uv run python -c 'some python code'`."

No explicit preference statement (e.g., "prefer Python over bash") appears in the plugin-creator skill content itself for hook scripts or MCP servers. Hook examples show shell scripts (`.sh`). MCP server examples show a binary (`servers/db-server`) with no language specified.

**WHEN**: PEP 723 / `uv run` reference appears in the "Tooling" section. "ANY language" for scripts appears in `references/advanced-features.md` under "Visual Output — Bundled Scripts". Hook script example (`.sh`) appears under "Hook Configuration".

**THEN**: NOT COVERED BY THIS SKILL with an explicit preference statement for hooks or MCP. The skill states scripts can be in any language for visual output. For the bundled validator tooling, Python with PEP 723 inline metadata (run via `uv run`) is used. Hook examples show shell scripts. No preference ordering is stated.
