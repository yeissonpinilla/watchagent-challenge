#!/usr/bin/env python3
"""
Query WatchAgent SQLite data and return structured analysis as JSON.

Usage:
  python .cursor/skills/weather-data-analysis/scripts/analyze.py summary
  python .cursor/skills/weather-data-analysis/scripts/analyze.py city-stats --city Toronto
  python .cursor/skills/weather-data-analysis/scripts/analyze.py compare-cities
  python .cursor/skills/weather-data-analysis/scripts/analyze.py events-breakdown
  python .cursor/skills/weather-data-analysis/scripts/analyze.py recent-trends --city Ottawa --limit 24
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import Event, LiveReading, MonthlyBaseline  # noqa: E402

DEFAULT_DB = os.getenv("DATABASE_URL", "sqlite:///./data/watchagent.db")


def get_session(database_url: str):
    if database_url.startswith("sqlite:///./"):
        rel = database_url.replace("sqlite:///./", "")
        db_path = ROOT / rel
        db_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{db_path.as_posix()}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def cmd_summary(db) -> dict:
    reading_count = db.query(LiveReading).count()
    event_count = db.query(Event).count()
    cities = [row[0] for row in db.query(LiveReading.city).distinct().all()]

    latest_by_city = {}
    for city in cities:
        row = (
            db.query(LiveReading)
            .filter_by(city=city)
            .order_by(LiveReading.timestamp.desc())
            .first()
        )
        if row:
            latest_by_city[city] = {
                "timestamp": row.timestamp,
                "temperature_2m": row.temperature_2m,
                "wind_speed_10m": row.wind_speed_10m,
                "precipitation": row.precipitation,
            }

    return {
        "analysis": "summary",
        "readings_stored": reading_count,
        "events_stored": event_count,
        "cities_with_data": cities,
        "latest_reading_by_city": latest_by_city,
    }


def cmd_city_stats(db, city: str | None) -> dict:
    query = db.query(LiveReading)
    if city:
        query = query.filter(LiveReading.city == city)

    rows = query.all()
    if not rows:
        return {"analysis": "city-stats", "city": city, "error": "no readings found"}

    by_city: dict[str, list] = defaultdict(list)
    for row in rows:
        by_city[row.city].append(row)

    stats = {}
    for name, city_rows in by_city.items():
        temps = [r.temperature_2m for r in city_rows if r.temperature_2m is not None]
        winds = [r.wind_speed_10m for r in city_rows if r.wind_speed_10m is not None]
        precs = [r.precipitation for r in city_rows if r.precipitation is not None]

        stats[name] = {
            "reading_count": len(city_rows),
            "temperature_2m": {
                "min": min(temps) if temps else None,
                "max": max(temps) if temps else None,
                "avg": round(sum(temps) / len(temps), 2) if temps else None,
            },
            "wind_speed_10m": {
                "min": min(winds) if winds else None,
                "max": max(winds) if winds else None,
                "avg": round(sum(winds) / len(winds), 2) if winds else None,
            },
            "precipitation_hours": sum(1 for p in precs if p and p > 0),
        }

    return {"analysis": "city-stats", "stats": stats}


def cmd_compare_cities(db) -> dict:
    city_stats = cmd_city_stats(db, city=None)["stats"]
    if not city_stats:
        return {"analysis": "compare-cities", "error": "no readings found"}

    ranking = sorted(
        city_stats.items(),
        key=lambda item: item[1]["temperature_2m"]["avg"] or 0,
        reverse=True,
    )

    return {
        "analysis": "compare-cities",
        "warmest_to_coolest_by_avg_temp": [
            {"city": city, "avg_temperature_2m": data["temperature_2m"]["avg"]}
            for city, data in ranking
        ],
        "windiest_by_avg_wind": sorted(
            [
                {"city": city, "avg_wind_speed_10m": data["wind_speed_10m"]["avg"]}
                for city, data in city_stats.items()
            ],
            key=lambda x: x["avg_wind_speed_10m"] or 0,
            reverse=True,
        ),
        "most_precipitation_hours": sorted(
            [
                {"city": city, "precipitation_hours": data["precipitation_hours"]}
                for city, data in city_stats.items()
            ],
            key=lambda x: x["precipitation_hours"],
            reverse=True,
        ),
    }


def cmd_events_breakdown(db, city: str | None) -> dict:
    query = db.query(Event)
    if city:
        query = query.filter(Event.city == city)

    rows = query.all()
    by_type = Counter(row.event_type for row in rows)
    by_city = Counter(row.city for row in rows)

    recent = (
        query.order_by(Event.timestamp.desc())
        .limit(10)
        .all()
    )

    return {
        "analysis": "events-breakdown",
        "total_events": len(rows),
        "by_type": dict(by_type.most_common()),
        "by_city": dict(by_city.most_common()),
        "recent_events": [
            {
                "city": e.city,
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "value": e.value,
                "reason": e.reason,
            }
            for e in recent
        ],
    }


def cmd_recent_trends(db, city: str, limit: int) -> dict:
    rows = (
        db.query(LiveReading)
        .filter_by(city=city)
        .order_by(LiveReading.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not rows:
        return {"analysis": "recent-trends", "city": city, "error": "no readings found"}

    rows = list(reversed(rows))
    temps = [r.temperature_2m for r in rows]

    return {
        "analysis": "recent-trends",
        "city": city,
        "window_size": len(rows),
        "from": rows[0].timestamp,
        "to": rows[-1].timestamp,
        "temperature_trend": {
            "start": temps[0],
            "end": temps[-1],
            "change": round(temps[-1] - temps[0], 2),
            "min": min(temps),
            "max": max(temps),
        },
        "readings": [
            {
                "timestamp": r.timestamp,
                "temperature_2m": r.temperature_2m,
                "wind_speed_10m": r.wind_speed_10m,
                "precipitation": r.precipitation,
            }
            for r in rows
        ],
    }


def cmd_baseline_context(db, city: str, month: int) -> dict:
    baseline = (
        db.query(MonthlyBaseline)
        .filter_by(city=city, month=month)
        .first()
    )

    if not baseline:
        return {
            "analysis": "baseline-context",
            "city": city,
            "month": month,
            "error": "no baseline for city/month",
        }

    return {
        "analysis": "baseline-context",
        "city": city,
        "month": month,
        "temp_mean": baseline.temp_mean,
        "temp_std": baseline.temp_std,
        "temp_min": baseline.temp_min,
        "temp_max": baseline.temp_max,
        "temp_p5": baseline.temp_p5,
        "temp_p95": baseline.temp_p95,
        "wind_mean": baseline.wind_mean,
        "wind_std": baseline.wind_std,
    }


COMMANDS = {
    "summary": lambda db, args: cmd_summary(db),
    "city-stats": lambda db, args: cmd_city_stats(db, args.city),
    "compare-cities": lambda db, args: cmd_compare_cities(db),
    "events-breakdown": lambda db, args: cmd_events_breakdown(db, args.city),
    "recent-trends": lambda db, args: cmd_recent_trends(db, args.city, args.limit),
    "baseline-context": lambda db, args: cmd_baseline_context(db, args.city, args.month),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="WatchAgent weather data analysis")
    parser.add_argument(
        "command",
        choices=sorted(COMMANDS.keys()),
        help="Analysis to run",
    )
    parser.add_argument("--city", help="Filter or target city (Ottawa, Toronto, Vancouver)")
    parser.add_argument("--limit", type=int, default=24, help="Reading window for recent-trends")
    parser.add_argument("--month", type=int, help="Month 1-12 for baseline-context")
    parser.add_argument(
        "--database-url",
        default=DEFAULT_DB,
        help="SQLAlchemy database URL (default: DATABASE_URL env or ./data/watchagent.db)",
    )
    args = parser.parse_args()

    if args.command == "recent-trends" and not args.city:
        parser.error("recent-trends requires --city")
    if args.command == "baseline-context" and (not args.city or not args.month):
        parser.error("baseline-context requires --city and --month")

    db = get_session(args.database_url)
    try:
        result = COMMANDS[args.command](db, args)
    finally:
        db.close()

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
