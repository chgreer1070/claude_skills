# Codebase Analysis: Cross-Reference Patterns in Backlog Ecosystem

## Current Link Conventions

The backlog ecosystem uses three distinct referencing patterns, each with a specific scope:

### 1. Relative markdown links with `./` prefix (SKILL.md to own references)

Skills link to their own reference files using `[text](./references/filename.md)`:

```text
# backlog-tools-administrator/SKILL.md
[./references/domain-registry.md](./references/domain-registry.md)
[domain registry](./references/domain-registry.md)

# work-backlog-item/SKILL.md
[sam-definition.md](./references/sam-definition.md)
[github-integration.md](./references/github-integration.md)
[validation-plan.md](./references/validation-plan.md)
```

### 2. Relative `../../` paths (SKILL.md to `.claude/docs/`)

When a SKILL.md needs to reference a docs file, the path traverses up two levels:

```text
# work-backlog-item/SKILL.md (at .claude/skills/work-backlog-item/SKILL.md)
[.claude/docs/sdlc-layers/](../../docs/sdlc-layers/)
[.claude/docs/sdlc-layers/arl-human-probing-design.md](../../docs/sdlc-layers/arl-human-probing-design.md)

# groom-backlog-item/SKILL.md (at .claude/skills/groom-backlog-item/SKILL.md)
[.claude/docs/sdlc-layers/arl-human-probing-design.md](../../docs/sdlc-layers/arl-human-probing-design.md)
```

Pattern: From `.claude/skills/{name}/SKILL.md`, the path to `.claude/docs/` is `../../docs/`.

### 3. Skill activation syntax (inter-skill references)

Skills reference other skills by slash-command name rather than file path:

```text
# work-backlog-item/SKILL.md
Skill(skill: "groom-backlog-item", args: "{item title}")
Skill(skill: "create-backlog-item", args: "--auto {title}")
Skill(skill: "add-new-feature", args: "{composed feature request}")

# create-backlog-item/SKILL.md
/groom-backlog-item {title}
/work-backlog-item {title}

# backlog/SKILL.md
"create-backlog-item — invokes backlog add"
"work-backlog-item — invokes backlog list, backlog close..."
```

### 4. Inline backtick paths (non-link references)

Several files reference paths in backticks without markdown link syntax. These are informational rather than navigable:

```text
# backlog/SKILL.md
`.claude/backlog/` per-item files
`uv run .claude/skills/backlog/scripts/backlog.py`

# groom-backlog-item/SKILL.md
`.claude/docs/backlog-item-groomed-schema.md` (inside agent prompt strings)
`.claude/backlog/{priority}-{slug}.md`
```

### 5. Within-references cross-links (`./` relative to current dir)

Reference files link to sibling reference files using `./`:

```text
# backlog/references/state-machine.md
[./item-schema.md](./item-schema.md)

# work-backlog-item/references/example-sessions.md
[github-integration.md](./github-integration.md)
```

### 6. Broken/non-standard path (observed)

One reference uses a repo-root-relative path without `./` or `../../`:

```text
# work-backlog-item/references/github-integration.md:198
[issue-stories.md](.claude/skills/gh/references/issue-stories.md)
```

This is incorrect. From `.claude/skills/work-backlog-item/references/`, the path should be `../../gh/references/issue-stories.md`.

## Existing Cross-References

### Map of which backlog files link to which

```text
CLAUDE.md (Backlog Operations section)
  --> .claude/skills/backlog/scripts/backlog.py (backtick, inline)
  --> .claude/skills/backlog/SKILL.md (prose: "See .claude/skills/backlog/SKILL.md")
  --> /backlog-tools-administrator (skill activation syntax)
  --> /create-backlog-item (skill activation syntax)
  --> /work-backlog-item (skill activation syntax)

backlog/SKILL.md
  --> (no outgoing markdown links to other files)
  --> create-backlog-item, work-backlog-item (prose mentions, not links)

work-backlog-item/SKILL.md
  --> ./references/sam-definition.md
  --> ./references/github-integration.md (x3)
  --> ./references/validation-plan.md
  --> ../../docs/sdlc-layers/ (x2)
  --> ../../docs/sdlc-layers/arl-human-probing-design.md
  --> /groom-backlog-item (Skill invocation)
  --> /create-backlog-item (Skill invocation)
  --> /add-new-feature (Skill invocation)
  --> /implement-feature (prose)

groom-backlog-item/SKILL.md
  --> ../../docs/sdlc-layers/arl-human-probing-design.md
  --> .claude/docs/backlog-item-groomed-schema.md (backtick in prompt string)
  --> /fact-check (Skill invocation)
  --> backlog.py subcommands (backtick paths)

create-backlog-item/SKILL.md
  --> (no outgoing markdown links)
  --> /groom-backlog-item (prose)
  --> /work-backlog-item (prose)
  --> backlog.py add (backtick path)

backlog-tools-administrator/SKILL.md
  --> ./references/domain-registry.md (x4)
  --> /improve-processes (Skill invocation)
  --> backlog.py, tests paths (backtick paths in Step 3A)

backlog-tools-administrator/references/domain-registry.md
  --> .claude/docs/backlog-item-groomed-schema.md (backtick, plain text)
  --> .claude/docs/backlog-lifecycle.draft.md (backtick, plain text)
  --> All skill paths, agent paths, reference paths (plain text inventory)
  --> (no markdown links to any listed files — uses backtick paths only)

backlog/references/state-machine.md
  --> ./item-schema.md

work-backlog-item/references/example-sessions.md
  --> ./github-integration.md

work-backlog-item/references/github-integration.md
  --> .claude/skills/gh/references/issue-stories.md (BROKEN: wrong relative path)

project_workflow.draft.md
  --> (no markdown links — uses Mermaid node labels and prose)
  --> References all backlog skills by slash-command name
  --> References domain-registry.md path in prose

.claude/docs/backlog-lifecycle.draft.md
  --> (no outgoing markdown links at all)
  --> References skill/script paths in backtick notation only
```

