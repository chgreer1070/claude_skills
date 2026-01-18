# toml-python

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Claude Code plugin for working with TOML configuration files in Python using tomlkit, which preserves comments and formatting during read-modify-write cycles.

## Features

- **Comment-Preserving Editing** - Modify TOML files without losing user comments or formatting
- **Comprehensive API Guidance** - Complete tomlkit API reference with examples
- **Production Patterns** - Atomic updates, validation, error handling best practices
- **Library Selection** - Clear guidance on tomlkit vs tomllib (stdlib)
- **XDG Integration** - Config file location standards
- **Type Safety** - TOML to Python type mappings and dataclass patterns

## Installation

### Prerequisites

- Claude Code 2.1 or later
- Python 3.8+ (for tomlkit usage)

### Install Plugin

```bash
# Method 1: Using Claude Code CLI
cc plugin install toml-python

# Method 2: Manual installation
git clone <repository-url> ~/.claude/plugins/toml-python
cc plugin reload
```

## Quick Start

```python
import tomlkit
from pathlib import Path

# Load or create config
config_path = Path.home() / '.config' / 'myapp' / 'config.toml'

if config_path.exists():
    with open(config_path, 'r') as f:
        doc = tomlkit.load(f)
else:
    doc = tomlkit.document()
    doc.add(tomlkit.comment("Application configuration"))
    doc.add(tomlkit.nl())

# Modify while preserving comments
doc.setdefault('app', tomlkit.table())
doc['app']['name'] = 'myapp'
doc['app']['version'] = '1.0.0'

# Save atomically
config_path.parent.mkdir(parents=True, exist_ok=True)
with open(config_path, 'w') as f:
    tomlkit.dump(doc, f)
```

## Capabilities

The plugin provides one skill that is automatically activated by Claude when working with TOML files in Python:

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | toml-python | Read/write TOML config files with comment preservation using tomlkit | Automatic when keywords detected |

**Trigger Keywords:** pyproject.toml, .toml files, tomlkit, tomllib, config files, atomic updates

## Usage

### When the Skill Activates

Claude automatically applies this skill when you:

- Read or write `pyproject.toml` or other `.toml` configuration files
- Edit TOML files while preserving comments and formatting
- Design configuration file formats for Python tools
- Work with code using `tomlkit` or `tomllib`
- Implement atomic config file updates
- Mention TOML, pyproject.toml, or configuration management

### What the Skill Provides

**Library Selection Guidance:**

- Use **tomlkit** for reading AND writing with comment preservation
- Use **tomllib** (stdlib, Python 3.11+) for read-only access with minimal dependencies

**API Reference:**

- Complete tomlkit API (parse, load, dump, write)
- Document creation and manipulation methods
- Error handling with exception types
- Type conversion helpers

**Production Patterns:**

- Load-or-create config pattern
- Single value updates preserving comments
- Atomic file updates preventing corruption
- Config validation with error messages

**Integration Patterns:**

- XDG Base Directory specification for config locations
- Dataclass integration for type-safe configs
- TOML syntax and type mappings

### Manual Invocation

```text
@toml-python
```

or

```text
Skill(command: "toml-python")
```

## Examples

### Example 1: Update Config Value Preserving Comments

**Scenario:** User has a config file with comments and wants to change one value without losing documentation.

**Code:**

```python
import tomlkit

def update_config_value(path: str, section: str, key: str, value):
    """Update single value while preserving all comments."""
    with open(path, 'r') as f:
        doc = tomlkit.load(f)

    if section not in doc:
        doc[section] = tomlkit.table()

    doc[section][key] = value

    with open(path, 'w') as f:
        tomlkit.dump(doc, f)

# Usage
update_config_value('config.toml', 'database', 'port', 5433)
```

**Result:** Only the database port changes; all comments, formatting, and other values remain identical.

---

### Example 2: Atomic Config Updates

**Scenario:** Production application needs to update config without risking corruption from crashes or failures.

**Code:**

