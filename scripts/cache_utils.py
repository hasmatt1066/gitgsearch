"""
cache_utils.py - Cache management utilities

Provides functions for checking cache staleness, completeness, and status.
Used by the orchestrator to determine when to refresh data.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def load_json_file(filepath: str) -> Optional[Dict]:
    """Load a JSON file and return its contents, or None if not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_config(config_path: str = None) -> Dict:
    """Load configuration file with defaults."""
    if config_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "..", "config.json")

    config = load_json_file(config_path)
    if config is None:
        # Return defaults if config not found
        return {
            "cache_staleness_days": 30,
            "year_range": {"start": 2020, "end": 2026}
        }
    return config


def normalize_school_dir_name(school_name: str) -> str:
    """Convert school name to directory name format."""
    return school_name.lower().replace(" ", "_").replace("-", "_")


def get_cache_path(school_name: str, cache_base_dir: str = None) -> str:
    """Get the cache directory path for a school."""
    if cache_base_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_base_dir = os.path.join(script_dir, "..", "cache")

    school_dir = normalize_school_dir_name(school_name)
    return os.path.join(cache_base_dir, school_dir)


def get_roster_path(school_name: str, cache_base_dir: str = None) -> str:
    """Get the roster.json path for a school."""
    cache_path = get_cache_path(school_name, cache_base_dir)
    return os.path.join(cache_path, "roster.json")


def get_coaches_dir(school_name: str, cache_base_dir: str = None) -> str:
    """Get the coaches directory path for a school."""
    cache_path = get_cache_path(school_name, cache_base_dir)
    return os.path.join(cache_path, "coaches")


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def get_cache_age_days(roster_path: str) -> Optional[int]:
    """
    Get the age of cached data in days.

    Args:
        roster_path: Path to roster.json file

    Returns:
        Number of days since data was fetched, or None if cannot determine
    """
    roster = load_json_file(roster_path)
    if roster is None:
        return None

    fetched_date_str = roster.get("fetched_date")
    if not fetched_date_str:
        return None

    fetched_date = parse_date(fetched_date_str)
    if fetched_date is None:
        return None

    age = datetime.now() - fetched_date
    return age.days


def is_cache_stale(roster_path: str, staleness_days: int = 30) -> bool:
    """
    Check if cached data is stale (older than staleness_days).

    Args:
        roster_path: Path to roster.json file
        staleness_days: Number of days after which cache is considered stale

    Returns:
        True if cache is stale or doesn't exist, False if fresh
    """
    age = get_cache_age_days(roster_path)
    if age is None:
        return True  # No cache or invalid date = stale
    return age > staleness_days


def cache_exists(school_name: str, cache_base_dir: str = None) -> bool:
    """Check if any cache exists for a school."""
    roster_path = get_roster_path(school_name, cache_base_dir)
    return os.path.exists(roster_path)


def get_cached_coaches(school_name: str, cache_base_dir: str = None) -> List[Dict]:
    """
    Get list of coaches with cached career data.

    Handles two cache formats:
    1. Individual files: coaches/dan_lanning.json, coaches/drew_mehringer.json, etc.
    2. Combined file: coaches/all_coaches.json (array of coach objects)

    Args:
        school_name: Name of the school
        cache_base_dir: Base cache directory

    Returns:
        List of coach dictionaries with at least 'name' field
    """
    coaches_dir = get_coaches_dir(school_name, cache_base_dir)
    if not os.path.exists(coaches_dir):
        return []

    coaches = []

    # Check for combined all_coaches.json file first
    all_coaches_path = os.path.join(coaches_dir, "all_coaches.json")
    if os.path.exists(all_coaches_path):
        data = load_json_file(all_coaches_path)
        if data and isinstance(data, list):
            return data

    # Otherwise, load individual coach files
    for filename in os.listdir(coaches_dir):
        if filename.endswith(".json") and filename != "all_coaches.json":
            filepath = os.path.join(coaches_dir, filename)
            coach_data = load_json_file(filepath)
            if coach_data and isinstance(coach_data, dict):
                coaches.append(coach_data)

    return coaches


def get_cached_coach_names(school_name: str, cache_base_dir: str = None) -> List[str]:
    """
    Get list of coach names with cached career data.

    Args:
        school_name: Name of the school
        cache_base_dir: Base cache directory

    Returns:
        List of coach names (normalized to lowercase with underscores)
    """
    coaches = get_cached_coaches(school_name, cache_base_dir)
    names = []
    for coach in coaches:
        name = coach.get("name", "")
        if name:
            # Normalize to match file naming convention
            normalized = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
            names.append(normalized)
    return names


def get_roster_coaches(school_name: str, cache_base_dir: str = None) -> List[Dict]:
    """
    Get list of coaches from roster.json.

    Args:
        school_name: Name of the school
        cache_base_dir: Base cache directory

    Returns:
        List of coach dictionaries from roster, or empty list if not found
    """
    roster_path = get_roster_path(school_name, cache_base_dir)
    roster = load_json_file(roster_path)
    if roster is None:
        return []
    return roster.get("coaches", [])


