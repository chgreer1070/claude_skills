# Backlog Core Parsing Patterns and Architecture

**Analysis date**: 2026-03-21
**Codebase location**: `.worktrees/pr-483/.claude/skills/backlog/backlog_core/`
**Scope**: Data flow from disk → Pydantic models → MCP response, entry block format, section handling, GitHub sync format.

---

## 1. Data Flow: Item Disk → Pydantic Model → MCP Response

### 1.1 Call Chain Overview

```
Per-item file (.claude/backlog/{priority}-{slug}.md)
    ↓
parse_item_file(text: str, path: Path) → BacklogItem
    ↓
BacklogItem (Pydantic model instance)
    ↓
operations.*() functions (add_item, list_items, view_item, etc.)
    ↓
server.py MCP tools (@mcp.tool())
    ↓
MCP response dict (messages, warnings, errors, data)
```

### 1.2 Stage 1: Load from Disk → parse_item_file()

**Location**: `.claude/skills/backlog/backlog_core/parsing.py`

**Function signature**:
```python
def parse_item_file(text: str, path: Path) -> BacklogItem:
    """Parse a single per-item backlog file (frontmatter + body).

    Handles both flat and research-style metadata blocks.
    Returns BacklogItem with parsed fields from frontmatter and body.
    """
```

**Input**: Raw file text (markdown with YAML frontmatter)

**Processing**:
1. Check for frontmatter delimiter `---` at start
   - If missing: return empty BacklogItem with raw_body set
   - If present: extract frontmatter via `_parse_frontmatter(text)`

2. Frontmatter extraction:
   - Uses `loads_frontmatter()` from `frontmatter_utils`
   - Returns tuple: `(fm, meta, body)`
     - `fm`: PyYAML dict of parsed YAML
     - `meta`: dict representation (PyYAML internal)
     - `body`: markdown body after frontmatter

3. Field resolution (research-style priority):
   - Read `name`, `description`, `metadata.*` from frontmatter
   - Fall back to flat format: `title`, `source`, `added`, `priority`, `item_type`, `status`, `issue`, `plan`, `files`, `suggested_location`, `research_first`, `groomed`
   - Merge helper `_fm_str(fm, meta, field)` safely extracts values from nested dicts

4. Special field handling:
   - `groomed`: if not in frontmatter, scan body for `## Groomed` section marker
   - `plan`: stored as string path or issue reference
   - `last_synced`: timestamp of last GitHub sync operation

**Output**: `BacklogItem` Pydantic model with all fields populated

---

### 1.3 Stage 2: BacklogItem → Operations Functions

**Module**: `.claude/skills/backlog/backlog_core/operations.py`

**Pattern**: Operations functions accept `BacklogItem` instances and return `dict` or `list[BacklogItem]`:

```python
def add_item(
    title: str,
    priority: str,
    description: str,
    source: str = "Not specified",
    type_val: str = "Feature",
    output: Output | None = None,
) -> dict[str, Any]:
    """Create a new backlog item.

    1. Validate inputs (priority, type)
    2. Check for fuzzy duplicates
    3. Build BacklogItem instance
    4. Write to .claude/backlog/{priority}-{slug}.md
    5. Create GitHub issue (if not force-skipped)
    6. Return dict: {title, priority, issue, file_path, messages, warnings}
    """
```

**Typical operation flow**:
1. Validate inputs
2. Call parsing functions to build BacklogItem or find existing items
3. Perform file I/O (write, edit, delete)
4. Call github functions to sync/create/close issues
5. Populate Output object with status messages
6. Return dict with result data

**Critical property**: Functions do NOT directly use typer for output. Instead:
- Accept optional `output: Output` parameter
- Call `output.info()`, `output.warn()`, `output.error()` to record messages
- Return dict with `messages`, `warnings`, `errors` keys (via `output.to_dict()`)

---

### 1.4 Stage 3: Dict → MCP Response

**Module**: `.claude/skills/backlog/backlog_core/server.py`

**Pattern**: FastMCP 3.x tools wrap operations functions:

```python
@mcp.tool()
def backlog_add(
    title: str,
    priority: str,
    description: str,
    source: str = "Not specified",
    type_val: str = "Feature",
) -> dict[str, Any]:
    """Add a new backlog item."""
    output = Output()
    try:
        result = operations.add_item(title, priority, description, source, type_val, output)
        return {
            **result,
            **output.to_dict(),
        }
    except ItemNotFoundError as e:
        return {"error": str(e), **output.to_dict()}
    except DuplicateItemError as e:
        return {"error": str(e), "duplicates": e.duplicates, **output.to_dict()}
```

