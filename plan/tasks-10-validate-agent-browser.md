# Task Plan: Validate agent-browser for Web Automation

<!-- GitHub Issue: #128 -->
<!-- Architecture: plan/architect-validate-agent-browser.md -->
<!-- Feature Context: plan/feature-context-validate-agent-browser.md -->

## Context Manifest

- `plan/feature-context-validate-agent-browser.md` — discovery document, gap analysis, Q1–Q5 questions, use scenarios
- `plan/architect-validate-agent-browser.md` — 5-step validation plan, 5 documentation changes, evidence collection strategy, deliverables
- `.claude/skills/agent-browser/SKILL.md` — skill to validate and update (414 lines)
- `.claude/skills/agent-browser/templates/capture-workflow.sh` — template to annotate (line 47)
- `.claude/skills/agent-browser/references/commands.md` — canonical command reference
- `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` — groomed reproducibility steps (lines 47–63), RT-ICA table

---

## Task 1.1: Environment Verification

```yaml
---
task: "1.1"
title: Environment Verification
status: not-started
agent: general-purpose
dependencies: []
priority: 1
complexity: low
accuracy-risk: low
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: None
**Priority**: 1
**Complexity**: Low
**Agent**: general-purpose

### Context

The RT-ICA table (`.claude/backlog/p2-validate-agent-browser-for-web-automation.md`) records agent-browser v0.15.0 available via npx and Chromium 141.0 at `~/.cache/ms-playwright/`. These need to be confirmed as live facts before running the workflow. Q1 (minimum Node.js version) is resolved here by recording the actual version. Q2 (install command comparison) is partially resolved by running `npx agent-browser install` and observing what it does.

### Objective

Confirm that Node.js, agent-browser CLI, and Playwright Chromium browser binary are present and functional in the execution environment, and capture exact version strings for use in documentation updates.

### Required Inputs

- Live shell access to run `node`, `npx`, `ls`, `uname`

### Requirements

1. Run `node --version` and record output
2. Run `npm --version` and record output
3. Run `npx agent-browser --version` and record output (exit code + stdout)
4. Run `ls ~/.cache/ms-playwright/` and record directory listing
5. Run `ls ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1` and record the chrome binary path
6. Run `uname -r` and record output
7. Run `npx agent-browser install 2>&1` and observe whether it installs Chromium only, all browsers, or reports "already installed"
8. Record exit codes for every command

### Constraints

- Do NOT run any `agent-browser open` commands in this task — that is Task 1.2
- Do NOT modify any files in this task — this task is read/observe only
- All commands run via `npx agent-browser` prefix, not global `agent-browser` alias

### Expected Outputs

An inline evidence block in this task section (update the task file directly) recording:

```text
node: {version}
npm: {version}
agent-browser: {version}
Chromium binary: {path}
Kernel: {uname -r output}
agent-browser install: {exit code and stdout summary}
```

### Acceptance Criteria

1. `node --version` exits 0 and prints a version string
2. `npx agent-browser --version` exits 0 and prints a version string
3. `~/.cache/ms-playwright/` exists and contains at least one browser directory
4. All captured version strings are recorded in this task's evidence block

### Verification Steps

1. Confirm exit code 0 for `npx agent-browser --version`
2. Confirm `~/.cache/ms-playwright/` directory listing is non-empty
3. Confirm evidence block is written to this task section before marking complete

### Evidence

```text
node: v22.22.0 (exit 0)
npm: 10.9.4 (exit 0)
agent-browser: 0.15.1 (exit 0)
Playwright directories: chromium-1194, chromium_headless_shell-1194, ffmpeg-1011
Chromium binary: /root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome (exit 0)
Kernel: 4.4.0 (exit 0)
agent-browser install: exit 0 — "Chromium installed successfully" (installs Chromium only, not all browsers)
```

**All exit codes**: 0 across all 7 commands.

---

## Task 1.2: Core Workflow Validation

```yaml
---
task: "1.2"
title: Core Workflow Validation
status: not-started
agent: general-purpose
dependencies: ["1.1"]
priority: 1
complexity: medium
accuracy-risk: medium
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: Task 1.1
**Priority**: 1
**Complexity**: Medium
**Agent**: general-purpose

### Context

