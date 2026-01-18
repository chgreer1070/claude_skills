# Hatchling Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-Unknown-lightgrey) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

Comprehensive documentation for Hatchling, the modern Python build backend that implements PEP 517/518/621/660 standards. This plugin provides Claude with expert knowledge of Hatchling configuration, build system setup, Python packaging, and troubleshooting.

## Features

- **Complete Hatchling Reference** - Detailed documentation covering all aspects of Hatchling build backend
- **Standards Compliance** - PEP 517/518/621/660 implementation guidance
- **Configuration Expertise** - pyproject.toml setup, metadata, dependencies, entry points
- **Build Customization** - Build hooks, version management, file selection patterns
- **Plugin System** - Extensibility through builders, hooks, and metadata plugins
- **Migration Support** - Setuptools migration guidance and compatibility information
- **Troubleshooting** - Error handling, validation, and common issue resolution

## Installation

### Prerequisites

- Claude Code version 2.1 or higher
- Python project using or planning to use Hatchling as build backend

### Install Plugin

```bash
# Method 1: If published to marketplace
cc plugin install hatchling

# Method 2: Manual installation from local path
git clone <repository-url> ~/.claude/plugins/hatchling
cc plugin reload
```

## Quick Start

After installation, Claude automatically uses the Hatchling skill when you work on Python packaging tasks:

```text
User: Help me configure Hatchling for my Python package

Claude: I'll help you set up Hatchling as your build backend.
First, let's create a pyproject.toml with the build system configuration...
```

Or explicitly activate the skill:

```text
@hatchling

Configure a Python package with:
- Package metadata
- Entry points for CLI tools
- Build hooks for version management
```

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | hatchling | Comprehensive Hatchling documentation for build configuration, packaging, version management, and troubleshooting | `@hatchling` or automatic |

## Usage

### Skill: hatchling

**User Invocable**: Yes (default)

**When Claude Uses This Skill**:
- Working with Hatchling configuration
- Setting up Python build systems
- Configuring pyproject.toml for packaging
- Managing project metadata and dependencies
- Setting up entry points (CLI tools, plugins)
- Implementing build hooks
- Managing versions (code, regex, environment sources)
- Building wheel and source distributions
- Migrating from setuptools
- Troubleshooting Hatchling build errors
- Implementing custom plugins or builders

**Reference Documentation Structure**:

The skill includes 20+ reference documents organized by topic:

- **Project Configuration**: Metadata, dependencies, entry points, dynamic fields
- **Build Targets**: Wheel, sdist, binary, custom builders
- **File Selection**: Git-style patterns, VCS integration, include/exclude
- **Build Hooks**: Custom hooks, version hooks, build data passing
- **Version Management**: Multiple sources, schemes, validation
- **Plugin System**: Builders, hooks, metadata plugins, extensibility
- **Build Environment**: Dependencies, UV vs pip, Cython integration
- **Integration**: PEP standards, setuptools migration, CMake/extensions
- **Special Features**: Type hints (PEP 561), namespace packages, src-layout
- **Standards**: Python packaging overview, PEP references, distribution formats
- **Operations**: CLI building, error handling, release notes

**Activation**:

```text
@hatchling
```

Or use the Skill tool:

```text
Skill(command: "hatchling")
```

## Configuration Examples

### Example 1: Basic Python Package Setup

**Scenario**: Setting up Hatchling for a new Python package

**User Request**:
```text
Help me configure Hatchling for my Python package "myapp" with a CLI entry point
```

**What Claude Does**:
1. Activates the hatchling skill
2. References project metadata configuration
3. Creates pyproject.toml with:
   - Build system configuration
   - Package metadata
   - CLI entry point
   - Appropriate file selection patterns

**Result**: Complete pyproject.toml ready for building and distribution

---

### Example 2: Dynamic Version Management

**Scenario**: Configure version from source code file

**User Request**:
```text
@hatchling

Set up dynamic version reading from __version__ in my package's __init__.py
```

**What Claude Does**:
1. References version management documentation
2. Configures `[tool.hatch.version]` section
3. Sets up version source and path
4. Explains version validation and schemes

**Result**: Automatic version detection from source code

---

### Example 3: Custom Build Hook

**Scenario**: Implement build hook to generate code during build

**User Request**:
```text
I need to run a code generator during the build process. How do I set this up with Hatchling?
```

**What Claude Does**:
1. References build hooks documentation
2. Explains hook interface and execution order
3. Provides custom hook implementation example
4. Configures hook in pyproject.toml
5. Shows how to pass data between hooks

