# Plugin Lifecycle Skill — Knowledge Audit

Answers derived exclusively from the plugin-lifecycle skill (`plugins/plugin-creator/skills/plugin-lifecycle/SKILL.md`), the plugin-creator CLAUDE.md loaded alongside it, and the reference skills it composes: `claude-plugins-reference-2026`, `claude-skills-overview-2026`, `hooks-guide` (including `inline-agent-hooks.md` and `claude-code.md` references).

---

## Q1: What is a plugin?

**GIVEN**: Plugins extend Claude Code with skills, agents, hooks, MCP servers, and LSP servers. A plugin is a directory containing a `.claude-plugin/plugin.json` manifest file plus any combination of those components. The `plugin.json` file defines the plugin's metadata and configuration, and the only required field is `name` (kebab-case, unique identifier). The plugin-lifecycle skill describes a plugin as something that goes through seven phases — assess, research, design, create, debug, optimize, verify — to become "marketplace-ready."

**WHEN**: This definition is presented in the `claude-plugins-reference-2026` skill opening section ("Plugins extend Claude Code with skills, agents, hooks, MCP servers, and LSP servers") and in the plugin-lifecycle SKILL.md frontmatter description ("Orchestrate the full plugin development lifecycle from blank canvas to marketplace-ready").

**THEN**: The reader understands a plugin is a self-contained, distributable package of Claude Code extensions identified by a `.claude-plugin/plugin.json` manifest, containing any combination of skills, agents, hooks, MCP servers, and LSP servers.

---

## Q2: What are the capabilities of a plugin?

**GIVEN**: Plugins can include any combination of six component types:

1. **Skills** — `SKILL.md` files that deliver instructions to Claude when invoked via `/skill-name`. Can include dynamic context injection (`!`command`` syntax), string substitutions (`$ARGUMENTS`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_PLUGIN_ROOT}`), subagent isolation (`context: fork`), and extended thinking (including "ultrathink").
2. **Agents** — `.md` agent definition files for specialized sub-agent types with configurable models, tools, MCP servers, hooks, and permission modes.
3. **Hooks** — Event handlers responding to Claude Code lifecycle events: PreToolUse, PostToolUse, PostToolUseFailure, Stop, UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, Setup, PreCompact, Notification, PermissionRequest.
4. **MCP servers** — External tool integration via the Model Context Protocol, configured in `.mcp.json` or inline in `plugin.json`.
5. **LSP servers** — Language Server Protocol servers for code intelligence (diagnostics, go-to-definition, find-references, type info), configured in `.lsp.json` or inline in `plugin.json`.
6. **Output styles** — Custom output formatting via the `outputStyles` field in `plugin.json`.

Additional runtime capabilities include: visual output via bundled scripts generating HTML, plugin caching (copied to cache directory for execution), and marketplace distribution.

**WHEN**: Component types are enumerated in the `claude-plugins-reference-2026` "Plugin Components Overview" table and the plugin-creator CLAUDE.md "Core Capabilities" section. Advanced features (dynamic context, string substitutions, subagent isolation) are documented in `claude-skills-overview-2026`.

**THEN**: The reader selects which capabilities to include based on the plugin's purpose and designs components accordingly during Phase 3 (Design) and Phase 4 (Create) of the lifecycle.

---

## Q3: Who is the user of a plugin?

**GIVEN**: The skill identifies multiple user categories:

1. **End users (developers)** — Install plugins via `claude plugin install`, invoke skills with `/name`, interact with agents. Plugins are installed at user, project, local, or managed scope.
2. **Plugin authors/developers** — Create plugins through the lifecycle phases (assess, research, design, create, debug, optimize, verify). The plugin-lifecycle skill itself is the primary tool for this audience.
3. **Team leads / project maintainers** — Configure plugins in `.claude/settings.json` for team sharing via version control (project scope).
4. **Enterprise administrators** — Control plugin sources via `strictKnownMarketplaces` in managed settings, enforce organization-wide hooks with `allowManagedHooksOnly`.
5. **Claude (the AI agent)** — Can auto-invoke skills based on task context when `disable-model-invocation` is not set to `true`.

The plugin-creator CLAUDE.md also notes the distinction between plugin consumers (who invoke skills and receive hook enforcement in their Claude Code session) and plugin developers (who work inside the plugin directory during development).

**WHEN**: Installation scopes are defined in "Plugin Installation Scopes" of `claude-plugins-reference-2026`. Enterprise features are in its "Enterprise Features" section. Invocation control (human vs. Claude) is in "Invocation Control" of `claude-skills-overview-2026`. The consumer/developer distinction appears in the plugin-creator CLAUDE.md under "Plugin System Fundamentals > Plugin Caching."

**THEN**: The reader understands that plugins serve developers, teams, and enterprises at different scopes, and that both human users and Claude are consumers of plugin capabilities. Content for plugin consumers goes into SKILL.md, hooks, or agent definitions — not into CLAUDE.md inside the plugin directory.

---

## Q4: What systems or tools can load these plugins?

**GIVEN**: **Claude Code** is the sole system documented as loading plugins. Specific evidence:

- The `claude plugin install`, `claude plugin validate`, `claude plugin enable/disable` CLI commands all operate within Claude Code.
- Plugin.json schema source URL: `https://code.claude.com/docs/en/plugins-reference.md`
- Skills source URL: `https://code.claude.com/docs/en/skills.md`
- Distribution is via Claude Code Plugin Marketplaces.
- Testing without installation: `claude --plugin-dir ./my-plugin` loads a plugin for the current session only.