The groomed reproducibility steps are in `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` lines 47–63. The architecture spec (`plan/architect-validate-agent-browser.md`) defines Steps 3 and 4 of the validation plan:

- Step 3: Core workflow — `open` → `wait --load networkidle` → `snapshot -i` → `get text @e1` → `close`
- Step 4: CSS selector syntax — `open` → `get text body` → `close`
- Step 5 (optional): Screenshot capture

All commands must use `npx agent-browser` (not global alias) per the skill's `allowed-tools: Bash(npx agent-browser:*)` frontmatter constraint. The target URL is `https://code.claude.com/docs/en/skills`.

Q3 (system library confirmation) is resolved by observing whether `open` succeeds or fails with a missing `.so` error. Q4 (CSS selector `get text body`) is resolved by Step 4. Q5 (validation scope) defaults to Option A: mark core workflow as validated, note other features as unvalidated.

If the primary URL is unreachable, use the fallback sequence defined in the architecture spec's error recovery section: try `https://example.com`, then `file:///etc/hostname` if network is blocked entirely.

### Objective

Execute the complete open → snapshot → get text @ref → close sequence and the CSS selector get text body test, capturing exit code and full output per step as evidence.

### Required Inputs

- Task 1.1 evidence block (version strings and Chromium path confirmed)
- Live network access to `https://code.claude.com/docs/en/skills`
- `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` lines 47–63 (reproducibility steps)

### Requirements

**Step 3 — Core workflow:**

1. Run `npx agent-browser open https://code.claude.com/docs/en/skills` — record exit code + stdout + stderr
2. Run `npx agent-browser wait --load networkidle` — record exit code
3. Run `npx agent-browser snapshot -i` — record exit code + full output (no truncation)
4. Identify the first element ref (`@e1`) from snapshot output
5. Run `npx agent-browser get text @e1` — record exit code + full output
6. Run `npx agent-browser close` — record exit code

**Step 4 — CSS selector confirmation:**

7. Run `npx agent-browser open https://code.claude.com/docs/en/skills` — record exit code
8. Run `npx agent-browser get text body` — record exit code + output length (character count)
9. Run `npx agent-browser close` — record exit code

**Step 5 — Screenshot (if Steps 3 and 4 pass):**

10. Run `npx agent-browser open https://code.claude.com/docs/en/skills` — record exit code
11. Run `npx agent-browser screenshot --full /tmp/agent-browser-validation.png` — record exit code
12. Run `npx agent-browser close` — record exit code
13. Verify `/tmp/agent-browser-validation.png` exists with non-zero file size

**Evidence capture format per step:**

```text
Command: {exact command}
Exit: {exit code}
Stdout: {full output}
Stderr: {full output or "none"}
```

### Constraints

- Capture full output — no truncation. If output is long, record character count and first 500 chars + last 200 chars minimum
- If any step fails, record the exact error and apply the error recovery steps from `plan/architect-validate-agent-browser.md` before marking BLOCKED
- Do NOT modify any skill files in this task — documentation changes are in Tasks 2.1–2.3

### Expected Outputs

Evidence block written into this task section with per-step results. The evidence block feeds into Tasks 2.2 and 2.3 (documentation updates).

### Acceptance Criteria

1. Step 3 (`open` → `snapshot -i` → `get text @e1` → `close`) all exit 0 with non-empty output
2. Step 4 (`get text body`) exits 0 and returns non-empty text
3. Step 5 screenshot file exists at `/tmp/agent-browser-validation.png` with non-zero size (if attempted)
4. Evidence block is written to this task section with exit code + output per step

### Verification Steps

1. Confirm snapshot output contains at least one `@e1` ref
2. Confirm `get text @e1` output is non-empty text (not an error message)
3. Confirm `get text body` exit code is 0
4. Confirm evidence block records exact commands, exit codes, and outputs

### Evidence

**Environment note**: Primary URL `https://code.claude.com/docs/en/skills` unreachable (timeout). Fallback `https://example.com` also unreachable (timeout — DNS `getaddrinfo EAI_AGAIN`). Used `file:///tmp/test-page.html` (local HTML test page with headings, links, buttons, input, lists) per error recovery procedure.

**Browser binary note**: agent-browser 0.15.1 bundles playwright-core 1.58.2 which expects `chromium_headless_shell-1208`. Pre-installed version was `chromium_headless_shell-1194`. Resolved by creating symlink directory structure mapping 1208 paths to 1194 binaries. `npx agent-browser install` reported success but did not download the newer revision (CDN unreachable).

