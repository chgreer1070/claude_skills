# clang-format Configuration

Configure the clang-format code formatting tool using ready-to-use templates, integration scripts, and comprehensive reference documentation.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install clang-format@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/clang-format
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [clang-format Configuration](./skills/clang-format/SKILL.md) | The model must invoke this skill when any trigger occurs - (1) user mentions "clang-format" or ".clang-format", (2) user requests analyzing code style/formatting patterns/conventions, (3) user requests creating/modifying/generating formatting configuration, (4) user troubleshoots formatting behavior or unexpected results, (5) user asks about brace styles/indentation/spacing/alignment/line breaking/pointer alignment, (6) user wants to preserve existing style/minimize whitespace changes/reduce formatting diffs/codify dominant conventions. |

## Quick Start

Analyze your existing C++ codebase and generate a matching .clang-format configuration:

```text
@clang-format

Analyze my C++ code in src/ and generate a .clang-format file that matches my existing style.
```

Claude will:
1. Examine your code samples for patterns (braces, indentation, spacing, alignment)
2. Generate configuration hypotheses and test them against your code
3. Measure the impact of each configuration (line changes vs whitespace changes)
4. Present the best-fit configuration with impact analysis
5. Create the .clang-format file after your approval

## What This Plugin Provides

- **7 Ready-to-Use Templates**: Google C++, Linux kernel, Microsoft Visual Studio, Modern C++17/20, Compact, Readable, and Multi-language configurations
- **Code Style Analysis**: Systematic analysis of existing code to generate matching configurations
- **Impact Measurement**: Weighted scoring system to minimize formatting disruption (prioritizes reducing line changes over whitespace changes)
- **Comprehensive Reference**: Category-organized documentation covering all clang-format options (braces, indentation, spacing, alignment, line breaking, etc.)
- **Integration Scripts**: Editor and git integration examples
- **Troubleshooting Workflows**: Systematic approaches to diagnose formatting behavior

## Use Cases

- **New Projects**: Start with proven templates optimized for common scenarios
- **Legacy Codebases**: Generate configurations that match existing style to minimize diffs
- **Team Standards**: Establish consistent formatting across team members
- **Formatting Troubleshooting**: Debug unexpected clang-format behavior with comprehensive option reference

## License

See [LICENSE](./LICENSE) file for details.
