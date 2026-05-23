# dot-dash

Real-time multi-session dashboard for Claude Code. Watch all your active Claude sessions from a
browser, stream live transcripts, and inject prompts — all from one place.

## Screenshots

### Token Gate

![Token gate login screen](./docs/screenshots/01-token-gate.png)

On first open, paste the bearer token from `~/.claude/dot-dash/token` to connect.

### Session Dashboard

![Dashboard showing active sessions](./docs/screenshots/02-dashboard-sessions.png)

All active Claude Code sessions appear in the left panel. The WebSocket connection status shows
**● live** in the top-right.

### Session Selected — Transcript and Controls

![Session selected with transcript pane and controls](./docs/screenshots/03-session-selected.png)

Selecting a session opens the **Transcript** pane (live events stream) and the **Controls** panel
on the right — inject a message into the next user prompt, or deregister the session.

## Features

- **Live session list** — Sessions register automatically via `SessionStart` / `SessionEnd` hooks
- **Transcript streaming** — Tails `~/.claude/projects/*/*.jsonl` and broadcasts events via WebSocket
- **Prompt injection** — Queue a message from the dashboard; the `UserPromptSubmit` hook prepends it to the next user turn
- **Bearer token auth** — Auto-generated token stored at `~/.claude/dot-dash/token` on first start
- **Dark UI** — Runs entirely on localhost, no external service dependencies

## Quick Start

```bash
# 1. Start the server
bash plugins/dot-dash/scripts/start-server.sh

# 2. Open the dashboard
open http://localhost:7765

# 3. Paste the token from
cat ~/.claude/dot-dash/token
```

The server defaults to port `7765`. Override with `DOT_DASH_PORT`.

> **Marketplace-installed users:** The script is at
> `~/.claude/plugins/cache/jamie-bitflight-skills/dot-dash/<version>/scripts/start-server.sh`.
> Alternatively, use the `/dot-dash` skill to let Claude manage it:
>
> ```text
> /dot-dash start    — start the server
> /dot-dash stop     — stop the running server
> /dot-dash status   — check if server is running and show active sessions
> /dot-dash token    — print the bearer token
> ```

## Architecture

```text
Claude Code session
  │
  ├── SessionStart hook → POST /internal/session/register
  ├── SessionEnd hook   → POST /internal/session/deregister
  └── UserPromptSubmit  → GET  /internal/inject/{sessionId}

dot-dash server (Hono + Node.js)
  ├── Watches ~/.claude/projects/**/*.jsonl (chokidar)
  ├── Broadcasts events via WebSocket (/ws)
  └── Serves React frontend (static build)

Browser dashboard (React 18 + Vite)
  └── WsManager — auto-reconnects, dispatches to useReducer
```

Hooks fire at session lifecycle events (5-second timeout each) and on every user prompt
submission to check for queued injections.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DOT_DASH_PORT` | `7765` | HTTP + WebSocket port |
| `DOT_DASH_TOKEN` | _(auto-generated)_ | Bearer token saved to `~/.claude/dot-dash/token` |

## Installation

```bash
/plugin install dot-dash@jamie-bitflight-skills
```
