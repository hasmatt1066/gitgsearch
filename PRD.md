# Product Requirements Document: NMDP Coach Cross-Reference System

**Version:** 1.1
**Date:** 2026-01-22
**Status:** Ready for Development

---

## 1. Executive Summary

### 1.1 Purpose
Build a CLI tool powered by Claude Code that identifies "warm leads" for NMDP's Get In The Game (GITG) program by cross-referencing current football coaching staff at target schools against NMDP's historical partnership database.

### 1.2 Problem Statement
NMDP's business development team needs to identify coaches who have previously worked with NMDP programs at other schools. These coaches represent warm leads because they already understand NMDP's mission and have experience running GITG programs. Currently, there is no systematic way to identify these connections.

### 1.3 Solution
A multi-agent system that:
1. Retrieves the current coaching staff roster for a queried school
2. Researches each coach's career history (last 6 years)
3. Cross-references that history against NMDP's GITG database
4. Outputs a structured CSV report identifying overlaps

---

## 2. User Stories

### 2.1 Primary Use Case
**As a** NMDP business development team member
**I want to** query a school and see which coaches have prior NMDP experience
**So that** I can prioritize outreach to warm leads who already know our program

### 2.2 Example Workflow
1. User runs: `claude "Check coaches at CU Boulder for NMDP connections"`
2. System retrieves CU Boulder's football coaching staff
3. System researches each coach's career history
4. System cross-references against GITG database
5. System outputs CSV: `output/university_of_colorado_2026-01-22.csv`
6. User reviews CSV to identify warm leads

---

## 3. Scope

### 3.1 In Scope (MVP)
- Single school queries
- Football coaching staff only (head coach + all assistant coaches)
- Career history from 2020-present (6-year window)
- Cross-reference against existing GITG JSON database
- CSV output format
- Data caching for re-queries
- Source URL tracking for all data points

### 3.2 Out of Scope (Future Considerations)
- Batch processing multiple schools
- Other sports beyond football
- Automated outreach/email generation
- Integration with CRM systems
- Historical trend analysis

### 3.3 Explicitly Excluded
- Browser automation (too slow, reliability concerns)
- Paid API integrations
- Supporting staff (strength & conditioning, etc.)

---

## 4. Data Sources

### 4.1 NMDP GITG Database
- **File:** `data/gitg_school_years.json`
- **Format:** JSON object with school names as keys, arrays of academic years as values
- **Size:** ~525 schools
- **Coverage:** Historical GITG program partnerships
- **Example:**
```json
{
  "ALBRIGHT COLLEGE": ["2018-2019", "2019-2020", "2021-2022", "2022-2023", "2023-2024", "2024-2025"],
  "UNIVERSITY OF COLORADO": ["2021-2022", "2022-2023"]
}
```

### 4.2 Web Sources for Coach Data
Priority order for searching:
1. **Official athletic department staff pages** - Primary source for current roster
2. **Wikipedia** - Career history for head coaches and notable assistants
3. **Sports-Reference.com** - Coaching trees and historical data
4. **Web search:** `"[Coach Name] football coach career history"`
5. **News search:** `"[Coach Name] hired [school]"` - For recent moves

### 4.3 School Name Aliases
- **File:** `data/school_aliases.json`
- **Purpose:** Map common name variations to canonical NMDP database names
- **Manually curated and extensible**
- **Example:**
```json
{
  "UNIVERSITY OF COLORADO": ["CU Boulder", "Colorado Buffaloes", "CU", "Colorado", "University of Colorado Boulder"],
  "UNIVERSITY OF SOUTHERN CALIFORNIA": ["USC", "Southern Cal", "Trojans"]
}
```

---

## 5. System Architecture

### 5.1 High-Level Design Philosophy
Balance non-deterministic AI capabilities (web search, data extraction, reasoning) with deterministic script-based operations (matching, validation, output generation).

**Guiding Principle:** Claude handles tasks requiring interpretation and judgment; Python scripts handle tasks requiring consistency and repeatability.

