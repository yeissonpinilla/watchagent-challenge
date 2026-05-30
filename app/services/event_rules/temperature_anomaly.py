from .base import EventRule


class TemperatureAnomalyRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading):
        events = []

        if not baseline:
            return events

        temp = reading.temperature_2m

        if abs(temp - baseline.temp_mean) > 2 * baseline.temp_std:
            events.append({
                "type": "TEMP_ANOMALY",
                "city": reading.city,
                "timestamp": reading.timestamp,
                "value": temp,
                "reason": "outside 2 std dev of monthly baseline"
            })

        if temp < baseline.temp_p5 or temp > baseline.temp_p95:
            events.append({
                "type": "TEMP_PERCENTILE_ANOMALY",
                "city": reading.city,
                "timestamp": reading.timestamp,
                "value": temp,
                "reason": "outside 5-95 percentile baseline"
            })

        return events