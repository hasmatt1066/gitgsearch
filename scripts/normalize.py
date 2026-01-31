"""
normalize.py - School name normalization

Canonicalizes school names to match the NMDP GITG database format.
Uses alias lookup, direct matching, and optional fuzzy matching.
"""

import json
import re
import sys
from typing import Optional, Dict, List, Set, Tuple
from difflib import SequenceMatcher


def load_json_file(filepath: str) -> Dict:
    """Load a JSON file and return its contents."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_school_name(name: str) -> str:
    """
    Clean and standardize a school name for comparison.

    - Convert to uppercase
    - Remove extra whitespace
    - Remove common prefixes/suffixes that vary
    """
    name = name.upper().strip()
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name


def build_reverse_alias_map(aliases: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Build a reverse mapping from aliases to canonical names.

    Args:
        aliases: Dict with canonical names as keys, lists of aliases as values

    Returns:
        Dict mapping each alias (uppercase) to its canonical name
    """
    reverse_map = {}
    for canonical, alias_list in aliases.items():
        if canonical.startswith("_"):  # Skip comment fields
            continue
        canonical_upper = canonical.upper()
        for alias in alias_list:
            reverse_map[alias.upper()] = canonical_upper
    return reverse_map


def fuzzy_match(name: str, candidates: Set[str], threshold: float = 0.85) -> Optional[Tuple[str, float]]:
    """
    Find the best fuzzy match for a name among candidates.

    Args:
        name: The name to match
        candidates: Set of possible matches
        threshold: Minimum similarity ratio (0-1)

    Returns:
        Tuple of (best_match, score) if found above threshold, else None
    """
    best_match = None
    best_score = 0

    name_upper = name.upper()

    for candidate in candidates:
        # Calculate similarity ratio
        score = SequenceMatcher(None, name_upper, candidate.upper()).ratio()

        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate

    if best_match:
        return (best_match, best_score)
    return None


class SchoolNormalizer:
    """
    Normalizes school names to canonical NMDP database format.
    """

    def __init__(self, nmdp_db_path: str, aliases_path: str):
        """
        Initialize the normalizer.

        Args:
            nmdp_db_path: Path to gitg_school_years.json
            aliases_path: Path to school_aliases.json
        """
        self.nmdp_db = load_json_file(nmdp_db_path)
        self.aliases = load_json_file(aliases_path)

        # Build set of canonical NMDP school names (uppercase)
        self.nmdp_schools = set(k.upper() for k in self.nmdp_db.keys())

        # Build reverse alias map
        self.reverse_aliases = build_reverse_alias_map(self.aliases)

        # Track fuzzy matches for logging/review
        self.fuzzy_match_log = []

    def normalize(self, name: str, use_fuzzy: bool = False, fuzzy_threshold: float = 0.85) -> Tuple[str, str]:
        """
        Normalize a school name to canonical NMDP format.

        Args:
            name: School name to normalize
            use_fuzzy: Whether to attempt fuzzy matching as fallback
            fuzzy_threshold: Minimum similarity for fuzzy match

        Returns:
            Tuple of (normalized_name, match_type)
            match_type is one of: "exact", "alias", "fuzzy", "none"
        """
        cleaned = clean_school_name(name)

        # 1. Direct match to NMDP database
        if cleaned in self.nmdp_schools:
            return (cleaned, "exact")

        # 2. Check reverse alias map
        if cleaned in self.reverse_aliases:
            canonical = self.reverse_aliases[cleaned]
            return (canonical, "alias")

        # 3. Try fuzzy matching if enabled
        if use_fuzzy:
            result = fuzzy_match(cleaned, self.nmdp_schools, fuzzy_threshold)
            if result:
                match, score = result
                self.fuzzy_match_log.append({
                    "original": name,
                    "matched_to": match,
                    "score": score
                })
                return (match, "fuzzy")

        # 4. No match found - return original (uppercase)
        return (cleaned, "none")

    def normalize_batch(self, names: List[str], use_fuzzy: bool = True) -> List[Dict]:
        """
        Normalize a batch of school names.

        Args:
            names: List of school names
            use_fuzzy: Whether to use fuzzy matching

        Returns:
            List of dicts with original, normalized, and match_type
        """
        results = []
        for name in names:
            normalized, match_type = self.normalize(name, use_fuzzy)
            results.append({
                "original": name,
                "normalized": normalized,
                "match_type": match_type,
                "in_nmdp_db": normalized in self.nmdp_schools
            })
        return results

    def get_fuzzy_match_log(self) -> List[Dict]:
        """Return log of fuzzy matches for review."""
        return self.fuzzy_match_log

    def clear_fuzzy_match_log(self):
        """Clear the fuzzy match log."""
        self.fuzzy_match_log = []

    def is_nfl_team(self, name: str) -> bool:
        """
        Check if a name appears to be an NFL team.

        NFL teams won't be in the NMDP database, so this helps
        distinguish "no match because NFL" from "no match because unknown college".
        """
        nfl_keywords = [
            "49ERS", "BEARS", "BENGALS", "BILLS", "BRONCOS", "BROWNS",
            "BUCCANEERS", "CARDINALS", "CHARGERS", "CHIEFS", "COLTS",
            "COMMANDERS", "COWBOYS", "DOLPHINS", "EAGLES", "FALCONS",
            "GIANTS", "JAGUARS", "JETS", "LIONS", "PACKERS", "PANTHERS",
            "PATRIOTS", "RAIDERS", "RAMS", "RAVENS", "SAINTS", "SEAHAWKS",
            "STEELERS", "TEXANS", "TITANS", "VIKINGS",
            "NFL", "NATIONAL FOOTBALL LEAGUE"
        ]

        nfl_cities = [
            "ARIZONA", "ATLANTA", "BALTIMORE", "BUFFALO", "CAROLINA",
            "CHICAGO", "CINCINNATI", "CLEVELAND", "DALLAS", "DENVER",
            "DETROIT", "GREEN BAY", "HOUSTON", "INDIANAPOLIS", "JACKSONVILLE",
            "KANSAS CITY", "LAS VEGAS", "LOS ANGELES", "MIAMI", "MINNESOTA",
            "NEW ENGLAND", "NEW ORLEANS", "NEW YORK", "PHILADELPHIA",
            "PITTSBURGH", "SAN FRANCISCO", "SEATTLE", "TAMPA BAY",
            "TENNESSEE", "WASHINGTON"
        ]

        name_upper = name.upper()

        # Check for NFL team names
        for keyword in nfl_keywords:
            if keyword in name_upper:
                # Make sure it's not a college with similar name
                if "UNIVERSITY" not in name_upper and "COLLEGE" not in name_upper:
                    return True

        # Check for NFL city + common suffix patterns
        for city in nfl_cities:
            if name_upper.startswith(city):
                remainder = name_upper[len(city):].strip()
                for keyword in nfl_keywords:
                    if keyword in remainder:
                        return True

        return False


