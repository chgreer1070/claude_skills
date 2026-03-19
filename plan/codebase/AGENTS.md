# Agent Reference Patterns Analysis

**Analysis Date:** 2026-03-18
**Focus:** Agent references across python3-development and development-harness plugins

---

## Executive Summary

The `python3-development` plugin currently contains 19 agents. The refactoring removes 9 agents (moving them to `development-harness` or deprecating them) to consolidate the workflow. Key findings:

- **9 agents to be removed from python3-development**: code-reviewer, ecosystem-researcher-v1.1-rt-ica, python-cli-architect, python-cli-design-spec, python-code-reviewer, python-pytest-architect, semantic-code-search, t0-baseline-capture, tn-verification-gate
- **Shared agents (present in both)**: 10 agents exist in both plugins (codebase-analyzer, context-gathering, context-refinement, doc-drift-auditor, ecosystem-researcher, feature-researcher, feature-verifier, integration-checker, plan-validator, swarm-task-planner)
- **Reference locations**: Agent names appear in 16 skill files, 1 rules file, and 1 MEMORY.md note
- **Plugin.json**: Does not declare an explicit agents array (uses auto-discovery) — no manual updates needed

---

## Current Agent Inventory

### python3-development Agents (19 total)

```
Agents present only in python3-development (to be removed):
- code-reviewer.md
- ecosystem-researcher-v1.1-rt-ica.md
- python-cli-architect.md
- python-cli-design-spec.md
- python-code-reviewer.md
- python-pytest-architect.md
- semantic-code-search.md
- t0-baseline-capture.md
- tn-verification-gate.md

Agents shared with development-harness:
- codebase-analyzer.md
- context-gathering.md
- context-refinement.md
- doc-drift-auditor.md
- ecosystem-researcher.md
- feature-researcher.md
- feature-verifier.md
- integration-checker.md
- plan-validator.md
- swarm-task-planner.md
```

### development-harness Agents (12 total)

```
Agents shared with python3-development (staying):
- codebase-analyzer.md
- context-gathering.md
- context-refinement.md
- doc-drift-auditor.md
- ecosystem-researcher.md
- feature-researcher.md
- feature-verifier.md
- integration-checker.md
- plan-validator.md
- swarm-task-planner.md

Agents unique to development-harness:
- generic-stage-agent.md
- service-docs-maintainer.md
```

---

## Agent Reference Locations

### Skills Referencing Agents (16 files with agent references)

| Skill File | Agent References | Reference Pattern |
|-----------|-----------------|------------------|
| `orchestrate/SKILL.md` | python-cli-architect, python-pytest-architect, python-code-reviewer, python-cli-design-spec, swarm-task-planner | `subagent_type="python3-development:..."` |
| `snakepolish/SKILL.md` | python-pytest-architect, python-code-reviewer | Task context notes |
| `python3-development/SKILL.md` | python-cli-architect, python-pytest-architect, python-code-reviewer, python-cli-design-spec, swarm-task-planner | `subagent_type` in docs, direct delegation guidance |
| `python3-test-design/SKILL.md` | python-pytest-architect | Agent recommendation |
| `python-cli-architect/SKILL.md` (nested skill) | shebangpython, modernpython | Reference patterns |
| `python-cli-architect/references/architecture-spec-patterns.md` | shebangpython | Activation reference |
| `python-cli-architect/references/quality-gate.md` | shebangpython | Skill activation |
| `create-feature-task/SKILL.md` | python-cli-architect, python-pytest-architect | Agent delegation guidance |
| `specialist-skill-routing/SKILL.md` | Various (ty, uv, hatchling, toml-python, pre-commit, async-python-patterns, python3-packaging, python3-publish-release-pipeline, pypi-readme-creator, stinkysnake) | Skill references, not agent references |
| `python3-development/references/python-development-orchestration.md` | python-cli-architect, python-pytest-architect, python-code-reviewer, python-cli-design-spec, swarm-task-planner | Mermaid diagrams + delegation steps |
| `python3-development/references/PEP723.md` | shebangpython | Skill reference |
| `use-command-template/SKILL.md` | (no agent refs, skill command examples) | — |
| `stinkysnake/SKILL.md` | python-code-reviewer, python-pytest-architect | Agent delegation in phases |
| `python3-development/planning/reference-document-architecture.md` | (stdlib-scripting todo) | Documentation plan |

