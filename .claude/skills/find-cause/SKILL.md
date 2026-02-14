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

### Step 2 — Reproduce the problem

Execute the failing operation yourself. Capture the exact command, the exact output, and the exit code. If you cannot reproduce it, state that and ask the user for reproduction steps.

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
