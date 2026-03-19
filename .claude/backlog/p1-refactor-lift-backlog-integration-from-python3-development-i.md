---
name: 'refactor: Lift backlog integration from python3-development into development-harness (dh)'
description: "The backlog integration skills (create-backlog-item, groom-backlog-item, work-backlog-item) and their supporting scripts currently live in the python3-development plugin. Phase 3 of the dh architecture refactor lifts these into the development-harness (dh) plugin so that dh becomes the universal process engine with backlog as its upstream intake layer. python3-development retains the skills as forwarding references only.\n\nScope:\n- Move backlog skills directory from python3-development to dh plugin\n- Move backlog scripts (backlog.py, task_status_hook.py, etc.) to dh\n- Update plugin.json and marketplace.json entries\n- Add forwarding references in python3-development pointing to dh\n- Verify backlog MCP server registration in dh plugin.json\n- Update all internal references from python3-development: to dh: namespace\n\nDependencies: Depends on Phase 1 completion (dh namespace established) — #581 Phase 1 is now done."
metadata:
  topic: refactor-lift-backlog-integration-from-python3-development-i
  source: 'GitHub Issue #581 — Development Harness Architecture Refactor, Phase 3'
  added: '2026-03-18'
  priority: P1
  type: Refactor
  status: open
  issue: '#843'
  groomed: '2026-03-19'
  last_synced: '2026-03-19T00:18:23Z'
  plan: plan/P777-backlog-lift-to-dh-followup-1.yaml
---

## RT-ICA

<div><sub>2026-03-19T00:12:39Z</sub>

RT-ICA Snapshot (Step 3.5): Lift backlog integration from python3-development into dh
Goal: Move backlog integration skills (create-backlog-item, groom-backlog-item, work-backlog-item) and supporting infrastructure from python3-development plugin to dh plugin.
Conditions:
1. Location of backlog skills in python3-development | Status: AVAILABLE
2. Backlog scripts exact paths (backlog.py, task_status_hook.py, etc.) | Status: DERIVABLE
3. dh plugin structure (plugin.json, skills directory layout) | Status: AVAILABLE
4. Skills to move: create-backlog-item, groom-backlog-item, work-backlog-item | Status: AVAILABLE
5. Internal namespace references within backlog skills | Status: DERIVABLE
6. Backlog MCP server registration status in dh plugin.json | Status: DERIVABLE
7. Forwarding reference mechanism (how to keep python3-development working) | Status: AVAILABLE
8. Symlinks in python3-development pointing to backlog skills | Status: DERIVABLE
AVAILABLE count: 4
DERIVABLE count: 4
MISSING count: 0
</div>

## Groomed (2026-03-19)

### Issue Classification

<div><sub>2026-03-19T00:13:19Z</sub>

Type: refactor

Scenario-target: Move backlog skills from python3-development to development-harness to establish dh as the universal process engine with backlog as upstream intake.

