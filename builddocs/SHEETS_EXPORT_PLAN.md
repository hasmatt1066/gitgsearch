# Plan: Add Google Sheets Export to Batch Loop

## Status: IMPLEMENTED

## Summary

Google Sheets export now happens automatically after each school completes in the batch loop.

## Implementation Details

### 1. `batch_progress.json` - New `sheets_export` Block

```json
{
  "sheets_export": {
    "enabled": true,
    "sheet_id": "16XA3nRP9dspdTStYgm__PYKZY3qNofqoxmakGhXfg-I",
    "last_successful_export": null,
    "last_export_school_count": 0,
    "failed_exports": []
  }
}
```

### 2. `prompts/batch_loop.md` - Added Step 7.5

After Step 7 (Update Progress), before Step 8 (Report Progress):

```markdown
### Step 7.5: Export to Google Sheets

After each school completes, export all cached data to Google Sheets.

1. Check if `sheets_export.enabled` is true
2. Run: `python3 google_sheets_export.py "[SHEET_ID]"`
3. On success: Update tracking fields
4. On failure: Log to `failed_exports`, continue to next school
```

### 3. `CLAUDE.md` - Documented Behavior

Added "Batch Loop Auto-Export" section under Google Sheets Integration.

## How It Works

### Export Frequency
- **Every school** - exports after each school completes

### Data Accumulation Across Batches
The export script scans ALL cached data, not just the current batch:

```
Batch 1: Processes 50 schools → cache has 50 schools
  → Export includes all 50 schools

Batch 2: Processes 50 more → cache now has 100 schools
  → Export includes all 100 schools
```

### Failure Handling
- Export failure does NOT stop the batch
- Failure is logged to `sheets_export.failed_exports`
- Next successful export will include all data (self-healing)

### Failed Export Entry Format
```json
{
  "school": "University of Example",
  "timestamp": "2026-01-31T12:00:00.000000",
  "error": "API rate limit exceeded"
}
```

## Files Modified

| File | Change |
|------|--------|
| `batch_progress.json` | Added `sheets_export` block |
| `prompts/batch_loop.md` | Added Step 7.5 |
| `CLAUDE.md` | Added Batch Loop Auto-Export documentation |

## Rollback

To disable auto-export:
```json
{
  "sheets_export": {
    "enabled": false,
    ...
  }
}
```

Batch will continue processing without export attempts.

## Manual Export

Can always run manually:
```bash
cd scripts && python3 google_sheets_export.py "16XA3nRP9dspdTStYgm__PYKZY3qNofqoxmakGhXfg-I"
```
