from app.db.session import SessionLocal
from app.db.models import HistoricalReading
from app.core.config import CITIES, HISTORICAL_DATA_DAYS
import requests
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


def fetch(city, lat, lon):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": str(date.today() - timedelta(days=HISTORICAL_DATA_DAYS)),
        "end_date": str(date.today()),
        "hourly": (
            "temperature_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "apparent_temperature,"
            "weather_code"
        )
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        logger.info(
            "historical_fetch_success",
            extra={
                "city": city,
                "status": response.status_code,
                "url": response.url
            }
        )

        return response.json()

    except requests.exceptions.Timeout:
        logger.warning(
            "historical_fetch_timeout",
            extra={"city": city}
        )
        return None

    except requests.exceptions.HTTPError as e:
        logger.warning(
            "historical_fetch_http_error",
            extra={
                "city": city,
                "status": getattr(e.response, "status_code", None)
            }
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.warning(
            "historical_fetch_failed",
            extra={
                "city": city,
                "error": str(e)
            }
        )
        return None


def parse(data, city):
    hourly = data["hourly"]

    times = hourly["time"]
    temps = hourly["temperature_2m"]
    wind = hourly["wind_speed_10m"]
    prec = hourly["precipitation"]
    app_temp = hourly["apparent_temperature"]
    weather_code = hourly["weather_code"]

    rows = []

    for i in range(len(times)):
        rows.append({
            "city": city,
            "timestamp": times[i],
            "temperature_2m": temps[i],
            "wind_speed_10m": wind[i],
            "precipitation": prec[i],
            "apparent_temperature": app_temp[i],
            "weather_code": weather_code[i],
        })

    return rows

def store(session, rows):
    for row in rows:
        exists = session.query(HistoricalReading).filter_by(
            city=row["city"],
            timestamp=row["timestamp"]
        ).first()

        if exists:
            continue

        session.add(HistoricalReading(**row))

    session.commit()

def run():
    session = SessionLocal()

    for city, (lat, lon) in CITIES.items():
        data = fetch(city, lat, lon)
        if data is None:          # ← esto falta
            continue
        rows = parse(data, city)
        store(session, rows)

    session.close()

if __name__ == "__main__":
    run()