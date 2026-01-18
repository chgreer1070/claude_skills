# Technical Reference

Complete technical reference for PyPI README formats, validation, and best practices.

## Supported Formats

PyPI's `readme_renderer` supports three formats with specific constraints.

### Plain Text (text/plain)

**Content Type:** `text/plain`

**Characteristics:**
- No formatting capabilities
- Renders exactly as written
- No markup processing

**When to Use:**
- Minimal documentation requirements
- Legacy packages
- Machine-generated content

**Configuration:**

```toml
[project]
readme = {file = "README.txt", content-type = "text/plain"}
```

---

### reStructuredText (text/x-rst)

**Content Type:** `text/x-rst`

**Characteristics:**
- Rich formatting with directives and roles
- Standard docutils processing
- **No Sphinx extensions allowed**
- Strict indentation requirements

**Allowed Features:**
- Admonitions (`.. note::`, `.. warning::`, `.. tip::`, `.. important::`)
- Code blocks (`.. code-block:: python`)
- Tables (grid and simple table syntax)
- Inline markup (bold, italic, literals)
- Explicit links and references
- Images
- Lists (bulleted, numbered, definition)

**Prohibited Features:**
- Sphinx roles (`:py:func:`, `:ref:`, `:doc:`, `:mod:`)
- Sphinx directives (`:automodule:`, `:autosummary:`, `:toctree:`)
- Custom roles and directives
- Sphinx extensions (autodoc, intersphinx, etc.)

**Configuration:**

```toml
[project]
readme = "README.rst"  # Auto-detects text/x-rst
# or explicit:
readme = {file = "README.rst", content-type = "text/x-rst"}
```

**Validation:**

```bash
# Validate RST syntax
uv run --with docutils rst2html.py README.rst /dev/null

# Check PyPI rendering
uv run --with twine twine check dist/*
```

---

### Markdown (text/markdown)

**Content Type:** `text/markdown`

**Variants:**
1. **GitHub Flavored Markdown (GFM)** - Default variant
2. **CommonMark** - Strict CommonMark specification

**GFM Features (Supported):**
- Fenced code blocks with language specifiers
- Tables
- Strikethrough (`~~text~~`)
- Task lists
- Autolinks
- Syntax highlighting

**GFM Features (Limited PyPI Support):**
- Alerts (`> [!NOTE]`) - Render as blockquotes on PyPI
- Emoji shortcodes - May not render on PyPI
- HTML tags - Stripped for security

**Configuration:**

```toml
[project]
readme = "README.md"  # Auto-detects text/markdown with GFM variant

# Explicit GFM:
readme = {file = "README.md", content-type = "text/markdown; variant=GFM"}

# CommonMark:
readme = {file = "README.md", content-type = "text/markdown; variant=CommonMark"}
```

**Validation:**

```bash
# Local GitHub preview
uvx grip README.md

# Check PyPI rendering
uv run --with twine twine check dist/*
```

---

## pyproject.toml Configuration

### Basic Configuration

```toml
[project]
name = "package-name"
version = "1.0.0"
description = "One-line package description"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
```

### README Field Options

**Simple String (Auto-Detection):**

```toml
readme = "README.md"   # Detects text/markdown
readme = "README.rst"  # Detects text/x-rst
readme = "README.txt"  # Detects text/plain
```

**Explicit Table:**

```toml
readme = {file = "README.md", content-type = "text/markdown"}
```

**With Variant:**

```toml
readme = {file = "README.md", content-type = "text/markdown; variant=GFM"}
readme = {file = "README.md", content-type = "text/markdown; variant=CommonMark"}
```

**Multiple Files (Not Recommended):**

```toml
# Concatenates files - avoid unless necessary
readme = {files = ["README.md", "CHANGELOG.md"], content-type = "text/markdown"}
```

### Project URLs

```toml
[project.urls]
Homepage = "https://example.com"
Documentation = "https://docs.example.com"
Repository = "https://github.com/user/package"
Issues = "https://github.com/user/package/issues"
Changelog = "https://github.com/user/package/blob/main/CHANGELOG.md"
Funding = "https://github.com/sponsors/user"
```

---

## Validation Tools

### Twine Check

Primary tool for validating PyPI README rendering.

**Installation:**

