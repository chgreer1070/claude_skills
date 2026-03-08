---
name: Fix $N corruption in bash-development and perl-development SKILL.md code examples
description: "bash-development and perl-development plugin SKILL.md files contain shell code examples with `$N` variable references (including `${N}` brace form). All forms are substituted by the skill engine at load time — there is no safe escape in SKILL.md body.\n\nAffected files confirmed via grep:\n- plugins/bash-development/skills/bash-portability/SKILL.md — ${1} × 5\n- plugins/bash-development/skills/bash-testing/SKILL.md — ${1}, ${2}\n- plugins/bash-development/skills/bash-logging/SKILL.md — ${1}, ${2}\n- plugins/bash-development/skills/bash-development/SKILL.md — ${1}, ${2}\n- plugins/bash-development/skills/bash-52-features/SKILL.md — many ${N} occurrences\n- plugins/bash-development/skills/bash-53-features/SKILL.md — many ${N} occurrences\n- plugins/perl-development/skills/perl-lint/SKILL.md — ${1}\n- plugins/perl-development/skills/perl-validate/SKILL.md — ${1}\n\nWhen invoked with arguments, `${1}` renders as the argument value, corrupting code examples. When invoked without arguments, `${1}` renders as empty string, also corrupting examples.\n\nFix: Move all shell code examples containing `$N` patterns from SKILL.md body into `references/*.md` files. Reference files are NOT subject to substitution. Link to them from SKILL.md.\n\nNote: These skills have no `argument-hint` frontmatter and are not argument-routing skills. Their code examples are reference material that should live in reference files regardless."
metadata:
  topic: fix-n-corruption-in-bash-development-and-perl-development-sk
  source: Session 2026-03-08 — canary testing of argument substitution
  added: '2026-03-08'
  priority: P1
  type: Bug
  status: open
  issue: '#552'
  last_synced: '2026-03-08T15:17:24Z'
---