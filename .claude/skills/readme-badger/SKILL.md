---
name: readme-badger
description: Insert badge images into README files across multiple markup formats (Markdown, reStructuredText, AsciiDoc, Textile, RDoc, Org-mode, MediaWiki, Pod, and plaintext). Use when a task requires programmatically adding shields.io or other badge URLs to project documentation files.
---

# readme-badger

A Node.js library that inserts badge images into README files. It detects the file format from
the extension, produces format-correct badge markup, and inserts it at the right position
(after the first header, or appended to an existing badge line in Markdown).

SOURCE: `package.json` and `lib/index.js` from <https://github.com/gitterHQ/readme-badger>
(accessed 2026-03-03). Canonical upstream: <https://gitlab.com/gitlab-org/gitter/readme-badger>

## Installation

```bash
npm install readme-badger
```

Version 0.3.0 (latest). MIT license. One runtime dependency: `balanced-match ^1.0.0`.

SOURCE: `package.json` at <https://github.com/gitterHQ/readme-badger> (accessed 2026-03-03)

## Core API

```javascript
var badger = require('readme-badger');

// Insert a badge into README content
var newContent = badger.addBadge(content, fileExt, imageUrl, linkUrl, altText);

// Check whether the format renders badge images (vs. plaintext fallback)
var supportsImages = badger.hasImageSupport(fileExt);
```

### `addBadge(content, fileExt, imageUrl, linkUrl, altText)`

| Parameter  | Type   | Required | Description |
|------------|--------|----------|-------------|
| `content`  | string | yes      | Full text of the README file |
| `fileExt`  | string | yes      | File extension without the dot (e.g. `"md"`, `"rst"`) |
| `imageUrl` | string | yes      | URL of the badge image |
| `linkUrl`  | string | yes      | URL the badge links to |
| `altText`  | string | yes      | Alt text — shown as plain text in formats that lack image support |

Returns the modified `content` string with the badge inserted. All four string parameters are
asserted non-empty; an `AssertionError` is thrown if any is missing.

`fileExt` is case-insensitive. Unknown extensions fall back to plaintext (appends `altText`
on a new line at the end of the file).

### `hasImageSupport(fileExt)`

Returns `true` if the extension maps to a format that renders badge images. Returns `false`
for unknown extensions (plaintext fallback).

Use this to decide whether to include a URL in `altText` — for plaintext formats the
`altText` is the only visible output, so embedding the link URL in it is recommended.

## Supported Formats

See [./references/format-support.md](./references/format-support.md) for per-format badge
syntax and insertion logic.

| Extension(s)                   | `hasImageSupport` | Insertion point |
|-------------------------------|-------------------|-----------------|
| `md`, `mdown`, `mkdn`, `markdown` | `true`        | Appends to last badge line, or after first `#` header |
| `rst`                          | `true`            | After first underline-style header |
| `asciidoc`, `adoc`, `asc`      | `true`            | After first `=` / `---` header |
| `textile`                      | `true`            | After `h1.` header |
| `rdoc`                         | `true`            | After `===` header |
| `org`                          | `true`            | After `*` header |
| `mediawiki`, `wiki`            | `true`            | After `=` header |
| `pod`                          | `true`            | After `=head1` |
| anything else / omitted        | `false`           | Bottom of file (altText only) |

SOURCE: `lib/index.js` and individual format modules from <https://github.com/gitterHQ/readme-badger>
(accessed 2026-03-03)

## Usage Pattern

```javascript
var fs = require('fs');
var badger = require('readme-badger');

var filePath = 'README.md';
var ext = filePath.split('.').pop(); // 'md'

// Recommend including URL in altText for formats that don't render images
var altText = badger.hasImageSupport(ext)
  ? 'Join the chat at Gitter'
  : 'Join the chat at https://gitter.im/my/room';

var content = fs.readFileSync(filePath, 'utf8');
var updated = badger.addBadge(
  content,
  ext,
  'https://badges.gitter.im/my/room.svg',
  'https://gitter.im/my/room',
  altText
);
fs.writeFileSync(filePath, updated);
```

## Markdown Smart Insert

Markdown gets special treatment: if the file already contains badge lines (lines matching
`[![...](...)`)(`...)`), the new badge is appended to the **last** such line rather than
inserted below the header. This groups all badges together.

If no existing badge line is found, the badge is inserted on the line immediately after the
first `#` header line.

SOURCE: `lib/markdown.js` from <https://github.com/gitterHQ/readme-badger> (accessed 2026-03-03)

## References

- [Format-specific syntax and insertion logic](./references/format-support.md)
- npm: <https://www.npmjs.com/package/readme-badger>
- Source (GitLab, canonical): <https://gitlab.com/gitlab-org/gitter/readme-badger>
- Source (GitHub, archived): <https://github.com/gitterHQ/readme-badger>