### 5.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (Main Claude)                  │
│  - Receives user query                                          │
│  - Loads configuration and databases                            │
│  - Spawns and coordinates agents                                │
│  - Manages workflow and checkpoints                             │
│  - Produces final output                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       ROSTER AGENT                              │
│  - Searches for school's official athletic staff page           │
│  - Extracts coaching staff names and positions                  │
│  - Handles varied page formats                                  │
│  - Outputs structured roster JSON                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CAREER RESEARCH AGENTS (Parallel)              │
│  - Partitioned: 2-3 coaches per agent                           │
│  - Search Wikipedia, staff pages, news articles                 │
│  - Extract career history with source URLs                      │
│  - Adaptive query reformulation on failed searches              │
│  - Output: Structured career JSON per coach                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION AGENT                           │
│  - Reviews all career research outputs                          │
│  - Checks for: missing data, missing sources, timeline gaps     │
│  - Can request re-research (up to 2 retries per coach)          │
│  - Flags unresolvable issues for user notification              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DETERMINISTIC SCRIPTS (Python)                  │
│  - validate.py: Schema validation                               │
│  - normalize.py: School name canonicalization                   │
│  - cross_reference.py: NMDP overlap detection                   │
│  - generate_csv.py: Final output generation                     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Task Allocation Matrix

| Task | Handler | Rationale |
|------|---------|-----------|
| Find coaching staff page | Claude (Roster Agent) | Requires web search, page interpretation |
| Extract names/positions from page | Claude (Roster Agent) | Varied HTML formats, messy data |
| Research career history | Claude (Career Agents) | Adaptive searching, reasoning about ambiguous data |
| Validate JSON schema | Python script | Must be consistent, rule-based |
| Normalize school names | Python script | Must be deterministic |
| Parse year ranges | Python script | Must be deterministic |
| Match against NMDP database | Python script | Must be deterministic, no hallucination risk |
| Generate CSV output | Python script | Must be consistent format |
| Assess data quality | Claude (Verification Agent) | Requires judgment about what "makes sense" |

---

## 6. Data Schemas

### 6.1 Configuration Schema
**File:** `config.json`
```json
{
  "year_range": {
    "start": 2020,
    "end": 2026
  },
  "cache_staleness_days": 30,
  "max_retries_per_coach": 2,
  "coaches_per_research_agent": 3,
  "search_sources": [
    "athletic_staff_page",
    "wikipedia",
    "sports_reference",
    "web_search",
    "news_search"
  ]
}
```

### 6.2 Roster Schema
**File:** `cache/[school_name]/roster.json`

Each coach entry includes a `source_type` to indicate provenance:
- `official_roster` - Listed on official athletic department page
- `news_report` - Found via news articles, not yet on official page
- `departure_reported` - On official page but news indicates they've left

```json
{
  "school": "University of Colorado",
  "school_normalized": "UNIVERSITY OF COLORADO",
  "fetched_date": "2026-01-22",
  "official_roster_url": "https://cubuffs.com/sports/football/coaches",
  "roster_notes": "Official page shows Pat Shurmur as OC, but news reports indicate departure. Brennan Marion hired as replacement per ESPN.",
  "coaches": [
    {
      "name": "Deion Sanders",
      "position": "Head Coach",
      "source_type": "official_roster",
      "source_url": "https://cubuffs.com/sports/football/coaches"
    },
    {
      "name": "Pat Shurmur",
      "position": "Offensive Coordinator",
      "source_type": "departure_reported",
      "source_url": "https://cubuffs.com/sports/football/coaches"
    },
    {
      "name": "Brennan Marion",
      "position": "Offensive Coordinator",
      "source_type": "news_report",
      "source_url": "https://www.espn.com/college-football/story/brennan-marion-colorado"
    }
  ]
}
```

**Source Type Rationale:** Athletic department websites often lag behind actual staff changes. By tracking source type, users can see which coaches are confirmed vs. reported, enabling informed decisions about outreach timing.

