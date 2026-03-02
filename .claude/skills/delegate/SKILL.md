---
name: delegate
description: Quick delegation template for sub-agent prompts. Use when assigning work to a sub-agent, before invoking the Agent tool, or when preparing prompts for specialized agents. Provides the WHERE-WHAT-WHY framework. For comprehensive delegation guidance, activate the agent-orchestration how-to-delegate skill.
user-invocable: true
---
# Delegation Template

**Workflow Reference**: See [Multi-Agent Orchestration](./../../knowledge/workflow-diagrams/multi-agent-orchestration.md) for complete delegation flow with DONE/BLOCKED signaling.

**Step 1:** Analyze the task. Do you have the "WHERE, WHAT, WHY"?

**Step 2:** Construct the prompt using the template below.

---

## Template

```text
Your ROLE_TYPE is sub-agent.

[Task Identification - one sentence]

OBSERVATIONS:
- [Verbatim error messages]
- [What exists and where — file paths, not line numbers]
- [Environment state]

DEFINITION OF SUCCESS:
- [Specific measurable outcome]
- [Acceptance criteria]
- [Verification method]

CONTEXT:
- Location: [Where to look]
- Scope: [Boundaries]
- Constraints: [Hard requirements vs Preferences]

AVAILABLE RESOURCES:
- [List available MCP tools]
- [Reference docs with @filepath]

YOUR TASK:
1. Run /verify (as completion criteria guide)
2. Perform comprehensive context gathering
3. Form hypothesis → Experiment → Verify
4. Implement solution
5. Only report completion after /verify criteria are met
```

**Authoring guidance** (for the orchestrator filling in this template — do not include these annotations in the delivered prompt):

- **OBSERVATIONS**: References to source material — file paths, reference docs, user guides, verbatim error messages. Point the agent to where knowledge lives. Do not pre-read files and report line numbers (the agent finds those during context gathering). Do not include interpretations, assumptions, or analysis derived from pattern matching or training data. If you have no observations, you are not ready to delegate — gather context first.
- **DEFINITION OF SUCCESS**: The "WHAT". Measurable outcomes the agent can verify.
- **CONTEXT**: The "WHERE" and "WHY". Location narrows scope; constraints bound the solution space.

---

## Delegation Rules

Check before sending:

| Rule               | Check                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------- |
| **Formula**        | Delegation = Observations + Success Criteria + Resources - Assumptions - Micromanagement |
| **No HOW**         | Do NOT tell agent _how_ to implement (e.g., "Change line 42 to X")                       |
| **Constraints OK** | DO tell agent _constraints_ (e.g., "Must use the 'requests' library")                    |
| **No Assumptions** | Do NOT say "The issue is probably..."                                                    |
| **Full Scope**     | If code smell found, instruct agent to audit _entire pattern_, not single instance       |

---

## Quick Checklist

- [ ] Starts with `Your ROLE_TYPE is sub-agent.`
- [ ] Contains only factual observations
- [ ] No assumptions stated as facts
- [ ] Defines WHAT and WHY, not HOW
- [ ] Lists resources without prescribing tools
