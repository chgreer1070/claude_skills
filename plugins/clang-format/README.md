<p align="center">
  <img src="./assets/hero.png" alt="clang-format Configuration" width="800" />
</p>

# clang-format Configuration

Helps Claude configure clang-format to match your existing code style rather than overwrite it.
Bundles 7 ready-to-use templates, 3 editor integration scripts, and complete reference documentation
for all clang-format options.

## Problem

Introducing clang-format without the right configuration causes:

- Thousands of whitespace-only line changes that pollute git history
- Breaking every in-progress feature branch
- Days of bikeshedding over brace styles and indent widths
- Configs copied from the internet that silently misrepresent your style

This plugin changes that workflow: analyze first, measure impact, confirm before applying.

## Requirements

- Claude Code v2.0+
- `clang-format` installed (`apt install clang-format` or `brew install clang-format`)

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install clang-format@jamie-bitflight-skills
```

## Quick Start

The plugin activates automatically when you mention clang-format or request formatting help.
Describe what you want and Claude will route to the correct workflow:

```text
"Set up clang-format for this C++ project without changing the existing style"
"Add format-on-save to my editor"
"Make clang-format run before I commit"
"Why is clang-format putting braces in the wrong place?"
```

## Workflows

### Analyze existing code and generate matching configuration

Claude will:

1. Examine representative files (braces, indentation, spacing, line breaking)
2. Map patterns to the closest built-in template
3. Generate 3–5 configuration hypotheses as temporary files
4. Run `clang-format --style=... | diff` on 3–5 samples per hypothesis
5. Score each hypothesis: line-count changes (weight 10) + whitespace changes (weight 1)
6. Present a comparison table and example diffs
7. Wait for your approval before creating `.clang-format`

**Result:** You see exactly what will change before anything is applied.

### Create a new configuration from a template

Pick a template from the seven bundled options:

| Template | Style |
|----------|-------|
| `google-cpp-modified` | Google C++ with 4-space indent, 120-col limit |
| `linux-kernel` | Linux kernel (tabs, K&R braces) |
| `microsoft-visual-studio` | Microsoft/Visual Studio conventions |
| `modern-cpp17-20` | Modern C++17/20 idioms |
| `compact-dense` | Space-constrained environments |
| `readable-spacious` | Readability-first, generous whitespace |
| `multi-language` | C++, JavaScript, and Java in one file |

### Set up editor integration

Claude installs the correct integration for your editor — Vim, Emacs, VS Code, CLion. For
pre-commit hooks, the bundled script works with both `pre-commit` (Python) and `prek` (Rust).

### Troubleshoot formatting behavior

Claude runs `--dump-config` to find the active configuration, maps your complaint to one of 9
option categories, consults the relevant reference guide, and suggests targeted fixes.

## What's Bundled

- **7 configuration templates** in `assets/configs/`
- **3 integration scripts** in `assets/integrations/` — Vim, Emacs/Spacemacs, and pre-commit
- **Reference documentation** in `references/` — all clang-format options organized by category
  (braces, indentation, spacing, alignment, line breaking, and more), plus full CLI usage guide

## Example

**Without this plugin:** Claude copies a config from the internet and applies it. 2,847 lines
change across 93 files. Your git history is now useless.

**With this plugin:** Claude analyzes 5 files, tests 3 configurations, and reports:

```
Config A: impact score 340 (34 line changes × 10 + 14 whitespace changes × 1)
Config B: impact score 128
Config C: impact score 82  ← recommended

Example diff for Config C:
  - void foo(int x){
  + void foo(int x) {
```

You approve Config C. Claude creates `.clang-format`. Eight lines change. Your history stays clean.

---

> **The Ancient Woe**
>
> *The arrogant new scribe who arrives at the monastery and begins writing the holy texts in a completely different, erratic calligraphy, ruining the visual harmony of a tome that took three generations to pen.*

> **The Bard's Decree**
>
> *"Mimic the ancient hands! Study the slant of the ink and the breadth of the margins! Thou shalt conform thy quill to the masters who came before thee, lest the tapestry be violently torn!"*
