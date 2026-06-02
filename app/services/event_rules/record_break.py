from .base import EventRule


class RecordBreakRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading, recent_readings=None):
        try:
            if not baseline:
                return []

            events = []
            temp = reading.temperature_2m

            if temp > baseline.temp_max:
                events.append({
                    "type": "RECORD_HIGH",
                    "city": reading.city,
                    "timestamp": reading.timestamp,
                    "value": temp,
                    "reason": "new monthly maximum temperature vs historical baseline",
                })

            if temp < baseline.temp_min:
                events.append({
                    "type": "RECORD_LOW",
                    "city": reading.city,
                    "timestamp": reading.timestamp,
                    "value": temp,
                    "reason": "new monthly minimum temperature vs historical baseline",
                })

            return events
        except Exception:
            return []
