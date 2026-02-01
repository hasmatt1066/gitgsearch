"""
manage_locations.py - Utility for managing school location data

Helps add, update, and verify school location mappings.
"""

import json
import os
import sys


def load_json(path: str) -> dict:
    """Load JSON file."""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_json(path: str, data: dict):
    """Save JSON file with pretty formatting."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {path}")


def add_school_location(locations_path: str, school_name: str, state: str, county: str):
    """
    Add or update a school's location.

    Args:
        locations_path: Path to school_locations.json
        school_name: Canonical school name (uppercase)
        state: State name
        county: County name
    """
    locations = load_json(locations_path)

    school_key = school_name.upper()
    locations[school_key] = {
        "state": state,
        "county": county
    }

    save_json(locations_path, locations)
    print(f"Added: {school_key} -> {state}, {county}")


def list_missing_locations(cache_dir: str, locations_path: str, aliases_path: str):
    """
    List schools in cache that don't have location data.

    Args:
        cache_dir: Path to cache directory
        locations_path: Path to school_locations.json
        aliases_path: Path to school_aliases.json
    """
    locations = load_json(locations_path)
    aliases = load_json(aliases_path)

    # Get all location keys (including aliases)
    known_schools = set(locations.keys())
    for canonical, alias_list in aliases.items():
        if canonical in locations:
            for alias in alias_list:
                known_schools.add(alias.upper())

    # Check cached schools
    missing = []
    if os.path.exists(cache_dir):
        for school_dir in os.listdir(cache_dir):
            school_path = os.path.join(cache_dir, school_dir)
            if os.path.isdir(school_path):
                # Try to get actual school name from roster
                roster_path = os.path.join(school_path, "roster.json")
                if os.path.exists(roster_path):
                    roster = load_json(roster_path)
                    if roster and isinstance(roster, dict):
                        # Roster is a dict with "school" key
                        school_name = roster.get("school", roster.get("school_name", school_dir.replace("_", " ").title()))
                    elif roster and isinstance(roster, list) and len(roster) > 0:
                        # Roster is a list of coaches
                        school_name = roster[0].get("current_school", school_dir.replace("_", " ").title())
                    else:
                        school_name = school_dir.replace("_", " ").title()
                else:
                    school_name = school_dir.replace("_", " ").title()

                # Check if we have location data
                upper_name = school_name.upper()
                if upper_name not in known_schools:
                    # Also check if it matches any alias
                    found = False
                    for canonical, alias_list in aliases.items():
                        if canonical.startswith("_"):
                            continue
                        for alias in alias_list:
                            if alias.upper() in upper_name or upper_name in alias.upper():
                                if canonical in locations:
                                    found = True
                                    break
                        if found:
                            break

                    if not found:
                        missing.append(school_name)

    if missing:
        print(f"Schools missing location data ({len(missing)}):")
        for school in sorted(missing):
            print(f"  - {school}")
    else:
        print("All cached schools have location data!")

    return missing


def bulk_add_from_file(locations_path: str, input_file: str):
    """
    Bulk add schools from a CSV/TSV file.

    Expected format (one per line):
    SCHOOL NAME,State,County

    Args:
        locations_path: Path to school_locations.json
        input_file: Path to input file
    """
    locations = load_json(locations_path)

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try comma first, then tab
            if "," in line:
                parts = line.split(",")
            elif "\t" in line:
                parts = line.split("\t")
            else:
                print(f"Skipping invalid line: {line}")
                continue

            if len(parts) >= 3:
                school = parts[0].strip().upper()
                state = parts[1].strip()
                county = parts[2].strip()

                locations[school] = {
                    "state": state,
                    "county": county
                }
                print(f"Added: {school}")

    save_json(locations_path, locations)


def main():
    """CLI entry point."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    locations_path = os.path.join(base_dir, "data", "school_locations.json")
    aliases_path = os.path.join(base_dir, "data", "school_aliases.json")
    cache_dir = os.path.join(base_dir, "cache")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_locations.py missing")
        print("    - List schools missing location data")
        print()
        print("  python manage_locations.py add <school> <state> <county>")
        print("    - Add a single school location")
        print()
        print("  python manage_locations.py bulk <input_file>")
        print("    - Bulk add from CSV file (SCHOOL,State,County)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "missing":
        list_missing_locations(cache_dir, locations_path, aliases_path)

    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: python manage_locations.py add <school> <state> <county>")
            sys.exit(1)
        school = sys.argv[2]
        state = sys.argv[3]
        county = sys.argv[4]
        add_school_location(locations_path, school, state, county)

    elif command == "bulk":
        if len(sys.argv) < 3:
            print("Usage: python manage_locations.py bulk <input_file>")
            sys.exit(1)
        input_file = sys.argv[2]
        bulk_add_from_file(locations_path, input_file)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
