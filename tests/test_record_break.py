from app.services.event_rules.record_break import RecordBreakRule


def test_record_high_fires_when_above_baseline_max(baseline, reading):
    reading.temperature_2m = 25.0  # baseline temp_max=20

    events = RecordBreakRule().evaluate(reading, baseline, None)

    assert len(events) == 1
    assert events[0]["type"] == "RECORD_HIGH"
    assert events[0]["value"] == 25.0


def test_record_break_does_not_fire_within_historical_range(baseline, reading):
    reading.temperature_2m = 16.0  # between temp_min=10 and temp_max=20

    events = RecordBreakRule().evaluate(reading, baseline, None)

    assert events == []


def test_record_low_fires_when_below_baseline_min(baseline, reading):
    reading.temperature_2m = 8.0  # baseline temp_min=10

    events = RecordBreakRule().evaluate(reading, baseline, None)

    assert len(events) == 1
    assert events[0]["type"] == "RECORD_LOW"
    assert events[0]["value"] == 8.0


def test_returns_empty_when_baseline_missing(reading):
    events = RecordBreakRule().evaluate(reading, None, None)

    assert events == []
