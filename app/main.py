"""FastAPI application factory.

``build_default_app`` is the Uvicorn factory. It does not open sockets.
The lifespan opens Redis and the upstream HTTP clients, then closes them on
shutdown. Objects passed into ``create_app`` are test doubles: the lifespan
does not replace or close them.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.completions import router as completions_router
from app.api.health import router as health_router
from app.cache.service import CacheService
from app.providers.base import Provider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.runtime import AppRuntime, build_runtime
from app.security import GatewayUnauthorized, PayloadTooLarge
from app.settings import Settings

_RESOURCE_NAMES = (
    "settings",
    "cache",
    "router",
    "redis",
    "local",
    "cloud",
    "quota",
)


def create_app(
    *,
    settings: Settings | None = None,
    cache: CacheService | None = None,
    router: Router | None = None,
    redis: object | None = None,
    local: Provider | None = None,
    cloud: Provider | None = None,
    quota: DailyQuota | None = None,
) -> FastAPI:
    app = FastAPI(title="LLM Router Gateway", lifespan=lifespan)
    app.add_exception_handler(GatewayUnauthorized, _unauthorized)
    app.add_exception_handler(PayloadTooLarge, _payload_too_large)
    app.state.settings = settings
    app.state.cache = cache
    app.state.router = router
    app.state.redis = redis
    app.state.local = local
    app.state.cloud = cloud
    app.state.quota = quota
    app.include_router(completions_router)
    app.include_router(health_router)
    return app


async def _unauthorized(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        {"error": {"message": "missing or invalid X-API-Key", "type": "unauthorized"}},
        status_code=401,
    )


async def _payload_too_large(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "message": "request body exceeds the size limit",
                "type": "payload_too_large",
            }
        },
        status_code=413,
    )


def build_default_app() -> FastAPI:
    """Uvicorn factory. Resources open in the lifespan, not at import."""
    return create_app()


def _is_unwired(app: FastAPI) -> bool:
    return all(getattr(app.state, name) is None for name in _RESOURCE_NAMES)


def _bind(app: FastAPI, runtime: AppRuntime) -> None:
    app.state.settings = runtime.settings
    app.state.cache = runtime.cache
    app.state.router = runtime.router
    app.state.redis = runtime.redis
    app.state.local = runtime.local
    app.state.cloud = runtime.cloud
    app.state.quota = runtime.quota


def _clear(app: FastAPI) -> None:
    for name in _RESOURCE_NAMES:
        setattr(app.state, name, None)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    owned: AppRuntime | None = None
    if _is_unwired(app):
        owned = build_runtime()
        _bind(app, owned)
    try:
        yield
    finally:
        if owned is not None:
            try:
                await owned.aclose()
            finally:
                _clear(app)
