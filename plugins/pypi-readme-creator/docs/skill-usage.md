# Skill Usage Guide

How to effectively use the pypi-readme-creator skill with Claude Code.

## Skill Overview

**Name:** `pypi-readme-creator`

**Description:** Generate professional, PyPI-compliant README files in Markdown or reStructuredText that render correctly across PyPI, GitHub, GitLab, and BitBucket.

**User Invocable:** Yes (auto-activated by Claude)

**Tools Used:** Read, Grep, Glob, Write, Edit, Bash

---

## Activation Triggers

Claude automatically activates this skill when you:

1. **Create README files** - Mention creating or generating a README for a Python package
2. **PyPI preparation** - Discuss preparing a package for PyPI publication
3. **Rendering errors** - Troubleshoot README rendering issues on PyPI
4. **Format conversion** - Convert between Markdown and reStructuredText
5. **Validation** - Run `twine check` or validate README markup
6. **Configuration** - Configure `readme` field in `pyproject.toml`

### Example Activation Phrases

```
Create a README.md for my Python package
Fix my README.rst rendering errors on PyPI
Convert README.md to reStructuredText
Set up pyproject.toml for PyPI publication
Validate my README with twine check
Generate a PyPI-compliant README
```

---

## Usage Patterns

### Pattern 1: Create New README

**When:** Starting a new Python package or replacing an inadequate README.

**Request Format:**

```
Create a [Markdown/RST] README for my package '[package-name]'.

Package details:
- [Brief description]
- [Key features]
- [Installation method]
- [Python version requirement]
- [License]
- [Repository URL]
```

**What Claude Does:**
1. Activates pypi-readme-creator skill
2. Analyzes package requirements
3. Generates README with proper structure
4. Includes essential sections (installation, usage, examples)
5. Adds appropriate badges
6. Ensures PyPI compatibility

**Output:** Complete README file ready for `twine check` validation.

---

### Pattern 2: Fix Validation Errors

**When:** `twine check` reports errors or README doesn't render on PyPI.

**Request Format:**

```
Fix my README.[md/rst] PyPI validation errors:
[paste twine check output or describe errors]
```

**What Claude Does:**
1. Reads existing README
2. Identifies syntax or markup issues
3. Replaces Sphinx-specific syntax (if RST)
4. Fixes indentation, spacing, or structure
5. Validates changes conceptually
6. Suggests running `twine check` to verify

**Output:** Corrected README with PyPI-compliant markup.

---

### Pattern 3: Format Conversion

**When:** Need to switch between Markdown and reStructuredText.

**Request Format:**

```
Convert my README.md to README.rst
[or]
Convert my README.rst to README.md

Preserve all sections, code examples, and links.
```

**What Claude Does:**
1. Reads source README
2. Converts syntax while preserving semantics
3. Adjusts code blocks, links, emphasis, headers
4. Updates pyproject.toml configuration
5. Notes any features that don't translate directly

**Output:** Converted README in target format with configuration updates.

---

### Pattern 4: Sphinx Integration

**When:** Project uses Sphinx docs and needs PyPI-compatible README.

**Request Format:**

```
Set up sphinx-readme to generate README.rst from my Sphinx docs.
Source file: docs/index.rst
Output: README.rst in project root
```

**What Claude Does:**
1. Adds `sphinx-readme` to documentation dependencies
2. Configures `conf.py` with extension settings
3. Explains build process
4. Documents conversion behavior
5. Provides validation workflow

**Output:** Configured sphinx-readme with usage instructions.

---

### Pattern 5: Template Usage

**When:** Want to start with a proven structure.

**Request Format:**

```
Use the [Markdown/RST] template to create a README for '[package-name]'.
Customize for: [specific domain or features]
```

**What Claude Does:**
1. Accesses appropriate template from references
2. Adapts structure to package specifics
3. Customizes sections with relevant content
4. Maintains template quality standards
5. Includes domain-specific examples

**Output:** README based on template structure with customized content.

---

### Pattern 6: Validation Workflow

**When:** Need to validate README before publishing.

**Request Format:**

```
Show me how to validate my README before publishing to PyPI.
Include local testing and TestPyPI verification.
```

**What Claude Does:**
1. Provides step-by-step validation commands
2. Explains each validation tool
3. Shows expected outputs
4. Includes TestPyPI workflow
5. Documents troubleshooting steps

**Output:** Complete validation workflow with commands.

---

## Skill Reference Files

The skill includes three reference templates accessed automatically by Claude:

### 1. markdown-template.md

Production-ready Markdown template with:
- Modern badge configuration
- GitHub Flavored Markdown features
- Code examples with syntax highlighting
- Proper heading hierarchy
- Project URL structure

### 2. rst-template.rst

Production-ready reStructuredText template with:
- Proper section header hierarchy
- Standard docutils directives
- Admonitions and code blocks
- Grid and simple table syntax
- Link reference definitions