**Key Reference Patterns:**
- Skill files use `subagent_type="python3-development:{agent-name}"` format for agent delegation
- Architecture reference docs contain Mermaid diagrams with agent names in node labels
- SKILL.md files reference agents in text descriptions and delegation guidance sections

### Local Workflow Rules File

**File**: `.claude/rules/local-workflow.md`

**Agent references by phase:**

- **Phase 1 Planning agents** (lines 34-48):
  - feature-researcher (line 42) — stays (in both)
  - codebase-analyzer (line 43) — stays (in both)
  - python-cli-design-spec (line 44) — **REMOVED**
  - swarm-task-planner (line 45) — stays (in both)
  - plan-validator (line 46) — stays (in both)
  - context-gathering (line 47) — stays (in both)

- **Phase 1 Agent locations table** (lines 54-63):
  - Lines 58: python-cli-design-spec — **REMOVED**
  - Lines 62-63: t0-baseline-capture, tn-verification-gate — **REMOVED**

- **Phase 3 Quality gates agents** (lines 256-276):
  - Line 256: code-reviewer — **REMOVED**
  - Lines 270-276: feature-verifier, integration-checker, doc-drift-auditor, service-docs-maintainer, context-refinement, t0-baseline-capture, tn-verification-gate
  - Lines 269, 275-276: code-reviewer, t0-baseline-capture, tn-verification-gate marked as python3-development only (lines show "—" in dh column) — **REMOVED**

**Update locations in local-workflow.md:**
1. Line 36: Remove or update "Architecture spec" row — python-cli-design-spec reference
2. Line 44: Remove "python-cli-design-spec" from Phase 3 delegation sequence
3. Line 58: Remove python-cli-design-spec agent location entry
4. Lines 62-63: Remove t0-baseline-capture and tn-verification-gate agent location entries
5. Line 256: Remove or update code-reviewer phase reference
6. Line 269: Remove code-reviewer from agent locations table
7. Lines 275-276: Remove t0-baseline-capture, tn-verification-gate from agent locations table

---

## Reference Patterns in python-development-orchestration.md

**File**: `plugins/python3-development/skills/python3-development/references/python-development-orchestration.md`

This document contains extensive agent references in orchestration guidance:

### Agents Referenced (20+ locations)

**python-cli-architect:**
- Lines 24, 50, 54, 56, 78, 104, 129, 151, 173, 186, 256, 267, 294, 303, 307, 475, 502, 530, 549, 555
- Context: Default agent for implementation tasks (used in 5+ workflow scenarios)
- Pattern: Labeled as "DEFAULT" for most implementation paths

**python-pytest-architect:**
- Lines 26, 55, 74, 105, 129, 150, 171, 175, 309, 471, 498, 505, 510
- Context: Test design and test-first scenarios
- Pattern: Used in parallel with python-cli-architect

**python-code-reviewer:**
- Lines 27, 57, 83, 106, 127, 172, 175, 330, 476, 485, 502, 509
- Context: Code quality review (Phase 4 in most workflows)
- Pattern: Appears as Phase 4 in every implementation scenario

**python-cli-design-spec:**
- Lines 28, 54, 70, 102, 467, 471
- Context: Architecture design (Phase 1 in feature development)
- Pattern: Produces plan/architect-{slug}.md artifacts

**swarm-task-planner:**
- Lines 60, 103
- Context: Task breakdown and parallel planning
- Pattern: Referenced as Phase 3 (task decomposition)

### Update Strategy for python-development-orchestration.md

