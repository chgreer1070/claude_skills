---
name: 'bash-development: Fix bash-53-features inaccuracies and task_output bug'
description: "Two issues:\n\n1. **bash-53-features/SKILL.md inaccuracies** (features exist but details wrong):\n   - GLOBSORT: `:asc`/`:desc` suffixes fabricated — actual syntax is `+`/`-` prefix; `date` not a valid specifier (should be `mtime`); missing specifiers: `blocks`, `atime`, `ctime`, `numeric`, `nosort`\n   - `${ command; }` examples: missing required space after `{` (bash.1 requires space/tab/newline/`|` after `{`)\n   - `${| command; }` REPLY examples: misleading — REPLY is local within substitution, r"
metadata:
  topic: bash-development-fix-bash-53-features-inaccuracies-and-tasko
  source: Plugin code review session 2026-02-21
  added: '2026-02-21'
  priority: P1
  type: Feature
  status: done
---
