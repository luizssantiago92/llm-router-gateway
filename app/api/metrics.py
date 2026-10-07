from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.observability import RequestMetrics, metrics_media_type

router = APIRouter()


@router.get("/metrics")
async def metrics(request: Request) -> PlainTextResponse:
    """Prometheus text for request counts and latency totals.

    This route does not require a credential. The body is counters only.
    """
    collected = getattr(request.app.state, "metrics", None)
    if not isinstance(collected, RequestMetrics):
        return PlainTextResponse("", media_type=metrics_media_type())
    return PlainTextResponse(collected.render(), media_type=metrics_media_type())
