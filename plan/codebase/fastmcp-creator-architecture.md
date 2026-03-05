# fastmcp-creator Plugin Architecture

**Analysis Date:** 2026-03-05
**Plugin:** `fastmcp-creator`
**Plugin version:** 2.4.3 (from `plugins/fastmcp-creator/.claude-plugin/plugin.json`)

---

## 1. Plugin Directory Layout

```text
plugins/fastmcp-creator/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest (name, description, version, author)
│   └── validator.json       # Validator rule overrides (SK006 suppressed)
├── assets/
│   └── hero.png             # Marketplace display image
├── README.md                # Human-facing README
└── skills/
    ├── fastmcp-creator/     # Primary skill — MCP server development
    │   ├── SKILL.md         # 729-line skill body; exceeds SK006 threshold (suppressed)
    │   ├── references/      # 9 reference files (knowledge base)
    │   │   ├── accessing_online_resources.md
    │   │   ├── claude-code-mcp-integration.md
    │   │   ├── community-practices.md
    │   │   ├── development-guidelines.md
    │   │   ├── evaluation-guide.md
    │   │   ├── example-projects.md
    │   │   ├── mcp-best-practices.md
    │   │   ├── prompts-and-templates.md
    │   │   └── typescript-mcp-server.md
    │   └── scripts/         # Evaluation harness (shipped with the skill)
    │       ├── connections.py
    │       ├── evaluation.py
    │       ├── example_evaluation.xml
    │       ├── get_environment.py
    │       └── requirements.txt
    ├── fastmcp-client-cli/  # Thin skill — fastmcp list/call CLI reference
    │   └── SKILL.md
    └── fastmcp-python-tests/ # Thin skill — pytest patterns for FastMCP servers
        └── SKILL.md
```

**Key observation:** This plugin has NO `agents/` directory, NO `hooks/` directory, and NO `mcpServers` field. It is purely skill-based. The three skills are independent and load-on-demand — no auto-bundling.

---

## 2. plugin.json Structure

**File:** `plugins/fastmcp-creator/.claude-plugin/plugin.json`

```json
{
  "name": "fastmcp-creator",
  "description": "Build Model Context Protocol (MCP) servers...",
  "version": "2.4.3",
  "author": {
    "name": "Jamie Nelson",
    "url": "https://github.com/bitflight-devops"
  }
}
```

**Fields present:** `name`, `description`, `version`, `author`

**Fields absent:** `mcpServers`, `agents`, `skills`, `hooks`, `keywords`, `license`

Skills are auto-discovered from `skills/*/SKILL.md` — no explicit `skills` field means auto-discovery mode is active (SK009 does not trigger).

---

## 3. validator.json — Rule Suppression

**File:** `plugins/fastmcp-creator/.claude-plugin/validator.json`

```json
{
  "ignore": {
    "skills/fastmcp-creator": ["SK006"]
  }
}
```

SK006 is the warning threshold (body tokens > `TOKEN_WARNING_THRESHOLD` = 4400). The `fastmcp-creator` SKILL.md is intentionally large (comprehensive reference) and the SK006 warning is suppressed via this file. SK007 (error threshold = 8800 tokens) is NOT suppressed — if the skill were to grow beyond 8800 body tokens it would fail validation.

---

## 4. Skill Structure and Frontmatter

All three skills follow the same frontmatter pattern:

```yaml
---
name: <skill-name>        # lowercase-hyphens only (SK001/SK002/SK003 enforced)
description: <text>       # Must have trigger phrases (SK005); min 20 chars (SK004)
---
```

`fastmcp-client-cli` adds an extra field:

```yaml
---
name: fastmcp-client-cli
description: Query and invoke tools on MCP servers...
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Task
argument-hint: "<docs_path> <output_plugin> [output_skill]"
---
```

**Skill classification by size:**

| Skill | Content pattern |
|---|---|
| `fastmcp-creator` | Large (SK006 suppressed) — comprehensive MCP dev workflow |
| `fastmcp-client-cli` | Thin — CLI quick reference only |
| `fastmcp-python-tests` | Medium — pytest patterns for FastMCP |

---

## 5. fastmcp-creator SKILL.md Content Pattern

**File:** `plugins/fastmcp-creator/skills/fastmcp-creator/SKILL.md`

The SKILL.md uses a 4-phase workflow structure:

```
Phase 0: Requirements Intake    → AskUserQuestion calls, intent branching
Phase 1: Deep Research          → MCP spec study, API docs, implementation plan
Phase 2: Implementation         → Python (FastMCP) or TypeScript/Node patterns
Phase 3: Review and Refine      → Code quality checklist, safe test strategy
Phase 4: Create Evaluations     → Evaluation harness, XML output format
```

Notable structural conventions:

- **Runtime shell commands** at top of SKILL.md using `!` prefix:

  ```markdown
  !`python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Python not found in PATH"`
  ```

  This pattern executes at skill load time to inject environment context.

- **RULE/CONSTRAINT/TRIGGER keywords** used as semantic markers throughout:

  ```markdown
  RULE: The model must activate the python3-development skill before setting up Python MCP server projects
  CONSTRAINT: The python3-development skill contains: ...
  TRIGGER: The model must follow this 4-phase workflow when building MCP servers
  ```

- **Reference links** use relative `./references/` paths (not absolute):

  ```markdown
  [FastMCP Development Guidelines](./references/development-guidelines.md)
  ```

- **Code examples are inline** in SKILL.md (Python and TypeScript), with full working patterns — not delegated to references.

- **Decision trees** use Mermaid `flowchart TD` and plain text `DECISION_TREE:` blocks.

- **Cross-skill activation** is explicit:

  ```markdown
  Skill(skill: "python3-development:python3-development")
  ```

---

## 6. Reference File Conventions

The `references/` directory contains 9 files. Observed patterns from reading 3:

### `references/development-guidelines.md`

```markdown
# FastMCP 3.x Development Guidelines

Complete guide to building MCP servers with FastMCP 3.x...

**VERSION**: This guide covers FastMCP 3.0+...

## Architecture Overview (FastMCP 3.x)
...
RULE: The model must instantiate FastMCP object before registering tools
RULE: The model must use decorators to expose Python functions as MCP capabilities
RULE: The model must not implement low-level MCP protocol details
```

Pattern: Starts with H1 title + one-line summary sentence. Uses `RULE:` prefixes. No YAML frontmatter (reference files have none). Organized by concept.

### `references/claude-code-mcp-integration.md`

```markdown
# Claude Code MCP Integration Reference

How Claude Code discovers...

**Why read this**: ...

SOURCE: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp.md) (accessed 2026-03-01)
```

Pattern: Includes `SOURCE:` citation with URL and access date. This is the citation standard for externally-sourced information (`source-fidelity.md` rule).

### `references/accessing_online_resources.md`

Uses tables for tool selection matrix. Includes experimental evidence section with `SOURCE:` attribution. Uses `<eg>` custom tags for code examples (non-standard Markdown).

### `references/mcp-best-practices.md`

Uses `RULE:`, `PATTERN:`, `EXAMPLES:`, `CONSTRAINTS:`, `RATIONALE:` keyword labels consistently. Pattern mirrors SKILL.md label style.

**Reference file rules observed:**
- No YAML frontmatter (only SKILL.md has frontmatter)
- H1 title required
- Citation required for all externally-sourced facts (`SOURCE: [title](url) (accessed YYYY-MM-DD)`)
- `RULE:` / `CONSTRAINT:` / `PATTERN:` prefixes for prescriptive guidance
- Inline code blocks with language specifiers
- Links to sibling reference files use `./filename.md` relative paths

---

## 7. mcpServers in plugin.json — Existing Pattern

Only one plugin in the repository uses `mcpServers` in `plugin.json`:

**File:** `plugins/agentskill-kaizen/.claude-plugin/plugin.json`

```json
{
  "name": "agentskill-kaizen",
  "version": "0.6.81",
  "mcpServers": {
    "kaizen-duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-motherduck",
        "--db-path",
        "${CLAUDE_PLUGIN_ROOT}/data/kaizen.duckdb",
        "--read-only"
      ],
      "env": {
        "HOME": "$USERPROFILE"
      }
    },
    "kaizen-analysis": {
      "command": "uv",
      "args": [
        "run",
        "--script",
        "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"
      ]
    }
  }
}
```

**Pattern observations:**

- `mcpServers` is a top-level field in `plugin.json` (sibling to `name`, `version`, `description`)
- Server names use lowercase-hyphens: `kaizen-duckdb`, `kaizen-analysis`
- `${CLAUDE_PLUGIN_ROOT}` is the variable for plugin-relative paths (NOT `./` or `__file__`)
- Two launch strategies present:
  1. **`uvx`** — for PyPI-published MCP servers (no local code, pulls from registry)
  2. **`uv run --script`** — for local Python PEP 723 scripts bundled with the plugin
- `env` field maps environment variables; uses `$USERPROFILE` (non-`${...}` style for env vars)
- No `cwd` field in either server definition (relies on plugin root being the working directory)

**Alternative: `.mcp.json` at plugin root**

The `references/claude-code-mcp-integration.md` documents that plugins can also use a `.mcp.json` file at plugin root instead of inline `mcpServers` in `plugin.json`. The agentskill-kaizen pattern (inline in `plugin.json`) is the only observed in-repo example.

---

## 8. Plugin Linting Rules (plugin_validator.py)

**File:** `plugins/plugin-creator/scripts/plugin_validator.py`

Invoked via pre-commit hook:

```yaml
- id: plugin-validator
  entry: uv run -q --no-sync plugins/plugin-creator/scripts/plugin_validator.py --fix
  files: ^(plugins|\.claude)/.*(SKILL\.md|CLAUDE\.md|agents/.*\.md|commands/.*\.md|plugin\.json|hooks\.json)$
