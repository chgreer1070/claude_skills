# Plugin-Creator Patterns, Architecture, and Conventions

**Analysis Date:** 2026-03-04
**Plugin:** `plugin-creator`
**Plugin Path:** `plugins/plugin-creator/`
**Plugin Version:** 6.0.6 (per `plugins/plugin-creator/.claude-plugin/plugin.json`)

---

## Table of Contents

1. [Plugin Directory Structure](#1-plugin-directory-structure)
2. [Skill Frontmatter Conventions](#2-skill-frontmatter-conventions)
3. [Agent Frontmatter Conventions](#3-agent-frontmatter-conventions)
4. [Skill Input/Output Artifact Contracts](#4-skill-inputoutput-artifact-contracts)
5. [Agent Input/Output Artifact Contracts](#5-agent-inputoutput-artifact-contracts)
6. [Workflow Patterns: Orchestration and Delegation](#6-workflow-patterns-orchestration-and-delegation)
7. [How Skills Reference Each Other](#7-how-skills-reference-each-other)
8. [Delegation Format Standard](#8-delegation-format-standard)
9. [Validation Script Patterns](#9-validation-script-patterns)
10. [Plugin.json Schema and Registration](#10-pluginjson-schema-and-registration)
11. [Conventions Specific to Plugin-Creator](#11-conventions-specific-to-plugin-creator)

---

## 1. Plugin Directory Structure

**Source:** `plugins/plugin-creator/.claude-plugin/plugin.json`, Glob results

```text
plugins/plugin-creator/
├── .claude-plugin/
│   └── plugin.json                 # REQUIRED: manifest (agents registered here)
├── .claude/
│   ├── rules/
│   │   ├── frontmatter-requirements.md
│   │   └── plugin-json.md
│   └── reports/                    # investigation/audit outputs
├── agents/                         # All .md files, each = one agent
│   ├── plugin-assessor.md
│   ├── refactor-planner.md
│   ├── refactor-executor.md
│   ├── refactor-validator.md
│   ├── subagent-refactorer.md
│   ├── contextual-ai-documentation-optimizer.md
│   ├── hook-creator.md
│   └── agent-creator.md
├── skills/                         # Each subdirectory = one skill
│   ├── plugin-creator/SKILL.md
│   ├── skill-creator/SKILL.md
│   ├── agent-creator/SKILL.md
│   ├── assessor/SKILL.md
│   ├── ensure-complete/SKILL.md
│   ├── implement-refactor/SKILL.md
│   ├── refactor-plugin/SKILL.md
│   ├── refactor-skill/SKILL.md
│   ├── lint/SKILL.md
│   ├── hooks-guide/SKILL.md
│   ├── claude-skills-overview-2026/SKILL.md
│   ├── claude-plugins-reference-2026/SKILL.md
│   └── [13+ more skill directories]
├── scripts/                        # Python scripts (PEP 723 inline deps)
│   ├── plugin_validator.py
│   ├── create_plugin.py
│   ├── auto_sync_manifests.py
│   ├── fix_tool_formats.py
│   ├── frontmatter_core.py
│   ├── frontmatter_utils.py
│   └── normalize_frontmatter.py
├── references/                     # Plugin-level reference docs
│   ├── ARCHITECTURE.md
│   ├── USAGE.md
│   └── ERROR_CODES.md
├── docs/
│   └── ERROR_CODES.md
├── examples/
│   ├── agents/example-agent.md
│   └── skills/example-skill/SKILL.md
├── planning/                       # Internal planning artifacts
├── CLAUDE.md                       # Dev-time context for Claude
└── README.md
```

**Key structural rules observed:**

- `.claude-plugin/` contains ONLY `plugin.json`. All other components live at plugin root — never inside `.claude-plugin/`.
- Skills are **auto-discovered** from `skills/*/SKILL.md`. The `plugin.json` does NOT have a `skills` field (auto-discovery mode, Mode A).
- Agents are **explicitly registered** in `plugin.json` `agents` array with `"./agents/filename.md"` paths.
- `CLAUDE.md` at plugin root is development-time context only — not delivered to plugin users.

---

## 2. Skill Frontmatter Conventions

**Sources:** All SKILL.md files read directly.

### Minimal frontmatter pattern

```yaml
---
name: skill-name
description: 'One-line description with trigger keywords. Use when [specific situation].'
user-invocable: true
---
```

### Full frontmatter with all observed fields

```yaml
---
name: assessor
description: Assess a plugin and create refactoring task files for parallel agent execution. Use when you need to analyze a plugin structure, score its quality, and generate a phased refactoring plan with design map and implementation tasks.
argument-hint: <plugin-name>
model: sonnet
user-invocable: true
---
```

### Field usage observed across plugin-creator skills

| Field | Type | Found In | Notes |
|-------|------|----------|-------|
| `name` | string | All skills | Must match directory name; required per agentskills.io spec |
| `description` | string | All skills | Single-line only — NEVER multiline `>-` or `\|-` indicators |
| `argument-hint` | string | `assessor`, `ensure-complete`, `refactor-plugin`, `lint`, `implement-refactor` | Shown in autocomplete |
| `model` | string | `assessor`, `ensure-complete`, `implement-refactor`, `plugin-creator`, `agent-creator` | `sonnet` used; omit to inherit |
| `user-invocable` | boolean | Most skills | `false` for background/delegated skills (e.g., `feature-discovery`) |
| `license` | string | `skill-creator` | Non-standard; documents license for reference |
| `metadata` | object | NOT in plugin-creator skills; used in `.claude/skills/` | Seen in `add-new-feature`, not in plugin-creator |

### Description field rules

- **Always single-line.** Quoted with `'...'` when description contains colons or special chars.
- Include "Use when [situation]" pattern to enable Claude's auto-invocation.
- Include domain-specific trigger keywords.
- Max 1024 characters.
- Do NOT use YAML multiline indicators (`>-`, `|-`, `|`).

**Example from `assessor/SKILL.md:3`:**

```yaml
description: Assess a plugin and create refactoring task files for parallel agent execution. Use when you need to analyze a plugin structure, score its quality, and generate a phased refactoring plan with design map and implementation tasks.
```

**Example from `lint/SKILL.md:3`:**

```yaml
description: Run the plugin validator on a skill, agent, or plugin directory rts token complexity, broken links, frontmatter issues, and structural problems. Use when checking skill quality, validating before commit, or diagnosing validator warnings. Pass the path as an argument.
```

### `allowed-tools` field

- **Format**: Comma-separated string — NEVER a YAML list/array.
- Not observed in `plugin-creator` skills (tool inheritance used). Present in agent frontmatter instead.

```yaml
# CORRECT
allowed-tools: Read, Grep, Glob

# WRONG (will cause validation error)
allowed-tools:
  - Read
  - Grep
```

### `disable-model-invocation` and `user-invocable`

```yaml
# Hidden from / menu but Claude can auto-invoke
user-invocable: false

# User can invoke with /name but Claude cannot auto-load
disable-model-invocation: true
```

`feature-discovery` uses `user-invocable: false` — it is delegated by orchestrators, not called by users directly.

---

## 3. Agent Frontmatter Conventions

**Source:** `plugins/plugin-creator/agents/plugin-assessor.md:1-6`, `agents/refactor-planner.md:1-6`

### Agent file structure

```markdown
---
description: 'Detailed description with trigger keywords. Use when [situation], [situation2].'
model: sonnet
skills: comma-separated-skill-names
color: cyan
---

# Agent Title

Identity paragraph describing the agent's role and expertise.

## Core Identity / Competencies

<identity>...</identity>

## Assessment Protocol / Workflow

<workflow>...</workflow>

## Report Format

<report_format>...</report_format>

## Rules

<rules>...</rules>
```

### Agent frontmatter fields observed

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `description` | string | `'Analyze Claude Code plugins...'` | Delegation trigger text; 1024 char max |
| `model` | string | `sonnet` | `sonnet` used consistently in plugin-creator agents |
| `skills` | string | `claude-skills-overview-2026, claude-plugins-reference-2026, hooks-guide` | Comma-separated; NOT inherited from parent |
| `color` | string | `cyan` | UI-only terminal color; optional |
| `tools` | string | Not set in these agents | When absent, inherits all tools |
| `permissionMode` | string | Not set in these agents | When absent, uses `default` |

**`plugin-assessor.md:1-6`:**

```yaml
---
name: plugin-assessor
description: Analyze Claude Code plugins for structural correctness, frontmatter optimization, schema compliance, and enhancement opportunities. Use when reviewing plugins before marketplace submission, auditing existing plugins, validating plugin structure, or identifying improvements. Handles large plugins with many reference files. Detects orphaned documentation, duplicate content, and missing cross-references.
model: sonnet
skills: claude-skills-overview-2026, claude-plugins-reference-2026, hooks-guide
---
```

**`refactor-planner.md:1-6`:**

```yaml
---
name: refactor-planner
description: Analyze plugin structure and create comprehensive executable refactoring plans with prioritized tasks and parallelization strategy. Use when planning plugin refactoring, breaking down large refactoring efforts into executable tasks, splitting oversized skills that exceed validator token thresholds (SK006/SK007), or assessing plugin quality before systematic improvements. Identifies refactoring opportunities, maps dependencies, and generates task files for execution.
model: sonnet
color: cyan
---
```

### Agent body conventions

Agents use XML semantic tags to organize content:

```markdown
<identity>
Role and expertise description.
</identity>

<workflow>
Step-by-step process.
</workflow>

<rules>
MUST/MUST NOT constraints.
</rules>

<report_format>
Expected output structure with code fences.
</report_format>

<scoring>
Quality scoring criteria tables.
</scoring>

<interaction>
Invocation and completion protocols.
</interaction>
```

### Agent registration in plugin.json

Agents require **explicit registration** as individual file paths:

```json
{
  "agents": [
    "./agents/agent-creator.md",
    "./agents/hook-creator.md",
    "./agents/refactor-planner.md",
    "./agents/refactor-executor.md",
    "./agents/refactor-validator.md",
    "./agents/subagent-refactorer.md",
    "./agents/contextual-ai-documentation-optimizer.md",
    "./agents/plugin-assessor.md"
  ]
}
```

Skills are NOT listed in `plugin.json` — they are auto-discovered from `skills/*/`.

---

## 4. Skill Input/Output Artifact Contracts

**Sources:** All SKILL.md files read directly.

### `/plugin-creator:plugin-creator` (`skills/plugin-creator/SKILL.md`)

**Type:** Orchestrator — never executes work directly, only delegates.

**Input:**
- User description of plugin to create
- RT-ICA prerequisite check (Phase 0)
- Discussion phase preferences

**Output artifacts:**

```text
.claude/plan/{plugin-name}/
├── PROJECT.md          # Vision and goals
├── REQUIREMENTS.md     # Scoped deliverables
├── STATE.md            # Decisions, blockers, current position
├── discuss-CONTEXT.md  # User preferences from discussion
├── research-FINDINGS.md # 4-way parallel research results
├── design-PLAN.md      # Architecture with XML task specs
├── validation-REPORT.md # Multi-layer verification results
└── SUMMARY.md          # Completion record
```

**Agents delegated to:** `plugin-creator:plugin-assessor` (research), `general-purpose` (docs/validation), `plugin-docs-writer` (README)

**Gate:** Plan Checker must return PASS before implementation begins.

---

### `/plugin-creator:assessor` (`skills/assessor/SKILL.md`)

**Type:** Orchestrator — 4-phase sequential workflow.

**Input:** `$ARGUMENTS` = plugin directory name (e.g., `python3-development`)

**Phases:**

1. Tier 1: Structural analysis via `plugin-assessor` agent
2. Tier 2: Skill lifecycle audit via `plugin-creator:audit-skill-lifecycle`
3. Tier 3: Agent lifecycle audit via `plugin-creator:audit-agent-lifecycle`
4. Tier 4: Skill completeness audit (optional)

**Output artifacts:**

```text
[inline report in conversation]
.claude/audits/                    # Audit reports from Tiers 2–4
.claude/plan/refactor-design-{slug}.md   # Phase 2 design map
.claude/plan/tasks-refactor-{slug}.md    # Phase 3 task file
.claude/plan/REFACTOR-PLAN.md            # Phase 3 index (created/updated)
[Context Manifest appended to task file in Phase 4]
```

**Exit signal:** Returns structured final summary with parallelization groups; tells orchestrator to run `/plugin-creator:implement-refactor {plugin-slug}`.

---

### `/plugin-creator:implement-refactor` (`skills/implement-refactor/SKILL.md`)

**Type:** Orchestrator — executes tasks from a plan file.

**Input:** `$ARGUMENTS` = plugin slug OR path to `.md` task file

**Task routing table:**

| Issue Type | Agent | Skill/Agent Reference |
|---|---|---|
| `SKILL_SPLIT` | `plugin-creator:refactor-skill` | skill invocation |
| `AGENT_OPTIMIZE` | `subagent-refactorer` | agent via Agent tool |
| `DOC_IMPROVE` | `contextual-ai-documentation-optimizer` | agent via Agent tool |
| `ORPHAN_RESOLVE` | `contextual-ai-documentation-optimizer` | agent via Agent tool |
| `STRUCTURE_FIX` | `contextual-ai-documentation-optimizer` | agent via Agent tool |
| Validation | `plugin-assessor` | agent via Agent tool |
| Documentation | `plugin-docs-writer` | agent (external dep) |

**Output artifacts:**
- Task file updated: tasks transition `❌ NOT STARTED` → `🔄 IN PROGRESS` → `✅ COMPLETE`
- Calls `plugin-creator:ensure-complete` upon all tasks `✅ COMPLETE`
- Follow-up task files: `.claude/plan/tasks-refactor-{slug}-followup-{N}.md`
- `REFACTOR-PLAN.md` updated: entry moved from Active to Completed

**Recursive behavior:** If `ensure-complete` creates follow-up tasks, `implement-refactor` recurses until no follow-ups are generated.

---

### `/plugin-creator:ensure-complete` (`skills/ensure-complete/SKILL.md`)

**Type:** Orchestrator — post-refactoring quality gate.

**Input:** `$ARGUMENTS` = path to task file

**Phases (sequential, each controlled by TodoWrite):**

1. Plugin Validation — delegates to `plugin-assessor` agent
2. Code Review — delegates to `python-code-reviewer` agent
3. Documentation Audit — delegates to `doc-drift-auditor` agent
4. Gap Identification — creates follow-up task file via `swarm-task-planner` if needed

**Gap decision logic:**

```text
IF (score_improvement < expected) OR
   (critical_issues > 0) OR
   (high_issues > 2) OR
   (drift_items > 0):
    → CREATE follow-up task file
ELSE:
    → Refactoring is complete
```

**Output artifacts:**
- Phase summaries in conversation
- Follow-up task file: `.claude/plan/tasks-refactor-{slug}-followup-{N}.md`
- `REFACTOR-PLAN.md` updated (on completion with no follow-ups)

---

### `/plugin-creator:refactor-plugin` (`skills/refactor-plugin/SKILL.md`)

**Type:** Entry-point workflow — wraps assessor.

**Input:** `$ARGUMENTS` = path to plugin directory (e.g., `./plugins/python3-development`)

**Actions:**
1. Validates input (plugin path has `plugin.json` or `skills/`)
2. Invokes `plugin-creator:assessor` skill
3. Displays plan summary
4. Awaits user decision: Continue / Review / Abort

**Output artifacts:** Same as `assessor` (delegates to it entirely).

---

### `/plugin-creator:skill-creator` (`skills/skill-creator/SKILL.md`)

**Type:** Interactive creation workflow.

**Input:** User describes desired skill

**7-step process:**

1. Understand skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Determine location and distribution strategy
4. Initialize skill via `init_skill.py` (MANDATORY)
5. Edit the skill
6. Package (optional — plugin distribution only)
7. Iterate

**Init script invocation pattern:**

```bash
${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/init_skill.py <skill-name> --path <output-directory>
```

**Output artifacts:**
- New skill directory at specified path with `SKILL.md`, `scripts/`, `references/`, `assets/`
- For plugin skills: no `plugin.json` update needed (auto-discovered)
- For plugin agents: `plugin.json` `agents` array updated

---

### `/plugin-creator:agent-creator` (`skills/agent-creator/SKILL.md`)

**Type:** Interactive creation workflow.

**Input:** User describes desired agent

**8-phase process:**

1. Discovery (read `.claude/agents/`)
2. Requirements gathering (AskUserQuestion)
3. Template selection (archetypes + existing agents)
4. Template adaptation (section-by-section)
5. Agent file creation
6. Validation (frontmatter checklist)
7. Scope and file placement (project/user/plugin)
8. Post-creation validation (run `plugin_validator.py`)

**Scope decision → file placement:**

| Scope | Path | plugin.json update? |
|---|---|---|
| Project | `.claude/agents/{name}.md` | No |
| User | `~/.claude/agents/{name}.md` | No |
| Plugin | `{plugin}/agents/{name}.md` | YES — add to `agents` array |

**Validation command:**

```bash
uv run plugins/plugin-creator/scripts/plugin_validator.py validate {path}
```

---

### `/plugin-creator:lint` (`skills/lint/SKILL.md`)

**Type:** Script invocation wrapper — minimal SKILL.md body.

**Input:** `$ARGUMENTS` = path to skill, agent, or plugin directory

**Body (complete):**

```text
!`${CLAUDE_PLUGIN_ROOT}/scripts/plugin_validator.py $ARGUMENTS`

@${CLAUDE_PLUGIN_ROOT}/references/ERROR_CODES.md
```

This demonstrates the "dynamic context injection" pattern — the `!` prefix runs the command before Claude sees the skill body; the `@` prefix injects the file content. The skill has no markdown instructions — it is a pure script executor.

**Output:** Validator output in conversation + ERROR_CODES.md reference loaded.

---

## 5. Agent Input/Output Artifact Contracts

### `plugin-assessor` agent (`agents/plugin-assessor.md`)

**Skills loaded:** `claude-skills-overview-2026, claude-plugins-reference-2026, hooks-guide`

**Input:** Prompt with plugin path (typically from `assessor` skill or `ensure-complete`)

**9-phase assessment protocol:**

1. Discovery — glob all capability files
2. Manifest Validation — validate `plugin.json` schema
3. Skills Analysis — frontmatter, content, reference audit, link validation
4. Commands Analysis
5. Agents Analysis — frontmatter, description quality
6. Hooks Validation
7. MCP Configuration Validation
8. Cross-Reference Analysis — link graph, declared vs actual capabilities
9. Enhancement Identification

**Output:** Inline Plugin Assessment Report with scoring breakdown:

```text
## Executive Summary
- Overall Score: X/100
- Marketplace Ready: Yes / No / With Changes
- Critical Issues: N

## Skills Analysis Table
## Refactoring Recommendations (SKILL_SPLIT, AGENT_OPTIMIZE, DOC_IMPROVE, ORPHAN_RESOLVE, STRUCTURE_FIX)
## Scoring Breakdown (9 components with weights)
## Action Items (Critical / Recommended / Optional)
```

**Scoring weights:**

| Component | Weight |
|---|---|
| Structural validity | 20% |
| Manifest completeness | 15% |
| Frontmatter correctness | 20% |
| Description quality | 15% |
| Reference organization | 15% |
| Documentation quality | 10% |
| Enhancement potential | 5% |

---

### `refactor-planner` agent (`agents/refactor-planner.md`)

**Input:** Prompt with plugin path

**Output format (inline in conversation):**

```markdown
## Refactoring Analysis: [plugin-name]

### Executive Summary
- Plugin Path, Components Found, Overall Health, Refactoring Scope

### Component Analysis
- Skills table (Lines, Domains, Split Needed, Issues)
- Agents table (Description Quality, Issues)

### Issues Found (Critical / High / Medium)

### Recommended Tasks (T1, T2, … each with ID, Type, Target, Dependencies, Agent, Acceptance Criteria, Can Parallelize With)

### Parallelization Strategy (Group A, Group B, Sequential)

### Next Steps
```

**Does NOT write files** — output is conversation-only. The `assessor` skill's Phase 2 delegates design-file creation to `python-cli-design-spec` agent, not `refactor-planner`.

---

## 6. Workflow Patterns: Orchestration and Delegation

**Sources:** `skills/plugin-creator/SKILL.md`, `skills/assessor/SKILL.md`, `skills/implement-refactor/SKILL.md`

### Core orchestration principle

Skills are orchestrators. They coordinate by delegating to sub-agents. **The orchestrator does not execute work directly.**

```text
plugin-creator (orchestrator skill)
  └── delegates to → plugin-assessor agent (research)
  └── delegates to → general-purpose agent (docs verification)
  └── delegates to → Plan agent (design)
  └── delegates to → plugin-docs-writer agent (README)
```

### Parallel agent spawning pattern

Multiple independent agents are launched in a single message:

```text
# From plugin-creator/SKILL.md — 4-way parallel research:
Agent(subagent_type="plugin-creator:plugin-assessor", prompt="RESEARCHER 1: EXISTING SOLUTIONS...")
Agent(subagent_type="plugin-creator:plugin-assessor", prompt="RESEARCHER 2: CLAUDE CODE FEATURES...")
Agent(subagent_type="plugin-creator:plugin-assessor", prompt="RESEARCHER 3: ARCHITECTURE PATTERNS...")
Agent(agent="general-purpose", prompt="RESEARCHER 4: PITFALLS & OFFICIAL DOCS...")
```

### Sequential phase pattern

When phases depend on prior output:

```text
Phase 1 output (assessment) → Phase 2 input (design)
Phase 2 output (design map) → Phase 3 input (task file)
Phase 3 output (task file)  → Phase 4 input (context)
```

### TodoWrite completion tracking pattern

Every multi-phase workflow creates tasks BEFORE starting any work:

```python
# From assessor/SKILL.md — mandatory pattern:
TaskCreate(subject="Phase 1: ...", description="...", activeForm="...")
TaskCreate(subject="Phase 2: ...", description="...", activeForm="...")
# ... all tasks first, then start Phase 1
```

Rules:
1. Create ALL tasks BEFORE starting Phase 1
2. Mark each task `in_progress` BEFORE starting that work
3. Mark each task `completed` AFTER verification passes
4. Do NOT display final summary until ALL tasks are `completed`

### Completion tracking with structured summaries

Each phase must display a summary before proceeding:

```text
=== PHASE N COMPLETE: [Phase Name] ===

[Key metrics and file paths]
[Counts of issues found / files created]
```

Final summary uses a box-drawing format:

```text
================================================================================
                    PLUGIN REFACTORING PLANNING COMPLETE
================================================================================
...
================================================================================
                         READY FOR PARALLEL EXECUTION
================================================================================
```

---

## 7. How Skills Reference Each Other

**Sources:** All SKILL.md files read directly, `CLAUDE.md` at plugin-creator root.

### Activation syntax for cross-skill references

Skills reference other skills using the activation syntax `plugin-name:skill-name`:

```text
# Correct — in skill body or CLAUDE.md:
Skill(skill: "plugin-creator:assessor", args: "$ARGUMENTS")
Skill(skill: "plugin-creator:audit-skill-lifecycle", args: "$ARGUMENTS")
Skill(skill: "plugin-creator:refactor-skill")
```

NOT the file path. NOT `See /assessor/SKILL.md`. The activation invocation is:

```text
Skill(skill="plugin-creator:skill-name")
```

Or the slash-command form for human-readable references:

```text
/plugin-creator:assessor
/plugin-creator:implement-refactor
```

### Cross-plugin skill references

When a skill references a skill from another plugin:

```text
Skill(skill: "plugin-creator:refactor-skill")   # within same plugin
Skill(skill: "python3-development:something")    # cross-plugin
```

### The global delegation warning pattern

Every skill in `plugin-creator` begins its body with this exact line:

```text
> When editing files in `plugins/`, `.claude/`, `AGENTS.md`, or `CLAUDE.md` — delegate to `subagent_type="plugin-creator:contextual-ai-documentation-optimizer"`.
```

This is a blockquote (Markdown `>`) placed as the **first line of the body**, after the frontmatter. It appears in: `assessor`, `plugin-creator`, `skill-creator`, `agent-creator`, `refactor-plugin`, `ensure-complete`, `implement-refactor`.

**Skills that do NOT have this line:** `lint` (body is `!command` + `@file` only), reference skills like `claude-skills-overview-2026`.

### Progressive disclosure — reference files

Skills keep SKILL.md lean and link to `references/` files:

```markdown
# In SKILL.md body:
For multi-step processes: See references/workflows.md
For output formats: See [agentskills best-practices](../agentskills/references/best-practices.md)
```

The `@` prefix in skill body loads a file's content at invocation time:

```text
# From lint/SKILL.md:
@${CLAUDE_PLUGIN_ROOT}/references/ERROR_CODES.md
```

### Dynamic context injection

The `!` prefix runs a shell command and injects its output:

```text
# From skill-creator/SKILL.md:
!`python3 -c "import os, pathlib; ..."`

# From lint/SKILL.md:
!`${CLAUDE_PLUGIN_ROOT}/scripts/plugin_validator.py $ARGUMENTS`
```

---

## 8. Delegation Format Standard

**Source:** `.claude/rules/delegation-format.md`

### Standard format for a workflow step that delegates

```text
N. Task is [description] with subagent_type="plugin:agent-name"
   Context to include in the prompt: [specific file paths, artifacts, or data to pass]
   Output: [specific artifact the agent produces — file path, format, content]
```

### How it appears in skill bodies (observed pattern)

Skills use the Agent tool call syntax inline in documentation:

```text
Agent(
    subagent_type="plugin-creator:plugin-assessor",
    prompt="""
Your ROLE_TYPE is sub-agent.

<context>
WHERE you are working:
- Plugin root: ./plugins/$ARGUMENTS
...
</context>

<success_criteria>
MUST deliver:
1. Complete Plugin Assessment Report with ALL sections populated
...
</success_criteria>

<exploration_steps>
EXECUTE the full plugin-assessor protocol:
...
</exploration_steps>

<output_specification>
GENERATE a Plugin Assessment Report...
</output_specification>
"""
)
```

### Agent prompt structure (consistent pattern)

Every sub-agent prompt in plugin-creator includes these XML sections:

```text
Your ROLE_TYPE is sub-agent.

<context>
WHERE you are working: (paths)
WHAT already exists: (prior artifacts)
</context>

<success_criteria>
MUST deliver:
1. [Specific, measurable output]
</success_criteria>

<exploration_steps>
EXECUTE these steps in order:
1. [Step]
</exploration_steps>

<output_specification> OR <instructions>
[What to produce and where to write it]
</output_specification>

<available_resources>
[Tools, access, reference skills]
</available_resources>
```

### Agent routing table pattern

Skills define a routing table for which agent handles which task type:

```text
| Issue Type     | Agent                                   |
| -------------- | --------------------------------------- |
| SKILL_SPLIT    | plugin-creator:refactor-skill           |
| AGENT_OPTIMIZE | subagent-refactorer                     |
| DOC_IMPROVE    | contextual-ai-documentation-optimizer   |
| ORPHAN_RESOLVE | contextual-ai-documentation-optimizer   |
| STRUCTURE_FIX  | contextual-ai-documentation-optimizer   |
```

---

## 9. Validation Script Patterns

**Source:** `CLAUDE.md` at `plugins/plugin-creator`, `scripts/` glob

### Validator invocation

```bash
# Single file or directory:
uv run plugins/plugin-creator/scripts/plugin_validator.py {path}

# Auto-fix mode:
uv run plugins/plugin-creator/scripts/plugin_validator.py --fix {path}

# Check only (no fixes):
uv run plugins/plugin-creator/scripts/plugin_validator.py --check {path}

# Batch validation:
uv run plugins/plugin-creator/scripts/plugin_validator.py batch {plugin-path}
```

### What validator checks (per CLAUDE.md)

- Frontmatter schema: YAML syntax, forbidden multiline indicators (`>-`, `|-`), required fields, field types, tools/skills as comma-separated strings
- Plugin structure: `plugin.json` schema compliance, component path references, version consistency
- Skill complexity: Token-based thresholds (`TOKEN_WARNING_THRESHOLD` = SK006, `TOKEN_ERROR_THRESHOLD` = SK007)
- Internal links: Markdown link validity, progressive disclosure structure

### Auto-fixes applied by validator

- YAML arrays → comma-separated strings
- Multiline descriptions → single-line strings
- Unquoted colons in descriptions → adds quotes
- Missing `name:` fields → auto-adds from directory name

### Error code system

Error codes are documented at `plugins/plugin-creator/references/ERROR_CODES.md` and `docs/ERROR_CODES.md`. 23 codes across 9 validators. SK006 = warning threshold, SK007 = error threshold for skill token complexity.

### Plugin structure validation

```bash
claude plugin validate {plugin-directory}
```

Validates: `plugin.json` in `.claude-plugin/`; JSON syntax; required `name` field; kebab-case name; all paths start with `./`; `agents` field is array of individual file paths (not directory string); referenced files exist.

### Auto-sync manifests (pre-commit hook)

```bash
uv run -q --no-sync plugins/plugin-creator/scripts/auto_sync_manifests.py
```

Runs automatically on `git commit`. Detects CRUD operations on plugins/components from staged changes, updates `plugin.json` component arrays, bumps semver.

---

## 10. Plugin.json Schema and Registration

**Source:** `plugins/plugin-creator/.claude-plugin/plugin.json`

### Observed plugin.json structure

```json
{
  "name": "plugin-creator",
  "description": "Complete plugin development toolkit...",
  "version": "6.0.6",
  "author": {
    "name": "Jamie Nelson",
    "url": "https://github.com/bitflight-devops"
  },
  "homepage": "https://github.com/...",
  "repository": "https://github.com/bitflight-devops/claude_skills",
  "license": "MIT",
  "keywords": ["plugin-development", "agent-creation", "skill-creation", "validation", "refactoring", "frontmatter"],
  "agents": [
    "./agents/agent-creator.md",
    "./agents/hook-creator.md",
    "./agents/refactor-planner.md",
    "./agents/refactor-executor.md",
    "./agents/refactor-validator.md",
    "./agents/subagent-refactorer.md",
    "./agents/contextual-ai-documentation-optimizer.md",
    "./agents/plugin-assessor.md"
  ]
}
```

**No `skills` field present** — skills auto-discovered from `skills/*/` (Mode A). Adding `skills` field opts into manual allowlist (Mode B) and fires SK009.

### Required plugin.json fields

| Field | Type | Constraint |
|---|---|---|
| `name` | string | Kebab-case, max 64 chars, matches directory |
| (all others optional) | | |

### Path format in plugin.json

- All paths MUST start with `./`
- `agents` MUST be an array of individual file paths — NOT a directory string
- Skills NOT listed — auto-discovery only

---

## 11. Conventions Specific to Plugin-Creator

### Slug generation

Plugin directory name used directly as slug (already lowercase + hyphens):

```text
plugin directory: python3-development
slug:             python3-development   (no transformation needed)
```

### Plan file naming conventions

```text
.claude/plan/refactor-design-{plugin-slug}.md     # Design map
.claude/plan/tasks-refactor-{plugin-slug}.md      # Task file
.claude/plan/tasks-refactor-{slug}-followup-{N}.md  # Follow-up tasks
.claude/plan/REFACTOR-PLAN.md                     # Index (create if absent)
```

### Task status symbols (in task files)

```text
❌ NOT STARTED    # Task not begun
🔄 IN PROGRESS    # Task executing
✅ COMPLETE       # Task done and verified
```

### Task format in task files

```markdown
## Task {ID}: {Descriptive Name}

**Status**: ❌ NOT STARTED
**Dependencies**: [Comma-separated Task IDs or "None"]
**Priority**: [Integer 1-5, where 1 is highest]
**Complexity**: [Low/Medium/High]
**Agent**: [agent-name or plugin:skill-name]

**Target**: [File path being refactored]
**Issue Type**: [SKILL_SPLIT | AGENT_OPTIMIZE | DOC_IMPROVE | ORPHAN_RESOLVE | STRUCTURE_FIX]

**Acceptance Criteria**:
1. [Minimum 3 specific, measurable criteria]

**Required Inputs**:
- Design spec section: [which section]
- Source files: [paths]

**Expected Outputs**:
- [File paths to be created/modified]

**Can Parallelize With**: [Comma-separated Task IDs or "None"]
**Reason**: [Why parallelization is safe]

**Verification Steps**:
1. [Minimum 3 verification steps]
```

### Constraints in task planning

- NO temporal language in tasks: never "First, then, finally, before, after" — use "Dependencies: Task 1, Task 2"
- Minimum 3 acceptance criteria per task
- Minimum 3 verification steps per task
- Explicit parallelization analysis required

### Environment variables in skills

```text
${CLAUDE_PLUGIN_ROOT}  — Absolute path to plugin installation directory
${CLAUDE_PROJECT_DIR}  — Project root
$ARGUMENTS             — All arguments passed at invocation
$ARGUMENTS[N] or $N    — Specific argument by 0-based index
${CLAUDE_SESSION_ID}   — Current session ID
```

### Script execution convention

All Python scripts use PEP 723 inline metadata (dependencies install automatically via `uv run`):

```bash
uv run plugins/plugin-creator/scripts/plugin_validator.py {path}
```

Scripts are always run from repository root or use `${CLAUDE_PLUGIN_ROOT}`.

### CLAUDE.md scope and content

`plugins/plugin-creator/CLAUDE.md` is **dev-time only** — loaded when Claude works inside the plugin source directory. It is not delivered to plugin users. It contains:

- Component inventory (skills, agents, scripts with descriptions)
- Workflow reference tables
- Validation command reference
- Error code system overview
- Plugin system fundamentals (caching, scopes, env vars)

Plugin users receive instructions via SKILL.md and agent files only.

### Progressive disclosure design

SKILL.md body target: under 5k words (validated by `plugin_validator.py` SK006/SK007 thresholds). Detailed content goes to `references/` files, linked from SKILL.md. Reference files have Table of Contents at top (Claude Code reads files partially).

### Avoid deeply nested references

All reference files link directly from SKILL.md (one level deep). References do not link to sub-references.

---

_Pattern and architecture analysis: 2026-03-04_
_Sources: Direct file reads of all specified skill, agent, and config files._