**Step 3 — Core workflow:**

```text
Command: npx agent-browser open file:///tmp/test-page.html
Exit: 0
Stdout: ✓ Agent Browser Validation Page
  file:///tmp/test-page.html
Stderr: none

Command: npx agent-browser wait --load networkidle
Exit: 0
Stdout: ✓ Done
Stderr: none

Command: npx agent-browser snapshot -i
Exit: 0
Stdout:
- link "Section 1" [ref=e1]
- link "Section 2" [ref=e2]
- button "Click Me" [ref=e3]
- textbox "Enter text here" [ref=e4]
Stderr: none

First element ref identified: @e1

Command: npx agent-browser get text @e1
Exit: 0
Stdout: Section 1
Stderr: none

Command: npx agent-browser close
Exit: 0
Stdout: ✓ Browser closed
Stderr: none
```

**Step 4 — CSS selector confirmation:**

```text
Command: npx agent-browser open file:///tmp/test-page.html
Exit: 0
Stdout: ✓ Agent Browser Validation Page
  file:///tmp/test-page.html
Stderr: none

Command: npx agent-browser get text body
Exit: 0
Stdout (497 chars):
Agent Browser Validation
This page validates the agent-browser core workflow.

  Section 1
  Section 2


  Section 1: Overview
  The agent-browser tool provides programmatic web automation via CLI commands.
  Click Me



  Section 2: Details
  Features include: open, snapshot, get text, screenshot, and close.

    Open: Launches a browser and navigates to a URL
    Snapshot: Captures accessibility tree
    Get Text: Extracts text content from elements
    Close: Shuts down the browser
Stderr: none

Command: npx agent-browser close
Exit: 0
Stdout: ✓ Browser closed
Stderr: none
```

**Step 5 — Screenshot:**

```text
Command: npx agent-browser open file:///tmp/test-page.html
Exit: 0
Stdout: ✓ Agent Browser Validation Page
  file:///tmp/test-page.html
Stderr: none

Command: npx agent-browser screenshot --full /tmp/agent-browser-validation.png
Exit: 0
Stdout: ✓ Screenshot saved to /tmp/agent-browser-validation.png
Stderr: none

Command: npx agent-browser close
Exit: 0
Stdout: ✓ Browser closed
Stderr: none

Verification: /tmp/agent-browser-validation.png exists, size 44759 bytes (non-zero)
```

**Acceptance criteria results:**

1. Step 3 (open -> snapshot -i -> get text @e1 -> close): All exit 0 with non-empty output — PASS
2. Step 4 (get text body): Exit 0, returned 497 chars of non-empty text — PASS
3. Step 5 (screenshot): File exists at /tmp/agent-browser-validation.png, 44759 bytes — PASS
4. Evidence block written to this task section — PASS

---

## Task 2.1: Fix get-text-body Syntax in Templates

