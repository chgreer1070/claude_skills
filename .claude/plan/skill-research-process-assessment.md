# Skill Research Process — Completeness Assessment

**Date**: 2026-02-25
**Subject**: `.claude/skills/skill-research-process/`
**Reference**: `plugins/python3-development/skills/uv/` (quality benchmark)

---

## Assessment Question 1: Would invocation produce a `ty` skill matching `uv` quality?

**Verdict: NO — significant gaps prevent equivalent output.**

### Sub-question: Does it know how to read local doc directories as input?

**NO.** The skill has no stage that reads a local directory path argument. The process assumes web-based MCP research (mcp\_\_Ref\_\_, mcp\_\_exa\_\_) as the primary input. The argument-hint is `<tool-or-library-name>` (a name string), not a path. Invoking `/skill-research-process .claude/worktrees/ty/docs/` would be treated as the tool name "`.claude/worktrees/ty/docs/`" — the categorization agent would attempt web searches for that string, not read the local directory.

**What is missing**: A Stage 0 that detects whether the argument is a local path or a tool name, and when it is a path, reads the directory structure and file index before launching the categorization agent.

### Sub-question: Does it produce reference files matching uv skill structure?

**PARTIALLY.** The process produces `references/{category}/index.md` files. The uv skill has named, purpose-specific reference files:

- `cli_reference.md` — complete CLI command reference
- `configuration.md` — all config options and env vars
- `migration-guide.md` — step-by-step migration from competing tools
- `quick-reference.md` — command quick-reference by subcommand
- `troubleshooting.md` — common issues and solutions

The skill-research-process generates category subdirectories with `index.md` files. It has no guidance on which reference file types to produce for a CLI tool, no templates for CLI reference structure, no instruction to produce a migration guide or troubleshooting reference. The output shape is determined entirely by what the categorization agent invents — with no structural anchor.

### Sub-question: Does it produce a sync script for keeping the skill current?

**NO.** The uv skill includes `scripts/sync_uv_releases.py` — a PEP 723 script that queries the GitHub Releases API, identifies new releases, and updates the Version Information section in SKILL.md. The skill-research-process has no stage, instruction, or template for producing a release-tracking sync script. Nothing in the workflow prompts creation of automation to keep the skill current after initial creation.

### Sub-question: Does it follow uv skill structural conventions?

**PARTIALLY.** The skill instructs activation of `/plugin-creator:skill-creator` for structure guidance, which covers frontmatter fields, section ordering, and SKILL.md constraints. However:

- No assets/ directory guidance — uv has `assets/pyproject_templates/`, `assets/docker_examples/`, `assets/github_actions/`, `assets/script_examples/`. skill-research-process never mentions assets.
- No instruction to produce working code examples (templates, config files) as assets.
- The `references/` output uses a category-subdirectory pattern (`references/{category}/index.md`) rather than flat named files (`references/cli_reference.md`). These are structurally different and the category-subdirectory approach requires an extra navigation layer.

---

## Assessment Question 2: Gaps Between skill-research-process and uv-quality Output

| Gap | Severity | Evidence |
|-----|----------|----------|
| No local path input handling | Critical | Argument-hint is tool name, no path detection stage |
| No sync/release-tracking script production | High | uv has `scripts/sync_uv_releases.py`; process has no script creation stage |
| No assets/ directory production | High | uv has 7 asset files in 4 subdirs; process never mentions assets |
| No CLI-tool reference file templates | High | uv has 5 named reference files with specific purposes; process generates open-ended categories |
| Category-subdirectory vs flat reference files | Medium | Adds navigation layer; uv uses flat named files directly under references/ |
| No freshness/version tracking metadata | Medium | Documented in gaps-analysis.md but not fixed |
| Citation enforcement is advisory not structural | Medium | Gates exist but no automated verification |
| Delegation template misalignment | Low | gaps-analysis.md item 5: prompts don't follow agent-orchestration template format |
| No progress tracking for long-running research | Low | gaps-analysis.md item — background agents need status checking |

---

## Assessment Question 3: What Would Need to Be Added or Changed

### 1. Stage 0: Input Detection and Local Directory Reading (Critical)

Add a pre-stage that:

1. Checks whether the argument is a local filesystem path (starts with `./`, `/`, `~`, or contains `/`)
2. If local path: reads the directory structure, lists all documentation files, extracts titles and headings, and passes this index to the categorization agent as primary source material
3. If tool name: proceeds with current web-based research flow

This stage should use `Glob` and `Read` tools — no MCP required. The categorization agent prompt template in `references/agent-prompts.md` needs a local-path variant.

### 2. Reference File Type Templates for CLI Tools (High)

Add a reference file `references/cli-tool-reference-templates.md` that defines the standard named reference files to produce for a CLI tool skill:

- `cli_reference.md` — command/subcommand/flag reference
- `configuration.md` — config file options, environment variables
- `migration-guide.md` — migration from competing tools (with command mapping tables)
- `quick-reference.md` — scannable cheat sheet by use case
- `troubleshooting.md` — common errors and solutions

The categorization agent should be instructed to map its categories to these standard file types when the subject is a CLI tool, rather than inventing arbitrary category names.

### 3. Sync Script Production Stage (High)

Add a Stage 4 (Post-Integration) that instructs production of a `scripts/sync_{tool-name}_releases.py` script using the PEP 723 + uv pattern. The script should:

- Query the tool's GitHub Releases API
- Identify releases newer than the last recorded version in SKILL.md
- Update the Version Information section with new entries

The `references/agent-prompts.md` needs a sync-script agent prompt that delegates to `@python3-development:python-cli-architect` with the uv sync script as a structural reference (path, not transcription).

### 4. Assets Directory Production (High)

Stage 3 (Integration) should include an assets step:

- Identify reusable templates produced during research (config files, workflow files, Dockerfiles, pyproject.toml examples)
- Write these as files in `assets/{category}/` rather than embedding them inline in reference markdown
- Update SKILL.md Resources section to list assets directories

### 5. Flatten Reference Output Structure (Medium)

Change the research agent output from `references/{category}/index.md` to `references/{category-slug}.md`. This matches the uv skill's flat structure and avoids the extra navigation indirection. Update Stage 2 and Stage 3 accordingly.

### 6. Automated Citation Verification (Medium)

Quality Gate 2 (Anti-Hallucination Checkpoint) is currently a manual checklist. Add a script or structured output requirement:

- Research agents must produce a `citations.json` alongside each reference file
- Gate 2 validation reads `citations.json` files and reports any reference file with zero citations
- This makes citation enforcement structural rather than advisory

---

## Summary

**skill-research-process** is a solid research orchestration framework — its parallel agent pattern, quality gates, and citation requirements are well-designed. It would produce *some* output for a `ty` skill, but that output would be structurally different from the uv skill and missing key components.

**The three most impactful gaps to close:**

1. **Local directory input** — without this, `/skill-research-process .claude/worktrees/ty/docs/` cannot work as intended
2. **CLI reference file templates** — without these, the output has arbitrary category names instead of the named reference files that make the uv skill navigable
3. **Sync script production** — without this, the produced skill has no mechanism to stay current as `ty` releases new versions

The `references/gaps-analysis.md` file already documents several of these gaps (verification, citation enforcement, freshness tracking). This assessment confirms those and adds the local-path input handling, assets production, and sync script gaps as additional critical items not previously captured.
