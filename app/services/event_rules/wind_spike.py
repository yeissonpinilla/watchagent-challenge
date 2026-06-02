from .base import EventRule


class WindSpikeRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading):
        events = []

        if not baseline:
            return events

        wind = reading.wind_speed_10m

        if abs(wind - baseline.wind_mean) > 2 * baseline.wind_std:
            events.append({
                "type": "WIND_SPIKE",
                "city": reading.city,
                "timestamp": reading.timestamp,
                "value": wind,
                "reason": "deviation from baseline wind"
            })

        return events