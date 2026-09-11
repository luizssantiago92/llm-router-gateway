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
