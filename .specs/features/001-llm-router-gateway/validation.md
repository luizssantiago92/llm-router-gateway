# Validation: 001-llm-router-gateway

- Verifier: independent agent (clean context; did not author the production or test code)
- Verifier-Mode: subagent
- Date: 2026-09-11
- Diff range: origin/main...HEAD (branch cursor/loop-llm-router-gateway-e287)
- Independent pytest: `python3 -m pytest -q` → 38 passed
- Verdict: FAIL

## Coverage

| Requirement | Test evidence | Result |
| --- | --- | --- |
| REQ-001 | tests/test_chat_completions.py:61 | pass |
| REQ-002 | tests/test_chat_completions.py:97 | pass |
| REQ-003 | tests/test_chat_completions.py:117 | pass |
| REQ-004 | tests/test_health.py:55 | pass |
| REQ-005 | tests/test_cache.py:32 | pass |
| REQ-006 | tests/test_chat_completions.py:84 | fail |
| REQ-007 | tests/test_chat_completions.py:63 | pass |
| REQ-008 | tests/test_chat_completions.py:138 | pass |
| REQ-009 | tests/test_evaluator.py:10 | pass |
| REQ-010 | tests/test_routing.py:15 | pass |
| REQ-011 | tests/test_routing.py:30 | pass |
| REQ-012 | tests/test_fallback.py:16 | pass |
| REQ-013 | tests/test_chat_completions.py:137 | pass |
| REQ-014 | tests/test_chat_completions.py:87 | fail |
| REQ-015 | tests/test_harness_imports.py:15 | fail |
| REQ-016 | tests/test_settings.py:22 | pass |
| REQ-017 | tests/test_compose_config.py:9 | pass |
| REQ-018 | tests/eval/test_routing_eval.py:26 | pass |

Coverage notes (verifier judgment; assertive line is the table citation):

- REQ-001: HTTP 200 plus OpenAI-shaped `choices[0].message.content` at tests/test_chat_completions.py:65.
- REQ-002: HTTP 422, `local.calls == 0`, `cloud.calls == 0`, and `redis.data == {}` (no Redis SET).
- REQ-003: HTTP 422 and `local.calls == 0` (simple prompt would have called local if streaming were accepted).
- REQ-004: HTTP 200 `status=ok` at tests/test_health.py:55; HTTP 200 `status=degraded` at tests/test_health.py:68; HTTP 503 at tests/test_health.py:76.
- REQ-005: SHA-256 of canonical `messages`+`max_tokens`+`temperature` only; a model-name field in the payload is killed by tests/test_cache.py:32.
- REQ-006: Hit path asserts `cached is True` and `local.calls == 1`, but never asserts the stored completion body or numeric JSON `latency_ms`. Mutant M10 (empty content on hit) survived.
- REQ-007: Miss returns `cached is False` and writes Redis (`assert redis.data` at tests/test_chat_completions.py:68); TTL 3600 at tests/test_cache.py:46.
- REQ-008: Dual 502 leaves `redis.data == {}`; CacheService refuses 4xx/5xx/timeout writes at tests/test_cache.py:57.
- REQ-009: Word count 151 is complex at tests/test_evaluator.py:10; case-insensitive keyword match at tests/test_evaluator.py:14.
- REQ-010: Simple prompt `local.calls == 1` and `cloud.calls == 0`.
- REQ-011: Keyword-complex prompt `cloud.calls == 1` and `local.calls == 0`.
- REQ-012: Primary 5xx hops once (`cloud.calls == 1` at tests/test_fallback.py:16); primary timeout hops once at tests/test_fallback.py:30; no third attempt at tests/test_fallback.py:42.
- REQ-013: HTTP 502 and no Redis write of the error body.
- REQ-014: Only `"x-latency-ms" in second.headers` (presence). No assertion that JSON `latency_ms` is a number or that `X-Cache` / `X-Latency-Ms` / `X-Provider` match JSON field values. Mutants M11–M13 survived.
- REQ-015: pyproject names FastAPI/httpx/redis/pydantic/pytest-asyncio. Tests inject fakes and never construct `build_default_app()`. Switching `redis.asyncio.Redis` to blocking `redis.Redis` survived (M14).
- REQ-016: `REDIS_URL` / local base URL / cloud key load from the environment; committed `.env.example` values are empty at tests/test_settings.py:60; `load_dotenv` absent at tests/test_settings.py:65.
- REQ-017: Compose defines isolated `api` and `redis` services; Dockerfile runs uvicorn factory at tests/test_compose_config.py:18.
- REQ-018: Golden eval records simple vs complex destinations; cache hit/miss, routing, 5xx/timeout fallback, and health ok/degraded/Redis-down tests exist and passed in the independent pytest run.

