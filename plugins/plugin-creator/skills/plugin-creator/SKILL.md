---
name: plugin-creator
description: 'Orchestrates specialized agents to create high-quality Claude Code plugins. Delegates to researcher agents for domain knowledge, Explore agents for code discovery, validation agents for official docs verification, and review agents for quality checks. Use when creating new plugins or improving existing ones.'
---

# Claude Code Plugin Creator - Agentic Orchestration Workflow

This skill orchestrates specialized agents through a comprehensive plugin creation workflow. The orchestrator (you) delegates to sub-agents for research, discovery, validation, and implementation - never performing these tasks directly.

**Workflow Diagram**: See [workflow-diagram.md](./references/workflow-diagram.md) for visual ASCII diagrams of the complete plugin creation flow.

---

## Orchestration Principles

<orchestration_rules>

**The orchestrator MUST delegate, not execute.**

| Task Type              | Delegate To           | Never Do Directly         |
| ---------------------- | --------------------- | ------------------------- |
| Domain research        | Explore agent         | Read docs yourself        |
| Code pattern discovery | Explore agent         | Grep/search yourself      |
| Official docs fetch    | WebFetch or Explore   | Assume from training data |
| Schema validation      | validation scripts    | Manually check fields     |
| Quality review         | plugin-assessor agent | Review your own work      |
| Documentation writing  | plugin-docs-writer    | Write README yourself     |

**Why delegation matters:**

1. Sub-agents have focused context and specialized prompts
2. Delegation creates audit trails of verified information
3. Prevents hallucination by requiring source verification
4. Enables parallel work and thoroughness

</orchestration_rules>

---

## Phase 0: RT-ICA Prerequisite Check

<prerequisite_checkpoint>

**STOP. Before creating any plugin, perform RT-ICA assessment.**

Invoke the `rt-ica` skill to verify prerequisites:

```text
RT-ICA SUMMARY
==============

Goal:
- Create a Claude Code plugin for [purpose]

Success Output:
- Functional plugin that [specific outcome]

Conditions (reverse prerequisites):
1. Purpose clarity | Requires: Clear problem statement | Why: Determines plugin scope
2. Target users | Requires: Who will use this | Why: Shapes UX decisions
3. Component selection | Requires: Skills vs Agents vs Hooks | Why: Architecture
4. Existing solutions | Requires: Check for similar plugins | Why: Avoid duplication
5. Source material | Requires: Documentation/APIs to encode | Why: Content accuracy
6. Verification method | Requires: How to test the plugin works | Why: Quality gate

Verification:
- [Check each condition: AVAILABLE / DERIVABLE / MISSING]

Decision:
- [APPROVED / BLOCKED]
```

**IF BLOCKED**: Request missing information before proceeding.

**IF APPROVED**: Continue to Phase 1.

</prerequisite_checkpoint>

---

## Phase 1: Research (Delegate to Explore Agents)

<research_phase>

### 1a. Check for Existing Solutions

**Delegate to Explore agent:**

```
Task(
  subagent_type="Explore",
  prompt="Search for existing plugins, skills, or implementations related to [domain].

  CHECK:
  1. plugins/ directory for similar plugins
  2. ~/.claude/skills/ for related skills
  3. GitHub/npm for published Claude Code plugins with similar purpose

  REPORT:
  - Existing solutions found (with paths/URLs)
  - Gaps that the new plugin could fill
  - Patterns to follow or avoid"
)
```

### 1b. Gather Domain Knowledge

**Delegate to Explore agent for codebase research:**

```
Task(
  subagent_type="Explore",
  prompt="Research [domain] to understand what knowledge the plugin should encode.

  INVESTIGATE:
  1. Official documentation URLs
  2. API references and schemas
  3. Best practices guides
  4. Common patterns and anti-patterns

  COLLECT:
  - Authoritative sources with URLs and access dates
  - Key concepts that Claude needs to know
  - Decision rules for when to apply patterns
  - Examples of correct and incorrect usage"
)
```

