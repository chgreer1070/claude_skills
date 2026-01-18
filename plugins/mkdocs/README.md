# MkDocs Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Comprehensive MkDocs documentation plugin for Claude Code. Provides complete reference guides for MkDocs CLI commands, configuration options, Material theme customization, plugin integration, and real-world deployment examples.

## Features

- **Complete CLI Reference** - All MkDocs commands with options, arguments, and examples
- **Configuration Guide** - Full mkdocs.yml schema with every available setting
- **Material Theme Documentation** - Comprehensive Material for MkDocs theme customization
- **Plugin Integration** - Reference for mkdocstrings, gen-files, literate-nav, mkdoxy, and more
- **Real-World Examples** - Production deployment workflows for GitHub Actions and GitLab CI

## Installation

### Prerequisites

- Claude Code 2.1+

### Install Plugin

```bash
# Using Claude Code plugin system
cc plugin install mkdocs

# Manual installation
git clone <repository-url> ~/.claude/plugins/mkdocs
cc plugin reload
```

## Quick Start

Activate the skill when working with MkDocs projects:

```
@mkdocs help me set up a new documentation site with Material theme
```

The skill automatically provides context-aware guidance for:
- Initializing new MkDocs projects
- Configuring mkdocs.yml files
- Customizing Material theme features
- Integrating plugins like mkdocstrings
- Setting up CI/CD deployment

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | mkdocs | Comprehensive MkDocs reference including CLI commands, configuration schema, Material theme options, plugin documentation, and deployment workflows | `@mkdocs` or `Skill(command: "mkdocs")` |

## Usage

### Working with MkDocs Configuration

```
@mkdocs I need to configure navigation with tabs and a table of contents
```

Claude will reference the Material theme configuration guide to help you set up:
- `theme.features` for navigation tabs
- TOC integration options
- Section organization

### CLI Command Help

```
@mkdocs How do I deploy to GitHub Pages with a custom domain?
```

Claude will provide:
- Complete `mkdocs gh-deploy` command reference
- GitHub Actions workflow examples
- Custom domain configuration (CNAME file)

### Plugin Integration

```
@mkdocs Set up mkdocstrings to auto-generate API docs from my Python package
```

Claude will guide you through:
- Plugin installation and configuration
- Handler options for Python docstrings
- Usage syntax in markdown files
- Cross-reference inventory setup

### Theme Customization

```
@mkdocs I want dark mode with a custom color palette
```

Claude will show you:
- Multiple palette configuration with toggle
- System preference detection
- Custom color scheme definitions
- CSS variable overrides

## Reference Documentation

The skill includes five comprehensive reference files:

### [CLI Reference](./skills/mkdocs/references/cli_reference.md)

Complete documentation for all MkDocs commands:
- `mkdocs new` - Create new projects
- `mkdocs serve` - Development server with live reload
- `mkdocs build` - Build static site
- `mkdocs gh-deploy` - Deploy to GitHub Pages
- `mkdocs get-deps` - List required dependencies

