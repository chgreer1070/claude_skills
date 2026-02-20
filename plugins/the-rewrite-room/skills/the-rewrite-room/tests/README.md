# Test Suite

This directory contains fixtures and expected outputs for validating the-rewrite-room router and workflow contracts.

## Purpose

- Verify the router classifies task descriptions to the correct workflows
- Verify validators produce expected findings for known-bad inputs
- Provide concrete examples for documenting each workflow's behavior

## Fixture Catalog

### stale-docs-after-refactor

Tests the drift-audit workflow.

- `code.py` — module with `process_data(items: list[str]) -> dict`
- `docs.md` — documentation still referencing the old name `process_items`

Expected: drift-audit classifies this as a stale-reference finding with file:line evidence.

### documented-but-unimplemented

Tests the drift-audit workflow for the documented-but-unimplemented pattern.

- `code.py` — `DataProcessor` class with `load()` and `filter()` but no `export_csv()`
- `docs.md` — documents `export_csv(path: str)` as if it exists

Expected: drift-audit finds `export_csv` documented but absent from code.

### implemented-but-undocumented

Tests the drift-audit workflow for the implemented-but-undocumented pattern.

- `code.py` — fully implemented `validate_schema()` and `normalize_keys()` functions
- `docs.md` — generic overview with no mention of either function

Expected: drift-audit finds both functions undocumented.

### invalid-glfm

Tests the formatting-validation workflow for GLFM syntax errors.

- `invalid.md` — invalid alert type, malformed mermaid block, unclosed collapsible

Expected: glfm-validator returns FAIL with evidence of at least one GLFM error.

### negative-prompt-patterns

Tests the prompt-optimization workflow against prohibition-heavy SKILL.md files.

- `prompt.md` — 10 prohibition-only patterns with no positive alternatives

Expected: prompt-optimization converts at least 1 prohibition to a positive directive.

### summarization-sources

Tests the summarization workflow.

- `file-source.md` — 200-line agent orchestration reference document
- `multi-source-manifest.md` — manifest listing 3 sources for multi-source synthesis

Expected: summarization produces output with all 5 required sections and explicit confidence.

## How to Run Each Fixture Manually

### Router classification test

```bash
# Should classify to drift-audit
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/router.py \
  classify "The README is out of sync with the code — process_items was renamed to process_data"

# Should classify to prompt-optimization
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/router.py \
  classify "This SKILL.md uses too many prohibitions, rewrite it for AI comprehension" \
  --artifact SKILL.md

# Should classify to formatting-validation
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/router.py \
  classify "Validate the frontmatter in this agent file"
```

### Link checker test

```bash
# Check a single fixture file
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/link_checker.py \
  check plugins/the-rewrite-room/skills/the-rewrite-room/SKILL.md

# Check all docs in the plugin
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/link_checker.py \
  check-dir plugins/the-rewrite-room/
```

### File metrics test

```bash
# Count tokens in the summarization fixture
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/file_metrics.py \
  count plugins/the-rewrite-room/skills/the-rewrite-room/tests/fixtures/summarization-sources/file-source.md

# Scan all docs in the plugin
uv run plugins/the-rewrite-room/skills/the-rewrite-room/scripts/file_metrics.py \
  scan plugins/the-rewrite-room/
```

## How to Verify Expected Outputs

Each expected output file in `tests/expected/` defines:

- `expected_workflow` — the workflow the router should select
- `expected_chain` — the chain of workflows that should run
- `expected_validators` — validators that must run
- `expected_status` — DONE, BLOCKED, or FAILED
- `required_findings` — findings that must appear in output
- `forbidden_in_output` — phrases that must NOT appear (speculation markers)

After running a workflow against a fixture, compare the actual STATUS block against the expected YAML. All `required_findings` must be present with evidence. All `forbidden_in_output` phrases must be absent.

## How to Add a New Fixture

1. Create a subdirectory under `tests/fixtures/`
2. Add source files that demonstrate the drift/validation/optimization pattern
3. Add an expected output YAML to `tests/expected/` following the existing schema
4. Document the fixture in this README under "Fixture Catalog"
