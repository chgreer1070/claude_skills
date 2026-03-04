# Plugin Lifecycle Skill — Knowledge Audit

Answers derived exclusively from the plugin-lifecycle skill and the reference skills it composes:
`claude-plugins-reference-2026`, `claude-skills-overview-2026`, `hooks-guide` (including `inline-agent-hooks.md` and `claude-code.md` references).

---

## Q1: What is a plugin?

**GIVEN**: Plugins extend Claude Code with skills, agents, hooks, MCP servers, and LSP servers. A plugin is a directory containing a `.claude-plugin/plugin.json` manifest file plus any combination of those components. The `plugin.json` file defines the plugin's metadata and configuration, and the only required field is `name` (kebab-case, unique identifier). The plugin-lifecycle skill describes a plugin as something that goes through seven phases — assess, research, design, create, debug, optimize, verify — to become "marketplace-ready."

**WHEN**: This definition is presented in the `claude-plugins-reference-2026` skill opening section ("Plugins extend Claude Code with skills, agents, hooks, MCP servers, and LSP servers") and in the plugin-lifecycle SKILL.md description ("Orchestrate the full plugin development lifecycle from blank canvas to marketplace-ready").

**THEN**: The reader understands a plugin is a self-contained, distributable package of Claude Code extensions identified by a `.claude-plugin/plugin.json` manifest, containing any combination of skills, agents, hooks, MCP servers, and LSP servers.

---

## Q2: What are the capabilities of a plugin?

**GIVEN**: Plugins can include any combination of six component types:
1. **Skills**: SKILL.md directories that Claude can invoke automatically — create `/name` shortcuts
2. **Commands**: Markdown files creating `/name` shortcuts (legacy; use skills instead)
3. **Agents**: Specialized subagents for specific tasks that Claude can invoke automatically
4. **Hooks**: Event handlers responding to Claude Code events (PreToolUse, PostToolUse, Stop, SubagentStart, SubagentStop, SessionStart, SessionEnd, and many more)
5. **MCP Servers**: Model Context Protocol servers for external tool integration — start automatically when the plugin is enabled, appear as standard MCP tools
6. **LSP Servers**: Language Server Protocol servers for code intelligence — instant diagnostics, go to definition, find references, hover information, type information

Additionally, plugins support: environment variable substitution (`${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PROJECT_DIR}`), marketplace distribution, version management (semver), installation scopes (user/project/local/managed), enterprise features (required marketplaces, managed restrictions), and private repository authentication.

**WHEN**: Presented in the "Plugin Components Overview" and "Plugin Components Reference" sections of `claude-plugins-reference-2026`.

**THEN**: The reader knows the full range of extension points a plugin can provide and can select the appropriate component types for their use case.

---

## Q3: Who is the user of a plugin?

**GIVEN**: The skill identifies multiple user categories:
1. **End users (developers)**: Install plugins via `claude plugin install`, invoke skills with `/name`, interact with agents — plugins are installed at user, project, local, or managed scope
2. **Plugin authors/developers**: Create plugins through the lifecycle phases (assess, research, design, create, debug, optimize, verify) — the plugin-lifecycle skill itself is the primary tool for this audience
3. **Team leads / project maintainers**: Configure plugins in `.claude/settings.json` for team sharing via version control (project scope)
4. **Enterprise administrators**: Control plugin sources via `strictKnownMarketplaces` in managed settings, enforce organization-wide hooks with `allowManagedHooksOnly`

The `claude-skills-overview-2026` skill also distinguishes between: the user who invokes a skill directly (`/skill-name`), and Claude itself which can auto-invoke skills based on task context.

**WHEN**: Installation scopes are defined in "Plugin Installation Scopes" of `claude-plugins-reference-2026`. Enterprise features are in the "Enterprise Features" section. Invocation control is in "Invocation Control" of `claude-skills-overview-2026`.

**THEN**: The reader understands that plugins serve developers, teams, and enterprises at different scopes, and that both human users and Claude (the AI agent) are consumers of plugin capabilities.

---

## Q4: What systems or tools can load these plugins?

**GIVEN**: The skill explicitly names **Claude Code** as the system that loads plugins. Specific loading mechanisms include:
1. **CLI installation**: `claude plugin install <plugin> [--scope user|project|local]`
2. **Testing without installation**: `claude --plugin-dir ./my-plugin` (session-only loading)
3. **Marketplace installation**: plugins distributed via marketplace.json repositories (GitHub, GitLab, git URL sources)
4. **Plugin caching**: Claude Code copies plugins to a cache directory rather than using them in-place — for security and verification

