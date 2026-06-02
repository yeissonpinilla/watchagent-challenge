from types import SimpleNamespace

from app.services.event_rules.sudden_change import SuddenTemperatureChangeRule


def test_sudden_change_fires_when_delta_exceeds_threshold(reading):
    previous = SimpleNamespace(temperature_2m=15.0)
    reading.temperature_2m = 18.0  # delta = 3 > 2

    events = SuddenTemperatureChangeRule().evaluate(reading, None, previous)

    assert len(events) == 1
    assert events[0]["type"] == "SUDDEN_TEMP_CHANGE"
    assert events[0]["city"] == "Toronto"
    assert events[0]["timestamp"] == "2026-05-01T12:00"
    assert events[0]["value"] == 3.0
    assert events[0]["reason"] == "large short-term change"


def test_sudden_change_does_not_fire_when_delta_within_threshold(reading):
    previous = SimpleNamespace(temperature_2m=15.0)
    reading.temperature_2m = 16.0  # delta = 1 <= 2

    events = SuddenTemperatureChangeRule().evaluate(reading, None, previous)

    assert events == []


def test_returns_empty_when_previous_missing(reading):
    events = SuddenTemperatureChangeRule().evaluate(reading, None, None)

    assert events == []
