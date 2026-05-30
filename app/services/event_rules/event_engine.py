from app.db.session import SessionLocal
from app.db.models import MonthlyBaseline, HistoricalReading, Event

from app.services.event_rules.temperature_anomaly import TemperatureAnomalyRule
from app.services.event_rules.wind_spike import WindSpikeRule
from app.services.event_rules.sudden_change import SuddenTemperatureChangeRule


class EventEngine:

    def __init__(self):
        self.rules = [
            TemperatureAnomalyRule(),
            WindSpikeRule(),
            SuddenTemperatureChangeRule(),
        ]

    def get_baseline(self, db, city, month):
        return db.query(MonthlyBaseline).filter_by(
            city=city,
            month=month
        ).first()

    def get_previous(self, db, city):
        return (
            db.query(HistoricalReading)
            .filter_by(city=city)
            .order_by(HistoricalReading.timestamp.desc())
            .offset(1)
            .first()
        )

    def run(self, reading):
        db = SessionLocal()

        month = int(reading.timestamp[5:7])

        baseline = self.get_baseline(db, reading.city, month)
        previous = self.get_previous(db, reading.city)

        events = []

        for rule in self.rules:
            events.extend(rule.evaluate(reading, baseline, previous))

        for e in events:
            db.add(Event(
                event_type=e["type"],
                city=e["city"],
                timestamp=e["timestamp"],
                value=e.get("value"),
                reason=e["reason"]
            ))

        db.commit()
        db.close()

        return events

if __name__ == "__main__":
    from types import SimpleNamespace

    engine = EventEngine()

    # Fake baseline (simulate a “normal May in Toronto”)
    fake_baseline = SimpleNamespace(
        temp_mean=15,
        temp_std=3,
        temp_p5=10,
        temp_p95=20,
        wind_mean=10,
        wind_std=2,
        precip_mean=1.0
    )

    # Fake previous reading
    prev = SimpleNamespace(
        temperature_2m=15
    )

    # Override engine DB lookups for testing
    engine.get_baseline = lambda db, city, month: fake_baseline
    engine.get_previous = lambda db, city: prev

    # Create test readings
    test_readings = [
        # Normal reading (should NOT trigger much)
        SimpleNamespace(
            city="Toronto",
            timestamp="2026-05-30T10:00",
            temperature_2m=15,
            wind_speed_10m=10,
            precipitation=0.0
        ),

        # Heat anomaly (should trigger TEMP_ANOMALY)
        SimpleNamespace(
            city="Toronto",
            timestamp="2026-05-30T11:00",
            temperature_2m=25,
            wind_speed_10m=10,
            precipitation=0.0
        ),

        # Wind spike (should trigger WIND_SPIKE)
        SimpleNamespace(
            city="Toronto",
            timestamp="2026-05-30T12:00",
            temperature_2m=15,
            wind_speed_10m=25,
            precipitation=0.0
        ),

        # Sudden temperature change (should trigger SUDDEN_TEMP_CHANGE)
        SimpleNamespace(
            city="Toronto",
            timestamp="2026-05-30T13:00",
            temperature_2m=30,
            wind_speed_10m=10,
            precipitation=0.0
        ),
    ]

    print("\n=== EVENT ENGINE TEST START ===\n")

    for r in test_readings:
        events = engine.run(r)

        print(f"\nReading: {r.timestamp} | temp={r.temperature_2m} wind={r.wind_speed_10m}")
        print(f"Events triggered: {len(events)}")

        for e in events:
            print(" ->", e["type"], "|", e["reason"])

    print("\n=== TEST COMPLETE ===\n")