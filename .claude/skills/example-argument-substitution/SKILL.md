---
name: example-argument-substitution
description: Example skill demonstrating the argument substitution pattern — capture the first word, second word, and all words into named XML tags at the top, then reference the tags throughout.
argument-hint: "<action> [target] [--flag]"
user-invocable: true
---

# Argument Substitution Pattern — Example Skill

Arguments are captured once at the top into named tags. All routing and logic below references the tags, not the raw substitution variables.

<action>$0</action>
<target>$1</target>
<all_args>$ARGUMENTS</all_args>

---

## How This Works

When this skill is invoked as `/example-argument-substitution greet world --loud`:

- first word → `greet` → captured as `<action>greet</action>`
- second word → `world` → captured as `<target>world</target>`
- all words → `greet world --loud` → captured as `<all_args>greet world --loud</all_args>`

Everything below uses `<action>`, `<target>`, and `<all_args>` — never the raw positional variables again.

See [./references/argument-substitution-reference.md](./references/argument-substitution-reference.md)
for the full variable syntax — that file is NOT subject to substitution.

---

## Routing

Dispatch based on `<action>`:

```mermaid
flowchart TD
    Start(["Read <action>"]) --> Q{action value?}
    Q -->|"greet"| Greet["Say hello to <target>"]
    Q -->|"farewell"| Farewell["Say goodbye to <target>"]
    Q -->|"inspect"| Inspect["Show all_args: <all_args>"]
    Q -->|"(empty)"| Help["Output: /example-argument-substitution greet|farewell|inspect [target]"]
    Q -->|"(anything else)"| Unknown["Output: Unknown action '<action>'. Valid: greet, farewell, inspect"]
```

---

## Actions

### greet

**Trigger:** `<action>` is `greet`

Output:

```text
Hello, <target>!
(invoked as: <all_args>)
```

If `<target>` is empty, substitute `world`.

### farewell

**Trigger:** `<action>` is `farewell`

Output:

```text
Goodbye, <target>. It was a pleasure.
(invoked as: <all_args>)
```

If `<target>` is empty, substitute `friend`.

### inspect

**Trigger:** `<action>` is `inspect`

Show all substituted values:

```text
action   = <action>
target   = <target>
all_args = <all_args>
```

Useful for debugging — run `/example-argument-substitution inspect` to see what the skill received.

---

## Example Invocations

| Command | `<action>` | `<target>` | `<all_args>` |
|---------|-----------|-----------|-------------|
| `/example-argument-substitution greet Alice` | `greet` | `Alice` | `greet Alice` |
| `/example-argument-substitution farewell Bob` | `farewell` | `Bob` | `farewell Bob` |
| `/example-argument-substitution inspect` | `inspect` | _(empty)_ | `inspect` |
| `/example-argument-substitution` | _(empty)_ | _(empty)_ | _(empty)_ |

---

## Command Substitution

Skills also support command substitution via `!` followed by a backtick-wrapped shell command.
The output is inlined into the skill content at load time.

Live example — this ran when the skill loaded:

!`echo "SKILL_LOADED_AT=$(date '+%Y-%m-%dT%H:%M:%S')"`

Practical uses: inject git branch, current directory, environment state.

---

## Code Block Pitfall: Positional Variables

ALL bare positional variable forms (first word, second word, all-args, brace forms) are substituted
in SKILL.md at load time — including inside fenced code blocks, in single-quoted strings, and in
awk field references. There is no safe way to write the literal syntax of substitution variables
inside SKILL.md without them being consumed.

The broken patterns and the exhaustive pitfall table (including backslash escaping, which does NOT
work, and language-specific naming like Perl's program-name variable) are documented in the
reference file only — that file is not subject to substitution and can show the literal syntax
safely.

See [./references/argument-substitution-reference.md](./references/argument-substitution-reference.md)
for the full pitfall table.

---

## Argument Substitution Documentation

For full documentation of the substitution syntax and the pre-declaration pattern — including why
reference files can document these literals safely — see
[./references/argument-substitution-reference.md](./references/argument-substitution-reference.md).

That file is loaded separately and is NOT subject to substitution at skill-load time, making
it the correct place to explain the syntax to other skill authors.
