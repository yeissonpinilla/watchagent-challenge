from abc import ABC, abstractmethod


class EventRule(ABC):

    @abstractmethod
    def evaluate(self, reading, baseline, previous_reading, recent_readings=None):
        """
        Returns list of events (can be empty)
        """
        pass