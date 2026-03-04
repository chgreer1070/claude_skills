---
name: Claudebin
description: Claudebin is a minimalistic tool for publishing and sharing Claude Code sessions. Users run /claudebin:share inside any Claude Code session to upload the conversation to claudebin.com and receive a shareable URL with syntax highlighting, tool calls, and the full conversation thread.
license: MIT
metadata:
  topic: claudebin
  category: developer-tools
  source_url: https://claudebin.com
  github: wunderlabs-dev/claudebin.com
  plugin_github: wunderlabs-dev/claudebin
  version: "no-releases"
  verified: "2026-03-04"
  next_review: "2026-06-04"
---

## Overview

Claudebin is a two-part open-source platform for publishing and sharing Claude Code sessions. The web application (Next.js 16 + Supabase) hosts session threads at `claudebin.com`, while a companion Claude Code plugin provides the `/claudebin:share` slash command that uploads sessions from inside the editor. Sessions are parsed into structured message threads with syntax highlighting, tool call display, and embed support.

SOURCE: [wunderlabs-dev/claudebin.com README](https://github.com/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| No standard way to share Claude Code sessions with teammates or the public | `/claudebin:share` command uploads the current session and returns a shareable URL in seconds |
| Copy-pasting conversation transcripts loses tool call formatting and code syntax highlighting | Session processing pipeline parses JSONL conversation data into structured messages with full syntax highlighting |
| Sharing full session context requires manual export and hosting | Supabase Storage + background processing pipeline auto-generates a hosted thread from the raw JSONL upload |
| Session sharing requires authentication management | Browser-based GitHub OAuth flow is triggered automatically on first share; CLI polling handles the auth handoff |
| Teams cannot browse or discover public sessions | Public thread browsing at `/threads`, user profiles, view counts, and likes enable discovery |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| GitHub Stars (web app) | 54 | 2026-03-04 |
| GitHub Stars (plugin) | 19 | 2026-03-04 |
| Forks (web app) | 4 | 2026-03-04 |
| Contributors (web app) | 3 | 2026-03-04 |
| Open Issues | 19 | 2026-03-04 |
| Latest Release | None (unreleased) | 2026-03-04 |
| Created | 2025-12-12 | 2026-03-04 |
| Last Push | 2026-03-02 | 2026-03-04 |
| Primary Language | TypeScript | 2026-03-04 |

SOURCE: [GitHub API: repos/wunderlabs-dev/claudebin.com](https://api.github.com/repos/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)

---

## Key Features

### Claude Code Plugin Integration

- Installable from the Claude Code marketplace: `claude plugin marketplace add wunderlabs-dev/claudebin`
- Single slash command `/claudebin:share` publishes the current session and returns a `claudebin.com/threads/{id}` URL
- Automatic browser-based GitHub OAuth on first use; subsequent shares require no additional auth steps
- `CLAUDEBIN_API_URL` environment variable allows pointing the plugin at a self-hosted or local instance

SOURCE: [wunderlabs-dev/claudebin README](https://github.com/wunderlabs-dev/claudebin) (accessed 2026-03-04)

### Session Processing Pipeline

```text
Plugin uploads JSONL -> Store in Supabase Storage -> Parse into messages -> Generate title (LLM) -> Ready
```

- Raw JSONL session data is uploaded via `POST /api/sessions/publish`
- Background pipeline parses conversation data into structured `messages` rows in PostgreSQL
- LLM-generated title summarizes the session content
- Polling endpoint `GET /api/sessions/poll` lets the plugin wait for processing completion before returning the URL

SOURCE: [wunderlabs-dev/claudebin.com README -- Architecture](https://github.com/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)

### Public Thread Hosting and Discovery

- Threads viewable at `/threads/[id]` with full syntax highlighting and tool call display
- Embeddable version at `/threads/[id]/embed` for external sites
- Public browsing at `/threads` with featured threads on the homepage
- User profiles at `/profile/[username]` showing published sessions
- View counts and likes tracked via denormalized triggers on the `sessions` table

### CLI Authentication Flow

- `POST /api/auth/start` initiates a temporary auth session stored in `cli_auth_sessions` table
- Browser redirect completes GitHub OAuth and writes the token
- Plugin polls `GET /api/auth/poll` until the token is available
- `POST /api/auth/refresh` and `GET /api/auth/validate` handle token lifecycle
- OpenAPI spec published at `/api/openapi.json`

---

## Technical Architecture

```text
Claude Code Editor
     |
     | /claudebin:share (slash command)
     v
claudebin Plugin (MCP server, TypeScript/Bun)
     |
     | POST /api/sessions/publish (JSONL upload)
     | GET  /api/sessions/poll   (processing status)
     v
claudebin.com Web App (Next.js 16, Vercel)
     |
     | Server Actions / API Routes
     v
Supabase (PostgreSQL + Auth + Storage)
     |
     |- profiles   (GitHub OAuth user data)
     |- sessions   (published threads, view/like counts via triggers)
     |- messages   (parsed conversation messages, full-text search)
     |- session_likes
     |- cli_auth_sessions (temporary CLI OAuth tokens)
```

**Monorepo structure**:

```text
claudebin.com/
├── app/                  # Next.js 16 web application
│   └── src/
│       ├── app/          # Pages and API routes
│       ├── components/   # UI components (shadcn/ui + Tailwind CSS)
│       ├── containers/   # Page containers
│       ├── server/
│       │   ├── actions/  # Server actions (mutations)
│       │   ├── repos/    # Data access (Supabase)
│       │   ├── services/ # Business logic
│       │   └── api/      # OpenAPI schemas
│       └── context/      # React context providers
└── supabase/             # Database migrations
```

**Tech stack**:

| Component | Technology |
|-----------|------------|
| Framework | Next.js 16, Turbopack |
| Database | Supabase (PostgreSQL with Row Level Security) |
| Auth | Supabase Auth, GitHub OAuth |
| Styling | Tailwind CSS, shadcn/ui |
| Tooling | Bun, Biome |
| Plugin runtime | TypeScript, Bun |

SOURCE: [wunderlabs-dev/claudebin.com README -- Tech Stack](https://github.com/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)

---

## Installation & Usage

```bash
# Install the Claude Code plugin from the marketplace
claude plugin marketplace add wunderlabs-dev/claudebin
claude plugin install claudebin@claudebin-marketplace
```

Inside any Claude Code session:

```text
/claudebin:share
```

Returns a link like `https://claudebin.com/threads/abc123`.

**Local development with a self-hosted instance**:

```bash
# Web app
bun install
bun dev          # starts on port 3000

# Plugin (in a separate repo: wunderlabs-dev/claudebin)
cd /path/to/claudebin/mcp
bun install
bun run build

# Run Claude pointing the plugin at your local instance
CLAUDEBIN_API_URL=http://localhost:3000 claude --plugin-dir /path/to/claudebin --dangerously-skip-permissions
```

**Environment variables required for web app**:

The web app requires Supabase credentials (project URL and anon key). These are set in a `.env.local` file following the Supabase Next.js integration pattern.

SOURCE: [wunderlabs-dev/claudebin README -- Installation](https://github.com/wunderlabs-dev/claudebin) (accessed 2026-03-04)
SOURCE: [wunderlabs-dev/claudebin.com README -- Getting Started](https://github.com/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)

---

## Relevance to Claude Code Development

### Applications

- Direct utility for sharing Claude Code sessions with teammates for review, onboarding, or debugging collaboration — no manual export needed.
- The embeddable thread view (`/threads/[id]/embed`) enables publishing Claude Code sessions in documentation, blog posts, or internal wikis.
- Self-hosting is fully supported; teams with data residency requirements can deploy the Next.js app and Supabase instance internally.

### Patterns Worth Adopting

- **JSONL upload + async processing + polling**: The session upload flow (upload raw data, poll for processing completion, return final URL) is a clean pattern for any agent workflow that involves server-side processing with latency. The `POST publish / GET poll` API pair is reusable in other session-capture tools.
- **CLI auth via browser redirect + token polling**: The `cli_auth_sessions` table approach for bridging browser OAuth to a CLI process is a clean, stateless handoff pattern. The CLI polls until the browser auth completes and writes the token — no WebSocket required.
- **Row Level Security on multi-tenant data**: Using PostgreSQL RLS at the Supabase layer for session visibility (public vs. private threads) keeps authorization logic in the database rather than scattered across API routes.
- **Denormalized counts via triggers**: Tracking `view_count` and `like_count` on the `sessions` table via database triggers avoids expensive `COUNT(*)` queries on read-heavy endpoints — an applicable pattern for any analytics-adjacent feature in this repo.

### Integration Opportunities

- Claude Code skill output (plans, analysis, code reviews) could be published to Claudebin as a collaboration artifact, making skill-generated content shareable outside the editor.
- The `/api/openapi.json` spec enables automated integration testing or client generation for tools that consume the Claudebin API programmatically.
- The embed view could be used in generated documentation to show real Claude Code sessions as interactive examples alongside written explanations.

---

## References

- [wunderlabs-dev/claudebin.com GitHub Repository](https://github.com/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)
- [wunderlabs-dev/claudebin Plugin GitHub Repository](https://github.com/wunderlabs-dev/claudebin) (accessed 2026-03-04)
- [claudebin.com Website](https://claudebin.com) (accessed 2026-03-04)
- [GitHub API: repos/wunderlabs-dev/claudebin.com](https://api.github.com/repos/wunderlabs-dev/claudebin.com) (accessed 2026-03-04)
- [GitHub API: repos/wunderlabs-dev/claudebin](https://api.github.com/repos/wunderlabs-dev/claudebin) (accessed 2026-03-04)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-03-04 |
| Version at Verification | No versioned releases; main branch at 2026-03-02 push |
| Next Review Recommended | 2026-06-04 |
