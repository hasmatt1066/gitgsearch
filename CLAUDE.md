# NMDP Coach Cross-Reference System

## System Overview

This system identifies "warm leads" for NMDP's Get In The Game (GITG) program by finding coaches at target schools who have prior NMDP experience from previous positions.

**Core workflow:**
1. User queries a school (e.g., "Check CU Boulder coaches")
2. System retrieves current football coaching staff
3. System researches each coach's career history (2020-present)
4. System cross-references against NMDP's GITG database
5. System outputs CSV report identifying overlaps

## File Structure

```
gitgsearch2/
├── CLAUDE.md                 # This file - master instructions
├── PRD.md                    # Product requirements document
├── config.json               # Configurable parameters
├── data/
│   ├── gitg_school_years.json   # NMDP partnership database
│   └── school_aliases.json      # School name mappings
├── scripts/
│   ├── cache_utils.py        # Cache staleness and completeness checking
│   ├── validate.py           # Schema validation
│   ├── normalize.py          # School name normalization
│   ├── cross_reference.py    # NMDP overlap detection
│   └── generate_csv.py       # CSV output generation
├── prompts/
│   ├── roster_search.md      # Roster agent instructions
│   ├── career_research.md    # Career research agent instructions
│   └── verification.md       # Verification agent instructions
├── cache/                    # Cached data by school
└── output/                   # Generated reports
```

## How to Run a Search

When the user asks to check coaches at a school, follow this workflow:

### Step 1: Parse the Query
Extract the school name from the user's query. Examples:
- "Check CU Boulder" → "CU Boulder"
- "Find coaches at University of Colorado" → "University of Colorado"
- "Search Texas A&M coaching staff" → "Texas A&M"

### Step 2: Check for Cached Data

**Run the cache status check:**

```bash
cd scripts && python3 cache_utils.py "[SCHOOL NAME]"
```

This will output one of four recommendations:

1. **"use_cache"** - Cache is fresh and complete
   > "I found complete cached data for [School] from [date] ([X] days old). Use cached data or refresh?"
   - If user says use cache: Skip to Step 6 (Cross-Reference)
   - If user says refresh: Continue to Step 3

2. **"refresh_recommended"** - Cache exists but is stale (older than `cache_staleness_days`)
   > "I found cached data for [School] from [date], but it's [X] days old (stale after 30 days). Refresh data or use stale cache?"
   - If user says refresh: Continue to Step 3
   - If user says use stale: Skip to Step 6 (Cross-Reference)

3. **"resume_research"** - Roster exists but career research is incomplete
   > "I found partial data for [School]: roster complete but [N] coaches missing career data. Resume research or start fresh?"
   - Shows list of coaches missing career data
   - If user says resume: Skip to Step 4 with only missing coaches
   - If user says start fresh: Continue to Step 3

4. **"no_cache"** - No cached data exists
   > "No cached data found for [School]. Starting fresh search."
   - Continue to Step 3

**Cache directory structure:**
```
cache/
  university_of_colorado/
    roster.json
    coaches/
      all_coaches.json       # Combined format (all coaches in one file)
      # OR individual files:
      deion_sanders.json
      pat_shurmur.json
      ...
```

**Force refresh option:** If user explicitly requests fresh data (e.g., "refresh CU Boulder coaches"), skip the cache check and proceed directly to Step 3.

### Step 3: Retrieve Roster (Roster Agent)

**Spawn a Task agent** to find the coaching staff:

```
Task: Find football coaching roster
Agent type: general-purpose
Prompt: Follow the instructions in prompts/roster_search.md to find the current football coaching staff for [SCHOOL NAME]. Return the roster as JSON.
```

The agent should return a JSON roster. Save it to `cache/[school_name]/roster.json`.

**Display roster to user for confirmation:**
> Found 12 coaches for University of Colorado:
> 1. Deion Sanders - Head Coach
> 2. Pat Shurmur - Offensive Coordinator
> ...
>
> Proceed with career research? (y/n)

### Step 4: Research Careers (Career Research Agents)

**Partition coaches** into groups of 2-3 (based on `config.json` setting).

**Spawn parallel Task agents** for each group:

```
Task: Research coach careers (batch 1)
Agent type: general-purpose
Prompt: Follow the instructions in prompts/career_research.md. Research career history for these coaches:
1. [Coach Name] - [Position] at [School]
2. [Coach Name] - [Position] at [School]
3. [Coach Name] - [Position] at [School]

Return JSON array with career data for each coach.
```

As each agent completes, save individual coach files to `cache/[school_name]/coaches/[coach_name].json`.

### Step 5: Verify Data (Verification Agent)

**Spawn a Task agent** to verify all research:

```
Task: Verify career research data
Agent type: general-purpose
Prompt: Follow the instructions in prompts/verification.md. Review all coach career data and identify any issues. Here is the data to verify:
[Include all coach JSON data]

Max retries per coach: 2
```

If verification flags coaches for re-research:
1. Check retry count (max 2 per coach)
2. Spawn new Career Research agent for flagged coaches
3. Re-run verification
4. After max retries, accept data with warnings

### Step 6: Cross-Reference (Deterministic)

Run the Python scripts to find overlaps:

```bash
cd scripts
python cross_reference.py ../cache/[school_name]/coaches ../data/gitg_school_years.json ../data/school_aliases.json ../config.json
```

This returns deterministic results - same input always produces same output.

### Step 7: Generate Output

Run the CSV generator:

```bash
python generate_csv.py "[school_name]"
```

This creates `output/[school_name]_[date].csv`.

**Display summary to user:**
> ## Search Complete
>
> **School:** University of Colorado
> **Coaches processed:** 12
> **NMDP overlaps found:** 2
>
> **Warm Leads:**
> - Deion Sanders: Jackson State (2021-2022)
> - John Smith: Texas State (2020-2021)
>
> **Report saved:** output/university_of_colorado_2026-01-22.csv

## Important Configuration

### config.json Settings
- `year_range.start`: 2020 (adjustable)
- `year_range.end`: 2026 (current year)
- `cache_staleness_days`: 30 (when to refresh cache)
- `max_retries_per_coach`: 2 (verification retry limit)
- `coaches_per_research_agent`: 3 (batch size)

### School Name Normalization
The system uses `data/school_aliases.json` to map common names to NMDP database format:
- "CU Boulder" → "UNIVERSITY OF COLORADO-BOULDER"
- "USC" → "UNIVERSITY OF SOUTHERN CALIFORNIA"

If a school name doesn't match, the cross-reference will still run but won't find overlaps for unmatched names.

## Error Handling

### No Football Program
If roster search finds no football program:
> "No football program found for [School]. This system only supports football coaching staff."

### Website Unreachable
If athletic website is down:
> "Could not access [School]'s athletic website. Try again later or provide an alternative URL."

### Ambiguous Coach Name
If a coach name is too common to research:
> "Coach [Name] has a common name. Found multiple coaches with this name. Marking as AMBIGUOUS - manual verification recommended."

### No Career History Found
If research finds nothing:
> "No career history found for [Coach]. They may be new to coaching or have limited online presence. Marking as UNVERIFIED."

## Resuming from Partial State

If a search fails mid-way (network error, timeout, etc.), the cache will contain partial data. Here's how to resume:

### Check Current State

Run the cache status check:
```bash
cd scripts && python3 cache_utils.py "[SCHOOL NAME]"
```

This will show:
- How many coaches are in the roster
- How many have career data cached
- Which specific coaches are missing data
- A recommendation (usually "resume_research")

### Resume Career Research

When resuming, **only research the missing coaches**:

1. Get the list of missing coaches from cache_utils.py output
2. Skip Step 3 (roster already exists)
3. In Step 4, spawn Career Research Agents for **only the missing coaches**:

```
Task: Research coach careers (resume batch)
Agent type: general-purpose
Prompt: Follow the instructions in prompts/career_research.md. Research career history for these coaches:
1. [Missing Coach 1] - [Position] at [School]
2. [Missing Coach 2] - [Position] at [School]

Return JSON array with career data for each coach.
```

4. Save results to individual coach files in `cache/[school_name]/coaches/`
5. Run cache_utils.py again to verify completion
6. Continue to Step 5 (Verification) and Step 6 (Cross-Reference)

### Example Resume Flow

