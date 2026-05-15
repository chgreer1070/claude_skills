## Agent Integration Analysis

### alignment-analyst.md

- **Classification**: BEHAVIOUR_CHANGE
- **MCP tools referenced**: `backlog_view`, `backlog_groom`, `backlog_update`, `backlog_close`, `backlog_resolve`
- **GitHub-specific**: Yes — Phase 1c explicitly runs `gh pr list -R Jamie-BitFlight/claude_skills --state merged --search "development-harness"` to extract PR numbers, then cites those PR numbers (e.g., `PR #N`) as mission alignment citations in the report. The entire `reverses-merged-direction` concern category depends on GitHub PR history.
- **Required change**: The `gh pr list` call and citation of `PR #N` numbers breaks with beads because beads has no PR concept. Historical direction signals would need to come from `bd log` or git history instead. The concern category `reverses-merged-direction` would need renaming or a beads-native equivalent. The `backlog_view`, `backlog_groom`, `backlog_update` calls work transparently through the MCP layer regardless of backend — no change needed for those.
- **bd CLI equivalent**: `bd log --limit 20` (no beads equivalent for merged PR history — git log is the alternative)

---

### backlog-item-groomer.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `backlog_list`, `backlog_view`, `backlog_add`, `backlog_update`, `backlog_groom`, `backlog_close`, `backlog_resolve`, `backlog_sync`, `backlog_normalize`, `backlog_pull`
- **GitHub-specific**: No — the agent interacts via MCP tools only. It reads item fields (`description`, `title`), calls `backlog_list` to find dependencies, and writes groomed content via `backlog_groom`. No direct GitHub URL construction or `#NNN` format use in logic paths.
- **Required change**: `backlog_sync`, `backlog_normalize`, and `backlog_pull` are GitHub-sync operations with no beads equivalent. When `BACKLOG_BACKEND=beads`, calling these will fail or no-op. Instructions should note that sync/normalize/pull are not applicable with beads backend and should be skipped. The `backlog_add` call in Step 4 dependency listing returns items from whatever backend is active — works transparently.
- **bd CLI equivalent**: `bd list`, `bd view <id>`, `bd add`, `bd update <id>`, `bd groom <id> --section <section>` (sync/normalize/pull — no beads equivalent)

---

### classifier.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `backlog_view`, `backlog_list`, `backlog_groom`, `backlog_update`, `backlog_close`, `backlog_resolve`
- **GitHub-specific**: Yes — the recurring-pattern analysis writes `#<issue>` formatted references in the Root-Cause Analysis section output: `- #<issue> — <title> — <year-month closed>`. This format assumes GitHub issue numbers as identifiers. With beads, IDs are UUIDs or bead slugs, not `#N`.
- **Required change**: The output format for recurring-pattern Root-Cause Analysis writes `#<issue>` identifiers. When `BACKLOG_BACKEND=beads`, these should reference bead IDs instead (e.g., `bd:<bead-id>` or the bead slug). The `backlog_list(search="...", include_closed=True, status="resolved")` call works transparently if beads backend supports search with resolved status.
- **bd CLI equivalent**: `bd list --search "<key terms>" --status resolved`, `bd view <id>`, `bd groom <id>`

---

### codebase-analyzer.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`, `sam_plan`
- **GitHub-specific**: Yes — `backlog_comment_issue`, `backlog_list_comments`, `backlog_read_comment`, and `backlog_list_issues` are GitHub comment/issue list operations. The agent uses `issue_number` as a required parameter for `artifact_register`. The agent description says "Pass the config dict to `sam_plan(action='create')` and receive the plan address back."
- **Required change**: `backlog_comment_issue`, `backlog_list_comments`, `backlog_read_comment`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_sync` are GitHub-specific or sync operations. With beads, these either won't exist or will no-op. The `issue_number` field used for artifact registration maps to bead ID when backend=beads — the MCP layer should abstract this, but agent instructions use `issue_number` terminology throughout. Add a note that `issue_number` maps to `bead_id` with beads backend.
- **bd CLI equivalent**: `bd view <id>`, `bd list`, artifact operations via beads artifact storage

---

### code-reviewer.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — `backlog_comment_issue`, `backlog_list_comments`, `backlog_read_comment`, `backlog_list_issues` are GitHub-specific. The `issue_number` field is required for `artifact_register`. The output format says `registered as artifact codebase-analysis / code-review-{task_id}-{slug} on issue #{issue_number}` — uses `#N` format.
- **Required change**: The `issue #{issue_number}` phrasing in status output uses GitHub issue syntax. With beads backend, this becomes bead ID. GitHub-comment MCP tools won't be available. The artifact registration pattern itself works if the ArtifactBackend is beads-compatible (using `LocalFilesystemArtifactProvider` or a beads artifact provider). Add note that `issue_number` = bead ID when backend=beads, and that comment tools are not available.
- **bd CLI equivalent**: `bd view <id>`, artifact operations via configured artifact provider

