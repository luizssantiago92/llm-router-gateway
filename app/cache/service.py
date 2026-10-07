"""Exact-match Redis cache keyed by SHA-256 of the request identity."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable
from typing import Any, Protocol

from app.redis_failures import REDIS_FAILURES


class RedisLike(Protocol):
    """Subset of ``redis.asyncio.Redis`` used by the exact-match cache."""

    def get(self, key: str) -> Awaitable[bytes | str | None]: ...

    def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ) -> Awaitable[bool | str | bytes | None]: ...


def cache_key(
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int | None,
    *,
    top_p: float | None = None,
    stop: list[str] | None = None,
    model: str | None = None,
) -> str:
    """Hash the prompt identity.

    Omitted sampling and model stay out of the payload so an older key still
    matches. A caller-selected cloud model is part of the identity because it
    changes the completion.
    """
    identity: dict[str, Any] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if top_p is not None:
        identity["top_p"] = top_p
    if stop:
        identity["stop"] = stop
    if model:
        identity["model"] = model
    payload = json.dumps(
        identity,
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
        *,
        top_p: float | None = None,
        stop: list[str] | None = None,
        model: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            raw = await self._redis.get(
                cache_key(
                    messages,
                    temperature,
                    max_tokens,
                    top_p=top_p,
                    stop=stop,
                    model=model,
                )
            )
        except REDIS_FAILURES:
            return None
        if raw is None:
            return None
        try:
            loaded = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            return None
        if not isinstance(loaded, dict):
            return None
        return loaded

    async def store(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
        value: dict[str, Any],
        *,
        top_p: float | None = None,
        stop: list[str] | None = None,
        model: str | None = None,
        status_code: int | None = None,
        timed_out: bool = False,
    ) -> None:
        if timed_out:
            return
        if status_code is not None and status_code >= 400:
            return
        try:
            await self._redis.set(
                cache_key(
                    messages,
                    temperature,
                    max_tokens,
                    top_p=top_p,
                    stop=stop,
                    model=model,
                ),
                json.dumps(value, ensure_ascii=False),
                ex=self._ttl_seconds,
            )
        except REDIS_FAILURES:
            return
