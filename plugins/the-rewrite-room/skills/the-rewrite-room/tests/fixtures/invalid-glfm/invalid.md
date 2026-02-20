# Invalid GLFM Fixture

This file contains GLFM-specific syntax that is invalid or non-standard.

## Invalid Alert Block

GitLab Flavored Markdown uses `> [!NOTE]` alert syntax. The following uses an unsupported alert type:

> [!CAUTION_EXTENDED]
> This alert type does not exist in GLFM. Only NOTE, TIP, IMPORTANT, WARNING, and CAUTION are valid.

## Invalid Table Alignment

The following table uses `:-:` (center-align) which is valid in standard Markdown, but tests
GFM/GLFM rendering compatibility across renderers:

| Left | :-: Center :-: | Right |
|------|:--------------:|------:|
| a    | b              | c     |

## Malformed Mermaid Block

The following mermaid diagram has a syntax error (missing arrow type):

```mermaid
flowchart TD
    A B
    B C
```

## Invalid Collapsible

GitLab collapsible sections require `<details>` and `<summary>` tags. The following
uses incorrect nesting:

<details>
<summary>Click to expand</summary>
Content here

Note: the closing tag is missing — this is intentionally malformed.
