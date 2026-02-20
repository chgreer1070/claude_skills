---
adapter: summarizer-adapter
wraps: plugins/summarizer/skills/summarizer/SKILL.md
normalizes_to: summary-block-v1
version: "1.0"
---

# summarizer Adapter

## Wrapped Component

`plugins/summarizer/skills/summarizer/SKILL.md`

The summarizer skill produces output with YAML frontmatter (source_type, source_path, method, confidence, word counts) and structured sections (Summary, What Was Found, What Was NOT Found, Uncertain, Sources). The SubagentStop hook validates this output automatically before the session ends.

## Native Output Contract

```yaml
---
source_type: file|url|image|multi-source
source_path: path/or/url
summarized_at: 2026-02-20
method: file-summarization|url-summarization|image-summarization|multi-source-synthesis
word_count_source: N
word_count_summary: N
compression_ratio: 0.NN
confidence: high|medium|low
confidence_notes: [reason if not high]
---
```

With sections: Summary, What Was Found, What Was NOT Found, Uncertain, Sources.

## Adapter Transformation

The adapter maps the native structured output to `summary-block-v1`:

```text
STATUS: DONE|BLOCKED|FAILED
SUMMARY: [extracted from Summary section — first 2 sentences]
ARTIFACTS:
  - path/to/summary-output.md
VALIDATION:
  - fidelity-enforcer: PASS|FAIL
FIDELITY:
  sources_read: N
  sources_inaccessible: N
  confidence: high|medium|low
NOTES: [confidence_notes if confidence is not high]
```

## Fidelity Check Mapping

The adapter reads the native output and checks:

- "What Was NOT Found" section is present and explicitly written (not omitted)
- "Uncertain" section is present and explicitly written (not omitted)
- YAML frontmatter `confidence` field is present
- No vague quantifiers ("many", "several", "some") where counts were available

If any fidelity check fails, `fidelity-enforcer` is set to FAIL and STATUS is FAILED.

## BLOCKED Mapping

The summarizer skill does not produce BLOCKED status in normal operation. If a source is inaccessible, the native output records it in "What Was NOT Found." The adapter preserves this and sets `sources_inaccessible` count in the FIDELITY section.