---

### context-refinement.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — same GitHub-specific comment tools (`backlog_comment_issue`, `backlog_list_comments`, `backlog_read_comment`, `backlog_list_issues`) are declared in the tools field. The agent also references the "Intent Source" as a human-decision artifact linked in the backlog item body — this depends on GitHub issue body structure for discovering the path.
- **Required change**: GitHub-comment MCP tools not available with beads. The Intent Source discovery from the issue body needs a beads-compatible path (bead metadata field or bead description). `backlog_normalize`, `backlog_pull`, `backlog_sync` not applicable. Add note mapping `issue_number` → `bead_id`.
- **bd CLI equivalent**: `bd view <id>`, `sam_plan` operations unchanged (SAM backend is separate from backlog backend)

---

### contract-verification.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools declared in frontmatter. The agent itself is read-only (no backlog writes in its procedure) — it returns a `<concerns>` block and does not call backlog MCP tools in its instructions. The full backlog tool list in frontmatter is likely inherited from a template; actual usage is limited to reading the architect spec via `artifact_read`.
- **Required change**: Frontmatter tool list includes GitHub-specific tools that aren't called by the agent body. No behavioral change needed for beads — the agent's core procedure uses only `artifact_read` (works transparently) and file reads. Low-priority cleanup of unused tools in frontmatter.
- **bd CLI equivalent**: No direct bd calls; artifact reads work through configured ArtifactBackend

---

### dh-context-gathering.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools declared in frontmatter. The agent procedure uses `sam_plan(action='read')` and `sam_plan(action='update', context=...)` exclusively. No backlog MCP calls appear in the actual procedure steps. The tool list is over-broad.
- **Required change**: No behavioral change needed — actual procedure uses SAM MCP only. Frontmatter tool list includes GitHub-specific tools not called in the agent body. Low-priority frontmatter cleanup.
- **bd CLI equivalent**: SAM operations unchanged; no direct bd calls

---

### doc-drift-auditor.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools in frontmatter. The agent's procedure uses `artifact_register(issue_number=..., type="audit-report", ...)` and checks that `issue_number` is provided. The `#` syntax appears in the BLOCKED format: `artifact_register` returns an error — report the exact error text.
- **Required change**: The `issue_number` parameter requirement is core to the agent's operation — with beads backend, this must be a bead ID instead. The error-handling instruction "Block immediately if `artifact_register` returns an error — report the exact error text and do not fall back to writing to disk" is correct behavior regardless of backend. Add note that `issue_number` = bead ID when backend=beads.
- **bd CLI equivalent**: `bd view <id>`, artifact registration via configured ArtifactBackend

---

### ecosystem-researcher.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools declared in frontmatter. The procedure writes output via `sam_plan` only — no backlog MCP calls appear in the agent's actual steps. Full backlog tool list in frontmatter is over-broad template inheritance.
- **Required change**: No behavioral change needed — actual procedure uses SAM MCP only. Frontmatter tool list includes GitHub-specific tools not called in the procedure. Low-priority frontmatter cleanup.
- **bd CLI equivalent**: SAM operations unchanged; no direct bd calls

---

### fact-checker.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `backlog_view`, `backlog_groom`
- **GitHub-specific**: Minimal — the agent body uses `gh` CLI via Bash (listed in `skills: [gh]`) as one verification method: "Bash with `gh` — query GitHub API for repo metadata, releases, file content." This is for external fact verification (checking library releases, etc.), not for backlog item identity. The `backlog_view` and `backlog_groom` calls use a `selector` parameter that can be `#N`, title substring, or URL.
- **Required change**: The `selector` format `#N` used in the grooming swarm dispatch works transparently if the backlog backend resolves it. With beads backend, the selector would be a bead ID or slug — no agent instruction change needed if the MCP layer handles resolution. The `gh` CLI usage for external verification (checking library releases on GitHub) is unrelated to the backend and requires no change.
- **bd CLI equivalent**: `bd view <selector>`, `bd groom <selector> --section "Fact-Check"`

---

### feature-researcher.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools in frontmatter. The procedure uses `sam_plan` for creating and updating the feature context document. No backlog MCP calls appear in the actual procedure steps.
- **Required change**: No behavioral change needed — actual procedure uses SAM MCP only. Frontmatter tool list is over-broad. Low-priority cleanup.
- **bd CLI equivalent**: SAM operations unchanged

