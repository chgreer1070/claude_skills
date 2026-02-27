---
name: Validate is-fast for Web Content Extraction
description: "Test is-fast CLI tool on host with unrestricted network access.\n**Validation steps**:\n- Install: `curl --proto '=https' --tlsv1.2 -LsSf https://github.com/Magic-JD/is-fast/releases/latest/download/is-fast-installer.sh | sh`\n- Test: `is-fast --direct https://code.claude.com/docs/en/skills --piped`\n- Verify it extracts text content from JS-rendered pages\n- Compare output quality with curl, lynx, w3m\n- Test CSS selector filtering with `--selector`\n**Blocked on 2026-02-05**: DNS resolution failed in restricted environment"
metadata:
  topic: validate-is-fast-for-web-content-extraction
  source: Session experimentation 2026-02-05
  added: '2026-02-05'
  priority: P2
  type: Feature
  status: open
  issue: '#127'
  groomed: '2026-02-27'
  last_synced: '2026-02-27T10:43:11Z'
---

## Fact-Check

**Date**: 2026-02-27
**Claims checked**: 5
**VERIFIED**: 4 | **REFUTED**: 1 | **INCONCLUSIVE**: 0

| Claim | Verdict | Source |
|-------|---------|--------|
| Install URL valid (curl installer script) | VERIFIED | [GitHub release assets](https://github.com/Magic-JD/is-fast/releases/latest) (accessed 2026-02-27) |
| `--direct` flag opens URL in TUI | VERIFIED | [README](https://github.com/Magic-JD/is-fast) (accessed 2026-02-27) |
| `--piped` flag outputs to stdout | VERIFIED | [README](https://github.com/Magic-JD/is-fast) (accessed 2026-02-27) |
| `--selector` flag for CSS filtering | VERIFIED | [README](https://github.com/Magic-JD/is-fast) (accessed 2026-02-27) |
| Extracts text from JS-rendered pages | **REFUTED** | [Cargo.toml](https://raw.githubusercontent.com/Magic-JD/is-fast/main/Cargo.toml) — uses `ureq` (plain HTTP) + `scraper` (static HTML parser), no browser engine |

## RT-ICA

**Goal**: Confirm whether is-fast is a viable CLI tool for extracting web content in terminal/agent environments

| # | Condition | Status | Info needed |
|---|-----------|--------|-------------|
| 1 | Tool installable via documented method | AVAILABLE | Install script verified via HTTP 200 and README |
| 2 | --direct flag opens URL in viewer | AVAILABLE | Documented in README with examples |
| 3 | --piped flag outputs to stdout | AVAILABLE | Documented in README with examples |
| 4 | --selector flag filters by CSS selector | AVAILABLE | Documented in README with examples |
| 5 | Extracts JS-rendered page content | MISSING | REFUTED — uses ureq (HTTP GET) + scraper (static HTML), no browser engine |
| 6 | Unrestricted network access for testing | MISSING | Blocked on DNS resolution in restricted env |
| 7 | Comparison baseline (curl/lynx/w3m output) | DERIVABLE | Can be produced during validation testing |
| 8 | Tool version and release status | AVAILABLE | v0.17.7, 2025-11-03, 164 stars, Rust, not archived |

**Decision**: APPROVED (with corrections)
**Missing**: JS rendering claim must be removed from description. Needs unrestricted network host.

## Groomed (2026-02-27)

### Reproducibility

1. Obtain host with unrestricted network access (DNS, HTTP/HTTPS)
2. Install is-fast: `curl --proto '=https' --tlsv1.2 -LsSf https://github.com/Magic-JD/is-fast/releases/latest/download/is-fast-installer.sh | sh`
3. Verify installation: `is-fast --version` (expect v0.17.7+)
4. Test --direct flag: `is-fast --direct https://example.com`
5. Test --piped flag: `is-fast --direct https://example.com --piped`
6. Test --selector flag: `is-fast --direct https://example.com --piped --selector "h1"`
7. Compare text extraction output with curl, lynx, and w3m on same URLs (3+ test URLs)

### Priority

5/10 — P2 item validating a static-HTML extraction tool. Useful as baseline comparison but lower priority than JS-capable alternatives (carbonyl, agent-browser). Part of web tooling evaluation roadmap.

### Impact

- Completes comparison matrix across is-fast, curl, lynx, w3m, carbonyl, agent-browser
- Determines if is-fast is suitable for agent workflows requiring fast, reliable text extraction from static HTML
- Establishes baseline for plain-HTTP extraction (fastest method when JS not needed)

### Scope

- Install and verify is-fast v0.17.7+ on unrestricted host
- Test --direct, --piped, and --selector flags against 3+ URLs
- Compare output quality with curl, lynx, w3m
- Document that is-fast does NOT render JavaScript (static HTML only)
- Write validation report with findings and recommendation

### Output / Evidence

- Installation success: `is-fast --version` output
- Flag tests: stdout from --piped tests on 3+ URLs
- Comparison table: output quality vs curl/lynx/w3m (formatting, content completeness, selector accuracy)
- Validation report documenting findings and recommendation for Claude Code workflows

### Dependencies

- **Requires**: Host with unrestricted network access (DNS + HTTP/HTTPS outbound)
- **Related items**: [Carbonyl Browser Integration](./p2-carbonyl-browser-integration-for-claude-code.md) (#126), [Validate agent-browser](./p2-validate-agent-browser-for-web-automation.md) (#128), [Validate carbonyl](./p2-validate-carbonyl-terminal-browser.md) (#129)

### Research

No existing research/ entry for is-fast. Key facts from primary sources:
- [Magic-JD/is-fast](https://github.com/Magic-JD/is-fast) — Rust-based terminal internet search and web content viewer
- v0.17.7 released 2025-11-03, 164 stars, not archived
- Uses ureq (plain HTTP client) + scraper (static HTML parser) — no JS rendering capability
- Install via curl script, Homebrew, or cargo

### Skills

- /agent-browser — related web automation skill
- /research-curator — for creating research/ entry if is-fast is validated

### Agents

No specialized agent needed. Validation is manual CLI testing.

### Prior Work

- Session experimentation 2026-02-05: initial attempt blocked by DNS resolution failure
- Fact-check 2026-02-27: verified install URL, CLI flags; refuted JS rendering claim

### Decision

APPROVED with corrections. The item description's claim about JS-rendered page extraction is false and must be removed. Validation scope should focus on static HTML extraction quality comparison.