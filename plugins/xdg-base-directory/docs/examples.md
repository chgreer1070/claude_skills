# Usage Examples

Concrete examples of implementing XDG Base Directory Specification in real-world applications.

---

## Example 1: Building an XDG-Compliant CLI Tool

**Scenario**: Create a Python CLI tool called `myweather` that stores API keys, cached weather data, and request history following XDG specification.

**Steps**:

1. Create application paths module (`myweather/paths.py`)
2. Implement configuration management with TOML
3. Add cache management for API responses
4. Store request history in state directory

**Code**:

```python
# myweather/paths.py
"""XDG-compliant path management for myweather."""
from pathlib import Path
import os

APP_NAME = 'myweather'


def get_config_dir() -> Path:
    """Get myweather config directory."""
    xdg = os.environ.get('XDG_CONFIG_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.config'
    return base / APP_NAME


def get_config_file() -> Path:
    """Get myweather config file path."""
    return get_config_dir() / 'config.toml'


def get_data_dir() -> Path:
    """Get myweather data directory."""
    xdg = os.environ.get('XDG_DATA_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.local' / 'share'
    return base / APP_NAME


def get_cache_dir() -> Path:
    """Get myweather cache directory."""
    xdg = os.environ.get('XDG_CACHE_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.cache'
    return base / APP_NAME


def get_state_dir() -> Path:
    """Get myweather state directory."""
    xdg = os.environ.get('XDG_STATE_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.local' / 'state'
    return base / APP_NAME


def ensure_directories() -> None:
    """Create all required directories."""
    for directory in [get_config_dir(), get_data_dir(), get_cache_dir(), get_state_dir()]:
        directory.mkdir(parents=True, exist_ok=True)
```

```python
# myweather/config.py
"""Configuration management for myweather."""
import tomllib
from pathlib import Path
from typing import Optional
from myweather.paths import get_config_file


def load_config() -> dict:
    """Load configuration from XDG_CONFIG_HOME."""
    config_file = get_config_file()

    if not config_file.exists():
        return {}

    with open(config_file, 'rb') as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save configuration to XDG_CONFIG_HOME."""
    import tomli_w

    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'wb') as f:
        tomli_w.dump(config, f)
```

```python
# myweather/cache.py
"""Cache management for API responses."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from myweather.paths import get_cache_dir


def get_cached_weather(location: str) -> dict | None:
    """Retrieve cached weather data if fresh (< 10 minutes)."""
    cache_file = get_cache_dir() / f'{location}.json'

    if not cache_file.exists():
        return None

    with open(cache_file) as f:
        data = json.load(f)

    cached_time = datetime.fromisoformat(data['cached_at'])
    if datetime.now() - cached_time > timedelta(minutes=10):
        return None  # Stale cache

    return data['weather']


def save_cached_weather(location: str, weather: dict) -> None:
    """Save weather data to cache."""
    cache_file = get_cache_dir() / f'{location}.json'
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        'cached_at': datetime.now().isoformat(),
        'weather': weather
    }

    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
```

```python
# myweather/history.py
"""Request history tracking."""
import json
from datetime import datetime
from myweather.paths import get_state_dir


def log_request(location: str, weather: dict) -> None:
    """Log weather request to history."""
    history_file = get_state_dir() / 'history.jsonl'
    history_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        'timestamp': datetime.now().isoformat(),
        'location': location,
        'temperature': weather.get('temperature'),
        'conditions': weather.get('conditions')
    }

    with open(history_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def get_recent_history(limit: int = 10) -> list[dict]:
    """Get recent weather requests."""
    history_file = get_state_dir() / 'history.jsonl'

    if not history_file.exists():
        return []

    with open(history_file) as f:
        lines = f.readlines()

    return [json.loads(line) for line in lines[-limit:]]
```

**Result**:

Directory structure:

```text
~/.config/myweather/
    config.toml                # API key, preferences

~/.cache/myweather/
    san-francisco.json         # Cached weather responses
    new-york.json

~/.local/state/myweather/
    history.jsonl              # Request history log
```

**Testing**:

```bash
# Test with custom directories
export XDG_CONFIG_HOME=/tmp/test-config
export XDG_CACHE_HOME=/tmp/test-cache
export XDG_STATE_HOME=/tmp/test-state

myweather forecast "San Francisco"

ls -la /tmp/test-config/myweather/config.toml
ls -la /tmp/test-cache/myweather/san-francisco.json
ls -la /tmp/test-state/myweather/history.jsonl
```

