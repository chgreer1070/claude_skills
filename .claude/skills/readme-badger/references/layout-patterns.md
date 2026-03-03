# Badge Layout Patterns and Best Practices

Reference for badge arrangement, grouping conventions, project-type selection, anti-patterns,
and HTML vs Markdown syntax decisions.

Sources gathered from primary repositories (accessed 2026-03-03).

---

## 1. Layout Patterns

### Pattern A: Single Centered Row (`<p align="center">`)

The most widely used pattern among mature Python and JS projects. All badges live inside
a single `<p align="center">` block, rendered inline with whitespace between them.

**Example — Vue 2** (SOURCE: <https://github.com/vuejs/vue> accessed 2026-03-03):

```html
<p align="center">
  <a href="https://circleci.com/gh/vuejs/vue/tree/dev">
    <img src="https://img.shields.io/circleci/project/github/vuejs/vue/dev.svg?sanitize=true" alt="Build Status">
  </a>
  <a href="https://codecov.io/github/vuejs/vue?branch=dev">
    <img src="https://img.shields.io/codecov/c/github/vuejs/vue/dev.svg?sanitize=true" alt="Coverage Status">
  </a>
  <a href="https://www.npmjs.com/package/vue">
    <img src="https://img.shields.io/npm/v/vue.svg?sanitize=true" alt="Version">
  </a>
  <a href="https://www.npmjs.com/package/vue">
    <img src="https://img.shields.io/npm/l/vue.svg?sanitize=true" alt="License">
  </a>
</p>
```

**When to use**: Projects with 3–8 badges that fit on one row without crowding. Centered
presentation signals a polished, professional README.

**Key properties**:

- Each `<img>` is wrapped in `<a>` for click-through
- `alt` attributes are descriptive, not empty
- `sanitize=true` parameter prevents SVG XSS in older GitHub rendering (now optional)
- Logo above badges in a separate `<p align="center">` block

---

### Pattern B: Two-Tier (Hero Badge + Metadata Row)

First row: one large identity badge (project-branded, custom endpoint badge). Second row:
operational metadata badges (CI, version, license, downloads).

**Example — Ruff** (SOURCE: <https://github.com/astral-sh/ruff> accessed 2026-03-03):

```markdown
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![image](https://img.shields.io/pypi/v/ruff.svg)](https://pypi.python.org/pypi/ruff)
[![image](https://img.shields.io/pypi/l/ruff.svg)](https://github.com/astral-sh/ruff/blob/main/LICENSE)
[![image](https://img.shields.io/pypi/pyversions/ruff.svg)](https://pypi.python.org/pypi/ruff)
[![Actions status](https://github.com/astral-sh/ruff/workflows/CI/badge.svg)](https://github.com/astral-sh/ruff/actions)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.com/invite/astral-sh)
```

**Example — uv** (SOURCE: <https://github.com/astral-sh/uv> accessed 2026-03-03):

```markdown
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![image](https://img.shields.io/pypi/v/uv.svg)](https://pypi.python.org/pypi/uv)
[![image](https://img.shields.io/pypi/l/uv.svg)](https://pypi.python.org/pypi/uv)
[![image](https://img.shields.io/pypi/pyversions/uv.svg)](https://pypi.python.org/pypi/uv)
[![Actions status](https://github.com/astral-sh/uv/actions/workflows/ci.yml/badge.svg)](https://github.com/astral-sh/uv/actions)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.gg/astral-sh)
```

The Astral pattern: custom branded endpoint badge first, then PyPI version/license/pyversions,
then CI, then community (Discord).

**When to use**: Projects with a strong brand identity that want to promote their own
badge as a "use this project" signal (e.g., "Built with uv").

---

### Pattern C: Left-Aligned Inline (After H1)

Badges appear on the same line as (or immediately after) the `# Title` heading, using
standard Markdown syntax. No centering.

**Example — React** (SOURCE: <https://github.com/facebook/react> accessed 2026-03-03):

```markdown
# [React](https://react.dev/) &middot; [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/facebook/react/blob/main/LICENSE) [![npm version](https://img.shields.io/npm/v/react.svg?style=flat)](https://www.npmjs.com/package/react) [![(Runtime) Build and Test](https://github.com/facebook/react/actions/workflows/runtime_build_and_test.yml/badge.svg)](https://github.com/facebook/react/actions/workflows/runtime_build_and_test.yml) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://legacy.reactjs.org/docs/how-to-contribute.html#your-first-pull-request)
```

**Example — Vue 3 core** (SOURCE: <https://github.com/vuejs/core> accessed 2026-03-03):

```markdown
# vuejs/core [![npm](https://img.shields.io/npm/v/vue.svg)](https://www.npmjs.com/package/vue) [![build status](https://github.com/vuejs/core/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vuejs/core/actions/workflows/ci.yml) [![Download](https://img.shields.io/npm/dm/vue)](https://www.npmjs.com/package/vue)
```

**When to use**: Projects that prefer minimal decoration. Works best with 2–4 compact
badges. Common in framework source repos where the README is developer-facing rather than
marketing-facing.

---

### Pattern D: Left-Aligned Stacked (One Badge Per Line)

Each badge on its own line in Markdown. Renders as a vertical list (wrapped inline in
GitHub's renderer, but each occupies its own rendered paragraph if separated by blank lines,
or flows inline if not).

**Example — Pydantic** (SOURCE: <https://github.com/pydantic/pydantic> accessed 2026-03-03):

```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/pydantic/pydantic/ci.yml?branch=main&logo=github&label=CI)](https://github.com/pydantic/pydantic/actions?query=event%3Apush+branch%3Amain+workflow%3ACI)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://static.pepy.tech/badge/pydantic/month)](https://pepy.tech/project/pydantic)
[![versions](https://img.shields.io/pypi/pyversions/pydantic.svg)](https://github.com/pydantic/pydantic)
[![license](https://img.shields.io/github/license/pydantic/pydantic.svg)](https://github.com/pydantic/pydantic/blob/main/LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://docs.pydantic.dev/latest/contributing/#badges)
[![llms.txt](https://img.shields.io/badge/llms.txt-green)](https://docs.pydantic.dev/latest/llms.txt)
```

Pydantic uses 9 badges on consecutive lines — GitHub wraps them into a horizontal flow.
This is the most common Python library pattern for projects with 6–12 badges.

**When to use**: When you have many badges (6+) and want them scannable in source while
flowing naturally in the rendered view.

---

### Pattern E: Reference-Style Badges

Badge URLs defined as reference links at the bottom of the file, referenced inline in the text.
Separates URL clutter from content.

**Example — Tokio** (SOURCE: <https://github.com/tokio-rs/tokio> accessed 2026-03-03):

```markdown
[![Crates.io][crates-badge]][crates-url]
[![MIT licensed][mit-badge]][mit-url]
[![Build Status][actions-badge]][actions-url]
[![Discord chat][discord-badge]][discord-url]

[crates-badge]: https://img.shields.io/crates/v/tokio.svg
[crates-url]: https://crates.io/crates/tokio
[mit-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[mit-url]: https://github.com/tokio-rs/tokio/blob/master/LICENSE
[actions-badge]: https://github.com/tokio-rs/tokio/workflows/CI/badge.svg
[actions-url]: https://github.com/tokio-rs/tokio/actions?query=workflow%3ACI+branch%3Amaster
[discord-badge]: https://img.shields.io/discord/500028886025895936.svg?logo=discord&style=flat-square
[discord-url]: https://discord.gg/tokio
```

**When to use**: Rust crates — this is the dominant Rust community convention. Also suitable
for any project maintaining many long badge URLs. Makes diffs cleaner because URL changes
don't touch the header section.

---

### Pattern F: Per-Section Badges (Ecosystem Table)

Badges embedded in a table alongside project names. Each row = one sub-project with its
live version badge.

**Example — Vue 2 ecosystem table** (SOURCE: <https://github.com/vuejs/vue> accessed 2026-03-03):

```markdown
| Project               | Status                                    | Description                |
| --------------------- | ----------------------------------------- | -------------------------- |
| [vue-router]          | [![vue-router-status]][vue-router-package] | Single-page application routing |
| [vuex]                | [![vuex-status]][vuex-package]             | Large-scale state management    |

[vue-router-status]: https://img.shields.io/npm/v/vue-router.svg
[vue-router-package]: https://npmjs.com/package/vue-router
```

**When to use**: Monorepos or projects with multiple related packages. The table pattern
is the only case where badges appear mid-document rather than at the top.

---

### Pattern G: `<div align="center">` Block

Alternative to `<p align="center">`. Used when content includes headings or multiple
block-level elements that need centering.

**Example — henriquesebastiao/badges** (SOURCE: <https://github.com/henriquesebastiao/badges> accessed 2026-03-03):

```html
<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/henriquesebastiao/badges?style=flat&color=FFD700)](https://github.com/henriquesebastiao/badges/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/henriquesebastiao/badges?style=flat)](https://github.com/henriquesebastiao/badges/network)
[![GitHub License](https://img.shields.io/github/license/henriquesebastiao/badges?style=flat&color=22c55e)](https://github.com/henriquesebastiao/badges/blob/main/LICENSE)

</div>
```

**When to use**: When centering a mix of badges and other block elements (headings,
subheadings, descriptive text). `<div>` is necessary when `<p>` would not contain
block-level children correctly.

---

## 2. Badge Grouping Conventions

Observed grouping order across 8+ analyzed repositories
(uv, Ruff, Pydantic, FastAPI, Black, Tokio, Vue 2/3, React):

### Standard Group Order

```text
1. Project identity badge (custom endpoint, branded badge) — optional
2. CI / build status
3. Code coverage
4. Package version (PyPI, npm, crates.io)
5. Downloads
6. Python/Node/Rust version compatibility
7. License
8. Community (Discord, Gitter, chat)
9. Contributor badge — optional
10. Vanity/fun (PRs Welcome, for-the-badge style) — optional
```

### Group Descriptions

**Project identity**: A custom shields.io endpoint badge using the project's own JSON file.
Astral projects (uv, Ruff) publish `assets/badge/v0.json` or `assets/badge/v2.json` in
their repo. Pydantic publishes `docs/badge/v2.json`. This badge acts as a "seal of
authenticity" and signals current major version.

**Build/CI status**: GitHub Actions workflow badge, CircleCI badge, or similar. Always
first among operational badges — it is the highest-signal badge for whether the project
is healthy. Use the workflow file path format (`actions/workflows/{name}.yml/badge.svg`)
rather than the deprecated workflow name format.

**Coverage**: Codecov, Coveralls, or custom coverage badge. Follows CI directly because
it is also a health signal.

**Package version**: Shields.io auto-fetches from PyPI (`/pypi/v/{pkg}`), npm (`/npm/v/{pkg}`),
or crates.io (`/crates/v/{pkg}`). Links to the registry page.

**Downloads**: `pepy.tech` for Python (`/badge/{pkg}/month`), `npm` for JS. Monthly
downloads preferred over total (avoids stale large numbers on inactive projects).

**Python/Node/Rust version**: `img.shields.io/pypi/pyversions/{pkg}` — communicates
compatibility range at a glance.

**License**: Last operational badge. Low-urgency information, consistent with how
license is footer-positioned in documentation generally.

**Community**: Discord, Gitter, Slack. Placed after operational badges because it is
engagement-oriented rather than project-health oriented.

---

## 3. Badge Selection by Project Type

### Python Libraries / CLIs

Minimum viable set:

```markdown
[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions)
[![PyPI](https://img.shields.io/pypi/v/{package}.svg)](https://pypi.org/project/{package}/)
[![Python versions](https://img.shields.io/pypi/pyversions/{package}.svg)](https://pypi.org/project/{package}/)
[![License](https://img.shields.io/github/license/{owner}/{repo}.svg)](https://github.com/{owner}/{repo}/blob/main/LICENSE)
```

Full set adds:

```markdown
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/{owner}/{repo}.svg)](...)
[![Downloads](https://static.pepy.tech/badge/{package}/month)](https://pepy.tech/project/{package})
[![conda-forge](https://img.shields.io/conda/dn/conda-forge/{package}.svg)](https://anaconda.org/conda-forge/{package}/)
```

SOURCE: Observed in Pydantic, FastAPI, Black, uv, Ruff READMEs (accessed 2026-03-03).

---

### JavaScript / TypeScript Packages

Minimum viable set:

```markdown
[![npm](https://img.shields.io/npm/v/{package}.svg)](https://www.npmjs.com/package/{package})
[![Build](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions)
[![License](https://img.shields.io/npm/l/{package}.svg)](./LICENSE)
```

Full set adds:

```markdown
[![npm downloads](https://img.shields.io/npm/dm/{package}.svg)](https://www.npmjs.com/package/{package})
[![bundle size](https://img.shields.io/bundlephobia/minzip/{package})](https://bundlephobia.com/package/{package})
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
```

SOURCE: Vue 2, Vue 3, React READMEs (accessed 2026-03-03); Badges4-README.md-Profile
<https://github.com/alexandresanlim/Badges4-README.md-Profile> (accessed 2026-03-03).

---

### Rust Crates

Minimum viable set (reference-style convention):

```markdown
[![Crates.io][crates-badge]][crates-url]
[![MIT licensed][mit-badge]][mit-url]
[![Build Status][actions-badge]][actions-url]

[crates-badge]: https://img.shields.io/crates/v/{crate}.svg
[crates-url]: https://crates.io/crates/{crate}
[mit-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[mit-url]: ./LICENSE
[actions-badge]: https://github.com/{owner}/{repo}/workflows/CI/badge.svg
[actions-url]: https://github.com/{owner}/{repo}/actions
```

Full set adds:

```markdown
[discord-badge]: https://img.shields.io/discord/{server-id}.svg?logo=discord&style=flat-square
[docs-badge]: https://docs.rs/{crate}/badge.svg
[docs-url]: https://docs.rs/{crate}
```

SOURCE: Tokio README <https://github.com/tokio-rs/tokio> (accessed 2026-03-03).

---

### Claude Code Plugins

Claude Code plugins are distributed via the Claude Code marketplace. The `SKILL.md` is
the primary consumer-facing surface. Badges communicate:

1. **Plugin compatibility**: Claude Code version constraint
2. **License**: MIT or similar (required for marketplace)
3. **Skills count**: number of skills included
4. **Stability**: stable / beta / experimental

Recommended set for Claude Code plugins — use `flat` or `flat-square` style, not
`for-the-badge` (too large for skill documentation contexts):

```markdown
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-D97757?logo=claude&logoColor=white)](https://claude.ai/code)
[![License](https://img.shields.io/github/license/{owner}/{repo}?color=22c55e)](./LICENSE)
[![Skills](https://img.shields.io/badge/skills-{N}-blue)](./SKILL.md)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)](./CHANGELOG.md)
```

For the Claude badge, use the Simple Icons slug `claude` with color `D97757`
(Anthropic brand orange). SOURCE: Badges4-README.md-Profile AI section
<https://github.com/alexandresanlim/Badges4-README.md-Profile> (accessed 2026-03-03).

Optional additions for plugin repos:

```markdown
[![GitHub Actions](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{owner}/{repo}/actions)
[![last commit](https://img.shields.io/github/last-commit/{owner}/{repo})](https://github.com/{owner}/{repo}/commits)
```

**Layout recommendation for Claude Code plugins**: Left-aligned stacked (Pattern D)
works best. Plugin READMEs are read in narrow panels; centering does not help and
`<p align="center">` adds HTML noise to skill files consumed by AI agents.

---

### Documentation-Only Repos

Keep badges minimal — a documentation repo has no package version or CI test coverage:

```markdown
[![License](https://img.shields.io/github/license/{owner}/{repo})](./LICENSE)
[![last commit](https://img.shields.io/github/last-commit/{owner}/{repo})](https://github.com/{owner}/{repo}/commits)
[![GitHub stars](https://img.shields.io/github/stars/{owner}/{repo}?style=social)](https://github.com/{owner}/{repo}/stargazers)
```

Avoid CI badges unless the repo has its own build pipeline (e.g., docs linting, link checking).

---

### Monorepos with Multiple Packages

Use the per-section table pattern (Pattern F):

```markdown
| Package | Version | Downloads |
|---------|---------|-----------|
| [core](./packages/core) | [![npm](https://img.shields.io/npm/v/@org/core.svg)](https://www.npmjs.com/package/@org/core) | [![downloads](https://img.shields.io/npm/dm/@org/core)](https://www.npmjs.com/package/@org/core) |
| [plugin-a](./packages/plugin-a) | [![npm](https://img.shields.io/npm/v/@org/plugin-a.svg)](https://www.npmjs.com/package/@org/plugin-a) | [![downloads](https://img.shields.io/npm/dm/@org/plugin-a)](https://www.npmjs.com/package/@org/plugin-a) |
```

Top-level badges at the repo header cover only repo-wide signals: overall CI, license,
community. Per-package version and download badges belong in the table.

SOURCE: Vue 2 ecosystem table pattern (accessed 2026-03-03).

---

## 4. Anti-Patterns

### 4.1 Badge Overload

More than 12 badges in the header. Signs of overload:

- Multiple badges carrying the same information (e.g., three different "code quality" badges)
- Badges that merely list tech stack with no live data (static "Built with Python" repeated
  next to a PyPI version badge that already implies Python)
- Social vanity badges duplicating information available on the GitHub repo page itself
  (star count, fork count, watcher count — all visible in the GitHub UI header)

**Rule**: If removing a badge loses no actionable information, remove it.

---

### 4.2 Broken / Stale Badges

Badges pointing to deleted CI workflows, retired services (Travis CI, older CodeClimate
endpoints), or renamed packages. GitHub renders broken image placeholders — they appear
as `[badge name]` text or broken image icons, signaling abandonment.

**Prevention**:

- Use GitHub Actions workflow badges via the file path format, not the deprecated
  workflow-name format: `actions/workflows/{file}.yml/badge.svg` not `workflows/{Name}/badge.svg`
- Audit badges when migrating CI providers
- Prefer official shields.io dynamic badges over service-specific badge URLs where possible

---

### 4.3 Mixed Styles

Combining `flat`, `flat-square`, `for-the-badge`, and `social` in the same badge row.
Each style has a different height and visual weight. The result looks unintentional.

**Rule**: Pick one style per README and apply it consistently. Shields.io styles in order
of common usage:

1. `flat` — default, most widely used
2. `flat-square` — popular in Rust ecosystem (Tokio uses it for Discord badge)
3. `for-the-badge` — high impact, profile READMEs and landing pages
4. `social` — for star/follow counts, visually distinct by design
5. `plastic` — largely historical, avoid in new projects

SOURCE: Shields.io styles documented at <https://shields.io/#styles> referenced in
Ileriayo/markdown-badges tips section (accessed 2026-03-03).

---

### 4.4 Vanity Badges with No Information

Examples of zero-information badges:

- `Made with Love` — not actionable
- `Awesome` self-awarded — no criteria
- `Open Source` — implied by being on GitHub
- `Maintained` — cannot be verified from the badge; goes stale when maintenance stops

**Exception**: `PRs Welcome` has legitimate utility — it signals contribution policy
to potential contributors who may not know whether unsolicited PRs are welcome.

---

### 4.5 Unlinked Badges

A badge with no surrounding `<a>` or `[...]` link. Provides information but no navigation.

```markdown
# Wrong — badge leads nowhere
![Version](https://img.shields.io/pypi/v/mypackage.svg)

# Correct — badge links to PyPI page
[![Version](https://img.shields.io/pypi/v/mypackage.svg)](https://pypi.org/project/mypackage/)
```

**Exception**: Purely decorative static badges (e.g., technology stack badges in a
profile README) where there is no meaningful destination URL.

---

### 4.6 Raster Badges Where SVG Works

PNG badges at specific pixel sizes look blurry on Retina/HiDPI displays. SVG (the
Shields.io default) scales cleanly. Use raster only when SVG is not rendered correctly —
Slack embeds and HTML email are the documented cases. SOURCE: awesome-badges raster
badges section <https://github.com/badges/awesome-badges> (accessed 2026-03-03).

---

## 5. HTML vs Markdown Syntax

### When to Use `![alt](url)` Markdown Syntax

Use standard Markdown image syntax when:

- No wrapping link is needed (rare)
- The badge is inside a table cell (`<a>` tags in table cells can cause rendering issues
  in some Markdown renderers)
- The file will be processed by a Markdown-strict parser that does not allow inline HTML

```markdown
[![License](https://img.shields.io/github/license/owner/repo)](https://github.com/owner/repo/blob/main/LICENSE)
```

The `[![alt](img-url)](link-url)` form is the canonical Markdown badge pattern. It renders
in all GitHub Markdown contexts.

---

### When to Use `<img>` Tags

Use `<img>` inside HTML blocks when:

- You need `width` or `height` control (e.g., logo images sized to match badge height)
- The badge is inside a `<p align="center">` or `<div align="center">` container where
  you also need `<a>` wrapping with `target="_blank"`
- You need `srcset` or `<picture>` for dark/light mode variants

```html
<p align="center">
  <a href="https://github.com/fastapi/fastapi/actions" target="_blank">
    <img src="https://github.com/fastapi/fastapi/actions/workflows/test.yml/badge.svg" alt="Test">
  </a>
</p>
```

SOURCE: FastAPI README pattern (accessed 2026-03-03); Black README pattern (accessed 2026-03-03).

---

### When to Wrap in `<a>` Links

Always wrap badge `<img>` tags in `<a>` links when the badge communicates live data
(CI status, version, coverage). This is the dominant convention across all analyzed repos.

The only case to omit the link is a static decorative badge where no destination exists
or where the badge is already descriptive enough that navigation would add no value.

---

### `target="_blank"` on Badge Links

FastAPI uses `target="_blank"` on every badge link. Vue 2 does not. Neither is wrong.

**Rule**: Use `target="_blank"` when the badge links to an external service (CI provider,
PyPI, npm) and you want the user to stay on the GitHub README while checking the destination.
Omit it for links within the same GitHub org or for simplicity.

---

## 6. Style Consistency Reference

| Style | Height | Use Case |
|-------|--------|----------|
| `flat` | 20px | Default — works everywhere |
| `flat-square` | 20px | Rust ecosystem preference |
| `for-the-badge` | 28px | Landing pages, profile READMEs |
| `social` | 20px | Star/fork counts only |
| `plastic` | 18px | Legacy only, avoid |

SOURCE: Ileriayo/markdown-badges tips section, Shields.io documentation
<https://shields.io/#styles> (accessed 2026-03-03);
henriquesebastiao/badges styles table (accessed 2026-03-03).

---

## 7. Badge Services Reference

| Service | Best For | URL Pattern |
|---------|----------|-------------|
| [Shields.io](https://shields.io/) | Everything — the standard | `https://img.shields.io/...` |
| [Badgen.net](https://badgen.net/) | Speed, alternative to Shields | `https://badgen.net/...` |
| [Pepy.tech](https://pepy.tech/) | Python download counts | `https://static.pepy.tech/badge/{pkg}` |
| [coverage-badge (samuelcolvin)](https://coverage-badge.samuelcolvin.workers.dev/) | Python coverage | `https://coverage-badge.samuelcolvin.workers.dev/{owner}/{repo}.svg` |
| [Visitor badge](https://visitorbadge.io/) | Profile visitor count | `https://api.visitorbadge.io/api/visitors?path=...` |

SOURCE: awesome-badges dynamic badge services list (accessed 2026-03-03);
Pydantic README coverage badge URL (accessed 2026-03-03).
