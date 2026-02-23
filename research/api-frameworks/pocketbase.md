# PocketBase

**Research Date**: 2026-02-23
**Source URL**: <https://pocketbase.io>
**GitHub Repository**: <https://github.com/pocketbase/pocketbase>
**Version at Research**: v0.36.5
**License**: MIT

---

## Overview

PocketBase is an open-source Go backend packaged as a single portable executable. It bundles an embedded SQLite database with realtime subscriptions, built-in authentication and file management, an admin dashboard UI, and a REST-ish API — all in one binary that launches with a single command. It can also be used as a Go framework/toolkit to embed into custom applications and extend with Go or JavaScript hooks.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| Backend setup for small-to-medium projects requires assembling many services (database, auth, storage, API) | Ships a single ~30MB binary with all core backend components pre-integrated and ready to run |
| Running separate database, auth, and storage servers increases infrastructure cost and complexity | Embeds SQLite (with realtime capabilities) plus file storage and user management inside one process |
| Building an admin UI for data and user management takes significant time | Provides a built-in superuser dashboard at `/_/` for full CRUD, collection management, and user administration |
| Extending a backend to fit custom business logic requires framework-specific knowledge | Supports JavaScript VM hooks and Go embedding so logic can be added without rewriting the core |
| Scaling from prototype to production backend is often a rewrite | Portable single-file design works for local dev and can run on any Linux/macOS/Windows target with no runtime dependencies |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| GitHub Stars | 56,299 | 2026-02-23 |
| Forks | 3,141 | 2026-02-23 |
| Latest Release | v0.36.5 | 2026-02-21 |
| Language | Go | 2026-02-23 |
| Open Issues | 21 | 2026-02-23 |
| Created | 2022-07-05 | 2026-02-23 |

---

## Key Features

### Embedded Database

- SQLite-based persistent storage with zero external database dependencies
- Realtime subscriptions via SSE (Server-Sent Events) for live collection data updates
- Supports migrations via JS migration files (`pb_migrations/`) that can be committed to version control
- Collection-level schema management through the admin UI or API

### Authentication

- Built-in user (record) auth with email/password, username/password, and OAuth2 providers
- Superuser accounts for admin dashboard access
- Token-based auth with configurable expiry
- Record-level access rules and field-level visibility controls

### File Storage

- Local file storage by default; S3-compatible backend configurable for production
- Built-in image resizing and thumbnail generation
- File fields on collections with size and type constraints

### Admin Dashboard

- Full-featured web UI at `/_/` for managing collections, records, users, settings, and logs
- No separate admin app needed; served by the same binary
- Log viewer for API request history and debugging

### REST-ish API

- Auto-generated CRUD endpoints for every collection
- Filter, sort, and expand relations via query params
- Real-time collection subscriptions via `/api/realtime`
- SDK clients for JavaScript/Node.js/React Native and Dart/Flutter

### Go Framework Mode

- Import as a standard Go library package (`github.com/pocketbase/pocketbase`)
- Attach custom routes, middleware, and event hooks via the `OnServe` event
- Statically compile into a single binary with `CGO_ENABLED=0 go build`
- JS VM plugin enabled by default in prebuilt executable for scripting hooks

---

## Technical Architecture

### Deployment Modes

```text
Standalone executable (prebuilt binary)
  ↓
./pocketbase serve
  ↓
Listens on :8090
  ├── /          → serves pb_public/ static files (if present)
  ├── /_/        → admin dashboard (superuser auth required)
  └── /api/      → REST-ish API (record CRUD, auth, files, realtime)

Data persisted in:
  pb_data/       → SQLite DB, uploaded files, logs
  pb_migrations/ → JS migration scripts (commit to VCS)
```

### Go Embedding Pattern

```go
app := pocketbase.New()
app.OnServe().BindFunc(func(se *core.ServeEvent) error {
    se.Router.GET("/hello", func(re *core.RequestEvent) error {
        return re.String(200, "Hello world!")
    })
    return se.Next()
})
app.Start()
```

### Realtime Subscription Flow

```text
Client connects to /api/realtime (SSE)
  ↓
Subscribes to collection events (create/update/delete)
  ↓
Server pushes JSON event payloads on data changes
  ↓
Client JS SDK dispatches events to subscribed callbacks
```

