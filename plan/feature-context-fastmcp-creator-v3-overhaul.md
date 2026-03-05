# Feature Context: FastMCP Creator Plugin v3 Overhaul

## Document Metadata

- **Generated**: 2026-03-05
- **Input Type**: existing_document
- **Source**: `.claude/backlog/p1-fastmcp-creator-plugin-v3-overhaul-authoritative-skill-meta-.md` (backlog item)
- **Status**: QUESTIONS_RESOLVED

---

## Original Request

Overhaul the fastmcp-creator plugin to be a comprehensive, authoritative FastMCP v3 skill with zero speculation, grounded in local v3 docs and real-world GitHub usage.

Three deliverables:
1. Runnable MCP server at `plugins/fastmcp-creator/server/` — serves reference files as MCP resources, exposes prompts, provides helper tools (scaffold, validate, version-check, search-docs). Registered in plugin.json via mcpServers.
2. New reference files — replacing current 7 files, generated from `.claude/worktrees/fastmcp/docs/`. Topics: server-core, providers, transforms, auth, client-sdk, apps, advanced, deployment, testing, integrations, migration, real-world-patterns.
3. Rewritten SKILL.md — dense capability map with trigger matrix, feature decision flowcharts, zero speculation, every claim sourced.

---

## Core Intent Analysis

### WHO (Target Users)

Developers using Claude Code to build, extend, or debug FastMCP v3 MCP servers. The skill is loaded by Claude Code agents, not read by humans directly.

### WHAT (Desired Outcome)

A plugin where every factual claim in SKILL.md and reference files is sourced from the local `.claude/worktrees/fastmcp/docs/` directory — no training-data speculation. The plugin also ships a live MCP server that exposes reference docs as resources and provides scaffold/validate tools.

### WHEN (Trigger Conditions)

- User asks Claude to build a new FastMCP server
- User asks about v3-specific features (providers, transforms, apps, tasks, elicitation, storage backends)
- User asks to extend an existing MCP server
- User encounters a FastMCP bug or error
- User asks which FastMCP feature to use for a given problem

### WHY (Problem Being Solved)

The current skill contains v2-era content and unverified claims. When Claude Code uses it to generate FastMCP v3 code, it produces incorrect patterns (wrong decorator syntax, missing provider architecture awareness, speculative `.mcpb` packaging that may not match v3). The overhaul replaces speculation with documentation-grounded, versioned facts.

---

## Current State Assessment

### Current SKILL.md (`plugins/fastmcp-creator/skills/fastmcp-creator/SKILL.md`)

**Version**: 2.4.3 (per `plugin.json`)

**What it covers well:**
- Basic `@mcp.tool` / `@mcp.resource` / `@mcp.prompt` decorator patterns
- Agent-centric design principles (workflow-oriented tools, context window efficiency)
- Phase-based workflow (intake → research → implement → test → evaluate)
- TypeScript/Node SDK path (fully covered, not in scope for this overhaul)
- Evaluation guide reference

**What is outdated or wrong:**
- Decorator syntax shows `@mcp.tool()` with parentheses throughout, but v3 docs (`quickstart.mdx`) show `@mcp.tool` without parentheses as the canonical pattern
- Provider architecture section (`development-guidelines.md`) names 5 providers but the actual v3 built-in set is LocalProvider, FastMCPProvider, ProxyProvider, FileSystemProvider, SkillsProvider, OpenAPIProvider — not the 5 named in the skill
- Transforms section names 5 transforms but the accurate v3 built-in list is: Namespace, ToolTransform, Enabled (Visibility), ResourcesAsTools, PromptsAsTools — different from the current listing
- Background tasks: shows `@mcp.tool(task=TaskConfig(mode="required"))` but v3 docs (`tasks.mdx`) show `@mcp.tool(task=True)` — diverged API
- `.mcpb` packaging described as current practice — this is community speculation, not verified against v3 official docs
- `require_auth` documented as valid — v3 release notes confirm it was removed; `require_scopes` is the correct pattern
- State methods (`ctx.get_state`, `ctx.set_state`) described as async — unverified against v3 docs
- Apps section: SKILL.md describes apps as "HTML API in v3.0.0" which is correct, but v3.1 Python-native framework is described as coming soon — apps/overview.mdx confirms 3.1 is NOT yet released as of the local docs

