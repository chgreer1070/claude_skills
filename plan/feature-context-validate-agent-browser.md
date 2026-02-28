# Feature Context: Validate agent-browser for Web Automation

## Document Metadata

- **Generated**: 2026-02-28
- **Input Type**: existing_document
- **Source**: GitHub Issue #128, backlog item `.claude/backlog/p2-validate-agent-browser-for-web-automation.md`
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Test agent-browser (Playwright-based) on host with unrestricted network and Playwright browsers installed.

**Validation steps**:

- Install browsers: `npx playwright install` or `agent-browser install`
- Test: `npx agent-browser open https://code.claude.com/docs/en/skills`
- Test: `npx agent-browser snapshot -i` (get element refs)
- Test: `npx agent-browser get text @e1` (extract page text via element ref)
- Verify snapshot/interact/re-snapshot workflow works
- Document prerequisites for skill to function

**Context**:

- Blocked on 2026-02-05: Could not download Playwright browsers (DNS resolution failed, missing system libs)
- Skill location: `.claude/skills/agent-browser/SKILL.md`
- GitHub Issue: #128
- Priority: IDEA
- Source: Session experimentation 2026-02-05

**Fact-Check Summary**:

- agent-browser npm package exists (v0.15.0, Vercel Labs) — VERIFIED
- `npx agent-browser open <url>` works — VERIFIED
- `npx agent-browser snapshot -i` gets element refs — VERIFIED
- `npx agent-browser get text body` — REFUTED (body works as CSS selector but documented syntax is `get text <selector>` with @ref)
- snapshot/interact/re-snapshot workflow — VERIFIED

---

## Core Intent Analysis

### WHO (Target Users)

- **AI agents** using the `/agent-browser` skill to automate web tasks in Claude Code sessions
- **Claude Code skill authors** who need to verify the skill works before documenting it as production-ready
- **Developers** evaluating agent-browser as a web automation tool for agent workflows

### WHAT (Desired Outcome)

A confirmed working end-to-end demonstration of the agent-browser skill on a host with full network access and Playwright browsers installed. The outcome includes:

1. Confirmed installation path (npm global install or npx) with verified Playwright browser binary location
2. At least one successful open → snapshot → get text → close sequence on a real URL
3. Documented prerequisites (Node.js version, Playwright binary location, system library requirements, network requirements) that skill users need to have satisfied before the skill works
4. Corrected validation syntax (refuted `get text body` claim replaced with verified `get text @e1` or `get text body` as CSS selector with clarifying note)

### WHEN (Trigger Conditions)

- When an AI agent is assigned a web automation task and loads the `/agent-browser` skill
- When a developer wants to confirm agent-browser will work in their environment before depending on it
- When the skill documentation is being reviewed for accuracy (prerequisites section currently absent)

### WHY (Problem Being Solved)

The `/agent-browser` skill exists and is documented, but has never been verified to work end-to-end in this repository's execution environment. Two failure modes have been observed:

1. **Environment gap**: The 2026-02-05 session could not install Playwright browser binaries (DNS resolution failed, system libraries missing). The skill documentation does not state what environment conditions are required.
2. **Syntax error in backlog**: The original validation step `npx agent-browser get text body` was documented in the backlog item but the fact-check (2026-02-26) determined this is misleading — `body` functions as a CSS selector, not the expected `@ref` pattern. An agent following the original steps would be working from partially incorrect examples.

Without a successful end-to-end test and a documented prerequisites checklist, any agent or developer loading this skill has an unknown probability of failure.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: CLI tool skill with prerequisites section (gh skill)

- **Location**: `.claude/skills/gh/SKILL.md`
- **Pattern**: The `/gh` skill wraps the `gh` CLI and addresses the "tool may not be installed" problem explicitly. It documents an installation script (`uv run .claude/skills/gh/scripts/setup_gh.py`), describes what the script does step by step, documents the `GITHUB_TOKEN` auth mechanism, and lists the `--force` / `--dry-run` / `--bin-dir` flags for controlling installation. It also names the specific failure condition it solves (`"failed to determine base repo"` error due to proxy git remotes).
- **Relevance**: This is the direct model for what the agent-browser skill's prerequisites section should look like. The gh skill treats "tool may not be installed" as a documented first-class concern, not an assumed precondition.

#### Pattern 2: Validation backlog items with RT-ICA tables (is-fast, carbonyl)