```bash
uv add --dev twine
# or use with --with flag
uv run --with twine twine check dist/*
```

**Usage:**

```bash
# After building package
uv build

# Validate distributions
uv run --with twine twine check dist/*
```

**Output:**

```
Checking dist/package-1.0.0-py3-none-any.whl: Passed
Checking dist/package-1.0.0.tar.gz: Passed
```

**Common Errors:**

| Error | Meaning | Solution |
|-------|---------|----------|
| `Unknown interpreted text role "py:func"` | Sphinx role in RST | Remove Sphinx-specific roles |
| `Unexpected indentation` | RST indentation error | Fix indentation, add blank lines |
| `Unknown directive type "automodule"` | Sphinx directive | Replace with standard directives |
| `Content-Type mismatch` | Wrong file/content-type | Verify pyproject.toml readme setting |

---

### readme_renderer (Direct Usage)

Test README rendering programmatically.

**Installation:**

```bash
uv add --dev readme-renderer
```

**Usage:**

```python
from readme_renderer.rst import render as rst_render
from readme_renderer.markdown import render as md_render

# Test RST rendering
with open("README.rst") as f:
    html = rst_render(f.read())
    if html is None:
        print("RST rendering failed")
    else:
        print("RST rendering succeeded")

# Test Markdown rendering
with open("README.md") as f:
    html = md_render(f.read())
    if html is None:
        print("Markdown rendering failed")
    else:
        print("Markdown rendering succeeded")
```

---

### docutils (RST Validation)

Validate reStructuredText syntax.

**Installation:**

```bash
uv run --with docutils rst2html.py README.rst /dev/null
```

**Options:**

```bash
# Generate HTML preview
uv run --with docutils rst2html.py README.rst README.html

# Strict validation
uv run --with docutils rst2html.py --strict README.rst /dev/null

# Show warnings
uv run --with docutils rst2html.py --report=2 README.rst /dev/null
```

---

### grip (Markdown Preview)

Preview Markdown as GitHub renders it.

**Installation:**

```bash
uv tool install grip
```

**Usage:**

```bash
# Start preview server
uvx grip README.md

# Opens browser at http://localhost:6419
# Auto-reloads on file changes
```

---

## Publishing Workflow

### Complete Pre-Publish Checklist

```bash
# 1. Build the package
uv build

# 2. Validate README rendering
uv run --with twine twine check dist/*

# 3. Test installation locally
uv pip install dist/*.whl

# 4. Upload to TestPyPI
uv run --with twine twine upload --repository testpypi dist/*

# 5. Visit TestPyPI page
# https://test.pypi.org/project/package-name/

# 6. Test installation from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ package-name

# 7. Upload to production PyPI
uv run --with twine twine upload dist/*
```

### PyPI Credentials Configuration

**Method 1: .pypirc file**

```bash
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBp...
EOF

chmod 600 ~/.pypirc
```

