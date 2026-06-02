---
name: weather-data-analysis
description: >-
  Query WatchAgent SQLite data (live readings, events, baselines) and return
  structured JSON analysis. Use when the user asks about stored weather data,
  trends, per-city comparisons, event counts, or time-window summaries.
---

# Weather Data Analysis

Run the analysis script against the project database. Default DB path: `./data/watchagent.db` (set `DATABASE_URL` to override).

## Commands

```bash
# Overview: counts, cities, latest reading per city
python .cursor/skills/weather-data-analysis/scripts/analyze.py summary

# Min/max/avg stats for one city or all cities
python .cursor/skills/weather-data-analysis/scripts/analyze.py city-stats --city Toronto

# Rank cities by avg temperature, wind, precipitation hours
python .cursor/skills/weather-data-analysis/scripts/analyze.py compare-cities

# Event counts by type and city, plus 10 most recent events
python .cursor/skills/weather-data-analysis/scripts/analyze.py events-breakdown
python .cursor/skills/weather-data-analysis/scripts/analyze.py events-breakdown --city Ottawa

# Temperature trend over last N readings for a city
python .cursor/skills/weather-data-analysis/scripts/analyze.py recent-trends --city Vancouver --limit 24

# Monthly baseline stats used for event detection
python .cursor/skills/weather-data-analysis/scripts/analyze.py baseline-context --city Toronto --month 6
```

## Workflow

1. Ensure the stack has collected data (`docker compose up` or poller running).
2. Pick the command that best matches the user's question.
3. Run the script from the repo root.
4. Summarize the JSON output in plain language for the user.

## Question → command mapping

| User question | Command |
|---------------|---------|
| "How much data do we have?" | `summary` |
| "What's the average temp in Ottawa?" | `city-stats --city Ottawa` |
| "Which city is warmest?" | `compare-cities` |
| "What events fired most often?" | `events-breakdown` |
| "How did Toronto temp change recently?" | `recent-trends --city Toronto` |
| "What's normal for Toronto in June?" | `baseline-context --city Toronto --month 6` |
