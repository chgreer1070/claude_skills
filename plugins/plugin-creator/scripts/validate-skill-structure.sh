#!/bin/bash
# Skill Structure Validator
# Validates skill directories for correct structure and content quality

set -euo pipefail

# Usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path/to/skill-directory>"
    echo ""
    echo "Validates skill structure for:"
    echo "  - SKILL.md presence and frontmatter"
    echo "  - Required fields (name, description)"
    echo "  - Line count limits (<500 recommended)"
    echo "  - Progressive disclosure structure"
    echo "  - Reference file validity"
    exit 1
fi

SKILL_DIR="$1"

echo "Validating skill: $SKILL_DIR"
echo ""

error_count=0
warning_count=0

# Check 1: Directory exists
if [ ! -d "$SKILL_DIR" ]; then
    echo "ERROR: Directory not found: $SKILL_DIR"
    exit 1
fi
echo "OK Directory exists"

# Check 2: SKILL.md exists
SKILL_FILE="$SKILL_DIR/SKILL.md"
if [ ! -f "$SKILL_FILE" ]; then
    echo "ERROR: SKILL.md not found in $SKILL_DIR"
    exit 1
fi
echo "OK SKILL.md exists"

# Check 3: Frontmatter structure
FIRST_LINE=$(head -1 "$SKILL_FILE")
if [ "$FIRST_LINE" != "---" ]; then
    echo "ERROR: SKILL.md must start with YAML frontmatter (---)"
    ((error_count++))
else
    echo "OK Starts with frontmatter"
fi

# Check 4: Frontmatter closes
if ! tail -n +2 "$SKILL_FILE" | grep -q '^---$'; then
    echo "ERROR: Frontmatter not closed (missing second ---)"
    ((error_count++))
else
    echo "OK Frontmatter properly closed"
fi

# Extract frontmatter
FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$SKILL_FILE" | head -50)

# Check 5: Name field
NAME=$(echo "$FRONTMATTER" | grep '^name:' | sed 's/name: *//' | sed "s/^['\"]//;s/['\"]$//")
if [ -z "$NAME" ]; then
    echo "ERROR: Missing required field: name"
    ((error_count++))
else
    echo "OK name: $NAME"

    # Validate name format
    if ! [[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]] && ! [[ "$NAME" =~ ^[a-z0-9]$ ]]; then
        echo "WARN name should be lowercase with hyphens only"
        ((warning_count++))
    fi
fi

# Check 6: Description field
DESCRIPTION=$(echo "$FRONTMATTER" | grep '^description:' | sed 's/description: *//')
if [ -z "$DESCRIPTION" ]; then
    echo "ERROR: Missing required field: description"
    ((error_count++))
else
    desc_length=${#DESCRIPTION}
    echo "OK description: ${desc_length} characters"

    if [ "$desc_length" -lt 20 ]; then
        echo "WARN description too short (minimum 20 characters recommended)"
        ((warning_count++))
    fi

    # Check for trigger phrases
    if ! echo "$DESCRIPTION" | grep -qi "use when\|use this\|trigger\|activate"; then
        echo "WARN description should include trigger phrases"
        ((warning_count++))
    fi
fi

# Check 7: Line count
BODY_START=$(grep -n '^---$' "$SKILL_FILE" | tail -1 | cut -d: -f1)
TOTAL_LINES=$(wc -l <"$SKILL_FILE")
BODY_LINES=$((TOTAL_LINES - BODY_START))

echo "OK Line count: $BODY_LINES lines (body), $TOTAL_LINES total"

if [ $BODY_LINES -gt 500 ]; then
    echo "WARN Skill body exceeds 500 lines - consider splitting"
    ((warning_count++))
elif [ $BODY_LINES -gt 800 ]; then
    echo "ERROR Skill body exceeds 800 lines - must split"
    ((error_count++))
fi

# Check 8: Progressive disclosure
echo ""
echo "Checking progressive disclosure..."

if [ -d "$SKILL_DIR/references" ]; then
    REF_COUNT=$(find "$SKILL_DIR/references" -name "*.md" 2>/dev/null | wc -l)
    echo "OK references/: $REF_COUNT files"
else
    echo "INFO No references/ directory"
fi

if [ -d "$SKILL_DIR/examples" ]; then
    EX_COUNT=$(find "$SKILL_DIR/examples" -name "*" -type f 2>/dev/null | wc -l)
    echo "OK examples/: $EX_COUNT files"
else
    echo "INFO No examples/ directory"
fi

if [ -d "$SKILL_DIR/scripts" ]; then
    SC_COUNT=$(find "$SKILL_DIR/scripts" -name "*" -type f 2>/dev/null | wc -l)
    echo "OK scripts/: $SC_COUNT files"
else
    echo "INFO No scripts/ directory"
fi

# Check 9: Internal links
echo ""
echo "Checking internal links..."

# Find markdown links in SKILL.md
LINKS=$(grep -oE '\[([^]]+)\]\(([^)]+)\)' "$SKILL_FILE" | grep -oE '\(./[^)]+\)' | tr -d '()' || true)

if [ -n "$LINKS" ]; then
    while IFS= read -r link; do
        FULL_PATH="$SKILL_DIR/$link"
        # Remove ./ prefix for path resolution
        FULL_PATH="${FULL_PATH//\/.\//\/}"
        if [ -f "$FULL_PATH" ]; then
            echo "OK Link valid: $link"
        else
            echo "ERROR Broken link: $link"
            ((error_count++))
        fi
    done <<<"$LINKS"
else
    echo "INFO No internal links found"
fi

# Summary
echo ""
echo "========================================"

if [ $error_count -eq 0 ] && [ $warning_count -eq 0 ]; then
    echo "PASS All checks passed!"
    exit 0
elif [ $error_count -eq 0 ]; then
    echo "PASS WITH WARNINGS: $warning_count warning(s)"
    exit 0
else
    echo "FAIL: $error_count error(s), $warning_count warning(s)"
    exit 1
fi
