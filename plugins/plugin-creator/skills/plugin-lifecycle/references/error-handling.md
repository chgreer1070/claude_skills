# Error Handling

| Failure | Recovery |
|---------|----------|
| RT-ICA returns BLOCKED | Present missing inputs to user; do not proceed to Discussion or Research until resolved |
| Discussion phase skipped (user provides no answers) | Use defaults: user-invocable=true, balanced verbosity, no tool restrictions; note assumptions in discuss-CONTEXT.md |
| Researcher subagent returns empty output | Re-spawn that researcher with more specific prompt; do not proceed to Design with incomplete findings |
| research-FINDINGS.md merge incomplete (one researcher missing) | Identify which research-N file is absent; re-run that researcher; do not proceed to Design until all 4 are present |
| Plan checker returns FAIL | Return design-PLAN.md and FAIL feedback to planner; iterate up to 3 times before escalating to user |
| plugin_validator.py not found | Verify path `plugins/plugin-creator/scripts/plugin_validator.py`; check git status; the script must exist before Debug phase can run |
| SK007 error (skill exceeds token limit) | Run `/plugin-creator:refactor-skill` — this error requires splitting, not editing |
| SK006 warning (skill approaching limit) | Extract content to `references/` directory; re-validate after extraction |
| Broken link errors after Create phase | Read the file containing the link; verify the target path exists; fix with Edit tool directly |
| claude plugin validate fails with path error | Confirm `.claude-plugin/plugin.json` exists at the plugin root; path must start with `./` |
| Documentation phase produces no README.md | Re-run documentation task with explicit instruction to create README.md; verify file exists before proceeding |
| Verify phase passes Layers 1–3 but fails Layer 4 | Read each broken cross-reference; fix with Edit tool; re-run Layer 4 check manually before returning to Phase 5 |
| STATE.md absent (session resumed) | Read all artifact files in `.claude/plan/{plugin-name}/` to reconstruct current phase; create STATE.md from inferred state |
| Validator output is ambiguous (warnings only, no errors) | Treat as passing — warnings do not block progression; note warnings in STATE.md for future optimization |
