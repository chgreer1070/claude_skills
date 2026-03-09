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

Claude will show you a numbered list of available sessions, ask which one to inspect, scan it,
and render the PNG. No other steps required.

## What You Get

### Terminal output

```text
task:      writing a Claude Code plugin
claude:    Validation Error Severity Guide
           1 (Critical): Missing required fields...
           2 (High): Invalid path references...
user:      I LITERALLY just said no scoring. what the fuck

PNG written: rtfp_artifact.png
```

### The PNG

A dark terminal-style image styled after the Claude Code interface:

- Title bar: "rtfp — Read The Fucking Prompt" with red/yellow/green window dots
- `task:` — one dry line describing what you were working on
- `claude:` — the assistant output that triggered the reaction
- `user:` — your reply, in vivid color

<!-- Example PNG: rtfp_example.png (not yet available) -->

Built for sharing. Drop it in a Slack channel, a PR comment, or a post.

## Requirements

- Claude Code v2.0+
- Python 3.11+ (via `uv`)
- At least one Claude Code session transcript on your machine (generated automatically during
  normal use)