No other system, IDE, or tool is documented as being able to load these plugins.

**WHEN**: Referenced throughout the `claude-plugins-reference-2026` skill via official docs URLs, CLI command references, and in the plugin-creator CLAUDE.md "CLI Commands Reference" section.

**THEN**: The reader targets Claude Code as the sole runtime for plugin consumption. Distribution is via the Claude Code plugin marketplace system.

---

## Q5: Where is data stored in plugins?

**GIVEN**: The skill identifies these storage locations:

**Plugin structure (author-side):**

- `.claude-plugin/plugin.json` — the required manifest file
- `commands/` — legacy command location (use `skills/` instead)
- `agents/` — agent definition files
- `skills/` — skills with `<name>/SKILL.md` structure
- `hooks/hooks.json` — hook configuration
- `.mcp.json` — MCP server definitions
- `.lsp.json` — LSP server configurations
- `scripts/` — hook and utility scripts

**Plugin lifecycle artifacts (planning-side):**

- `.claude/plan/{plugin-name}/PROJECT.md` — vision and goals
- `.claude/plan/{plugin-name}/STATE.md` — current phase, decisions, blockers
- `.claude/plan/{plugin-name}/research-FINDINGS.md` — Phase 2 output
- `.claude/plan/{plugin-name}/design-PLAN.md` — Phase 3 output
- `.claude/plan/{plugin-name}/assessment-REPORT.md` — Phase 1 output
- `.claude/plan/{plugin-name}/validation-REPORT.md` — Phase 7 output
- `.claude/plan/{plugin-name}/SUMMARY.md` — completion record

**Installation (consumer-side):**

- `~/.claude/settings.json` — user scope
- `.claude/settings.json` — project scope
- `.claude/settings.local.json` — local scope (gitignored)
- `managed-settings.json` — managed scope (read-only)
- Plugin cache directory — Claude Code copies plugins here; `${CLAUDE_PLUGIN_ROOT}` resolves to this location

**Agent memory (subagent-side):**

- `~/.claude/agent-memory/<name>/` — user scope memory
- `.claude/agent-memory/<name>/` — project scope memory
- `.claude/agent-memory-local/<name>/` — local scope memory (not version-controlled)

**MCP server data:**

- Example: `"DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"` — data stored inside the plugin's cached directory

**WHEN**: Plugin structure in "Plugin Directory Structure" and "File Locations Reference" of `claude-plugins-reference-2026`. Lifecycle artifacts in "Artifact System" of `plugin-lifecycle` SKILL.md. Installation settings in "Plugin Installation Scopes." Agent memory in `inline-agent-hooks.md`. MCP data in the MCP server example.

**THEN**: The reader uses `${CLAUDE_PLUGIN_ROOT}` for all paths to scripts and data files within hooks and MCP configs to ensure correct resolution from the cache location. Planning artifacts go in `.claude/plan/{plugin-name}/`.

---

## Q6: What environment variables are available in plugins?

**GIVEN**: The skill documents three environment variables:

| Variable | Value | Usage |
|----------|-------|-------|
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin directory (in cache) | Reference scripts, configs, and data from hooks, MCP servers, and commands. Ensures correct paths regardless of installation location. |
| `${CLAUDE_PROJECT_DIR}` | Project root directory (where Claude Code was started) | Project-relative paths from within plugin scripts. |
| `$ARGUMENTS` | Command arguments from user input | Passed to command's bash execution; available via `$ARGUMENTS` in SKILL.md content. |

