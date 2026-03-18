---
description: Write source-attributed content from URLs or content blocks. Fetches sources, cross-references claims, and produces content with hyperlinked citations. Pass the source URL and content context.
argument-hint: '<source URL> [key points to emphasize] [content type: blog|research|social|brief]'
agent: rewrite-room-cite
allowed-tools: Read, Write, Edit, Grep, Glob, WebFetch, WebSearch
---

Route this citation and attribution task to the rewrite-room-cite agent.

Task: $ARGUMENTS

The agent will fetch the source, cross-reference claims, and produce attributed content with the structured output format (executive summary, deep dive, key takeaways, cited from).
