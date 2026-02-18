# Ecosystem Context Patterns

Detailed analysis of ECOSYSTEM CONTEXT anti-patterns and correct patterns for delegating to sub-agents.

## Anti-Pattern: Tool List Enumeration

**Why this anti-pattern is harmful:**

The tool-list anti-pattern comes from slot-filling behavior triggered by the word "RESOURCES." When the orchestrator sees a list-style heading during generation, it fills the slot with the most readily available pattern from training data — tool names.

**Anti-pattern example (reductive, limiting):**

```text
AVAILABLE RESOURCES:
- WebFetch tool
- Read tool
- Bash tool
```

**Problems with this pattern:**

1. Lists specific tools implying these are the only options available
2. Listing `WebFetch` without mentioning superior MCP alternatives causes agents to use low-fidelity tools
3. Provides no context about the project ecosystem or toolchain
4. Agents cannot make informed tool selection decisions from a tool list alone
5. Omits authenticated CLIs, MCP specialists, activated skills, and domain conventions

**Why tool lists feel natural but are wrong:**

The orchestrator has 50+ tools available, including specialized MCP servers for documentation, web research, GitHub, Docker, and more. A list of 3 generic tools implies the rest do not exist or should not be used. This is the opposite of empowering world-building context.

---

## Correct Pattern: Ecosystem Description

**What world-building context achieves:**

- Agent understands the project toolchain and can make informed decisions
- Agent knows which MCP servers are preferred for which tasks
- Agent understands activated skills and domain conventions
- Agent can discover better approaches because full context is available

**Correct pattern example (world-building, empowering):**

```text
ECOSYSTEM CONTEXT:
- The `gh` CLI is pre-authenticated for GitHub operations (issues, PRs, API queries)
- Excellent MCP servers installed — check your <functions> list and prefer MCP tools
  (like `Ref`, `context7`, `exa`) over built-in alternatives since they are domain specialists
- This Python project uses `uv` — activate the `uv` skill, use `uv run python` instead of
  `python3`, `uv pip` instead of `pip`
- Project uses `hatchling` as build backend — activate the `hatchling` skill for build/publish guidance
- Recent linting fixes documented in `.claude/reports/` showing common issues and resolutions
- Package validation scripts in `./scripts/` — check README.md for available validators
- Full project context available including tests, configs, and documentation
```

**Why this works:**

1. Describes the ecosystem — agent knows what tools are contextually relevant
2. Names preferred MCP alternatives — agent avoids low-fidelity fallbacks
3. Specifies activated skills — agent leverages domain expertise
4. Points to relevant documentation locations — agent discovers efficiently
5. Full project access confirmed — agent does not artificially limit scope

---

## Pattern Components

### Authenticated CLI Tools

When CLI tools are pre-authenticated, explicitly state this:

```text
The `gh` CLI is pre-authenticated for GitHub operations
The `glab` CLI is configured for GitLab access
AWS CLI is configured with appropriate credentials
```

**Why**: Agents default to API-based approaches when CLI availability is unknown. Stating authentication removes this uncertainty.

### MCP Server Preferences

Name which MCP servers are available and why they are preferred:

```text
Excellent MCP servers installed — check <functions> list and prefer these specialists:
- `Ref` — high-fidelity verbatim documentation (unlike WebFetch which returns AI summaries)
- `context7` — library API docs (current versions, comprehensive)
- `exa` — web research (curated, high-quality sources)
- `mcp-docker` — container operations
```

**Documentation fidelity hierarchy:**

- `Ref` — high fidelity (output IS the source, verbatim)
- `exa` — medium fidelity (Markdown-formatted extraction, preserves code blocks)
- `WebFetch` — low fidelity (summarized, strips specifics) — NEVER for "how-to" implementation

See [Accessing Online Resources](./accessing_online_resources.md) for tool selection criteria and experimental evidence.

### Language and Tooling Ecosystems

State the toolchain so agents use correct commands:

```text
Python project using `uv` — activate `uv` skill, use `uv run`/`uv pip` exclusively
Node project using `pnpm` — use `pnpm` instead of `npm`
Rust project — use `cargo` commands, check Cargo.toml for features
```

### Baseline Context (Always Include)

Every delegation should include this baseline:

```text
ECOSYSTEM CONTEXT:
- Full project context available — explore freely with all tools
- Check <functions> list for MCP tools — prefer MCP specialists (Ref, context7, exa) over built-in alternatives
- Check <available_skills> and activate relevant skills for domain expertise
- Maximize parallel execution for independent tool calls
- [Add project-specific context here: authenticated CLIs, toolchain conventions, validation scripts]
```

The last line is the single customization point. The baseline above it is always correct.

---

## Common Mistakes Reference

| Mistake | What it does | Better approach |
|---|---|---|
| `- WebFetch tool` | Names a low-fidelity tool without context | `Excellent MCP servers available — prefer Ref/exa over WebFetch` |
| `- Read tool` | States a universal capability as if it's special | Omit — agents always have Read; describe what's worth reading |
| `- Bash tool` | States a universal capability | Omit — describe what bash-accessible tooling is relevant |
| Tool list only | No ecosystem context | Describe the toolchain, authenticated CLIs, activated skills |
| Missing MCP names | Agent defaults to WebFetch | Name Ref, context7, exa and their specializations |
| No skill references | Agent misses domain expertise | Name activated skills and what they provide |

SOURCE: Prior diagnostic session identifying 6 structural causes of orchestrator tool-enumeration anti-pattern (2026-02-17)
