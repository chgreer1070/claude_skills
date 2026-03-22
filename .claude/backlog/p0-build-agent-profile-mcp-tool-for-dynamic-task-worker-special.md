---
name: Build agent-profile MCP tool for dynamic task-worker specialization via skill bundling
description: "Build an MCP tool that dynamically compiles agent definitions into loadable skill bundles for the task-worker.\n\nConcept: The task-worker needs to become any specialist by loading the right skills. Currently this requires knowing which skills to load. An MCP tool can automate this by reading an agent definition file, parsing its skills: frontmatter, recursively resolving each skill (SKILL.md + references/), and returning the complete agent prompt with all skill content bundled.\n\nExample flow:\n1. SAM task metadata says: agent: python-cli-architect\n2. Task-worker calls: load_agent_profile('python-cli-architect')\n3. MCP tool reads: plugins/python3-development/agents/python-cli-architect.md\n4. Parses frontmatter: skills: [python3-development, python-cli-architect]\n5. For each skill: reads SKILL.md, resolves references/ contents\n6. Returns: bundled prompt = agent body + all skill content concatenated\n7. Task-worker injects this into its context and becomes the specialist\n\nFastMCP capabilities to use:\n- SkillsDirectoryProvider for accessing skill files\n- @mcp.prompt for parameterized agent profile prompts\n- PromptsAsTools to expose prompts as callable tools\n- mount() + Namespace for composing with existing sam/backlog servers\n\nThis replaces the current pattern where the orchestrator must know which subagent_type to route to. The task-worker self-configures by loading the agent profile that matches its task metadata.\n\nAlso applies to grooming: instead of the orchestrator spawning 5 different agent types (impact-analyst, fact-checker, etc.), the grooming swarm uses task-workers that load role-specific grooming skills. The roles become skills, not agent types."
metadata:
  topic: build-agent-profile-mcp-tool-for-dynamic-task-worker-special
  source: 'Session 2026-03-22: designing peak customization for task-worker agent composition'
  added: '2026-03-22'
  priority: completed
  type: Feature
  status: done
  issue: '#979'
  last_synced: '2026-03-22T01:56:35Z'
  groomed: '2026-03-22'
  plan: plan/P979-agent-profile-mcp-tool.yaml
---

## RT-ICA

<div><sub>2026-03-22T01:51:03Z</sub>

RT-ICA Snapshot: Build agent-profile MCP tool for dynamic task-worker specialization
Goal: MCP tool that reads agent definitions, recursively resolves skills, returns bundled prompt for task-worker injection
Conditions:
1. FastMCP SkillsDirectoryProvider API | AVAILABLE | Evidence: read from providers.md reference this session
2. FastMCP @mcp.prompt API | AVAILABLE | Evidence: read from providers.md this session
3. FastMCP PromptsAsTools transform | AVAILABLE | Evidence: read from transforms.md this session
4. Agent frontmatter YAML schema (skills: field format) | DERIVABLE
5. Recursive skill path resolution from plugin directories | DERIVABLE
6. Existing sam/backlog MCP server architecture | DERIVABLE
7. Agent file locations across all plugins | DERIVABLE
8. Token budget for bundled content | DERIVABLE
9. Task-worker integration pattern | AVAILABLE | Evidence: task-worker.md created this session
AVAILABLE: 4, DERIVABLE: 5, MISSING: 0
Decision: APPROVED
</div>

## Groomed (2026-03-22)

### Issue Classification

<div><sub>2026-03-22T01:52:06Z</sub>

**Type**: Procedural

This is a new MCP tool being built from scratch with clear design, available FastMCP APIs (SkillsDirectoryProvider, @mcp.prompt, PromptsAsTools, mount/Namespace), concrete acceptance criteria, and a documented integration pattern (task-worker skill bundling).

Scope is bounded: read agent definitions, resolve skills recursively, return bundled prompt. No missing knowledge or design exploration required — the concept is validated and the implementation path is clear.
</div>

### Impact Radius

<div><sub>2026-03-22T01:52:19Z</sub>

### Scope

<div><sub>2026-03-22T01:54:56Z</sub>

**New module**: `plugins/development-harness/agent_profile/` — a FastMCP 3.x MCP server that compiles agent definitions into loadable skill bundles.

