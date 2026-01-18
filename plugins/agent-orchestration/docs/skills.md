# Skills Reference

## agent-orchestration

**Location**: `skills/agent-orchestration/SKILL.md`

**Description**: This skill should be used when the model's ROLE_TYPE is orchestrator and needs to delegate tasks to specialist sub-agents. Provides scientific delegation framework ensuring world-building context (WHERE, WHAT, WHY) while preserving agent autonomy in implementation decisions (HOW). Use when planning task delegation, structuring sub-agent prompts, or coordinating multi-agent workflows.

**User Invocable**: Yes

**When to Use**:
- When your ROLE_TYPE is orchestrator
- Before using the Task tool to delegate to sub-agents
- When structuring sub-agent prompts
- When coordinating multi-agent workflows
- When verifying sub-agent completion claims

### Activation

```
@agent-orchestration
```

or

```
Skill(command: "agent-orchestration")
```

The skill automatically applies when orchestrating sub-agent tasks.

### Core Framework Components

#### 1. Scientific Method Alignment

Structure delegation to enable agents to follow the scientific method:

1. **Observation** → Provide factual observations, not interpretations
2. **Hypothesis** → Let agent form their own hypothesis
3. **Prediction** → Let agent make testable predictions
4. **Experimentation** → Let agent design and execute tests
5. **Verification** → Let agent verify against official sources
6. **Conclusion** → Let agent determine if hypothesis is rejected

**Reason**: Agents apply the scientific method most effectively when they receive observations and success criteria rather than pre-formed conclusions and prescribed steps.

#### 2. Pre-Delegation Verification Checklist

Before delegating, verify the delegation includes:

✅ **Observations without assumptions**
- Raw error messages verbatim (only those already in your context)
- Observed locations (file:line references where issues were seen)
- Command outputs you already received during your work
- State facts using "observed", "measured", "reported"
- Replace "I think", "probably", "likely", "seems" with verifiable observations

⚠️ **Critical: Pass-Through vs. Pre-Gathering**
- **Pass-through (correct)**: Include data already in your context (user messages, prior agent reports, errors you encountered)
- **Pre-gathering (incorrect)**: DO NOT run commands to collect data for the agent - they will gather their own data
- Example: DO NOT run `ruff check .` or `pytest` to collect errors before delegating to linting/testing agents
- **Reason**: Pre-gathering wastes context, duplicates agent work, and causes context rot

✅ **Definition of success**
- Specific, measurable outcome
- Acceptance criteria
- Verification method
- Focus on WHAT must work, not HOW to implement it

✅ **World-building context**
- Problem location (WHERE)
- Identification criteria (WHAT)
- Expected outcomes (WHY)
- Available resources and tools

✅ **Preserved agent autonomy**
- List available tools and resources
- Trust agent's 200k context window for comprehensive analysis
- Let agent choose implementation approach
- Enable agent to discover patterns and solutions

#### 3. Delegation Template

**Full template structure:**

