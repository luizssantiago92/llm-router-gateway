from __future__ import annotations

from redis.asyncio import Redis

from app.api.completions import router as completions_router
from app.api.health import router as health_router
from app.cache.service import CacheService
from app.providers.gemini import GeminiProvider
from app.providers.ollama import OllamaProvider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings
from fastapi import FastAPI


def create_app(
    *,
    settings: Settings | None = None,
    cache: CacheService | None = None,
    router: Router | None = None,
    redis: object | None = None,
    local: object | None = None,
    cloud: object | None = None,
    quota: DailyQuota | None = None,
) -> FastAPI:
    app = FastAPI(title="LLM Router Gateway")
    app.state.settings = settings
    app.state.cache = cache
    app.state.router = router
    app.state.local = local
    app.state.cloud = cloud
    app.state.redis = redis
    app.state.quota = quota
    app.include_router(completions_router)
    app.include_router(health_router)
    return app


def build_default_app() -> FastAPI:
    settings = Settings.from_env()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    cache = CacheService(redis, settings.cache_ttl_seconds)
    quota = DailyQuota(redis, settings.chat_daily_limit)
    local = OllamaProvider(
        settings.ollama_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
    )
    cloud = GeminiProvider(
        settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.upstream_timeout_seconds,
    )
    router = Router(local, cloud, word_threshold=settings.complexity_word_threshold)
    return create_app(
        settings=settings,
        cache=cache,
        router=router,
        redis=redis,
        local=local,
        cloud=cloud,
        quota=quota,
    )
