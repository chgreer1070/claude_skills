# Documentation Index

This document provides an overview of all documentation files in the pypi-readme-creator plugin.

## Primary Documentation

### README.md

**Purpose:** Main entry point for the plugin

**Contents:**
- Overview and features
- Installation instructions
- Quick start guide
- Capabilities table
- Usage guidelines
- Configuration examples
- Quick troubleshooting
- Links to supplementary docs

**Audience:** All users (first-time and experienced)

**When to read:** Always start here for an overview

---

## Supplementary Documentation (docs/)

### docs/examples.md

**Purpose:** Detailed, real-world usage examples

**Contents:**
- 7 comprehensive usage scenarios
- Step-by-step workflows
- Before/after code examples
- Expected outputs and results

**Examples Included:**
1. New Python Package - Complete README
2. Sphinx Documentation to PyPI README
3. Fix Existing README with Validation Errors
4. Convert Markdown to reStructuredText
5. Add GitHub Flavored Markdown Features
6. Local Testing Workflow
7. Template-Based Quick Start

**Audience:** Users needing concrete examples for specific tasks

**When to read:** When you have a specific README creation or fixing task

---

### docs/reference.md

**Purpose:** Complete technical reference

**Contents:**
- Format specifications (Plain Text, RST, Markdown)
- pyproject.toml configuration options
- Validation tools (twine, readme_renderer, docutils, grip)
- Publishing workflow
- Sphinx integration details
- Format comparison table
- Best practices
- Common issues and solutions
- External resource links

**Audience:** Users needing technical details, format constraints, or validation information

**When to read:**
- When troubleshooting validation errors
- When configuring pyproject.toml
- When understanding format differences
- When integrating with Sphinx

---

### docs/skill-usage.md

**Purpose:** Guide for using the skill with Claude Code

**Contents:**
- Skill overview and activation triggers
- Usage patterns with examples
- Best practices for requests
- Understanding skill behavior
- Combining with other skills
- Troubleshooting skill activation
- Quality expectations
- Advanced usage

**Audience:** Claude Code users wanting to optimize their interaction with the skill

**When to read:**
- When skill doesn't activate as expected
- When learning how to phrase requests effectively
- When combining with other skills
- When understanding what the skill can and cannot do

---

## Reference Files (skills/pypi-readme-creator/references/)

These files are accessed automatically by Claude when the skill is activated.

### markdown-template.md

**Purpose:** Production-ready Markdown README template

**Contents:**
- Complete README structure
- Badge examples
- Installation section
- Usage examples with code
- GFM features
- Proper formatting

**When used:** Template-based README generation requests

---

### rst-template.rst

**Purpose:** Production-ready reStructuredText README template

**Contents:**
- Complete README structure
- RST directives and roles
- Admonitions
- Code blocks
- Tables (grid and simple)
- Link references

**When used:** Template-based RST README generation requests

---

### sphinx-readme-example.md

**Purpose:** Guide for sphinx-readme extension

**Contents:**
- Installation instructions
- Configuration examples
- Conversion behavior
- Build workflow
- Limitations and workarounds

**When used:** Sphinx integration requests

---

## Quick Navigation Guide

**I want to...**

- **Get started quickly** → [README.md](./README.md) Quick Start section
- **See concrete examples** → [docs/examples.md](./docs/examples.md)
- **Understand format requirements** → [docs/reference.md](./docs/reference.md) Supported Formats section
- **Validate my README** → [docs/reference.md](./docs/reference.md) Validation Tools section
- **Fix validation errors** → [docs/examples.md](./docs/examples.md) Example 3 + [docs/reference.md](./docs/reference.md) Common Issues
- **Set up Sphinx integration** → [docs/examples.md](./docs/examples.md) Example 2 + [docs/reference.md](./docs/reference.md) Sphinx Integration
- **Learn how to phrase requests** → [docs/skill-usage.md](./docs/skill-usage.md) Usage Patterns
- **Troubleshoot skill activation** → [docs/skill-usage.md](./docs/skill-usage.md) Troubleshooting
- **Understand format differences** → [docs/reference.md](./docs/reference.md) Format Comparison
- **Publish to PyPI** → [docs/reference.md](./docs/reference.md) Publishing Workflow

---

## Documentation Quality Standards

All documentation in this plugin follows these standards:

### Markdown Quality
- All code fences have language specifiers
- Blank lines before and after code blocks
- Proper heading hierarchy (no skipped levels)
- Relative links for internal navigation

### Content Quality
- Concrete examples over abstract descriptions
- Clear, concise technical writing
- Active voice and present tense
- Tested commands and code snippets

### Structure
- Clear table of contents in main README
- Cross-references between documents
- Progressive complexity (basic → advanced)
- Consistent formatting throughout

---

## Maintenance Notes

**Last Updated:** 2026-01-18

**Version:** 1.0.0

**Documentation Coverage:**
- ✓ Installation guide
- ✓ Quick start examples
- ✓ Detailed usage examples (7 scenarios)
- ✓ Technical reference
- ✓ Skill usage guide
- ✓ Troubleshooting
- ✓ Format specifications
- ✓ Validation workflows
- ✓ Tool integration guides

**Known Gaps:** None

---

## Contributing to Documentation

When updating documentation:

1. **Verify accuracy** - Test all commands and examples
2. **Update version numbers** - Keep references current
3. **Check links** - Ensure all internal and external links work
4. **Follow standards** - Maintain quality standards listed above
5. **Update this index** - If adding new documentation files

---

## External Resources

For official documentation beyond this plugin:

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI README Guide](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/)
- [readme_renderer GitHub](https://github.com/pypa/readme_renderer)
- [sphinx-readme Documentation](https://sphinx-readme.readthedocs.io/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)
