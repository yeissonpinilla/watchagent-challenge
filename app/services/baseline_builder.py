from collections import defaultdict
from statistics import mean, stdev
import numpy as np
from datetime import datetime

from app.db.session import SessionLocal
from app.db.models import HistoricalReading, MonthlyBaseline


def parse_month(ts: str) -> int:
    # Open-Meteo format: "2024-01-01T13:00"
    return datetime.fromisoformat(ts).month


def load_historical():
    db = SessionLocal()
    return db.query(HistoricalReading).all()


def group_by_city_month(rows):
    grouped = defaultdict(list)

    for r in rows:
        month = parse_month(r.timestamp)
        grouped[(r.city, month)].append(r)

    return grouped


def compute_stats(values):
    if not values:
        return None

    return {
        "mean": float(mean(values)),
        "std": float(stdev(values)) if len(values) > 1 else 0.0,
        "min": float(min(values)),
        "max": float(max(values)),
        "p5": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
    }


def build_baselines():
    db = SessionLocal()
    rows = load_historical()

    grouped = group_by_city_month(rows)
    db.query(MonthlyBaseline).delete()
    db.commit()

    for (city, month), data in grouped.items():

        temps = [r.temperature_2m for r in data]
        winds = [r.wind_speed_10m for r in data]
        precs = [r.precipitation for r in data]

        temp_stats = compute_stats(temps)
        wind_stats = compute_stats(winds)
        prec_stats = compute_stats(precs)

        baseline = MonthlyBaseline(
            city=city,
            month=month,

            temp_mean=temp_stats["mean"],
            temp_std=temp_stats["std"],
            temp_min=temp_stats["min"],
            temp_max=temp_stats["max"],
            temp_p5=temp_stats["p5"],
            temp_p95=temp_stats["p95"],

            wind_mean=wind_stats["mean"],
            wind_std=wind_stats["std"],

            precip_mean=prec_stats["mean"],
        )

        db.add(baseline)

    db.commit()
    db.close()

if __name__ == "__main__":
    build_baselines()
    print("Baselines computed successfully")