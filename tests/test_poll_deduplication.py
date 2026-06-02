from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, LiveReading
from app.services.event_rules.event_engine import EventEngine
from app.services.poller import poll_once

MOCK_API_RESPONSE = {
    "current": {
        "time": "2026-05-30T10:00",
        "temperature_2m": 18.0,
        "apparent_temperature": 17.0,
        "precipitation": 0.0,
        "wind_speed_10m": 10.0,
        "weather_code": 0,
    }
}


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return factory


@patch("app.services.event_rules.event_engine.SessionLocal")
@patch("app.services.poller.SessionLocal")
@patch("app.services.poller.fetch_current")
@patch("app.services.poller.CITIES", {"Toronto": (43.70, -79.42)})
def test_poll_once_stores_duplicate_reading_only_once(
    mock_fetch,
    mock_poller_session,
    mock_engine_session,
    session_factory,
):
    mock_poller_session.side_effect = session_factory
    mock_engine_session.side_effect = session_factory
    mock_fetch.return_value = MOCK_API_RESPONSE

    engine = EventEngine()

    poll_once(engine)
    poll_once(engine)

    db = session_factory()
    try:
        count = db.query(LiveReading).count()
        rows = db.query(LiveReading).all()
    finally:
        db.close()

    assert count == 1
    assert rows[0].city == "Toronto"
    assert rows[0].timestamp == "2026-05-30T10:00"
    assert mock_fetch.call_count == 2
