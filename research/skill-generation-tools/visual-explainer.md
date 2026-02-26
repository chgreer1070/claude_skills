---
name: visual-explainer
description: Agent skill + prompt templates that generate rich, self-contained HTML pages for visual diff reviews, architecture overviews, plan audits, data tables, and project recaps. Replaces ASCII art and terminal tables with styled, browser-rendered diagrams using Mermaid, CSS Grid, HTML tables, Chart.js, and optional AI-generated illustrations.
license: MIT
metadata:
  topic: visual-explainer
  category: skill-generation-tools
  source_url: https://github.com/nicobailon/visual-explainer
  github: nicobailon/visual-explainer
  version: "0.1.4"
  verified: "2026-02-26"
  next_review: "2026-05-26"
---

# visual-explainer

**Research Date**: 2026-02-26
**Source URL**: <https://github.com/nicobailon/visual-explainer>
**GitHub Repository**: <https://github.com/nicobailon/visual-explainer>
**Version at Research**: v0.1.4
**License**: MIT

---

## Overview

visual-explainer is a Claude Code agent skill and collection of prompt templates that generate self-contained HTML pages for technical diagrams, diff reviews, architecture overviews, and data tables. Instead of ASCII art and box-drawing terminal output, it produces browser-rendered pages with real typography, dark/light theme support, interactive Mermaid diagrams with zoom/pan, and optional AI-generated illustrations via surf-cli. The skill ships with five prompt templates (`/generate-web-diagram`, `/diff-review`, `/plan-review`, `/project-recap`, `/fact-check`) covering the most common visualization workflows in code review and project communication.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| Agents default to ASCII art and box-drawing characters for diagrams, producing unreadable output beyond trivial cases | Skill provides design workflow with 11 diagram types routed to appropriate renderers (Mermaid, CSS Grid, HTML tables, Chart.js) |
| Complex terminal tables (4+ rows, 3+ columns) wrap and break in monospace output | Proactive table rendering rule: agent generates HTML page instead of ASCII table automatically |
| No standard way to visualize diff reviews, plan audits, or architecture comparisons in agent workflows | Five prompt templates (`/diff-review`, `/plan-review`, `/project-recap`, `/fact-check`, `/generate-web-diagram`) cover common review workflows |
| Generated diagrams look identical — same dark theme with blue accents every time | Nine aesthetic directions (editorial, blueprint, neon, terminal, IDE-inspired palettes like Dracula/Nord/Catppuccin) with a "swap test" quality check to enforce variety |
| Mermaid theming is unreliable across built-in themes | Forces `theme: 'base'` with full `themeVariables` control; documents CSS override patterns for pixel-perfect SVG styling |
| Agent-generated HTML often contains CSS class collisions | Documents known collision: `.node` class conflicts with Mermaid's internal `.node` SVG class — renames card components to `.ve-card` |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| GitHub Stars | 3,114 | 2026-02-26 |
| Forks | 206 | 2026-02-26 |
| Contributors | 1 | 2026-02-26 |
| Latest Release | v0.1.4 | 2026-02-25 |
| Open Issues | 3 | 2026-02-26 |
| Watchers | 15 | 2026-02-26 |
| Repository Age | 10 days (created 2026-02-16) | 2026-02-26 |
| Primary Language | HTML (100%) | 2026-02-26 |

---

## Key Features

### Diagram Type Routing

- 11 diagram types automatically routed to the optimal renderer based on content
- Mermaid for topology-focused diagrams: flowcharts, sequence diagrams, ER, state machines, mind maps
- CSS Grid for text-heavy architecture overviews where card content (descriptions, code references, tool lists) matters more than connections
- HTML `<table>` for data tables, comparisons, audits — semantic markup with accessibility and copy-paste behavior
- Chart.js via CDN for dashboards with bar, line, pie, and radar charts
- CSS timeline with central line and alternating cards for roadmap views

### Proactive Table Rendering

- Skill instructs the agent to render HTML instead of ASCII for any table with 4+ rows or 3+ columns
- Activates automatically without user prompting — agent opens the HTML page and reports the file path
- Brief text summary still provided in chat alongside the full HTML table

### Five Prompt Templates

- `/generate-web-diagram` — open-ended diagram generation for any topic with aesthetic selection
- `/diff-review` — full diff review page with before/after architecture diagrams, KPI dashboard, Good/Bad/Ugly code review, decision log, and re-entry context; accepts branch, commit hash, `HEAD`, PR number, or range
- `/plan-review` — cross-references an implementation plan file against actual codebase, flags risks and gaps, produces current vs. planned architecture comparison
- `/project-recap` — scans recent git activity for architecture snapshot, decision log, and cognitive debt hotspots; designed for context-switching back to a project
- `/fact-check` — verifies factual accuracy of any review page or plan document against actual code

### Mermaid Deep Theming System

