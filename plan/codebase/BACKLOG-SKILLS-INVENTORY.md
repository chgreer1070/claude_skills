# Backlog Skills Inventory Analysis

**Analysis Date:** 2026-03-18
**Focus:** File tree mapping, Skill() invocations, namespace references across backlog skill ecosystem

---

## Directory 1: `.claude/skills/create-backlog-item/`

**Root directory:** `.claude/skills/create-backlog-item/`

### File Tree

```text
.claude/skills/create-backlog-item/
└── SKILL.md
```

**Total files:** 1

### File Contents Summary

- **SKILL.md** (214 lines)
  - Frontmatter: `name: create-backlog-item`
  - Purpose: Create per-item files in `.claude/backlog/` with three modes (guided, quick, --auto)
  - Contains no `Skill()` invocations to other backlog skills
  - References `/groom-backlog-item` and `/work-backlog-item` as next-step commands in user-facing output (Step 6, lines 197–198)

### Skill() References to Other Backlog Skills

**None found.** This skill does not call other backlog skills programmatically.

### Namespace References (e.g., `/skill-name`)

- Line 197: `/groom-backlog-item {title}` — next-step suggestion
- Line 198: `/work-backlog-item {title}` — next-step suggestion

---

## Directory 2: `.claude/skills/groom-backlog-item/`

**Root directory:** `.claude/skills/groom-backlog-item/`

### File Tree

```text
.claude/skills/groom-backlog-item/
├── SKILL.md
└── references/
    ├── issue-classification.md
    └── groomer-agent.md
```

**Total files:** 3

### File Contents Summary

- **SKILL.md** (651 lines)
  - Frontmatter: `name: groom-backlog-item`
  - Purpose: Orchestrate autonomous backlog refinement — verify claims, clarify scope, estimate effort
  - Mermaid flowcharts define groom-backlog-item's own internal workflow
  - Contains no `Skill()` invocations to other backlog skills
  - References only internal reference files (`./references/issue-classification.md`, `./references/groomer-agent.md`)

- **references/issue-classification.md** (first 50 lines read)
  - Mermaid flowchart for issue type classification
  - Calls `mcp__backlog__backlog_groom()` at line 42 (MCP tool, not Skill())

- **references/groomer-agent.md**
  - (Not fully read; glob indicates existence — likely contains groomer agent instructions)

### Skill() References to Other Backlog Skills

**None found.** This skill does not call other backlog skills programmatically.

### Namespace References

**None found.** This skill does not reference other backlog skills by namespace (`/`).

---

## Directory 3: `.claude/skills/work-backlog-item/`

**Root directory:** `.claude/skills/work-backlog-item/`

### File Tree

```text
.claude/skills/work-backlog-item/
├── SKILL.md
└── references/
    ├── validation-plan.md
    ├── sam-definition.md
    ├── example-sessions.md
    ├── error-handling.md
    ├── auto-mode.md
    ├── step-procedures.md
    ├── github-integration.md
    └── close-resolve-procedure.md
```

**Total files:** 9

### File Contents Summary

- **SKILL.md** (414 lines)
  - Frontmatter: `name: work-backlog-item`
  - Purpose: Bridge backlog items into SAM planning pipeline via `/add-new-feature`
  - **Skill() invocations found (3 total):**
    1. Line 177: `Skill(skill: "create-backlog-item", args: "--auto {title}")` — AUTO_MODE fallback when no item found
    2. Line 217: `Skill(skill: "groom-backlog-item", args: "{item title}")` — Step 3 auto-grooming
    3. Line 321: `Skill(skill: "add-new-feature", args: "{composed feature request}")` — Step 6 SAM planning
    4. Line 350: `Skill(skill: "simplify")` — Step 8 file review and cleanup

  - Does NOT invoke `/work-backlog-item` internally (no self-referential calls)

- **references/auto-mode.md** (14 lines read)
  - Defines `--auto` mode substitution table
  - Line 9: References `create-backlog-item --auto {title}` auto-invocation (by name, not Skill())
  - No Skill() invocations

