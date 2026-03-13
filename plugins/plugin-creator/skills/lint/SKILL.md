---
name: lint
description: Run the plugin validator on a skill, agent, or plugin directory rts token complexity, broken links, frontmatter issues, and structural problems. Use when checking skill quality, validating before commit, or diagnosing validator warnings. Pass the path as an argument.
argument-hint: <path-to-skill-or-plugin>
user-invocable: true
---

<lint_target>$ARGUMENTS</lint_target>

!`uvx skilllint@latest <lint_target/>`

@${CLAUDE_PLUGIN_ROOT}/references/ERROR_CODES.md
