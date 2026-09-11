from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    redis_ok = await _redis_ok(request.app.state.redis)
    local_ok = await _provider_ok(request.app.state.local)
    cloud_ok = await _provider_ok(request.app.state.cloud)
    payload = {
        "status": "ok",
        "redis": "up" if redis_ok else "down",
        "providers": {
            "local": "up" if local_ok else "down",
            "cloud": "up" if cloud_ok else "down",
        },
    }
    if not redis_ok:
        payload["status"] = "down"
        return JSONResponse(payload, status_code=503)
    if not local_ok or not cloud_ok:
        payload["status"] = "degraded"
        return JSONResponse(payload, status_code=200)
    return JSONResponse(payload, status_code=200)


async def _redis_ok(redis: object) -> bool:
    if redis is None:
        return False
    ping = getattr(redis, "ping", None)
    if ping is None:
        return True
    try:
        result = await ping()
        return bool(result)
    except Exception:
        return False


async def _provider_ok(provider: object) -> bool:
    if provider is None:
        return False
    health = getattr(provider, "health", None)
    if health is None:
        return True
    try:
        return bool(await health())
    except Exception:
        return False
