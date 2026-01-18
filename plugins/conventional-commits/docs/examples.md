# Usage Examples

This document provides concrete, real-world examples of using Conventional Commits in various development scenarios.

## Example 1: Feature Development Workflow

**Scenario**: You're adding a new user profile feature to a web application.

**Steps**:

1. Create feature branch and implement changes
2. Stage changes: `git add src/components/UserProfile.jsx src/api/users.js`
3. Commit with appropriate type and scope

**Code**:

```bash
git commit -m "feat(profile): add user profile page with avatar upload

Implement new profile page component with:
- Avatar upload and preview
- Profile information editing
- Save/cancel functionality

Add API endpoint for profile updates at /api/users/:id/profile

Refs: #234"
```

**Result**:
- Clear feature addition (MINOR version bump)
- Scope identifies affected area (profile)
- Body provides implementation details
- Footer links to issue tracker

---

## Example 2: Critical Bug Fix

**Scenario**: Production bug where user sessions expire prematurely, causing data loss.

**Steps**:

1. Identify root cause in session management
2. Implement fix with additional validation
3. Add regression test
4. Commit fix and test separately

**Code**:

```bash
# Commit the fix
git commit -m "fix(auth): prevent premature session expiration

Session timeout was calculated from server start time instead of
last activity time, causing sessions to expire after 30 minutes
regardless of user activity.

Now correctly updates last activity timestamp on each request
and calculates timeout from that value.

Fixes: #567"

# Commit the test
git commit -m "test(auth): add regression test for session timeout

Verify session timeout correctly extends on user activity and
does not expire while user is active."
```

**Result**:
- Two focused commits (PATCH version bump for fix)
- Fix explains both problem and solution
- Test commit documents what's being prevented
- Issue reference for tracking

---

## Example 3: Breaking API Change

**Scenario**: Redesigning authentication API to improve security, requiring client updates.

**Steps**:

1. Implement new authentication flow
2. Update API endpoints
3. Create migration guide
4. Commit with breaking change notation

**Code**:

```bash
git commit -m "feat(api)!: redesign authentication endpoints

BREAKING CHANGE: Authentication endpoints have been moved and redesigned for improved security.

Changes:
- POST /auth/login → POST /api/v2/auth/signin
- POST /auth/register → POST /api/v2/auth/signup
- POST /auth/refresh → POST /api/v2/auth/token/refresh
- Response format now includes 'expiresAt' timestamp
- Tokens are now scoped with 'audience' claim

Migration:
1. Update all authentication endpoint URLs to /api/v2/auth/*
2. Update token refresh logic to use new response format
3. Add 'audience' parameter when requesting tokens

See docs/migration-v2-auth.md for complete migration guide.

Refs: #789"
```

**Result**:
- MAJOR version bump indicated by `!`
- BREAKING CHANGE footer explains impact
- Detailed migration instructions
- Link to comprehensive migration guide

---

## Example 4: Performance Optimization

**Scenario**: Database queries causing slow page load times in user dashboard.

**Steps**:

1. Profile application to identify bottleneck
2. Optimize database queries with indexing
3. Implement caching layer
4. Benchmark improvements

**Code**:

```bash
git commit -m "perf(dashboard): optimize user dashboard query performance

Reduce dashboard load time from 3.2s to 0.4s (87% improvement).

Changes:
- Add composite index on (user_id, created_at, status)
- Implement Redis caching for frequently accessed user data
- Batch related entity queries to reduce N+1 problems
- Use query result streaming for large datasets

Benchmark results (1000 users, 10000 records):
- Before: avg 3.2s, p95 5.1s, p99 8.3s
- After: avg 0.4s, p95 0.6s, p99 0.9s

Refs: #456"
```

