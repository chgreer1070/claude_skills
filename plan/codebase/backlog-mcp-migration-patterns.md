# Backlog CLI-to-MCP Migration Patterns

**Analysis Date:** 2026-03-02
**Package:** backlog / backlog_core
**Source files analyzed:**
- `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`
- `.claude/skills/backlog/backlog_core/server.py`
- `.claude/skills/work-backlog-item/SKILL.md`
- `.claude/skills/create-backlog-item/SKILL.md`
- `.claude/skills/groom-backlog-item/SKILL.md`
- `.claude/skills/backlog/SKILL.md`
- `.claude/hooks/stop-backlog-reminder.cjs`
- `.claude/agents/backlog-item-groomer.md`
- `.claude/agents/backlog-mcp-validator.md`
- `.claude/CLAUDE.md` (Backlog Operations section)
- `.mcp.json`

---

## 1. Current CLI Invocation Patterns

### Base Command Form

All CLI calls follow the same base pattern:

```bash
uv run .claude/skills/backlog/scripts/backlog.py <subcommand> [args] -R Jamie-BitFlight/claude_skills
```

The `-R Jamie-BitFlight/claude_skills` flag is appended to every invocation that touches GitHub. It is always the last argument.

### Invocation Locations by File

**`.claude/skills/work-backlog-item/SKILL.md`** — 19 CLI calls. Patterns observed:

```bash
# List all items (Step 0, Step 1)
uv run .claude/skills/backlog/scripts/backlog.py list --format json --with-status -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py list --format json -R Jamie-BitFlight/claude_skills

# View single item by selector (Step 1b, Step 9a, Step 2.5)
uv run .claude/skills/backlog/scripts/backlog.py view "{$0}" --format json -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py view "{$1}" --format json -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py view "#{issue_number}" --format json -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py view "#{N}" --format json -R Jamie-BitFlight/claude_skills

# Close item (Step 9f)
uv run .claude/skills/backlog/scripts/backlog.py close "{title}" --plan "{plan file path}" --checklist-pass -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py close "#{N}" --plan "{plan file path}" --checklist-pass -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py close "{title}" --reason "Already implemented via commit {sha}" -R Jamie-BitFlight/claude_skills

# Resolve item (Step 9b)
uv run .claude/skills/backlog/scripts/backlog.py resolve "{title or #N}" --reason "{reason}" -R Jamie-BitFlight/claude_skills

# Update item — plan, status, create-issue (Step 7, Step 2.7, Step 2.5a)
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --plan "plan/tasks-{N}-{slug}.md" -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --status in-progress -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --create-issue -R Jamie-BitFlight/claude_skills
```

Source: `.claude/skills/work-backlog-item/SKILL.md` lines 97, 155, 195, 233, 301, 419, 453, 473, 566, 584, 590, 641, 650, 660, 685.

**`.claude/skills/create-backlog-item/SKILL.md`** — 1 CLI call (Step 5):

```bash
uv run .claude/skills/backlog/scripts/backlog.py add \
  --title "{title}" \
  --priority "{priority}" \
  --description "{description}" \
  --source "{source}" \
  --type "{type}" \
  -R Jamie-BitFlight/claude_skills
```

With optional append: `--research-first "{research_first}"`. The `--no-create-issue` flag is conditionally appended for P2/Ideas or when user declines. Source: `.claude/skills/create-backlog-item/SKILL.md` lines 163–169.

**`.claude/skills/groom-backlog-item/SKILL.md`** — 6 CLI calls:

```bash
# Step 1: load backlog
uv run .claude/skills/backlog/scripts/backlog.py list --format json

# Step 2: validity check — stale item gate
uv run .claude/skills/backlog/scripts/backlog.py view "#{N}" --format json -R Jamie-BitFlight/claude_skills

# Step 2: close already-implemented items
uv run .claude/skills/backlog/scripts/backlog.py close "{title}" --reason "Already implemented via PR #{pr} / commit {sha}" -R Jamie-BitFlight/claude_skills

# Step 7: recurring-pattern measurement
uv run .claude/skills/backlog/scripts/backlog.py list --format json --status resolved

# Step 9: incremental groomed content write
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --section "..." --content "..."

# Step 9: pre-use signature check (guard against wrong subcommand)
uv run .claude/skills/backlog/scripts/backlog.py <subcommand> --help
```