---

### feature-verifier.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools in frontmatter. Step 1 uses `artifact_read(issue_number={issue_number}, artifact_type="architect")` and `artifact_read(issue_number={issue_number}, artifact_type="task-plan")`. The `issue_number` is referenced throughout. The backlog item's Concerns section may contain `CONTRACT:` prefixed entries — these are read from the backlog item body.
- **Required change**: `issue_number` parameter throughout maps to bead ID when backend=beads. GitHub-comment tools not called in procedure. The Concerns section reading from backlog item body via `artifact_read` works if beads ArtifactBackend stores the content. Add note mapping `issue_number` → `bead_id`.
- **bd CLI equivalent**: `bd view <id>`, artifact reads via configured ArtifactBackend

---

### generic-stage-agent.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools in frontmatter. The procedure is minimal: load skills, read task/artifact file, follow stage workflow, run quality gates, write output artifact. No backlog MCP calls appear in the procedure itself.
- **Required change**: No behavioral change needed — actual procedure uses SAM MCP and file operations. Frontmatter tool list is over-broad. Low-priority cleanup.
- **bd CLI equivalent**: SAM operations unchanged

---

### impact-analyst.md

- **Classification**: BEHAVIOUR_CHANGE
- **MCP tools referenced**: `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_create_milestone`, `backlog_create_project`, `backlog_create_sam_task`, `backlog_get_ready_sam_tasks`, `backlog_get_sam_tasks`, `backlog_get_soonest_milestone`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_labels`, `backlog_list_merged_prs`, `backlog_list_milestones`, `backlog_list_projects`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_strike_entry`, `backlog_sync`, `backlog_update`, `backlog_update_sam_task_status`, `backlog_view`, `dispatch_conflicts`, `dispatch_create_plan`, `dispatch_item_status`, `dispatch_read`, `dispatch_spawn`, `dispatch_stale_check`, `dispatch_validate`, `dispatch_wave_start`, `dispatch_wave_status`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — deeply. The agent has the widest tool surface of all agents. It uses `backlog_list_merged_prs` (GitHub-specific — lists merged PRs), `backlog_list_labels` (GitHub label management), `backlog_create_milestone`, `backlog_list_milestones`, `backlog_create_project`, `backlog_list_projects` (GitHub Projects/Milestones), `backlog_comment_issue`, `backlog_list_comments`, `backlog_read_comment` (GitHub comment operations). The core procedure calls `backlog_view(selector=selector, summary=False)` and `backlog_groom(section="Impact Radius")` — these work transparently. However, the expanded tool surface implies the agent may attempt GitHub-specific operations depending on context.
- **Required change**: Most GitHub-specific tools (`backlog_list_merged_prs`, `backlog_list_labels`, `backlog_create_milestone`, `backlog_list_milestones`, `backlog_create_project`, `backlog_list_projects`, all comment tools) will fail or no-op with beads backend. The core procedure steps (`backlog_view`, `backlog_groom`) work transparently. If the agent's `SendMessage` broadcasts reference `#N` item selectors, those need to use bead IDs instead. The dispatch tools (`dispatch_*`) are backend-independent (SQLite dispatch state). Medium priority — core behavior unaffected but large tool surface creates failure surface.
- **bd CLI equivalent**: `bd view <id>`, `bd groom <id> --section "Impact Radius"`, `bd list`; milestone/project/label/comment tools have no beads equivalent

---

### integration-checker.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — GitHub-comment tools in frontmatter. The procedure uses `artifact_read(issue_number={issue_number}, artifact_type="task-plan")` to read the plan. `issue_number` is referenced as a required input.
- **Required change**: `issue_number` maps to bead ID when backend=beads. GitHub-comment tools not called in procedure. Add note mapping terminology. Low behavioral impact.
- **bd CLI equivalent**: `bd view <id>`, artifact reads via configured ArtifactBackend

---

### plan-validator.md

