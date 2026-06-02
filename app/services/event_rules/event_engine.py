from app.db.session import SessionLocal
from app.db.models import MonthlyBaseline, Event, LiveReading

from app.services.event_rules.temperature_anomaly import TemperatureAnomalyRule
from app.services.event_rules.wind_spike import WindSpikeRule
from app.services.event_rules.sudden_change import SuddenTemperatureChangeRule
from app.services.event_rules.sudden_wind_change import SuddenWindChangeRule
from app.services.event_rules.record_break import RecordBreakRule
from app.services.event_rules.precipitation_change import PrecipitationChangeRule


class EventEngine:

    def __init__(self):
        self.rules = [
            TemperatureAnomalyRule(),
            WindSpikeRule(),
            RecordBreakRule(),
            SuddenTemperatureChangeRule(),
            SuddenWindChangeRule(),
            PrecipitationChangeRule(),
        ]

    def get_baseline(self, db, city, month):
        return db.query(MonthlyBaseline).filter_by(
            city=city,
            month=month
        ).first()

    def get_previous(self, db, city, current_timestamp=None):
        query = db.query(LiveReading).filter_by(city=city)

        if current_timestamp is not None:
            query = query.filter(LiveReading.timestamp != current_timestamp)

        return query.order_by(LiveReading.timestamp.desc()).first()

    def get_recent_readings(self, db, city, current_timestamp, limit=24):
        return (
            db.query(LiveReading)
            .filter_by(city=city)
            .filter(LiveReading.timestamp != current_timestamp)
            .order_by(LiveReading.timestamp.desc())
            .limit(limit)
            .all()
        )

    def run(self, reading):
        db = SessionLocal()

        month = int(reading.timestamp[5:7])

        baseline = self.get_baseline(db, reading.city, month)
        previous = self.get_previous(db, reading.city, reading.timestamp)
        recent = self.get_recent_readings(db, reading.city, reading.timestamp)

        events = []

        for rule in self.rules:
            events.extend(rule.evaluate(reading, baseline, previous, recent))

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