Source: `.claude/skills/groom-backlog-item/SKILL.md` lines 25, 65, 71, 94, 195, 198.

**`.claude/skills/work-backlog-item/references/step-procedures.md`** — 2 CLI calls:

```bash
uv run .claude/skills/backlog/scripts/backlog.py list --format json --with-status -R Jamie-BitFlight/claude_skills
uv run .claude/skills/backlog/scripts/backlog.py update "{title}" --plan "plan/quick/{slug}.md" -R Jamie-BitFlight/claude_skills
```

Source: `.claude/skills/work-backlog-item/references/step-procedures.md` lines 12, 117.

### Invocation Context Format

CLI calls in skill SKILL.md files appear inside fenced bash code blocks within numbered procedural steps. They are always presented as the literal command to run. The surrounding prose names the step number (e.g., "Step 1", "Step 9f") and describes what to do with the output.

```text
### Step 0: Interactive Browser

1. Invoke the backlog script to list items with status:

   ```bash
   uv run .claude/skills/backlog/scripts/backlog.py list --format json --with-status -R Jamie-BitFlight/claude_skills
   ```

   Parse the JSON output. Each entry has `section`, `title`, `issue`, `plan`, `status`, ...
```

This is the universal format: bash code block containing the exact command, followed by prose describing how to interpret the output. Source: `.claude/skills/work-backlog-item/SKILL.md:94-100`.

---

## 2. MCP Tool Call Patterns

### Server Registration

The backlog MCP server is registered in **two places**:

**`.mcp.json`** (project-level, no `cwd`):

```json
{
  "mcpServers": {
    "backlog": {
      "command": "uv",
      "args": ["run", "python", "-m", "backlog_core.server"]
    }
  }
}
```

Source: `.mcp.json` lines 25–29. Note: No `cwd` is specified here — the server relies on the shell's working directory when invoked.

**Agent frontmatter** (`.claude/agents/backlog-item-groomer.md` and `.claude/agents/backlog-mcp-validator.md`):

```yaml
mcpServers:
  backlog:
    command: uv
    args:
      - run
      - python
      - -m
      - backlog_core.server
    cwd: .claude/skills/backlog
```

Source: `.claude/agents/backlog-item-groomer.md` lines 7–15, `.claude/agents/backlog-mcp-validator.md` lines 7–15. Agent-level registration includes `cwd: .claude/skills/backlog`, which the project-level `.mcp.json` entry lacks.

### Tool Access Naming Convention

In agent `tools` frontmatter fields, MCP tools are listed with the `mcp__<server>__<tool>` naming pattern:

```yaml
tools: Glob, Grep, Read, mcp__backlog__backlog_list, mcp__backlog__backlog_view, mcp__backlog__backlog_add, mcp__backlog__backlog_update, mcp__backlog__backlog_groom, mcp__backlog__backlog_close, mcp__backlog__backlog_resolve, mcp__backlog__backlog_sync, mcp__backlog__backlog_normalize, mcp__backlog__backlog_pull
```

Source: `.claude/agents/backlog-item-groomer.md` line 4, `.claude/agents/backlog-mcp-validator.md` line 5.

The `mcp__backlog__*` prefix is the naming convention for all 10 backlog tools when referenced in agent tool lists.

### Tool Call Syntax in Agent Files

The `backlog-mcp-validator.md` agent documents native MCP tool call syntax in prose code blocks:

```text
mcp__backlog__backlog_add(title="test", priority="P2", description="test", create_issue=false)
mcp__backlog__backlog_list()
mcp__backlog__backlog_view(selector="test")
mcp__backlog__backlog_sync(dry_run=true)
mcp__backlog__backlog_close(selector="test", plan="test", checklist_pass=true)
mcp__backlog__backlog_resolve(selector="test", reason="test")
mcp__backlog__backlog_update(selector="test", status="in-progress")
mcp__backlog__backlog_groom(selector="test", section="Test", content="test content")
mcp__backlog__backlog_normalize(dry_run=true)
mcp__backlog__backlog_pull(dry_run=true)
```

