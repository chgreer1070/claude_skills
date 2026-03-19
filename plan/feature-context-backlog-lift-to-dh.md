# Feature Context: Lift Backlog Integration Skills to development-harness Plugin

## Document Metadata

- **Generated**: 2026-03-18
- **Input Type**: existing_document
- **Source**: GitHub Issue #843, groomed backlog item `.claude/backlog/p1-refactor-lift-backlog-integration-from-python3-development-i.md`
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Move three backlog integration skills from project-level (`.claude/skills/`) into the development-harness plugin (`plugins/development-harness/skills/`), making dh the universal process engine with backlog as its upstream intake layer. The backlog MCP server (`.claude/skills/backlog/`) is NOT moving.

---

## Core Intent Analysis

### WHO (Target Users)

1. **Plugin authors** installing the development-harness (dh) plugin who want the full intake-to-implementation pipeline without project-level skill setup.
2. **Orchestrators** loading dh skills that need the backlog intake layer (create, groom, work) as part of the same plugin.
3. **Future language plugin developers** building on dh's process engine who need backlog intake without duplicating skills.

### WHAT (Desired Outcome)

Three skills relocate from `.claude/skills/` (project-level) to `plugins/development-harness/skills/` (plugin-level):

| Skill | Current Location | Files |
|-------|-----------------|-------|
| `create-backlog-item` | `.claude/skills/create-backlog-item/` | SKILL.md |
| `groom-backlog-item` | `.claude/skills/groom-backlog-item/` | SKILL.md + 2 reference files |
| `work-backlog-item` | `.claude/skills/work-backlog-item/` | SKILL.md + 8 reference files |

After the move, any caller that previously used bare `Skill(skill="work-backlog-item")` must use the namespaced form `Skill(skill="development-harness:work-backlog-item")` (or the short alias if one exists).

The backlog MCP server at `.claude/skills/backlog/` remains project-level — it is infrastructure, not a process skill.

### WHEN (Trigger Conditions)

- When a user installs the dh plugin and expects backlog intake skills to be available without project-level `.claude/skills/` setup.
- When the orchestrator invokes `/work-backlog-item` as part of the SAM planning pipeline and expects it to resolve from the dh plugin namespace.

### WHY (Problem Being Solved)

Currently, the three backlog intake skills live at project level, making them invisible to dh plugin consumers who don't have this repo's `.claude/skills/` directory. Moving them into dh makes the plugin self-contained: install dh, get the full pipeline from backlog intake through implementation. This also eliminates duplication pressure — future language plugins (beyond python3-development) can depend on dh's backlog intake rather than each maintaining copies.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: dh Plugin Auto-Discovery

- **Location**: `plugins/development-harness/skills/` (directory contains ~15 skills; no `plugin.json` `skills` key override found — glob for `plugins/development-harness/plugin.json` returned no results)
- **Relevance**: Confirms auto-discovery is active. Dropping skill directories into `plugins/development-harness/skills/` should register them automatically without `plugin.json` edits.
- **Reusable**: The existing directory structure convention (skill-name directory containing SKILL.md and optional references/).

#### Pattern 2: Cross-Plugin Skill Invocation (interop skill)

- **Location**: `plugins/development-harness/skills/interop/SKILL.md:116`
- **Relevance**: Already uses `Skill(skill="work-backlog-item", args="#N")` with bare name. This is one of the call sites that breaks after the move.
- **Reusable**: Shows the pattern that needs updating — bare name to namespaced form.

#### Pattern 3: Hook-Based Skill References

- **Location**: `.claude/hooks/stop-backlog-reminder.cjs:8-9`
- **Relevance**: Project-level hook that injects `Skill(skill: "create-backlog-item")` and `Skill(skill: "work-backlog-item")` into session context. These are bare-name references that may or may not need namespace update depending on resolution rules for project-level hooks calling plugin skills.
- **Reusable**: Pattern shows hooks as a call site category distinct from skill-to-skill calls.

#### Pattern 4: Self-Referencing Between the Three Skills

- **Location**: `.claude/skills/work-backlog-item/SKILL.md:177,217` and `.claude/skills/work-backlog-item/references/step-procedures.md:77,197-198`
- **Relevance**: `work-backlog-item` invokes both `create-backlog-item` and `groom-backlog-item` via `Skill()` calls. After the move, all three are siblings in the same plugin — resolution behavior for intra-plugin bare names needs clarification.
- **Reusable**: Determines whether internal references need namespace prefix or not.

### Existing Infrastructure

- **Backlog MCP server** (`.claude/skills/backlog/`) — stays project-level, provides `mcp__backlog__*` tools. All three skills call these MCP tools; the MCP server does not need to move for the skills to function from a different location.
- **Backlog tools administrator** (`.claude/skills/backlog-tools-administrator/`) — references all three skills by path in `references/domain-registry.md`. Paths will need updating.
- **`.claude/CLAUDE.md`** — Session Start section references `/create-backlog-item` and `/work-backlog-item`; Backlog Operations section references all three. These are slash-command references (user-facing), not `Skill()` calls.
- **`plan/` directory** — Multiple plan artifacts reference the skills by bare name in code examples and architecture docs. These are historical documentation, not live call sites.