**Key properties**:
- Creates local `Output()` instance per tool call
- Calls operation function with output parameter
- Merges result dict with output.messages/warnings/errors
- Catches all `BacklogError` subclasses and converts to error responses
- Returns merged dict as MCP response

---

## 2. Entry Block Format

### 2.1 Data Structure

Entry blocks are HTML `<div>` containers with an ISO-8601 timestamp in a `<sub>` tag:

```html
<div><sub>2026-03-15T14:30:45Z</sub>

Markdown content here.
</div>
```

### 2.2 Struck Entry (Retracted/Superseded)

When an entry is struck, it is wrapped in a `<details><summary>` block preserving the original content:

```html
<div><sub>2026-03-15T14:30:45Z</sub>
<details><summary>struck: 2026-03-15T15:00:00Z — superseded by new analysis</summary>

Original content preserved here.
</details>
</div>
```

**Format**: `struck: {timestamp} — {reason}`

### 2.3 Entry ID Assignment

**Entry ID** = the ISO-8601 timestamp from the `<sub>` tag.

**Duplicate timestamp handling**: If two entries have the same timestamp (at parse time), assign suffixes `-0`, `-1`, etc. in document order. No pre-check at write time.

**Regex pattern**: `<div><sub>([^<]+)</sub>` extracts the entry ID (timestamp string).

### 2.4 Legacy Migration

On first append to a section containing unwrapped plaintext:

1. Use the item's `added` date as the base: `{added}T00:00:00Z`
2. Wrap existing text: `<div><sub>{added}T00:00:00Z</sub>\n\n{text}\n</div>`
3. Append new entry with current timestamp

**Result**: Old content becomes an entry block, new content is a fresh entry.

---

## 3. Section Handling

### 3.1 Section Identification

Sections are identified by `##` markdown headers within the body:

```python
# Regex pattern
SECTION_RE = re.compile(r"^##\s+(P0|P1|P2|Ideas)")
```

**Valid section names**: `P0`, `P1`, `P2`, `Ideas`

**Map to full headers**: (from `models.py`)
```python
PRIORITY_SECTIONS: dict[str, str] = {
    "P0": "## P0 - Must Have",
    "P1": "## P1 - Should Have",
    "P2": "## P2 - Could Have",
    "Idea": "## Ideas",
    "Ideas": "## Ideas",
}
```

### 3.2 Section Extraction: extract_sections()

**Location**: `parsing.py`

**Signature**:
```python
def extract_sections(body: str) -> dict[str, str]:
    """Extract all sections from a body string.

    Returns dict mapping section name → raw section content (from header to next ## or EOF).
    """
```

**Process**:
1. Split body by `##` markers
2. For each section, extract header line (e.g., "## P0 - Must Have")
3. Identify priority from header using SECTION_RE
4. Return dict: `{"P0": "## P0 - Must Have\n...", "P1": "...", ...}`

### 3.3 Section Appending/Replacing: append_or_replace_section()

**Signature**:
```python
def append_or_replace_section(
    body: str,
    section_name: str,
    new_content: str,
    replace: bool = False,
) -> str:
    """Append new content to a section, or replace all content if replace=True.

    For append: wraps new_content in entry block.
    For replace: strikes all existing entries, appends new entry.
    """
```

**Append flow**:
1. Find or create section header in body
2. If section exists:
   - Check for existing entry blocks (legacy migration if needed)
   - Wrap `new_content` in `<div><sub>{timestamp}</sub>\n\n{content}\n</div>`
   - Append to section
3. If section doesn't exist:
   - Add section header at appropriate priority position
   - Append entry block with new content

**Replace flow**:
1. Extract all entries from existing section
2. Strike each entry with reason (e.g., "replaced")
3. Append new entry with fresh timestamp

### 3.4 Section Reconstruction: reconstruct_body_from_sections()

**Signature**:
```python
def reconstruct_body_from_sections(body: str, updated_sections: dict[str, str]) -> str:
    """Rebuild body by merging updated sections back into original body.

    Preserves sections not in updated_sections dict.
    """
```

**Process**:
1. Start with original body
2. For each key in updated_sections:
   - Find original section in body
   - Replace with updated_sections[key]
3. For missing sections:
   - Add section at appropriate priority position
4. Return reconstructed body

---

## 4. GitHub Sync Format

### 4.1 Issue Body Building: build_issue_body()

**Location**: `parsing.py`

**Signature**:
```python
def build_issue_body(item: BacklogItem) -> str:
    """Build a GitHub issue body from a BacklogItem.

    Constructs frontmatter section + all body sections.
    """
```

**Structure**:

```markdown
<!-- Frontmatter as YAML inside HTML comment -->
<!-- metadata:
field1: value1
field2: value2
-->

## P0 - Must Have
<!-- Entry blocks go here -->

## Groomed
<!-- Groomed content and analysis -->
```

### 4.2 Issue Body → Local File: Pulled Data Merge

**Function**: `pull_items()` and sub-functions in `operations.py`

**Flow**:
1. Fetch issue body from GitHub
2. Parse sections from body
3. For each section:
   - **Entry-aware merge**: Keep longer entries (prefer GitHub if longer, local if longer)
   - Preserve struck entries (don't lose retraction history)
4. Write merged body back to local item file

**Entry comparison**: Entry block lengths compared, longer one wins.

### 4.3 Groomed Sync: sync_groomed_to_github_issue()

**Location**: `github.py`

**Signature**:
```python
def sync_groomed_to_github_issue(
    item: BacklogItem,
    output: Output | None = None,
) -> bool:
    """Update GitHub issue with latest groomed content from local file.

    Returns True if updated, False if no change.
    """
```

**Process**:
1. Read local item file
2. Extract groomed section from body
3. Find `## Groomed` in GitHub issue body
4. Replace/append groomed section
5. Post updated body to GitHub
6. Update item's `last_synced` timestamp

---

## 5. Field Mapping and Metadata

### 5.1 Field Index Map

From `models.py`:

```python
_FIELD_TO_INDEX: dict[str, int] = {
    "description": 0,
    "suggested location": 1,
    "research first": 2,
    "decision needed": 3,
    "files": 4,
    "required work": 5,
}
```

**Usage**: When parsing body "extra fields" (flat metadata format), map field name → index for validation.

### 5.2 Frontmatter Building: build_backlog_frontmatter()

**Signature**:
```python
def build_backlog_frontmatter(
    title: str,
    description: str,
    source: str,
    added: str,
    priority: str,
    item_type: str,
    status: str,
    issue: str = "",
    plan: str = "",
    research_first: str = "",
) -> str:
    """Build a complete frontmatter block for a backlog item.

    Returns string with --- delimiters and YAML fields.
    """
```

**Output format** (research-style):

```yaml
---
name: Full Item Title
description: One-sentence summary
metadata:
  source: Where this came from
  added: 2026-03-15
  priority: P1
  type: Feature
  status: open
  issue: "#42"
  plan: plan/tasks-5-feature.md
  research_first: Understand current auth flow
---
```

---

## 6. Test Fixtures and File Format Examples

### 6.1 Test Item Factory: write_test_item()

From `tests/conftest.py`:

```python
@pytest.fixture
def write_test_item(backlog_dir):
    """Factory: create per-item file with valid frontmatter in test backlog_dir.

    Usage:
        filepath = write_test_item("My Title", priority="P0", issue="#42")

    Returns the Path to the created file.
    """
    def _write(
        title: str,
        priority: str = "P1",
        issue: str = "",
        description: str = "Test item",
        status: str = "open",
        type_val: str = "Feature",
    ) -> Path:
        from backlog_core.parsing import build_backlog_frontmatter, title_to_slug

        slug = title_to_slug(title)
        filepath = backlog_dir / f"{priority.lower()}-{slug}.md"
        fm = build_backlog_frontmatter(
            title, description, "test", "2026-01-01", priority, type_val, status, issue, "", ""
        )
        filepath.write_text(fm, encoding="utf-8")
        return filepath

    return _write
```

### 6.2 Filename Convention

Backlog items are stored at: `.claude/backlog/{priority}-{slug}.md`

**Example filenames**:
- `p0-auth-system-refactor.md` (P0 priority)
- `p1-add-sdk-support.md` (P1 priority)
- `p2-performance-tuning.md` (P2 priority)
- `ideas-experimental-feature.md` (Ideas/exploratory)

**Slug generation** (`title_to_slug()`):
- Convert title to lowercase
- Replace non-alphanumeric with hyphens
- Strip leading/trailing hyphens
- Example: "Add SDK Support" → "add-sdk-support"

---

## 7. Pydantic Models

### 7.1 BacklogItem

From `models.py`:

```python
class BacklogItem(BaseModel):
    """Parsed backlog item from a per-item file."""
    title: str = ""
    description: str = ""
    source: str = "Not specified"
    added: str = ""
    priority: str = ""
    item_type: str = "Feature"
    issue: str = ""  # "#N" or empty
    plan: str = ""   # file path or empty
    research_first: str = ""
    files: str = ""
    suggested_location: str = ""
    section: str = ""  # "P0", "P1", "P2", "Ideas"
    file_path: str = ""  # absolute path
    skip: bool = False
    groomed: str = ""  # "true", "false", or empty
    last_synced: str = ""  # ISO timestamp
    raw_body: str = ""  # unparsed body if no frontmatter
```

**All fields default to empty/falsy** so items can be constructed incrementally during parsing.

### 7.2 Output

```python
class Output(BaseModel):
    """Structured output collector replacing direct typer.echo() calls."""
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def info(self, msg: str) -> None:
        """Record an informational message."""
        self.messages.append(msg)

    def warn(self, msg: str) -> None:
        """Record a warning message."""
        self.warnings.append(msg)

    def error(self, msg: str) -> None:
        """Record an error message."""
        self.errors.append(msg)

    def to_dict(self) -> dict[str, list[str]]:
        """Return all collected messages as a dict."""
        return self.model_dump()
```

### 7.3 Other Models

- **IssueStatus**: `status` (string) + `milestone` (string)
- **PullRequestRef**: `number` (int), `title` (str), `url` (str)
- **ViewItemResult**: Extended BacklogItem with GitHub data (number, state, body, labels, milestone)
- **IssueLocalFields**: Fields extracted from PyGithub Issue object (title, body, priority, item_type, status, updated_at, milestone)
- **SamTask**: SAM task metadata from `<!-- sam:task ... -->` comment blocks (task_id, feature, task_type, status, agent, priority, skills, dependencies)

---

## 8. Module Dependency Graph

```
models.py
  ├─ Constants: BACKLOG_DIR, SECTION_RE, GITHUB_ISSUE_URL_RE, etc.
  ├─ Exceptions: BacklogError, ItemNotFoundError, DuplicateItemError, etc.
  └─ Pydantic models: BacklogItem, Output, IssueStatus, etc.

parsing.py
  ├─ imports: models
  ├─ imports: frontmatter_utils (from plugin-creator/scripts)
  └─ functions: parse_item_file, extract_sections, append_or_replace_section, etc.

github.py
  ├─ imports: models, parsing
  └─ functions: get_github, create_issue_for_item, fetch_github_issue_body, etc.

operations.py
  ├─ imports: models, parsing, github
  └─ functions: add_item, list_items, view_item, sync_items, close_item, etc.

server.py
  ├─ imports: models, operations
  ├─ FastMCP instance: mcp = FastMCP("backlog")
  └─ tools: @mcp.tool() decorated functions

backlog.py (CLI wrapper)
  ├─ imports: operations, models
  ├─ Typer app: app = Typer()
  └─ commands: add, list, view, sync, close, resolve, update, groom, normalize, pull
```

**Critical constraint**: No circular imports. Models is isolated. Parsing depends only on models. GitHub depends on models+parsing. Operations orchestrates all three.

---

## 9. Summary of Key Patterns

| Pattern | Location | Example |
|---------|----------|---------|
| **Per-item file** | `.claude/backlog/{priority}-{slug}.md` | `p0-auth-refactor.md` |
| **Entry block** | HTML `<div><sub>ISO-timestamp</sub>` container | `<div><sub>2026-03-15T14:30:45Z</sub>\n\nContent</div>` |
| **Struck entry** | `<details><summary>struck: timestamp — reason</summary>` | Retracted entries wrapped in collapsible block |
| **Section header** | Markdown `## Priority` | `## P0 - Must Have` |
| **Frontmatter** | YAML with research-style metadata | `name`, `description`, `metadata.*` fields |
| **Field mapping** | `_FIELD_TO_INDEX` dict | Maps field name to index for validation |
| **Slug generation** | `title_to_slug()` | "Add SDK Support" → "add-sdk-support" |
| **GitHub sync** | Issue body = frontmatter + sections | Pull merges GitHub body into local file |
| **Output handling** | Operations accept `output: Output` parameter | Messages collected in Output object, not echoed directly |
| **Error handling** | Raise `BacklogError` subclasses | Operations throw, server catches and converts to error response |

---

## References

- **Architecture spec**: `.claude/skills/backlog/backlog_core/ARCHITECTURE.md`
- **Pydantic models**: `.claude/skills/backlog/backlog_core/models.py` (lines 129-264)
- **Parsing functions**: `.claude/skills/backlog/backlog_core/parsing.py`
- **Operations CRUD**: `.claude/skills/backlog/backlog_core/operations.py`
- **GitHub integration**: `.claude/skills/backlog/backlog_core/github.py`
- **MCP server**: `.claude/skills/backlog/backlog_core/server.py`
- **Test fixtures**: `.claude/skills/backlog/tests/conftest.py`
- **Entry block spec**: `docs/superpowers/specs/2026-03-10-backlog-mcp-timestamped-entry-blocks-design.md`
