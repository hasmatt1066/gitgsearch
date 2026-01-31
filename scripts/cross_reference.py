"""
cross_reference.py - NMDP overlap detection

Deterministically cross-references coach career histories against
the NMDP GITG database to find overlaps where a coach was at a school
during the same academic year NMDP ran a program there.
"""

import json
import re
import sys
import os
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime

# Import normalizer
from normalize import SchoolNormalizer, normalize_school_name

# Import logger (optional - may not be set up when running standalone)
try:
    from logger import get_logger
    _has_logger = True
except ImportError:
    _has_logger = False


def _log(level: str, message: str):
    """Log a message if logger is available."""
    if _has_logger:
        logger = get_logger()
        getattr(logger, level)(message)


def _log_info(message: str):
    _log("info", message)


def _log_debug(message: str):
    _log("debug", message)


def _log_warning(message: str):
    _log("warning", message)


def load_json_file(filepath: str) -> Dict:
    """Load a JSON file and return its contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_year_range(years_str: str, current_year: int = None) -> List[int]:
    """
    Parse a year range string into a list of football seasons (calendar years).

    Year Range Semantics:
    ---------------------
    In college football, "2020-2022" means the coach was there for the 2020, 2021,
    AND 2022 football seasons. The end year is INCLUSIVE - it represents the last
    season coached, not the year they departed.

    Each calendar year maps to an academic year:
    - 2020 season → 2020-2021 academic year (Fall 2020 - Spring 2021)
    - 2021 season → 2021-2022 academic year
    - 2022 season → 2022-2023 academic year

    For "present", we include up to but NOT including the current calendar year,
    since the current season's academic year is still in progress.

    Args:
        years_str: String like "2020-2022" or "2024-present"
        current_year: Year to use for "present" (defaults to current year)

    Returns:
        List of calendar years representing football seasons

    Examples:
        "2020-2022" -> [2020, 2021, 2022]  (3 seasons, 3 academic years)
        "2024-present" -> [2024, 2025] (if current_year is 2026)
        "2023-2023" -> [2023]  (single season)
        "2019-2021" -> [2019, 2020, 2021]  (e.g., Dan Lanning at Georgia)
    """
    if current_year is None:
        current_year = datetime.now().year

    years_str = years_str.strip().lower()

    # Handle "present"
    if "present" in years_str:
        match = re.match(r"(\d{4})\s*-\s*present", years_str)
        if match:
            start_year = int(match.group(1))
            # Include years up to current year - 1
            # (current season is still in progress, academic year not complete)
            return list(range(start_year, current_year))
        return []

    # Handle standard year range (end year is INCLUSIVE)
    match = re.match(r"(\d{4})\s*-\s*(\d{4})", years_str)
    if match:
        start_year = int(match.group(1))
        end_year = int(match.group(2))
        # "2020-2022" means seasons 2020, 2021, 2022 (end year inclusive)
        return list(range(start_year, end_year + 1))

    # Handle single year
    match = re.match(r"(\d{4})", years_str)
    if match:
        return [int(match.group(1))]

    return []


def year_to_academic_year(year: int) -> str:
    """
    Convert a calendar year to academic year format.

    Args:
        year: Calendar year (e.g., 2020)

    Returns:
        Academic year string (e.g., "2020-2021")
    """
    return f"{year}-{year + 1}"


def find_overlaps_for_coach(
    career_history: List[Dict],
    nmdp_db: Dict[str, List[str]],
    normalizer: SchoolNormalizer,
    year_range_start: int = 2020,
    year_range_end: int = 2026
) -> List[Dict]:
    """
    Find NMDP program overlaps for a single coach's career history.

    Args:
        career_history: List of career stint dictionaries
        nmdp_db: NMDP database (school -> [academic years])
        normalizer: SchoolNormalizer instance
        year_range_start: Earliest year to consider
        year_range_end: Latest year to consider

    Returns:
        List of overlap dictionaries with school, academic_year, coach_position
    """
    overlaps = []

    for stint in career_history:
        school = stint.get("school", "")
        years_str = stint.get("years", "")
        position = stint.get("position", "Unknown")

        # Skip if missing data
        if not school or not years_str:
            continue

        # Check if this is an NFL team (skip - no NMDP overlap possible)
        if normalizer.is_nfl_team(school):
            continue

        # Normalize the school name
        normalized_school, match_type = normalizer.normalize(school)

        # Check if school is in NMDP database
        if normalized_school not in nmdp_db:
            continue

        # Get the years the coach was at this school
        coach_years = parse_year_range(years_str, year_range_end)

        # Filter to configured year range
        coach_years = [y for y in coach_years if year_range_start <= y < year_range_end]

        # Get NMDP program years for this school
        nmdp_years = set(nmdp_db[normalized_school])

        # Find overlaps
        for year in coach_years:
            academic_year = year_to_academic_year(year)
            if academic_year in nmdp_years:
                overlaps.append({
                    "school": normalized_school,
                    "school_original": school,
                    "academic_year": academic_year,
                    "coach_position": position,
                    "match_type": match_type
                })

    return overlaps


def cross_reference_coach(
    coach_data: Dict,
    nmdp_db: Dict[str, List[str]],
    normalizer: SchoolNormalizer,
    config: Dict = None
) -> Dict:
    """
    Cross-reference a single coach's data against NMDP database.

    Args:
        coach_data: Coach data dictionary (from cache)
        nmdp_db: NMDP database
        normalizer: SchoolNormalizer instance
        config: Configuration dict (optional)

    Returns:
        Result dictionary with coach info and overlap findings
    """
    config = config or {}
    year_start = config.get("year_range", {}).get("start", 2020)
    year_end = config.get("year_range", {}).get("end", 2026)

    career_history = coach_data.get("career_history", [])

    overlaps = find_overlaps_for_coach(
        career_history,
        nmdp_db,
        normalizer,
        year_start,
        year_end
    )

    return {
        "coach_name": coach_data.get("name", "Unknown"),
        "current_position": coach_data.get("current_position", "Unknown"),
        "current_school": coach_data.get("current_school", "Unknown"),
        "research_status": coach_data.get("research_status", "Unknown"),
        "career_history": career_history,
        "has_overlap": len(overlaps) > 0,
        "overlaps": overlaps,
        "overlap_count": len(overlaps)
    }


def cross_reference_all_coaches(
    coaches_dir: str,
    nmdp_db_path: str,
    aliases_path: str,
    config_path: str = None
) -> List[Dict]:
    """
    Cross-reference all coaches in a directory against NMDP database.

    Args:
        coaches_dir: Path to directory containing coach JSON files
        nmdp_db_path: Path to GITG database
        aliases_path: Path to school aliases
        config_path: Path to config.json (optional)

    Returns:
        List of cross-reference results for all coaches
    """
    _log_info(f"Loading NMDP database from {nmdp_db_path}")

    # Load databases
    nmdp_db = load_json_file(nmdp_db_path)
    # Convert keys to uppercase for consistent matching
    nmdp_db = {k.upper(): v for k, v in nmdp_db.items()}

    _log_info(f"NMDP database contains {len(nmdp_db)} schools")

    # Load config if provided
    config = {}
    if config_path and os.path.exists(config_path):
        config = load_json_file(config_path)
        _log_debug(f"Loaded config: year_range={config.get('year_range', {})}")

    # Initialize normalizer
    normalizer = SchoolNormalizer(nmdp_db_path, aliases_path)
    _log_info(f"Loaded {len(normalizer.reverse_aliases)} school aliases")

    results = []
    overlaps_found = 0

    # Process each coach file
    if os.path.isdir(coaches_dir):
        files = [f for f in os.listdir(coaches_dir) if f.endswith(".json")]
        _log_info(f"Processing {len(files)} coach files from {coaches_dir}")

        for filename in files:
            filepath = os.path.join(coaches_dir, filename)
            try:
                coach_data = load_json_file(filepath)

                # Handle all_coaches.json (array format)
                if isinstance(coach_data, list):
                    _log_debug(f"Processing combined file {filename} with {len(coach_data)} coaches")
                    for coach in coach_data:
                        result = cross_reference_coach(coach, nmdp_db, normalizer, config)
                        results.append(result)
                        if result["has_overlap"]:
                            overlaps_found += 1
                            _log_debug(f"  Found {result['overlap_count']} overlap(s) for {result['coach_name']}")
                else:
                    result = cross_reference_coach(coach_data, nmdp_db, normalizer, config)
                    results.append(result)
                    if result["has_overlap"]:
                        overlaps_found += 1
                        _log_debug(f"  Found {result['overlap_count']} overlap(s) for {result['coach_name']}")

            except Exception as e:
                _log_warning(f"Error processing {filename}: {e}")

    _log_info(f"Cross-reference complete: {len(results)} coaches, {overlaps_found} with overlaps")

    return results


def format_overlaps_summary(overlaps: List[Dict]) -> str:
    """
    Format overlaps into a human-readable summary string.

    Args:
        overlaps: List of overlap dictionaries

    Returns:
        Formatted string like "Texas State (2021-2022), Ohio State (2020-2021)"
    """
    if not overlaps:
        return ""

    # Group by school
    by_school = {}
    for overlap in overlaps:
        school = overlap["school"]
        year = overlap["academic_year"]
        if school not in by_school:
            by_school[school] = []
        by_school[school].append(year)

    # Format each school
    parts = []
    for school, years in by_school.items():
        years_str = ", ".join(sorted(years))
        parts.append(f"{school} ({years_str})")

    return "; ".join(parts)


if __name__ == "__main__":
    """CLI usage: python cross_reference.py <coaches_dir> [nmdp_db_path] [aliases_path] [config_path]"""

    if len(sys.argv) < 2:
        print("Usage: python cross_reference.py <coaches_dir> [nmdp_db_path] [aliases_path] [config_path]")
        print("  coaches_dir: Directory containing coach JSON files")
        print("  nmdp_db_path: Path to gitg_school_years.json")
        print("  aliases_path: Path to school_aliases.json")
        print("  config_path: Path to config.json")
        sys.exit(1)

    coaches_dir = sys.argv[1]

    # Default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_nmdp_path = os.path.join(script_dir, "..", "data", "gitg_school_years.json")
    default_aliases_path = os.path.join(script_dir, "..", "data", "school_aliases.json")
    default_config_path = os.path.join(script_dir, "..", "config.json")

    nmdp_path = sys.argv[2] if len(sys.argv) > 2 else default_nmdp_path
    aliases_path = sys.argv[3] if len(sys.argv) > 3 else default_aliases_path
    config_path = sys.argv[4] if len(sys.argv) > 4 else default_config_path

    try:
        results = cross_reference_all_coaches(coaches_dir, nmdp_path, aliases_path, config_path)

        # Print summary
        total_coaches = len(results)
        coaches_with_overlap = sum(1 for r in results if r["has_overlap"])

        print(f"\nCross-Reference Results")
        print(f"=" * 50)
        print(f"Total coaches processed: {total_coaches}")
        print(f"Coaches with NMDP overlap: {coaches_with_overlap}")
        print()

        if coaches_with_overlap > 0:
            print("Overlaps found:")
            for result in results:
                if result["has_overlap"]:
                    print(f"\n  {result['coach_name']} ({result['current_position']})")
                    for overlap in result["overlaps"]:
                        print(f"    - {overlap['school']}, {overlap['academic_year']}")
                        print(f"      Position at time: {overlap['coach_position']}")

        # Output as JSON
        print("\n\nJSON Output:")
        print(json.dumps(results, indent=2))

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
