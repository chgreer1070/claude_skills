# rtfp — Read The Fucking Prompt

Scans a Claude Code session transcript for the single strongest user reaction to an instruction-following failure, reconstructs the assistant output that caused it, and renders the exchange as a shareable terminal-style PNG.

## What It Does

You gave Claude instructions. At some point it ignored them, and you had a reaction.

RTFP finds that moment. It scans your session transcript, identifies the most striking instance where the assistant ignored or violated explicit instructions, reconstructs what Claude said and what you were working on, and renders a terminal-style image showing:

- **task** — one dry line describing what you were doing
- **claude** — the assistant output that triggered the reaction
- **user** — your reply, in vivid color

Output is exactly three things. It does not analyze your session or build a report. It finds one exchange and renders it.

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install rtfp@jamie-bitflight-skills
```

## Usage

```text
/rtfp
```

Claude lists your available sessions by number, asks which one to inspect, scans it, and writes the PNG. No other steps required.

### Example terminal output

```text
task:      writing a Claude Code plugin
claude:    Validation Error Severity Guide
           1 (Critical): Missing required fields...
           2 (High): Invalid path references...
user:      I LITERALLY just said no scoring. what the fuck

PNG written: rtfp_artifact.png
```

### The PNG

A dark terminal-style image styled after the Claude Code interface — title bar reading "rtfp — Read The Fucking Prompt" with red/yellow/green window dots. Built for sharing in Slack, PR comments, or social posts.

## When to Use

- You want to share a screenshot of Claude ignoring your instructions
- You're collecting examples of instruction-following failures for evaluation
- You want the most striking moment from a frustrating session rendered cleanly
- You need evidence for a bug report or feedback about assistant behavior

## How It Works

The skill uses a multi-step fan-out scan: it reads the session transcript, dispatches parallel subagents to scan batches of messages for user reactions, merges the flagged candidates, picks the single strongest reaction, reconstructs the surrounding context window, and renders the PNG via a Python script.

## Requirements

- Claude Code v2.0+
- Python 3.11+ (via `uv`)
- At least one Claude Code session transcript (generated automatically during normal use at `~/.claude/projects/`)
