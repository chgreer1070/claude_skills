# Feature Context: Validate is-fast for Web Content Extraction

## Document Metadata

- **Generated**: 2026-03-02
- **Input Type**: existing_document
- **Source**: GitHub Issue #127, backlog item `./.claude/backlog/p2-validate-is-fast-for-web-content-extraction.md`
- **Status**: DISCOVERY_COMPLETE

---

## Original Request

Test is-fast CLI tool on a host with unrestricted network access to validate viability for Claude Code web content extraction workflows.

**Key validation steps**:

1. Install: `curl --proto '=https' --tlsv1.2 -LsSf https://github.com/Magic-JD/is-fast/releases/latest/download/is-fast-installer.sh | sh`
2. Verify: `is-fast --version` (expect v0.17.7+)
3. Test `--direct` flag: `is-fast --direct https://example.com`
4. Test `--piped` flag: `is-fast --direct https://example.com --piped`
5. Test `--selector` flag: `is-fast --direct https://example.com --piped --selector "h1"`
6. Compare text extraction output with curl, lynx, w3m on 3+ test URLs
7. Document findings and viability assessment

**Context**:

- Blocked on 2026-02-05: DNS resolution failed in restricted environment
- GitHub Issue: #127
- Priority: P2
- Type: Validation task (not a feature implementation)
- Source: Session experimentation 2026-02-05
- Groomed: 2026-02-27

**Fact-Check Summary (2026-02-27)**:

- is-fast install URL valid — VERIFIED
- `--direct` flag (TUI viewer) — VERIFIED
- `--piped` flag (stdout output) — VERIFIED
- `--selector` flag (CSS filtering) — VERIFIED
- Extracts text from JS-rendered pages — **REFUTED** (uses ureq plain HTTP + scraper static HTML parser; no JS rendering capability)

---

## Core Intent Analysis

### WHO (Target Users)

- **AI agents** in Claude Code sessions that need static HTML content extraction (agents running in restricted environments with no JS rendering capability)
- **Skill authors** evaluating is-fast as a baseline tool for web content extraction
- **Product teams** building the web tooling evaluation matrix (comparison: is-fast vs. carbonyl vs. agent-browser vs. curl/lynx/w3m)

### WHAT (Desired Outcome)

A confirmed working end-to-end demonstration of is-fast on a host with full network access, documenting:

1. Installation succeeds and tool is executable (v0.17.7+)
2. Each flag (`--direct`, `--piped`, `--selector`) works as documented
3. Text extraction output quality compared against baseline tools (curl, lynx, w3m) on identical test URLs
4. A comparison table showing output accuracy, formatting differences, and selector filtering capability
5. A clear recommendation: is-fast is suitable/unsuitable as a baseline tool for static HTML extraction in agent workflows
6. **Critical correction**: is-fast does NOT render JavaScript — it extracts text from static HTML only

### WHEN (Trigger Conditions)

- When a Claude Code skill requires fast, lightweight static HTML text extraction without JS rendering
- When evaluating which tool to use as the baseline extraction method (fastest, no dependencies)
- When building documentation for agents on what extraction tools are available and when to use each

### WHY (Problem Being Solved)

1. **Environment feasibility**: is-fast was blocked by DNS failures in the restricted environment. Needs validation on an unrestricted host to confirm the tool itself works.
2. **Capability gap in documentation**: The original request incorrectly claimed is-fast renders JavaScript. This false claim was discovered and must be corrected before the tool is recommended to anyone.
3. **Missing comparison baseline**: No one has tested is-fast against curl/lynx/w3m side-by-side to know if its extraction quality is competitive. Its speed advantage (plain HTTP + static parse) is only valuable if output quality is acceptable.
4. **Skill integration decision**: Before creating a `/is-fast` skill or recommending is-fast in documentation, the team needs confirmed evidence that it works and produces acceptable output.

---

## Codebase Research

### Similar Patterns Found

#### Pattern 1: Validation backlog items with RT-ICA tables (agent-browser, carbonyl)

- **Location**: `.claude/backlog/p2-validate-agent-browser-for-web-automation.md`, `.claude/backlog/p2-validate-carbonyl-terminal-browser.md`, and corresponding feature-context documents
- **Relevance**: These items use identical structure: fact-check table → RT-ICA availability table → reproducibility steps → scope → output/evidence → dependencies. The is-fast validation follows the same pattern and forms part of the web tooling evaluation matrix.
- **Reusable**: The RT-ICA table format (condition/status/info needed) and the groomed reproducibility steps (step-by-step verification procedure)

