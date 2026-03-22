# Feature Context: Agent-Profile MCP Tool

## Document Metadata

- **Generated**: 2026-03-22
- **Agent**: feature-researcher
- **Source**: Backlog item #979 — "Build agent-profile MCP tool for dynamic task-worker specialization via skill bundling"
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Build an MCP tool that dynamically compiles agent definitions into loadable skill bundles for the
task-worker. The tool reads an agent definition file, parses its `skills:` frontmatter, recursively
resolves each skill (SKILL.md + references/), and returns the complete agent prompt with all skill
content bundled. This replaces the current pattern where the orchestrator must know which
`subagent_type` to route to — the task-worker self-configures by loading the agent profile that
matches its task metadata.

---

## WHAT: Desired Outcome

An agent (the task-worker or any orchestrator) can call a single MCP tool with an agent name and
receive back a complete, ready-to-inject bundle containing:

- The named agent's instruction body (the text below frontmatter in the `.md` file)
- All skill content declared in that agent's `skills:` field — each skill's SKILL.md and its
  `references/` directory contents

A companion tool lists all available agent names across all plugins, enabling discovery without
requiring the caller to know plugin structure.

### Success Conditions

1. A task-worker receiving a SAM task with `agent: python-cli-architect` in its metadata can call
   `load_agent_profile("python-cli-architect")` and immediately operate as a Python CLI specialist,
   without the orchestrator pre-selecting a `subagent_type`.
2. A dispatch orchestrator can spawn identical task-workers for parallel tasks; each worker
   self-specializes by reading its task's `agent:` field and loading the corresponding profile.
3. Any agent can enumerate available profiles without filesystem knowledge via `list_agent_profiles()`.

---

## WHY: Problem Being Solved

### Current State

The dispatch layer (orchestrator running `/dh:dispatch` or `/dh:work-milestone`) must know the
exact `subagent_type` string for every specialist agent and route each task to the correct one.
This creates tight coupling:

- Adding a new specialist agent requires updating dispatch routing logic, not just creating an
  agent file.
- Dispatching a grooming swarm requires the orchestrator to track 5+ different agent types
  (impact-analyst, fact-checker, scope-definer, etc.) and route each role correctly.
- The task-worker already loads skills from task metadata via `Skill()` calls, but the caller must
  supply the skill list — the worker cannot derive it from the agent definition itself.

### Root Cause

Agent identity (what skills and instructions define a specialist) is encoded in agent `.md` files,
but the dispatch layer cannot read those files at routing time. The information exists but is
inaccessible without an additional resolution step.

### Desired State

Task-workers self-configure. The SAM task says `agent: python-cli-architect` and the worker calls
the MCP tool to load that profile at runtime. The dispatch layer becomes agent-agnostic: it spawns
workers and workers determine their own specialization. Adding a new specialist is a matter of
creating an agent file — no dispatch changes required.

---

## Stakeholders

### Primary

**Task-worker agent** (`plugins/development-harness/agents/task-worker.md`) — the universal SAM
task executor that self-configures by loading skills. This tool directly enables its design intent:
the task-worker becomes any specialist at runtime without the orchestrator enumerating skill lists.

**Dispatch orchestrators** (agents using `/dh:dispatch` and `/dh:work-milestone`) — currently
must maintain per-agent routing tables. With this tool, dispatch logic simplifies to: spawn
task-worker + set agent name in task metadata.

### Secondary

**Grooming swarms** — the grooming workflow spawns multiple role-specific workers. Roles becoming
loadable profiles (instead of distinct `subagent_type` values) reduces the swarm's configuration
surface and makes new grooming roles addable without orchestrator changes.

**Plugin authors** — each new agent file becomes immediately available as a loadable profile,
with no registration step beyond creating the file with valid frontmatter.

---

## Risks

### R1: Consumption mechanism mismatch

The task-worker currently calls `Skill(skill="{name}")` for each skill individually. A bundled
string returned by `load_agent_profile()` is a different mechanism — it is text, not a skill
activation command. If the task-worker cannot inject the bundled string into its working context
effectively, the specialization does not take effect. This is the highest-risk open question.

### R2: SAM task schema does not expose the `agent:` field as structured data

