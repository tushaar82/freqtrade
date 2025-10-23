"""
Rate Limiter for Indian Brokers

Implements token bucket algorithm for rate limiting API requests to comply
with broker rate limits and prevent DDos protection triggers.
"""

import logging
import time
from collections import deque
from datetime import datetime
from threading import Lock
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with support for multiple rate limits.

    Supports:
    - Requests per second limits
    - Requests per minute limits
    - Requests per day limits
    - Per-endpoint specific limits
    """

    def __init__(
        self,
        requests_per_second: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None,
        min_request_interval: float = 0.0
    ):
        """
        Initialize rate limiter.

        :param requests_per_second: Maximum requests per second (None = unlimited)
        :param requests_per_minute: Maximum requests per minute (None = unlimited)
        :param requests_per_hour: Maximum requests per hour (None = unlimited)
        :param requests_per_day: Maximum requests per day (None = unlimited)
        :param min_request_interval: Minimum time between requests in seconds
        """
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.min_request_interval = min_request_interval

        # Request history tracking
        self._request_times: deque = deque()
        self._last_request_time: float = 0.0
        self._lock = Lock()

        # Statistics
        self._total_requests = 0
        self._total_wait_time = 0.0
        self._rate_limit_hits = 0

        logger.info(
            f"Rate limiter initialized: "
            f"{requests_per_second or 'unlimited'} req/s, "
            f"{requests_per_minute or 'unlimited'} req/min, "
            f"{requests_per_hour or 'unlimited'} req/hour, "
            f"{requests_per_day or 'unlimited'} req/day, "
            f"min interval: {min_request_interval}s"
        )

    def wait_if_needed(self, endpoint: Optional[str] = None) -> float:
        """
        Wait if rate limit would be exceeded.

        :param endpoint: Specific endpoint (for per-endpoint limits)
        :return: Wait time in seconds
        """
        with self._lock:
            current_time = time.time()
            wait_time = 0.0

            # Clean old request times
            self._cleanup_old_requests(current_time)

            # Check minimum interval
            if self.min_request_interval > 0:
                time_since_last = current_time - self._last_request_time
                if time_since_last < self.min_request_interval:
                    interval_wait = self.min_request_interval - time_since_last
                    wait_time = max(wait_time, interval_wait)

            # Check per-second limit
            if self.requests_per_second:
                second_wait = self._check_limit(current_time, 1.0, self.requests_per_second)
                wait_time = max(wait_time, second_wait)

            # Check per-minute limit
            if self.requests_per_minute:
                minute_wait = self._check_limit(current_time, 60.0, self.requests_per_minute)
                wait_time = max(wait_time, minute_wait)

            # Check per-hour limit
            if self.requests_per_hour:
                hour_wait = self._check_limit(current_time, 3600.0, self.requests_per_hour)
                wait_time = max(wait_time, hour_wait)

            # Check per-day limit
            if self.requests_per_day:
                day_wait = self._check_limit(current_time, 86400.0, self.requests_per_day)
                wait_time = max(wait_time, day_wait)

            # Wait if needed
            if wait_time > 0:
                self._rate_limit_hits += 1
                self._total_wait_time += wait_time
                logger.debug(f"Rate limit: waiting {wait_time:.3f}s before request")
                time.sleep(wait_time)
                current_time = time.time()

            # Record request
            self._request_times.append(current_time)
            self._last_request_time = current_time
            self._total_requests += 1

            return wait_time

    def _cleanup_old_requests(self, current_time: float):
        """Remove request times older than longest period"""
        max_period = 86400.0  # 1 day
        if self.requests_per_hour and not self.requests_per_day:
            max_period = 3600.0
        elif self.requests_per_minute and not (self.requests_per_hour or self.requests_per_day):
            max_period = 60.0
        elif self.requests_per_second and not any([
            self.requests_per_minute, self.requests_per_hour, self.requests_per_day
        ]):
            max_period = 1.0

        cutoff_time = current_time - max_period
        while self._request_times and self._request_times[0] < cutoff_time:
            self._request_times.popleft()

    def _check_limit(self, current_time: float, period: float, limit: int) -> float:
        """
        Check if limit would be exceeded and return wait time.

        :param current_time: Current timestamp
        :param period: Time period in seconds
        :param limit: Maximum requests in period
        :return: Wait time in seconds (0 if no wait needed)
        """
        cutoff_time = current_time - period

        # Count requests in period
        requests_in_period = sum(1 for t in self._request_times if t >= cutoff_time)

        if requests_in_period >= limit:
            # Find oldest request in period
            oldest_in_period = min((t for t in self._request_times if t >= cutoff_time), default=current_time)
            wait_time = (oldest_in_period + period) - current_time
            return max(0.0, wait_time + 0.01)  # Add 10ms buffer

        return 0.0

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                'total_requests': self._total_requests,
                'total_wait_time': self._total_wait_time,
                'rate_limit_hits': self._rate_limit_hits,
                'avg_wait_time': self._total_wait_time / max(1, self._rate_limit_hits),
                'requests_last_second': self._count_requests_in_period(1.0),
                'requests_last_minute': self._count_requests_in_period(60.0),
                'requests_last_hour': self._count_requests_in_period(3600.0),
            }

    def _count_requests_in_period(self, period: float) -> int:
        """Count requests in the last N seconds"""
        current_time = time.time()
        cutoff_time = current_time - period
        return sum(1 for t in self._request_times if t >= cutoff_time)

    def reset(self):
        """Reset rate limiter state"""
        with self._lock:
            self._request_times.clear()
            self._last_request_time = 0.0
            self._total_requests = 0
            self._total_wait_time = 0.0
            self._rate_limit_hits = 0
            logger.info("Rate limiter reset")


class BrokerRateLimits:
    """Predefined rate limits for Indian brokers"""

    # OpenAlgo - typically unlimited but good practice to limit
    OPENALGO = {
        'requests_per_second': 10,
        'requests_per_minute': 300,
        'min_request_interval': 0.05,  # 50ms
    }

    # Zerodha Kite Connect - 3 requests/second, with burst allowance
    ZERODHA = {
        'requests_per_second': 3,
        'requests_per_minute': 180,
        'min_request_interval': 0.33,  # ~333ms
    }

    # Angel One SmartAPI - 10 requests/second, 500/minute
    SMARTAPI = {
        'requests_per_second': 10,
        'requests_per_minute': 500,
        'min_request_interval': 0.1,  # 100ms
    }

    # Conservative default for unknown brokers
    DEFAULT = {
        'requests_per_second': 5,
        'requests_per_minute': 100,
        'min_request_interval': 0.2,  # 200ms
    }

    @classmethod
    def get_limiter(cls, broker: str) -> RateLimiter:
        """
        Get rate limiter for specific broker.

        :param broker: Broker name ('openalgo', 'zerodha', 'smartapi')
        :return: Configured RateLimiter instance
        """
        broker_lower = broker.lower()

        if broker_lower in ['openalgo', 'open_algo']:
            config = cls.OPENALGO
        elif broker_lower in ['zerodha', 'kite', 'kiteconnect']:
            config = cls.ZERODHA
        elif broker_lower in ['smartapi', 'smart_api', 'angelone', 'angel']:
            config = cls.SMARTAPI
        else:
            logger.warning(f"Unknown broker '{broker}', using default rate limits")
            config = cls.DEFAULT

        return RateLimiter(**config)


class EndpointRateLimiter:
    """
    Per-endpoint rate limiter.

    Allows different rate limits for different API endpoints.
    """

    def __init__(self, default_limiter: RateLimiter):
        """
        Initialize endpoint rate limiter.

        :param default_limiter: Default rate limiter for unspecified endpoints
        """
        self._default_limiter = default_limiter
        self._endpoint_limiters: Dict[str, RateLimiter] = {}
        self._lock = Lock()

    def add_endpoint_limit(
        self,
        endpoint: str,
        requests_per_second: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        min_request_interval: float = 0.0
    ):
        """
        Add specific rate limit for an endpoint.

        :param endpoint: Endpoint pattern (e.g., 'placeorder', 'quotes')
        :param requests_per_second: Max requests per second
        :param requests_per_minute: Max requests per minute
        :param min_request_interval: Minimum interval between requests
        """
        with self._lock:
            self._endpoint_limiters[endpoint] = RateLimiter(
                requests_per_second=requests_per_second,
                requests_per_minute=requests_per_minute,
                min_request_interval=min_request_interval
            )
            logger.info(f"Added rate limit for endpoint '{endpoint}'")

    def wait_if_needed(self, endpoint: Optional[str] = None) -> float:
        """
        Wait if rate limit would be exceeded.

        :param endpoint: Endpoint being accessed
        :return: Total wait time in seconds
        """
        wait_time = 0.0

        # Always apply default limit
        wait_time += self._default_limiter.wait_if_needed()

        # Apply endpoint-specific limit if exists
        if endpoint:
            with self._lock:
                if endpoint in self._endpoint_limiters:
                    wait_time += self._endpoint_limiters[endpoint].wait_if_needed()

        return wait_time

    def get_stats(self) -> Dict[str, any]:
        """Get combined statistics"""
        with self._lock:
            stats = {
                'default': self._default_limiter.get_stats(),
                'endpoints': {}
            }

            for endpoint, limiter in self._endpoint_limiters.items():
                stats['endpoints'][endpoint] = limiter.get_stats()

            return stats
