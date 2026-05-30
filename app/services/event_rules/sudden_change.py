from .base import EventRule


class SuddenTemperatureChangeRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading):
        if not previous_reading:
            return []

        delta = abs(reading.temperature_2m - previous_reading.temperature_2m)

        if delta > 2:
            return [{
                "type": "SUDDEN_TEMP_CHANGE",
                "city": reading.city,
                "timestamp": reading.timestamp,
                "value": delta,
                "reason": "large short-term change"
            }]

        return []