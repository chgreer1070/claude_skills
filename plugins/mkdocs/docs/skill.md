# Skill Reference

## mkdocs

**Location**: `skills/mkdocs/SKILL.md`

**Description**: Comprehensive guide for creating and managing MkDocs documentation projects with Material theme. Includes official CLI command reference with complete parameters and arguments, and mkdocs.yml configuration reference with all available settings and valid values. Use when working with MkDocs projects including site initialization, mkdocs.yml configuration, Material theme customization, plugin integration, or building static documentation sites from Markdown files.

**User Invocable**: Yes (default)

**Allowed Tools**: Not restricted (inherits defaults)

**Model**: Not specified (inherits default)

### When to Use

Activate this skill when:
- Initializing new MkDocs documentation projects
- Configuring mkdocs.yml files with theme, plugins, or navigation
- Customizing Material for MkDocs theme (colors, fonts, features)
- Integrating plugins (mkdocstrings, gen-files, literate-nav)
- Setting up deployment workflows (GitHub Actions, GitLab CI)
- Troubleshooting MkDocs build errors or warnings
- Migrating documentation from other systems
- User mentions "MkDocs", "Material theme", "documentation site", or "static docs"

### Activation

```
@mkdocs
```

or

```
Skill(command: "mkdocs")
```

### Hooks

This skill does not configure hooks.

### Reference Files

The skill provides progressive disclosure through five comprehensive reference files:

#### [cli_reference.md](../skills/mkdocs/references/cli_reference.md)

Complete command-line interface documentation for all MkDocs commands.

**Contents**:
- Global options (--version, --quiet, --verbose)
- `mkdocs build` - Build the documentation site
- `mkdocs serve` - Run development server with live reload
- `mkdocs new` - Create new MkDocs project
- `mkdocs gh-deploy` - Deploy to GitHub Pages
- `mkdocs get-deps` - Show required dependencies

**Key Information**:
- All command options with defaults
- Environment variable support (!ENV tag syntax)
- Common workflows (local development, GitHub Pages deployment, multi-language docs)
- Exit codes and error handling
- Configuration file detection order

**When Referenced**: CLI command syntax, deployment procedures, development server configuration

