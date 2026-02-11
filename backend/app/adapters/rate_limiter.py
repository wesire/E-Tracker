"""Rate limiter utility."""

import asyncio
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, max_calls: int, period: float):
        """Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a call, waiting if necessary."""
        async with self._lock:
            now = time.time()

            # Remove calls outside the time window
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                # Calculate wait time
                wait_time = self.period - (now - self.calls[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Remove expired calls after waiting
                    now = time.time()
                    while self.calls and self.calls[0] < now - self.period:
                        self.calls.popleft()

            self.calls.append(time.time())


class RateLimiterManager:
    """Manages multiple rate limiters."""

    def __init__(self):
        """Initialize rate limiter manager."""
        self._limiters: dict[str, RateLimiter] = {}

    def get_limiter(self, name: str, max_calls: int, period: float) -> RateLimiter:
        """Get or create a rate limiter.

        Args:
            name: Unique name for the rate limiter
            max_calls: Maximum number of calls allowed
            period: Time period in seconds

        Returns:
            RateLimiter instance
        """
        if name not in self._limiters:
            self._limiters[name] = RateLimiter(max_calls, period)
        return self._limiters[name]
