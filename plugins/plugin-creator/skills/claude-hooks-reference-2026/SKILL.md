---
name: claude-hooks-reference-2026
description: Complete reference for Claude Code hooks system (January 2026). Loads focused specialist skills for hooks-core-reference, hooks-io-api, and hooks-patterns. Use when creating hooks, understanding hook events, matchers, exit codes, JSON output control, environment variables, plugin hooks, or implementing hook scripts.
user-invocable: true
---
# Claude Code Hooks System - Complete Reference (January 2026)

This skill loads focused specialist components for comprehensive hooks coverage.

## Specialist Skills

- **hooks-core-reference**: Hook system fundamentals — events, configuration, matchers, environment variables, execution, security, debugging. Use `Skill(skill: "plugin-creator:hooks-core-reference")` for configuration and troubleshooting.

- **hooks-io-api**: JSON input/output API — what data hooks receive via stdin and what JSON they return to control Claude. Use `Skill(skill: "plugin-creator:hooks-io-api")` for writing hook scripts that process input or produce JSON output.

- **hooks-patterns**: Recipes and working examples — plugin hooks, frontmatter hooks, prompt-based hooks, complete code examples in Python/Node.js. Use `Skill(skill: "plugin-creator:hooks-patterns")` for implementation patterns and examples.

- **hooks-guide**: Step-by-step practical guide — how to write, configure, and debug Claude Code hook scripts end-to-end. Use `Skill(skill: "plugin-creator:hooks-guide")` for hands-on implementation walkthroughs.

## Usage

**Full coverage**: `Skill(skill: "plugin-creator:claude-hooks-reference-2026")` loads all specialist skills.

**Focused work**: Activate a specific specialist skill for targeted context.

## Quick Reference

| Need | Skill |
|------|-------|
| What events exist, how to configure hooks | `hooks-core-reference` |
| What JSON goes in/out of hook scripts | `hooks-io-api` |
| Plugin hooks, prompt hooks, code examples | `hooks-patterns` |
| Step-by-step implementation walkthroughs | `hooks-guide` |

## Sources

- [Hooks Reference](https://code.claude.com/docs/en/hooks.md) (accessed 2026-01-28)
- [Hooks Guide](https://code.claude.com/docs/en/hooks-guide.md)
- [Settings Reference](https://code.claude.com/docs/en/settings.md)
- [Plugin Components Reference](https://code.claude.com/docs/en/plugins-reference.md#hooks)