**Method 2: Environment variables**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...
```

**Method 3: Command line (not recommended)**

```bash
uv run --with twine twine upload --username __token__ --password pypi-... dist/*
```

### Generating API Tokens

**PyPI:**
1. Visit https://pypi.org/manage/account/token/
2. Create token with scope "Entire account" or specific project
3. Copy token (starts with `pypi-`)

**TestPyPI:**
1. Visit https://test.pypi.org/manage/account/token/
2. Create token
3. Copy token

---

## Sphinx Integration

### sphinx-readme Extension

Generate PyPI-compatible README.rst from Sphinx documentation.

**Installation:**

```bash
uv add --group docs sphinx-readme
```

**Configuration in conf.py:**

```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_readme',
]

readme_config = {
    'src_file': 'index.rst',       # Source file in docs/
    'out_file': '../README.rst',   # Output to project root
    'strip_roles': True,           # Remove Sphinx roles
    'strip_directives': ['toctree', 'automodule'],
}
```

**Build Process:**

```bash
# Build Sphinx docs (generates README.rst automatically)
uv run sphinx-build -b html docs/ docs/_build/html

# Verify README
uv run --with twine twine check dist/*
```

**Conversion Rules:**

| Sphinx Syntax | Converted To |
|---------------|--------------|
| `:py:func:`package.func`` | `package.func()` |
| `:ref:`label`` | Plain text or link |
| `:doc:`page`` | Link to hosted docs |
| `:mod:`package`` | `package` |
| `.. automodule::` | Removed |
| `.. toctree::` | Removed |

---

## Format Comparison

| Feature | Markdown | reStructuredText | Plain Text |
|---------|----------|------------------|------------|
| Code highlighting | ✓ | ✓ | ✗ |
| Tables | ✓ | ✓ | ✗ |
| Admonitions | Limited | ✓ | ✗ |
| Inline formatting | ✓ | ✓ | ✗ |
| GitHub compatibility | Excellent | Good | Basic |
| GitLab compatibility | Excellent | Good | Basic |
| Sphinx integration | Manual | ✓ (sphinx-readme) | ✗ |
| Ease of writing | Easy | Moderate | Trivial |
| Advanced tables | Limited | Excellent | ✗ |
| Cross-references | Links only | ✓ (with docutils) | ✗ |

---

## Best Practices

### Content Structure

1. **Project Identity** - Name, description, badges
2. **Installation** - Primary method first
3. **Quick Start** - Working example within 3-10 lines
4. **Features** - Bulleted list of capabilities
5. **Usage** - 2-3 progressive examples
6. **Documentation** - Link to full docs
7. **Contributing** - How to participate
8. **License** - Legal information

### Writing Guidelines

**Clarity:**
- Write for first-time users
- Use active voice and present tense
- Keep sentences under 25 words
- Define technical terms on first use

**Examples:**
- Provide copy-paste ready code
- Show expected output
- Test examples with current version
- Progress from basic to advanced

**Links:**
- Use descriptive text, not "click here"
- Verify all links before publishing
- Use stable URLs (not /latest/ for version-specific links)

**Badges:**
- Place at top of README
- Use shields.io or similar
- Include: PyPI version, Python versions, license, build status

### Validation Checklist

- [ ] Code examples tested with current version
- [ ] All links verified and working
- [ ] Badges display correctly
- [ ] `twine check` passes
- [ ] Tested on TestPyPI
- [ ] Rendering verified on PyPI
- [ ] Spelling and grammar checked
- [ ] Version numbers current
- [ ] License clearly stated
- [ ] Python version requirements specified

---

## Common Issues and Solutions

### RST Issues

**Issue: Indentation errors**

```rst
❌ WRONG:
.. code-block:: python
import package

✓ CORRECT:
.. code-block:: python

   import package
```

**Issue: Link spacing**

```rst
❌ WRONG:
`Link`_
.. _Link: https://example.com

✓ CORRECT:
`Link`_

.. _Link: https://example.com
```

**Issue: Section headers**

```rst
❌ WRONG:
Section
---  # Too short

✓ CORRECT:
Section
-------  # Match length
```

### Markdown Issues

**Issue: Missing language specifier**

````markdown
❌ WRONG:
```
code here
```

✓ CORRECT:
```python
code here
```
````

**Issue: Broken table syntax**

```markdown
❌ WRONG:
| Header |
| Cell |

✓ CORRECT:
| Header |
|--------|
| Cell   |
```

### Platform Differences

**GitHub vs PyPI:**
- GitHub: Full GFM support (alerts, task lists, emoji)
- PyPI: Basic GFM (alerts render as blockquotes)
- Solution: Test on TestPyPI, ensure graceful degradation

**Line Endings:**
- Unix: LF (`\n`)
- Windows: CRLF (`\r\n`)
- Solution: Configure git or use `dos2unix`

```bash
# Convert to Unix line endings
dos2unix README.md
```

---

## External Resources

### Official Documentation

- [Python Packaging Guide - PyPI README](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/)
- [readme_renderer on GitHub](https://github.com/pypa/readme_renderer)
- [sphinx-readme Documentation](https://sphinx-readme.readthedocs.io/)
- [Twine Documentation](https://twine.readthedocs.io/)

### Format Specifications

- [GitHub Flavored Markdown](https://github.github.com/gfm/)
- [CommonMark](https://commonmark.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [docutils Documentation](https://docutils.sourceforge.io/)

### Tools

- [grip - GitHub README preview](https://github.com/joeyespo/grip)
- [m2rr - Markdown to RST](https://github.com/qhua948/m2rr)
- [pandoc - Universal converter](https://pandoc.org/)
- [uv - Python package manager](https://docs.astral.sh/uv/)