Additionally, `${CLAUDE_SESSION_ID}` is available as a string substitution in SKILL.md content for use in log paths (e.g., `logs/${CLAUDE_SESSION_ID}.log`).

**WHEN**: Documented in the `claude-plugins-reference-2026` "Environment Variables" section and the plugin-creator CLAUDE.md "Environment Variables" table. `$ARGUMENTS` is documented in the plugin-lifecycle SKILL.md ("Arguments: `$ARGUMENTS`") and `claude-skills-overview-2026` "String Substitutions" section.

**THEN**: The reader uses `${CLAUDE_PLUGIN_ROOT}` in all hook commands and MCP server configs for portable paths, `${CLAUDE_PROJECT_DIR}` for project-relative access, and `$ARGUMENTS` to receive user input in skills.

---

## Q7: How many ways can an MCP server be made available to an agent?

**GIVEN**: The skill documents **three** ways to make an MCP server available to an agent:

1. **Plugin-level `.mcp.json` file**: Define MCP servers in `.mcp.json` at the plugin root, or inline in `plugin.json` under the `mcpServers` field. These servers start automatically when the plugin is enabled and appear as standard MCP tools.
2. **Agent frontmatter `mcpServers` field — reference by name**: List an already-configured server by name (e.g., `- slack`). The subagent gets access to that server. Subagents do NOT inherit MCP servers from the parent session unless explicitly listed.
3. **Agent frontmatter `mcpServers` field — inline definition**: Define the server configuration directly in the agent's frontmatter with the server name as key and a full MCP server config object as value (e.g., `internal-api: {type: http, url: "https://api.internal/mcp"}`).

The critical distinction is that subagents do NOT inherit MCP servers from the parent session — servers must be explicitly provided via one of these three mechanisms.

**WHEN**: Plugin-level MCP is in the "MCP Servers" component reference of `claude-plugins-reference-2026`. Agent-level MCP (reference by name and inline definition) is in the `inline-agent-hooks.md` reference under "mcpServers Field."

**THEN**: The reader chooses the appropriate mechanism: plugin-level for all agents in the plugin, agent-level reference for sharing existing servers, or agent-level inline for agent-specific server definitions.

---

## Q8: How are tools assigned to an agent?

**GIVEN**: Tools are assigned to agents through multiple mechanisms:

1. **Skill `allowed-tools` frontmatter field**: A comma-separated string (not an array) listing tools granted to Claude without per-use permission prompts when the skill is active. Example: `allowed-tools: Read, Grep, Glob, Bash(python:*)`.

2. **Agent type selection**: Built-in agent types have inherent tool access levels:
   - `Explore` — File/web/MCP (read-only)
   - `Plan` — File/web/MCP (read-only)
   - `general-purpose` — File/web/MCP + Bash/system (full access, default)
   - `Custom` — Custom tool set

3. **Agent frontmatter `allowedTools` field**: Explicitly lists which tools the agent has access to. Documented in `inline-agent-hooks.md` supported frontmatter fields.

4. **Context fork behavior**: When `context: fork` is set, the forked subagent has access to: File operations (Read, Write, Edit, Grep, Glob), Web operations (WebSearch, WebFetch), MCP tools (if configured), and Bash/system tools (depending on agent type). The Agent tool is NOT available in forked contexts.

**WHEN**: `allowed-tools` is documented in the `claude-skills-overview-2026` frontmatter fields table. Agent types are in the "Agent Types" table. Forked context tool restrictions are in "Tool Restrictions in Forked Contexts." Agent-level `allowedTools` is in `inline-agent-hooks.md`.

**THEN**: The reader uses `allowed-tools` in SKILL.md for skill-scoped tool grants, selects the appropriate agent type for built-in tool sets, uses `allowedTools` in agent frontmatter for explicit tool lists, and understands that forked contexts cannot use the Agent tool.

---

## Q9: How are tools hidden from an agent?

**GIVEN**: The skill documents these mechanisms for hiding tools from an agent:

1. **`disable-model-invocation: true`** in skill frontmatter: Removes the skill from Claude's context entirely, preventing Claude from auto-loading it and its associated `allowed-tools`. This is the primary "hiding" mechanism for skills.

2. **`user-invocable: false`** in skill frontmatter: Hides the skill from the user's `/` menu. Claude can still invoke it, but users do not see it. (Hides from user, not from agent.)

