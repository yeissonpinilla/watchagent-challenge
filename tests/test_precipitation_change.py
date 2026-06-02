from types import SimpleNamespace

from app.services.event_rules.precipitation_change import PrecipitationChangeRule


def test_precip_start_fires_when_transition_from_zero(reading):
    previous = SimpleNamespace(precipitation=0.0)
    reading.precipitation = 1.5

    events = PrecipitationChangeRule().evaluate(reading, None, previous)

    assert len(events) == 1
    assert events[0]["type"] == "PRECIP_START"
    assert events[0]["value"] == 1.5


def test_precip_start_does_not_fire_when_still_dry(reading):
    previous = SimpleNamespace(precipitation=0.0)
    reading.precipitation = 0.0

    events = PrecipitationChangeRule().evaluate(reading, None, previous)

    assert events == []


def test_precip_stop_fires_when_transition_to_zero(reading):
    previous = SimpleNamespace(precipitation=2.0)
    reading.precipitation = 0.0

    events = PrecipitationChangeRule().evaluate(reading, None, previous)

    assert len(events) == 1
    assert events[0]["type"] == "PRECIP_STOP"
    assert events[0]["value"] == 2.0


def test_returns_empty_when_previous_missing(reading):
    events = PrecipitationChangeRule().evaluate(reading, None, None)

    assert events == []