The `claude-skills-overview-2026` also notes that the skill format (SKILL.md) has a portable subset defined by the [Agent Skills Open Standard](https://agentskills.io) that works across "Claude Code, Cursor, Gemini CLI, OpenAI Codex, VS Code, and 20+ other agents" — but the plugin system itself (plugin.json, `.claude-plugin/` directory) is Claude Code-specific.

The `hooks-guide` skill covers hooks for Claude Code, GitHub Copilot, Cursor, Windsurf, and Amp — but the plugin packaging/distribution system described in the lifecycle skill is Claude Code only.

**WHEN**: CLI commands in "CLI Commands Reference" of `claude-plugins-reference-2026`. Caching in "Plugin Caching and File Resolution." Portable standard noted in the opening of `claude-skills-overview-2026`.

**THEN**: The reader knows that the plugin system is Claude Code-specific, while individual skills within plugins may be portable to other agents via the agentskills.io standard.

---

## Q5: Where is data stored in plugins?

**GIVEN**: The skill identifies these storage locations:

**Plugin structure (author-side):**
- `.claude-plugin/plugin.json` — the required manifest file (metadata directory contains ONLY this file)
- `commands/` — default command location
- `agents/` — default agent location
- `skills/` — agent skills with `<name>/SKILL.md` structure
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
- Plugin cache directory — Claude Code copies plugins here for use

**Agent memory (subagent-side, from inline-agent-hooks):**
- `~/.claude/agent-memory/<name>/` — user scope memory
- `.claude/agent-memory/<name>/` — project scope memory
- `.claude/agent-memory-local/<name>/` — local scope memory (not version-controlled)

**WHEN**: Plugin structure in "Plugin Directory Structure" and "File Locations Reference" of `claude-plugins-reference-2026`. Lifecycle artifacts in "Artifact System" of `plugin-lifecycle` SKILL.md. Installation settings in "Plugin Installation Scopes." Agent memory in the "memory Field" section of `inline-agent-hooks.md`.

**THEN**: The reader knows all data storage locations for plugin authoring, lifecycle planning, installation configuration, and agent persistence.

---

## Q6: What environment variables are available in plugins?

**GIVEN**: The skill documents these environment variables:

**Plugin-specific:**
| Variable | Description |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin directory — use in hooks, MCP servers, and scripts for correct paths regardless of installation location |
| `${CLAUDE_PROJECT_DIR}` | Project root directory (where Claude Code was started) |

**Skill-specific string substitutions (from `claude-skills-overview-2026`):**
| Variable | Description |
|---|---|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` or `$N` | Access a specific argument by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID |

**Hook-specific (from `claude-code.md` reference):**
| Variable | Description |
|---|---|
| `CLAUDE_PROJECT_DIR` | Project root directory (available in all hooks) |
| `CLAUDE_PLUGIN_ROOT` | Plugin root directory (available in plugin hooks) |
| `CLAUDE_ENV_FILE` | File path for persisting environment variables (SessionStart only) |
| `CLAUDE_CODE_REMOTE` | Set to `"true"` in remote web environments; not set in local CLI |

**Configuration override (from `claude-skills-overview-2026`):**
| Variable | Description |
|---|---|
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | Override the skill metadata budget limit |
| `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` | Set to `1` to disable background task functionality |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | Set to `1` to load CLAUDE.md from `--add-dir` directories |

**WHEN**: Plugin variables in "Environment Variables" of `claude-plugins-reference-2026`. Skill substitutions in "String Substitutions" of `claude-skills-overview-2026`. Hook variables in "Environment Variables" of `claude-code.md`. Configuration overrides scattered through `claude-skills-overview-2026` troubleshooting sections.

**THEN**: The reader has a complete inventory of environment variables available across plugin components, hooks, and skills.

---

## Q7: How many ways can an MCP server be made available to an agent?

**GIVEN**: The skill documents **three** ways to make an MCP server available to an agent:

1. **Plugin-level `.mcp.json` file**: Define MCP servers in `.mcp.json` at the plugin root, or inline in `plugin.json` under the `mcpServers` field. These servers start automatically when the plugin is enabled and appear as standard MCP tools. (Source: `claude-plugins-reference-2026`, "MCP Servers" section)

2. **Agent frontmatter `mcpServers` field — reference by name**: List an already-configured server by name (e.g., `- slack`). The subagent gets access to that server. Subagents do NOT inherit MCP servers from the parent session unless explicitly listed. (Source: `inline-agent-hooks.md`, "mcpServers Field" section)

3. **Agent frontmatter `mcpServers` field — inline definition**: Define the server configuration directly in the agent's frontmatter with the server name as key and a full MCP server config object as value (e.g., `internal-api: {type: http, url: "https://api.internal/mcp"}`). (Source: `inline-agent-hooks.md`, "mcpServers Field" section)

**WHEN**: Plugin-level MCP is in the "MCP Servers" component reference. Agent-level MCP is in the `inline-agent-hooks.md` reference under "mcpServers Field."

**THEN**: The reader knows there are 3 ways: plugin-level config file, agent-level reference to existing server, and agent-level inline definition. The critical distinction is that subagents do NOT inherit MCP servers — they must be explicitly declared.

---

## Q8: How are tools assigned to an agent?

**GIVEN**: The skill documents these mechanisms for assigning tools to an agent:

1. **Agent frontmatter `tools` field**: List specific tools the subagent can use. If omitted, the agent inherits all tools. (Source: `inline-agent-hooks.md`, Supported Frontmatter Fields table — `tools: No | Tools the subagent can use. Inherits all tools if omitted`)

2. **Skill frontmatter `allowed-tools` field**: Tools Claude can use without asking permission when this skill is active (comma-separated). This field is both a pre-approval mechanism AND a capability scoping mechanism — listed tools are granted without per-use permission prompts, and Claude is restricted to ONLY those tools. If `allowed-tools` is not specified, the skill inherits the tool capabilities of the parent agent. (Source: `claude-skills-overview-2026`, "All Frontmatter Fields" section)

3. **Agent frontmatter `mcpServers` field**: MCP servers listed in the agent frontmatter provide their tools to the agent. MCP tools follow the naming pattern `mcp__<server>__<tool>`. (Source: `inline-agent-hooks.md`, "mcpServers Field")

4. **Agent frontmatter `skills` field**: Skills preloaded into a subagent inject their full content, and if those skills have `allowed-tools`, those tools become available. (Source: `inline-agent-hooks.md`, "skills Field")

5. **Agent frontmatter `memory` field**: When `memory` is enabled, `Read`, `Write`, and `Edit` tools are automatically enabled so the subagent can manage its memory files. (Source: `inline-agent-hooks.md`, "memory Field")

**WHEN**: Agent tools in "Supported Frontmatter Fields" of `inline-agent-hooks.md`. Skill allowed-tools in "All Frontmatter Fields" of `claude-skills-overview-2026`.

**THEN**: The reader understands the five mechanisms by which tools become available to an agent: explicit `tools` field, skill `allowed-tools`, MCP server declarations, preloaded skills, and automatic enablement via `memory`.

---

## Q9: How are tools hidden from an agent?

**GIVEN**: The skill documents these mechanisms for hiding tools:

1. **Agent frontmatter `disallowedTools` field**: Tools to deny, removed from inherited or specified list. This explicitly removes tools from whatever set the agent would otherwise have. (Source: `inline-agent-hooks.md`, Supported Frontmatter Fields — `disallowedTools: No | Tools to deny, removed from inherited or specified list`)

2. **Skill frontmatter `allowed-tools` field (by omission)**: When `allowed-tools` is specified, Claude is restricted to ONLY those tools — effectively hiding all other tools. This also "reduces context size by limiting included tool definitions to only those the skill may need." (Source: `claude-skills-overview-2026`, the IMPORTANT callout under All Frontmatter Fields)

3. **Skill frontmatter `disable-model-invocation: true`**: This removes the skill's description from Claude's context entirely, so Claude cannot discover or auto-invoke it. While this hides the skill (not individual tools), it prevents Claude from accessing whatever tools that skill would have provided. (Source: `claude-skills-overview-2026`, "Invocation Control" section)

4. **Skill frontmatter `user-invocable: false`**: Hides the skill from the `/` menu so users cannot see or invoke it. Claude can still invoke it. (Source: `claude-skills-overview-2026`, "Invocation Control" section)

**WHEN**: `disallowedTools` in the Supported Frontmatter Fields table of `inline-agent-hooks.md`. Allowed-tools scoping in the IMPORTANT note of `claude-skills-overview-2026`. Invocation control in its dedicated section.

**THEN**: The reader knows tools are hidden via `disallowedTools` (explicit removal), `allowed-tools` (whitelist-only scoping), `disable-model-invocation` (removing from context), and `user-invocable: false` (hiding from user menu).

---

## Q10: How are tools denied from use from an agent?

**GIVEN**: The skill documents these mechanisms for denying tool use:

1. **Agent frontmatter `disallowedTools` field**: Explicitly removes named tools from the agent's available set, regardless of whether tools were inherited or explicitly listed. (Source: `inline-agent-hooks.md`)

2. **Permission rules — deny specific skills**: Using permission rules to deny specific skills: `Skill(deploy *)` in deny rules blocks that skill's invocation. (Source: `claude-skills-overview-2026`, "Restrict Claude's skill access")

3. **Permission rules — deny all skills**: Denying the `Skill` tool entirely in `/permissions` prevents Claude from invoking any skill. (Source: `claude-skills-overview-2026`, "Restrict Claude's skill access")

4. **PreToolUse hook with exit code 2**: A hook on `PreToolUse` that exits with code 2 blocks the tool call. stderr is fed back as error message. (Source: `claude-code.md`, "Exit Codes" section — `Exit 2: Blocking error. stderr is fed back as error message`)

5. **PreToolUse hook with JSON `permissionDecision: "deny"`**: A hook returning JSON with `hookSpecificOutput.permissionDecision: "deny"` prevents the tool call, and `permissionDecisionReason` is shown to Claude. (Source: `claude-code.md`, "PreToolUse Decision Control")

6. **PermissionRequest hook with `decision.behavior: "deny"`**: A hook on the `PermissionRequest` event that returns `behavior: "deny"` denies the permission, with an optional `message` telling Claude why. (Source: `claude-code.md`, "PermissionRequest Decision Control")

7. **Context fork tool restrictions**: When `context: fork` is set, the Agent tool is NOT available in forked contexts. Forked skills cannot delegate to other subagents. (Source: `claude-skills-overview-2026`, "Tool Restrictions in Forked Contexts")

**WHEN**: `disallowedTools` in `inline-agent-hooks.md`. Permission rules in `claude-skills-overview-2026` "Restrict Claude's skill access." Hook-based denial in `claude-code.md` Event Decision Control sections. Context fork restrictions in `claude-skills-overview-2026`.

**THEN**: The reader has seven distinct mechanisms for denying tool use: frontmatter `disallowedTools`, permission deny rules (specific or blanket), PreToolUse hook exit code 2, PreToolUse hook JSON deny, PermissionRequest hook deny, and context fork restrictions.

---

## Q11: What are the ways agents in a plugin are allowed to do tasks without permission requests but pre-approved within the scope of the plugin?

**GIVEN**: The skill documents these pre-approval / permission-bypass mechanisms:

1. **Skill `allowed-tools` field**: Tools listed in `allowed-tools` are granted to Claude without per-use permission prompts when the skill is active. This is the primary pre-approval mechanism. Example: `allowed-tools: Read, Grep, Glob, Bash(npm run:*)`. (Source: `claude-skills-overview-2026`, IMPORTANT callout: "Listed tools are granted to Claude without per-use permission prompts when the skill is active")

2. **Agent `permissionMode` field**: The agent frontmatter supports a `permissionMode` field with values: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, or `plan`. Setting `dontAsk` or `bypassPermissions` allows the agent to operate without permission prompts. (Source: `inline-agent-hooks.md`, Supported Frontmatter Fields — `permissionMode: No | Permission mode: default, acceptEdits, dontAsk, bypassPermissions, or plan`)

3. **PreToolUse hook auto-approval**: A PreToolUse hook can return `permissionDecision: "allow"` to bypass the permission system entirely for a specific tool call. The `permissionDecisionReason` is shown to the user but not Claude. (Source: `claude-code.md`, "PreToolUse Decision Control" — `"allow" bypasses permission system`)

4. **PermissionRequest hook auto-approval**: A PermissionRequest hook can return `behavior: "allow"` to grant permission programmatically. It can also return `updatedPermissions` to apply permanent permission rule updates (equivalent to user selecting "always allow"). (Source: `claude-code.md`, "PermissionRequest Decision Control")

5. **Background subagent upfront approval**: Background subagents (`background: true`) require upfront permission approval before launch — all permissions are pre-approved, and once running, any non-pre-approved permission is auto-denied. (Source: `inline-agent-hooks.md`, "background Field")

**WHEN**: `allowed-tools` in the Frontmatter Fields table and IMPORTANT note of `claude-skills-overview-2026`. `permissionMode` in the Supported Frontmatter Fields table of `inline-agent-hooks.md`. Hook-based auto-approval in `claude-code.md` Decision Control sections. Background approval in `inline-agent-hooks.md`.

**THEN**: The reader understands five pre-approval mechanisms: `allowed-tools` for skill-scoped tool approval, `permissionMode` for agent-wide permission bypass, PreToolUse hooks for per-call auto-approval, PermissionRequest hooks for programmatic permission grants, and background subagent upfront approval.

---

## Q12: How is the plugin namespace defined?

**GIVEN**: The skill documents plugin namespacing as follows:

1. **Plugin name in `plugin.json`**: The `name` field is a unique identifier in kebab-case (no spaces). This is the only required field. Example: `"deployment-tools"`. (Source: `claude-plugins-reference-2026`, Required Fields table)

2. **Skill namespacing via plugin prefix**: Plugin skills use a `plugin-name:skill-name` namespace, so they cannot conflict with other levels (personal, project, enterprise). When skills share the same name across levels, higher-priority locations win (enterprise > personal > project), but plugin skills are namespaced separately. (Source: `claude-skills-overview-2026`, "Location Priority" section — "Plugin skills use a `plugin-name:skill-name` namespace, so they cannot conflict with other levels")

3. **Marketplace namespacing**: Plugins in a marketplace are identified as `plugin-name@marketplace-name`. Example: `formatter@my-marketplace`. Reserved marketplace names include: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `life-sciences`. (Source: `claude-plugins-reference-2026`, "Plugin Marketplaces" and CLI examples)

4. **Skill `name` field**: The `name` field in SKILL.md frontmatter must match the directory name and satisfy `^[a-z][a-z0-9-]*$` (lowercase letters, numbers, hyphens only, max 64 chars). Required per the agentskills.io spec. (Source: `claude-skills-overview-2026`, Frontmatter Fields table)

**WHEN**: Plugin naming in "Required Fields" of `claude-plugins-reference-2026`. Skill namespacing in "Location Priority" of `claude-skills-overview-2026`. Marketplace naming in "Plugin Marketplaces."

**THEN**: The reader understands the three-tier namespace: `plugin-name` (kebab-case in plugin.json), `plugin-name:skill-name` (for skill resolution), and `plugin-name@marketplace-name` (for marketplace distribution). Plugin skills are namespaced independently from project/personal/enterprise skills.

---

## Q13: What scripting languages should be preferred when the script is shipping with the plugin as a hook or as MCP or tooling?

**GIVEN**: The skill does not explicitly state a preferred scripting language for plugin-shipped scripts. However, from the examples and patterns across all reference materials, the following observations can be made:

**Languages shown in examples:**
- **Shell/Bash**: Used in hook `command` fields throughout all references (`./scripts/format-code.sh`, `./scripts/security-check.sh`, `./scripts/validate-command.sh`). The `claude-code.md` hook reference, `inline-agent-hooks.md`, and `claude-plugins-reference-2026` all use `.sh` scripts in their examples.
- **Python**: Used in hook examples (`format-code.py` listed in plugin directory structure). The hooks-guide provides a dedicated `hooks-python.md` authoring guide.
- **JavaScript/Node.js**: Used for MCP servers (`npx @company/mcp-server`). The hooks-guide provides a dedicated `hooks-cjs.md` (Node.js CommonJS) authoring guide. The plugin directory structure shows `deploy.js`.

**From plugin-lifecycle SKILL.md itself**: All validator and tooling scripts use Python with `uv run` (`plugin_validator.py`, `create_plugin.py`, `fix_tool_formats.py`, `auto_sync_manifests.py`). One script uses Bash (`validate-task-file.sh`).

**From hooks-guide**: The skill provides dedicated authoring guides for exactly two languages: Node.js CJS (`hooks-cjs.md`) and Python (`hooks-python.md`), suggesting these are the two recommended languages for hook authoring.

The skill does **not** contain an explicit statement like "prefer language X for plugin scripts." The closest guidance is the hooks-guide routing diagram which routes authors to either Node.js CJS or Python based on their preference, treating both as first-class options.

**WHEN**: Examples distributed throughout all reference skills. Dedicated hook authoring guides in hooks-guide references.

**THEN**: Based on patterns in the skill (not an explicit recommendation): Shell/Bash for simple hook commands, Python or Node.js CJS for complex hook logic (both have dedicated authoring guides), and Node.js for MCP servers. The skill does not make an explicit language preference statement — this is inferred from examples and the existence of dedicated guides for Python and Node.js CJS only.