**Result**:
- Performance improvement with quantified results
- Technical details of optimization
- Benchmark data validates improvement
- No version bump (perf alone doesn't affect SemVer without feat/fix)

---

## Example 5: Refactoring Legacy Code

**Scenario**: Extracting authentication logic into reusable module to improve testability.

**Steps**:

1. Create new auth module structure
2. Extract functions from multiple files
3. Update imports across codebase
4. Verify no behavioral changes

**Code**:

```bash
git commit -m "refactor(auth): extract authentication logic into auth module

Move authentication-related functions from utils.py, views.py, and
middleware.py into new auth/ module with clear separation:

- auth/validators.py: Input validation functions
- auth/tokens.py: JWT token generation and verification
- auth/providers.py: OAuth provider integrations
- auth/middleware.py: Authentication middleware

No functional changes. All existing tests pass unchanged.
New module structure improves:
- Code organization and discoverability
- Testability (can now unit test auth logic in isolation)
- Reusability across projects

Total: 847 lines moved, 0 lines changed"
```

**Result**:
- Clear refactoring with no functional change
- Explains both what moved and why
- Emphasizes no behavioral changes
- Quantifies scope of refactor
- No version bump (refactor doesn't affect public API)

---

## Example 6: Documentation Update

**Scenario**: API reference documentation is outdated after several feature releases.

**Steps**:

1. Review all endpoints added in recent releases
2. Update API reference documentation
3. Add usage examples for new endpoints
4. Update changelog

**Code**:

```bash
git commit -m "docs(api): update API reference for v2.3 endpoints

Update API documentation to reflect endpoints added in v2.2 and v2.3:
- /api/v2/users/:id/preferences (added v2.2)
- /api/v2/users/:id/notifications (added v2.2)
- /api/v2/analytics/events (added v2.3)
- /api/v2/analytics/reports (added v2.3)

Add code examples for each endpoint in Python, JavaScript, and cURL.
Fix typos in authentication section."
```

**Result**:
- Clear documentation scope
- Lists specific updates
- No version bump (docs changes don't affect code)

---

## Example 7: Dependency Updates with Security Implications

**Scenario**: Critical security vulnerability in third-party dependency requires immediate update.

**Steps**:

1. Review security advisory
2. Update dependency to patched version
3. Run tests to verify compatibility
4. Document security context

**Code**:

```bash
git commit -m "build(deps)!: update axios to 1.6.5 to fix CVE-2024-xxxxx

BREAKING CHANGE: Axios 1.6.5 changes default timeout from infinity to 30s.

Security: Fixes CVSS 9.8 vulnerability allowing request smuggling via
malformed HTTP headers (CVE-2024-xxxxx). All production deployments
must update immediately.

Breaking change: Default timeout now 30 seconds. Services making
long-running requests must explicitly set timeout option:

  axios.get(url, { timeout: 60000 })

See: https://github.com/axios/axios/security/advisories/GH-SA-xxxx

Refs: #999"
```

**Result**:
- MAJOR version bump due to behavior change
- Security context clearly stated
- Migration path provided
- CVE reference for tracking
- Urgent deployment signal

---

## Example 8: Multiple Related Changes

**Scenario**: Implementing user notification system requires database, API, and UI changes.

**Steps**:

1. Add database migrations
2. Implement API endpoints
3. Create UI components
4. Create separate focused commits

**Code**:

```bash
# Commit 1: Database schema
git commit -m "feat(db): add notifications table and user preferences

Create notifications table with:
- notification_id (PK)
- user_id (FK to users)
- type (email, push, in-app)
- message, created_at, read_at

Add user notification preferences to users table.

Migration: 20240115_add_notifications.sql"

# Commit 2: API implementation
git commit -m "feat(api): add notification management endpoints

Implement REST endpoints:
- GET /api/v2/notifications - List user notifications
- POST /api/v2/notifications/mark-read - Mark notifications as read
- GET /api/v2/notifications/preferences - Get user preferences
- PUT /api/v2/notifications/preferences - Update preferences

All endpoints require authentication and return paginated results."

# Commit 3: UI components
git commit -m "feat(ui): add notification center component

Implement notification center dropdown:
- Real-time notification updates via WebSocket
- Mark as read functionality
- Filter by type (all, unread, alerts)
- Link to notification preferences page

Add notification preferences page for user configuration."

# Commit 4: Integration
git commit -m "feat(notifications): integrate notification system

Wire up notification components with API and WebSocket:
- Subscribe to user notification channel on login
- Update notification badge count in header
- Show toast for high-priority notifications
- Persist read state across sessions

Refs: #123, #124, #125"
```

**Result**:
- Four focused commits, each reviewable independently
- Clear progression: data → API → UI → integration
- Each commit is deployable and testable
- All trigger MINOR version bump together
- Issue references link related work

---

## Example 9: Reverting a Problematic Change

**Scenario**: A recent feature is causing issues in production and needs immediate rollback.

**Steps**:

1. Identify problematic commit
2. Test revert locally
3. Create revert commit with context

**Code**:

```bash
git revert abc123def

# Edit the commit message:
git commit --amend -m "revert: feat(cache): add Redis caching layer

This reverts commit abc123def.

Reason: Redis caching causing memory exhaustion in production.
Cache keys not expiring as configured, leading to unbounded growth.

Investigation ongoing in #888. Will reimplement with proper TTL
configuration and memory limits once root cause identified.

Refs: abc123def, #888"
```

**Result**:
- Clear revert with explanation
- Original commit referenced
- Reason for revert documented
- Path forward indicated
- PATCH version bump (reverting a feature)

---

## Example 10: Monorepo with Scopes

**Scenario**: Working in monorepo with multiple packages (frontend, backend, shared).

**Steps**:

1. Make changes to specific package
2. Use scope to indicate affected package
3. Keep commits focused to single scope when possible

**Code**:

```bash
# Frontend change
git commit -m "feat(frontend): add dark mode toggle

Implement dark mode with:
- Toggle switch in user preferences
- System preference detection
- Persistent user selection in localStorage
- CSS custom properties for theme colors

Refs: #234"

# Backend change
git commit -m "fix(backend): handle malformed JSON in webhook payload

Previously threw 500 error on malformed JSON. Now returns 400 Bad Request
with validation error details.

Fixes: #567"

# Shared package change
git commit -m "feat(shared): add date formatting utilities

Add formatDate, parseDate, and relativeDateString functions to
shared/utils package for consistent date handling across frontend
and backend.

Refs: #789"

# Multiple packages affected
git commit -m "feat(frontend,backend): implement real-time notifications

Add WebSocket support for real-time notifications:
- Backend: WebSocket server with user channels (backend/websocket)
- Frontend: WebSocket client and notification component (frontend/components)
- Shared: Message type definitions (shared/types)

Refs: #999"
```

**Result**:
- Scopes clearly identify affected packages
- Easy to filter commits by package
- Multiple scopes when change spans packages
- Clear for package maintainers and reviewers

---

## Common Patterns Summary

### When to Use Which Type

| Situation | Type | Example |
|-----------|------|---------|
| New user-facing functionality | `feat` | `feat: add user search` |
| Fix breaks user functionality | `fix` | `fix: prevent data loss on save` |
| Performance user notices | `perf` | `perf: reduce page load by 50%` |
| Update documentation | `docs` | `docs: add API examples` |
| Reformat code | `style` | `style: apply prettier formatting` |
| Restructure without behavior change | `refactor` | `refactor: extract validation` |
| Add/fix tests | `test` | `test: add edge case coverage` |
| Update build scripts | `build` | `build: upgrade webpack to v5` |
| Update CI pipeline | `ci` | `ci: add integration tests` |
| Other maintenance | `chore` | `chore: update .gitignore` |

### Scope Guidelines

- Use scopes consistently across team
- Common scopes: component names, module names, packages
- Keep scope short: `auth`, `api`, `db`, not `authentication-system`
- Document standard scopes in CONTRIBUTING.md

### Body Guidelines

Include body when:
- Change is non-obvious
- Multiple approaches were considered
- Breaking change needs explanation
- Performance impact is significant
- Migration steps are required

Omit body when:
- Change is self-explanatory from description
- Simple typo fix or formatting change
- Adding straightforward test

### Footer Guidelines

Common footers:
- `Refs: #123` - References related issues
- `Fixes: #123` - Closes issue (GitHub auto-close)
- `BREAKING CHANGE: description` - Documents breaking change
- `Reviewed-by: Name` - Credits reviewer
- `Co-authored-by: Name <email>` - Credits co-author
