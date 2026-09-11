"""Daily request quota keyed by caller API key (Redis)."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta, timezone


class QuotaExceededError(Exception):
    """Raised when the caller has exhausted the daily chat quota."""


class DailyQuota:
    def __init__(self, redis: object, daily_limit: int) -> None:
        self._redis = redis
        self._limit = daily_limit

    def _bucket_key(self, api_key: str) -> str:
        digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
        return f"quota:{digest}:{date.today().isoformat()}"

    async def consume(self, api_key: str) -> None:
        key = self._bucket_key(api_key)
        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, _seconds_until_midnight_utc())
        if count > self._limit:
            await self._redis.decr(key)
            raise QuotaExceededError(
                f"daily chat quota of {self._limit} requests exhausted"
            )

    async def refund(self, api_key: str) -> None:
        key = self._bucket_key(api_key)
        value = await self._redis.get(key)
        if value is None:
            return
        if int(value) <= 0:
            return
        await self._redis.decr(key)


def _seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return max(int((tomorrow - now).total_seconds()), 60)