**Source**: [MkDocs CLI Documentation](https://www.mkdocs.org/user-guide/cli/) (accessed 2026-01-18)

---

#### [configuration_reference.md](../skills/mkdocs/references/configuration_reference.md)

Complete mkdocs.yml configuration schema with all available settings.

**Contents**:
- Project information (site_name, site_url, site_description, repo_url)
- Navigation structure (nav, exclude_docs, draft_docs, not_in_nav)
- Theme configuration (name, palette, features, fonts)
- CSS and JavaScript customization
- Markdown extensions
- Plugins configuration
- Validation settings
- Environment variables and path references
- Configuration inheritance (INHERIT)

**Key Information**:
- Required vs optional settings
- Default values for all options
- Valid value types and constraints
- Complete theme configuration examples
- Plugin configuration patterns

**When Referenced**: Creating or modifying mkdocs.yml, theme customization, navigation setup, validation configuration

**Source**: [MkDocs Configuration Guide](https://www.mkdocs.org/user-guide/configuration/) (accessed 2026-01-18)

---

#### [material_theme_reference.md](../skills/mkdocs/references/material_theme_reference.md)

Comprehensive Material for MkDocs theme configuration and features.

**Contents**:
- Installation instructions
- Color schemes and palettes (light/dark mode, custom colors)
- Typography and fonts (Google Fonts, custom fonts)
- Navigation configuration (tabs, sections, instant loading, tracking)
- Search features (suggestions, highlighting, boosting)
- Header and footer customization
- Social cards configuration
- Analytics integration (Google Analytics, feedback widgets)
- Version management with mike
- Privacy and cookie consent
- Git repository integration
- Language configuration and i18n
- Built-in plugins (search, tags, social, blog, offline)
- Page metadata (front matter options)
- Icons and logos
- Advanced features (custom directory, admonitions, code highlighting, diagrams)

**Key Information**:
- Complete feature flags reference
- Theme palette configuration patterns
- Navigation feature combinations
- Plugin integration examples
- Best practices for performance, SEO, accessibility, privacy

**When Referenced**: Material theme setup, feature enablement, color/font customization, navigation structure, social cards, analytics

**Source**: [Material for MkDocs Documentation](https://squidfunk.github.io/mkdocs-material/) (accessed 2026-01-18)

---

#### [plugins_reference.md](../skills/mkdocs/references/plugins_reference.md)

Configuration reference for essential MkDocs plugins.

**Contents**:
- **mkdocstrings** - API documentation from docstrings (Python, C++)
- **mkdocs-gen-files** - Programmatically generate documentation pages
- **mkdocs-literate-nav** - Specify navigation in Markdown (SUMMARY.md)
- **mkdoxy** - Doxygen documentation integration for C/C++
- **mkdocs-typer2** - Typer CLI application documentation
- **mermaid2** - Mermaid diagram rendering
- **termynal** - Terminal session animations
- **mkdocs-git-latest-changes-plugin** - Recently updated pages

**Key Information**:
- Installation commands for each plugin
- Complete configuration options with defaults
- Usage examples in markdown
- Common patterns and best practices
- Multi-plugin configuration examples
- Performance considerations
- Version pinning recommendations

**When Referenced**: Plugin installation, API documentation generation, navigation automation, diagram integration, CLI documentation

**Sources**: Official documentation for each plugin (mkdocstrings.github.io, oprypin.github.io/mkdocs-gen-files, etc.) (accessed 2026-01-18)

---

#### [real_world_examples.md](../skills/mkdocs/references/real_world_examples.md)

Production MkDocs implementations and deployment workflows.

**Contents**:
- Active GitHub repositories using MkDocs (FastAPI, Pydantic, Django REST Framework, Material for MkDocs)
- Active GitLab repositories and examples
- GitHub Actions workflows (basic, advanced, multi-version)
- GitLab CI configurations (basic, Docker-based, multi-environment)
- CI/CD patterns and best practices
- Production site examples with notable features

**Key Information**:
- Real workflow YAML configurations from major projects
- Path-based trigger patterns
- Dependency management strategies
- Security best practices (permissions, concurrency)
- Multi-version documentation with mike
- Preview deployment patterns
- Caching strategies
- Docker image usage

**When Referenced**: CI/CD setup, deployment automation, workflow optimization, production patterns, real-world implementations

**Sources**:
- Public GitHub repositories: [fastapi/fastapi](https://github.com/fastapi/fastapi), [pydantic/pydantic](https://github.com/pydantic/pydantic), [squidfunk/mkdocs-material](https://github.com/squidfunk/mkdocs-material), [google/timesketch](https://github.com/google/timesketch), [MichaelCade/90DaysOfDevOps](https://github.com/MichaelCade/90DaysOfDevOps), etc.
- GitLab Pages examples: [gitlab.com/pages/mkdocs](https://gitlab.com/pages/mkdocs)
- Live production sites linked in file
(accessed 2026-01-18)

---

## Skill Structure

This skill follows a **Reference/Guidelines** pattern optimized for lookup and context-aware assistance:

1. **Progressive Disclosure**: Reference files loaded on-demand to avoid context pollution
2. **Comprehensive Coverage**: Complete documentation for CLI, configuration, theme, and plugins
3. **Real-World Validation**: Examples sourced from production implementations
4. **Source Attribution**: All information cited from official documentation or verified repositories

## Usage Patterns

### Pattern 1: Project Initialization

**User Query**: "Set up a new documentation site with MkDocs and Material theme"

**Skill Behavior**:
1. References cli_reference.md for `mkdocs new` command
2. References material_theme_reference.md for basic theme configuration
3. Provides step-by-step setup instructions
4. Suggests common features for initial configuration

### Pattern 2: Configuration Assistance

**User Query**: "Configure navigation tabs and a table of contents in the sidebar"

**Skill Behavior**:
1. References configuration_reference.md for nav structure
2. References material_theme_reference.md for theme features
3. Shows exact YAML configuration with feature flags
4. Explains feature interactions

### Pattern 3: Plugin Integration

**User Query**: "Add API documentation generation from my Python docstrings"

**Skill Behavior**:
1. References plugins_reference.md for mkdocstrings configuration
2. Provides installation command
3. Shows complete plugin configuration options
4. Demonstrates usage syntax in markdown

### Pattern 4: Deployment Setup

**User Query**: "Deploy my docs to GitHub Pages automatically"

**Skill Behavior**:
1. References cli_reference.md for gh-deploy command
2. References real_world_examples.md for GitHub Actions workflows
3. Provides complete workflow YAML
4. Explains GitHub Pages settings

### Pattern 5: Troubleshooting

**User Query**: "Build fails with 'page not found in navigation' warning"

**Skill Behavior**:
1. References configuration_reference.md for validation settings
2. Explains nav configuration requirements
3. Shows how to exclude or mark pages with not_in_nav
4. Recommends strict mode for CI/CD

## Skill Metadata

**Character Budget**: Not specified (reference files total ~65KB)

**Context Strategy**: Progressive disclosure - reference files loaded only when relevant to user query

**Update Frequency**: Reference files should be updated when MkDocs or Material theme release major versions with new features

**Verification Status**:
- CLI reference verified against MkDocs 1.6+ official documentation
- Configuration reference verified against official schema
- Material theme reference verified against Material for MkDocs 9.x documentation
- Plugins reference verified against current plugin documentation
- Real-world examples verified from public repositories (stars and workflow files confirmed)

## Related Skills

This skill complements:
- **python3-development** - When documenting Python packages with mkdocstrings
- **git** - When setting up GitHub/GitLab deployment workflows
- **yaml-configuration** - When editing mkdocs.yml files
- **ci-cd** - When configuring automated builds and deployments

## Maintenance Notes

**Last Updated**: 2026-01-18

**Known Limitations**:
- SKILL.md template not completed (TODO markers present)
- No hooks configured
- No scripts or assets bundled

**Future Enhancements**:
- Add migration guides (Sphinx, Jekyll, Hugo → MkDocs)
- Include theme comparison guide
- Add troubleshooting decision tree
- Expand plugin coverage (mike, macros, etc.)
- Add template mkdocs.yml files for common use cases
