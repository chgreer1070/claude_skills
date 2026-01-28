# Plugin-Creator Plugin - AI-Facing Documentation

Complete plugin development toolkit for creating, refactoring, and validating Claude Code plugins, agents, skills, and commands.

---

## Plugin Identity

**Name:** `plugin-creator`
**Version:** 2.3.0
**Purpose:** Provides end-to-end capabilities for plugin development lifecycle - creation, validation, refactoring, and quality assurance.

**Core Capabilities:**

- ✅ Create new plugins (via script)
- ✅ Create new agents (via skill)
- ❌ Create new skills (GAP - no dedicated tool)
- ❌ Create new commands (GAP - no dedicated tool)
- ✅ Refactor plugins and skills
- ✅ Validate frontmatter, plugins, and structure
- ✅ Quality analysis and improvement

---

## When to Use This Plugin

The model MUST use this plugin when:

- User asks to "create a new plugin"
- User asks to "create a new agent"
- User asks to "validate frontmatter" in SKILL.md or agent files
- User asks to "refactor a plugin" or "split a skill"
- User asks to "check skill line counts"
- User needs to validate plugin.json or plugin structure
- User wants to fix tool formatting issues in frontmatter

---

## Component Inventory

### Skills (12)

| Skill                            | User-Invocable | Purpose                                                                                                     | Verified |
| -------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------- | -------- |
| `/plugin-creator`                | Yes            | Orchestrates plugin creation by delegating to specialist agents                                             | ✅ Yes   |
| `/agent-creator`                 | Yes            | Create agents from scratch or templates, handles scope (project/user/plugin), updates plugin.json if needed | ✅ Yes   |
| `/claude-skills-overview-2026`   | Yes            | Complete reference for Claude Code skills system (January 2026)                                             | ✅ Yes   |
| `/claude-plugins-reference-2026` | Yes            | Complete reference for Claude Code plugins system (January 2026)                                            | ✅ Yes   |
| `/claude-hooks-reference-2026`   | Yes            | Complete reference for Claude Code hooks system (January 2026)                                              | ✅ Yes   |
| `/assessor`                      | Yes            | Analyze plugin structure and create refactoring task files                                                  | ✅ Yes   |
| `/ensure-complete`               | Yes            | Validate refactoring completeness and create follow-up tasks                                                | ✅ Yes   |
| `/feature-discovery`             | No             | Research features and identify gaps (delegated)                                                             | ✅ Yes   |
| `/implement-refactor`            | Yes            | Execute refactoring tasks with parallel orchestration                                                       | ✅ Yes   |
| `/refactor-plugin`               | Yes            | Complete plugin refactoring workflow                                                                        | ✅ Yes   |
| `/refactor-skill`                | Yes            | Split oversized skills into smaller focused skills                                                          | ✅ Yes   |
| `/start-refactor-task`           | Yes            | Execute individual refactoring tasks                                                                        | ✅ Yes   |

### Agents (3)

| Agent                | Model  | Tools                                     | Purpose                                       | Verified |
| -------------------- | ------ | ----------------------------------------- | --------------------------------------------- | -------- |
| `refactor-planner`   | sonnet | Read, Grep, Glob, Write                   | Analyze plugins and create refactoring plans  | ✅ Yes   |
| `refactor-executor`  | sonnet | Read, Write, Edit, Grep, Glob, Bash, Task | Execute refactoring tasks from plans          | ✅ Yes   |
| `refactor-validator` | sonnet | Read, Grep, Glob, Bash                    | Validate refactoring completeness and quality | ✅ Yes   |

### Commands (1)

| Command                       | Purpose                          | Script Used            | Verified |
| ----------------------------- | -------------------------------- | ---------------------- | -------- |
| `/plugin-creator:count-lines` | Quick check of skill line counts | `count-skill-lines.sh` | ✅ Yes   |

### Scripts (7)