### 1c. Fetch Official Claude Code Documentation

**MANDATORY: Always verify against current official docs.**

```
Task(
  subagent_type="general-purpose",
  prompt="Fetch the current official Claude Code documentation to verify plugin requirements.

  FETCH THESE URLs:
  1. https://code.claude.com/docs/en/plugins-reference.md - Plugin manifest schema
  2. https://code.claude.com/docs/en/skills.md - SKILL.md frontmatter format
  3. https://code.claude.com/docs/en/hooks.md - Hook configuration
  4. https://code.claude.com/docs/llms.txt - Check for NEW features added this week

  EXTRACT:
  - Required and optional fields for plugin.json
  - SKILL.md frontmatter field types (MUST be comma-separated strings, NOT arrays)
  - Any new features or deprecations since January 2026

  FLAG any discrepancies with existing knowledge."
)
```

**This step catches:**

- Hallucinated schema fields
- Outdated information from training data
- New features added to Claude Code

</research_phase>

---

## Phase 2: Design (Delegate to Planning Agent)

<design_phase>

### 2a. Architecture Planning

**Delegate to Plan agent:**

```
Task(
  subagent_type="Plan",
  prompt="Design the architecture for a Claude Code plugin: [name]

  INPUTS (from Phase 1 research):
  - Domain knowledge: [summary]
  - Existing solutions: [summary]
  - Official schema: [summary]

  DESIGN DECISIONS:
  1. Component selection - which types needed and why
  2. Skill structure - main SKILL.md vs reference files
  3. Agent definitions - if delegatable specialists needed
  4. Hook triggers - if automation needed
  5. File organization - directory structure

  OUTPUT:
  - Plugin architecture diagram (ASCII)
  - Component list with purposes
  - File tree showing all planned files
  - Dependencies and requirements"
)
```

### 2b. Skill Content Planning

**For each skill, delegate content planning:**

```
Task(
  subagent_type="Plan",
  prompt="Plan the content structure for skill: [skill-name]

  PLAN:
  1. Activation triggers - when should Claude load this?
  2. Core instructions - what behavior changes? (keep under 500 lines)
  3. Reference material - what goes in separate files?
  4. Examples - positive and negative patterns
  5. Sources section - what citations needed?

  OUTPUT:
  - SKILL.md outline with section headings
  - List of reference files needed
  - Frontmatter field values"
)
```

</design_phase>

---

## Phase 3: Implementation

### Option A: Scaffolding Script (Recommended)

The `create_plugin.py` script creates validated plugin structure:

```bash
# Create plugin with skill
uv run scripts/create_plugin.py create my-plugin -d "Description" -s my-skill -o ./plugins

# Create with multiple components
uv run scripts/create_plugin.py create my-plugin \
    -d "Multi-component plugin" \
    -s skill1 -s skill2 \
    -a agent1 \
    --hooks \
    -o ./plugins
```

The script self-validates all created files (CoVe pattern).

### Option B: Manual Implementation

<implementation_structure>

**Directory structure:**

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

**Critical Rules:**

1. `.claude-plugin/` contains ONLY `plugin.json`
2. All components go at plugin root, NOT inside `.claude-plugin/`
3. Commands in plugins are deprecated - use skills instead

</implementation_structure>