```
User: "Resume Oregon search"

Claude: Let me check the cache status for Oregon.

[Runs: python3 cache_utils.py "University of Oregon"]

Output shows:
- Roster coaches: 28
- Coaches with career data: 24
- Missing: Parker Flemming, Will Stein, Tosh Lupoi, Cutter Leftwich, Dallas Warmack

Claude: Found partial data for Oregon. 24 of 28 coaches complete.
Missing career data for 4 coaches:
- Parker Flemming
- Will Stein
- Tosh Lupoi
- Cutter Leftwich
- Dallas Warmack

Shall I resume research for these 4 coaches?

User: Yes

[Spawns Career Research Agent for the 4 missing coaches]
[Saves results]
[Continues to Cross-Reference]
```

### Force Fresh Start

If the cached data seems corrupted or outdated, delete the cache and start fresh:
```bash
rm -rf cache/[school_name]/
```

Then run the search again from Step 1.

## Data Quality Tracking

Every coach in the output has a Data Quality rating:
- **VERIFIED**: Career history found with source URLs
- **PARTIAL**: Some history found, some gaps or missing sources
- **UNVERIFIED**: No sources, or ambiguous identity

Source URLs are tracked for every career entry. Entries without source URLs are flagged.

## Agent Coordination

### Agent Types Used
1. **Roster Agent**: Finds current coaching staff (1 agent per search)
2. **Career Research Agents**: Research career history (multiple agents in parallel)
3. **Verification Agent**: Quality checks all data (1 agent, may trigger re-research)

### Context Management
Each agent receives focused context:
- Roster Agent: Just needs school name and search instructions
- Career Research Agents: Get 2-3 coaches each (keeps context small)
- Verification Agent: Reviews all data but has clear pass/fail criteria

### Checkpointing
Data is saved incrementally:
- Roster saved immediately after fetch
- Each coach saved individually after research
- If search fails mid-way, restart picks up from checkpoint

## Example Full Workflow

```
User: "Check coaches at CU Boulder for NMDP connections"

Claude: I'll search for NMDP connections among CU Boulder's football coaching staff.

[Step 1: Spawn Roster Agent]
[Agent returns roster with 12 coaches]

Claude: Found 12 coaches for University of Colorado:
1. Deion Sanders - Head Coach
2. Pat Shurmur - Offensive Coordinator
3. Robert Livingston - Defensive Coordinator
[... list continues]

Proceed with career research for all 12 coaches?

User: Yes

[Step 2: Spawn 4 Career Research Agents in parallel (3 coaches each)]
[Agents complete, data saved to cache]

[Step 3: Spawn Verification Agent]
[Agent flags 2 coaches for re-research: missing career history]

[Step 4: Spawn Re-research Agent for flagged coaches]
[Re-research completes]

[Step 5: Run cross_reference.py]
[Returns 2 overlaps found]

[Step 6: Run generate_csv.py]
[CSV saved to output/]

Claude: ## Search Complete

**School:** University of Colorado
**Coaches processed:** 12
**Data quality:** 10 VERIFIED, 2 PARTIAL

**NMDP Warm Leads Found: 2**

| Coach | Overlap School | Year |
|-------|----------------|------|
| Deion Sanders | Jackson State | 2021-2022 |
| Marcus Freeman | Ohio State | 2020-2021 |

Full report saved to: output/university_of_colorado_2026-01-22.csv
```

## Troubleshooting

### "School not found in NMDP database"
The school may use a different name in the database. Check `data/school_aliases.json` and add an alias if needed.

### "Cross-reference found no overlaps"
This is often correct - most coaches won't have NMDP overlaps. Verify:
1. Coach career data looks complete
2. Schools in their history are correctly normalized
3. The years align with GITG program years

### "Too many verification retries"
Some coaches (especially quality control/GA positions) have limited online presence. Accept UNVERIFIED status and move on.

### "Agent returned malformed data"
Re-run the specific agent. If persistent, check the prompt file for clarity.

## Maintenance

### Adding School Aliases
Edit `data/school_aliases.json`:
```json
"UNIVERSITY OF EXAMPLE": ["Example U", "Example State", "EU"]
```

### Updating Year Range
Edit `config.json`:
```json
"year_range": {
  "start": 2019,
  "end": 2026
}
```

### Clearing Cache
Delete `cache/[school_name]/` to force fresh research on next query.
