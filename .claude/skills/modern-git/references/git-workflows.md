# Modern Git Workflows & Best Practices Reference


## 1. The Fall of `git checkout`

`git checkout` overloaded two unrelated operations — branch switching and file restoration. File restoration (`git checkout -- file`) is **highly destructive**: a typo could wipe uncommitted work with no recovery path.

Git 2.23 (2019) introduced two focused replacements. `checkout` is not removed (backward compatibility) but is **strongly discouraged for daily use**.

### `git switch` — Branch Management Only

`switch` never overwrites modified files.

- `git switch main` — switch to an existing branch
- `git switch -c feature-branch` — create and switch (replaces `checkout -b`)
- `git switch -` — switch to the previously checked-out branch
- `git switch -c topic/fix upstream/main` — create branch tracking a remote

### `git restore` — File State Management Only

- `git restore <file>` — discard uncommitted working-directory changes
- `git restore --staged <file>` — unstage without losing modifications
- `git restore --source=HEAD~1 <file>` — restore file to a previous commit's state

---

## 2. Official Git Workflow Guidelines

SOURCE: `git help workflows`, `git help everyday`

### A. Separate Changes (Small, Logical Commits)

- Use `git add -p` (patch mode) to stage specific chunks — not whole files
- Make imperfect commits locally; clean up with `git rebase -i` before pushing
- Easier to squash commits later than to split one large commit

### B. Topic Branches

- Never commit directly to integration branches (`main`, `master`, `maint`)
- Create a topic branch for every feature or bugfix
- Fork from the oldest integration branch you'll eventually merge into

### C. Throw-Away Integration Branches

To test how multiple feature branches interact without contaminating `main`:

1. `git switch -c testing-integration main`
2. `git merge feature-A feature-B`
3. Test
4. Delete the branch — **never base new work on a throw-away branch**

### D. The "Merge Upwards" Rule

Commit fixes to the oldest branch that needs them. Periodically merge older branches upward (e.g., `maint` → `main`). Prevents regressions and ensures fixes flow into future releases.

---

## 3. Advanced Modern Git

SOURCE: Scott Chacon, "So You Think You Know Git" (talks)

### Fixup Commits and Autosquash

Avoids manual rebasing of "fix typo" commits:

1. `git commit --fixup <commit-hash>` — tag a fix to a specific earlier commit
2. `git rebase -i --autosquash main` — Git pairs and squashes fixups automatically

### Git Worktrees

Check out multiple branches simultaneously in different directories — same `.git` repo, no stashing required:

- `git worktree add ../my-project-hotfix hotfix-branch`
- `git worktree list`
- `git worktree remove ../my-project-hotfix`

---

## 4. Native Git Alternatives to GitButler Features

### A. Virtual Branches → `git worktree`

Same as Section 3. Work on multiple branches concurrently without touching each other's working directories.

### B. Commit Editing → Fixup + Autosquash

Same as Section 3.

### C. Conflict Resolution Memory → `rerere`

Remembers how you resolved a conflict and re-applies it automatically next time:

```bash
git config --global rerere.enabled true
git config --global rerere.autoupdate true
```

---

## 5. Modern Git Configurations