**What is missing entirely:**
- SkillsProvider (exposes Claude/Cursor/etc. skills as MCP resources via `skill://` URIs)
- Storage backends (`storage-backends.mdx`): pluggable in-memory/Redis/etc. for OAuth state and caching
- Elicitation API depth: multi-turn, multi-select, titled options, default values (v2.14.0+)
- Transform custom subclassing (the `Transform` base class pattern)
- Client SDK coverage: the skill has `EXCLUSIONS: Client-side MCP implementations` — this conflicts with the request to cover `client-sdk` as a reference topic
- `generate-cli` command (new in Beta 2)
- CIMD auth flow (Beta 2 addition)
- CodeMode (FastMCP 3.1 feature — dynamic tool search using BM25, Python code execution)
- Prefect Horizon deployment (`deployment/prefect-horizon.mdx`)
- Dependency injection (`servers/dependency-injection.mdx`)
- Middleware patterns (`servers/middleware.mdx`)
- Telemetry / OpenTelemetry wiring (`servers/telemetry.mdx`)
- Pagination built-in support (`servers/pagination.mdx`)
- Icons (`servers/icons.mdx`)

### Current Reference Files (8 files)

| File | Assessment |
|------|-----------|
| `development-guidelines.md` | Covers v3 architecture but has provider/transform naming errors; no citations |
| `community-practices.md` | `.mcpb` section is speculative; not sourced from official v3 docs |
| `mcp-best-practices.md` | Generic MCP — not FastMCP-specific; low v3 signal |
| `prompts-and-templates.md` | Prompt patterns — likely still accurate but uncited |
| `example-projects.md` | No v3-specific examples; no GitHub citations |
| `evaluation-guide.md` | Evaluation harness content — not affected by v3 changes |
| `typescript-mcp-server.md` | TypeScript — out of scope for this overhaul |
| `claude-code-mcp-integration.md` | Claude Code MCP config — external to FastMCP itself |

### Current `plugin.json`

```json
{
  "name": "fastmcp-creator",
  "version": "2.4.3",
  "author": { "name": "Jamie Nelson", "url": "https://github.com/bitflight-devops" }
}
```

**Missing**: `mcpServers` field (required for the server deliverable). No `skills` field listing skills. No `hooks` field.

### Sibling Skills

- `fastmcp-python-tests` — pytest patterns for FastMCP servers; references in-memory transport (`Client(mcp)`) which matches v3 patterns correctly
- `fastmcp-client-cli` — `fastmcp list` / `fastmcp call` / `fastmcp discover` CLI; appears accurate for v3 Beta 2+ (includes generate-cli reference, MCPConfig support)

---

## Target State

### Deliverable 1: MCP Server at `plugins/fastmcp-creator/server/`

A FastMCP server registered in `plugin.json` via `mcpServers` that:
- Exposes reference files as MCP resources (using FileSystemProvider or manual resources pointing to `references/`)
- Exposes prompts for common FastMCP tasks (scaffold server, choose provider, migrate from v2)
- Provides tools: scaffold (generate starter code), validate (check server syntax), version-check (compare installed vs latest), search-docs (search local docs dir)

Registered so it auto-starts when the plugin is enabled in Claude Code.

### Deliverable 2: New Reference Files

Generated from `.claude/worktrees/fastmcp/docs/`. Proposed topic mapping:

| Reference File | Source Docs |
|---|---|
| `server-core.md` | `servers/server.mdx`, `servers/tools.mdx`, `servers/resources.mdx`, `servers/prompts.mdx`, `servers/context.mdx` |
| `providers.md` | `servers/providers/overview.mdx`, `local.mdx`, `mounting.mdx`, `proxy.mdx`, `filesystem.mdx`, `skills.mdx`, `custom.mdx` |
| `transforms.md` | `servers/transforms/transforms.mdx`, `namespace.mdx`, `tool-transformation.mdx`, `resources-as-tools.mdx`, `prompts-as-tools.mdx` |
| `auth.md` | `servers/auth/authentication.mdx`, `full-oauth-server.mdx`, `oauth-proxy.mdx`, `oidc-proxy.mdx`, `remote-oauth.mdx`, `token-verification.mdx`, `servers/authorization.mdx` |
| `client-sdk.md` | `clients/client.mdx`, `transports.mdx`, `auth/bearer.mdx`, `auth/cimd.mdx`, `auth/oauth.mdx`, `sampling.mdx`, `elicitation.mdx` |
| `apps.md` | `apps/overview.mdx`, `apps/low-level.mdx` |
| `advanced.md` | `servers/tasks.mdx`, `servers/elicitation.mdx`, `servers/storage-backends.mdx`, `servers/middleware.mdx`, `servers/dependency-injection.mdx`, `servers/versioning.mdx`, `servers/visibility.mdx` |
| `deployment.md` | `deployment/running-server.mdx`, `deployment/http.mdx`, `deployment/server-configuration.mdx`, `deployment/prefect-horizon.mdx` |
| `testing.md` | `patterns/testing.mdx`, `development/tests.mdx` |
| `integrations.md` | Selected from `integrations/` (Anthropic, OpenAI, Gemini, FastAPI, Claude Code, Claude Desktop, Cursor, GitHub) |
| `migration.md` | `getting-started/upgrading/from-fastmcp-2.mdx`, `from-mcp-sdk.mdx`, `from-low-level-sdk.mdx` |
| `real-world-patterns.md` | `patterns/contrib.mdx`, `patterns/cli.mdx`, `community/showcase.mdx`, GitHub usage patterns |

