from .base import EventRule


class PrecipitationChangeRule(EventRule):

    def evaluate(self, reading, baseline, previous_reading, recent_readings=None):
        try:
            if not previous_reading:
                return []

            prev_precip = previous_reading.precipitation
            curr_precip = reading.precipitation

            if prev_precip == 0 and curr_precip > 0:
                return [{
                    "type": "PRECIP_START",
                    "city": reading.city,
                    "timestamp": reading.timestamp,
                    "value": curr_precip,
                    "reason": "precipitation started",
                }]

            if prev_precip > 0 and curr_precip == 0:
                return [{
                    "type": "PRECIP_STOP",
                    "city": reading.city,
                    "timestamp": reading.timestamp,
                    "value": prev_precip,
                    "reason": "precipitation stopped",
                }]

            return []
        except Exception:
            return []