#### Pattern 2: Feature context document with scope boundaries and open questions

- **Location**: `plan/feature-context-validate-agent-browser.md` (7 identified gaps, 5 unresolved questions with categories and why-it-matters)
- **Relevance**: is-fast validation also has environmental dependencies (network access), documentation gaps (JS rendering claim to correct), and scope boundaries (static HTML only vs. dynamic rendering).
- **Reusable**: The gap table structure (category: Prerequisites / Documentation / Validation history / Error recovery) and question format (category, gap, options, why-it-matters, resolution pending)

#### Pattern 3: CLI tool comparison matrix in documentation

- **Location**: Agent browser and carbonyl skills document feature comparison tables (capabilities vs. tool)
- **Relevance**: is-fast needs to be positioned in the comparison matrix: is-fast (plain HTTP, static HTML, fastest, no dependencies) vs. agent-browser (JS-capable, Playwright, slower, needs browsers) vs. carbonyl (full browser, slowest, full rendering).
- **Reusable**: The comparison table structure showing which tools support which features

### Existing Infrastructure

**is-fast project**:

- GitHub repository: `Magic-JD/is-fast` (v0.17.7, released 2025-11-03, 164 stars)
- Technology: Rust-based, uses `ureq` (HTTP client) + `scraper` (HTML parser), no browser engine
- Distribution: Installer script (curl), Homebrew, cargo
- Documentation: README on GitHub with CLI flag reference (verified 2026-02-27)

**Related validation items in repo**:

- `#126`: Carbonyl browser integration (full browser rendering)
- `#128`: agent-browser validation (Playwright-based, JS-capable)
- `#129`: Carbonyl validation (terminal browser, full features)

**Comparison baseline tools**:

- `curl` — HTTP client, returns raw response (no HTML parsing)
- `lynx` — Terminal web browser, renders basic HTML, no JS
- `w3m` — Terminal web browser, renders HTML, no JS
- All three are typical system utilities; extraction quality varies

### Code References

- `.claude/backlog/p2-validate-is-fast-for-web-content-extraction.md:30-46` — RT-ICA table documenting tool capabilities and validation readiness
- `.claude/backlog/p2-validate-is-fast-for-web-content-extraction.md:48-114` — Groomed reproducibility steps, scope definition, output specifications

---

## Use Scenarios

### Scenario 1: Agent needs lightweight static HTML extraction in a resource-constrained environment

**Actor**: Claude Code AI agent in a CLI-only environment (no GUI, no heavy binaries)

**Trigger**: User asks "fetch the main content from https://example.com/docs"

**Goal**: Agent quickly extracts readable text from the page without spinning up a full browser

**Expected outcome**: is-fast `--piped` returns clean text content suitable for further processing

**Current blockers**: Unknown if is-fast works on unrestricted hosts; no quality comparison available

**Desired state after validation**: Agent can choose is-fast if speed/simplicity is more important than handling JS-rendered content; documentation clarifies when to use is-fast vs. agent-browser

### Scenario 2: Skill author building a web content extraction skill

**Actor**: Developer creating a `/content-extractor` skill for Claude Code

**Trigger**: Needs to choose between curl, lynx, w3m, is-fast, agent-browser as the extraction backend

**Goal**: Select the best tool for the use case (trade-off: speed vs. JS rendering capability)

**Current state**: is-fast viability is unknown (unvalidated); comparison table does not exist

**Desired state after validation**: Comparison table clearly shows: is-fast fastest for static HTML, agent-browser required for JS, lynx/w3m as zero-dependency baselines

### Scenario 3: Documentation reviewer ensuring tool claims are accurate

**Actor**: Skill maintainer or documentation reviewer

**Trigger**: Reading tool recommendations in skill documentation

**Goal**: Verify that tool capabilities described (e.g., "extracts JS-rendered content") are accurate

**Current problem**: is-fast description claimed JS rendering capability, which was false

**Desired state after validation**: Documentation corrected; is-fast described as static-HTML-only; JS-capable tools (agent-browser, carbonyl) clearly distinguished

---

## Gap Analysis

### Identified Gaps

