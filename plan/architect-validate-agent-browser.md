# Architecture Spec: Validate agent-browser for Web Automation

**Date**: 2026-02-28
**Type**: Validation task (not a code implementation)
**Scope**: End-to-end validation of the core open → snapshot → get text → close workflow, documentation of prerequisites, and correction of the `get text body` syntax ambiguity.

---

## Overview

The `/agent-browser` skill wraps the `agent-browser` CLI (Vercel Labs, v0.15.0, Playwright-based) and documents a browser automation workflow for AI agents. The skill has never been run end-to-end in a controlled session — two observed failure modes blocked it in 2026-02-05 (DNS failure, missing system libs). The current environment has Playwright Chromium installed and network access, removing those blockers.

This spec defines what to validate, how to collect evidence, what to fix in the skill documentation, and how to close GitHub Issue #128.

---

## Scope

### In scope

- Core workflow validation: `open` → `snapshot -i` → `get text @e1` → `close`
- Confirming `get text body` (CSS selector) works and distinguishing it from `@ref` usage
- Node.js version check (resolve Q1 from feature context)
- Playwright browser install command comparison: `agent-browser install` vs `npx playwright install` (resolve Q2)
- System library confirmation — headless Chromium launch succeeds or fails with specific error (resolve Q3)
- Adding a Prerequisites section to SKILL.md (modeled after the `/gh` skill pattern)
- Correcting or annotating `get text body` in SKILL.md line 155 and `templates/capture-workflow.sh` line 47 (resolve Q4)
- Adding a validation status note to SKILL.md
- Closing GitHub Issue #128 with evidence

### Out of scope

- Parallel sessions (`--session`)
- State persistence (`state save` / `state load`)
- Video recording (`record start`)
- Proxy support
- iOS simulator
- JavaScript eval (`eval --stdin`)
- Authenticated session templates

These features remain undocumented as to validation status. The spec does not attempt to validate them. After this validation, SKILL.md will note which features are unvalidated.

---

## Validation Plan

### Step 1: Environment check

Capture the environment state before running any agent-browser commands.

```bash
node --version
npx agent-browser --version
ls ~/.cache/ms-playwright/
```

Expected output: Node.js version string, agent-browser version string (v0.15.0 or later), Chromium directory listing.

Success criteria:

- Node.js is present (version recorded for Q1)
- `npx agent-browser --version` exits 0 and prints a version string
- `~/.cache/ms-playwright/` exists and contains at least one browser directory

### Step 2: Install command comparison (resolve Q2)

Run `npx agent-browser install` and observe what it installs. Compare the output to what `npx playwright install chromium` would install.

```bash
npx agent-browser install 2>&1
```

Success criteria: Command exits 0. Output notes which browser binary was installed or "already installed". If the command installs only Chromium (not Firefox or WebKit), document that as the minimal install command.

### Step 3: Core workflow — open → snapshot → get text @ref → close

Run the four validation steps from the backlog item (`.claude/backlog/p2-validate-agent-browser-for-web-automation.md` lines 47–63) against `https://code.claude.com/docs/en/skills`.

```bash
npx agent-browser open https://code.claude.com/docs/en/skills
npx agent-browser wait --load networkidle
npx agent-browser snapshot -i
npx agent-browser get text @e1
npx agent-browser close
```

Success criteria per step:

| Step | Success Condition |
|------|------------------|
| `open` | Exits 0, no error output about missing libs or DNS failure |
| `wait --load networkidle` | Exits 0 within 30 seconds |
| `snapshot -i` | Output contains at least one `@e1` ref and a recognizable element description |
| `get text @e1` | Exits 0 and prints non-empty text |
| `close` | Exits 0 |

### Step 4: CSS selector syntax confirmation (resolve Q4)

Run `get text body` to confirm whether it works as a CSS selector and produces full page text.

```bash
npx agent-browser open https://code.claude.com/docs/en/skills
npx agent-browser get text body
npx agent-browser close
```

Success criteria: Exits 0 and returns text content. This confirms `body` works as a CSS selector. The documentation update (see below) will then clarify this is a CSS selector pattern, not an `@ref` pattern.

### Step 5: Screenshot capture (optional, scope extension per Q5 option C)

If Steps 3 and 4 pass, run one screenshot to confirm the capture workflow template is exercisable.

