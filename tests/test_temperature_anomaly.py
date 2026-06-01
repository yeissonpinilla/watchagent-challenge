from types import SimpleNamespace

from app.services.event_rules.temperature_anomaly import TemperatureAnomalyRule


def test_temp_anomaly_fires_when_beyond_two_std(baseline, reading):
    reading.temperature_2m = 28.0  # mean + 2*std = 21

    events = TemperatureAnomalyRule().evaluate(reading, baseline, None)

    types = [e["type"] for e in events]
    assert "TEMP_ANOMALY" in types
    anomaly = next(e for e in events if e["type"] == "TEMP_ANOMALY")
    assert anomaly["city"] == "Toronto"
    assert anomaly["timestamp"] == "2026-05-01T12:00"
    assert anomaly["value"] == 28.0
    assert anomaly["reason"] == "outside 2 std dev of monthly baseline"


def test_temp_anomaly_does_not_fire_when_within_two_std(baseline, reading):
    reading.temperature_2m = 16.0  # |16 - 15| = 1 < 2 * 3

    events = TemperatureAnomalyRule().evaluate(reading, baseline, None)

    assert "TEMP_ANOMALY" not in [e["type"] for e in events]


def test_percentile_anomaly_fires_when_below_p5(baseline, reading):
    reading.temperature_2m = 9.0  # below p5=10, within 2 std (|9-15|=6, not > 6)

    events = TemperatureAnomalyRule().evaluate(reading, baseline, None)

    types = [e["type"] for e in events]
    assert "TEMP_PERCENTILE_ANOMALY" in types
    assert "TEMP_ANOMALY" not in types


def test_percentile_anomaly_does_not_fire_when_within_p5_p95(baseline, reading):
    reading.temperature_2m = 16.0  # between p5=10 and p95=20

    events = TemperatureAnomalyRule().evaluate(reading, baseline, None)

    assert events == []


def test_returns_empty_when_baseline_missing(reading):
    events = TemperatureAnomalyRule().evaluate(reading, None, None)

    assert events == []