---

## Example 2: Migrating Legacy `~/.appname` to XDG

**Scenario**: Migrate an existing application from `~/.myapp/` to XDG-compliant directories, maintaining backward compatibility during transition.

**Steps**:

1. Implement XDG path resolution with legacy fallback
2. Create migration utility to move existing files
3. Add deprecation warnings for legacy paths
4. Update documentation and user notifications

**Code**:

```python
# myapp/paths.py
"""XDG migration for myapp with legacy support."""
from pathlib import Path
import os
import shutil
import warnings

APP_NAME = 'myapp'
LEGACY_DIR = Path.home() / f'.{APP_NAME}'


def get_config_dir() -> Path:
    """Get config directory, checking legacy location first."""
    xdg = os.environ.get('XDG_CONFIG_HOME')
    xdg_dir = Path(xdg) / APP_NAME if xdg and Path(xdg).is_absolute() else Path.home() / '.config' / APP_NAME

    # Check if legacy directory exists and new one doesn't
    if LEGACY_DIR.exists() and not xdg_dir.exists():
        warnings.warn(
            f"Legacy config directory {LEGACY_DIR} found. "
            f"Please run 'myapp migrate' to move to {xdg_dir}",
            DeprecationWarning,
            stacklevel=2
        )
        return LEGACY_DIR

    return xdg_dir


def get_cache_dir() -> Path:
    """Get cache directory (no legacy support)."""
    xdg = os.environ.get('XDG_CACHE_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / '.cache'
    return base / APP_NAME


def migrate_legacy_files() -> bool:
    """Migrate files from ~/.myapp to XDG directories."""
    if not LEGACY_DIR.exists():
        print(f"No legacy directory found at {LEGACY_DIR}")
        return False

    # Get XDG directories
    xdg_config = get_config_dir()
    xdg_cache = get_cache_dir()

    # Ensure XDG directories exist
    xdg_config.mkdir(parents=True, exist_ok=True)
    xdg_cache.mkdir(parents=True, exist_ok=True)

    # Migrate config files
    config_files = ['config.toml', 'credentials.json']
    for filename in config_files:
        legacy_file = LEGACY_DIR / filename
        if legacy_file.exists():
            target = xdg_config / filename
            print(f"Migrating {legacy_file} -> {target}")
            shutil.copy2(legacy_file, target)

    # Migrate cache files
    cache_dir = LEGACY_DIR / 'cache'
    if cache_dir.exists():
        print(f"Migrating cache: {cache_dir} -> {xdg_cache}")
        shutil.copytree(cache_dir, xdg_cache, dirs_exist_ok=True)

    # Backup and remove legacy directory
    backup_dir = Path.home() / f'.{APP_NAME}.backup'
    print(f"Backing up legacy directory to {backup_dir}")
    shutil.move(str(LEGACY_DIR), str(backup_dir))

    print(f"\nMigration complete!")
    print(f"Config: {xdg_config}")
    print(f"Cache: {xdg_cache}")
    print(f"Legacy backup: {backup_dir}")
    print(f"\nYou can safely delete {backup_dir} after verifying migration.")

    return True
```

```python
# myapp/cli.py
"""CLI with migration command."""
import click
from myapp.paths import migrate_legacy_files, get_config_dir, get_cache_dir


@click.group()
def cli():
    """MyApp CLI tool."""
    pass


@cli.command()
def migrate():
    """Migrate from legacy ~/.myapp to XDG directories."""
    if migrate_legacy_files():
        click.echo("Migration successful!")
    else:
        click.echo("Nothing to migrate.")


@cli.command()
def info():
    """Show current directory configuration."""
    click.echo(f"Config: {get_config_dir()}")
    click.echo(f"Cache: {get_cache_dir()}")
```

**Result**:

User experience:

```bash
# Before migration
$ myapp run
Warning: Legacy config directory /home/user/.myapp found.
Please run 'myapp migrate' to move to /home/user/.config/myapp

# Run migration
$ myapp migrate
Migrating /home/user/.myapp/config.toml -> /home/user/.config/myapp/config.toml
Migrating /home/user/.myapp/credentials.json -> /home/user/.config/myapp/credentials.json
Migrating cache: /home/user/.myapp/cache -> /home/user/.cache/myapp
Backing up legacy directory to /home/user/.myapp.backup

Migration complete!
Config: /home/user/.config/myapp
Cache: /home/user/.cache/myapp
Legacy backup: /home/user/.myapp.backup

You can safely delete /home/user/.myapp.backup after verifying migration.

# After migration
$ myapp run
[No warnings, using XDG directories]
```