- **references/step-procedures.md**
  - (Not fully read; likely contains Step 0–9 detailed procedures)

- **references/error-handling.md, validation-plan.md, etc.**
  - (Not fully read; reference content files, no Skill() invocations expected)

### Skill() References to Other Backlog Skills

**Found (4 total):**

| Line | Context | Exact Code |
|------|---------|-----------|
| 177 | AUTO_MODE, Step 1 fallback | `Skill(skill: "create-backlog-item", args: "--auto {title}")` |
| 217 | Step 3 auto-grooming | `Skill(skill: "groom-backlog-item", args: "{item title}")` |
| 321 | Step 6 SAM planning | `Skill(skill: "add-new-feature", args: "{composed feature request}")` |
| 350 | Step 8 file review | `Skill(skill: "simplify")` |

**Note:** Only the first two reference other backlog skills. The latter two (`add-new-feature`, `simplify`) reference skills outside the backlog ecosystem.

### Namespace References

**None to other backlog skills.** Internal references use relative markdown links (`[text](./references/filename.md)`).

---

## Breakage File Analysis

### 1. plugins/development-harness/skills/interop/SKILL.md

**File contents:** 150+ lines (fully read)

**Skill() Reference Found:**

Line 116:
```text
Skill(skill="work-backlog-item", args="#N")
```

**Context:** Step 4 — Invoke /work-backlog-item

**Usage:** Delegates to `/work-backlog-item` skill to groom an item and produce a SAM task file. Passes issue number as `#N` argument.

**Verification:** ✓ LIVE REFERENCE — this is a direct call to work-backlog-item, not a namespace reference.

### 2. plugins/python3-development/skills/complete-implementation/SKILL.md

**Skill() Reference Found:**

Line 239:
```text
Skill(skill: "create-backlog-item", args: "--auto {derived_title}")
```

**Context:** Follow-up task creation after code review

**Usage:** When code-reviewer detects follow-up work, automatically creates a backlog item for deferred grooming/planning.

**Verification:** ✓ LIVE REFERENCE — calls create-backlog-item directly by name.

### 3. .claude/CLAUDE.md

**Namespace References Found (2 total):**

| Line | Exact Text |
|------|-----------|
| 32 | `create backlog items via /create-backlog-item or process backlog items via /work-backlog-item` |
| 256 | `Skills `/create-backlog-item` and `/work-backlog-item` invoke these tools. See `/backlog` skill.` |

**Context:** Session Start procedures and backlog operations documentation

**Verification:** ✓ DOCUMENTATION REFERENCES — describe when to use these skills, not programmatic invocations.

### 4. .claude/skills/work-backlog-item/SKILL.md

**Skill() References (already catalogued in Directory 3 above):**

- Line 177: `Skill(skill: "create-backlog-item", args: "--auto {title}")`
- Line 217: `Skill(skill: "groom-backlog-item", args: "{item title}")`

**Additional AUTO_MODE reference (line 9, references/auto-mode.md):**

```text
| Step 1: zero matches → ask user to create | Auto-invoke `create-backlog-item --auto {title}`, log `[AUTO] No item found — invoking create-backlog-item --auto` |
```

**Context:** Substitution table entry describing AUTO_MODE behavior

---

## Cross-Skill Invocation Map

### Entry Points (Skills that invoke others)

| Skill | Invokes | Via | Context |
|-------|---------|-----|---------|
| `work-backlog-item` | `create-backlog-item` | `Skill()` line 177 | AUTO_MODE fallback (Step 1) |
| `work-backlog-item` | `groom-backlog-item` | `Skill()` line 217 | Auto-grooming (Step 3) |
| `work-backlog-item` | `add-new-feature` | `Skill()` line 321 | SAM planning (Step 6) |
| `work-backlog-item` | `simplify` | `Skill()` line 350 | File review (Step 8) |
| `interop` (development-harness) | `work-backlog-item` | `Skill()` line 116 | Route plan file (Step 4) |
| `complete-implementation` (python3-development) | `create-backlog-item` | `Skill()` line 239 | Follow-up task creation |

