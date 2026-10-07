<!-- retornatus-meta
{
  "change_id": "C-0009",
  "schema_version": 1
}
-->

# Situation

## Demand

Raise the branch-coverage gate from 85 to 90 and add the tests that keep the suite above that floor (cleanup plan item 12). One focused change.

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

- Demand stated: Raise the branch-coverage gate from 85 to 90 and add the tests that keep the suite above that floor (cleanup plan item 12). One focused change.
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
- Proposed WHAT: Raise the pytest branch-coverage gate from 85 to 90 and add tests that keep the suite above that floor. Cover Ollama sampling options, a Gemini timeout, and a health probe that returns false when Redis is absent. Do not change chat status codes, request ids, the Redis failure policy, or Gemini request mapping.
- DONE criterion: pytest exits 0
- DONE criterion: pytest with a branch-coverage floor of 90 exits 0
- DONE criterion: An Ollama request that includes top_p and stop returns those options
- DONE criterion: A Gemini timeout returns a retryable provider error
- DONE criterion: A health probe with no Redis client returns false

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

CI fails pytest when branch coverage is under 85. The comment in the workflow says a later test pass raises that floor to 90. Ollama sampling options, Gemini timeouts, and a health probe with no Redis client are not covered. Chat status codes, request ids, the Redis failure policy, and Gemini request mapping stay as they are.

## Reopened Situation

The workflow path needs a review claim before the scope gate can pass.
