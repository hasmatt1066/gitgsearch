#!/bin/bash
#
# Launch script for NMDP batch processing with Ralph Wiggum
#
# Usage: ./scripts/launch_batch.sh [--test]
#
# Options:
#   --test    Run with only 5 iterations (for testing)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROGRESS_FILE="$PROJECT_ROOT/batch_progress.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "NMDP Batch Processing Launcher"
echo "========================================"
echo ""

# Check for jq (required by Ralph)
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Install with: sudo apt install jq"
    exit 1
fi

# Check if batch_progress.json exists
if [ ! -f "$PROGRESS_FILE" ]; then
    echo -e "${YELLOW}No batch in progress.${NC}"
    echo "Initializing new batch..."
    echo ""
    cd "$SCRIPT_DIR" && python3 batch_init.py
    echo ""
fi

# Show current status
echo "Current batch status:"
cd "$SCRIPT_DIR" && python3 batch_status.py

# Determine iteration limit
if [ "$1" == "--test" ]; then
    MAX_ITERATIONS=50
    echo -e "${YELLOW}TEST MODE: Limited to $MAX_ITERATIONS iterations${NC}"
else
    # Calculate based on pending schools
    # Estimate ~7 iterations per school (roster + research batches + verify + cross-ref)
    PENDING=$(cat "$PROGRESS_FILE" | jq '.pending | length')
    MAX_ITERATIONS=$((PENDING * 8 + 20))  # Add buffer

    # Cap at reasonable maximum
    if [ $MAX_ITERATIONS -gt 500 ]; then
        MAX_ITERATIONS=500
    fi

    echo "Calculated max iterations: $MAX_ITERATIONS"
    echo "(Based on $PENDING pending schools × ~8 iterations each)"
fi

echo ""
echo "========================================"
echo "Ready to launch Ralph Wiggum batch loop"
echo "========================================"
echo ""
echo "The following command will be executed:"
echo ""
echo -e "${GREEN}/ralph-loop \"Read prompts/batch_loop.md and execute. Process schools from batch_progress.json following the workflow described. Working directory: $PROJECT_ROOT\" --max-iterations $MAX_ITERATIONS --completion-promise \"BATCH_COMPLETE\"${NC}"
echo ""
echo "To monitor progress while running:"
echo "  watch -n 30 'cat batch_progress.json | jq .'"
echo ""
echo "To cancel:"
echo "  /cancel-ralph"
echo ""
read -p "Launch batch processing? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Copy and paste this command to start:"
    echo ""
    echo "/ralph-loop \"Read prompts/batch_loop.md and execute. Process schools from batch_progress.json following the workflow described. Working directory: $PROJECT_ROOT\" --max-iterations $MAX_ITERATIONS --completion-promise \"BATCH_COMPLETE\""
    echo ""
    echo "(The script cannot directly invoke /ralph-loop - paste the command above into Claude Code)"
else
    echo "Cancelled."
fi