| # | Category | Gap Description | Impact |
|---|----------|-----------------|--------|
| 1 | Environment | Validation requires unrestricted network host (DNS, HTTP/HTTPS); restricted environment failed 2026-02-05 | Cannot proceed without access to an unrestricted host; task is currently BLOCKED on environment |
| 2 | Documentation | Original claim "extracts text from JS-rendered pages" is FALSE | Any agent or documentation reader following original description will expect JS rendering that does not exist; misleading technical claim |
| 3 | Comparison baseline | No side-by-side output comparison exists between is-fast, curl, lynx, w3m | Cannot assess whether is-fast extraction quality is acceptable relative to existing tools; speed advantage is meaningless if output is poor |
| 4 | Tool selection criteria | No documented guidance on when to use is-fast vs. other tools | Agents or skill authors have no decision framework for tool selection |
| 5 | Validation history | is-fast has never been tested end-to-end in this repository's context | "No blockers identified" in RT-ICA, but not "tested and working" — difference is material |
| 6 | Selector filtering | `--selector` flag claim verified in documentation but not tested in practice | Unknown if CSS selector filtering actually works correctly or has edge cases |
| 7 | Test URLs | Validation steps reference "3+ URLs" but do not specify which ones | Reproducer may choose unrepresentative URLs; need standardized test pages |

---

## Questions Requiring Resolution

### Q1: What is the target execution environment for this validation?

- **Category**: Scope
- **Gap**: Task requires "unrestricted network access" but the phrase is ambiguous. Does this mean: a public cloud host? Local machine with internet? Specific OS/arch?
- **Question**: Should validation happen on (A) a Linux host with full internet access, (B) any available unrestricted host, (C) a specific environment matching Claude Code production constraints?
- **Why It Matters**: Different environments have different system library availability, DNS resolver behavior, and proxy rules. Validation on the wrong environment provides no insight into production viability.
- **Resolution**: _pending_

### Q2: Should the comparison include only curl/lynx/w3m, or also agent-browser and carbonyl?

- **Category**: Scope
- **Gap**: Grooming section lists "curl, lynx, w3m" as comparison baselines. But the related items (#126, #128, #129) suggest is-fast should be positioned in a 6-tool matrix (is-fast, curl, lynx, w3m, agent-browser, carbonyl).
- **Question**: Should comparison output be limited to the three baseline tools already specified, or expanded to include JS-capable tools (agent-browser, carbonyl) to show the capability gap?
- **Options**:
  - A) Keep scope narrow: is-fast vs. curl/lynx/w3m only (static HTML tools only)
  - B) Expand scope: is-fast vs. all available tools, showing where JS rendering makes a difference
  - C) Two-phase approach: static comparison first (is-fast/curl/lynx/w3m), then optional JS-capable comparison
- **Why It Matters**: A is fastest to execute, allows early decision on static HTML tooling. B provides richer insight into capability trade-offs but takes longer. C balances both.
- **Resolution**: _pending_

### Q3: What constitutes "acceptable" output quality in the comparison table?

- **Category**: Acceptance criteria
- **Gap**: Grooming section says "compare output quality" but does not define what "quality" means or what pass/fail looks like. Is the metric: exact character match? semantic correctness? formatted readability? selector accuracy?
- **Question**: What specific metrics should be measured in the comparison table? (e.g., text content accuracy, formatting preservation, link extraction, element count matching, selector precision)
- **Options**:
  - A) Qualitative comparison: side-by-side output review, note formatting and content differences
  - B) Quantitative metrics: character count, paragraph count, link count, CSS selector accuracy (% of expected elements matched)
  - C) Hybrid: qualitative with quantitative spot checks on critical features
- **Why It Matters**: Without defined criteria, "quality" is subjective. Validation result may be ambiguous ("close enough?"). Defined metrics enable clear pass/fail decision.
- **Resolution**: _pending_

### Q4: Should selector filtering edge cases be tested (nested selectors, multiple matches, attribute selectors)?

- **Category**: Validation scope
- **Gap**: `--selector` flag is documented but validation steps only mention basic usage. Unknown if edge cases work correctly.
- **Question**: Does validation of `--selector` include only simple tag/class selectors (e.g., `--selector "h1"`, `--selector ".content"`), or also complex selectors (attribute selectors, descendant combinators, multiple matches)?
- **Options**:
  - A) Basic selectors only (h1, .classname, #id) — representative of common use
  - B) Include at least one complex selector (attribute selector or combinator) to test robustness
  - C) Full CSS selector test suite (5+ edge cases) to fully exercise the flag
