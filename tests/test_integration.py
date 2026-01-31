"""
test_integration.py - Integration tests for NMDP Coach Cross-Reference System

These tests run the full pipeline on known data and verify expected results.
Run with: python3 tests/test_integration.py
Or:       python3 -m pytest tests/test_integration.py -v
"""

import sys
import os
import json
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from cross_reference import (
    cross_reference_all_coaches,
    cross_reference_coach,
    parse_year_range,
    year_to_academic_year,
    load_json_file
)
from normalize import SchoolNormalizer, normalize_school_name
from generate_csv import generate_csv_report, generate_summary_stats, format_career_history
from cache_utils import get_cache_status, get_cache_completeness, is_cache_stale

# Paths relative to test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CACHE_DIR = os.path.join(PROJECT_DIR, "cache")

NMDP_DB_PATH = os.path.join(DATA_DIR, "gitg_school_years.json")
ALIASES_PATH = os.path.join(DATA_DIR, "school_aliases.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")


class TestOregonIntegration:
    """
    Integration tests using University of Oregon as test case.

    Known expected results (as of 2026-01-26):
    - 24 coaches in cache
    - 8 coaches with NMDP overlaps
    - Specific overlaps verified manually
    """

    SCHOOL_NAME = "University of Oregon"
    EXPECTED_COACH_COUNT = 24
    EXPECTED_OVERLAP_COUNT = 8

    # Known overlaps we expect to find
    EXPECTED_OVERLAPS = {
        "A'lique Terry": ["UNIVERSITY OF HAWAII AT MANOA"],
        "Brian Michalowski": ["OREGON STATE UNIVERSITY", "UNIVERSITY OF COLORADO-BOULDER"],
        "Chris Hampton": ["TULANE UNIVERSITY"],
        "Connor Boyd": ["UNIVERSITY OF COLORADO-BOULDER"],
        "Koa Ka'ai": ["UNIVERSITY OF HAWAII AT MANOA"],
        "Kyle Cogan": ["BENEDICTINE COLLEGE"],
        "Ross Douglas": ["UNIVERSITY OF RICHMOND"],
        "Zach Tinker": ["CENTRAL WASHINGTON UNIVERSITY"],
    }

    # Coaches we expect to have NO overlaps
    EXPECTED_NO_OVERLAPS = [
        "Dan Lanning",  # Oregon and Georgia - neither in NMDP during his tenure
        "Joe Lorig",    # Oregon and Penn State
    ]

    def test_oregon_cache_exists(self):
        """Oregon cache should exist and be complete."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")
        assert os.path.exists(coaches_dir), f"Oregon cache not found at {coaches_dir}"

    def test_cross_reference_coach_count(self):
        """Cross-reference should process all 24 Oregon coaches."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        assert len(results) == self.EXPECTED_COACH_COUNT, \
            f"Expected {self.EXPECTED_COACH_COUNT} coaches, got {len(results)}"

    def test_overlap_count(self):
        """Should find exactly 8 coaches with NMDP overlaps."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        coaches_with_overlap = [r for r in results if r["has_overlap"]]

        assert len(coaches_with_overlap) == self.EXPECTED_OVERLAP_COUNT, \
            f"Expected {self.EXPECTED_OVERLAP_COUNT} overlaps, got {len(coaches_with_overlap)}"

    def test_specific_overlaps_found(self):
        """Verify specific known overlaps are detected."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        # Build lookup by coach name
        results_by_name = {r["coach_name"]: r for r in results}

        for coach_name, expected_schools in self.EXPECTED_OVERLAPS.items():
            assert coach_name in results_by_name, f"Coach {coach_name} not found in results"

            result = results_by_name[coach_name]
            assert result["has_overlap"], f"{coach_name} should have overlap but doesn't"

            found_schools = [o["school"] for o in result["overlaps"]]
            for expected_school in expected_schools:
                assert expected_school in found_schools, \
                    f"{coach_name} missing expected overlap with {expected_school}. Found: {found_schools}"

    def test_no_false_positives(self):
        """Verify coaches without overlaps don't have false positives."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        results_by_name = {r["coach_name"]: r for r in results}

        for coach_name in self.EXPECTED_NO_OVERLAPS:
            if coach_name in results_by_name:
                result = results_by_name[coach_name]
                assert not result["has_overlap"], \
                    f"{coach_name} should NOT have overlap but found: {result.get('overlaps', [])}"

    def test_summary_stats(self):
        """Test summary statistics generation."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        stats = generate_summary_stats(results)

        assert stats["total_coaches"] == self.EXPECTED_COACH_COUNT
        assert stats["coaches_with_overlap"] == self.EXPECTED_OVERLAP_COUNT
        assert stats["coaches_without_overlap"] == self.EXPECTED_COACH_COUNT - self.EXPECTED_OVERLAP_COUNT
        assert "data_quality" in stats
        assert stats["data_quality"]["verified"] > 0


