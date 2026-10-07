"""Request ids, one JSON access line per request, and in-process counters.

The access line carries the request id, method, route, status, and latency.
It does not include the submitted message text or credential headers.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_LOGGER = logging.getLogger("app.access")
_METRICS_MEDIA_TYPE = "text/plain; version=0.0.4; charset=utf-8"
_ACCESS_HANDLER = "gateway-access"


def configure_access_logger() -> None:
    """Emit access lines at INFO, including when the root logger is quieter."""
    _LOGGER.setLevel(logging.INFO)
    if any(handler.name == _ACCESS_HANDLER for handler in _LOGGER.handlers):
        return
    handler = logging.StreamHandler()
    handler.name = _ACCESS_HANDLER
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(handler)


def resolve_request_id(presented: str | None) -> str:
    """Return a caller request id, or a generated id when the value is unusable."""
    if presented is not None and _REQUEST_ID.fullmatch(presented):
        return presented
    return uuid4().hex


def metrics_media_type() -> str:
    return _METRICS_MEDIA_TYPE


class RequestMetrics:
    """Process-local request counter and latency totals."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[tuple[str, str, str], int] = {}
        self._latency_sum: dict[tuple[str, str], int] = {}
        self._latency_count: dict[tuple[str, str], int] = {}

    def observe(self, method: str, path: str, status: int, latency_ms: int) -> None:
        status_label = str(status)
        with self._lock:
            key = (method, path, status_label)
            self._requests[key] = self._requests.get(key, 0) + 1
            latency_key = (method, path)
            self._latency_sum[latency_key] = self._latency_sum.get(latency_key, 0) + latency_ms
            self._latency_count[latency_key] = self._latency_count.get(latency_key, 0) + 1

    def render(self) -> str:
        with self._lock:
            requests = sorted(self._requests.items())
            latency = sorted(self._latency_sum.items())
            counts = dict(self._latency_count)
        lines = ["# TYPE gateway_http_requests_total counter"]
        for (method, path, status), value in requests:
            lines.append(
                "gateway_http_requests_total{"
                f'method="{_label(method)}",path="{_label(path)}",status="{_label(status)}"'
                f"}} {value}"
            )
        lines.append("# TYPE gateway_http_request_latency_ms_sum counter")
        lines.append("# TYPE gateway_http_request_latency_ms_count counter")
        for (method, path), value in latency:
            lines.append(
                "gateway_http_request_latency_ms_sum{"
                f'method="{_label(method)}",path="{_label(path)}"'
                f"}} {value}"
            )
            lines.append(
                "gateway_http_request_latency_ms_count{"
                f'method="{_label(method)}",path="{_label(path)}"'
                f"}} {counts[(method, path)]}"
            )
        lines.append("")
        return "\n".join(lines)


class AccessMiddleware:
    """Attach ``X-Request-Id``, count the request, and write one access line."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = resolve_request_id(_header(scope, b"x-request-id"))
        started = time.perf_counter()
        status_code = 500
        provider: str | None = None
        cached: bool | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, provider, cached
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = MutableHeaders(raw=list(message.get("headers", [])))
                headers["X-Request-Id"] = request_id
                message["headers"] = headers.raw
                provider = _response_header(headers, "x-provider")
                cache_header = _response_header(headers, "x-cache")
                if cache_header == "true":
                    cached = True
                elif cache_header == "false":
                    cached = False
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000)
            method = str(scope.get("method", ""))
            path = _route_path(scope)
            metrics = _metrics_for(scope)
            if metrics is not None:
                metrics.observe(method, path, status_code, latency_ms)
            _LOGGER.info(
                json.dumps(
                    _access_record(
                        request_id=request_id,
                        method=method,
                        path=path,
                        status=status_code,
                        latency_ms=latency_ms,
                        provider=provider,
                        cached=cached,
                    ),
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )


def _access_record(
    *,
    request_id: str,
    method: str,
    path: str,
    status: int,
    latency_ms: int,
    provider: str | None,
    cached: bool | None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "event": "http_request",
        "latency_ms": latency_ms,
        "method": method,
        "path": path,
        "request_id": request_id,
        "status": status,
    }
    if cached is not None:
        record["cached"] = cached
    if provider:
        record["provider"] = provider
    return record


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if isinstance(key, bytes) and isinstance(value, bytes) and key.lower() == name:
            return value.decode("latin-1")
    return None


def _response_header(headers: MutableHeaders, name: str) -> str | None:
    value = headers.get(name)
    if isinstance(value, str) and value:
        return value
    return None


def _route_path(scope: Scope) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return "unmatched"


def _metrics_for(scope: Scope) -> RequestMetrics | None:
    app = scope.get("app")
    metrics = getattr(getattr(app, "state", None), "metrics", None)
    if isinstance(metrics, RequestMetrics):
        return metrics
    return None


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "").replace('"', '\\"')
