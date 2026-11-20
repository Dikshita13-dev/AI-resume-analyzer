"""Tiny thread-safe in-memory usage counter (no database)."""
import threading
from collections import defaultdict


class UsageLimiter:
    def __init__(self, limit: int):
        self.limit = limit
        self._used = defaultdict(int)
        self._lock = threading.Lock()

    def used(self, key: str) -> int:
        with self._lock:
            return self._used[key]

    def remaining(self, key: str) -> int:
        return max(self.limit - self.used(key), 0)

    def reserve(self, key: str) -> bool:
        """Atomically take one slot. Returns False if the key is out of analyses."""
        with self._lock:
            if self._used[key] >= self.limit:
                return False
            self._used[key] += 1
            return True

    def refund(self, key: str) -> None:
        """Give a slot back (used when the analysis fails)."""
        with self._lock:
            if self._used[key] > 0:
                self._used[key] -= 1
