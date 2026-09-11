"""Exact-match Redis cache keyed by SHA-256 of the request identity."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol


class RedisLike(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ex: int | None = None) -> None: ...


def cache_key(messages: list[dict[str, str]], temperature: float, max_tokens: int | None) -> str:
    payload = json.dumps(
        {"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CacheService:
    def __init__(self, redis: RedisLike, ttl_seconds: int) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def get(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
    ) -> dict[str, Any] | None:
        raw = await self._redis.get(cache_key(messages, temperature, max_tokens))
        if raw is None:
            return None
        return json.loads(raw)

    async def store(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
        value: dict[str, Any],
        *,
        status_code: int | None = None,
        timed_out: bool = False,
    ) -> None:
        if timed_out:
            return
        if status_code is not None and status_code >= 400:
            return
        await self._redis.set(
            cache_key(messages, temperature, max_tokens),
            json.dumps(value, ensure_ascii=False),
            ex=self._ttl_seconds,
        )
