---
name: Carbonyl Browser Integration for Claude Code
description: "Research whether carbonyl (terminal Chromium browser) can work with
  Claude Code for reliable web content extraction. Carbonyl renders pages in terminal
  but needs a TTY.\n**Research areas**:\n- Can carbonyl run via tmux/screen/script
  to provide a pseudo-TTY?\n- Could carbonyl be wrapped with a screenshot tool (e.g.,
  termshot, asciinema) that passes images back to Claude?\n- What's the minimal TTY
  setup needed for headless carbonyl operation?\n- Compare with is-fast, lynx, w3m
  for text extraction capabilities\n**Context**: WebFetch is unreliable (summarizing
  agents hallucinate), Playwright requires browser downloads that may be blocked.
  Carbonyl is self-contained but needs TTY."
metadata:
  topic: carbonyl-browser-integration-for-claude-code
  source: Session experimentation 2026-02-05
  added: '2026-02-05'
  priority: P2
  type: Feature
  status: open
  groomed: '2026-02-24'
  issue: '#195'
---

## Groomed (2026-02-24)

### Reproducibility

1. Install carbonyl (terminal Chromium browser) in a dev environment
2. Run carbonyl with a URL; observe it requires a TTY for rendering
3. Attempt to use carbonyl from Claude Code (headless/agent context) — verify whether it fails or works

### Output / Evidence

- Carbonyl docs: <https://github.com/nicksanders/carbonyl> — states TTY requirement for rendering
- Claude Code runs in non-interactive contexts; MCP browser tools may not have a real TTY

### Priority

6/10 — Nice-to-have for web content extraction; alternatives exist (agent-browser MCP, WebFetch). Would unlock terminal-based rendering if feasible.

### Impact

- Unblocks: Reliable web content extraction without full browser stack
- Bottleneck: If carbonyl requires TTY, Claude Code agent sessions may not provide one

### Benefits

- Lighter-weight than full Chromium for simple page rendering
- Terminal output could be easier to parse than DOM

### Expected Behavior

Carbonyl (or a wrapper) should either:
- Work in Claude Code's execution context (no TTY needed, or TTY is available), or
- Be documented as incompatible so we use alternative tools (agent-browser, WebFetch)

### Acceptance Criteria

1. Research carbonyl's TTY requirements against primary sources (carbonyl repo, docs)
2. Test or document: does carbonyl run in `uv run` / subprocess context used by Claude Code?
3. Decision: carbonyl viable for Claude Code → document integration path; else → document as not viable, recommend alternatives

### Resources

| Type | Item |
|------|------|
| Repo | carbonyl: <https://github.com/nicksanders/carbonyl> |
| Skill | agent-browser (cursor-ide-browser MCP) |
| Prior work | cursor-ide-browser for web automation |

### Dependencies

- None blocking; exploratory research item

## Fact-Check

Test fact-check summary for verification.

## Groomed (2026-02-24)

### Test Section

Some test content.
