"""Daily request quota keyed by caller API key (Redis)."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable
from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol

from redis.exceptions import RedisError

from app.redis_failures import REDIS_FAILURES

_COUNTER_FAILURES = (RedisError, OSError, ValueError)


class QuotaExceededError(Exception):
    """Raised when the caller has exhausted the daily chat quota."""


class QuotaUnavailableError(Exception):
    """Raised when the daily counter cannot be updated.

    The request is refused. The gateway does not call a provider without
    a successful consume, because the quota store is fail-closed.
    """


class QuotaRedis(Protocol):
    """Subset of ``redis.asyncio.Redis`` used by the daily quota counter."""

    def incr(self, key: str) -> Awaitable[int]: ...

    def expire(self, key: str, seconds: int) -> Awaitable[bool]: ...

    def get(self, key: str) -> Awaitable[bytes | str | None]: ...

    def decr(self, key: str) -> Awaitable[int]: ...


# Fixed salt so the same caller maps to the same daily bucket. This is a key
# id, not a stored password check, and it stays deterministic across processes.
_QUOTA_SALT = b"llm-router-gateway-quota-v1"


class DailyQuota:
    def __init__(self, redis: QuotaRedis, daily_limit: int) -> None:
        self._redis = redis
        self._limit = daily_limit

    def _bucket_key(self, api_key: str) -> str:
        digest = hashlib.scrypt(
            api_key.encode("utf-8"),
            salt=_QUOTA_SALT,
            n=2**14,
            r=8,
            p=1,
            dklen=16,
        )
        return f"quota:{digest.hex()}:{date.today().isoformat()}"

    async def consume(self, api_key: str) -> None:
        key = self._bucket_key(api_key)
        try:
            count = int(await self._redis.incr(key))
        except _COUNTER_FAILURES as exc:
            raise QuotaUnavailableError("quota store unavailable") from exc
        if count == 1:
            try:
                await self._redis.expire(key, _seconds_until_midnight_utc())
            except REDIS_FAILURES as exc:
                raise QuotaUnavailableError("quota store unavailable") from exc
        if count > self._limit:
            try:
                await self._redis.decr(key)
            except REDIS_FAILURES:
                raise QuotaExceededError(
                    f"daily chat quota of {self._limit} requests exhausted"
                ) from None
            raise QuotaExceededError(f"daily chat quota of {self._limit} requests exhausted")

    async def refund(self, api_key: str) -> None:
        key = self._bucket_key(api_key)
        try:
            value = await self._redis.get(key)
            if value is None:
                return
            if int(value) <= 0:
                return
            await self._redis.decr(key)
        except _COUNTER_FAILURES:
            return


def _seconds_until_midnight_utc() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return max(int((tomorrow - now).total_seconds()), 60)
