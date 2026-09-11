from __future__ import annotations

from redis.asyncio import Redis

from app.api.completions import router as completions_router
from app.cache.service import CacheService
from app.providers.ollama import OllamaProvider
from app.providers.openai import OpenAIProvider
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
) -> FastAPI:
    app = FastAPI(title="LLM Router Gateway")
    app.state.settings = settings
    app.state.cache = cache
    app.state.router = router
    app.state.local = local
    app.state.cloud = cloud
    app.state.redis = redis
    app.include_router(completions_router)
    return app


def build_default_app() -> FastAPI:
    settings = Settings.from_env()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    cache = CacheService(redis, settings.cache_ttl_seconds)
    local = OllamaProvider(
        settings.ollama_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
    )
    cloud = OpenAIProvider(
        settings.openai_api_key,
        model=settings.openai_model,
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
    )
