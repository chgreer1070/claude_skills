# Shields.io API Reference

Full technical reference for the shields.io badge service — URL patterns, query parameters,
badge styles, dynamic endpoints, color system, and custom endpoint APIs.

SOURCE: [shields.io](https://shields.io/) (accessed 2026-03-03)
SOURCE: [shields.io/badges](https://shields.io/badges) (accessed 2026-03-03)
SOURCE: [badges/shields README — badge-maker](https://github.com/badges/shields/blob/master/badge-maker/README.md) (accessed 2026-03-03)
SOURCE: [shields.io/docs/logos](https://shields.io/docs/logos) (accessed 2026-03-03)
SOURCE: [gh api repos/badges/shields](https://api.github.com/repos/badges/shields) (accessed 2026-03-03)

**Repository stats (as of 2026-03-03):** 26,170 stars · 5,582 forks · 317 open issues
**License:** Creative Commons Zero v1.0 Universal
**Primary language:** JavaScript
**Description:** Concise, consistent, and legible badges in SVG and raster format

---

## 1. Static Badge URL Pattern

### Full Syntax

```text
https://img.shields.io/badge/{LABEL}-{MESSAGE}-{COLOR}
```

The `badgeContent` path parameter encodes label, message, and color separated by dashes.
Message + color only (no label) is also valid:

```text
https://img.shields.io/badge/{MESSAGE}-{COLOR}
```

### Character Encoding Rules

| URL input | Badge output |
| --- | --- |
| Underscore `_` or `%20` | Space |
| Double underscore `__` | Underscore `_` |
| Double dash `--` | Dash `-` |

Spaces must be encoded as `_` or `%20`. Special characters require percent-encoding.

### Concrete Examples

```text
https://img.shields.io/badge/any_text-you_like-blue
https://img.shields.io/badge/just%20the%20message-8A2BE2
https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge
https://img.shields.io/badge/coverage-95%25-orange
https://img.shields.io/badge/github-repo-blue?logo=github
```

---

## 2. Query Parameters (Universal)

All badge endpoints — static and dynamic — accept these query parameters.

### `style`

Controls the visual design of the badge. Default is `flat` for most badges.

**Possible values:** `flat` | `flat-square` | `plastic` | `for-the-badge` | `social`

```text
https://img.shields.io/badge/build-passing-green?style=for-the-badge
```

### `logo`

Icon slug from [simple-icons](https://simpleicons.org/). Click an icon title on simple-icons
to copy its slug. Full slug list: [slugs.md](https://github.com/simple-icons/simple-icons/blob/master/slugs.md).

```text
https://img.shields.io/badge/github-repo-blue?logo=github
https://img.shields.io/npm/v/npm.svg?logo=nodedotjs
```

Custom logos can be passed as base64-encoded SVG via the `logo` parameter:

```text
?logo=data:image/svg%2bxml;base64,{BASE64_SVG}
```

### `logoColor`

Color of the logo icon. Supports hex, rgb, rgba, hsl, hsla, and CSS named colors.
Only works for simple-icons logos — not for custom logos.

```text
?logo=javascript&logoColor=f5f5f5
?logo=github&logoColor=white
```

### `logoSize`

Set to `auto` to make icons adaptively resize. Useful for wider logos like `amd` or `amg`.
Only works for simple-icons logos — not for custom logos.

```text
?logo=amd&logoSize=auto
```

### `label`

Override the default left-hand-side text. Requires URL-encoding for spaces or special characters.

```text
?label=healthiness
?label=my%20custom%20label
```

### `labelColor`

Background color of the left (label) side. Supports hex, rgb, rgba, hsl, hsla, CSS named colors.

```text
?labelColor=abcdef
?labelColor=555
```

### `color`

Background color of the right (message) side. Supports hex, rgb, rgba, hsl, hsla, CSS named colors.

```text
?color=fedcba
?color=4c1
?color=brightgreen
```

### `cacheSeconds`

HTTP cache lifetime in seconds. Shields applies a per-badge minimum; values below the minimum
are ignored. Use to increase freshness for frequently-updated data.

```text
?cacheSeconds=3600
?cacheSeconds=300
```

### `link`

Array of up to two URLs specifying what clicking the left/right of a badge does.
**Only works in `<object>` HTML tags** — not in `<img>` tags or markdown.

```text
?link=https://example.com&link=https://example.com/docs
```

---

## 3. All 5 Badge Styles

### `flat` (default)

Flat design with a subtle gradient. Square corners on each half, slight shadow effect.
The default for nearly all badges.

```text
https://img.shields.io/badge/build-passing-brightgreen?style=flat
```

**When to use:** General-purpose. Default choice for most README files.

### `flat-square`

Identical to `flat` but with perfectly square corners — no rounded edges anywhere.

```text
https://img.shields.io/badge/build-passing-brightgreen?style=flat-square
```

**When to use:** When your design aesthetic requires sharp rectangular elements, or you want
badges to blend with code-block styling.

### `plastic`

Glossy pill-shaped design with a stronger gradient (convex highlight at top).
Taller and more three-dimensional than flat styles. Original shields.io style.

```text
https://img.shields.io/badge/build-passing-brightgreen?style=plastic
```

**When to use:** Legacy projects that used shields before the flat style was introduced.
Less common in modern READMEs.

### `for-the-badge`

Large format with all-uppercase text. Wider padding, bolder presence.
The badge is significantly taller than the other styles.

```text
https://img.shields.io/badge/build-PASSING-brightgreen?style=for-the-badge
```

**When to use:** Hero sections, promotional READMEs, when you want badges to be visually
prominent or make a statement.

### `social`

Styled like GitHub's own social buttons (star, fork, follow). Lighter background, count-bubble
appearance. Default for star and fork badges.

```text
https://img.shields.io/github/stars/badges/shields?style=social
```

**When to use:** Star counts, follower counts, fork counts — metrics that mirror the GitHub UI.

---

## 4. Color Reference

### Named Colors (Shields-Specific)

These names are defined in the badge-maker library. They differ from some CSS color values.

| Name | Typical Hex | Semantic Use |
| --- | --- | --- |
| `brightgreen` | `#4c1` / bright green | Build passing, tests passing, 100% coverage |
| `green` | `#97ca00` | Good/healthy status |
| `yellowgreen` | `#a4a61d` | Mostly good |
| `yellow` | `#dfb317` | Warning, moderate |
| `orange` | `#fe7d37` | Caution |
| `red` | `#e05d44` | Failing, error, critical |
| `blue` | `#007ec6` | Informational, version |
| `grey` / `gray` | `#555` | Default label background |
| `lightgrey` / `lightgray` | `#9f9f9f` | Default message background (inactive) |

### Semantic Aliases

These aliases map to one of the named colors above:

| Alias | Maps to |
| --- | --- |
| `success` | `brightgreen` |
| `important` | `orange` |
| `critical` | `red` |
| `informational` | `blue` |
| `inactive` | `lightgrey` |

### Hex Colors

Three- or six-character hex, optionally prefixed with `#`:

```text
?color=9cf
?color=007fff
?color=%23007fff
```

Note: The `#` character must be percent-encoded as `%23` in URLs when used in query strings.

### CSS Color Functions

Any valid CSS color is accepted:

```text
?color=rgb(255,128,0)
?color=rgba(255,128,0,0.8)
?color=hsl(120,100%,40%)
?color=hsla(120,100%,40%,0.5)
```

CSS named colors (aqua, fuchsia, lightslategray, etc.) are also accepted.

---

## 5. Dynamic Badge Endpoints — GitHub

All GitHub badges require `{user}` and `{repo}` path parameters.
GitHub API rate limits apply; authorize the Shields.io GitHub app to increase limits:
`https://img.shields.io/github-auth`

### Stars

```text
GET /github/stars/:user/:repo
https://img.shields.io/github/stars/badges/shields
```

Default style: `social`

### Forks

```text
GET /github/forks/:user/:repo
https://img.shields.io/github/forks/badges/shields
```

Default style: `social`

### Issues and Pull Requests

```text
GET /github/:variant/:user/:repo
https://img.shields.io/github/issues/badges/shields
```

`variant` values: `issues` | `issues-raw` | `issues-closed` | `issues-closed-raw` |
`issues-pr` | `issues-pr-raw` | `issues-pr-closed` | `issues-pr-closed-raw`

### Contributors

```text
GET /github/:metric/:user/:repo
https://img.shields.io/github/contributors/badges/shields
```

`metric` values:
- `contributors` — named contributors only (excludes anonymous commits)
- `contributors-anon` — includes anonymous commits

Note: Co-authors are not counted due to API endpoint limitations.

### Last Commit

```text
GET /github/last-commit/:user/:repo
https://img.shields.io/github/last-commit/badges/shields
```

Additional query params:
- `path` — restrict to a specific file path (e.g., `?path=README.md`)
- `display_timestamp` — `author` (default) or `committer`

### Repo Size

```text
GET /github/repo-size/:user/:repo
https://img.shields.io/github/repo-size/badges/shields
```

### Code Size

```text
GET /github/languages/code-size/:user/:repo
https://img.shields.io/github/languages/code-size/badges/shields
```

### Top Language

```text
GET /github/languages/top/:user/:repo
https://img.shields.io/github/languages/top/badges/shields
```

### License

```text
GET /github/license/:user/:repo
https://img.shields.io/github/license/badges/shields
```

### GitHub Actions Workflow Status

```text
GET /github/actions/workflow/status/:user/:repo/:workflow
https://img.shields.io/github/actions/workflow/status/badges/shields/unit-tests.yml
```

Additional query params:
- `branch` — target a specific branch (e.g., `?branch=main`)
- `event` — filter by trigger event (e.g., `?event=push`)

### Latest Release / Tag

```text
GET /github/v/release/:user/:repo
https://img.shields.io/github/v/release/badges/shields
```

Additional query params:
- `include_prereleases` — `true` or `false`
- `sort` — `date` (default) or `semver`
- `filter` — wildcard pattern to filter tag/release names; prefix with `!` to negate
- `display_name` — `tag` (default) or `release`

### Release Downloads

```text
GET /github/downloads/:user/:repo/total
https://img.shields.io/github/downloads/badges/shields/total
```

### Deployments

```text
GET /github/deployments/:user/:repo/:environment
https://img.shields.io/github/deployments/badges/shields/shields-staging
```

---

## 6. Dynamic Badge Endpoints — Package Registries

### npm Version

```text
GET /npm/v/:packageName
https://img.shields.io/npm/v/badge-maker
```

Additional query params:
- `registry_uri` — override registry (default: `https://registry.npmjs.com`)

Scoped packages: `@author/package-name` — encode the `@` as `%40` or use the path directly.

### PyPI Version

```text
GET /pypi/v/:packageName
https://img.shields.io/pypi/v/Django
```

Additional query params:
- `pypiBaseUrl` — override registry (default: `https://pypi.org`)

### Crates.io Version (Rust)

```text
GET /crates/v/:crate
https://img.shields.io/crates/v/rustc-serialize
```

---

## 7. Dynamic Badge Endpoints — Code Quality

### Codecov

```text
GET /codecov/c/:vcsName/:user/:repo
https://img.shields.io/codecov/c/github/codecov/example-node
```

`vcsName` values: `github` | `gh` | `bitbucket` | `bb` | `gitlab` | `gl`

Additional query params:
- `token` — required for private repositories (find in project settings under badge section)
- `flag` — display coverage for a specific [Codecov flag](https://docs.codecov.io/docs/flags)
- `component` — display coverage for a specific [Codecov component](https://docs.codecov.com/docs/components)

---

## 8. Dynamic Badge Endpoints — Social

### Discord

Requires the server's widget setting to be enabled by a server admin.
`serverId` is found in the Discord channel URL.

```text
GET /discord/:serverId
https://img.shields.io/discord/308323056592486420
```

---

## 9. Endpoint Badge API (Custom Dynamic Badges)

The endpoint badge lets you serve badge content from your own JSON endpoint.
Shields fetches your URL and renders the badge from the response.

### URL Pattern

```text
GET /badge/endpoint
https://img.shields.io/badge/endpoint?url={YOUR_ENDPOINT_URL}
```

Required query parameter: `url` — the URL of your JSON endpoint.

### JSON Response Schema

Your endpoint must return JSON matching this schema:

```json
{
  "schemaVersion": 1,
  "label": "hello",
  "message": "sweet world",
  "color": "orange"
}
```

| Property | Required | Default | Description |
| --- | --- | --- | --- |
| `schemaVersion` | yes | — | Always the number `1` |
| `label` | yes | — | Left-side text. Empty string omits the left side. Overridable by query string. |
| `message` | yes | — | Right-side text. Cannot be empty. |
| `color` | no | `lightgrey` | Right-side background color. Supports all color formats. Overridable by query string. |
| `labelColor` | no | `grey` | Left-side background color. Overridable by query string. |
| `isError` | no | `false` | Set `true` to treat as an error badge. Prevents user color override. |
| `namedLogo` | no | none | A simple-icons slug. Overridable by query string. |
| `logoSvg` | no | none | An SVG string for a custom logo. |
| `logoColor` | no | none | Color for the simple-icons logo. Overridable by query string. |
| `logoSize` | no | none | Set `auto` for adaptive icon sizing. simple-icons only. |
| `style` | no | `flat` | Default template. Overridable by query string. |

### Example

```text
https://img.shields.io/badge/endpoint?url=https://your-server.com/api/badge
```

Your server returns:

```json
{
  "schemaVersion": 1,
  "label": "uptime",
  "message": "99.9%",
  "color": "brightgreen"
}
```

---

## 10. Dynamic Data Extraction Badges

### Dynamic JSON Badge

Extract any value from a JSON document using a JSONPath selector.

```text
GET /badge/dynamic/json
https://img.shields.io/badge/dynamic/json?url={JSON_URL}&query={JSONPATH}
```

Required query params:
- `url` — URL to a JSON document
- `query` — JSONPath expression (see [jsonpath.com](https://jsonpath.com/))

Optional:
- `prefix` — string to prepend to the extracted value (e.g., `[`)
- `suffix` — string to append to the extracted value (e.g., `]`)

Example — extract package name from package.json:

```text
https://img.shields.io/badge/dynamic/json?url=https://github.com/badges/shields/raw/master/package.json&query=$.name&label=package
```

### Dynamic YAML Badge

Extract any value from a YAML document using a JSONPath selector.

```text
GET /badge/dynamic/yaml
https://img.shields.io/badge/dynamic/yaml?url={YAML_URL}&query={JSONPATH}
```

Required query params: `url`, `query`
Optional: `prefix`, `suffix`

Example:

```text
https://img.shields.io/badge/dynamic/yaml?url=https://raw.githubusercontent.com/badges/shields/master/.github/dependabot.yml&query=$.version
```

### Dynamic TOML Badge

Extract any value from a TOML document using a JSONPath selector.

```text
GET /badge/dynamic/toml
https://img.shields.io/badge/dynamic/toml?url={TOML_URL}&query={JSONPATH}
```

Required query params: `url`, `query`
Optional: `prefix`, `suffix`

### Dynamic XML Badge

Extract any value from an XML document using an XPath selector.

```text
GET /badge/dynamic/xml
https://img.shields.io/badge/dynamic/xml?url={XML_URL}&query={XPATH}
```

Required query params: `url`, `query` (XPath expression)
Optional: `prefix`, `suffix`

Note: For XML with a default namespace prefix, use `local-name()`:

```text
&query=/*[local-name()='myelement']
```

Useful resources: [XPather](http://xpather.com/), [XPath Cheat Sheet](https://devhints.io/xpath/)

---

## 11. Logo System

### SimpleIcons (Preferred)

Shields.io integrates with [SimpleIcons](https://simpleicons.org/) — a library of 3000+ brand icons.

Reference by slug:

```text
?logo=github
?logo=nodedotjs
?logo=python
?logo=docker
?logo=rust
```

Find slugs at [simpleicons.org](https://simpleicons.org/) (click icon title to copy slug) or
in [slugs.md](https://github.com/simple-icons/simple-icons/blob/master/slugs.md).

Note: The simple-icons site may contain icons not yet pulled into Shields.io. See
[discussion #5369](https://github.com/badges/shields/discussions/5369) for update cadence.

### Custom Logos (Base64 SVG)

Pass any SVG as a base64-encoded data URI:

```text
?logo=data:image/svg%2bxml;base64,{BASE64_ENCODED_SVG}
```

Limitations:
- `logoColor` parameter does not work with custom logos
- `logoSize=auto` does not work with custom logos

### logoColor

Sets the icon color for simple-icons logos. Not supported for custom logos.

```text
https://img.shields.io/badge/logo-javascript-blue?logo=javascript&logoColor=f5f5f5
```

---

## 12. badge-maker NPM Library

For rendering badges server-side or in your own application.

```bash
npm install badge-maker
```

### Library Usage

```javascript
import { makeBadge, ValidationError } from 'badge-maker'

const format = {
  label: 'build',       // optional
  message: 'passed',    // required
  color: 'brightgreen', // optional
  labelColor: '#555',   // optional
  style: 'flat',        // optional: 'plastic'|'flat'|'flat-square'|'for-the-badge'|'social'
  logoBase64: 'data:image/svg+xml;base64,...', // optional custom logo
  links: ['https://example.com', 'https://docs.example.com'], // optional, max 2
  idSuffix: 'dd',       // optional: unique suffix to prevent CSS cross-contamination in inline SVG
}

const svg = makeBadge(format)
```

### CLI Usage

```bash
npm install -g badge-maker
badge build passed :brightgreen > mybadge.svg
```

### Output Format

badge-maker produces SVG only. For raster conversion:
- JavaScript: use [gm](https://www.npmjs.com/package/gm)
- CLI: pipe to ImageMagick: `badge build passed :green | magick svg:- gif:-`

---

## 13. Self-Hosting

Run your own Shields.io instance behind a firewall:

```bash
docker pull shieldsio/shields
docker run -p 8080:80 shieldsio/shields
```

Image: [shieldsio/shields on Docker Hub](https://registry.hub.docker.com/r/shieldsio/shields/)

---

## 14. Output Formats

Shields.io serves badges in the following formats. Append the extension to the badge URL:

```text
https://img.shields.io/badge/build-passing-green.svg   (default, SVG)
https://img.shields.io/badge/build-passing-green.png   (PNG raster)
```

---

## 15. Markdown Integration Patterns

### Standard badge with link

```markdown
[![Alt text](https://img.shields.io/badge/LABEL-MESSAGE-COLOR)](https://target-url.com)
```

### Static badge examples

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
```

### Dynamic badge examples

```markdown
[![GitHub stars](https://img.shields.io/github/stars/badges/shields?style=social)](https://github.com/badges/shields)
[![npm version](https://img.shields.io/npm/v/badge-maker.svg)](https://npmjs.org/package/badge-maker)
[![PyPI version](https://img.shields.io/pypi/v/Django.svg)](https://pypi.org/project/Django/)
[![CI](https://img.shields.io/github/actions/workflow/status/owner/repo/ci.yml?branch=main)](https://github.com/owner/repo/actions)
[![codecov](https://img.shields.io/codecov/c/github/owner/repo)](https://codecov.io/gh/owner/repo)
```

### For-the-badge style examples

```markdown
[![Built with Python](https://img.shields.io/badge/Built%20with-Python-blue?style=for-the-badge&logo=python)](https://python.org)
[![Made with Love](https://img.shields.io/badge/Made%20with-Love-red?style=for-the-badge)](https://github.com/badges/shields)
```
