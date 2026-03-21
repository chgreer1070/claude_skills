# Feature Context: Consolidate SAM Workflow Skills

## Document Metadata

- **Generated**: 2026-03-21
- **Input Type**: existing_document
- **Source**: Backlog items #957, #958, #959 and comparison report `.claude/reports/skill-migration-comparison-2026-03-21.md`
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Migrate language-agnostic SAM workflow skills from the `python3-development` plugin to the `development-harness` (dh) plugin. Three backlog items track this:

- **#957**: Remove 5 duplicate skills (identical copies in both plugins)
- **#958**: Migrate SAM hook scripts (`task_status_hook.py`, `task_format.py`, `get_task_context.py`)
- **#959**: Migrate 4 skills (`implement-feature`, `start-task`, `complete-implementation`, `add-new-feature`) and 2 agents (`t0-baseline-capture`, `tn-verification-gate`)

---

## Core Intent Analysis

### WHO (Target Users)

- **Plugin authors** building language plugins that compose with the development harness
- **Session orchestrators** (Claude Code main context) invoking SAM workflow skills during feature development
- **The development-harness plugin itself** as the canonical owner of language-agnostic development process

### WHAT (Desired Outcome)

All language-agnostic SAM workflow skills, agents, and hook scripts live in the `development-harness` plugin. The `python3-development` plugin retains only Python-specific components (agents, orchestrate skill, language manifest). Users invoke SAM workflow skills via `/dh:` namespace instead of `/python3-development:`.

### WHEN (Trigger Conditions)

This consolidation is needed NOW because:

1. The dh plugin CLAUDE.md already advertises 7 workflow stage skills (`/dh:discovery`, `/dh:execution`, etc.) but only the documentation references exist -- the actual skill directories have not been created
2. The `local-workflow.md` references skills by their python3-development locations, creating coupling between process documentation and a language-specific plugin
3. New language plugins cannot use SAM workflow skills without depending on the Python plugin

### WHY (Problem Being Solved)

**Architectural misplacement**: Language-agnostic development process skills are trapped inside a language-specific plugin. This violates the Voltron composition model where the harness owns process and language plugins own specialists.

**Duplication**: 5 skills exist as identical copies in both plugins, creating maintenance burden and divergence risk.

**Blocked composition**: The dh plugin's CLAUDE.md describes a 7-stage pipeline with workflow skills, but 4 of the core workflow skills (`implement-feature`, `start-task`, `complete-implementation`, `add-new-feature`) only exist in python3-development.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Voltron Role Resolution in dh

- **Location**: `plugins/development-harness/skills/development-harness/SKILL.md:22-66`
- **Relevance**: The dh orchestrator already has a role resolution protocol that detects project language, loads a language manifest, and resolves abstract roles (architect, test-designer, code-reviewer, design-spec, linting) to concrete agents. Skills like `add-new-feature` (Phase 3 hardcodes `python-cli-design-spec`) and `complete-implementation` (Phase 1 hardcodes `code-reviewer`) must use this resolution mechanism instead of hardcoded agent names.
- **Reusable**: The role resolution flowchart and manifest schema provide the pattern for replacing hardcoded Python agent references with dynamic role lookups.

#### Pattern 2: dh Implementation Manager Already Uses sam CLI

- **Location**: `plugins/development-harness/skills/implementation-manager/SKILL.md` (per comparison report)
- **Relevance**: The dh version of implementation-manager already references `uv run sam` (modern CLI) while python3-dev still references the old `implementation_manager.py`. This confirms dh is the forward-looking canonical location. The dh version also documents `claim` and `read` commands that python3-dev lacks.
- **Reusable**: The dh implementation-manager SKILL.md serves as the template for how migrated skills should reference the sam CLI.

#### Pattern 3: Hook Script Path Resolution via CLAUDE_SKILL_DIR

- **Location**: `plugins/python3-development/skills/start-task/SKILL.md` (per comparison report, hook frontmatter)
- **Relevance**: The `start-task` skill's hook references `${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py` -- a relative path that assumes co-location with implementation-manager in the same plugin. After migration, this path must still resolve correctly within dh's skill directory structure.
- **Reusable**: This path pattern is the mechanism for hook scripts; migrated skills must maintain equivalent relative paths.

#### Pattern 4: Advertised but Missing dh Workflow Skills

- **Location**: `plugins/development-harness/CLAUDE.md` (Skills Overview section, lines listing `/dh:discovery` through `/dh:final-verification`)
- **Relevance**: The dh CLAUDE.md lists 7 workflow stage skills (`/dh:discovery`, `/dh:planning`, `/dh:context-integration`, `/dh:task-decomposition`, `/dh:execution`, `/dh:forensic-review`, `/dh:final-verification`) but NONE of these skill directories exist. Only references to them appear in documentation files (`default-development-flow.md`, `sdlc-stage-taxonomy.md`, `implementation-manager/SKILL.md`, `poc-validation-guide.md`). The migrating skills (`implement-feature`, `start-task`, `complete-implementation`, `add-new-feature`) map to stages S5/S6/S7 and S1-S4 respectively -- they may be the intended implementations of these advertised skills.
- **Reusable**: The naming convention and stage mapping in dh documentation provides guidance for where migrated skills should land.

