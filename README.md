# WatchAgent

A weather monitoring service for Ottawa, Toronto, and Vancouver. It polls live conditions from Open-Meteo, detects notable weather events using historical baselines and recent readings, stores everything in SQLite, and exposes the data through a REST API.

## Architecture

```
┌──────────────────────── BOOTSTRAP (first run only) ────────────────────────┐
│                                                                           │
│  Open-Meteo          historical_ingestor          historical_readings   │
│  Archive API    ──▶  (3 cities, ~90 days)    ──▶  (deduped hourly rows) │
│                                                                           │
│                              │                                            │
│                              ▼                                            │
│                    baseline_builder  ──▶  monthly_baselines               │
│                    (per city + month)     (mean, std, min, max, p5/p95)   │
│                                                                           │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   SQLite (./data)   │
                         │─────────────────────│
                         │ historical_readings │
                         │ monthly_baselines   │
                         │ live_readings       │
                         │ events              │
                         └──────────┬──────────┘
                                    │
┌──────────────────────── LIVE LOOP (every 5 min) ─────────────────────────┐
│                                    │                                      │
│  Open-Meteo          poller        │                                      │
│  Forecast API   ──▶ (dedup store)─┼──▶ live_readings                    │
│                                    │                                      │
│                                    ▼                                      │
│                         event_engine (6 rules)                            │
│                         uses: baselines + previous reading +            │
│                               last 24 live readings                       │
│                                    │                                      │
│                                    ▼                                      │
│                              events                                       │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    ▼
                           FastAPI (:8000)
                           /health /readings /events

         Cursor skill: weather-data-analysis/scripts/analyze.py
                         (reads same SQLite DB for ad-hoc analysis)
```

**Bootstrap (first run):** `app/bootstrap.py` creates tables. If `monthly_baselines` is empty, it calls `historical_ingestor` (Open-Meteo archive) then `baseline_builder`. Live polling never hits the archive API after that.

**Live data flow:**
1. Poller fetches current conditions for each city.
2. Readings are stored only when `(city, timestamp)` is new (deduplication).
3. Event engine evaluates the reading against monthly baselines, the previous live reading, and up to 24 recent live readings.
4. Triggered events are persisted and queryable via the API.

## Technology choices

| Choice | Why |
|--------|-----|
| **FastAPI** | Lightweight, async-ready, automatic OpenAPI docs, easy query params for `/readings` and `/events`. |
| **SQLAlchemy + SQLite** | No external DB service needed; file persists in `./data` via Docker volume. Unique constraints enforce dedup at the schema level. |
| **Open-Meteo** | Free, no API key, works from Docker; separate forecast (live) and archive (historical) endpoints. |
| **pytest** | Standard Python testing; mocks for API calls keep CI fast and deterministic. |

## Setup and run

### Docker (recommended)

```bash
git clone <your-repo>
cd watchagent-challenge
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Database file: `./data/watchagent.db` (persists across container restarts)

First startup may take a minute while historical data is ingested and baselines are built.

### Local development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data

python -m app.bootstrap          # init DB + baselines if empty
python -m app.services.poller &  # background poller
uvicorn app.main:app --reload --port 8000
```

