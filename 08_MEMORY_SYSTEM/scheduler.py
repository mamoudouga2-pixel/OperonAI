"""
Retention scheduler (spec 8.19, 8.30 cleanup_interval_minutes).

Deliberately does not spawn real background threads/timers here -
Part 01 Core owns the actual scheduling loop; this class just knows
"has enough time passed to run cleanup again" and performs one pass
when asked.
"""

import time


class Scheduler:
    def __init__(self, cleanup, interval_minutes=60):
        self.cleanup = cleanup
        self.interval_minutes = interval_minutes
        self._last_run = None

    def due(self, now=None):
        now = now or time.time()
        if self._last_run is None:
            return True
        return (now - self._last_run) >= self.interval_minutes * 60

    def run(self, records, policy, now=None):
        result = self.cleanup.run(records, policy)
        self._last_run = now or time.time()
        return result