class TestColoradoIntegration:
    """
    Integration tests using University of Colorado as test case.

    Colorado uses the all_coaches.json format (single file with array).
    """

    SCHOOL_NAME = "University of Colorado"
    EXPECTED_COACH_COUNT = 25

    def test_colorado_cache_exists(self):
        """Colorado cache should exist."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_colorado", "coaches")
        assert os.path.exists(coaches_dir), f"Colorado cache not found"

    def test_all_coaches_json_format(self):
        """Colorado uses all_coaches.json format - verify it's handled."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_colorado", "coaches")
        all_coaches_path = os.path.join(coaches_dir, "all_coaches.json")

        assert os.path.exists(all_coaches_path), "all_coaches.json not found"

        data = load_json_file(all_coaches_path)
        assert isinstance(data, list), "all_coaches.json should contain a list"
        assert len(data) == self.EXPECTED_COACH_COUNT, \
            f"Expected {self.EXPECTED_COACH_COUNT} coaches, got {len(data)}"

    def test_cross_reference_handles_combined_format(self):
        """Cross-reference should handle all_coaches.json format."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_colorado", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        assert len(results) == self.EXPECTED_COACH_COUNT, \
            f"Expected {self.EXPECTED_COACH_COUNT} coaches from combined file, got {len(results)}"


class TestNormalization:
    """Test school name normalization end-to-end."""

    def test_alias_resolution(self):
        """Test that aliases resolve correctly."""
        normalizer = SchoolNormalizer(NMDP_DB_PATH, ALIASES_PATH)

        test_cases = [
            ("CU Boulder", "UNIVERSITY OF COLORADO-BOULDER"),
            ("University of Colorado", "UNIVERSITY OF COLORADO-BOULDER"),
            ("Hawaii", "UNIVERSITY OF HAWAII AT MANOA"),
            ("University of Hawaii", "UNIVERSITY OF HAWAII AT MANOA"),
            ("Oregon State", "OREGON STATE UNIVERSITY"),
            ("Tulane", "TULANE UNIVERSITY"),
        ]

        for input_name, expected in test_cases:
            result, match_type = normalizer.normalize(input_name)
            assert result == expected, \
                f"'{input_name}' should normalize to '{expected}', got '{result}'"

    def test_no_fuzzy_false_positives(self):
        """Verify fuzzy matching is disabled - no false positives."""
        normalizer = SchoolNormalizer(NMDP_DB_PATH, ALIASES_PATH)

        # These should NOT match anything (fuzzy matching disabled)
        no_match_cases = [
            "University of Oregon",  # Not in NMDP database
            "Random University",
            "Fake State College",
        ]

        for input_name in no_match_cases:
            result, match_type = normalizer.normalize(input_name)
            # Should return the cleaned name, not a fuzzy match
            assert match_type in ["none", "exact"], \
                f"'{input_name}' should not fuzzy match, got match_type='{match_type}'"


class TestCacheUtilities:
    """Test cache utility functions."""

    def test_cache_status_oregon(self):
        """Test cache status for Oregon."""
        status = get_cache_status("University of Oregon", CACHE_DIR)

        assert status["exists"] == True
        assert status["fetched_date"] is not None
        assert status["completeness"]["has_roster"] == True
        assert status["completeness"]["roster_coach_count"] > 0

    def test_cache_status_nonexistent(self):
        """Test cache status for non-existent school."""
        status = get_cache_status("Fake University", CACHE_DIR)

        assert status["exists"] == False
        assert status["recommendation"] == "no_cache"


class TestCSVGeneration:
    """Test CSV output generation."""

    def test_csv_generation(self):
        """Test that CSV can be generated without errors."""
        coaches_dir = os.path.join(CACHE_DIR, "university_of_oregon", "coaches")

        results = cross_reference_all_coaches(
            coaches_dir, NMDP_DB_PATH, ALIASES_PATH, CONFIG_PATH
        )

        # Generate to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            config = load_json_file(CONFIG_PATH)
            output_path = generate_csv_report(results, temp_path, config)

            assert os.path.exists(output_path)

            # Verify file has content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 1, "CSV should have header + data rows"

                # Check header
                header = lines[0].strip()
                assert "Coach Name" in header
                assert "NMDP Overlap" in header
                assert "Data Quality" in header
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_career_history_formatting(self):
        """Test career history string formatting."""
        career = [
            {"school": "Oregon", "years": "2022-2026"},
            {"school": "Georgia", "years": "2019-2021"},
        ]

        result = format_career_history(career, year_start=2020)

        assert "Oregon" in result
        assert "Georgia" in result
        assert "2022-2026" in result or "2022-" in result


def run_tests():
    """Run all tests manually (without pytest)."""
    test_classes = [
        TestOregonIntegration,
        TestColoradoIntegration,
        TestNormalization,
        TestCacheUtilities,
        TestCSVGeneration,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()
        for method_name in sorted(dir(instance)):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"  PASS: {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  FAIL: {method_name}")
                    print(f"        {e}")
                    failed += 1
                    errors.append((test_class.__name__, method_name, str(e)))
                except Exception as e:
                    print(f"  ERROR: {method_name}")
                    print(f"         {type(e).__name__}: {e}")
                    failed += 1
                    errors.append((test_class.__name__, method_name, f"{type(e).__name__}: {e}"))

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for cls, method, error in errors:
            print(f"  {cls}.{method}: {error}")

    return failed == 0


if __name__ == "__main__":
    print("Running Integration Tests for NMDP Coach Cross-Reference System")
    print("=" * 60)

    success = run_tests()
    sys.exit(0 if success else 1)
