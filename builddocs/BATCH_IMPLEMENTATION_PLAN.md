# Batch Processing Implementation Plan

## Overview

Implement autonomous batch processing of multiple schools using the Ralph Wiggum plugin for Claude Code. This enables processing all western region colleges without manual intervention.

**Goal:** Process 50-100 schools autonomously, generating NMDP warm lead reports for each.

---

## Phase 1: Data Files

### 1.1 School List Definition
- [x] Create `data/target_schools_west.json`
- [x] Define JSON schema with required fields:
  - `name`: Official school name
  - `conference`: Athletic conference
  - `state`: State abbreviation (for regional grouping)
  - `priority`: Optional ranking (1=high, 2=medium, 3=low)
- [x] Populate with initial school list (24 western schools)
- [x] Validate all school names against `data/school_aliases.json`

**Schema:**
```json
{
  "batch_name": "West Region 2026",
  "created": "2026-01-31",
  "schools": [
    {
      "name": "University of Colorado",
      "conference": "Big 12",
      "state": "CO",
      "priority": 1
    }
  ]
}
```

### 1.2 Progress Tracker
- [x] Create `batch_progress.json` schema
- [x] Include fields: started, last_updated, current_school, completed, failed, pending
- [x] Failed entries should include error reason

**Schema:**
```json
{
  "batch_name": "West Region 2026",
  "started": null,
  "last_updated": null,
  "current_school": null,
  "completed": [],
  "failed": [],
  "pending": []
}
```

---

## Phase 2: Scripts

### 2.1 Batch Initialization Script
- [x] Create `scripts/batch_init.py`
- [x] Read school list from `data/target_schools_west.json`
- [x] Initialize `batch_progress.json` with all schools in pending
- [x] Set started timestamp
- [x] Validate no duplicate schools
- [x] Handle case where progress file already exists (prompt to reset or resume)

**Usage:**
```bash
cd scripts && python3 batch_init.py
# or
cd scripts && python3 batch_init.py --reset  # Force fresh start
```

### 2.2 Batch Status Script
- [x] Create `scripts/batch_status.py`
- [x] Display summary: X completed, Y failed, Z pending
- [x] Show current school in progress (if any)
- [x] Show list of failed schools with reasons
- [x] Calculate estimated completion (based on avg time per school)

**Usage:**
```bash
cd scripts && python3 batch_status.py
```

### 2.3 Batch Resume Script
- [x] Create `scripts/batch_resume.py`
- [x] Move current_school back to front of pending (if interrupted mid-school)
- [x] Clear current_school field
- [x] Display resume instructions

**Usage:**
```bash
cd scripts && python3 batch_resume.py
```

### 2.4 Aggregate Results Script
- [x] ~~Create `scripts/aggregate_results.py`~~ (Using existing `generate_master_report.py`)
- [x] Combine all individual school CSVs into master CSV
- [x] Generate summary statistics:
  - Total schools processed
  - Total coaches researched
  - Total NMDP overlaps found
  - Schools with most overlaps
- [x] Output to `output/master_report_[date].xlsx`

**Usage:**
```bash
cd scripts && python3 generate_master_report.py
```

---

## Phase 3: Ralph Wiggum Configuration

### 3.1 Verify Prerequisites
- [ ] Confirm Ralph Wiggum plugin installed: `/plugin list`
- [ ] Confirm jq installed: `which jq`
- [ ] Test Ralph with simple loop (3 iterations max)

### 3.2 Create Batch Prompt File
- [x] Create `prompts/batch_loop.md`
- [x] Include all guardrails from research
- [x] Include stuck detection (3 retries max)
- [x] Include escape hatches for common failures
- [x] Include progress output format

### 3.3 Create Launch Script
- [x] Create `scripts/launch_batch.sh`
- [x] Wrapper script that:
  - Verifies batch_progress.json exists
  - Shows current status
  - Confirms user wants to start/resume
  - Generates Ralph command with correct parameters

**Usage:**
```bash
./scripts/launch_batch.sh
```

---

## Phase 4: Testing

### 4.1 Unit Tests
- [ ] Test batch_init.py with sample school list
- [ ] Test batch_status.py with various progress states
- [ ] Test batch_resume.py recovery logic
- [ ] Test aggregate_results.py with sample CSVs

### 4.2 Integration Test (3 Schools)
- [ ] Create test school list with 3 schools (mix of cached/uncached)
- [ ] Run full batch with `--max-iterations 30`
- [ ] Verify progress tracking works correctly
- [ ] Verify failure handling (intentionally include one problematic school)
- [ ] Verify aggregated output is correct

### 4.3 Stress Test (10 Schools)
- [ ] Run batch with 10 schools
- [ ] Monitor for context degradation
- [ ] Monitor for rate limiting
- [ ] Measure average time per school
- [ ] Document any issues encountered

---

## Phase 5: Production Run

### 5.1 Prepare Full School List
- [ ] Compile complete list of western region schools
- [ ] Validate all school names
- [ ] Prioritize schools (if processing in priority order)
- [ ] Save to `data/target_schools_west.json`

### 5.2 Pre-Flight Checklist
- [ ] Clear any stale cache if needed
- [ ] Verify disk space for cache and output
- [ ] Initialize batch_progress.json
- [ ] Test network connectivity
- [ ] Set up monitoring (terminal with `watch` command)

### 5.3 Execute
- [ ] Launch Ralph batch loop
- [ ] Monitor first 3-5 schools
- [ ] Verify progress is being saved correctly
- [ ] Check for any recurring errors

### 5.4 Post-Processing
- [ ] Run aggregate_results.py
- [ ] Review failed schools
- [ ] Manually retry any critical failures
- [ ] Generate final report

---

## File Checklist

| File | Status | Description |
|------|--------|-------------|
| `data/target_schools_west.json` | [x] | School list for batch processing (24 schools) |
| `batch_progress.json` | [x] | Progress tracking (root level) |
| `scripts/batch_init.py` | [x] | Initialize progress from school list |
| `scripts/batch_status.py` | [x] | Display batch progress |
| `scripts/batch_resume.py` | [x] | Reset interrupted school |
| `scripts/generate_master_report.py` | [x] | Combine all CSVs (pre-existing) |
| `scripts/launch_batch.sh` | [x] | Wrapper to start Ralph loop |
| `prompts/batch_loop.md` | [x] | Ralph prompt with guardrails |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Session disconnect | File-based state survives; use batch_resume.py |
| Rate limiting | Conservative iteration limit; monitor early |
| Infinite loop on one school | 3-retry limit then mark failed and continue |
| Context degradation | One school per iteration; natural context reset |
| Corrupted progress file | Git commit progress file periodically |
| Cost overrun | Set --max-iterations conservatively |

---

## Success Criteria

- [ ] All schools in pending list are processed (completed or failed with reason)
- [ ] Aggregated CSV contains all warm leads across all schools
- [ ] Failed schools have clear error documentation
- [ ] Total run completes within expected iteration limit
- [ ] No manual intervention required during run

---

## Notes

- Start with 5-school test before full batch
- Monitor first few iterations before walking away
- Use `/cancel-ralph` if loop appears stuck
- Check `batch_progress.json` periodically during run