Source: `.claude/agents/backlog-mcp-validator.md` lines 172–182.

### MCP Tool Call Reference (from backlog-item-groomer)

The `backlog-item-groomer` agent uses MCP tools with parenthetical notation referencing the `mcp__backlog__*` qualifier:

```text
Call the `backlog_list` MCP tool (via `mcp__backlog__backlog_list`) to get all backlog items.
```

Source: `.claude/agents/backlog-item-groomer.md` line 88.

### Current State: Only Agents Use MCP Tools

No SKILL.md file currently instructs the orchestrator to call MCP tools directly. The two agents that use MCP tools are:

- `.claude/agents/backlog-item-groomer.md` — has `mcpServers` frontmatter + `mcp__backlog__*` in `tools`
- `.claude/agents/backlog-mcp-validator.md` — has `mcpServers` frontmatter + `mcp__backlog__*` in `tools`, uses native MCP calls exclusively (no Bash/Read/Write/Edit allowed)

The `.claude/settings.json` `permissions.allow` list includes `"mcp__backlog__*"` (line 13), confirming project-level MCP tool access is pre-authorized.

---

## 3. Skill Instruction Format

### How SKILL.md Files Instruct Operations

SKILL.md files use **bash code blocks within prose steps** to instruct the orchestrator to perform backlog operations. The format is consistent across all three backlog-related skills.

**Pattern:**

```text
### Step N: [Step Name]

[Prose describing the action and why]

```bash
uv run .claude/skills/backlog/scripts/backlog.py <subcommand> [args] -R Jamie-BitFlight/claude_skills
```

[Prose describing how to handle the output or what to do next]
```

**No inline `Bash(...)` tool calls are used in SKILL.md files.** Instructions are written as literal shell commands in fenced bash blocks, which the orchestrator running the skill executes using its Bash tool.

**Conditional command construction** is described in prose with conditional markers:

```text
- If priority is P0 or P1 and ... do NOT add `--no-create-issue` (script creates issue by default).
- If priority is P2 or Idea: add `--no-create-issue`.
```

Source: `.claude/skills/create-backlog-item/SKILL.md` lines 176–179.

**Inline prose invocations** (non-bash) use `Skill(skill: "...", args: "...")` notation for skill delegation:

```text
Skill(skill: "groom-backlog-item", args: "{item title}")
```

Source: `.claude/skills/work-backlog-item/SKILL.md` line 319.

**Agent delegation** in skills uses `Agent(subagent_type: "...", prompt: "...")` notation:

```text
Agent(
  description: "Groom backlog item",
  subagent_type: "backlog-item-groomer",
  prompt: "..."
)
```

Source: `.claude/skills/groom-backlog-item/SKILL.md` lines 251–257.

### Backlog Subcommand Documentation Style in SKILL.md

`groom-backlog-item/SKILL.md` uses a shortened form without `uv run` prefix in prose descriptions (Step 9 section header annotations):

```text
backlog groom "{item title}" --section "Fact-Check" --content "{fact-check summary}"
```

Source: `.claude/skills/groom-backlog-item/SKILL.md` lines 294–303. This is a prose shorthand used in annotation blocks, not a runnable command. All actually-runnable commands use the full `uv run .claude/skills/backlog/scripts/backlog.py` prefix.

---

## 4. Hook Files

### `.claude/hooks/stop-backlog-reminder.cjs`

**Location:** `/home/user/claude_skills/.claude/hooks/stop-backlog-reminder.cjs`

**Trigger:** Stop hook — runs at end of session.

**Content:**

```javascript
const output = {
  additionalContext: `<backlog-reminder>
New ideas or deferred work discovered this session? → Skill(skill: "create-backlog-item", args: "--auto {title}") to add and track.
Completed items? → Skill(skill: "work-backlog-item", args: "close {title}") to verify and close.
</backlog-reminder>`,
};

console.log(JSON.stringify(output));
```