## Discrimination Sensor

Isolated scratch: `git worktree add /tmp/verify-001-sensor HEAD`. Mutants applied one at a time with `__pycache__` cleared and `PYTHONDONTWRITEBYTECODE=1`. Scratch discarded afterward. Working tree besides this report matches the pre-sensor baseline.

| Mutant | Expected killer | Result |
| --- | --- | --- |
| M1 invalid body accepted (`messages` default empty) | tests/test_chat_completions.py:97 | killed |
| M2 `stream:true` accepted (validator no-op) | tests/test_chat_completions.py:117 | killed |
| M3 cache hit skipped (always miss / still call providers) | tests/test_chat_completions.py:84 | killed |
| M4 dual-failure writes error body to Redis | tests/test_chat_completions.py:138 | killed |
| M5 dual failure returns HTTP 200 | tests/test_chat_completions.py:137 | killed |
| M6 Redis-down health returns 200 | tests/test_health.py:76 | killed |
| M7 degraded health returns 503 | tests/test_health.py:67 | killed |
| M8 cache key includes model name | tests/test_cache.py:32 | killed |
| M9 third retry of primary after secondary fails | tests/test_fallback.py:41 | killed |
| M10 cache hit returns empty content instead of stored completion | tests/test_chat_completions.py:84 | survived |
| M11 omit JSON `latency_ms` field | tests/test_chat_completions.py | survived |
| M12 `X-Latency-Ms` header always `0` (mismatch vs JSON) | tests/test_chat_completions.py | survived |
| M13 JSON `latency_ms` is a string, not a number | tests/test_chat_completions.py | survived |
| M14 production factory uses blocking `redis.Redis` | tests/test_harness_imports.py:15 | survived |
| M15 classify always simple (cloud never primary) | tests/test_routing.py:29 | killed |
| M16 skip Redis SET on successful miss | tests/test_chat_completions.py:68 | killed |

## Security Review

- Reviewer: independent agent (clean context)
- Date: 2026-09-11
- Path: full OWASP checklist (HTTP API, user JSON, Redis, env secrets, Compose, outbound Ollama/OpenAI)
- Mutants tested: M1–M16 (validation bypass, cache, 502, health status, SSRF not user-controlled)
- Result: pass

### Injection

- SQL/NoSQL parameterization: pass (N/A for SQL). Redis keys are SHA-256 hex from server-side canonical JSON, not concatenated user strings as commands. No query builder interpolates prompts into Redis protocol beyond `SET`/`GET` of JSON values.
- Shell commands: pass. No `subprocess` / `os.system` in `app/`.
- Template / XSS: pass (N/A). JSON API via `JSONResponse`; no HTML templates.

### Broken Authentication

- Session/token expiry: N/A. Spec assumption D-002: caller authentication is absent in v1 (internal network). No session cookies or caller JWTs.
- Password hashing: N/A. No password store.
- Credentials in URLs/logs/client storage: pass. OpenAI key is sent as `Authorization: Bearer` to OpenAI only (`app/providers/openai.py`). No application `logging` of secrets. Tests use fixture value `sk-test`, not a live key. `.env` is gitignored (`.gitignore:6`); `.env.example` has empty values (`tests/test_settings.py:60`).

### Sensitive Data Exposure

- Secrets in environment, not source: pass. `Settings.from_env()` reads `REDIS_URL`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY` (`tests/test_settings.py:22`). Compose interpolates `${OPENAI_API_KEY}` rather than a literal key (`docker-compose.yml`).
- TLS in transit / encryption at rest: pass with residual. Outbound OpenAI default base is `https://api.openai.com/v1`. Ollama URL is operator env (often HTTP on the compose network). Redis stores prompt completions in plaintext; spec does not require at-rest encryption for the local ship unit.
- PII minimized in logs/responses: pass. No request-body logging in `app/`. 502 body is `{"error": {"message": str(exc), "type": "upstream_error"}}` without API keys. Completions echo model text by design.

### Access Control

- Authorization on protected endpoints: N/A by spec (D-002; out of scope: edge API keys, SSO, OAuth, multi-tenancy). Both `POST /v1/chat/completions` and `GET /health` are unauthenticated. Owner-accepted internal-network risk, not an omitted SHALL.
- IDOR: N/A. No per-user resource IDs; cache key is request-content hash, not a caller id.
- Server-side role checks: N/A. No roles in v1.

### Security Misconfiguration

- Default credentials: pass with residual. No app admin user. Compose Redis image `redis:7-alpine` has no `requirepass` and publishes `6379:6379` to the host (`docker-compose.yml`). Acceptable for the documented local Compose ship unit; not a production-hardening claim (Kubernetes is out of scope).
- Error messages: pass. FastAPI default 422 validation errors; upstream failures map to generic 502 JSON without stack traces. `create_app` does not enable debug.
- CORS: pass. No `CORSMiddleware`; default is not `*` with credentials.