## API reference

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "readings_stored": 12,
  "events_stored": 11
}
```

### `GET /readings`

Optional query params: `city` (Ottawa | Toronto | Vancouver), `limit` (default 50).

```bash
curl "http://localhost:8000/readings?city=Toronto&limit=10"
```

```json
{
  "readings": [
    {
      "id": 1,
      "city": "Toronto",
      "timestamp": "2026-06-01T20:45",
      "temperature_2m": 16.1,
      "apparent_temperature": 15.0,
      "precipitation": 0.0,
      "wind_speed_10m": 2.4,
      "weather_code": 0
    }
  ]
}
```

Results are ordered most recent first.

### `GET /events`

Optional query params: `city`, `limit` (default 50).

```bash
curl "http://localhost:8000/events?city=Ottawa&limit=5"
```

```json
{
  "events": [
    {
      "id": 1,
      "city": "Ottawa",
      "timestamp": "2026-06-01T20:45",
      "event_type": "SUDDEN_TEMP_CHANGE",
      "reason": "temperature change exceeds 2x rolling std of recent readings",
      "value": 2.8
    }
  ]
}
```

## Event detection design

Events answer: **what happened, in which city, when, and why it was notable.** Thresholds are derived from data — not hardcoded weather constants — so the same reading means different things in different cities and seasons.

### Historical context (monthly baselines)

On first run, ~90 days of archive data (`HISTORICAL_DATA_DAYS`) is ingested per city. Monthly baselines store mean, std, min, max, and p5/p95 for temperature and wind. Live polling never hits the archive API.

| Event type | Rule | Trigger |
|------------|------|---------|
| `TEMP_ANOMALY` | TemperatureAnomalyRule | Temperature outside 2σ of monthly mean |
| `TEMP_PERCENTILE_ANOMALY` | TemperatureAnomalyRule | Temperature outside 5th–95th percentile for that city/month |
| `WIND_SPIKE` | WindSpikeRule | Wind speed outside 2σ of monthly baseline mean |
| `RECORD_HIGH` | RecordBreakRule | Temperature above historical monthly max |
| `RECORD_LOW` | RecordBreakRule | Temperature below historical monthly min |

### Recent context (last 24 hours of live readings)

| Event type | Rule | Trigger |
|------------|------|---------|
| `SUDDEN_TEMP_CHANGE` | SuddenTemperatureChangeRule | \|Δtemp\| vs previous reading > 2× rolling std of recent temps |
| `SUDDEN_WIND_CHANGE` | SuddenWindChangeRule | \|Δwind\| vs previous reading > 2× rolling std of recent wind speeds |
| `PRECIP_START` | PrecipitationChangeRule | Precipitation transitions 0 → > 0 |
| `PRECIP_STOP` | PrecipitationChangeRule | Precipitation transitions > 0 → 0 |

**Design rationale:** Historical baselines capture "unusual for this city and season." Recent-reading rules capture sudden shifts within the last day. Comparing against the **previous stored reading** (excluding the current one) avoids self-comparison bugs. City-specific baselines matter because Ottawa's normal swing differs from Vancouver's.

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

Coverage includes:
- Each event rule (positive + negative cases)
- API response shape for `/health`, `/readings`, `/events`
- Poll deduplication integration test (same API response twice → one row)
- Event engine orchestration

CI runs on every push to `main` (see `.github/workflows/ci.yml`).

## Environment variables

See `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/watchagent.db` | SQLite database path |
| `POLL_INTERVAL_SECONDS` | `300` | Seconds between poll cycles |
| `HISTORICAL_DATA_DAYS` | `90` | Days of archive data for baseline build |

## Cursor setup

This project uses Cursor rules, a custom agent, and a data analysis skill as part of the engineering workflow.

### Rules (`.cursor/rules/`)

| Rule | Purpose |
|------|---------|
| `event_rules.mdc` | Contract for event rules: interface, event dict shape, baseline-derived thresholds, safety (no exceptions/logging in rules). |
| `logging.mdc` | Log levels and required context (city name) for poll/API failures and stored readings. |
| `tests.mdc` | Test conventions: SimpleNamespace fakes, mock Open-Meteo, positive/negative cases per rule, dedup tests. |
| `git-push.mdc` | Commit message quality and require user approval before `git push`. |

### Agent (`.cursor/agents/`)

**`event-rules-reviewer`** — Scoped to event detection code. Reviews or implements rules in `app/services/event_rules/`, checks threshold math, ensures tests follow conventions, and runs pytest after changes. Does not modify Docker or API routes unless event shapes change.

Invoke via the agent picker or by referencing `@event-rules-reviewer` in chat.

### Skill (`.cursor/skills/weather-data-analysis/`)

Runnable Python script that queries the SQLite database and returns structured JSON analysis. Use when asking questions about stored readings, events, or city comparisons from within Cursor.

```bash
# Overview of stored data
python .cursor/skills/weather-data-analysis/scripts/analyze.py summary

# Compare cities by average temperature
python .cursor/skills/weather-data-analysis/scripts/analyze.py compare-cities

# Event counts by type
python .cursor/skills/weather-data-analysis/scripts/analyze.py events-breakdown

# Recent temperature trend for one city
python .cursor/skills/weather-data-analysis/scripts/analyze.py recent-trends --city Toronto --limit 24
```

See `.cursor/skills/weather-data-analysis/SKILL.md` for the full command list.

#### Verifying the skill works

1. **Have data in the database** — either run the stack or bootstrap locally:
   ```bash
   docker compose up --build
   # or: python -m app.bootstrap && python -m app.services.poller  # one cycle, then stop
   ```
   Confirm `./data/watchagent.db` exists and `/health` shows `readings_stored > 0`.

2. **Run a command from the repo root** (same machine as the DB file):
   ```bash
   python .cursor/skills/weather-data-analysis/scripts/analyze.py summary
   ```
   You should get JSON with `readings_stored`, `events_stored`, and `latest_reading_by_city` for Ottawa, Toronto, and Vancouver.

3. **Try another command** to confirm queries work:
   ```bash
   python .cursor/skills/weather-data-analysis/scripts/analyze.py compare-cities
   python .cursor/skills/weather-data-analysis/scripts/analyze.py events-breakdown
   ```

4. **Use it in Cursor** — in chat, ask something like: *“How many events do we have per city?”* and invoke the **weather-data-analysis** skill (or run the script above). The agent should run `analyze.py` and summarize the JSON.

If `readings_stored` is 0, start Docker or run bootstrap + at least one poll cycle first. If you see `ModuleNotFoundError: app`, run commands from the project root (`d:\watchagent-challenge`), not from inside `.cursor/`.

## Project layout

```
app/
  main.py              # FastAPI endpoints
  bootstrap.py         # DB init + baseline seeding
  core/config.py       # Cities, URLs, env vars
  db/                  # SQLAlchemy models + session
  services/
    poller.py          # Live weather polling
    historical_ingestor.py
    baseline_builder.py
    event_rules/       # Event detection rules + engine
tests/                 # Unit and integration tests
.cursor/               # Rules, agent, skills
.github/workflows/     # CI (test + docker build)
```
