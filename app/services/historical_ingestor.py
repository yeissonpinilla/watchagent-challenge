from app.db.session import SessionLocal
from app.db.models import HistoricalReading
from app.core.config import CITIES, HISTORICAL_DATA_DAYS
import requests
from datetime import date, timedelta

def fetch(city, lat, lon):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": str(date.today() - timedelta(days=HISTORICAL_DATA_DAYS)),
        "end_date": str(date.today()),
        "hourly": "temperature_2m,precipitation,wind_speed_10m"
    }

    return requests.get(url, params=params).json()

def parse(data, city):
    hourly = data["hourly"]

    times = hourly["time"]
    temps = hourly["temperature_2m"]
    wind = hourly["wind_speed_10m"]
    prec = hourly["precipitation"]

    rows = []

    for i in range(len(times)):
        rows.append({
            "city": city,
            "timestamp": times[i],
            "temperature_2m": temps[i],
            "wind_speed_10m": wind[i],
            "precipitation": prec[i],
        })

    return rows

def store(session, rows):
    for r in rows:
        exists = session.query(HistoricalReading).filter_by(
            city=r["city"],
            timestamp=r["timestamp"]
        ).first()

        if exists:
            continue

        session.add(HistoricalReading(**r))

    session.commit()

def run():
    session = SessionLocal()

    for city, (lat, lon) in CITIES.items():
        data = fetch(city, lat, lon)
        rows = parse(data, city)
        store(session, rows)

    session.close()

if __name__ == "__main__":
    run()