### Vulnerable Components

- Audit: pass with residual. Direct project pins in the verifier environment: fastapi 0.141.1, httpx 0.28.1, redis 7.4.0, pydantic 2.13.5, uvicorn 0.52.4 — no pip-audit hits on those names. Environment-wide pip-audit reported advisories on unrelated system packages (pip, setuptools, jinja2, httplib2, pyjwt) plus transitive urllib3 2.6.3. No lockfile in the repo; residual is to pin/lock before production ship.

### SSRF / External Requests

- URL fetchers validate allowed domains/schemes: pass. User JSON cannot supply a fetch URL. `OLLAMA_BASE_URL` is environment-only; OpenAI `base_url` defaults to `https://api.openai.com/v1` (`app/providers/openai.py`). Message contents are JSON body fields, not request URLs.
- Internal network not reachable from user-controlled URLs: pass. No user-controlled URL fetcher. Outbound trust boundary is operator-configured Ollama plus OpenAI.

Evidence: tests/test_chat_completions.py:97, tests/test_settings.py:22, tests/test_settings.py:65, tests/test_compose_config.py:9.

## AppSec

- Applied: yes (Complex tier; HTTP JSON API; Redis; env secrets; outbound LLM providers)
- Assets: `OPENAI_API_KEY`, Redis-cached prompt/completion text, operator Redis URL
- Actors: unauthenticated internal caller (D-002), operator, Ollama, OpenAI
- Boundaries: caller JSON ↔ FastAPI; FastAPI ↔ Redis; FastAPI ↔ Ollama HTTP; FastAPI ↔ OpenAI HTTPS
- Top risks: (1) unauthenticated internal caller abuse of the facade (accepted by D-002); (2) prompt/completion data at rest in Redis without AUTH on published 6379; (3) operator-controlled `OLLAMA_BASE_URL` aimed at an unintended hop (not user SSRF)
- Focus: authZ N/A (no caller auth) | secrets pass (`tests/test_settings.py:65`) | injection pass (no SQL/shell) | deps residual urllib3 | PII logs pass (no prompt logging in `app/`)
- Result: pass

## QA

- Applied: yes (Complex backend API; regression on routing/cache/health)
- Smoke: `POST /v1/chat/completions` miss → local provider + Redis write (`tests/test_chat_completions.py:61`); repeat payload `cached true` (`tests/test_chat_completions.py:84`); `GET /health` ok (`tests/test_health.py:55`)
- Regression focus: complexity routing (`tests/test_routing.py:15`, `tests/test_routing.py:30`); one-hop fallback (`tests/test_fallback.py:16`); dual 502 (`tests/test_chat_completions.py:137`); health degraded vs Redis-down (`tests/test_health.py:68`, `tests/test_health.py:76`); golden eval destinations (`tests/eval/test_routing_eval.py:26`)
- Pyramid: unit (evaluator, cache key, router); API integration with fakes (chat, health); no live E2E (correct: `pytest -m "not live"`)
- Result: fail — smoke does not assert the cached completion body or observability field/header contract (see Gaps)

## Ship / AI evidence

- Ship Surface deploy unit: Compose `api` + `redis` asserted at tests/test_compose_config.py:9 and tests/test_compose_config.py:10; FastAPI process at tests/test_compose_config.py:18.
- AI Surface eval harness: golden simple vs complex destination counts at tests/eval/test_routing_eval.py:26 and tests/eval/test_routing_eval.py:27 (`assert destinations["local"] == 2`, `assert destinations["cloud"] == 2`). Default suite marker `not live` in `pyproject.toml`.

## Gaps

1. Surviving mutant / Weak assertion — REQ-014. `tests/test_chat_completions.py:87` only checks `"x-latency-ms" in second.headers`. Mutants that omit JSON `latency_ms`, stringify it, or freeze `X-Latency-Ms` at `0` all survived. Spec requires JSON `cached` (boolean), `latency_ms` (number), `provider` (string), and headers `X-Cache` / `X-Latency-Ms` / `X-Provider` whose values match those fields.
2. Surviving mutant / Weak assertion — REQ-006. Cache-hit test never asserts the stored completion body (`choices[0].message.content`). Mutant M10 returned empty content with `cached: true` and still passed.
3. Surviving mutant / Weak assertion — REQ-015. `tests/test_harness_imports.py:15` only greps `pyproject.toml`. Production `build_default_app()` using blocking `redis.Redis` survived because no test constructs the factory or inspects `redis.asyncio` on the request path.

## Interactive UAT

- Applied: skipped — backend-only API, no user-facing UI
- Steps: none
- Result: skipped
