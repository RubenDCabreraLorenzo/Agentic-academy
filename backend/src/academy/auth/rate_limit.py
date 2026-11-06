"""In-process token-bucket rate limiting for auth endpoints.

Per-process state is sufficient for the single API instance of the MVP (research R10); it is
disabled only by ``RATE_LIMIT_ENABLED=false`` (refused in production).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from fastapi import Request

from academy.config import get_settings
from academy.shared.errors import ProblemError


@dataclass
class _Bucket:
    tokens: float
    updated: float


class RateLimiter:
    def __init__(self, capacity: int, per_seconds: float) -> None:
        self.capacity = capacity
        self.rate = capacity / per_seconds
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        t = time.monotonic()
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = self._buckets[key] = _Bucket(self.capacity, t)
            b.tokens = min(self.capacity, b.tokens + (t - b.updated) * self.rate)
            b.updated = t
            if b.tokens < 1:
                return False
            b.tokens -= 1
            return True

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


#: 10 attempts per IP and 5 per email every 15 minutes.
by_ip = RateLimiter(10, 15 * 60)
by_email = RateLimiter(5, 15 * 60)


def check(request: Request, action: str, email: str | None = None) -> None:
    if not get_settings().rate_limit_enabled:
        return
    ip = request.client.host if request.client else "unknown"
    ok = by_ip.allow(f"{action}:{ip}")
    if email is not None:
        ok = by_email.allow(f"{action}:{email.lower()}") and ok
    if not ok:
        raise ProblemError(429, "rate_limited", "Too many attempts, try again later")