- Enforces `theme: 'base'` — the only Mermaid theme where all `themeVariables` are fully overridable
- Documents complete `themeVariables` set: `primaryColor`, `secondaryColor`, `tertiaryColor`, `lineColor`, `fontFamily`, `fontSize`, note colors
- CSS override patterns for SVG internals: `.nodeLabel`, `.edgeLabel`, `.actor`, `.messageText`, `.er.entityBox`
- `classDef` gotcha documentation: never set `color:` in classDef (breaks opposite color scheme) — use CSS overrides instead; use 8-digit hex fills with alpha for backgrounds that work in both themes
- ELK layout support (`@mermaid-js/layout-elk` CDN import pattern) for complex graphs
- Zoom controls (buttons + Ctrl/Cmd+scroll + drag-to-pan) required on every `.mermaid-wrap` container
- Dark mode handled at initialization time (`window.matchMedia` at load) since Mermaid SVG internals are static

### Reference System for Agent Guidance

- `references/css-patterns.md` — theme setup, depth tiers, node cards, grid layouts, data tables, status badges, KPI cards, before/after panels, SVG connectors, animations (fadeUp, fadeScale, drawIn, countUp), collapsible sections, overflow protection
- `references/libraries.md` — Mermaid CDN + ELK import, deep theming guide, Chart.js, anime.js, 13 Google Font pairings with pairing rationale
- `references/responsive-nav.md` — sticky sidebar TOC on desktop, horizontal scrollable bar on mobile, scroll spy for multi-section pages

### HTML Template Library

- `templates/architecture.html` — CSS Grid card layout, terracotta/sage palette, depth tiers, flow arrows, parallel branch pipeline
- `templates/mermaid-flowchart.html` — Mermaid flowchart with ELK layout, teal/cyan palette, zoom controls
- `templates/data-table.html` — HTML table with KPI cards, status badges, collapsible details, rose/cranberry palette

### Design Quality Enforcement

- "Squint test": hierarchy must be perceptible with blurred vision
- "Swap test": if replacing fonts/colors with a generic dark theme makes it indistinguishable, push further
- Nine named aesthetic directions enforced by workflow: monochrome terminal, editorial, blueprint, neon dashboard, paper/ink, sketch, IDE-inspired (Dracula/Nord/Catppuccin/Solarized/Gruvbox/One Dark), data-dense, gradient mesh
- `prefers-reduced-motion` respected in all animation patterns

### Optional AI Image Generation

- Detects `surf-cli` availability with `which surf`; skips image generation gracefully if absent
- Generates images via Gemini and embeds as base64 in self-contained HTML
- Use cases: hero banners, conceptual illustrations for abstract systems, educational diagrams
- Prompt craft guidance: match page palette, specify style and dominant colors, `--aspect-ratio 16:9` for banners

---

## Technical Architecture

### Workflow

```text
SKILL.md (workflow + design principles)
    |
    v
references/           <- agent reads before each generation
├── css-patterns.md   (layouts, animations, theming, depth tiers)
├── libraries.md      (Mermaid theming, Chart.js, anime.js, font pairings)
└── responsive-nav.md (sticky sidebar TOC for multi-section pages)
    |
    v
templates/            <- agent reads the matching reference template
├── architecture.html (CSS Grid cards — terracotta/sage palette)
├── mermaid-flowchart.html (Mermaid + ELK — teal/cyan palette)
└── data-table.html   (tables with KPIs and badges — rose/cranberry palette)
    |
    v
~/.agent/diagrams/filename.html -> opens in browser
```

### Generation Strategy

The agent follows a four-step workflow defined in SKILL.md:

1. **Think** (aesthetic selection): Commit to one of nine named aesthetics before writing HTML. Vary across generations.
2. **Structure** (reference reading): Read the appropriate template and reference files before generating. Never memorize — read fresh each time.
3. **Style** (design principles application): Typography, CSS custom properties for full palette, surface depth, background atmosphere, animation with stagger.
4. **Deliver** (file write + browser open): Write to `~/.agent/diagrams/`, open with `open` (macOS) or `xdg-open` (Linux), report file path.

### Output Format

Every diagram is a single self-contained `.html` file:

- No external assets except CDN links (Google Fonts, optional JS libraries)
- All CSS inline in `<style>` tags using CSS custom properties
- Both light and dark themes via `prefers-color-scheme` media query
- Mermaid, Chart.js, anime.js loaded from jsDelivr CDN when needed

### Known Technical Constraints

- Mermaid's `.node` class used internally for SVG `<g>` transform positioning — page-level `.node` styles leak into diagrams; fix is `.ve-card` namespace
- `stateDiagram-v2` labels reject colons, parentheses, `<br/>`, most special characters — documented fallback to `flowchart LR` for complex labels
- Sequence diagram messages cannot be quoted or escaped — curly braces, brackets, ampersands cause silent parse failures
- Mermaid ELK layout requires separate `@mermaid-js/layout-elk` CDN import; silently falls back to dagre without it
- Mermaid initializes once at load time — cannot reactively switch themes on OS theme change; Mermaid SVG internals are static, page CSS responds dynamically
- `handDrawn` mode removed in v0.1.4 — Rough.js hachure fills render unreadable diagonal scribbles with no user override

### Installation Method

