---
name: Validate carbonyl Terminal Browser
description: "Test carbonyl on host with proper TTY and network access.\n**Validation steps**:\n- Test basic: `npx -y carbonyl --no-sandbox https://example.com`\n- Test with tmux: `tmux new-session -d -s carbonyl 'npx -y carbonyl --no-sandbox https://example.com'`\n- Test screenshot capture: Can we grab terminal output as image?\n- Test text extraction: Can we pipe output or capture rendered text?\n- Compare JS rendering quality with other tools\n**Blocked on 2026-02-05**: Needs TTY (Inappropriate ioctl for device), DNS also blocked\n\n---"
metadata:
  topic: validate-carbonyl-terminal-browser
  source: Session experimentation 2026-02-05
  added: '2026-02-05'
  priority: P2
  type: Feature
  status: open
  issue: '#129'
  groomed: '2026-02-28'
  last_synced: '2026-02-28T17:47:54Z'
---

## Story

As a **developer**, I want **Test carbonyl on host with proper TTY and network access** so that **backlog items are tracked in GitHub**.

## Description

Test carbonyl on host with proper TTY and network access.
**Validation steps**:
- Test basic: `npx -y carbonyl --no-sandbox https://example.com`
- Test with tmux: `tmux new-session -d -s carbonyl 'npx -y carbonyl --no-sandbox https://example.com'`
- Test screenshot capture: Can we grab terminal output as image?
- Test text extraction: Can we pipe output or capture rendered text?
- Compare JS rendering quality with other tools
**Blocked on 2026-02-05**: Needs TTY (Inappropriate ioctl for device), DNS also blocked

---

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session experimentation 2026-02-05
- **Priority**: P2
- **Added**: 2026-02-05
- **Research questions**: None

## Fact-Check

Claims checked: 6
VERIFIED: 4 | REFUTED: 2 | INCONCLUSIVE: 0

### VERIFIED

1. **Carbonyl is available as npm package** — `npm search carbonyl` confirms package by fathyb. SOURCE: https://www.npmjs.com/package/carbonyl (2026-02-28)
2. **Invocation via `npx -y carbonyl --no-sandbox URL`** — Verified in source code (src/cli/cli.rs). Unrecognized flags passed to Chromium. SOURCE: https://github.com/fathyb/carbonyl (2026-02-28)
3. **Carbonyl renders JavaScript** — Chromium engine (Chrome/111.0.5511.1). Confirmed experimentally: JS-generated content captured via CDP `Runtime.evaluate`. SOURCE: Direct testing 2026-02-28
4. **Carbonyl can run inside tmux** — Confirmed experimentally: `tmux new-session -d -s carbonyl` provides PTY, carbonyl renders full page. SOURCE: Direct testing 2026-02-28

### REFUTED

5. **Screenshot/image capture from terminal** — Not documented. GitHub issue #174 (open since Nov 2023) requests `--dump` flag. Feature does not exist. SOURCE: https://github.com/fathyb/carbonyl/issues/174 (2026-02-28)
6. **Text extraction via piping** — Not a native feature. `tmux capture-pane` captures pixel blocks (▄), not text. However, text IS extractable via Chrome DevTools Protocol (`--remote-debugging-port=9222`, `Runtime.evaluate` → `document.body.innerText`). SOURCE: https://github.com/fathyb/carbonyl/issues/174 + direct testing 2026-02-28

## RT-ICA

**Goal**: Validate carbonyl terminal browser for use as a JS-capable web browsing tool in AI agent environments without direct TTY access.

**Decision**: APPROVED — all original blockers resolved; validation completed empirically.