```python
import tomlkit
from pathlib import Path
import tempfile
import shutil

def atomic_config_update(path: Path, updates: dict):
    """Update config atomically to prevent corruption."""
    with open(path, 'r') as f:
        doc = tomlkit.load(f)

    # Apply updates
    for section, values in updates.items():
        if section not in doc:
            doc[section] = tomlkit.table()
        for key, value in values.items():
            doc[section][key] = value

    # Write to temp file, then atomic move
    temp_fd, temp_path = tempfile.mkstemp(suffix='.toml')
    try:
        with open(temp_fd, 'w') as f:
            tomlkit.dump(doc, f)
        shutil.move(temp_path, path)
    except Exception:
        Path(temp_path).unlink(missing_ok=True)
        raise

# Usage
atomic_config_update(
    Path('config.toml'),
    {
        'database': {'host': 'db.example.com', 'port': 5432},
        'features': {'enable_api': True}
    }
)
```

**Result:** Config is updated atomically. If any error occurs, original file remains unchanged.

---

### Example 3: Config Validation

**Scenario:** Validate that a TOML config file has required structure before using it.

**Code:**

```python
import tomlkit
from tomlkit.exceptions import ParseError

def validate_config(path: str) -> tuple[bool, str]:
    """Validate config structure. Returns (is_valid, error_message)."""
    try:
        with open(path, 'r') as f:
            doc = tomlkit.load(f)
    except FileNotFoundError:
        return False, "Config file not found"
    except ParseError as e:
        return False, f"Invalid TOML at line {e.line}, col {e.col}"

    required_sections = ['app', 'database']
    missing = [s for s in required_sections if s not in doc]

    if missing:
        return False, f"Missing sections: {', '.join(missing)}"

    if 'name' not in doc.get('app', {}):
        return False, "Missing required key: app.name"

    return True, ""

# Usage
is_valid, error = validate_config('config.toml')
if not is_valid:
    print(f"Config validation failed: {error}")
    exit(1)
```

**Result:** Clear error messages identify missing sections, invalid syntax, or required keys.

---

### Example 4: Dataclass Integration

**Scenario:** Use type-safe dataclasses to represent config while preserving TOML comments.

**Code:**

```python
from dataclasses import dataclass
import tomlkit
from pathlib import Path

@dataclass
class AppConfig:
    name: str
    version: str
    debug: bool = False

@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    pool_size: int = 10

@dataclass
class Config:
    app: AppConfig
    database: DatabaseConfig

def load_config(path: Path) -> Config:
    """Load TOML config into dataclasses."""
    with open(path, 'r') as f:
        data = tomlkit.load(f)

    return Config(
        app=AppConfig(**data.get('app', {})),
        database=DatabaseConfig(**data.get('database', {})),
    )

def save_config(config: Config, path: Path):
    """Save dataclasses to TOML, preserving existing comments."""
    if path.exists():
        with open(path, 'r') as f:
            doc = tomlkit.load(f)
    else:
        doc = tomlkit.document()

    # Update from dataclasses
    if 'app' not in doc:
        doc['app'] = tomlkit.table()
    doc['app']['name'] = config.app.name
    doc['app']['version'] = config.app.version
    doc['app']['debug'] = config.app.debug

    if 'database' not in doc:
        doc['database'] = tomlkit.table()
    doc['database']['host'] = config.database.host
    doc['database']['port'] = config.database.port
    doc['database']['name'] = config.database.name
    doc['database']['pool_size'] = config.database.pool_size

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        tomlkit.dump(doc, f)

# Usage
config = load_config(Path('config.toml'))
config.database.port = 5433  # Type-safe modification
save_config(config, Path('config.toml'))  # Comments preserved
```

**Result:** Type-safe config access with IDE autocomplete, while preserving all TOML comments and formatting.

---

### Example 5: Load or Create Default Config

**Scenario:** Application needs config file; create sensible defaults if missing.

**Code:**

