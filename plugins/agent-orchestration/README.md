# Agent Orchestration

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Scientific delegation framework for orchestrator AIs coordinating specialist sub-agents. Provides world-building context (WHERE, WHAT, WHY) while preserving agent autonomy in implementation decisions (HOW).

## Features

- **Scientific Method Alignment** - Structure delegation to enable agents to follow observation → hypothesis → prediction → experimentation → verification → conclusion
- **Observation-Based Delegation** - Replace assumptions with factual observations, preventing cascade errors
- **Success Criteria Definition** - Clear, measurable outcomes that agents verify against
- **Agent Autonomy Preservation** - List available resources instead of prescribing implementation steps
- **Pre-Delegation Verification** - Comprehensive checklist ensuring quality delegation
- **Pattern Expansion Framework** - Treat single instances as representative of broader patterns requiring systemic fixes
- **Post-Completion Validation** - Type-specific verification protocols by commit type (fix, feat, refactor, etc.)
- **Tool Selection Guidance** - High-fidelity vs low-fidelity tool selection for accurate results

## Installation

### Prerequisites

- Claude Code 2.1+ with Task tool support
- Understanding of orchestrator/sub-agent pattern

### Install Plugin

```bash
# Method 1: Using cc plugin install (if in marketplace)
cc plugin install agent-orchestration

# Method 2: Manual installation
git clone https://github.com/yourorg/agent-orchestration.git ~/.claude/plugins/agent-orchestration
cc plugin reload
```

## Quick Start

When orchestrating sub-agents, activate this skill to access the delegation framework:

```
@agent-orchestration
```

The skill automatically applies when your ROLE_TYPE is orchestrator and you're using the Task tool for delegation.

### Minimal Delegation Example

```text
Your ROLE_TYPE is sub-agent.

Fix linting errors in the project.

OBSERVATIONS:
- User requested: "Fix all linting issues"
- Project uses ruff and mypy (observed in pyproject.toml)

DEFINITION OF SUCCESS:
- Pre-commit hooks pass without errors
- All configured linting rules satisfied
- Solutions follow existing project patterns

CONTEXT:
- Location: Project root
- Python project using uv for dependency management
- Linting configuration in pyproject.toml

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria
2. Activate holistic-linting skill for linting workflows
3. Run linting tools to gather comprehensive error data
4. Research root causes for each error category
5. Implement fixes following project conventions
6. Verify /is-it-done checklist items satisfied with evidence

AVAILABLE RESOURCES:
- Check <functions> list for MCP tools - prefer specialists over built-in tools
- Python project uses `uv` - activate uv skill, use `uv run`/`uv pip`
- Full project context available including tests and configs
```

## Capabilities

| Type | Name | Description | Activation |
|------|------|-------------|------------|
| Skill | agent-orchestration | Scientific delegation framework for task delegation to sub-agents | `@agent-orchestration` |

## Usage

### Core Principle

**Provide world-building context (WHERE, WHAT, WHY). Define success criteria. Trust agent expertise for implementation (HOW).**

The orchestrator's role is to:
- Route context and observations between user and agents
- Define measurable success criteria
- Enable comprehensive discovery
- Trust agent expertise and their 200k context windows

**Do not:**
- Prescribe implementation steps (HOW)
- Pre-gather data by running commands before delegation
- Make assumptions instead of stating observations
- Limit agent discovery by restricting tool access

### Delegation Template Structure

All Task tool invocations should follow this structure:

```text
Your ROLE_TYPE is sub-agent.

[Task identification]

OBSERVATIONS:
- [Factual observations from your work or other agents]
- [Verbatim error messages if applicable]
- [Observed locations: file:line references if already known]

DEFINITION OF SUCCESS:
- [Specific measurable outcome]
- [Acceptance criteria]
- [Verification method]

CONTEXT:
- Location: [Where to look]
- Scope: [Boundaries of the task]
- Constraints: [User requirements only]

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria
2. Perform comprehensive context gathering
3. Form hypothesis based on gathered evidence
4. Design and execute experiments
5. Verify findings against authoritative sources
6. Implement solution following discovered best practices
7. Verify /is-it-done checklist items satisfied with evidence

AVAILABLE RESOURCES:
- [World-building context about ecosystem, not restrictive tool list]
- [See docs/skills.md for effective resource description patterns]
```