### Code References

- `.claude/skills/create-backlog-item/SKILL.md` — source skill (1 file)
- `.claude/skills/groom-backlog-item/SKILL.md` — source skill + `references/issue-classification.md`, `references/groomer-agent.md`
- `.claude/skills/work-backlog-item/SKILL.md` — source skill + 8 reference files in `references/`
- `plugins/development-harness/skills/interop/SKILL.md:116` — bare-name `Skill()` call to `work-backlog-item`
- `.claude/hooks/stop-backlog-reminder.cjs:8-9` — bare-name `Skill()` references in hook
- `.claude/skills/backlog/SKILL.md:214-217` — documents relationship to all three skills
- `.claude/skills/backlog-tools-administrator/references/domain-registry.md:31-58` — hardcoded paths to all three skills and their reference files

---

## Use Scenarios

### Scenario 1: Plugin Consumer Gets Full Pipeline

**Actor**: Developer who installs the dh plugin via Claude Code marketplace
**Trigger**: Wants to use SAM workflow (backlog item to implementation) in their own project
**Goal**: Run `/development-harness:work-backlog-item` to plan and execute a feature
**Expected Outcome**: The skill resolves from the installed dh plugin without requiring any project-level `.claude/skills/` setup. The skill can call `mcp__backlog__*` tools (assuming the backlog MCP server is configured separately).

### Scenario 2: Orchestrator Runs SAM Pipeline

**Actor**: Claude Code orchestrator executing the SAM workflow in this repository
**Trigger**: `/implement-feature` or `/complete-implementation` invokes backlog skills as part of follow-up routing
**Goal**: Create or attach backlog items during the follow-up routing phase
**Expected Outcome**: `Skill(skill="development-harness:create-backlog-item", args="--auto {title}")` resolves correctly. Internal calls from `work-backlog-item` to `create-backlog-item` and `groom-backlog-item` also resolve.

### Scenario 3: Future Language Plugin Depends on dh

**Actor**: Author of a new language plugin (e.g., `rust-development`) that uses dh as its process engine
**Trigger**: Wants backlog intake without duplicating the three skills
**Goal**: Declare dh as a dependency and reference `development-harness:work-backlog-item` from their plugin's workflow skills
**Expected Outcome**: Cross-plugin skill invocation works using the namespaced form.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Behavior | Skill resolution for intra-plugin bare names — when `work-backlog-item` calls `Skill(skill="create-backlog-item")` and both are in the same plugin, does the bare name resolve? | Determines whether ~4 internal `Skill()` calls need namespace prefix |
| 2 | Scope | Whether project-level callers (`.claude/CLAUDE.md` slash commands, `.claude/hooks/stop-backlog-reminder.cjs`) need namespace update | If bare names don't resolve to plugin skills from project-level context, these break silently |
| 3 | Scope | Whether old `.claude/skills/{skill}/` directories should be deleted or kept as forwarding stubs | Deletion risks breaking any caller not yet updated; stubs add maintenance burden |
| 4 | Integration | `.claude/skills/backlog-tools-administrator/references/domain-registry.md` has hardcoded paths to all three skills and their reference files | Stale paths produce incorrect guidance for the backlog tools administrator |
| 5 | Scope | The namespace prefix — is it `dh:` (short alias) or `development-harness:` (full plugin name)? The backlog item uses both forms. | All call site updates must use the correct form consistently |
| 6 | Scope | How many plan artifacts in `plan/` contain bare-name `Skill()` calls that should be updated vs. treated as historical documentation | Mass-updating plan docs risks churn; leaving them risks copy-paste of stale patterns |

---

## Questions Requiring Resolution

### Q1: Intra-plugin bare-name resolution

- **Category**: Behavior
- **Gap**: When `work-backlog-item` calls `Skill(skill="create-backlog-item")` and both skills are in the same plugin (`development-harness`), does the bare name resolve within the plugin scope?
- **Question**: Does Claude Code resolve bare skill names within the calling skill's own plugin before checking project-level skills?
- **Options**:
  - A) Yes — bare names resolve intra-plugin; internal calls need no change
  - B) No — all `Skill()` calls require the full namespace; internal calls must become `development-harness:create-backlog-item`
- **Why It Matters**: Determines whether ~4 internal `Skill()` references in `work-backlog-item` and its reference files need updating.
- **Resolution**: _pending_

### Q2: Project-level caller resolution after move