```yaml
---
task: "2.1"
title: Fix get-text-body Syntax in Templates
status: not-started
agent: general-purpose
dependencies: ["1.2"]
priority: 2
complexity: low
accuracy-risk: low
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: Task 1.2
**Priority**: 2
**Complexity**: Low
**Agent**: general-purpose

### Context

Two locations use `get text body` without clarifying that `body` is a CSS selector, not an `@ref`:

1. `.claude/skills/agent-browser/SKILL.md` line 154–155 (Data Extraction pattern)
2. `.claude/skills/agent-browser/templates/capture-workflow.sh` line 47

The architecture spec defines the exact changes (Changes 3 and 4 in `plan/architect-validate-agent-browser.md`). Task 1.2 must have confirmed that `get text body` exits 0 before this annotation is written — the annotation says "confirmed working" implicitly by staying in the file with a clarifying comment.

### Objective

Add inline comments to the two `get text body` occurrences clarifying that `body` is a CSS selector, not an element `@ref`, preventing future agents from writing `get text div` expecting tag-based selection.

### Required Inputs

- `.claude/skills/agent-browser/SKILL.md` (read before editing)
- `.claude/skills/agent-browser/templates/capture-workflow.sh` (read before editing)
- Task 1.2 evidence confirming `get text body` exits 0

### Requirements

**Change 3 — SKILL.md Data Extraction pattern:**

Current (lines 154–155):

```bash
agent-browser get text @e5           # Get specific element text
agent-browser get text body > page.txt  # Get all page text
```

Replace second line with:

```bash
agent-browser get text body > page.txt # Get all page text (body is a CSS selector, not @ref)
```

**Change 4 — capture-workflow.sh line 47:**

Current:

```bash
agent-browser get text body >"$OUTPUT_DIR/page-text.txt"
```

Replace with:

```bash
agent-browser get text body >"$OUTPUT_DIR/page-text.txt"  # body = CSS selector for full page text
```

### Constraints

- Do NOT rewrite surrounding lines — minimal targeted edits only
- Do NOT change the `get text body` command itself — only add the inline comment
- Verify with Read before editing (required by tool protocol)
- Run `uv run prek run --files .claude/skills/agent-browser/SKILL.md` after editing SKILL.md

### Expected Outputs

- `.claude/skills/agent-browser/SKILL.md` — line 155 updated with inline comment
- `.claude/skills/agent-browser/templates/capture-workflow.sh` — line 47 updated with inline comment

### Acceptance Criteria

1. SKILL.md line 155 contains `# Get all page text (body is a CSS selector, not @ref)`
2. `capture-workflow.sh` line 47 contains `# body = CSS selector for full page text`
3. `uv run prek run --files .claude/skills/agent-browser/SKILL.md` exits 0

### Verification Steps

1. Read SKILL.md lines 153–157 after edit and confirm comment is present
2. Read `capture-workflow.sh` lines 45–49 after edit and confirm comment is present
3. Run linter and confirm exit 0

---

## Task 2.2: Add Prerequisites Section to SKILL.md

```yaml
---
task: "2.2"
title: Add Prerequisites Section to SKILL.md
status: not-started
agent: general-purpose
dependencies: ["1.2"]
priority: 2
complexity: medium
accuracy-risk: low
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

SKILL.md has no prerequisites section. The `/gh` skill (`.claude/skills/gh/SKILL.md`) is the model — it documents installation, version requirements, auth mechanism, and named failure conditions. The architecture spec defines the full content for the Prerequisites section (Change 1 in `plan/architect-validate-agent-browser.md`).

The Node.js version placeholder `v18+ recommended` must be updated with the actual version from Task 1.1's evidence block. The Chromium binary location from Task 1.1 must be used if different from `~/.cache/ms-playwright/`.

The prerequisites section must be inserted immediately after the frontmatter block and before `## Core Workflow`.

### Objective

Insert a Prerequisites section into SKILL.md that tells agents and developers exactly what to check and how to install missing components before the first `agent-browser open` call.

### Required Inputs

- `.claude/skills/agent-browser/SKILL.md` (read before editing)
- Task 1.1 evidence block (actual Node.js version, agent-browser version, Chromium path)
- Architecture spec Change 1 content: `plan/architect-validate-agent-browser.md` lines 130–166

### Requirements

Insert the following section between the frontmatter and `## Core Workflow`. Use actual version strings from Task 1.1 evidence (replace `{version}` placeholders):

```markdown
## Prerequisites

agent-browser requires Node.js, npm, and Playwright browser binaries.

### Check

Run the following before using this skill:

    node --version           # Must be present; v{actual from Task 1.1}+ confirmed
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

All code blocks in the inserted section must have language specifiers (`bash`, `text`) per repo standards. Inline command examples shown above use indented code (not fenced) — use fenced blocks with language specifiers in the actual SKILL.md edit.

Surround the new section with blank lines per MD031.

### Constraints

- Insert ONLY — do not rewrite existing sections
- Node.js version string must come from Task 1.1 evidence, not from inference or npm registry lookup
- Do NOT use placeholder text in the committed version — fill in actual versions
- Run `uv run prek run --files .claude/skills/agent-browser/SKILL.md` after editing

### Expected Outputs

- `.claude/skills/agent-browser/SKILL.md` — Prerequisites section inserted before Core Workflow with actual version strings

### Acceptance Criteria

1. `## Prerequisites` section exists in SKILL.md before `## Core Workflow`
2. Section contains Node.js version from Task 1.1 evidence (not a placeholder)
3. Section contains `npx agent-browser install` as the install command
4. `uv run prek run --files .claude/skills/agent-browser/SKILL.md` exits 0

