from pathlib import Path

import pytest

from app.settings import Settings, SETTINGS_KEYS


ROOT = Path(__file__).resolve().parents[1]


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "120")
    monkeypatch.setenv("COMPLEXITY_WORD_THRESHOLD", "80")
    monkeypatch.setenv("UPSTREAM_TIMEOUT_SECONDS", "15")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = Settings.from_env()

    assert settings.redis_url == "redis://cache:6379/0"
    assert settings.ollama_base_url == "http://ollama:11434"
    assert settings.openai_api_key == "sk-test"
    assert settings.cache_ttl_seconds == 120
    assert settings.complexity_word_threshold == 80
    assert settings.upstream_timeout_seconds == 15


def test_settings_use_documented_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "CACHE_TTL_SECONDS",
        "COMPLEXITY_WORD_THRESHOLD",
        "UPSTREAM_TIMEOUT_SECONDS",
        "OPENAI_API_KEY",
        "OLLAMA_BASE_URL",
        "REDIS_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-local")

    settings = Settings.from_env()

    assert settings.cache_ttl_seconds == 3600
    assert settings.complexity_word_threshold == 150
    assert settings.upstream_timeout_seconds == 30


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
    source = (ROOT / "app" / "settings.py").read_text(encoding="utf-8")
    assert "load_dotenv" not in source
    assert 'open(".env"' not in source
    assert 'Path(".env")' not in source
    assert (ROOT / ".env").exists() is False
