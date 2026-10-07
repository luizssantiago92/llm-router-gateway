"""Chat authentication as a FastAPI security dependency.

``APIKeyHeader`` and ``HTTPBearer`` are both optional schemes. A presented
credential is compared to ``GATEWAY_API_KEY`` as UTF-8 bytes so a non-ASCII
value is a 401, not a ``TypeError``. ``AuthFirstRoute`` runs that check before
the chat route reads the body.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Coroutine
from inspect import isawaitable
from typing import Annotated, Any

from fastapi import Request, Security
from fastapi.routing import APIRoute
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response

from app.deps import SettingsDep, get_settings
from app.settings import Settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    scheme_name="APIKeyHeader",
)
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="HTTPBearer")


class GatewayUnauthorized(Exception):
    """The chat credential is missing or does not match the gateway key."""


def keys_match(presented: str, expected: str) -> bool:
    """Return whether ``presented`` matches ``expected`` in constant time.

    An empty gateway key never matches. Values are compared as UTF-8 bytes
    because ``secrets.compare_digest`` rejects non-ASCII ``str`` inputs.
    """
    if not expected:
        return False
    return secrets.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


async def require_gateway_key(
    settings: SettingsDep,
    api_key: Annotated[str | None, Security(api_key_header)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> str:
    expected = settings.gateway_api_key
    presented_header = api_key or ""
    presented_bearer = credentials.credentials if credentials is not None else ""
    header_ok = keys_match(presented_header, expected)
    bearer_ok = keys_match(presented_bearer, expected)
    if header_ok:
        return presented_header
    if bearer_ok:
        return presented_bearer
    raise GatewayUnauthorized()


GatewayKeyDep = Annotated[str, Security(require_gateway_key)]


async def _settings_for(request: Request) -> Settings:
    override = request.app.dependency_overrides.get(get_settings)
    if override is None:
        return get_settings(request)
    result = override()
    if isawaitable(result):
        result = await result
    if not isinstance(result, Settings):
        raise RuntimeError("application settings are not configured")
    return result


async def enforce_gateway_key(request: Request) -> str:
    """Run the security dependency before the route reads a body."""
    override = request.app.dependency_overrides.get(require_gateway_key)
    if override is not None:
        result = override()
        if isawaitable(result):
            result = await result
        if not isinstance(result, str):
            raise GatewayUnauthorized()
        return result
    return await require_gateway_key(
        settings=await _settings_for(request),
        api_key=await api_key_header(request),
        credentials=await bearer_scheme(request),
    )


class AuthFirstRoute(APIRoute):
    """Reject a bad chat credential before request-body validation."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def auth_first(request: Request) -> Response:
            await enforce_gateway_key(request)
            return await original(request)

        return auth_first
