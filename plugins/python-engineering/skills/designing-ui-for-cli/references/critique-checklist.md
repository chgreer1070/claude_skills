# Critique Checklist for TUI/CLI Interfaces

Two-assessment critique adapted from impeccable for terminal interfaces. Produces a Nielsen score (0–40), an AI-slop verdict, a deterministic detector report, persona red-flags, and a prioritised action list.

## Two-Assessment Isolation Rule

Launch two independent assessments. Neither may see the other's output. This isolation is what makes the combined score honest. Running both in one head silently anchors them to each other; do not shortcut it for cost, speed, or context-size reasons.

Delegate each assessment to a separate sub-agent. Each returns structured findings as text. Do NOT output findings to the user yet.

Fall back to sequential in-head work only if the environment genuinely cannot spawn sub-agents.

## Assessment A: LLM Design Review

Read the relevant source files (Python CLI module, TCSS file, Rich console code, Questionary prompt definitions, `--help` output captured to a file). When a Textual app is the target, run it in a headless harness and capture screenshots or `--snapshot` output. Think like a design director.

### AI Slop Detection (CRITICAL)

Does this look like every other AI-generated terminal interface? Run the two-altitude category-reflex check from `./ai-slop-test.md`:

- First-order: theme + palette guessable from category alone (DevOps tool feels green-on-black; AI CLI feels purple-and-emoji)
- Second-order: aesthetic family guessable from category-plus-anti-references

The test: if someone said "AI made this," would you believe them immediately? If yes, slop verdict is FAIL.

Cross-check against the bans in `./anti-references.md`: lolcat output, splash on every invocation, fake throbbers, decorative borders on every panel, hacker green-on-black default, emoji-as-bullet for every list, gradient banners via 24-bit ANSI.

### Holistic Design Review

Visual hierarchy (eye flow on first render, primary action clarity), information architecture (subcommand grouping, cognitive load), emotional resonance (does it match register and operating context?), discoverability (are interactive elements obvious — keybindings shown? subcommands listed?), composition (column alignment, panel rhythm, padding), typography (text-style hierarchy: bold/dim/italic roles), colour (purposeful use, semantic meaning, accessibility), states & edge cases (empty, loading, error, success, non-TTY, NO_COLOR), microcopy (clarity, tone, helpfulness, error wording).

### Cognitive Load

Run the 8-item cognitive load checklist below. Report failure count: 0–1 = low (good), 2–3 = moderate, 4+ = critical.

- [ ] Single focus: can the user complete their primary task without distraction from competing elements?
- [ ] Chunking: is information presented in digestible groups (≤4 items per group)?
- [ ] Grouping: are related items visually grouped (panel borders, spacing, shared background)?
- [ ] Visual hierarchy: is it immediately clear what's most important on screen?
- [ ] One thing at a time: can the user focus on a single decision before moving to the next?
- [ ] Minimal choices: are decisions simplified (≤4 visible options at any decision point)?
- [ ] Working memory: does the user need to remember information from a previous screen to act on the current one?
- [ ] Progressive disclosure: is complexity revealed only when needed (default / `-v` / `-vv`)?

Count visible options at each decision point. If >4, flag it. Check for progressive disclosure: default output → `-v` adds detail → `-vv` adds debug.

### Emotional Journey

What emotion does this CLI evoke on first invocation? Is that intentional? Run peak-end rule: is the most intense moment positive (success message, completion summary), and does the experience end well (clean exit, useful final line)? Check for anxiety spikes at high-stakes moments (destructive ops, irreversible commits, production-affecting commands). Are there design interventions (confirm prompts with named action, `--dry-run` flag, undo where possible)?

### Nielsen's Heuristics

Score each of the 10 heuristics 0–4. Be honest with scores. A 4 means genuinely excellent. Most real interfaces score 20–32.

#### 1. Visibility of System Status

Keep users informed about what's happening through timely, appropriate feedback.

TUI checks:

- Spinner reflects actual progress, not a fake animation loop
- Long operations (>2s) show progress text describing what's happening
- Non-zero exit code distinct from success and surfaced before the prompt returns
- Multi-step processes show step indicator (`[2/5] Compiling...`)
- Streaming output flushes as it arrives, not buffered until completion

| Score | Criteria |
|-------|----------|
| 0 | No feedback; user is guessing what happened |
| 1 | Rare feedback; most actions produce no visible response |
| 2 | Partial; some states communicated, major gaps remain |
| 3 | Good; most operations give clear feedback, minor gaps |
| 4 | Excellent; every action confirms, progress is always visible |

#### 2. Match Between System and Real World

Speak the user's language. Use domain conventions. Information appears in natural, logical order.

TUI checks:

- Labels and column headers use user vocabulary, not implementation terms
- Error messages name the user-facing concept (`config file not found`), not the implementation (`FileNotFoundError: /etc/foo.yaml`)
- Subcommand verbs are plain English (`list`, `add`, `remove`), not internal jargon
- Status vocabulary consistent with platform conventions (`running` / `stopped` / `failed`, not custom enum names)

| Score | Criteria |
|-------|----------|
| 0 | Pure tech jargon, alien to users |
| 1 | Mostly confusing; requires domain expertise to navigate |
| 2 | Mixed; some plain language, some jargon leaks through |
| 3 | Mostly natural; occasional term needs context |
| 4 | Speaks the user's language fluently throughout |

#### 3. User Control and Freedom

Users need a clear emergency exit from unwanted states without extended dialogue.

TUI checks:

- Ctrl-C cancellation honoured; partial state cleaned up or recoverable
- Esc closes modals and prompts in Textual / Questionary
- `--dry-run` flag available for destructive ops
- No long unskippable splash screens
- Confirm prompts allow N/n as default to abort

| Score | Criteria |
|-------|----------|
| 0 | Users get trapped; no way out without refreshing |
| 1 | Difficult exits; must find obscure paths to escape |
| 2 | Some exits; main flows have escape, edge cases don't |
| 3 | Good control; users can exit and undo most actions |
| 4 | Full control; undo, cancel, back, and escape everywhere |

#### 4. Consistency and Standards

Users shouldn't wonder whether different words, situations, or actions mean the same thing.

TUI checks:

- Status symbol always occupies column 0 of a row (the Status Column Rule)
- Flag naming matches GNU conventions (`--long-name` / `-l`); no shouty `--LONGNAME` or undocumented single-dash long flags
- Subcommand verbs consistent across the tool (`add` always means add, never `add` here and `create` there)
- Colour-to-meaning mapping consistent (red = error in every subcommand, never red = active anywhere)
- Output format consistent (table columns in same order, headers in same case)

| Score | Criteria |
|-------|----------|
| 0 | Inconsistent everywhere; feels like different products stitched together |
| 1 | Many inconsistencies; similar things look/behave differently |
| 2 | Partially consistent; main flows match, details diverge |
| 3 | Mostly consistent; occasional deviation, nothing confusing |
| 4 | Fully consistent; cohesive system, predictable behavior |

#### 5. Error Prevention

Better than good error messages is a design that prevents problems in the first place.

TUI checks:

- Confirm before destructive ops (`questionary.confirm("Delete project? Cannot be undone")` — named action, not generic "Are you sure?")
- Constrained input via Choice / enum types instead of free-form strings
- Smart defaults that reduce errors (sensible config paths, current dir as fallback)
- Explicit `--force` required for irreversible operations
- Validation runs before destructive work begins, not midway

| Score | Criteria |
|-------|----------|
| 0 | Errors easy to make; no guardrails anywhere |
| 1 | Few safeguards; some inputs validated, most aren't |
| 2 | Partial prevention; common errors caught, edge cases slip |
| 3 | Good prevention; most error paths blocked proactively |
| 4 | Excellent; errors nearly impossible through smart constraints |

#### 6. Recognition Rather Than Recall