```python
import tomlkit
from pathlib import Path

def load_or_create_config(path: Path) -> tomlkit.TOMLDocument:
    """Load existing config or create default if missing."""
    if path.exists():
        with open(path, 'r') as f:
            return tomlkit.load(f)

    # Create default
    doc = tomlkit.document()
    doc.add(tomlkit.comment("Default configuration"))
    doc.add(tomlkit.nl())

    doc["app"] = tomlkit.table()
    doc["app"]["name"] = "myapp"
    doc["app"]["version"] = "1.0.0"
    doc["app"]["debug"] = False

    doc.add(tomlkit.nl())
    doc["database"] = tomlkit.table()
    doc["database"]["host"] = "localhost"
    doc["database"]["port"] = 5432
    doc["database"]["name"] = "myapp_db"

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        tomlkit.dump(doc, f)

    return doc

# Usage with XDG-compliant path
config_path = Path.home() / '.config' / 'myapp' / 'config.toml'
config = load_or_create_config(config_path)
```

**Result:** First run creates `~/.config/myapp/config.toml` with sensible defaults. Subsequent runs load existing config.

## Troubleshooting

### Issue: Comments Disappear After Modification

**Cause:** Using `doc.unwrap()` converts to plain Python dict, losing tomlkit metadata.

**Solution:** Modify the `TOMLDocument` directly, never unwrap before saving:

```python
# ❌ Wrong
doc = tomlkit.load(f)
pure_dict = doc.unwrap()
pure_dict['key'] = 'value'  # Comments lost
tomlkit.dump(pure_dict, f)

# ✅ Correct
doc = tomlkit.load(f)
doc['key'] = 'value'  # Comments preserved
tomlkit.dump(doc, f)
```

### Issue: KeyError When Accessing Config Values

**Cause:** Accessing keys that don't exist without checking.

**Solution:** Use `.get()` with defaults or check existence first:

```python
# ❌ Wrong
value = doc['section']['key']  # KeyError if missing

# ✅ Correct
value = doc.get('section', {}).get('key', 'default')

# Or check explicitly
if 'section' in doc and 'key' in doc['section']:
    value = doc['section']['key']
```

### Issue: ParseError on Valid TOML

**Cause:** File encoding issues or BOM characters.

**Solution:** Open files with explicit UTF-8 encoding:

```python
with open(path, 'r', encoding='utf-8') as f:
    doc = tomlkit.load(f)
```

### Issue: Type Mismatches (String vs Integer)

**Cause:** TOML types may not match Python expectations.

**Solution:** Validate types after loading:

```python
port = doc['database']['port']
if not isinstance(port, int):
    raise ValueError(f"Expected int for port, got {type(port)}")
```

### Issue: Config Corruption After Crash

**Cause:** Writing directly to config file without atomic operations.

**Solution:** Use the atomic update pattern (Example 2 above) to write to temp file and move atomically.

## Library Selection: tomlkit vs tomllib

### Use tomlkit when:

- Modifying existing config files (preserves comments and formatting)
- Building applications that write configuration
- Need single library for both reading and writing
- Python 3.8+ compatibility required

### Use tomllib when:

- Python 3.11+ only
- Read-only access sufficient (no writing capability)
- Minimal dependencies preferred
- Part of standard library

**Recommendation:** For config file management, tomlkit is the recommended choice.

## Related Skills

- **xdg-base-directory** - XDG-compliant config file locations
- **python3-development** - Python development patterns and best practices
- **uv** - Modern Python dependency management

## References

- [tomlkit Documentation](https://tomlkit.readthedocs.io/) - Complete API reference
- [tomlkit PyPI](https://pypi.org/project/tomlkit/) - Package information
- [tomlkit GitHub](https://github.com/sdispater/tomlkit) - Source code
- [TOML Specification](https://toml.io/en/) - TOML v1.0.0 specification
- [Python tomllib](https://docs.python.org/3.11/library/tomllib.html) - Stdlib alternative (read-only)

## License

MIT

## Contributing

This plugin is part of the Claude Skills repository. Contributions are welcome through pull requests.
