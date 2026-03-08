# Argument Substitution Reference

This file is a reference document linked from SKILL.md. It is loaded separately, NOT substituted
when the skill is invoked. This means the literal `$ARGUMENTS` syntax can be documented here
without being replaced at skill-load time.

## Available Substitution Variables

| Variable        | Description                                              |
|-----------------|----------------------------------------------------------|
| `$ARGUMENTS`    | All arguments passed when invoking the skill             |
| `$ARGUMENTS[N]` | Specific argument by 0-based index (e.g. `$ARGUMENTS[0]`) |
| `$0`, `$1`      | Shorthand: `$0` = first arg, `$1` = second arg           |

## The Pre-Declaration Pattern

Capture substitution variables into named XML tags at the very top of SKILL.md body,
then reference the tags throughout. This prevents garbled output in routing tables and
prose that describes the variables rather than using them.

**SKILL.md top (capture block):**

```markdown
<action>$0</action>
<target>$1</target>
<all_args>$ARGUMENTS</all_args>
```

**Rest of SKILL.md (reference tags, not `$` variables):**

```markdown
Dispatch based on `<action>`:
- greet → say hello to `<target>`
- farewell → say goodbye to `<target>`
```

## Why Reference Files Work for Documentation

Reference files are loaded separately by Claude when needed — they are NOT processed through
the substitution engine when the parent SKILL.md is loaded. This means:

- Document `$ARGUMENTS`, `$0`, `$1` syntax here freely
- The skill body (SKILL.md) gets substitution applied; this file does not
- Link this file from SKILL.md: `[Argument substitution reference](./references/argument-substitution-reference.md)`

## When to Use Each Approach

- **Pre-declaration tags**: Use in SKILL.md when routing/dispatch logic must reference args
- **Reference file**: Use for documenting the substitution syntax itself (like this file)
- **Direct `$ARGUMENTS`**: Use when you just want to pass the invocation args through to a task

---

## Code Block Pitfalls

Substitution applies inside fenced code blocks too. A bash example like:

```text
command_exists() {
    command -v "$1" >/dev/null 2>&1
}
```

If this appears in SKILL.md with a literal `$1`, it will be replaced with the user's argument
when the skill loads — corrupting the example.

### What Does NOT Work: Backslash Escaping

Writing `\$1` in SKILL.md does **not** prevent substitution. The engine strips the dollar sign
and substitutes the variable, leaving the backslash behind. Result when invoked with `foo`:

```text
command -v "\foo" >/dev/null 2>&1   ← broken: backslash kept, $1 substituted
```

This was verified by live canary test. Do not use backslash escaping for this purpose.

### What Does NOT Work: Brace Form

`${1}` (with curly braces) is **also substituted**. This is a common false assumption.
Verified by live canary test: `basename(${0})` in SKILL.md rendered as `basename(CANARY_VALUE)`,
not literally. Do not use brace form as an escape mechanism.

### What Does NOT Work: Single-Quoted Awk Programs

Awk's `$5` field reference looks like it should be safe in single quotes, but it is **also
substituted**. Verified by live canary test: `awk '{print $5}'` in SKILL.md rendered as
`awk '{print }'` — the `$5` was consumed.

Shell quoting context is irrelevant. The substitution engine operates on the raw file text
before any shell or interpreter sees it.

### What Works: Language-Specific Alternatives

For Perl `$0` (script name), use the `English` module alias:

```perl
use English qw(-no_match_vars);
SCRIPT_NAME => basename($PROGRAM_NAME),   # $PROGRAM_NAME == $0, no substitution risk
```

### Summary Table

| Pattern in SKILL.md | Substituted? | Use instead |
|---------------------|-------------|-------------|
| `$1` | YES — corrupts example | Move example to reference file |
| `\$1` | YES — backslash left behind | Move example to reference file |
| `${1}` | YES — also substituted (false safe) | Move example to reference file |
| `$ARGUMENTS` | YES — intended | ✓ use for capture in XML tag |
| `awk '{print $5}'` | YES — single quotes ignored | Move example to reference file |
| `awk "{print $5}"` | YES | Move example to reference file |
| Perl `$0` | YES | `$PROGRAM_NAME` via `use English` |
| Perl `$1` capture | YES | Move example to reference file or describe in prose |

**Universal rule**: there is no safe escape for `$N` in SKILL.md. Put all examples containing
`$N` in a reference file, which is NOT subject to substitution.

---

## Command Substitution

`` !`command` `` syntax in SKILL.md body is **executed at load time** — the command runs and
its stdout replaces the expression entirely. There is no safe escape for this in SKILL.md body.

To document `` !`command` `` syntax for skill authors, put examples in a reference file (this
file) — reference files are not subject to substitution or command execution.

**Example** (safe here in the reference file):

The session-start hook pattern uses:

```text
!`cat /path/to/context.md`
```

This executes `cat` at load time and injects the file contents into the skill prompt.

---

## Substitution Applies to Prose Too

`$ARGUMENTS`, `$0`, `$1` are substituted everywhere in SKILL.md — not just in code blocks.
Explanatory prose like "the value of `$0` is..." will have `$0` replaced with the actual
argument. The pre-declaration XML tag pattern exists precisely because of this:

```text
<action>$0</action>   ← $0 gets substituted here once, into the tag value
```

Then prose references `<action>` (the tag), which is not substituted.

---

### Testing Before Applying Broadly

Before applying any new escape pattern to multiple files, test it using this skill:

1. Add the pattern to this SKILL.md or its reference
2. Invoke: `/example-argument-substitution CANARY_TESTWORD`
3. Verify the canary does NOT appear in the rendered output where it shouldn't
4. Only then apply the pattern to other skills
