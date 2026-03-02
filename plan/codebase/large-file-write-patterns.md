# Large File Write Patterns

**Analysis Date:** 2026-03-02
**Repository:** claude_skills

## Overview

This document maps the existing patterns, conventions, and constraints for large file writing by agents in this repository. It covers where agents write, what size guidance exists, how delegation instructions flow, and how hooks observe write operations.

---

## 1. Agent File Write Patterns

### Agents That Produce Large Output Files

#### `swarm-task-planner`

**Locations:**
- `/home/user/claude_skills/plugins/python3-development/agents/swarm-task-planner.md`
- `/home/user/claude_skills/plugins/development-harness/agents/swarm-task-planner.md`

**Output files produced:**
- `plan/tasks-{N}-{slug}.md` — monolithic task plan file
- `plan/tasks-{slug}/` directory — individual per-task `.md` files (optional)
- `TASK/` directory — per-task worker prompt files (optional, when explicitly requested)

**Size policy (from agent at line 168):** "Single file for plans <500 lines, progressive disclosure for >=500 lines."

```text
Single file pattern (PLAN.md for <500 lines):
  plan/tasks-{N}-{slug}.md  ← entire plan as one file

Progressive disclosure pattern (>=500 lines):
  PLAN/
  ├── index.md
  ├── priority-1-foundation.md
  ├── priority-2-core.md
  ├── priority-3-advanced.md
  └── sync-checkpoints.md
```

Each task inside a task plan file follows a YAML frontmatter + CLEAR-ordered body format that can be 30–80+ lines per task. A plan with 10–20 tasks is routinely 400–700+ lines.

**Revision policy:** Edit in-place — never create `PLAN_v2.md` or `PLAN_latest.md`. Bump YAML frontmatter `version:` field.

#### `feature-researcher`

**Location:** `/home/user/claude_skills/plugins/python3-development/agents/feature-researcher.md`

**Output files produced:**
- `plan/feature-context-{slug}.md` — structured discovery document

**Size:** Typically 100–250 lines (fixed-section format).

#### `python-cli-design-spec`

**Location:** `/home/user/claude_skills/plugins/python3-development/agents/python-cli-design-spec.md`

**Output files produced:**
- `plan/architect-{slug}.md` — architecture specification

**Size:** Typically 200–500+ lines depending on feature scope.

#### `codebase-analyzer`

**Location:** `/home/user/claude_skills/plugins/python3-development/agents/codebase-analyzer.md`

**Output files produced:**
- `plan/codebase/PATTERNS.md`
- `plan/codebase/ARCHITECTURE.md`
- `plan/codebase/TESTING.md`
- `plan/codebase/CONVENTIONS.md`
- `plan/codebase/CONCERNS.md`

**Size guidance in agent (at line 60):** "A 200-line TESTING.md with real patterns is more valuable than a 50-line summary." No upper bound is stated. Full exploration depth is prioritized.

#### `context-gathering`

**Location:** `/home/user/claude_skills/plugins/python3-development/agents/context-gathering.md`

**Output:** Inserts a `## Context Manifest` section into an existing task file (edit, not create).

#### `context-refinement`

**Location:** `/home/user/claude_skills/plugins/python3-development/agents/context-refinement.md`

**Output:** Updates Context Manifest in task file; appends plan artifact annotations. Mutates existing files.

---

## 2. Rules Structure: `.claude/rules/*.md`

### File Inventory

```text
.claude/rules/
├── ci-workflows.md
├── delegation-format.md
├── interactive-terminal-workarounds.md
├── language-conventions.md
├── linting-exceptions.md
├── local-workflow.md
├── plugin-development.md
├── script-invocation.md
├── silent-failure-prevention.md
├── skill-content-optimization.md
├── skill-documentation-verification.md
├── yaml-toml-libraries.md
```

### How Rules Are Loaded

Rules files are **not imported** programmatically. They are referenced in `CLAUDE.md` via the pattern:

```markdown
- Rule Name: `.claude/rules/rule-file.md`
```

Claude Code loads rule files matching `paths:` frontmatter globs. Each rule file carries a frontmatter block:

```yaml
---
paths:
  - "**/SKILL.md"
  - "**/references/*.md"
---
```

This makes the rule active whenever Claude Code opens a file matching those globs. When no `paths:` key is present, the rule file must be explicitly read.

**Observed examples:**

- `/home/user/claude_skills/.claude/rules/skill-content-optimization.md` (line 1–5): `paths: ["**/SKILL.md", "**/references/*.md"]`
- `/home/user/claude_skills/.claude/rules/plugin-development.md` (line 1–5): `paths: ["plugins/**/*", ".claude-plugin/**/*"]`

### Rule File Structure Convention

Each rules file:
- Starts with optional `paths:` frontmatter for auto-loading
- Uses a single `# Title` H1 heading
- Contains focused, imperative rules under `##` subheadings
- Targets under 500 lines (per skill-content-optimization.md:16)
- Uses code fences with language specifiers for all examples
- No temporal language; present-tense imperative only

