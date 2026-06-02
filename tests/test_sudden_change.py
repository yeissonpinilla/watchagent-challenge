from types import SimpleNamespace

from app.services.event_rules.sudden_change import SuddenTemperatureChangeRule


def _recent_temps(*values):
    return [SimpleNamespace(temperature_2m=v) for v in values]


def test_sudden_change_fires_when_delta_exceeds_rolling_std(reading):
    previous = SimpleNamespace(temperature_2m=15.0)
    reading.temperature_2m = 20.0  # delta=5
    recent = _recent_temps(14.0, 15.0, 16.0, 15.0, 14.0)  # std ~ 0.74, threshold ~ 1.48

    events = SuddenTemperatureChangeRule().evaluate(reading, None, previous, recent)

    assert len(events) == 1
    assert events[0]["type"] == "SUDDEN_TEMP_CHANGE"
    assert events[0]["city"] == "Toronto"
    assert events[0]["timestamp"] == "2026-05-01T12:00"
    assert events[0]["value"] == 5.0
    assert events[0]["reason"] == "temperature change exceeds 2x rolling std of recent readings"


def test_sudden_change_does_not_fire_when_delta_within_rolling_std(reading):
    previous = SimpleNamespace(temperature_2m=15.0)
    reading.temperature_2m = 16.0
    recent = _recent_temps(14.0, 15.0, 16.0, 15.0, 14.0)

    events = SuddenTemperatureChangeRule().evaluate(reading, None, previous, recent)

    assert events == []


def test_returns_empty_when_previous_missing(reading):
    events = SuddenTemperatureChangeRule().evaluate(reading, None, None, _recent_temps(15, 16))

    assert events == []