### Adjacency summary

```text
                          backlog/    work-       groom-      create-     backlog-tools-  domain-     lifecycle.   CLAUDE.md
                          SKILL.md    backlog-    backlog-    backlog-    admin/          registry.md  draft.md
                                      item        item        item        SKILL.md
backlog/SKILL.md            --       mentions    (none)      mentions    (none)          (none)       (none)       (none)
work-backlog-item           (none)     --        Skill()     Skill()     (none)          (none)       (none)       (none)
groom-backlog-item          (none)    (none)       --        (none)      (none)          (none)       (none)       (none)
create-backlog-item         (none)    prose       prose        --        (none)          (none)       (none)       (none)
backlog-tools-admin         (none)    (none)      (none)      (none)       --            link(x4)     (none)       (none)
domain-registry.md          text      text        text        text       (none)            --         text         text
lifecycle.draft.md          text      text        text        text       (none)          (none)         --         (none)
CLAUDE.md                   text      prose       (none)      prose      prose           (none)       (none)         --
```

## Missing Cross-References

The following files should link to `backlog-lifecycle.md` (once promoted from draft) but currently do not:

1. **`backlog/SKILL.md`** -- No link to the lifecycle document. The SKILL.md describes subcommands but does not explain the lifecycle those subcommands implement. A link to the lifecycle doc would provide context.

2. **`work-backlog-item/SKILL.md`** -- No link to the lifecycle document. This skill implements the full lifecycle (create, groom, plan, close, resolve) but does not reference a lifecycle overview.

3. **`groom-backlog-item/SKILL.md`** -- No link to the lifecycle document. Grooming is a lifecycle phase but the skill does not reference the lifecycle context.

4. **`create-backlog-item/SKILL.md`** -- No link to the lifecycle document. Item creation is the first lifecycle phase.

5. **`backlog-tools-administrator/SKILL.md`** -- No link to the lifecycle document. The admin skill manages the ecosystem but does not reference the lifecycle overview.

6. **`backlog-tools-administrator/references/domain-registry.md`** -- Lists `backlog-lifecycle.draft.md` in plain text (backtick path) but does not use a markdown link. Should use `[backlog-lifecycle.md](../../../docs/backlog-lifecycle.md)` once promoted.

7. **`backlog/references/state-machine.md`** -- Describes state transitions that are a subset of the lifecycle. No link to the lifecycle doc for broader context.

8. **`CLAUDE.md` (Backlog Operations section)** -- Does not mention the lifecycle document at all.

9. **`project_workflow.draft.md`** -- Documents the backlog workflow visually but does not link to the lifecycle reference.

10. **`backlog-lifecycle.md` itself** -- Currently has zero outgoing markdown links. It references skill and script paths only in backtick notation. It should link back to each skill SKILL.md it describes.

## Path Convention for docs/ References

The target file will be `.claude/docs/backlog-lifecycle.md` (after promotion from `.draft.md`).

### From each location, the correct relative path is:

| Source file location | Relative path to `.claude/docs/backlog-lifecycle.md` |
|---|---|
| `.claude/skills/backlog/SKILL.md` | `[Backlog Lifecycle](../../docs/backlog-lifecycle.md)` |
| `.claude/skills/work-backlog-item/SKILL.md` | `[Backlog Lifecycle](../../docs/backlog-lifecycle.md)` |
| `.claude/skills/groom-backlog-item/SKILL.md` | `[Backlog Lifecycle](../../docs/backlog-lifecycle.md)` |
| `.claude/skills/create-backlog-item/SKILL.md` | `[Backlog Lifecycle](../../docs/backlog-lifecycle.md)` |
| `.claude/skills/backlog-tools-administrator/SKILL.md` | `[Backlog Lifecycle](../../docs/backlog-lifecycle.md)` |
| `.claude/skills/backlog-tools-administrator/references/domain-registry.md` | `[Backlog Lifecycle](../../../docs/backlog-lifecycle.md)` |
| `.claude/skills/backlog/references/state-machine.md` | `[Backlog Lifecycle](../../../docs/backlog-lifecycle.md)` |
| `.claude/skills/backlog/references/item-schema.md` | `[Backlog Lifecycle](../../../docs/backlog-lifecycle.md)` |
| `.claude/CLAUDE.md` | `[Backlog Lifecycle](./docs/backlog-lifecycle.md)` |
| `.claude/project_workflow.draft.md` | `[Backlog Lifecycle](./docs/backlog-lifecycle.md)` |
| `.claude/docs/backlog-lifecycle.md` (back-links) | See per-target paths below |