Run once to permanently modernize Git behavior (Scott Chacon's recommendations):

```bash
# Sort branches by most recently modified
git config --global branch.sort -committerdate

# Display branch lists in columns
git config --global column.ui auto

# Auto-prune deleted remote-tracking branches
git config --global fetch.prune true

# git pull rebases instead of creating merge commits
git config --global pull.rebase true

# Reuse Recorded Resolution for merge conflicts
git config --global rerere.enabled true
git config --global rerere.autoupdate true
```

---

## 6. Advanced Commands

### Safer Force Pushing

Never use `--force`. It overwrites others' pushes made while you were rebasing.

```bash
git push --force-with-lease
```

Checks that the remote branch matches your local tracking branch before forcing. Rejects if someone else pushed changes you haven't fetched.

### Background Repository Optimization

```bash
git maintenance start
```

Sets up a cron job (hourly/daily/weekly) to run maintenance tasks (pack files, commit graphs) automatically.

### Advanced History Searching

- `git log -S "function_name"` — **Pickaxe**: find the exact commit that added or removed a string
- `git log -L 15,25:path/to/file.txt` — trace evolution of specific lines over time

---

## 7. Repository Cleanup, Maintenance & Plugins

### A. Identity Normalization

**Safe (`.mailmap`):** No history rewrite.

```text
Canonical Name <canonical@email.com> Old Name <old@email.com>
```

Place in repo root. Git applies in `log` and `blame` without changing hashes.

**Permanent (`git-filter-repo`):** Modern replacement for `filter-branch`.

```bash
git filter-repo --mailmap .mailmap
```

Requires force push after.

**Preventative (`includeIf`):** Auto-apply work email only inside work directories.

```ini
# ~/.gitconfig
[includeIf "gitdir:~/work/"]
    path = ~/work/.gitconfig-work
```

### B. Safely Cleaning Untracked Files

`git clean` deletes untracked files — use safe flags:

- `git clean -id` — interactive mode (prompts before deleting)
- `git clean -nd` — dry run (shows what would be deleted, doesn't act)

### C. Cleaning Up Stale Branches

```bash
# Remove local refs to deleted remote branches
git fetch --prune

# Delete all local branches already merged into current branch
git branch --merged | grep -v "\*" | xargs -n 1 git branch -d
```

`-d` (lowercase) is safe — Git refuses to delete branches with unmerged work. Never use `-D` for mass cleanup.

### D. Analyzing and Fixing Repository Bloat

**Native garbage collection (safe):**

```bash
git gc --prune=now
```

Compresses revisions into packfiles, removes unreachable orphaned objects.

**`git-sizer` (GitHub tool — analysis only, no modification):**

```bash
brew install git-sizer
git-sizer --verbose
```

Reports metrics: massive blobs, too many refs, other systemic problems.

**`git-filter-repo` (large file removal — rewrites history):**

```bash
git filter-repo --strip-blobs-bigger-than 50M
```

Use when `git-sizer` reveals accidentally committed large files.

### E. Stash Cleanup

```bash
git stash list                  # view full stash stack
git stash show -p stash@{2}     # inspect a specific stash
git stash drop stash@{2}        # delete a specific stash
git stash clear                 # delete all stashes
```

---

## 8. Cheat Sheet

### Branch Management

| Legacy Command | Modern Replacement | Purpose |
|---|---|---|
| `git checkout main` | `git switch main` | Switch to existing branch |
| `git checkout -b feat` | `git switch -c feat` | Create and switch |
| `git checkout -` | `git switch -` | Switch to previous branch |

### File & State Management

| Legacy Command | Modern Replacement | Purpose |
|---|---|---|
| `git checkout -- file` | `git restore file` | Discard working-dir changes |
| `git reset HEAD file` | `git restore --staged file` | Unstage without losing changes |

### Advanced Workflows

| Scenario | Command |
|---|---|
| Context switch without stashing | `git worktree add <path> <branch>` |
| Fix a specific older commit | `git commit --fixup <sha>` then `git rebase -i --autosquash` |
| Stage part of a file | `git add -p` |
| Test multiple features together | Throw-away integration branch |

---

## 9. Git Revisions & History Navigation

SOURCE: `git help revisions`

### Relative References

- `HEAD` — currently checked-out commit
- `@` — shortcut for `HEAD`
- `HEAD^` / `HEAD^1` — first parent of current commit
- `HEAD~3` — great-grandparent (equivalent to `HEAD^^^`)
- `@{-1}` — branch/commit before current one (`git switch @{-1}` = `git switch -`)

### Time-Based & Reflog References

- `master@{yesterday}` — state of local `master` branch yesterday
- `HEAD@{5.minutes.ago}` — where `HEAD` was 5 minutes ago
- `master@{1}` — previous value of `master` before its last change

### Range Notations

- `A..B` (two-dot) — commits reachable from `B` but not `A`. Example: `git log origin/main..HEAD` shows what you've done since branching.
- `A...B` (three-dot) — commits reachable from either but **not both** (symmetric difference).

### Searching History

- `:/<text>` — commit whose message matches text. Example: `git show :/fix nasty bug`
- `HEAD^{/<text>}` — search for commit message starting from `HEAD`
- `git grep "hello" v2.5` — search string inside codebase exactly as it existed at `v2.5` tag

---

## 10. GitButler & the `but` CLI

GitButler provides a GUI and CLI for virtual branches and unlimited undo (Operations Log).

### Desktop App

- Download: <https://gitbutler.com/downloads>
- Source: <https://github.com/gitbutlerapp/gitbutler>

### `but` CLI Installation

CLI page: <https://gitbutler.com/cli>

**Install script (recommended — macOS / Linux):**

```bash
curl -fsSL https://gitbutler.com/install.sh | sh
```

**Homebrew (macOS / Linux):**

```bash
brew install gitbutler
```

**Direct binary — user-local install (Linux x86_64, no sudo required):**

```bash
curl -LO https://releases.gitbutler.com/releases/release/0.19.5-2897/linux/x86_64/but
chmod +x but
mkdir -p ~/.local/bin
mv but ~/.local/bin/but
# Add to PATH if not already present (add to ~/.bashrc or ~/.zshrc):
# export PATH="$HOME/.local/bin:$PATH"
```

**Direct binary — system-wide install (Linux x86_64, requires sudo):**

```bash
curl -LO https://releases.gitbutler.com/releases/release/0.19.5-2897/linux/x86_64/but
chmod +x but
sudo mv but /usr/local/bin/but
```

**Via desktop app (installs `but` CLI for you):**

1. Download and install the GitButler desktop app from <https://gitbutler.com/downloads>
2. Open the app → go to **Settings**
3. Click **Install CLI** — this installs `but` to your system PATH automatically, no terminal steps required

### Basic `but` Commands

- `but status` — view uncommitted changes and virtual branch stacks
- `but branch` — manage virtual branches
- `but commit` — stage and commit in one step
- `but undo` — revert repository to a previous state via Operations Log

### GitButler + Claude Code Integration

SOURCE: <https://docs.gitbutler.com/features/coding-agents> (accessed 2026-03-06)

GitButler can orchestrate Claude Code agents attached to specific branches — including multiple agents running in parallel, each committing to their own branch.

**How it works:**

- Click the AI stars icon on a branch header (or use the new-branch + AI session shortcut) to start a session
- Each agent session is tied to a branch; changes are assigned to the correct branch automatically as long as they are mutually exclusive
- Branch context is injected into the agent's prompt automatically
- Multiple agents can run concurrently on separate branches

**Setup — Claude Code must be installed first:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then log in to Claude Code (requires an Anthropic account via API key or a Claude plan). GitButler does not charge for agent use — billing goes directly through Anthropic.

**In-app options:**

- **Model selection** — choose from active Anthropic models in the chat box dialog
- **Thinking mode** — lower modes are faster; higher modes are slower, more expensive, and produce better results
- **Prompt templates** — save reusable prompts; edit via a JSON file opened in your editor
- **Clear Context** — reset the branch session context without changing the branch
