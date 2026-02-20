# Multi-Source Summarization Manifest

This manifest lists 3 source files for multi-source summarization testing.

## Sources

1. **Agent Orchestration Reference**
   - Path: `plugins/the-rewrite-room/skills/the-rewrite-room/tests/fixtures/summarization-sources/file-source.md`
   - Type: file
   - Focus: Core orchestration principles, anti-patterns, quality gates

2. **Global CLAUDE.md Summarization Rules**
   - Path: `~/.claude/CLAUDE.md` (Summarization Rules section)
   - Type: file (section extract)
   - Focus: Summarization decision flow, 5000-char threshold, tool selection

3. **Fidelity Rules**
   - Path: `plugins/the-rewrite-room/skills/the-rewrite-room/references/fidelity-rules.md`
   - Type: file
   - Focus: 7 rules for summarization fidelity enforcement

## Synthesis Goal

Produce a consolidated reference covering:

- When to summarize vs. delegate
- What fidelity rules apply to all summaries
- How multi-source synthesis differs from single-source summarization
- What validators run on summarization output

## Expected Output Format

Use the `structured` template with all 5 required sections:

- Summary
- What Was Found
- What Was NOT Found
- Uncertain
- Sources