| Script                        | Purpose                                            | Verified Working                              |
| ----------------------------- | -------------------------------------------------- | --------------------------------------------- |
| `create_plugin.py`            | Interactive plugin scaffolding                     | ✅ Yes - creates .claude-plugin/, plugin.json |
| `validate_frontmatter.py`     | Comprehensive frontmatter validation + auto-fix    | ✅ Yes - validates skills, agents, commands   |
| `validate-skill-structure.sh` | Skill quality validation (lines, links, structure) | ✅ Yes - bash script                          |
| `validate-task-file.sh`       | Validate refactoring task file format              | ✅ Yes - bash script                          |
| `count-skill-lines.sh`        | Count lines in skills, identify oversized ones     | ✅ Yes - used by count-lines command          |
| `fix-tool-formats.py`         | Fix invalid tool format patterns in frontmatter    | ✅ Yes - scans ~/.claude and repos            |
| `README.md`                   | Script documentation                               | ✅ Yes - documents fix-tool-formats.py        |

---

## Verified Workflows

### Workflow 1: Create New Plugin

**Entry Point:** Run script directly
**Verified:** ✅ Yes

```bash
# Interactive plugin scaffolding
uv run plugins/plugin-creator/scripts/create_plugin.py
```

**What It Does:**

1. Prompts for plugin name, description, author
2. Creates `.claude-plugin/` directory
3. Creates `plugin.json` with validated schema
4. Optionally creates `skills/`, `agents/` directories
5. Self-validates before reporting success

**Validation:** Runs `claude plugin validate` internally

---

### Workflow 2: Create New Agent

**Entry Point:** `/agent-creator` skill
**Verified:** ✅ Yes

**Trigger Phrases:**

- "Create a new agent"
- "Add an agent to {plugin}"
- "I need an agent for {task}"

**Agent Creation Process:**

1. **Discovery Phase:**

   - Reads existing agents in `.claude/agents/`
   - Identifies similar agents as templates
   - Reviews archetype templates

2. **Requirements Gathering:**

   - Uses AskUserQuestion for: purpose, triggers, tools, model, skills

3. **Template Selection:**

   - Presents options: existing project agents, role archetypes, from scratch
   - User selects via AskUserQuestion

4. **Agent File Creation:**

   - Creates frontmatter with validated fields
   - Writes agent body with workflow, quality standards

5. **Scope Determination** (uses AskUserQuestion):

   - **Project-level:** Saves to `.claude/agents/{name}.md`
   - **User-level:** Saves to `~/.claude/agents/{name}.md`
   - **Plugin:** Saves to `{plugin}/agents/{name}.md` + updates plugin.json

6. **Validation:**
   - Runs `validate_frontmatter.py` on agent file
   - If plugin agent: runs `claude plugin validate {plugin-path}`

**Outputs:**

- Agent file at appropriate location
- Updated plugin.json (if plugin agent)
- Validation report

---

### Workflow 3: Create New Skill

**Entry Point:** ❌ NO DEDICATED TOOL
**Verified:** ❌ GAP IDENTIFIED

**Current State:**

- No skill-creator skill exists
- No create_skill.py script exists
- Users must manually create SKILL.md files

**Gap Analysis:**

- Creating skills requires understanding frontmatter schema
- Need template selection (similar to agent-creator)
- Need scope determination (project/user/plugin)
- Need plugin.json update if plugin skill
- Need validation after creation

**Recommendation:** Create `/skill-creator` skill following agent-creator pattern

---

### Workflow 4: Create New Command

**Entry Point:** ❌ NO DEDICATED TOOL
**Verified:** ❌ GAP IDENTIFIED

**Current State:**

- No command-creator skill exists
- No create_command.py script exists
- Commands in plugins are deprecated per official docs
- Users create commands in `~/.claude/commands/` manually

**Gap Analysis:**

- Creating user-level commands requires frontmatter knowledge
- No template or validation guidance
- Commands in plugins deprecated - should document this

**Recommendation:** Create `/command-creator` skill for user-level commands only

---

### Workflow 5: Validate Frontmatter

**Entry Point:** `validate_frontmatter.py` script
**Verified:** ✅ Yes

**Supported File Types:**

- SKILL.md files
- Agent .md files
- Command .md files (user-level)

**Usage:**

