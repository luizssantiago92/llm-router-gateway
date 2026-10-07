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
    from app import runtime as runtime_mod
    from app.providers import gemini, ollama

    assert runtime_mod.Redis is AsyncRedis
    runtime_src = inspect.getsource(runtime_mod.build_runtime)
    assert "Redis.from_url" in runtime_src
    assert "GeminiProvider" in runtime_src
    assert "httpx.AsyncClient" in runtime_src
    factory_src = inspect.getsource(main_mod)
    assert "lifespan=lifespan" in factory_src
    assert "on_event" not in factory_src
    assert "return create_app()" in inspect.getsource(main_mod.build_default_app)
    ollama_src = inspect.getsource(ollama)
    gemini_src = inspect.getsource(gemini)
    assert "httpx.AsyncClient" in ollama_src
    assert "httpx.AsyncClient" in gemini_src
    assert "httpx.Client(" not in ollama_src
    assert "httpx.Client(" not in gemini_src
