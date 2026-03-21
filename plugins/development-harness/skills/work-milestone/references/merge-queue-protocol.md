# Merge Queue Protocol

The orchestrator owns the merge slot. Only one merge proceeds at a time. Workers signal COMPLETE and wait for the merge outcome.

## Merge Slot Lifecycle

```mermaid
flowchart TD
    Signal(["Worker signals COMPLETE"]) --> Queue["Add to merge queue<br>(ordered by signal time)"]
    Queue --> Slot{"Merge slot free?"}
    Slot -->|"Busy — another merge in progress"| Wait["Queue this completion.<br>Return to Monitor for<br>other team members."]
    Wait --> Slot
    Slot -->|"Free — acquire slot"| PreVerify

    PreVerify{"Pre-Verification Check<br>Worker's base commit matches<br>current integration branch HEAD?"}
    PreVerify -->|"Matches — skip re-test"| AttemptMerge
    PreVerify -->|"Diverged — rebase and run gates"| RunGates

    RunGates["Rebase worktree branch onto<br>integration branch HEAD.<br>Run quality gate commands<br>from dispatch plan pre_merge list."]
    RunGates --> GatesResult{"Gates pass?"}
    GatesResult -->|"All pass"| AttemptMerge
    GatesResult -->|"Any fail"| GateFail["Send gate failure to worker via SendMessage.<br>Worker fixes and re-signals COMPLETE.<br>Release merge slot."]
    GateFail --> Wait

    AttemptMerge["Squash merge worktree branch<br>into integration branch.<br>Commit message: conventional commit<br>with item title and issue number."]
    AttemptMerge --> MergeResult{"Merge result?"}

    MergeResult -->|"Clean"| Success["Push integration branch.<br>Update item status via backlog MCP.<br>Release merge slot.<br>Clean up worktree."]

    MergeResult -->|"1-2 files conflicting"| Classify["Classify conflict severity"]
    Classify --> Severity{"Conflict type"}

    Severity -->|"Trivial — whitespace,<br>import order, adjacent additions"| AutoResolve["Auto-resolve.<br>Run quality gates after resolve."]
    Severity -->|"Medium — same function<br>edited differently"| AutoResolve
    AutoResolve --> AutoResult{"Resolve succeeded?"}
    AutoResult -->|"Yes"| Success
    AutoResult -->|"No"| AssignBack

    Severity -->|"Heavy — file refactored<br>by multiple worktrees"| AssignBack
    MergeResult -->|"3+ files conflicting"| AssignBack

    AssignBack["Abort merge.<br>Create PR from worktree branch<br>targeting integration branch.<br>Create resolution backlog item.<br>Add to current milestone.<br>Report to user for design review.<br>Release merge slot."]
    AssignBack --> Done(["Slot released"])
    Success --> Done
```

## Conflict Severity Classification

```mermaid
flowchart TD
    Conflict(["Merge conflict detected"]) --> Count{"How many files<br>have conflicts?"}

    Count -->|"0 files — clean merge"| Clean(["No conflict — proceed"])

    Count -->|"1-2 files"| Severity{"Conflict type?<br>Observable: git diff<br>conflict markers"}

    Severity -->|"Whitespace, import order,<br>adjacent-line additions"| Trivial["TRIVIAL — auto-resolve"]
    Severity -->|"Same function/block<br>edited differently"| Medium["MEDIUM — auto-resolve attempt<br>with quality gate verification"]
    Severity -->|"File restructured or<br>refactored differently<br>by both worktrees"| Heavy["HEAVY — assign_back<br>Create PR for design review"]

    Count -->|"3+ files"| Heavy

    Trivial --> AutoResolve(["Orchestrator resolves<br>and runs gates"])
    Medium --> AutoResolve
    Heavy --> PR(["Abort merge.<br>Create PR + resolution task."])
```

## Assign Back Details

When a heavy conflict triggers assign_back:

1. Abort the in-progress merge: `git merge --abort`
2. Push the worktree branch to origin (if not already pushed)
3. Create a PR from the worktree branch targeting the integration branch
4. Create a backlog item for the conflict resolution task:
   - Title: `Resolve merge conflict: {item A title} vs {item B title}`
   - Body: PR link, conflicting files list, both workers' approaches
   - Label: `conflict-resolution`
   - Assign to current milestone
5. SendMessage to both workers with the resolution task issue number
6. Report to user: PR link, resolution task link, conflict file list
7. Release merge slot

The resolution task is dispatched in the next wave like any other item. The team member implementing it has access to both original PRs and can make a design decision or implement a merge manually.

## Quality Gate Commands

Gate commands are defined in the dispatch plan under `quality_gates`:

```yaml
quality_gates:
  pre_merge:
    - "uv run prek run --all-files"
    - "uv run ruff check ."
  post_merge:
    - "uv run pytest tests/ -x"
```

`pre_merge` gates run before each individual item merge. `post_merge` gates run once on the full integration branch before landing to main.

A gate failure on an individual merge returns the failure output to the worker via SendMessage. The worker fixes the issue and re-signals COMPLETE.

A `post_merge` failure on the integration branch triggers a specialist agent delegation in a worktree on the integration branch. The orchestrator does not attempt self-repair.

## Integration Branch Landing

After all waves complete:

1. Run full `pre_merge` + `post_merge` gate suite on integration branch
2. If any gate fails: delegate fix to specialist agent, re-run gates
3. If all gates pass:

```bash
git switch main
git merge --no-ff milestone/{N}-{slug}
git push origin main
```

4. Delete integration branch: `git push origin --delete milestone/{N}-{slug}`
5. Invoke `/complete-milestone {N}`