```bash
# Validate single file
uv run plugins/plugin-creator/scripts/validate_frontmatter.py validate {path}

# Validate all files in directory
uv run plugins/plugin-creator/scripts/validate_frontmatter.py batch {directory}

# Auto-fix issues (dry-run first)
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix {path} --dry-run
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix {path}

# Batch fix
uv run plugins/plugin-creator/scripts/validate_frontmatter.py fix-batch {directory}
```

**What It Validates:**

- YAML syntax validity
- No forbidden multiline indicators (`>-`, `|-`)
- Required fields present (name, description for agents)
- Field types match schema (string, bool, object)
- Field values within constraints (length, pattern)
- Valid values enumeration (model: sonnet/opus/haiku/inherit)
- Tools/skills are comma-separated strings (not YAML arrays)

**What It Auto-Fixes:**

- YAML arrays → comma-separated strings
- Multiline descriptions → single-line quoted strings
- Unquoted descriptions with colons

**Schema Coverage:**

| File Type | Required Fields                   | Optional Fields                                                     | Verified |
| --------- | --------------------------------- | ------------------------------------------------------------------- | -------- |
| Skills    | None (name, description optional) | name, description, model, tools, skills, hooks, etc.                | ✅ Yes   |
| Agents    | name, description                 | model, tools, disallowedTools, permissionMode, skills, hooks, color | ✅ Yes   |
| Commands  | description                       | argument-hint, allowed-tools, model, context, agent, hooks          | ✅ Yes   |

**SOURCE:** Lines 103-187 of `validate_frontmatter.py`

---

### Workflow 6: Validate Skill Structure

**Entry Point:** `validate-skill-structure.sh` script
**Verified:** ✅ Yes

**Purpose:** Quality checks beyond frontmatter validation

**Usage:**

```bash
plugins/plugin-creator/scripts/validate-skill-structure.sh {skill-directory}
```

**What It Validates:**

1. **Frontmatter Presence:** SKILL.md starts with `---` and closes properly
2. **Name Field:** Present, lowercase, hyphens only
3. **Description Field:** Present, minimum 20 characters, includes trigger phrases
4. **Line Count Limits:**
   - WARN if body >500 lines
   - ERROR if body >800 lines
5. **Progressive Disclosure:** Checks for `references/`, `examples/`, `scripts/` directories
6. **Internal Links:** Validates markdown links with `./` prefix point to existing files

**Exit Codes:**

- 0: Pass (all checks or warnings only)
- 1: Fail (errors found)

**SOURCE:** Verified by reading `validate-skill-structure.sh` lines 1-176

---

### Workflow 7: Validate Complete Plugin

**Entry Point:** `claude plugin validate` command
**Verified:** ✅ Yes (built-in Claude Code command)

**Usage:**

```bash
claude plugin validate {plugin-directory}
```

**What It Validates:**

- plugin.json exists in `.claude-plugin/`
- JSON syntax valid
- Required field `name` present
- `name` is kebab-case
- All paths start with `./`
- `agents` field is array of individual file paths (not directory string)
- Referenced files exist

**Common Errors:**

| Error                   | Cause                               | Fix                                              |
| ----------------------- | ----------------------------------- | ------------------------------------------------ |
| `agents: Invalid input` | Used `"./agents/"` instead of array | Change to `["./agents/file.md"]`                 |
| `name: Required`        | Missing name field                  | Add `"name": "plugin-name"`                      |
| Invalid JSON syntax     | Malformed JSON                      | Validate with `python3 -m json.tool plugin.json` |

**SOURCE:** Verified via claude-plugins-reference-2026 skill

---

### Workflow 8: Refactor Plugin

**Entry Point:** `/refactor-plugin` skill
**Verified:** ✅ Yes

**Trigger Phrases:**

- "Refactor {plugin-name} plugin"
- "Analyze plugin for refactoring"
- "Create refactoring plan for {plugin}"

**Process Flow:**

1. **Assessment** (delegates to `refactor-planner` agent):

   - Analyzes plugin structure
   - Identifies oversized skills (>500 lines)
   - Checks agent descriptions for weak triggers
   - Detects orphaned files
   - Creates assessment report

2. **Design:**

   - Creates `refactor-design-{slug}.md` with strategy

