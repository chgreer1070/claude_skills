# is-fast Validation Architecture

## Validation Goal

Establish whether is-fast (static HTML parser + ureq HTTP) can reliably extract **complete, structured content** from technical documentation pages without:
- Summarizing or paraphrasing content
- Dropping structural elements (tables, code blocks, lists)
- Losing semantic accuracy (e.g., parameter types, field names, exact code syntax)
- Requiring authentication (for restricted network scenarios)

This validation directly addresses the WebFetch tool's limitations: tables summarized, code examples replaced with paraphrasing, and scenario-specific details lost.

---

## Test URLs and Expected Content

### Test URL 1: Skill Frontmatter Schema (Claude Code Ecosystem)

**URL**: `https://raw.githubusercontent.com/Jamie-BitFlight/claude_skills/main/.claude/docs/SKILL.md` or equivalent published documentation

**Purpose**: Validate table extraction with semantic content (field names, types, descriptions)

**Expected Content Structure**:
```
- Table with columns: Field | Type | Required | Description | Default
- At least 5 rows (e.g., name, description, frontmatter, hooks, tags)
- Inline code markers (backticks) for field types (e.g., `string`, `boolean[]`)
- Nested properties (e.g., hooks → type, matcher, command)
- Example YAML blocks showing actual syntax
```

**Success Criteria**:
- Table extracted with ALL 5+ columns visible
- Field type annotations preserved (e.g., `string`, `string[]`, `{...}`)
- No truncation of description text
- Example YAML blocks verbatim (no syntax highlighting substitution)

---

### Test URL 2: Docker Compose Specification (Tables + Code Examples)

**URL**: `https://docs.docker.com/reference/compose-file/` (or official Docker Compose schema reference)

**Purpose**: Validate extraction of technical schema documentation with mixed tables and code

**Expected Content Structure**:
```
- Property definition tables: service name | type | required | default | example
- Code examples showing actual compose syntax (YAML)
- Nested property descriptions (e.g., `services.build`, `services.environment`)
- Notes about version support, breaking changes
```

**Success Criteria**:
- Table columns all present (property, type, required, default)
- Code blocks in YAML syntax preserved exactly
- No "Here's what it looks like" summaries in place of actual examples
- Nested indentation and structure maintained
- Version/warning callouts preserved

---

### Test URL 3: Packer HCL Schema (Scenario-Based Examples)

**URL**: `https://developer.hashicorp.com/packer/docs/templates/hcl_templates` (or equivalent schema documentation)

**Purpose**: Validate extraction of scenario-specific documentation and exact code examples

**Expected Content Structure**:
```
- Configuration block examples: datasource, variable, local, build
- Multi-line HCL snippets with actual syntax highlighting
- Scenario descriptions: "For use in X scenario, configure Y like this..."
- Inline parameter documentation with type constraints
```

**Success Criteria**:
- Scenario descriptions preserved word-for-word
- HCL code blocks verbatim with syntax preserved
- No paraphrasing of configuration examples
- Comments within code blocks preserved
- All parameter options listed (not summarized)

---

### Test URL 4: GitLab YAML Schema (Complex Nested Documentation)

**URL**: `https://docs.gitlab.com/ee/ci/yaml/` (GitLab CI/CD configuration schema)

**Purpose**: Validate extraction of complex nested structures with many examples

**Expected Content Structure**:
```
- Nested configuration keys with path notation (e.g., `artifacts.reports.coverage_report`)
- Type definitions (string, boolean, integer array)
- Multiple examples per section showing variations
- Edge cases and gotchas documented inline
- Links to related sections (preserved or clearly indicated)
```

**Success Criteria**:
- Nested key paths preserved exactly (e.g., `artifacts.reports.coverage_report`)
- All examples extracted (not just first one)
- Type constraints verbatim
- Edge case documentation complete
- Gotcha callouts not lost

---

## Tool Comparison Matrix

