"""
test_cross_reference.py - Unit tests for cross_reference.py

Run with: python3 -m pytest tests/test_cross_reference.py -v
Or:       python3 tests/test_cross_reference.py
"""

import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from cross_reference import parse_year_range, year_to_academic_year


class TestParseYearRange:
    """Tests for parse_year_range function."""

    def test_standard_range_inclusive(self):
        """End year should be INCLUSIVE - '2020-2022' includes 2020, 2021, AND 2022."""
        result = parse_year_range("2020-2022")
        assert result == [2020, 2021, 2022], f"Expected [2020, 2021, 2022], got {result}"

    def test_single_season_range(self):
        """'2023-2023' should return just [2023]."""
        result = parse_year_range("2023-2023")
        assert result == [2023], f"Expected [2023], got {result}"

    def test_two_season_range(self):
        """'2021-2022' should return [2021, 2022]."""
        result = parse_year_range("2021-2022")
        assert result == [2021, 2022], f"Expected [2021, 2022], got {result}"

    def test_dan_lanning_georgia(self):
        """Real example: Dan Lanning at Georgia '2019-2021' coached 3 seasons."""
        result = parse_year_range("2019-2021")
        assert result == [2019, 2020, 2021], f"Expected [2019, 2020, 2021], got {result}"

    def test_present_excludes_current_year(self):
        """'2024-present' with current_year=2026 should give [2024, 2025]."""
        result = parse_year_range("2024-present", current_year=2026)
        assert result == [2024, 2025], f"Expected [2024, 2025], got {result}"

    def test_present_single_season(self):
        """'2025-present' with current_year=2026 should give [2025]."""
        result = parse_year_range("2025-present", current_year=2026)
        assert result == [2025], f"Expected [2025], got {result}"

    def test_present_with_spaces(self):
        """Should handle spaces around dash."""
        result = parse_year_range("2024 - present", current_year=2026)
        assert result == [2024, 2025], f"Expected [2024, 2025], got {result}"

    def test_case_insensitive_present(self):
        """Should handle 'Present' and 'PRESENT'."""
        result1 = parse_year_range("2024-Present", current_year=2026)
        result2 = parse_year_range("2024-PRESENT", current_year=2026)
        assert result1 == [2024, 2025]
        assert result2 == [2024, 2025]

    def test_single_year_no_range(self):
        """Single year '2023' should return [2023]."""
        result = parse_year_range("2023")
        assert result == [2023], f"Expected [2023], got {result}"

    def test_invalid_format_returns_empty(self):
        """Invalid format should return empty list."""
        assert parse_year_range("invalid") == []
        assert parse_year_range("") == []
        assert parse_year_range("twenty-twenty") == []

    def test_whitespace_handling(self):
        """Should handle leading/trailing whitespace."""
        result = parse_year_range("  2020-2022  ")
        assert result == [2020, 2021, 2022]


class TestYearToAcademicYear:
    """Tests for year_to_academic_year function."""

    def test_standard_conversion(self):
        """2020 should map to '2020-2021'."""
        assert year_to_academic_year(2020) == "2020-2021"
        assert year_to_academic_year(2021) == "2021-2022"
        assert year_to_academic_year(2022) == "2022-2023"

    def test_matches_nmdp_format(self):
        """Output should match NMDP database format exactly."""
        # NMDP uses format like "2021-2022"
        result = year_to_academic_year(2021)
        assert result == "2021-2022"
        assert "-" in result
        assert len(result) == 9  # "YYYY-YYYY"


class TestIntegration:
    """Integration tests combining parse and convert."""

    def test_coach_at_school_matches_nmdp(self):
        """
        Simulate: Coach at School X from 2020-2022.
        NMDP had program at School X in 2021-2022.
        Should find overlap.
        """
        coach_years_str = "2020-2022"
        nmdp_years = ["2020-2021", "2021-2022", "2022-2023"]

        parsed_years = parse_year_range(coach_years_str)
        coach_academic_years = [year_to_academic_year(y) for y in parsed_years]

        # Check for overlap
        overlap = set(coach_academic_years) & set(nmdp_years)

        assert "2020-2021" in overlap
        assert "2021-2022" in overlap
        assert "2022-2023" in overlap
        assert len(overlap) == 3

    def test_no_overlap_when_years_dont_match(self):
        """
        Coach at School X from 2020-2021.
        NMDP had program in 2023-2024.
        Should NOT find overlap.
        """
        coach_years_str = "2020-2021"
        nmdp_years = ["2023-2024"]

        parsed_years = parse_year_range(coach_years_str)
        coach_academic_years = [year_to_academic_year(y) for y in parsed_years]

        overlap = set(coach_academic_years) & set(nmdp_years)
        assert len(overlap) == 0


def run_tests():
    """Run all tests manually (without pytest)."""
    test_classes = [TestParseYearRange, TestYearToAcademicYear, TestIntegration]

    passed = 0
    failed = 0

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"  PASS: {test_class.__name__}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  FAIL: {test_class.__name__}.{method_name}")
                    print(f"        {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ERROR: {test_class.__name__}.{method_name}")
                    print(f"         {e}")
                    failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("Running cross_reference.py tests...\n")
    success = run_tests()
    sys.exit(0 if success else 1)
