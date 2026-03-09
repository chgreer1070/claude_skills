---
name: 'RTFP: Read The Fucking Prompt — Claude Code plugin for session reaction mining'
description: "Plugin that scans Claude Code session transcripts to find the strongest user reactions to instruction-following failures, reconstructs the assistant output that triggered them, and turns the best exchange into a shareable terminal-style PNG artifact.\n\n## Constraints\n\n- Session data stored in JSONL files on disk (storage layer)\n- DuckDB is the query layer for inspecting session data\n- First-pass batch files contain ONLY user-authored messages (no assistant, tool, system, or developer messages)\n- Each batched entry preserves: source session file path + original message index id\n\n## Workflow\n\n### Session selection\nAssistant finds and presents recent sessions from the current project with titles. User selects one.\n\n### Stage 1: User-only extraction and batching\n- Read selected session JSONL\n- Filter to user-authored messages only — exclude everything else\n- Create temporary batch files ~100k tokens each (user messages only)\n- Purpose: emotional-reply detection only, NOT contextual reconstruction\n\n### Stage 2: Subagent detection over user-only batch files\n- For each batch file, start a subagent\n- Subagent identifies messages with strong emotional reactions: frustration, disappointment, disbelief, argument, insults, other clearly negative emotional responses aimed at the assistant\n- Each subagent returns: (1) JSON file with flagged message indexes grouped by source file, (2) plain list of flagged entries\n- Parent assistant merges returned index ids per file into a single working set\n\n### Stage 3: Context reconstruction after candidate selection\n- Given merged flagged indexes, select: (1) single most emotional/rage-filled response, (2) runner-up if present\n- ONLY at this stage go back to the full session transcript\n- Retrieve each flagged user message from full session\n- Inspect nearby transcript entries\n- Determine current activity/task\n- Identify assistant message(s) that triggered the reaction\n\n### Output artifact\nThree elements only:\n1. Short dry task summary (e.g. 'task: writing a Claude Code plugin') — scene-setting only, not diagnosis\n2. Assistant output that triggered the reaction\n3. User's emotional reply\n\nRendered as PNG with terminal interface aesthetic, ready for social media.\n\n## Anti-requirements\n- NOT a generic analytics tool\n- NO broad taxonomy\n- NO scoring\n- NO verdicts\n- NO extra evaluative layers\n\n## Key constraint sentence\n'The first-pass temporary batch files must contain only user-authored messages, because they are for emotional-reply detection only; full transcript context must be retrieved later during reconstruction.'"
metadata:
  topic: rtfp-read-the-fucking-prompt-claude-code-plugin-for-session-
  source: User request
  added: '2026-03-09'
  priority: P1
  type: Feature
  status: open
  issue: '#555'
  last_synced: '2026-03-09T03:38:24Z'
  groomed: '2026-03-09'
---

## Fact-Check

**Date**: 2026-03-09
**Claims checked**: 3

| Verdict | Count |
|---------|-------|
| VERIFIED | 2 |
| REFUTED | 1 |
| INCONCLUSIVE | 0 |

### Claim 1: Claude Code stores sessions as JSONL files at `~/.claude/projects/<encoded-project-path>/*.jsonl`
**Verdict**: VERIFIED
**Source**: Claude Code official documentation
**Evidence**: Confirmed session storage format and path structure via primary source lookup.
**Citation**: Anthropic Claude Code documentation (accessed 2026-03-09)

### Claim 2: DuckDB can query JSONL directly via `read_ndjson()` or `read_json_auto()` without prior import
**Verdict**: VERIFIED
**Source**: DuckDB JSON extension documentation
**Evidence**: `read_ndjson()` and `read_json_auto()` are built-in DuckDB functions for inline NDJSON querying.
**Citation**: DuckDB JSON documentation (accessed 2026-03-09)

### Claim 3: tiktoken `cl100k_base` encoding is the recommended approximation for Claude token counting
**Verdict**: REFUTED
**Source**: Anthropic documentation and Propel 2025 guide
**Evidence**: `p50k_base` is the recommended tiktoken encoding for offline Claude token approximation. `cl100k_base` is the GPT-4 encoding. **Fix applied**: Both `extract_batches.py` and `bucket_day_data.py` updated to use `p50k_base`.
**Citation**: Anthropic docs + Propel 2025 guide (accessed 2026-03-09)

## RT-ICA

**Goal**: Build a skill/plugin that mines Claude Code session transcripts to surface the strongest user emotional reactions to assistant instruction-following failures, and renders the best exchange as a terminal-style PNG artifact.

**Conditions**:

1. Session JSONL format is known and accessible | Status: AVAILABLE | Info: VERIFIED — `~/.claude/projects/<encoded>/*.jsonl`, one JSON object per line
2. Token counting uses `p50k_base` tiktoken encoding | Status: AVAILABLE | Info: VERIFIED — cl100k_base REFUTED; p50k_base corrected in both scripts
3. DuckDB JSONL query capability | Status: AVAILABLE | Info: VERIFIED — `read_ndjson()` and `read_json_auto()` confirmed
4. Stage 1 user-only batch file schema | Status: AVAILABLE | Info: Defined and implemented in `extract_batches.py`
5. Stage 2 heuristic emotional detection (no LLM) | Status: AVAILABLE | Info: Implemented in `detect_reactions.py` — profanity, negative phrases, ALL CAPS, punctuation density, short message bursts
6. Stage 3 context reconstruction (triggering assistant output) | Status: DERIVABLE | Info: `reconstruct_context.py` agent was running at grooming time; logic: walk backward in JSONL from flagged user message to find preceding assistant message
7. Stage 4 terminal-style PNG rendering | Status: AVAILABLE | Info: `render_artifact.py` implemented with Pillow; S108/F401 bugs fixed
8. End-to-end orchestrating skill | Status: MISSING | Info: No skill or script ties all 4 stages together; `rtfp/SKILL.md` needs update to reflect corrected stage definitions
9. DuckDB integration in pipeline | Status: MISSING | Info: Spec calls for DuckDB as query layer; no script currently uses it — all scripts use direct Python JSONL parsing
10. Plugin structure (vs. skill/scripts) | Status: MISSING | Info: Currently implemented as skills/scripts for immediate testability; migration to `rtfp/` plugin dir is planned (user message 2026-03-09)
11. PNG design matches Claude Code terminal aesthetic | Status: DERIVABLE | Info: Claude.com/product/claude-code design elements available; current `render_artifact.py` uses basic Pillow — may need redesign

**Decision**: BLOCKED

**Missing**:
- End-to-end orchestrating skill/script
- DuckDB integration as query layer
- Plugin structure migration (skills → plugin)
- Terminal-style PNG design fidelity to Claude Code aesthetic

## Groomed (2026-03-09)

### Issue Classification

**Type**: `unbounded-design`

**Rationale**: RTFP is a net-new feature with no prior implementation to debug or recover. The scope boundary (what counts as an "emotional reaction", what constitutes the "best" exchange, PNG fidelity target) requires design decisions rather than root-cause analysis.

**scenario-target**: A user who has been ignoring their own CLAUDE.md instructions discovers the RTFP skill produces a social-media-ready PNG capturing their most visceral frustration — surfaced automatically from session history without manual search.

**Analysis Method**: design-framing — define the minimal MVP boundary, identify the observable acceptance criteria for each stage, and defer aesthetic/scoring decisions to iteration.

**No RCA required** (not a defect or recurring pattern).