```text
Your ROLE_TYPE is sub-agent.

[Task identification]

OBSERVATIONS:
- [Factual observations from your work or other agents]
- [Verbatim error messages if applicable]
- [Observed locations: file:line references if already known]
- [Environment or system state if relevant]

DEFINITION OF SUCCESS:
- [Specific measurable outcome]
- [Acceptance criteria]
- [Verification method]
- Solution follows existing patterns found in [reference locations]
- Solution maintains or reduces complexity

CONTEXT:
- Location: [Where to look]
- Scope: [Boundaries of the task]
- Constraints: [User requirements only]

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria for this task type
2. Use the /is-it-done checklists as your working guide throughout this task
3. Perform comprehensive context gathering using:
   - Available functions and MCP tools from the <functions> list
   - Relevant skills from the <available_skills> list
   - Project file exploration and structure analysis
   - External resources (CI/CD logs, API responses, configurations)
   - Official documentation and best practices
   - Known issues, forums, GitHub issues if relevant
4. Form hypothesis based on gathered evidence
5. Design and execute experiments to test hypothesis
6. Verify findings against authoritative sources
7. Implement solution following discovered best practices
8. Verify each /is-it-done checklist item as you complete it
9. Only report completion after all /is-it-done criteria satisfied with evidence

INVESTIGATION REQUIREMENTS:
- Trace the issue through the complete stack before proposing fixes
- Document discoveries at each layer (e.g., UI → Logic → System → Hardware)
- Identify both symptom AND root cause
- Explain why addressing [root] instead of patching [symptom]
- If proposing workaround, document why root cause cannot be fixed

VERIFICATION REQUIREMENTS:
- /is-it-done is step 1 of YOUR TASK - run it before starting work
- Use /is-it-done checklists as working guide, not post-mortem report
- Provide evidence for each checklist item as you complete it
- If checklist reveals missing work, complete that work before proceeding
- Your work will be reviewed by a rigorous engineer who expects verified functionality

AVAILABLE RESOURCES:
[See "Writing Effective AVAILABLE RESOURCES" section below]
```

#### 4. Writing Effective AVAILABLE RESOURCES

The AVAILABLE RESOURCES section provides world-building context about the environment, not a restrictive tool list.

**Anti-pattern (reductive, limiting):**

```text
AVAILABLE RESOURCES:
- WebFetch tool
- Read tool
- Bash tool
```

**Problem**: Lists specific tools, implying these are the only options. Agent has dozens of tools but now thinks they should only use three.

**Correct pattern (world-building, empowering):**

```text
AVAILABLE RESOURCES:
- The `gh` CLI is pre-authenticated for GitHub operations (issues, PRs, API queries)
- Excellent MCP servers are installed for specialized tasks - check your <functions> list and prefer MCP tools (like `Ref`, `context7`, `exa`) over built-in alternatives since they're specialists at their domain
- This Python project uses `uv` for all operations - activate the `uv` skill and use `uv run python` instead of `python3`, `uv pip` instead of `pip`
- Project uses `hatchling` as build backend - activate the `hatchling` skill for build/publish guidance
- This repository uses GitLab CI - use `gitlab-ci-local` to validate pipeline changes locally before pushing
- Recent linting fixes are documented in `.claude/reports/` showing common issues and resolutions
- Package validation scripts live in `./scripts/` - check its README.md for available validators to run after changes
- Full project context available including tests, configs, and documentation
```

**Why this works**:
1. Describes capabilities, not constraints
2. Provides context for tool selection
3. References skills to activate
4. Points to project-specific resources
5. Explains ecosystem conventions

##### Resource Description Patterns

**For authenticated CLI tools:**

```text
The `gh` CLI is pre-authenticated for GitHub operations
The `glab` CLI is configured for GitLab access
AWS CLI is configured with appropriate credentials
```

**For MCP server preferences:**

```text
Excellent MCP servers installed - check <functions> list and prefer these specialists:
- `Ref` for documentation (high-fidelity verbatim source, unlike WebFetch which returns AI summaries)
- `context7` for library API docs (current versions, comprehensive)
- `exa` for web research (curated, high-quality sources)
- `mcp-docker` for container operations
```

**For language/tooling ecosystems:**

```text
Python project using `uv` - activate `uv` skill, use `uv run`/`uv pip` exclusively
Node project using `pnpm` - use `pnpm` instead of `npm`
Rust project - use `cargo` commands, check Cargo.toml for features
```

**For CI/CD validation:**

```text
GitHub Actions - use `act` to validate workflow changes locally
GitLab CI - use `gitlab-ci-local` to test pipeline before pushing
Code quality checks (linting, formatting) performed and issues addressed per the holistic-linting skill
```

#### 5. Pattern Expansion Framework

**Core Principle**: When user identifies a code smell, bug, or anti-pattern at a specific location, treat it as a symptom of a broader pattern that likely exists elsewhere.

**What users say:**
- "Fix walrus operator in _some_func()"
- "Add error handling to this API call"
- "This validation is duplicated"

