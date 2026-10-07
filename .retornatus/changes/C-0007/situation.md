<!-- retornatus-meta
{
  "change_id": "C-0007",
  "schema_version": 1
}
-->

# Situation

## Demand

Make the Gemini adapter honor caller sampling and model choice (polish item: Gemini provider support). One focused change.

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

- Demand stated: Make the Gemini adapter honor caller sampling and model choice (polish item: Gemini provider support). One focused change.
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
- Proposed WHAT: Forward caller sampling to the Gemini generation config. When temperature is omitted, leave it out of that config; the cache key and the local adapter still use 1.0. When top_p is sent, copy it to Gemini topP and include it in the cache key. When top_p is omitted, the cache key stays the same. A request model whose name starts with gemini selects the cloud model for that call. Any other model name keeps the configured cloud model. Map a Gemini finish reason onto finish_reason. A blocked Gemini prompt with no text is a non-retryable provider failure, so the route returns HTTP 502 and does not call the secondary provider. Do not add structured logs or change the Redis failure policy.
- DONE criterion: pytest exits 0
- DONE criterion: An omitted temperature is absent from the Gemini generation config
- DONE criterion: A provided top_p is copied into the Gemini generation config as topP
- DONE criterion: An omitted top_p keeps the same cache key
- DONE criterion: A model name that starts with gemini returns that model in the Gemini request URL
- DONE criterion: A non-gemini model name returns the configured cloud model in the Gemini request URL
- DONE criterion: A Gemini MAX_TOKENS finish reason returns finish_reason length
- DONE criterion: A blocked Gemini prompt with no text returns HTTP 502 and does not call the secondary provider

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

The Gemini adapter always sends temperature and ignores top_p, stop, and the caller model. The route replaces an omitted temperature with 1.0 before the adapter runs, so Gemini cannot tell an omission from an explicit 1.0. finish_reason is always stop. A safety block with no text comes back as an empty completion. The cache key is the messages, temperature, and max_tokens triple and must stay that triple when the new fields are omitted.

## Reopened Situation

Restated sampling criteria so each one names the returned result.
