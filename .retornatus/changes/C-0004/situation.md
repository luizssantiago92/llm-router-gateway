<!-- retornatus-meta
{
  "change_id": "C-0004",
  "schema_version": 1
}
-->

# Situation

## Demand

Cap chat request size and reject out-of-range chat fields (polish item: request limits and body size cap, finding LLM-A2). One focused change.

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

- Demand stated: Cap chat request size and reject out-of-range chat fields (polish item: request limits and body size cap, finding LLM-A2). One focused change.
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
- Proposed WHAT: Bound POST /v1/chat/completions: role is system, user, or assistant; each content is 1 to 32000 characters; messages length is 1 to 50; combined message characters are at most 64000; temperature is omitted or between 0 and 2; max_tokens is omitted or between 1 and 4096. When temperature is omitted, upstream calls still receive 1.0 and Gemini sampling stays unchanged. Refuse a body over the byte cap with HTTP 413 after a valid credential. A missing credential still returns HTTP 401 before the body is read, including when the body exceeds the cap. Numeric caps are settings with those safe defaults, and settings may only tighten them. Do not add an OpenAI error envelope, retries, Gemini model changes, or structured logs.
- DONE criterion: pytest exits 0
- DONE criterion: An empty message list is rejected
- DONE criterion: A role other than system, user, or assistant is rejected
- DONE criterion: temperature below 0 or above 2 is rejected
- DONE criterion: max_tokens below 1 or above 4096 is rejected
- DONE criterion: A message of 32001 characters is rejected and a message of 32000 characters is accepted
- DONE criterion: A list of 51 messages is rejected and a list of 50 messages is accepted
- DONE criterion: Combined message characters above 64000 are rejected and 64000 are accepted
- DONE criterion: A chat body larger than the size cap returns HTTP 413
- DONE criterion: A missing credential on an oversized chat body returns HTTP 401

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

Chat currently accepts an empty message list, a role outside system/user/assistant, temperature below 0, negative max_tokens, and a body far larger than a completion needs. Auth already returns 401 before body validation. The safer order for an oversized body with no credential is 401 without reading the body: the check is header-only, so it does not buffer the payload, and it does not reveal the size cap. A valid credential then gets 413 when Content-Length or a chunked body exceeds the cap, and only then does field validation run. Omitted temperature must still be passed to providers as 1.0. Gemini sampling code stays untouched.