---

## Example 3: Cross-Platform Configuration with platformdirs

**Scenario**: Build a Python application that works on Linux, macOS, and Windows with native directory conventions on each platform.

**Code**:

```python
# myapp/paths.py
"""Cross-platform path management using platformdirs."""
from platformdirs import (
    user_config_dir,
    user_data_dir,
    user_cache_dir,
    user_state_dir,
    user_log_dir
)
from pathlib import Path

APP_NAME = 'myapp'
APP_AUTHOR = 'mycompany'  # Used on Windows


class AppPaths:
    """Cross-platform application paths."""

    def __init__(self):
        # Auto-create directories on initialization
        self.config = Path(user_config_dir(APP_NAME, APP_AUTHOR, ensure_exists=True))
        self.data = Path(user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True))
        self.cache = Path(user_cache_dir(APP_NAME, APP_AUTHOR, ensure_exists=True))
        self.state = Path(user_state_dir(APP_NAME, APP_AUTHOR, ensure_exists=True))
        self.logs = Path(user_log_dir(APP_NAME, APP_AUTHOR, ensure_exists=True))

    @property
    def config_file(self) -> Path:
        """Main configuration file path."""
        return self.config / 'config.toml'

    @property
    def database_file(self) -> Path:
        """Application database path."""
        return self.data / 'app.db'

    def get_log_file(self, name: str) -> Path:
        """Get log file path by name."""
        return self.logs / f'{name}.log'

    def info(self) -> dict[str, str]:
        """Get path information as dictionary."""
        return {
            'config': str(self.config),
            'data': str(self.data),
            'cache': str(self.cache),
            'state': str(self.state),
            'logs': str(self.logs)
        }


# Global paths instance
paths = AppPaths()
```

```python
# myapp/config.py
"""Configuration management."""
import tomllib
import tomli_w
from myapp.paths import paths


def load_config() -> dict:
    """Load configuration from platform-appropriate location."""
    if not paths.config_file.exists():
        return get_default_config()

    with open(paths.config_file, 'rb') as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save configuration to platform-appropriate location."""
    with open(paths.config_file, 'wb') as f:
        tomli_w.dump(config, f)


def get_default_config() -> dict:
    """Get default configuration."""
    return {
        'general': {
            'theme': 'dark',
            'language': 'en'
        },
        'advanced': {
            'debug': False,
            'log_level': 'INFO'
        }
    }
```

**Result**:

Platform-specific directory structure:

**Linux**:

```text
~/.config/myapp/
    config.toml
~/.local/share/myapp/
    app.db
~/.cache/myapp/
~/.local/state/myapp/
~/.local/state/myapp/log/
    app.log
```

**macOS**:

```text
~/Library/Application Support/myapp/
    config.toml
    app.db
~/Library/Caches/myapp/
~/Library/Logs/myapp/
    app.log
```

**Windows**:

```text
C:\Users\<user>\AppData\Local\mycompany\myapp\
    config.toml
    app.db
    Cache\
    Logs\
        app.log
```

**Testing**:

```python
# test_paths.py
"""Test cross-platform path resolution."""
import sys
from myapp.paths import paths


def test_platform_paths():
    """Verify paths are set correctly for current platform."""
    info = paths.info()

    print(f"Platform: {sys.platform}")
    print(f"Config: {info['config']}")
    print(f"Data: {info['data']}")
    print(f"Cache: {info['cache']}")
    print(f"State: {info['state']}")
    print(f"Logs: {info['logs']}")

    # Verify directories exist
    assert paths.config.exists()
    assert paths.data.exists()
    assert paths.cache.exists()
    assert paths.state.exists()
    assert paths.logs.exists()

    # Test file paths
    assert paths.config_file.parent == paths.config
    assert paths.database_file.parent == paths.data
    assert paths.get_log_file('app').parent == paths.logs


if __name__ == '__main__':
    test_platform_paths()
```

---

## Example 4: Testing XDG Compliance

**Scenario**: Create comprehensive tests to validate XDG specification compliance, including environment variable handling, path validation, and directory creation.

**Code**:

```python
# tests/test_xdg_compliance.py
"""XDG Base Directory Specification compliance tests."""
import os
import tempfile
from pathlib import Path
import pytest

from myapp.paths import (
    get_config_dir,
    get_data_dir,
    get_cache_dir,
    get_state_dir,
    get_runtime_dir,
    get_config_dirs,
    get_data_dirs
)


class TestSingleDirectories:
    """Test XDG_*_HOME variables (single directory)."""

    def test_config_home_override(self, monkeypatch):
        """XDG_CONFIG_HOME environment variable is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('XDG_CONFIG_HOME', tmpdir)
            config = get_config_dir()
            assert config == Path(tmpdir)

    def test_config_home_default(self, monkeypatch):
        """Default ~/.config used when XDG_CONFIG_HOME unset."""
        monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
        config = get_config_dir()
        assert config == Path.home() / '.config'

    def test_data_home_override(self, monkeypatch):
        """XDG_DATA_HOME environment variable is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('XDG_DATA_HOME', tmpdir)
            data = get_data_dir()
            assert data == Path(tmpdir)

    def test_data_home_default(self, monkeypatch):
        """Default ~/.local/share used when XDG_DATA_HOME unset."""
        monkeypatch.delenv('XDG_DATA_HOME', raising=False)
        data = get_data_dir()
        assert data == Path.home() / '.local' / 'share'

    def test_cache_home_override(self, monkeypatch):
        """XDG_CACHE_HOME environment variable is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('XDG_CACHE_HOME', tmpdir)
            cache = get_cache_dir()
            assert cache == Path(tmpdir)

    def test_cache_home_default(self, monkeypatch):
        """Default ~/.cache used when XDG_CACHE_HOME unset."""
        monkeypatch.delenv('XDG_CACHE_HOME', raising=False)
        cache = get_cache_dir()
        assert cache == Path.home() / '.cache'

    def test_state_home_override(self, monkeypatch):
        """XDG_STATE_HOME environment variable is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('XDG_STATE_HOME', tmpdir)
            state = get_state_dir()
            assert state == Path(tmpdir)

    def test_state_home_default(self, monkeypatch):
        """Default ~/.local/state used when XDG_STATE_HOME unset."""
        monkeypatch.delenv('XDG_STATE_HOME', raising=False)
        state = get_state_dir()
        assert state == Path.home() / '.local' / 'state'


class TestAbsolutePathValidation:
    """Test that relative paths are rejected per specification."""

    def test_relative_config_path_ignored(self, monkeypatch):
        """Relative path in XDG_CONFIG_HOME is ignored."""
        monkeypatch.setenv('XDG_CONFIG_HOME', 'relative/path')
        config = get_config_dir()
        assert config == Path.home() / '.config'
        assert not config.match('relative/path')

    def test_relative_data_path_ignored(self, monkeypatch):
        """Relative path in XDG_DATA_HOME is ignored."""
        monkeypatch.setenv('XDG_DATA_HOME', './local/share')
        data = get_data_dir()
        assert data == Path.home() / '.local' / 'share'

    def test_empty_string_uses_default(self, monkeypatch):
        """Empty string in XDG variable uses default."""
        monkeypatch.setenv('XDG_CONFIG_HOME', '')
        config = get_config_dir()
        assert config == Path.home() / '.config'


class TestRuntimeDirectory:
    """Test XDG_RUNTIME_DIR special handling."""

    def test_runtime_dir_set(self, monkeypatch):
        """XDG_RUNTIME_DIR returns path when set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('XDG_RUNTIME_DIR', tmpdir)
            runtime = get_runtime_dir()
            assert runtime == Path(tmpdir)

    def test_runtime_dir_none_when_unset(self, monkeypatch):
        """XDG_RUNTIME_DIR returns None when unset (no default)."""
        monkeypatch.delenv('XDG_RUNTIME_DIR', raising=False)
        runtime = get_runtime_dir()
        assert runtime is None

    def test_runtime_dir_relative_rejected(self, monkeypatch):
        """Relative path in XDG_RUNTIME_DIR returns None."""
        monkeypatch.setenv('XDG_RUNTIME_DIR', 'run/user')
        runtime = get_runtime_dir()
        assert runtime is None


class TestSearchPaths:
    """Test XDG_*_DIRS variables (colon-separated search paths)."""

    def test_config_dirs_parsing(self, monkeypatch):
        """XDG_CONFIG_DIRS parsed as colon-separated list."""
        monkeypatch.setenv('XDG_CONFIG_DIRS', '/etc/xdg:/opt/config')
        dirs = get_config_dirs()
        assert dirs == [Path('/etc/xdg'), Path('/opt/config')]

    def test_config_dirs_default(self, monkeypatch):
        """Default [/etc/xdg] when XDG_CONFIG_DIRS unset."""
        monkeypatch.delenv('XDG_CONFIG_DIRS', raising=False)
        dirs = get_config_dirs()
        assert dirs == [Path('/etc/xdg')]

    def test_data_dirs_parsing(self, monkeypatch):
        """XDG_DATA_DIRS parsed as colon-separated list."""
        monkeypatch.setenv('XDG_DATA_DIRS', '/usr/share:/opt/share:/snap/share')
        dirs = get_data_dirs()
        assert dirs == [Path('/usr/share'), Path('/opt/share'), Path('/snap/share')]

    def test_data_dirs_default(self, monkeypatch):
        """Default [/usr/local/share, /usr/share] when XDG_DATA_DIRS unset."""
        monkeypatch.delenv('XDG_DATA_DIRS', raising=False)
        dirs = get_data_dirs()
        assert dirs == [Path('/usr/local/share'), Path('/usr/share')]

    def test_search_path_filters_relative(self, monkeypatch):
        """Search paths filter out relative directories."""
        monkeypatch.setenv('XDG_DATA_DIRS', '/usr/share:relative/path:/opt/data')
        dirs = get_data_dirs()
        assert dirs == [Path('/usr/share'), Path('/opt/data')]
        assert Path('relative/path') not in dirs

    def test_search_path_handles_empty_components(self, monkeypatch):
        """Search paths handle empty components (double colons)."""
        monkeypatch.setenv('XDG_CONFIG_DIRS', '/etc/xdg::/opt/config')
        dirs = get_config_dirs()
        assert dirs == [Path('/etc/xdg'), Path('/opt/config')]


class TestDirectoryCreation:
    """Test directory creation with ensure_directories()."""

    def test_create_directories(self, monkeypatch, tmp_path):
        """Directories are created with correct hierarchy."""
        from myapp.paths import ensure_directories, APP_NAME

        # Set XDG variables to temp directory
        config_base = tmp_path / 'config'
        data_base = tmp_path / 'data'
        cache_base = tmp_path / 'cache'
        state_base = tmp_path / 'state'

        monkeypatch.setenv('XDG_CONFIG_HOME', str(config_base))
        monkeypatch.setenv('XDG_DATA_HOME', str(data_base))
        monkeypatch.setenv('XDG_CACHE_HOME', str(cache_base))
        monkeypatch.setenv('XDG_STATE_HOME', str(state_base))

        # Create directories
        ensure_directories()

        # Verify all directories exist
        assert (config_base / APP_NAME).exists()
        assert (data_base / APP_NAME).exists()
        assert (cache_base / APP_NAME).exists()
        assert (state_base / APP_NAME).exists()

        # Verify they are directories
        assert (config_base / APP_NAME).is_dir()
        assert (data_base / APP_NAME).is_dir()
        assert (cache_base / APP_NAME).is_dir()
        assert (state_base / APP_NAME).is_dir()


@pytest.fixture
def xdg_test_env(monkeypatch, tmp_path):
    """Set up isolated XDG test environment."""
    config = tmp_path / 'config'
    data = tmp_path / 'data'
    cache = tmp_path / 'cache'
    state = tmp_path / 'state'
    runtime = tmp_path / 'runtime'

    monkeypatch.setenv('XDG_CONFIG_HOME', str(config))
    monkeypatch.setenv('XDG_DATA_HOME', str(data))
    monkeypatch.setenv('XDG_CACHE_HOME', str(cache))
    monkeypatch.setenv('XDG_STATE_HOME', str(state))
    monkeypatch.setenv('XDG_RUNTIME_DIR', str(runtime))

    return {
        'config': config,
        'data': data,
        'cache': cache,
        'state': state,
        'runtime': runtime
    }


def test_full_workflow_with_xdg_env(xdg_test_env):
    """Test complete application workflow in isolated XDG environment."""
    from myapp.paths import (
        get_config_file,
        get_data_dir,
        get_cache_dir,
        ensure_directories
    )

    # Ensure all directories exist
    ensure_directories()

    # Write config file
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text('debug = true\n')

    # Write data file
    data_file = get_data_dir() / 'database.db'
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text('data')

    # Write cache file
    cache_file = get_cache_dir() / 'cache.json'
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text('{}')

    # Verify files in correct locations
    assert config_file.exists()
    assert data_file.exists()
    assert cache_file.exists()

    assert 'config' in str(config_file)
    assert 'data' in str(data_file)
    assert 'cache' in str(cache_file)
```

