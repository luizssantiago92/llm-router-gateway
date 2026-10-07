"""Process-wide Redis connection and upstream HTTP clients."""

from __future__ import annotations

import httpx
from redis.asyncio import Redis

from app.cache.service import CacheService
from app.providers.base import Provider
from app.providers.demo import DEMO_LATENCY_SECONDS, DemoProvider
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings


class AppRuntime:
    """Resources the lifespan owns and closes on shutdown."""

    def __init__(
        self,
        *,
        settings: Settings,
        redis: Redis,
        local_client: httpx.AsyncClient,
        cloud_client: httpx.AsyncClient,
        local: Provider,
        cloud: Provider,
        cache: CacheService,
        quota: DailyQuota,
        router: Router,
    ) -> None:
        self.settings = settings
        self.redis = redis
        self.local_client = local_client
        self.cloud_client = cloud_client
        self.local = local
        self.cloud = cloud
        self.cache = cache
        self.quota = quota
        self.router = router

    async def aclose(self) -> None:
        try:
            await self.redis.aclose()
        finally:
            try:
                await self.local_client.aclose()
            finally:
                await self.cloud_client.aclose()


def build_runtime(settings: Settings | None = None) -> AppRuntime:
    """Open async Redis and one HTTP client per upstream provider."""
    resolved = Settings.from_env() if settings is None else settings
    redis = Redis.from_url(resolved.redis_url, decode_responses=True)
    timeout = resolved.upstream_timeout_seconds
    local_client = httpx.AsyncClient(timeout=timeout)
    cloud_client = httpx.AsyncClient(timeout=timeout)
    local: Provider
    cloud: Provider
    if resolved.provider_mode == "demo":
        local = DemoProvider("local", delay_seconds=DEMO_LATENCY_SECONDS)
        cloud = DemoProvider("cloud", delay_seconds=DEMO_LATENCY_SECONDS)
    else:
        local = OllamaProvider(
            resolved.ollama_base_url,
            timeout_seconds=timeout,
            client=local_client,
        )
        cloud = GeminiProvider(
            resolved.gemini_api_key,
            model=resolved.gemini_model,
            timeout_seconds=timeout,
            client=cloud_client,
        )
    cache = CacheService(redis, resolved.cache_ttl_seconds)
    quota = DailyQuota(redis, resolved.chat_daily_limit)
    router = Router(local, cloud, word_threshold=resolved.complexity_word_threshold)
    return AppRuntime(
        settings=resolved,
        redis=redis,
        local_client=local_client,
        cloud_client=cloud_client,
        local=local,
        cloud=cloud,
        cache=cache,
        quota=quota,
        router=router,
    )
