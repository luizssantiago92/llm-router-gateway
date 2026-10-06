# Changelog

Project-level notes (not a library semver). Product page: [README](../README.md). Guide: [docs/guide](guide/README.md).

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