3. **Agent type selection**: Using `Explore` or `Plan` agent types inherently restricts the agent to read-only tools, effectively hiding write tools from those agents.

4. **Forked context restrictions**: The Agent tool is not available in forked contexts (`context: fork`), hiding delegation capability from subagents.

The skill does not document a dedicated "hide specific built-in tools from an agent" mechanism beyond these approaches.

**WHEN**: `disable-model-invocation` and `user-invocable` are in `claude-skills-overview-2026` under "Invocation Control." Agent type restrictions are in the "Agent Types" table. Forked context restrictions are in "Tool Restrictions in Forked Contexts."

**THEN**: The reader uses `disable-model-invocation: true` to hide a skill (and its tools) from Claude's awareness, `user-invocable: false` to hide from the user menu, and selects restricted agent types to limit available tools by design.

---

## Q10: How are tools denied from use from an agent?

**GIVEN**: The skill documents these explicit denial mechanisms:

1. **Agent frontmatter `disallowedTools` field**: Explicitly removes named tools from the agent's available set, regardless of whether tools were inherited or explicitly listed. (Source: `inline-agent-hooks.md`)

2. **Permission rules — deny specific skills**: Using permission rules in `/permissions`: `Skill(deploy *)` in deny rules blocks that skill's invocation. (Source: `claude-skills-overview-2026`, "Restrict Claude's skill access")

3. **Permission rules — deny all skills**: Denying the `Skill` tool entirely in `/permissions` prevents Claude from invoking any skill. (Source: `claude-skills-overview-2026`)

4. **PreToolUse hook with exit code 2**: A hook on `PreToolUse` that exits with code 2 blocks the tool call. stderr is fed back as an error message. (Source: `claude-code.md`, "Exit Codes")

5. **PreToolUse hook with JSON `permissionDecision: "deny"`**: A hook returning JSON with `hookSpecificOutput.permissionDecision: "deny"` prevents the tool call, and `permissionDecisionReason` is shown to Claude. (Source: `claude-code.md`, "PreToolUse Decision Control")

6. **PermissionRequest hook with `decision.behavior: "deny"`**: A hook on the `PermissionRequest` event that returns `behavior: "deny"` denies the permission request, with an optional message. (Source: `claude-code.md`)

**WHEN**: `disallowedTools` is in `inline-agent-hooks.md` supported frontmatter fields. Permission rules are in `claude-skills-overview-2026` "Restrict Claude's skill access." Hook-based denial is in `claude-code.md` under "Exit Codes" and "PreToolUse Decision Control."

**THEN**: The reader uses `disallowedTools` in agent frontmatter for agent-scoped denial, permission rules for user/project-scoped denial, and PreToolUse/PermissionRequest hooks for programmatic, conditional denial with custom logic.

---

## Q11: What are the ways agents in a plugin are allowed to do tasks without permission requests but pre-approved within the scope of the plugin?

**GIVEN**: The skill documents these pre-approval mechanisms:

1. **Skill `allowed-tools` field**: Tools listed are granted to Claude without per-use permission prompts when the skill is active. Example: `allowed-tools: Read, Grep, Glob, Bash(npm run:*)`. (Source: `claude-skills-overview-2026` — "Listed tools are granted to Claude without per-use permission prompts when the skill is active")

2. **Agent `permissionMode` field**: The agent frontmatter supports a `permissionMode` field with values: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, or `plan`. Setting `dontAsk` or `bypassPermissions` allows the agent to operate without permission prompts. (Source: `inline-agent-hooks.md`, Supported Frontmatter Fields)

3. **PreToolUse hook auto-approval**: A PreToolUse hook can return `permissionDecision: "allow"` to bypass the permission system entirely for a specific tool call. The `permissionDecisionReason` is shown to the user but not Claude. (Source: `claude-code.md`, "PreToolUse Decision Control")

4. **PermissionRequest hook auto-approval**: A PermissionRequest hook can return `decision.behavior: "allow"` to auto-approve a permission request without user interaction. (Source: `claude-code.md`)

5. **Hook auto-execution**: Hooks configured in `hooks.json` execute automatically when their trigger events fire — no permission prompts. A `command` hook running `${CLAUDE_PLUGIN_ROOT}/scripts/format.sh` on every Write or Edit fires without user approval.

6. **Background agent mode**: The agent `background` field, when set to `true`, requires all permission approval before launch — all permissions are pre-approved, and once running, any non-pre-approved permission is auto-denied. (Source: `inline-agent-hooks.md`, "background Field")

