---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
license: Complete terms in LICENSE.txt
user-invocable: true
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend Claude's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

**This skill is for creating NEW skills from scratch.** For refactoring EXISTING skills (splitting oversized skills, reorganizing multi-domain skills), use the skill-refactor skill:

```
Skill(command: "refactor-skill")
```

**When to use skill-creator vs skill-refactor:**

- **skill-creator:** Creating a new skill from requirements, examples, or user needs
- **skill-refactor:** Splitting an existing skill that's >500 lines or covers multiple domains
- Both skills can be used together: create with skill-creator, refactor later with skill-refactor as needs evolve

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else Claude needs: system prompt, conversation history, other Skills' metadata, and the actual user request.

**Default assumption: Claude is already very smart.** Only add context Claude doesn't already have. Challenge each piece of information: "Does Claude really need this explanation?" and "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

### Skill Tokenomics and Budget Constraints

Skills use progressive disclosure to manage context efficiently:

1. **Metadata (name + description)** - Always loaded into `<available_skills>` block (~100 words per skill)
2. **SKILL.md body** - Loaded only when skill activates (<5k words recommended)
3. **Bundled resources** - Loaded on demand by Claude (unlimited)

**Budget Constraints:**

| Resource                   | Limit         | Notes                                                            |
| -------------------------- | ------------- | ---------------------------------------------------------------- |
| `name` field               | 64 chars      | Lowercase, numbers, hyphens only                                 |
| `description` field        | 1024 chars    | Critical for skill selection                                     |
| `<available_skills>` block | ~15,000 chars | Separate from global context window, includes ALL skill metadata |
| Skills before truncation   | ~34-36        | Varies by description complexity and length                      |

**Truncation Behavior:**

When total skill metadata exceeds ~15,000 characters:

1. Skills are truncated from the `<available_skills>` block
2. Truncated skills cannot be auto-invoked by Claude
3. User can still invoke truncated skills explicitly with `/skill-name`
4. Run `/context` to check for a warning about excluded skills

To increase the limit, set the `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable.

**Fallback Strategy:**

If you have many skills, embed pointers in CLAUDE.md as a safeguard:

```markdown
## Skills Available
- For debugging: use `/scientific-thinking` skill
- For delegation: use `/delegate` skill
```

This ensures Claude can find skills even if truncated from `<available_skills>`.

**CRITICAL YAML BUG:**

Do NOT use YAML multiline indicators in descriptions:

```yaml
# WRONG - will show ">-" as description
description: >-
  This is a multiline description that breaks.

# WRONG - same problem
description: |-
  This breaks too.

