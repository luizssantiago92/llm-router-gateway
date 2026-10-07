<!-- retornatus-meta
{
  "change_id": "C-0006",
  "schema_version": 1
}
-->

# Situation

## Demand

Make Redis failures and provider failures explicit (polish item: resilience with a fail-open cache, a fail-closed quota, live and ready probes, and provider failover). One focused change.

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

- Demand stated: Make Redis failures and provider failures explicit (polish item: resilience with a fail-open cache, a fail-closed quota, live and ready probes, and provider failover). One focused change.
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
- Proposed WHAT: Treat cache Redis failures as a miss or a skipped write so a chat completion still returns. Treat a Redis failure while consuming daily quota as HTTP 503 and do not call a provider. Add a live health endpoint that returns HTTP 200 without probing dependencies, and a ready health endpoint that returns HTTP 503 when Redis is down or both providers are down, and HTTP 200 when Redis is up and at least one provider is up. Keep the existing health probe. On a retryable or unexpected primary provider failure, call the opposite provider once. A non-retryable primary failure does not call the secondary. Two provider failures return HTTP 502. Do not change Gemini sampling, add structured logs, or add a third provider attempt.
- DONE criterion: pytest exits 0
- DONE criterion: A Redis read failure on the cache returns the upstream completion
- DONE criterion: A Redis write failure after a completion returns HTTP 200
- DONE criterion: A Redis failure while consuming quota returns HTTP 503 and does not call a provider
- DONE criterion: The live health endpoint returns HTTP 200
- DONE criterion: The ready health endpoint returns HTTP 503 when Redis is down
- DONE criterion: The ready health endpoint returns HTTP 200 when Redis is up and one provider is up
- DONE criterion: The ready health endpoint returns HTTP 503 when both providers are down
- DONE criterion: A retryable primary failure returns the secondary completion
- DONE criterion: A non-retryable primary failure does not call the secondary provider
- DONE criterion: Two provider failures return HTTP 502

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

Cache reads and writes currently raise when Redis fails, so a chat request can die before or after a provider succeeds. Quota uses the same Redis client with no separate failure policy. GET /health mixes process liveness with dependency checks and returns 503 when Redis is down. The router already hops once on a retryable ProviderError and does not hop on a non-retryable primary failure. An unexpected exception from a provider is not part of that hop. This change keeps one hop, splits live from ready, fails open only for the cache, and fails closed when the quota counter cannot be updated.

## Reopened Situation

Restated the non-retryable primary failure so the HTTP result is observable.
