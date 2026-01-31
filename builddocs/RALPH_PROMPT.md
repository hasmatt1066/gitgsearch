# Ralph Wiggum Batch Prompt

Copy the command below to launch the batch processing loop.

---

## Launch Command

```bash
/ralph-loop "You are processing a batch of schools for NMDP coach cross-referencing.

## STATE MANAGEMENT
Read batch_progress.json at the START of every iteration. This is your only source of truth.

## COMPLETION CHECK
If 'pending' array is empty and 'current_school' is null:
  Output: <promise>BATCH_COMPLETE</promise>
  Stop immediately.

## STUCK DETECTION
If you encounter the same error 3 times for one school:
  - Move school to 'failed' array with error description
  - Continue to next school
  - Do NOT get stuck retrying indefinitely

## WORKFLOW FOR EACH SCHOOL
1. Take FIRST school from 'pending', move to 'current_school'
2. Save batch_progress.json immediately
3. Run: cd scripts && python3 cache_utils.py \"[SCHOOL NAME]\"
4. Follow cache_utils recommendation (use_cache, refresh, resume, or no_cache)
5. Execute the GITG workflow per CLAUDE.md
6. Run cross_reference.py and generate_csv.py
7. On success: move school to 'completed', clear 'current_school'
8. On failure: move school to 'failed' with reason, clear 'current_school'
9. Save batch_progress.json
10. Output progress: 'Completed [N] of [TOTAL]. Just finished: [SCHOOL]. Status: [SUCCESS/FAILED]'

## GUARDRAILS
- ALWAYS read batch_progress.json fresh at iteration start
- ALWAYS save batch_progress.json after ANY state change
- If a school fails, log reason and CONTINUE to next school
- If roster search finds no football program, mark as failed and continue
- If WebSearch/WebFetch fails repeatedly, mark school as failed and continue
- Do NOT retry a failed school more than once per batch run

## CONTEXT MANAGEMENT
After completing each school, the iteration ends naturally.
Ralph will restart with fresh context for the next school.

Working directory: /mnt/c/Users/mhast/Desktop/gitgsearch2" --max-iterations 200 --completion-promise "BATCH_COMPLETE"
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/ralph-loop "..." --max-iterations N` | Start loop |
| `/cancel-ralph` | Stop loop |
| `Ctrl+C` | Interrupt |

---

## Iteration Limits by Batch Size

| Schools | Recommended --max-iterations |
|---------|------------------------------|
| 5 (test) | 50 |
| 10 | 100 |
| 25 | 200 |
| 50 | 350 |
| 100 | 600 |

Assumes ~5-7 iterations per school (roster + research batches + verification + cross-reference).

---

## Monitoring During Run

```bash
# Watch progress file
watch -n 30 'cat batch_progress.json | jq "{ completed: (.completed | length), failed: (.failed | length), pending: (.pending | length), current: .current_school }"'

# Quick status
cat batch_progress.json | jq '.completed | length'

# See failures
cat batch_progress.json | jq '.failed'
```

---

## Recovery After Interruption

If interrupted mid-school:

```bash
# Check current state
cat batch_progress.json | jq '.current_school'

# Reset current school back to pending
cd scripts && python3 batch_resume.py

# Restart Ralph loop (same command)
```
