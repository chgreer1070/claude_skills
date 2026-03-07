# Extraction Patterns

How to extract AI-usable knowledge atoms from each user-facing documentation type. Apply these patterns in Phase 1 of the `user-docs-to-ai-skill` workflow.

## Table of Contents

1. [Extraction Atom Format](#extraction-atom-format)
2. [How-To Guides](#how-to-guides)
3. [API References](#api-references)
4. [Tutorials](#tutorials)
5. [Conceptual Explanations](#conceptual-explanations)
6. [Examples and Code Samples](#examples-and-code-samples)
7. [Format-Specific Extraction](#format-specific-extraction)
   - [PDF Documents](#pdf-documents)
   - [Word Documents](#word-documents)
   - [Excel and Spreadsheet Files](#excel-and-spreadsheet-files)
   - [PowerPoint Presentations](#powerpoint-presentations)
   - [AsciiDoc](#asciidoc)
   - [reStructuredText](#restructuredtext)
   - [Jupyter Notebooks](#jupyter-notebooks)
   - [HTML Documentation](#html-documentation)
   - [Man Pages](#man-pages)
   - [TOML, YAML, and JSON Config Files](#toml-yaml-and-json-config-files)
   - [Plain Text](#plain-text)
8. [What to Preserve Verbatim](#what-to-preserve-verbatim)
9. [What to Abstract](#what-to-abstract)
10. [Anti-Patterns](#anti-patterns)

---

## Extraction Atom Format

Every extracted piece of knowledge is an atom:

```text
ATOM: <one-sentence fact, constraint, parameter, or pattern>
TYPE: command | parameter | constraint | pattern | error | example
SOURCE: <filename:section-heading>
```

Collect all atoms into a flat list before grouping. Do not filter or discard atoms during extraction — filter during grouping.

---

## How-To Guides

How-to guides are procedure documents. They contain steps, conditions, and outcomes.

**Extract:**

- Each numbered step as a separate `TYPE: pattern` atom
- Conditional branches ("if X, then Y") as `TYPE: constraint` atoms
- Prerequisites listed before steps as `TYPE: constraint` atoms
- Warning/caution blocks as `TYPE: constraint` atoms
- The goal stated in the heading as the atom context

**Example — source text:**

```text
## Configure the output directory

Before running, ensure the target directory exists.

1. Set `output.dir` in your config file.
2. If using relative paths, they resolve from the project root.
3. Run `ty check --output-dir ./results` to verify.

> Warning: existing files in the output directory are overwritten without confirmation.
```

**Extracted atoms:**

```text
ATOM: output.dir must be set in config before running
TYPE: parameter
SOURCE: docs/configuration.md:Configure the output directory

ATOM: target directory must exist before running
TYPE: constraint
SOURCE: docs/configuration.md:Configure the output directory

ATOM: relative paths resolve from project root
TYPE: constraint
SOURCE: docs/configuration.md:Configure the output directory

ATOM: `ty check --output-dir ./results` verifies the output directory configuration
TYPE: command
SOURCE: docs/configuration.md:Configure the output directory

ATOM: existing files in the output directory are overwritten without confirmation
TYPE: constraint
SOURCE: docs/configuration.md:Configure the output directory
```

**Skip:**

- Motivational framing ("This guide will help you...")
- Navigation hints ("See the next section for...")
- Version history context unless it changes current behavior

---

## API References

API references are schema documents. They contain parameters, types, defaults, and constraints.

**Extract:**

- Every parameter name, type, and default as a `TYPE: parameter` atom
- Every enum value list — preserve exactly, do not paraphrase
- Every required vs optional distinction as a `TYPE: constraint` atom
- Every error code or error message pattern as a `TYPE: error` atom
- Return type and shape as a `TYPE: pattern` atom

**Preserve verbatim:** parameter names, type names, enum values, error codes, CLI flag syntax. These are identifiers — paraphrasing causes hallucination downstream.

**Example — source text:**

```text
### `check` command

`ty check [OPTIONS] [PATH]`

Options:
  --output-dir PATH     Write diagnostics to this directory. Default: stdout.
  --format [text|json]  Output format. Default: text.
  --strict              Treat warnings as errors. Default: off.
  --python-version VER  Target Python version. Must be 3.8–3.13.
```

**Extracted atoms:**

```text
ATOM: ty check command syntax is `ty check [OPTIONS] [PATH]`
TYPE: command
SOURCE: docs/cli.md:check command

ATOM: --output-dir PATH writes diagnostics to a directory; default is stdout
TYPE: parameter
SOURCE: docs/cli.md:check command

ATOM: --format accepts [text|json]; default is text
TYPE: parameter
SOURCE: docs/cli.md:check command

ATOM: --strict treats warnings as errors; default is off
TYPE: parameter
SOURCE: docs/cli.md:check command

ATOM: --python-version accepts 3.8 through 3.13 only
TYPE: constraint
SOURCE: docs/cli.md:check command
```

---

## Tutorials

Tutorials are learning documents. They introduce concepts through worked examples. They often contain both conceptual explanation AND procedural steps.

**Extract:**

- The concept being taught as a `TYPE: pattern` atom — what it IS, not why it's interesting
- Each code example as a `TYPE: example` atom — preserve the code verbatim
- Each "why this works" explanation distilled to a single constraint or pattern atom
- Prerequisites listed or implied at the start as `TYPE: constraint` atoms

**Skip:**

- Narrative scaffolding ("In this tutorial, we will learn...")
- Motivational context ("Understanding X will help you Y")
- Analogies and metaphors — extract only the technical fact the analogy explains

---

## Conceptual Explanations

Conceptual docs explain how something works internally. Extract the facts, not the explanation style.

**Extract:**

- Each named concept as a `TYPE: pattern` atom stating what it does
- Relationships between concepts ("X depends on Y", "X replaces Y") as `TYPE: constraint` atoms
- Limitations stated explicitly as `TYPE: constraint` atoms
- Behavior under edge conditions as `TYPE: constraint` atoms

**Skip:**

- Historical background ("This was introduced in version 2.0 because...")
- Design rationale unless it directly constrains usage
- Comparisons to other tools unless they reveal constraints

---

## Examples and Code Samples

Code examples are the highest-fidelity source. They show exact invocation patterns.

**Extract:**

- Every code block as a `TYPE: example` atom — copy verbatim, do not rewrite
- The comment or heading above the code block as the atom description
- If the example demonstrates a constraint ("notice that X must come before Y"), extract that as a separate `TYPE: constraint` atom

**Preserve verbatim:** All code. Never paraphrase code examples — rewriting introduces subtle errors. If the original code has a bug, copy it exactly and add a note in the atom description.

---

## Format-Specific Extraction

Apply these patterns when the source document is not plain markdown. Each format has a preferred read tool, extraction targets, and items to skip.

---

### PDF Documents

**Tool:** Use `Read` (Claude supports `.pdf` natively with `pages` parameter) for standard PDFs. Use MCP server `mcp-file-contents-reader` (tool: `file-reader`) when the Read tool returns empty content.

**Extract:**

- Headings and section structure as atom context
- Body paragraphs as `TYPE: pattern` or `TYPE: constraint` atoms — one claim per atom
- Code blocks or monospaced text as `TYPE: example` atoms — copy verbatim
- Tables as `TYPE: parameter` atoms — one row per atom with column headers as field names

**Skip:**

- Page headers, footers, and page numbers
- Table of contents entries (use the referenced sections instead)
- Watermarks and legal boilerplate

**Note:** Scanned PDFs without OCR yield empty text. If Read returns no content, try `mcp-file-contents-reader`. If both fail, report the file as unreadable and skip it.

**Example — source PDF section:**

```text
## Rate Limits

Requests are capped at 100 per minute per API key.
Exceeding the limit returns HTTP 429.
```

**Extracted atoms:**

```text
ATOM: API requests are capped at 100 per minute per API key
TYPE: constraint
SOURCE: api-guide.pdf:Rate Limits

ATOM: exceeding the rate limit returns HTTP 429
TYPE: error
SOURCE: api-guide.pdf:Rate Limits
```

---

### Word Documents

**Tool:** Use `mcp-file-contents-reader` (tool: `file-reader`) for `.docx` and `.doc` files. The Read tool does not support Word format.

**Extract:**

- Heading hierarchy — map Heading 1/2/3 to `#`/`##`/`###` for atom SOURCE fields
- Tables — each data row becomes a `TYPE: parameter` atom; column headers name the fields
- Numbered and bulleted lists — each item as a separate atom
- Callout boxes and "Note:" paragraphs as `TYPE: constraint` atoms

**Skip:**

- Bold, italic, color, and font formatting — extract text content only
- Track-changes markup and comments
- Document metadata (author, revision date) unless operationally relevant

**Example — source Word table:**

```text
| Parameter     | Type    | Default | Required |
|---------------|---------|---------|----------|
| timeout       | integer | 30      | No       |
| retry_count   | integer | 3       | No       |
| api_key       | string  | —       | Yes      |
```

**Extracted atoms:**

```text
ATOM: timeout parameter is type integer, default 30, optional
TYPE: parameter
SOURCE: setup-guide.docx:Configuration Parameters

ATOM: retry_count parameter is type integer, default 3, optional
TYPE: parameter
SOURCE: setup-guide.docx:Configuration Parameters

ATOM: api_key parameter is type string, required, no default
TYPE: parameter
SOURCE: setup-guide.docx:Configuration Parameters
```

---

### Excel and Spreadsheet Files

**Tool:** Use `mcp-file-contents-reader` for `.xlsx` and `.xls`. Read `.csv` directly with the Read tool.

**Extract:**

- Column headers as field names for `TYPE: parameter` atoms
- Each data row as a separate atom — include all non-empty field values
- Configuration sheets where each row defines a setting — extract as `TYPE: parameter` atoms with name, type, default, and description
- Lookup tables (e.g., error codes → descriptions) as `TYPE: error` atoms

**Skip:**

- Empty rows and formatting-only rows
- Chart objects and pivot table metadata
- Summary/total rows that duplicate computed values

**Example — source CSV:**

```text
setting,type,default,description
log_level,string,INFO,Logging verbosity (DEBUG|INFO|WARN|ERROR)
max_connections,integer,10,Maximum concurrent database connections
cache_ttl,integer,300,Cache entry lifetime in seconds
```

**Extracted atoms:**

```text
ATOM: log_level setting is type string, default INFO, accepts DEBUG|INFO|WARN|ERROR
TYPE: parameter
SOURCE: config-reference.csv:sheet1

ATOM: max_connections setting is type integer, default 10
TYPE: parameter
SOURCE: config-reference.csv:sheet1

ATOM: cache_ttl setting is type integer, default 300 seconds
TYPE: parameter
SOURCE: config-reference.csv:sheet1
```

---

### PowerPoint Presentations

**Tool:** Use `mcp-file-contents-reader` (tool: `file-reader`) for `.pptx` and `.ppt`. The Read tool does not support PowerPoint format.

**Extract:**

- Slide titles as section headings for atom SOURCE fields
- Bullet points as individual atoms — one bullet per atom
- Code or command text on slides as `TYPE: example` or `TYPE: command` atoms — copy verbatim
- Speaker notes as supplementary `TYPE: constraint` atoms when they add detail absent from slide content

**Skip:**

- Decorative text, theme placeholders, and footer text
- Slide numbers
- Repeated header/footer content present on every slide
- Transition and animation metadata

**Example — source slide:**

```text
Slide title: Authentication Flow

Bullets:
- Client sends POST /auth with credentials
- Server returns JWT valid for 24 hours
- Token must be sent as Bearer in Authorization header

Speaker notes:
Tokens are not refreshable — clients must re-authenticate after expiry.
```

**Extracted atoms:**

```text
ATOM: client authenticates by sending POST /auth with credentials
TYPE: pattern
SOURCE: architecture-overview.pptx:Authentication Flow

ATOM: server returns JWT valid for 24 hours
TYPE: constraint
SOURCE: architecture-overview.pptx:Authentication Flow

ATOM: JWT token must be sent as Bearer in Authorization header
TYPE: constraint
SOURCE: architecture-overview.pptx:Authentication Flow

ATOM: JWT tokens are not refreshable; clients must re-authenticate after expiry
TYPE: constraint
SOURCE: architecture-overview.pptx:Authentication Flow
```

---

### AsciiDoc

**Tool:** Read directly with the Read tool. `.adoc` and `.asciidoc` files are plain text.

**Extract:**

- `=` headings map to `#` markdown — use as atom SOURCE section names
- Admonition blocks (`NOTE:`, `TIP:`, `WARNING:`, `IMPORTANT:`, `CAUTION:`) as `TYPE: constraint` atoms — prefix atom text with the admonition type
- `[source,lang]` blocks as `TYPE: example` atoms — copy content verbatim
- Definition lists (`term:: definition`) as `TYPE: parameter` atoms

**Skip:**

- AsciiDoc attribute definitions (`:toc:`, `:author:`, etc.)
- Cross-reference anchors (`[[anchor-id]]`) — use heading text in SOURCE instead
- Include directives — follow them and extract from the included file separately

**Example — source AsciiDoc:**

```text
== Installation

[source,bash]
----
pip install mypackage==2.1.0
----

WARNING: Installing without a version pin may break existing integrations.

NOTE: Python 3.9 or later is required.
```

**Extracted atoms:**

```text
ATOM: `pip install mypackage==2.1.0` installs the package at a pinned version
TYPE: example
SOURCE: install-guide.adoc:Installation

ATOM: WARNING — installing without a version pin may break existing integrations
TYPE: constraint
SOURCE: install-guide.adoc:Installation

ATOM: NOTE — Python 3.9 or later is required
TYPE: constraint
SOURCE: install-guide.adoc:Installation
```

---

### reStructuredText

**Tool:** Read directly with the Read tool. `.rst` files are plain text.

**Extract:**

- Underline-style headings (lines followed by `===`, `---`, `~~~`, `^^^`) map to `#`/`##`/`###` — use heading text in SOURCE fields
- `.. code-block:: lang` directives — copy enclosed content as `TYPE: example` atoms
- `.. warning::`, `.. note::`, `.. important::` directives as `TYPE: constraint` atoms
- Field lists (`:param name:`, `:type name:`, `:returns:`) as `TYPE: parameter` atoms
- Cross-references (`:ref:\`label\``) resolve to the referenced section name

**Skip:**

- RST substitution definitions (`.. |name| replace::`)
- Directive options not affecting content (`:class:`, `:align:`)
- `.. toctree::` directives — follow linked files and extract from each separately

**Example — source RST:**

```text
connect
-------

.. code-block:: python

    client.connect(host="localhost", port=5432)

.. warning::

    Calling connect() twice raises ConnectionError.

:param host: Database hostname. Default: localhost.
:param port: Database port. Default: 5432.
```

**Extracted atoms:**

```text
ATOM: `client.connect(host="localhost", port=5432)` establishes a database connection
TYPE: example
SOURCE: api-reference.rst:connect

ATOM: calling connect() twice raises ConnectionError
TYPE: constraint
SOURCE: api-reference.rst:connect

ATOM: host parameter is type string, default localhost
TYPE: parameter
SOURCE: api-reference.rst:connect

ATOM: port parameter is type integer, default 5432
TYPE: parameter
SOURCE: api-reference.rst:connect
```

---

### Jupyter Notebooks

**Tool:** Read directly with the Read tool. Claude supports `.ipynb` natively — cell types, outputs, and metadata are accessible.

**Extract:**

- Code cells as `TYPE: example` atoms — copy cell source verbatim
- Markdown cells — apply standard markdown extraction patterns from other sections
- Output cells containing error tracebacks as `TYPE: error` atoms — copy the exception type and message verbatim; skip the full traceback stack
- Cell-level headings (markdown cells with `#`) as section context for SOURCE fields

**Skip:**

- Raw cell content (format-specific display directives not relevant to extraction)
- Output cells containing rendered plots or images — note their presence in the atom description if the code cell references them
- Kernel metadata and cell execution counts

**Example — source notebook cells:**

```text
[markdown cell]
## Loading Data

[code cell]
df = pd.read_csv("data/input.csv", parse_dates=["timestamp"])

[output cell — error]
FileNotFoundError: [Errno 2] No such file or directory: 'data/input.csv'
```

**Extracted atoms:**

```text
ATOM: `df = pd.read_csv("data/input.csv", parse_dates=["timestamp"])` loads CSV with timestamp parsing
TYPE: example
SOURCE: analysis.ipynb:Loading Data

ATOM: pd.read_csv raises FileNotFoundError when the target file does not exist
TYPE: error
SOURCE: analysis.ipynb:Loading Data
```

---

### HTML Documentation

**Tool:** Use the Read tool for local `.html` and `.htm` files. Use `WebFetch` for URLs. Both return text content with HTML stripped.

**Extract:**

- `<h1>`–`<h6>` headings as section structure for SOURCE fields
- `<code>` and `<pre>` blocks as `TYPE: example` or `TYPE: command` atoms — copy content verbatim
- `<table>` elements — apply the same extraction as spreadsheet rows: column headers as field names, each row as a `TYPE: parameter` atom
- `<blockquote>` and `<aside>` elements labeled as notes or warnings as `TYPE: constraint` atoms

**Skip:**

- Navigation menus, sidebars, breadcrumbs, and footers — these are site chrome, not content
- Cookie consent banners and analytics scripts
- Social sharing buttons and feedback widgets
- Repeated boilerplate present on every page (site header, global nav)

**Example — source HTML:**

```text
<h2>Configuration</h2>
<table>
  <tr><th>Key</th><th>Type</th><th>Default</th></tr>
  <tr><td>debug</td><td>boolean</td><td>false</td></tr>
  <tr><td>port</td><td>integer</td><td>8080</td></tr>
</table>
<pre><code>export DEBUG=true PORT=9000 ./server</code></pre>
```

**Extracted atoms:**

```text
ATOM: debug configuration key is type boolean, default false
TYPE: parameter
SOURCE: config.html:Configuration

ATOM: port configuration key is type integer, default 8080
TYPE: parameter
SOURCE: config.html:Configuration

ATOM: `export DEBUG=true PORT=9000 ./server` starts the server with debug and custom port
TYPE: example
SOURCE: config.html:Configuration
```

---

### Man Pages

**Tool:** Run `man -l <file> | col -b` via Bash to convert to plain text, then apply standard text extraction. The `col -b` flag strips backspace-encoded bold and underline formatting.

**Extract:**

- `SYNOPSIS` section — each usage line as a `TYPE: command` atom
- `OPTIONS` section — each flag and its description as a `TYPE: parameter` atom
- `DESCRIPTION` section — each behavioral statement as a `TYPE: pattern` or `TYPE: constraint` atom
- `ERRORS` or `EXIT STATUS` sections — each code and meaning as a `TYPE: error` atom
- `ENVIRONMENT` section — each variable as a `TYPE: parameter` atom

**Skip:**

- `SEE ALSO` references
- `AUTHORS` and `BUGS` sections unless they document behavioral constraints
- Repeated header/footer lines injected by `man` rendering

**Example — source man page (after `col -b`):**

```text
SYNOPSIS
    grep [OPTIONS] PATTERN [FILE...]

OPTIONS
    -i       Ignore case distinctions
    -n       Prefix each match with line number
    -r       Read files recursively under each directory
```

**Extracted atoms:**

```text
ATOM: grep command syntax is `grep [OPTIONS] PATTERN [FILE...]`
TYPE: command
SOURCE: grep.1:SYNOPSIS

ATOM: -i flag makes grep ignore case distinctions
TYPE: parameter
SOURCE: grep.1:OPTIONS

ATOM: -n flag prefixes each match line with its line number
TYPE: parameter
SOURCE: grep.1:OPTIONS

ATOM: -r flag reads files recursively under each directory
TYPE: parameter
SOURCE: grep.1:OPTIONS
```

---

### TOML, YAML, and JSON Config Files

**Tool:** Read directly with the Read tool. All three formats are plain text.

**Extract:**

- Each key that has an inline comment (`#` for TOML/YAML, not available in JSON) as a `TYPE: parameter` atom — include key name, value type inferred from the example value, and comment text as the description
- Nested keys — use dot notation in the atom (e.g., `database.host`)
- Each key's default value as part of the atom fact
- Enum-constrained values (where comments list valid options) as `TYPE: constraint` atoms

**Skip:**

- Keys with no comment and no obvious semantic meaning (e.g., generated UUIDs, timestamps)
- Structural nesting markers that carry no semantic meaning on their own
- Commented-out keys — extract only active configuration

**Example — source TOML:**

```toml
[server]
host = "0.0.0.0"       # Bind address; use 127.0.0.1 for localhost-only
port = 8080             # Listening port; must be > 1024 for non-root
workers = 4             # Number of worker processes

[logging]
level = "INFO"          # Verbosity: DEBUG | INFO | WARN | ERROR
```

**Extracted atoms:**

```text
ATOM: server.host sets the bind address; use 127.0.0.1 to restrict to localhost
TYPE: parameter
SOURCE: config.toml:server

ATOM: server.port sets the listening port; must be greater than 1024 for non-root users
TYPE: parameter
SOURCE: config.toml:server

ATOM: server.workers sets the number of worker processes; default 4
TYPE: parameter
SOURCE: config.toml:server

ATOM: logging.level sets verbosity; accepts DEBUG | INFO | WARN | ERROR; default INFO
TYPE: parameter
SOURCE: config.toml:logging
```

---

### Plain Text

**Tool:** Read directly with the Read tool.

**Extract:**

- Lines in ALL CAPS that act as section headings — use as SOURCE section names
- Lines followed by `===` or `---` that act as underline-style headings — use as SOURCE section names
- Each paragraph as a candidate atom — evaluate whether it states a fact, constraint, or pattern
- Lines matching command syntax patterns (starting with `$`, indented uniformly, containing flags) as `TYPE: command` atoms

**Skip:**

- Blank separator lines
- Lines consisting only of punctuation used as visual dividers (`---`, `===`, `***`)
- Repeated boilerplate lines (e.g., license notices copied verbatim into every section)

**Note:** Plain text has no structural markup. Apply heuristic heading detection first to establish section context before extracting atoms. When no heading structure is detectable, use the filename as the SOURCE section.

**Example — source plain text:**

```text
INSTALLATION
============

Run the installer script as root:

    sudo ./install.sh --prefix /usr/local

The installer writes files to /usr/local/bin and /usr/local/share.
Do not interrupt the installer — partial installs require manual cleanup.
```

**Extracted atoms:**

```text
ATOM: `sudo ./install.sh --prefix /usr/local` installs the package as root
TYPE: command
SOURCE: README.txt:INSTALLATION

ATOM: installer writes files to /usr/local/bin and /usr/local/share
TYPE: pattern
SOURCE: README.txt:INSTALLATION

ATOM: interrupting the installer leaves a partial install requiring manual cleanup
TYPE: constraint
SOURCE: README.txt:INSTALLATION
```

---

## What to Preserve Verbatim

These categories must be copied character-for-character into reference files:

| Category | Reason |
|----------|--------|
| CLI flag names and syntax | Flags are identifiers — paraphrasing causes wrong invocations |
| Parameter names and types | Type names are formal specifications |
| Enum values | Any deviation causes runtime errors |
| Error messages | Error strings are used for pattern matching |
| Code examples | Rewriting introduces bugs |
| Configuration key names | Keys must match exactly |
| File format syntax | Format specs are normative |

---

## What to Abstract

These categories should be distilled, not copied verbatim:

| Category | Abstraction approach |
|----------|---------------------|
| Narrative introductions | Drop entirely — extract only the technical claim |
| Step-by-step prose | Convert to `ATOM: do X to achieve Y` |
| Analogies | Extract the constraint the analogy illustrates |
| Repetitive examples | Extract one canonical example; note that others exist |
| Version history | Extract only if current behavior differs from prior |
| FAQ sections | Treat each Q/A pair as a constraint atom |

---

## Anti-Patterns

**Summarizing code instead of copying it:**

```text
# WRONG
ATOM: Run the check command with appropriate flags
TYPE: command

# CORRECT
ATOM: `ty check --strict --format json ./src` runs strict checking with JSON output
TYPE: command
SOURCE: docs/quickstart.md:Running checks
```

**Merging multiple constraints into one atom:**

```text
# WRONG
ATOM: The config file must be named ty.toml and placed in the project root and must include the python-version field
TYPE: constraint

# CORRECT — three separate atoms
ATOM: Config file must be named ty.toml
TYPE: constraint
SOURCE: docs/configuration.md:Config file location

ATOM: Config file must be placed in the project root
TYPE: constraint
SOURCE: docs/configuration.md:Config file location

ATOM: Config file must include the python-version field
TYPE: constraint
SOURCE: docs/configuration.md:Required fields
```

**Extracting motivational framing as knowledge:**

```text
# WRONG
ATOM: ty is a fast Python type checker designed for modern workflows
TYPE: pattern

# CORRECT — skip marketing copy; extract the technical fact
ATOM: ty checks Python type annotations without running the code
TYPE: pattern
SOURCE: docs/overview.md:What ty does
```

**Paraphrasing error messages:**

```text
# WRONG
ATOM: ty reports an error when the config file is missing
TYPE: error

# CORRECT — copy the exact message
ATOM: ty emits "error: no ty.toml found in current directory or any parent directory" when no config file exists
TYPE: error
SOURCE: docs/errors.md:Configuration errors
```