### 6.3 Coach Career Schema
**File:** `cache/[school_name]/coaches/[coach_name].json`
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
      "position": "Head Coach",
      "years": "2018-2019",
      "source_url": "https://en.wikipedia.org/wiki/Pat_Shurmur"
    }
  ],
  "notes": "",
  "last_updated": "2026-01-22"
}
```

### 6.4 Research Status Values
- `FOUND` - Career history successfully retrieved with sources
- `PARTIAL` - Some history found, gaps remain
- `NOT_FOUND` - Unable to find career history
- `AMBIGUOUS` - Multiple people with same name, unable to determine correct one

### 6.5 Overlap Result Schema
**Internal structure after cross-reference script runs:**
```json
{
  "coach_name": "John Smith",
  "has_overlap": true,
  "overlaps": [
    {
      "school": "TEXAS STATE UNIVERSITY",
      "academic_year": "2021-2022",
      "coach_position_at_time": "Running Backs Coach"
    }
  ]
}
```

---

## 7. Output Specification

### 7.1 CSV Output Format
**File:** `output/[school_name]_[date].csv`

| Column | Description | Example |
|--------|-------------|---------|
| Coach Name | Full name | Pat Shurmur |
| Current Position | Role at queried school | Offensive Coordinator |
| Career History (2020-Present) | Summary of positions | Colorado (2024-present), Broncos (2022-2023), Giants (2020-2021) |
| Source URLs | Pipe-separated list of sources | https://cubuffs.com/... \| https://en.wikipedia.org/... |
| NMDP Overlap | YES or NO | NO |
| Overlap Details | If YES: School, Year | Texas State, 2021-2022 |
| Data Quality | VERIFIED (has sources) or UNVERIFIED | VERIFIED |

### 7.2 Example CSV Row
```csv
"Pat Shurmur","Offensive Coordinator","Colorado (2024-present), Broncos (2022-2023), Giants (2020-2021)","https://cubuffs.com/coaches/shurmur | https://en.wikipedia.org/wiki/Pat_Shurmur","NO","","VERIFIED"
```

---

## 8. Agent Specifications

### 8.1 Roster Agent
**Purpose:** Retrieve current coaching staff for the queried school

**Inputs:**
- School name (user query)
- School aliases (for search variations)

**Process:**
1. Search for official athletic staff page
2. Fetch and parse the page
3. Extract all football coaching staff (head coach + assistants)
4. Exclude support staff (strength & conditioning, etc.)

**Outputs:**
- Structured roster JSON per schema 6.2
- Saved to cache

**Error Handling:**
- No football program found → Notify user, abort
- Athletic website unreachable → Notify user, suggest retry later
- Ambiguous school name → Ask user for clarification

### 8.2 Career Research Agent
**Purpose:** Research career history for assigned coaches

**Inputs:**
- List of 2-3 coaches (partitioned from full roster)
- Configuration (year range, search sources)

**Process:**
1. For each coach:
   a. Search Wikipedia for career history
   b. Search Sports-Reference
   c. Perform web search: "[Name] football coach career history"
   d. Search news: "[Name] hired [school]" for recent moves
2. Extract positions, schools, years from sources
3. Record source URL for each data point
4. If search fails, reformulate query and retry

**Outputs:**
- Structured career JSON per schema 6.3 for each coach
- Saved to cache individually (enables checkpointing)

**Error Handling:**
- No history found → Set status to NOT_FOUND, continue
- Ambiguous name (multiple coaches) → Set status to AMBIGUOUS, add notes
- Common name with no distinguishing info → Flag for verification

### 8.3 Verification Agent
**Purpose:** Quality check all career research before cross-referencing

**Inputs:**
- All coach career JSONs from research phase
- Verification criteria

**Process:**
1. For each coach, check:
   - Is career_history empty? → Flag for re-research
   - Are source_urls missing for entries? → Flag as unverified
   - Are there timeline gaps within the year range? → Flag for re-research
   - Do the positions/schools make logical sense? → Flag anomalies
2. For flagged coaches, request re-research (max 2 retries)
3. After retries exhausted, mark final status

**Outputs:**
- Verified/flagged status for each coach
- Re-research requests (up to 2 per coach)
- Final quality assessment

**Verification Failure Triggers:**
- No career history found at all
- Career history found but no source URLs
- Gaps in timeline within 2020-2026 range

**Retry Limit:** 2 attempts per coach, then accept current state with flags

---

## 9. Python Scripts Specification

### 9.1 validate.py
**Purpose:** Validate coach data against required schema

**Function:**
```python
def validate_coach_data(data: dict) -> tuple[bool, list[str]]:
    """
    Returns (is_valid, list_of_errors)
    Checks required fields, year format, data types
    """