### Existing Infrastructure

1. **sam CLI** (`uv run sam`): Language-agnostic task plan management already used by dh's implementation-manager
2. **Backlog MCP tools** (`mcp__plugin_dh_backlog__*`): Used by `complete-implementation` for follow-up routing
3. **Role resolution protocol**: `plugins/development-harness/skills/development-harness/references/role-resolution-protocol.md`
4. **Language manifest schema**: `plugins/development-harness/skills/development-harness/references/language-manifest-schema.md`
5. **`local-workflow.md`**: `.claude/rules/local-workflow.md` -- primary consumer documentation for the SAM workflow, references all migrating skills extensively (30 occurrences)

### Code References

- `plugins/development-harness/skills/development-harness/SKILL.md:57-64` -- Abstract role definitions (architect, test-designer, code-reviewer, design-spec, linting)
- `plugins/development-harness/CLAUDE.md` -- Skills Overview lists 7 workflow stage skills that do not exist as directories
- `.claude/rules/local-workflow.md` -- 30 references to the migrating skills; must be updated post-migration
- `plugins/python3-development/skills/implementation-manager/scripts/` -- Hook scripts directory (task_status_hook.py, task_format.py, get_task_context.py, test_task_parsing.py)
- `plugins/python3-development/commands/development/create-feature-task.md` -- References migrating skills
- `plugins/python3-development/commands/development/config/command-patterns.yml` -- References migrating skills

---

## Use Scenarios

### Scenario 1: New Language Plugin Author

**Actor**: Developer creating a TypeScript language plugin
**Trigger**: Wants to use SAM workflow for TypeScript projects
**Goal**: Invoke `/dh:implement-feature` and have it resolve TypeScript-specific agents from a manifest
**Expected Outcome**: The harness runs the execution loop, resolving `code-reviewer` to a TypeScript code reviewer declared in the TypeScript manifest, without requiring the python3-development plugin to be installed

### Scenario 2: Existing Python Developer

**Actor**: Developer using the python3-development plugin for Python projects
**Trigger**: Runs `/add-new-feature` or `/implement-feature` as they do today
**Goal**: Same workflow behavior as before migration
**Expected Outcome**: Skills resolve from dh namespace, Python-specific agents resolve via language manifest, no behavioral regression

### Scenario 3: Removing Duplicate Skills

**Actor**: Repository maintainer
**Trigger**: Notices divergence between identical skill copies
**Goal**: Single canonical location for each skill
**Expected Outcome**: 5 duplicate skills removed from python3-development; dh copies remain as canonical; no broken skill references

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Integration | `add-new-feature` Phase 3 hardcodes `python-cli-design-spec` agent -- needs role resolution via language manifest | Migration blocked until Phase 3 uses abstract `design-spec` role |
| 2 | Integration | `complete-implementation` Phase 1 hardcodes `code-reviewer` agent -- needs role resolution | Migration blocked until Phase 1 uses abstract `code-reviewer` role |
| 3 | Scope | dh CLAUDE.md advertises 7 workflow stage skills that do not exist -- should migrated skills map to these names or keep their current names? | Naming decision affects all downstream references |
| 4 | Integration | `start-task` hook path `${CLAUDE_SKILL_DIR}/../../implementation-manager/scripts/task_status_hook.py` assumes co-location -- must work in dh directory structure | Hook breaks if relative path does not resolve after migration |
| 5 | Scope | `local-workflow.md` has 30 references to migrating skills -- must be updated to reflect new dh namespace | Stale documentation causes agent routing failures |
| 6 | Scope | `subagent-contract` exists in 3 locations (python3-dev, plugin-creator, and referenced by agents) -- consolidation location unclear | Agents declaring `skills: subagent-contract` may fail to resolve after migration |
| 7 | Integration | python3-development `commands/development/` directory references migrating skills -- needs updating or removal | Commands route to nonexistent skills post-migration |
| 8 | Scope | dh `implementation-manager/scripts/` has only stale `.pyc` files -- needs clean scripts directory | Hook scripts have no destination directory in dh |

---

## Questions Requiring Resolution

### Q1: Should migrated skills keep their current names or adopt dh stage names?

- **Category**: Scope
- **Gap**: Gap #3 -- dh CLAUDE.md advertises `/dh:execution`, `/dh:final-verification` etc. but the migrating skills are named `implement-feature`, `complete-implementation` etc.
- **Question**: Should `implement-feature` become `/dh:execution`, `complete-implementation` become `/dh:final-verification`, etc.? Or should they keep their current names and the dh CLAUDE.md be updated to match?
- **Options**:
  - A) Rename to match dh stage taxonomy (`/dh:execution`, `/dh:discovery`, etc.)
  - B) Keep current names (`/dh:implement-feature`, `/dh:complete-implementation`, etc.) and update dh CLAUDE.md
  - C) Keep current names AND create the stage-named skills as thin wrappers that delegate to the migrated skills