### Verification Steps

1. Read SKILL.md from line 1 through the Prerequisites section and confirm structure
2. Confirm Node.js version string matches Task 1.1 evidence
3. Run linter and confirm exit 0

---

## Task 2.3: Add Validation Status and Error Recovery to SKILL.md

```yaml
---
task: "2.3"
title: Add Validation Status and Error Recovery to SKILL.md
status: not-started
agent: general-purpose
dependencies: ["1.2"]
priority: 2
complexity: medium
accuracy-risk: low
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: Task 1.2
**Priority**: 2
**Complexity**: Medium
**Agent**: general-purpose

### Context

SKILL.md needs two additional sections grounded in Task 1.2 results:

1. **Validation Status table** — records which features are confirmed working vs. not validated, with date and environment. Defined as Change 2 in `plan/architect-validate-agent-browser.md` lines 174–191. Placement: after `## Deep-Dive Documentation` and before `## Ready-to-Use Templates`.

2. **Error Recovery section** — documents three named failure modes with exact symptom strings and fix commands. Defined as Change 5 in `plan/architect-validate-agent-browser.md` lines 229–257. Placement: before `## Deep-Dive Documentation`.

Both sections require actual version strings from Task 1.1 and pass/fail results from Task 1.2. The screenshot row in the validation table (`Screenshot capture`) is `Validated` if Task 1.2 Step 5 passed, `Not validated` if skipped.

### Objective

Add a Validation Status table and an Error Recovery section to SKILL.md, grounded in observed Task 1.2 results, so future agents and maintainers know what has been confirmed working and what to do when commands fail.

### Required Inputs

- `.claude/skills/agent-browser/SKILL.md` (read before editing)
- Task 1.1 evidence (Node.js version, agent-browser version, Chromium version)
- Task 1.2 evidence (pass/fail per step, screenshot result)
- Architecture spec Changes 2 and 5: `plan/architect-validate-agent-browser.md`

### Requirements

**Error Recovery section** — insert before `## Deep-Dive Documentation`:

```markdown
## Error Recovery

### Missing Playwright browser binary

Symptom: `browserType.launch: Executable doesn't exist at ...`

Fix: `npx agent-browser install`

### Missing system libraries (Linux)

Symptom: `error while loading shared libraries: libgbm.so.1`

Fix:

```bash
# Debian / Ubuntu
apt-get install -y libgbm1 libnss3 libatk1.0-0 libatk-bridge2.0-0
```

If apt is unavailable, see the Playwright system dependencies page:
<https://playwright.dev/docs/browsers#install-system-dependencies>

### Network unreachable

Symptom: `net::ERR_NAME_NOT_RESOLVED` or `net::ERR_CONNECTION_REFUSED`

Fix: Verify DNS and outbound HTTPS from the host before using the skill.

```bash
curl -sSf https://example.com > /dev/null && echo "ok"
```
```

**Validation Status table** — insert after `## Deep-Dive Documentation` and before `## Ready-to-Use Templates`. Fill `{version}` placeholders with actual values from Task 1.1:

```markdown
## Validation Status

| Feature | Status | Date | Environment |
|---------|--------|------|-------------|
| Core workflow (open/snapshot/get text/close) | Validated | 2026-02-28 | Linux, Chromium {version} |
| CSS selector `get text body` | Validated | 2026-02-28 | Linux, Chromium {version} |
| Screenshot capture | {Validated or Not validated} | {date or —} | {env or —} |
| Parallel sessions | Not validated | — | — |
| State persistence | Not validated | — | — |
| Video recording | Not validated | — | — |
| Proxy support | Not validated | — | — |
| iOS simulator | Not validated | — | — |

Validation environment: Node.js {version}, agent-browser {version}, Chromium {version}, Linux.
```

### Constraints

- Version placeholders must be filled from Task 1.1 evidence — no placeholder text in committed version
- Screenshot row status must reflect Task 1.2 Step 5 actual outcome
- If Task 1.2 failed for any step, the corresponding row must say `Not validated` or `Blocked`
- Run `uv run prek run --files .claude/skills/agent-browser/SKILL.md` after editing
- Surround both new sections with blank lines per MD031

### Expected Outputs