Minimize memory load. Make objects, actions, and options visible or easily retrievable.

TUI checks:

- Keybinding hints visible in footer (Textual `Footer` widget or Rich panel showing `q quit  / search`)
- Help text reachable from every level (`tool --help`, `tool subcommand --help`, `tool subcommand sub --help`)
- Recent items / history surfaced where relevant (shell history, recent files)
- Autocomplete via shell-completion script
- Choice prompts list options instead of requiring the user to type them from memory

| Score | Criteria |
|-------|----------|
| 0 | Heavy memorization; users must remember paths and commands |
| 1 | Mostly recall; many hidden features, few visible cues |
| 2 | Some aids; main actions visible, secondary features hidden |
| 3 | Good recognition; most things discoverable, few memory demands |
| 4 | Everything discoverable; users never need to memorize |

#### 7. Flexibility and Efficiency of Use

Accelerators, invisible to novices, speed up expert interaction.

TUI checks:

- Short flags + long flags + aliases for power users (`-v` / `--verbose`)
- Pipeable output: stdout is line-oriented and ANSI-free when not a TTY
- Config file support so repeated invocations don't repeat flags
- Bulk operations (accept multiple positional args, glob patterns)
- Shell-completion script generated and installable

| Score | Criteria |
|-------|----------|
| 0 | One rigid path; no shortcuts or alternatives |
| 1 | Limited flexibility; few alternatives to the main path |
| 2 | Some shortcuts; basic keyboard support, limited bulk actions |
| 3 | Good accelerators; keyboard nav, some customization |
| 4 | Highly flexible; multiple paths, power features, customizable |

#### 8. Aesthetic and Minimalist Design

Interfaces should not contain irrelevant or rarely needed information. Every element should serve a purpose.

TUI checks:

- Progressive disclosure: default output is minimal, `-v` adds detail, `-vv` adds debug
- No decorative chrome (borders that don't aid hierarchy, splash on every invocation, emoji-as-bullet for every list)
- Spacing and panel padding earn their place
- One element dominant per screen — not five panels of equal weight
- Copy follows "every word earns its place"; no em dashes

| Score | Criteria |
|-------|----------|
| 0 | Overwhelming; everything competes for attention equally |
| 1 | Cluttered; too much noise, hard to find what matters |
| 2 | Some clutter; main content clear, periphery noisy |
| 3 | Mostly clean; focused design, minor visual noise |
| 4 | Perfectly minimal; every element earns its pixel |

#### 9. Help Users Recognize, Diagnose, and Recover from Errors

Error messages should use plain language, precisely indicate the problem, and constructively suggest a solution.

TUI checks:

- Error format defined in the shape brief and applied consistently (what happened, why, how to fix)
- Suggestions for typo'd subcommands (`did you mean: install?`)
- User input preserved on error (don't wipe the prompt buffer on validation failure)
- Tracebacks formatted via `rich.traceback` or Typer pretty exceptions, hidden behind `--debug` for end-users
- Exit code distinct per error class so wrappers can branch

| Score | Criteria |
|-------|----------|
| 0 | Cryptic errors; codes, jargon, or no message at all |
| 1 | Vague errors; "Something went wrong" with no guidance |
| 2 | Clear but unhelpful; names the problem but not the fix |
| 3 | Clear with suggestions; identifies problem and offers next steps |
| 4 | Perfect recovery; pinpoints issue, suggests fix, preserves user work |

#### 10. Help and Documentation

Even if the system is usable without docs, help should be easy to find, task-focused, and concise.

TUI checks:

- `--help` useful at every level (top-level, subcommand, sub-subcommand)
- `man` page or equivalent (`mkdocs` site, `--help-all` flag)
- Example invocations included in `--help` output, not just flag listings
- Help text fits on a typical 80-cell terminal without horizontal scroll
- README links surfaced from `--help` epilogue

| Score | Criteria |
|-------|----------|
| 0 | No help available anywhere |
| 1 | Help exists but hard to find or irrelevant |
| 2 | Basic help; FAQ or docs exist, not contextual |
| 3 | Good documentation; searchable, mostly task-focused |
| 4 | Excellent contextual help; right info at the right moment |

### Score Summary

Total possible: 40 points (10 heuristics × 4 max)

| Score Range | Rating | What It Means |
|-------------|--------|---------------|
| 36–40 | Excellent | Minor polish only; ship it |
| 28–35 | Good | Address weak areas, solid foundation |
| 20–27 | Acceptable | Significant improvements needed before users are happy |
| 12–19 | Poor | Major UX overhaul required; core experience broken |
| 0–11 | Critical | Redesign needed; unusable in current state |

Be honest with scores. A 4 means genuinely excellent. Most real interfaces score 20–32.

### Issue Severity (P0–P3)

Tag each individual issue found during scoring with a priority level:

| Priority | Name | Description | Action |
|----------|------|-------------|--------|
| P0 | Blocking | Prevents task completion entirely | Fix immediately; this is a showstopper |
| P1 | Major | Causes significant difficulty or confusion | Fix before release |
| P2 | Minor | Annoyance, but workaround exists | Fix in next pass |
| P3 | Polish | Nice-to-fix, no real user impact | Fix if time permits |

Tip: if you're unsure between two levels, ask: "Would a user contact support about this?" If yes, it's at least P1.

### Assessment A Output

Return structured findings covering: AI slop verdict, heuristic scores (per-heuristic and total /40), cognitive load failure count, what's working (2–3 items), priority issues (3–5 with what / why / fix / severity tag), minor observations, and provocative questions.

## Assessment B: Deterministic Detector

Run a deterministic checker against the source files. Each check is a binary pass/fail with a file location.

### TCSS lint

For projects with Textual TCSS files, run TCSS validation:

- Selector validity: every selector resolves to a Textual widget class or `:focus` / `:hover` / `:disabled` / `:dark` / `:light` pseudo-state
- Theme variable usage: `$primary` / `$accent` / `$surface` / `$panel` / `$boost` referenced from variables, not hard-coded hex per-rule
- No conflicting `:dark` / `:light` rules
- Border-style tokens limited to TCSS-supported set (`none`, `ascii`, `round`, `thick`, `heavy`, `double`, `dashed`)

### Rich markup escape audit

Scan source for Rich markup patterns:

- User-supplied input rendered through `console.print()` without `escape()` is a finding (XSS-equivalent: a filename containing `[red]` corrupts output)
- Hard-coded markup tags that don't close (`[bold]` without `[/bold]`)
- Style strings in `Text` constructor that aren't valid Rich style names

### Terminal-width tests

Render the primary command output at 80, 100, 120, and 160 cells. Check:

- No horizontal scroll at 80 cells for the primary command path
- Truncation strategy explicit (Rich `Text.truncate()` with ellipsis, not silent cell-cut)
- Tables collapse columns or switch to vertical layout at narrow widths
- Width detection respects `COLUMNS` env var

### NO_COLOR check

Run the target with `NO_COLOR=1`:

- All ANSI colour escape sequences absent from output
- Status still distinguishable by symbol or text label, not colour alone
- Exit code unchanged from coloured run

### Non-TTY fallback test

Pipe the target's stdout to a file or `cat`:

- ANSI escape sequences stripped automatically
- Progress bars suppressed; replaced with line-oriented status messages or silenced
- Output is line-oriented and parseable
- No interactive prompts blocking the pipe

### Assessment B Output

Return: TCSS lint findings, Rich markup audit findings, width-test results per tier, NO_COLOR result, non-TTY result. Each finding includes file path and line number where applicable. Note any false positives.

## Generate Combined Critique Report

Synthesize both assessments into a single report. Do NOT simply concatenate. Weave the findings together, noting where the LLM review and detector agree, where the detector caught issues the LLM missed, and where detector findings are false positives.

Structure your feedback as a design director would.

### Anti-Patterns Verdict

Start here. Does this look AI-generated?

LLM assessment: your own evaluation of AI slop tells. Cover overall aesthetic feel, layout sameness, generic composition, missed opportunities for personality.

Deterministic scan: summarize what the automated detector found, with counts and file locations. Note any additional issues the detector caught that you missed, and flag any false positives.

### Design Health Score

Present the Nielsen's 10 heuristics scores as a table:

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | ? | [specific finding or "n/a" if solid] |
| 2 | Match System / Real World | ? | |
| 3 | User Control and Freedom | ? | |
| 4 | Consistency and Standards | ? | |
| 5 | Error Prevention | ? | |
| 6 | Recognition Rather Than Recall | ? | |
| 7 | Flexibility and Efficiency | ? | |
| 8 | Aesthetic and Minimalist Design | ? | |
| 9 | Error Recovery | ? | |
| 10 | Help and Documentation | ? | |
| Total | | ??/40 | [Rating band] |

### Overall Impression

A brief gut reaction: what works, what doesn't, and the single biggest opportunity.

### What's Working

Highlight 2–3 things done well. Be specific about why they work.

### Priority Issues

The 3–5 most impactful design problems, ordered by importance.

For each issue, tag with P0–P3 severity:

- [P?] What: name the problem clearly
- Why it matters: how this hurts users or undermines goals
- Fix: what to do about it (be concrete; name the file and the change)
- Suggested next step: which checklist or reference to consult next (`./audit-checklist.md`, `./polish-checklist.md`, `./colour-strategy.md`, `./register-decision.md`, `./theme-decision.md`, `./shape-brief-template.md`, `./ai-slop-test.md`, `./anti-references.md`)

### Persona Red Flags

Auto-select 2–3 personas most relevant to this CLI type using the selection table below. Walk through the primary user action as each persona and list specific red flags found.

#### Persona Selection Table

| CLI Type | Primary Personas | Why |
|----------|------------------|-----|
| Dashboards (Textual TUIs, persistent views) | Alex, Sam | Power users, accessibility |
| One-shot scripts (single-invocation tools) | Jordan, Riley | First-timers, edge cases |
| Data pipelines (ETL, batch processors) | Alex, Riley | Power users, edge cases |
| Interactive prompts (Questionary wizards) | Jordan, Sam, Casey | Clarity, accessibility, slow connections |

#### Personas

##### Alex (Power User)

Profile: expert with similar CLI tools. Expects efficiency, hates hand-holding. Will find shortcuts or leave.

TUI red flags:

- Forced splash screens that can't be skipped (`--quiet` / `--no-splash` missing)
- No `--quiet` mode or `--json` output mode for scripting
- No shell completion (bash / zsh / fish) generated
- One-item-at-a-time when batch is natural (no glob support, no `--all` flag)
- Redundant confirmation steps for low-risk reversible actions

##### Jordan (Confused First-Timer)

Profile: never used this type of CLI. Needs guidance at every step. Will abandon rather than figure it out.

TUI red flags:

- Cryptic error codes (`Error: EACCES` with no plain-English follow-up)
- Icon-only or symbol-only status with no text label
- No `--help` at every level (top-level only, subcommands silent)
- No example invocations in help output
- Ambiguous next steps after running a subcommand (no "now run X" hint)

##### Sam (Accessibility-Dependent)

Profile: uses screen reader through terminal, keyboard-only, may have low vision or colour-blindness.

TUI red flags:

- Status conveyed by colour alone (red text without `✗` symbol; green without `✓`)
- Screen-reader-via-terminal mode broken (Textual app blocks readers; Rich live regions don't announce updates)
- No `NO_COLOR` env var support
- No high-contrast mode or `--mono` flag
- Focus indicator missing or invisible against terminal background

##### Riley (Stress Tester)

Profile: methodical user who pushes interfaces beyond the happy path. Tests edge cases, tries unexpected inputs.

TUI red flags:

- Silent failures on edge inputs (empty file, file with one byte, file with 1M lines)
- Broken state on Ctrl-C mid-flow (lock files left behind, partial writes)
- Fake progress bars on instant operations (50ms task showing animated bar)
- Unexpected behaviour when stdin is closed, redirected, or piped
- Inconsistent error formatting across subcommands

##### Casey (Distracted / Slow Connection User)

Profile: translates from "distracted mobile user" to "user on slow SSH connection". Frequently interrupted, low patience, possibly on high-latency link.

TUI red flags:

- Heavy first-render that lags noticeably on slow SSH (large initial screen redraw, full-screen TUI before showing partial output)
- No streaming output (waits to buffer entire result before printing)
- Blocking on remote operations with no progress text
- Animation frame rate too high for the connection (Textual 60fps over SSH stutters)
- No `--no-animation` or `--simple` flag

Be specific. Name the exact elements and interactions that fail each persona. Don't write generic persona descriptions; write what broke for them.

### Minor Observations

Quick notes on smaller issues worth addressing.

### Questions to Consider

Provocative questions that might unlock better solutions:

- "What if the primary action were more prominent in the help output?"
- "Does this need this many subcommands?"
- "What would a confident version of this CLI's voice look like?"

Remember:

- Be direct. Vague feedback wastes everyone's time.
- Be specific. "The status column in `tool list`," not "some elements."
- Say what's wrong AND why it matters to users.
- Give concrete suggestions. Cut "consider exploring..." entirely.
- Prioritize ruthlessly. If everything is important, nothing is.
- Don't soften criticism. Developers need honest feedback to ship great design.

## User-Driven Scope Selection

After presenting findings, use targeted questions based on what was actually found. STOP and call the AskUserQuestion tool to clarify. These answers will shape the action plan.

Ask questions along these lines (adapt to the specific findings; do NOT ask generic questions):

1. Priority direction: based on the issues found, ask which category matters most right now. For example: "I found problems with status visibility, error wording, and width handling. Which area should we tackle first?" Offer the top 2–3 issue categories as options.

2. Design intent: if the critique found a tonal mismatch, ask whether it was intentional. For example: "The CLI feels brutalist and terse. Is that the intended voice, or should it feel warmer / more guided?" Offer 2–3 tonal directions as options based on what would fix the issues found.

3. Scope: ask how much the user wants to take on. For example: "I found N issues. Want to address everything, or focus on the top 3?" Offer scope options: "Top 3 only", "All issues", "Critical only".

4. Constraints (optional; only ask if relevant): if findings touch many areas, ask if anything is off-limits. For example: "Should any subcommands stay as-is?" This prevents the plan from touching things the user considers done.

Rules for questions:

- Every question must reference specific findings from the report. Never ask generic "who is your audience?" questions.
- Keep it to 2–4 questions maximum. Respect the user's time.
- Offer concrete options, not open-ended prompts.
- If findings are straightforward (e.g., only 1–2 clear issues), skip questions and go directly to Recommended Actions.

## Recommended Actions

After receiving the user's answers, present a prioritized action summary reflecting the user's priorities and scope.

Order by user's stated priorities first, then by impact. Each item maps a Priority Issue to a checklist or reference file in this skill:

- Anti-pattern issues → re-read `./anti-references.md` and `./ai-slop-test.md`, revise the offending surface
- Colour / theme issues → re-read `./colour-strategy.md` and `./theme-decision.md`, pick the correct level
- Register mismatch → re-read `./register-decision.md`, confirm brand-cli vs product-cli
- Width / layout issues → re-read `./shape-brief-template.md` Section 5 (Layout Strategy), revise width tier
- Accessibility issues → run the audit checklist (`./audit-checklist.md`) Inclusion & Accessibility dimension
- Polish-level issues → run the polish checklist (`./polish-checklist.md`) at end of fix pass

Skip items that would address zero issues. If the user chose a limited scope, only include items within that scope. If the user marked areas as off-limits, exclude items that would touch those areas.

## Re-run Loop

Re-run `/impeccable critique` after fixes to see your score improve.
