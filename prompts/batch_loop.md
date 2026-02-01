# Batch Processing Loop Instructions

You are processing a batch of schools for NMDP coach cross-referencing.

## STATE MANAGEMENT

Read `batch_progress.json` at the START of every iteration. This is your only source of truth.

```bash
cat batch_progress.json
```

## COMPLETION CHECK

**Before doing anything else**, check if the batch is complete:

If `pending` array is empty AND `current_school` is null:
- Output: `<promise>BATCH_COMPLETE</promise>`
- Stop immediately. Do not process anything else.

## STUCK DETECTION

If you encounter the same error 3 times for one school:
1. Move school to `failed` array with error description
2. Continue to next school
3. Do NOT get stuck retrying indefinitely

Common failures to handle gracefully:
- No football program found → mark failed, continue
- Website unreachable → mark failed, continue
- WebSearch/WebFetch rate limited → wait briefly, retry once, then mark failed
- Coach research returns no data → complete with partial data, don't fail

## WORKFLOW FOR EACH SCHOOL

### Step 1: Claim the School
1. Read `batch_progress.json`
2. Take the FIRST school from `pending` array
3. Move it to `current_school`
4. Save `batch_progress.json` immediately

### Step 2: Check Cache Status
```bash
cd scripts && python3 cache_utils.py "[SCHOOL NAME]"
```

Follow the recommendation:
- `use_cache` → Skip to Step 5
- `refresh_recommended` → Proceed to Step 3 (or use stale cache if acceptable)
- `resume_research` → Skip to Step 4 with only missing coaches
- `no_cache` → Proceed to Step 3

### Step 3: Retrieve Roster
Spawn a Task agent to find the coaching staff:
- Agent type: `general-purpose`
- Follow instructions in `prompts/roster_search.md`
- Save roster to `cache/[school_name]/roster.json`

If no football program found:
- Mark school as failed with reason "No football program"
- Continue to next school

### Step 4: Research Careers
For each coach (or missing coaches if resuming):
- Spawn Task agents for career research (batch 2-3 coaches per agent)
- Follow instructions in `prompts/career_research.md`
- Save each coach to `cache/[school_name]/coaches/[coach_name].json`

### Step 5: Cross-Reference
Run the deterministic cross-reference:
```bash
cd scripts && python3 cross_reference.py ../cache/[school_name]/coaches ../data/gitg_school_years.json ../data/school_aliases.json ../config.json
```

### Step 6: Generate CSV
```bash
cd scripts && python3 generate_csv.py "[school_name]"
```

### Step 7: Update Progress
1. Move school from `current_school` to `completed` array
2. Clear `current_school` to null
3. Update `last_updated` timestamp
4. Save `batch_progress.json`

### Step 7.5: Export to Google Sheets

After each school completes, export all cached data to Google Sheets.

1. Check if `sheets_export.enabled` is true in `batch_progress.json`
2. If enabled, run the export:
```bash
cd scripts && python3 google_sheets_export.py "[SHEET_ID from sheets_export.sheet_id]"
```

3. **On success:**
   - Update `sheets_export.last_successful_export` to current timestamp
   - Update `sheets_export.last_export_school_count` to `len(completed)`
   - Save `batch_progress.json`

4. **On failure:**
   - Log a warning with the error message
   - Add entry to `sheets_export.failed_exports`:
     ```json
     {"school": "[SCHOOL_NAME]", "timestamp": "[ISO_TIMESTAMP]", "error": "[ERROR_MESSAGE]"}
     ```
   - Save `batch_progress.json`
   - **Continue to next school** - do NOT stop the batch

**Note:** The export script rebuilds the entire sheet from ALL cached data. This ensures:
- Data from previous batch runs is preserved
- No duplicates possible
- Always a complete, accurate snapshot

### Step 8: Report Progress
Output a progress message:
```
Completed [N] of [TOTAL]. Just finished: [SCHOOL]. Status: SUCCESS
Overlaps found: [X]
```

## GUARDRAILS

- ALWAYS read `batch_progress.json` fresh at iteration start
- ALWAYS save `batch_progress.json` after ANY state change
- If a school fails, log reason and CONTINUE to next school
- If roster search finds no football program, mark as failed and continue
- If WebSearch/WebFetch fails repeatedly, mark school as failed and continue
- Do NOT retry a failed school more than once per batch run
- Do NOT get stuck on verification retries - after 2 retries, accept partial data

## CONTEXT MANAGEMENT

After completing each school, the iteration ends naturally.
Ralph will restart with fresh context for the next school.

## ERROR RECOVERY

If you find `current_school` is set when you start:
- The previous iteration was interrupted mid-processing
- You may either:
  1. Continue processing that school from where it left off (check cache)
  2. Reset it to pending and start fresh

Check the cache to determine where it stopped:
```bash
ls cache/[school_name]/ 2>/dev/null || echo "No cache exists"
```

## FILE LOCATIONS

- Progress tracker: `batch_progress.json` (project root)
- School list: `data/target_schools_west.json`
- Cache: `cache/[school_name]/`
- Output: `output/[school_name]_[date].csv`
- Scripts: `scripts/`
- Prompts: `prompts/`

## EXAMPLE ITERATION

```
[Read batch_progress.json]
Batch: West Region 2026
Pending: ["University of Oregon", "USC", ...]
Current: null

[Claim first pending school]
Moving "University of Oregon" to current_school
[Save batch_progress.json]

[Check cache]
$ python3 cache_utils.py "University of Oregon"
Recommendation: no_cache

[Spawn roster agent]
Found 28 coaches for University of Oregon

[Spawn career research agents - 10 agents, 3 coaches each]
Researched all 28 coaches

[Run cross-reference]
Found 2 NMDP overlaps

[Generate CSV]
Saved to output/university_of_oregon_2026-01-31.csv

[Update progress]
Moving "University of Oregon" to completed
[Save batch_progress.json]

Completed 1 of 24. Just finished: University of Oregon. Status: SUCCESS
Overlaps found: 2
```
