# Tasks: refresh-research --layer filtering logic

<!-- Fixes #248 -->

**Backlog item**: refresh-research: Implement --layer filtering logic
**Priority**: P2
**Issue**: #248

## Summary

The `--layer` flag is documented in `.claude/skills/refresh-research/SKILL.md` (lines 18, 45) but the workflow instructions don't actually implement the filtering. Step 1 parses only the Freshness Tracking section — it never extracts `layer` metadata from entry frontmatter. Step 2 lists `--layer` as a filter option but has no data to filter on.

**Fix**: Update Step 1 to extract `layer` metadata from each entry's YAML frontmatter alongside staleness data. Update Step 2 with explicit filtering logic. Update the inventory table, summary report, and argument-hint to include layer.

## Architecture

**Files modified**: 1 file — `.claude/skills/refresh-research/SKILL.md`
**No Python changes**: `knowledge-explorer.py` already supports `--layer` in its `list` command (line 1429). The refresh-research skill is an AI-read SKILL.md, not a script. All changes are instruction updates.

## Tasks

- [x] 1. Update frontmatter `argument-hint` to include `--layer`
- [x] 2. Update Step 1 to extract `layer` metadata from entry frontmatter
- [x] 3. Add `Layer` column to the inventory table in Step 1
- [x] 4. Update Step 2 with explicit `--layer` filtering logic and AND-combination with other filters
- [x] 5. Update Step 6 summary report `**Scope**` line to include `--layer` option
- [x] 6. Add error handling for `--layer` with no matching entries
- [x] 7. Lint the modified SKILL.md with `uv run prek run --files`
- [x] 8. Verify: read modified SKILL.md and confirm all 7 acceptance criteria are satisfied

## Acceptance Criteria

1. `/refresh-research --layer 0` processes only entries with `metadata.layer: "0"`
2. `/refresh-research --layer 1` processes only entries with `metadata.layer: "1"`
3. `/refresh-research --layer 2` processes only entries with `metadata.layer: "2"`
4. Entries without `layer` metadata are skipped when `--layer` is specified
5. Report shows filtered count
6. `--dry-run --layer 1` displays target list without spawning agents
7. `--layer` and `--category` can be combined (AND logic)