This document will require significant updates because:
1. It teaches users to delegate to agents that will be removed
2. Delegation guidance flows must be rewritten to use development-harness agents
3. Multiple scenario diagrams reference removed agents by name
4. The "Default vs Restricted" decision tree for python-cli-architect vs stdlib-scripting may be impacted

Affected sections (by reference count):
- "Agent Selection" table (lines 24-28): 5 agent names
- Scenario 1 (feature from scratch): 5 agents
- Scenario 2 (feature in existing project): 6 agents
- Scenario 3 (code review): 4 agents
- Scenario 4 (refactoring): 4 agents
- Scenario 5 (bug fixing): 4 agents
- "When to use" sections: 8 agents

---

## Ecosystem Researcher Versioning

### Version in python3-development

**File**: `plugins/python3-development/agents/ecosystem-researcher-v1.1-rt-ica.md`

**Frontmatter (lines 1-7):**
```yaml
name: ecosystem-researcher
description: Researches domain ecosystems, technology landscapes, and tooling options before roadmap creation. Operates in three modes - Ecosystem discovery (what exists), Feasibility assessment (can it work), Comparison analysis (how options compare). Produces comprehensive research documents with confidence levels and source attribution. Use before major architectural decisions or technology selection.
tools: Read, Grep, Glob, Write, Edit, WebSearch, WebFetch, mcp__Ref__ref_search_documentation, mcp__Ref__ref_read_url, mcp__exa__get_code_context_exa, mcp__sequential_thinking__sequentialthinking
model: haiku
skills: subagent-contract
color: purple
```

**Key traits:**
- Model: haiku
- Tools: 10 total (includes sequential thinking, web search via MCP Ref/exa)
- Skills: subagent-contract
- Research modes: discovery, feasibility, comparison

### Version in development-harness

**File**: `plugins/development-harness/agents/ecosystem-researcher.md`

**Frontmatter (lines 1-7):**
```yaml
name: ecosystem-researcher
description: Researches domain ecosystems and technology landscapes before roadmap creation. Supports three modes - Ecosystem discovery, Feasibility assessment, and Comparison analysis. Use when exploring new domains, evaluating technology choices, or comparing implementation approaches. Requires MCP research servers (Ref, exa, context7, or firecrawl) - BLOCKs if none available.
tools: Read, Grep, Glob, mcp__ref__*, mcp__exa__*, mcp__context7__*, mcp__firecrawl__*
model: haiku
skills: subagent-contract
color: blue
```

**Key differences:**
- Tools: 4 MCP server families (vs 10 specific tools in v1.1)
- Color: blue (vs purple)
- Tool pattern: wildcard `mcp__*` (vs specific tool names)
- Fallback behavior: explicit BLOCK statement for missing MCP servers
- Description: Shorter, more constraint-focused

**Analysis:**
The development-harness version is more general (supports multiple MCP backends) while the python3-development version is more prescriptive (specific tools like Exa, Ref). The v1.1-rt-ica variant may be for RT-ICA (Rapid Task Identification & Completion Analysis) workflows. When removing ecosystem-researcher-v1.1-rt-ica, the simpler development-harness version becomes the canonical reference.

---

## Plugin Configuration Analysis

### python3-development/plugin.json

**Structure**: No explicit `"agents"` array found in plugin.json declaration.

**Auto-discovery behavior:**
Since agents array is not explicitly declared, the plugin uses auto-discovery:
- Scans `plugins/python3-development/agents/` directory
- Registers all `.md` files as agents
- No manual updates needed to plugin.json (auto-discovery handles new/removed agents automatically)

**Implication:**
When the 9 agents are deleted from `plugins/python3-development/agents/`, they will automatically be unregistered from the plugin. No plugin.json edits required.

---

## Skill Files With Agent References (Detailed)

### High-Impact Files (10+ agent references)

**1. orchestrate/SKILL.md** (lines 43-62)