# CORRECT - single quoted string
description: 'This works correctly. Use single quotes for descriptions with special characters or keep on one line.'
```

The Claude Code skill indexer does not parse YAML multiline indicators correctly - the description appears as ">-" instead of actual content.

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) section on Skill Tokenomics.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of Claude as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)

Every SKILL.md consists of:

- **Frontmatter** (YAML): Metadata fields like `name`, `description`, `argument-hint`, `allowed-tools`, `model`, `context`, `user-invocable`, `disable-model-invocation`, and `hooks`. The `description` field (or first paragraph if omitted) is what Claude reads to determine when the skill gets used, thus it is very important to be clear and comprehensive in describing what the skill is and when it should be used.
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by Claude for patching or environment-specific adjustments

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform Claude's process and thinking.

- **When to include**: For documentation that Claude should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when Claude determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output Claude produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables Claude to use files without loading them into context

#### What to Not Include in a Skill

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- etc.

The skill should only contain the information needed for an AI agent to do the job at hand. It should not contain auxilary context about the process that went into creating it, setup and testing procedures, user-facing documentation, etc. Creating additional documentation files just adds clutter and confusion.

### Advanced Skill Patterns

#### Context Fork (Isolated Execution)

Add `context: fork` to frontmatter when you want a skill to run in isolation without access to conversation history.

**When to use:**

- Skill has explicit, complete instructions that don't need conversation context
- Want to prevent conversation history from affecting skill behavior
- Need predictable, consistent execution independent of what user discussed earlier

**When NOT to use:**

- Skill contains only guidelines (e.g., "use these API conventions") without actionable task
- Need access to conversation context or previous discussion
- Need to delegate to other subagents (Task tool not available in forked contexts)

**Agent types:**

```yaml
context: fork
agent: Explore  # or Plan, general-purpose, custom-agent-name
```

| Agent             | Model    | Tools                      | Use Case                     |
| ----------------- | -------- | -------------------------- | ---------------------------- |
| `Explore`         | Haiku    | File/web/MCP (read-only)   | Fast codebase analysis       |
| `Plan`            | Inherits | File/web/MCP (read-only)   | Research before planning     |
| `general-purpose` | Inherits | File/web/MCP + Bash/system | Complex operations (default) |

**Tool restrictions:**

- Forked contexts have Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Bash, MCP tools
- **Task tool is NOT available** - cannot delegate to other subagents
- For hierarchical delegation, parent must run in main context (no `context: fork`)

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) section on Context Fork Behavior.

#### Invocation Control

Control who can invoke your skill:

1. **Default behavior:** Both user and Claude can invoke

   - User types `/skill-name`
   - Claude loads automatically when relevant
   - Description always in context, full skill loads on activation

2. **Manual-only (disable auto-invoke):**

   ```yaml
   disable-model-invocation: true
   ```

   - Only user can invoke with `/skill-name`
   - Claude cannot load it automatically
   - Description NOT in Claude's context
   - **Use for:** Workflows with side effects (`/deploy`, `/send-slack-message`)
   - **Why:** You control timing, Claude won't deploy just because code looks ready

3. **Background knowledge (hide from menu):**
   ```yaml
   user-invocable: false
   ```
   - Only Claude can invoke (automatically when relevant)
   - Not shown in `/` autocomplete menu
   - Description always in context, full skill loads when Claude activates it
   - **Use for:** Background knowledge that isn't actionable as command (`/legacy-system-context`)
   - **Why:** Claude should know this when relevant, but `/legacy-system-context` isn't a meaningful user action

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) section on Invocation Control.

#### Hooks (Lifecycle Automation)

Skills can define hooks in frontmatter to respond to events during the skill's lifecycle:

**Events:**

- `PreToolUse` - Before tool executes
- `PostToolUse` - After successful execution
- `Stop` - When skill finishes

**Example:**

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"           # Regex pattern matching tool name
      hooks:
        - type: command
          command: "./scripts/check.sh"
          once: true            # Run only once per session
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "./scripts/lint.sh"
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup.sh"
```

**Hook I/O:**

- Receives JSON via stdin (session info, tool name, parameters)
- Exit 0: Success
- Exit 2: Blocking error (prevents tool, shows stderr)
- Other: Non-blocking error

**Complete documentation:** See [claude-hooks-reference-2026](../claude-hooks-reference-2026/SKILL.md) for all events, matchers, JSON output control, and examples.

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) section on Hooks in Skills.

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by Claude (Unlimited because scripts can be executed without reading into context window)

#### Progressive Disclosure Patterns

Keep SKILL.md body to the essentials and under 500 lines to minimize context bloat. Split content into separate files when approaching this limit. When splitting out content into other files, it is very important to reference them from SKILL.md and describe clearly when to read them, to ensure the reader of the skill knows they exist and when to use them.

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.

**Pattern 1: High-level guide with references**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

Claude loads FORMS.md, REFERENCE.md, or EXAMPLES.md only when needed.

**Pattern 2: Domain-specific organization**

For Skills with multiple domains, organize content by domain to avoid loading irrelevant context:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When a user asks about sales metrics, Claude only reads sales.md.

Similarly, for skills supporting multiple frameworks or variants, organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

When the user chooses AWS, Claude only reads aws.md.

**Pattern 3: Conditional details**

Show basic content, link to advanced content:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

Claude reads REDLINING.md or OOXML.md only when the user needs those features.

**Important guidelines:**

- **Avoid deeply nested references** - Keep references one level deep from SKILL.md. All reference files should link directly from SKILL.md.
- **Structure longer reference files** - For files longer than 100 lines, include a table of contents at the top so Claude can see the full scope when previewing.

