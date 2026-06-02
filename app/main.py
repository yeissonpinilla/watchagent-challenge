from typing import Generator

from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session

from app.db.models import Event, LiveReading
from app.db.session import SessionLocal

app = FastAPI(title="WatchAgent")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _reading_to_dict(reading: LiveReading) -> dict:
    return {
        "id": reading.id,
        "city": reading.city,
        "timestamp": reading.timestamp,
        "temperature_2m": reading.temperature_2m,
        "apparent_temperature": reading.apparent_temperature,
        "precipitation": reading.precipitation,
        "wind_speed_10m": reading.wind_speed_10m,
        "weather_code": reading.weather_code,
    }


def _event_to_dict(event: Event) -> dict:
    return {
        "id": event.id,
        "city": event.city,
        "timestamp": event.timestamp,
        "event_type": event.event_type,
        "reason": event.reason,
        "value": event.value,
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    readings_stored = db.query(LiveReading).count()
    events_stored = db.query(Event).count()

    return {
        "status": "ok",
        "readings_stored": readings_stored,
        "events_stored": events_stored,
    }


@app.get("/readings")
def readings(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
    db: Session = Depends(get_db),
):
    query = db.query(LiveReading)

    if city is not None:
        query = query.filter(LiveReading.city == city)

    rows = (
        query.order_by(LiveReading.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {"readings": [_reading_to_dict(row) for row in rows]}


@app.get("/events")
def events(
    city: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if city is not None:
        query = query.filter(Event.city == city)

    rows = (
        query.order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {"events": [_event_to_dict(row) for row in rows]}
