import time
import logging
import requests
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.db.models import LiveReading
from app.core.config import CITIES, OPEN_METEO_URL, POLL_INTERVAL_SECONDS
from app.services.event_rules.event_engine import EventEngine

logger = logging.getLogger(__name__)


def fetch_current(city: str, lat: float, lon: float) -> dict | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()

        logger.info(
            "poll_success",
            extra={"city": city, "status": response.status_code}
        )

        return response.json()

    except requests.exceptions.Timeout:
        logger.warning(
            "poll_timeout",
            extra={"city": city}
        )
        return None

    except requests.exceptions.HTTPError as e:
        logger.warning(
            "poll_http_error",
            extra={"city": city, "status": getattr(e.response, "status_code", None)}
        )
        return None

    except requests.exceptions.RequestException as e:
        logger.warning(
            "poll_request_failed",
            extra={"city": city, "error": str(e)}
        )
        return None


def parse_current(data: dict, city: str) -> dict | None:
    current = data.get("current")

    if not current:
        logger.warning("poll_empty_response", extra={"city": city})
        return None

    return {
        "city": city,
        "timestamp": current["time"],
        "temperature_2m": current["temperature_2m"],
        "apparent_temperature": current["apparent_temperature"],
        "precipitation": current["precipitation"],
        "wind_speed_10m": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }


def store_if_new(db, reading_data: dict) -> LiveReading | None:
    """
    Insert reading only if this (city, timestamp) pair is new.
    Returns the LiveReading object if stored, None if duplicate.
    UniqueConstraint on (city, timestamp) is the source of truth,
    but we check first to avoid relying on exception handling for control flow.
    """
    exists = (
        db.query(LiveReading)
        .filter_by(city=reading_data["city"], timestamp=reading_data["timestamp"])
        .first()
    )

    if exists:
        logger.debug(
            "poll_duplicate_skipped",
            extra={"city": reading_data["city"], "timestamp": reading_data["timestamp"]}
        )
        return None

    reading = LiveReading(**reading_data)
    db.add(reading)
    db.commit()
    db.refresh(reading)

    logger.info(
        "poll_reading_stored",
        extra={"city": reading_data["city"], "timestamp": reading_data["timestamp"]}
    )

    return reading


def poll_once(engine: EventEngine) -> None:
    """
    Single poll cycle: fetch all cities, store new readings, run event detection.
    """
    db = SessionLocal()

    try:
        for city, (lat, lon) in CITIES.items():
            data = fetch_current(city, lat, lon)

            if data is None:
                continue

            reading_data = parse_current(data, city)

            if reading_data is None:
                continue

            reading = store_if_new(db, reading_data)

            if reading is None:
                continue  # duplicate — event engine already ran for this reading

            events = engine.run(reading)

            if events:
                logger.info(
                    f"poll_events_detected_{city}_{len(events)}",
                    extra={"city": city, "count": len(events)}
                )

    except Exception as e:
        logger.error(
            "poll_cycle_failed",
            extra={"error": str(e)},
            exc_info=True
        )

    finally:
        db.close()


def run() -> None:
    logger.info("poller_started", extra={"interval_seconds": POLL_INTERVAL_SECONDS})

    engine = EventEngine()

    while True:
        poll_start = datetime.now(timezone.utc).isoformat()
        logger.info("poll_cycle_start", extra={"at": poll_start})

        poll_once(engine)

        logger.info("poll_cycle_done", extra={"sleeping_seconds": POLL_INTERVAL_SECONDS})
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()