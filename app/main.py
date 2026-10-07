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
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from app import __version__
from app.api.completions import router as completions_router
from app.api.health import router as health_router
from app.cache.service import CacheService
from app.providers.base import Provider
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.runtime import AppRuntime, build_runtime
from app.schemas.chat import error_payload
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
    app = FastAPI(
        title="LLM Router Gateway",
        version=__version__,
        description=(
            "OpenAI-shaped chat facade. Token counts are copied from the provider. "
            "A count the provider did not report is null; the gateway does not estimate it."
        ),
        lifespan=lifespan,
    )
    app.add_exception_handler(GatewayUnauthorized, _unauthorized)
    app.add_exception_handler(PayloadTooLarge, _payload_too_large)
    app.add_exception_handler(RequestValidationError, _invalid_request)
    app.add_exception_handler(404, _not_found)
    app.add_api_route("/", _docs_redirect, methods=["GET"], include_in_schema=False)
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


def _docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=307)


async def _unauthorized(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        error_payload(
            "missing or invalid X-API-Key",
            "unauthorized",
            code="invalid_api_key",
        ),
        status_code=401,
    )


async def _payload_too_large(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        error_payload(
            "request body exceeds the size limit",
            "payload_too_large",
            code="payload_too_large",
        ),
        status_code=413,
    )


def _validation_param(exc: RequestValidationError) -> str | None:
    errors = exc.errors()
    if not errors:
        return None
    loc = errors[0].get("loc", ())
    parts = [str(part) for part in loc if str(part) != "body"]
    if not parts:
        return None
    return ".".join(parts)


async def _invalid_request(_request: Request, exc: Exception) -> JSONResponse:
    param = _validation_param(exc) if isinstance(exc, RequestValidationError) else None
    return JSONResponse(
        error_payload(
            "request validation failed",
            "invalid_request_error",
            param=param,
            code="validation_error",
        ),
        status_code=422,
    )


async def _not_found(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        error_payload("Not Found", "not_found", code="not_found"),
        status_code=404,
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
