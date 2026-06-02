from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.event_rules.event_engine import EventEngine


@patch("app.services.event_rules.event_engine.SessionLocal")
def test_run_returns_events_from_rules(mock_session_local, baseline):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    engine = EventEngine()
    engine.get_baseline = lambda db, city, month: baseline
    engine.get_previous = lambda db, city: SimpleNamespace(temperature_2m=15.0)

    reading = SimpleNamespace(
        city="Toronto",
        timestamp="2026-05-30T11:00",
        temperature_2m=28.0,
        wind_speed_10m=10.0,
        precipitation=0.0,
    )

    events = engine.run(reading)

    assert len(events) >= 1
    assert all(
        {"type", "city", "timestamp", "value", "reason"} <= set(e.keys())
        for e in events
    )
    assert mock_db.add.call_count == len(events)
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.services.event_rules.event_engine.SessionLocal")
def test_run_returns_empty_when_no_rules_fire(mock_session_local, baseline):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    engine = EventEngine()
    engine.get_baseline = lambda db, city, month: baseline
    engine.get_previous = lambda db, city: SimpleNamespace(temperature_2m=15.0)

    reading = SimpleNamespace(
        city="Toronto",
        timestamp="2026-05-30T10:00",
        temperature_2m=16.0,
        wind_speed_10m=10.0,
        precipitation=0.0,
    )

    events = engine.run(reading)

    assert events == []
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.services.event_rules.event_engine.SessionLocal")
def test_run_extracts_month_from_timestamp(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    captured = {}

    def capture_baseline(db, city, month):
        captured["month"] = month
        return None

    engine = EventEngine()
    engine.get_baseline = capture_baseline
    engine.get_previous = lambda db, city: None

    reading = SimpleNamespace(
        city="Toronto",
        timestamp="2026-07-15T14:00",
        temperature_2m=20.0,
        wind_speed_10m=10.0,
        precipitation=0.0,
    )

    engine.run(reading)

    assert captured["month"] == 7
