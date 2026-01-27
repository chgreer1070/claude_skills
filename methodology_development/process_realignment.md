## Transcript note (not a finalized spec)

This file is a **transcript-like clarification** of a concept I was teasing out in a chat session after a misunderstanding about my intent.

- This is **not** meant to be a finalized methodology document.
- Terminology may shift; later lines may correct earlier ones.
- The goal is to make my intent harder to misread.

## Local glossary (terms as used in this transcript)

- **Desired outcome**: the end state/value (what "done" means at the user/business level).
- **Objectives**: component outcomes that collectively achieve the desired outcome (often phrased as "the system/user can...").
- **Acceptance criteria**: testable statements proving each objective is met (observable, verifiable, pass/fail).
- **Skill**: a structured, in-band process wrapper (system-prompt-like structure) that drives the conversation and dispatches work.
- **Skill(fork)**: a forked subprocess skill (isolated context) that performs work and returns a structured summary + artifacts back to the main conversation.

## Markers I use when adding clarifying detail

- **MISUNDERSTANDING:** what I think the other party thought I meant (the misread).
- **CLARIFICATION:** what I actually mean (the intended interpretation).
- **REPHRASE:** a better wording that avoids the misread.
- **NOTE:** non-normative aside / context / caveat.

---

Your workflow:

1. Skill: Discovery of desired outcome and objectives (user provided a feature, issue, task, enablement, structure change, documentation, pipeline and release flow, versioning, stakeholders, ... or anything else that comes in that is part of the project could be provided as the input and this should be treated in a flexible manner)

   NOTE: By "goal" in earlier conversation, I mean the combination of:

   - Desired outcome (end state/value)
   - Objectives (component outcomes)
   - Acceptance criteria (verification)

   A common structure is:

   - Desired outcome → 1..N objectives
   - Each objective → 1..N acceptance criteria (plus optional "anti-criteria" / non-goals)
     a. Primary Assistant: Context Gathering
     - conversational
     - dispatches researcher agents
       - Skill: Agent with tasks for online research
       - Skill: Agents with tasks for local repository discovery
       - Skill: Agents with git analysis tasks
       - Skill: Agents with GitHub or GitLab remote (or local filepath) repository reference gathering tasks.
       - Skill: Agents that check packages, latest version documentation for any mentioned technologies, i.e. if the user says it for gcc 10.3 then ensure the reference doc or url for gcc 10.3 has been collected as reference material. If the user says we are creating a release pipeline for GitLab, we should know what the current gitlab pipeline schema is and the available predefined variables.
     - Skill: validates findings with user asking contextual questions about if the findings and resources to ensure alignment towards intended goal
       b. review and restate the goal and intent to the user until user approves

2. Skill: Architecture/Design - Identifies what is required to achieve the desired outcome + objectives
   a. Skill(fork): Creates or updates the Project Requirements Documentation (PRD) artifact and reports what was changed in the document. `project-requirements-documentation`, `prd-feature-scope-{scope-slug}`
   b. Skill(fork): Creates or updates the non-functional Requirements (NFR) artifact and reports what was changed in the document. `non-functional-requirements`, `nfr-scope-{scope-slug}`
   c. Skill(fork): Creates or updates the System Architecture Diagram, and descides if the project is at the threshold of also requiring Component Architecture (C4) design and System Context Diagram (C4) which shows the interfaces and flow of data and processes through the application. The skill is Provided as input the previous steps structured summary output and the artifacts from a and b. `system-architecture-diagram`, `component-architecture-diagram`, `system-context-diagram`
   d. Skill(fork): Creates or updates the meta project infrastructure documentation with changes to project configuration files like linting rules, packaging, publishing, CI/CD workflows, tooling, tool setup processes. Meta Project Infrastructure (MPI) `mpi-{linting,ci-cd,packaging,tooling,contributing,debugging,...etc}`
   e. SKill: Updates the Architecture Descision Records (ADR) `adr-{index}-{decision-slug}`

3. Skill(fork): Planning Coordination - The plan references what has or hasn't yet been created towards the architecture documents and each phase or step in the plan has a link to what part of which document it implements. This takes the change to the architecture artifacts and organises when it can be done in the sequence of existing items within the plan, and ensures that tthe tasks that are not overlapping are done concurrently, and the tasks that are overlapping in their scope or files they touch are done sequentially, and tasks are done in a way that future tasks can benefit from the creation of items from the previous task. Such as, if one task is creating shared utility functions, it would be done before a task that may need to use those utility functions.
4. Implementation (with git worktrees)
   a. Orchestrator agent manages the creation and cleanup of worktrees, and starting the Workers concurrently or in sequence based on the plan (not agents, independant claude instances started via the cli, or sdk)
5. Verification (multi-phase)
   └─→ Input: Implementation + Original Desired Outcome request
   Agent: Verification Agent
   Phases:
   1. Correctness (DoD, acceptance criteria)
   2. Regression (existing systems unaffected)
   3. Design Compliance (follows ADRs, patterns)
   4. Quality Standards (linting, tests, CI/CD)
   5. Documentation (runbooks, API docs complete)
      Output: verification-report.md with issue list
