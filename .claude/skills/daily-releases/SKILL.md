---
description: 'Create GitHub Releases and git tags for every calendar day with commits. Groups commits by UTC date, categorizes by conventional commit type (feat/fix/refactor/docs/test/ci/chore), and generates structured changelogs. Use to backfill daily releases for the entire repository history or maintain ongoing daily release artifacts.'
disable-model-invocation: true
argument-hint: '[options]'
---

# Daily Releases

Automatically create GitHub Releases with categorized changelogs for every calendar day the repository had commits.

## Quick Start

```bash
# Preview what would be created (no changes)
/daily-releases --dry-run

# Create all daily releases for entire history
/daily-releases

# Process specific date range
/daily-releases --start-date 2026-02-01 --end-date 2026-02-28

# Process one specific day
/daily-releases --start-date 2026-02-21 --end-date 2026-02-21
```

## How It Works

The script reads all commits on a branch, groups them by UTC date, and for each day intelligently handles releases:

1. **Groups commits** by conventional commit type:
   - `feat:` → Enhancements
   - `fix:` → Bug Fixes
   - `refactor:` → Technical Debt
   - `docs:` → Documentation
   - `test:` → Testing
   - `ci:`, `build:` → Build & CI
   - `chore:`, `style:`, `perf:` → Non-Functional

2. **Generates markdown changelog** with categorized changes

3. **Smart release handling**:
   - **New day** (no release exists): Creates `daily-YYYY-MM-DD` tag and GitHub Release
   - **New commits on existing day**: Renames old tag to `daily-YYYY-MM-DD-r2` (or `-r3`, etc.), creates new `daily-YYYY-MM-DD` tag, updates release with all commits
   - **Same commits, missing release notes**: Updates release body only (tag unchanged)

4. **Pushes tags and releases** to remote

## Options

```
--start-date TEXT       Only process days on or after this date (YYYY-MM-DD)
--end-date TEXT         Only process days on or before this date (YYYY-MM-DD)
--branch TEXT           Git branch/ref to read commits from (default: HEAD)
--dry-run              Print what would be created without making changes
--skip-existing        Skip days where release tag already exists (default: True)
```

## Features

- **Smart updates**: Detects new commits on existing days and updates releases appropriately
  - New commits → Creates versioned tag (`-r2`, `-r3`, etc.) for old commits, updates main tag
  - Missing release notes → Updates notes only, tag unchanged
  - No changes → Skips day (no duplicates)
- **Backfill capable**: Process entire repository history in one run
- **Conventional commits**: Automatically parses commit types for categorization
- **Dry-run preview**: See exactly what would be created before making changes
- **Date filtering**: Process specific date ranges or single days
- **Safe re-runs**: Can run daily without creating duplicates or orphaned releases

## Examples

### Backfill entire repository

```bash
/daily-releases
```

Processes all commits grouped by date. On first run, creates releases for every day with commits.

### Preview before committing

```bash
/daily-releases --dry-run
```

Shows what releases would be created without making any changes.

### Process specific month

```bash
/daily-releases --start-date 2026-02-01 --end-date 2026-02-28
```

Creates releases only for February 2026.

### Daily updates with new commits

```bash
/daily-releases
```

Run this daily. The script automatically:
- Creates releases for new days
- Updates release notes if commits changed but tag didn't
- Renames old tags to `-r2`, `-r3` if new commits added to existing day
- Main tag always points to latest commit of the day

### Verify output before pushing

```bash
/daily-releases --start-date 2026-02-21 --end-date 2026-02-21 --dry-run
```

Preview a single day's release before creating it.

## Output

For each day processed:

- **Git tag**: `daily-YYYY-MM-DD` (points to last commit of that day)
- **GitHub Release**: Named `Daily Release - YYYY-MM-DD` with markdown changelog
- **Changelog content**: Changes grouped by type (Enhancements, Bug Fixes, etc.)

## Requirements

- Git repository with commits
- `gh` (GitHub CLI) installed and authenticated
- Commits on a branch (default: HEAD/main)

## Notes

- Day boundaries are UTC
- Merge commits are categorized as non-functional/chore
- When new commits appear on an existing day, old tag is renamed to `-r2`, `-r3`, etc.
- New main tag (`daily-YYYY-MM-DD`) always points to the latest commit of the day
- Safe to run daily without creating duplicates
- Use `--dry-run` to preview changes before committing