Source: `.claude/hooks/stop-backlog-reminder.cjs` lines 7–11.

**Pattern:** Uses `Skill(skill: "...", args: "...")` notation — references the skill names `create-backlog-item` and `work-backlog-item`. Does not reference `backlog.py` or MCP tool names directly. The hook injects `additionalContext` into the session via `JSON.stringify(output)`.

**No `session-start-backlog.cjs` exists.** A search for `session-start-backlog` returns references in documentation and backlog items (e.g., `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md` mentions it at line 72), but the file itself is not present at `.claude/hooks/`. The `.claude/settings.json` does not register a SessionStart hook for backlog — only a Setup hook (`run-commands-try-all.cjs`). The migration map entry describing `session-start-backlog.cjs` refers to a file that does not currently exist.

---

## 5. MCP Server Tool Signatures

All tools are defined in `.claude/skills/backlog/backlog_core/server.py`. All return `dict`. On success, the dict contains result keys plus optional `messages: list[str]` and `warnings: list[str]`. On error, the dict contains `"error": str`.

### `backlog_add`

```python
def backlog_add(
    title: str,                      # required — Item title
    priority: str,                   # required — "P0" | "P1" | "P2" | "Ideas"
    description: str,                # required — Item description
    source: str = "Not specified",   # optional — Where this item came from
    type_: str = "Feature",          # optional — alias "type"; "Feature"|"Bug"|"Refactor"|"Docs"|"Chore"
    create_issue: bool = True,       # optional — Create GitHub issue
    force: bool = False,             # optional — Skip fuzzy duplicate check
) -> dict
# Returns: {file_path, title, priority, issue (if created), messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 17–51. The `type_` parameter has `alias="type"` in the Pydantic Field — callers pass `type`, not `type_`.

### `backlog_list`

```python
def backlog_list(
    with_status: bool = False,       # optional — Include GitHub issue status per item
    from_github: bool = False,       # optional — Refresh local cache from GitHub first
    label: str | None = None,        # optional — Filter by GitHub label
    section: str | None = None,      # optional — Filter by priority: P0, P1, P2, Ideas
    status: str | None = None,       # optional — Filter by status value (e.g. "needs-grooming")
    title: str | None = None,        # optional — Filter by title substring (case-insensitive)
) -> dict
# Returns: {items: [{title, priority, issue, plan}], messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 54–94. Note: The `section`, `status`, and `title` filter parameters are present in `server.py` but are NOT listed in the `backlog-mcp-validator.md` tool reference (which only lists `with_status`, `from_github`, `label`). This is a documentation gap in the validator agent.

### `backlog_view`

```python
def backlog_view(
    selector: str,                   # required — URL | "#N" | bare number | title substring
    offset: int = 0,                 # optional — Skip N lines from body (pagination)
    limit: int = 0,                  # optional — Max body lines to return (0 = all)
) -> dict
# Returns: {title, priority, issue, plan, file_path, body, groomed, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 97–118.

### `backlog_sync`

```python
def backlog_sync(
    dry_run: bool = False,           # optional — Preview without making changes
) -> dict
# Returns: {created, pushed, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 121–138.

### `backlog_close`

```python
def backlog_close(
    selector: str,                   # required — title substring | "#N" | bare number | URL
    plan: str,                       # required — Plan path or completion summary
    checklist_pass: bool = False,    # optional — MUST be true to close
    cleanup: bool = False,           # optional — Remove local file after close
    force: bool = False,             # optional — Close even with open PRs
) -> dict
# Returns: {title, issue (if present), messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 141–170.

### `backlog_resolve`

```python
def backlog_resolve(
    selector: str,                   # required — title substring | "#N" | bare number | URL
    reason: str,                     # required — Reason for resolving
    cleanup: bool = False,           # optional — Remove local file after resolve
    force: bool = False,             # optional — Resolve even with open PRs
) -> dict
# Returns: {title, reason, issue (if present), messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 173–198.

### `backlog_update`