**What users mean:**
- "The developer consistently missed this pattern throughout the codebase"
- "Audit and fix ALL instances of this pattern, not just the one I pointed out"
- "This instance represents a systemic issue"

**Holistic delegation (enables agent understanding):**

```text
OBSERVATIONS:
- User identified assign-then-check pattern at _some_func():45-47
- This suggests developer consistently missed walrus operator opportunities
- Code smell indicates systematic review needed across file/module

DEFINITION OF SUCCESS:
- Pattern eliminated from [file/module] scope
- All assign-then-check conditionals converted to walrus where appropriate
- Similar patterns addressed in related code

YOUR TASK:
1. Run SlashCommand /is-it-done to understand completion criteria
2. Fix the specific instance user identified
3. Audit entire [file/module] for similar patterns
4. Apply same fix to all discovered instances
5. Document pattern occurrences found and fixed
6. Verify /is-it-done checklist items satisfied with evidence
```

#### 6. Post-Completion Validation Protocol

The orchestrator must verify sub-agent completion claims using type-specific verification:

**For bug fixes (fix:)**
- Require proof bug reproduced before fix
- Require proof same test now passes
- Require edge case testing evidence
- Require regression test suite results

**For features (feat:)**
- Require end-to-end demonstration
- Require ALL acceptance criteria verification
- Require edge case testing evidence
- Require integration testing proof

**For refactoring (refactor:)**
- Require proof tests passed before refactoring
- Require proof tests still pass after refactoring
- Require proof behavior unchanged
- Require proof performance not degraded

See [post-completion-validation-protocol.md](../skills/agent-orchestration/post-completion-validation-protocol.md) for complete verification checklists by commit type.

#### 7. Tool Selection Guidance

For accurate results, agents must use high-fidelity tools for technical documentation:

| Tool | Fidelity | Purpose | Use When |
|------|----------|---------|----------|
| **WebFetch** | **Low** (Summarized) | Scoping & Overview | Need high-level summary, NOT implementation details |
| **Exa** | **Medium** (Markdown) | Content Extraction | Need code snippets, structured content |
| **Ref** | **High** (Verbatim) | Deep Reading | Need authoritative, verbatim technical documentation |

**Critical Rule**: NEVER use WebFetch for "How-To" guides. Use Ref or Exa for technical documentation to ensure accuracy, precision, and fidelity.

See [accessing_online_resources.md](../skills/agent-orchestration/references/accessing_online_resources.md) for detailed tool selection guide.

### Reference Files

The skill includes comprehensive reference documentation:

#### Skill Root Directory

- **[clear-framework.md](../skills/agent-orchestration/clear-framework.md)** - CLEAR framework (Concise, Logical, Explicit, Adaptive, Reflective) for evaluating and improving prompts
- **[hallucination-triggers.md](../skills/agent-orchestration/hallucination-triggers.md)** - Identifying and avoiding hallucination triggers in delegation
- **[how-confident.md](../skills/agent-orchestration/how-confident.md)** - Assessing confidence levels in agent responses
- **[is-it-done_gemini.md](../skills/agent-orchestration/is-it-done_gemini.md)** - Completion criteria by task type (Gemini-optimized version)
- **[post-completion-validation-protocol.md](../skills/agent-orchestration/post-completion-validation-protocol.md)** - Type-specific verification protocols by commit type

#### References Subdirectory

- **[accessing_online_resources.md](../skills/agent-orchestration/references/accessing_online_resources.md)** - Definitive guide for tool selection (WebFetch vs Exa vs Ref)
- **[synthesis-improvements-from-research.md](../skills/agent-orchestration/references/synthesis-improvements-from-research.md)** - Research-based improvements to delegation framework

### Common Anti-Patterns to Avoid

#### The Pre-Gathering Anti-Pattern

**Problem**: Running commands to collect data before delegating wastes context and duplicates agent work.