- **Location**: `.claude/backlog/p2-validate-is-fast-for-web-content-extraction.md`, related items #126, #129
- **Pattern**: The web tooling evaluation pattern in this repository uses a consistent structure: fact-check table → RT-ICA availability table → reproducibility steps → scope → output/evidence → dependencies. The is-fast backlog item is directly related (web content extraction tool, same blocked-on-DNS context, same pattern of groomed reproducibility steps).
- **Relevance**: The agent-browser validation follows the same evaluation pattern. These items form a comparison matrix: is-fast (static HTML), agent-browser (JS-capable via Playwright), carbonyl (#129), curl/lynx/w3m (baselines).

#### Pattern 3: Feature context document with gap table (orchestrator-discipline, plugin-linter)

- **Location**: `plan/feature-context-validate-orchestrator-discipline.md`, `plan/feature-context-plugin-linter.md`
- **Pattern**: Feature context documents in this repo use a structured gap table with columns: `#`, `Category`, `Gap Description`, `Impact`. Resolution questions are numbered Q1–QN with options A/B/C and a "Why It Matters" sub-field.
- **Relevance**: This document follows that structure.

#### Pattern 4: Skill with templates directory (agent-browser)

- **Location**: `.claude/skills/agent-browser/templates/`
- **Pattern**: Three shell script templates exist: `form-automation.sh`, `authenticated-session.sh`, `capture-workflow.sh`. The `capture-workflow.sh` template uses `agent-browser get text body` (line 47) — the same pattern that the fact-check refuted as misleading. This is a pre-existing inconsistency between a template and the verified syntax.
- **Relevance**: A side-effect of the validation work should be confirming whether `get text body` (as CSS selector) actually works in practice, so templates can be confirmed or corrected.

### Existing Infrastructure

The agent-browser skill directory at `.claude/skills/agent-browser/` is fully documented:

- **SKILL.md** — 414-line file covering core workflow, all command categories, common patterns (form submission, auth, data extraction, parallel sessions, JS eval, diff), configuration, and ref lifecycle
- **references/** — 7 reference files: `commands.md` (full command reference), `snapshot-refs.md` (ref lifecycle and troubleshooting), `session-management.md`, `authentication.md`, `video-recording.md`, `profiling.md`, `proxy-support.md`
- **templates/** — 3 shell scripts: `form-automation.sh`, `authenticated-session.sh`, `capture-workflow.sh`
- **Backlog item** — `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` contains groomed reproducibility steps, RT-ICA table, dependency notes, and fact-check results

The backlog item's RT-ICA table (groomed 2026-02-26) records:

| Condition | Status |
|-----------|--------|
| agent-browser CLI available | AVAILABLE — v0.15.0 via npx |
| Playwright browsers installed | AVAILABLE — Chromium 141.0 at `/root/.cache/ms-playwright/` |
| Network access for test URLs | DERIVABLE — environment has network; target URL accessibility unverified |
| Skill documentation exists | AVAILABLE — SKILL.md + 7 references + 3 templates |
| Validation step syntax correct | MISSING — `get text body` refuted |
| System libs for rendering | DERIVABLE — headless mode should work; headed may need X11 |

**Decision from RT-ICA**: APPROVED — no blockers for headless validation.

### Code References

- `.claude/skills/agent-browser/SKILL.md:1-5` — frontmatter: `allowed-tools: Bash(npx agent-browser:*), Bash(agent-browser:*)` — skill scopes itself to these two invocation patterns
- `.claude/skills/agent-browser/SKILL.md:11-28` — Core Workflow section (open → snapshot → interact → re-snapshot) — the primary pattern to validate
- `.claude/skills/agent-browser/SKILL.md:69-72` — `get text` command documented as `agent-browser get text @e1` (element ref) — the verified syntax
- `.claude/skills/agent-browser/SKILL.md:154-156` — `get text body > page.txt` appears in Data Extraction pattern — uses `body` as CSS selector
- `.claude/skills/agent-browser/templates/capture-workflow.sh:47` — `agent-browser get text body` used in template — affected by the refuted claim
- `.claude/skills/agent-browser/references/commands.md:55-64` — Get Information section lists `get text @e1`, `get html @e1`, `get value @e1`, `get attr @e1 href`, `get title`, `get url`, `get count ".item"`, `get box @e1`, `get styles @e1`
- `.claude/backlog/p2-validate-agent-browser-for-web-automation.md:19-39` — RT-ICA table with current availability assessment
- `.claude/backlog/p2-validate-agent-browser-for-web-automation.md:47-63` — Groomed reproducibility steps

---

## Use Scenarios

### Scenario 1: Agent receives a web scraping task and loads the skill

**Actor**: Claude Code AI agent in a session with the agent-browser skill installed

**Trigger**: User asks "extract the main content from https://example.com/docs and summarize it"

**Goal**: Agent successfully navigates to the URL, takes a snapshot, uses element refs to extract text, and returns the content to the user

**Expected prerequisites to be satisfied**:

1. `npx agent-browser` is resolvable (Node.js and npm installed, or agent-browser globally installed)
2. Playwright Chromium binary is present at `~/.cache/ms-playwright/` or equivalent
3. Network access to the target URL is available
4. System libraries for headless Chromium rendering are present (no missing `.so` files)

**Current state**: The skill will fail silently or with an unclear error if any prerequisite is absent. SKILL.md does not list prerequisites; an agent loading the skill has no guidance on what to check if the first command fails.

**Desired state after validation**: Skill includes a Prerequisites section that lists each requirement, how to check it, and the install command to satisfy it.

### Scenario 2: Developer evaluating agent-browser for a new Claude Code plugin

**Actor**: Plugin developer considering whether to use agent-browser for a web task within their plugin

**Trigger**: Developer reads `.claude/skills/agent-browser/SKILL.md` to decide if this tool is suitable

**Goal**: Developer can determine whether agent-browser will work in their deployment environment without having to run it first

**Current state**: SKILL.md contains no prerequisites section. The developer must infer that Node.js, npm, and Playwright browsers are needed, and has no guidance on system library requirements or the install command for browser binaries.

**Desired state after validation**: A documented prerequisites checklist in SKILL.md with install commands and version requirements, derived from observed behavior during the validation run.

### Scenario 3: Validation confirms snapshot/interact/re-snapshot workflow on a real documentation page

**Actor**: Skill maintainer running the validation sequence defined in the backlog item

**Trigger**: Host with unrestricted network access is available; Playwright Chromium is confirmed installed

**Goal**: Confirm that the four-step core workflow (open → snapshot → interact → re-snapshot) works end-to-end on `https://code.claude.com/docs/en/skills`

**Steps to execute**:

1. `npx agent-browser open https://code.claude.com/docs/en/skills`
2. `npx agent-browser snapshot -i` — observe element refs in output
3. `npx agent-browser get text @e1` — observe text output for first ref
4. `npx agent-browser close`

**Expected outcome**: Each command exits without error; snapshot output contains `@e1`, `@e2`, ... refs; `get text @e1` returns the text content of that element.

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Documentation | SKILL.md has no prerequisites section | Any agent or user attempting to use the skill without Playwright browsers installed will get an opaque failure with no remediation guidance |
| 2 | Documentation | Validated syntax for `get text` is not clearly differentiated from CSS-selector usage in SKILL.md | Agents may use `get text body` (works as CSS selector) without understanding it is not a documented @ref pattern; potential confusion for agents that try `get text heading` or other tag names |
| 3 | Template correctness | `templates/capture-workflow.sh:47` uses `agent-browser get text body` — this is functional but not the canonical @ref syntax | Template teaches a pattern that may not generalize; agents using the template as a model may write `get text div` or `get text p` expecting tag-based selection when those are not interactive refs |
| 4 | Validation history | End-to-end validation has never been completed on an unrestricted host | There is no confirmed evidence that the full workflow works; current state is "no blockers identified in RT-ICA" but not "tested and confirmed working" |
| 5 | Environment documentation | Node.js version requirement, npm requirement, and supported OS/arch for agent-browser v0.15.0 are not documented in SKILL.md | Agents cannot verify compatibility before attempting installation |
| 6 | Error recovery | SKILL.md does not document what to do if Playwright browser binaries are missing at runtime | When `agent-browser open <url>` fails due to missing browser binary, the agent receives an error with no next step in the skill guidance |
| 7 | Syntax clarification | The original backlog item stated `get text body` as the validation step; this was refuted as "misleading but functional" — but the distinction is not captured in SKILL.md | Future maintainers or agents reading only SKILL.md will encounter `get text body` in the Data Extraction pattern (line 154) without knowing it is a CSS selector, not a standard @ref |

---

## Questions Requiring Resolution

### Q1: What is the minimum Node.js version required for agent-browser v0.15.0?

- **Category**: Prerequisites
- **Gap**: SKILL.md does not specify a Node.js version. The npm registry metadata for agent-browser should declare this, but it is not surfaced in the skill documentation.
- **Why It Matters**: Claude Code sessions may run on hosts with Node.js 16, 18, or 20. If agent-browser requires Node 18+ and the host has 16, the skill fails with a version error that is not explained.
- **Resolution**: _pending_ — check `package.json` `engines` field for agent-browser v0.15.0 during validation

### Q2: Does `agent-browser install` (the built-in install command) work identically to `npx playwright install`?

- **Category**: Prerequisites
- **Gap**: The original backlog item listed both `npx playwright install` and `agent-browser install` as options. The RT-ICA accepted both without verifying they produce identical results. It is possible `agent-browser install` installs only the Chromium binary used by agent-browser, while `npx playwright install` installs all browsers (Chromium, Firefox, WebKit).
- **Why It Matters**: Documenting the correct minimal install command avoids agents installing 3 browser binaries when only 1 is needed.
- **Resolution**: _pending_ — test both commands during validation and compare installed paths

### Q3: Does headless Chromium rendering work without additional system libraries in the target execution environment?

- **Category**: Prerequisites
- **Gap**: The 2026-02-05 session was blocked by missing system libs in addition to DNS failures. The RT-ICA notes "headless mode should work; headed may need X11" but this is marked DERIVABLE, not AVAILABLE — meaning it was inferred, not confirmed.
- **Why It Matters**: Missing system libraries (e.g., `libgbm.so.1`, `libnss3.so`, `libatk-1.0.so.0`) cause Chromium to crash at launch with an error that does not mention agent-browser. An agent encountering this has no guidance in the skill.
- **Resolution**: _pending_ — observe whether `agent-browser open <url>` succeeds or produces a library-missing error during validation

### Q4: Should `get text body` be documented as a CSS-selector pattern, explicitly separated from @ref usage?

- **Category**: Documentation correctness
- **Gap**: `get text body` appears in two places: `SKILL.md:154` (Data Extraction pattern) and `templates/capture-workflow.sh:47`. The fact-check ruled it "misleading but functional." The commands reference documents `get text @e1` as the canonical form. There is no explanation of when CSS selectors are valid vs. when @refs are required.
- **Options**:
  - A) Keep `get text body` as-is, add an inline comment clarifying it is a CSS selector
  - B) Replace `get text body` with `get text @e1` (from snapshot) plus a comment about `body` as fallback
  - C) Add a note in the Data Extraction pattern section distinguishing @ref usage from CSS selector usage
- **Why It Matters**: Agents use SKILL.md as a pattern library. If `get text body` is shown without context, they may write `get text h1` or `get text .content` expecting those to work without understanding the selector/ref distinction.
- **Resolution**: _pending_ — depends on what works during validation testing

### Q5: Is the skill ready to be marked production-validated after a successful test run, or are there other behaviors (parallel sessions, state persistence, JS eval) that also need validation?

- **Category**: Scope
- **Gap**: The validation task as defined in the backlog focuses on the core workflow (open, snapshot, get text, close). The skill documents many additional features: parallel sessions, state persistence (`state save`/`state load`), JS eval, video recording, proxy support, iOS simulator. None of these have been validated.
- **Options**:
  - A) Mark core workflow as validated; explicitly scope remaining features as unvalidated in SKILL.md
  - B) Validate only core workflow; leave other features undocumented as to validation status
  - C) Expand validation scope to include at least one additional feature (e.g., screenshot capture)
- **Why It Matters**: A skill marked "validated" without caveat implies all documented features work. If only the core workflow is confirmed, that should be stated.
- **Resolution**: _pending_ — depends on time available during validation session

---

## Goals (Pending Resolution)

These goals will be finalized after questions are resolved.

1. At least one complete open → snapshot → `get text @e1` → close sequence executes without error on a real URL
2. Prerequisites are documented in SKILL.md with exact install commands, version requirements, and system library check
3. The `get text body` usage in SKILL.md and templates is either confirmed with a clarifying note or replaced with canonical @ref usage
4. A validation status note is added to SKILL.md (date confirmed, host conditions, browser binary version)
5. The backlog item (GitHub Issue #128) is updated with the validation result and closed if passing

---

## Next Steps

1. Execute the groomed reproducibility steps from `.claude/backlog/p2-validate-agent-browser-for-web-automation.md` (lines 47–63) on a host with unrestricted network access
2. Capture exact command output for each step as evidence
3. Resolve Q1 (Node.js version), Q2 (install command), Q3 (system libs) from observed behavior during the run
4. Resolve Q4 (get text body documentation) based on whether CSS selector usage is confirmed
5. Resolve Q5 (validation scope) — decide whether to mark only core workflow or expand scope
6. Update SKILL.md with prerequisites section and corrected/clarified syntax
7. Close GitHub Issue #128 with validation evidence or document new blockers if the run fails
