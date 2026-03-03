# Badge Services Reference

Comprehensive coverage of badge generation services, GitHub-native badges, custom/endpoint
badges, trending badge types (2025-2026), and accessibility guidance.

SOURCE: Research conducted 2026-03-03 from primary sources listed in each section.

---

## 1. Badgen.net

**Repository**: [badgen/badgen.net](https://github.com/badgen/badgen.net) — 1,529 stars, ISC
license, TypeScript, hosted on Vercel Edge Network

SOURCE: [badgen/badgen.net GitHub](https://github.com/badgen/badgen.net) (accessed 2026-03-03)

### URL Pattern

```text
# Static badge
https://badgen.net/badge/:subject/:status/:color?icon=github

# Live badge (service-specific)
https://badgen.net/:service/:path

# Flat style variant (identical API, different visual)
https://flat.badgen.net/badge/:subject/:status/:color
```

Parameter anatomy:

```text
https://badgen.net/badge/:subject/:status/:color?icon=github
                   ──┬──  ───┬───  ──┬───  ──┬── ────┬──────
                     │       │       │       │       └─ Options (icon, label, etc.)
                     │       │       │       │
                     │      TEXT    TEXT    RGB / COLOR_NAME (optional)
                     │
                  "badge" — default (static) badge generator
```

### Two Visual Styles

| Style | Base URL |
|-------|----------|
| Classic (rounded) | `https://badgen.net` |
| Flat (square) | `https://flat.badgen.net` |

Set globally via `BADGE_STYLE=flat` env var when self-hosting.

SOURCE: [badgen.net README](https://github.com/badgen/badgen.net/blob/main/README.md) (accessed 2026-03-03)

### URL Options (Query Parameters)

| Option | Description | Example |
|--------|-------------|---------|
| `color` | Override badge right-side color | `?color=pink` |
| `icon` | Builtin icon slug or external SVG URL | `?icon=docker` |
| `label` | Override left-side subject text | `?label=container` |
| `labelColor` | Override left-side color | `?labelColor=pink` |
| `list` | Replace `,` with separator in status text | `?list=\|` |
| `scale` | Custom badge scale multiplier | `?scale=2` |
| `cache` | CDN cache lifetime in seconds (min 300, default 86400) | `?cache=600` |

### Built-in Icons

Badgen maintains its own icon set via [badgen/badgen-icons](https://github.com/badgen/badgen-icons).
Icons are referenced by slug with `?icon=<slug>`.

External icons are supported by passing a full SVG URL: `?icon=https://example.com/icon.svg`

SOURCE: [badgen/badgen-icons GitHub](https://github.com/badgen/badgen-icons) (accessed 2026-03-03)

### Live Badge Generators

Badgen supports live data for the following services (each at `/service/...`):

`/github`, `/gitlab`, `/npm`, `/pypi`, `/crates`, `/docker`, `/pub`, `/npm`, `/hackage`,
`/winget`, `/bundlephobia`, `/bundlejs`, `/codecov`, `/coveralls`, `/codeclimate`, `/travis`,
`/circleci`, `/dependabot`, `/snyk`, `/uptime-robot`, `/discord`, `/matrix`, `/opencollective`,
`/rubygems`, `/homebrew`, `/nuget`, `/packagist`, `/maven`, `/cocoapods`, `/chrome-web-store`,
`/vs-marketplace`, `/open-vsx`, `/jsdelivr`, `/liberapay`, `/mastodon`, `/reddit`, `/tidelift`,
`/peertube`, `/appveyor`, `/codacy`, `/azure-pipelines`, `/jenkins`, `/badgesize`

SOURCE: [badgen.net/help](https://badgen.net/help) (accessed 2026-03-03)

### Advanced Generators

| Generator | Purpose |
|-----------|---------|
| `/https` | Turn any JSON API endpoint into a live badge |
| `/memo` | Memo badge updatable via PUT request |
| `/runkit` | Create arbitrary live badges with RunKit IDE |

### GitHub-Specific Badgen Badges

```text
# Standard repo stats
/github/stars/:owner/:repo
/github/forks/:owner/:repo
/github/watchers/:owner/:repo
/github/license/:owner/:repo
/github/releases/:owner/:repo
/github/tags/:owner/:repo
/github/tag/:owner/:repo            ← latest tag
/github/contributors/:owner/:repo

# Release channels
/github/release/:owner/:repo
/github/release/:owner/:repo/stable

# CI checks
/github/checks/:owner/:repo/:ref?
/github/checks/:owner/:repo/:ref/:check_name+

# Issues and PRs
/github/issues/:owner/:repo
/github/open-issues/:owner/:repo
/github/closed-issues/:owner/:repo
/github/prs/:owner/:repo
/github/merged-prs/:owner/:repo

# Activity
/github/commits/:owner/:repo/:ref?
/github/last-commit/:owner/:repo/:ref?

# Security
/github/dependabot/:owner/:repo
```

SOURCE: [badgen.net/github](https://badgen.net/github) (accessed 2026-03-03)

### Self-Hosting Badgen

Docker image: `amio/badgen` (Docker Hub)

```bash
docker run -p 3000:3000 amio/badgen
```

Key environment variables for self-hosted instances:

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKENS` | Comma-delimited GitHub tokens for GitHub badges |
| `GITHUB_API` | Custom GitHub API endpoint (for GitHub Enterprise) |
| `NPM_REGISTRY` | Custom npm registry endpoint |
| `BADGE_STYLE` | Set to `flat` for flat design globally |
| `SENTRY_DSN` | Error monitoring |
| `GITLAB_TOKENS` | GitLab tokens for GitLab badges |
| `GITLAB_API` | Custom GitLab REST API endpoint |
| `GITLAB_API_GRAPHQL` | Custom GitLab GraphQL endpoint |
| `DOCKER_REGISTRY_API` | Custom Docker registry endpoint |

### How Badgen Differs from Shields.io

| Aspect | Badgen | Shields.io |
|--------|--------|------------|
| Codebase size | ~2K LoC (TypeScript) | ~22K LoC |
| Performance | Faster — SVG generated directly from char-width table | Slower — more processing overhead |
| Infrastructure | Vercel Edge Network (Cloudflare-powered, globally cached) | Self-hosted, global CDN |
| Styles | 2 (classic, flat) | 5 (flat, flat-square, plastic, social, for-the-badge) |
| Icon source | Proprietary badgen-icons set | SimpleIcons (thousands of icons) |
| Logo support | Builtin slugs + external SVG URL | SimpleIcons slugs + base64-encoded custom SVG |
| Endpoint badge | `/https` path | `/endpoint?url=...` query param |
| Dynamic endpoint schema | Custom — returns SVG text directly | JSON schema (schemaVersion, label, message, color) |

**When to prefer Badgen over Shields.io:**

- Speed is a priority (Badgen generates SVG purely in JS without canvas/pdfkit)
- Simpler URL structure preferred
- Fewer style variants needed
- Using `/memo` for manually updateable badges
- Using RunKit for prototype live badges without deploying code

**When to prefer Shields.io over Badgen:**

- Need `for-the-badge` or `social` styles
- Need the `plastic` style
- Need SimpleIcons coverage (thousands of brand logos)
- Need the JSON endpoint schema (`/endpoint`) for structured dynamic badges
- Need base64-embedded custom SVG logos
- Service already has Shields.io live badge support but not Badgen support

SOURCE: [The Badgen Story in README](https://github.com/badgen/badgen.net/blob/main/README.md) (accessed 2026-03-03)

---

## 2. For The Badge

**Site**: [forthebadge.com](https://forthebadge.com/)
**GitHub**: [forthebadge/for-the-badge](https://github.com/forthebadge/for-the-badge)
**Scale**: 3,000,000+ projects using it, 100,000 monthly visitors, since 2014

SOURCE: [forthebadge.com](https://forthebadge.com/) (accessed 2026-03-03)

### Design Philosophy

"Badges for badges' sake." For the Badge produces oversized, humorous, decorative SVG badges
for README files. They make no technical claims — they express personality, humor, or project
character.

### Badge Dimensions

For the Badge badges are notably larger than standard badges — they use all-caps text in a bold
font on a wide rectangular shape. This is distinct from the compact informational badges of
Shields.io and Badgen.

### Badge Collection

As of 2026-03-03, For the Badge offers 135 official badges plus 16 community submissions.
Selected examples:

**Build/Status:**

```text
WORKS ON MY MACHINE
FUCK IT SHIP IT
FIXED BUGS
NOT A BUG A FEATURE
```

**Made With (language):**

```text
MADE WITH PYTHON
MADE WITH JAVASCRIPT
MADE WITH TYPESCRIPT
MADE WITH RUST
MADE WITH GO
MADE WITH KOTLIN
MADE WITH SWIFT
MADE WITH C
MADE WITH C++
MADE WITH C#
MADE WITH JAVA
MADE WITH RUBY
MADE WITH ELIXIR
MADE WITH FLUTTER
MADE WITH VUE
MADE WITH NEXT 13
MADE WITH MARKDOWN
```

**Powered By:**

```text
POWERED BY COFFEE
POWERED BY ELECTRICITY
POWERED BY PULL REQUESTS
POWERED BY OXYGEN
POWERED BY CODERS SWEAT
```

**Humor/Personality:**

```text
GLUTEN FREE
CONTAINS TECHNICAL DEBT
IT WORKS WHY
NO RAGRETS
CTRL C CTRL V
CONTAINS CAT GIFS
```

**License:**

```text
LICENSE MIT
LICENSE ISC
CC 0
CC BY
CC BY SA
```

**Compatibility (satirical):**

```text
COMPATIBILITY IE 6
COMPATIBILITY BLACKBERRY
COMPATIBILITY EMACS
COMPATIBILITY PC LOAD LETTER
```

**AI/Modern (community additions as of 2026-03-03):**

```text
VIBE CODED
```

### URL Pattern

For the Badge does not have a programmatic API for generating arbitrary text. All badges are
pre-made assets served from their CDN:

```text
https://forthebadge.com/images/badges/<badge-slug>.svg
```

Example:

```markdown
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
```

### Generator

For custom one-off designs, For the Badge provides a visual generator at
[forthebadge.com/generator](https://forthebadge.com/generator) with:

- Real-time preview
- Interactive controls
- AI-powered suggestions
- REST API for automation

The REST API URL is documented at [forthebadge.com/api](https://forthebadge.com/api).

### When For the Badge is Appropriate

- README personality sections
- Fun project/personal portfolio pages
- Expressing humor about project state
- Communicating project culture (not technical status)
- Developer profile READMEs

### When For the Badge is Inappropriate

- Indicating build status, test results, or version numbers
- Production project dashboards
- Professional enterprise project documentation
- Anywhere factual status must be conveyed accurately
- Contexts where badge size causes layout problems (FTB badges are 2-3x larger)

SOURCE: [forthebadge.com/badges](https://forthebadge.com/badges) (accessed 2026-03-03)

---

## 3. GitHub Native Badges

These badges come from GitHub itself — no external service required.

### 3.1 GitHub Actions Workflow Status Badge

GitHub Actions generates a built-in status badge for every workflow. No Shields.io or Badgen
dependency.

**URL pattern:**

```text
https://github.com/<OWNER>/<REPO>/actions/workflows/<WORKFLOW-FILE>/badge.svg
```

**Query parameters:**

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `branch` | Show status for a specific branch | `?branch=main` |
| `event` | Show status for a specific trigger event | `?event=push` |

**Example Markdown:**

```markdown
![Build Status](https://github.com/owner/repo/actions/workflows/main.yml/badge.svg)
![Build on main](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg?branch=main)
![Push trigger](https://github.com/owner/repo/actions/workflows/ci.yml/badge.svg?event=push)
```

**How to generate from UI:**

1. Navigate to the repository on GitHub
2. Click **Actions** tab
3. Select the workflow in the left sidebar
4. Click the dropdown next to "Filter workflow runs"
5. Select **Create status badge**
6. Optionally filter by branch or event
7. Click **Copy status badge Markdown**

**Notes:**

- Private repository badges are not accessible externally
- Default branch status shown when no branch specified
- If no runs on default branch, shows status of most recent run across all branches

SOURCE: [GitHub Docs — Adding a workflow status badge](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/monitoring-workflows/adding-a-workflow-status-badge) (accessed 2026-03-03)

### 3.2 GitHub Sponsors Badge

GitHub Sponsors does not provide a dedicated native SVG badge URL. The standard approach uses
Shields.io static badge with the GitHub Sponsors logo from SimpleIcons:

```markdown
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/USERNAME)
```

Or using the `for-the-badge` style:

```markdown
[![Github-sponsors](https://img.shields.io/badge/sponsor-30363D?style=for-the-badge&logo=GitHub-Sponsors&logoColor=#EA4AAA)](https://github.com/sponsors/USERNAME)
```

SOURCE: [Ileriayo/markdown-badges](https://github.com/Ileriayo/markdown-badges) (accessed 2026-03-03)

### 3.3 GitHub Discussions Badge

No native GitHub SVG badge for Discussions exists. Use Badgen's GitHub badge:

```markdown
[![Discussions](https://badgen.net/github/discussions/OWNER/REPO)](https://github.com/OWNER/REPO/discussions)
```

Or a Shields.io static badge:

```markdown
[![GitHub Discussions](https://img.shields.io/github/discussions/OWNER/REPO)](https://github.com/OWNER/REPO/discussions)
```

Shields.io provides a live `/github/discussions/:owner/:repo` badge that fetches the count
from the GitHub API.

### 3.4 Dependabot Badge

Badgen provides a native Dependabot status badge:

```markdown
[![Dependabot](https://badgen.net/github/dependabot/OWNER/REPO)](https://github.com/OWNER/REPO)
```

Shields.io also provides a static Dependabot badge using the SimpleIcons logo:

```markdown
[![Dependabot](https://img.shields.io/badge/Dependabot-025E8C?logo=dependabot&logoColor=fff)](URL)
```

SOURCE: [badgen.net/github](https://badgen.net/github) (accessed 2026-03-03),
[inttter/md-badges](https://github.com/inttter/md-badges) (accessed 2026-03-03)

---

## 4. Custom and Self-Hosted Badges

### 4.1 Shields.io Endpoint Badge

The endpoint badge turns any JSON API into a live badge. Shields.io fetches the URL and
renders the returned data as a badge.

**URL:**

```text
https://img.shields.io/endpoint?url=<JSON_ENDPOINT_URL>
```

**Required JSON schema:**

```json
{
  "schemaVersion": 1,
  "label": "hello",
  "message": "sweet world",
  "color": "orange"
}
```

**Full JSON schema:**

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `schemaVersion` | Yes | — | Always `1` |
| `label` | Yes | — | Left text (or `""` to omit left side) |
| `message` | Yes | — | Right text; cannot be empty |
| `color` | No | `lightgrey` | Right background color |
| `labelColor` | No | `grey` | Left background color |
| `isError` | No | `false` | `true` prevents color override; future: affects cache |
| `namedLogo` | No | none | SimpleIcons slug |
| `logoSvg` | No | none | Custom SVG string |
| `logoColor` | No | none | Logo color (SimpleIcons only) |
| `logoSize` | No | none | `auto` for adaptive resize (SimpleIcons only) |
| `style` | No | `flat` | Default template; overridable by query string |

**Query parameters** (can override JSON values):

`style`, `logo`, `logoColor`, `logoSize`, `label`, `labelColor`, `color`, `cacheSeconds`, `link`

**Supported colors:** named colors (`blue`, `green`, `red`, `orange`, `yellow`, `brightgreen`,
`grey`, `lightgrey`), plus any hex, rgb, rgba, hsl, hsla, or CSS named color.

**Example — uv version badge from official assets:**

```markdown
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
```

This is the official pattern Astral uses: they host a versioned JSON file in the uv repo that
Shields.io fetches and renders as a live badge.

SOURCE: [shields.io/badges/endpoint-badge](https://shields.io/badges/endpoint-badge) (accessed 2026-03-03)

### 4.2 Badgen `/https` Endpoint Badge

Badgen's `/https` generator turns a live JSON endpoint into a badge. Unlike Shields.io, the
endpoint must return Badgen-compatible data directly as an SVG or a structured response that
Badgen understands.

```text
https://badgen.net/https/<encoded-url>
```

Use RunKit for prototyping: [badgen.net/runkit](https://badgen.net/runkit) lets you write a
serverless function that returns badge data, enabling arbitrary live badges without deploying.

SOURCE: [badgen.net/help](https://badgen.net/help) (accessed 2026-03-03)

### 4.3 Badgen `/memo` Badge

A memo badge stores content server-side and can be updated via HTTP PUT:

```text
# Create/read
GET https://badgen.net/memo/<id>

# Update
PUT https://badgen.net/memo/<id>
Body: { "status": "new-value", "color": "blue" }
```

Use case: CI systems or external scripts that push badge state without a full badge service.

### 4.4 Shields.io Dynamic JSON Badge

Shields.io provides a `/badge/dynamic/json` badge that fetches a JSON URL and extracts a value
using a JSONPath expression:

```text
https://img.shields.io/badge/dynamic/json?url=<URL>&label=<LABEL>&query=<JSONPATH>&color=<COLOR>
```

Example — show a value from a package.json:

```markdown
![Version](https://img.shields.io/badge/dynamic/json?url=https://raw.githubusercontent.com/owner/repo/main/package.json&label=version&query=$.version&color=blue)
```

### 4.5 Self-Hosted Shields.io

The Shields.io server is open source at [badges/shields](https://github.com/badges/shields).
Self-hosting removes rate-limit concerns for internal badge infrastructure.

```bash
# Run via Docker
docker run -p 8080:80 shieldsio/shields

# Or build and run
git clone https://github.com/badges/shields
cd shields && npm install && npm run build && npm start
```

Configuration is via environment variables including `GITHUB_TOKEN` for authenticated GitHub
API requests (higher rate limit).

SOURCE: [badges/shields GitHub](https://github.com/badges/shields) (accessed 2026-03-03)

### 4.6 Self-Hosted Badgen

```bash
docker run -p 3000:3000 amio/badgen
```

Env vars listed in Section 1 control service integrations and endpoints.

---

## 5. Trending Badge Types (2025-2026)

### 5.1 AI Tool Badges

**Claude (Anthropic):**

SimpleIcons includes the Claude logo as `claude` with Anthropic brand color `#D97757`.

```markdown
![Claude](https://img.shields.io/badge/Claude-D97757?logo=claude&logoColor=fff)
![Claude](https://img.shields.io/badge/Claude-D97757?style=for-the-badge&logo=claude&logoColor=white)
```

SOURCE: [inttter/md-badges](https://github.com/inttter/md-badges) (accessed 2026-03-03),
[Ileriayo/markdown-badges](https://github.com/Ileriayo/markdown-badges) (accessed 2026-03-03)

**ChatGPT / OpenAI:**

```markdown
![ChatGPT](https://img.shields.io/badge/ChatGPT-74aa9c?logo=openai&logoColor=white)
![ChatGPT](https://img.shields.io/badge/ChatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)
```

**GitHub Copilot:**

```markdown
![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-000?logo=githubcopilot&logoColor=fff)
```

**Google Gemini:**

```markdown
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-886FBF?logo=googlegemini&logoColor=fff)
```

### 5.2 MCP (Model Context Protocol) Badges

No official MCP icon exists in SimpleIcons as of 2026-03-03. Use the Claude logo as a proxy
or create a static text badge:

```markdown
![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-D97757?logo=claude&logoColor=white)
![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue)
```

For a future-proof approach, use a Shields.io endpoint badge pointing to a hosted JSON file
when an official MCP SimpleIcons slug is added. Monitor:
[SimpleIcons slugs.md](https://github.com/simple-icons/simple-icons/blob/master/slugs.md)

MCP was open-sourced by Anthropic (November 2024) and adopted widely by 2025-2026 across
Claude, ChatGPT, VS Code, and other clients.

SOURCE: [Anthropic — Introducing Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) (accessed 2026-03-03)

### 5.3 Package Manager Badges

**uv (Astral's Python package manager):**

Official endpoint badge from uv's own hosted JSON asset:

```markdown
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
```

This badge shows the current uv version from the official asset file in the uv repository.

SOURCE: [astral-sh/uv README](https://github.com/astral-sh/uv) (accessed 2026-03-03)

**pnpm:**

```markdown
![pnpm](https://img.shields.io/badge/pnpm-F69220?logo=pnpm&logoColor=fff)
![pnpm](https://img.shields.io/badge/pnpm-F69220?style=for-the-badge&logo=pnpm&logoColor=fff)
```

**Bun:**

```markdown
![Bun](https://img.shields.io/badge/Bun-000?logo=bun&logoColor=fff)
![Bun](https://img.shields.io/badge/Bun-000?style=for-the-badge&logo=bun&logoColor=fff)
```

SOURCE: [inttter/md-badges Package Manager section](https://github.com/inttter/md-badges) (accessed 2026-03-03)

### 5.4 Runtime Badges

**Deno:**

```markdown
![Deno](https://img.shields.io/badge/Deno-000?logo=deno&logoColor=fff)
![Deno JS](https://img.shields.io/badge/deno%20js-000000?style=for-the-badge&logo=deno&logoColor=white)
```

**Bun (as runtime):**

```markdown
![Bun](https://img.shields.io/badge/Bun-000?logo=bun&logoColor=fff)
```

**Node.js:**

```markdown
![Node.js](https://img.shields.io/badge/Node.js-6DA55F?logo=node.js&logoColor=white)
```

SOURCE: [Ileriayo/markdown-badges](https://github.com/Ileriayo/markdown-badges) (accessed 2026-03-03)

### 5.5 For the Badge — "Vibe Coded"

For the Badge added a community badge "VIBE CODED" capturing the 2025 trend of AI-assisted
development. It is a community submission (not in the official 135-badge set).

```markdown
[![forthebadge](https://forthebadge.com/images/badges/vibe-coded.svg)](https://forthebadge.com)
```

SOURCE: [forthebadge.com/badges](https://forthebadge.com/badges) (accessed 2026-03-03)

---

## 6. Badge Accessibility

### 6.1 Alt Text Best Practices

Every badge embedded as a Markdown image should have descriptive alt text:

```markdown
![Build status: passing](https://img.shields.io/badge/build-passing-brightgreen)
```

Guidelines:

- Alt text should describe both label and message when both convey meaning
- For purely decorative For the Badge badges, an empty alt (`![](...)`) is acceptable but
  consider using the badge text for screen reader users
- Do not rely on badge image content alone — provide context in surrounding README text
- Shields.io SVGs include `title` and `aria-label` attributes that screen readers can use

SOURCE: [Exploring badge accessibility — usethis](https://usethis.r-lib.org/articles/badge-accessibility.html) (accessed 2026-03-03)

### 6.2 Color Contrast

WCAG AA requires a minimum contrast ratio of 4.5:1 for normal text, 3:1 for large text.

Shields.io auto-selects text color (white or black) based on badge background lightness.
Custom badge colors should be verified with a contrast checker.

Common issues:

- Light yellow (`yellow`, `#FFFF00`) with white text fails contrast
- Avoid relying on color alone to convey meaning — add text label
- `brightgreen` (#4c1) passes with white text; `yellow` (#dfb317) requires dark text

**Verification tool:** [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

SOURCE: [GitHub badges/shields issue #4661](https://github.com/badges/shields/issues/4661) (accessed 2026-03-03),
[Common Mistakes When Using Shields.io Badges](https://infinitejs.com/posts/common-mistakes-shields-io-badges/) (accessed 2026-03-03)

### 6.3 Dark Mode Considerations

GitHub READMEs render in both light and dark mode. Badge behavior:

- **Shields.io**: Badges are SVG files — their colors are fixed. A badge with a white
  background and dark text becomes nearly invisible in GitHub dark mode. Use dark or colorful
  backgrounds that remain visible in both modes.
- **Transparent backgrounds**: Some badge services support transparent backgrounds; these adapt
  to the viewer's theme but may cause text legibility issues.

Recommended approach for dark mode compatibility:

- Use colored (not white or near-white) badge backgrounds
- Avoid `#fff`, `#f0f0f0`, or similar near-white colors as badge background
- For For the Badge badges, the oversized format and high-contrast design generally fares well
  in dark mode
- Test badge appearance by switching GitHub to dark mode before publishing

GitHub supports specifying different images per color scheme via HTML:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="dark-badge.svg">
  <source media="(prefers-color-scheme: light)" srcset="light-badge.svg">
  <img alt="Badge" src="light-badge.svg">
</picture>
```

SOURCE: [Dark Mode UX Design — Influencers Time](https://www.influencers-time.com/designing-dark-mode-for-ux-comfort-and-cognitive-ease/) (accessed 2026-03-03),
[shields/spec/SPECIFICATION.md](https://github.com/badges/shields/blob/master/spec/SPECIFICATION.md) (accessed 2026-03-03)

### 6.4 SVG ARIA Support

Shields.io SVGs contain both `<title>` and `aria-label` attributes. Example from a generated
badge SVG:

```xml
<svg ... aria-label="build: passing">
  <title>build: passing</title>
  ...
</svg>
```

This allows screen readers to announce badge content even when the `alt` attribute on the
surrounding `<img>` is absent or generic. Badgen SVGs include a `<title>` element.

---

## 7. Quick-Reference: Service Comparison

| Feature | Shields.io | Badgen | For the Badge |
|---------|-----------|--------|---------------|
| Static badges | Yes | Yes | Pre-made only |
| Live/dynamic badges | Yes (many services) | Yes (many services) | No |
| Custom text | Yes | Yes | No |
| Styles | 5 | 2 | 1 (fixed oversized) |
| Icon library | SimpleIcons (thousands) | Proprietary set | None |
| Custom logo | Base64-encoded SVG | External SVG URL | No |
| Endpoint/dynamic | `/endpoint?url=` | `/https/` path | No |
| Self-hosted | Yes (Docker) | Yes (Docker) | No |
| Flat/square option | Yes (`flat-square`) | Yes (`flat.badgen.net`) | No |
| Dark mode safe | Depends on colors chosen | Depends on colors chosen | Generally yes |
| SVG ARIA | `aria-label` + `title` | `title` | N/A |

---

## 8. Curated Badge Collections

| Repository | Stars | Focus |
|-----------|-------|-------|
| [Ileriayo/markdown-badges](https://github.com/Ileriayo/markdown-badges) | 16,300+ | Developer branding, profiles, projects — `for-the-badge` style |
| [inttter/md-badges](https://github.com/inttter/md-badges) | — | Extensive Shields.io list with CLI tool `mdbadges-cli` |
| [chetanraj/awesome-github-badges](https://github.com/chetanraj/awesome-github-badges) | 161 | Curated service list (older, last updated 2022) |
| [forthebadge/for-the-badge](https://github.com/forthebadge/for-the-badge) | — | Official source for all FTB badge assets |

SOURCE: [chetanraj/awesome-github-badges GitHub](https://github.com/chetanraj/awesome-github-badges) (accessed 2026-03-03),
[Ileriayo/markdown-badges GitHub](https://github.com/Ileriayo/markdown-badges) (accessed 2026-03-03),
[inttter/md-badges GitHub](https://github.com/inttter/md-badges) (accessed 2026-03-03)
