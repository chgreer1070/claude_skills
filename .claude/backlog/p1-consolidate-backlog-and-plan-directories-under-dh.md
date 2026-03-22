---
name: Consolidate backlog and plan directories under .dh/
description: Backlog items live in .claude/backlog/ and plan artifacts live in plan/ at project root. These are both development-harness artifacts but stored in inconsistent locations. All development-harness artifacts (backlog items, plan files, reports, context files) need to be consolidated under a single .dh/ directory. A migration tool is needed that moves existing files, corrects any internal path references, and updates all consumers. The migration tool must analyze real existing files to determine what path patterns exist and how to detect and transform them — not assume patterns from documentation.
metadata:
  topic: consolidate-backlog-and-plan-directories-under-dh
  source: User request — session 2026-03-21, observed inconsistency between .claude/backlog/ and plan/ locations
  added: '2026-03-22'
  priority: P1
  type: Refactor
  status: open
  issue: '#981'
  last_synced: '2026-03-22T13:17:58Z'
  groomed: '2026-03-22'
  plan: plan/P981-consolidate-dh-paths.yaml
---

## RT-ICA

<div><sub>2026-03-22T12:27:20Z</sub>

RT-ICA Snapshot: Consolidate backlog and plan directories under .dh/
Goal: Move .claude/backlog/ and plan/ under a single .dh/ directory with migration tooling

Conditions:
1. Current directory structure of .claude/backlog/ — what files exist | Status: DERIVABLE
2. Current directory structure of plan/ — what files exist | Status: DERIVABLE
3. All consumers of .claude/backlog/ paths — scripts, skills, agents, hooks, CLAUDE.md, rules | Status: DERIVABLE
4. All consumers of plan/ paths — scripts, skills, agents, hooks, CLAUDE.md, rules | Status: DERIVABLE
5. Target directory layout under .dh/ — how to organize the merged content | Status: MISSING (human design decision)
6. Whether .claude/context/ directory is also in scope for migration | Status: MISSING (human scoping decision)
7. Whether .claude/reports/ directory is also in scope for migration | Status: MISSING (human scoping decision)
8. Migration strategy — big bang vs incremental with symlinks | Status: MISSING (human design decision)
9. Impact on installed plugin cache paths (~/.claude/plugins/cache/) | Status: DERIVABLE
10. Impact on CI workflows referencing these paths | Status: DERIVABLE

AVAILABLE count: 0
DERIVABLE count: 5
MISSING count: 4
</div>

## Groomed (2026-03-22)


### Impact

<div><sub>2026-03-22T00:00:00Z</sub>

<div><sub>2026-03-22T12:28:34Z</sub>
</div>

<div><sub>2026-03-22T12:31:18Z</sub>

Five categories of systems will be affected (summarized from Impact Radius):

**1. Code — Producers (12–15 files)**
- backlog_core/server.py, backlog_core/operations.py — MCP write operations to backlog
- sam_core/ tools — task plan file creation
- task_status_hook.py, get_task_context.py — runtime file I/O to context/status
- Backlog MCP server initialization — directory setup on startup
- All hardcoded path strings must be updated

**2. Code — Consumers (15–20 files)**
- backlog_core/parsing.py — filesystem discovery of backlog items
- sam_status, sam_ready MCP tools — plan directory querying
- artifact_provider.py, artifact_read — artifact file path construction
- Hook scripts — multiple hardcoded path patterns
- .gitignore patterns — glob matching for plan/, .claude/backlog/, .claude/context/, .claude/reports/
- Pre-commit hooks — may exclude directories by path

