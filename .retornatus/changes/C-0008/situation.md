<!-- retornatus-meta
{
  "change_id": "C-0008",
  "schema_version": 1
}
-->

# Situation

## Demand

Add observability for the gateway: structured access logs, request ids, and metrics (audit polish item 11). One focused change.

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

- Demand stated: Add observability for the gateway: structured access logs, request ids, and metrics (audit polish item 11). One focused change.
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
- Proposed WHAT: Add a request id on every HTTP response. When the caller sends X-Request-Id as 1 to 128 characters of letters, digits, dot, underscore, or hyphen, return that id. Otherwise return a generated id. Write one JSON access log line per request containing the request id, method, route, status, and latency in milliseconds, and leave out the submitted message text and credential headers. Expose unauthenticated GET /metrics as Prometheus text whose request counter increases after a handled request. Do not change chat status codes, the Redis failure policy, or Gemini sampling.
- DONE criterion: pytest exits 0
- DONE criterion: A chat response returns an X-Request-Id header
- DONE criterion: A caller-supplied request id returns that same id
- DONE criterion: An access log line returns the request id and the status and leaves out the submitted message text
- DONE criterion: GET /metrics returns a request counter that is higher after a chat request

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

The gateway returns cache, latency, and provider on chat responses and does not write an access log or a request id. There is no metrics page. Design notes say structured logs must not carry secrets or full prompts. Chat status codes, the Redis failure policy, and Gemini sampling stay as they are.