```python
def backlog_update(
    selector: str,                           # required — title substring | "#N" | bare number | URL
    plan: str | None = None,                 # optional — Plan file path to attach
    status: str | None = None,              # optional — e.g. "in-progress"
    create_issue: bool = False,              # optional — Create GitHub issue if missing (P0/P1 only)
    groomed_content: str | None = None,     # optional — Full groomed content (replaces groomed section)
    section: str | None = None,             # optional — Section name for incremental update
    content: str | None = None,             # optional — Content for named section
    title: str | None = None,               # optional — New title for the item
    description: str | None = None,         # optional — New description text
) -> dict
# Returns: {title, changes, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 201–263.

**CLI-only parameters not exposed via MCP:** `groomed_file: str | None` and `groomed: bool` exist on `operations.update_item()` but are absent from the MCP tool wrapper. Source: `.claude/skills/backlog/backlog_core/DOCUMENTATION_DRIFT_AUDIT.md` FIND-10.

### `backlog_groom`

```python
def backlog_groom(
    selector: str,                           # required — title substring | "#N" | bare number | URL
    groomed_content: str | None = None,     # optional — Full groomed content (replaces groomed section)
    section: str | None = None,             # optional — Section name for incremental update
    content: str | None = None,             # optional — Content for named section
) -> dict
# Returns: {title, synced, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 266–297.

**CLI-only parameter not exposed via MCP:** `groomed_file: str | None` exists on `operations.groom_item()` but is absent from the MCP tool wrapper. Source: DOCUMENTATION_DRIFT_AUDIT.md FIND-11.

### `backlog_normalize`

```python
def backlog_normalize(
    dry_run: bool = False,           # optional — Preview without modifying files
) -> dict
# Returns: {normalized, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 300–318.

### `backlog_pull`

```python
def backlog_pull(
    dry_run: bool = False,           # optional — Preview without modifying local files
    force: bool = False,             # optional — Overwrite even if local version is newer
) -> dict
# Returns: {pulled, messages, warnings}
```

Source: `.claude/skills/backlog/backlog_core/server.py` lines 321–343.

---

## 6. CLI-to-MCP Parameter Mapping

The complete mapping from CLI flags to MCP parameters (sourced from `.claude/skills/backlog/CLI_TO_MCP_MIGRATION.md`):

| CLI Subcommand + Flag | MCP Tool + Parameter |
|---|---|
| `backlog add --title X` | `backlog_add(title=X)` |
| `backlog add --priority P1` | `backlog_add(priority="P1")` |
| `backlog add --description D` | `backlog_add(description=D)` |
| `backlog add --source S` | `backlog_add(source=S)` |
| `backlog add --type T` | `backlog_add(type=T)` |
| `backlog add --create-issue` | `backlog_add(create_issue=True)` |
| `backlog add --no-create-issue` | `backlog_add(create_issue=False)` |
| `backlog list --format json` | `backlog_list()` |
| `backlog list --with-status` | `backlog_list(with_status=True)` |
| `backlog view "<selector>" --format json` | `backlog_view(selector="<selector>")` |
| `backlog sync --dry-run` | `backlog_sync(dry_run=True)` |
| `backlog close "<title>" --plan PATH --checklist-pass` | `backlog_close(selector="<title>", plan=PATH, checklist_pass=True)` |
| `backlog close "<title>" --reason "..."` | N/A — use `backlog_resolve` for reason-based closes |
| `backlog resolve "<title>" --reason "..."` | `backlog_resolve(selector="<title>", reason="...")` |
| `backlog update "<title>" --plan PATH` | `backlog_update(selector="<title>", plan=PATH)` |
| `backlog update "<title>" --status in-progress` | `backlog_update(selector="<title>", status="in-progress")` |
| `backlog update "<title>" --create-issue` | `backlog_update(selector="<title>", create_issue=True)` |
| `backlog update "<title>" --section S --content C` | `backlog_update(selector="<title>", section=S, content=C)` |
| `backlog groom "<title>" --section S --content C` | `backlog_groom(selector="<title>", section=S, content=C)` |
| `backlog groom "<title>" --groomed-content BODY` | `backlog_groom(selector="<title>", groomed_content=BODY)` |
| `-R Jamie-BitFlight/claude_skills` | N/A — MCP server uses `DEFAULT_REPO` constant |

---

## 7. CLAUDE.md Backlog Operations Section

Current policy in `.claude/CLAUDE.md` (lines 214–220, under `### Backlog Operations`):