**In scope:**
- `load_agent_profile(agent_name)` tool: reads agent `.md` frontmatter, extracts `skills:` field, recursively resolves each skill URI to `SKILL.md` + `references/` content, returns bundled string (agent body + all skill content)
- Skill URI normalization: maps bare names, plugin-qualified names (`dh:skill`), and domain paths (`domains/foo`) to actual file paths across all `plugins/*/skills/` directories
- Circular dependency detection: visited-set guard during recursive resolution
- Graceful error handling: missing agent file returns error message; missing individual skill logs warning and continues with remaining skills
- `list_agent_profiles()` tool: enumerate all agents by name across plugins
- Integration with `backlog_core/server.py` via `mount()` with `profile_` namespace prefix — no new MCP server entry required in `.mcp.json`

**Out of scope:**
- Modifying existing agent files
- Changing task-worker behavior (it already loads skills; this automates skill selection)
- Caching bundled prompts across sessions (stateless tool only)
- Modifying SAM schema task objects to embed `agent_profile` field (optional future integration, not this item)
</div>

### Acceptance Criteria

<div><sub>2026-03-22T01:55:03Z</sub>

- [ ] `load_agent_profile(agent_name: str) -> str` tool exists and is callable via MCP
- [ ] Tool locates the named agent file by searching `plugins/*/agents/{agent_name}.md` across all plugins
- [ ] Tool parses YAML frontmatter from agent `.md` file and extracts the `skills:` field correctly
- [ ] Tool resolves bare skill names (e.g., `subagent-contract`), plugin-qualified names (e.g., `dh:validation-protocol`), and domain paths (e.g., `domains/enterprise-spring-xml`) to actual `SKILL.md` file paths
- [ ] Tool reads each resolved `SKILL.md` and its `references/` directory contents (all `.md` files in `references/`)
- [ ] Tool returns a single bundled string: agent body (below frontmatter) concatenated with all resolved skill content, separated by section headers
- [ ] Tool detects and breaks circular skill dependencies without infinite recursion (returns partial bundle with warning note)
- [ ] Calling `load_agent_profile("nonexistent-agent")` returns a structured error string, not a Python exception/crash
- [ ] Calling `load_agent_profile` for an agent with a missing skill in its `skills:` list returns the bundle with a warning for the missing skill but includes all resolvable skills
- [ ] `list_agent_profiles() -> list[str]` tool returns all agent names found across `plugins/*/agents/` directories
- [ ] Both tools are accessible via the mounted `backlog_core` MCP server with `profile_` namespace prefix (i.e., `profile_load_agent_profile`, `profile_list_agent_profiles`)
- [ ] Unit tests cover: frontmatter parsing, URI normalization (all three formats), recursive resolution, circular detection, missing agent, missing skill
- [ ] Integration test covers: end-to-end `load_agent_profile("task-worker")` returns non-empty string containing task-worker body and its declared skill content
</div>

### Files

<div><sub>2026-03-22T01:55:14Z</sub>

**Create (new module):**
- `plugins/development-harness/agent_profile/__init__.py`
- `plugins/development-harness/agent_profile/resolver.py` — skill URI normalization and recursive resolution logic
- `plugins/development-harness/agent_profile/server.py` — FastMCP server with `load_agent_profile` and `list_agent_profiles` tools
- `plugins/development-harness/tests/test_agent_profile_resolver.py` — unit tests for resolver
- `plugins/development-harness/tests/test_agent_profile_server.py` — integration test for end-to-end bundling

**Modify (integration):**
- `plugins/development-harness/backlog_core/server.py` — add `mcp.mount(agent_profile_server, prefix="profile")` after server construction
- `plugins/development-harness/pyproject.toml` — no new deps expected (uses `ruamel.yaml` already present; `pathlib` stdlib); confirm fastmcp already declared

**No changes required:**
- `plugins/development-harness/.mcp.json` — agent_profile mounts into backlog_core, no separate server entry needed
- `plugins/development-harness/sam_schema/server.py` — optional future integration, out of scope
- All existing agent `.md` files — read-only inputs
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — optional future integration, out of scope
</div>

### Dependencies

<div><sub>2026-03-22T01:55:19Z</sub>