**Example**:
```text
❌ INCORRECT: Pre-gathering linting errors

User: "Address linting issues"
Orchestrator runs: ruff check .
Orchestrator captures: 244 errors
Orchestrator pastes: All 244 errors into delegation prompt

Problem: Wasted context. Agent would run linting anyway to gather comprehensive data.
```

**Correct Pattern**:
```text
✅ CORRECT: Delegate with context and success criteria

"Run linting against the project. Resolve all issues at root cause.

SUCCESS CRITERIA:
- Code quality checks (linting, formatting) performed and issues addressed per the holistic-linting skill
- All configured linting rules satisfied
- Solutions follow project patterns

CONTEXT:
- Python project using ruff and mypy
- Configuration in pyproject.toml"
```

#### The Assumption Cascade

**Problem**: Stating "I think the issue is X, which probably means Y, so likely Z needs fixing" creates chain of unverified assumptions.

**Replace with**: "[Observed symptoms]. Success: [desired behavior]. Investigate comprehensively before implementing."

#### The Prescription Trap

**Problem**: Instructing "Fix this by doing A, then B, then C" prevents agent from discovering better approaches.

**Replace with**: "Fix [observation]. Success: [outcome]. Available resources: [list]."

#### The Reductive Tool List

**Problem**: Listing "AVAILABLE RESOURCES: WebFetch, Read, Bash" when agent has 50+ tools including specialized MCP servers.

**Replace with**: World-building context that describes the ecosystem:

```text
AVAILABLE RESOURCES:
- The `gh` CLI is pre-authenticated for GitHub operations
- Excellent MCP servers installed - check <functions> list and prefer MCP tools over built-in alternatives
- This Python project uses `uv` - activate the `uv` skill
- Recent fixes documented in `.claude/reports/`
```

### Role-Specific Rules for Orchestrators

As an orchestrator, your role is:

1. **Context router, not researcher**
   - Pass observations through to agents
   - Do NOT run analysis commands to gather data for agents
   - Let agents generate research and discoveries

2. **Success definer, not implementation planner**
   - Define what must work when done
   - Specify how to verify completion
   - Trust agents to determine steps

3. **Discovery enabler, not scope limiter**
   - List available resources
   - Enable comprehensive investigation
   - Trust agent judgment on scope

4. **Agent capability truster**
   - Agents have comprehensive documentation access
   - Agents have 200k context windows
   - Agents know their specialized domains

5. **Scientific rigor maintainer**
   - State only what you've observed
   - Mark assumptions explicitly when necessary
   - Enable agent verification protocols

### Verification Questions Before Delegating

Before sending delegation, verify:

1. **Am I enabling full discovery?**
   - Listed available tools/access → ENABLING ✅
   - Specified which tool to use → LIMITING (rewrite)

2. **Am I stating facts or making assumptions?**
   - "Fails with error X" → FACT ✅
   - "Probably fails because..." → ASSUMPTION (rewrite)

3. **Am I defining WHAT or prescribing HOW?**
   - "Must successfully build the package" → WHAT ✅
   - "Run 'npm build' to build" → HOW (rewrite)

4. **Am I sharing observations or solutions?**
   - "Line 42 contains 'import X'" → OBSERVATION ✅
   - "Change line 42 to 'import Y'" → SOLUTION (rewrite)

5. **Am I trusting agent expertise?**
   - "Investigate using available resources" → TRUST ✅
   - "Check this specific documentation" → DISTRUST (rewrite)

### Delegation Formula

**Scientific delegation = Observations + Success Criteria + Available Resources - Assumptions - Prescriptions**

This formula maximizes agent effectiveness by:
- Providing complete factual context (enables accurate hypothesis formation)
- Defining clear success metrics (prevents scope ambiguity)
- Enabling full toolkit access (allows optimal tool selection)
- Removing limiting assumptions (prevents cascade errors)
- Trusting agent expertise (leverages specialized domain knowledge)

Apply this framework to every sub-agent delegation to ensure optimal outcomes.