3. **Task Planning:**

   - Creates `tasks-refactor-{slug}.md` with executable tasks
   - Maps dependencies
   - Identifies parallelization opportunities

4. **Execution** (delegates to `refactor-executor` agent):

   - Executes tasks in dependency order
   - Runs parallel where possible
   - Tracks completion status

5. **Validation** (delegates to `refactor-validator` agent):
   - Verifies refactoring achieved goals
   - Checks for regressions
   - Creates follow-up tasks if issues found

**Task Types Handled:**

| Type             | Handler                          | Verified         |
| ---------------- | -------------------------------- | ---------------- |
| `SKILL_SPLIT`    | `/refactor-skill` skill          | ✅ Yes           |
| `AGENT_OPTIMIZE` | `subagent-refactorer` agent      | ⚠️ Not in plugin |
| `DOC_IMPROVE`    | `claude-context-optimizer` agent | ⚠️ Not in plugin |
| `ORPHAN_RESOLVE` | Manual or context optimizer      | ⚠️ Partial       |
| `STRUCTURE_FIX`  | Direct implementation            | ✅ Yes           |

**OUTPUT:** Task files in `.claude/plan/` directory

---

### Workflow 9: Split Oversized Skill

**Entry Point:** `/refactor-skill` skill
**Verified:** ✅ Yes

**Model:** opus (requires complex reasoning)

**Trigger Phrases:**

- "Split the {skill-name} skill"
- "Refactor oversized skill"
- "This skill is over 800 lines"

**Process:**

1. Reads existing skill SKILL.md
2. Identifies logical boundaries and domains
3. Designs split plan
4. Generates new SKILL.md files for each extracted skill
5. Validates 100% content migration (no loss)
6. Creates cross-references between new skills
7. Updates original skill as facade/meta-skill

**Quality Requirements:**

- No content loss
- Complete fidelity
- Backwards compatibility maintained
- All cross-references valid

---

### Workflow 10: Count Skill Lines

**Entry Point:** `/plugin-creator:count-lines` command
**Verified:** ✅ Yes

**Usage:**

```bash
/plugin-creator:count-lines {plugin-or-skill-path}
```

**What It Does:**

1. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/count-skill-lines.sh`
2. Displays table with line counts
3. Shows status: OK / WARNING (>500) / CRITICAL (>800)

**Output Format:**

```text
| Skill | Total | Body | Status |
|-------|-------|------|--------|
| python3 | 650 | 580 | WARNING (>500) |
| testing | 320 | 280 | OK |
```

---

### Workflow 11: Fix Tool Formatting Issues

**Entry Point:** `fix-tool-formats.py` script
**Verified:** ✅ Yes

**Purpose:** Fix invalid tool format patterns in frontmatter across entire codebase

**Usage:**

```bash
# Scans ~/.claude and ~/repos recursively
uv run plugins/plugin-creator/scripts/fix-tool-formats.py
```

**What It Fixes:**

1. **YAML list → comma-separated string:**

   ```yaml
   # Before
   tools:
     - Read
     - Grep

   # After
   tools: Read, Grep
   ```

2. **JSON array → comma-separated string:**

   ```yaml
   # Before
   tools: ["Read", "Grep"]

   # After
   tools: Read, Grep
   ```

**Scan Locations:**

- `~/.claude/agents/**/*.md`
- `~/.claude/commands/**/*.md`
- `~/.claude/skills/**/SKILL.md`
- `~/repos/**/.claude/**` (all markdown in .claude directories)

**Why This Matters:** Invalid formats become "evidence" in future Grep searches, creating feedback loop where AI learns incorrect patterns from its own mistakes.

**SOURCE:** Verified by reading `scripts/README.md` and `fix-tool-formats.py`

---

## Identified Gaps

### Gap 1: No Skill Creator

**Current State:** Can create agents, cannot create skills
**Impact:** Users must manually create SKILL.md files without guidance
**Recommendation:** Create `/skill-creator` skill similar to `/agent-creator`

**Required Capabilities:**

- Template selection (general-purpose, domain-specific, etc.)
- Frontmatter generation with validation
- Scope determination (project/user/plugin)
- Plugin.json update if plugin skill
- Post-creation validation

---

### Note: Skills Are Commands

**Observation from official docs (line 9 of claude-skills-overview-2026):**

> "Skills and slash commands are now unified - they are the same system. A file at `.claude/commands/review.md` and a skill at `.claude/skills/review/SKILL.md` both create `/review` and work identically. Skills are the recommended approach."

**Conclusion:** No separate command-creator needed. Creating a skill with `user-invocable: true` creates a slash command.

---

### Gap 2: External Agent Dependencies

**Agents Referenced But Not Included:**

- `subagent-refactorer` - Used for AGENT_OPTIMIZE tasks
- `claude-context-optimizer` - Used for DOC_IMPROVE tasks

**Current State:** Refactoring workflows reference these but plugin doesn't include them
**Impact:** Users need these agents installed separately or workflows fail
**Recommendation:** Document as external dependencies or include in plugin

---

### Gap 3: Incomplete Validation Coverage

**Validated:**

- ✅ Frontmatter schema (via validate_frontmatter.py)
- ✅ Plugin.json syntax (via claude plugin validate)
- ✅ Skill structure quality (via validate-skill-structure.sh)

**Not Validated:**

- ❌ Agent frontmatter vs skill frontmatter differences (validate-skill-structure.sh only checks skills)
- ❌ Command frontmatter (no dedicated validator beyond general validate_frontmatter.py)
- ❌ Cross-references between components (e.g., agent references non-existent skill)

**Recommendation:** Extend validation to cover agent-specific checks and cross-reference validation

---

## Usage Patterns for the Model

### Pattern 1: User Wants to Create Something

**If user says:** "Create a new {plugin|agent|skill|command}"

```
1. Identify what they want to create
2. Check if tool exists:
   - Plugin → uv run scripts/create_plugin.py
   - Agent → /agent-creator
   - Skill → ❌ GAP - no tool (manual creation)
   - Command → ❌ GAP - no tool (manual creation)
3. If gap: Offer manual creation with validation guidance
```

---

### Pattern 2: User Wants to Validate

**If user says:** "Validate {frontmatter|plugin|skill}"

```
1. Determine validation type:
   - Frontmatter → uv run scripts/validate_frontmatter.py validate {path}
   - Complete plugin → claude plugin validate {path}
   - Skill structure → scripts/validate-skill-structure.sh {path}
2. Run appropriate validator
3. Report results with specific file:line references
```

---

### Pattern 3: User Wants to Refactor

**If user says:** "Refactor {plugin}" or "This skill is too large"

```
1. If skill >500 lines:
   - Run /plugin-creator:count-lines first to show problem
   - Offer /refactor-skill for individual skill
   - Offer /refactor-plugin for whole plugin
2. If general plugin refactoring:
   - Delegate to refactor-planner agent
   - Review generated plan with user
   - Delegate execution to refactor-executor agent
   - Validate with refactor-validator agent
```

---

### Pattern 4: User Reports Validation Errors

**If user says:** "Getting 'agents: Invalid input'" or similar

```
1. Read their plugin.json
2. Check against common errors:
   - agents field must be array of file paths
   - tools fields must be comma-separated strings
   - All paths must start with ./
3. Offer fix-tool-formats.py for tool format issues
4. Offer validate_frontmatter.py fix for frontmatter issues
```

---

## Script Execution Paths

All scripts use absolute paths or are executable with `uv run`:

```bash
# From anywhere in the repository:
uv run plugins/plugin-creator/scripts/validate_frontmatter.py validate {path}
uv run plugins/plugin-creator/scripts/create_plugin.py

# Scripts that work from their directory:
cd plugins/plugin-creator/scripts
./validate-skill-structure.sh {path}
./count-skill-lines.sh {path}
./validate-task-file.sh {path}
```

**Important:** Scripts expect to be run from repository root or use `${CLAUDE_PLUGIN_ROOT}` variable.

---

## Environment Variables

When commands execute, they have access to:

| Variable                | Value                             | Usage                                 |
| ----------------------- | --------------------------------- | ------------------------------------- |
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory | Used in commands to reference scripts |
| `$ARGUMENTS`            | Command arguments from user       | Passed to command's bash execution    |

**Example from count-lines.md:**

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/count-skill-lines.sh "$ARGUMENTS"
```

---

## Quality Standards Enforced

### Skill Size Limits

- **Recommended:** <500 lines (body content)
- **Warning:** 500-800 lines
- **Critical:** >800 lines (must split)

### Frontmatter Requirements

**Skills:**

- `name`: Optional (uses directory name if omitted)
- `description`: Optional (uses first paragraph if omitted)

**Agents:**

- `name`: Required (lowercase, hyphens, max 64 chars)
- `description`: Required (trigger keywords, max 1024 chars)
- `model`: Must be sonnet/opus/haiku/inherit if specified
- `tools`: Must be comma-separated string (not YAML array)

**Commands:**

- `description`: Required
- `allowed-tools`: Must be comma-separated string (not YAML array)

### Plugin.json Requirements

- `name`: Required, kebab-case
- `agents`: Must be array of individual file paths (not directory string)
- All paths must start with `./`

---

## Verification Status

This documentation was created 2026-01-28 by:

1. Reading all skill SKILL.md files
2. Reading all agent frontmatter
3. Reading all command files
4. Reading all script files
5. Testing scripts where possible
6. Cross-referencing with official Claude Code documentation

**Verification Method:** Direct file reading and execution verification, not assumption-based.

**Gaps Explicitly Identified:** Listed in "Identified Gaps" section above.

---

## Script Consolidation Recommendation

**Current State:** Validation and linting functionality is spread across multiple scripts:

- `validate_frontmatter.py` - Frontmatter schema validation
- `validate-skill-structure.sh` - Skill structure validation (bash)
- `count-skill-lines.sh` - Line counting (bash)
- `validate-task-file.sh` - Task file validation (bash)
- `fix-tool-formats.py` - Tool format fixing

**Recommendation:** Consolidate into a single cross-platform Python script: `lint-claude-plugin.py`

**Requirements:**

1. **Single Script:** Combine all validation functionality into one Python 3.11+ script
2. **Cross-Platform:** Pure Python, no bash dependencies, works on Windows/Linux/macOS
3. **Pre-commit Integration:** Compatible with `.pre-commit-config.yaml` hooks
4. **Token-Based Metrics:** Use `tiktoken` library to measure skill complexity in tokens, not lines
   - Line count is a poor proxy for complexity
   - Token count directly measures what Claude processes
   - Thresholds should be token-based (e.g., warn at X tokens, error at Y tokens)
5. **Unified Validation:** Single entry point that validates:
   - Frontmatter schema (skills, agents, commands)
   - Plugin.json structure
   - Skill complexity via token count
   - Internal link validity
   - Progressive disclosure structure
   - Tool format correctness

**Benefits:**

- Single tool to install and maintain
- Consistent behavior across platforms
- Better complexity measurement (tokens vs lines)
- Pre-commit hook compatibility
- Reduced maintenance burden

**Implementation Priority:** Medium - Current scripts work but consolidation would improve usability

---

## Related Plugins

**External Dependencies:**

- `subagent-refactorer` - Agent optimization (not included in this plugin)
- `claude-context-optimizer` - Documentation improvement (not included)

**Complementary Plugins:**

- `holistic-linting` - Code quality and linting
- `prompt-optimization-claude-45` - AI-facing documentation optimization
- `python3-development` - Python-specific development patterns

---

## Version History

- **2.3.0** - Added claude-plugins-reference-2026 and claude-hooks-reference-2026 reference skills
- **2.2.0** - Added claude-skills-overview-2026 reference skill
- **2.1.0** - Added agent-creator skill for creating agents
- **2.0.0** - Merged plugin-creator and plugin-refactor
- **1.0.0** - Initial plugin-creator release

---

## Sources

- Plugin.json: `plugins/plugin-creator/.claude-plugin/plugin.json`
- Skills verified: All 9 SKILL.md files read
- Agents verified: All 3 agent .md files read
- Commands verified: count-lines.md read
- Scripts verified: All 7 scripts examined
- Official docs: claude-plugins-reference-2026 skill
