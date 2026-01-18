# clang-format Configuration Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-unspecified-gray) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A comprehensive Claude Code plugin for configuring, analyzing, and troubleshooting clang-format code formatting. Includes ready-to-use templates, integration scripts, and extensive reference documentation.

## Features

- **Automated Code Style Analysis** - Generate clang-format configurations that match existing codebases with minimal disruption
- **Impact-Driven Configuration** - Test and score configuration changes to minimize merge conflicts and code review noise
- **7 Ready-to-Use Templates** - Pre-configured styles for Google C++, Linux Kernel, Modern C++17/20, and more
- **Editor Integration** - Pre-built scripts for Vim, Emacs, and git hooks
- **Comprehensive Documentation** - 194 style options organized by category with examples
- **Multi-Language Support** - Configure C++, Java, JavaScript, and more in a single file

## Installation

### Prerequisites

- Claude Code 2.1 or later
- clang-format tool installed on your system

```bash
# Verify clang-format installation
clang-format --version
```

### Install Plugin

```bash
# From a Claude Code marketplace (if published)
cc plugin install clang-format

# Manual installation
git clone <repository-url> ~/.claude/plugins/clang-format
cc plugin reload
```

## Quick Start

The plugin activates automatically when you mention clang-format or request code style analysis:

```
Analyze the code style in src/ and generate a matching .clang-format configuration
```

Claude will:
1. Examine your code samples for formatting patterns
2. Generate multiple configuration hypotheses
3. Test each against representative files
4. Score configurations by their impact (line changes vs whitespace changes)
5. Present the minimal-disruption configuration with detailed comparison

## Capabilities

| Type | Name | Description | Invocation |
|------|------|-------------|------------|
| Skill | clang-format Configuration | Configures clang-format using templates, analyzes existing code style, troubleshoots formatting issues | Auto-invoked when discussing clang-format, code formatting, or style configuration |

## Usage

### Analyzing Existing Code Style

The most powerful feature of this plugin is generating configurations that match your existing codebase:

```
Generate a .clang-format file that matches the style in src/core/
```

Claude will:
- Systematically examine brace placement, indentation, spacing, and alignment
- Test multiple configuration hypotheses
- Use weighted scoring to find the minimal-impact configuration:
  - Line count changes (weight: 10) - highest impact on merges and diffs
  - Whitespace changes (weight: 1) - lower impact, aesthetic only
- Present comparison tables showing all tested configurations
- Provide example diffs and test commands
- Wait for your approval before finalizing

For detailed workflow documentation, see [Skills Reference](./docs/skills.md).

### Creating New Configurations

Start from pre-built templates:

```
I need a .clang-format file using Google C++ style with 120 column limit
```

Available templates:
- `google-cpp-modified.clang-format` - Google C++ style, 4-space indent, 120 columns
- `linux-kernel.clang-format` - Linux kernel standards (tabs, K&R braces)
- `microsoft-visual-studio.clang-format` - Microsoft/Visual Studio conventions
- `modern-cpp17-20.clang-format` - Modern C++17/20 with contemporary idioms
- `compact-dense.clang-format` - Space-efficient style
- `readable-spacious.clang-format` - Spacious style prioritizing readability
- `multi-language.clang-format` - Multi-language configuration

### Troubleshooting Formatting

When formatting produces unexpected results:

```
clang-format is putting braces in the wrong place. Why is this happening?
```

Claude will:
- Verify configuration detection with `--dump-config`
- Identify the affected formatting category
- Consult relevant reference documentation
- Suggest configuration changes to achieve desired formatting

### Setting Up Editor Integration

```
Set up format-on-save in Vim for C++ files
```

Claude provides integration scripts for:
- **Vim** - Format on save configuration
- **Emacs** - clang-format integration
- **Git hooks** - Automatic formatting of staged files (pre-commit/prek compatible)

## Bundled Resources

The skill includes extensive bundled resources accessible through Claude:

### Configuration Templates