### plugin.json Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does and trigger keywords",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "repository": "https://github.com/you/my-plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "skills": ["./skills/my-skill"]
}
```

| Field          | Type           | Required | Purpose                                  |
| -------------- | -------------- | -------- | ---------------------------------------- |
| `name`         | string         | Yes      | Kebab-case identifier, max 64 chars      |
| `version`      | string         | No       | Semantic versioning (X.Y.Z)              |
| `description`  | string         | No       | Max 1024 chars, include trigger keywords |
| `author`       | object         | No       | `{name, email?, url?}`                   |
| `keywords`     | array          | No       | Discovery tags (JSON array)              |
| `agents`       | string\|array  | No       | Path(s) to agent files                   |
| `skills`       | string\|array  | No       | Path(s) to skill directories             |
| `hooks`        | string\|object | No       | Hook config path or inline               |
| `mcpServers`   | string\|object | No       | MCP config path or inline                |
| `lspServers`   | string\|object | No       | LSP config path or inline                |
| `outputStyles` | string\|array  | No       | Path(s) to output style files            |

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-manifest-schema>

### SKILL.md Frontmatter

```yaml
---
name: my-skill
description: 'Detailed description including trigger keywords. Use when [situation].'
allowed-tools: Read, Grep, Glob
---
```

| Field                      | Type                   | Default         | Purpose                                    |
| -------------------------- | ---------------------- | --------------- | ------------------------------------------ |
| `name`                     | string                 | directory name  | Display name (lowercase, hyphens, max 64)  |
| `description`              | string                 | first paragraph | When to use; for auto-invocation           |
| `argument-hint`            | string                 | none            | Autocomplete hint (e.g., `[issue-number]`) |
| `allowed-tools`            | comma-separated string | none            | Tools without permission prompts           |
| `model`                    | string                 | default         | Model when skill is active                 |
| `context`                  | string                 | none            | `fork` for isolated subagent               |
| `agent`                    | string                 | general-purpose | Subagent type when `context: fork`         |
| `user-invocable`           | boolean                | true            | `false` hides from `/` menu                |
| `disable-model-invocation` | boolean                | false           | `true` prevents Claude auto-loading        |

**CRITICAL**: YAML frontmatter fields like `allowed-tools` MUST be comma-separated strings, NOT arrays.

**Source**: <https://code.claude.com/docs/en/skills.md>

---

## Phase 3b: Advanced Features Reference

<advanced_features>

This section documents powerful plugin capabilities the AI MUST consider when designing plugins. These features can transform a basic plugin into an exceptional one.

### Dynamic Context Injection

The `!`command`` syntax runs shell commands BEFORE skill content is sent to Claude. Output replaces the placeholder.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh:*)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

**How it works:**

1. Each `!`command`` executes immediately (before Claude sees anything)
2. Output replaces the placeholder in skill content
3. Claude receives fully-rendered prompt with actual data

**Use cases:**

- Inject git status, branch info, or PR details
- Include current date/time or environment info
- Fetch live API data for context
- Run diagnostics before a task

**Source**: <https://code.claude.com/docs/en/skills.md#inject-dynamic-context>

### String Substitutions

Skills support these variables:

| Variable                | Description                                             |
| ----------------------- | ------------------------------------------------------- |
| `$ARGUMENTS`            | Text passed when invoking the skill                     |
| `${CLAUDE_SESSION_ID}`  | Current session ID (for logging, correlating output)    |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory (hooks, MCP, scripts) |

**Example:**

```yaml
---
name: session-logger
description: Log activity for this session
---

Log the following to logs/${CLAUDE_SESSION_ID}.log:

$ARGUMENTS
```

### Running Skills in Subagents

Add `context: fork` to run a skill in an isolated subagent. The skill content becomes the subagent's prompt.

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:

1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

**When to use:**

- Long-running research tasks
- Tasks that need isolation from main conversation
- Read-only exploration (use Explore agent)
- Complex planning (use Plan agent)

**Available agent types:**

- `Explore` - Read-only tools for codebase exploration
- `Plan` - Architecture and planning tasks
- `general-purpose` - Full tool access

**Source**: <https://code.claude.com/docs/en/skills.md#run-skills-in-a-subagent>

### Visual Output - Bundled Scripts

Skills can bundle scripts in ANY language to generate visual output (HTML files that open in browser).

**Example: Codebase Visualizer**

```text
my-skill/
├── SKILL.md
└── scripts/
    └── visualize.py
```

**SKILL.md:**

```yaml
---
name: codebase-visualizer
description: Generate interactive tree visualization of codebase
allowed-tools: Bash(python:*)
---

# Codebase Visualizer

Run the visualization script from project root:

\`\`\`bash
python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .
\`\`\`

Creates codebase-map.html and opens it in browser.
```