def get_cache_completeness(school_name: str, cache_base_dir: str = None) -> Dict:
    """
    Check how complete the cache is for a school.

    Args:
        school_name: Name of the school
        cache_base_dir: Base cache directory

    Returns:
        Dictionary with completeness information:
        - has_roster: bool
        - roster_coach_count: int
        - cached_coach_count: int
        - missing_coaches: list of coach names without career data
        - completion_percentage: float (0-100)
    """
    roster_coaches = get_roster_coaches(school_name, cache_base_dir)
    cached_coach_names = set(get_cached_coach_names(school_name, cache_base_dir))

    # Normalize roster coach names to match file naming convention
    def normalize_name(name: str) -> str:
        return name.lower().replace(" ", "_").replace("'", "").replace("-", "_")

    roster_names = {normalize_name(c.get("name", "")): c.get("name", "") for c in roster_coaches}

    missing = []
    for normalized, original in roster_names.items():
        if normalized not in cached_coach_names:
            missing.append(original)

    roster_count = len(roster_coaches)
    cached_count = len(cached_coach_names)

    # Calculate completion percentage
    if roster_count == 0:
        completion = 0.0
    else:
        completion = (cached_count / roster_count) * 100

    return {
        "has_roster": roster_count > 0,
        "roster_coach_count": roster_count,
        "cached_coach_count": cached_count,
        "missing_coaches": missing,
        "completion_percentage": round(completion, 1)
    }


def get_cache_status(school_name: str, cache_base_dir: str = None, config: Dict = None) -> Dict:
    """
    Get comprehensive cache status for a school.

    Args:
        school_name: Name of the school
        cache_base_dir: Base cache directory
        config: Configuration dictionary (optional, will load if not provided)

    Returns:
        Dictionary with full cache status:
        - exists: bool
        - school_name: str
        - cache_path: str
        - fetched_date: str or None
        - age_days: int or None
        - staleness_days: int (from config)
        - is_stale: bool
        - completeness: dict (from get_cache_completeness)
        - recommendation: str ("use_cache", "refresh_recommended", "no_cache")
    """
    if config is None:
        config = load_config()

    staleness_days = config.get("cache_staleness_days", 30)

    roster_path = get_roster_path(school_name, cache_base_dir)
    cache_path = get_cache_path(school_name, cache_base_dir)

    exists = os.path.exists(roster_path)

    if not exists:
        return {
            "exists": False,
            "school_name": school_name,
            "cache_path": cache_path,
            "fetched_date": None,
            "age_days": None,
            "staleness_days": staleness_days,
            "is_stale": True,
            "completeness": {
                "has_roster": False,
                "roster_coach_count": 0,
                "cached_coach_count": 0,
                "missing_coaches": [],
                "completion_percentage": 0.0
            },
            "recommendation": "no_cache"
        }

    roster = load_json_file(roster_path)
    fetched_date = roster.get("fetched_date") if roster else None
    age_days = get_cache_age_days(roster_path)
    is_stale = is_cache_stale(roster_path, staleness_days)
    completeness = get_cache_completeness(school_name, cache_base_dir)

    # Determine recommendation
    if is_stale:
        recommendation = "refresh_recommended"
    elif completeness["completion_percentage"] < 100:
        recommendation = "resume_research"
    else:
        recommendation = "use_cache"

    return {
        "exists": True,
        "school_name": school_name,
        "cache_path": cache_path,
        "fetched_date": fetched_date,
        "age_days": age_days,
        "staleness_days": staleness_days,
        "is_stale": is_stale,
        "completeness": completeness,
        "recommendation": recommendation
    }


def format_cache_status(status: Dict) -> str:
    """
    Format cache status as human-readable string.

    Args:
        status: Dictionary from get_cache_status()

    Returns:
        Formatted multi-line string for display
    """
    lines = []
    lines.append(f"Cache Status for: {status['school_name']}")
    lines.append("-" * 50)

    if not status["exists"]:
        lines.append("No cached data found.")
        lines.append(f"Cache path: {status['cache_path']}")
        return "\n".join(lines)

    lines.append(f"Cache path: {status['cache_path']}")
    lines.append(f"Fetched date: {status['fetched_date']}")
    lines.append(f"Age: {status['age_days']} days (stale after {status['staleness_days']} days)")
    lines.append(f"Status: {'STALE' if status['is_stale'] else 'FRESH'}")
    lines.append("")

    comp = status["completeness"]
    lines.append(f"Roster coaches: {comp['roster_coach_count']}")
    lines.append(f"Coaches with career data: {comp['cached_coach_count']}")
    lines.append(f"Completion: {comp['completion_percentage']}%")

    if comp["missing_coaches"]:
        lines.append("")
        lines.append("Missing career data for:")
        for coach in comp["missing_coaches"][:10]:  # Limit to 10
            lines.append(f"  - {coach}")
        if len(comp["missing_coaches"]) > 10:
            lines.append(f"  ... and {len(comp['missing_coaches']) - 10} more")

    lines.append("")
    rec_messages = {
        "use_cache": "Recommendation: Use cached data (fresh and complete)",
        "refresh_recommended": "Recommendation: Refresh data (cache is stale)",
        "resume_research": "Recommendation: Resume career research (incomplete)",
        "no_cache": "Recommendation: Fetch new data (no cache exists)"
    }
    lines.append(rec_messages.get(status["recommendation"], ""))

    return "\n".join(lines)


if __name__ == "__main__":
    """CLI usage: python cache_utils.py <school_name> [cache_dir]"""

    if len(sys.argv) < 2:
        print("Usage: python cache_utils.py <school_name> [cache_dir]")
        print("  school_name: Name of school to check cache for")
        print("  cache_dir: Base cache directory (default: ../cache)")
        print()
        print("Examples:")
        print("  python cache_utils.py 'University of Oregon'")
        print("  python cache_utils.py 'CU Boulder'")
        sys.exit(1)

    school_name = sys.argv[1]
    cache_dir = sys.argv[2] if len(sys.argv) > 2 else None

    status = get_cache_status(school_name, cache_dir)
    print(format_cache_status(status))

    # Exit with code based on recommendation
    if status["recommendation"] == "use_cache":
        sys.exit(0)
    elif status["recommendation"] in ["refresh_recommended", "resume_research"]:
        sys.exit(1)
    else:
        sys.exit(2)
