# Usage Examples

Concrete examples demonstrating how to use the pypi-readme-creator plugin for various README creation scenarios.

## Example 1: New Python Package - Complete README

**Scenario:** You've created a new Python package called `json-validator` that validates JSON against schemas. You need a complete README for PyPI publication.

**Steps:**

1. Create a request describing your package

```
Create a comprehensive README.md for my Python package 'json-validator'.

Package details:
- Validates JSON files and strings against JSON Schema
- Supports Draft 7 and Draft 2020-12 schemas
- Python 3.11+ required
- CLI and library usage
- MIT licensed
- Repository: https://github.com/user/json-validator

Include installation, quick start, usage examples, and badges.
```

2. Claude activates the pypi-readme-creator skill

3. Generated README includes:
   - Project name and one-line description
   - Badges for PyPI version, Python compatibility, license
   - Installation section with `pip install json-validator`
   - Quick start with minimal example
   - Usage examples for both CLI and library
   - Link to documentation (if exists)
   - Contributing section
   - License information

**Code Example Generated:**

```markdown
# json-validator

![PyPI version](https://img.shields.io/pypi/v/json-validator.svg)
![Python versions](https://img.shields.io/pypi/pyversions/json-validator.svg)
![License](https://img.shields.io/pypi/l/json-validator.svg)

Validate JSON files and strings against JSON Schema (Draft 7 and Draft 2020-12).

## Installation

```bash
pip install json-validator
```

## Quick Start

```python
from json_validator import validate

# Validate JSON against schema
result = validate(
    data={"name": "Alice", "age": 30},
    schema={"type": "object", "properties": {"name": {"type": "string"}}}
)
print(result.is_valid)  # True
```

## Usage

### Library Usage

```python
import json_validator

# Validate from file
validator = json_validator.Validator("schema.json")
result = validator.validate_file("data.json")

if not result.is_valid:
    print(f"Validation errors: {result.errors}")
```

### CLI Usage

```bash
# Validate JSON file
json-validator --schema schema.json data.json

# Validate with Draft 2020-12
json-validator --draft 2020-12 --schema schema.json data.json
```

## Features

- Support for JSON Schema Draft 7 and Draft 2020-12
- CLI and Python library interfaces
- Detailed error messages with line numbers
- Batch validation of multiple files
- Custom format validators

## Documentation

Full documentation available at https://json-validator.readthedocs.io

## Contributing

Report issues at https://github.com/user/json-validator/issues

## License

MIT License - see LICENSE file for details.
```

**Result:** PyPI-compliant README ready for publication after running `twine check`.

---

## Example 2: Sphinx Documentation to PyPI README

**Scenario:** Your project uses Sphinx for documentation with extensive use of Sphinx roles (`:py:func:`, `:ref:`, etc.). You need to generate a PyPI-compatible README.rst without manually converting all the roles.

**Steps:**

1. Request sphinx-readme setup

```
I have a Sphinx-based documentation project. Set up sphinx-readme to automatically
generate a PyPI-compatible README.rst from my docs/index.rst file. I want the
README in the project root.
```

2. Claude activates the skill and generates configuration

**Generated conf.py additions:**

```python
# Add to conf.py
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_readme',  # Add this
]

# Configure sphinx-readme
readme_config = {
    'src_file': 'index.rst',      # Source in docs/
    'out_file': '../README.rst',   # Output to project root
}
```

3. Update build process

**Generated commands:**

```bash
# Install sphinx-readme
uv add --group docs sphinx-readme

# Build docs (automatically generates README.rst)
uv run sphinx-build -b html docs/ docs/_build/html

# Verify README rendering
uv run --with twine twine check dist/*
```

**Result:** Sphinx-specific roles automatically converted to PyPI-compatible equivalents. For example:
- `:py:func:`mypackage.function`` → `mypackage.function()`
- `:ref:`section`` → Plain text link
- Admonitions and code blocks preserved

---

## Example 3: Fix Existing README with Validation Errors

**Scenario:** You have an existing README.rst that fails `twine check` validation with Sphinx role errors.

**Error Output:**

```
warning: `long_description_content_type` missing.
warning: line 42: Unknown interpreted text role "py:func".
warning: line 58: Unknown interpreted text role "ref".
warning: line 73: Unknown directive type "automodule".
```

**Steps:**

1. Request validation fix

```
My README.rst fails twine check validation with these errors:
- Unknown interpreted text role "py:func" on line 42
- Unknown interpreted text role "ref" on line 58
- Unknown directive type "automodule" on line 73

Fix these to be PyPI-compliant while preserving the intent.
```

2. Claude reads the README and identifies issues

**Before (line 42):**

```rst
Use the :py:func:`mypackage.process_data` function to process data.
```

**After (line 42):**

```rst
Use the ``mypackage.process_data()`` function to process data.
```

**Before (line 58):**

```rst
See :ref:`advanced-usage` for more details.
```

**After (line 58):**

```rst
See `Advanced Usage`_ for more details.

.. _Advanced Usage: https://mypackage.readthedocs.io/en/latest/advanced.html
```

**Before (line 73):**

```rst
.. automodule:: mypackage
   :members:
```

**After (line 73):**

```rst
API Documentation
=================

Full API documentation available at https://mypackage.readthedocs.io/en/latest/api.html
```