### Deliverable 3: Rewritten SKILL.md

- Trigger matrix: maps user intent to provider/transform/feature selection
- Feature decision flowcharts (Mermaid): choose provider type, choose transport, choose auth approach
- Zero speculation: every claim cites the source `.mdx` file
- Removes TypeScript/Node section (separate skill concern)
- Adds explicit v3.0 vs v3.1 gating (CodeMode, Python-native Apps are 3.1 only)
- Reflects correct decorator syntax (`@mcp.tool` not `@mcp.tool()`)

---

## V3 Docs Breadth (Verified)

The local docs at `.claude/worktrees/fastmcp/docs/` contain 97+ `.mdx` files across these subdirectories:

- `servers/` — 39 files (tools, resources, prompts, context, auth/*, providers/*, transforms/*, plus: elicitation, sampling, tasks, storage-backends, middleware, dependency-injection, versioning, visibility, pagination, progress, telemetry, icons, logging, lifespan)
- `clients/` — 15 files (client, transports, auth/bearer+cimd+oauth, sampling, elicitation, tasks, progress, roots, notifications, logging, prompts, resources, tools, generate-cli, cli)
- `integrations/` — 26 files (Anthropic, OpenAI, Gemini, ChatGPT, Google, Claude Code, Claude Desktop, Cursor, Goose, Gemini-CLI, FastAPI, GitHub, Auth0, AuthKit, AWS Cognito, Azure, Descope, Discord, Eunomia, OCI, OpenAPI, Permit, Scalekit, Supabase, WorkOS, MCP JSON config)
- `apps/` — 2 files (overview, low-level)
- `deployment/` — 4 files (running-server, http, server-configuration, prefect-horizon)
- `patterns/` — 3 files (testing, cli, contrib)
- `getting-started/` — 5 files (welcome, installation, quickstart, upgrading/from-fastmcp-2, from-mcp-sdk, from-low-level-sdk)
- `development/` — 4 files (contributing, releases, tests, v3-notes/*)
- `python-sdk/` — 40+ auto-generated SDK reference files

---

## Real-World Usage Patterns (GitHub Research)

SOURCE: Exa search for FastMCP v3 usage patterns (accessed 2026-03-05), FastMCP release notes at `gofastmcp.com/changelog`

**Key v3 adoption patterns observed:**

1. **ProxyProvider for transport bridging** — developers wrap remote HTTP MCP servers behind local stdio servers using `create_proxy("http://remote/mcp")`. Common for enterprise environments where clients only support stdio.

2. **mount() + namespace for server composition** — teams build specialized sub-servers and compose them: `main.mount(weather_server, namespace="weather")`. This is the primary way large codebases organize tools.

3. **FileSystemProvider with reload=True for development** — hot-reload without server restart. Production deployments disable reload.

4. **SkillsProvider for AI tool skill sharing** — `ClaudeSkillsProvider()` exposes `~/.claude/skills/` as MCP resources; `sync_skills()` used to download skills from a server. Highly relevant to this plugin itself.

5. **`@mcp.tool(task=True)` for long-running ops** — requires `fastmcp[tasks]` extra; uses Docket for distributed execution with Redis. Not widely deployed yet but documented.

6. **Visibility + require_scopes for access control** — `ctx.enable_components(tags={"premium"})` unlocks features per-session; `@mcp.tool(auth=require_scopes("write"))` for endpoint-level auth.

7. **Prefect Horizon for managed deployment** — `fastmcp run server.py:mcp` via GitHub integration; free for personal use. Replacing the speculative `.mcpb` approach in current skill.

8. **CodeMode (3.1)** — dynamic tool search using BM25 + schema inspection + Python execution. Not in 3.0; do not document as current.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Scope | Client SDK is listed as an EXCLUSION in current SKILL.md but is a requested reference topic | Conflict must be resolved: include or exclude? |
| 2 | Scope | TypeScript/Node SDK coverage — current SKILL.md covers it heavily; request is silent on it | Removing it breaks users who use TypeScript path |
| 3 | Behavior | MCP server in `server/` must expose reference files — but refs are markdown inside the plugin; FileSystemProvider path will depend on install location | Server path resolution depends on how plugin is installed |
| 4 | Behavior | `plugin.json` `mcpServers` field — what command should the server run? `uv run fastmcp run server/server.py:mcp`? `python server/server.py`? | Command syntax affects users without uv |
| 5 | Behavior | "validate" helper tool — what does it validate? FastMCP server syntax? Plugin YAML frontmatter? Both? | Scope of validate tool is undefined |
| 6 | Behavior | "version-check" helper tool — compare installed fastmcp vs what version? PyPI latest? The worktree version? | Version source undefined |
| 7 | Behavior | Apps in v3.1 not yet released — should reference file document it as "upcoming" or skip entirely? | Risk of documenting unreleased features as available |
| 8 | Integration | SkillsProvider is highly relevant to THIS plugin (it could serve the plugin's own reference files) — is that the intent of the MCP server? | The MCP server's resource model is underspecified |
| 9 | User | `rwr:user-docs-to-ai-skill` skill exists and could generate reference files automatically from the local docs — is it in scope for this workflow? | Could reduce manual reference file authoring significantly |
| 10 | Scope | "real-world patterns" reference file requires GitHub search — is the Exa search sufficient, or are specific repos required? | Pattern quality depends on search completeness |

---

## Questions Requiring Resolution

### Q1: Client SDK — include or exclude?

- **Category**: Scope
- **Gap**: SKILL.md currently lists "Client-side MCP implementations" as an explicit exclusion. The request lists `client-sdk` as a reference topic target.
- **Question**: Should the overhauled skill teach users how to write FastMCP clients (using `Client`, transports, auth), or remain server-only?
- **Options**:
  - A) Include client-sdk: add `client-sdk.md` reference covering `Client`, transports, bearer/CIMD/OAuth auth, sampling, elicitation from client side
  - B) Keep exclusion: client-sdk belongs in a separate skill; the overhaul keeps server-only focus
- **Why It Matters**: Including it doubles the surface area of the skill and changes its trigger conditions. `fastmcp-client-cli` already covers CLI usage; a full client SDK reference is distinct.
- **Resolution**: **A) Include client-sdk** — explicitly listed as a reference topic in the backlog description (brainstorming session 2026-03-05). Add `client-sdk.md` covering Client, transports, bearer/CIMD/OAuth auth, sampling, elicitation from client side.

### Q2: TypeScript/Node — keep or remove?

- **Category**: Scope
- **Gap**: The current skill devotes ~200 lines to TypeScript/Node patterns. The overhaul request is silent on this.
- **Question**: Does the overhauled SKILL.md keep the TypeScript/Node path, remove it, or move it to a separate skill?
- **Options**:
  - A) Keep TypeScript section (current behavior, users can still build TS MCP servers)
  - B) Remove TypeScript section (FastMCP is Python-only; TS users use the `@modelcontextprotocol/sdk` directly)
  - C) Move to separate `typescript-mcp-server` skill in the plugin
- **Why It Matters**: TypeScript MCP servers are common. Removing this leaves a gap for users who want a TypeScript path.
- **Resolution**: **B) Remove TypeScript section** — the brainstorming session focused entirely on Python v3 FastMCP; TypeScript was not mentioned. The existing `typescript-mcp-server.md` reference file stays as-is (preserved, not overwritten) but is de-featured from the rewritten SKILL.md. TypeScript users use `@modelcontextprotocol/sdk` directly.

### Q3: MCP server command in plugin.json

- **Category**: Integration
- **Gap**: `plugin.json` `mcpServers` requires a startup command. The command must work for all users regardless of whether they have `uv`, `pip`, or a system Python.
- **Question**: What should the server startup command be?
- **Options**:
  - A) `uv run fastmcp run plugins/fastmcp-creator/server/server.py:mcp` — requires uv (standard for this repo)
  - B) `fastmcp run plugins/fastmcp-creator/server/server.py:mcp` — requires fastmcp in PATH
  - C) `python plugins/fastmcp-creator/server/server.py` — requires Python + fastmcp installed
- **Why It Matters**: Wrong command prevents the server from starting. This repo uses uv universally, so option A may be the right choice.
- **Resolution**: **A) `uv run fastmcp run plugins/fastmcp-creator/server/server.py:mcp`** — this repo uses uv universally (CLAUDE.md: "All Python via uv, uv run"). Plugin users who install via marketplace will have uv available (it is the runtime for Claude Code skills).

### Q4: MCP server resource model

- **Category**: Behavior
- **Gap**: The request says the server "serves reference files as MCP resources." This could mean:
  - Use `SkillsProvider` to expose the skill directory itself
  - Use `FileSystemProvider` to expose the `references/` folder
  - Manually register each reference file as a resource
- **Question**: Should the server use `SkillsProvider`/`FileSystemProvider` to auto-discover files, or manually register known reference files?
- **Options**:
  - A) `SkillsProvider` pointing at the plugin's skill directory — self-referential, exposes `SKILL.md` + all refs as `skill://` URIs
  - B) `FileSystemProvider("references/")` — exposes references as filesystem resources with hot-reload capability
  - C) Manual resource registration — explicit control, no dynamic discovery
- **Why It Matters**: `SkillsProvider` is the most elegant self-hosting pattern, but requires the server to know its own installation path.
- **Resolution**: **B) `FileSystemProvider("references/")` with path relative to server.py** — more portable than SkillsProvider (no install-path assumption), simpler than manual registration, enables hot-reload during development. Server resolves `references/` relative to `__file__`.

### Q5: Apps v3.1 — document or skip?

- **Category**: Behavior
- **Gap**: `apps/overview.mdx` states that FastMCP 3.1 will add a Python-native app framework but it is NOT yet released. The low-level HTML API is available in 3.0.
- **Question**: Should the `apps.md` reference document only 3.0 low-level API, or include 3.1 Python-native framework as "coming soon"?
- **Options**:
  - A) Document only what is available in 3.0 (low-level HTML + JS API)
  - B) Document 3.0 low-level with a clearly marked "FastMCP 3.1 — not yet released" section
- **Why It Matters**: Documenting unreleased features as available causes broken code. But omitting them leaves users unaware of the roadmap.
- **Resolution**: **B) Document v3.0 low-level HTML API only, with a clearly marked `> ⚠️ FastMCP 3.1 (unreleased)` callout** for the Python-native framework. This matches the fact-check verdict and prevents broken code generation.

### Q6: Use `rwr:user-docs-to-ai-skill` for reference generation?

- **Category**: Integration
- **Gap**: The `/the-rewrite-room:user-docs-to-ai-skill` skill exists at `plugins/the-rewrite-room/skills/user-docs-to-ai-skill/SKILL.md` and is designed to convert a docs directory into reference files. The worktree at `.claude/worktrees/fastmcp/docs/` is exactly the input it expects.
- **Question**: Should reference file generation delegate to `user-docs-to-ai-skill`, or should each reference file be authored directly from the docs?
- **Options**:
  - A) Delegate to `user-docs-to-ai-skill` with `.claude/worktrees/fastmcp/docs/` as input — automated, consistent with existing tooling
  - B) Author reference files manually — more control over AI-facing optimization and topic grouping
  - C) Hybrid: use `user-docs-to-ai-skill` for bulk extraction, then hand-edit grouping and SKILL.md trigger matrix
- **Why It Matters**: The reference files need to be AI-optimized (dense, citation-carrying), not just converted markdown. `user-docs-to-ai-skill` may produce the right quality, but this should be confirmed.
- **Resolution**: **C) Hybrid** — delegate to `rwr:user-docs-to-ai-skill` for bulk extraction from `.claude/worktrees/fastmcp/docs/`, then use `plugin-creator:contextual-ai-documentation-optimizer` for the SKILL.md trigger matrix and decision flowcharts. This was the explicit starting point stated in the brainstorming session.

---

## Goals (Resolved)

1. Replace all current reference files with v3-accurate, source-cited replacements generated from `.claude/worktrees/fastmcp/docs/` via `rwr:user-docs-to-ai-skill`
2. Rewrite SKILL.md with correct v3 decorator syntax, accurate provider/transform taxonomy, source citations, trigger matrix, Mermaid flowcharts — no TypeScript section
3. Add missing v3 topics: SkillsProvider, storage backends, dependency injection, telemetry, pagination, elicitation depth, middleware, client-sdk
4. Correct known errors: `require_auth` removed, `@mcp.tool` vs `@mcp.tool()`, `task=True` vs `task=TaskConfig()`
5. Build MCP server at `plugins/fastmcp-creator/server/` using FileSystemProvider("references/") for resource serving, prompts for common tasks, helper tools (scaffold, validate, version-check, search-docs)
6. Register server in `plugin.json` via `mcpServers` with command `uv run fastmcp run plugins/fastmcp-creator/server/server.py:mcp`
7. Document Apps: v3.0 low-level HTML API only; v3.1 Python-native framework marked as unreleased
8. Include client-sdk reference covering Client, transports, auth, sampling, elicitation

---

## Dependencies and Constraints

- **Local docs source**: `.claude/worktrees/fastmcp/docs/` — 97+ `.mdx` files verified present
- **Sibling skills to preserve**: `fastmcp-python-tests` and `fastmcp-client-cli` are accurate for v3 and must not be overwritten
- **`rwr:user-docs-to-ai-skill`**: Available at `plugins/the-rewrite-room/skills/user-docs-to-ai-skill/SKILL.md` — potential automation path
- **Citation requirement**: Repo CLAUDE.md requires every factual claim to cite a source
- **Plugin.json schema**: `mcpServers` field is supported and auto-starts on plugin enable (confirmed in project memory)
- **FastMCP version**: Local worktree is the v3.0+ codebase; v3.1 (CodeMode, Python-native Apps) is NOT yet released
- **No `.mcpb` packaging in v3 official docs**: The current community-practices.md `.mcpb` section is speculative; v3 official deployment docs cover Prefect Horizon, HTTP, stdio — not `.mcpb`

---

## Next Steps

After questions Q1–Q6 are resolved:

1. Update "Resolution" fields in Questions section above
2. Decide on `user-docs-to-ai-skill` delegation vs manual authoring for reference files
3. Finalize Goals section
4. Proceed to architecture design (`python-cli-design-spec` agent for the MCP server)

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-05_

### Design Refinements

1. **mcp.add_provider() vs mcp.include() — scaffold template bug**: Implementation confirmed
   `mcp.add_provider()` is the correct FastMCP v3 API for attaching providers. The implemented
   `server.py` uses it correctly. However, the `scaffold_server()` tool's generated template
   still emits `mcp.include()`, which is the old API and will fail at runtime.
   - Original: Feature context correctly identified the server as using `FileSystemProvider`; was
     silent on the specific mount method
   - Actual: `server.py` line 40 uses `mcp.add_provider()`; scaffold tool output is incorrect
   - Recorded in: plan/tasks-1-fastmcp-creator-v3-overhaul.md, DN-1

2. **accessing_online_resources.md is a phantom file**: Listed as a preserve target in both the
   feature context and task file, this file never existed in the repository. No constraint was
   violated but future plans should remove this filename from all preserve lists.
   - Original: File listed in "Files to PRESERVE" section
   - Actual: File not present; glob confirms absence
   - Recorded in: plan/tasks-1-fastmcp-creator-v3-overhaul.md, DN-2

3. **Local docs worktree is incomplete for advanced topics**: The feature context stated the worktree
   contains "97+ .mdx files verified present" but five files expected by the architecture spec were
   absent (`storage-backends.mdx`, `middleware.mdx`, `dependency-injection.mdx`, `versioning.mdx`,
   `visibility.mdx`). The `advanced.md` reference file was written from only the two available
   source files. Future work targeting these topics requires a worktree refresh.
   - Original: "97+ .mdx files verified present" — implied sufficient coverage for all 12 topics
   - Actual: Five source files absent; advanced.md covers only tasks and elicitation
   - Recorded in: plan/tasks-1-fastmcp-creator-v3-overhaul.md, DN-3
5. Proceed to task decomposition (`swarm-task-planner` agent)