## Skill Creation Process

Skill creation involves these steps:

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Determine skill location and distribution strategy
4. Initialize the skill (run init_skill.py or create directory manually)
5. Edit the skill (implement resources and write SKILL.md)
6. Package the skill (OPTIONAL - only if distributing via plugins)
7. Iterate based on real usage

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Step 3: Determine Skill Location and Distribution Strategy

Before creating a skill, decide where it will live. **If unclear, STOP and ask the user.**

| Location                      | Purpose             | Distribution           | Use When                                                     |
| ----------------------------- | ------------------- | ---------------------- | ------------------------------------------------------------ |
| **Plugin** (bundled)          | `plugins/*/skills/` | Via plugin marketplace | Creating reusable skills for public/team distribution        |
| **Project** (version control) | `.claude/skills/`   | Via git (team-shared)  | Project-specific skills shared with team via version control |
| **User** (personal)           | `~/.claude/skills/` | Manual (personal use)  | Personal skills used across all your projects                |

**Location priority when skills share same name:** managed/enterprise > user (~/.claude/skills/) > project (.claude/skills/). Plugin skills use `plugin-name:skill-name` namespace and don't conflict with other levels.

**CRITICAL:** Packaging (step 6) is ONLY needed for plugin distribution. If creating skills in `.claude/skills/` or `~/.claude/skills/`, they are already in their final location - skip the packaging step entirely.

**Automatic discovery:** Claude Code automatically discovers skills from nested `.claude/skills/` directories. For example, if editing `packages/frontend/`, Claude also looks in `packages/frontend/.claude/skills/`. This supports monorepo setups where packages have their own skills.

**When location is unclear:** STOP and ask: "Where should this skill be created? (1) Plugin for marketplace distribution, (2) Project-level (.claude/skills/) for team sharing via git, or (3) User-level (~/.claude/skills/) for personal use?"

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) section on Directory Structure and Location Priority.

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 4: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

**For plugin skills:**

When creating a new skill for plugin distribution, run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates example resource directories: `scripts/`, `references/`, and `assets/`
- Adds example files in each directory that can be customized or deleted

**For project/user skills:**

Create the skill directory manually:

```bash
# Project skill
mkdir -p .claude/skills/my-skill

# User skill
mkdir -p ~/.claude/skills/my-skill

# Create SKILL.md
touch .claude/skills/my-skill/SKILL.md
```

Create optional subdirectories as needed:

- `references/` for documentation loaded on demand
- `scripts/` for executable code
- `assets/` for templates and resources

After initialization, customize or remove the generated SKILL.md and example files as needed.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Include information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See references/workflows.md for sequential workflows and conditional logic
- **Specific output formats or quality standards**: See references/output-patterns.md for template and example patterns

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.

Any example files and directories not needed for the skill should be deleted. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter. All fields are optional, but `description` is strongly recommended:

- `name`: Optional. The skill name (defaults to directory name if omitted). Lowercase letters, numbers, and hyphens only. Max 64 characters.
- `description`: Optional but strongly recommended. This is the primary triggering mechanism for your skill, and helps Claude understand when to use the skill. If omitted, uses the first paragraph of markdown content.
  - Include both what the Skill does and specific triggers/contexts for when to use it.
  - Include all "when to use" information here - Not in the body. The body is only loaded after triggering, so "When to Use This Skill" sections in the body are not helpful to Claude.
  - Max 1024 characters.
  - **CRITICAL:** Do NOT use YAML multiline indicators (`>-`, `|-`, `|`) - they are broken and will display as ">-" instead of your text. Use single-line quoted strings instead.
  - Example description for a `docx` skill: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