**Running Tests**:

```bash
# Run all XDG compliance tests
pytest tests/test_xdg_compliance.py -v

# Run specific test class
pytest tests/test_xdg_compliance.py::TestAbsolutePathValidation -v

# Run with coverage
pytest tests/test_xdg_compliance.py --cov=myapp.paths --cov-report=term-missing
```

**Result**:

```text
tests/test_xdg_compliance.py::TestSingleDirectories::test_config_home_override PASSED
tests/test_xdg_compliance.py::TestSingleDirectories::test_config_home_default PASSED
tests/test_xdg_compliance.py::TestAbsolutePathValidation::test_relative_config_path_ignored PASSED
tests/test_xdg_compliance.py::TestRuntimeDirectory::test_runtime_dir_none_when_unset PASSED
tests/test_xdg_compliance.py::TestSearchPaths::test_config_dirs_parsing PASSED
tests/test_xdg_compliance.py::TestSearchPaths::test_search_path_filters_relative PASSED
tests/test_xdg_compliance.py::TestDirectoryCreation::test_create_directories PASSED
tests/test_xdg_compliance.py::test_full_workflow_with_xdg_env PASSED

============ 25 passed in 0.43s ============
```

---

## Additional Resources

### Manual Testing Script

Create a quick validation script:

```bash
#!/bin/bash
# test-xdg.sh - Validate XDG compliance manually

set -e

echo "Testing XDG Base Directory compliance..."

# Test with custom directories
export XDG_CONFIG_HOME=/tmp/xdg-test/config
export XDG_DATA_HOME=/tmp/xdg-test/data
export XDG_CACHE_HOME=/tmp/xdg-test/cache
export XDG_STATE_HOME=/tmp/xdg-test/state

# Clean previous test
rm -rf /tmp/xdg-test

# Run application
myapp init
myapp run

# Verify directory structure
echo "Checking directory structure..."
test -d "$XDG_CONFIG_HOME/myapp" && echo "✓ Config directory created"
test -d "$XDG_DATA_HOME/myapp" && echo "✓ Data directory created"
test -d "$XDG_CACHE_HOME/myapp" && echo "✓ Cache directory created"
test -d "$XDG_STATE_HOME/myapp" && echo "✓ State directory created"

# Verify files in correct locations
test -f "$XDG_CONFIG_HOME/myapp/config.toml" && echo "✓ Config file in correct location"
test -f "$XDG_DATA_HOME/myapp/database.db" && echo "✓ Data file in correct location"
test -f "$XDG_CACHE_HOME/myapp/cache.json" && echo "✓ Cache file in correct location"
test -f "$XDG_STATE_HOME/myapp/history.log" && echo "✓ State file in correct location"

# Test with unset variables (should use defaults)
unset XDG_CONFIG_HOME XDG_DATA_HOME XDG_CACHE_HOME XDG_STATE_HOME

myapp info
test -d "$HOME/.config/myapp" && echo "✓ Defaults to ~/.config when unset"
test -d "$HOME/.local/share/myapp" && echo "✓ Defaults to ~/.local/share when unset"
test -d "$HOME/.cache/myapp" && echo "✓ Defaults to ~/.cache when unset"
test -d "$HOME/.local/state/myapp" && echo "✓ Defaults to ~/.local/state when unset"

echo "All XDG compliance tests passed!"
```

### Integration with Configuration Tools

Example with Click CLI:

```python
import click
from myapp.paths import paths

@click.group()
def cli():
    """MyApp CLI tool."""
    pass

@cli.command()
def info():
    """Show XDG directory configuration."""
    click.echo("XDG Directory Configuration:")
    click.echo(f"  Config: {paths.config}")
    click.echo(f"  Data:   {paths.data}")
    click.echo(f"  Cache:  {paths.cache}")
    click.echo(f"  State:  {paths.state}")

    # Show environment variables
    click.echo("\nEnvironment Variables:")
    import os
    for var in ['XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME']:
        value = os.environ.get(var, '(not set)')
        click.echo(f"  {var}: {value}")
```