SOURCE: [MkDocs CLI Documentation](https://www.mkdocs.org/user-guide/cli/)

### [Configuration Reference](./skills/mkdocs/references/configuration_reference.md)

Complete mkdocs.yml schema with all available settings:
- Project information (site_name, site_url, repo_url)
- Navigation and page structure
- Theme configuration
- Plugin configuration
- Markdown extensions
- Validation settings

SOURCE: [MkDocs Configuration](https://www.mkdocs.org/user-guide/configuration/)

### [Material Theme Reference](./skills/mkdocs/references/material_theme_reference.md)

Comprehensive Material for MkDocs theme documentation:
- Color schemes and palettes
- Typography and fonts
- Navigation features (tabs, sections, instant loading)
- Search configuration
- Social cards
- Analytics integration
- Version management with mike

SOURCE: [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

### [Plugins Reference](./skills/mkdocs/references/plugins_reference.md)

Documentation for essential MkDocs plugins:
- **mkdocstrings** - API documentation from docstrings
- **mkdocs-gen-files** - Programmatically generate pages
- **mkdocs-literate-nav** - Navigation in Markdown
- **mkdoxy** - C/C++ Doxygen integration
- **mkdocs-typer2** - Typer CLI documentation
- **mermaid2** - Diagram support
- **termynal** - Terminal animations
- **git-latest-changes** - Recently updated pages

SOURCES: Plugin-specific official documentation linked in reference file

### [Real-World Examples](./skills/mkdocs/references/real_world_examples.md)

Production deployments and CI/CD workflows:
- Active GitHub repositories using MkDocs (FastAPI, Pydantic, Material for MkDocs)
- GitHub Actions workflows (basic, multi-version, preview deployments)
- GitLab CI configurations (Docker images, caching, multi-environment)
- Best practices for path-based triggers, dependency management, and security

SOURCES: Public GitHub and GitLab repositories (links provided in reference file)

## Examples

### Example 1: Create New Documentation Site

**Scenario**: Start a new documentation project with Material theme

**Steps**:
1. Activate the mkdocs skill
2. Ask for guidance on project structure
3. Receive complete setup instructions

**Code**:
```bash
# Create new project
mkdocs new my-project
cd my-project

# Install Material theme
pip install mkdocs-material

# Configure mkdocs.yml
cat > mkdocs.yml << EOF
site_name: My Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
EOF

# Start development server
mkdocs serve
```

**Result**: Fully configured MkDocs project with Material theme and modern features

---

### Example 2: Deploy to GitHub Pages

**Scenario**: Set up automated deployment to GitHub Pages using GitHub Actions

**Steps**:
1. Ask for GitHub Actions workflow example
2. Receive complete workflow configuration
3. Configure GitHub Pages settings

**Code**:
```yaml
# .github/workflows/docs.yml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install mkdocs-material
          pip install mkdocs-minify-plugin

      - name: Build site
        run: mkdocs build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

**Result**: Automated documentation deployment on every push to main branch

---

### Example 3: API Documentation with mkdocstrings

**Scenario**: Generate API documentation from Python docstrings

**Steps**:
1. Ask for mkdocstrings setup
2. Configure plugin in mkdocs.yml
3. Use autodoc syntax in markdown

**Code**:

mkdocs.yml:
```yaml
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true
            show_signature_annotations: true

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
```

docs/api/reference.md:
```markdown
# API Reference

## Core Module

::: mypackage.core
    options:
      members:
        - MyClass
        - my_function
      show_source: false
```

**Result**: Auto-generated API documentation with docstrings, signatures, and examples

## Troubleshooting

### Build Warnings in Strict Mode

**Issue**: `mkdocs build --strict` fails with navigation warnings

**Solution**: Review validation settings in mkdocs.yml:
```yaml
validation:
  nav:
    omitted_files: warn
    not_found: warn
  links:
    not_found: warn
```

### Plugin Not Found

**Issue**: Error message "Error: MkDocs encountered an error loading plugin 'plugin-name'"

**Solution**:
```bash
# Install missing plugin
pip install mkdocs-plugin-name

# Verify installation
mkdocs get-deps
```

### Theme Not Loading

**Issue**: Site displays without styling

**Solution**: Ensure theme is installed and configured correctly:
```bash
pip install mkdocs-material

# In mkdocs.yml
theme:
  name: material  # Must match installed theme
```

### GitHub Pages 404

**Issue**: Site deploys but shows 404 error

**Solution**: Check GitHub Pages settings in repository:
1. Settings → Pages → Source should be "GitHub Actions"
2. Ensure workflow has correct permissions
3. Verify `site_url` in mkdocs.yml matches GitHub Pages URL

## Contributing

Contributions welcome! Areas for improvement:
- Additional plugin documentation
- More CI/CD workflow examples
- Theme customization recipes
- Migration guides from other documentation systems

## License

This plugin provides reference documentation. MkDocs is licensed under BSD 2-Clause License. Material for MkDocs is licensed under MIT License.

## Credits

Documentation compiled from official sources:
- [MkDocs Project](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) by Martin Donath
- Plugin documentation from respective maintainers
- Real-world examples from public repositories

Plugin maintained by the Claude Code community.
