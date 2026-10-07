import pytest
from fastapi.exceptions import RequestValidationError
from httpx import ASGITransport, AsyncClient

from app.main import _validation_param, create_app
from app.observability import AccessMiddleware, RequestMetrics
from app.providers.base import count_or_none


def test_count_or_none_rejects_booleans_and_negatives() -> None:
    assert count_or_none(True) is None
    assert count_or_none(-1) is None
    assert count_or_none(0) == 0


def test_validation_param_is_absent_when_the_error_has_no_field() -> None:
    assert _validation_param(RequestValidationError([])) is None
    only_body = RequestValidationError(
        [{"loc": ("body",), "msg": "invalid", "type": "value_error"}]
    )
    assert _validation_param(only_body) is None


@pytest.mark.asyncio
async def test_metrics_without_a_collector_returns_an_empty_body() -> None:
    app = create_app()
    app.state.metrics = "not-metrics"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.text == ""


@pytest.mark.asyncio
async def test_non_http_scope_is_forwarded() -> None:
    seen: dict[str, str] = {}

    async def inner(scope, receive, send) -> None:
        del receive, send
        seen["type"] = str(scope["type"])

    middleware = AccessMiddleware(inner)
    await middleware({"type": "lifespan"}, _unused, _unused)
    assert seen["type"] == "lifespan"


def test_metrics_render_escapes_label_characters() -> None:
    metrics = RequestMetrics()
    metrics.observe('say "hi"\n', "/v1/chat/completions", 200, 3)
    body = metrics.render()
    assert 'method="say \\"hi\\""' in body
    assert 'path="/v1/chat/completions"' in body
    assert body.endswith("\n")


async def _unused(message=None):
    del message