| Aspect | is-fast | curl | lynx | w3m |
|--------|---------|------|------|-----|
| **HTML Parsing** | Static HTML parser + structural extraction | Raw HTML (no parsing) | Terminal rendering | Terminal rendering |
| **Table Extraction** | Cell-by-cell structured extraction | Raw HTML with tags | Visual blocks (unreliable) | Visual blocks (unreliable) |
| **Code Block Preservation** | Verbatim text nodes | Raw HTML with tags | Rendered text (loses syntax) | Rendered text (loses syntax) |
| **Semantic Accuracy** | High (no paraphrasing) | High (raw data) | Medium (rendering artifacts) | Medium (rendering artifacts) |
| **Network Connectivity** | ureq HTTP (works offline with cache) | Requires curl binary | Requires curses, $TERM | Requires ncurses, $TERM |
| **Authentication Support** | Basic HTTP auth via headers | Full curl auth suite | Limited (basic auth) | Limited (basic auth) |
| **Execution Environment** | Portable (embedded HTTP) | Requires system curl | Requires system lynx + TTY | Requires system w3m + TTY |
| **Output Format** | Structured (JSON, TOML, plain text) | Raw HTML (requires manual parsing) | Text with ANSI codes | Text with formatting codes |
| **Usability for Docs** | High (complete, accurate) | Low (requires post-processing) | Low (visual artifacts) | Low (visual artifacts) |

---

## Completeness Metrics

### Metric 1: Table Structural Completeness

**Definition**: A table is "complete" when:
1. ALL columns are extracted (count matches expected)
2. ALL rows are extracted (count matches expected)
3. Cell content is verbatim (no truncation or summarization)
4. Cell markup is preserved (backticks for code, bold/italic if applicable)

**Measurement**:
```
Completeness Score = (
    (Columns_Extracted / Columns_Expected) * 0.25 +
    (Rows_Extracted / Rows_Expected) * 0.25 +
    (Cell_Content_Accuracy / 100) * 0.25 +
    (Markup_Preserved / 100) * 0.25
) * 100
```

**Target**: 100% for documentation use (no partial tables acceptable)

**Example**:
- Expected: 5 columns × 8 rows with inline code
- Extracted: 5 columns × 8 rows, code preserved
- Score: 100%

---

### Metric 2: Code Block Verbatim Accuracy

**Definition**: Code is "accurate" when:
1. Syntax matches source exactly (character-for-character)
2. Indentation/whitespace preserved
3. Comments within code preserved
4. No syntax highlighting codes injected (e.g., `\x1b[38;...`)
5. Language context clear (e.g., YAML, HCL, Python, JSON)

**Measurement**:
```
Accuracy Score = (
    (Syntax_Match / 100) * 0.4 +
    (Indentation_Preserved / 100) * 0.3 +
    (Comments_Preserved / 100) * 0.2 +
    (No_Markup_Pollution / 100) * 0.1
) * 100
```

**Target**: 100% for production documentation extraction

**Example - Failure Modes**:
- Tool extracts: "Here's a basic example:" (FAIL - summarization)
- Tool extracts: `key: value\n` but source was `key: value  # comment` (FAIL - 90% accuracy)
- Tool extracts with ANSI codes: `\x1b[32m` prefix (FAIL - markup pollution)

---

### Metric 3: Scenario-Specific Documentation Preservation

**Definition**: Scenario documentation is "preserved" when:
1. Descriptive text is verbatim (not paraphrased)
2. Exact wording of instructions maintained
3. Examples linked to scenarios are all present
4. Warnings/caveats with specific conditions not lost

**Measurement**:
```
Preservation Score = (
    (Exact_Text_Match / 100) * 0.4 +
    (Examples_Count_Match / 100) * 0.3 +
    (Warnings_Complete / 100) * 0.2 +
    (Links_Preserved_Or_Indicated / 100) * 0.1
) * 100
```

**Target**: 100% for use in requirements gathering and validation

**Example - Failure Modes**:
- Original: "For testing purposes, use the `test` environment variable"
- Extracted: "Set the environment variable for testing" (FAIL - paraphrased)
- Missing examples that were in original (FAIL - incompleteness)

---

## Accuracy Metrics

### Metric 4: Text Extraction Accuracy

**Definition**: Percentage of text correctly extracted vs. expected, accounting for:
- Typos introduced
- Character loss (e.g., special characters, Unicode)
- Word boundary errors