```bash
uv run .claude/skills/backlog/scripts/backlog.py add|list|sync|close|resolve|update ...
```

The policy states: "**Single interface**: Use `.claude/skills/backlog/scripts/backlog.py` for all backlog and GitHub issue CRUD. GitHub Issues are the source of truth; `.claude/backlog/` per-item files are the local cache. Editing per-item files directly or using `gh` for issue CRUD bypasses sync logic — use the script."

This is the authoritative policy document that all agents read. It currently mandates CLI-only usage. Source: `.claude/CLAUDE.md` Backlog Operations section.

---

## 8. Migration Status Summary

| Component | Current Interface | MCP Ready |
|---|---|---|
| `.mcp.json` | registered | yes — server entry exists, no `cwd` |
| `.claude/settings.json` permissions | `mcp__backlog__*` allowed | yes |
| `.claude/agents/backlog-item-groomer.md` | MCP tools | yes — migrated |
| `.claude/agents/backlog-mcp-validator.md` | MCP tools only | yes — migrated |
| `.claude/skills/work-backlog-item/SKILL.md` | CLI (19 calls) | no |
| `.claude/skills/create-backlog-item/SKILL.md` | CLI (1 call) | no |
| `.claude/skills/groom-backlog-item/SKILL.md` | CLI (6 calls) | no |
| `.claude/skills/backlog/SKILL.md` | CLI documentation | no |
| `.claude/hooks/stop-backlog-reminder.cjs` | Skill references (no direct CLI) | N/A — no change needed |
| session-start-backlog.cjs | does not exist | N/A |
| `.claude/CLAUDE.md` policy | CLI mandate | no |
| `.github/workflows/backlog-sync.yml` | CLI (keep as-is) | CI stays CLI |

---

## 9. Constraints and Observations

### `cwd` Discrepancy

The project-level `.mcp.json` entry for `backlog` has no `cwd` field. Agent frontmatter entries include `cwd: .claude/skills/backlog`. Without `cwd`, the server command `uv run python -m backlog_core.server` must be run from the repository root where `.claude/skills/backlog/` is a reachable path. The agent-level `cwd` is the authoritative safe form. Source: `.mcp.json` line 25–29 vs `.claude/agents/backlog-item-groomer.md` lines 7–15.

### `--help` Guard in groom-backlog-item

`groom-backlog-item/SKILL.md` line 276 instructs the orchestrator to verify subcommand signatures with `--help` before using an unfamiliar subcommand. This guard is a CLI-specific safety pattern (`sync` vs `update` vs `groom` have different argument shapes). MCP tools do not need this guard since their schemas are fixed and declared via Pydantic `Field` annotations.

### CLI-Only Parameters

Two parameters in `operations.py` are not exposed via MCP:
- `update_item(groomed_file=..., groomed: bool=...)` — file-path and stdin reading
- `groom_item(groomed_file=...)` — file-path reading

These are CLI-only. MCP callers must provide content inline as strings. Source: DOCUMENTATION_DRIFT_AUDIT.md FIND-10 and FIND-11.

### `backlog_list` Filtering Parameters

The server exposes `section`, `status`, and `title` filter parameters on `backlog_list` that the CLI migration map does not document (the CLI migration map only maps `--format json` and `--with-status`). Source: `server.py` lines 59–68.

### Return Shape

Every tool returns a `dict`. The key `"error"` appears on failure. The keys `"messages"` and `"warnings"` are always lists (empty if nothing to report). Result data keys vary per tool (see signatures above). This is the contract that all callers must check. Source: `server.py` entire file; error pattern at lines 50–51, 93–94, etc.

---

*Analysis: 2026-03-02*
