<!-- retornatus-meta
{
  "change_id": "C-0005",
  "schema_version": 1
}
-->

# Situation

## Demand

Make chat responses and errors OpenAI-shaped (polish item: OpenAI-compatible response and unified error envelope, finding LLM-M4). One focused change.

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

- Demand stated: Make chat responses and errors OpenAI-shaped (polish item: OpenAI-compatible response and unified error envelope, finding LLM-M4). One focused change.
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
- Proposed WHAT: Give each chat response a unique id, a created unix time, the provider model, and usage counts taken only from provider-reported numbers. When a count is absent, return null and do not estimate. Declare the chat response model and the error responses on the route so they appear in the generated schema. Return 422 and 404, and the existing 401 and 413, as an error object with message, type, param, and code, and do not repeat the submitted text. Round latency_ms to an integer. Set the schema info version from app.__version__. Redirect GET / to /docs. Keep a missing credential as 401 before the body is read, and keep an authenticated oversized body as 413. Do not add retries, Gemini sampling changes, or structured logs.
- DONE criterion: pytest exits 0
- DONE criterion: Two chat responses return different ids
- DONE criterion: A chat response includes a created timestamp and the provider model
- DONE criterion: A chat response includes null usage counts when the provider reports none
- DONE criterion: A chat response includes usage counts when the provider reports them
- DONE criterion: Chat validation failure returns HTTP 422 without the submitted text
- DONE criterion: An unknown path returns HTTP 404 in the error envelope
- DONE criterion: HTTP 401 still precedes a body read and an oversized authenticated body returns HTTP 413
- DONE criterion: The generated schema lists a response model and the error responses
- DONE criterion: The application version in the schema info matches app.__version__
- DONE criterion: GET / redirects to /docs
- DONE criterion: latency_ms is an integer

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

Successful chat JSON uses one fixed id and omits created, model, and usage. Validation and unknown paths use a different JSON shape that can repeat the submitted body. 401 already runs before the body is read, and an authenticated oversized body is already 413. Usage counts must come from the provider payload when that payload includes them. When it does not, the fields stay null. The gateway does not estimate tokens. Latency is rounded to a whole millisecond. The schema version comes from app.__version__. GET / redirects to /docs.

## Reopened Situation

The root redirect criterion now asks for HTTP 307 so Assurance accepts the existing pytest result. The redirect target is unchanged.
