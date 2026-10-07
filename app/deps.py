"""FastAPI providers for process-wide gateway resources."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.cache.service import CacheService
from app.quota.daily import DailyQuota
from app.routing.router import Router
from app.settings import Settings


def _state(request: Request, name: str) -> object:
    value: object = getattr(request.app.state, name)
    return value


def get_settings(request: Request) -> Settings:
    settings = _state(request, "settings")
    if not isinstance(settings, Settings):
        raise RuntimeError("application settings are not configured")
    return settings


def get_redis(request: Request) -> object | None:
    redis = _state(request, "redis")
    return redis


def get_cache(request: Request) -> CacheService:
    cache = _state(request, "cache")
    if not isinstance(cache, CacheService):
        raise RuntimeError("cache is not configured")
    return cache


def get_router(request: Request) -> Router:
    gateway = _state(request, "router")
    if not isinstance(gateway, Router):
        raise RuntimeError("router is not configured")
    return gateway


def get_quota(request: Request) -> DailyQuota | None:
    quota = _state(request, "quota")
    if quota is None:
        return None
    if not isinstance(quota, DailyQuota):
        raise RuntimeError("quota is not configured")
    return quota


def get_local(request: Request) -> object | None:
    return _state(request, "local")


def get_cloud(request: Request) -> object | None:
    return _state(request, "cloud")


SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[object | None, Depends(get_redis)]
CacheDep = Annotated[CacheService, Depends(get_cache)]
RouterDep = Annotated[Router, Depends(get_router)]
QuotaDep = Annotated[DailyQuota | None, Depends(get_quota)]
LocalDep = Annotated[object | None, Depends(get_local)]
CloudDep = Annotated[object | None, Depends(get_cloud)]
