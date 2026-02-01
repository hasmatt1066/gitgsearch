"""
google_sheets_export.py - Export coach cross-reference results to Google Sheets

Exports the master report data to a Google Sheet with:
- Master Results tab: All coaches from all schools
- Territory tabs: One tab per NMDP territory
- Formatting with color-coded overlap highlighting
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional
from datetime import datetime
import os
import sys
import json
import time

# Load .env file if present
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not required if env vars are set another way

from cross_reference import load_json_file
from generate_csv import (
    get_career_entries_with_urls,
    determine_data_quality,
    format_overlaps_summary
)
from generate_master_report import (
    aggregate_all_results,
    get_all_cached_schools
)


class GoogleSheetsExporter:
    """Export GITG coach data to Google Sheets"""

    def __init__(self, creds_path: str = None, sheet_id: str = None):
        """
        Initialize the exporter.

        Args:
            creds_path: Path to Google service account credentials JSON
            sheet_id: Google Sheet ID (from the URL)
        """
        self.creds_path = creds_path or os.getenv('GOOGLE_SHEETS_CREDS')
        self.sheet_id = sheet_id or os.getenv('GITG_SHEET_ID')
        self.client = None
        self.workbook = None

    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.creds_path, scope
            )
            self.client = gspread.authorize(creds)
            self.workbook = self.client.open_by_key(self.sheet_id)
            print(f"[OK] Authenticated with Google Sheets: {self.workbook.title}")
            return True

        except Exception as e:
            print(f"[ERROR] Google Sheets authentication failed: {e}")
            return False

    def _get_or_create_sheet(self, sheet_name: str, rows: int = 1000, cols: int = 20):
        """Get existing sheet or create new one"""
        try:
            return self.workbook.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            return self.workbook.add_worksheet(title=sheet_name, rows=rows, cols=cols)

    def _col_letter(self, col_num: int) -> str:
        """Convert column number to letter (1=A, 2=B, etc.)"""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(col_num % 26 + 65) + result
            col_num //= 26
        return result

    def _apply_overlap_formatting(self, worksheet, row_index: int, num_cols: int, has_overlap: bool):
        """Apply row highlighting for coaches with NMDP overlap"""
        if has_overlap:
            # Light green for overlap rows
            color = {"red": 0.77, "green": 0.94, "blue": 0.81}
            end_col = self._col_letter(num_cols)
            worksheet.format(
                f"A{row_index}:{end_col}{row_index}",
                {"backgroundColor": color}
            )

    def export_results(
        self,
        results: List[Dict],
        year_start: int = 2020,
        max_career_cols: int = 5
    ) -> bool:
        """
        Export cross-reference results to Google Sheets.

        Args:
            results: List of coach result dictionaries (with territory info)
            year_start: Earliest year for career history
            max_career_cols: Number of career history columns

        Returns:
            True if successful
        """
        if not self.client:
            if not self.authenticate():
                return False

        try:
            # Build headers
            headers = [
                "School", "State", "County", "Territory",
                "Coach Name", "Position"
            ]
            for i in range(max_career_cols):
                headers.append(f"Career {i+1}")
            headers.extend(["NMDP Overlap", "Overlap Details", "Data Quality", "Last Updated"])
            num_cols = len(headers)

            # === Master Results Tab ===
            print("Updating Master Results tab...")
            master_sheet = self._get_or_create_sheet("Master Results", rows=len(results) + 10, cols=num_cols)
            master_sheet.clear()

            # Write headers
            master_sheet.update(values=[headers], range_name='A1')
            time.sleep(0.5)
            master_sheet.format('A1:' + self._col_letter(num_cols) + '1', {
                "backgroundColor": {"red": 0.27, "green": 0.45, "blue": 0.77},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER"
            })

            # Write data rows
            rows_data = self._build_rows(results, year_start, max_career_cols)
            if rows_data:
                end_row = len(rows_data) + 1
                time.sleep(0.5)
                master_sheet.update(values=rows_data, range_name=f'A2:{self._col_letter(num_cols)}{end_row}')

            # Freeze header row
            # Note: Overlap highlighting is handled by conditional formatting rules in the sheet
            master_sheet.freeze(rows=1)

            print(f"  Master Results: {len(results)} coaches")

            # === Territory Tabs ===
            territories = {}
            for result in results:
                territory = result.get('territory', 'Unknown')
                if territory not in territories:
                    territories[territory] = []
                territories[territory].append(result)

            for territory, territory_results in sorted(territories.items()):
                # Sanitize sheet name (max 100 chars, no special chars)
                sheet_name = territory[:100].replace("/", "-").replace("\\", "-")
                print(f"Updating {sheet_name} tab...")

                territory_sheet = self._get_or_create_sheet(
                    sheet_name,
                    rows=len(territory_results) + 10,
                    cols=num_cols
                )
                territory_sheet.clear()

                # Write headers
                territory_sheet.update(values=[headers], range_name='A1')
                time.sleep(0.5)
                territory_sheet.format('A1:' + self._col_letter(num_cols) + '1', {
                    "backgroundColor": {"red": 0.27, "green": 0.45, "blue": 0.77},
                    "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    "horizontalAlignment": "CENTER"
                })

                # Write data rows
                rows_data = self._build_rows(territory_results, year_start, max_career_cols)
                if rows_data:
                    end_row = len(rows_data) + 1
                    time.sleep(0.5)
                    territory_sheet.update(values=rows_data, range_name=f'A2:{self._col_letter(num_cols)}{end_row}')

                # Freeze header row
                # Note: Overlap highlighting is handled by conditional formatting rules in the sheet
                territory_sheet.freeze(rows=1)
                print(f"  {sheet_name}: {len(territory_results)} coaches")

            # === Summary Tab ===
            self._update_summary_tab(results, territories)

            print(f"\n[OK] Export complete!")
            print(f"    Sheet URL: https://docs.google.com/spreadsheets/d/{self.sheet_id}")
            return True

        except Exception as e:
            print(f"[ERROR] Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _build_rows(
        self,
        results: List[Dict],
        year_start: int,
        max_career_cols: int
    ) -> List[List]:
        """Build row data from results"""
        rows = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        for result in results:
            career_history = result.get("career_history", [])
            career_entries = get_career_entries_with_urls(career_history, year_start)

            row = [
                result.get("searched_school", result.get("current_school", "Unknown")),
                result.get("state", "Unknown"),
                result.get("county", "Unknown"),
                result.get("territory", "Unknown"),
                result.get("coach_name", "Unknown"),
                result.get("current_position", "Unknown")
            ]

            # Career columns
            for i in range(max_career_cols):
                if i < len(career_entries):
                    display_text, _ = career_entries[i]
                    row.append(display_text)
                else:
                    row.append("")

            # Overlap info
            row.append("YES" if result.get("has_overlap") else "NO")
            row.append(format_overlaps_summary(result.get("overlaps", [])))
            row.append(determine_data_quality(career_history, result.get("research_status", "")))
            row.append(timestamp)

            rows.append(row)

        return rows

    def _update_summary_tab(self, results: List[Dict], territories: Dict[str, List]):
        """Update summary statistics tab"""
        summary_sheet = self._get_or_create_sheet("Summary", rows=50, cols=10)
        summary_sheet.clear()
        time.sleep(1)  # Rate limit

        # Overall stats
        total_coaches = len(results)
        coaches_with_overlap = sum(1 for r in results if r.get('has_overlap'))
        total_overlaps = sum(r.get('overlap_count', 0) for r in results)
        unique_schools = len(set(r.get('searched_school', '') for r in results))

        # Build all data at once
        all_data = [
            ["GITG Coach Cross-Reference Summary"],
            [""],
            ["Last Updated", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["", ""],
            ["Overall Statistics", ""],
            ["Total Schools Searched", unique_schools],
            ["Total Coaches", total_coaches],
            ["Coaches with NMDP Overlap", coaches_with_overlap],
            ["Overlap Rate", f"{(coaches_with_overlap/total_coaches*100):.1f}%" if total_coaches > 0 else "0%"],
            ["Total Overlap Instances", total_overlaps],
            ["", ""],
            ["By Territory", "Coaches", "Overlaps"]
        ]

        # Add territory breakdown
        for territory, territory_results in sorted(territories.items()):
            overlaps = sum(1 for r in territory_results if r.get('has_overlap'))
            all_data.append([territory, len(territory_results), overlaps])

        # Single batch update
        summary_sheet.update(values=all_data, range_name='A1')


def export_to_google_sheets(
    cache_base_dir: str,
    nmdp_db_path: str,
    aliases_path: str,
    config_path: str,
    locations_path: str,
    territory_path: str,
    creds_path: str,
    sheet_id: str
) -> bool:
    """
    Main function to export all cached data to Google Sheets.

    Args:
        cache_base_dir: Path to cache directory
        nmdp_db_path: Path to GITG database
        aliases_path: Path to school aliases
        config_path: Path to config file
        locations_path: Path to school locations
        territory_path: Path to territory mapping
        creds_path: Path to Google credentials JSON
        sheet_id: Google Sheet ID

    Returns:
        True if successful
    """
    print("Aggregating all cached school data...")
    results = aggregate_all_results(
        cache_base_dir, nmdp_db_path, aliases_path, config_path,
        locations_path, territory_path
    )

    if not results:
        print("No results found in cache")
        return False

    print(f"\nTotal coaches: {len(results)}")

    # Load config for year range
    config = load_json_file(config_path) if os.path.exists(config_path) else {}
    year_start = config.get("year_range", {}).get("start", 2020)

    # Calculate max career entries
    max_career = 0
    for result in results:
        entries = get_career_entries_with_urls(result.get("career_history", []), year_start)
        max_career = max(max_career, len(entries))
    max_career = max(max_career, 5)  # Minimum 5 columns

    # Export to Google Sheets
    exporter = GoogleSheetsExporter(creds_path, sheet_id)
    return exporter.export_results(results, year_start, max_career)


def main():
    """CLI entry point"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    # Default paths
    cache_dir = os.path.join(base_dir, "cache")
    nmdp_path = os.path.join(base_dir, "data", "gitg_school_years.json")
    aliases_path = os.path.join(base_dir, "data", "school_aliases.json")
    config_path = os.path.join(base_dir, "config.json")
    locations_path = os.path.join(base_dir, "data", "school_locations.json")
    territory_path = os.path.join(base_dir, "data", "territory_mapping.json")
    creds_path = os.path.join(base_dir, "data", "google_sheets_credentials.json")

    # Get sheet ID from environment or command line
    sheet_id = os.getenv('GITG_SHEET_ID')
    if len(sys.argv) > 1:
        sheet_id = sys.argv[1]

    if not sheet_id:
        print("ERROR: No Google Sheet ID provided.")
        print("Usage: python google_sheets_export.py <SHEET_ID>")
        print("   or: Set GITG_SHEET_ID environment variable")
        print("\nTo get the Sheet ID:")
        print("  1. Open your Google Sheet")
        print("  2. Copy the ID from the URL:")
        print("     https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit")
        sys.exit(1)

    if not os.path.exists(creds_path):
        print(f"ERROR: Credentials file not found: {creds_path}")
        sys.exit(1)

    success = export_to_google_sheets(
        cache_dir, nmdp_path, aliases_path, config_path,
        locations_path, territory_path, creds_path, sheet_id
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