```

**Validation Rules:**
- Required fields: name, current_position, current_school, career_history
- Year format: `YYYY-YYYY` or `YYYY-present`
- career_history must be a list
- Each career entry must have: school, position, years

### 9.2 normalize.py
**Purpose:** Canonicalize school names to match NMDP database

**Function:**
```python
def normalize_school_name(name: str, aliases: dict, nmdp_schools: set) -> str:
    """
    Returns canonical school name from NMDP database
    Uses alias lookup, then direct match, then fuzzy match as fallback
    Logs fuzzy matches for manual review
    """
```

**Matching Priority:**
1. Direct alias lookup (case-insensitive)
2. Direct match to NMDP database (case-insensitive)
3. Fuzzy match with 90% threshold (logged for review)
4. Return original if no match (won't match NMDP)

### 9.3 cross_reference.py
**Purpose:** Detect overlaps between coach history and NMDP database

**Function:**
```python
def find_overlaps(coach_career: list, nmdp_db: dict, aliases: dict) -> list:
    """
    Returns list of overlap objects
    Parses year ranges, normalizes school names, checks for matches
    """
```

**Logic:**
1. For each career stint in coach history:
   a. Normalize school name
   b. Parse years into list (e.g., "2020-2022" → [2020, 2021, 2022])
   c. For each year, construct academic year (2020 → "2020-2021")
   d. Check if school + academic_year exists in NMDP database
2. Return all matches

**Year Parsing Rules:**
- "2020-2022" → [2020, 2021] (academic years 2020-2021, 2021-2022)
- "2024-present" → [2024, 2025] (assuming current year 2026)
- NFL teams → Skip (no NMDP match possible, but still logged in history)

### 9.4 generate_csv.py
**Purpose:** Generate final CSV output from processed data

**Function:**
```python
def generate_csv(school_name: str, coaches: list, overlaps: dict, output_path: str):
    """
    Creates CSV file with all coach data and overlap analysis
    """
```

**Output Columns:**
- Coach Name
- Current Position
- Career History (2020-Present)
- Source URLs
- NMDP Overlap (YES/NO)
- Overlap Details
- Data Quality (VERIFIED/UNVERIFIED)

---

## 10. File Structure

```
gitgsearch2/
├── CLAUDE.md                      # Master instructions for Claude Code
├── PRD.md                         # This document
├── config.json                    # Configurable parameters
│
├── data/
│   ├── gitg_school_years.json     # NMDP database (existing)
│   └── school_aliases.json        # Name mappings (manually curated)
│
├── scripts/
│   ├── validate.py                # Schema validation
│   ├── normalize.py               # School name normalization
│   ├── cross_reference.py         # NMDP overlap detection
│   └── generate_csv.py            # Final CSV output generation
│
├── prompts/
│   ├── roster_search.md           # Instructions for roster agent
│   ├── career_research.md         # Instructions for career research agents
│   └── verification.md            # Instructions for verification agent
│
├── cache/
│   └── [school_name]/             # Normalized, lowercase, underscores
│       ├── roster.json            # Current coaching staff
│       └── coaches/
│           └── [coach_name].json  # Individual career histories
│
└── output/
    ├── [school_name]_[date].csv   # Final reports
    └── logs/
        └── [school_name]_[date].log  # Run logs for debugging
```

---

## 11. Workflow Detail

### 11.1 Complete Execution Flow

```
USER: "Check coaches at CU Boulder for NMDP connections"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: INITIALIZATION                                          │
│  - Parse school name from query                                 │
│  - Load config.json                                             │
│  - Load gitg_school_years.json                                  │
│  - Load school_aliases.json                                     │
│  - Check cache for existing data                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: ROSTER RETRIEVAL                                        │
│  - Spawn Roster Agent                                           │
│  - Agent searches for athletic staff page                       │
│  - Agent extracts coaching staff                                │
│  - Validate roster against schema                               │
│  - Save to cache/[school]/roster.json                           │
│  - Display roster to user for confirmation                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    [USER CONFIRMS ROSTER]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: CAREER RESEARCH                                         │
│  - Partition coaches (2-3 per agent)                            │
│  - Spawn Career Research Agents in parallel                     │
│  - Each agent researches assigned coaches                       │
│  - Save each coach to cache individually (checkpoint)           │
│  - Collect all results                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: VERIFICATION                                            │
│  - Spawn Verification Agent                                     │
│  - Agent reviews all career data                                │
│  - Flags issues: missing data, no sources, gaps                 │
│  - Requests re-research for flagged coaches (max 2 retries)     │
│  - Produces final verified dataset                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: CROSS-REFERENCE (Deterministic)                         │
│  - Run validate.py on all coach data                            │
│  - Run normalize.py to canonicalize school names                │
│  - Run cross_reference.py to find NMDP overlaps                 │
│  - Results are deterministic given same inputs                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: OUTPUT GENERATION                                       │
│  - Run generate_csv.py                                          │
│  - Save to output/[school]_[date].csv                           │
│  - Generate log file                                            │
│  - Display summary to user                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
               OUTPUT: CSV file + summary message