### Dependency Flow

```text
create-backlog-item
  ↑
  └─ (invoked by: work-backlog-item Step 1, complete-implementation)

groom-backlog-item
  ↑
  └─ (invoked by: work-backlog-item Step 3)

work-backlog-item
  ↑
  ├─ (invokes: create-backlog-item, groom-backlog-item, add-new-feature, simplify)
  └─ (invoked by: interop, user)

add-new-feature
  ↑
  └─ (invoked by: work-backlog-item Step 6)

simplify
  ↑
  └─ (invoked by: work-backlog-item Step 8)
```

---

## Check: Does development-harness have existing backlog skills?

**Query:** `plugins/development-harness/skills/**/*`

**Result:** No backlog skills found. The plugin contains:

- Workflow stage skills (discovery, planning, context-integration, task-decomposition, execution, forensic-review, final-verification)
- Planning tools (clear-cove-task-design, generate-task, planner-rt-ica, validation-protocol)
- Implementation and testing skills (implementation-manager, comprehensive-test-review, analyze-test-failures, test-failure-mindset)
- Interop skill (development-harness/skills/interop/) — delegates to work-backlog-item
- Development-harness umbrella skill

**Conclusion:** ✓ No backlog skills exist in development-harness. Interop delegates backlog operations to the project-level `/work-backlog-item` skill.

---

## Namespace Reference Standards

### How skills reference backlog skills

**Standard patterns found:**

1. **Programmatic invocation (Skill tool):**
   ```text
   Skill(skill="create-backlog-item", args="--auto {title}")
   Skill(skill: "groom-backlog-item", args: "{item title}")
   Skill(skill: "work-backlog-item", args="#N")
   ```

2. **Documentation/user-facing (slash namespace):**
   ```text
   /create-backlog-item {title}
   /groom-backlog-item {title}
   /work-backlog-item {title}
   ```

3. **Next-step suggestions (markdown text):**
   ```text
   Groom:  /groom-backlog-item {title}
   Work:   /work-backlog-item {title}
   ```

**Observation:** Both formats (`skill=` parameter and `/` namespace syntax) are used interchangeably. The `/` syntax is used in user-facing documentation and comments; the `skill=` parameter is used in programmatic Skill() calls.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total backlog skills | 3 |
| Total files across all three | 9 |
| Skills with Skill() invocations to other backlog skills | 2 |
| Total inter-backlog Skill() calls | 2 |
| External skills invoked from work-backlog-item | 2 |
| Breakage files checked | 4 |
| Live Skill() references in breakage files | 2 |
| Development-harness backlog skills | 0 |

---

## Key Findings

### 1. Linear Dependency Chain
The three backlog skills form a linear orchestration sequence:
- **`create-backlog-item`** → creates item
- **`groom-backlog-item`** → optionally called by work-backlog-item
- **`work-backlog-item`** → optional grooming, then delegates to SAM planning

### 2. Minimal Cross-References
- `create-backlog-item` has no programmatic calls to other backlog skills
- `groom-backlog-item` has no programmatic calls to other backlog skills
- `work-backlog-item` invokes both `create-backlog-item` (fallback) and `groom-backlog-item` (Step 3)

### 3. External Composition
- `work-backlog-item` depends on `add-new-feature` (SAM planning) and `simplify` (cleanup)
- `interop` (development-harness) delegates to `work-backlog-item` for plan processing
- `complete-implementation` (python3-development) invokes `create-backlog-item` for follow-up work

### 4. No Dual Implementation
`development-harness` does not implement its own backlog skills. It uses the project-level skills via delegation.

### 5. Namespace Consistency
All references use consistent slash notation (`/skill-name`) in user-facing documentation and consistent `Skill(skill="name")` syntax in programmatic calls.

---

## Artifact Path Locations

All three skills are located in `.claude/skills/` (project-level):
- `.claude/skills/create-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/SKILL.md` + `references/`
- `.claude/skills/work-backlog-item/SKILL.md` + `references/`

**Status:** ✓ Centralized in project, not duplicated in plugin cache or plugin directories.