**Measurement**:
```
Text_Accuracy = (Levenshtein_Match(extracted, expected) / expected_length) * 100
```

**Target**: >99% (typos/character loss <1%)

**Test Method**: Character-by-character diff between expected and extracted using `diff -u` or similar

---

### Metric 5: Formatting Preservation

**Definition**: Markup and semantic formatting preserved:
- Inline code (backticks or equivalent indication)
- Bold/italic (or equivalent indicator)
- Links (URL or clear link indicator)
- Lists (indentation and bullet structure)
- Code block boundaries (clear start/end)

**Measurement**:
```
Formatting_Score = (Markup_Elements_Preserved / Markup_Elements_Total) * 100
```

**Target**: 100% for code-heavy documentation

---

### Metric 6: Markup Pollution

**Definition**: Unwanted codes injected by rendering or conversion:
- ANSI escape codes (color, bold: `\x1b[...`)
- HTML entities left unescaped (e.g., `&nbsp;`, `&lt;`)
- Terminal control characters (TAB, BEL)

**Measurement**:
```
Pollution_Score = 100 - (UnwantedChars_Count / Total_Chars) * 100
```

**Target**: 100% (zero pollution)

---

## Task Breakdown (for swarm-task-planner)

### Task 1: Test Environment Setup and Metrics Definition

**Status**: NOT STARTED
**Priority**: 1 (Critical)
**Complexity**: Medium
**Dependencies**: None

**Acceptance Criteria**:
- [ ] Four test URLs identified and confirmed accessible (without auth)
- [ ] Expected content structure documented for each URL (in detail: specific table names, code block counts, etc.)
- [ ] Completeness metric definitions operationalized (how to count columns, rows, examples)
- [ ] Accuracy metric definitions with concrete thresholds
- [ ] Baseline curl raw output captured for reference
- [ ] Test checklist document created with 20+ validation points

**Deliverables**:
- `plan/test-urls.md`: Full URL list with expected structure breakdown
- `plan/metrics-definition.md`: Operationalized metric definitions with test procedures
- `plan/baseline-outputs/`: Directory containing raw curl output for each test URL

**Estimated Effort**: 2-3 hours

---

### Task 2: Tool Installation and Sample Validation

**Status**: NOT STARTED
**Priority**: 1 (Critical)
**Complexity**: Low
**Dependencies**: Task 1

**Acceptance Criteria**:
- [ ] is-fast installed and verified working (verify with `is-fast --version` or equivalent)
- [ ] curl available (system binary or verify with `curl --version`)
- [ ] lynx installed and verified (TTY workaround if needed: tmux method)
- [ ] w3m installed and verified (TTY workaround if needed: tmux method)
- [ ] Sample extraction run on ONE test URL with all four tools
- [ ] Sample outputs saved for manual inspection (raw output files)
- [ ] Each tool confirmed produces output (not errors)

**Deliverables**:
- `plan/sample-outputs/`: Directory with is-fast, curl, lynx, w3m outputs for one test URL
- `plan/tool-installation-log.md`: Installation steps and verification results

**Estimated Effort**: 1 hour

---

### Task 3: Full Validation Run (All URLs, All Tools)

**Status**: NOT STARTED
**Priority**: 1 (Critical)
**Complexity**: High (requires careful output capture and processing)
**Dependencies**: Task 2

**Acceptance Criteria**:
- [ ] All four tools run against all four test URLs
- [ ] Outputs captured consistently (naming: `{tool}-{url-slug}.{format}`)
- [ ] All outputs successfully stored (16 total: 4 tools × 4 URLs)
- [ ] No extraction errors or timeouts (document any that occur)
- [ ] Raw outputs indexed with metadata (timestamp, tool version, URL, extraction time)
- [ ] Validation log created showing run sequence and timing

**Deliverables**:
- `plan/validation-runs/`: Directory structure:
  - `is-fast/`: 4 files (one per URL)
  - `curl/`: 4 files (raw HTML)
  - `lynx/`: 4 files (terminal output)
  - `w3m/`: 4 files (terminal output)
- `plan/validation-run-log.md`: Execution log with timestamps and any issues

**Estimated Effort**: 1-2 hours (mostly automated)