```bash
npx agent-browser open https://code.claude.com/docs/en/skills
npx agent-browser screenshot --full /tmp/agent-browser-validation.png
npx agent-browser close
```

Success criteria: Exits 0 and `/tmp/agent-browser-validation.png` exists with non-zero file size.

---

## Documentation Changes

### Change 1: Prerequisites section in SKILL.md

Add a `## Prerequisites` section immediately after the frontmatter block and before `## Core Workflow`. Modeled after the `/gh` skill's Installation section — explicit install path, install command, version requirement, how to check, what to do if missing.

Section content to write:

```text
## Prerequisites

agent-browser requires Node.js, npm, and Playwright browser binaries.

### Check

Run the following before using this skill:

    node --version           # Must be present; v18+ recommended
    npx agent-browser --version  # Must print a version string
    ls ~/.cache/ms-playwright/   # Must contain a Chromium directory

### Install Playwright browsers

If the browser binary is missing, install it:

    npx agent-browser install

This installs only the Chromium binary used by agent-browser.
Do NOT use `npx playwright install` (installs Chromium + Firefox + WebKit — unnecessary for agent-browser).

### System libraries (Linux headless)

Headless Chromium on Linux requires standard rendering libraries
(libgbm, libnss3, libatk, etc.). These are present in most CI
and development environments. If `agent-browser open` exits with
a missing `.so` error, see Error Recovery below.

### Network

The target URL must be reachable from the host. DNS and outbound
HTTPS (port 443) must be available. Verify with:

    curl -sSf https://example.com > /dev/null && echo "ok"
```

The exact version requirement for Node.js will be filled in after Q1 is resolved during validation. The placeholder text "v18+ recommended" will be updated to "v{actual version from Q1}" or the verified minimum.

### Change 2: Validation status note in SKILL.md

Add a `## Validation Status` section after `## Deep-Dive Documentation` and before `## Ready-to-Use Templates`.

```text
## Validation Status

| Feature | Status | Date | Environment |
|---------|--------|------|-------------|
| Core workflow (open/snapshot/get text/close) | Validated | 2026-02-28 | Linux, Chromium {version} |
| CSS selector `get text body` | Validated | 2026-02-28 | Linux, Chromium {version} |
| Screenshot capture | Validated | 2026-02-28 | Linux, Chromium {version} |
| Parallel sessions | Not validated | — | — |
| State persistence | Not validated | — | — |
| Video recording | Not validated | — | — |
| Proxy support | Not validated | — | — |
| iOS simulator | Not validated | — | — |

Validation environment: Node.js {version}, agent-browser {version}, Chromium {version}, Linux.
```

Fill in actual versions from Step 1 output.

### Change 3: Clarify `get text body` in SKILL.md Data Extraction pattern

Current SKILL.md line 154–155:

```bash
agent-browser get text @e5           # Get specific element text
agent-browser get text body > page.txt  # Get all page text
```

The second line is correct but needs a clarifying comment. Update to:

```bash
agent-browser get text @e5             # Get specific element text (from snapshot ref)
agent-browser get text body > page.txt # Get all page text (body is a CSS selector, not @ref)
```

### Change 4: Annotate `capture-workflow.sh` line 47

Current `templates/capture-workflow.sh` line 47:

```bash
agent-browser get text body >"$OUTPUT_DIR/page-text.txt"
```

Add an inline comment:

```bash
agent-browser get text body >"$OUTPUT_DIR/page-text.txt"  # body = CSS selector for full page text
```

This is the minimal change. The `body` selector is confirmed working (Step 4 success criteria). The comment prevents future maintainers from assuming `body` is a special keyword or an `@ref`.

### Change 5: Error Recovery section in SKILL.md

Add an `## Error Recovery` section before `## Deep-Dive Documentation`.

```text
## Error Recovery

### Missing Playwright browser binary

Symptom: `browserType.launch: Executable doesn't exist at ...`

Fix: `npx agent-browser install`

### Missing system libraries (Linux)

Symptom: `error while loading shared libraries: libgbm.so.1`

Fix:

    # Debian / Ubuntu
    apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0

    # If apt is unavailable, check the Playwright system dependencies page:
    # https://playwright.dev/docs/browsers#install-system-dependencies

### Network unreachable

Symptom: `net::ERR_NAME_NOT_RESOLVED` or `net::ERR_CONNECTION_REFUSED`

