# Commit Messages and PR Body — `Fixes #N` Restriction

`Fixes #N`, `Closes #N`, and `Resolves #N` commit trailers trigger automatic GitHub issue closure on merge. **These trailers are restricted to the `/complete-implementation` final commit step only.**

- **Task-level commits** (produced by `/start-task` during implementation) must NEVER include `Fixes #N`, `Closes #N`, or `Resolves #N`. Including them causes premature issue closure before quality gates in `/complete-implementation` have run.
- **The `/complete-implementation` final commit step** is the only place these trailers appear. After all quality gates pass, the final commit includes `Fixes #N` to close the issue on merge.
- **PR description**: do NOT add `Fixes #N` manually to the PR body during implementation. The `/complete-implementation` final commit carries the trailer — GitHub links the commit to the issue automatically.

This restriction ensures issues close only after the full pipeline (code review, feature verification, integration check, doc drift audit) has completed successfully.