### 3. sphinx-readme-example.md

Guide for using sphinx-readme extension:
- Installation and configuration
- Conversion behavior explanation
- Build workflow integration
- Limitations and workarounds

---

## Best Practices for Requests

### Be Specific About Format

```
✓ GOOD: "Create a Markdown README for my package"
✗ VAGUE: "Create a README"
```

### Provide Package Context

```
✓ GOOD: "Package is a CLI tool for JSON validation, requires Python 3.11+"
✗ INSUFFICIENT: "Create a README for my package"
```

### Include Relevant Details

When requesting README creation, provide:
- Package name
- Brief description (1-2 sentences)
- Key features (3-5 bullets)
- Installation method
- Python version requirements
- License type
- Repository URL

### Specify Constraints

```
✓ GOOD: "Create README.md compatible with both PyPI and GitHub"
✓ GOOD: "Fix RST errors without using Sphinx roles"
✗ UNCLEAR: "Make it work on PyPI"
```

---

## Understanding Skill Behavior

### What the Skill Knows

The skill has comprehensive knowledge of:

1. **PyPI Requirements**
   - Format constraints (no Sphinx extensions in RST)
   - Validation tools (`twine check`, `rst2html.py`)
   - Content-type configuration
   - Publishing workflow

2. **Format Syntax**
   - Markdown (GFM and CommonMark variants)
   - reStructuredText (docutils directives only)
   - Cross-platform compatibility

3. **Best Practices**
   - Content structure and organization
   - Writing style for documentation
   - Validation workflows
   - Common pitfalls and solutions

4. **Tools Integration**
   - uv for package management
   - twine for validation and publishing
   - sphinx-readme for Sphinx integration
   - grip for Markdown preview
   - docutils for RST validation

### What the Skill Does Not Do

- Does not automatically publish packages (security)
- Does not access private repositories without credentials
- Does not generate API documentation (use Sphinx for that)
- Does not create CHANGELOG or LICENSE files (separate concerns)

---

## Combining with Other Skills

### uv Skill

For package management operations:

```
@uv build the package and @pypi-readme-creator validate the README
```

### hatchling Skill

For build configuration:

```
Configure hatchling as build backend and create PyPI-compliant README
```

### gitlab-skill

For GitLab-specific features:

```
Create README with GitLab Flavored Markdown features
```

---

## Troubleshooting Skill Activation

### Skill Not Activating

**Symptoms:** Claude doesn't use PyPI-specific guidance.

**Solutions:**
1. Be explicit: "Using the pypi-readme-creator skill, generate..."
2. Mention PyPI explicitly: "Create a README for PyPI publication"
3. Reference validation: "Create README that passes twine check"

### Wrong Format Generated

**Symptoms:** Got RST when wanted Markdown (or vice versa).

**Solutions:**
1. Specify format explicitly: "Create Markdown README"
2. Include file extension: "Generate README.md"
3. Clarify if unclear: "I need Markdown format, not RST"

### Missing Sections

**Symptoms:** README lacks important sections.

**Solutions:**
1. Request specific sections: "Include contributing and license sections"
2. Reference checklist: "Include all essential sections for PyPI"
3. Use template: "Use the Markdown template as base"

---

## Quality Expectations

When the skill generates or modifies README files, expect:

1. **PyPI Compliance**
   - Passes `twine check` validation
   - No Sphinx-specific syntax in RST
   - Proper content-type configuration

2. **Content Quality**
   - Clear, concise writing
   - Working code examples
   - Proper heading hierarchy
   - Essential sections included

3. **Format Correctness**
   - Valid syntax (Markdown or RST)
   - Proper code fence language specifiers
   - Correct indentation (especially RST)
   - Valid link syntax

4. **Platform Compatibility**
   - Renders correctly on PyPI
   - Compatible with GitHub/GitLab
   - Graceful degradation of platform-specific features

---

## Advanced Usage

### Custom pyproject.toml Configuration

Request specific content-type variants:

```
Configure pyproject.toml with CommonMark variant instead of GFM
```

### Multi-Platform Optimization

Optimize for multiple platforms:

```
Create README.md that works on PyPI, GitHub, and GitLab.
Note any platform-specific rendering differences.
```

### Batch Operations

Handle multiple files:

```
Review all README files in my monorepo packages and ensure
PyPI compliance for each.
```

### Migration Projects

Large-scale format changes:

```
Convert all project READMEs from RST to Markdown while
preserving existing content and ensuring PyPI compatibility.
```

---

## Related Documentation

- [Examples Guide](./examples.md) - Detailed usage examples
- [Technical Reference](./reference.md) - Format specifications and validation
- [README.md](../README.md) - Plugin overview

---

## Feedback and Improvements

The skill continuously improves based on:
- PyPI rendering engine updates
- New Python packaging standards
- Community best practices
- Tool ecosystem changes

If you encounter issues or have suggestions, report them via the repository issue tracker.