---

## 3. Delegation Patterns

### Chain: CLAUDE.md → Skill → Agent → Sub-agent

The delegation chain is described in `/home/user/claude_skills/.claude/rules/local-workflow.md` and formalized in `/home/user/claude_skills/.claude/rules/delegation-format.md`.

**Key constraint from delegation-format.md:11-13:**
> The Agent tool is only available to the orchestrator — the main Claude Code context running the session. Subagents spawned via `subagent_type`, or skills loaded with `context: fork`, do NOT have the Agent tool and cannot delegate further.

**Delegation instruction format** (delegation-format.md:38-46):

```text
N. Task is [description] with subagent_type="plugin:agent-name"
   Context to include in the prompt: [specific file paths, artifacts, or data to pass]
   Output: [specific artifact the agent produces — file path, format, content]
```

### How `/add-new-feature` Delegates File Production

From `/home/user/claude_skills/.claude/skills/add-new-feature/SKILL.md`:

```text
Phase 1 → feature-researcher      → plan/feature-context-{slug}.md
Phase 2 → codebase-analyzer       → plan/codebase/{FOCUS}.md
Phase 3 → python-cli-design-spec  → plan/architect-{slug}.md
Phase 4 → swarm-task-planner      → plan/tasks-{N}-{slug}.md
Phase 5 → plan-validator          → PASS/BLOCKED gate (no file output)
Phase 6 → context-gathering       → mutates task file (inserts Context Manifest)
```

Each phase agent receives file paths in its prompt — not file contents. This is explicitly stated in `CLAUDE.md` line 55: "Pass file paths to agents — transcribing file contents into prompts bypasses agent verification."

### Where Sub-agents Write Files

Sub-agents write output files directly using the `Write` tool. The orchestrator does not re-write or validate content; it passes artifact paths forward to the next phase.

The `Write` tool schema (from hooks-guide/references/claude-code.md:280-285):

```text
Write
  file_path: string  — absolute path to file
  content:   string  — content to write
```

No size constraint is documented in the tool schema. The tool performs a full overwrite atomically.

---

## 4. Hook Infrastructure

### Hook Types That Exist

From `/home/user/claude_skills/plugins/plugin-creator/skills/hooks-guide/references/claude-code.md`:

| Event | When It Fires | Can Block? |
|---|---|---|
| `PreToolUse` | Before a tool call executes | Yes |
| `PostToolUse` | After a tool call succeeds | No |
| `SubagentStop` | When a subagent finishes | Yes |
| `SubagentStart` | When a subagent is spawned | No |
| `SessionStart` | Session begins or resumes | No |
| `Stop` | When Claude finishes responding | Yes |
| `TaskCompleted` | When a task is marked complete | Yes |

Hook types: `"command"` (shell command), `"prompt"` (LLM evaluation), `"agent"` (subagent with tool access).

### How Hooks Are Configured

Three configuration locations are used in this repo:

**1. Skill frontmatter** — active while skill is loaded:

```yaml
# From .claude/skills/implement-feature/SKILL.md:6-11
hooks:
  SubagentStop:
  - hooks:
    - type: command
      command: python3 "./plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py"
```

```yaml
# From .claude/skills/start-task/SKILL.md:6-12
hooks:
  PostToolUse:
  - matcher: Write|Edit|Bash
    hooks:
    - type: command
      command: python3 "./plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py"
```

**2. Plugin `hooks/hooks.json`** — auto-discovered when plugin is enabled.

**3. Settings files** — `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`.

### What the Hook Script Does on Write

The hook script at `/home/user/claude_skills/plugins/python3-development/skills/implementation-manager/scripts/task_status_hook.py` handles two events:

- **`SubagentStop`**: Parses the sub-agent prompt for `/start-task` invocation, extracts task file path and task ID, marks task `COMPLETE`, adds `Completed` timestamp, deletes context file.
- **`PostToolUse` on `Write|Edit|Bash`**: Reads `.claude/context/active-task-{session_id}.json`, updates `LastActivity` timestamp in the task file.

The hook **observes** write operations but does not **intercept** or **modify** what is written. The `PostToolUse` event cannot block (hook-code.md:163: "No — Shows stderr to Claude (tool already ran)").

The hook uses `Path.write_text()` for its own file updates — a full replacement of the task file content on each timestamp update (task_status_hook.py:516, 560-562).

---

## 5. Existing File Size Guidance

### Skill Body Tokens (plugin_validator.py)

The definitive thresholds are set in `/home/user/claude_skills/plugins/plugin-creator/scripts/plugin_validator.py`:

```python
TOKEN_WARNING_THRESHOLD = 4400   # SK006 — extract to references/
TOKEN_ERROR_THRESHOLD   = 8800   # SK007 — must split skill
```

These govern skill SKILL.md files, not agent output files or plan artifacts.

**What SK006/SK007 trigger:**
- SK006 (>4400 tokens): Warning — extract content to `references/` subdirectory
- SK007 (>8800 tokens): Critical — must split into multiple skills via `/refactor-skill`

