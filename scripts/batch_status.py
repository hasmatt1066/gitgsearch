#!/usr/bin/env python3
"""
Batch status display for NMDP coach cross-reference system.

Shows current progress of batch processing.
"""

import json
import os
import sys
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PROGRESS_PATH = os.path.join(PROJECT_ROOT, "batch_progress.json")


def load_progress() -> dict | None:
    """Load progress file if it exists."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r") as f:
            return json.load(f)
    return None


def format_duration(start_str: str) -> str:
    """Format duration since start."""
    try:
        start = datetime.fromisoformat(start_str)
        delta = datetime.now() - start
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        if delta.days > 0:
            return f"{delta.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "unknown"


def show_detailed_status(progress: dict) -> None:
    """Display detailed progress status."""
    total = progress["total_schools"]
    completed = len(progress["completed"])
    failed = len(progress["failed"])
    pending = len(progress["pending"])

    # Header
    print(f"\n{'='*60}")
    print(f"BATCH STATUS: {progress['batch_name']}")
    print(f"{'='*60}")

    # Progress bar
    if total > 0:
        done = completed + failed
        pct = done / total
        bar_width = 40
        filled = int(bar_width * pct)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"\n[{bar}] {pct*100:.1f}%")

    # Stats
    print(f"\n{'─'*30}")
    print(f"Total schools:     {total}")
    print(f"Completed:         {completed}")
    print(f"Failed:            {failed}")
    print(f"Pending:           {pending}")
    print(f"{'─'*30}")

    # Timing
    if progress.get("started"):
        print(f"\nStarted:      {progress['started']}")
        print(f"Running for:  {format_duration(progress['started'])}")

    if progress.get("last_updated"):
        print(f"Last update:  {progress['last_updated']}")

    # Current school
    if progress["current_school"]:
        print(f"\n>>> Currently processing: {progress['current_school']}")

    # Completed schools
    if progress["completed"]:
        print(f"\nCompleted ({len(progress['completed'])}):")
        for school in progress["completed"][-10:]:  # Show last 10
            print(f"  ✓ {school}")
        if len(progress["completed"]) > 10:
            print(f"  ... and {len(progress['completed']) - 10} more")

    # Failed schools
    if progress["failed"]:
        print(f"\nFailed ({len(progress['failed'])}):")
        for item in progress["failed"]:
            if isinstance(item, dict):
                print(f"  ✗ {item['name']}: {item.get('reason', 'Unknown error')}")
            else:
                print(f"  ✗ {item}")

    # Next up
    if progress["pending"]:
        print(f"\nNext up:")
        for school in progress["pending"][:5]:
            print(f"  → {school}")
        if len(progress["pending"]) > 5:
            print(f"  ... and {len(progress['pending']) - 5} more")

    print(f"\n{'='*60}\n")

    # Estimate completion
    if completed > 0 and pending > 0:
        try:
            start = datetime.fromisoformat(progress["started"])
            elapsed = (datetime.now() - start).total_seconds()
            avg_per_school = elapsed / (completed + failed)
            remaining_seconds = avg_per_school * pending
            remaining_hours = remaining_seconds / 3600
            print(f"Estimated time remaining: {remaining_hours:.1f} hours")
            print(f"(based on {avg_per_school/60:.1f} min avg per school)")
        except:
            pass


def show_json(progress: dict) -> None:
    """Output progress as JSON."""
    print(json.dumps(progress, indent=2))


def main():
    args = sys.argv[1:]

    progress = load_progress()

    if not progress:
        print("No batch in progress.")
        print("Run 'python batch_init.py' to start a new batch.")
        sys.exit(1)

    if "--json" in args:
        show_json(progress)
    else:
        show_detailed_status(progress)


if __name__ == "__main__":
    main()
