<!-- retornatus-meta
{
  "change_id": "C-0013",
  "schema_version": 1
}
-->

# Situation

## Demand

Rewrite the front page for a recruiter (cleanup plan item 16).

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
- architecture: docs/architecture.md
- code path present: `app/main.py`
- no health endpoint symbols detected in app/main.py
- Retornatus already initialized

## Known facts

- Demand stated: Rewrite the front page for a recruiter (cleanup plan item 16).
- Repo: stack manifests: `pyproject.toml`
- Repo: tests: tests/, pytest (pyproject)
- Repo: ci: `ci.yml`, `codeql.yml`, `retornatus.yml`
- Repo: architecture: docs/architecture.md
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
- Situation narrative provided by agent/human
- Proposed WHAT: Replace the long front page with a short recruiter page: an icon, CI CodeQL license and Python badges, one value sentence, a mermaid request path, a Swagger WebP at or under 80 KB, a short cache animation, a one-minute demo, engineering decisions, a private-reporting section, and short limitations with no fixed test count. Point operators at the existing architecture, API, and operations pages. Do not change application behavior.
- DONE criterion: pytest exits 0
- DONE criterion: pytest with a branch-coverage floor of 90 exits 0
- DONE criterion: The front page returns a one-minute demo heading
- DONE criterion: The front page returns an engineering-decisions heading
- DONE criterion: The swagger image returns under 80 kilobytes

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

The front page is a long operator walkthrough. Architecture, API, and operations pages already hold that depth. There is no icon, no status badges, no mermaid block, and no screenshot. Package version stays 0.1.0. Application behavior stays as it is.
