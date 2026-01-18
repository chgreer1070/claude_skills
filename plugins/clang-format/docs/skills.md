# Skills Reference

The clang-format Configuration plugin provides one comprehensive skill for all clang-format configuration tasks.

## clang-format Configuration

**Location**: `skills/clang-format/SKILL.md`

**Description**: The model must invoke this skill when any trigger occurs - (1) user mentions "clang-format" or ".clang-format", (2) user requests analyzing code style/formatting patterns/conventions, (3) user requests creating/modifying/generating formatting configuration, (4) user troubleshoots formatting behavior or unexpected results, (5) user asks about brace styles/indentation/spacing/alignment/line breaking/pointer alignment, (6) user wants to preserve existing style/minimize whitespace changes/reduce formatting diffs/codify dominant conventions.

**User Invocable**: Yes (default)

**Allowed Tools**: All tools (no restrictions)

**Model**: Default (inherits from session)

### When to Use

This skill activates automatically in these scenarios:

1. **Explicit Mention** - User says "clang-format" or ".clang-format"
2. **Code Style Analysis** - User requests analyzing formatting patterns or conventions in existing code
3. **Configuration Operations** - User wants to create, modify, or generate `.clang-format` files
4. **Troubleshooting** - User investigates unexpected formatting behavior or results
5. **Style Inquiries** - User asks about specific formatting options (braces, indentation, spacing, alignment, line breaking, pointer alignment)
6. **Minimal Disruption** - User wants to preserve existing style, minimize whitespace changes, reduce formatting diffs, or codify dominant conventions

### Activation

This skill is automatically invoked by Claude when triggers are detected. Users do not need to explicitly activate it.

Alternatively, users can manually invoke:

```
@clang-format Configuration
```

Or via the Skill tool:

```
Skill(command: "clang-format Configuration")
```

### Workflow Routing

Once invoked, the skill routes to appropriate workflows based on the trigger type:

**Trigger 1: Explicit clang-format mention**
- For specific options → Consult references/01-09.md for relevant category
- For complete reference → Direct to references/complete/clang-format-style-options.md
- For CLI usage → Reference references/cli-usage.md

**Trigger 2: Code style analysis request**
- Follow "Analyzing Existing Code Style" workflow
- Examine code samples systematically (braces→indentation→spacing→breaking→alignment)
- Map patterns to closest template in assets/configs/
- Generate configuration hypotheses
- Test and score each hypothesis by impact:
  - Line count changes (weight: 10) - affects rebasing, diffs, reviews
  - Whitespace changes (weight: 1) - aesthetic only
  - Lower score = better (minimal disruption)
- Present comparison table with scores and example diffs
- Await user approval before finalizing

**Trigger 3: Configuration file operations**
- Creating new → Follow "Creating New Configuration from Template" workflow
- Modifying existing → Read current config, consult relevant category guide
- Generating from code → Use Trigger 2 workflow

**Trigger 4: Formatting behavior investigation**
- Follow "Troubleshooting Formatting Issues" workflow
- Verify config detection with --dump-config
- Identify affected category, consult references/0X.md
- Test isolated options with minimal config

**Trigger 5: Style option inquiries**
- Map question to category: braces→03, indentation→04, spacing→05, alignment→01, breaking→02
- Reference specific category guide in references/
- Provide examples from quick-reference.md if applicable

**Trigger 6: Minimal-disruption requests**
- Use "Analyzing Existing Code Style" workflow
- Emphasize starting from closest template
- Test on representative samples before project-wide application
- Document which patterns were preserved vs normalized

### Bundled Resources

The skill includes extensive resources that Claude accesses on-demand:

**Configuration Templates** (`assets/configs/`):
- `google-cpp-modified.clang-format` - Google C++ style with 4-space indent, 120 columns
- `linux-kernel.clang-format` - Linux kernel coding standards (tabs, K&R braces)
- `microsoft-visual-studio.clang-format` - Microsoft/Visual Studio conventions
- `modern-cpp17-20.clang-format` - Modern C++17/20 style with contemporary idioms
- `compact-dense.clang-format` - Compact style for space-constrained environments
- `readable-spacious.clang-format` - Spacious style prioritizing readability
- `multi-language.clang-format` - Multi-language configuration (C++, JavaScript, Java)

**Integration Scripts** (`assets/integrations/`):
- `pre-commit` - Git hook for automatic formatting (supports pre-commit and prek frameworks)
- `vimrc-clang-format.vim` - Vim format-on-save configuration
- `emacs-clang-format.el` - Emacs clang-format integration

**Reference Documentation** (`references/`):

Quick Navigation:
- `index.md` - Documentation hub
- `quick-reference.md` - Complete configurations with explanations
- `cli-usage.md` - CLI usage, editor setup, CI/CD integration