Located in `skills/clang-format/assets/configs/`:
- 7 ready-to-use `.clang-format` templates
- Optimized for common scenarios and style guides
- Fully commented and customizable

### Integration Scripts

Located in `skills/clang-format/assets/integrations/`:
- `pre-commit` - Git hook for automatic formatting (supports pre-commit and prek frameworks)
- `vimrc-clang-format.vim` - Vim format-on-save configuration
- `emacs-clang-format.el` - Emacs integration

### Reference Documentation

Located in `skills/clang-format/references/`:

**Quick Navigation:**
- `index.md` - Documentation hub and overview
- `quick-reference.md` - Complete working configurations with explanations
- `cli-usage.md` - Command-line usage, editor setup, CI/CD integration

**Option Categories (01-09.md):**
1. Alignment - Vertical alignment of declarations, assignments, operators
2. Breaking - Line breaking and wrapping rules
3. Braces - Brace placement styles (K&R, Allman, GNU, etc.)
4. Indentation - Indentation rules and special cases
5. Spacing - Whitespace control around operators, keywords
6. Includes - Include/import organization and sorting
7. Languages - Language-specific options (C++, Java, JavaScript)
8. Comments - Comment formatting and reflow
9. Advanced - Penalty system, raw string formatting, experimental features

**Complete Reference:**
- `complete/clang-format-cli.md` - Full command-line interface documentation
- `complete/clang-format-style-options.md` - All 194 style options with examples

## Examples

### Example 1: Minimal-Disruption Configuration

**Scenario**: Introducing clang-format to an existing codebase with established formatting conventions

```
Analyze the code style in src/ and generate a .clang-format that preserves our existing patterns
```

**Result**: Claude generates and tests multiple configurations, scoring each by its impact on existing code. You receive a comparison table showing:
- Impact scores for each hypothesis
- Breakdown of line changes vs whitespace changes
- Example diffs for representative files
- Test commands to verify against your own file selections

### Example 2: Template-Based Configuration

**Scenario**: Starting a new project with Google C++ style guide

```
Create a .clang-format file using Google C++ style with 120 column limit and 4-space indentation
```

**Result**: Claude copies the `google-cpp-modified.clang-format` template to your project root and verifies it meets your requirements.

### Example 3: Troubleshooting Unexpected Formatting

**Scenario**: clang-format is not wrapping function parameters as expected

```
clang-format isn't breaking function parameters across multiple lines when they exceed the column limit. How do I fix this?
```

**Result**: Claude:
- Checks your configuration with `--dump-config`
- References `02-breaking.md` documentation
- Identifies relevant options: `BinPackParameters`, `AllowAllParametersOfDeclarationOnNextLine`, `AlignAfterOpenBracket`
- Suggests configuration changes with examples
- Provides test commands to verify the fix

See [Examples Documentation](./docs/examples.md) for more scenarios.

## Troubleshooting

### Plugin Not Activating

The skill activates when any trigger occurs:
1. User mentions "clang-format" or ".clang-format"
2. User requests analyzing code style/formatting patterns
3. User requests creating/modifying formatting configuration
4. User troubleshoots formatting behavior
5. User asks about brace styles/indentation/spacing/alignment
6. User wants to preserve existing style or minimize formatting changes

### clang-format Tool Not Found

Ensure clang-format is installed:

```bash
# Ubuntu/Debian
sudo apt-get install clang-format

# macOS
brew install clang-format

# Verify installation
clang-format --version
```

### Configuration Not Being Detected

Verify configuration file location and syntax:

```bash
# Check which configuration clang-format is using
clang-format --dump-config file.cpp

# Test configuration syntax
clang-format --style=file --dry-run file.cpp
```

## Contributing

Contributions are welcome. When adding or updating reference documentation, please:
- Maintain the category-based organization (01-09.md)
- Include practical examples for each option
- Test configurations before documenting
- Follow the existing documentation structure

## License

Unspecified - please check with the plugin author for license information.

## Credits

This plugin provides comprehensive clang-format configuration guidance and automation for Claude Code users.
