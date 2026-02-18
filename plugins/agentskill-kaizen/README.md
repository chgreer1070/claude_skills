# agentskill-kaizen

Analyze Claude Code session transcripts to find inefficiencies, anti-patterns, and repeated mistakes, then generate fixes automatically.

## Why Install This?

Every Claude Code session is recorded as a JSONL transcript. Those transcripts contain evidence of:

- Claude using Bash for file operations instead of built-in tools
- The same mistakes repeated across dozens of sessions
- Workflows that could be automated but are still done manually
- User corrections and interruptions that signal recurring AI misbehavior

This plugin reads those transcripts and produces actionable outputs: hook scripts that prevent recurring mistakes, skill patches that fill knowledge gaps, and CLAUDE.md updates with rationale and evidence.

## Getting Started

Load the plugin directly for a trial run:

```bash
claude --plugin-dir ./plugins/agentskill-kaizen
```

## Commands

### /agentskill-kaizen:analyze

Runs a full autonomous analysis pipeline against your session transcripts. Spawns a transcript analyst that queries your JSONL data with SQL, runs process mining algorithms, and writes a structured findings report.

```bash
/agentskill-kaizen:analyze
/agentskill-kaizen:analyze --project -home-user-repos-myproject
/agentskill-kaizen:analyze --dimensions tool-misuse,errors,frustration
```

**Arguments:**

- `--project <name>` (optional): Scope analysis to a specific project. The project key is the directory path with `/` replaced by `-`. Defaults to the current project.
- `--dimensions <list>` (optional): Comma-separated list of analysis dimensions. Defaults to `all`.

  Available dimensions: `tool-misuse`, `errors`, `frustration`, `tooling-gaps`, `delegation`, `shortest-path`, `red-herrings`, `interruptions`, `missing-hooks`, `all`

**What it does:** Resolves your transcript directory at `~/.claude/projects/{project-key}/`, creates a `.planning/kaizen/` output directory, and delegates deep analysis to the transcript-analyst. Results are written to `.planning/kaizen/analysis-{YYYY-MM-DD}.md` with per-finding severity (critical / warning / info), frequency counts, and session IDs as evidence.

---

### /agentskill-kaizen:explore

Interactive transcript exploration where you steer the investigation in real time. Claude presents an initial survey of your corpus, then follows your direction to dig into specific patterns.

```bash
/agentskill-kaizen:explore
/agentskill-kaizen:explore --project -home-user-repos-myproject
```

**Arguments:**

- `--project <name>` (optional): Scope to a specific project transcript directory. Defaults to the current project.

**What it does:** Runs a quick SQL survey of your transcripts (session count, date range, top tools, error rate, interrupt count), presents the findings with suggested directions, then runs targeted queries based on your responses. Saves findings to `.planning/kaizen/exploration-{date}.md` on request.

**When to use this instead of analyze:** When you already have a hunch about where to look, or when you want to investigate a specific dimension before running a full analysis.

---

### /agentskill-kaizen:report

Generates a summary report from previously written analysis files. Does not run new analysis — reads what is already in `.planning/kaizen/`.

```bash
/agentskill-kaizen:report
/agentskill-kaizen:report --latest
/agentskill-kaizen:report --all
```

**Arguments:**

- `--latest` (default): Summarize only the most recent analysis file.
- `--all`: Aggregate findings across all analysis and exploration files in `.planning/kaizen/`.

**What it does:** Extracts anti-patterns and their frequency counts, groups findings by severity, and writes an executive summary to `.planning/kaizen/report-{YYYY-MM-DD}.md`. With `--all`, includes trend analysis showing whether patterns are improving or worsening over time. Displays the top 5 findings inline so you can act without opening the file.

---

### /agentskill-kaizen:generate-hooks

Translates discovered anti-patterns into Claude Code hook configurations. By default, writes draft proposals you can review before installing anything.

```bash
/agentskill-kaizen:generate-hooks
/agentskill-kaizen:generate-hooks --install
/agentskill-kaizen:generate-hooks --from .planning/kaizen/analysis-2026-02-18.md
```

