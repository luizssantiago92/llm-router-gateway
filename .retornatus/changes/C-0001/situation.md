<!-- retornatus-meta
{
  "change_id": "C-0001",
  "schema_version": 1
}
-->

# Situation

## Demand

Install Retornatus as the agent-governance layer for this FastAPI repo and retire leftover Spec Guardrails agent tooling.

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

- Demand stated: Install Retornatus as the agent-governance layer for this FastAPI repo and retire leftover Spec Guardrails agent tooling.
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
- Proposed WHAT: Initialize Retornatus with the fastapi preset, add the pull-request action used by gold-queen-api, and document Changes in CONTRIBUTING. Do not change application behavior.
- DONE criterion: pytest exits 0
- DONE criterion: CONTRIBUTING.md documents that contributors use Retornatus Changes
- DONE criterion: Human review note for "retornatus workflow review": deleting the new workflow file rolls back this gate and leaves the existing lint and coverage jobs in place

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

Python 3.10+ FastAPI demo. CI already runs ruff, format, mypy, pip-audit, and pytest on 3.10, 3.12, and 3.13, plus CodeQL. Spec Guardrails packs were removed earlier. Retornatus 1.9.1 is installed with uv tool install, not as a pyproject dependency, because the package requires Python 3.11+.

## Reopened Situation

DONE for the contributor doc must be a repository observation. The word documented is the marker; documents was inferred as a test.