---

### Task 4: Analysis and Comparative Evaluation

**Status**: NOT STARTED
**Priority**: 2 (High)
**Complexity**: High (requires judgment on completeness and accuracy)
**Dependencies**: Task 3

**Acceptance Criteria**:
- [ ] Each tool output manually reviewed for table completeness (columns/rows/content)
- [ ] Code block accuracy assessed (syntax preservation, comment preservation)
- [ ] Scenario-specific documentation checked for paraphrasing/loss
- [ ] Markup pollution detected and documented
- [ ] Completeness scores calculated for each tool-URL combination (16 scores)
- [ ] Accuracy scores calculated (text accuracy, formatting preservation)
- [ ] Detailed notes on failure modes (screenshots, quoted excerpts showing issues)
- [ ] Comparative matrix populated with numerical scores

**Deliverables**:
- `plan/analysis-results/`: Directory with:
  - `completeness-scores.csv`: 4 tools × 4 URLs + metrics
  - `accuracy-scores.csv`: Text accuracy, formatting scores
  - `detailed-findings.md`: Per-tool, per-URL findings with evidence
  - `failure-modes.md`: Documented extraction failures with examples
- `plan/tool-comparison-matrix-populated.md`: Evidence-backed matrix with scores

**Estimated Effort**: 3-4 hours

---

### Task 5: Validation Report and Recommendation

**Status**: NOT STARTED
**Priority**: 2 (High)
**Complexity**: Medium
**Dependencies**: Task 4

