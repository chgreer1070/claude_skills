# RTFP — Read The Fucking Prompt

Finds the single strongest user reaction to an AI instruction-following failure in a chosen
Claude Code session, reconstructs the assistant output that triggered it, and renders the
exchange as a terminal-style PNG ready for social media.

## Installation

```bash
/plugin install frustration-analyzer@jamie-bitflight-skills
```

Or for local testing:

```bash
claude --plugin-dir ./plugins/frustration-analyzer
```

## What It Does

RTFP runs a 3-stage pipeline against a session's JSONL transcript file:

```text
Stage 1: Extract user-only messages → batch files
Stage 2: Subagents detect emotional reactions per batch → flagged indexes (parallel)
Stage 3: Reconstruction agent picks winner → reads full context → 3-field artifact
Output:  Terminal-style PNG
```

The final artifact contains exactly three things:

1. **task** — a single dry line describing what was being worked on
2. **assistant said** — the assistant output that triggered the reaction
3. **user replied** — the user's exact words

## Quick Start

```text
/rtfp
```

The plugin lists your recent sessions, you pick one, and it runs the pipeline automatically.

Or pass a session path directly:

```text
/rtfp ~/.claude/projects/myproject/abc123.jsonl
```

### Generate a Social Media Post

After running RTFP and generating a PNG, you can optionally generate text for social media
sharing:

```text
/rtfp ~/.claude/projects/myproject/abc123.jsonl --social
```

This produces both the PNG and a plain-text social media post suitable for X/Twitter,
Bluesky, or internal Slack sharing.

## Example Output

```
┌─ RTFP ──────────────────────────────────────────┐

  task: writing a Claude Code plugin

  assistant:
    Here is a bulleted list of steps:
    - Step 1: Create the SKILL.md file
    - Step 2: Add frontmatter

  user:
    I said no bullets. How are you still doing bullets.

└──────────────────────────────────────────────────┘
```

PNG saved to `/tmp/rtfp-abc123.png`

## Architecture

**Data layer** — Claude Code sessions are stored as JSONL files in `~/.claude/projects/`.
DuckDB is the query layer: it reads, filters, and analyzes session data directly without
creating a persistent database.

**Stage 1 — User-only extraction** — The session JSONL is queried via DuckDB. Only
user-authored messages are written to batch files. No assistant content, tool outputs,
system messages, or context windows are included at this stage. Batches are token-aware:
large sessions are split intelligently to keep each batch under a token threshold, ensuring
efficient processing and preventing context overruns during analysis.

**Stage 2 — Parallel detection** — One `batch-detector` subagent per batch file. Each
subagent identifies messages containing strong emotional reactions (frustration, disbelief,
arguments) and returns a flagged index file. Detector thresholds are configurable per run.

**Stage 3 — Context reconstruction** — One `context-reconstructor` subagent reads the
merged flags, picks the strongest incident, goes back to the full transcript, and writes a
3-field artifact: `task_summary`, `assistant_excerpt`, `user_reply`.

**Render** — The 3-field artifact is rendered as a dark-background terminal-style PNG using PIL.
Rendering is configurable: font size, color scheme, and output resolution can be customized
before export.

## Agents

| Agent | Role |
|-------|------|
| `frustration-analyst` | Orchestrator — runs the full pipeline, presents result |
| `batch-detector` | Stage 2 — detects emotional reactions in a user-only batch file |
| `context-reconstructor` | Stage 3 — picks winner, reads full context, produces 3-field artifact |

## MCP Server

The plugin registers an MCP server (`frustration-analyzer`) that provides the tools used
by the pipeline. The server runs as a `uv` script — no separate install step needed.

| Tool | Description |
|------|-------------|
| `list_sessions` | List JSONL session files from `~/.claude/projects/`, sorted by recency |
| `extract_user_messages` | Write a user-only batch JSONL from a session file (Stage 1) |
| `get_context_window` | Return N messages before/after a target line (Stage 3 reconstruction) |
| `get_scenario` | Alternative context retrieval by file + line position |
| `render_rage_receipt` | Render task_summary + assistant_excerpt + user_reply as a terminal PNG |
| `scan_transcripts` | Paginated user message extraction with context (direct use) |
| `generate_social_post` | Generate a text social media post from a user message |

## Privacy

Session transcripts may contain personal, business, or identifying details. Content is
always shown raw — no mechanical filtering is applied. After presenting a PNG, the plugin
asks whether any details should be replaced with placeholders before sharing externally.

## What This Is Not

- Not a corpus-wide analytics tool — one session per run
- Not an insult scorer — no taxonomy, no ratings, no verdicts
- Not a sentiment analyzer — it finds specific instruction-following failures
