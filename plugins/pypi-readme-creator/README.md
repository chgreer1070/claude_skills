# pypi-readme-creator

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A Claude Code plugin that generates professional, PyPI-compliant README files in Markdown or reStructuredText that render correctly across PyPI, GitHub, GitLab, and BitBucket.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Capabilities](#capabilities)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Related Skills](#related-skills)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Format Support** - Create README files in Markdown (GFM/CommonMark) or reStructuredText
- **PyPI Compliance** - Ensures README renders correctly on PyPI without validation errors
- **Sphinx Integration** - Leverage `sphinx-readme` to generate PyPI-compatible RST from Sphinx docs
- **Platform Compatibility** - Test and validate rendering across multiple platforms
- **Best Practices** - Follow documentation standards for clarity, accessibility, and user focus
- **Validation Workflow** - Pre-publish checklist with `twine check` integration
- **Template Library** - Three production-ready templates for immediate use

## Installation

### Prerequisites

- Claude Code version 2.1 or higher
- Python 3.11+ (for package validation tools)

### Install Plugin

```bash
# Method 1: Manual installation
git clone <repository-url> ~/.claude/plugins/pypi-readme-creator
cc plugin reload

# Method 2: Symlink from development directory
ln -s /path/to/plugins/pypi-readme-creator ~/.claude/plugins/pypi-readme-creator
cc plugin reload
```

## Quick Start

When working on a Python package that needs a README for PyPI:

```
Create a PyPI-compliant README.md for my Python package 'data-processor'
with installation instructions, usage examples, and badges.
```

Claude will automatically activate the skill and generate a comprehensive README following PyPI best practices.

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | pypi-readme-creator | Generate PyPI-compliant README files in Markdown or reStructuredText | Auto-activated by Claude |

## Usage

### When Claude Activates This Skill

The skill automatically activates when you:

- Create or update README files for Python packages
- Prepare a package for PyPI publication
- Troubleshoot README rendering errors on PyPI
- Convert between Markdown and reStructuredText formats
- Configure the `readme` field in `pyproject.toml`
- Validate README markup with `twine check`

### Format Selection

**Choose Markdown (README.md) when:**
- Starting a new project without existing RST documentation
- Prioritizing GitHub/GitLab compatibility
- Team prefers Markdown syntax
- Documentation is primarily user-facing

**Choose reStructuredText (README.rst) when:**
- Project uses Sphinx for documentation
- Need advanced table formatting
- Existing RST documentation infrastructure
- Using `sphinx-readme` to generate from Sphinx docs

### Essential README Sections

1. **Project Identity** - Name, description, badges, value proposition
2. **Installation** - `pip install package-name` with alternatives
3. **Quick Start** - Minimal working example (3-10 lines)
4. **Features** - Key capabilities and unique aspects
5. **Usage Examples** - 2-3 concrete examples showing common use cases
6. **Documentation Link** - Link to full docs if available
7. **Contributing** - How to report issues and submit changes
8. **License** - License name and link to LICENSE file

## Configuration

### pyproject.toml Integration

**Markdown README:**

```toml
[project]
readme = "README.md"  # Auto-detects text/markdown
```

**reStructuredText README:**

```toml
[project]
readme = "README.rst"  # Auto-detects text/x-rst
```

**Explicit Content Type:**

```toml
[project]
readme = {file = "README.md", content-type = "text/markdown; variant=GFM"}
```

### Validation Workflow

```bash
# 1. Build the package
uv build

# 2. Validate README rendering
uv run --with twine twine check dist/*

# 3. Test on TestPyPI
uv run --with twine twine upload --repository testpypi dist/*

# 4. Verify rendering at https://test.pypi.org/project/package-name/

# 5. Upload to PyPI
uv run --with twine twine upload dist/*
```

## Examples

### Example 1: Create Markdown README

**Scenario:** You have a new Python package and need a PyPI-compliant README.

**Prompt:**

```
Create a README.md for my package 'data-processor' that:
- Describes a Python library for processing CSV/JSON data
- Includes installation via pip
- Shows 2-3 usage examples
- Adds badges for PyPI version and Python compatibility
- Includes a license section (MIT)
```

**Result:** Claude generates a complete README.md with proper structure, syntax highlighting, and PyPI-compatible markup.

---

### Example 2: Convert Sphinx Docs to PyPI README

**Scenario:** Your project uses Sphinx for documentation, and you need a PyPI-compatible README without Sphinx-specific roles.

**Prompt:**

```
Set up sphinx-readme to generate a PyPI-compatible README.rst from my Sphinx
documentation. Configure it to convert the index.rst file.
```

**Result:** Claude configures `sphinx-readme` extension in `conf.py`, sets up the build process, and explains the conversion workflow.

---

### Example 3: Fix PyPI Rendering Errors

**Scenario:** Your README has Sphinx roles that fail `twine check` validation.

**Error:**

```
warning: `long_description_content_type` missing. defaulting to `text/x-rst`.
warning: Unknown interpreted text role "py:func".
```

**Prompt:**

```
Fix my README.rst to be PyPI-compliant. Remove Sphinx-specific roles
and replace with standard docutils equivalents.
```

**Result:** Claude identifies Sphinx-specific syntax (`:py:func:`, `:ref:`, `:doc:`) and replaces them with PyPI-compatible alternatives like inline literals and explicit links.

---

### Example 4: Add GitHub Flavored Markdown Features

**Scenario:** You want to use GFM features like alerts and task lists.

**Prompt:**

```
Update my README.md to use GitHub alerts for warnings and notes.
Ensure it's compatible with PyPI rendering.
```

**Result:** Claude adds GFM alerts with `> [!NOTE]` and `> [!WARNING]` syntax while explaining PyPI compatibility considerations.

## Troubleshooting

### Common Issues

**Issue: Sphinx roles not rendering on PyPI**

```
Error: Unknown interpreted text role "py:func"
```

**Solution:** Replace Sphinx roles with standard RST or use `sphinx-readme` to auto-convert.

```rst
❌ WRONG: See :py:func:`package.function` for details.
✓ CORRECT: See ``package.function()`` for details.
```

---

**Issue: Code block indentation errors in RST**

```
Error: Unexpected indentation
```

**Solution:** Ensure blank line after `.. code-block::` directive and proper indentation.

```rst
✓ CORRECT:
.. code-block:: python

   import package  # Blank line after directive, 3-space indent
```

---

**Issue: README not showing on PyPI**

**Solution:** Verify `readme` field in `pyproject.toml` and run `twine check`.

```bash
uv run --with twine twine check dist/*
```

Check that content type matches file format (`.md` → `text/markdown`, `.rst` → `text/x-rst`).

---

**Issue: Different rendering on GitHub vs PyPI**

**Solution:** Test on TestPyPI before publishing. GitHub supports more GFM features than PyPI.

```bash
# Upload to TestPyPI first
uv run --with twine twine upload --repository testpypi dist/*

# Visit https://test.pypi.org/project/package-name/ to verify
```

## Documentation

### Quick Links

- **[Usage Examples](./docs/examples.md)** - 7 detailed examples covering common scenarios
- **[Technical Reference](./docs/reference.md)** - Complete format specifications, validation tools, and best practices
- **[Skill Usage Guide](./docs/skill-usage.md)** - How to effectively use the skill with Claude Code

### Reference Templates

The plugin includes three production-ready templates (accessed automatically by Claude):

1. **markdown-template.md** - Modern Markdown README with badges, code examples, and GFM features
2. **rst-template.rst** - reStructuredText README with directives, admonitions, and tables
3. **sphinx-readme-example.md** - Guide for using `sphinx-readme` extension

## Related Skills

- **uv** - Python project and package management (`@uv`)
- **hatchling** - Build backend configuration
- **gitlab-skill** - GitLab Flavored Markdown features

## Contributing

This plugin is part of the Claude Code Skills repository. To contribute:

1. Report issues at the repository issue tracker
2. Submit pull requests with improvements
3. Follow existing code style and documentation standards

## License

See LICENSE file in the plugin directory.

## Credits

Created as part of the Claude Code plugin ecosystem to improve Python package documentation quality and PyPI publishing workflows.