**WHEN**: `allowed-tools` in the frontmatter fields table of `claude-skills-overview-2026`. `permissionMode` in `inline-agent-hooks.md`. Hook-based auto-approval in `claude-code.md` Decision Control sections. Background approval in `inline-agent-hooks.md`.

**THEN**: The reader selects the appropriate pre-approval mechanism: `allowed-tools` for skill-scoped tool approval, `permissionMode` for agent-wide approval, hooks for programmatic conditional approval, and `background` for fully pre-approved autonomous agents.

---

## Q12: How is the plugin namespace defined?

**GIVEN**: The skill documents plugin namespacing at multiple levels:

1. **Plugin name in `plugin.json`**: The `name` field is a unique identifier in kebab-case (no spaces, max 64 chars). This is the only required field. Example: `"deployment-tools"`. (Source: `claude-plugins-reference-2026`, Required Fields)

2. **Skill namespacing via plugin prefix**: Plugin skills use a `plugin-name:skill-name` namespace, so they cannot conflict with other levels (personal, project, enterprise). When skills share the same name across levels, higher-priority locations win (enterprise > personal > project), but plugin skills are namespaced separately. Examples throughout the skill: `plugin-creator:skill-creator`, `plugin-creator:assessor`. (Source: `claude-skills-overview-2026`, "Location Priority")

3. **Marketplace namespacing**: Plugins in a marketplace are identified as `plugin-name@marketplace-name`. Example: `formatter@my-marketplace`. Reserved marketplace names include: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `life-sciences`. (Source: `claude-plugins-reference-2026`, "Plugin Marketplaces" and CLI examples)

4. **Skill `name` field**: The `name` field in SKILL.md frontmatter must match the directory name and satisfy `^[a-z][a-z0-9-]*$` (lowercase letters, numbers, hyphens only, max 64 chars). Required per the agentskills.io spec. (Source: plugin-creator CLAUDE.md, "Skill Name Field")

**WHEN**: Plugin name field is in the plugin.json schema. Namespaced skill references appear throughout the plugin-lifecycle SKILL.md (e.g., `Skill(skill="plugin-creator:assessor")`). Marketplace namespacing is in the CLI commands reference.

**THEN**: The reader sets the `name` field in `plugin.json` using kebab-case. Skills are automatically namespaced as `plugin-name:skill-name`. Distribution uses `plugin-name@marketplace-name` for marketplace identification.

---

## Q13: What scripting languages should be preferred when the script is shipping with the plugin as a hook or as MCP or tooling?

**GIVEN**: The skill does not state an explicit single preferred language but provides strong signals through examples and dedicated authoring guides:

**Languages with dedicated authoring guides in the hooks-guide skill:**

- **Python** — `hooks-python.md` authoring guide
- **Node.js (CommonJS)** — `hooks-cjs.md` authoring guide

These are the only two languages with dedicated hook authoring documentation, suggesting they are the two recommended languages.

**Languages shown in examples across the skill ecosystem:**

- **Shell/Bash** — Used in hook `command` fields throughout all references (`./scripts/format-code.sh`, `./scripts/security-check.sh`, `./scripts/validate-command.sh`). Used for simple hook scripts.
- **Python** — Used for all validator and tooling scripts in the plugin-lifecycle itself (`plugin_validator.py`, `create_plugin.py`, `fix_tool_formats.py`, `auto_sync_manifests.py`), run via `uv run`.
- **JavaScript/Node.js** — Used for MCP servers (`npx @company/mcp-server`). Plugin directory structure examples show `deploy.js`.

**Constraints noted:**

- Scripts must be executable (`chmod +x`) per the constraints section.
- `${CLAUDE_PLUGIN_ROOT}` must be used for path resolution in hook commands.
- LSP servers require separate binary installation — plugins configure the connection, not the server.

**WHEN**: Hook authoring guides are listed in the hooks-guide skill references. Python usage is demonstrated in every script in the plugin-lifecycle and plugin-creator plugins. Shell usage is in hook command examples across `claude-plugins-reference-2026` and `claude-code.md`. Node.js usage is in MCP server examples.

**THEN**: The reader prefers Python or Node.js (CommonJS) for hooks and tooling (the two languages with dedicated authoring guides), Shell/Bash for simple hook commands, and Node.js for MCP servers. Python with `uv run` is the de facto standard for plugin tooling scripts in this ecosystem.