### From `backlog-lifecycle.md` back to each skill:

| Target | Relative path from `.claude/docs/backlog-lifecycle.md` |
|---|---|
| `backlog/SKILL.md` | `[backlog](../skills/backlog/SKILL.md)` |
| `work-backlog-item/SKILL.md` | `[work-backlog-item](../skills/work-backlog-item/SKILL.md)` |
| `groom-backlog-item/SKILL.md` | `[groom-backlog-item](../skills/groom-backlog-item/SKILL.md)` |
| `create-backlog-item/SKILL.md` | `[create-backlog-item](../skills/create-backlog-item/SKILL.md)` |
| `backlog-tools-administrator/SKILL.md` | `[backlog-tools-administrator](../skills/backlog-tools-administrator/SKILL.md)` |
| `backlog/references/state-machine.md` | `[state-machine](../skills/backlog/references/state-machine.md)` |
| `backlog/references/item-schema.md` | `[item-schema](../skills/backlog/references/item-schema.md)` |
| `backlog/scripts/backlog.py` | `[backlog.py](../skills/backlog/scripts/backlog.py)` |

## Recommendations

### 1. Follow the established `../../docs/` convention for SKILL.md files

All four backlog SKILL.md files sit at `.claude/skills/{name}/SKILL.md`. They already use `../../docs/sdlc-layers/` to reach `.claude/docs/`. Use the same pattern for backlog-lifecycle:

```markdown
[Backlog Lifecycle](../../docs/backlog-lifecycle.md)
```

### 2. Add a one-line "Lifecycle reference" near the top of each SKILL.md

Place it after the frontmatter block and first heading, before the workflow section. Observed pattern from other skills:

```markdown
# Work Backlog Item

Bridge a backlog item into the SAM planning pipeline...

**Lifecycle reference**: See [Backlog Lifecycle](../../docs/backlog-lifecycle.md) for the full item lifecycle, state transitions, and data architecture.
```

This mirrors the `**Workflow Reference**: See [...]` pattern used by `/scientific-thinking`, `/verify`, `/delegate`, and `/subagent-contract` SKILL.md files.

### 3. Add back-links from backlog-lifecycle.md to each skill

Convert the backtick paths currently in `backlog-lifecycle.draft.md` to proper markdown links. The file currently uses:

```text
`/create-backlog-item`
`.claude/skills/backlog/scripts/backlog.py`
```

These should become:

```markdown
[`/create-backlog-item`](../skills/create-backlog-item/SKILL.md)
[`backlog.py`](../skills/backlog/scripts/backlog.py)
```

### 4. Convert domain-registry.md entries to markdown links

The domain registry lists every file in backtick notation. Convert to markdown links so they are navigable:

```markdown
# Current (plain text):
- `.claude/skills/backlog/SKILL.md` — Script documentation

# Proposed (linked):
- [`.claude/skills/backlog/SKILL.md`](../../backlog/SKILL.md) — Script documentation
```

### 5. Fix the broken cross-reference in github-integration.md

`work-backlog-item/references/github-integration.md` line 198 has:

```markdown
[issue-stories.md](.claude/skills/gh/references/issue-stories.md)
```

This should be:

```markdown
[issue-stories.md](../../gh/references/issue-stories.md)
```

### 6. Add backlog-lifecycle.md to the CLAUDE.md Backlog Operations section

Add a single line linking to the lifecycle doc:

```markdown
**Lifecycle**: See [Backlog Lifecycle](./docs/backlog-lifecycle.md) for state transitions, data architecture, and the full item lifecycle.
```

### 7. Link conventions summary table

| From | To | Pattern |
|---|---|---|
| SKILL.md | own references/ | `[text](./references/file.md)` |
| SKILL.md | .claude/docs/ | `[text](../../docs/file.md)` |
| SKILL.md | another skill | Use `/skill-name` activation syntax |
| references/*.md | sibling reference | `[text](./file.md)` |
| references/*.md | .claude/docs/ | `[text](../../../docs/file.md)` |
| .claude/CLAUDE.md | .claude/docs/ | `[text](./docs/file.md)` |
| .claude/docs/*.md | .claude/skills/ | `[text](../skills/{name}/SKILL.md)` |