```
Referenced agents:
- /python3-development:add-new-feature (skill, not agent)
- /python3-development:implement-feature (skill, not agent)
- /python3-development:complete-implementation (skill, not agent)
- python3-development:python-cli-architect (line 56) **REMOVE**
- python3-development:python-pytest-architect (line 57) **REMOVE**
- python3-development:python-code-reviewer (line 58) **REMOVE**
- python3-development:python-cli-design-spec (line 59) **REMOVE**
- python3-development:swarm-task-planner (line 60) **KEEP**
- python3-development:stdlib-scripting (line 62, skill not agent)

Update: Lines 56-59 must delegate to development-harness agents or be rewritten
```

**2. python3-development/SKILL.md** (lines 697-761)

```
Multiple references in sections:
- Line 697: "Implement with subagent_type="python3-development:python-cli-architect"" **REMOVE**
- Line 700: "python3-development:python-cli-architect then subagent_type="python3-development:python-pytest-architect"" **REMOVE BOTH**
- Lines 750-761: Agent references in "See Also" links section

Update: Rewrite delegation guidance to use development-harness agents
```

**3. python3-development/references/python-development-orchestration.md** (50+ lines)

```
Extensive refactoring needed:
- Lines 24-28: Agent selection table
- Lines 54-58: Scenario 1 Mermaid diagram
- Lines 102-107: Scenario 2 workflow
- Lines 127-129: Code review scenario
- Lines 150-154: Refactoring scenario
- Lines 171-176: Bug fix scenario
- Lines 256-307: "When to use" decision trees
- Lines 467-530: Detailed delegation examples

This is the most heavily impacted document.
```

**4. snakepolish/SKILL.md** (lines 14-27)

```
Task context notes reference:
- /python3-development:stinkysnake (skill)
- python3-development:python-pytest-architect (line 27) **REMOVE**

Update: Small impact, 1 agent reference to update
```

**5. stinkysnake/SKILL.md** (lines 75-483)

```
Complex workflow with agent phases:
- Line 75: Phase 9 references /python3-development:snakepolish
- Line 476: Agent(subagent_type="python3-development:python-code-reviewer", ...) **REMOVE**
- Line 477: Agent(subagent_type="python3-development:python-pytest-architect", ...) **REMOVE**

Update: 2 agent delegations to redirect to development-harness
```

---

## Update Summary by File Type

### Skill Files Requiring Updates (6 files)

| File | Agent References | Removal Count | Priority |
|------|-----------------|---------------|----------|
| `orchestrate/SKILL.md` | 4 agents | 4 | HIGH |
| `python3-development/SKILL.md` | 5 agents | 5 | HIGH |
| `python3-development/references/python-development-orchestration.md` | 20+ agents | 20+ | CRITICAL |
| `stinkysnake/SKILL.md` | 2 agents | 2 | HIGH |
| `snakepolish/SKILL.md` | 1 agent | 1 | MEDIUM |
| `python-cli-architect/references/quality-gate.md` | 1 skill (shebangpython) | 0 | LOW |

### Rules Files Requiring Updates (1 file)

| File | Location | References | Count | Priority |
|------|----------|-----------|-------|----------|
| `.claude/rules/local-workflow.md` | Phase tables + diagram | 9 agents | 11 lines | CRITICAL |

### Reference Removal Checklist

**Agents to remove from all files:**

- [ ] code-reviewer — 5 files (orchestrate, python3-development, local-workflow, stinkysnake, snakepolish)
- [ ] python-cli-architect — 8+ files (orchestrate, python3-development, python-development-orchestration, stinkysnake, snakepolish, plus 4+ documentation tables)
- [ ] python-cli-design-spec — 6 files (orchestrate, python3-development, python-development-orchestration, local-workflow x2)
- [ ] python-code-reviewer — 5 files (orchestrate, python3-development, python-development-orchestration, stinkysnake, snakepolish)
- [ ] python-pytest-architect — 8+ files (orchestrate, python3-development, python-development-orchestration, stinkysnake, snakepolish, plus tables)
- [ ] t0-baseline-capture — 2 files (local-workflow x2 locations)
- [ ] tn-verification-gate — 2 files (local-workflow x2 locations)
- [ ] semantic-code-search — 0 files (no skill references found, remove agent file only)
- [ ] ecosystem-researcher-v1.1-rt-ica — 0 files (no skill references found, remove agent file only, ecosystem-researcher stays)

