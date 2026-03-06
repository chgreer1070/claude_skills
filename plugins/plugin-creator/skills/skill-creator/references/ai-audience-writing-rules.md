# AI-Audience Writing Rules for Reference Files

Skills and reference files are AI-only artifacts. The audience is Claude reading text via the `Read` tool — not a human reading rendered markdown in a browser.

## NEVER: Table of Contents

Do not add a Table of Contents to any reference file. Claude navigates by line offset (`Read(file, offset=N, limit=M)`), not by anchor fragments. A ToC consumes tokens and provides zero navigational benefit to the Read tool.

## NEVER: Anchor Links

Do not add anchor links (`[text](#heading-anchor)`). They are non-functional for AI consumers. The Read tool returns line-numbered content — there is no anchor resolution. Anchor fragment bugs (mismatched slugs, special characters in headings, subsection vs section depth) cannot be discovered until a human renders the file, by which point multiple orchestrator turns have been wasted debugging them.

## NEVER: Emphasis for Visual Effect

Do not use bold or italic for visual emphasis only. `**Bold**` and `*italic*` add no signal for AI consumption — they cost tokens without conveying additional meaning. Use emphasis only when it encodes semantics (e.g., MUST, NEVER as modal qualifiers).

## Write Dense, Direct Prose

Every sentence must carry information. Avoid:

- Decorative horizontal rules as section dividers
- Nested bullets that could be a single sentence
- Repeated headers that restate the parent heading
- Background context the reader already has

The test: if a sentence were deleted, would the reader lose information? If no — delete it.

## Why These Rules Exist

Broken anchor fragments in AI-facing reference files are a recurring failure pattern. An orchestrator that adds a ToC with anchor links will spend multiple turns debugging mismatched slugs — a Grep to find the actual heading text, an Edit to correct the anchor, a re-read to verify, repeated for each broken entry. NEVER add human-navigation constructs to AI-facing files. Delegate body content to `contextual-ai-documentation-optimizer`, which enforces these rules by design.
