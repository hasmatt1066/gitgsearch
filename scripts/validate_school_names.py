#!/usr/bin/env python3
"""
Validates that all school names in target list have matching aliases.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def build_alias_lookup(aliases: dict) -> dict:
    """Build a lookup from any name variation to canonical name."""
    lookup = {}

    for canonical, variations in aliases.items():
        if canonical.startswith("_"):  # Skip comments
            continue

        # The canonical name itself
        lookup[canonical.upper()] = canonical

        # All aliases
        for alias in variations:
            lookup[alias.upper()] = canonical

    return lookup


def validate_schools(target_path: str, aliases_path: str) -> tuple[list, list]:
    """Validate school names against aliases. Returns (matched, unmatched)."""
    targets = load_json(target_path)
    aliases = load_json(aliases_path)

    lookup = build_alias_lookup(aliases)

    matched = []
    unmatched = []

    for school in targets.get("schools", []):
        name = school.get("name", "")
        canonical = school.get("canonical", "")

        # Check if name matches
        name_match = lookup.get(name.upper())
        canonical_match = lookup.get(canonical.upper())

        if name_match or canonical_match:
            matched.append({
                "name": name,
                "canonical": canonical,
                "resolved_to": name_match or canonical_match
            })
        else:
            unmatched.append({
                "name": name,
                "canonical": canonical
            })

    return matched, unmatched


def main():
    target_path = os.path.join(PROJECT_ROOT, "data", "target_schools_west.json")
    aliases_path = os.path.join(PROJECT_ROOT, "data", "school_aliases.json")

    matched, unmatched = validate_schools(target_path, aliases_path)

    print(f"\n{'='*60}")
    print(f"SCHOOL NAME VALIDATION")
    print(f"{'='*60}")
    print(f"\nMatched: {len(matched)}")
    print(f"Unmatched: {len(unmatched)}")

    if unmatched:
        print(f"\n{'─'*60}")
        print("UNMATCHED SCHOOLS (need aliases added):")
        print(f"{'─'*60}")
        for school in unmatched:
            print(f"  ✗ {school['name']}")
            print(f"    Canonical: {school['canonical']}")

    if matched:
        print(f"\n{'─'*60}")
        print("MATCHED SCHOOLS:")
        print(f"{'─'*60}")
        for school in matched:
            status = "✓" if school["resolved_to"] == school["canonical"] else "~"
            print(f"  {status} {school['name']} → {school['resolved_to']}")

    print(f"\n{'='*60}")

    if unmatched:
        print(f"\n⚠ {len(unmatched)} schools need aliases added!")
        sys.exit(1)
    else:
        print("\n✓ All school names validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