**3. Tests and Fixtures (50+ files)**
- Test fixtures in plugins/development-harness/tests_sam/fixtures/*.yaml — hardcoded paths
- Test assertions (20+ references) — path validation in test expectations
- Mock path construction in test data generators
- SAM CLI integration tests with plan/ arguments

**4. Documentation (25–30 files)**
- .claude/rules/local-workflow.md — comprehensive path descriptions
- plugins/development-harness/docs/ — multiple architecture/lifecycle docs referencing paths
- TASK_FILE_FORMAT.md — naming convention documentation
- CLAUDE.md (project + plugin) — extensively documented paths
- Agent descriptions — artifact creation paths documented
- Skill SKILL.md files — 20+ files document expected path structure

**5. Configuration and CI (3–4 files)**
- .gitignore — patterns for old directory locations
- .pre-commit-config.yaml — may exclude directories by path
- .github/workflows/backlog-sync.yml — may reference .claude/backlog/
- .github/workflows/code-quality.yml — may exclude plan/ from linting

**6. GitHub Issues (Unknown count, requires API iteration)**
- Artifact manifest entries in issue bodies — contain plan/ paths stored by artifact_register
- Must be updated via artifact_register with new .dh/plan/ paths

**Critical path dependencies**: Code changes must precede file movement to avoid runtime errors. Documentation updates must follow migration to avoid stale guidance.
</div>

### Issue Classification

<div><sub>2026-03-22T12:28:52Z</sub>

### Reproducibility

<div><sub>2026-03-22T12:30:56Z</sub>

To observe the inconsistent directory layout:

1. List current backlog directory:
   ```bash
   ls -la .claude/backlog/ | head -20
   ```
   Expected: 332 .md files with naming pattern p0-*, p1-*, p2-*, idea-*, completed-*

2. List current plan directory:
   ```bash
   ls -la plan/ | head -20
   ```
   Expected: 391 files including architect-*.md, feature-context-*.md, P{NNN}-*.yaml, T0-baseline-*.yaml, TN-verification-*.yaml, codebase/ subdirectory

3. Verify inconsistent storage:
   ```bash
   echo "Backlog location: .claude/backlog/"
   echo "Plan location: plan/ (root level)"
   ```
   Observation: Backlog items under .claude/, plan artifacts at project root. Both are development-harness artifacts but stored in different hierarchies.

4. Confirm no .dh/ directory exists:
   ```bash
   ls -d .dh/ 2>&1 || echo "Directory does not exist (expected)"
   ```

All conditions are observably present and verified by prior fact-checking agent.
</div>

### Priority

<div><sub>2026-03-22T12:31:04Z</sub>

**Assessed as P1 (High Priority)**

Justification:

1. **Blocking dependency**: Dependent work (kage-bunshin dispatch orchestration, referenced as #??? in issue classification) expects `.dh/` paths and cannot proceed without this consolidation.

2. **Codebase maturity**: Development-harness is stable enough for organization improvements without technical risk. No active feature development depends on the current scattered layout.

3. **Scope clarity**: Unlike speculative refactoring, this consolidation is bounded — exactly 4 directories (backlog, plan, context, reports) with known reference patterns (601 files involved, 138 + 463 direct references).

4. **Technical debt precedent**: The inconsistency was established at different times (backlog in 2026-02-27, plan at project inception) without architect decision to consolidate. Fixing it now establishes a clean precedent for future development-harness artifacts.

5. **Not urgent**: The systems work correctly independently. P1 reflects importance to dependent work and architectural cleanliness, not operational failure or breakage.

Risk of deferral: Kage-bunshin work blocked; dependency chain grows longer; more code accumulates expecting scattered paths, making future consolidation more expensive.
</div>

### Scope

<div><sub>2026-03-22T12:31:27Z</sub>
<details><summary>struck: 2026-03-22T13:01:13Z — Scope revised per user design decisions 2026-03-22 — three-tier architecture</summary>

**In Scope** (confirmed by prior analysis):

- Move `.claude/backlog/*.md` to `.dh/backlog/`
- Move `plan/` contents to `.dh/plan/`
- Update all Python code in backlog_core/, sam_core/, artifact provider
- Update all hook scripts (task_status_hook.py, get_task_context.py, etc.)
- Update all SKILL.md and agent description files
- Update .gitignore patterns
- Update all test fixtures and test assertions
- Update artifact manifests in GitHub Issues (via artifact_register MCP calls)
- Update static CI workflow files
- Create migration tool to analyze and transform existing files

**Out of Scope** (pending design decision):

- `.claude/context/` directory (currently proposed for inclusion as `.dh/context/` but not confirmed)
- `.claude/reports/` directory (currently proposed for inclusion as `.dh/reports/` but not confirmed)
- `.claude/rules/` and `.claude/decisions/` — remain in `.claude/` as project meta-information
- `.claude/agents/`, `.claude/hooks/` — remain in `.claude/` as project meta-configuration
- Plugin cache paths (`~/.claude/plugins/cache/`) — no changes needed (runtime code is in repo)

**Design Decisions Required Before Implementation**:

1. Scope approval: Are `.claude/context/` and `.claude/reports/` included in consolidation?
2. Target layout confirmation: Approve proposed `.dh/` structure (backlog/, plan/, context/, reports/, dispatch-state.db, settings.json)
3. Migration strategy: Big bang (move all at once) vs incremental with symlinks?
4. Backward compatibility: Should old paths be supported in parallel during transition, or require plugin reinstallation?

**No scope changes to other directories**: Only development-harness artifacts move. All other project meta-information remains in `.claude/`.
</details>
</div>

<div><sub>2026-03-22T13:01:13Z</sub>

**Three-Tier DH State Architecture**

Tier 1 — Project Config (`.dh/` in repo, committed to git):
- DH settings shared across developers/machines
- Agent and skill overrides
- Project-level DH configuration
- Analogous to `.claude/` for Claude Code config

Tier 2 — Persistent State (`~/.dh/projects/{slug}/`, NOT in git):
- `backlog/` — local read/write cache of GitHub Issues (source of truth: GitHub API)
- `plan/` — task plans, architect specs, feature context (source of truth: GitHub Issue artifacts)
- `milestones/` — milestone data
- `research/` — research artifacts
- Backed by SQLite database, accessed via backlog and SAM MCP servers
- Rebuilt on demand from GitHub backend

Tier 3 — Ephemeral State (`~/.dh/projects/{slug}/`, NOT in git):
- `context/` — active-task session JSON, SAM task cache
- `reports/` — investigation reports
- `dispatch-state.db` — kage-bunshin dispatch state
- No backend sync — host-local only

**Slug format**: Absolute project path with `/` replaced by `-`, leading `-`
Example: `/home/ubuntulinuxqa2/repos/claude_skills` → `-home-ubuntulinuxqa2-repos-claude-skills`

**In scope**:
- Move `.claude/backlog/` → `~/.dh/projects/{slug}/backlog/` (Tier 2)
- Move `plan/` → `~/.dh/projects/{slug}/plan/` (Tier 2)
- Move `.claude/context/` → `~/.dh/projects/{slug}/context/` (Tier 3)
- Move `.claude/reports/` → `~/.dh/projects/{slug}/reports/` (Tier 3)
- Create `.dh/` in-repo for project config (Tier 1)
- SQLite migration for local cache layer behind MCP APIs
- Update all consumers (Python scripts, skills, agents, hooks, docs, CI)
- Update .gitignore (remove old paths, add .dh/ exclusions as needed)

**Out of scope**:
- Other `.claude/` directories (memory, rules, skills) — these are Claude Code config, not DH
- GitHub API changes — existing artifact manifest system continues as-is
- MCP API surface changes — consumers use same MCP tools, backend changes are transparent
</div>

### Output / Evidence

<div><sub>2026-03-22T12:31:37Z</sub>

**Current Documented State** (verified 2026-03-22):

```
.claude/
├── backlog/              (332 .md files: p0-*.md, p1-*.md, p2-*.md, idea-*.md, completed-*.md)
├── context/              (active-task-{session_id}.json files, ephemeral)
├── plan/                 (14 planning/local files: orchestrator-discipline-assessment.md, etc.)
└── reports/              (development-harness generated reports)

plan/                     (391 artifacts at project root)
├── architect-*.md        (architecture specifications)
├── feature-context-*.md  (feature research artifacts)
├── P{NNN}-*.yaml         (task plans, main plan files)
├── P{NNN}-*.md           (legacy markdown task plans)
├── T0-baseline-*.yaml    (acceptance criteria baseline files)
├── TN-verification-*.yaml (verification gate result files)
└── codebase/             (subdirectory with codebase analysis .md files)
```

**Evidence of Consolidated Nature**:
- All backlog items (332 files) created/maintained by backlog MCP server in plugins/development-harness/
- All plan artifacts (391 files) created/maintained by SAM MCP server in plugins/development-harness/
- All context files generated by task_status_hook.py (development-harness)
- All reports generated by doc-drift-auditor and service-docs-maintainer agents (development-harness)
- Conclusion: These are exclusively development-harness artifacts with no cross-plugin consumers

**File Reference Inventory** (from Impact Radius analysis):
- 138 files reference `.claude/backlog/` paths
- 463 files reference `plan/` paths
- 50+ test files hardcoded with path assertions
- 25+ documentation files with path descriptions
- 3–4 configuration files with glob patterns

**No .dh/ directory currently exists** — consolidation requires creation and population.

After migration, observable evidence of success:
- `.dh/backlog/*.md` contains all 332 backlog items
- `.dh/plan/` contains all 391 plan artifacts
- All Python paths point to `.dh/` locations
- All tests pass with updated path assertions
- .gitignore patterns match `.dh/` instead of old paths
- No remaining references to `plan/` or `.claude/backlog/` in active code (documentation may contain historical examples)
</div>

### Dependencies

<div><sub>2026-03-22T12:31:48Z</sub>
<details><summary>struck: 2026-03-22T13:02:02Z — Dependencies updated — all design decisions resolved, no blockers remain</summary>

**This Item Blocks**:

- Kage-bunshin dispatch orchestration work (referenced as #??? in issue) — expects `.dh/dispatch-state.db` storage location
- Any future development-harness artifact work — will assume `.dh/` convention once established
- Plugin marketplace installs — if installed plugins hardcode old paths, they will fail after migration

**This Item Is Blocked By**:

1. **Design Decision: Target Directory Layout** — approval of proposed structure
   - Current proposal: `.dh/backlog/`, `.dh/plan/`, `.dh/context/`, `.dh/reports/`, `.dh/dispatch-state.db`
   - Required action: User review and approval

2. **Design Decision: Scope Confirmation** — whether `.claude/context/` and `.claude/reports/` are included
   - Current proposal: Both included in `.dh/`
   - Required action: User confirmation of scope boundaries

3. **Design Decision: Migration Strategy** — big bang vs incremental with symlinks
   - Current proposal: Big bang (move all files at once)
   - Required action: User approval of migration approach
   - Rationale: Symlinks during transition create complexity, dual-path code, and recovery challenges

4. **Design Decision: Backward Compatibility** — plugin version support
   - Current options: (A) Support old paths in parallel during transition, (B) Require plugin reinstallation
   - Required action: User decision on backward compatibility policy

**Prerequisite Work** (can be done in parallel):

- Path constant extraction — consolidate hardcoded paths into DH_ROOT constant (recommended approach)
- Test framework updates — prepare test infrastructure for path parameterization
- Documentation audit — identify all files that will need updating

**Runtime Code Dependencies** (no external blockers):
- backlog MCP server (ready)
- SAM MCP server (ready)
- Hook scripts (ready)
- All code is in repo and can be updated immediately
</details>
</div>

<div><sub>2026-03-22T13:02:02Z</sub>

**This Item Blocks**:
- Kage-bunshin dispatch orchestration — expects shared state outside worktrees
- Any future multi-session/multi-worktree work — currently blocked by git conflicts on shared state files
- SQLite-backed MCP tools — this item establishes the DB location and schema

**This Item Is Blocked By**:
- Nothing — all design decisions resolved (2026-03-22)

**Prerequisite Work** (can be done as early tasks in the plan):
- Path constant module — centralize `DH_PROJECT_ROOT` and `DH_STATE_ROOT` computation
- SQLite schema design — tables for backlog items, SAM tasks, artifacts, milestones
- Slug computation utility — project path → slug function (shared by backlog + SAM MCP servers)

**Runtime Dependencies**:
- backlog MCP server (will be modified — new backend)
- SAM MCP server (will be modified — new backend)
- Hook scripts (will be modified — new context path)
- GitHub API (unchanged — remains source of truth for persistent state)
</div>

### Research

<div><sub>2026-03-22T12:31:57Z</sub>

**Questions Requiring Investigation During Design Phase**:

1. **Are there existing symlinks or hardlinks in current paths that migration tool must detect?**
   - Run: `find .claude/backlog/ plan/ -type l -o -type h`
   - Impact: May affect clean migration, could create loops

2. **Do any .gitignore patterns exclude subdirectories within plan/ or .claude/backlog/?**
   - Run: `grep -A5 -B5 'plan\|backlog\|context\|reports' .gitignore`
   - Impact: Affects .gitignore update logic

3. **Are there pre-commit hook configurations that reference these directories?**
   - Check: `.pre-commit-config.yaml` for exclude patterns
   - Impact: CI must be updated to match new paths

4. **How many GitHub Issues currently have artifact manifests with plan/ references?**
   - Requires: API iteration to count issues with artifact_register comments
   - Impact: Drives migration tool complexity for manifest updates

5. **Which installed plugin versions expect .claude/backlog/ or plan/ paths?**
   - Check: plugin.json versions in ~/.claude/plugins/cache/
   - Impact: Determines backward compatibility requirements

6. **Are there any CI workflows that upload artifacts from plan/ or .claude/backlog/?**
   - Search: `.github/workflows/*.yml` for artifact paths
   - Impact: Affects CI workflow updates

7. **Do any shell scripts or makefiles reference these paths?**
   - Run: `grep -r 'plan/\|\.claude/backlog\|\.claude/context\|\.claude/reports' . --include='*.sh' --include='Makefile'`
   - Impact: May need additional script updates

8. **What is the GitHub Actions artifact upload size for .claude/backlog/?**
   - Run: `du -sh .claude/backlog/ plan/ .claude/context/ .claude/reports/`
   - Impact: Affects migration timing (large directories may timeout)
</div>

### Skills

<div><sub>2026-03-22T12:32:07Z</sub>

**Claude Code Skills Relevant for Implementation**:

1. `/plugin-creator:contextual-ai-documentation-optimizer` — for updating SKILL.md and agent description files
   - Used for: Rewriting artifact output paths in skill frontmatter and agent docs
   - Critical for: Ensuring agent instructions correctly describe new `.dh/` paths

2. `/plugin-creator:skill-creator` or `/plugin-creator:subagent-refactorer` — for modifying skills if workflow needs changes
   - Used for: Updating implementation-manager skill if artifact output paths change
   - May not be needed if MCP servers handle path changes transparently

3. `/python3-development:python-cli-architect` — for migration tool design and implementation
   - Used for: Writing tool to analyze paths, move files, update references
   - Critical for: Ensuring migration is robust and reversible

4. `/python3-development:python-pytest-architect` — for test updates
   - Used for: Updating test fixtures, path assertions, test data generators
   - Scope: 50+ test files in development-harness plugin

5. `/dh:create-backlog-item` — for tracking follow-up work
   - Used for: Creating backlog items for CI workflow updates, doc updates if needed
   - Not critical path but supports visibility

6. `python3-development:python-code-reviewer` — for code review after path consolidation
   - Used for: Verifying all path references are updated correctly
   - Scope: All backlog_core, sam_core, artifact provider, hook scripts

**Plugin Skills Not Needed** (documentation updates handled separately):
- Markup/documentation optimizers not needed — documentation updates are textual corrections, not optimization work

**MCP Servers (Not Skills) Used During Execution**:
- backlog MCP server — will need code updates for path changes
- SAM MCP server — will need code updates for path changes
- artifact_register MCP tool — will need to be called to update GitHub manifests after migration
</div>

### Agents

<div><sub>2026-03-22T12:32:17Z</sub>

**Implementation Agents Required** (from python3-development and development-harness plugins):

1. **@python3-development:python-cli-architect** — PRIMARY for migration tool
   - Task: Design and implement migration tool that:
     * Analyzes existing file paths in all 601 affected files
     * Detects path patterns without assuming from docs
     * Moves files from old to new locations
     * Updates internal path references in all producer/consumer code
     * Updates test fixtures and assertions
     * Calls artifact_register for GitHub manifest updates
     * Provides rollback capability
   - Output: migration_tool.py + test suite

2. **@python3-development:python-pytest-architect** — for test updates
   - Task: Update all test fixtures in plugins/development-harness/tests_*/:
     * Update hardcoded path assertions to use .dh/ paths
     * Update test data generators
     * Update fixture YAML files
   - Scope: 50+ test files
   - Output: Updated test files + passing test suite