**Acceptance Criteria**:
- [ ] Executive summary: is-fast suitable/unsuitable for docs extraction (YES/NO with confidence)
- [ ] Detailed comparison results: scores for each tool-URL combination
- [ ] Recommendation logic: when to use which tool (use case decision tree)
- [ ] Risk assessment: known failure modes and mitigation strategies
- [ ] Portability matrix: which tools work in restricted environments (offline, no TTY, customer machine)
- [ ] Implementation guidance: how to integrate is-fast into WebFetch replacement workflow
- [ ] Limitations and edge cases documented
- [ ] Fallback strategy defined (if is-fast fails, what's the next best tool?)
- [ ] Success criteria mapping: original problem statement addressed?

**Deliverables**:
- `plan/VALIDATION-REPORT.md`: Comprehensive validation report (1500-2500 words)
- `plan/recommendation.md`: Executive summary and decision guidance

**Estimated Effort**: 2-3 hours

---

## Success Criteria (Tool-Specific)

### is-fast Succeeds If:

1. **Table Completeness**: 100% on all four test URLs
   - All columns extracted
   - All rows extracted
   - No cell content summarized or truncated

2. **Code Accuracy**: 100% on all code blocks
   - Verbatim syntax preservation
   - No markup pollution (ANSI codes, HTML entities)
   - Comments and indentation preserved

3. **Scenario Documentation**: 100% on Packer and GitLab examples
   - Exact wording preserved (not paraphrased)
   - All examples extracted (not summarized to one)
   - Warnings and caveats complete

4. **Environment Compatibility**: Works in ALL tested environments
   - Local machine with network
   - Offline (with prior fetch or cache)
   - Restricted network (no external dependencies)
   - CI/CD runner without TTY

5. **Usability**: Output format easily consumable by downstream processes
   - Structured extraction (JSON, TOML, or plain text with clear boundaries)
   - No manual post-processing needed for common use cases
   - Integration straightforward with WebFetch replacement workflow

### Recommendation: is-fast is Best Tool If:

- Scores ≥90% on completeness AND accuracy metrics
- Works in restricted network and offline scenarios
- Requires zero post-processing (structured output)
- Integration cost minimal (can drop into WebFetch replacement)

### Fallback Tools (If is-fast Fails):

1. **curl** (raw HTML extraction):
   - Pro: Complete HTML, no content loss, portable
   - Con: Requires manual HTML parsing and structure extraction
   - Use when: Completeness is non-negotiable, downstream can parse HTML

2. **lynx/w3m** (last resort):
   - Pro: Already renders and extracts text
   - Con: Visual artifacts, TTY requirement, markup loss
   - Use when: is-fast unavailable and acceptable to lose formatting

---

## Validation Output Structure

### Report Directory Layout

```
plan/
├── architect-validate-is-fast.md          ← This document
├── test-urls.md                           ← Test URLs with expected content
├── metrics-definition.md                  ← Operationalized metrics
├── baseline-outputs/
│   ├── curl-url1.html
│   ├── curl-url2.html
│   ├── curl-url3.html
│   ├── curl-url4.html
├── sample-outputs/
│   ├── is-fast-url1.txt
│   ├── curl-url1.html
│   ├── lynx-url1.txt
│   └── w3m-url1.txt
├── validation-runs/
│   ├── is-fast/
│   ├── curl/
│   ├── lynx/
│   └── w3m/
├── validation-run-log.md                  ← Execution log
├── analysis-results/
│   ├── completeness-scores.csv
│   ├── accuracy-scores.csv
│   ├── detailed-findings.md
│   └── failure-modes.md
├── tool-comparison-matrix-populated.md    ← Final matrix with scores
├── VALIDATION-REPORT.md                   ← Comprehensive report
└── recommendation.md                      ← Executive summary
```

---

## Architectural Constraints and Assumptions

### Constraint 1: Real URLs Only
All test URLs must be publicly accessible without authentication. This ensures reproducibility and rules out enterprise portals.

### Constraint 2: No Manual Paraphrasing in Baseline
Expected content structure must be documented by reading source pages directly, not by manually summarizing. This prevents circularity.

### Constraint 3: Completeness Over Ease
Metrics favor complete extraction over ease of parsing. Loss of completeness is worse than extra post-processing work.

### Constraint 4: Environment Portability Required
Tool comparison must account for restricted network scenarios (offline cache, no external deps, no TTY). This is non-negotiable for customer/offline use.

### Assumption 1: Tables Are HTML Tables
Assumption that test URLs use `<table>` HTML elements (not divs pretending to be tables). If not found, substitute with actual table-based documentation.

### Assumption 2: Code Blocks Are `<pre>` or `<code>`
Code examples are wrapped in semantic HTML (`<pre>`, `<code>`, or language-specific tags). If pages use fenced code blocks in HTML, those are preserved.

### Assumption 3: Rendering Doesn't Improve Extraction
Terminal rendering (lynx, w3m) is expected to lose semantic structure. This is expected baseline, not a failure mode.

---

## Quality Checkpoints

### Checkpoint 1: After Task 1
- [ ] Four test URLs confirmed accessible (manually visited)
- [ ] Expected structure documented matches actual page structure
- [ ] Metrics are measurable (not subjective)

### Checkpoint 2: After Task 2
- [ ] All four tools successfully extract data from sample URL
- [ ] Sample outputs are readable and non-empty
- [ ] Tool versions documented

### Checkpoint 3: After Task 3
- [ ] All 16 outputs (4 tools × 4 URLs) successfully captured
- [ ] No tool crashed or timed out
- [ ] File sizes reasonable (not truncated)

### Checkpoint 4: After Task 4
- [ ] Scores assigned objectively (using metric definitions)
- [ ] Failure modes documented with evidence (quoted text or diff)
- [ ] Comparative matrix populated with all 16 results

### Checkpoint 5: After Task 5
- [ ] Recommendation clearly states YES/NO for is-fast
- [ ] Confidence level justified by scores
- [ ] Fallback strategy defined and justified
- [ ] Original problem statement (WebFetch limitations) addressed

---

## Next Steps

1. Review and refine test URLs (Checkpoint 1)
2. Create test environment and install tools (Task 1-2)
3. Execute validation runs with careful output capture (Task 3)
4. Analyze results and populate comparison matrix (Task 4)
5. Write comprehensive validation report (Task 5)
6. Decision: Proceed with is-fast integration or explore alternatives

---

## Success Metrics for This Validation Itself

This validation plan is successful if:
- All 16 outputs are captured and analyzed
- Completeness and accuracy scores are calculated (not skipped)
- Recommendation is data-driven (backed by scores and evidence)
- Original problem (WebFetch limitations) is clearly addressed in report
- Next steps clear: integrate is-fast or escalate to alternative research
