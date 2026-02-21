# dasel — Structured Data Query and Transform

Query, modify, and convert structured data files (JSON, YAML, TOML, XML, CSV, HCL, INI) using [dasel v3](https://github.com/TomWright/dasel). One consistent query syntax for every format.

## Why Install This?

When you ask Claude to extract, update, or convert structured data files, Claude may:

- Use slow, format-specific tools (separate commands for JSON vs YAML vs XML)
- Write custom scripts for simple one-field updates
- Read entire config files into context when a targeted query would suffice
- Suggest `jq` for JSON but have no equivalent for YAML, TOML, or XML

This plugin gives Claude deep knowledge of dasel v3 syntax and workflows, plus installation tooling, so Claude can query and transform any supported format with a single tool.

## What You Get

### Skills

**dasel-reference** — Complete dasel v3 syntax reference. Covers selectors (dot notation, array indexing, slices, recursive descent, object construction), all 19 built-in functions (`filter`, `map`, `each`, `search`, `sortBy`, `keys`, `merge`, and more), modification syntax, format conversion, variable assignment, and conditionals. Includes detailed references for format-specific patterns.

**data-exploration** — Systematic workflows for exploring unfamiliar structured data. Claude follows a step-by-step sequence: discover top-level keys, navigate nested structures, sample arrays, inspect types, and extract values — without reading entire large files into context.

**data-transformation** — Patterns for modifying and converting structured data safely. Covers in-place field updates, format conversion, array append/batch-update, object construction via spread, field removal by reconstruction, and multi-step transformations with variables.

**setup** — Install, update, and troubleshoot the dasel v3 binary. Covers all platforms, SHA256 verification, PATH setup, and common error diagnosis.

**Enterprise XML domain skills** — Five specialized skills for common enterprise XML formats:

| Skill | File type | Coverage |
|---|---|---|
| `enterprise-installanywhere` | `.iap_xml` | Action sequences, variables, platform branches, installer comparison |
| `enterprise-spring-xml` | Spring bean XML | Bean discovery, dependency wiring, JMS mapping, property injection |
| `enterprise-maven-pom` | `pom.xml` | Dependency versions, groupId/scope filtering, multi-module hierarchy |
| `enterprise-hibernate-hbm` | `.hbm.xml` | Entity-table bindings, property-column mapping, relationship tracing |
| `enterprise-tomcat-web` | `web.xml` | Servlet enumeration, filter chains, listener listing, context params |

### Agents

**data-explorer** (`haiku`) — Fast read-only exploration agent. Executes dasel queries against structured data files, discovers structure, lists keys, samples arrays, and extracts values. Always shows the exact command it ran. Never modifies files.

**dasel-guide** (`haiku`) — Teaches dasel v3 query syntax. Does not execute commands — explains how to construct selectors, provides complete copy-pasteable examples, and clarifies v3 syntax differences from v2.

**data-analyst** (`sonnet`) — Structural analysis agent for multi-file work. Handles schema comparison, pattern detection across large file sets, cross-file diffing, and migration planning. Writes intermediate results to `/tmp/` and produces reproducible analysis reports.

### Session Hook

At session start, the plugin checks whether dasel is installed and injects its version into session context. If dasel is missing, Claude is prompted to run `/dasel:setup`.

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install dasel@jamie-bitflight-skills
```

## Install dasel

After installing the plugin, install the dasel binary:

```bash
/dasel:setup
```

This runs `scripts/install_dasel.py`, which detects your platform, downloads the correct binary from [GitHub Releases](https://github.com/TomWright/dasel/releases), verifies the SHA256 digest, and installs to user-space:

- **Linux / macOS / WSL2**: `~/.local/bin/dasel`
- **Windows**: `%LOCALAPPDATA%\Programs\dasel\dasel.exe`

Supported platforms: Linux x86\_64, Linux ARM64, macOS, Windows x64.

Options:

```bash
/dasel:setup              # Install or update to latest
/dasel:setup --force      # Reinstall even if already at latest
/dasel:setup --dry-run    # Preview without changes
```

## Usage

Once installed, Claude automatically applies dasel knowledge when you work with structured data files.

### Query data

```
Extract all database hostnames from config.yaml
```

Claude uses dasel to navigate nested YAML without reading the entire file:

```bash
cat config.yaml | dasel -i yaml 'database.connection.host'
```

### Explore unknown files

```
What fields does this JSON response have?
```

Claude discovers structure systematically:

```bash
cat response.json | dasel -i json 'keys($this)'
cat response.json | dasel -i json 'users[0]'
```

### Update config values

```
Set the server port to 9090 in config.yaml
```

Claude uses the safe update pattern (write to temp, then rename):

```bash
cat config.yaml | dasel -i yaml --root 'server.port = 9090' > config_tmp.yaml && mv config_tmp.yaml config.yaml
```

### Convert formats

```
Convert this JSON config to YAML
```

```bash
cat data.json | dasel -i json -o yaml > data.yaml
```

### Batch updates

```
Increment all version fields in data.json by 1
```

```bash
cat data.json | dasel -i json --root 'items.each(version = version + 1)'
```

### Query XML

```
List all bean IDs in this Spring applicationContext.xml
```

Claude uses enterprise XML patterns:

```bash
dasel -f applicationContext.xml -i xml 'beans.bean.filter(has("-id")).map("-id")'
```

## Example: Before and After

**Without this plugin:**

```
You: Extract all active user emails from users.json
Claude: [reads the entire file, then writes a Python script]
```

**With this plugin:**

```
You: Extract all active user emails from users.json
Claude: [runs targeted dasel query]

  cat users.json | dasel -i json 'users.filter(active == true).map(email)'

  Result:
  "alice@example.com"
  "bob@example.com"
```

## dasel v3 Basics

dasel uses a unified query syntax across all supported formats. Input comes from stdin; format must be specified explicitly with `-i`:

```bash
# Query a value
echo '{"db": {"host": "localhost"}}' | dasel -i json 'db.host'

# Format conversion
cat config.toml | dasel -i toml -o yaml

# Modify and output full document
echo '{"port": 3000}' | dasel -i json --root 'port = 8080'

# Filter and map
cat data.json | dasel -i json 'users.filter(active == true).map(name)'
```

**Key flags:**

| Flag | Purpose |
|---|---|
| `-i <format>` | Input format (json, yaml, toml, xml, csv, hcl, ini) |
| `-o <format>` | Output format (defaults to input format) |
| `--root` | Output full document after modification |
| `--compact` | Compact output |
| `--var name=value` | Pass a variable into the query |

**v3 differences from v2:**

- `put` and `delete` subcommands removed — use assignment with `--root` instead
- Query/selector syntax completely revamped — v2 selectors are not compatible
- CLI framework changed from Cobra to Kong

## Supported Formats

| Format | File types |
|---|---|
| JSON | `.json` |
| YAML | `.yaml`, `.yml` |
| TOML | `.toml` |
| XML | `.xml`, `.iap_xml`, and others |
| CSV | `.csv` |
| HCL | `.hcl`, `.tf` |
| INI | `.ini` |

## Requirements

- Claude Code v2.0+
- dasel v3 binary (install with `/dasel:setup`)
- Python 3.11+ and `uv` (for the install script)

## References

- [dasel GitHub repository](https://github.com/TomWright/dasel)
- [dasel v3 documentation](https://daseldocs.tomwright.me)
- [dasel releases](https://github.com/TomWright/dasel/releases)
