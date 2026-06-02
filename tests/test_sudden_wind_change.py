from types import SimpleNamespace

from app.services.event_rules.sudden_wind_change import SuddenWindChangeRule


def _recent_winds(*values):
    return [SimpleNamespace(wind_speed_10m=v) for v in values]


def test_sudden_wind_change_fires_when_delta_exceeds_rolling_std(reading):
    previous = SimpleNamespace(wind_speed_10m=10.0)
    reading.wind_speed_10m = 20.0
    recent = _recent_winds(8.0, 9.0, 10.0, 11.0, 12.0)  # std ~ 1.58, threshold ~ 3.16

    events = SuddenWindChangeRule().evaluate(reading, None, previous, recent)

    assert len(events) == 1
    assert events[0]["type"] == "SUDDEN_WIND_CHANGE"
    assert events[0]["value"] == 10.0


def test_sudden_wind_change_does_not_fire_when_delta_within_rolling_std(reading):
    previous = SimpleNamespace(wind_speed_10m=10.0)
    reading.wind_speed_10m = 11.0
    recent = _recent_winds(8.0, 9.0, 10.0, 11.0, 12.0)

    events = SuddenWindChangeRule().evaluate(reading, None, previous, recent)

    assert events == []


def test_returns_empty_when_previous_missing(reading):
    events = SuddenWindChangeRule().evaluate(reading, None, None, _recent_winds(10, 11))

    assert events == []
