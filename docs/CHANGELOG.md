# Changelog

Project-level notes (not a library semver). Product page: [README](../README.md). Guide: [docs/guide](guide/README.md).

## 2026-09-12

- README follows the [Spec Guardrails](https://github.com/luizssantiago92/spec-guardrails) product layout (What it is, Quick start, problem, three pillars, How it works, contract, limitations).
- Human docs move under `docs/guide/` (Overview, Quick-start, How-it-works, Architecture, API, Development, concepts, FAQ, Glossary, Limitations).
- C-009: significant PRs update README + matching guide pages in the **same** PR.
- Compose interpolates `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, and `UPSTREAM_TIMEOUT_SECONDS` from `.env`.
- Compose maps `host.docker.internal` → `host-gateway` for optional host Ollama on Linux.

## 2026-09-11

- Gemini free-tier cloud + demo `X-API-Key` + daily Redis quota (REQ-019–REQ-022). OpenAI happy path removed.
- Domain spec archived from `001-llm-router-gateway` (REQ-001–REQ-018) then extended.
- Compose demo smoke: health `degraded` without Ollama; chat `provider=cloud`.
- Independent `/verify` PASS; feature archive.

## 2026-09-10

- Spec Guardrails `python-platform` install; elicit from `prd.md`; project constitution including C-008.