| # | Condition | Status | Evidence |
|---|-----------|--------|----------|
| 1 | TTY available | AVAILABLE | `tmux 3.4` provides PTY; `script` (util-linux 2.39.3) also works; Python `pty.openpty()` allocates `/dev/pts/0` |
| 2 | DNS/network access | AVAILABLE | `curl https://example.com` returns HTTP 200 |
| 3 | Node.js/npx available | AVAILABLE | Node v22.22.0, npx 10.9.4 |
| 4 | Root access | AVAILABLE | uid=0(root) |
| 5 | Carbonyl installs | AVAILABLE | `npx -y carbonyl --version` returns `Carbonyl 0.0.2` |
| 6 | JS rendering works | AVAILABLE | Chrome DevTools Protocol confirms JS execution; `document.body.innerText` returns JS-generated content |
| 7 | Text extraction possible | AVAILABLE (via CDP) | `--remote-debugging-port=9222` + WebSocket CDP → `Runtime.evaluate` extracts text. Terminal capture gives only pixel blocks |
| 8 | Screenshot capture | MISSING | Not implemented (GitHub fathyb/carbonyl#174 open). No native `--dump` flag |

**Original blockers (2026-02-05) — all resolved:**

- "Needs TTY" → `tmux` / `script` / Python `pty` provide PTY
- "DNS also blocked" → DNS works; curl resolves and fetches successfully

## Groomed (2026-02-28)

### Validation Results (2026-02-28)

**Environment**: Linux 4.4.0, root access, Node v22.22.0, tmux 3.4
**Carbonyl version**: 0.0.2 (Chrome/111.0.5511.1, Protocol 1.3)

#### Test Results

| Test | Result | Method |
|------|--------|--------|
| Install via npx | PASS | `npx -y carbonyl --version` → `Carbonyl 0.0.2` |
| Basic rendering (example.com) | PASS | `script -qc "npx -y carbonyl --no-sandbox URL"` renders page with URL bar |
| tmux PTY workaround | PASS | `tmux new-session -d -s carbonyl` provides PTY, full page renders |
| JS rendering | PASS | CDP `Runtime.evaluate` on data: URL with `<script>` returns JS-generated text |
| Text extraction (terminal) | FAIL | `tmux capture-pane -p` returns pixel blocks (▄), not readable text |
| Text extraction (CDP) | PASS | `--remote-debugging-port=9222` + WebSocket → `document.body.innerText` returns actual text |
| DevTools Protocol access | PASS | Full CDP 1.3 via localhost:9222, WebSocket debugging available |
| Screenshot capture | FAIL | Not implemented (fathyb/carbonyl#174 open since Nov 2023) |
| JS execution | PASS | `JSON.stringify({jsWorks: true, ...})` returns correctly |
| Page navigation | PASS | URL bar updates, page content loads |

#### Key Findings

1. **TTY blocker resolved**: `tmux`, `script`, and Python `pty` all provide working PTYs
2. **DNS blocker resolved**: Network and DNS fully functional
3. **Rendering mode**: Carbonyl renders in half-block pixel mode (▄▄) by default — terminal text capture shows pixels, not characters
4. **Text extraction strategy**: Chrome DevTools Protocol is the correct approach for extracting page content, not terminal scraping
5. **Practical usage pattern for AI agents**:

   ```bash
   tmux new-session -d -s browser "npx -y carbonyl --no-sandbox --remote-debugging-port=9222 URL"
   # Then use CDP WebSocket at ws://localhost:9222/devtools/page/... for:
   # - Runtime.evaluate → document.body.innerText (text extraction)
   # - Page.navigate → navigate to URLs
   # - DOM.getDocument → full DOM access
   ```

#### Comparison Context

- **vs Lynx/w3m**: Carbonyl renders JS; Lynx/w3m cannot
- **vs Puppeteer headless**: Carbonyl uses real Chromium but renders to terminal; both support CDP
- **vs WebFetch tool**: Carbonyl executes JS and renders CSS; WebFetch gets static HTML only
- **Unique value**: Full Chromium with CDP in terminal environments without X11/display

#### Limitations

- v0.0.2 is old (Chrome 111, released ~2023); upstream repo has limited recent activity
- No native text dump or screenshot feature
- Rendering is pixel-based — not useful for direct terminal text reading
- Requires PTY (tmux/script workaround needed in non-TTY environments)

#### Recommendation

Carbonyl is validated as functional. For AI agent use cases, the CDP interface (not terminal rendering) is the primary value. Consider whether Puppeteer/Playwright in headless mode would be simpler for the same CDP-based text extraction, since carbonyl's terminal rendering adds no value when text is extracted via CDP.