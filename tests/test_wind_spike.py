from app.services.event_rules.wind_spike import WindSpikeRule


def test_wind_spike_fires_when_beyond_two_std(baseline, reading):
    reading.wind_speed_10m = 25.0  

    events = WindSpikeRule().evaluate(reading, baseline, None)

    assert len(events) == 1
    assert events[0]["type"] == "WIND_SPIKE"
    assert events[0]["city"] == "Toronto"
    assert events[0]["timestamp"] == "2026-05-01T12:00"
    assert events[0]["value"] == 25.0
    assert events[0]["reason"] == "deviation from baseline wind"


def test_wind_spike_does_not_fire_when_within_two_std(baseline, reading):
    reading.wind_speed_10m = 11.0 

    events = WindSpikeRule().evaluate(reading, baseline, None)

    assert events == []


def test_returns_empty_when_baseline_missing(reading):
    events = WindSpikeRule().evaluate(reading, None, None)

    assert events == []