- **Classification**: BEHAVIOUR_CHANGE
- **MCP tools referenced**: `sam_task`, `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — Dimension 10 (Impact Radius Coverage) explicitly calls `backlog_view(selector="{issue_number}")` to retrieve the groomed backlog item and read its Impact Radius section. The procedure says: "If a GitHub issue number is present, retrieve the backlog item via `backlog_view(selector="{issue_number}")`". The `issue` frontmatter field in SAM task YAML may contain a GitHub issue number or a backlog item path — both are used for retrieval.
- **Required change**: Dimension 10 uses `backlog_view(selector="{issue_number}")` — this works transparently with beads backend if the MCP layer routes by bead ID. However, the instruction text says "GitHub issue number" explicitly, which creates confusion. The check `"If a GitHub issue number is present, retrieve the backlog item via backlog_view"` needs rewording to "If a backlog item ID is present" to be backend-agnostic. The selector format (`#N` vs bead-id) must resolve correctly in the MCP layer.
- **bd CLI equivalent**: `bd view <id>`, `sam_plan` operations unchanged

---

### rtica-assessor.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `backlog_view`, `backlog_groom`, `backlog_update`, `backlog_close`, `backlog_resolve`
- **GitHub-specific**: Minimal — the agent uses `backlog_view(selector=<item_ref>, summary=False, sections=["description", "Impact Radius", "Fact-Check"])` and `backlog_groom(selector=<item_ref>, section="RT-ICA", content=...)`. The `item_ref` format can be `#N`, title substring, or URL — so `#N` format appears in the selector. The `SendMessage` broadcasts use `<item_ref>` which may be `#N`.
- **Required change**: If beads IDs are not prefixed with `#`, the `item_ref` format in broadcasts would change. If the MCP layer accepts bead IDs as selectors (not just `#N`), no change needed. The agent procedure is otherwise backend-agnostic. Low behavioral impact if selector resolution is handled by MCP layer.
- **bd CLI equivalent**: `bd view <id>`, `bd groom <id> --section "RT-ICA"`

---

### service-docs-maintainer.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `backlog_view`, `backlog_list`, `backlog_groom`, `backlog_update`, `backlog_close`, `backlog_resolve`
- **GitHub-specific**: No — the agent's procedure uses `git diff`, `git log`, file reads, and the Edit tool. No GitHub issue numbers or `#NNN` format used in logic paths. The backlog tools in the frontmatter are for optional backlog-item context reading, not for core operation.
- **Required change**: None for core behavior. Backlog MCP tools work transparently through backend abstraction. No GitHub-specific logic present.
- **bd CLI equivalent**: `bd view <id>`, `bd list` — but not actually called in the procedure

---

### swarm-task-planner.md

- **Classification**: BEHAVIOUR_CHANGE
- **MCP tools referenced**: `sam_plan`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — the agent generates task YAML that includes `issue` frontmatter field which stores GitHub issue numbers. The agent explicitly instructs: "Do NOT generate `Fixes #N`, `Closes #N`, or `Resolves #N` in task acceptance criteria" — this shows GitHub trailer awareness. The TN bookend template says `t0_baseline_source: "artifact:T0-baseline:issue={issue_number}"` — hard-codes `issue=` terminology. The PLAN.md frontmatter template references `issue:` fields. The generated task YAML propagates `issue_number` into every downstream agent that reads it.
- **Required change**: The generated task YAML uses `issue:` as the field name for the backlog item reference. With beads backend, this field stores a bead ID instead of a GitHub issue number. The prohibition on `Fixes #N`, `Closes #N` trailers is a git commit message concern — unrelated to backend. The `t0_baseline_source` field format `artifact:T0-baseline:issue={issue_number}` uses GitHub terminology but is a string label for human reference only. The `sam_plan` registration path is backend-independent. Primary change: document that `issue:` field in generated task YAML holds a bead ID when backend=beads.
- **bd CLI equivalent**: `bd list`, `bd view <id>`, artifact registration via configured ArtifactBackend; `sam_plan` unchanged

---

### t0-baseline-capture.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — the `issue_number` field is required for `artifact_register`. The STATUS output block says `type=T0-baseline, issue={issue_number}` — uses issue terminology. The registration call: `artifact_register(issue_number={issue_number}, type="T0-baseline", ...)`.
- **Required change**: `issue_number` maps to bead ID when backend=beads. The terminology in STATUS output and comments uses "issue number" — should be generalized to "item ID" or the MCP layer should accept either. The agent's core procedure (reading plan file, running Bash commands, building YAML, calling `artifact_register`) is backend-agnostic except for the `issue_number` field name.
- **bd CLI equivalent**: `bd view <id>`, artifact registration via configured ArtifactBackend

---

### task-worker.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: None declared in frontmatter (no `tools:` field). The agent uses `mcp__plugin_dh_sam__sam_task` and `mcp__plugin_dh_backlog__profile_load` via its procedure instructions.
- **GitHub-specific**: No — the agent reads the task `agent` field via `sam_task(action='read')` and loads a profile via `profile_load(agent_name=...)`. No GitHub issue numbers, `#NNN` format, or GitHub-specific operations in the procedure.
- **Required change**: None. The agent is purely SAM-focused with profile loading. Both SAM and profile operations are backend-agnostic. No change needed for beads.
- **bd CLI equivalent**: SAM operations unchanged; no direct bd calls

