# readme-badger — Format Support Reference

Per-format badge syntax and insertion logic, derived from source modules.

SOURCE: All modules in `lib/` from <https://github.com/gitterHQ/readme-badger> (accessed 2026-03-03)

---

## Markdown (`md`, `mdown`, `mkdn`, `markdown`)

**Badge syntax:**

```text
[![altText](imageUrl)](linkUrl)
```

**Insertion logic:**

1. Scan lines in reverse for the last line matching the badge pattern `[![...](...)`)(`...)`.
2. If found: append the new badge to that line separated by a space, using `balanced-match`
   to find the exact end of the last badge's link parentheses.
3. If not found: locate the first header line (matching `/^\s*(\#+|={3,}|-{3,})/`). Insert
   the badge on the line immediately after it, adding an extra blank line if the line after
   the header is non-empty.

**Example (appended to existing badges):**

```markdown
# My Project

[![Build Status](https://travis-ci.org/me/proj.svg)](https://travis-ci.org/me/proj) [![New Badge](https://img.shields.io/badge/new-badge.svg)](https://example.com)
```

**Example (after header, no existing badges):**

```markdown
# My Project

[![New Badge](https://img.shields.io/badge/new-badge.svg)](https://example.com)

Project description here.
```

---

## reStructuredText (`rst`)

**Badge syntax:**

```rst
.. image:: imageUrl
   :alt: altText
   :target: linkUrl
```

**Insertion logic:**

Scan for the first RST-style section header — a line whose characters are all from
`= - \` : ' " ~ ^ _ * + # < >`, whose length is >= the line above it, and that line above
is non-empty. Insert after that header block.

**Example:**

```rst
My Project
==========

.. image:: https://img.shields.io/badge/new-badge.svg
   :alt: New Badge
   :target: https://example.com
```

---

## AsciiDoc (`asciidoc`, `adoc`, `asc`)

**Badge syntax:**

```asciidoc
image:imageUrl[link="linkUrl"]
```

Note: `altText` is not included in the AsciiDoc output — only `imageUrl` and `linkUrl` are used.

**Insertion logic:**

Scan for the first line matching `/^\s*(\=+|={3,}|-{3,})/`. Insert after that header block.

---

## Textile (`textile`)

**Badge syntax:**

```textile
!imageUrl(altText)!:linkUrl
```

**Insertion logic:**

Scan for the first line matching `/^\s*(h1\.\s)/`. Insert after that header block.

---

## RDoc (`rdoc`)

**Badge syntax:**

```rdoc
{<img src="imageUrl" alt="altText">}[linkUrl]
```

**Insertion logic:**

Scan for the first line matching `/^\s*(\=+)/`. Insert after that header block.

---

## Org-mode (`org`)

**Badge syntax:**

```org
  #+ATTR_HTML: title="altText"
  [[linkUrl][file:imageUrl]]
```

**Insertion logic:**

Scan for the first line matching `/^\s*(\*\s)/` (org heading). Insert after that heading.

---

## MediaWiki (`mediawiki`, `wiki`)

**Badge syntax:**

```html
<a href="linkUrl"><img src="imageUrl" alt="altText"/></a>
```

**Insertion logic:**

Scan for the first line matching `/^\s*(\=+)/`. Insert after that header block.

---

## Pod (`pod`)

**Badge syntax:**

```pod
=begin HTML

<p><a href="linkUrl"><img src="imageUrl" alt="altText"></a></p>

=end HTML
```

**Insertion logic:**

Scan for the first line matching `/^\s*(\=head1)/`. Insert after that `=head1` block.

---

## Plaintext / Unknown Extensions

**Output:**

`altText` appended on a new line at the bottom of the file. `imageUrl` and `linkUrl` are
not used. The `linkUrl` stripped of query parameters is used internally by the plaintext
module (the original plaintext.js uses `linkUrl.split('?')[0]`), but only `altText` appears
in the final output.

**Recommendation:** Include the full target URL in `altText` so the link is accessible in
plaintext contexts:

```javascript
var altText = 'Join the chat at https://gitter.im/my/room';
```

`hasImageSupport()` returns `false` for these extensions, which can be used to conditionally
set `altText` to include a URL.