**Pattern:** Script does heavy lifting, Claude orchestrates.

**Use cases:**

- Dependency graphs
- Test coverage reports
- API documentation
- Database schema visualizations
- Performance dashboards

**Source**: <https://code.claude.com/docs/en/skills.md#generate-visual-output>

### Hook Configuration

Plugins can provide event handlers that respond to Claude Code events.

**Hook types:**

| Type      | Purpose                           |
| --------- | --------------------------------- |
| `command` | Execute shell commands or scripts |
| `prompt`  | Evaluate a prompt with LLM        |
| `agent`   | Run agentic verifier with tools   |

**Available events:**

| Event                | When                      | Has Matcher |
| -------------------- | ------------------------- | ----------- |
| `PreToolUse`         | Before tool executes      | Yes         |
| `PostToolUse`        | After tool succeeds       | Yes         |
| `PostToolUseFailure` | After tool fails          | Yes         |
| `Stop`               | Claude finishes           | No          |
| `UserPromptSubmit`   | User submits prompt       | No          |
| `SessionStart`       | Session begins/resumes    | Yes         |
| `SessionEnd`         | Session ends              | No          |
| `SubagentStart`      | Subagent starts           | Yes         |
| `SubagentStop`       | Subagent stops            | Yes         |
| `Setup`              | Maintenance/init flags    | No          |
| `PreCompact`         | Before context compaction | No          |

**Example hooks/hooks.json:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**IMPORTANT:** Always use `${CLAUDE_PLUGIN_ROOT}` for script paths - it resolves to the correct cached location.

**Source**: <https://code.claude.com/docs/en/hooks.md>

### MCP Server Integration

Plugins can bundle MCP servers for external tool integration.

**Location:** `.mcp.json` at plugin root or inline in plugin.json

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

**Source**: <https://code.claude.com/docs/en/mcp.md>

### LSP Server Integration

Plugins can provide Language Server Protocol servers for code intelligence.

**Location:** `.lsp.json` at plugin root

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  }
}
```

**LSP provides:**

- Instant diagnostics (errors/warnings after each edit)
- Code navigation (go to definition, find references)
- Type information and documentation

**Note:** Users must install the language server binary separately.

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#lsp-servers>

### Plugin Caching Behavior

**Critical knowledge for plugin developers:**

Claude Code COPIES plugins to a cache directory rather than using them in-place.

**Implications:**

1. External files outside plugin directory are NOT copied
2. Use symlinks if you need external dependencies (symlinks are followed during copy)
3. `${CLAUDE_PLUGIN_ROOT}` always points to correct cached location

**Source**: <https://code.claude.com/docs/en/plugins-reference.md#plugin-caching-and-file-resolution>

### Path Behavior Rules

**Custom paths SUPPLEMENT default directories, they don't REPLACE them.**

```json
{
  "skills": ["./custom/skills/"]
}
```

This adds custom skills IN ADDITION TO `skills/` directory.

- All paths must be relative and start with `./`
- Multiple paths can be arrays for flexibility
- Same naming/namespacing rules apply

### Skill Invocation Control

Control who can invoke skills:

| Frontmatter                      | User | Claude | Use Case                    |
| -------------------------------- | ---- | ------ | --------------------------- |
| (default)                        | Yes  | Yes    | Most skills                 |
| `disable-model-invocation: true` | Yes  | No     | Workflows with side effects |
| `user-invocable: false`          | No   | Yes    | Background knowledge only   |

**Example - deploy skill only user can trigger:**

```yaml
---
name: deploy
description: Deploy application to production
disable-model-invocation: true
---
```

### Extended Thinking

Include "ultrathink" anywhere in skill content to enable extended thinking mode.

</advanced_features>

---

## Phase 4: Validation (Delegate to Validation Agents)

<validation_phase>

### 4a. Run Automated Validation Scripts

```bash
# Validate plugin structure
uv run scripts/create_plugin.py validate ./plugins/my-plugin