---

### tn-verification-gate.md

- **Classification**: INSTRUCTION_UPDATE
- **MCP tools referenced**: `sam_plan`, `sam_task`, `sam_active_task`, `artifact_get`, `artifact_list`, `artifact_migrate`, `artifact_read`, `artifact_register`, `backlog_add`, `backlog_close`, `backlog_comment_issue`, `backlog_groom`, `backlog_list`, `backlog_list_comments`, `backlog_list_issues`, `backlog_normalize`, `backlog_pull`, `backlog_read_comment`, `backlog_resolve`, `backlog_sync`, `backlog_update`, `backlog_view`, `profile_list`, `profile_load`
- **GitHub-specific**: Yes — `issue_number` is required for both `artifact_read` (reading T0 baseline) and `artifact_register` (registering TN result). The assembled YAML includes `t0_baseline_source: "artifact:T0-baseline:issue={issue_number}"` — uses GitHub terminology as a string label. The STATUS and BLOCKED outputs use `issue={issue_number}` phrasing.
- **Required change**: Same as t0-baseline-capture — `issue_number` maps to bead ID when backend=beads. The `t0_baseline_source` field format uses "issue=" terminology but is a human-readable string, not a functional identifier. Generalize terminology in agent instructions from "issue number" to "item ID". Core procedure (running Bash commands, computing CriterionStatus matrix, calling `artifact_register`) is backend-agnostic.
- **bd CLI equivalent**: `bd view <id>`, artifact read/register via configured ArtifactBackend

---

## Summary Table

| Agent | Classification | MCP Tools Count | GitHub-specific | Priority |
|---|---|---|---|---|
| alignment-analyst | BEHAVIOUR_CHANGE | 5 | Yes — gh pr list, PR #N citations | High |
| backlog-item-groomer | INSTRUCTION_UPDATE | 10 | No | Medium |
| classifier | INSTRUCTION_UPDATE | 6 | Yes — #N in Root-Cause output | Medium |
| codebase-analyzer | INSTRUCTION_UPDATE | 22 | Yes — comment tools, issue_number | Medium |
| code-reviewer | INSTRUCTION_UPDATE | 22 | Yes — comment tools, issue_number | Medium |
| context-refinement | INSTRUCTION_UPDATE | 22 | Yes — comment tools, Intent Source | Medium |
| contract-verification | INSTRUCTION_UPDATE | 22 | Yes — comment tools (unused in body) | Low |
| dh-context-gathering | INSTRUCTION_UPDATE | 22 | Yes — comment tools (unused in body) | Low |
| doc-drift-auditor | INSTRUCTION_UPDATE | 22 | Yes — comment tools, issue_number | Medium |
| ecosystem-researcher | INSTRUCTION_UPDATE | 22 | Yes — comment tools (unused in body) | Low |
| fact-checker | INSTRUCTION_UPDATE | 2 | Minimal — gh for external verification only | Low |
| feature-researcher | INSTRUCTION_UPDATE | 22 | Yes — comment tools (unused in body) | Low |
| feature-verifier | INSTRUCTION_UPDATE | 22 | Yes — comment tools, issue_number | Medium |
| generic-stage-agent | INSTRUCTION_UPDATE | 22 | Yes — comment tools (unused in body) | Low |
| impact-analyst | BEHAVIOUR_CHANGE | 43 | Yes — milestone, project, label, PR, comment tools | High |
| integration-checker | INSTRUCTION_UPDATE | 22 | Yes — comment tools, issue_number | Medium |
| plan-validator | BEHAVIOUR_CHANGE | 22 | Yes — Dimension 10 uses issue_number for backlog_view | High |
| rtica-assessor | INSTRUCTION_UPDATE | 5 | Minimal — #N in selector format only | Low |
| service-docs-maintainer | INSTRUCTION_UPDATE | 6 | No | None |
| swarm-task-planner | BEHAVIOUR_CHANGE | 22 | Yes — generates task YAML with issue: field, #N trailer prohibition | High |
| t0-baseline-capture | INSTRUCTION_UPDATE | 22 | Yes — issue_number required for artifact_register | Medium |
| task-worker | NO_CHANGE | 0 | No | None |
| tn-verification-gate | INSTRUCTION_UPDATE | 22 | Yes — issue_number required for artifact_register and artifact_read | Medium |
