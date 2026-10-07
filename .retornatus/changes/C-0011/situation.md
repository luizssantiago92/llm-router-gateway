<!-- retornatus-meta
{
  "change_id": "C-0011",
  "schema_version": 1
}
-->

# Situation

## Demand

Harden Compose and the API image (cleanup plan item 14). One focused change.

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

- Demand stated: Harden Compose and the API image (cleanup plan item 14). One focused change.
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
- Proposed WHAT: Publish the API on 127.0.0.1 port 8000, pin the Redis image by digest, add healthchecks, depend on Redis only when it is healthy, and restart unless stopped. Add an image HEALTHCHECK that probes /health/live. Add a Makefile with dev, test, lint, and demo. Apply the same loopback, digest, health, and restart rules to the zero-key compose file. Do not change chat status codes, request ids, demo provider behavior, or the Redis failure policy.
- DONE criterion: pytest exits 0
- DONE criterion: pytest with a branch-coverage floor of 90 exits 0
- DONE criterion: The compose file returns an API port bound to 127.0.0.1
- DONE criterion: The compose file returns a Redis image pinned by digest
- DONE criterion: The image healthcheck returns a probe of /health/live
- DONE criterion: make test returns a pytest command

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

Compose publishes the API on every interface at port 8000 and pins Redis only by the floating tag redis:7-alpine. Services have no healthcheck, depends_on does not wait for healthy, and there is no restart policy. The image has no HEALTHCHECK. There is no Makefile. The zero-key compose file has the same port and tag gaps. Do not edit .env.example or Dependabot pull requests.
