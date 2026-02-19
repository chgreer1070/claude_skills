---
description: Summarize web content by fetching URLs, extracting key passages with quote-grounding, and producing structured output. Activates on summarize this URL, what does this page say, summarize this article, read and summarize, summarize the documentation at, tl;dr this link, give me the highlights of this page, what's important on this site. Routes to fetching strategy based on content type — documentation, articles, API references, READMEs. Reports partial accessibility explicitly.
---

# URL Summarization

Apply this methodology when summarizing web content from URLs.

## When to Activate

The model MUST use this skill when:

- User provides a URL and asks for a summary
- User says "summarize this article/page/documentation"
- User asks "what does this page say"
- User requests "read and summarize [URL]"
- Task requires extracting information from web-accessible content

## Fetching Methodology

The model MUST follow this decision tree for fetching URL content:

```text
URL PROVIDED
  │
  ├─ Is it docs.anthropic.com or code.claude.com?
  │   ├─ Yes → Append .md to path
  │   │         Example: /docs/guide → /docs/guide.md
  │   │         Use mcp__Ref__ref_read_url
  │   └─ No ↓
  │
  ├─ Is it documentation (docs subdomain, /docs/, /api/, /reference/)?
  │   ├─ Yes → Use mcp__Ref__ref_read_url
  │   │         Tool optimized for documentation sites
  │   └─ No ↓
  │
  ├─ Is it a generic web page?
  │   └─ Yes → Use WebFetch
  │             Fall back if mcp__Ref fails
```

### Error Handling

When fetching fails, the model MUST report explicitly:

```text
Unable to access [URL]: [error details]
Reason: [HTTP 404 | timeout | SSL error | authentication required | etc.]
```

The model MUST NOT:

- Guess content from the URL path or domain
- Summarize based on the page title alone
- Assume content based on site reputation
- Fabricate information when source is inaccessible

### Partial Accessibility

When only some sections of a page load:

```markdown
## What Was Found

Content extracted from sections: Introduction, API Reference, Authentication
Total sections accessible: 3 of 7

## What Was NOT Found

Unable to access sections: Rate Limits, Error Codes, Webhooks, Changelog
Reason: Pagination links did not resolve, or content blocked by JavaScript
```

## Content Type Strategies

Adapt summarization approach based on web content type:

| Content Type | Extract | Emphasis |
|--------------|---------|----------|
| **Documentation** | API structure, authentication, rate limits, key concepts, version info | Technical accuracy, preserve parameter details, note external references |
| **Articles/Blogs** | Thesis, supporting points, evidence, conclusions, publication date | Logical flow, distinguish opinion from facts, note if dated |
| **API Reference** | Base URL, auth method, endpoints/methods, request/response formats, rate limits, error codes | Machine-parseable structure, exact paths, required vs optional parameters |
| **GitHub README** | Purpose, installation, usage examples, dependencies, license | Actionable setup steps, stable vs experimental features |
| **Generic Pages** | Visible text, headings, significant quotes | Report low confidence, note navigation vs content density |

## Quote-Grounding Technique

The model MUST use this two-phase approach for text-heavy sources.

### Phase 1: Extract Key Passages

Before writing any summary, extract relevant quotes:

```markdown
EXTRACTED PASSAGES:

1. "The API uses JWT tokens for authentication. Tokens expire after 24 hours."
   (Source: Section 2.1, Authentication)

2. "Rate limit is 100 requests per minute per API key. Burst allowance: 150 req/min for 10 seconds."
   (Source: Section 4.3, Rate Limiting)

3. "Webhooks are not currently supported. Feature planned for Q2 2026."
   (Source: Roadmap section, footer)
```

### Phase 2: Summarize from Extracts

Write the summary by organizing and condensing the extracted passages. Every claim in the summary MUST trace back to an extract.

If a claim cannot be traced to an extract, it is potentially hallucinated and MUST be removed or verified against the source.

SOURCE: Grounding technique from Anthropic prompt engineering documentation (<https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips>, accessed 2026-02-06).

## Structured Output

The model MUST use the format defined in [Structured Summary](../summarizer/templates/structured.md).

Required components:

1. YAML frontmatter with source_type: url
2. Summary section (BLUF style)
3. What Was Found section (with source references)
4. What Was NOT Found section (distinguish absence from nonexistence)
5. Uncertain section (ambiguous content)
6. Sources section (full URL with access date)

## Fidelity Rules

The model MUST follow all rules in [Fidelity Rules](../summarizer/references/fidelity-rules.md):

- Read before summarizing (fetch the URL, do not guess)
- Extract before abstracting (quote-grounding technique)
- Preserve counts and specifics (exact numbers, not "many" or "several")
- Distinguish absence from nonexistence ("not mentioned" vs "doesn't exist")
- No lossy re-summarization (relay agent results with counts intact)
- State confidence explicitly (with rationale in YAML frontmatter)
- Structured output always (use all sections, write "None" if empty)

## Output Rendering

1. **Read template** - Load the template file at `../summarizer/templates/{format_id}.md` (default: `structured`). The template defines the schema, required sections, and fidelity constraints for the selected format.
2. **Render** - Produce output following the template's Schema section. Use the template's Example as a reference for structure and style.
3. **Verify fidelity** - Confirm the output satisfies the template's Fidelity Constraints and all applicable [Fidelity Rules](../summarizer/references/fidelity-rules.md).

## Anti-Patterns

The model MUST NOT:

- Summarize a URL without fetching it
- Guess content from domain name or path segments
- Describe content based on page title alone
- Drop exact numbers in favor of vague quantifiers
- Upgrade "not found on this page" to "feature doesn't exist"
- Omit the "What Was NOT Found" section
- Present low-confidence interpretations as definitive facts
- Re-summarize another agent's URL summary (relay instead)

## Example Output

See [Structured Summary](../summarizer/templates/structured.md) for complete specification. Brief example:

```yaml
---
source_type: url
source_path: "https://example.com/docs/api-v2"
method: hybrid
confidence: high
confidence_notes: "Full page accessible, structured technical reference"
---
```

Summary leads with most important information. What Was Found lists discoveries with source references. What Was NOT Found distinguishes absence from nonexistence. Uncertain section captures ambiguous content. Sources section includes full URL with access date.
