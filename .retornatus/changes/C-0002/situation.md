<!-- retornatus-meta
{
  "change_id": "C-0002",
  "schema_version": 1
}
-->

# Situation

## Demand

Improve FastAPI app startup/shutdown and dependency wiring (polish item: FastAPI lifespan / deps). One focused change. Do not implement later polish items.

## Project context

# Project

Retornatus continuity map for llm-router-gateway.

## Identity

- Repository: llm-router-gateway
- README signal: # LLM Router Gateway

## Language / stack

- `pyproject.toml`

## Important directories

- `app`
- `tests`
- `docs`
- `.github`
- `.cursor`

## Tests

- tests/
- pytest (pyproject)

## CI

- `ci.yml`
- `codeql.yml`
- `retornatus.yml`

## Architecture clues

- (none detected)

## Environment capabilities

- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False

## Existing Retornatus state

- changes: 0
- rules: 0
- skills: 0

## Conventions

_Agents: update this file when durable project conventions are discovered._

## Stack notes

_Fill during Wake / first Change. Prefer facts from the repo over assumptions._

## Repo signals (inferred)

- stack manifests: `pyproject.toml`
- tests: tests/, pytest (pyproject)
- ci: `ci.yml`, `codeql.yml`, `retornatus.yml`
- code path present: `app/main.py`
- no health endpoint symbols detected in app/main.py
- Retornatus already initialized

## Known facts

- Demand stated: Improve FastAPI app startup/shutdown and dependency wiring (polish item: FastAPI lifespan / deps). One focused change. Do not implement later polish items.
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `codeql.yml`, `retornatus.yml`
- Repo: code path present: `app/main.py`
- Repo: no health endpoint symbols detected in app/main.py
- Repo: Retornatus already initialized
- Repository: llm-router-gateway
- README signal: # LLM Router Gateway
- `pyproject.toml`
- `app`
- `tests`
- `docs`
- `.github`
- `.cursor`
- tests/
- pytest (pyproject)
- `ci.yml`
- `codeql.yml`
- `retornatus.yml`
- (none detected)
- Detected: `cursor`
- native_rules: True
- native_skills: True
- native_sandbox: False
- changes: 0
- rules: 0
- skills: 0
- Situation narrative provided by agent/human
- Proposed WHAT: Replace eager resource construction in the Uvicorn factory with a FastAPI lifespan that opens the async Redis client and the upstream HTTP clients on startup and closes them on shutdown. Expose FastAPI dependency providers for settings, Redis, cache, router, quota, and the local and cloud provider clients so chat and health handlers receive those objects explicitly. Tests may still inject fakes through create_app; the lifespan must not replace or close injected objects. Public HTTP routes, status codes, and response bodies stay the same. Out of scope: an API-key security dependency, input size limits, OpenAI error mapping, retries, Gemini model changes, structured logs, a coverage-floor change, a demo mode, and Dependabot pull requests 17 and 18. Keep the process entrypoint app.main:build_default_app.
- DONE criterion: pytest exits 0
- DONE criterion: The default FastAPI lifespan opens an async Redis client and httpx.AsyncClient instances and closes them on shutdown
- DONE criterion: Chat and health handlers receive settings, Redis, and provider clients through FastAPI dependencies
- DONE criterion: POST /v1/chat/completions and GET /health keep their current status codes and payloads when the app is configured

## Constraints

- Prefer pytest for automated verification (inferred from repo)
- Prefer pytest for automated verification (inferred from repo)

## Assumptions

- (none)

## Ambiguities

- (none)

## Missing decisions

- (none)

## Contract readiness

- Sufficient: **yes**
- Rationale: Demand, WHAT, and DONE are sufficiently clear; repo/kickoff signals incorporated; no material requirements ambiguity detected

## Agent narrative

The gateway is a Python 3.10+ FastAPI app. Uvicorn starts app.main:build_default_app with --factory (Dockerfile). build_default_app currently constructs Settings, redis.asyncio.Redis, CacheService, DailyQuota, OllamaProvider, GeminiProvider, and Router before the server is serving, and never closes Redis or HTTP clients. There is no @app.on_event handler. Handlers in app/api/completions.py and app/api/health.py read request.app.state. Tests build fakes with create_app(...) and httpx ASGITransport, which does not enter the production lifespan. CI is ruff, ruff format, mypy, pytest with an 85% branch-coverage gate, and pip-audit on Python 3.10, 3.12, and 3.13. Retornatus 1.9.1 required checks are pytest, ruff, ruff-format, and mypy. Constraints: do not add an API-key security dependency, input size limits, OpenAI error mapping, retries, Gemini model changes, structured logs, a coverage-floor change, or a demo mode; do not change Dependabot PRs 17 and 18; do not switch the entrypoint away from app.main:build_default_app; no public API behavior change except startup correctness.