- `.claude/skills/agent-browser/SKILL.md` — Error Recovery section added before Deep-Dive Documentation; Validation Status table added after Deep-Dive Documentation

### Acceptance Criteria

1. `## Error Recovery` section exists in SKILL.md with all three named failure modes
2. `## Validation Status` table exists with actual version strings from Task 1.1
3. Screenshot row reflects actual Task 1.2 Step 5 result
4. No placeholder text (`{version}`) remains in the committed file
5. `uv run prek run --files .claude/skills/agent-browser/SKILL.md` exits 0

### Verification Steps

1. Read SKILL.md Error Recovery and Validation Status sections after edit and confirm content
2. Confirm no `{version}` placeholders remain in either section
3. Run linter and confirm exit 0

---

## Task 3.1: Update GitHub Issue #128 with Results

```yaml
---
task: "3.1"
title: Update GitHub Issue #128 with Results
status: not-started
agent: general-purpose
dependencies: ["1.2", "2.1", "2.2", "2.3"]
priority: 3
complexity: low
accuracy-risk: low
---
```

**Status**: ✅ COMPLETE
**Started**: 2026-02-28T00:00:00Z
**Completed**: 2026-02-28T00:00:00Z
**Dependencies**: Tasks 1.2, 2.1, 2.2, 2.3
**Priority**: 3
**Complexity**: Low
**Agent**: general-purpose

### Context

GitHub Issue #128 tracks this validation task. The backlog item at `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` is the local cache. The architecture spec calls for a closing comment with per-step evidence summary and issue closure.

Use `gh issue comment` and `gh issue close` with `-R Jamie-BitFlight/claude_skills` on every command (git remote points to a local proxy — `gh` cannot auto-detect the repo).

The comment must summarize validation results: pass/fail per step, environment, versions, and a reference to the task file for full evidence. If any step failed, the comment explains what failed and marks the issue BLOCKED rather than closing it.

### Objective

Post a closing validation summary comment on GitHub Issue #128 and close the issue if all validation steps passed, or mark it BLOCKED with the specific failure evidence if any step failed.

### Required Inputs

- Task 1.1 evidence block (version strings)
- Task 1.2 evidence block (pass/fail per step)
- Tasks 2.1–2.3 completion status
- `gh` CLI available (install via `/gh` skill if needed: `Skill(skill: "gh")`)

### Requirements

1. Verify `gh` is available: `gh --version`
2. Confirm all prior tasks completed (check task statuses in this file)
3. Compose a comment summarizing:
   - Environment: Node.js version, agent-browser version, Chromium version, OS
   - Per-step results (pass/fail) for Steps 3, 4, and optionally Step 5 from Task 1.2
   - Documentation changes made (Prerequisites section, Error Recovery section, Validation Status table, template annotation)
   - Link to this task file: `plan/tasks-10-validate-agent-browser.md`
4. Post the comment:

   ```bash
   gh issue comment 128 -R Jamie-BitFlight/claude_skills --body "{comment text}"
   ```

5. If all validation steps passed, close the issue:

   ```bash
   gh issue close 128 -R Jamie-BitFlight/claude_skills --comment "Closing: all validation steps passed. See task file for full evidence."
   ```

6. If any step failed or was BLOCKED, do NOT close — post a BLOCKED comment instead with the specific error from Task 1.2 evidence

### Constraints

- Always pass `-R Jamie-BitFlight/claude_skills` to every `gh` command
- Do NOT close the issue if Task 1.2 has any BLOCKED or failed step
- Comment must reference the task file path for full evidence traceability
- Do NOT fabricate or summarize evidence — use exact exit codes and outputs from Task 1.2 evidence block

### Expected Outputs

- GitHub Issue #128 has a comment with validation summary
- GitHub Issue #128 is closed (if all steps passed) or remains open with BLOCKED comment (if any step failed)

### Acceptance Criteria

1. `gh issue view 128 -R Jamie-BitFlight/claude_skills` shows a new comment with validation results
2. If all steps passed: issue state is `closed`
3. If any step failed: issue state is `open` and comment contains the specific error message from Task 1.2

### Verification Steps

1. Run `gh issue view 128 -R Jamie-BitFlight/claude_skills` and confirm comment is present
2. Confirm issue state matches expected outcome (closed or open with BLOCKED comment)