**Already available — no new installs required:**
- FastMCP 3.x (`fastmcp` declared in `plugins/development-harness/pyproject.toml`) — provides `FastMCP`, `mount()`, `@mcp.tool`
- `ruamel.yaml` (already in dev-harness dependencies) — for frontmatter parsing
- Python `pathlib` (stdlib) — for file traversal
- Existing `plugins/development-harness/backlog_core/server.py` — mount target

**Structural dependencies (must exist before implementation):**
- `plugins/*/agents/*.md` files with YAML frontmatter `skills:` field — verified present (60+ files, Fact-Check Claim 4)
- `plugins/*/skills/*/SKILL.md` files — verified present (100+ files, Impact Radius)
- `plugins/*/.claude-plugin/plugin.json` manifests — needed for plugin enumeration during skill URI resolution

**No external service dependencies** — tool is purely file-system reads at call time
</div>

### Effort

<div><sub>2026-03-22T01:55:29Z</sub>

**Medium** (3–5 implementation tasks)

Breakdown:
- `resolver.py`: skill URI normalization (3 formats) + recursive file traversal + cycle detection — Medium complexity, ~150–200 lines
- `server.py`: 2 FastMCP tools + mount integration — Low complexity, ~80–100 lines
- `backlog_core/server.py` mount wiring — Low complexity, ~5 lines
- Unit tests (`test_agent_profile_resolver.py`) — Medium, ~200–300 lines (fixture agents + skills needed)
- Integration test (`test_agent_profile_server.py`) — Low, ~50–80 lines

No new dependencies to install. No schema migrations. No breaking changes to existing tools.

Primary uncertainty: skill URI normalization — three formats in the wild (`bare`, `plugin:skill`, `domain/path`) require correct mapping to `plugins/{plugin}/skills/{skill}/SKILL.md`. The resolver needs to traverse all plugins to find a match for bare names. This is well-defined but requires careful path logic.
</div>

### Resources

<div><sub>2026-03-22T01:55:35Z</sub>

**FastMCP:**
- FastMCP mount() API: `gofastmcp.com/servers/composition.md` (verified in Fact-Check Claim 3)
- FastMCP SkillsDirectoryProvider: `gofastmcp.com/servers/providers/skills.md` (verified in Fact-Check Claim 1) — reference for how skill URIs are structured
- FastMCP PromptsAsTools: `gofastmcp.com/servers/transforms/prompts-as-tools.md` (optional, if prompt exposure needed)
- Load `/fastmcp-creator:fastmcp-creator` skill before designing the server

**Existing code patterns to follow:**
- `plugins/development-harness/backlog_core/artifact_provider.py` — pattern for file-based content registration and discovery
- `plugins/development-harness/backlog_core/server.py` — target mount point and FastMCP server structure to match
- `plugins/development-harness/sam_schema/server.py` — second FastMCP server example in same codebase

**Skill resolution precedent:**
- `plugins/plugin-creator/SKILL.md` — existing skill resolution logic reference
- Agent frontmatter examples: `plugins/development-harness/agents/task-worker.md` (bare name), `plugins/dasel/agents/dasel-guide.md` (multiple formats)
</div>


## Impact Radius

### MCP Server Infrastructure (Write)
- **plugins/development-harness/backlog_core/server.py** — FastMCP 3.x server exposing backlog operations as MCP tools. Adding agent-profile tool requires extending this server with new agent profile lookup and skill bundling logic. Estimated scope: +150–200 lines for new tool method + data classes.
- **plugins/development-harness/sam_schema/server.py** — FastMCP server for SAM task/plan operations. May need hooks to populate `agent_profile` field on task objects if task-worker consumes bundled prompts. Impact: non-blocking, optional integration point.
- **plugins/development-harness/.mcp.json** — MCP server registration. Will need entry for new agent-profile server if deployed as separate service, OR tool registration if bundled into backlog_core.

