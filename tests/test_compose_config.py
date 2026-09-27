from pathlib import Path

import yaml


def test_compose_defines_isolated_api_and_redis_services() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert "api" in services
    assert "redis" in services
    assert services["api"].get("build") == "."
    assert "redis" in str(services["redis"].get("image", "")).lower()
    extra_hosts = services["api"].get("extra_hosts") or []
    assert "host.docker.internal:host-gateway" in extra_hosts
    env = services["api"]["environment"]
    assert env["REDIS_URL"] == "redis://:${REDIS_PASSWORD:?REDIS_PASSWORD is required}@redis:6379/0"
    assert "CACHE_TTL_SECONDS:-3600" in str(env["CACHE_TTL_SECONDS"])
    assert "COMPLEXITY_WORD_THRESHOLD:-150" in str(env["COMPLEXITY_WORD_THRESHOLD"])
    assert "UPSTREAM_TIMEOUT_SECONDS:-30" in str(env["UPSTREAM_TIMEOUT_SECONDS"])
    ports = services["redis"].get("ports") or []
    assert ports == ["127.0.0.1:6379:6379"]
    command = services["redis"].get("command") or []
    assert "--requirepass" in command
    assert any("REDIS_PASSWORD" in str(part) for part in command)


def test_dockerfile_runs_fastapi_app() -> None:
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn" in text
    assert "app.main:build_default_app" in text
    assert "USER app" in text
    assert "USER root" not in text
    assert "python:3.12-slim@sha256:" in text
