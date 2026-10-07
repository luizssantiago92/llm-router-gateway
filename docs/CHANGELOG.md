# Changelog

Project-level notes (not a library semver). Product page: [README](../README.md). Guide: [docs/guide](guide/README.md).

## 2026-10-07

- Cache Redis failures fail open: a read error is a miss, and a write error still returns the completion. Quota Redis failures fail closed with HTTP 503 and do not call a provider. `GET /health/live` does not probe dependencies. `GET /health/ready` is ready only when Redis is up and at least one provider is up. A retryable or unexpected primary failure hops once; a non-retryable primary failure does not.

## 2026-10-06

- Chat responses include a unique id, `created`, `model`, and provider-reported `usage` (null when the provider sent no count). Validation and unknown paths use the same `{"error": ...}` envelope as 401 and 413, without repeating the submitted text. `latency_ms` is a whole millisecond. `GET /` redirects to `/docs`. The schema version is `app.__version__`.
- Chat rejects out-of-range roles, message sizes, temperature, and `max_tokens`, and refuses an authenticated body over 256 KiB with HTTP 413. A missing credential on an oversized body is still HTTP 401, and the body is not read. Settings can tighten those ceilings.
- Chat accepts `X-API-Key` or `Authorization: Bearer` through a FastAPI security dependency. The key is compared as UTF-8 bytes, and a missing or non-ASCII credential is HTTP 401 before the body is validated.
- The Uvicorn factory registers a FastAPI lifespan that opens the async Redis client and the upstream HTTP clients on startup and closes them on shutdown. Chat and health handlers receive those resources through FastAPI dependencies.
- CI runs `ruff check`, `ruff format --check`, `mypy app`, pytest with an 85% branch-coverage gate, and `pip-audit` on Python 3.10, 3.12, and 3.13. Pushes to `main` are not cancelled by a later push.
- CodeQL analyzes Python and GitHub Actions on pull requests, pushes to `main`, and a weekly schedule.
- Dependabot groups minor and patch updates for the `uv` ecosystem and GitHub Actions (Mondays 09:00 America/Sao_Paulo).

## 2026-09-27

- GitHub Actions CI runs `ruff` and pytest with least-privilege `contents: read` and SHA-pinned actions.
- Python dependencies are locked with `uv.lock`. `pyproject.toml` keeps upper bounds and stays pip-compatible.
- Compose requires `REDIS_PASSWORD` and publishes Redis on `127.0.0.1:6379` only.
- The API image runs as non-root user `app` from a digest-pinned `python:3.12-slim` base.
- The Gemini adapter sends the API key in the `x-goog-api-key` header.
- MIT `LICENSE` (Copyright Luiz Santiago) and `SECURITY.md`.

## 2026-09-14

- Root README uses a numbered operator path (TOC, Prepare / Run / Verify, first-access checks, checklist, command cheat sheet, repo map).
- Human docs remain under `docs/guide/`.

## 2026-09-12

- README follows a product layout (What it is, Quick start, problem, three pillars, How it works, contract, limitations).
- Human docs move under `docs/guide/` (Overview, Quick-start, How-it-works, Architecture, API, Development, concepts, FAQ, Glossary, Limitations).
- Significant PRs update README + matching guide pages in the **same** PR.
- Compose interpolates `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, and `UPSTREAM_TIMEOUT_SECONDS` from `.env`.
- Compose maps `host.docker.internal` → `host-gateway` for optional host Ollama on Linux.

## 2026-09-11

- Gemini free-tier cloud + demo `X-API-Key` + daily Redis quota (REQ-019–REQ-022). OpenAI happy path removed.
- Domain spec archived from `001-llm-router-gateway` (REQ-001–REQ-018) then extended.
- Compose demo smoke: health `degraded` without Ollama; chat `provider=cloud`.
- Independent `/verify` PASS; feature archive.

## 2026-09-10

- Project kickoff from `prd.md` (now `docs/history/PRD.pt-BR.md`).