3. **@plugin-creator:contextual-ai-documentation-optimizer** — for AI-facing content
   - Task: Update SKILL.md and agent description files:
     * Update artifact output paths documented in skill frontmatter
     * Update artifact creation paths in agent descriptions
     * Update path expectations in agent instructions
   - Scope: 20+ skill/agent files
   - Output: Updated SKILL.md and agent .md files

4. **@python3-development:python-code-reviewer** — for code verification
   - Task: Review all changes post-migration:
     * Verify all hardcoded path references are updated
     * Verify no dangling references to old paths
     * Verify test suite passes
   - Scope: backlog_core/, sam_core/, artifact provider, hooks
   - Output: Review findings + pass/fail verification

**Supporting Agents** (may be needed conditionally):

5. Backlog MCP server maintenance — if path constants need extraction to single location
   - Task: Add DH_ROOT = ".dh" constant, update all path builders to use it
   - Optional: Could be part of python-cli-architect's migration tool work

6. CI workflow updates — if manual verification of .github/workflows/*.yml is needed
   - Task: Update artifact paths in GitHub Actions workflows
   - Scope: backlog-sync.yml, code-quality.yml
   - Manual action if not parameterized by migration tool

**Agent Coordination Pattern**:
- Migration tool (python-cli-architect) produces changes and runs tests
- Test architect updates failing tests to match new paths
- Doc optimizer updates SKILL.md and agent descriptions
- Code reviewer verifies all changes are correct and safe
- Final verification: All tests pass, no old paths in active code
</div>

### Prior Work

<div><sub>2026-03-22T12:32:28Z</sub>

**Related Consolidation and Migration Efforts** (from project history):

1. **Backlog MCP Migration (2026-02-27)** — Prior attempt to consolidate backlog under one system
   - What was done: Migrated backlog items to `.claude/backlog/` with MCP server
   - Outcome: Successful MCP implementation, but plan artifacts were not addressed
   - Reference: `plugins/development-harness/skills/backlog/CLI_TO_MCP_MIGRATION.md`
   - Lesson: Piecemeal migration created the inconsistency this item now addresses

2. **GitHub Issue Artifact Manifest System (2026-03-22)** — Artifact registry infrastructure
   - What was done: artifact_register MCP tool, artifact_provider module, manifest sections in issue bodies
   - Outcome: Plan artifacts now registered with GitHub Issues as source of truth
   - Reference: `plugins/development-harness/docs/artifact-manifest-*.md`
   - Implication: Migration tool must use artifact_register to update existing manifests

3. **Plan File Format Migrations** (historical)
   - Legacy markdown task files (`plan/tasks-*.md`) coexist with YAML format (`plan/P{NNN}-*.yaml`)
   - Tools: `rename_plan_files.py`, `split_task_file.py`, `migrate_task_format.py` (in plugins/)
   - Lesson: Path migration can be combined with format migration if needed
   - Caution: These historical migrations show migration tools themselves need testing

4. **Hook System Development (2026-03-22)** — Context file infrastructure
   - What was done: task_status_hook.py, SubagentStop/PostToolUse hooks
   - Current behavior: Writes to `.claude/context/active-task-{session_id}.json`
   - Impact: Migration must update context file write paths in hook scripts
   - Reference: `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py`

**Lessons from Prior Migrations**:
- **Piecemeal updates leave inconsistencies** — This item exists because backlog and plan were not consolidated together
- **Tools outlive their purpose** — rename_plan_files.py and migrate_task_format.py still exist; consolidation tool may need similar longevity
- **Test fixtures get stale** — Prior migrations did not systematically update all test files; this item must do comprehensive test updates
- **Documentation drifts** — CLI_TO_MCP_MIGRATION.md is now historical; post-migration docs must be updated carefully
- **GitHub integrations require API awareness** — artifact_register is a good precedent for API-aware migrations

**No Previous Consolidation Attempt** — This is the first attempt to consolidate backlog and plan under a single namespace.
</div>

### Files

<div><sub>2026-03-22T12:32:41Z</sub>

**Key Files That Will Be Modified** (not exhaustive, organized by category):

**Python Code — Path Changes Required** (12–15 files):
- `plugins/development-harness/backlog_core/server.py` — MCP server initialization, directory setup
- `plugins/development-harness/backlog_core/operations.py` — file write operations, CRUD paths
- `plugins/development-harness/backlog_core/parsing.py` — glob patterns for backlog discovery
- `plugins/development-harness/backlog_core/artifact_provider.py` — artifact path construction
- `plugins/development-harness/sam_core/server.py` — SAM MCP initialization
- `plugins/development-harness/sam_core/operations.py` — plan file discovery and read
- `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — context file paths, task file I/O
- `plugins/development-harness/skills/implementation-manager/scripts/get_task_context.py` — context file read paths
- `scripts/rename_plan_files.py` — utility for plan file operations
- Any other scripts in `plugins/development-harness/` or `scripts/` using hardcoded paths

**Configuration Files** (3–4 files):
- `.gitignore` — update glob patterns for plan/, .claude/backlog/, .claude/context/, .claude/reports/
- `.pre-commit-config.yaml` — update directory exclusion patterns if present
- `.github/workflows/backlog-sync.yml` — artifact upload paths
- `.github/workflows/code-quality.yml` — linting exclusion patterns if present

**Test Files** (50+ files):
- `plugins/development-harness/tests_sam/fixtures/*.yaml` — path references in test data
- `plugins/development-harness/tests_backlog/test_*.py` — path assertions (20+ references)
- `plugins/development-harness/tests_sam/test_*.py` — SAM CLI and path tests
- `plugins/python3-development/skills/implementation-manager/tests/test_task_status_hook/*.py` — hook script tests

**Documentation Files** (25–30 files):
- `.claude/rules/local-workflow.md` — comprehensive path documentation
- `.claude/CLAUDE.md` — path references throughout
- `plugins/development-harness/CLAUDE.md` — plugin development paths
- `plugins/development-harness/docs/plan-artifact-lifecycle.md` — artifact storage path docs
- `plugins/development-harness/docs/workflow-architecture-diagram.md` — diagram references paths
- `plugins/development-harness/docs/TASK_FILE_FORMAT.md` — artifact naming conventions
- `plugins/development-harness/skills/backlog/references/item-schema.md` — item location docs
- `plugins/development-harness/skills/*/SKILL.md` (20+ files) — agent instruction files

**Skill and Agent Files** (20+ files):
- `plugins/development-harness/skills/add-new-feature/SKILL.md` — instructs agents to create plan/ artifacts
- `plugins/development-harness/skills/implement-feature/SKILL.md` — assumes plan/ paths
- `plugins/development-harness/skills/start-task/SKILL.md` — context file path documentation
- `plugins/development-harness/skills/complete-implementation/SKILL.md` — artifact output paths
- `plugins/development-harness/agents/*.md` (15+ agent files) — artifact creation paths described

**GitHub Issues** (Unknown number, requires API iteration):
- All open issues with artifact manifest sections containing plan/ paths — requires artifact_register updates

**Files NOT Modified** (remain in .claude/):
- `.claude/rules/`, `.claude/decisions/`, `.claude/agents/`, `.claude/hooks/` — project meta-information stays in place
- `.claude/CLAUDE.md` — remains but paths are updated
</div>

### Resources

<div><sub>2026-03-22T12:32:52Z</sub>

**External References and Documentation**:

1. **Project Documentation on Current Paths**:
   - `.claude/rules/local-workflow.md` — comprehensive workflow documentation with current paths
   - `plugins/development-harness/docs/plan-artifact-lifecycle.md` — plan artifact storage and lifecycle
   - `plugins/development-harness/docs/workflow-architecture-diagram.md` — data flow diagram with path references

2. **MCP Server and Tool Documentation**:
   - `plugins/development-harness/backlog_core/` — backlog MCP server implementation
   - `plugins/development-harness/sam_core/` — SAM MCP server implementation
   - `plugins/development-harness/backlog_core/artifact_provider.py` — artifact manifest registration logic

3. **Migration Tool Precedents**:
   - `plugins/development-harness/skills/backlog/CLI_TO_MCP_MIGRATION.md` — historical migration guide, shows API patterns
   - `plugins/python3-development/scripts/split_task_file.py` — example path-aware file transformation
   - `plugins/python3-development/scripts/migrate_task_format.py` — example format migration (can be combined with path migration)

4. **Hook and Script References**:
   - `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` — context file I/O patterns
   - `plugins/development-harness/skills/implementation-manager/scripts/get_task_context.py` — context file access patterns

5. **Test Infrastructure**:
   - `plugins/development-harness/tests_sam/fixtures/` — test data directory with YAML fixtures
   - `plugins/development-harness/tests_backlog/` — backlog test suite structure

6. **GitHub Integration**:
   - GitHub Issues API for artifact manifest updates (requires GITHUB_TOKEN)
   - `artifact_register` MCP tool for updating manifests after migration
   - PyGithub library for issue body manipulation (if custom script needed)

7. **Linting and CI Configuration**:
   - `.github/workflows/code-quality.yml` — linting pipeline that must be updated
   - `.pre-commit-config.yaml` — hook configuration (may exclude directories)
   - `pyproject.toml` — project configuration, test runners, linting tools

**No External Tools Required** — All migration can be done with:
- Python standard library (os, pathlib, shutil, re)
- PyYAML for YAML fixture updates
- PyGithub or backlog MCP for GitHub manifest updates
- Pre-existing test frameworks (pytest)

**Validation Resources**:
- Test suites in `plugins/development-harness/tests_*` — can be used to verify migration
- Pre-commit hooks — can be run after migration to catch linting issues
- GitHub Actions workflows — can be verified after migration to ensure CI still works
</div>

### Effort

<div><sub>2026-03-22T12:33:07Z</sub>
<details><summary>struck: 2026-03-22T13:01:44Z — Effort revised to XL reflecting SQLite migration and three-tier architecture</summary>

**Estimate: Large (3–4 weeks full-time, parallelizable to 1.5–2 weeks with agents)**

Justification by component:

**1. Migration Tool Design and Development: Medium (4–5 days)**
- Analyze all 601 affected files for path patterns — 1 day
- Design path transformation strategy (find-and-replace vs AST-based) — 0.5 day
- Implement file moving and reference updating — 2 days
- Implement GitHub artifact manifest updates via artifact_register — 1 day
- Add rollback capability — 0.5 day
- Test on small subset (10 backlog items, 5 plan files) — 1 day

**2. Python Code Updates: Medium (3–4 days)**
- backlog_core/ path changes (server, operations, parsing) — 1 day
- sam_core/ path changes (server, operations) — 1 day
- artifact_provider and hook scripts — 1 day
- Path constant extraction (optional optimization) — 0.5 day
- Testing and verification — 0.5 day

**3. Test Updates: Large (4–5 days)**
- Identify all hardcoded path assertions and fixtures — 1 day
- Update 50+ test files with new paths — 2 days
- Update test data generators and YAML fixtures — 1 day
- Run full test suite and fix failures — 1 day

**4. Documentation Updates: Medium (3–4 days)**
- Update .claude/rules/local-workflow.md (comprehensive) — 1 day
- Update CLAUDE.md files (project + plugin) — 0.5 day
- Update plugin docs (artifact lifecycle, workflow diagram) — 0.5 day
- Update SKILL.md and agent description files (20+ files) — 1 day
- Update documentation-only files (TASK_FILE_FORMAT.md, schema docs) — 0.5 day

**5. Configuration and CI: Small (1–2 days)**
- Update .gitignore patterns — 0.25 day
- Update .pre-commit-config.yaml if needed — 0.25 day
- Update GitHub Actions workflows — 0.5 day
- Test CI workflow execution — 0.5 day

**6. Integration and Verification: Medium (2–3 days)**
- Run full migration on production files — 1 day
- Verify all tests pass — 0.5 day
- Code review of all changes — 0.5 day
- Final spot-checks for lingering old paths — 0.5 day

**Total Work: 17–23 days of effort**

**Parallelization Strategy** (with 3–4 agents, can compress to 1.5–2 weeks):
- Migration tool development (python-cli-architect) — parallel with test prep
- Python code updates (python-cli-architect or python-code-reviewer) — can start once tool design done
- Test updates (python-pytest-architect) — can start immediately, update as code changes
- Documentation updates (contextual-ai-documentation-optimizer) — can start immediately, review-blocking only at end
- Code review (python-code-reviewer) — final phase after all changes

**Risk Factors Increasing Effort**:
- GitHub API rate limiting (artifact manifest updates) — may require retry logic
- Circular path references in test data — may require iterative fixing
- Symlinks or hardlinks in current directories — would require special handling
- Plugin cache conflicts — if installed plugins expect old paths

**Risk Factors Decreasing Effort**:
- Well-defined scope (exactly 4 directories, no scope creep)
- Clear path patterns (all hardcoded strings, no environment variables)
- Comprehensive prior analysis (Impact Radius already mapped all consumers)
- Good test coverage (50+ test files provide validation harness)

**Estimate Type**: Medium-High confidence, based on:
- Prior migration work (backlog MCP, task format migrations) provides precedent
- Impact Radius analysis has already mapped all dependencies
- Path patterns are simple (no nested substitutions, environment-based paths)
- No architectural unknowns remain
</details>
</div>

<div><sub>2026-03-22T13:01:44Z</sub>

**XL** — this is a foundational architecture change, not a directory rename.

Three major work streams:
1. **SQLite backend** — new database schema, migration of flat-file operations to DB queries, transaction safety for concurrent access
2. **Path resolution refactor** — extract all hardcoded paths into centralized constants, update 50+ Python files, 25+ doc files, CI workflows
3. **Three-tier directory setup** — `.dh/` in-repo config, `~/.dh/projects/{slug}/` runtime state, slug computation, auto-creation on first use

Parallelizable: streams 1 and 2 can run concurrently after the path constant module is defined. Stream 3 is foundational and runs first.

Risk: high blast radius (600+ file references), but consumers are behind MCP APIs — most path changes are internal to the MCP servers.
</div>

### Acceptance Criteria

<div><sub>2026-03-22T12:33:23Z</sub>
<details><summary>struck: 2026-03-22T13:01:31Z — Acceptance criteria revised to match three-tier architecture design</summary>

**Specific, Testable Completion Criteria**:

**Directory Structure**:
- [ ] Directory `.dh/` exists at project root
- [ ] Directory `.dh/backlog/` contains exactly 332 .md files (matching count from `.claude/backlog/`)
- [ ] Directory `.dh/plan/` contains exactly 391 files (matching count from old `plan/`)
- [ ] Directory `.dh/context/` exists and is ready for active-task context files
- [ ] Directory `.dh/reports/` exists and is ready for generated reports
- [ ] Old directories `.claude/backlog/`, `.claude/context/`, `.claude/reports/`, `plan/` no longer exist (moved, not copied)

**Code Updates**:
- [ ] `plugins/development-harness/backlog_core/server.py` uses `.dh/backlog/` paths (observable: grep `.dh/backlog` server.py)
- [ ] `plugins/development-harness/sam_core/server.py` uses `.dh/plan/` paths (observable: grep `.dh/plan` sam_core/server.py)
- [ ] `plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py` writes to `.dh/context/` (observable: grep `.dh/context` task_status_hook.py)
- [ ] `get_task_context.py` reads from `.dh/context/` (observable: grep `.dh/context` get_task_context.py)
- [ ] artifact_provider.py constructs paths using `.dh/plan/` (observable: grep `.dh/plan` artifact_provider.py)
- [ ] No grep results for `plan/` or `.claude/backlog` in Python code (excluding tests and docs)
- [ ] All Python code linting passes: `uv run ruff check plugins/development-harness/`

**Test Suite**:
- [ ] All test files in `plugins/development-harness/tests_*` pass: `uv run pytest plugins/development-harness/tests_*/`
- [ ] No test failures due to hardcoded path references
- [ ] Test fixtures in `plugins/development-harness/tests_sam/fixtures/*.yaml` reference `.dh/plan/` (observable: grep `.dh/plan` fixtures/)
- [ ] Test assertions on paths updated to use `.dh/` (observable: grep `.dh/` test_*.py | count >= count of plan/ references in old tests)

**Configuration Files**:
- [ ] `.gitignore` patterns exclude `.dh/backlog/`, `.dh/plan/`, `.dh/context/`, `.dh/reports/` (observable: grep `.dh/` .gitignore)
- [ ] `.gitignore` no longer excludes `plan/`, `.claude/backlog/`, `.claude/context/`, `.claude/reports/` (observable: grep should not match)
- [ ] `.pre-commit-config.yaml` updated if it excluded old directories (observable: verify no stale patterns)
- [ ] `.github/workflows/backlog-sync.yml` uses `.dh/backlog/` paths if it references artifact paths
- [ ] `.github/workflows/code-quality.yml` uses `.dh/` paths if it excludes directories

**Documentation**:
- [ ] `.claude/rules/local-workflow.md` references `.dh/` paths (observable: grep `.dh/backlog`, `.dh/plan`, no old paths)
- [ ] `.claude/CLAUDE.md` path references updated to `.dh/` (observable: grep `.dh/`, no old plan/ or .claude/backlog/)
- [ ] `plugins/development-harness/docs/plan-artifact-lifecycle.md` references `.dh/plan/` (observable: grep `.dh/plan`)
- [ ] `plugins/development-harness/skills/add-new-feature/SKILL.md` documents plan artifacts at `.dh/plan/` location
- [ ] `plugins/development-harness/agents/*.md` describe artifact output at `.dh/` paths
- [ ] No trailing "old path" examples in documentation (grep for `plan/` in docs should find zero references outside historical sections)

**GitHub Integration**:
- [ ] Artifact manifest entries in open GitHub Issues updated to `.dh/plan/` paths
- [ ] artifact_register calls use `.dh/plan/` for all new artifact registrations (observable post-migration)
- [ ] No issues with artifact_read failures due to path mismatches

**Migration Tool**:
- [ ] Migration tool script exists and is documented
- [ ] Tool successfully moves all 723 files (332 backlog + 391 plan) without data loss
- [ ] Tool updates all internal path references in backlog item YAML frontmatter if any exist
- [ ] Tool provides rollback instructions or capability
- [ ] Tool exit code is 0 on success

**Final Verification**:
- [ ] Full test suite passes: `uv run pytest plugins/development-harness/`
- [ ] All linting passes: `uv run ruff check . && uv run mypy plugins/`
- [ ] No git diff shows remaining references to `plan/` or `.claude/backlog/` in active code
- [ ] MCP servers (backlog and SAM) start successfully and serve requests from `.dh/` paths
- [ ] Fresh backlog item can be created and is written to `.dh/backlog/`
- [ ] Fresh task plan can be created and is written to `.dh/plan/`
- [ ] All 14 conditions from RT-ICA "AVAILABLE" state remain valid post-migration
</details>
</div>

<div><sub>2026-03-22T13:01:31Z</sub>

**Tier 1 — In-Repo Config (.dh/)**:
- [ ] `.dh/` directory exists in repo root with project DH config
- [ ] Settings, agent/skill overrides stored and committed
- [ ] `.dh/` is documented in CLAUDE.md / CONTRIBUTING.md

**Tier 2 — Persistent State (~/.dh/projects/{slug}/)**:
- [ ] `~/.dh/projects/{slug}/` created automatically on first MCP tool call
- [ ] Slug computed correctly from project absolute path (/ → -, leading -)
- [ ] `backlog/` cache populated from GitHub Issues via backlog MCP
- [ ] `plan/` artifacts cached locally, backed by GitHub Issue artifact manifests
- [ ] SQLite database stores structured data (backlog items, SAM tasks, milestones)
- [ ] MCP API surface unchanged — consumers call same tools, backend is transparent
- [ ] `backlog_sync` / `backlog_pull` rebuild cache from GitHub backend
- [ ] Concurrent worktree access works without conflicts (kage-bunshin safe)

**Tier 3 — Ephemeral State (~/.dh/projects/{slug}/)**:
- [ ] `context/` stores active-task session JSON (no backend sync)
- [ ] `reports/` stores investigation reports (no backend sync)
- [ ] Ephemeral files cleaned up by existing hook lifecycle

**Migration**:
- [ ] All Python scripts updated — no hardcoded `.claude/backlog/` or `plan/` paths remain
- [ ] All SKILL.md files updated — no references to old paths
- [ ] All agent .md files updated — no references to old paths
- [ ] All rules files updated — no references to old paths
- [ ] CLAUDE.md updated with new directory conventions
- [ ] .gitignore updated (remove old exclusions, add new as needed)
- [ ] CI workflows updated (.github/workflows/)
- [ ] Old directories removed from repo after migration verified
- [ ] Tests pass with new path structure

**Verification**:
- [ ] `grep -r '.claude/backlog' --include='*.py' --include='*.md' --include='*.yml'` returns zero results (excluding migration tool itself)
- [ ] `grep -r 'plan/' --include='*.py'` shows no hardcoded plan/ path references
- [ ] MCP tools (backlog_list, sam_status, etc.) work with new backend
- [ ] Parallel sessions (kage-bunshin) can read/write shared state without corruption
</div>

### Architecture Decision — In-Repo vs User-Level

<div><sub>2026-03-22T13:12:27Z</sub>
<details><summary>struck: 2026-03-22T13:14:16Z — Contradiction resolved — user confirmed Option B (user-level ~/.dh/ for runtime/cached data, in-repo .dh/ for shared config only)</summary>

**CONTRADICTION IDENTIFIED (2026-03-22 alignment review)**

The issue description and "Suggested target layout" describe moving backlog/, plan/, context/, reports/ into in-repo `.dh/`. But the Acceptance Criteria (Tier 2/3) move those same directories to `~/.dh/projects/{slug}/` outside git. These are fundamentally different architectures:

- **Option A** (matches description): In-repo `.dh/backlog/`, `.dh/plan/`, `.dh/context/`, `.dh/reports/` — a directory rename. Git-tracked. Each worktree gets its own copy.
- **Option B** (matches AC Tier 2/3): User-level `~/.dh/projects/{slug}/` — outside git, shared across worktrees, backed by SQLite for structured data.

**These cannot both be correct.** The "Suggested target layout" showing dispatch-state.db inside in-repo `.dh/` is also wrong — a SQLite DB used across worktrees cannot be in-repo (git conflicts, not visible from other worktrees).

**Resolution required before planning**: Which architecture is intended? The answer determines whether this is a directory rename (Option A — small scope) or a backend replacement (Option B — large scope with SQLite migration).

**Related**: #986 already uses `~/.dh/projects/{slug}/dispatch-state.db` for dispatch runtime state. That decision is independent of this item regardless of which option is chosen here.

**Also contradictory**: The Dependencies section claims "all design decisions resolved (2026-03-22)" but the Outstanding Questions section lists 5 open items. Either the questions were resolved (update the Outstanding Questions section) or they were not (correct the Dependencies claim).

SOURCE: plan/alignment-review-981-vs-986.md (alignment review agent, 2026-03-22)
</details>
</div>

<div><sub>2026-03-22T13:14:16Z</sub>

**RESOLVED (2026-03-22 — user decision)**

Two namespaces, clear separation by purpose:

- **In-repo `.dh/`** — committed, shared across developers via git. Contains only settings and project-level configuration that should be version-controlled. Analogous to how `.claude/settings.json` is committed and shared today. If no shared settings exist yet, this directory starts empty or is created when needed.
- **User-level `~/.dh/projects/{slug}/`** — per-user, outside git. Contains runtime state (dispatch-state.db), cached artifacts (backlog file cache), plan working copies, context files, reports, and any other ephemeral or user-specific data. Not shared, not committed.

This means #981 is **Option B**: backlog cache, plan artifacts, context, and reports move OUT of the repo to `~/.dh/projects/{slug}/`. The in-repo `.dh/` directory is reserved for committed shared config only.

The "Suggested target layout" in the original issue description showing `backlog/`, `plan/`, `context/`, `reports/` under in-repo `.dh/` is **superseded** by this decision. Those directories belong in `~/.dh/projects/{slug}/`.

`{project-stub}` derivation: absolute repo root path with `/` replaced by `-` (Claude Code convention).

SOURCE: User decision, session 2026-03-22
</div>

### Naming Convention

<div><sub>2026-03-22T13:12:41Z</sub>

**Two namespaces exist simultaneously — document this clearly in all implementation artifacts:**

- In-repo `.dh/` = committed config/settings only (Tier 1 in AC)
- User-level `~/.dh/` = runtime state, cached artifacts, SQLite databases (Tier 2/3 in AC)

A developer reading the issue title "under .dh/" would assume in-repo. The AC reveal both namespaces. The distinction must be unambiguous in the description, any resulting design doc, and CLAUDE.md updates.

`{project-stub}` derivation follows Claude Code convention: absolute repo root path with `/` replaced by `-` (e.g., `/home/user/repos/claude_skills` → `-home-user-repos-claude_skills`). This is the same convention used by #986 for dispatch-state.db.

SOURCE: plan/alignment-review-981-vs-986.md
</div>

### Sequencing with #986

<div><sub>2026-03-22T13:12:52Z</sub>

**#986 implements first, #981 second.**

#986 (dispatch orchestration MCP tools) adds four new tools to server.py using current `plan/` paths. #981 migrates `plan/` to a new location. Both touch server.py — parallel branches will merge-conflict.

When #981 implements, its migration sweep must include updating any path constants that #986 introduced (dispatch_read references to `plan/milestone-{N}-dispatch.yaml`).

#986 has no dependency on #981 and can proceed now.

SOURCE: plan/alignment-review-981-vs-986.md
</div>

### Outstanding Questions Resolution

<div><sub>2026-03-22T13:17:58Z</sub>

**All 5 outstanding questions from RT-ICA are now RESOLVED (2026-03-22).**

**Q1 — Target directory layout**: RESOLVED. Superseded by two-namespace architecture decision. In-repo `.dh/` for committed config; `~/.dh/projects/{slug}/` for runtime state. None of the original Options A/B/C apply. See "Architecture Decision" section.

**Q2 — Scope of context/ and reports/**: RESOLVED. Both in scope, moving to `~/.dh/projects/{slug}/context/` and `~/.dh/projects/{slug}/reports/` (Tier 3 in AC).

**Q3 — Migration strategy**: RESOLVED. Big bang recommended — avoid symlink complexity. Prototype on small subset (10 backlog items, 5 plan files) before migrating all 600+ files.

**Q4 — Plugin cache interaction**: RESOLVED (derivable). Plugin cache (`~/.claude/plugins/cache/`) and DH state (`~/.dh/projects/{slug}/`) are separate namespaces with no overlap. Plugin cache is Claude Code infrastructure, not DH state.

**Q5 — Backward compatibility**: RESOLVED. Grep of `~/.claude/plugins/cache/` found 30 files referencing `.claude/backlog` or `plan/` paths. Breakdown: 26 are SKILL.md and reference documentation (describe paths to Claude, not runtime file access). 4 are Python runtime code (`dispatch_schema/paths.py`, `readers/yaml_reader.py`, `writers/yaml_writer.py`, `core/models.py`) — all run INSIDE the MCP server process. No external consumer reads `.claude/backlog/` or `plan/` directly — all access goes through backlog MCP and SAM MCP tools. When paths change, update the MCP server internals and the documentation references in the next plugin version. No backward compatibility shim is needed.

The "Dependencies" section claim "all design decisions resolved" is now accurate. The "Outstanding Questions" section in the original RT-ICA can be marked resolved.
</div>


## Classification

**Type**: `unbounded-design` — system consolidation and organizational refactoring

---

## Reasoning

This issue does not fit the other categories:

- **NOT procedural** — Not a process or workflow improvement. The workflow is working correctly; the problem is the organizational structure.
- **NOT recurring-pattern** — Not a problem that keeps happening. The structure was established once (backlog in 2026-02-27, plan/ at project inception) and remains that way.
- **NOT defect** — Nothing is broken. Both systems function independently and correctly.
- **NOT missing-guardrail** — All appropriate constraints exist (backlog is immutable per MCP, plan paths are well-documented). The constraint is what should change.

---

## Root Cause Analysis (5-Whys)

**Why is the structure inconsistent?**
1. Backlog items were migrated to `.claude/backlog/` in 2026-02-27 following the user's Claude Code config convention.
2. Plan artifacts (architect specs, task files, T0/TN verification) were placed at project root as `plan/` decades earlier, before development-harness consolidation was planned.
3. No architect decision was made at the time of backlog migration to consolidate these two artifact families under one namespace.

**Why wasn't consolidation done at migration time?**
1. The backlog MCP server was being built; consolidation would have required re-architecting both the MCP and all consuming skills/agents in parallel.
2. The plan system was stable and working; moving it would have broken all existing references without clear payoff at that moment.

**Why consolidate now?**
1. Dependent work (kage-bunshin dispatch orchestration, #981) is being sequenced and expects `.dh/` paths.
2. The development-harness is mature enough that consolidation is an organizational improvement without technical risk.
3. A dedicated consolidation task allows the migration to be done once, correctly, with full reference scanning and tool support.

**Why call this "unbounded-design" rather than "refactor"?**
1. The scope includes more than moving directories: it defines a new organizational schema for development-harness artifacts (.dh/ hierarchy).
2. It requires design decisions not yet made: target layout, migration strategy (big bang vs. incremental), scope boundaries (is .claude/context/ included?).
3. It establishes a precedent for future development-harness artifact locations.

---

## Current State

- **Backlog**: 332 items in `.claude/backlog/*.md` (local cache, GitHub Issues are source of truth)
- **Plans**: 65+ architect/task files in `plan/` at project root (source of truth)
- **Reports**: `{N}` items in `.claude/reports/` — generated, short-lived
- **Context files**: `.claude/context/active-task-{session_id}.json` — ephemeral, session-scoped
- **Rules/decisions**: `.claude/rules/*.md`, `.claude/decisions/` — meta-documentation
- **No `.dh/` directory exists yet**

---

## Dependency Chain

This issue blocks:
- #??? (kage-bunshin dispatch storage — references `.dh/dispatch-state.db`)
- Future work that assumes `.dh/` as the development-harness root

This issue is blocked by:
- Design decision: What should `.dh/` contain and how should it be organized?
- Design decision: Migration strategy — all-at-once or incremental with symlinks?
- Design decision: Scope — what directories qualify as "development-harness artifacts"?

---

## Observed Patterns Requiring Design Input

1. **Backlog references in 84 plugin files** — many skills and agents expect `.claude/backlog/` location
2. **Plan references in 4 plugin files + TASK_FILE_FORMAT.md** — tools generate `plan/P{N}` and `plan/tasks-*` paths
3. **Hardcoded paths in Python scripts** — `.claude/backlog`, `plan/` appear in script constants and glob patterns
4. **Documentation precedent** — CLAUDE.md and local-workflow.md extensively document both locations
5. **Dependent artifacts** — backlog items link to plan files via `plan: "..."` metadata field

---

## Next Steps

Before implementation:
1. **Design decision**: Propose target `.dh/` layout — suggested structure below for review
2. **Scope decision**: Confirm scope boundaries (reports? context? rules? knowledge? audits?)
3. **Strategy decision**: Approve migration approach (big bang recommended to avoid symlink complexity)

**Suggested target layout** (pending approval):
```
.dh/
├── backlog/              # Backlog per-item files (was .claude/backlog/)
├── plan/                 # Plan artifacts: architects, tasks, T0/TN (was plan/)
├── context/              # Active task context files (was .claude/context/)
├── reports/              # Generated reports (was .claude/reports/)
├── dispatch-state.db     # Dispatch orchestration state (new, for kage-bunshin)
└── settings.json         # Project settings (future, for user config system)
```

All other `.claude/` content (agents, hooks, CLAUDE.md, rules, decisions) stays in `.claude/` as project meta-information rather than development-harness artifacts.

</div>


## Impact Radius Analysis — Consolidate backlog and plan directories under .dh/

### Overview
Consolidating `.claude/backlog/`, `plan/`, `.claude/context/`, and `.claude/reports/` under `.dh/` will require updates across five categories of systems: code producers/consumers, documentation, configuration files, CI workflows, and agent instructions.

---

## Code — Producers (systems that create files in current paths)

| System | File Path | Role | Breaking Risk | Staleness Risk |
|--------|-----------|------|---|---|
| `backlog_core/server.py` | plugins/development-harness/backlog_core/server.py | MCP server for backlog CRUD | HIGH — hardcoded path strings | No — code runs dynamically |
| `backlog_core/operations.py` | plugins/development-harness/backlog_core/operations.py | Backlog write operations | HIGH — file I/O paths | No — code runs dynamically |
| `artifact_provider.py` | plugins/development-harness/backlog_core/artifact_provider.py | GitHub artifact manifest registration | MEDIUM — path concatenation | No — code runs dynamically |
| `sam_create` MCP tool | plugins/development-harness/sam_core/... | SAM task plan file creation | HIGH — hardcoded plan/ prefix | No — code runs dynamically |
| `task_status_hook.py` | plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py | Writes task status, timestamps to plan files | HIGH — active-task context file paths | No — code runs dynamically |
| `get_task_context.py` | plugins/development-harness/skills/implementation-manager/scripts/get_task_context.py | Reads .claude/context/ files at runtime | HIGH — hardcoded context path | No — code runs dynamically |
| `rename_plan_files.py` | scripts/rename_plan_files.py | Utility for plan file migration | HIGH — operates on plan/ | MEDIUM — documents old naming convention |
| Backlog MCP server init | plugins/development-harness/backlog_core/server.py | Initializes backlog directory on startup | HIGH — directory setup | No — code runs dynamically |

---

## Code — Consumers (systems that read from current paths)

| System | File Path | Role | Breaking Risk | Staleness Risk |
|--------|-----------|------|---|---|
| `backlog_core/parsing.py` | plugins/development-harness/backlog_core/parsing.py | Parses .claude/backlog/*.md files | HIGH — path globbing patterns | No — code runs dynamically |
| `sam_status` / `sam_ready` MCP tools | plugins/development-harness/sam_core/... | Queries plan/ directory for task files | HIGH — filesystem discovery | No — code runs dynamically |
| `artifact_provider.py` | plugins/development-harness/backlog_core/artifact_provider.py | Reads artifact files from plan/ | HIGH — path construction | No — code runs dynamically |
| Hook scripts (task_status_hook.py) | plugins/development-harness/skills/implementation-manager/scripts/task_status_hook.py | Reads task files, context files | HIGH — multiple path patterns | No — code runs dynamically |
| SAM MCP artifact_read | plugins/development-harness/backlog_core/artifact_provider.py | Reads artifacts from root worktree paths | HIGH — path safety validation | No — code runs dynamically |
| `.gitignore` patterns | .gitignore | Ignores plan/, .claude/backlog/, .claude/context/, .claude/reports/ | HIGH — gitignore patterns will not match new paths | Yes — patterns are static |
| Pre-commit hooks | .pre-commit-config.yaml | May exclude plan/ directory from checks | HIGH — glob patterns | Yes — patterns are static |

---

## Code — Other References (path strings in literals, comments, test fixtures)

| System | File Path | Count | Breaking Risk | Staleness Risk |
|--------|-----------|-------|---|---|
| Test fixtures | plugins/development-harness/tests_sam/fixtures/*.yaml | 10+ | MEDIUM — test data hardcoded | Yes — fixtures document old structure |
| Test suite expectations | plugins/development-harness/tests_backlog/test_*.py | 20+ references | MEDIUM — test assertions on paths | Yes — test paths are static |
| Test data generators | plugins/python3-development/skills/implementation-manager/tests/test_task_status_hook/test_subagent_stop_integration.py | 5+ | MEDIUM — mock path construction | Yes — test paths are static |
| Sam CLI integration tests | plugins/development-harness/tests/test_operations_sam.py | 8+ | MEDIUM — CLI invocation with plan/ args | Yes — test paths are static |

---

## Documentation (files describing current paths)

| System | File Path | Content Type | Breaking Risk | Staleness Risk |
|--------|-----------|---|---|---|
| Local workflow guide | .claude/rules/local-workflow.md | Describes all paths (plan/, .claude/context/, .claude/reports/) | No | HIGH — comprehensive path descriptions throughout |
| Backlog lifecycle draft | plugins/development-harness/docs/backlog-lifecycle.draft.md | Documents backlog directory structure | No | HIGH — describes .claude/backlog/ structure |
| Backend providers docs | plugins/development-harness/docs/backend-providers.md | References filesystem paths in architecture | No | MEDIUM — conceptual paths, not hardcoded |
| Plan artifact lifecycle | plugins/development-harness/docs/plan-artifact-lifecycle.md | Documents plan/ and artifact locations | No | HIGH — specific path examples |
| Workflow architecture diagram | plugins/development-harness/docs/workflow-architecture-diagram.md | References plan/, .claude/context/, .claude/backlog/ | No | MEDIUM — conceptual diagram, paths are references |
| Backlog MCP migration guide | plugins/development-harness/skills/backlog/CLI_TO_MCP_MIGRATION.md | References old filesystem paths vs MCP | No | HIGH — explicitly documents migration from old paths |
| Backlog skill README | plugins/development-harness/skills/backlog/README.md | Describes backlog/.claude/backlog/ interface | No | MEDIUM — conceptual overview |
| Task file format spec | plugins/development-harness/docs/TASK_FILE_FORMAT.md | Documents T0/TN file naming in plan/ | No | MEDIUM — naming convention docs |
| Item schema reference | plugins/development-harness/skills/backlog/references/item-schema.md | Describes backlog item file location | No | HIGH — explicit path documentation |
| Artifact manifest docs | plugins/development-harness/docs/artifact-manifest-*.md | References plan/ artifact locations | No | HIGH — path-specific guidance |

---

## Configuration / CI

| System | File Path | Breaking Risk | Staleness Risk |
|--------|-----------|---|---|
| `.gitignore` | .gitignore | HIGH — patterns for plan/ and .claude/backlog/ need updates | Yes — gitignore is static |
| `.pre-commit-config.yaml` | .pre-commit-config.yaml | MEDIUM — may exclude plan/ from checks (need to verify) | Yes — config is static |
| GitHub Actions: backlog-sync | .github/workflows/backlog-sync.yml | MEDIUM — may reference .claude/backlog/ in artifact upload paths | Yes — workflow is static |
| GitHub Actions: code-quality | .github/workflows/code-quality.yml | MEDIUM — may exclude plan/ from linting | Yes — workflow is static |

---

## Agent Instructions (documentation that tells agents what to expect)

| System | File Path | Content | Breaking Risk | Staleness Risk |
|--------|-----------|---------|---|---|
| `/add-new-feature` skill | plugins/development-harness/skills/add-new-feature/SKILL.md | Instructs agents to create plan/ artifacts | No | HIGH — artifact creation paths documented |
| `/implement-feature` skill | plugins/development-harness/skills/implement-feature/SKILL.md | Instructs agents to query plan/ via SAM | No | HIGH — assumes current SAM paths |
| `/start-task` skill | plugins/development-harness/skills/start-task/SKILL.md | Instructs agents to read .claude/context/ files | No | HIGH — explicit path in workflow description |
| `/complete-implementation` skill | plugins/development-harness/skills/complete-implementation/SKILL.md | Instructs agents to read plan artifacts, write reports to .claude/reports/ | No | HIGH — agent output paths documented |
| `plan-validator` agent | plugins/development-harness/agents/plan-validator.md | Validates plans in plan/ directory | No | MEDIUM — agent description references plan/ |
| `t0-baseline-capture` agent | plugins/development-harness/agents/t0-baseline-capture.md | Creates T0 baseline file in plan/ | No | MEDIUM — artifact creation path described |
| `tn-verification-gate` agent | plugins/development-harness/agents/tn-verification-gate.md | Creates TN verification file in plan/ | No | MEDIUM — artifact creation path described |
| `context-refinement` agent | plugins/development-harness/agents/context-refinement.md | Updates Context Manifest in plan artifacts | No | MEDIUM — file location described |
| `code-reviewer` agent | plugins/development-harness/agents/code-reviewer.md | May create follow-up plan files | No | MEDIUM — implicit assumption of plan/ location |
| `feature-researcher` agent | plugins/development-harness/agents/feature-researcher.md | Produces feature-context files in plan/ | No | HIGH — output path documented |
| CLAUDE.md project rules | .claude/CLAUDE.md | References plan/ and .claude/backlog/ extensively | No | HIGH — comprehensive path documentation |
| CLAUDE.md plugin rules | plugins/development-harness/CLAUDE.md | Plugin-specific path conventions | No | MEDIUM — plugin development paths |
| Local workflow rules | .claude/rules/local-workflow.md | Comprehensive workflow documentation including all paths | No | HIGH — master documentation of path structure |

---

## Systems Inventory — Complete Path Reference Breakdown

### Producers (Create files)
- **Backlog MCP server** → writes to `.claude/backlog/*.md`
- **SAM MCP/CLI** → writes to `plan/P{NNN}-*.yaml`, `plan/tasks-{N}-*.{md,yaml}`, `plan/T0-baseline-*.yaml`, `plan/TN-verification-*.yaml`
- **Task status hook** → writes to plan files + `.claude/context/active-task-{sid}.json`
- **Feature researchers** → writes to `plan/feature-context-*.md`
- **Architecture agents** → writes to `plan/architect-*.md`
- **Codebase analyzers** → writes to `plan/codebase/*.md`
- **Code reviewers** → writes to `plan/tasks-{N}-*-followup-{k}.md` (follow-ups)
- **Doc drift auditor** → writes to `.claude/reports/` (read-only for audit, but may generate reports)
- **Service docs maintainer** → may write to `.claude/reports/` for drift documentation

### Consumers (Read files)
- **Backlog MCP/CLI** → reads `.claude/backlog/*.md`, parses YAML frontmatter
- **SAM MCP/CLI** → reads `plan/P{NNN}-*.yaml`, `plan/tasks-{N}-*.yaml`, individual task files
- **Start-task skill** → reads task files from plan/, writes to active-task context
- **Implement-feature skill** → queries SAM for ready tasks, orchestrates dispatches
- **Complete-implementation skill** → reads plan files, T0/TN verification files, generates reports
- **Hooks** → reads/writes context files, task files, status updates
- **Artifact provider** → reads all artifacts from plan/ for manifest registration
- **GitHub sync** → reads backlog items from .claude/backlog/ to sync with GitHub Issues
- **Worktree-isolated agents** → read artifacts via `artifact_read` MCP (requires full path safety validation)

### Hard Dependencies (must be updated)
1. All Python code paths in backlog_core/, sam_core/, artifact provider
2. All SKILL.md agent instruction files (.add-new-feature, .implement-feature, .start-task, .complete-implementation)
3. All agent .md descriptions referencing plan/ creation
4. .gitignore patterns for plan/, .claude/backlog/, .claude/context/, .claude/reports/
5. Test fixtures and test assertions on path names
6. Hook scripts' hardcoded path variables
7. MCP server initialization code for directory creation

### Documentation that will become stale
- .claude/rules/local-workflow.md (core workflow documentation)
- plugins/development-harness/docs/plan-artifact-lifecycle.md
- plugins/development-harness/docs/workflow-architecture-diagram.md
- All agent frontmatter descriptions of file output locations
- CLAUDE.md (both project and plugin levels)
- Artifact manifest reference documentation
- Item schema documentation

---

## Ecosystem Completeness Checklist

- [ ] **Path constants**: Are path prefixes defined in a single location (e.g., `DH_ROOT = ".dh"`)? — Currently NO, paths are inline strings
- [ ] **Path resolution**: Is there a centralized path builder (e.g., `get_item_path(item_id)`)? — Currently NO, path construction is scattered
- [ ] **Test coverage**: Do tests verify both old and new paths during migration? — YES (test fixtures exist, but must be updated)
- [ ] **Gitignore updates**: Are patterns for all four directories covered? — Requires verification of current .gitignore
- [ ] **CI/CD paths**: Are artifact upload paths in GitHub Actions verified? — Requires verification of workflow files
- [ ] **Agent instruction clarity**: Are agent SKILL.md files explicit about expected path structure? — MEDIUM clarity, paths are referenced but scattered
- [ ] **MCP migration plan**: Is there a backlog item for "Update all MCP path references"? — Unknown, may exist in backlog already
- [ ] **Rollback procedure**: Can the migration be reversed if needed? — Not documented

---

## Estimated Impact Severity

**Breaking Changes (must be fixed before migration)**: 12–15 files
- All Python files in backlog_core/, sam_core/, artifact provider
- Hook scripts with hardcoded paths
- All SKILL.md agent instruction files

**Stale Documentation (must be updated after migration)**: 25–30 files
- .claude/CLAUDE.md
- .claude/rules/local-workflow.md
- Backlog/SAM documentation in plugins/
- Agent descriptions with path references
- Skill frontmatter with artifact output paths

**Static Configuration (must be updated)**: 3–4 files
- .gitignore
- .pre-commit-config.yaml
- GitHub Actions workflows (.github/workflows/*.yml)

**Test Fixtures (must be updated)**: 10+ test files
- All test assertions on plan/ and backlog paths
- Test data generators
- Fixture YAML files

---

## Data Migration Considerations

- **GitHub Issues**: Issue bodies contain artifact manifest sections with `plan/` paths — these become out of date immediately after directory move. Migration tool must update artifact manifest paths in all linked issues.
- **Worktree Artifacts**: Artifacts registered in GitHub issue comments will have paths prefixed with `plan/` — these need rewriting to `.dh/plan/`.
- **Local Backlog Files**: Item filenames in `.claude/backlog/` are not path-relative — but their YAML frontmatter may contain `issue: N` which links to GitHub. No direct path updates needed in item files, but the MCP server must know the new location.
- **SAM Task Files**: Each task file's `started`, `completed`, `LastActivity` timestamps and GitHub sub-issue links reference will remain valid — only filesystem paths change.

---

## Recommended Migration Sequencing

1. **Phase 1**: Create constants/builders for path resolution (centralize path logic)
2. **Phase 2**: Update all Python code (backlog_core, sam_core, hooks, artifact provider)
3. **Phase 3**: Update SKILL.md and agent descriptions to reference new paths
4. **Phase 4**: Update static config (.gitignore, pre-commit, workflows)
5. **Phase 5**: Create and test migration tool for file movement + manifest updates
6. **Phase 6**: Update all documentation and rules files
7. **Phase 7**: Update test fixtures and test assertions
8. **Phase 8**: Execute migration (file move + GitHub manifest updates)

</div>

## Fact-Check

<div><sub>2026-03-22T12:29:06Z</sub>

## Fact-Check Results

### Claim 1: "Backlog items live in .claude/backlog/"

**Evidence**: 
- Directory exists: `/home/ubuntulinuxqa2/repos/claude_skills/.claude/backlog/`
- File count: 332 .md files in this directory
- Files observed: `p0-*.md`, `p1-*.md`, `p2-*.md`, `idea-*.md`, `completed-*.md`

**Verdict**: VERIFIED — backlog items definitively live in `.claude/backlog/`

---

### Claim 2: "Plan artifacts live in plan/ at project root"

**Evidence**: 
- Directory exists: `/home/ubuntulinuxqa2/repos/claude_skills/plan/`
- File count: 391 files (.md + .yaml) in this directory
- Files observed: `architect-*.md`, `feature-context-*.md`, `P{NNN}-*.yaml`, `TN-verification-*.yaml`, `T0-baseline-*.yaml`, `codebase/` subdirectory

**Verdict**: VERIFIED — plan artifacts live at `plan/` (root level)

---

### Claim 3: "These are both development-harness artifacts"

**Evidence**: 
- Backlog MCP server location: `plugins/development-harness/backlog_core/server.py` — hardcoded to read from `.claude/backlog/`
- SAM schema server: `plugins/development-harness/sam_schema/server.py` — hardcoded to read from `plan/`
- Artifact provider: `plugins/development-harness/backlog_core/artifact_provider.py` — integrates with plan/ artifact locations
- All references (138 files mention `.claude/backlog`, 463 files mention `plan/`) — predominantly within development-harness plugin code and skills
- Skills that consume these: `/dh:add-new-feature`, `/dh:implement-feature`, `/dh:start-task`, `/dh:complete-implementation` — all part of development-harness

**Verdict**: VERIFIED — both directories are created, maintained, and consumed exclusively by development-harness plugin and its MCP servers

---

### Claim 4: "stored in inconsistent locations"

**Current Layout**:
```
.claude/
├── backlog/        (332 backlog items)
├── context/        (active-task-*.json context files)
├── plan/           (14 files: orchestrator-discipline-assessment.md, etc.)
├── reports/        (development harness reports)
└── [other DH artifacts]

plan/              (391 artifacts at root level)
├── architect-*.md
├── feature-context-*.md
├── P{NNN}-*.yaml
├── T0-baseline-*.yaml
├── TN-verification-*.yaml
└── codebase/ subdirectory
```

**Analysis**: 
- Backlog items: `.claude/backlog/`
- Plan artifacts (main): `plan/` at root
- Plan artifacts (secondary/temp): `.claude/plan/` for local planning
- Context files: `.claude/context/`
- Reports: `.claude/reports/`

**Verdict**: VERIFIED — development-harness artifacts ARE stored in inconsistent locations. Backlog in `.claude/` tree, primary plan artifacts at project root. This is objectively inconsistent.

---

### Claim 5: "A migration tool is needed that moves existing files, corrects any internal path references, and updates all consumers"

**Scope Analysis**:

**Files referencing these paths**:
- `.claude/backlog/`: 138 files (include backlog items themselves, DH skills, agent files, CI workflows, documentation)
- `plan/`: 463 files (DH code, tests, skills, documentation, examples)

**Path patterns found** (via grep):
- Hard-coded paths in Python code: `.claude/backlog`, `plan/`
- SKILL.md references: documented paths in workflow skills
- YAML frontmatter: artifact paths stored in GitHub issue bodies
- CI workflow: `.github/workflows/backlog-sync.yml` references `.claude/backlog`
- Documentation references: plan artifact path patterns in `.claude/rules/local-workflow.md`

**Migration complexity factors**:
1. **High-impact consumers**: backlog_core/server.py, sam_schema/server.py, artifact_provider.py, artifact_registry.py — all hardcoded
2. **Documentation artifacts**: GitHub issue bodies contain path references in artifact manifests (requires API mutation)
3. **Test fixtures**: 50+ test files use hard-coded paths
4. **CI workflows**: `.github/workflows/backlog-sync.yml` must be updated
5. **Skill SKILL.md files**: 20+ skill files document path expectations

**Is migration tool proportionate?**
- Yes. 463 + 138 = 601 total files involved
- 50+ Python files with hard-coded paths to update
- GitHub API calls needed to update artifact manifests in issue bodies
- Test fixtures require path substitution across test suites
- This is beyond manual find-and-replace capability

**Verdict**: PARTIALLY VERIFIED — A migration tool is justified by scope, but must:
1. Analyze existing path patterns (not assume)
2. Update hard-coded paths in 50+ Python files
3. Migrate GitHub artifact manifest entries (artifact_register calls needed)
4. Update CI workflow references
5. Update skill documentation (SKILL.md files)
6. Provide rollback capability in case of conflicts

---

### Summary Table

| Claim | Evidence | Verdict |
|-------|----------|---------|
| Backlog items in `.claude/backlog/` | 332 .md files present | VERIFIED |
| Plan artifacts in `plan/` root | 391 files present | VERIFIED |
| Both are DH artifacts | All consumed by development-harness plugin | VERIFIED |
| Stored inconsistently | Mixed `.claude/` and root-level locations | VERIFIED |
| Migration tool needed + proportionate | 601 files involved, 50+ hard-coded paths | VERIFIED (with caveats) |

---

### Outstanding Questions (From Item RT-ICA)

The following items remain unresolved and require human design decisions:

1. **Target directory layout under .dh/** — How to organize consolidated content? (MISSING)
   - Option A: `.dh/backlog/` + `.dh/plan/`
   - Option B: `.dh/items/` + `.dh/specs/`
   - Option C: Flat `.dh/` with suffixes: `item-*.md`, `spec-*.md`

2. **Scope expansion**: Are `.claude/context/` and `.claude/reports/` also in migration scope? (MISSING)

3. **Migration strategy**: Big bang vs incremental with symlinks? (MISSING)

4. **Cache impacts**: How does plugin cache path (`~/.claude/plugins/cache/`) interact with consolidated paths? (DERIVABLE)

5. **Backward compatibility**: Do installed plugin versions need to support old paths during transition? (MISSING)

---

### Recommendations

1. **Proceed with migration design** — all factual claims are verified
2. **Resolve scope questions** before implementation — consolidation scope affects tool complexity
3. **Create design document** addressing target layout, migration strategy, and compatibility
4. **Prototype on small subset** (10 backlog items, 5 plan files) before migrating all 600+ files
</div>

## RT-ICA

<div><sub>2026-03-22T13:00:54Z</sub>

RT-ICA Final: Consolidate backlog and plan directories under .dh/
Goal: Establish three-tier DH state architecture — in-repo config (.dh/), persistent cache (~/.dh/projects/{slug}/), ephemeral state (~/.dh/projects/{slug}/)

Conditions:
1. Current directory structure of .claude/backlog/ | AVAILABLE | Citation: fact-checker verified 332 .md files
2. Current directory structure of plan/ | AVAILABLE | Citation: fact-checker verified 391 artifacts
3. All consumers of .claude/backlog/ paths | AVAILABLE | Citation: impact-analyst found 84 plugin files, 138 total files
4. All consumers of plan/ paths | AVAILABLE | Citation: impact-analyst found 463 files mentioning plan/
5. Target directory layout | AVAILABLE | Citation: user decision 2026-03-22 — three tiers: .dh/ (in-repo config), ~/.dh/projects/{slug}/ (persistent + ephemeral state)
6. Whether .claude/context/ is in scope | AVAILABLE | Citation: user confirmed — moves to ~/.dh/projects/{slug}/context/ (ephemeral tier)
7. Whether .claude/reports/ is in scope | AVAILABLE | Citation: user confirmed — moves to ~/.dh/projects/{slug}/reports/ (ephemeral tier)
8. Migration strategy | AVAILABLE | Citation: user decision — SQLite database behind existing MCP APIs; GitHub Issues/Projects as persistent backend
9. Impact on installed plugin cache paths | AVAILABLE | Citation: self-resolution — cache picks up new paths from repo on reinstall
10. Impact on CI workflows | AVAILABLE | Citation: impact-analyst identified .github/workflows/backlog-sync.yml
11. Symlinks/hardlinks in current paths | AVAILABLE | Citation: find returned 0
12. Directory sizes | AVAILABLE | Citation: .claude/backlog/ 2.5M, plan/ 6.0M, context/ 64K, reports/ 1.6M
13. GitHub artifact manifests with path references | DERIVABLE | Info: requires API iteration; not blocking for planning
14. Backward compatibility policy | AVAILABLE | Citation: user decision — SQLite + MCP migration means consumers use MCP API, not file paths; no backward compat shim needed
15. What stays in-repo (.dh/) | AVAILABLE | Citation: user decision — project config (settings, agent/skill overrides) committed to git for cross-developer sharing
16. SQLite migration scope | AVAILABLE | Citation: user decision — local cache becomes SQLite DB accessible via backlog and SAM MCP servers

AVAILABLE count: 15
DERIVABLE count: 1
MISSING count: 0

Decision: APPROVED — all conditions resolved
</div>