The flow depends on task metadata containing a parseable `agent:` field that `sam_read` returns
in its JSON response. If this field exists only in markdown display (legacy format) but not in the
structured JSON output, the task-worker cannot read it programmatically. The feature only delivers
value if the agent name reaches the worker as structured data.

### R3: Name collision across plugins

Multiple plugins may define agents with the same filename (e.g., `code-reviewer.md` in two
different plugins). Bare-name resolution (`load_agent_profile("code-reviewer")`) becomes
ambiguous. Silent wrong-agent resolution would be harder to detect than an explicit error.

### R4: Bundled content size

An agent with many skills (e.g., 6–8 skills, each with a references/ directory) could produce a
bundled string exceeding the practical context injection size. There is no established limit for
what a task-worker can usefully absorb in a single profile load.

### R5: Stale profiles at runtime

Agent and skill files are read from disk at call time. If a skill file is deleted or moved between
plugin updates, the tool either fails or returns an incomplete bundle. Partial profiles (some
skills missing) may be worse than a clear failure, since the worker operates under a false
assumption of complete specialization.

### R6: Circular skill dependencies

If skill A declares a dependency on skill B which declares a dependency on skill A (directly or
transitively), naive recursive resolution loops infinitely. This must be detected and broken, but
the correct behavior when a cycle is found (fail, warn, or truncate) is not specified.

---

## Open Questions

### Q1: How does the task-worker consume the bundled profile string?

The task-worker currently calls `Skill(skill="{name}")` for each skill. A bundled string is text,
not a skill activation. Does the worker:

- Treat the string as context injected into its working memory (like reading a document)?
- Use the profile tool to get a list of resolved skill paths, then call `Skill()` for each?
- Use both: bundled content for immediate use AND structured skill list for formal loading?

**Why it matters**: Determines the tool's return type (string vs. structured data) and whether
the task-worker agent file needs modification to use this tool.

### Q2: Does `sam_read` return the `agent:` field as structured data?

The flow depends on `sam_read` returning the task's `agent:` value in its JSON response. The
legacy markdown format has an `**Agent**:` field, but it is unclear whether this propagates through
`sam_read` as a named key or is only available in raw markdown.

**Why it matters**: If the agent field is not in `sam_read` output, the task-worker cannot
self-specialize — the orchestrator must explicitly tell it which profile to load, which moves the
coupling back into the dispatch layer.

### Q3: How are agent name collisions across plugins resolved?

Multiple plugins could define agents with the same filename. When a bare name is used
(e.g., `load_agent_profile("code-reviewer")`), should the tool:

- Require plugin-qualified names always (e.g., `python3-development:code-reviewer`)?
- Allow bare names when unambiguous; error when multiple matches exist?
- Use a priority order (e.g., the plugin owning the task's plugin namespace wins)?

**Why it matters**: Bare names are simpler for task metadata but create silent failure modes when
the wrong plugin's agent is loaded.

### Q4: Does the grooming use case need skill-only bundles without an agent file?

The backlog item mentions grooming roles becoming "skills, not agent types." Some grooming roles
may not have corresponding agent `.md` files — they would be pure skill bundles. Should the tool
support `load_skill_bundle(skills: list[str])` as a second entry point, or do all profiles
require an agent file?

**Why it matters**: Determines whether grooming roles must create agent files or can compose
skills ad hoc.

### Q5: What happens when a profile is partially resolvable?

If an agent declares 6 skills and 1 is missing, should the tool:

- Return the partial bundle with a warning?
- Fail entirely?
- Return the full bundle minus the missing skill with no indication?

**Why it matters**: Silent partial profiles cause the worker to operate under a false assumption
of complete specialization. A clear failure is easier to debug than silent missing context.

### Q6: What frontmatter fields should the bundle include?

Agent frontmatter contains `tools:`, `model:`, `skills:`, `name:`, `description:`. The
task-worker cannot change its own tool permissions or model at runtime. Should the bundle include:

- Body + skills only (the injectable content)?
- Full frontmatter as a structured header + body + skills (informational; consumer decides)?

**Why it matters**: Including `tools:` and `model:` adds information the worker cannot currently
act on, but may be useful for orchestrators making routing decisions.

---

## Codebase Research

### Existing Patterns

**Task-worker skill loading** (`plugins/development-harness/agents/task-worker.md`, lines 39–45):
The task-worker already loads skills from task metadata by iterating the `skills:` field and
calling `Skill(skill="{name}")` for each. The agent-profile tool extends this: instead of the
orchestrator supplying the skill list, the worker derives it from the agent definition.

**Agent files with `skills:` declarations**: Verified across 28+ agent files in 8 plugins.
Three URI formats are in active use:

1. Bare names: `subagent-contract`, `clear-cove-task-design`
2. Plugin-qualified names: `dh:subagent-contract`, `dh:validation-protocol`
3. Domain paths: `domains/enterprise-installanywhere`, `domains/enterprise-spring-xml`

All three formats must be resolvable to actual SKILL.md files. SOURCE: grep across
`plugins/*/agents/*.md` (verified 2026-03-22, backlog item #979 fact-check section).

**File-based content discovery** (`plugins/development-harness/backlog_core/artifact_provider.py`):
An existing pattern for traversing plugin directories and discovering registered content. The
agent-profile tool does analogous work — discovering agent files and resolving their dependencies
to file paths.

**MCP server composition** (`plugins/development-harness/backlog_core/server.py`): The backlog
MCP server demonstrates FastMCP `mount()` for composing sub-servers with namespace prefixes. The
agent-profile server would follow this same composition pattern. SOURCE: verified in backlog item
#979 fact-check (Claim 3, 2026-03-22).

### Code References

- `plugins/development-harness/agents/task-worker.md` — primary consumer; current skill loading pattern
- `plugins/development-harness/backlog_core/artifact_provider.py` — file discovery pattern
- `plugins/development-harness/backlog_core/server.py` — candidate server for composition
- `plugins/development-harness/sam_schema/server.py` — second server in same plugin, structural reference
- `plugins/development-harness/skills/dispatch/SKILL.md` — current dispatch routing (the pattern being replaced)

---

## Use Scenarios

### Scenario 1: Task-worker self-specializes from SAM task metadata

A SAM task has `agent: python-cli-architect` in its metadata. The task-worker reads this field,
calls `load_agent_profile("python-cli-architect")`, and receives the agent's instruction body
plus all skills declared in that agent's frontmatter. The worker injects this into its context
and operates as a Python CLI specialist for the remainder of the task. The dispatch orchestrator
did not need to know the agent type at routing time.

### Scenario 2: Dispatch creates a homogeneous worker team

Multiple SAM tasks are ready. Each specifies a different `agent:` value. The orchestrator spawns
identical task-workers with identical delegation prompts. Each worker reads its own task's
`agent:` field and calls `load_agent_profile()` independently. No per-agent routing tables in the
dispatch logic.

### Scenario 3: Grooming swarm with loadable roles

A grooming swarm needs impact analysis, fact-checking, and scope definition. Instead of spawning
three different `subagent_type` values, the orchestrator spawns three task-workers. Each calls
`load_agent_profile("impact-analyst")`, `load_agent_profile("fact-checker")`, etc. New grooming
roles are added by creating agent files — no swarm orchestration changes required.

### Scenario 4: Discovering available specialists

An orchestrator planning dispatch needs to know what agents exist. `list_agent_profiles()` returns
all agent names across all plugins without requiring plugin filesystem knowledge.

---

## Goals (Pending Resolution of Open Questions)

1. Task-workers can self-specialize by loading an agent profile at runtime, eliminating
   per-agent routing in the dispatch layer.
2. All agent definitions across all plugins are discoverable and enumerable via a single MCP tool
   call.
3. Skill URI resolution handles all three formats found in the codebase (bare, plugin-qualified,
   domain path).
4. Missing or circular skill dependencies produce observable warnings rather than silent partial
   output.
5. The tool integrates with the existing MCP server infrastructure without requiring a new
   top-level server entry (pending Q3 resolution on mount point).
6. The bundled output format enables the task-worker to operate as the named specialist
   (pending Q1 resolution on consumption mechanism).

---

## Next Steps

1. Resolve Q1 (consumption mechanism) and Q2 (SAM schema field availability) — both gate whether
   the task-worker needs modification as part of this feature or can adopt the tool unchanged.
2. Resolve Q3 (name collision strategy) — gates the tool's API contract.
3. After questions are resolved: proceed to architecture design via `python-cli-design-spec` agent.
