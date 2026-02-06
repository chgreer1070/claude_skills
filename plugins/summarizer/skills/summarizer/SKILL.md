---
description: Summarization decision tree and fidelity methodology. Activates when summarizing files, URLs, images, or multi-source content. Routes to the correct summarization approach based on source type. Enforces anti-hallucination rules — read before summarizing, extract before abstracting, preserve counts, distinguish absence from nonexistence, prevent lossy re-summarization chains.
---
# Summarizer

Route to the correct summarization methodology and enforce fidelity rules across all summarization operations.

## Decision Tree

When the model needs to summarize content, follow this decision tree to select the correct approach:

```text
INPUT RECEIVED
  │
  ├─ Is it a FILE path?
  │   ├─ Yes → Load file-summarization skill
  │   │         Run file-metrics.py to assess size
  │   │         Select strategy based on size thresholds
  │   └─ No ↓
  │
  ├─ Is it a URL?
  │   ├─ Yes → Load url-summarization skill
  │   │         Fetch content first, then summarize
  │   └─ No ↓
  │
  ├─ Is it an IMAGE (path to .png, .jpg, .gif, .svg, .webp, screenshot)?
  │   ├─ Yes → Load image-summarization skill
  │   │         Read image with Read tool (multimodal)
  │   └─ No ↓
  │
  ├─ Is it MULTIPLE sources (list of files, URLs, or mixed)?
  │   ├─ Yes → Summarize each source individually first
  │   │         Then load multi-source-synthesis skill
  │   │         Combine with deduplication and attribution
  │   └─ No ↓
  │
  └─ Is it INLINE TEXT (pasted content, agent output, conversation excerpt)?
      └─ Yes → Apply fidelity rules directly
               Use extractive method: identify key passages first
               Produce structured output
```

## Delegation Decision

When the summarization task is autonomous (user asks to summarize something and move on), delegate to a specialized agent:

| Source Type | Agent | When to Use |
|-------------|-------|-------------|
| File(s) | @file-summarizer | Summarizing files without immediate follow-up questions |
| URL(s) | @url-summarizer | Summarizing web content autonomously |
| Image(s) | @image-summarizer | Describing visual content autonomously |

When the summarization is part of the current conversation flow (user wants to discuss the content), apply the relevant skill methodology directly rather than delegating.

## Fidelity Rules (Mandatory)

These rules apply to ALL summarization regardless of source type. See [Fidelity Rules](./references/fidelity-rules.md) for full details.

**Rule 1: Read Before Summarizing** - Read actual content. Never guess from filenames or paths.

**Rule 2: Extract Before Abstracting** - Pull quotes/passages first, then summarize from extracts.

**Rule 3: Preserve Counts and Specifics** - Keep exact numbers. "7 of 10" not "most."

**Rule 4: Distinguish Absence from Nonexistence** - "Not mentioned in source" not "doesn't exist."

**Rule 5: No Lossy Re-Summarization** - When relaying agent results, relay counts and references. Do not summarize the summary.

**Rule 6: State Confidence Explicitly** - Every summary includes confidence level with rationale.

**Rule 7: Structured Output Always** - Use the format defined in [Output Format](./references/output-format.md).

## Output Format

All summaries MUST use structured markdown with YAML frontmatter. See [Output Format](./references/output-format.md) for the complete specification.

Required sections in every summary:

1. **YAML frontmatter** - source_type, source_path, method, confidence, word counts
2. **Summary** - the condensed content (BLUF style)
3. **What Was Found** - items discovered with source references
4. **What Was NOT Found** - items searched for but absent
5. **Uncertain** - ambiguous items requiring interpretation
6. **Sources** - full attribution with access dates

## Anti-Patterns

The model MUST NOT:

- Summarize a file based on its name without reading it
- Summarize a URL based on its domain without fetching it
- Describe an image based on its filename without viewing it
- Re-summarize a sub-agent's summary (relay instead)
- Upgrade "not found" to "doesn't exist"
- Drop counts ("7 of 10" → "most")
- Omit the "What Was NOT Found" section
- Present uncertain information as definitive
- Summarize from excerpts (head/tail/grep) without disclosing the limitation
