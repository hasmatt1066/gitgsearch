#!/usr/bin/env python3
"""
Batch resume utility for NMDP coach cross-reference system.

Handles recovery from interrupted batch processing.
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


def save_progress(progress: dict) -> None:
    """Save progress to file."""
    progress["last_updated"] = datetime.now().isoformat()
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, indent=2)


def reset_current_school(progress: dict) -> bool:
    """Move current_school back to front of pending queue."""
    current = progress.get("current_school")

    if not current:
        print("No school currently in progress.")
        return False

    print(f"Resetting: {current}")

    # Move to front of pending
    progress["pending"].insert(0, current)
    progress["current_school"] = None

    save_progress(progress)

    print(f"'{current}' moved back to pending queue.")
    print(f"Pending schools: {len(progress['pending'])}")
    return True


def retry_failed(progress: dict, school_name: str = None) -> bool:
    """Move a failed school back to pending for retry."""
    if not progress["failed"]:
        print("No failed schools to retry.")
        return False

    if school_name:
        # Find specific school in failed list
        found = None
        for i, item in enumerate(progress["failed"]):
            name = item["name"] if isinstance(item, dict) else item
            if name.lower() == school_name.lower():
                found = i
                break

        if found is None:
            print(f"School '{school_name}' not found in failed list.")
            return False

        item = progress["failed"].pop(found)
        name = item["name"] if isinstance(item, dict) else item
        progress["pending"].insert(0, name)
        save_progress(progress)
        print(f"'{name}' moved from failed to pending.")
        return True
    else:
        # Move all failed schools back to pending
        count = 0
        while progress["failed"]:
            item = progress["failed"].pop(0)
            name = item["name"] if isinstance(item, dict) else item
            progress["pending"].append(name)
            count += 1

        save_progress(progress)
        print(f"Moved {count} failed schools back to pending.")
        return True


def show_status(progress: dict) -> None:
    """Show brief status."""
    print(f"\nBatch: {progress['batch_name']}")
    print(f"Current school: {progress['current_school'] or 'None'}")
    print(f"Completed: {len(progress['completed'])}")
    print(f"Failed: {len(progress['failed'])}")
    print(f"Pending: {len(progress['pending'])}")
    print()


def main():
    args = sys.argv[1:]

    progress = load_progress()

    if not progress:
        print("No batch in progress.")
        print("Run 'python batch_init.py' to start a new batch.")
        sys.exit(1)

    if not args:
        # Default: reset current school if any
        show_status(progress)

        if progress["current_school"]:
            print("A school was interrupted mid-processing.")
            print(f"Current school: {progress['current_school']}")
            print("\nOptions:")
            print("  python batch_resume.py reset    - Move current school back to pending")
            print("  python batch_resume.py retry    - Move all failed schools back to pending")
            print("  python batch_resume.py retry \"School Name\" - Retry specific failed school")
        elif progress["failed"]:
            print(f"\n{len(progress['failed'])} failed schools.")
            print("Use 'python batch_resume.py retry' to retry all failed schools.")
        else:
            print("Batch can be resumed normally. No action needed.")
        return

    command = args[0].lower()

    if command == "reset":
        reset_current_school(progress)
    elif command == "retry":
        school_name = args[1] if len(args) > 1 else None
        retry_failed(progress, school_name)
    elif command == "status":
        show_status(progress)
    else:
        print(f"Unknown command: {command}")
        print("Commands: reset, retry, status")
        sys.exit(1)


if __name__ == "__main__":
    main()