**Result**: Working build hook that generates code during wheel/sdist creation

---

### Example 4: Setuptools Migration

**Scenario**: Migrate existing setup.py project to Hatchling

**User Request**:
```text
Help me migrate my project from setuptools to Hatchling
```

**What Claude Does**:
1. References integration and migration documentation
2. Analyzes current setup.py configuration
3. Converts to pyproject.toml format
4. Identifies setuptools-specific features
5. Provides Hatchling equivalents or alternatives
6. Explains compatibility considerations

**Result**: Complete migration plan with new pyproject.toml

---

### Example 5: Troubleshooting Build Errors

**Scenario**: Debug Hatchling build failure

**User Request**:
```text
Getting "No files found for inclusion" error when building with Hatchling
```

**What Claude Does**:
1. References error handling and file selection documentation
2. Explains VCS integration requirements
3. Identifies common causes (missing .gitignore, force-include needed)
4. Provides diagnostic steps
5. Shows configuration fixes

**Result**: Clear explanation and fix for the build error

## Troubleshooting

### Skill Not Activating

If Claude doesn't automatically use the Hatchling skill:

1. **Explicitly activate**: Use `@hatchling` in your prompt
2. **Use trigger keywords**: Mention "Hatchling", "pyproject.toml", "Python packaging", "build backend"
3. **Verify installation**: Run `cc plugin list` to confirm plugin is installed and enabled

### Reference Files Not Loading

The skill uses progressive disclosure - reference files are loaded on demand:

- Claude loads specific references when needed for your question
- You can explicitly reference documentation: "Check the build hooks reference"
- All 20+ reference files are available through navigation from SKILL.md

### Build Configuration Issues

When working on Hatchling configuration:

- Provide your current pyproject.toml for context
- Specify your Python version and packaging goals
- Mention any migration context (from setuptools, poetry, etc.)
- Share specific error messages for troubleshooting

## Documentation Organization

The plugin's skill includes comprehensive reference documentation:

```
skills/hatchling/
├── SKILL.md                           # Main skill definition
└── references/                        # Progressive disclosure references
    ├── project-metadata/              # Package metadata configuration
    ├── build-system/                  # Build backend setup
    ├── wheel-target/                  # Wheel build configuration
    ├── sdist-target/                  # Source distribution config
    ├── build-targets/                 # Target types and builders
    ├── target-config/                 # Target-specific configuration
    ├── file-selection/                # Pattern matching and VCS
    ├── build-hooks/                   # Hook system and custom hooks
    ├── advanced-features/             # Advanced build features
    ├── version-management/            # Version sources and schemes
    ├── metadata-hooks/                # Metadata customization
    ├── context-formatting/            # Dynamic configuration
    ├── plugins/                       # Plugin system
    ├── build-environment/             # Build environment internals
    ├── integration/                   # PEP compliance and migration
    ├── special-config/                # Special features (PEP 561, etc.)
    ├── core-concepts/                 # Architecture and principles
    ├── standards/                     # PEP references and specs
    ├── cli-building/                  # Command-line usage
    ├── error-handling/                # Validation and troubleshooting
    └── release-notes/                 # Version history
```

## Related Resources

### Official Hatchling Documentation
- [Hatchling Documentation](https://hatch.pypa.io/latest/config/build/)
- [Hatch Project](https://hatch.pypa.io/)

### Python Packaging Standards
- [PEP 517 - Build System Interface](https://peps.python.org/pep-0517/)
- [PEP 518 - Build System Dependencies](https://peps.python.org/pep-0518/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [PEP 660 - Editable Installs](https://peps.python.org/pep-0660/)

### Python Packaging Guide
- [PyPA Packaging Guide](https://packaging.python.org/)

## Contributing

To contribute to this plugin:

1. Fork the repository
2. Create a feature branch
3. Add or update reference documentation
4. Ensure all markdown follows formatting standards
5. Test with Claude Code
6. Submit a pull request

### Adding Reference Documentation

When adding new reference files:

- Place in appropriate `references/` subdirectory
- Use markdown with proper heading hierarchy
- Include code examples with language specifiers
- Link from SKILL.md main reference list
- Follow the existing documentation structure

## License

License information not specified in plugin.json.

## Credits

Plugin maintained as part of the Claude Code skills repository.

---

**Plugin Version**: 1.0.0
**Claude Code Compatibility**: 2.1+
**Last Updated**: 2026-01-18
