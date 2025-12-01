#!/bin/bash
# Cleanup old log files
#
# Usage:
#   bash cleanup_old_logs.sh              # Interactive - asks for confirmation
#   bash cleanup_old_logs.sh --auto       # Auto-delete logs older than 7 days
#   bash cleanup_old_logs.sh --days 30    # Delete logs older than 30 days

DAYS=0
AUTO_DELETE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_DELETE=true
            shift
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: bash cleanup_old_logs.sh [--auto] [--days N]"
            exit 1
            ;;
    esac
done

cd data || exit 1

# Count files to be deleted
if [ "$DAYS" -eq 0 ]; then
    APP_COUNT=$(find . -name "app_*.log" -type f 2>/dev/null | wc -l)
    RUN_COUNT=$(find . -name "run_*.log" -type f 2>/dev/null | wc -l)
else
    APP_COUNT=$(find . -name "app_*.log" -type f -mtime +$DAYS 2>/dev/null | wc -l)
    RUN_COUNT=$(find . -name "run_*.log" -type f -mtime +$DAYS 2>/dev/null | wc -l)
fi
TOTAL=$((APP_COUNT + RUN_COUNT))

if [ $TOTAL -eq 0 ]; then
    echo "✅ No log files older than $DAYS days found."
    exit 0
fi

echo "Found $TOTAL log files older than $DAYS days:"
echo "  - App logs: $APP_COUNT"
echo "  - Run logs: $RUN_COUNT"
echo

if [ "$AUTO_DELETE" = false ]; then
    # Interactive mode - ask for confirmation
    echo "Files to be deleted:"
    if [ "$DAYS" -eq 0 ]; then
        find . -name "app_*.log" -o -name "run_*.log" -type f | head -20
    else
        find . -name "app_*.log" -o -name "run_*.log" -type f -mtime +$DAYS | head -20
    fi
    if [ $TOTAL -gt 20 ]; then
        echo "  ... and $((TOTAL - 20)) more"
    fi
    echo

    read -p "Delete these files? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Delete files
echo "Deleting..."
if [ "$DAYS" -eq 0 ]; then
    find . -name "app_*.log" -type f -delete
    find . -name "run_*.log" -type f -delete
else
    find . -name "app_*.log" -type f -mtime +$DAYS -delete
    find . -name "run_*.log" -type f -mtime +$DAYS -delete
fi

echo "✅ Deleted $TOTAL log files."
