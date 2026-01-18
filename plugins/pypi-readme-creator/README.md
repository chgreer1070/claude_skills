# PyPI README Creator

Generate professional, PyPI-compliant README files in Markdown or reStructuredText that render correctly on PyPI, GitHub, GitLab, and BitBucket.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add jamie-bitflight/claude_skills
/plugin install pypi-readme-creator@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/pypi-readme-creator
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [pypi-readme-creator](./skills/pypi-readme-creator/SKILL.md) | When creating a README for a Python package. When preparing a package for PyPI publication. When README renders incorrectly on PyPI. When choosing between README.md and README.rst. When running twine check and seeing rendering errors. When configuring readme field in pyproject.toml. |

## Quick Start

When preparing a Python package for PyPI publication, activate this skill to get guidance on README creation:

```text
@pypi-readme-creator

I'm publishing a Python package to PyPI. I need a README that:
- Works on both PyPI and GitHub
- Includes installation instructions
- Shows code examples with syntax highlighting
- Passes twine check validation

My package is a CLI tool using Typer and Rich.
```

The skill provides:
- Format selection guidance (Markdown vs reStructuredText)
- Essential README sections and content structure
- Format-specific syntax examples
- PyPI integration with pyproject.toml
- Validation workflow with `twine check`
- Common issues and solutions

For complete templates and examples, see the [reference files](./skills/pypi-readme-creator/references/) included with this skill.

## License

See individual skill files for license information.