```

### 11.2 Caching Behavior

**On first query for a school:**
- Fetch roster, save to cache
- Research each coach, save individually
- Generate output

**On re-query for same school:**
- Check cache age against `cache_staleness_days`
- If fresh: Use cached data, skip to cross-reference
- If stale: Re-fetch roster, compare to cached
  - Show diff to user (new coaches, removed coaches, changed positions)
  - User confirms update
  - Only research NEW coaches (use cache for existing)

### 11.3 Checkpointing

If execution fails mid-process:
- Roster saved immediately after fetch
- Each coach saved individually after research
- On restart: Check what's already cached, resume from there
- Prevents duplicate work and lost data

---

## 12. Error Handling

### 12.1 Error Types and Responses

| Error | Detection | Response |
|-------|-----------|----------|
| No football program | Roster agent finds no football staff | Notify user: "No football program found for [school]" |
| Website unreachable | HTTP error or timeout | Notify user: "Could not reach [school] athletic site. Try again later." |
| Coach name too common | Multiple distinct coaches with same name found | Notify user: "[Coach Name] is ambiguous. Found multiple coaches with this name. Manual verification needed." |
| No career history found | Research agent exhausts all sources | Mark as NOT_FOUND, include in output with flag |
| Career history has no sources | Verification agent detects missing URLs | Mark as UNVERIFIED, include in output with flag |
| Timeline gaps | Verification agent detects missing years | Attempt re-research (2 retries), then mark as PARTIAL |
| School name not in NMDP database | Normalization script returns no match | Coach's stint at that school simply won't show overlap (expected for NFL, etc.) |

### 12.2 Retry Logic

```
For each flagged coach:
  retry_count = 0
  while retry_count < 2 and issues_remain:
    Re-run career research with different search strategies
    Re-verify results
    retry_count += 1

  if issues_remain:
    Accept current state, mark with appropriate status
    Include in output with quality flags