Rationale: This is Phase 3 of the planned dh architecture refactor (#581). The scope is bounded — move skill directories, update namespace references, add forwarding stubs in python3-development. This is deliberate architectural consolidation, not a symptom or defect response.

Classification: **refactor** (bounded)
</div>

### Impact Radius

<div><sub>2026-03-19T00:15:09Z</sub>

### Scope

<div><sub>2026-03-19T00:17:42Z</sub>

**In scope:**

- Move 3 skill directories from `.claude/skills/` (project-level) to `plugins/development-harness/skills/`:
  - `.claude/skills/create-backlog-item/` → `plugins/development-harness/skills/create-backlog-item/`
  - `.claude/skills/groom-backlog-item/` → `plugins/development-harness/skills/groom-backlog-item/`
  - `.claude/skills/work-backlog-item/` → `plugins/development-harness/skills/work-backlog-item/`
- Fix 4 hard breakages (B1–B4): update bare-name `Skill()` calls to `dh:` namespace prefix
- Remove source directories from `.claude/skills/` after move

**Not in scope:**

- `.claude/skills/backlog/` (MCP server + CLI backing the backlog system) — stays project-level, unaffected
- `plugins/python3-development/plugin.json` and `plugins/development-harness/.claude-plugin/plugin.json` — no manual entries needed; skill auto-discovery handles new skills placed under `plugins/development-harness/skills/`
- `plugins/python3-development/skills/implementation-manager/scripts/` — SAM workflow scripts, separate concern
- Forwarding stubs in python3-development — not required; all callers will use `dh:` namespace prefix directly

**Key constraint:** `plugins/development-harness/.claude-plugin/plugin.json` does NOT use an explicit `skills` list — auto-discovery is active. No plugin.json edits are needed when the 3 skill directories are placed under `plugins/development-harness/skills/`.
</div>

### Files

<div><sub>2026-03-19T00:17:56Z</sub>

**Files to move (13 files — preserve directory structure during move):**

`create-backlog-item` (1 file):
- `.claude/skills/create-backlog-item/SKILL.md`

`groom-backlog-item` (3 files):
- `.claude/skills/groom-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/references/groomer-agent.md`
- `.claude/skills/groom-backlog-item/references/issue-classification.md`

`work-backlog-item` (9 files):
- `.claude/skills/work-backlog-item/SKILL.md`
- `.claude/skills/work-backlog-item/references/auto-mode.md`
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md`
- `.claude/skills/work-backlog-item/references/error-handling.md`
- `.claude/skills/work-backlog-item/references/example-sessions.md`
- `.claude/skills/work-backlog-item/references/github-integration.md`
- `.claude/skills/work-backlog-item/references/sam-definition.md`
- `.claude/skills/work-backlog-item/references/step-procedures.md`
- `.claude/skills/work-backlog-item/references/validation-plan.md`

**Call sites to update (B1–B4):**

B1 — `plugins/development-harness/skills/interop/SKILL.md` line 116
- `Skill(skill="work-backlog-item", args="#N")` → `Skill(skill="dh:work-backlog-item", args="#N")`

B2 — `plugins/python3-development/skills/complete-implementation/SKILL.md` line 239
- `Skill(skill: "create-backlog-item", args: "--auto {derived_title}")` → `Skill(skill="dh:create-backlog-item", args="--auto {derived_title}")`

B3 — `.claude/CLAUDE.md` lines 32, 226, 256
- `/create-backlog-item` → `/dh:create-backlog-item`
- `/work-backlog-item` → `/dh:work-backlog-item`

B4 — `.claude/skills/work-backlog-item/SKILL.md` (internal cross-refs, lines 177 and 217)
- `Skill(skill="create-backlog-item")` → `Skill(skill="dh:create-backlog-item")`
- `Skill(skill="groom-backlog-item")` → `Skill(skill="dh:groom-backlog-item")`

Note: B4 updates are made to the file at its SOURCE location before moving, or immediately after moving to the destination.
</div>

### Dependencies

<div><sub>2026-03-19T00:18:05Z</sub>

**Phase 1 (dh namespace establishment) — DONE (#581).** The `dh:` namespace prefix pattern is established and in use. Evidence: `Skill(skill="dh:planning")` and `Skill(skill="dh:context-integration")` already appear in `plugins/development-harness/agents/generic-stage-agent.md`.

No other blockers. This item is unblocked and ready to implement.
</div>

### Acceptance Criteria

<div><sub>2026-03-19T00:18:16Z</sub>

- [ ] All 3 skill directories exist under `plugins/development-harness/skills/`: `create-backlog-item/`, `groom-backlog-item/`, `work-backlog-item/`
- [ ] `/dh:create-backlog-item`, `/dh:groom-backlog-item`, and `/dh:work-backlog-item` invoke correctly without bare-name fallback
- [ ] Zero bare `Skill(skill="create-backlog-item")`, `Skill(skill="groom-backlog-item")`, and `Skill(skill="work-backlog-item")` calls remain in any file under `plugins/`
- [ ] `.claude/CLAUDE.md` references updated from `/create-backlog-item` and `/work-backlog-item` to `/dh:create-backlog-item` and `/dh:work-backlog-item`
- [ ] `.claude/skills/create-backlog-item/`, `.claude/skills/groom-backlog-item/`, and `.claude/skills/work-backlog-item/` directories no longer exist after move
</div>

### Effort

<div><sub>2026-03-19T00:18:23Z</sub>

Low complexity. Single session.

- 3 skill directories to move (13 files total, directory structure preserved)
- 4 call site string updates (B1–B4)
- No logic changes, no new code, no plugin.json edits required
- Auto-discovery handles registration of new skills in dh
</div>


## Affected Systems Inventory

### Key Finding: Skills Do Not Yet Exist in python3-development

The three skills targeted for migration (`create-backlog-item`, `groom-backlog-item`, `work-backlog-item`) currently live at:

- `.claude/skills/create-backlog-item/` (project-level, not in any plugin)
- `.claude/skills/groom-backlog-item/` (project-level, not in any plugin)
- `.claude/skills/work-backlog-item/` (project-level, not in any plugin)

They are NOT present under `plugins/python3-development/skills/`. The backlog item title says "Lift from python3-development" but the source is the project-level `.claude/skills/` directory. This changes the migration scope: the move is from project-level to `plugins/development-harness/`.

---

### Skill Files (Source of Truth to Be Moved)

**create-backlog-item**
- `.claude/skills/create-backlog-item/SKILL.md`

**groom-backlog-item**
- `.claude/skills/groom-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/references/groomer-agent.md`
- `.claude/skills/groom-backlog-item/references/issue-classification.md`

**work-backlog-item**
- `.claude/skills/work-backlog-item/SKILL.md`
- `.claude/skills/work-backlog-item/references/auto-mode.md`
- `.claude/skills/work-backlog-item/references/close-resolve-procedure.md`
- `.claude/skills/work-backlog-item/references/error-handling.md`
- `.claude/skills/work-backlog-item/references/example-sessions.md`
- `.claude/skills/work-backlog-item/references/github-integration.md`
- `.claude/skills/work-backlog-item/references/sam-definition.md`
- `.claude/skills/work-backlog-item/references/step-procedures.md`
- `.claude/skills/work-backlog-item/references/validation-plan.md`

**Total: 13 files to move.**

---

### Supporting Infrastructure

**Backlog scripts (project-level, shared)**
- `.claude/skills/backlog/scripts/backlog.py`
- `.claude/skills/backlog/scripts/state_handler.py`
- `.claude/skills/backlog/backlog_core/__init__.py`
- `.claude/skills/backlog/backlog_core/entry_blocks.py`
- `.claude/skills/backlog/backlog_core/github.py`
- `.claude/skills/backlog/backlog_core/models.py`
- `.claude/skills/backlog/backlog_core/operations.py`
- `.claude/skills/backlog/backlog_core/parsing.py`
- `.claude/skills/backlog/backlog_core/server.py`

These are the MCP server and CLI backing the backlog system. They live at project-level, not in either plugin. **Not in scope for migration** unless the intent is to also move the MCP server into dh.

**implementation-manager scripts (python3-development)**
- `plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py`
- `plugins/python3-development/skills/implementation-manager/scripts/implementation_manager.py`
- `plugins/python3-development/skills/implementation-manager/scripts/task_format.py`

These are referenced by the SAM workflow but do not directly implement backlog skills. Not in scope for this migration.

**development-harness symlinks to python3-development scripts**
- `plugins/development-harness/skills/implementation-manager/scripts/implementation_manager.py` → symlink to `plugins/python3-development/...`
- `plugins/development-harness/skills/implementation-manager/scripts/task_format.py` → symlink to `plugins/python3-development/...`

These symlinks are unaffected by the backlog skill migration.

**MCP server registration**
- `plugins/python3-development/.claude-plugin/plugin.json` — `mcpServers` key exists but no backlog server registered (field is present but empty-ish at inspection point)
- `plugins/development-harness/.claude-plugin/plugin.json` — `mcpServers: {}` (empty)
- `.claude-plugin/marketplace.json` — exists; will need a new entry or version bump when dh gains these skills

The backlog MCP server (`backlog_core/server.py`) is registered elsewhere (project-level CLAUDE.md / MCP config), not via plugin.json. **No plugin.json MCP registration changes required** for the skill migration itself.

---

### Files That Reference These Skills (Cross-Plugin)

**plugins/development-harness/skills/interop/SKILL.md**
- Directly invokes `/work-backlog-item` via `Skill(skill="work-backlog-item", args="#N")`
- Currently works because skills are resolved project-level
- After move: must resolve via `development-harness:work-backlog-item`
- **Breaks**: YES if skill namespace changes. **Content update needed**: YES — `Skill()` call must use new namespace.

**plugins/python3-development/skills/complete-implementation/SKILL.md**
- References `Skill(skill: "create-backlog-item", args: "--auto ...")` (line 239)
- References `/work-backlog-item` in instructional text (lines 274, 287, 358, 371)
- After move to dh: python3-development is a separate plugin; cross-plugin Skill() calls require namespace prefix
- **Breaks**: YES — `Skill(skill: "create-backlog-item")` will not resolve if skill moves to dh and caller is in python3-development
- **Code change needed**: YES — add `development-harness:` namespace prefix, OR keep a thin launcher in python3-development that delegates to dh

**plugins/plugin-creator/.claude/reports/validator-findings-investigation.md**
- Internal report file referencing these skill names
- **Breaks**: NO — this is a static report/doc, not executable
- **Stale**: YES (minor) — refers to current location

---

### Files That Reference These Skills (Project-level)

**High-coupling files (operational):**
- `.claude/CLAUDE.md` — lines 32, 226, 256: instructs users to invoke `/create-backlog-item` and `/work-backlog-item` by bare name. After move, project-level resolution would fail unless project CLAUDE.md is updated to reference `development-harness:` namespace or dh is always installed.
- `.claude/rules/local-workflow.md` — lines 289, 416: references `create-backlog-item --auto` in orchestration instructions

**Content-only references (documentation, no breakage):**
- `.claude/skills/backlog-tools-administrator/SKILL.md`
- `.claude/skills/backlog/SKILL.md`, `references/`, `templates/`
- `.claude/skills/evaluate-sdlc-layers/SKILL.md`
- `.claude/skills/group-items-to-milestone/SKILL.md`
- `.claude/skills/session-historian/SKILL.md`
- `.claude/skills/complete-milestone/SKILL.md`, `start-milestone/SKILL.md`
- `.claude/skills/work-backlog-item/references/*.md` (self-referential, will move with the skill)
- `.claude/hooks/stop-backlog-reminder.cjs`
- Numerous `.claude/backlog/p*.md` files (78 total contain references — all backlog item files, not executable)
- `.claude/docs/` files (ADRs, process audits, lifecycle docs)

---

## 5-Question Checklist Per System

### Skill Files (13 files being moved)
1. **Break on move?** — YES, all relative `./references/` links within SKILL.md files must remain valid at new path. References use `./references/filename.md` — valid as long as directory structure is preserved during move.
2. **Stale?** — NO (they are the canonical source, moving with content intact)
3. **Code change?** — NO internal code changes needed; directory move only
4. **Content update?** — MAYBE: `work-backlog-item/SKILL.md` and `create-backlog-item/SKILL.md` may contain self-references to their old location; audit needed
5. **Test coverage?** — NO test exists for skill invocation routing

### `plugins/development-harness/skills/interop/SKILL.md`
1. **Break?** — YES, bare `skill="work-backlog-item"` stops resolving once skill leaves project-level
2. **Stale?** — YES
3. **Code change?** — YES — `Skill(skill="work-backlog-item")` → `Skill(skill="development-harness:work-backlog-item")`
4. **Content update?** — YES
5. **Test?** — NO

### `plugins/python3-development/skills/complete-implementation/SKILL.md`
1. **Break?** — YES — `Skill(skill: "create-backlog-item")` cross-plugin call breaks
2. **Stale?** — YES
3. **Code change?** — YES — add `development-harness:` prefix, or introduce thin forwarding skill in python3-development
4. **Content update?** — YES
5. **Test?** — NO

### `.claude/CLAUDE.md`
1. **Break?** — YES (operationally) — bare `/create-backlog-item` and `/work-backlog-item` invocations in instructions become unresolvable if project-level skills are removed and dh is not installed
2. **Stale?** — YES after move
3. **Code change?** — NO (instructions, not code)
4. **Content update?** — YES — update namespace references OR document that dh must be installed
5. **Test?** — NO

### `.claude/rules/local-workflow.md`
1. **Break?** — Soft break: instructions reference bare `create-backlog-item --auto`; agents following these instructions will fail to resolve
2. **Stale?** — YES after move
3. **Code change?** — NO
4. **Content update?** — YES — update namespace in orchestration instructions
5. **Test?** — NO

### `.claude-plugin/marketplace.json`
1. **Break?** — NO (doesn't break existing entries)
2. **Stale?** — YES — dh plugin entry needs updated skill list / version bump
3. **Code change?** — NO
4. **Content update?** — YES — add backlog skills to dh's listed capabilities; bump version
5. **Test?** — NO

### `plugins/python3-development/.claude-plugin/plugin.json` and `plugins/development-harness/.claude-plugin/plugin.json`
1. **Break?** — NO (no backlog MCP registered in either; skill auto-discovery handles skills directory)
2. **Stale?** — NO for MCP section; dh plugin.json does NOT use explicit `skills` list (auto-discovery), so no update needed there
3. **Code change?** — NO
4. **Content update?** — NO (auto-discovery handles new skills in `plugins/development-harness/skills/`)
5. **Test?** — NO

### Backlog scripts (`.claude/skills/backlog/`)
1. **Break?** — NO — these are independent of which plugin hosts the skill launchers
2. **Stale?** — NO
3. **Code change?** — NO
4. **Content update?** — NO
5. **Test?** — YES — `.claude/skills/backlog/tests/test_scenarios.py` exists

---

## Summary Risk Table

| File / System | Breaks | Stale | Code Change | Content Update | Has Test |
|---|---|---|---|---|---|
| 13 skill files (move) | Directory-relative links — preserve structure | No | No | Audit self-refs | No |
| `dh/skills/interop/SKILL.md` | YES | YES | YES | YES | No |
| `p3d/skills/complete-implementation/SKILL.md` | YES | YES | YES | YES | No |
| `.claude/CLAUDE.md` | YES (soft) | YES | No | YES | No |
| `.claude/rules/local-workflow.md` | Soft | YES | No | YES | No |
| `.claude-plugin/marketplace.json` | No | YES | No | YES | No |
| `plugin.json` files (both plugins) | No | No | No | No | No |
| `backlog/` scripts + MCP server | No | No | No | No | YES |
| `dh`/`p3d` symlinked impl-manager scripts | No | No | No | No | No |
| 78 backlog item `.md` files | No | No | No | No | No |

---

## Key Decision Required

**Cross-plugin skill invocation**: After the move, `complete-implementation` (in python3-development) calls `create-backlog-item` (now in development-harness). Two options:

1. **Namespace prefix** — update all callers to use `development-harness:create-backlog-item`. Requires p3d to depend on dh being installed.
2. **Thin forwarding skill** — keep a `create-backlog-item` stub in python3-development that delegates to `development-harness:create-backlog-item`. Preserves backward compatibility; adds indirection.

This decision gates the `complete-implementation` fix approach and should be resolved before implementation begins.

</div>


## Fact-Check

<div><sub>2026-03-19T00:13:33Z</sub>

## Verification Results (2026-03-19)

**Claim 1: Backlog skills currently live in python3-development plugin**
- **Status: REFUTED**
- Evidence: Glob searches for `plugins/python3-development/skills/{create,groom,work}-backlog-item/**` returned NO files
- Actual location: `.claude/skills/` (project level, not plugin level)
  - `.claude/skills/create-backlog-item/SKILL.md`
  - `.claude/skills/groom-backlog-item/SKILL.md` (+ references/)
  - `.claude/skills/work-backlog-item/SKILL.md` (+ references/)

**Claim 2: dh does NOT currently have these backlog skills**
- **Status: VERIFIED**
- Evidence: Glob searches for `plugins/development-harness/skills/{create,groom,work}-backlog-item/**` returned NO files
- Conclusion: dh plugin has no backlog integration skills

**Claim 3: Backlog MCP server registered in python3-development**
- **Status: INCONCLUSIVE**
- Evidence: Grep for "backlog" in `plugins/python3-development/.claude-plugin/` returned no matches
- Cannot verify without seeing marketplace.json MCP servers section or dh plugin.json for comparison

**Claim 4: python3-development retains skills as forwarding references only (post-move)**
- **Status: PENDING** (future state, not verifiable yet)

## Architectural Insight

The backlog integration is currently at project scope (`.claude/skills/`), not plugin scope. The refactoring actually involves TWO operations:
1. Move skills from `.claude/skills/` → `plugins/development-harness/skills/`
2. Create forwarding references back to dh from python3-development namespace

The description's framing ("currently live in python3-development") appears to assume project-level and plugin-level skills are equivalent, but they are distinct scopes. This needs clarification in the scope statement.
</div>

## RT-ICA

<div><sub>2026-03-19T00:16:57Z</sub>

## RT-ICA — Final (Step 8.5)

**Item**: refactor: Lift backlog integration from python3-development into development-harness (dh)
**Decision**: APPROVED — all conditions resolved
**Assessed**: 2026-03-18

---

### Condition Assessment

| # | Condition | Status | Source |
|---|-----------|--------|--------|
| 1 | Location of backlog skills | RESOLVED | `.claude/skills/` (not python3-development). Three skills confirmed: `create-backlog-item`, `groom-backlog-item`, `work-backlog-item` |
| 2 | Backlog scripts exact paths | RESOLVED | Scripts live in `.claude/skills/backlog/scripts/` (MCP server + CLI). No per-skill scripts inside the three migration targets. |
| 3 | dh plugin structure | RESOLVED | `plugins/development-harness/skills/` exists with working skills. SKILL.md components auto-discovered. |
| 4 | Skills to move | RESOLVED | Exactly 3 skills: `create-backlog-item`, `groom-backlog-item`, `work-backlog-item` — all at `.claude/skills/` |
| 5 | Internal namespace references within backlog skills | RESOLVED | `work-backlog-item/SKILL.md` invokes `create-backlog-item` and `groom-backlog-item` by bare name (lines 177, 217). These are intra-group cross-references — all three move together, so relative bare-name calls within the group remain valid IF the invocation strategy uses `dh:` prefix consistently (see condition 7). |
| 6 | Backlog MCP server registration | RESOLVED | `backlog` MCP server is NOT registered in either `plugin.json`. It is a separate project-level MCP server. Migration does not affect MCP registration. |
| 7 | Cross-plugin invocation strategy | RESOLVED | `dh:skill-name` namespace prefix is the established pattern. Evidence: `Skill(skill="dh:planning")`, `Skill(skill="dh:context-integration")` used in `plugins/development-harness/agents/generic-stage-agent.md` and `docs/poc-validation-guide.md`. Bare-name invocations in callers are the break surface — they require update to `dh:` prefix post-migration. |
| 8 | Symlinks in python3-development | RESOLVED | No backlog-related symlinks found in `plugins/python3-development/skills/`. One unrelated symlink (`accessing_online_resources.md`) exists. No symlink cleanup needed for this migration. |

---

### Hard Breakages Requiring Action

Three call sites use bare-name invocations that break once skills leave project-level:

**B1** — `plugins/development-harness/skills/interop/SKILL.md` line 116
```
Skill(skill="work-backlog-item", args="#N")
```
Fix: update to `Skill(skill="dh:work-backlog-item", args="#N")`

**B2** — `plugins/python3-development/skills/complete-implementation/SKILL.md` line 239
```
Skill(skill: "create-backlog-item", args: "--auto {derived_title}")
```
Fix: update to `Skill(skill="dh:create-backlog-item", args="--auto {derived_title}")`

**B3** — `.claude/CLAUDE.md` user-facing instructions
Instructs users to invoke `/create-backlog-item` and `/work-backlog-item` by bare name.
Fix: update to `/dh:create-backlog-item` and `/dh:work-backlog-item` (or document that `dh` plugin must be installed).

---

### Internal Cross-References Within Migrated Skills

`work-backlog-item/SKILL.md` calls `create-backlog-item` and `groom-backlog-item` by bare name. Since all three skills move together into `dh`, these calls must be updated to `dh:create-backlog-item` and `dh:groom-backlog-item` as part of the same migration commit.

`groom-backlog-item/references/issue-classification.md` calls `Skill(skill="find-cause")` — this is an external dependency on a separate skill not part of this migration. No change needed; it resolves by bare name if `find-cause` is project-level, or requires a namespace prefix if it is not. Out of scope for this migration.

---

### Scope Summary

**Files to move** (copy to `plugins/development-harness/skills/`, remove from `.claude/skills/`):
- `.claude/skills/create-backlog-item/` → `plugins/development-harness/skills/create-backlog-item/`
- `.claude/skills/groom-backlog-item/` → `plugins/development-harness/skills/groom-backlog-item/`
- `.claude/skills/work-backlog-item/` → `plugins/development-harness/skills/work-backlog-item/`

**Files to update** (bare-name → dh: prefix):
- `plugins/development-harness/skills/interop/SKILL.md` (B1)
- `plugins/python3-development/skills/complete-implementation/SKILL.md` (B2)
- `.claude/CLAUDE.md` (B3)
- `.claude/skills/work-backlog-item/SKILL.md` (internal cross-refs to `create-backlog-item` and `groom-backlog-item`)

**Files NOT affected**:
- `.claude/skills/backlog/` (MCP server + CLI — separate concern, stays project-level)
- `plugins/python3-development/plugin.json` (no backlog skill entries)
- `plugins/development-harness/plugin.json` (auto-discovery handles new skills; no manual registration needed)

---

### Risk

Low. The migration is a directory move + 4 call-site string updates. No logic changes. The `dh:` namespace prefix pattern is already established and in use. The backlog MCP server is decoupled and unaffected.

**APPROVED — ready to plan and implement.**
</div>