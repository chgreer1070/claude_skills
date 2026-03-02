---
name: 'refresh-research: Implement --layer filtering logic'
description: 'The `--layer` flag is documented in refresh-research but filtering logic is not implemented. When `--layer 0`, `--layer 1`, or `--layer 2` is passed, only research entries with matching layer metadata should be refreshed. Success: `/refresh-research --layer 1` processes only Layer 1 entries. Depends on research entries having `layer` metadata (already added).'
metadata:
  topic: refresh-research-implement-layer-filtering-logic
  source: Session observation — SDLC layer implementation (2026-02-23)
  added: '2026-02-23'
  priority: P2
  type: Feature
  status: open
  issue: '#248'
  groomed: '2026-02-28'
  last_synced: '2026-02-28T17:40:45Z'
  plan: plan/tasks-9-refresh-research-layer-filtering.md
---

## Story

As a **developer**, I want **The `--layer` flag is documented in refresh-research but filtering logic is n...** so that **backlog items are tracked in GitHub**.

## Description

The `--layer` flag is documented in refresh-research but filtering logic is not implemented. When `--layer 0`, `--layer 1`, or `--layer 2` is passed, only research entries with matching layer metadata should be refreshed. Success: `/refresh-research --layer 1` processes only Layer 1 entries. Depends on research entries having `layer` metadata (already added).

## Acceptance Criteria

- [ ] Work matches description
- [ ] Plan or implementation complete

## Context

- **Source**: Session observation — SDLC layer implementation (2026-02-23)
- **Priority**: P2
- **Added**: 2026-02-23
- **Research questions**: None

**Suggested location**: `.claude/skills/refresh-research/SKILL.md` and `knowledge-explorer.py`

## Fact-Check

Claims checked: 3
VERIFIED: 2 | REFUTED: 0 | INCONCLUSIVE: 1

1. VERIFIED: --layer flag is documented in refresh-research SKILL.md
   Evidence: Lines 18, 45 of .claude/skills/refresh-research/SKILL.md
   Citation: Direct file read (2026-02-28)

2. VERIFIED: Filtering logic is not implemented in refresh-research workflow
   Evidence: Step 1 of SKILL.md parses only Freshness Tracking section, does not extract layer metadata from entry frontmatter. Step 2 mentions --layer filter but Step 1 provides no layer data to filter on. The instruction is inoperable as written.
   Citation: Direct file read (2026-02-28)

3. INCONCLUSIVE: Research entries having layer metadata (already added)
   Evidence: Only 3 of ~50+ entries have layer metadata: harness-engineering-openai.md (layer 0), tornado.md (layer 2), fastapi.md (layer 2), copier-astral.md (layer 1). Most entries lack layer metadata. knowledge-explorer.py list --layer 1 returns only 1 entry.
   Citation: grep layer:.*[012] research/ + uv run knowledge-explorer.py list --layer 1 (2026-02-28)

## RT-ICA

Goal: Implement --layer filtering in refresh-research so /refresh-research --layer N processes only research entries with matching SDLC layer metadata.

Conditions:
1. refresh-research SKILL.md exists with --layer documentation | AVAILABLE | Lines 18, 45
2. knowledge-explorer.py list command supports --layer filtering | AVAILABLE | Line 1429, tested working
3. Research entries have layer metadata in frontmatter | DERIVABLE | Only 3-4 entries have it; most need it added but the filtering logic works regardless
4. Step 1 of SKILL.md needs to extract layer metadata from entries | MISSING (this is the work)
5. Step 2 of SKILL.md needs explicit filtering logic using layer data | MISSING (this is the work)
6. knowledge-explorer.py list --layer can be leveraged instead of manual parsing | AVAILABLE | Tested (2026-02-28)

Decision: APPROVED
Missing: Items 4 and 5 are the implementation work itself, not external blockers. All prerequisites are available.

## Groomed (2026-02-28)

### Priority

7/10 — Enables targeted research refresh by SDLC layer; unblocks planned knowledge-base restructuring work. Currently documented but inoperable. Medium complexity (layer metadata already in parser, just need to thread it through workflow).

### Impact

- Blocks: Knowledge-base layer-based operations and documentation of layer-scoped research audits
- Bottleneck: --layer flag advertised in SKILL.md but non-functional; workflow relies on stale-detection only

### Benefits

- Layer-specific research refreshes become functional (e.g., refresh only Layer 1 entries)
- Enables knowledge-base audits scoped to process, language, or stack layers
- Unblocks downstream SDLC documentation that depends on per-layer research coverage

### Expected Behavior

When invoking `/refresh-research --layer 1`, only research entries with `metadata.layer: "1"` in frontmatter are processed. Other entries are skipped. If no entries match the layer filter, report "No entries found for layer X" and stop.

### Desired Structure

**Step 1 (Inventory and Staleness Detection)**: Extract `layer` metadata field from each entry frontmatter (in addition to category, version, and freshness dates). Build inventory table with columns: `| File | Category | Layer | Last Verified | Next Review | Stale? |`

**Step 2 (Apply Scope Filter)**: When `--layer` is passed, filter inventory to entries where `entry.layer == requested_layer`. Preserve existing logic for `--all`, `--stale`, `--category`, and `--dry-run`.

### Acceptance Criteria

1. `/refresh-research --layer 0` processes only entries with `metadata.layer: "0"`
2. `/refresh-research --layer 1` processes only entries with `metadata.layer: "1"`
3. `/refresh-research --layer 2` processes only entries with `metadata.layer: "2"`
4. Entries without `layer` metadata are skipped when `--layer` is specified
5. Report shows filtered count: e.g., "Targeted: 8 / 47 scanned (skipped 39 without layer metadata)"
6. `--dry-run --layer 1` displays target list without spawning agents
7. Multiple scope flags (`--layer` and `--category`) can be combined; both filters apply (AND logic)

### Resources

| Type | Item |
|------|------|
| Skill | /refresh-research |
| Skill | /knowledge-explorer |
| Prior work | research/knowledge-explorer.py (list command, lines 1429-1439, working --layer implementation) |
| Reference | .claude/docs/sdlc-layers/ |

### Dependencies

- Depends on: None — layer metadata already present in entry frontmatter (SDLC layer implementation complete)
- Blocks: Research curation workflows requiring layer-scoped updates; knowledge-base audits by layer

### Blockers

None — RT-ICA APPROVED. All prerequisites available:
- SKILL.md has --layer documented (lines 18, 45)
- knowledge-explorer.py demonstrates working --layer filter (line 1429-1439)
- Entry frontmatter supports layer metadata (dataclass at line 267)

### Effort

Small — Extend existing staleness detection logic in Step 1 to extract layer field (1 line of code); add conditional filter in Step 2 (2-3 lines). Reference implementation exists in knowledge-explorer.py list command (proven pattern).