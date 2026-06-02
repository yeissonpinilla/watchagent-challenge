from statistics import stdev

from .base import EventRule


class SuddenWindChangeRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading, recent_readings=None):
        try:
            if not previous_reading:
                return []

            recent = recent_readings or []
            winds = [r.wind_speed_10m for r in recent]

            if len(winds) < 2:
                return []

            wind_std = stdev(winds)
            if wind_std == 0:
                return []

            delta = abs(reading.wind_speed_10m - previous_reading.wind_speed_10m)
            threshold = 2 * wind_std

            if delta > threshold:
                return [{
                    "type": "SUDDEN_WIND_CHANGE",
                    "city": reading.city,
                    "timestamp": reading.timestamp,
                    "value": delta,
                    "reason": "wind change exceeds 2x rolling std of recent readings",
                }]

            return []
        except Exception:
            return []
