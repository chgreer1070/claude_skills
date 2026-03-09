# rtfp — Read The Fucking Prompt

Mine your Claude Code session transcripts to find the single most enraging moment when Claude
completely ignored your CLAUDE.md instructions. Render it as a shareable terminal-style PNG.

## Why This Exists

If you use Claude Code seriously, you have a CLAUDE.md. You've written rules. You've been
explicit. And at some point Claude has looked directly at those rules and done the opposite,
and you've had a reaction.

RTFP finds that moment. The one where you stopped being polite. It pulls the assistant output
that caused it, the task you were working on, and your exact reply — and turns it into a
dark-terminal screenshot you can share.

It doesn't analyze your session. It doesn't build a report. It finds one moment and renders it.

## What You Get

### The `/rtfp` Command

Type `/rtfp` to start the pipeline. Claude will:

1. Show you a numbered list of available Claude Code sessions
2. Ask which session to inspect
3. Scan it for emotional reactions to instruction-following failures
4. Pick the strongest one
5. Render a PNG and show you the text summary

```text
task:      writing a Claude Code plugin
claude:    Here is a scoring rubric for severity of instruction violations: ...
user:      I LITERALLY JUST SAID NO SCORING. what the fuck

PNG: rtfp_artifact.png
```

### The PNG Artifact

The output is a dark terminal-style image styled after the Claude Code interface:

- Title bar with "rtfp — Read The Fucking Prompt" and red/yellow/green window dots
- `task:` — one dry line describing what you were working on (not the incident, the work)
- Divider
- `claude:` — the assistant output that triggered the reaction
- Divider
- `user:` — your reply, rendered in vivid color

Built for sharing. Drop it in a Slack channel, a PR comment, or a post.

## How It Works

The pipeline has four stages:

### Stage 1: Session Listing

Lists available Claude Code session transcripts on your machine. You pick the one to analyze.

### Stage 2: Batch Extraction

The session JSONL is split into batches of user messages. Each batch becomes a separate file
for parallel scanning.

### Stage 3: Reaction Detection

Each batch is scanned for emotional signals. Two modes are available (see Pipeline Modes below).
Messages are scored on:

- Profanity and expletives (highest weight)
- Negative phrases: "you ignored", "I told you", "READ THE", "not what I asked", "still wrong"
- ALL CAPS words (3+ characters, fully uppercase)
- Punctuation runs (three or more consecutive `!` or `?`)
- Short-message bursts (under 50 characters with any signal — the "one-word reply" tell)

The top candidates from each batch are merged into a working set.

### Stage 4: Context Reconstruction and Rendering

From the flagged messages, the pipeline walks backward through the transcript to find the
assistant output that immediately preceded each reaction. The strongest exchange is selected
as the winner. The `render_artifact.py` script produces the terminal PNG.

## Pipeline Modes

### Default Mode (LLM Subagent Scan)

Claude spawns one subagent per batch file. Each subagent reads its batch and judges which
messages represent genuine emotional reactions to assistant failures. Subagents can distinguish
between frustration aimed at the AI versus general frustration, and handle subtler signals
that heuristics miss.

Use this when accuracy matters.

### Fast Mode (Heuristic Scripts)

The same detection logic is available as a standalone Python script that runs without spawning
any subagents. The `detect_reactions.py` script applies the weighted signal scoring directly
and outputs flagged message indexes.

Use this for speed, or when running the pipeline programmatically outside a Claude Code session.

## Installation

Add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Install the plugin:

```bash
/plugin install rtfp@jamie-bitflight-skills
```

## Usage

In any Claude Code session:

```bash
/rtfp
```

Claude will prompt you to select a session, then run the full pipeline. The PNG is written to
`rtfp_artifact.png` in your current working directory.

## Standalone Scripts

All pipeline stages are available as standalone Python scripts. Run them via `uv run`.

### `list_sessions.py`

Lists available Claude Code session transcript files.

```bash
uv run plugins/rtfp/scripts/list_sessions.py --json
```

Output: JSON array of session file paths with metadata.

### `extract_batches.py`

Splits a session JSONL into batch files for parallel scanning.

```bash
uv run plugins/rtfp/scripts/extract_batches.py <session_jsonl_path> --out-dir /tmp/rtfp-batches
```

Output: JSON array of batch file paths written to stdout.

### `detect_reactions.py`

Scores user messages in a batch file using heuristic signals. The fast-mode alternative to
LLM subagent scanning.

```bash
uv run plugins/rtfp/scripts/detect_reactions.py <batch_file_path>
```

Output: JSON with flagged message indexes and scores.

### `reconstruct_context.py`

Given flagged message indexes, walks the session transcript backward to find the triggering
assistant output and selects the winner.

```bash
uv run plugins/rtfp/scripts/reconstruct_context.py \
  --flagged-file /tmp/rtfp-flagged.json \
  --session-file /path/to/session.jsonl
```

Output: JSON with `task_summary`, `triggering_assistant_output`, and `user_reaction`.

### `render_artifact.py`

Renders the terminal-style PNG from the reconstructed context JSON.

```bash
uv run plugins/rtfp/scripts/render_artifact.py \
  --input-file /tmp/rtfp-result.json \
  --output rtfp_artifact.png
```

Output: PNG file at the specified path.

## Example

You are writing a Claude Code plugin. You specified in CLAUDE.md: "Do not add severity ratings
or scoring to output." Claude produces a detailed 5-point severity rubric for plugin validation
errors. You reply: `I LITERALLY just said no scoring. what the fuck`

RTFP finds that exchange. The PNG shows:

```text
task:      writing a Claude Code plugin
claude:    Validation Error Severity Guide
           1 (Critical): Missing required fields...
           2 (High): Invalid path references...
user:      I LITERALLY just said no scoring. what the fuck
```

## Requirements

- Claude Code v2.0+
- Python 3.11+ (via `uv`)
- Claude Code session transcripts on your machine (generated automatically during normal use)