def normalize_school_name(name: str, aliases: Dict, nmdp_schools: Set) -> str:
    """
    Standalone function to normalize a single school name.

    This is a simpler interface for use in cross_reference.py.

    Args:
        name: School name to normalize
        aliases: Alias dictionary (canonical -> [aliases])
        nmdp_schools: Set of canonical NMDP school names

    Returns:
        Normalized school name (uppercase)
    """
    cleaned = clean_school_name(name)

    # Direct match
    if cleaned in nmdp_schools:
        return cleaned

    # Build reverse alias map and check
    reverse_aliases = build_reverse_alias_map(aliases)
    if cleaned in reverse_aliases:
        return reverse_aliases[cleaned]

    # Fuzzy match as fallback
    result = fuzzy_match(cleaned, nmdp_schools, 0.85)
    if result:
        return result[0]

    # No match - return cleaned original
    return cleaned


if __name__ == "__main__":
    """CLI usage: python normalize.py <school_name> [nmdp_db_path] [aliases_path]"""
    import os

    if len(sys.argv) < 2:
        print("Usage: python normalize.py <school_name> [nmdp_db_path] [aliases_path]")
        print("  school_name: Name to normalize")
        print("  nmdp_db_path: Path to gitg_school_years.json (default: ../data/gitg_school_years.json)")
        print("  aliases_path: Path to school_aliases.json (default: ../data/school_aliases.json)")
        sys.exit(1)

    school_name = sys.argv[1]

    # Default paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_nmdp_path = os.path.join(script_dir, "..", "data", "gitg_school_years.json")
    default_aliases_path = os.path.join(script_dir, "..", "data", "school_aliases.json")

    nmdp_path = sys.argv[2] if len(sys.argv) > 2 else default_nmdp_path
    aliases_path = sys.argv[3] if len(sys.argv) > 3 else default_aliases_path

    try:
        normalizer = SchoolNormalizer(nmdp_path, aliases_path)
        normalized, match_type = normalizer.normalize(school_name)

        print(f"Original: {school_name}")
        print(f"Normalized: {normalized}")
        print(f"Match type: {match_type}")
        print(f"In NMDP database: {normalized in normalizer.nmdp_schools}")
        print(f"Is NFL team: {normalizer.is_nfl_team(school_name)}")

        if match_type == "fuzzy":
            log = normalizer.get_fuzzy_match_log()
            if log:
                print(f"Fuzzy match score: {log[-1]['score']:.2%}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
