# Tasks: 001-llm-router-gateway

Vertical slices follow `design.md`: settings and schemas first, then cache/evaluator/adapters in parallel, then router, then HTTP routes, then Compose and eval.

### Phase 1

### T1: Scaffold async Python project harness
- **Requirement**: REQ-015, REQ-018
- **Files**: pyproject.toml, app/__init__.py, tests/conftest.py, tests/test_harness_imports.py
- **Depends on**: —
- **Tests**: tests/test_harness_imports.py
- **Gate**: pytest tests/test_harness_imports.py
- **Done when**: `pyproject.toml` declares FastAPI, httpx, redis, pydantic v2, and pytest-asyncio, and `pytest tests/test_harness_imports.py` imports the `app` package
- [x] complete

### Phase 2

### T2: Add environment-backed settings module
- **Requirement**: REQ-016
- **Files**: app/settings.py, .env.example, tests/test_settings.py
- **Depends on**: T1
- **Tests**: tests/test_settings.py
- **Gate**: pytest tests/test_settings.py
- **Done when**: settings load `REDIS_URL`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, `CACHE_TTL_SECONDS`, `COMPLEXITY_WORD_THRESHOLD`, and `UPSTREAM_TIMEOUT_SECONDS` from the environment, `.env.example` lists keys without values, and tests fail if those keys are read from a committed secrets file
- [x] complete

### T3: Add Pydantic chat request schemas
- **Requirement**: REQ-001, REQ-002, REQ-003
- **Files**: app/schemas/chat.py, app/schemas/__init__.py, tests/test_schemas.py
- **Depends on**: T1
- **Tests**: tests/test_schemas.py
- **Gate**: pytest tests/test_schemas.py
- **Done when**: a valid `messages` + `temperature` + `max_tokens` body parses, invalid bodies raise ValidationError, and `stream=true` is rejected
- [x] complete

### T4: Add Provider protocol with fakes
- **Requirement**: REQ-015
- **Files**: app/providers/base.py, app/providers/fake.py, app/providers/__init__.py, tests/test_provider_protocol.py
- **Depends on**: T1
- **Tests**: tests/test_provider_protocol.py
- **Gate**: pytest tests/test_provider_protocol.py
- **Done when**: `Provider.complete` is an async protocol, the fake adapter returns a completion, and the fake can raise a 5xx-equivalent or timeout error for fallback tests
- [x] complete

### Phase 3

### T5: Implement Redis exact-match cache
- **Requirement**: REQ-005, REQ-006, REQ-007, REQ-008
- **Files**: app/cache/service.py, app/cache/__init__.py, tests/test_cache.py
- **Depends on**: T2
- **Tests**: tests/test_cache.py
- **Gate**: pytest tests/test_cache.py
- **Done when**: the cache key is SHA-256 of canonical `messages`+`temperature`+`max_tokens` (model name excluded), GET returns a stored completion, SET uses `CACHE_TTL_SECONDS` default 3600, and 4xx/5xx/timeout payloads are not written
- [x] complete

### T6: Implement prompt complexity evaluator
- **Requirement**: REQ-009
- **Files**: app/routing/evaluator.py, app/routing/__init__.py, tests/test_evaluator.py
- **Depends on**: T2
- **Tests**: tests/test_evaluator.py
- **Gate**: pytest tests/test_evaluator.py
- **Done when**: word count above `COMPLEXITY_WORD_THRESHOLD` (default 150) or a case-insensitive keyword match (`code`, `algorithm`, `implement`, `debug`, `function`, `class`, `step by step`, `reason`) returns complex, and other prompts return simple
- [x] complete

### T7: Implement Ollama local provider adapter
- **Requirement**: REQ-010
- **Files**: app/providers/ollama.py, tests/test_ollama_adapter.py
- **Depends on**: T2, T4
- **Tests**: tests/test_ollama_adapter.py
- **Gate**: pytest tests/test_ollama_adapter.py
- **Done when**: the adapter sends OpenAI-shaped messages to `OLLAMA_BASE_URL` over async httpx and maps the reply to the shared Completion type (HTTP faked in tests)
- [x] complete

### T8: Implement OpenAI cloud provider adapter
- **Requirement**: REQ-011
- **Files**: app/providers/openai.py, tests/test_openai_adapter.py
- **Depends on**: T2, T4
- **Tests**: tests/test_openai_adapter.py
- **Gate**: pytest tests/test_openai_adapter.py
- **Done when**: the adapter calls OpenAI Chat Completions with `OPENAI_API_KEY` over async httpx and maps the reply to the shared Completion type (HTTP faked in tests)
- [x] complete

### Phase 4