Option Categories:
- `01-alignment.md` - Vertical alignment of declarations, assignments, operators
- `02-breaking.md` - Line breaking and wrapping rules
- `03-braces.md` - Brace placement styles (K&R, Allman, GNU, etc.)
- `04-indentation.md` - Indentation rules and special cases
- `05-spacing.md` - Whitespace control around operators, keywords
- `06-includes.md` - Include/import organization and sorting
- `07-languages.md` - Language-specific options (C++, Java, JavaScript)
- `08-comments.md` - Comment formatting and reflow
- `09-advanced.md` - Penalty system, raw string formatting, experimental features

Complete Reference:
- `complete/clang-format-cli.md` - Full CLI documentation
- `complete/clang-format-style-options.md` - All 194 style options with examples

### Common Workflows

**Creating New Configuration from Template:**

1. Identify requirements (style guide, team preferences, language)
2. Select closest template from assets/configs/
3. Copy template to project root as .clang-format
4. Test formatting: `clang-format --dry-run file.cpp`
5. Customize specific options using references/01-09.md
6. Verify changes: `clang-format file.cpp | diff - file.cpp`

**Analyzing Existing Code Style:**

1. Examine code samples for formatting patterns
2. Identify key characteristics:
   - Brace placement → references/03-braces.md
   - Indentation → references/04-indentation.md
   - Spacing → references/05-spacing.md
   - Line breaking → references/02-breaking.md
   - Alignment → references/01-alignment.md
3. Map patterns to closest base style
4. Start with matching template
5. Override specific options to match observed patterns
6. Test on representative samples
7. Iterate until formatting matches existing style

**Setting Up Editor Integration:**

Vim:
1. Copy assets/integrations/vimrc-clang-format.vim to .vimrc
2. Restart Vim or source configuration
3. Save C/C++/Java files to trigger formatting

Emacs:
1. Copy assets/integrations/emacs-clang-format.el to Emacs config
2. Restart Emacs or evaluate configuration
3. Save supported files to trigger formatting

**Setting Up Git Hooks:**

Option 1 - Using pre-commit/prek framework (recommended):

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-clang-format
    rev: v19.1.7
    hooks:
      - id: clang-format
```

Then: `pre-commit install` or `prek install`

Option 2 - Manual git hook:

```bash
cp assets/integrations/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Troubleshooting Formatting Issues:**

1. Verify configuration: `clang-format --dump-config file.cpp`
2. Check CLI options in references/cli-usage.md
3. Identify affected category (braces, spacing, breaking, etc.)
4. Consult relevant references/0X.md guide
5. Test isolated options with minimal config
6. For comprehensive details, check references/complete/clang-format-style-options.md

**Setting Up CI/CD Checks:**

```bash
# Check formatting without modifying files
clang-format --dry-run --Werror src/**/*.{cpp,h}
```

Configure to fail build on violations.

### Key Concepts

**Base Styles**: Predefined configurations (LLVM, Google, Chromium, Mozilla, WebKit, Microsoft, GNU) provide starting points. Set with `BasedOnStyle: Google` then override specific options.

**Multi-Language Support**: Configure different languages separately in single file using `Language:` key. See assets/configs/multi-language.clang-format for example.

**Penalty System**: clang-format uses penalties to choose between formatting alternatives. Higher penalty values discourage specific choices. See references/09-advanced.md for details.

**Progressive Refinement**: Start with template closest to requirements, then customize incrementally. Test frequently on representative code samples.

**Impact Scoring**: The skill uses weighted scoring to minimize disruption:
- Line count changes (weight: 10) - High impact on merges, rebasing, code review
- Whitespace changes (weight: 1) - Low impact, aesthetic only
- Lower score = better (less disruption)

### Testing Configurations

```bash
# Preview changes without modifying file
clang-format --dry-run file.cpp

# Show diff of proposed changes
clang-format file.cpp | diff - file.cpp

# Apply formatting to file
clang-format -i file.cpp

# Format entire project
find src include -name '*.cpp' -o -name '*.h' | xargs clang-format -i

# Check formatting in CI (fail on violations)
clang-format --dry-run --Werror src/**/*.{cpp,h}
```

### Navigation Strategy

For most tasks, the skill follows this progression:

1. **Start with templates** - Browse assets/configs/ for ready-to-use configurations
2. **Quick reference** - Check references/quick-reference.md for complete configurations
3. **Category guides** - Consult references/01-09.md for specific option categories
4. **CLI usage** - Reference references/cli-usage.md for command-line details
5. **Complete reference** - Use references/complete/ for exhaustive option documentation

### Hooks

This skill does not configure any hooks.

### Reference Files

The skill includes 24 reference files organized by category:

**Assets** (11 files):
- 7 configuration templates (assets/configs/)
- 3 integration scripts (assets/integrations/)

**Documentation** (13 files):
- 3 quick navigation files (index.md, quick-reference.md, cli-usage.md)
- 9 category guides (01-09.md)
- 2 complete references (complete/*.md)

All reference files support progressive disclosure - Claude loads them on-demand as needed for the user's specific task.

---

[← Back to README](../README.md)
