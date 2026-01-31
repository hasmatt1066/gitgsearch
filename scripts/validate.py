"""
validate.py - Schema validation for coach data

Validates coach career data against required schema before cross-referencing.
Returns validation status and list of errors/warnings.
"""

import re
import json
import sys
from typing import Tuple, List, Dict, Any

# Valid research status values
VALID_STATUSES = ["FOUND", "PARTIAL", "NOT_FOUND", "AMBIGUOUS"]

# Valid source types for roster entries
VALID_SOURCE_TYPES = ["official_roster", "news_report", "departure_reported"]

# Required fields for coach data
REQUIRED_FIELDS = ["name", "current_position", "current_school", "career_history", "research_status"]

# Required fields for each career entry
CAREER_ENTRY_FIELDS = ["school", "position", "years"]

# Year format pattern: YYYY-YYYY or YYYY-present
YEAR_PATTERN = r"^\d{4}-(present|\d{4})$"


def validate_year_format(years: str) -> bool:
    """Check if year string matches expected format."""
    return bool(re.match(YEAR_PATTERN, years, re.IGNORECASE))


def validate_career_entry(entry: Dict[str, Any], index: int) -> List[str]:
    """Validate a single career history entry."""
    errors = []
    warnings = []

    # Check required fields
    for field in CAREER_ENTRY_FIELDS:
        if field not in entry or not entry[field]:
            errors.append(f"Career entry {index}: missing required field '{field}'")

    # Validate year format if present
    if "years" in entry and entry["years"]:
        if not validate_year_format(entry["years"]):
            errors.append(f"Career entry {index}: invalid year format '{entry['years']}' (expected YYYY-YYYY or YYYY-present)")

    # Check for source URL (warning, not error)
    if "source_url" not in entry or not entry["source_url"]:
        warnings.append(f"Career entry {index}: missing source_url (data will be marked UNVERIFIED)")

    return errors, warnings


def validate_coach_data(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate coach data against required schema.

    Args:
        data: Coach data dictionary

    Returns:
        Tuple of (is_valid, errors, warnings)
        - is_valid: True if no errors (warnings don't invalidate)
        - errors: List of error messages (blocking issues)
        - warnings: List of warning messages (non-blocking issues)
    """
    errors = []
    warnings = []

    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            if field != "career_history":  # career_history can be empty list
                errors.append(f"Required field '{field}' is empty")

    # Validate research_status
    if "research_status" in data and data["research_status"]:
        if data["research_status"] not in VALID_STATUSES:
            errors.append(f"Invalid research_status: '{data['research_status']}' (valid: {VALID_STATUSES})")

    # Validate career_history
    if "career_history" in data:
        if not isinstance(data["career_history"], list):
            errors.append("career_history must be a list")
        else:
            for i, entry in enumerate(data["career_history"]):
                if not isinstance(entry, dict):
                    errors.append(f"Career entry {i}: must be a dictionary")
                else:
                    entry_errors, entry_warnings = validate_career_entry(entry, i)
                    errors.extend(entry_errors)
                    warnings.extend(entry_warnings)

    # Check for empty career history with FOUND status
    if data.get("research_status") == "FOUND" and not data.get("career_history"):
        warnings.append("research_status is FOUND but career_history is empty")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_roster_data(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate roster data against required schema.

    Args:
        data: Roster data dictionary

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    required_fields = ["school", "fetched_date", "coaches"]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    # Check for official_roster_url (new field, warning if missing)
    if "official_roster_url" not in data or not data["official_roster_url"]:
        warnings.append("Missing official_roster_url for roster")

    if "coaches" in data:
        if not isinstance(data["coaches"], list):
            errors.append("coaches must be a list")
        elif len(data["coaches"]) == 0:
            warnings.append("coaches list is empty")
        else:
            for i, coach in enumerate(data["coaches"]):
                if not isinstance(coach, dict):
                    errors.append(f"Coach entry {i}: must be a dictionary")
                else:
                    if "name" not in coach or not coach["name"]:
                        errors.append(f"Coach entry {i}: missing name")
                    if "position" not in coach or not coach["position"]:
                        errors.append(f"Coach entry {i}: missing position")

                    # Validate source_type field
                    if "source_type" not in coach or not coach["source_type"]:
                        warnings.append(f"Coach entry {i} ({coach.get('name', 'unknown')}): missing source_type")
                    elif coach["source_type"] not in VALID_SOURCE_TYPES:
                        errors.append(f"Coach entry {i} ({coach.get('name', 'unknown')}): invalid source_type '{coach['source_type']}' (valid: {VALID_SOURCE_TYPES})")

                    # Validate source_url for each coach
                    if "source_url" not in coach or not coach["source_url"]:
                        warnings.append(f"Coach entry {i} ({coach.get('name', 'unknown')}): missing source_url")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_file(filepath: str, data_type: str = "coach") -> Tuple[bool, List[str], List[str]]:
    """
    Validate a JSON file.

    Args:
        filepath: Path to JSON file
        data_type: "coach" or "roster"

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, [f"File not found: {filepath}"], []
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"], []

    if data_type == "coach":
        return validate_coach_data(data)
    elif data_type == "roster":
        return validate_roster_data(data)
    else:
        return False, [f"Unknown data_type: {data_type}"], []


if __name__ == "__main__":
    """CLI usage: python validate.py <filepath> [coach|roster]"""
    if len(sys.argv) < 2:
        print("Usage: python validate.py <filepath> [coach|roster]")
        print("  filepath: Path to JSON file to validate")
        print("  type: 'coach' (default) or 'roster'")
        sys.exit(1)

    filepath = sys.argv[1]
    data_type = sys.argv[2] if len(sys.argv) > 2 else "coach"

    is_valid, errors, warnings = validate_file(filepath, data_type)

    print(f"Validating: {filepath}")
    print(f"Type: {data_type}")
    print(f"Valid: {is_valid}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid and not warnings:
        print("\nNo issues found.")

    sys.exit(0 if is_valid else 1)
