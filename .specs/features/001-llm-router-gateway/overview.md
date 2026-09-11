# Feature overview: 001-llm-router-gateway

> Generated 2026-09-11T01:21:32.777Z. Refresh with `feature-overview 001-llm-router-gateway --write`.

## Summary

| Field | Value |
| --- | --- |
| Goal | REQ-001 — - **Acceptance Criteria**: WHEN a client sends `POST /v1/chat/completions` with a body that includes `messages`, `temperature`, and `max_tokens` THEN the system SHALL accept the request using an OpenAI Chat Completions-compatible schema and SHALL return a completion JSON object on success |
| Phase | — |
| Branch | — |
| Tasks | 13/13 complete (0 open) |
| Validation | PASS |
| Next | npx @luizsantiago/spec-guardrails archive-feature 001-llm-router-gateway — fold into domain memory |

## Artifacts

| Artifact | Status |
| --- | --- |
| spec | present |
| tasks | present |
| design | present |
| validation | present |
| taskGraph | present |

## Tasks

| Task | Title | Requirement | Status |
| --- | --- | --- | --- |
| T1 | Scaffold async Python project harness | REQ-015, REQ-018 | done |
| T2 | Add environment-backed settings module | REQ-016 | done |
| T3 | Add Pydantic chat request schemas | REQ-001, REQ-002, REQ-003 | done |
| T4 | Add Provider protocol with fakes | REQ-015 | done |
| T5 | Implement Redis exact-match cache | REQ-005, REQ-006, REQ-007, REQ-008 | done |
| T6 | Implement prompt complexity evaluator | REQ-009 | done |
| T7 | Implement Ollama local provider adapter | REQ-010 | done |
| T8 | Implement OpenAI cloud provider adapter | REQ-011 | done |
| T9 | Implement router with one-hop fallback | REQ-010, REQ-011, REQ-012, REQ-013 | done |
| T10 | Add chat completions FastAPI route | REQ-001, REQ-002, REQ-003, REQ-006, REQ-007, REQ-014, REQ-015 | done |
| T13 | Add offline routing eval harness | REQ-018 | done |
| T11 | Add health check FastAPI route | REQ-004 | done |
| T12 | Add Docker Compose ship unit | REQ-017 | done |

## Traceability (REQ → task → evidence)

| REQ | Task(s) | Test evidence |
| --- | --- | --- |
| REQ-001 | T3, T10 | tests/test_chat_completions.py:77 |
| REQ-002 | T3, T10 | tests/test_chat_completions.py:114 |
| REQ-003 | T3, T10 | tests/test_chat_completions.py:134 |
| REQ-004 | T11 | tests/test_health.py:55 |
| REQ-005 | T5 | tests/test_cache.py:32 |
| SHA-256 | — | tests/test_cache.py:32 |
| REQ-006 | T5, T10 | tests/test_chat_completions.py:102 |
| REQ-007 | T5, T10 | tests/test_chat_completions.py:80 |
| REQ-008 | T5 | tests/test_chat_completions.py:155 |
| REQ-009 | T6 | tests/test_evaluator.py:10 |
| REQ-010 | T7, T9 | tests/test_routing.py:15 |
| REQ-011 | T8, T9 | tests/test_routing.py:30 |
| REQ-012 | T9 | tests/test_fallback.py:16 |
| REQ-013 | T9 | tests/test_chat_completions.py:154 |
| REQ-014 | T10 | tests/test_chat_completions.py:51 |
| REQ-015 | T1, T4, T10 | tests/test_harness_imports.py:33 |
| REQ-016 | T2 | tests/test_settings.py:22 |
| REQ-017 | T12 | tests/test_compose_config.py:9 |
| REQ-018 | T1, T13 | tests/eval/test_routing_eval.py:26 |
| RNF-02 | — | — |

## Operational traceability (Ship Surface)

| Field | Value |
| --- | --- |
| API / contract | `POST /v1/chat/completions`, `GET /health` (OpenAPI from FastAPI) |
| Migrations | N/A (no SQL datastore) |
| Env / secrets | `REDIS_URL`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, `UPSTREAM_TIMEOUT_SECONDS` — values from env, never git |
| Deploy unit | Docker Compose services `api` and `redis` |
| CI | `pytest` (asyncio) must pass before merge; optional `docker compose config` in `quality.checks` |
| Rollback | Redeploy previous Compose image tag / git SHA; flush Redis only if a bad cache schema shipped |
| Observability | JSON `cached`, `latency_ms`, `provider`; headers `X-Cache`, `X-Latency-Ms`, `X-Provider`; structured logs without secrets |

_Parsed from `design.md` when present. Does not infer undeclared deploy paths._

## AI traceability (AI Surface)

| Field | Value |
| --- | --- |
| Capability | Chat completion routing (no RAG, no tools) |
| Model / provider | Local default Llama 3 8B class via Ollama; cloud default OpenAI chat model from env `OPENAI_MODEL` |
| Tools / MCP scope | Deny all tools/MCP in v1 |
| Eval harness | `pytest tests/eval/test_routing_eval.py` plus unit routing tests; golden prompts for simple vs complex; `pytest -m "not live"` default |
| PII / data policy | Do not log full prompts in production logs; no prompt corpora committed with PII; secrets never sent in test fixtures |
| Fallback / degrade | On 5xx or timeout, one hop to the opposite-tier provider; if both fail, HTTP 502 and no cache write |
| Cost guard | Prefer local on simple prompts; cache exact repeats; no third retry; execution-policy budgets apply during agent Execute |

_Eval harness and fallback must be documented for AI paths — gate `validate_ship_surface` enforces structure only._

_Evidence rows populate after `validation.md` exists. Structural gaps are caught by `validate-traceability` and `validate-ship-surface`._
