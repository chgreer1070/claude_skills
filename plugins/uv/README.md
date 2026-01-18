# uv Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-unknown-lightgrey) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Expert guidance for Astral's uv - an extremely fast Python package and project manager. This plugin provides comprehensive knowledge for working with Python projects, managing dependencies, creating scripts with PEP 723 metadata, installing tools, managing Python versions, and configuring package indexes.

## Features

- **Project Management** - Initialize, configure, and manage Python projects with modern tooling
- **Dependency Management** - Add, remove, lock, and sync dependencies with reproducible lockfiles
- **Script Creation** - Create portable single-file scripts with PEP 723 inline metadata
- **Tool Management** - Install and run Python tools globally or ephemerally
- **Python Version Management** - Install, manage, and switch between Python versions
- **Virtual Environments** - Create and manage isolated Python environments
- **pip Compatibility** - Drop-in replacement for pip, pip-compile, and pip-sync
- **Workspace Support** - Manage monorepo projects with multiple packages
- **CI/CD Integration** - Optimize continuous integration with uv's speed
- **Migration Support** - Migrate from pip, poetry, and other tools

## Installation

### Prerequisites

- **Claude Code**: Version 2.1 or later
- **uv**: Install from [astral.sh/uv](https://docs.astral.sh/uv/)

```bash
# Install uv on Unix/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install uv on Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install via pip
pip install uv

# Install via Homebrew
brew install uv
```

### Install Plugin

```bash
# Method 1: Using cc plugin install (if plugin is published)
cc plugin install uv

# Method 2: Manual installation
git clone <repository-url> ~/.claude/plugins/uv
cc plugin reload
```

## Quick Start

```bash
# Initialize a new Python project
uv init myproject
cd myproject

# Add dependencies
uv add fastapi uvicorn sqlalchemy

# Add development dependencies
uv add --dev pytest ruff mypy

# Run your application
uv run python main.py

# Run tests
uv run pytest
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | uv | Expert guidance for Astral's uv package manager, covering all aspects of Python project management | `@uv` or auto-activated |

## Usage

### Skills

The plugin provides one comprehensive skill that covers all aspects of uv usage:

**uv Skill** - Automatically activates when you're working with Python projects, managing dependencies, creating scripts, or performing any uv-related tasks. The skill provides expert guidance for:

- Initializing and managing Python projects
- Adding, removing, and updating dependencies
- Creating portable scripts with PEP 723 metadata
- Managing Python versions
- Configuring virtual environments
- Building and publishing packages
- CI/CD integration
- Troubleshooting common issues

For detailed skill documentation, see [docs/skills.md](./docs/skills.md).

### Common Use Cases

**Start a New Project:**

```bash
# Initialize with recommended structure
uv init myproject
cd myproject

# Add dependencies
uv add requests pandas matplotlib

# Add dev tools
uv add --dev pytest ruff black
```

**Create a Portable Script:**

```bash
# Create script with metadata
uv init --script analyze.py --python 3.11

# Add dependencies to script
uv add --script analyze.py pandas matplotlib

# Run the script
uv run analyze.py
```

**Migrate from pip/requirements.txt:**

```bash
# Import existing dependencies
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# Use uv going forward
uv sync
```

**Migrate from Poetry:**

```bash
# Automated migration
uvx migrate-to-uv

# Preview changes first
uvx migrate-to-uv --dry-run
```

## Configuration

The uv skill automatically activates based on context. No additional configuration is required. The skill includes comprehensive reference documentation:

- **CLI Reference** - Complete command and argument reference
- **Configuration** - All configuration options and environment variables
- **Troubleshooting** - Common issues and solutions

All reference files are automatically loaded on demand when needed.

## Examples

### Initialize a Web Application

```bash
# Create new application
uv init webapp --app
cd webapp

# Add web framework and dependencies
uv add fastapi uvicorn sqlalchemy pydantic

# Add development tools
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy

# Run the application
uv run uvicorn main:app --reload
```

### Create a Data Analysis Script

```bash
# Create script with dependencies
uv init --script analyze.py --python 3.11
uv add --script analyze.py pandas matplotlib seaborn

# Edit analyze.py with your analysis code
# ...

# Lock for reproducibility
uv lock --script analyze.py

# Make executable
chmod +x analyze.py

# Run
./analyze.py
```

### Set Up CI/CD with GitHub Actions

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync --frozen --all-extras

      - name: Run tests
        run: uv run pytest
```

For more examples, see [docs/examples.md](./docs/examples.md).

## Troubleshooting

### "Externally Managed" Error

**Problem**: `error: The interpreter is externally managed`

**Solution**: Use virtual environments instead of `--system`:

```bash
uv venv
source .venv/bin/activate
uv pip install package
```

### Build Failures

**Problem**: Package fails to build from source

**Solutions**:

- Install system dependencies: `apt-get install python3-dev build-essential`
- Add version constraints: `uv add "numpy>=1.20"`
- Check error message for missing modules

### Lockfile Out of Sync

**Problem**: Dependencies changed but lockfile not updated

**Solutions**:

```bash
uv lock           # Regenerate lockfile
uv sync --locked  # Error if out of sync (CI mode)
uv sync --frozen  # Don't update lockfile
```

For comprehensive troubleshooting, the skill includes detailed reference documentation that's automatically loaded when needed.

## Contributing

Contributions are welcome! When contributing:

1. Ensure all documentation follows Claude Code markdown standards
2. Use relative links with `./` prefix for file references
3. Add language specifiers to all code fences
4. Verify all file paths exist before documenting
5. Test changes with actual uv commands

## License

This plugin documentation is provided as-is for use with Claude Code.

## Credits

- **uv** by [Astral](https://astral.sh/) - The fast Python package manager
- **Documentation** compiled from official uv documentation and community resources

## Resources

- [Official uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [uv Concepts Guide](https://docs.astral.sh/uv/concepts/)
- [Migration Guides](https://docs.astral.sh/uv/guides/migration/)