**Agents to keep but verify:**

- [ ] codebase-analyzer — stays, referenced in local-workflow (present in both plugins)
- [ ] context-gathering — stays, referenced in local-workflow (present in both plugins)
- [ ] context-refinement — stays, referenced in local-workflow (present in both plugins)
- [ ] doc-drift-auditor — stays, referenced in local-workflow (present in both plugins)
- [ ] ecosystem-researcher — stays (both versions consolidated), referenced implicitly
- [ ] feature-researcher — stays, referenced in local-workflow (present in both plugins)
- [ ] feature-verifier — stays, referenced in local-workflow (present in both plugins)
- [ ] integration-checker — stays, referenced in local-workflow (present in both plugins)
- [ ] plan-validator — stays, referenced in local-workflow (present in both plugins)
- [ ] swarm-task-planner — stays, referenced in orchestrate and python3-development (present in both plugins)

---

## Critical References for Architect

### Files with Extensive Delegation Sequences

1. **python-development-orchestration.md** — Contains 5+ workflow scenarios with agent delegation chains. Each scenario needs rewriting to route to development-harness agents or to acknowledge the removal.

2. **local-workflow.md** — Contains two explicit agent location tables (Phase 1 and Phase 3) that directly reference removed agents by filepath. These are critical documentation for developers following the SAM workflow.

3. **orchestrate/SKILL.md** — Introduces the three-phase workflow (/add-new-feature → /implement-feature → /complete-implementation) and lists agent delegation guidance. Updates here affect downstream learning paths.

### Downstream Impact Assessment

**Skills that depend on removed agents (via subagent_type delegation):**
- `/python3-development:orchestrate` — delegates to 4 removed agents
- `/python3-development:python3-development` — teaches 5 removed agent delegations
- `/python3-development:stinkysnake` — delegates to 2 removed agents

**Skills that will NOT be affected:**
- All utility skills (ty, uv, pre-commit, hatchling, etc.) — no agent delegations
- All test-related skills — reference agents but don't delegate to them
- Reference documents for PEP 723, modern patterns — teach concepts, not agents

---

## Memory Note Context

From `.claude/projects/.../MEMORY.md` (session 2026-03-09):

> **Agent and Skill Writing Discipline**
> - **NEVER write agent body content directly as orchestrator** — always delegate to `plugin-creator:contextual-ai-documentation-optimizer`

This discipline applies to any agent updates needed during this refactoring. When updating agent files or their references, use the appropriate delegation workflow rather than direct edits.

---

## Summary of Analysis

**Total files with agent references:** 17 (16 skills + 1 rules file)

**Agents to be removed:** 9

**High-impact update zones:**
1. `.claude/rules/local-workflow.md` — 11 reference lines across 2 tables + data flow diagram
2. `python-development-orchestration.md` — 50+ reference lines in 5+ scenarios
3. `orchestrate/SKILL.md` — 4 agent references in delegation guidance
4. `python3-development/SKILL.md` — 5+ agent references in concepts section
5. `stinkysnake/SKILL.md` — 2 agent delegations in workflow phases

**Files with zero references (safe to delete):**
- `semantic-code-search.md` — not mentioned in any skill or documentation
- `ecosystem-researcher-v1.1-rt-ica.md` — not directly referenced (kept version in both plugins)

**Plugin configuration impact:** None (auto-discovery handles agent removal)

---

_Analysis completed: 2026-03-18_
_Prepared for architect agent to design reference update strategy_