- `argument-hint`: Optional. Hint shown during autocomplete to indicate expected arguments. Example: `[issue-number]` or `[filename] [format]`.
- `allowed-tools`: Optional. Tools Claude can use without asking permission when this skill is active (comma-separated). Example: `Read, Grep, Glob, Bash(npm run:*)`
- `model`: Optional. Model to use when this skill is active. Options: `claude-opus-4-5-20251101`, `claude-sonnet-4-20250514`, `opus`, `sonnet`, `haiku`
- `context`: Optional. Set to `fork` to run in a forked subagent context for isolation. See advanced patterns below.
- `agent`: Optional. Which subagent type to use when `context: fork` is set. Options: `Explore`, `Plan`, `general-purpose`, or custom agent name.
- `user-invocable`: Optional. Set to `false` to hide from the `/` menu. Use for background knowledge users shouldn't invoke directly. Default: `true`.
- `disable-model-invocation`: Optional. Set to `true` to prevent Claude from automatically loading this skill. Use for workflows you want to trigger manually with `/name`. Default: `false`.
- `hooks`: Optional. Hooks scoped to this skill's lifecycle. See hooks documentation for configuration format.

**Complete field reference:** See [claude-skills-overview-2026 skill](../claude-skills-overview-2026/SKILL.md) for definitive schema documentation.

##### Body

Write instructions for using the skill and its bundled resources.

**Advanced Body Features:**

1. **String Substitutions** - Skills support dynamic value replacement:

   - `$ARGUMENTS` - All arguments passed when invoking the skill
   - `$ARGUMENTS[N]` or `$N` - Specific argument by 0-based index (e.g., `$0`, `$1`)
   - `${CLAUDE_SESSION_ID}` - Current session ID for logging or session-specific files

   Example:

   ```markdown
   ---
   name: migrate-component
   description: Migrate a component from one framework to another
   ---

   Migrate the $0 component from $1 to $2.
   Preserve all existing behavior and tests.
   ```

   Running `/migrate-component SearchBar React Vue` replaces `$0` with `SearchBar`, `$1` with `React`, and `$2` with `Vue`.

2. **Dynamic Context Injection** - Preprocess shell commands before skill content reaches Claude:

   - Syntax: \`\!\`command\`\` runs immediately (before Claude sees anything)
   - Command output replaces the placeholder
   - Claude receives fully-rendered prompt with actual data
   - Use for fetching PR data, git status, API responses, etc.

   Example (summarize GitHub PR):

   ```markdown
   ---
   name: pr-summary
   description: Summarize GitHub pull request changes
   ---

   Pull Request Data:
   \`\!`gh pr view $0 --json title,body,commits`\`\`

   Create a summary of the changes above.
   ```

3. **Extended Thinking Mode** - Include the word "ultrathink" anywhere in skill content to enable extended thinking mode for complex reasoning tasks.

**SOURCE:** [claude-skills-overview-2026](../claude-skills-overview-2026/SKILL.md) sections on String Substitutions and Dynamic Context Injection.

### Step 6: Packaging a Skill (OPTIONAL - Plugin Distribution Only)

**IMPORTANT:** This step is ONLY required when distributing skills via plugins. Skip this step if:

- Creating skills in `.claude/skills/` (project-level, shared via git)
- Creating skills in `~/.claude/skills/` (user-level, personal use)
- Skills are already in their final location

**Only for plugin skills:**

Once development of the skill is complete and you plan to distribute it via a plugin, package it into a distributable .skill file. The packaging process automatically validates the skill first to ensure it meets all requirements:

```bash
scripts/package_skill.py <path/to/skill-folder>
```

Optional output directory specification:

```bash
scripts/package_skill.py <path/to/skill-folder> ./dist
```

The packaging script will:

1. **Validate** the skill automatically, checking:

   - YAML frontmatter format and fields
   - Skill naming conventions and directory structure
   - Description completeness and quality
   - File organization and resource references

2. **Package** the skill if validation passes, creating a .skill file named after the skill (e.g., `my-skill.skill`) that includes all files and maintains the proper directory structure for distribution. The .skill file is a zip file with a .skill extension.

If validation fails, the script will report the errors and exit without creating a package. Fix any validation errors and run the packaging command again.

**Alternative: Bundle in Plugin Directly**

Instead of creating standalone .skill files, you can include skills directly in a plugin's `skills/` directory and reference them in `plugin.json`. This is the recommended approach for plugin-bundled skills. See [claude-plugins-reference-2026](../claude-plugins-reference-2026/SKILL.md) for plugin creation documentation.

### Step 6: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again
