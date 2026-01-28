#!/bin/bash
# Skill Line Counter
# Counts lines in skills and identifies those exceeding thresholds

set -euo pipefail

# Usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path/to/plugin-or-skill>"
    echo ""
    echo "Counts lines in skill SKILL.md files and reports:"
    echo "  - Total lines per skill"
    echo "  - Body lines (excluding frontmatter)"
    echo "  - Skills exceeding 500 line threshold"
    echo "  - Skills exceeding 800 line critical threshold"
    exit 1
fi

TARGET="$1"

echo "Counting skill lines in: $TARGET"
echo ""

# Determine if target is a skill directory or plugin
if [ -f "$TARGET/SKILL.md" ]; then
    # Single skill
    SKILL_FILES="$TARGET/SKILL.md"
elif [ -d "$TARGET/skills" ]; then
    # Plugin with skills directory
    SKILL_FILES=$(find "$TARGET/skills" -name "SKILL.md" 2>/dev/null || true)
elif [ -d "$TARGET" ]; then
    # Maybe a skills directory directly
    SKILL_FILES=$(find "$TARGET" -name "SKILL.md" 2>/dev/null || true)
else
    echo "ERROR: Target not found or not a valid skill/plugin directory"
    exit 1
fi

if [ -z "$SKILL_FILES" ]; then
    echo "No SKILL.md files found"
    exit 0
fi

echo "| Skill | Total | Body | Status |"
echo "|-------|-------|------|--------|"

over_500=0
over_800=0

for skill_file in $SKILL_FILES; do
    SKILL_DIR=$(dirname "$skill_file")
    SKILL_NAME=$(basename "$SKILL_DIR")

    TOTAL_LINES=$(wc -l <"$skill_file")

    # Find end of frontmatter (second ---)
    FRONTMATTER_END=$(grep -n '^---$' "$skill_file" | head -2 | tail -1 | cut -d: -f1)
    if [ -z "$FRONTMATTER_END" ]; then
        BODY_LINES="$TOTAL_LINES"
    else
        BODY_LINES=$((TOTAL_LINES - FRONTMATTER_END))
    fi

    # Determine status
    if [ "$BODY_LINES" -gt 800 ]; then
        STATUS="CRITICAL (>800)"
        over_800=$((over_800 + 1))
    elif [ "$BODY_LINES" -gt 500 ]; then
        STATUS="WARNING (>500)"
        over_500=$((over_500 + 1))
    else
        STATUS="OK"
    fi

    echo "| $SKILL_NAME | $TOTAL_LINES | $BODY_LINES | $STATUS |"
done

echo ""
echo "========================================"
echo "Summary:"
echo "  Skills within limits: $(($(echo "$SKILL_FILES" | wc -w) - over_500 - over_800))"
echo "  Skills over 500 lines (warning): $over_500"
echo "  Skills over 800 lines (critical): $over_800"

if [ "$over_800" -gt 0 ]; then
    echo ""
    echo "CRITICAL: $over_800 skill(s) exceed 800 lines and MUST be split"
    exit 1
elif [ "$over_500" -gt 0 ]; then
    echo ""
    echo "WARNING: $over_500 skill(s) exceed 500 lines and should be considered for splitting"
    exit 0
else
    echo ""
    echo "All skills within recommended limits"
    exit 0
fi