- **Category**: Integration
- **Gap**: Project-level files (`.claude/CLAUDE.md`, `.claude/hooks/stop-backlog-reminder.cjs`) currently reference these skills by bare name. After the skills move to a plugin, do bare names from project-level context resolve to installed plugin skills?
- **Question**: When a project-level hook or CLAUDE.md references `/create-backlog-item`, does Claude Code search installed plugins if no project-level skill matches?
- **Options**:
  - A) Yes — plugin skills are in the resolution path for project-level references
  - B) No — project-level callers must use the namespaced form
- **Why It Matters**: If B, then `.claude/CLAUDE.md` Session Start, Backlog Operations sections, and the stop-backlog-reminder hook all need updates.
- **Resolution**: _pending_

### Q3: Delete originals or keep forwarding stubs?

- **Category**: Scope
- **Gap**: After moving the skills, the original `.claude/skills/{skill}/` directories could be deleted (clean break) or kept as thin forwarding stubs (backward compatibility).
- **Question**: Should the original project-level skill directories be deleted after the move, or should they be kept as forwarding stubs that delegate to the dh namespace?
- **Options**:
  - A) Delete originals — clean break, update all callers at once
  - B) Keep forwarding stubs — backward compatible, remove later
- **Why It Matters**: Option A is simpler but requires all callers to be updated atomically. Option B adds temporary indirection but allows incremental migration.
- **Resolution**: _pending_

### Q4: Canonical namespace prefix

- **Category**: Scope
- **Gap**: The backlog item uses both `dh:` and `development-harness:` as the namespace prefix in different sections.
- **Question**: What is the canonical namespace prefix — `dh:` (if short aliases are supported) or `development-harness:` (full plugin directory name)?
- **Options**:
  - A) `development-harness:` — full plugin directory name (verified resolution mechanism)
  - B) `dh:` — short alias (if Claude Code supports plugin aliases)
- **Why It Matters**: All updated call sites must use a single consistent form.
- **Resolution**: _pending_

### Q5: Plan artifact updates

- **Category**: Scope
- **Gap**: Multiple files under `plan/` contain bare-name `Skill()` calls in code examples (e.g., `plan/tasks-1-followup-routing.md`, `plan/architect-followup-routing.md`, `plan/codebase/cross-references-backlog.md`).
- **Question**: Should plan artifacts be updated to reflect the new namespace, or are they treated as historical documentation that doesn't need updating?
- **Options**:
  - A) Update plan artifacts — prevents copy-paste of stale patterns
  - B) Leave as-is — they are historical records, not live call sites
- **Why It Matters**: Updating adds scope and churn; not updating risks propagating stale patterns when agents reference plan docs.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

_These goals will be finalized after questions are resolved._

1. Three backlog intake skills (`create-backlog-item`, `groom-backlog-item`, `work-backlog-item`) exist in `plugins/development-harness/skills/` and resolve via the dh plugin namespace.
2. All live call sites (skills, hooks, CLAUDE.md) use the correct namespace prefix and resolve successfully.
3. The backlog MCP server (`.claude/skills/backlog/`) remains project-level and continues functioning.
4. The backlog-tools-administrator domain registry reflects the new skill locations.
5. No bare-name `Skill()` calls to the three moved skills remain in live (non-plan) files.

---

## Next Steps

After questions are resolved:

1. Update "Resolution" fields in Questions section
2. Finalize Goals section
3. Proceed to RT-ICA assessment
4. Then proceed to architecture design

---

## Post-Implementation Annotations

_Added by context-refinement agent on 2026-03-18_

### Design Refinements

1. **Relative link breakage from path depth change (not anticipated in gap analysis)**: The gap analysis
   identified 6 gaps but did not include relative link depth as a risk. When skills moved from
   `.claude/skills/{skill}/` (2 levels deep) to `plugins/development-harness/skills/{skill}/` (4 levels
   deep), all cross-directory upward-traversal links broke. This was not a Q-question gap — it was a
   mechanical consequence of directory relocation that the gap analysis did not model.
   - Files affected: `work-backlog-item/SKILL.md` (3 links to `.claude/docs/sdlc-layers/`) and
     `work-backlog-item/references/github-integration.md` (1 link to `.claude/skills/gh/references/`).
   - Fix: Depth correction (+2 `../` segments). Detected by LK001 linting in T01.
   - Future guidance: Add "upward-traversal link audit" as a standard step in any skill relocation task.

2. **Intra-dh bare names confirmed working (Q1 validated in practice)**: The feature context listed Q1
   as "pending" resolution. The architect spec resolved it as "bare names work within dh — no updates
   needed." This was confirmed correct during implementation: `interop/SKILL.md` and
   `work-backlog-item/SKILL.md` bare `Skill()` calls to sibling skills resolved without `dh:` prefix.

3. **complete-implementation/SKILL.md reference count exceeded spec**: The spec's Codebase Research
   identified `complete-implementation/SKILL.md` lines ~239, ~250-251 as the change scope. Implementation
   found 7 total locations. The feature context note "Multiple plan artifacts reference the skills by bare
   name" applied to live SKILL.md files as well, not just plan artifacts.
