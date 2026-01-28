#!/bin/bash
# Refactoring Task File Validator
# Validates task files for correct structure and completeness

set -euo pipefail

# Usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 <path/to/tasks-refactor-*.md>"
    echo ""
    echo "Validates task file for:"
    echo "  - Task structure and required fields"
    echo "  - Status field format"
    echo "  - Dependency references"
    echo "  - Acceptance criteria presence"
    echo "  - Agent assignments"
    exit 1
fi

TASK_FILE="$1"

echo "Validating task file: $TASK_FILE"
echo ""

error_count=0
warning_count=0

# Check 1: File exists
if [ ! -f "$TASK_FILE" ]; then
    echo "ERROR: File not found: $TASK_FILE"
    exit 1
fi
echo "OK File exists"

# Check 2: File naming convention
BASENAME=$(basename "$TASK_FILE")
if [[ ! "$BASENAME" =~ ^tasks-refactor-.*\.md$ ]]; then
    echo "WARN File naming should follow pattern: tasks-refactor-{slug}.md"
    ((warning_count++))
else
    echo "OK File naming follows convention"
fi

# Check 3: Count tasks
TASK_COUNT=$(grep -c '^## Task ' "$TASK_FILE" || true)
if [ "$TASK_COUNT" -eq 0 ]; then
    echo "ERROR: No tasks found (expected '## Task' headers)"
    ((error_count++))
else
    echo "OK Found $TASK_COUNT tasks"
fi

# Check 4: Validate each task
echo ""
echo "Validating individual tasks..."

# Extract task IDs
TASK_IDS=$(grep '^## Task ' "$TASK_FILE" | grep -oE 'Task [A-Za-z0-9]+' | cut -d' ' -f2 || true)

for task_id in $TASK_IDS; do
    echo ""
    echo "--- Task $task_id ---"

    # Extract task block (from ## Task ID to next ## or EOF)
    TASK_BLOCK=$(awk "/^## Task $task_id/,/^## Task [^$task_id]|^$/" "$TASK_FILE" | head -100)

    # Check Status field
    if echo "$TASK_BLOCK" | grep -q '\*\*Status\*\*:'; then
        STATUS=$(echo "$TASK_BLOCK" | grep '\*\*Status\*\*:' | head -1 | sed 's/.*Status\*\*: *//')
        if [[ "$STATUS" =~ (NOT\ STARTED|IN\ PROGRESS|COMPLETE|BLOCKED) ]]; then
            echo "OK Status: $STATUS"
        else
            echo "WARN Status format unexpected: $STATUS"
            ((warning_count++))
        fi
    else
        echo "ERROR Missing Status field"
        ((error_count++))
    fi

    # Check Dependencies field
    if echo "$TASK_BLOCK" | grep -q '\*\*Dependencies\*\*:'; then
        echo "OK Dependencies field present"
    else
        echo "ERROR Missing Dependencies field"
        ((error_count++))
    fi

    # Check Agent field
    if echo "$TASK_BLOCK" | grep -q '\*\*Agent\*\*:'; then
        AGENT=$(echo "$TASK_BLOCK" | grep '\*\*Agent\*\*:' | head -1 | sed 's/.*Agent\*\*: *//')
        echo "OK Agent: $AGENT"
    else
        echo "ERROR Missing Agent field"
        ((error_count++))
    fi

    # Check Target field
    if echo "$TASK_BLOCK" | grep -q '\*\*Target\*\*:'; then
        echo "OK Target field present"
    else
        echo "WARN Missing Target field"
        ((warning_count++))
    fi

    # Check Acceptance Criteria
    if echo "$TASK_BLOCK" | grep -qi 'acceptance criteria'; then
        CRITERIA_COUNT=$(echo "$TASK_BLOCK" | grep -cE '^[0-9]+\.' || true)
        if [ "$CRITERIA_COUNT" -ge 3 ]; then
            echo "OK Acceptance criteria: $CRITERIA_COUNT items"
        else
            echo "WARN Acceptance criteria should have at least 3 items (found $CRITERIA_COUNT)"
            ((warning_count++))
        fi
    else
        echo "ERROR Missing Acceptance Criteria section"
        ((error_count++))
    fi

    # Check Verification Steps
    if echo "$TASK_BLOCK" | grep -qi 'verification steps'; then
        echo "OK Verification steps present"
    else
        echo "WARN Missing Verification Steps section"
        ((warning_count++))
    fi
done

# Check 5: Dependency consistency
echo ""
echo "Checking dependency consistency..."

for task_id in $TASK_IDS; do
    DEPS=$(grep -A1 "^## Task $task_id" "$TASK_FILE" | grep -oE 'Dependencies.*' | sed 's/.*: *//' | tr ',' '\n' | tr -d ' ' || true)
    for dep in $DEPS; do
        if [ "$dep" != "None" ] && [ -n "$dep" ]; then
            if ! echo "$TASK_IDS" | grep -q "^$dep$"; then
                echo "ERROR Task $task_id references non-existent dependency: $dep"
                ((error_count++))
            fi
        fi
    done
done
echo "OK Dependency check complete"

# Check 6: Parallelization info
echo ""
echo "Checking parallelization info..."
PARALLEL_COUNT=$(grep -c 'Can Parallelize With' "$TASK_FILE" || true)
if [ "$PARALLEL_COUNT" -gt 0 ]; then
    echo "OK Parallelization info present in $PARALLEL_COUNT tasks"
else
    echo "INFO No parallelization info found"
fi

# Summary
echo ""
echo "========================================"

if [ "$error_count" -eq 0 ] && [ "$warning_count" -eq 0 ]; then
    echo "PASS All checks passed!"
    exit 0
elif [ "$error_count" -eq 0 ]; then
    echo "PASS WITH WARNINGS: $warning_count warning(s)"
    exit 0
else
    echo "FAIL: $error_count error(s), $warning_count warning(s)"
    exit 1
fi