# Validate all frontmatter
uv run scripts/validate_frontmatter.py batch ./plugins/my-plugin
```

### 4b. Verify Against Official Documentation

**MANDATORY: Delegate verification to catch hallucinations.**

```
Task(
  subagent_type="general-purpose",
  prompt="Verify the plugin at ./plugins/my-plugin against official Claude Code documentation.

  FETCH AND COMPARE:
  1. https://code.claude.com/docs/en/plugins-reference.md - Verify plugin.json schema
  2. https://code.claude.com/docs/en/skills.md - Verify SKILL.md frontmatter

  CHECK FOR:
  - Fields that don't exist in official schema
  - Incorrect field types (arrays vs comma-separated strings)
  - Missing required fields
  - Outdated patterns

  REPORT:
  - Compliance status for each file
  - Specific violations with line numbers
  - Recommendations for fixes"
)
```

### 4c. Quality Assessment

**Delegate to plugin-assessor agent:**

```
Task(
  subagent_type="plugin-assessor",
  prompt="Assess the plugin at ./plugins/my-plugin for quality and marketplace readiness.

  ASSESS:
  - Structural correctness
  - Frontmatter optimization
  - Schema compliance
  - Documentation completeness
  - Cross-reference integrity"
)
```

</validation_phase>

---

## Phase 5: Documentation (Delegate to Docs Agent)

<documentation_phase>

**Delegate to plugin-docs-writer agent:**

```
Task(
  subagent_type="plugin-docs-writer",
  prompt="Generate comprehensive documentation for the plugin at ./plugins/my-plugin.

  CREATE:
  - README.md with installation, usage, and examples
  - docs/skills.md if multiple skills
  - Configuration guide if hooks or MCP servers included

  ENSURE:
  - All features documented
  - Installation instructions accurate
  - Examples are runnable"
)
```

</documentation_phase>

---

## Phase 6: Final Verification

<final_checkpoint>

**STOP. Before claiming complete, verify with evidence.**

### Invoke verify Skill

```text
VERIFICATION SUMMARY:
Task Type: FEATURE
Works Check: [PASS/FAIL] - Evidence: validation script output
Quality Gates: [PASS/FAIL] - Evidence: plugin-assessor report
Docs Check: [PASS/FAIL] - Evidence: README.md exists and accurate
Honesty Check: [PASS/FAIL] - Evidence: all claims cite sources

VERDICT: [COMPLETE / NOT COMPLETE - reason]
```

**Only mark complete when:**

1. All automated validation scripts pass
2. plugin-assessor reports no critical issues
3. Official docs verification found no schema violations
4. All factual claims in skills cite sources

</final_checkpoint>

---

## Quick Reference: Agent Delegation

| Phase    | Agent Type           | Purpose                                   |
| -------- | -------------------- | ----------------------------------------- |
| Research | `Explore`            | Code discovery, pattern analysis          |
| Research | `general-purpose`    | Fetch and analyze official documentation  |
| Design   | `Plan`               | Architecture decisions, content structure |
| Validate | validation scripts   | Schema and structure validation           |
| Validate | `plugin-assessor`    | Quality assessment                        |
| Document | `plugin-docs-writer` | README and documentation generation       |

---

## Tooling

| Script                              | Purpose                             |
| ----------------------------------- | ----------------------------------- |
| `scripts/create_plugin.py create`   | Scaffold new plugin with validation |
| `scripts/create_plugin.py validate` | Check existing plugin structure     |
| `scripts/validate_frontmatter.py`   | Validate frontmatter against schema |

Scripts use PEP 723 inline metadata - dependencies install automatically via `uv run`.

---

## Sources

Official Claude Code documentation (verified January 2026):

- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete schema
- [Skills Documentation](https://code.claude.com/docs/en/skills) - SKILL.md format
- [Hooks Reference](https://code.claude.com/docs/en/hooks) - Hook configuration
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - Distribution
- [Documentation Index](https://code.claude.com/docs/llms.txt) - Check for new features