### T9: Implement router with one-hop fallback
- **Requirement**: REQ-010, REQ-011, REQ-012, REQ-013
- **Files**: app/routing/router.py, tests/test_routing.py, tests/test_fallback.py
- **Depends on**: T4, T6
- **Tests**: tests/test_routing.py, tests/test_fallback.py
- **Gate**: pytest tests/test_routing.py tests/test_fallback.py
- **Done when**: simple prompts call the local provider first, complex prompts call the cloud provider first, a primary 5xx or timeout retries the opposite-tier provider once, a second failure returns a 502-equivalent error, and no third attempt is made (providers injected as fakes)
- [x] complete

### Phase 5

### T10: Add chat completions FastAPI route
- **Requirement**: REQ-001, REQ-002, REQ-003, REQ-006, REQ-007, REQ-014, REQ-015
- **Files**: app/main.py, app/api/completions.py, app/api/__init__.py, tests/test_chat_completions.py
- **Depends on**: T3, T5, T7, T8, T9
- **Tests**: tests/test_chat_completions.py
- **Gate**: pytest tests/test_chat_completions.py
- **Done when**: `POST /v1/chat/completions` validates with Pydantic, rejects `stream=true` with HTTP 422, serves Redis hits with `cached=true` and no provider call, writes successful misses, returns JSON `cached`/`latency_ms`/`provider` plus headers `X-Cache`/`X-Latency-Ms`/`X-Provider`, and uses async I/O only
- [x] complete

### T13: Add offline routing eval harness
- **Requirement**: REQ-018
- **Files**: tests/eval/test_routing_eval.py
- **Depends on**: T9
- **Tests**: tests/eval/test_routing_eval.py
- **Gate**: pytest tests/eval/test_routing_eval.py -m "not live"
- **Done when**: a golden prompt set records simple vs complex destination counts without live provider calls
- [x] complete

### Phase 6

### T11: Add health check FastAPI route
- **Requirement**: REQ-004
- **Files**: app/api/health.py, app/main.py, tests/test_health.py
- **Depends on**: T10
- **Tests**: tests/test_health.py
- **Gate**: pytest tests/test_health.py
- **Done when**: `GET /health` returns HTTP 200 `status=ok` when Redis and both upstreams are up, HTTP 200 `status=degraded` when Redis is up and an upstream is down, and HTTP 503 when Redis is down
- [x] complete

### T12: Add Docker Compose ship unit
- **Requirement**: REQ-017
- **Files**: docker-compose.yml, Dockerfile, tests/test_compose_config.py
- **Depends on**: T10
- **Tests**: tests/test_compose_config.py
- **Gate**: pytest tests/test_compose_config.py
- **Done when**: Compose defines isolated `api` and `redis` services and the Dockerfile runs the FastAPI app
- [x] complete

## Test Coverage Matrix

| Requirement | Task | Tests | Notes |
| --- | --- | --- | --- |
| REQ-001 | T3, T10 | tests/test_schemas.py, tests/test_chat_completions.py | OpenAI-shaped body accepted |
| REQ-002 | T3, T10 | tests/test_schemas.py, tests/test_chat_completions.py | HTTP 422, no Redis SET, no provider |
| REQ-003 | T3, T10 | tests/test_schemas.py, tests/test_chat_completions.py | `stream=true` → 422 |
| REQ-004 | T11 | tests/test_health.py | ok / degraded / Redis 503 |
| REQ-005 | T5 | tests/test_cache.py | SHA-256 canonical triple, no model name |
| REQ-006 | T5, T10 | tests/test_cache.py, tests/test_chat_completions.py | Hit skips providers |
| REQ-007 | T5, T10 | tests/test_cache.py, tests/test_chat_completions.py | Miss SET with TTL |
| REQ-008 | T5 | tests/test_cache.py | Errors not written |
| REQ-009 | T6 | tests/test_evaluator.py | Threshold or keywords |
| REQ-010 | T7, T9 | tests/test_ollama_adapter.py, tests/test_routing.py | Local primary for simple |
| REQ-011 | T8, T9 | tests/test_openai_adapter.py, tests/test_routing.py | Cloud primary for complex |
| REQ-012 | T9 | tests/test_fallback.py | One hop on 5xx or timeout |
| REQ-013 | T9 | tests/test_fallback.py | Dual failure → 502, no cache |
| REQ-014 | T10 | tests/test_chat_completions.py | JSON fields + headers |
| REQ-015 | T1, T4, T10 | tests/test_harness_imports.py, tests/test_provider_protocol.py, tests/test_chat_completions.py | Async FastAPI/httpx/redis |
| REQ-016 | T2 | tests/test_settings.py | Env only, no git secrets |
| REQ-017 | T12 | tests/test_compose_config.py | api + redis services |
| REQ-018 | T1, T13 | tests/test_harness_imports.py, tests/eval/test_routing_eval.py | Suite + golden routing eval |

## Gate Check Commands

| Level | Command |
| --- | --- |
| Task | the per-task `Gate` field |
| Feature | pytest -m "not live" |
| Ship | docker compose -f docker-compose.yml config |