- **Why It Matters**: Affects all downstream references in `local-workflow.md`, agent files, commands, and user muscle memory. Renaming is a one-time cost but creates consistency with the 7-stage model. Keeping names preserves compatibility but leaves the advertised stage skills unimplemented.
- **Resolution**: _pending_

### Q2: Where should subagent-contract be consolidated?

- **Category**: Scope
- **Gap**: Gap #6 -- 3 copies exist across python3-dev and plugin-creator
- **Question**: Should `subagent-contract` live in dh (since migrated agents need it), plugin-creator (since it is a general-purpose contract), or remain in multiple plugins?
- **Options**:
  - A) Consolidate to dh -- co-located with the agents that use it
  - B) Consolidate to plugin-creator -- it is a generic orchestration pattern, not specific to dh
  - C) Keep copies in both dh and plugin-creator (each plugin's agents resolve locally)
- **Why It Matters**: Agents declaring `skills: subagent-contract` in frontmatter resolve the skill from the plugin they belong to. After migrating `t0-baseline-capture` and `tn-verification-gate` to dh, they need a dh-local copy or cross-plugin resolution must work.
- **Resolution**: _pending_

### Q3: Does the python3-development language manifest already exist?

- **Category**: Integration
- **Gap**: Gaps #1 and #2 -- hardcoded Python agent references need language manifest resolution
- **Question**: Does `python3-development` already provide a `references/language-manifest.md` that declares role mappings (architect -> python-cli-design-spec, code-reviewer -> python-code-reviewer, etc.)? If not, creating one is a prerequisite for migration.
- **Why It Matters**: Without a language manifest, the migrated skills cannot resolve Python-specific agents at runtime. The manifest is the bridge between the language-agnostic harness and the Python-specific specialists.
- **Resolution**: _pending_

### Q4: Should local-workflow.md be updated as part of this migration or separately?

- **Category**: Scope
- **Gap**: Gap #5 -- 30 references to migrating skills in documentation
- **Question**: Is updating `local-workflow.md` in scope for this migration, or should it be a separate follow-up task?
- **Options**:
  - A) Update inline as part of migration -- ensures documentation stays consistent
  - B) Create a separate backlog item -- keeps migration scope focused on file moves
- **Why It Matters**: `local-workflow.md` is the primary reference document for the SAM workflow. Stale references cause agent routing failures. However, updating 30 references adds scope.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Remove 5 identical duplicate skills from python3-development (clear-cove-task-design, generate-task, planner-rt-ica, implementation-manager SKILL.md, validation-protocol)
2. Migrate hook scripts (task_status_hook.py, task_format.py, get_task_context.py) to dh's implementation-manager/scripts/ directory
3. Migrate 4 workflow skills (implement-feature, start-task, complete-implementation, add-new-feature) to dh, replacing hardcoded Python agent references with role resolution
4. Migrate 2 agents (t0-baseline-capture, tn-verification-gate) to dh/agents/
5. Ensure subagent-contract is resolvable from dh context (pending Q2)
6. Update local-workflow.md and other consumer documentation (pending Q4)
7. Create or verify python3-development language manifest with role mappings (pending Q3)

---

## Risks and Dependencies

### Dependencies

- **Language manifest**: Skills `add-new-feature` and `complete-implementation` cannot be migrated until their hardcoded agent references are replaced with role resolution. This requires either an existing or newly created language manifest for python3-development.
- **Hook script co-location**: `start-task` and `implement-feature` both reference `task_status_hook.py` via relative paths. The hook scripts (#958) should be migrated BEFORE the skills (#959) to ensure paths resolve correctly.
- **sam CLI**: Already language-agnostic and installed via `uv run sam`. No migration needed for the CLI itself.

### Risks

- **Behavioral regression**: Migrated skills must produce identical behavior for Python projects. The role resolution adds an indirection layer that could fail if the manifest is misconfigured or missing.
- **Cross-plugin skill resolution**: Agents declaring `skills: subagent-contract` must resolve the skill from their new plugin context. If cross-plugin resolution does not work, agents will fail to load the contract.
- **Documentation drift**: 30+ references in `local-workflow.md`, plus references in python3-development's README.md, CLAUDE.md, and commands/ directory, all need updating. Missing any creates stale routing.

### Ordering Constraint

The three backlog items have a natural dependency order:

1. **#957 first** (remove duplicates) -- no dependencies, lowest risk
2. **#958 second** (migrate hook scripts) -- creates the destination for hook paths
3. **#959 last** (migrate skills and agents) -- depends on hook scripts being in place and role resolution being implemented

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design