3. Validate the fixes

```bash
uv run --with twine twine check dist/*
# Output: Checking dist/mypackage-1.0.0.tar.gz: Passed
```

**Result:** README passes validation and renders correctly on PyPI.

---

## Example 4: Convert Markdown to reStructuredText

**Scenario:** Your project has a Markdown README, but you want to switch to reStructuredText for consistency with Sphinx documentation.

**Steps:**

1. Request conversion

```
Convert my README.md to README.rst format. Preserve all sections, code examples,
badges, and links. The package is 'data-processor'.
```

2. Claude reads README.md and converts syntax

**Before (Markdown):**

```markdown
# data-processor

![PyPI version](https://img.shields.io/pypi/v/data-processor.svg)

Process CSV and JSON data with a simple API.

## Installation

```bash
pip install data-processor
```

## Usage

```python
from data_processor import process

result = process("data.csv")
```

## Features

- CSV processing
- JSON processing
- Type validation
```

**After (reStructuredText):**

```rst
================
data-processor
================

.. image:: https://img.shields.io/pypi/v/data-processor.svg
   :target: https://pypi.org/project/data-processor/
   :alt: PyPI version

Process CSV and JSON data with a simple API.

Installation
============

.. code-block:: bash

   pip install data-processor

Usage
=====

.. code-block:: python

   from data_processor import process

   result = process("data.csv")

Features
========

- CSV processing
- JSON processing
- Type validation
```

3. Update pyproject.toml

**Generated change:**

```toml
[project]
readme = "README.rst"  # Changed from README.md
```

**Result:** Fully converted README.rst with equivalent formatting and PyPI compatibility.

---

## Example 5: Add GitHub Flavored Markdown Features

**Scenario:** You want to enhance your README.md with GitHub-specific features like alerts and task lists while maintaining PyPI compatibility.

**Steps:**

1. Request GFM enhancement

```
Add GitHub alerts to my README.md for:
- A warning about breaking changes in version 2.0
- A note about Python 3.11+ requirement
- A tip about async API performance

Ensure PyPI compatibility.
```

2. Claude generates GFM alerts

**Generated Content:**

```markdown
## Installation

> [!NOTE]
> This package requires Python 3.11 or higher.

```bash
pip install mypackage
```

## Upgrading from 1.x

> [!WARNING]
> Version 2.0 includes breaking changes. See the [migration guide](https://docs.example.com/migration) before upgrading.

## Performance

> [!TIP]
> Use the async API for better performance with I/O-bound operations.

```python
import asyncio
from mypackage import async_process

async def main():
    result = await async_process("data.json")
    print(result)

asyncio.run(main())
```
```

3. Explain PyPI rendering

Claude notes: "These GitHub alerts will render as blockquotes on PyPI, maintaining readability even though the special alert styling won't appear."

**Result:** Enhanced README with GFM features that gracefully degrade on PyPI.

---

## Example 6: Local Testing Workflow

**Scenario:** Before publishing to PyPI, you want to test how your README renders locally.

**Steps:**

1. Request testing workflow

```
Show me how to test my README.md locally before publishing to PyPI.
I want to preview it as GitHub renders it and validate PyPI compatibility.
```

2. Claude provides testing commands

**For Markdown (GitHub preview):**

```bash
# Install grip
uv tool install grip

# Preview README.md
uvx grip README.md
# Opens browser at http://localhost:6419 with GitHub-styled rendering
```

**For reStructuredText (docutils validation):**

```bash
# Convert RST to HTML for preview
uv run --with docutils rst2html.py README.rst README.html

# Open in browser
xdg-open README.html  # Linux
open README.html      # macOS

# Validate RST syntax (errors only)
uv run --with docutils rst2html.py README.rst /dev/null
```

**For PyPI validation:**

```bash
# Build package
uv build

# Check README rendering
uv run --with twine twine check dist/*

# Expected output:
# Checking dist/mypackage-1.0.0-py3-none-any.whl: Passed
# Checking dist/mypackage-1.0.0.tar.gz: Passed
```

**Full pre-publish workflow:**

```bash
# 1. Test locally
uvx grip README.md  # or rst2html.py for RST

# 2. Build package
uv build

# 3. Validate
uv run --with twine twine check dist/*

# 4. Upload to TestPyPI
uv run --with twine twine upload --repository testpypi dist/*

# 5. Visit TestPyPI and verify rendering
# https://test.pypi.org/project/mypackage/

# 6. Install from TestPyPI and test
uv pip install --index-url https://test.pypi.org/simple/ mypackage

# 7. If satisfied, upload to production PyPI
uv run --with twine twine upload dist/*
```

**Result:** Comprehensive testing workflow that catches rendering issues before publication.

---

## Example 7: Template-Based Quick Start

**Scenario:** You want to start with a template and customize it for your package.

**Steps:**

1. Request template usage

```
Use the Markdown README template for my package 'api-client'.
Customize it for a REST API client library with async support.
```

2. Claude accesses the markdown-template.md reference

3. Generates customized README based on template structure

**Result:** Production-ready README with template structure customized for your specific package, including:
- Package-specific installation instructions
- API client usage examples
- Async/await examples
- Authentication configuration
- Error handling patterns

The template provides the structure, and Claude adapts the content to your package's domain and features.
