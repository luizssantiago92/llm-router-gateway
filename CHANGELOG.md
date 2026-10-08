# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-08

### Changed

- The application version is `1.0.0` in `pyproject.toml` and `app.__version__`. The OpenAPI `info.version` follows that value. The git tag and the GitHub release are applied after this change is on `main`.
- The front page leads with an icon, status badges, a one-minute demo, and pictures of the OpenAPI page and a cache hit. Setup detail stays in `docs/operations.md`.
- Human pages are `docs/architecture.md`, `docs/api.md`, and `docs/operations.md`. Archived kickoff material stays in `docs/history/`.
- This file is the changelog. `CONTRIBUTING.md` states Retornatus, uv, and squash merges. Pull requests and issues use GitHub templates.

## [0.1.0] - 2026-10-07

Work shipped on `main` through the Compose hardening merge. Earlier notes were dated; they are kept here under the package version `0.1.0`.

### Added

- Compose publishes the API on `127.0.0.1:8000` only and pins `redis:7-alpine` by digest. The API starts after Redis is healthy, and both services restart unless stopped. The image probes `GET /health/live`. `make dev`, `make test`, `make lint`, and `make demo` are the local shortcuts. (2026-10-07)
- `PROVIDER_MODE=demo` serves chat without a Gemini key. Demo providers echo the caller text, pause briefly, and fail when the prompt contains `simulate-local-failure` or `simulate-cloud-failure`, so one fallback hop is visible. `compose.demo.yml` and `scripts/demo.sh` use the gateway key `demo`. Live mode still requires the Gemini and gateway keys. (2026-10-07)
- The pytest branch-coverage gate is 90%. Adapter and health tests cover Ollama sampling options, Gemini timeouts, and a health probe with no Redis client. (2026-10-07)
- Every response returns `X-Request-Id` (a caller token, or a generated id). One JSON access log line records the request id, method, route, status, and latency, and leaves out the submitted message text and credential headers. `GET /metrics` returns Prometheus counters for requests and latency. (2026-10-07)
- Gemini generation config receives `temperature` only when the caller set it, plus `topP`, `maxOutputTokens`, and `stopSequences` when those fields are set. A Gemini model id on the request selects the cloud model for that call. Gemini `MAX_TOKENS` maps to `finish_reason` `length`. A blocked Gemini prompt with no text returns HTTP 502 and does not call the other provider. (2026-10-07)
- Cache Redis failures fail open: a read error is a miss, and a write error still returns the completion. Quota Redis failures fail closed with HTTP 503 and do not call a provider. The quota bucket id is a scrypt digest of the caller credential. `GET /health/live` does not probe dependencies. `GET /health/ready` is ready only when Redis is up and at least one provider is up. A retryable or unexpected primary failure hops once; a non-retryable primary failure does not. (2026-10-07)
- Chat responses include a unique id, `created`, `model`, and provider-reported `usage` (null when the provider sent no count). Validation and unknown paths use the same `{"error": ...}` envelope as 401 and 413, without repeating the submitted text. `latency_ms` is a whole millisecond. `GET /` redirects to `/docs`. The schema version is `app.__version__`. (2026-10-06)
- Chat rejects out-of-range roles, message sizes, temperature, and `max_tokens`, and refuses an authenticated body over 256 KiB with HTTP 413. A missing credential on an oversized body is still HTTP 401, and the body is not read. Settings can tighten those ceilings. (2026-10-06)
- Chat accepts `X-API-Key` or `Authorization: Bearer` through a FastAPI security dependency. The key is compared as UTF-8 bytes, and a missing or non-ASCII credential is HTTP 401 before the body is validated. (2026-10-06)
- The Uvicorn factory registers a FastAPI lifespan that opens the async Redis client and the upstream HTTP clients on startup and closes them on shutdown. Chat and health handlers receive those resources through FastAPI dependencies. (2026-10-06)
- CI runs `ruff check`, `ruff format --check`, `mypy app`, pytest with an 85% branch-coverage gate, and `pip-audit` on Python 3.10, 3.12, and 3.13. Pushes to `main` are not cancelled by a later push. The gate was later raised to 90%. (2026-10-06)
- CodeQL analyzes Python and GitHub Actions on pull requests, pushes to `main`, and a weekly schedule. (2026-10-06)
- Dependabot groups minor and patch updates for the `uv` ecosystem and GitHub Actions (Mondays 09:00 America/Sao_Paulo). (2026-10-06)
- GitHub Actions CI runs `ruff` and pytest with least-privilege `contents: read` and SHA-pinned actions. (2026-09-27)
- Python dependencies are locked with `uv.lock`. `pyproject.toml` keeps upper bounds and stays pip-compatible. (2026-09-27)
- Compose requires `REDIS_PASSWORD` and publishes Redis on `127.0.0.1:6379` only. (2026-09-27)
- The API image runs as non-root user `app` from a digest-pinned `python:3.12-slim` base. (2026-09-27)
- The Gemini adapter sends the API key in the `x-goog-api-key` header. (2026-09-27)
- MIT `LICENSE` (Copyright Luiz Santiago) and `SECURITY.md`. (2026-09-27)
- Root README uses a numbered operator path. Human pages were under `docs/guide/`. (2026-09-14)
- README follows a product layout. Significant pull requests update the README and the matching human page in the same pull request. (2026-09-12)
- Compose interpolates `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, and `UPSTREAM_TIMEOUT_SECONDS` from `.env`, and maps `host.docker.internal` to `host-gateway`. (2026-09-12)
- Gemini free-tier cloud, a demo `X-API-Key`, and a daily Redis quota (REQ-019–REQ-022). The OpenAI happy path was removed. (2026-09-11)
- Domain spec archived from `001-llm-router-gateway` (REQ-001–REQ-018), then extended. (2026-09-11)
- Project kickoff from `prd.md` (now `docs/history/PRD.pt-BR.md`). (2026-09-10)
