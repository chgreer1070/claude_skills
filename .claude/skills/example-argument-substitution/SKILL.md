---
name: example-argument-substitution
description: Example skill demonstrating the argument substitution pattern — capture the first word, second word, and all words into named XML tags at the top, then reference the tags throughout.
argument-hint: "<action> [target] [--flag]"
user-invocable: true
---

# Argument Substitution Pattern — Example Skill

## How to Use This Skill

**Read this file before running it.** Then run it twice:

1. With 0 arguments: `/example-argument-substitution`
2. With 10 arguments: `/example-argument-substitution CANARY_A CANARY_B CANARY_C CANARY_D CANARY_E CANARY_F CANARY_G CANARY_H CANARY_I CANARY_J`

Compare what you see in each run against the capture block below to understand exactly what gets substituted and what stays empty.

---

## Capture Block

Arguments are captured once at the top into named XML tags. Everything below references the tags.

<arg0>$0</arg0>
<arg1>$1</arg1>
<arg2>$2</arg2>
<arg3>$3</arg3>
<arg4>$4</arg4>
<arg5>$5</arg5>
<arg6>$6</arg6>
<arg7>$7</arg7>
<arg8>$8</arg8>
<arg9>$9</arg9>
<all_args>$ARGUMENTS</all_args>
<arg_by_index_0>$ARGUMENTS[0]</arg_by_index_0>
<arg_by_index_1>$ARGUMENTS[1]</arg_by_index_1>
<arg_by_index_2>$ARGUMENTS[2]</arg_by_index_2>

---

## What the Capture Block Shows

When invoked with 10 CANARY arguments, each tag above receives one value:

- `<arg0>` = first argument (same as `$ARGUMENTS[0]`)
- `<arg1>` = second argument (same as `$ARGUMENTS[1]`)
- `<arg2>` through `<arg9>` = subsequent arguments
- `<all_args>` = all arguments as a single string
- `<arg_by_index_N>` = bracket-index form — verify it matches `<argN>`

When invoked with 0 arguments, all tags render empty.

See [./references/argument-substitution-reference.md](./references/argument-substitution-reference.md)
for the complete variable reference — that file is NOT subject to substitution.

---

## Routing (uses `<arg0>` as action)

Dispatch based on `<arg0>`:

```mermaid
flowchart TD
    Start(["Read <arg0>"]) --> Q{arg0 value?}
    Q -->|"greet"| Greet["Say hello to <arg1>"]
    Q -->|"farewell"| Farewell["Say goodbye to <arg1>"]
    Q -->|"inspect"| Inspect["Show all captured values"]
    Q -->|"(empty)"| Help["Output usage line"]
    Q -->|"(anything else)"| Unknown["Output: Unknown action. Valid: greet, farewell, inspect"]
```

---

## Actions

### greet

**Trigger:** `<arg0>` is `greet`

Output:

```text
Hello, <arg1>!
(invoked as: <all_args>)
```

If `<arg1>` is empty, substitute `world`.

### farewell

**Trigger:** `<arg0>` is `farewell`

Output:

```text
Goodbye, <arg1>. It was a pleasure.
(invoked as: <all_args>)
```

If `<arg1>` is empty, substitute `friend`.

### inspect

**Trigger:** `<arg0>` is `inspect`

Output all captured values:

```text
arg0              = <arg0>
arg1              = <arg1>
arg2              = <arg2>
arg3              = <arg3>
arg4              = <arg4>
arg5              = <arg5>
arg6              = <arg6>
arg7              = <arg7>
arg8              = <arg8>
arg9              = <arg9>
all_args          = <all_args>
arg_by_index_0    = <arg_by_index_0>
arg_by_index_1    = <arg_by_index_1>
arg_by_index_2    = <arg_by_index_2>
```

---

## Command Substitution

Skills also support command substitution via `!` followed by a backtick-wrapped shell command.
The output is inlined into the skill content at load time.

Live example — this ran when the skill loaded:

!`echo "SKILL_LOADED_AT=$(date '+%Y-%m-%dT%H:%M:%S')"`

Practical uses: inject git branch, current directory, environment state.

---

## Code Block Pitfall: Positional Variables

ALL positional variable forms are substituted at load time — including inside fenced code blocks,
single-quoted strings, awk field references, and brace forms. There is no safe escape in SKILL.md.

The full pitfall table (backslash escaping, brace form, single-quoted awk — all false-safe) is in
the reference file, which is NOT subject to substitution:

[./references/argument-substitution-reference.md](./references/argument-substitution-reference.md)

---

## Argument Substitution Documentation

For full documentation of all substitution variables, the pre-declaration pattern, and verified
pitfall evidence, see:

[./references/argument-substitution-reference.md](./references/argument-substitution-reference.md)