### Pre-Delegation Verification

Before delegating, verify the delegation includes:

✅ **Observations without assumptions**
- Raw error messages verbatim (only those already in your context)
- Observed locations (file:line references you've seen)
- Command outputs you already received
- State facts: "observed", "measured", "reported"
- Replace "I think", "probably", "seems" with verifiable observations

✅ **Definition of success**
- Specific, measurable outcome
- Acceptance criteria
- Verification method

✅ **World-building context**
- Problem location (WHERE)
- Identification criteria (WHAT)
- Expected outcomes (WHY)
- Available resources and tools

✅ **Preserved agent autonomy**
- List available tools and resources
- Trust agent's 200k context window
- Let agent choose implementation approach
- Enable agent to discover patterns

### Pattern Expansion

When user identifies a code smell, bug, or anti-pattern at a specific location, treat it as representative of a broader pattern:

**User says**: "Fix walrus operator in _some_func()"

**User means**: "Audit and fix ALL instances of this pattern throughout the file/module"

**Correct delegation**:

```text
OBSERVATIONS:
- User identified assign-then-check pattern at _some_func():45-47
- Pattern suggests developer consistently missed walrus operator opportunities
- Code smell indicates systematic review needed

DEFINITION OF SUCCESS:
- Pattern eliminated from file scope
- All assign-then-check conditionals converted where appropriate
- Similar patterns addressed in related code

YOUR TASK:
1. Fix the specific instance user identified
2. Audit entire file for similar patterns
3. Apply same fix to all discovered instances
4. Document pattern occurrences found and fixed
```

## Examples

See [docs/examples.md](./docs/examples.md) for concrete usage examples including:
- Linting task delegation
- Feature implementation delegation
- Bug fix delegation
- Investigation delegation
- Pattern expansion scenarios

## Reference Documentation

The skill includes comprehensive reference materials:

- **[clear-framework.md](./skills/agent-orchestration/clear-framework.md)** - CLEAR framework (Concise, Logical, Explicit, Adaptive, Reflective) for prompt evaluation
- **[post-completion-validation-protocol.md](./skills/agent-orchestration/post-completion-validation-protocol.md)** - Type-specific verification by commit type
- **[accessing_online_resources.md](./skills/agent-orchestration/references/accessing_online_resources.md)** - Tool selection guide (WebFetch vs Exa vs Ref)
- **Additional references** - Hallucination triggers, confidence assessment, completion criteria

See [docs/skills.md](./docs/skills.md) for complete skill documentation including reference file descriptions.

## Troubleshooting

### Agent Claims Completion Without Evidence

**Problem**: Sub-agent says "task complete" without providing execution evidence.

**Solution**: Apply post-completion validation protocol. Request specific evidence:
- Terminal output demonstrating behavior
- Test execution results (not just exit codes)
- Evidence that acceptance criteria are met

### Agent Produces Narrow Fix Instead of Systemic Fix

**Problem**: Agent fixed only the single instance user mentioned, not the pattern.

**Solution**: Apply pattern expansion framework. Delegation should state:
- User identified pattern at specific location
- Pattern indicates systematic issue
- Audit entire [file/module] for all instances

### Pre-Gathering Anti-Pattern

**Problem**: Orchestrator runs commands (linting, testing) to collect data before delegating.

**Solution**: Stop pre-gathering. Delegate with task description and success criteria. Let agent run commands themselves to gather comprehensive data in full context.

### Low-Fidelity Tool Selection

**Problem**: Agent uses WebFetch for technical documentation, receives summaries instead of source material.

**Solution**: Include in AVAILABLE RESOURCES section:
```text
- Excellent MCP servers installed - check <functions> list and prefer MCP tools:
  - `Ref` for documentation (high-fidelity verbatim source)
  - `context7` for library API docs
  - `exa` for web research
```

## Contributing

Contributions welcome. Please ensure:
- Delegation patterns follow scientific method alignment
- Examples include verification evidence
- Documentation uses observational language (not assumptions)

## License

MIT

## Credits

Developed as part of Claude Code skills ecosystem. Based on scientific delegation principles and context rot research.