---

## Installation & Usage

```bash
# Download prebuilt binary (Linux amd64)
wget https://github.com/pocketbase/pocketbase/releases/latest/download/pocketbase_linux_amd64.zip
unzip pocketbase_linux_amd64.zip

# Start the server (creates pb_data/ and pb_migrations/ alongside executable)
./pocketbase serve

# Visit http://127.0.0.1:8090/_/ to set up the first superuser
```

```go
// Embed as Go library
import "github.com/pocketbase/pocketbase"

app := pocketbase.New()
// attach hooks, routes, etc.
if err := app.Start(); err != nil {
    log.Fatal(err)
}
```

```javascript
// JavaScript SDK (browser / Node.js)
import PocketBase from 'pocketbase';

const pb = new PocketBase('http://127.0.0.1:8090');

// Authenticate
await pb.collection('users').authWithPassword('user@example.com', 'password');

// List records
const records = await pb.collection('posts').getFullList({ sort: '-created' });

// Realtime subscription
pb.collection('posts').subscribe('*', (e) => {
    console.log(e.action, e.record);
});
```

---

## Relevance to Claude Code Development

### Applications

- **Rapid backend for agent-tooling prototypes**: Claude Code can scaffold new tools that need user auth, data persistence, and a REST API without configuring separate services — spin up PocketBase in seconds
- **Local AI workflow state storage**: Store agent session state, task history, and metadata in a lightweight local SQLite-backed API accessible from any language via HTTP
- **MCP server backend**: Use PocketBase as the data layer for custom MCP servers, providing record storage, auth, and realtime events with minimal overhead
- **Plugin marketplace data layer**: PocketBase's collection API and realtime subscriptions could back a local marketplace registry or skills catalog with live updates

### Patterns Worth Adopting

- **Single-binary distribution**: PocketBase's zero-dependency single-executable model is a compelling pattern for distributing tools — relevant to how Claude Code plugins could bundle lightweight backends
- **Migration-as-code**: Storing schema migrations as JS files in `pb_migrations/` (committed to VCS) is a clean approach to database schema versioning for AI workflow tooling
- **Embedded admin UI**: Shipping an admin dashboard within the same binary eliminates the need for separate front-end tooling, which could be replicated in Claude Code plugin tooling

### Integration Opportunities

- **Claude Code session storage**: Pair PocketBase with a Claude Code session hook to persist agent task history, outputs, and metadata locally for post-session review
- **Realtime skill event bus**: Use PocketBase's SSE realtime API as a lightweight pub/sub bus for multi-agent workflows where agents need to observe each other's state changes
- **Auth layer for local MCP tools**: PocketBase's built-in auth with token management could secure locally-run MCP servers that expose sensitive capabilities

### Competitive Analysis

| Tool | Approach | Trade-off vs PocketBase |
|------|----------|------------------------|
| Supabase | Managed cloud PostgreSQL + Auth + Storage | Full-featured but requires cloud account; no single-binary deployment |
| Firebase | Google cloud BaaS with Firestore | Proprietary lock-in; no self-hosted option |
| Appwrite | Open-source BaaS with Docker compose | Multi-container setup; heavier operational footprint |
| Directus | Open-source headless CMS/API | More configuration overhead; targets larger data models |
| PocketBase | Single Go binary, SQLite, self-hosted | Pre-1.0, not production-critical; SQLite limits horizontal scale |

---

## References

- [PocketBase Documentation](https://pocketbase.io/docs) (accessed 2026-02-23)
- [pocketbase/pocketbase GitHub Repository](https://github.com/pocketbase/pocketbase) (accessed 2026-02-23)
- [PocketBase JavaScript SDK — pocketbase/js-sdk](https://github.com/pocketbase/js-sdk) (accessed 2026-02-23)
- [PocketBase Dart SDK — pocketbase/dart-sdk](https://github.com/pocketbase/dart-sdk) (accessed 2026-02-23)
- [PocketBase Changelog](https://github.com/pocketbase/pocketbase/blob/master/CHANGELOG.md) (accessed 2026-02-23)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-23 |
| Version at Verification | v0.36.5 |
| Next Review Recommended | 2026-05-23 |