**Arguments:**

- `--install` (optional): Write hook configurations directly to project settings instead of draft files.
- `--from <file>` (optional): Source a specific analysis file. Defaults to the most recent analysis file.

**What it does:** Reads hook-eligible findings (tool misuse, missing context injection, quality gate violations, repeated manual corrections), then generates full hook configurations with scripts and testing instructions. In draft mode, each hook lands in `.planning/kaizen/hooks/` as a separate file:

```text
.planning/kaizen/hooks/
├── tool-misuse-prevention.md
├── edit-before-read-guard.md
└── research-to-files-enforcement.md
```

Each file contains the hook JSON configuration, the associated script, rationale tied back to the evidence from analysis, and instructions for testing the hook before installing.

---

## What the Analysis Covers

Ten dimensions are analyzed across your session history:

| Dimension | What it finds |
|---|---|
| Tool Misuse | Bash calls used for file read/write/search instead of built-in tools |
| Repeated Errors | Edit-before-Read patterns, stale edits, denied tool calls |
| User Frustration | Corrections, denials, interrupts, "you keep doing this" signals |
| Tooling Gaps | Multi-step sequences that repeat identically and could be a single script |
| Delegation Patterns | Whether Claude uses specialist agents or defaults to general-purpose |
| Shortest Path | Wasted steps when the same goal was reached faster in other sessions |
| Red Herrings | Investigation branches that were abandoned without producing output |
| System Interruptions | Context compaction events or API errors that derailed work mid-task |
| Missing Hooks | Recurring manual corrections that a PreToolUse hook would prevent |
| Direct SQL Access | DuckDB queries against raw JSONL for custom ad-hoc investigation |

---

## Improvement Outputs

Findings translate into five types of improvements:

- **Hook scripts** — PreToolUse, SubagentStart, SubagentStop, and Stop hooks that enforce correct behavior automatically
- **Agent prompt refinements** — Delegation prompts for the subagent-refactorer to fix specific misbehavior
- **Skill patches** — Delegation prompts for plugin-creator to fill knowledge gaps in existing skills
- **CLAUDE.md updates** — Exact markdown additions with evidence and rationale
- **Script automation proposals** — Replacement scripts for multi-step manual workflows

All outputs are proposals by default. Nothing is modified until you review and approve.

---

## Typical Workflow

```bash
# 1. Run full analysis on the current project
/agentskill-kaizen:analyze

# 2. Review the summary of findings
/agentskill-kaizen:report

# 3. Generate hooks for the top anti-patterns
/agentskill-kaizen:generate-hooks

# 4. Review drafts in .planning/kaizen/hooks/, then install when ready
/agentskill-kaizen:generate-hooks --install

# 5. Deep-dive on anything that needs more investigation
/agentskill-kaizen:explore
```

---

## Example

You run `/agentskill-kaizen:analyze` and the report shows:

```
Tool Misuse: 593 occurrences across 45 sessions — CRITICAL
  Finding: Bash used for file read operations (cat, grep, find)
  Evidence: Session abc123 line 456, Session def789 line 123
  Recommendation: PreToolUse hook to deny Bash file-op patterns
```

You run `/agentskill-kaizen:generate-hooks` and get a draft hook at `.planning/kaizen/hooks/tool-misuse-prevention.md` containing a complete hook JSON configuration and a JavaScript check script that blocks `cat`, `grep`, `find`, and `sed` from running via Bash. After reviewing it, you run `--install` and the hook is active from the next session.

---

## Requirements

- Claude Code CLI v2.0+
- `uv` installed (for running the process mining MCP server and its dependencies)
- `uvx` installed (for running the DuckDB MCP server)
- Session transcripts in `~/.claude/projects/` — these are generated automatically by Claude Code during normal use

The first run will download Python dependencies for the analysis server (fastmcp, pm4py, pandas, prefixspan, scikit-learn). Subsequent runs use the cached environment.