```

---

## 13. Configuration Parameters

**File:** `config.json`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `year_range.start` | 2020 | Earliest year to consider for career history |
| `year_range.end` | 2026 | Latest year (current year) |
| `cache_staleness_days` | 30 | Days before cached data is considered stale |
| `max_retries_per_coach` | 2 | Maximum re-research attempts per coach |
| `coaches_per_research_agent` | 3 | How many coaches each research agent handles |
| `search_sources` | [list] | Ordered list of sources to search |

**All parameters are adjustable** for future tuning without code changes.

---

## 14. Logging

### 14.1 Log Format
**File:** `output/logs/[school_name]_[date].log`

```
[2026-01-22 14:30:01] INFO: Starting search for: University of Colorado
[2026-01-22 14:30:02] INFO: Fetching roster from: https://cubuffs.com/sports/football/coaches
[2026-01-22 14:30:05] INFO: Found 12 coaches
[2026-01-22 14:30:06] INFO: User confirmed roster
[2026-01-22 14:30:07] INFO: Spawning 4 career research agents (3 coaches each)
[2026-01-22 14:30:45] INFO: Agent 1 complete: Sanders (FOUND), Shurmur (FOUND), Lewis (FOUND)
[2026-01-22 14:31:12] INFO: Agent 2 complete: Smith (NOT_FOUND), Jones (FOUND), Williams (FOUND)
[2026-01-22 14:31:30] INFO: Verification flagged: Smith - no career history
[2026-01-22 14:31:31] INFO: Retry 1 for Smith
[2026-01-22 14:32:00] INFO: Retry 1 failed for Smith - still no history found
[2026-01-22 14:32:01] INFO: Retry 2 for Smith
[2026-01-22 14:32:30] INFO: Retry 2 failed for Smith - accepting NOT_FOUND status
[2026-01-22 14:33:00] INFO: Cross-reference complete: 2 overlaps found
[2026-01-22 14:33:01] INFO: CSV generated: output/university_of_colorado_2026-01-22.csv
[2026-01-22 14:33:02] INFO: Search complete. 12 coaches processed, 2 overlaps found, 1 unresolved.
```

### 14.2 Log Levels
- `INFO` - Normal operations
- `WARN` - Issues that don't stop execution (e.g., missing source URL)
- `ERROR` - Issues that require user attention or stop execution

---

## 15. Future Considerations (Post-MVP)

### 15.1 Batch Processing
- Accept `schools.txt` file with multiple schools
- Process sequentially or in parallel
- Generate combined report

### 15.2 Other Sports
- Extend to basketball, volleyball, etc.
- Separate databases per sport
- Configurable sport selection

### 15.3 Alias Learning
- When fuzzy matching is used, prompt user to confirm
- If confirmed, auto-add to `school_aliases.json`
- Build up alias file organically over time

### 15.4 CRM Integration
- Export directly to Salesforce, HubSpot, etc.
- Track outreach status per coach

---

## 16. Acceptance Criteria

### 16.1 MVP Complete When:
1. [ ] User can query a single school by name
2. [ ] System retrieves current football coaching roster
3. [ ] System researches career history for all coaches (2020-present)
4. [ ] Each career entry includes source URL where available
5. [ ] System cross-references against GITG database
6. [ ] System outputs CSV with all columns specified
7. [ ] Overlaps are correctly identified (verified manually on test cases)
8. [ ] Data is cached for subsequent queries
9. [ ] Errors are handled gracefully with user notifications
10. [ ] Configuration is adjustable via config.json

### 16.2 Quality Criteria:
- Cross-reference matching is 100% accurate (deterministic scripts)
- Career history retrieval has source URLs for >80% of entries
- System completes single-school query in <5 minutes
- Cached queries complete in <30 seconds

---

## 17. Glossary

| Term | Definition |
|------|------------|
| NMDP | National Marrow Donor Program |
| GITG | Get In The Game - NMDP's program partnering with college athletics |
| Warm Lead | A coach who has prior NMDP experience from a previous position |
| Overlap | When a coach was at a school during the same academic year NMDP ran a GITG program there |
| Academic Year | Format: "2020-2021" representing the school year starting Fall 2020 |
| Canonical Name | The standardized school name as it appears in the GITG database |
| Cache Staleness | How long before cached data should be refreshed |

---

## 18. Appendix

### 18.1 Sample GITG Database Entry
```json
"UNIVERSITY OF COLORADO": [
  "2021-2022",
  "2022-2023"
]
```

### 18.2 Sample Alias Entry
```json
"UNIVERSITY OF COLORADO": [
  "CU Boulder",
  "Colorado Buffaloes",
  "CU",
  "Colorado",
  "University of Colorado Boulder",
  "UC Boulder"
]
```

### 18.3 Sample Final CSV Output
```csv
Coach Name,Current Position,Career History (2020-Present),Source URLs,NMDP Overlap,Overlap Details,Data Quality
"Deion Sanders","Head Coach","Colorado (2023-present), Jackson State (2020-2022)","https://cubuffs.com/coaches/sanders | https://en.wikipedia.org/wiki/Deion_Sanders","YES","Jackson State, 2021-2022","VERIFIED"
"Pat Shurmur","Offensive Coordinator","Colorado (2024-present), Broncos (2022-2023), Giants (2020-2021)","https://cubuffs.com/coaches/shurmur | https://en.wikipedia.org/wiki/Pat_Shurmur","NO","","VERIFIED"
"John Smith","RB Coach","Colorado (2023-present)","","NO","","UNVERIFIED"
```

---

**Document Revision History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-22 | Claude + User | Initial PRD based on design discussions |
| 1.1 | 2026-01-22 | Claude + User | Added source_type annotation for roster entries (official_roster, news_report, departure_reported) to track data provenance. Updated roster schema, validation, and roster_search.md prompt. |
