# gitgsearch

A CLI tool that finds **warm leads** for NMDP's *Get In The Game* (GITG)
programme by cross-referencing current college football coaching staff against
NMDP's historical partnership records.

A coach who ran a GITG programme at a previous school already understands the
mission. This finds those people systematically, where previously there was no
way to.

## How it works

Four stages, run per school:

1. **Roster** — retrieve the current coaching staff for a target school
2. **Career research** — trace each coach's history over the last six years
3. **Cross-reference** — match that history against the GITG partnership database
4. **Report** — emit a structured CSV of the overlaps

Each stage is driven by a prompt in [`prompts/`](prompts/) and executed by
Claude Code; `scripts/` holds the Python that orchestrates, caches, and exports.

## Setup

```bash
pip install -r requirements.txt   # if present; otherwise install per-script imports
cp .env.example .env
```

`.env` needs:

| Key | Purpose |
|---|---|
| `GOOGLE_SHEETS_CREDS` | path to a Google service-account JSON |
| `GITG_SHEET_ID` | the target Google Sheet ID (from its URL) |

The service-account JSON is **not** in this repo and must not be committed.

## Running

```bash
scripts/launch_batch.sh          # start a batch run
python scripts/batch_status.py   # check progress
python scripts/batch_resume.py   # resume an interrupted run
python scripts/generate_csv.py   # emit the report
python scripts/google_sheets_export.py   # push results to Sheets
```

Batch state is checkpointed, so a long run can be interrupted and resumed
rather than restarted.

## Layout

```
prompts/     the four stage prompts (roster, career, verification, batch loop)
scripts/     orchestration, caching, cross-reference, export
data/        school aliases, locations, territory mapping, year records
builddocs/   architecture and implementation planning
config.json  run configuration
PRD.md       full product requirements
```

## Further reading

- [`PRD.md`](PRD.md) — requirements, user stories, output spec
- [`builddocs/API_ARCHITECTURE_DESIGN.md`](builddocs/API_ARCHITECTURE_DESIGN.md)
- [`builddocs/BATCH_IMPLEMENTATION_PLAN.md`](builddocs/BATCH_IMPLEMENTATION_PLAN.md)
- [`IMPROVEMENTS.md`](IMPROVEMENTS.md) — known gaps and next steps

## Licence

No licence is currently declared — all rights reserved.
