<!-- retornatus-meta
{
  "change_id": "C-0010",
  "schema_version": 1
}
-->

# Situation

## Demand

Add a zero-key demo mode (cleanup plan item 13). One focused change.

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

- Demand stated: Add a zero-key demo mode (cleanup plan item 13). One focused change.
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
- Proposed WHAT: Add PROVIDER_MODE=demo. Demo providers echo the caller text, pause briefly, and fail on a documented prompt so one hop of fallback is visible. Cache and quota still use Redis. A documented gateway key is used when GATEWAY_API_KEY is absent. Live mode still requires GEMINI_API_KEY and GATEWAY_API_KEY and still calls Ollama and Gemini. Add a compose file and a curl script for that demo.
- DONE criterion: pytest exits 0
- DONE criterion: pytest with a branch-coverage floor of 90 exits 0
- DONE criterion: A demo-mode settings load returns the documented gateway key when GATEWAY_API_KEY is absent
- DONE criterion: A live-mode settings load returns an error when GEMINI_API_KEY is absent
- DONE criterion: A simple demo prompt that asks the local provider to fail returns a cloud echo
- DONE criterion: A repeated demo prompt returns a cache hit

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

The process requires GEMINI_API_KEY and GATEWAY_API_KEY before it serves. Compose will not start Redis without REDIS_PASSWORD. There is no in-process provider. Cache and quota already use Redis. PROVIDER_MODE is absent, so the default remains live. Do not change live chat status codes, request ids, the Redis failure policy, or Gemini request mapping. Do not edit .env.example or Dependabot pull requests.
