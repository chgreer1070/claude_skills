# Structured Summary Output Format

All summarization output from this plugin MUST use this format. The format serves two purposes: (1) preserving fidelity by forcing explicit categorization of findings, and (2) providing machine-parseable metadata for downstream consumers.

## YAML Frontmatter

```yaml
---
source_type: file | url | image | multi-source
source_path: "<exact path, URL, or list of sources>"
summarized_at: "<ISO 8601 timestamp>"
method: extractive | abstractive | hybrid
word_count_source: <integer or null if not applicable>
word_count_summary: <integer>
compression_ratio: <float or null>
confidence: high | medium | low
confidence_notes: "<why this confidence level>"
---
```

### Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| `source_type` | Yes | What kind of source was summarized |
| `source_path` | Yes | Exact path or URL. For multi-source, use YAML list |
| `summarized_at` | Yes | When the summary was generated |
| `method` | Yes | `extractive` = selected passages from source. `abstractive` = new text generated from source. `hybrid` = combination |
| `word_count_source` | Yes | Word count of original. `null` for images or inaccessible sources |
| `word_count_summary` | Yes | Word count of the summary section |
| `compression_ratio` | No | `word_count_summary / word_count_source`. Omit for images |
| `confidence` | Yes | Overall confidence in summary accuracy |
| `confidence_notes` | Yes | Explanation of confidence level |

### Confidence Level Criteria

| Level | Criteria |
|-------|----------|
| `high` | Full source was read. Content is factual/structured. No ambiguity in interpretation |
| `medium` | Source partially accessible, or content requires interpretation, or source is dated |
| `low` | Source inaccessible/truncated, content ambiguous, conflicting information present |

## Markdown Body Sections

The body MUST contain these sections in this order:

### 1. Summary

The actual condensed content. Rules:

- Lead with the most important information (BLUF - Bottom Line Up Front)
- Use the source's own terminology
- Attribute claims to their source location when the source has multiple sections
- Do NOT add information not present in the source
- Do NOT interpret ambiguous content as definitive

### 2. What Was Found

Bulleted list of key items discovered in the source, each with a source reference:

```markdown
## What Was Found

- REST API uses JWT authentication (source: Section 3.2, lines 45-67)
- Rate limiting set to 100 req/min per API key (source: Section 5.1, line 112)
- Deprecation notice for v1 endpoints effective 2025-06-01 (source: Header banner)
```

### 3. What Was NOT Found

Items that were searched for or expected but absent from the source:

```markdown
## What Was NOT Found

- No mention of WebSocket support in the API documentation
- No pricing information found on the page
- Authentication section references "SSO guide" but no link was accessible
```

CRITICAL RULE: "Not found in source" is NOT the same as "does not exist." The model MUST use language that distinguishes between these:

| Correct | Incorrect |
|---------|-----------|
| "The document does not mention X" | "X is not supported" |
| "No information about X was found in this source" | "X doesn't exist" |
| "Unable to determine X from this source" | "X is not possible" |
| "X was not present in the sections examined" | "There is no X" |

### 4. Uncertain

Items where the source was ambiguous or the summarizer's interpretation may not be accurate:

```markdown
## Uncertain

- The "enterprise tier" section mentions "custom limits" but does not specify values
- Diagram on page 3 appears to show a microservices architecture, but labels are partially obscured
```

### 5. Sources

Full attribution with access dates:

```markdown
## Sources

- API Documentation v2.3, https://example.com/docs/api (accessed 2026-02-06)
- Architecture diagram, ./docs/architecture.png (read from local file)
```

## Size-Based Strategy Selection

The summarization approach varies based on source size:

| Source Size | Strategy | Detail Level |
|------------|----------|-------------|
| Small (< 2,000 words) | Present key facts directly, minimal compression | High - preserve most content |
| Medium (2,000 - 10,000 words) | Extract key sections, group by theme | Medium - capture themes and specifics |
| Large (> 10,000 words) | Map-reduce: chunk, summarize each, synthesize | Lower per-section, comprehensive overall |

SOURCE: Size thresholds adapted from Anthropic knowledge-synthesis skill (knowledge-work-plugins repository, accessed 2026-02-06). Strategy patterns informed by Map-Reduce Summarization methodology.
