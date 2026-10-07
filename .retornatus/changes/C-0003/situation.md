<!-- retornatus-meta
{
  "change_id": "C-0003",
  "schema_version": 1
}
-->

# Situation

## Demand

Make the chat API key a FastAPI security dependency (polish item: API key as a security dependency, finding LLM-A3). One focused change.

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

- Demand stated: Make the chat API key a FastAPI security dependency (polish item: API key as a security dependency, finding LLM-A3). One focused change.
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
- Proposed WHAT: Replace the inline X-API-Key check on POST /v1/chat/completions with a FastAPI security dependency that accepts APIKeyHeader (X-API-Key) or HTTPBearer (Authorization: Bearer). Compare the presented credential to GATEWAY_API_KEY as UTF-8 bytes with secrets.compare_digest so a non-ASCII value returns 401 instead of 500. Run that check before request-body validation, including invalid JSON. Expose both schemes in the OpenAPI securitySchemes. Keep the 401 JSON body and leave GET /health unauthenticated. Do not add input size limits, OpenAI error mapping, retries, Gemini model changes, structured logs, a coverage-floor change, or a demo mode.
- DONE criterion: pytest exits 0
- DONE criterion: A non-ASCII chat credential returns HTTP 401
- DONE criterion: Chat returns HTTP 401 before request-body validation when the credential is missing
- DONE criterion: The generated schema lists an API key header scheme and an HTTP bearer scheme

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

Chat currently reads X-API-Key inside the handler and compares strings with secrets.compare_digest. A non-ASCII credential raises TypeError and becomes HTTP 500. Body parsing in FastAPI 0.141 reads JSON before endpoint dependencies, so an unauthenticated invalid body can surface as 422. Health does not require a key. The previous change C-0002 injects settings and services with Depends and owns Redis in a lifespan. CI is ruff, ruff format, mypy, pytest at 85 percent branch coverage, and pip-audit on Python 3.10, 3.12, and 3.13. Retornatus required checks are pytest, ruff, ruff-format, and mypy. Constraints: GET /health stays unauthenticated; the 401 JSON body keeps error.type unauthorized; do not implement later polish items or touch Dependabot pull requests.
