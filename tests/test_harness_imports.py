from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_app_package_imports() -> None:
    import app

    assert app.__name__ == "app"


def test_pyproject_declares_async_stack() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for package in ("fastapi", "httpx", "redis", "pydantic", "pytest-asyncio"):
        assert package in text, f"{package} must be declared in pyproject.toml"
    assert "pydantic" in text
    pydantic_line = next(
        (line for line in text.splitlines() if "pydantic" in line and "pytest" not in line),
        "",
    )
    assert "2" in pydantic_line, "pydantic v2 must be declared"


def test_production_factory_uses_async_redis_and_httpx() -> None:
    import inspect

    from redis.asyncio.client import Redis as AsyncRedis

    from app import main as main_mod
    from app.providers import ollama, openai

    assert main_mod.Redis is AsyncRedis
    factory_src = inspect.getsource(main_mod.build_default_app)
    assert "Redis.from_url" in factory_src
    ollama_src = inspect.getsource(ollama)
    openai_src = inspect.getsource(openai)
    assert "httpx.AsyncClient" in ollama_src
    assert "httpx.AsyncClient" in openai_src
    assert "httpx.Client(" not in ollama_src
    assert "httpx.Client(" not in openai_src