### Agent Files (Read + Input)
- **plugins/development-harness/agents/task-worker.md** — Primary consumer of the new tool. Frontmatter will declare `skills` field; agent-profile tool reads agent definitions + resolves their skill dependencies recursively. Will be updated to call the new tool.
- **All agents in plugins/*/agents/*.md** (60+ across all plugins) — Input data source. The tool must traverse all agent files to read `skills:` field (YAML frontmatter), resolve skill URIs to actual skills, and build bundled prompts. Agents themselves remain read-only from tool perspective.

### Skill Files (Read + Input)
- **plugins/*/skills/*/SKILL.md** (100+ across all plugins) — Input data source. Tool must resolve skill URIs declared in agent `skills` fields to actual SKILL.md files and extract skill context/instructions for bundling.
- **plugins/development-harness/skills/dispatch/SKILL.md** — Potential consumer: if dispatch flow orchestrates task-worker invocations, it may pre-fetch bundled profiles for efficiency.
- **plugins/development-harness/skills/work-milestone/SKILL.md** — Potential consumer: if milestone dispatch does bulk task assignment.

### Plugin Manifests (Read)
- **plugins/*/.claude-plugin/plugin.json** (27 plugins) — Tool must traverse all manifests to resolve auto-discovered agent and skill locations (agents/, skills/ directories) and validate that resolved skill URIs are registered.

### Dispatch & Task Execution Flow (Update)
- **plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py** — Hook that runs after /start-task completes. May be updated to call agent-profile tool and cache bundled prompts in task context file (.claude/context/active-task-{sid}.json) for reuse by multiple tool invocations during task execution.
- **.claude/context/active-task-{CLAUDE_SESSION_ID}.json** — Runtime context file. Schema may be extended to include `bundled_agent_profile` field (optional, non-breaking).

