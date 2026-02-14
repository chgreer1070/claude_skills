---
description: 'Wrap investigation requests with evidence-chain discipline. Use when the user asks to find out why something happens, look into something, research a root cause, debug an issue, or investigate unexpected behavior. Transforms vague investigation requests into reproducible-proof investigations. Invoke with /find-cause <description of what to investigate>.'
argument-hint: '<what to investigate>'
---

# Find Cause

Rewrite the user's investigation request using the evidence-chain protocol below, then execute it. The user's original request is in `$ARGUMENTS`.

## Evidence-Chain Protocol

<evidence_chain_rules>

Every claim in the investigation output MUST have a corresponding evidence entry. Evidence is one of:

1. **Command output** — a command was executed and the output was captured
2. **File content** — a file was read and a specific line range is cited
3. **Direct observation** — a reproducible state was observed (directory listing, process output, HTTP response)

These are NOT evidence:

- Documentation that describes intended behavior (docs describe intent, not reality)
- Training data recall or pattern matching
- Inference from absence ("the docs don't mention it, so it must not exist")
- Reasoning from analogy ("X works this way, so Y does too")

</evidence_chain_rules>

## Investigation Procedure

### Step 1 — Disambiguate the question

Read the user's request in `$ARGUMENTS`. Formulate 2 or more distinct interpretations of what they are asking. Present these interpretations to the user using the `AskUserQuestion` tool so the user can select the correct one or provide their own clarification.

Each interpretation MUST be a concrete, falsifiable question — not a vague restatement. Frame each as "Are you asking X?" where X is specific enough to investigate.

Example for the request "find out why the tests fail":

- **Interpretation A**: "Why do tests fail when run locally but pass in CI?"
- **Interpretation B**: "Why does a specific test case produce an unexpected assertion error?"
- **Interpretation C**: "Why did tests start failing after a recent change?"

Do NOT proceed to Step 2 until the user has confirmed which interpretation is correct or provided their own.

If the user selects "Other" and provides additional context, reformulate the interpretations and ask again. Only proceed when you have a single, unambiguous question to investigate.

### Step 1.5 — Prerequisite check and reproduction safety

Before investigating, assess two things: what you need to know, and whether reproduction is safe.

#### A. List unknowns and fastest verification paths

For each unknown in the investigation:

1. **State the unknown** — What do you need to know?
2. **Identify the fastest verification** — Can you observe it directly by running the system, or must you read source/docs?
3. **Prefer direct observation** — If the system under investigation is available to run, running it produces observed facts. Reading source files and documentation to theorize about behavior is slower and less reliable.

If any unknown can be resolved by running the system, that verification MUST happen in Step 2 (reproduction), not through source reading or documentation research.

#### B. Classify reproduction constraints

<reproduction_safety>

Determine whether the problem has **bound** or **unbound** constraints:

**Bound constraints** — You can see the full system and evaluate the risks yourself:

- You can read the relevant files, understand what the operation does, and assess its effects
- All inputs, variables, and side effects are visible and evaluable
- You can determine whether reproduction is safe, destructive, or requires precautions
- Examples: a skill you can read and activate, a script whose behavior you can trace, a config you can parse

**Action**: Evaluate the risk. If safe, proceed to Step 2. If destructive or risky, establish precautions (temp directory, dry-run flag, backup) before reproducing. Do not ask the user further questions until you encounter something you cannot evaluate yourself.

**Unbound constraints** — You cannot see or evaluate the full system:

The operation involves systems you cannot inspect, infrastructure you do not have access to, credentials you do not possess, inputs/variables you cannot observe, or side effects you cannot predict.

**Action**: Before reproducing, evaluate and ask the user:

1. **Is the operation destructive?** — Does it delete data, send messages, modify shared state, deploy code, or have side effects that cannot be undone?
2. **What sandbox is needed?** — Docker container, temp directory, CI pipeline, remote host, local VM, cloud environment? What is available?
3. **Do you have all inputs?** — List what you know (commands, arguments, env vars, config values). State what is missing.
4. **Are there aspects you might have overlooked?** — Ask the user explicitly.

Use `AskUserQuestion` to gather missing sandbox requirements and inputs. Structure questions by what you know vs what you need.

</reproduction_safety>

Do NOT proceed to Step 2 until: (bound) you have confirmed reproduction is safe, or (unbound) the user has provided the missing inputs and sandbox strategy.

### Step 2 — Reproduce the problem

Execute the **same operation the user performed**, end-to-end. Not adjacent diagnostic commands — the actual operation.

- If the user activated a skill, activate that skill
- If the user ran a command, run that command
- If the user triggered a workflow, trigger that workflow
- If the operation is destructive, execute it in the sandbox established in Step 1.5

Capture the exact command/action, the exact output, and the exit code or observable result.

Diagnostic commands (ls, env, grep) are NOT reproduction. They are Step 3 (source reading). Reproduction means experiencing the same failure path the user experienced.

If you cannot reproduce the operation, state that and ask the user for reproduction steps.

Do NOT skip this step by relying on a transcript or description of the failure. Run it yourself.

### Step 3 — Read the source

Read the files involved in the failure. Cite file paths and line numbers for every relevant code path. Do not summarize — quote the specific lines that matter.

### Step 4 — Build the evidence chain

For each claim in your investigation, produce an entry in this format:

```text
CLAIM: [What you assert]
EVIDENCE: [Tool] — [file:line or command:output]
VERIFIED: [yes/no]
```

If a claim cannot be verified with available tools, mark it `VERIFIED: no` and state what verification step is missing.

### Step 5 — Present findings

Structure the output as:

```text
QUESTION: [Restated from Step 1]

EVIDENCE CHAIN:
1. CLAIM: ...
   EVIDENCE: ...
   VERIFIED: yes

2. CLAIM: ...
   EVIDENCE: ...
   VERIFIED: yes

ROOT CAUSE: [Single statement supported by the chain above]

UNVERIFIED ITEMS: [List any claims marked VERIFIED: no, with what would make them conclusive]
```

## Prohibited Behaviors

- Do NOT present inferences as conclusions
- Do NOT use words "probably", "likely", "seems", "I think", "I believe", "I assume"
- Do NOT assert causality without citing the observed evidence that supports it
- Do NOT skip reproduction by referencing a user-provided transcript — reproduce it yourself
- Do NOT fill gaps with theories — state "I don't have that information" and describe what tool or action would fill the gap
- Do NOT investigate components of a system before reproducing the system's behavior end-to-end — reproduction eliminates unknowns that component inspection cannot