Fix: Verify DNS and outbound HTTPS from the host before using the skill.

    curl -sSf https://example.com > /dev/null && echo "ok"
```

---

## Evidence Collection Strategy

### What to capture per command

For each validation step, capture:

1. The exact command as run (with full `npx agent-browser` prefix, not alias)
2. Exit code: `echo "Exit: $?"`
3. Full stdout — no truncation
4. Full stderr — separate capture if needed: `command 2>/tmp/stderr.txt`

Minimum evidence record per step:

```text
Command: npx agent-browser open https://code.claude.com/docs/en/skills
Exit: 0
Stdout: (full output)
Stderr: (full output, or "none")
```

### Environment record

Capture once before Step 1:

```bash
node --version
npm --version
npx agent-browser --version
ls ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1
uname -r
```

### Where to record results

Two locations:

1. The task file (wherever this spec produces one) — inline evidence block per step, updated as each step completes
2. GitHub Issue #128 comment — a summary comment with pass/fail per step and a link to the task file for full evidence

---

## Error Recovery (for the validation run itself)

These are recovery steps for the validation run, not for the skill docs.

### If Playwright browsers are missing

```bash
npx agent-browser install
```

If that fails, try:

```bash
npx playwright install chromium
```

If that also fails (network blocked):

- Record the error verbatim
- Do not proceed with Steps 3–5
- Update GitHub Issue #128 with the environment diagnosis
- Mark the task BLOCKED with the error as the blocker

### If system libs are missing

```bash
apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxdamage1 libxrandr2 libxfixes3 libxcursor1 libxi6 libxtst6 fonts-liberation
```

Retry `npx agent-browser open` after installation. If it still fails, record the specific missing library and mark BLOCKED.

### If target URL is unreachable

Try an alternative URL:

```bash
npx agent-browser open https://example.com
```

If `example.com` also fails, the issue is outbound network access, not the target URL. Record the DNS/connection error and use the fallback URL `file:///etc/hostname` with `--allow-file-access` to test at least the browser launch and snapshot steps in isolation.

---

## Deliverables

| Deliverable | File | Status After Validation |
|-------------|------|------------------------|
| Prerequisites section | `.claude/skills/agent-browser/SKILL.md` | Added |
| Validation status table | `.claude/skills/agent-browser/SKILL.md` | Added with actual versions |
| `get text body` annotation | `.claude/skills/agent-browser/SKILL.md` line 155 | Inline comment added |
| Error recovery section | `.claude/skills/agent-browser/SKILL.md` | Added |
| Template annotation | `.claude/skills/agent-browser/templates/capture-workflow.sh` line 47 | Inline comment added |
| GitHub Issue #128 update | GitHub Issue #128 | Comment with validation result, closed if passing |

All SKILL.md changes require `uv run prek run --files .claude/skills/agent-browser/SKILL.md` to pass before commit.

---

## Constraints

- All commands run via `npx agent-browser` (not global install) — matches the `allowed-tools` frontmatter in SKILL.md: `Bash(npx agent-browser:*)`
- No new files created in the skill directory — only SKILL.md and the existing template are modified
- Documentation changes are grounded in observed behavior from the validation run — no speculative claims about unvalidated features
- Validation status note uses actual version strings from Step 1 output — no placeholder text left in the committed version
- All code fences in SKILL.md changes use language specifiers (`bash`, `text`) per repo standards
- SKILL.md changes surrounded by blank lines per MD031 rule

---

## Success Criteria

The validation task is complete when:

1. Steps 3 and 4 (core workflow + CSS selector test) both exit 0 with non-empty output
2. SKILL.md has a Prerequisites section, Error Recovery section, and Validation Status table
3. `get text body` in SKILL.md line 155 has a clarifying inline comment
4. `templates/capture-workflow.sh` line 47 has a clarifying inline comment
5. `uv run prek run --files .claude/skills/agent-browser/SKILL.md` passes
6. GitHub Issue #128 has a closing comment with per-step evidence summary
7. GitHub Issue #128 is closed

If Steps 3 or 4 fail due to environment blockers (network, system libs), the task is marked BLOCKED with the specific error message as evidence. The documentation changes in Deliverables are still written if the environment state can be diagnosed (e.g., missing lib identified and documented in Error Recovery).
