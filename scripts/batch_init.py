#!/usr/bin/env python3
"""
Batch initialization script for NMDP coach cross-reference system.

Reads the target schools list and initializes the batch progress tracker.
"""

import json
import os
import sys
from datetime import datetime

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TARGET_SCHOOLS_PATH = os.path.join(PROJECT_ROOT, "data", "target_schools_west.json")
PROGRESS_PATH = os.path.join(PROJECT_ROOT, "batch_progress.json")


def load_target_schools(path: str = TARGET_SCHOOLS_PATH) -> dict:
    """Load the target schools list."""
    if not os.path.exists(path):
        print(f"Error: Target schools file not found: {path}")
        sys.exit(1)

    with open(path, "r") as f:
        return json.load(f)


def load_progress() -> dict | None:
    """Load existing progress file if it exists."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r") as f:
            return json.load(f)
    return None


def save_progress(progress: dict) -> None:
    """Save progress to file."""
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, indent=2)
    print(f"Progress saved to: {PROGRESS_PATH}")


def create_fresh_progress(schools_data: dict) -> dict:
    """Create a fresh progress tracker from schools data."""
    schools = schools_data.get("schools", [])

    # Sort by priority (lower number = higher priority)
    sorted_schools = sorted(schools, key=lambda s: s.get("priority", 99))

    # Extract just the school names for pending list
    pending = [s["name"] for s in sorted_schools]

    return {
        "batch_name": schools_data.get("batch_name", "Unnamed Batch"),
        "source_file": TARGET_SCHOOLS_PATH,
        "total_schools": len(pending),
        "started": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "current_school": None,
        "completed": [],
        "failed": [],
        "pending": pending
    }


def show_status(progress: dict) -> None:
    """Display current progress status."""
    total = progress["total_schools"]
    completed = len(progress["completed"])
    failed = len(progress["failed"])
    pending = len(progress["pending"])

    print(f"\n{'='*50}")
    print(f"Batch: {progress['batch_name']}")
    print(f"{'='*50}")
    print(f"Total schools:  {total}")
    print(f"Completed:      {completed} ({100*completed/total:.1f}%)" if total > 0 else "Completed:      0")
    print(f"Failed:         {failed}")
    print(f"Pending:        {pending}")

    if progress["current_school"]:
        print(f"\nCurrently processing: {progress['current_school']}")

    if progress["failed"]:
        print(f"\nFailed schools:")
        for item in progress["failed"]:
            if isinstance(item, dict):
                print(f"  - {item['name']}: {item.get('reason', 'Unknown error')}")
            else:
                print(f"  - {item}")

    print(f"{'='*50}\n")


def main():
    args = sys.argv[1:]
    force_reset = "--reset" in args or "-r" in args

    # Check for existing progress
    existing = load_progress()

    if existing and not force_reset:
        print("Existing batch progress found!")
        show_status(existing)

        completed = len(existing["completed"])
        failed = len(existing["failed"])
        pending = len(existing["pending"])

        if pending == 0 and existing["current_school"] is None:
            print("This batch is complete. Use --reset to start a new batch.")
            return

        print("Options:")
        print("  1. Resume existing batch (do nothing)")
        print("  2. Reset and start fresh (run with --reset)")
        print("\nTo reset: python batch_init.py --reset")
        return

    # Load schools and create fresh progress
    schools_data = load_target_schools()
    progress = create_fresh_progress(schools_data)

    # Save
    save_progress(progress)

    print("Batch initialized!")
    show_status(progress)

    print("Next steps:")
    print("  1. Review the pending schools list")
    print("  2. Launch the Ralph loop:")
    print('     /ralph-loop "..." --max-iterations 200 --completion-promise "BATCH_COMPLETE"')
    print("  Or use: ./scripts/launch_batch.sh")


if __name__ == "__main__":
    main()