### Testing (New + Existing)
- **plugins/development-harness/tests/** — New test suite required for agent-profile tool:
  - Unit: skill URI resolution, recursive dependency traversal, error handling (missing agents, circular skill dependencies)
  - Integration: full profile bundling end-to-end, compatibility with task-worker invocation
  - Fixtures: sample agents with varying skill declarations, mock skill files

### Documentation (New + Update)
- **plugins/development-harness/docs/agent-profile-tool.md** — NEW: Tool behavior, API contract, skill resolution algorithm, examples
- **plugins/development-harness/agents/task-worker.md** — Update: document how bundled profile is passed and consumed
- **plugins/development-harness/docs/task-execution-flow.md** — NEW/UPDATE: clarify where and when agent-profile tool is invoked in the dispatch → /start-task → /implement-feature flow

### Related Systems (Read-Only Dependencies)
- **backlog_core/models.py** — Contains Pydantic models for task objects; agent-profile tool output may require new data class (e.g., `AgentProfile` with fields: agent_name, bundled_prompt, skills_list, resolved_skill_paths). Non-breaking if added as optional field.
- **sam_schema/core/models.py** — Task model schema; same consideration as above.
- **plugins/plugin-creator/SKILL.md** — Used by agents to load/create new agents and skills. No direct impact, but agent-profile tool will need to mimic plugin-creator's skill resolution logic.

### Scope Summary
- **Writes**: 2 MCP servers (backlog_core or new agent-profile server), 1 hook update (task_status_hook.py), 1–2 new reference docs
- **Reads**: All agent files (plugins/*/agents/*.md), all skill files (plugins/*/skills/*/SKILL.md), all plugin.json manifests
- **Testing**: New unit + integration test suite (est. 500–800 lines)
- **No Breaking Changes**: Tool is additive; task-worker can adopt incrementally
</div>

## Fact-Check

<div><sub>2026-03-22T01:53:10Z</sub>

## Fact-Check

### Claim 1: FastMCP SkillsDirectoryProvider can serve skill files
**Status: VERIFIED ✓**
- **Source**: FastMCP docs (gofastmcp.com/servers/providers/skills.md)
- **Finding**: SkillsDirectoryProvider is a production-ready provider (FastMCP 3.0.0+) that scans skill directories and exposes each skill as MCP resources (skill://skillname/SKILL.md, skill://skillname/_manifest, and supporting files).
- **Implication**: Skills can be read as resources; agent-profile tool can iterate over skill URIs returned by SkillsDirectoryProvider and fetch SKILL.md content.

### Claim 2: PromptsAsTools transform exposes prompts as tools
**Status: VERIFIED ✓**
- **Source**: FastMCP docs (gofastmcp.com/servers/transforms/prompts-as-tools.md)
- **Finding**: PromptsAsTools is a production-ready transform (FastMCP 3.0.0+) that generates two tools: `list_prompts` (returns JSON metadata for all prompts) and `get_prompt` (renders a specific prompt with arguments).
- **Implication**: Agent-profile tool output (bundled prompts) can be exposed as tools via this transform if needed for tool-only clients.

### Claim 3: mount() method can compose multiple MCP servers
**Status: VERIFIED ✓**
- **Source**: FastMCP docs (github.com/jlowin/fastmcp, server.py mount() method signature)
- **Finding**: FastMCP.mount() establishes dynamic composition between servers. Mounted server's tools, resources, and prompts are accessible with optional namespace. Lifespan and middleware are invoked. Replaces deprecated import_server().
- **Implication**: Agent-profile tool can be implemented as separate MCP server and mounted into backlog_core or sam_schema servers with namespace (e.g., "profile_" prefix).

### Claim 4: Agent frontmatter has parseable skills: field
**Status: VERIFIED ✓**
- **Source**: Repo grep across plugins/*/agents/*.md (60+ files)
- **Finding**: All examined agents have YAML frontmatter with `skills:` field containing comma-separated skill identifiers or full URIs (e.g., `skills: subagent-contract`, `skills: dh:validation-protocol, clear-cove-task-design`).
- **Examples**:
  - `plugins/development-harness/agents/task-worker.md`: `skills: dh:subagent-contract`
  - `plugins/development-harness/agents/swarm-task-planner.md`: `skills: clear-cove-task-design`
  - `plugins/dasel/agents/dasel-guide.md`: `skills: dasel-reference, domains/enterprise-installanywhere, ...` (7 skills)
- **Implication**: Agent-profile tool can parse agent frontmatter, extract skills field, and resolve URIs to actual skill files.

### Additional Observations
- **Skill URI formats found**: Some use bare names (e.g., `subagent-contract`), some use plugin-qualified names (e.g., `dh:subagent-contract`), some use domain paths (e.g., `domains/enterprise-spring-xml`). Agent-profile tool must normalize these to locate actual SKILL.md files across all plugin directories.
- **Circular dependency risk**: Some skills may declare dependencies on other skills (not yet verified in this fact-check). Agent-profile tool must include cycle detection.
- **Precedent for skill resolution**: plugin-creator plugin already implements skill resolution logic; agent-profile tool should reuse or mirror this pattern.

### Conclusion
All four claims are technically sound. FastMCP provides the necessary components; repo structure supports the implementation pattern. No blocking issues identified.
</div>

## RT-ICA

<div><sub>2026-03-22T01:56:35Z</sub>

RT-ICA Final: Build agent-profile MCP tool for dynamic task-worker specialization
Goal: MCP tool that reads agent definitions, recursively resolves skills, returns bundled prompt
Conditions:
1. FastMCP SkillsDirectoryProvider API | Snapshot: AVAILABLE → Final: AVAILABLE
2. FastMCP @mcp.prompt API | Snapshot: AVAILABLE → Final: AVAILABLE
3. FastMCP PromptsAsTools transform | Snapshot: AVAILABLE → Final: AVAILABLE
4. Agent frontmatter YAML schema | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: fact-checker verified skills: field in agent files
5. Recursive skill path resolution | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: groomer documented 3 URI formats + bare-name search
6. Existing MCP server architecture | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: impact-analyst mapped backlog_core/server.py mount pattern
7. Agent file locations | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: impact-analyst inventoried all plugin agent directories
8. Token budget for bundled content | Snapshot: DERIVABLE → Final: AVAILABLE | Evidence: groomer addressed via references/ inclusion strategy
9. Task-worker integration | Snapshot: AVAILABLE → Final: AVAILABLE
10. (new) Artifact manifest system available | Final: AVAILABLE | Evidence: user provided architecture overview this session
Changes from snapshot:
- Conditions 4-8: DERIVABLE → AVAILABLE (resolved by swarm agents)
- Condition 10: new, AVAILABLE (artifact manifest MCP tools exist)
AVAILABLE: 10, DERIVABLE: 0, MISSING: 0
Decision: APPROVED
</div>