- **Why It Matters**: A is sufficient if use is expected to be simple. B catches common edge cases. C provides comprehensive validation but extends timeline.
- **Resolution**: _pending_

### Q5: After validation passes, should a `/is-fast` skill be created?

- **Category**: Integration
- **Gap**: Task is validation only. If validation succeeds and is-fast is deemed viable, the next step (skill creation) is not scoped.
- **Question**: Should validation completion trigger automatic skill creation, or should skill creation be a separate backlog item?
- **Options**:
  - A) Validation only — produce a report, no skill creation
  - B) Validation + skill creation — create `/is-fast` skill as part of this task if validation passes
  - C) Validation + optional skill — produce report, defer skill creation decision to team
- **Why It Matters**: A is minimal scope. B integrates the full evaluation path (validate → create skill → document). C provides flexibility for team decision.
- **Resolution**: _pending_

### Q6: What should happen to the false "JS rendering" claim in the backlog item?

- **Category**: Documentation correction
- **Gap**: Fact-check (2026-02-27) refuted the JS rendering claim, marked as "REFUTED" in the backlog item. The backlog says "JS rendering claim must be removed from description" but this hasn't been done yet.
- **Question**: Should the backlog item description be corrected before validation begins, or is this part of the validation task's cleanup?
- **Why It Matters**: If left uncorrected, the backlog item misleads anyone reading it. Correction can happen before or after validation; clarity on ownership prevents the task from being incomplete.
- **Resolution**: _pending_

---

## Goals (Pending Resolution)

These goals will be finalized after questions are resolved.

1. Confirm is-fast v0.17.7+ installs and executes successfully on an unrestricted host
2. Verify `--direct` (TUI viewer), `--piped` (stdout), and `--selector` (CSS filtering) flags all work as documented
3. Produce a side-by-side comparison table of text extraction output from is-fast, curl, lynx, and w3m on 3+ representative test URLs
4. Document that is-fast does NOT render JavaScript and is suitable only for static HTML extraction
5. Provide a clear recommendation on is-fast viability for Claude Code workflows (suitable as baseline/fast option, with documented limitations)
6. Correct the false JS rendering claim in documentation (either backlog item or new research entry)

---

## Related Work

This validation task is part of a larger web tooling evaluation initiative:

- **#126**: Carbonyl browser integration (terminal browser with full rendering)
- **#128**: Validate agent-browser (Playwright-based JS-capable extraction)
- **#129**: Validate carbonyl (full browser features)
- **is-fast (#127)**: Baseline static HTML extraction (this task)

These items form a comparison matrix that informs skill creation and tool selection recommendations.

---

## Blockers & Assumptions

### Blockers

1. **Environment requirement**: Validation cannot proceed on the restricted environment (DNS failed 2026-02-05). Requires access to a host with unrestricted outbound DNS and HTTP/HTTPS.

### Assumptions (from RT-ICA approval)

1. Install URL and CLI flags are documented and verified (✓ fact-checked 2026-02-27)
2. is-fast is actively maintained (v0.17.7, not archived)
3. Rust toolchain is available on the target host for compilation (if needed) or pre-built binaries work
4. Test URLs are accessible from the target host (needs validation during execution)

---

## Next Steps

1. **Resolve Q1**: Identify and confirm unrestricted host for validation
2. **Resolve Q2–Q5**: Document scope boundaries (comparison tools, quality metrics, selector depth, skill creation decision)
3. **Execute validation**: Install is-fast, run tests on 3+ URLs, capture output
4. **Resolve Q6**: Correct false JS rendering claim in documentation
5. **Produce comparison table**: Side-by-side analysis of extraction quality
6. **Write validation report**: Findings, recommendation, evidence
7. **Close issue #127** with result (pass/blocked)

---

## Success Criteria

- [ ] Validation executes on an unrestricted host (questions Q1 resolved)
- [ ] Scope boundaries documented (questions Q2–Q5 resolved)
- [ ] is-fast installed and `--version` outputs v0.17.7+
- [ ] All three flags (--direct, --piped, --selector) tested and working
- [ ] Comparison table completed for is-fast vs. curl/lynx/w3m on 3+ URLs
- [ ] False JS rendering claim corrected in documentation
- [ ] Clear recommendation written (suitable/unsuitable for Claude Code workflows)
- [ ] GitHub Issue #127 updated with validation results
