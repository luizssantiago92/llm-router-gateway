from pathlib import Path

import yaml


def test_compose_defines_isolated_api_and_redis_services() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]
    assert "api" in services
    assert "redis" in services
    assert services["api"].get("build") == "."
    assert "redis" in str(services["redis"].get("image", "")).lower()


def test_dockerfile_runs_fastapi_app() -> None:
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn" in text
    assert "app.main:build_default_app" in text
