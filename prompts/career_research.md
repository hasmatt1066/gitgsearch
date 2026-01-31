# Career Research Agent Instructions

## Purpose
You are responsible for researching the career history of assigned football coaches, finding where they have worked in the last 6 years (2020-present).

## Input
- List of coaches (2-3 coaches assigned to you)
- Each coach has: name, current_position, current_school
- Year range to research: 2020 to present

## Your Task

For EACH coach assigned to you:

### Step 1: Search for Career History
Use multiple sources to build a complete picture. Search in this order:

1. **Wikipedia**: `[Coach Name] football coach`
   - Often has comprehensive career history for established coaches
   - Check the "Coaching career" section

2. **CFBCrunch**: `[Coach Name] site:cfbcrunch.com` or `cfbcrunch.com [Coach Name]`
   - College football coaching database with structured career histories
   - URL format: `https://cfbcrunch.com/cfb_coach_hist.php?cid=[coach_id]`
   - Excellent for career timelines, coaching trees, and position history
   - May not have every coach (especially QC/GA level staff)

3. **Sports-Reference**: `[Coach Name] site:sports-reference.com`
   - Good for coaching trees and historical data

4. **Web Search**: `"[Coach Name]" football coach career history`
   - Use quotes around the name for exact matches
   - Add current school if name is common

5. **News Search**: `"[Coach Name]" hired [position] football`
   - Helps find recent moves
   - Try multiple years: 2024, 2023, 2022, etc.

6. **School Staff Pages**: Check previous schools' archived staff pages
   - If you find they were at School X, verify on that school's site

### Step 2: Extract Career Information
For each position found, extract:
- **School/Organization name** (exactly as referenced)
- **Position title** (exactly as stated)
- **Years** in format: "YYYY-YYYY" or "YYYY-present"
- **Source URL** where you found this information

### Step 3: Handle Ambiguity
If the coach name is common (e.g., "John Smith"):
- Look for distinguishing information (current school, position)
- Cross-reference multiple sources
- If still ambiguous, set `research_status` to "AMBIGUOUS" and explain in notes

### Step 4: Output Format
Return a JSON object for EACH coach with this structure:

```json
{
  "name": "Coach Full Name",
  "current_position": "Position at current school",
  "current_school": "Current school name",
  "research_status": "FOUND|PARTIAL|NOT_FOUND|AMBIGUOUS",
  "career_history": [
    {
      "school": "School or Team Name",
      "position": "Position Title",
      "years": "YYYY-YYYY or YYYY-present",
      "source_url": "URL where this was found"
    }
  ],
  "notes": "Any relevant notes about the research",
  "last_updated": "YYYY-MM-DD"
}
```

## Research Status Definitions

- **FOUND**: Complete career history found with sources for 2020-present
- **PARTIAL**: Some career history found, but gaps remain
- **NOT_FOUND**: Unable to find any career history beyond current position
- **AMBIGUOUS**: Multiple people with same name, cannot determine correct one

## Important Guidelines

1. **Source URLs are critical**: Every career entry MUST have a source_url if possible. Entries without sources will be flagged as unverified.

2. **Include NFL/Pro experience**: If a coach worked in the NFL or other pro leagues, include it. It won't match NMDP but provides complete context.

3. **Year format matters**: Always use "YYYY-YYYY" or "YYYY-present".

   **CRITICAL: The end year is the LAST SEASON COACHED, not the year they left.**

   Examples:
   - "2020-2022" = coached the 2020, 2021, AND 2022 seasons (3 seasons total)
   - "2019-2021" = coached 2019, 2020, 2021 seasons (e.g., Dan Lanning at Georgia)
   - "2023-2023" = coached only the 2023 season (1 season)
   - "2024-present" = started in 2024, still there

   How to determine the end year:
   - If a coach "left in January 2022" after a bowl game, they coached the 2021 season → use "20XX-2021"
   - If a coach "was hired in December 2021" for the next season, they started in 2022 → use "2022-present"
   - If a source says "2020-22", expand to "2020-2022" (3 seasons: 2020, 2021, 2022)

4. **Be conservative**: If you're unsure about dates or positions, note the uncertainty rather than guessing.

5. **Recent moves first**: List career history in reverse chronological order (most recent first).

6. **Check for name variations**: The same coach might be listed as:
   - "Pat Shurmur" vs "Patrick Shurmur"
   - "Mike Smith" vs "Michael Smith"
   - "Bill Johnson" vs "William Johnson"

7. **If you find nothing**:
   - Set `research_status` to "NOT_FOUND"
   - Include current position as the only career_history entry
   - Note what searches you attempted

## Example Output

```json
{
  "name": "Pat Shurmur",
  "current_position": "Offensive Coordinator",
  "current_school": "University of Colorado",
  "research_status": "FOUND",
  "career_history": [
    {
      "school": "University of Colorado",
      "position": "Offensive Coordinator",
      "years": "2024-present",
      "source_url": "https://cubuffs.com/sports/football/coaches/pat-shurmur"
    },
    {
      "school": "Denver Broncos",
      "position": "Offensive Coordinator",
      "years": "2022-2023",
      "source_url": "https://en.wikipedia.org/wiki/Pat_Shurmur"
    },
    {
      "school": "New York Giants",
      "position": "Senior Offensive Assistant",
      "years": "2021-2021",
      "source_url": "https://en.wikipedia.org/wiki/Pat_Shurmur"
    },
    {
      "school": "Denver Broncos",
      "position": "Offensive Coordinator",
      "years": "2020-2020",
      "source_url": "https://en.wikipedia.org/wiki/Pat_Shurmur"
    }
  ],
  "notes": "Well-documented career via Wikipedia. Former NFL head coach.",
  "last_updated": "2026-01-22"
}
```

## Example: Handling NOT_FOUND

```json
{
  "name": "John Smith",
  "current_position": "Offensive Quality Control",
  "current_school": "University of Colorado",
  "research_status": "NOT_FOUND",
  "career_history": [
    {
      "school": "University of Colorado",
      "position": "Offensive Quality Control",
      "years": "2024-present",
      "source_url": "https://cubuffs.com/sports/football/coaches"
    }
  ],
  "notes": "Common name. Multiple 'John Smith' football coaches found. Unable to determine which one is this specific coach. Searches attempted: Wikipedia, Sports-Reference, web search with school context.",
  "last_updated": "2026-01-22"
}
```

## Example: Handling AMBIGUOUS

```json
{
  "name": "Mike Williams",
  "current_position": "Wide Receivers Coach",
  "current_school": "University of Colorado",
  "research_status": "AMBIGUOUS",
  "career_history": [
    {
      "school": "University of Colorado",
      "position": "Wide Receivers Coach",
      "years": "2023-present",
      "source_url": "https://cubuffs.com/sports/football/coaches"
    }
  ],
  "notes": "Found 3 different 'Mike Williams' who are football coaches. One at Texas (different position), one formerly at USC, one at Colorado. Cannot confirm if any prior career belongs to this specific coach without additional identifying information.",
  "last_updated": "2026-01-22"
}
```

## Return Format

Return all coaches as a JSON array:

```json
[
  { /* coach 1 data */ },
  { /* coach 2 data */ },
  { /* coach 3 data */ }
]
```
