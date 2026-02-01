# Dual-Mode Architecture: API + Claude Code CLI

## Overview

This document outlines the design for adding an API-based orchestration option to the NMDP Coach Cross-Reference System. This **supplements** (not replaces) the existing Claude Code CLI approach, providing two complementary ways to process schools.

**Design Philosophy:** Both orchestration modes share the same data layer, processing scripts, and output formats. Choose the right tool for the job.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DUAL-MODE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────┐       ┌─────────────────────┐         │
│   │   CLAUDE CODE CLI   │       │    API-BASED        │         │
│   │   + Ralph Loop      │       │    Python           │         │
│   │                     │       │                     │         │
│   │ • Interactive       │       │ • Unattended        │         │
│   │ • Flexible          │       │ • Predictable       │         │
│   │ • Human-in-loop     │       │ • Fast batch        │         │
│   │ • Edge case handling│       │ • Cost transparent  │         │
│   └──────────┬──────────┘       └──────────┬──────────┘         │
│              │                             │                     │
│              └──────────────┬──────────────┘                     │
│                             │                                    │
│                             ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              SHARED DATA LAYER                           │   │
│   │                                                          │   │
│   │  • cache/[school]/roster.json                            │   │
│   │  • cache/[school]/coaches/[name].json                    │   │
│   │  • batch_progress.json                                   │   │
│   │  • data/*.json (aliases, locations, territories)         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │           SHARED PROCESSING SCRIPTS                      │   │
│   │                                                          │   │
│   │  • cross_reference.py                                    │   │
│   │  • generate_csv.py                                       │   │
│   │  • generate_master_report.py                             │   │
│   │  • google_sheets_export.py                               │   │
│   │  • cache_utils.py                                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Two Modes?

### Claude Code CLI Strengths

| Strength | Value |
|----------|-------|
| **Interactive debugging** | See agent reasoning, intervene when stuck |
| **Flexible prompts** | Natural language adapts to edge cases |
| **Zero API setup** | No additional keys beyond Claude Code |
| **Human-in-the-loop** | Easy to pause, review, adjust |
| **Rich context** | Agents understand nuanced instructions |
| **Conversational** | Ad-hoc queries ("check Coach X history") |

### Claude Code CLI Limitations

| Limitation | Impact |
|------------|--------|
| Session rate limits | "You've hit your limit" during parallel agents |
| Requires terminal | Must keep session active |
| Unpredictable throughput | Rate limits vary by time/usage |

### API-Based Strengths

| Strength | Value |
|----------|-------|
| **Predictable rate limits** | Token-based, not session-based |
| **True parallelism** | Full async control with `asyncio` |
| **Cost transparency** | ~$0.60/school (measurable) |
| **Unattended operation** | Run via cron, cloud function, overnight |
| **Better error handling** | Full control over retries and logging |
| **Faster throughput** | ~3-5 min/school vs ~10-15 min |

### API-Based Limitations

| Limitation | Impact |
|------------|--------|
| Less flexible | Structured prompts, less adaptable |
| Setup required | Need Anthropic + Tavily API keys |
| Less interactive | Can't easily intervene mid-process |

---

## When to Use Which

| Situation | Recommended | Reason |
|-----------|-------------|--------|
| First time processing a school | CLI | Handle edge cases interactively |
| Debugging a failed school | CLI | See reasoning, intervene |
| Processing 20+ schools overnight | API | Unattended, predictable |
| Hit Claude Code rate limits | API | Switch mid-batch |
| Complex/unusual roster page | CLI | Flexible parsing |
| Simple/known roster patterns | API | Faster |
| Ad-hoc queries ("check Coach X") | CLI | Conversational |
| Resuming partial research | Either | Both read same cache |
| Cost-sensitive batch | API | Transparent pricing |

---

## Shared Data Contracts

**Critical:** Both orchestrators must produce identical data formats so all downstream processing works seamlessly.

### roster.json

```json
{
  "school": "University of Oregon",
  "school_normalized": "UNIVERSITY OF OREGON",
  "retrieved_date": "2026-02-01",
  "official_roster_url": "https://goducks.com/sports/football/coaches",
  "roster_notes": "Optional notes about the roster",
  "coaches": [
    {"name": "Dan Lanning", "position": "Head Coach"},
    {"name": "Will Stein", "position": "Offensive Coordinator"}
  ]
}
```

### coaches/[name].json

```json
{
  "name": "Dan Lanning",
  "current_position": "Head Coach",
  "current_school": "University of Oregon",
  "career_history": [
    {
      "year": "2022-present",
      "school": "University of Oregon",
      "position": "Head Coach",
      "source_url": "https://goducks.com/..."
    },
    {
      "year": "2019-2021",
      "school": "University of Georgia",
      "position": "Defensive Coordinator",
      "source_url": "https://..."
    }
  ],
  "data_quality": "VERIFIED",
  "notes": "Former Georgia DC, led Oregon to CFP",
  "last_updated": "2026-02-01"
}
```

### batch_progress.json

```json
{
  "batch_name": "West Region Full 2026",
  "source_file": "/path/to/target_schools_west.json",
  "total_schools": 147,
  "started": "2026-01-31T10:39:24.658440",
  "last_updated": "2026-02-01T13:52:30.000000",
  "current_school": "University of Oregon",
  "completed": ["School A", "School B"],
  "failed": [],
  "pending": ["School C", "School D"],
  "sheets_export": {
    "enabled": true,
    "sheet_id": "...",
    "last_successful_export": "2026-02-01T09:46:00"
  }
}
```

**Both orchestrators read and write these exact formats.**

---

## Hybrid Scenarios

### Scenario 1: Start with CLI, Finish with API

```bash
# Morning: Interactive processing with Claude Code
/ralph-loop --prompt "Read prompts/batch_loop.md..."
# ... process 10 schools, hit rate limit ...
/ralph-loop:cancel-ralph

# Afternoon: Continue with API (unattended)
python api_orchestrator.py --resume
# Picks up from batch_progress.json, processes remaining schools
```

### Scenario 2: API Batch with CLI Cleanup

```bash
# Overnight: Run API batch
python api_orchestrator.py --max-schools 50

# Morning: Check results
python batch_status.py
# Shows: 48 completed, 2 failed

# Debug failures interactively with Claude Code
# (Just run normal workflow for those specific schools)
```

### Scenario 3: Mixed by School Complexity

```bash
# Simple schools via API (fast)
python api_orchestrator.py --schools "School A,School B,School C"

# Complex school via CLI (flexible)
# Use Claude Code interactively for tricky roster pages
```

### Scenario 4: Resume Partial Research

```bash
# Either orchestrator can resume incomplete research
python cache_utils.py "University of Oregon"
# Output: "Missing career data for: Coach A, Coach B"

# Resume with CLI
# (Claude Code reads existing cache, only researches missing coaches)

# OR resume with API
python api_orchestrator.py --school "University of Oregon" --resume-research
```

---

## File Structure (Dual-Mode)

```
gitgsearch2/
├── CLAUDE.md                     # Claude Code instructions (UNCHANGED)
├── batch_progress.json           # Shared state (UNCHANGED)
├── config.json                   # Shared config (EXTENDED for API settings)
│
├── prompts/                      # Claude Code prompts (UNCHANGED)
│   ├── batch_loop.md
│   ├── roster_search.md
│   └── career_research.md
│
├── scripts/
│   │
│   │ # SHARED SCRIPTS (work with both modes)
│   ├── cross_reference.py        # UNCHANGED
│   ├── generate_csv.py           # UNCHANGED
│   ├── generate_master_report.py # UNCHANGED
│   ├── google_sheets_export.py   # UNCHANGED
│   ├── cache_utils.py            # UNCHANGED
│   ├── batch_init.py             # UNCHANGED
│   ├── batch_status.py           # UNCHANGED
│   ├── batch_resume.py           # UNCHANGED
│   │
│   │ # API-SPECIFIC (NEW)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Main API batch controller
│   │   ├── roster_agent.py       # Web scraping + Claude API
│   │   ├── career_agent.py       # Search API + Claude API
│   │   ├── search_client.py      # Tavily wrapper
│   │   ├── rate_limiter.py       # Rate limiting utilities
│   │   └── models.py             # Pydantic data models
│   │
│   ├── api_orchestrator.py       # CLI entry point for API mode
│   └── requirements-api.txt      # API-specific dependencies
│
├── cache/                        # Shared cache (UNCHANGED format)
│   └── [school_name]/
│       ├── roster.json
│       └── coaches/
│           └── [coach_name].json
│
├── output/                       # Shared output (UNCHANGED)
│   └── [school]_[date].xlsx
│
└── data/                         # Shared data files (UNCHANGED)
    ├── gitg_school_years.json
    ├── school_aliases.json
    ├── school_locations.json
    └── territory_mapping.json
```

---

## Configuration Extension

Add API settings to existing `config.json`:

```json
{
  "year_range": {
    "start": 2020,
    "end": 2026
  },
  "cache_staleness_days": 30,
  "max_retries_per_coach": 2,
  "coaches_per_research_agent": 3,

  "api": {
    "enabled": true,
    "anthropic_model": "claude-sonnet-4-20250514",
    "search_provider": "tavily",
    "max_searches_per_coach": 3,
    "max_concurrent_coaches": 5,
    "max_concurrent_api_calls": 10,
    "retry_attempts": 3,
    "retry_delay_seconds": 2,
    "cost_tracking": true
  }
}
```

Claude Code mode ignores the `api` section. API mode uses it.

---

## API Mode: Component Design

### 1. Orchestrator (`scripts/api/orchestrator.py`)

```python
class BatchOrchestrator:
    """API-based batch processor that shares data layer with CLI mode."""

    def __init__(self, config_path: str, progress_path: str):
        self.config = load_config(config_path)
        self.progress = load_progress(progress_path)
        self.anthropic = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.search_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        self.roster_agent = RosterAgent(self.anthropic)
        self.career_agent = CareerResearchAgent(self.anthropic, self.search_client)

    async def process_school(self, school: str) -> SchoolResult:
        """Process a single school - same output as CLI mode."""
        cache_dir = get_cache_dir(school)

        # 1. Check for existing roster (may have been started by CLI)
        roster = load_cached_roster(cache_dir)
        if not roster:
            roster = await self.roster_agent.get_roster(school)
            save_roster(cache_dir, roster)  # Same format as CLI

        # 2. Check for existing career data (resume support)
        missing_coaches = get_coaches_missing_career_data(cache_dir, roster)

        # 3. Research only missing coaches
        if missing_coaches:
            careers = await self.career_agent.research_parallel(missing_coaches, school)
            for career in careers:
                save_coach_career(cache_dir, career)  # Same format as CLI

        # 4. Run shared scripts (same as CLI uses)
        subprocess.run(["python", "cross_reference.py", cache_dir, ...])
        subprocess.run(["python", "generate_csv.py", school])
        subprocess.run(["python", "google_sheets_export.py", SHEET_ID])

        return SchoolResult(school, len(roster.coaches), count_overlaps(school))

    async def run_batch(self, max_schools: int = None):
        """Process pending schools from shared batch_progress.json."""
        pending = self.progress["pending"]

        for school in pending[:max_schools]:
            self.progress["current_school"] = school
            self.save_progress()  # Same file CLI reads

            try:
                result = await self.process_school(school)
                self.progress["completed"].append(school)
                self.progress["pending"].remove(school)
            except Exception as e:
                self.progress["failed"].append({
                    "school": school,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

            self.save_progress()
```

### 2. Roster Agent (`scripts/api/roster_agent.py`)

```python
class RosterAgent:
    """Fetch and parse coaching rosters via web scraping + Claude API."""

    async def get_roster(self, school: str) -> Roster:
        # 1. Find roster URL
        url = await self._find_roster_url(school)

        # 2. Fetch HTML
        html = await self._fetch_page(url)

        # 3. Try direct parsing (BeautifulSoup)
        coaches = self._try_direct_parse(html)

        # 4. Claude fallback for complex pages
        if not coaches:
            coaches = await self._claude_extract(html, school)

        # Return in SAME FORMAT as CLI mode produces
        return Roster(
            school=school,
            school_normalized=normalize_school_name(school),
            retrieved_date=date.today().isoformat(),
            official_roster_url=url,
            coaches=coaches
        )
```

### 3. Career Research Agent (`scripts/api/career_agent.py`)

```python
class CareerResearchAgent:
    """Research coach careers via Tavily search + Claude synthesis."""

    async def research_coach(self, coach: Coach, school: str) -> CareerData:
        # 1. Search for career info
        search_results = await self._search_coach(coach.name, school)

        # 2. Synthesize with Claude
        career = await self._claude_synthesize(coach, school, search_results)

        # Return in SAME FORMAT as CLI mode produces
        return CareerData(
            name=coach.name,
            current_position=coach.position,
            current_school=school,
            career_history=career.history,
            data_quality=career.quality,
            notes=career.notes,
            last_updated=date.today().isoformat()
        )

    async def research_parallel(
        self, coaches: List[Coach], school: str, max_concurrent: int = 5
    ) -> List[CareerData]:
        """Research multiple coaches concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def with_limit(coach):
            async with semaphore:
                return await self.research_coach(coach, school)

        return await asyncio.gather(*[with_limit(c) for c in coaches])
```

---

## Search API Selection

| Provider | Cost | Quality | Free Tier | Recommendation |
|----------|------|---------|-----------|----------------|
| **Tavily** | $0.01/search | Excellent | 1000/day | **Recommended** |
| Brave | $0.009/search | Good | 2000/month | Alternative |
| Serper | $0.004/search | Good | 2500 credits | Budget option |

**Tavily selected for:**
- Built for AI research use cases
- Clean, relevant snippets
- Good free tier for development

---

## Cost Analysis (API Mode Only)

| Scope | Cost |
|-------|------|
| Per coach | ~$0.04 (3 searches + 1 Claude call) |
| Per school (15 coaches avg) | ~$0.60 |
| Full batch (147 schools) | ~$88 |

Claude Code mode has no per-call costs (subscription-based).

---

## CLI Interface (API Mode)

```bash
# Process all pending schools
python api_orchestrator.py

# Limit number of schools
python api_orchestrator.py --max-schools 10

# Process single school
python api_orchestrator.py --school "University of Oregon"

# Resume incomplete research for a school
python api_orchestrator.py --school "University of Oregon" --resume-research

# Dry run (no API calls, show what would happen)
python api_orchestrator.py --dry-run

# Verbose output
python api_orchestrator.py --verbose
```

---

## Implementation Phases

### Phase 1: Foundation (2-3 days)

- [ ] Create `scripts/api/` directory structure
- [ ] Create data models (`models.py`) matching existing formats
- [ ] Implement rate limiter
- [ ] Create orchestrator skeleton with progress file integration
- [ ] Verify it can read/write `batch_progress.json` correctly
- [ ] Set up logging

**Deliverable:** `python api_orchestrator.py --dry-run` works

### Phase 2: Roster Agent (1-2 days)

- [ ] Implement URL discovery with known domain mappings
- [ ] Implement HTML fetching with aiohttp
- [ ] Implement BeautifulSoup parsing for common patterns
- [ ] Implement Claude API fallback
- [ ] Verify output matches CLI format exactly
- [ ] Test with 5 schools (compare to existing cache)

**Deliverable:** Can fetch rosters, output matches CLI

### Phase 3: Career Research Agent (2-3 days)

- [ ] Set up Tavily API integration
- [ ] Implement search query generation
- [ ] Implement Claude synthesis with structured output
- [ ] Implement parallel research with semaphore
- [ ] Verify output matches CLI format exactly
- [ ] Test with 20 coaches (compare to existing cache)

**Deliverable:** Can research careers, output matches CLI

### Phase 4: Integration & Testing (1-2 days)

- [ ] Wire up full pipeline
- [ ] Test end-to-end with 3 new schools
- [ ] Verify cross_reference.py works with API-generated cache
- [ ] Verify google_sheets_export.py works
- [ ] Test hybrid scenario: start with CLI, finish with API
- [ ] Test resume scenario: API picks up CLI partial work

**Deliverable:** Full pipeline works, interoperable with CLI

### Phase 5: Production Hardening (1 day)

- [ ] Add cost tracking and reporting
- [ ] Add progress display (rich)
- [ ] Create `.env.example` for API keys
- [ ] Update CLAUDE.md with API mode instructions
- [ ] Document hybrid workflows

**Deliverable:** Ready for production use alongside CLI

---

## Environment Setup (API Mode)

```bash
# Install API-specific dependencies
pip install -r scripts/requirements-api.txt

# Set up environment variables
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TAVILY_API_KEY=tvly-...

# Verify setup
python api_orchestrator.py --dry-run
```

### Dependencies (`requirements-api.txt`)

```
anthropic>=0.18.0
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
tavily-python>=0.3.0
tenacity>=8.2.0
pydantic>=2.5.0
python-dotenv>=1.0.0
rich>=13.0.0
```

---

## Comparison Summary

| Aspect | Claude Code CLI | API Mode |
|--------|-----------------|----------|
| **Best for** | Interactive, edge cases, debugging | Batch processing, overnight runs |
| **Rate limits** | Session-based (unpredictable) | Token-based (predictable) |
| **Cost** | Subscription | ~$0.60/school |
| **Speed** | ~10-15 min/school | ~3-5 min/school |
| **Flexibility** | High (natural language) | Medium (structured) |
| **Unattended** | Requires terminal | Yes (cron, cloud) |
| **Setup** | None | API keys required |
| **Interoperability** | Full (shared data layer) | Full (shared data layer) |

---

## Key Principle: Data Layer Compatibility

**The most important design constraint:**

Both orchestrators MUST produce identical cache files so that:
1. CLI can resume API-started work
2. API can resume CLI-started work
3. All processing scripts work with either source
4. Hybrid workflows are seamless

This is enforced by:
- Shared Pydantic models defining exact schemas
- Integration tests comparing CLI vs API output
- Using existing scripts (cross_reference, generate_csv, etc.) unchanged

---

## Open Questions

1. **Search API** - Start with Tavily, evaluate Brave if needed?
2. **Claude model** - Sonnet for all, or Haiku for simple extractions?
3. **Hosting** - Local only, or option for AWS Lambda deployment?
4. **Domain mapping** - Build incrementally or populate upfront?

---

## Next Steps

1. ✅ Design approved
2. Set up Tavily API account
3. Create `scripts/api/` directory
4. Begin Phase 1 implementation
