from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.deps import CloudDep, LocalDep, RedisDep

router = APIRouter()


@router.get("/health/live")
async def health_live() -> JSONResponse:
    """Process liveness. This route does not probe Redis or providers."""
    return JSONResponse({"status": "live"}, status_code=200)


@router.get("/health/ready")
async def health_ready(redis: RedisDep, local: LocalDep, cloud: CloudDep) -> JSONResponse:
    """Readiness. Redis must be up, and at least one provider must be up."""
    redis_ok, local_ok, cloud_ok = await _probe(redis, local, cloud)
    ready = redis_ok and (local_ok or cloud_ok)
    return JSONResponse(
        _status_payload("ready" if ready else "not_ready", redis_ok, local_ok, cloud_ok),
        status_code=200 if ready else 503,
    )


@router.get("/health")
async def health(redis: RedisDep, local: LocalDep, cloud: CloudDep) -> JSONResponse:
    redis_ok, local_ok, cloud_ok = await _probe(redis, local, cloud)
    payload = _status_payload("ok", redis_ok, local_ok, cloud_ok)
    if not redis_ok:
        payload["status"] = "down"
        return JSONResponse(payload, status_code=503)
    if not local_ok or not cloud_ok:
        payload["status"] = "degraded"
        return JSONResponse(payload, status_code=200)
    return JSONResponse(payload, status_code=200)


def _status_payload(
    status: str,
    redis_ok: bool,
    local_ok: bool,
    cloud_ok: bool,
) -> dict[str, object]:
    return {
        "status": status,
        "redis": "up" if redis_ok else "down",
        "providers": {
            "local": "up" if local_ok else "down",
            "cloud": "up" if cloud_ok else "down",
        },
    }


async def _probe(
    redis: object | None,
    local: object | None,
    cloud: object | None,
) -> tuple[bool, bool, bool]:
    return (
        await _redis_ok(redis),
        await _provider_ok(local),
        await _provider_ok(cloud),
    )


async def _redis_ok(redis: object) -> bool:
    if redis is None:
        return False
    ping = getattr(redis, "ping", None)
    if ping is None:
        return True
    try:
        result = await ping()
        return bool(result)
    except Exception:  # noqa: BLE001 — a failed ping means Redis is down
        return False


async def _provider_ok(provider: object) -> bool:
    if provider is None:
        return False
    health = getattr(provider, "health", None)
    if health is None:
        return True
    try:
        return bool(await health())
    except Exception:  # noqa: BLE001 — a failed probe means the provider is down
        return False
