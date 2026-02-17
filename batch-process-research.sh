#!/bin/bash
# Batch process research files using the research-context-agent
# This script provides instructions for processing research files in batches

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Research Integration Opportunities - Batch Processor         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

# Count research files
TOTAL_FILES=$(find research/ -name "*.md" -type f ! -name "README.md" | wc -l)
echo -e "${GREEN}Found $TOTAL_FILES research files${NC}"
echo

# Parse command line arguments
CATEGORY=""
SINGLE_FILE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --category|-c)
            CATEGORY="$2"
            shift 2
            ;;
        --file|-f)
            SINGLE_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --category, -c CATEGORY    Process only files in this category"
            echo "  --file, -f FILE           Process a single file"
            echo "  --dry-run                 Show what would be processed"
            echo "  --help, -h                Show this help message"
            echo
            echo "This script requires processing through Claude Code Task tool."
            echo "For each file, it will print the command to run."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine which files to process
if [[ -n "$SINGLE_FILE" ]]; then
    if [[ ! -f "$SINGLE_FILE" ]]; then
        echo -e "${RED}Error: File not found: $SINGLE_FILE${NC}"
        exit 1
    fi
    FILES=("$SINGLE_FILE")
elif [[ -n "$CATEGORY" ]]; then
    if [[ ! -d "research/$CATEGORY" ]]; then
        echo -e "${RED}Error: Category not found: $CATEGORY${NC}"
        exit 1
    fi
    mapfile -t FILES < <(find "research/$CATEGORY" -name "*.md" -type f ! -name "README.md" | sort)
else
    mapfile -t FILES < <(find research/ -name "*.md" -type f ! -name "README.md" | sort)
fi

echo -e "${YELLOW}Files to process: ${#FILES[@]}${NC}"
echo

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}Dry run mode - showing files that would be processed:${NC}"
    for file in "${FILES[@]}"; do
        echo "  - $file"
    done
    exit 0
fi

echo -e "${BLUE}Processing Instructions:${NC}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "This script will guide you through processing each research file."
echo "For each file, you'll need to use Claude Code's Task tool to spawn"
echo "the research-context-agent."
echo
echo -e "${YELLOW}Press Enter to continue, or Ctrl+C to cancel...${NC}"
read -r

PROCESSED=0
SKIPPED=0

for file in "${FILES[@]}"; do
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}File [$((PROCESSED + SKIPPED + 1))/${#FILES[@]}]: ${GREEN}$file${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo
    
    # Check if file already has Integration Opportunities with the new format
    if grep -q "## Integration Opportunities" "$file" && grep -q "### Enhances Existing" "$file"; then
        echo -e "${GREEN}✓ File already has new Integration Opportunities format${NC}"
        echo -e "${YELLOW}Process anyway? [y/N]: ${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Skipping...${NC}"
            ((SKIPPED++))
            continue
        fi
    fi
    
    echo "Run this Task tool invocation in Claude Code:"
    echo
    echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
    cat <<EOF
You are the research-context-agent as defined in $REPO_ROOT/.claude/agents/research-context-agent.md

Please process this research file:
$REPO_ROOT/$file

Follow the three-phase process:
1. Absorb: Read and understand the research file
2. Search & Match: Find connections across the 5 dimensions
3. Append: Add or REPLACE the Integration Opportunities section

Use the structured format with:
- "### Enhances Existing" table
- "### New Skill Candidates" list
- "### New MCP Server Candidates" list
- "### Cross-References" list

Remember: Concrete over vague, skip empty sections, no false positives.
EOF
    echo -e "${GREEN}───────────────────────────────────────────────────────────────${NC}"
    echo
    echo -e "${YELLOW}After processing, press Enter to continue to next file...${NC}"
    read -r
    ((PROCESSED++))
done

echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Processing Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo
echo "Summary:"
echo "  - Total files: ${#FILES[@]}"
echo "  - Processed: $PROCESSED"
echo "  - Skipped: $SKIPPED"
echo
echo -e "${YELLOW}Note: Remember to review and commit the changes!${NC}"