### Plan File Size (swarm-task-planner)

From `plugins/python3-development/agents/swarm-task-planner.md:168`:

```text
Rule: Single file for plans <500 lines, progressive disclosure for >=500 lines
```

This is the only explicit line-count guidance for agent-produced plan files. The 500-line threshold triggers progressive disclosure (directory structure instead of monolithic file).

### Content Optimization (skill-content-optimization.md)

From `/home/user/claude_skills/.claude/rules/skill-content-optimization.md:16`:

```text
Target under 500 lines per file
```

This applies to SKILL.md and `references/*.md` files (as scoped by the `paths:` frontmatter).

### No Invented Limits (CLAUDE.md)

From `/home/user/claude_skills/.claude/CLAUDE.md:9-23`:

```text
Never introduce hard-coded truncation or length limits on content that a consumer
(human or agent) needs to read. Arbitrary limits (e.g., `[:500]`, `[:200]`,
`MAX_LEN = 1024`) remove the consumer's ability to control what they read...

Output full content by default — let the caller decide how much to read.
```

This rule applies to CLI output, JSON fields, error messages, and issue bodies. It prohibits truncation in agent-produced text output. It does not address splitting files into multiple parts.

### Read Tool Pagination

The `Read` tool supports `offset` and `limit` parameters (hooks-guide/references/claude-code.md:296-300). This provides post-hoc access control when a file is already large, but does not prevent large writes.

### No Write Tool Size Limit Documented

No maximum content size is documented for the `Write` tool in any file examined. The tool schema only specifies `file_path` (string) and `content` (string) — no size constraint appears.

---

## 6. Cross-Cutting Observations

### Pattern: Agents Write Full File, Hooks Mutate

Agents produce files in a single `Write` call. Post-write mutation (timestamp updates, status changes, manifest insertions) is done by hook scripts or a subsequent agent that reads then writes back the full content.

The `task_status_hook.py` pattern (lines 511-516):

```python
updated_content = update_task_status(content, task_id, "✅ COMPLETE")
updated_content = add_timestamp_to_task(updated_content, task_id, "Completed", timestamp)
resolved_path.write_text(updated_content, encoding="utf-8")
```

Every hook-triggered update rewrites the entire file — there is no append-only or partial-write path.

### Pattern: File Paths Passed, Not Contents

Delegation instructions pass file paths. The sub-agent reads the file itself. Example from local-workflow.md:

> "Pass file paths to agents — transcribing file contents into prompts bypasses agent verification."

This means the delegated agent controls read granularity (can use `offset`/`limit`), but must write the full file on output.

### Pattern: Two Task File Formats Coexist

The hook script (`task_status_hook.py:8-9`) and implementation manager support:

1. **YAML frontmatter** — individual `.md` files or monolithic files with `---` delimiters; fields are `snake_case`
2. **Legacy markdown** — monolithic file with `## Task N:` headers; fields are `**PascalCase**:` bold lines

Both formats are written in full on every update. No partial-field update path exists — the full file is read, mutated, and rewritten.

### Pattern: Progressive Disclosure for Plans ≥500 Lines

When a task plan would exceed 500 lines, `swarm-task-planner` splits it into a `PLAN/` directory:

```text
PLAN/
├── index.md               ← manifest of tasks
├── priority-1-foundation.md
├── priority-2-core.md
├── priority-3-advanced.md
└── sync-checkpoints.md
```

The `implementation_manager.py` script handles discovery of both layouts via `discover_plan_directory()`.

### Pattern: Same-File Conflict Avoidance

`swarm-task-planner` enforces a same-file conflict check at Phase 5 (line 497-500):

```text
For each Expected Output file path, count how many tasks list it.
If count > 1 and tasks are not dependency-chained: MERGE required.
```

This prevents two parallel agents from writing to the same file concurrently. The preferred resolution is task merging; chaining via dependencies is the alternative.

---

## 7. Summary: Guidance by Artifact Type

| Artifact Type | Size Guidance | Split Strategy | Enforced By |
|---|---|---|---|
| Skill SKILL.md body | >4400 tokens: SK006; >8800: SK007 (must split) | Extract to `references/`; split into multiple skills | `plugin_validator.py` |
| Plan task file (`plan/tasks-*.md`) | <500 lines: single file; >=500: `PLAN/` directory | Directory split with `index.md` | Agent rule in `swarm-task-planner.md:168` |
| Rules files (`.claude/rules/*.md`) | Target <500 lines | Split into composable rules files | `skill-content-optimization.md:16` |
| Plan artifacts (feature-context, architect) | No explicit limit | Not prescribed | None |
| Codebase analysis (`plan/codebase/*.md`) | "200-line with patterns > 50-line summary" (minimum quality) | Not prescribed | Agent guidance in `codebase-analyzer.md:60` |
| Write tool content | No documented limit | N/A | Not enforced |

---

*Analysis based on direct file reads: 2026-03-02*
