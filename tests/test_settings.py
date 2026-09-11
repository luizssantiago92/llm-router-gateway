from pathlib import Path

import pytest

from app.settings import Settings, SETTINGS_KEYS


ROOT = Path(__file__).resolve().parents[1]


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.setenv("GATEWAY_API_KEY", "gateway-test")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "120")
    monkeypatch.setenv("COMPLEXITY_WORD_THRESHOLD", "80")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("CHAT_DAILY_LIMIT", "3")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    settings = Settings.from_env()

    assert settings.redis_url == "redis://cache:6379/0"
    assert settings.ollama_base_url == "http://ollama:11434"
    assert settings.gemini_api_key == "gemini-test"
    assert settings.gateway_api_key == "gateway-test"
    assert settings.cache_ttl_seconds == 120
    assert settings.complexity_word_threshold == 80
    assert settings.upstream_timeout_seconds == 15
    assert settings.chat_daily_limit == 3
    assert settings.gemini_model == "gemini-3.5-flash"


def test_settings_use_documented_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in SETTINGS_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-local")
    monkeypatch.setenv("GATEWAY_API_KEY", "gateway-local")

    settings = Settings.from_env()

    assert settings.cache_ttl_seconds == 3600
    assert settings.complexity_word_threshold == 150
    assert settings.upstream_timeout_seconds == 30
    assert settings.chat_daily_limit == 5


def test_env_example_lists_keys_without_values() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in SETTINGS_KEYS:
        assert key in text
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        _, value = line.split("=", 1)
        assert value == "", f"committed example must not contain a secret value: {raw}"


def test_settings_do_not_read_committed_secret_files() -> None:
    import subprocess

    source = (ROOT / "app" / "settings.py").read_text(encoding="utf-8")
    assert "load_dotenv" not in source
    assert 'open(".env"' not in source
    assert 'Path(".env")' not in source
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    # Local `.env` is expected for operators; it must never be git-tracked.
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".env"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, ".env must not be tracked by git"