- Primary: `pi install https://github.com/nicobailon/visual-explainer` — installs skill and all slash commands in one step via `package.json` with `"keywords": ["pi-package"]`
- Alternative: `git clone https://github.com/nicobailon/visual-explainer.git ~/.claude/skills/visual-explainer`

---

## Installation & Usage

### Install

```bash
# Pi package manager (installs skill + all prompt templates)
pi install https://github.com/nicobailon/visual-explainer

# Manual clone
git clone https://github.com/nicobailon/visual-explainer.git ~/.claude/skills/visual-explainer
```

### Prompt Templates

```text
# Generate any diagram
/generate-web-diagram

# Diff review (branch vs main by default)
/diff-review
/diff-review main..HEAD
/diff-review abc123
/diff-review #42

# Plan review (cross-references plan file against codebase)
/plan-review ~/docs/refactor-plan.md

# Project mental model snapshot
/project-recap

# Verify accuracy of a review page or plan doc
/fact-check
```

### Natural Language Activation

```text
draw a diagram of our authentication flow
explain the system architecture visually
compare these requirements against the implementation plan
```

The skill activates automatically when the agent would otherwise render a complex ASCII table.

### Output Location

```bash
# Files written to:
~/.agent/diagrams/

# Agent opens automatically:
# macOS:
open ~/.agent/diagrams/filename.html
# Linux:
xdg-open ~/.agent/diagrams/filename.html
```

---

## Relevance to Claude Code Development

### Applications

- **Diff review automation**: `/diff-review` generates publication-quality HTML pages directly from git refs within Claude Code sessions — useful for PR reviews and architecture documentation
- **Plan validation**: `/plan-review` cross-references implementation plans against actual codebase, producing gap analysis and risk assessment — applicable to backlog planning workflows
- **Visual skill output**: Demonstrates a pattern where skill output is an HTML artifact opened in the browser rather than terminal text — relevant for skills that produce complex structured output
- **Proactive rendering heuristic**: The 4-row/3-column table threshold for switching to HTML is a concrete, implementable rule that could apply to any skill generating tabular data

### Patterns Worth Adopting

- **Reference-before-generate**: The workflow mandates reading reference files fresh before each generation rather than using memorized patterns — reduces drift from accumulated assumptions; applicable to any skill with complex output formatting
- **Named aesthetic directions**: Codifying nine aesthetic directions by name prevents generic defaults and enforces variety across generations — transferable pattern for any skill that produces visual or formatted output
- **Quality checks as workflow steps**: Squint test, swap test, overflow check, zoom controls check are embedded in the workflow as required verification before delivery — models how quality gates can be part of a skill workflow rather than post-hoc review
- **Semi-transparent fills for dual-theme CSS**: Using 8-digit hex fills (e.g., `fill:#b5761433`) that layer correctly over both light and dark backgrounds — practical pattern for any skill generating themed HTML
- **Graceful optional dependency handling**: `which surf` detection with silent skip avoids blocking on absent optional tools — applicable to any skill with optional integrations
- **CSS namespace discipline**: Documenting known third-party library class conflicts (`.node` vs Mermaid's `.node`) and providing namespaced alternatives (`.ve-card`) is a transferable practice for skills using external JS libraries

### Integration Opportunities

- **Claude Code skill output format**: visual-explainer establishes an HTML artifact output pattern that claude_skills could adopt for skills producing complex structured output (research summaries, diff analysis, plan audits)
- **Backlog visualization**: `/plan-review` pattern maps directly onto backlog item planning — a version of this skill could render backlog items as structured HTML pages
- **Research entry presentation**: Research entries in `./research/` could be rendered as styled HTML pages using this skill's table and card patterns rather than read as raw markdown
- **CI diff reports**: `/diff-review` prompt template could be adapted as a GitHub Actions step to generate HTML diff reports as PR artifacts
- **Skill compatibility with pi packages**: `package.json` with `"keywords": ["pi-package"]` and `"pi": {"skills": ["./"], "prompts": ["./prompts"]}` is the standard format for pi-installable skill packages — directly applicable to publishing claude_skills entries

---

## References

- [GitHub Repository](https://github.com/nicobailon/visual-explainer) (accessed 2026-02-26)
- [README.md](https://github.com/nicobailon/visual-explainer/blob/main/README.md) (accessed 2026-02-26)
- [SKILL.md](https://github.com/nicobailon/visual-explainer/blob/main/SKILL.md) (accessed 2026-02-26)
- [CHANGELOG.md](https://github.com/nicobailon/visual-explainer/blob/main/CHANGELOG.md) (accessed 2026-02-26)
- [references/libraries.md](https://github.com/nicobailon/visual-explainer/blob/main/references/libraries.md) (accessed 2026-02-26)
- [package.json](https://github.com/nicobailon/visual-explainer/blob/main/package.json) (accessed 2026-02-26)
- [GitHub API — repository metadata](https://api.github.com/repos/nicobailon/visual-explainer) (accessed 2026-02-26)
- [GitHub API — latest release v0.1.4](https://api.github.com/repos/nicobailon/visual-explainer/releases/latest) (accessed 2026-02-26)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-26 |
| Version at Verification | v0.1.4 |
| Next Review Recommended | 2026-05-26 |
