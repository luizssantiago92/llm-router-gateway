<!-- retornatus-meta
{
  "change_id": "C-0012",
  "schema_version": 1
}
-->

# Situation

## Demand

Consolidate the human pages, changelog, contributing notes, vulnerability page, and GitHub templates (cleanup plan item 15).

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

- Demand stated: Consolidate the human pages, changelog, contributing notes, vulnerability page, and GitHub templates (cleanup plan item 15).
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
- Proposed WHAT: Consolidate the human pages into docs/architecture.md, docs/api.md, and docs/operations.md, and keep archived material under docs/history. Place CHANGELOG.md at the repository root in Keep a Changelog form. State Retornatus, uv, and squash merges in CONTRIBUTING. Keep the vulnerability page aligned with private reporting. Add a pull request template and issue forms. Do not change application behavior, chat status codes, or the Compose ship unit.
- DONE criterion: pytest exits 0
- DONE criterion: pytest with a branch-coverage floor of 90 exits 0
- DONE criterion: The root changelog returns a Keep a Changelog heading
- DONE criterion: The architecture page returns the request path
- DONE criterion: The pull request template returns a test plan
- DONE criterion: The bug form returns a required description

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

Human pages are spread across docs/guide. The changelog is docs/CHANGELOG.md and is dated, not Keep a Changelog. CONTRIBUTING already names Retornatus and uv and does not state squash merges. SECURITY.md already points at private vulnerability reporting. There is no pull request template and no issue form. Archived kickoff files already live in docs/history. Application behavior stays as it is.