```

### Skill validation rules (SK-series)

| Code | Severity | Condition |
|---|---|---|
| SK001 | error | Skill name contains uppercase |
| SK002 | error | Skill name contains underscores |
| SK003 | error | Name has leading/trailing/consecutive hyphens or invalid format |
| SK004 | warning | Description < 20 chars (min) or > recommended length |
| SK005 | warning | Description missing trigger phrases (e.g., "Use when", "use when") |
| SK006 | warning | Body tokens > `TOKEN_WARNING_THRESHOLD` (4400) |
| SK007 | error | Body tokens > `TOKEN_ERROR_THRESHOLD` (8800) — must split |
| SK008 | error | Skill directory name violates naming convention |
| SK009 | info | Plugin uses manual skill selection (overrides auto-discovery) |

Token thresholds are constants in `plugin_validator.py`:
- `TOKEN_WARNING_THRESHOLD = 4400`
- `TOKEN_ERROR_THRESHOLD = 8800`

These are measured on **body content only** (frontmatter excluded).

### Frontmatter rules (FM-series)

FM001–FM010 cover: required fields, no colons in description values, name format `lowercase-hyphens`, missing `description`, empty `name`.

### Suppressing rules

Use `validator.json` in the plugin's `.claude-plugin/` directory:

```json
{
  "ignore": {
    "skills/skill-name": ["SK006"]
  }
}
```

The key is the relative path from plugin root to the skill directory.

---

## 9. Marketplace Registration

**File:** `.claude-plugin/marketplace.json`

Registration entry for fastmcp-creator:

```json
{
  "name": "fastmcp-creator",
  "source": "./plugins/fastmcp-creator"
}
```

All plugins use `"source": "./plugins/<plugin-dir-name>"` with relative paths. The marketplace `metadata.version` (currently `5.2.3`) must be bumped (minor) when adding a plugin.

The marketplace JSON `name` field must match the `name` field in the plugin's `plugin.json`.

---

## 10. rwr:user-docs-to-ai-skill Conventions

**File:** `plugins/the-rewrite-room/skills/user-docs-to-ai-skill/SKILL.md`

This skill converts documentation into Claude Code skill directories. It is the canonical tool for building new skills from existing docs.

**Input contract:**
- `$1` (`docs_path`) — GitHub URL or local directory path
- `$2` (`output_plugin`) — plugin name (e.g., `ty-skill`)
- `$3` (`output_skill`) — optional; derived from project name if omitted

**Output contract:** Creates `plugins/$2/skills/$3/` containing:
- `SKILL.md` — valid frontmatter + AI-facing workflow + links to all reference files
- `references/` — thematically grouped knowledge files, each linked from SKILL.md

**Workflow phases:**
1. Phase 0 — Input resolution (clone GitHub URL or use local path)
2. Phase 1 — Extraction (read all docs, apply per-type extraction patterns)
3. Phase 1.5 — Workflow identification (detect multi-step sequences → delegate to `process-siren`)
4. Phase 2 — Structure (scaffold output directory, classify atoms into themes)
5. Phase 3 — Write (references/*.md files, then SKILL.md)
6. Phase 4 — Verify (apply quality criteria checklist)

**Quality bar:** "Produces output equivalent in quality to fastmcp-creator" — meaning `fastmcp-creator` is the reference implementation for skill quality in this repository.

**Delegation:** Workflow-shaped atoms are delegated to `subagent_type='process-siren:process-siren'` before writing reference files.

---

## 11. Guidance for Adding mcpServers to fastmcp-creator

If a future task adds an MCP server to this plugin, follow the `agentskill-kaizen` pattern:

1. Add `mcpServers` as a top-level field in `plugins/fastmcp-creator/.claude-plugin/plugin.json`
2. Use `${CLAUDE_PLUGIN_ROOT}` for any paths relative to the plugin root
3. Use `uv run --script` for local PEP 723 scripts, `uvx` for published PyPI packages
4. Server names: lowercase-hyphens (e.g., `fastmcp-eval`)
5. No `cwd` field needed unless the server requires a specific working directory distinct from plugin root
6. Bump `version` in `plugin.json` and `metadata.version` in `.claude-plugin/marketplace.json`

---

_Architecture analysis: 2026-03-05_
