"""Environment-backed process settings. Values never come from git."""

from __future__ import annotations

import os
from dataclasses import dataclass

SETTINGS_KEYS = (
    "REDIS_URL",
    "OLLAMA_BASE_URL",
    "GEMINI_API_KEY",
    "GATEWAY_API_KEY",
    "CACHE_TTL_SECONDS",
    "COMPLEXITY_WORD_THRESHOLD",
    "UPSTREAM_TIMEOUT_SECONDS",
    "CHAT_DAILY_LIMIT",
)

_DEFAULTS = {
    "CACHE_TTL_SECONDS": "3600",
    "COMPLEXITY_WORD_THRESHOLD": "150",
    "UPSTREAM_TIMEOUT_SECONDS": "30",
    "CHAT_DAILY_LIMIT": "5",
    "GEMINI_MODEL": "gemini-3.5-flash",
}


@dataclass(frozen=True)
class Settings:
    redis_url: str
    ollama_base_url: str
    gemini_api_key: str
    gateway_api_key: str
    cache_ttl_seconds: int
    complexity_word_threshold: int
    upstream_timeout_seconds: int
    chat_daily_limit: int = 5
    gemini_model: str = "gemini-3.5-flash"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            redis_url=_require("REDIS_URL"),
            ollama_base_url=_require("OLLAMA_BASE_URL"),
            gemini_api_key=_require("GEMINI_API_KEY"),
            gateway_api_key=_require("GATEWAY_API_KEY"),
            cache_ttl_seconds=int(os.environ.get("CACHE_TTL_SECONDS", _DEFAULTS["CACHE_TTL_SECONDS"])),
            complexity_word_threshold=int(
                os.environ.get("COMPLEXITY_WORD_THRESHOLD", _DEFAULTS["COMPLEXITY_WORD_THRESHOLD"])
            ),
            upstream_timeout_seconds=int(
                os.environ.get("UPSTREAM_TIMEOUT_SECONDS", _DEFAULTS["UPSTREAM_TIMEOUT_SECONDS"])
            ),
            chat_daily_limit=int(os.environ.get("CHAT_DAILY_LIMIT", _DEFAULTS["CHAT_DAILY_LIMIT"])),
            gemini_model=os.environ.get("GEMINI_MODEL", _DEFAULTS["GEMINI_MODEL"]),
        )


def _require(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable {key}")
    return value
