# Requirements brief: LLM Router Gateway

## Goal

Ship a high-performance FastAPI reverse gateway that intercepts OpenAI-compatible chat-completion traffic, serves exact-match Redis cache hits in under 10 ms, routes cache misses by prompt complexity to a local model or a cloud LLM, and fails over automatically when the primary provider returns 5xx or times out.

## Context sources

- `prd.md` — Product Requirement Document (owner kickoff of record): §§1–6 (vision, business problem, goals, RF-01–RF-04, RNF-01–RNF-04, architecture flow)
- `README.md` — repository title only (`# llm-router-gateway`); no implementation notes
- `.specs/config.yaml` — `extends: python-platform` (Ship Surface + AI Surface apply on later Design/Verify)
- Git history — greenfield repo (`5854535` added the PRD; `eb2f9a6` initial commit)

## Current state

- Greenfield Python service: no application source, tests, Dockerfile, or Compose file yet.
- Product intent is fully described in `prd.md`; this brief complements that kickoff and does not replace it.
- Spec Guardrails installed with the `python-platform` preset; Brakes mode is available.
- Suggested complexity tier: **Complex** (new API surface, infrastructure, non-deterministic AI routing). `/specify` → Discuss → Design → Tasks is the expected path.

## Capabilities

- Expose `POST /v1/chat/completions` as a single facade for internal applications (`prd.md` RF-01).
- Expose `GET /health` that reports API liveness plus Redis and upstream-provider reachability (`prd.md` RF-01).
- Cache exact-match responses in Redis keyed by SHA-256 of the request identity, with a configurable TTL (`prd.md` RF-02).
- On cache hit, return the stored completion with `cached: true` and a reduced `latency_ms` targeting <10 ms (`prd.md` §3, RF-02).
- On cache miss, classify prompt complexity from approximate size plus keywords for code, advanced logic, or structured reasoning (`prd.md` RF-03).
- Route **simple** prompts to a local model instance (vLLM / Ollama; example Llama 3 8B) (`prd.md` RF-03).
- Route **complex** prompts to a cloud provider (OpenAI / Anthropic) (`prd.md` RF-03).
- If the primary provider returns HTTP 5xx or times out, retry once against the secondary provider before failing the request (`prd.md` RF-04).
- Persist successful (non-error) upstream responses in Redis before returning them (`prd.md` §6).
- Surface latency, chosen model/origin, and cache status on every completion response (`prd.md` §3).
- Run fully async (FastAPI + asyncio + httpx + redis-py async) with Pydantic v2 request/response validation (`prd.md` RNF-01, RNF-02).
- Provide `docker-compose.yml` isolating the FastAPI app and Redis (`prd.md` RNF-03).
- Cover routing, cache hit/miss, and fallback with async automated tests (`pytest-asyncio`) (`prd.md` RNF-04).
- Cut paid-API token volume by routing simple/repeated work away from cloud models (business target ≥30%) (`prd.md` §3).

## Interaction details

API-only service — no end-user UI in this pass.

### `POST /v1/chat/completions`

- **Contract:** OpenAI Chat Completions-compatible request body (`messages`, `temperature`, `max_tokens`; additional OpenAI fields may be accepted and ignored if unused).
- **Auth:** none at the gateway edge in v1 (internal-network facade). Upstream cloud credentials and local-runtime URLs come from environment variables, never from git.
- **Happy path (cache miss):** validate → cache lookup miss → classify complexity → call primary provider → on success, write Redis → return completion plus observability fields.
- **Happy path (cache hit):** validate → cache lookup hit → return stored completion with `cached: true` and `latency_ms` for the gateway hop.
- **Fallback:** primary 5xx or timeout → one attempt on the secondary provider → on success, cache and return; on failure, error response (not cached).
- **Client errors:** invalid payload (Pydantic) → HTTP 422; both providers unavailable after fallback → HTTP 502 or 504 as appropriate.
- **Observability:** response JSON includes `cached` (boolean), `latency_ms` (number), and provider/model origin; the same facts are mirrored on response headers (`X-Cache`, `X-Latency-Ms`, `X-Provider`).
- **Idempotency:** GET-like for identical cacheable requests (same messages + sampling params) within TTL; failed upstream calls are not cached.
- **Streaming:** not offered in v1 (`stream` if present is rejected or ignored — see D-009).

### `GET /health`

- Returns structured status for the API process, Redis connectivity, and each configured upstream.
- HTTP 200 when the gateway process is up; payload distinguishes `ok` vs `degraded` when Redis is up but an upstream is unreachable.
- HTTP 503 when Redis is unreachable (cache and write-back cannot operate).

## Constraints & out of scope

- **In scope:** FastAPI async gateway, Redis exact-match cache, complexity router, local + cloud providers with one-hop fallback, health endpoint, Compose (app + Redis), Pydantic v2 schemas, pytest-asyncio coverage for routing/cache/fallback, observability fields/headers.
- **Stack constraint:** Python 3.10+, FastAPI, asyncio, httpx, redis-py async, Pydantic v2 (`prd.md` RNF-01, RNF-02).
- **Ops constraint:** local/dev ship unit is Docker Compose; secrets only via env vars (`prd.md` RNF-03; engineering baseline).
- **AI platform (later Design):** document AI Surface — capability (chat routing), providers, eval harness, PII policy, fallback/degrade, cost guard. Gate will require eval harness + fallback when AI paths appear in tasks.
- **Ship platform (later Design):** document Ship Surface — health/OpenAPI, env/secrets, Compose deploy unit, CI, rollback. Gate will require deploy unit + CI + rollback when Compose/Docker paths appear in tasks.
- **Out of scope (this pass):**
  - Streaming completions (`text/event-stream`)
  - End-user authentication, API keys at the edge, SSO, multi-tenancy
  - Semantic / embedding cache (only exact SHA-256 match)
  - Prompt management UI, playground, or admin console
  - Billing dashboards, per-tenant quotas, rate limiting
  - RAG, tool-use/MCP agents, fine-tuning, embeddings APIs
  - Kubernetes / Helm / Terraform
  - Native Anthropic Messages request schema (Anthropic may still be an upstream adapter behind the OpenAI-shaped facade)
  - Production APM / live LLM tracing platforms

## Resolved questions

### D-001: What request/response schema does the facade speak?

- **Options considered**: A) OpenAI Chat Completions v1 B) Custom internal JSON C) Anthropic Messages as the public contract
- **Decision**: A — OpenAI-compatible `messages` / `temperature` / `max_tokens` on `POST /v1/chat/completions`, plus gateway fields `cached` and `latency_ms`
- **Rationale**: `prd.md` RF-01 calls out a standard payload (messages, temperature, max_tokens) and names the OpenAI-shaped path
- **Date**: 2026-09-10

### D-002: Does the gateway authenticate callers in v1?

- **Options considered**: A) No edge auth (internal network) B) Shared API key header C) OAuth/OIDC
- **Decision**: A — no caller auth in v1; upstream provider keys and local URLs via environment variables only
- **Rationale**: `prd.md` §1 describes an internal facade for internal applications and does not specify identity; adding auth would expand RF-01
- **Date**: 2026-09-10

### D-003: What is hashed for the exact-match cache key?

- **Options considered**: A) Concatenated message contents only B) Messages + `temperature` + `max_tokens` C) Full raw body including routed model name
- **Decision**: B — SHA-256 over a canonical serialization of `messages` + `temperature` + `max_tokens`
- **Rationale**: `prd.md` RF-02 hashes “prompt/messages”; sampling params change the completion so they belong in the key. The gateway chooses the model, so the routed model name is excluded
- **Date**: 2026-09-10

### D-004: What is the default cache TTL?

- **Options considered**: A) 60s B) 3600s C) No expiry
- **Decision**: B — configurable TTL via env (e.g. `CACHE_TTL_SECONDS`), default 3600
- **Rationale**: `prd.md` RF-02 requires a configurable TTL; one hour is a conservative default for repeated internal prompts without unbounded Redis growth
- **Date**: 2026-09-10

### D-005: How is “simple” vs “complex” decided?

- **Options considered**: A) Word/token-size threshold only B) Keyword list only C) Size threshold OR keywords for code / advanced logic / structured reasoning
- **Decision**: C — high complexity if approximate word/token count exceeds a configurable threshold **or** the prompt matches configured keywords (code, algorithms, stepwise reasoning, etc.); otherwise simple
- **Rationale**: `prd.md` RF-03 lists both size and keyword signals; defaults belong in config/env so Design can tune without a schema change
- **Date**: 2026-09-10

### D-006: Which concrete providers ship as defaults?

- **Options considered**: A) Ollama local + OpenAI cloud B) vLLM local + Anthropic cloud C) Pluggable adapters with A as the documented default pair
- **Decision**: C — provider interface with **Ollama (Llama 3 8B class)** as default local and **OpenAI** as default cloud; vLLM and Anthropic are adapter-ready but not required to run the happy path
- **Rationale**: `prd.md` RF-03 names both local options and both cloud vendors as examples; a single default pair keeps Compose and tests deterministic
- **Date**: 2026-09-10

### D-007: What is the fallback pairing?

- **Options considered**: A) Always cloud if anything fails B) Always local if anything fails C) Opposite tier: simple primary=local → fallback=cloud; complex primary=cloud → fallback=local; single retry
- **Decision**: C — one automatic hop to the other tier on HTTP 5xx or timeout; then fail the request
- **Rationale**: `prd.md` RF-04 requires trying the secondary before failing; one hop bounds latency and cost
- **Date**: 2026-09-10

### D-008: Observability — headers, payload, or both?

- **Options considered**: A) Payload fields only B) Headers only C) Both
- **Decision**: C — JSON fields `cached`, `latency_ms`, provider/model origin **and** headers `X-Cache`, `X-Latency-Ms`, `X-Provider`
- **Rationale**: `prd.md` §3 allows header or payload; both keeps clients and mesh proxies equally informed
- **Date**: 2026-09-10

### D-009: Are streaming completions in v1?

- **Options considered**: A) Full SSE streaming B) Buffer then return C) Out of scope
- **Decision**: C — non-streaming JSON only in this pass
- **Rationale**: `prd.md` architecture returns a final response after cache write; streaming would change cache, fallback, and latency semantics
- **Date**: 2026-09-10

### D-010: Are error responses cached?

- **Options considered**: A) Cache everything B) Cache only 2xx completions C) Cache 2xx and 4xx
- **Decision**: B — only successful completions are written to Redis
- **Rationale**: Caching faults would pin outages inside the TTL and fight RF-04 resilience
- **Date**: 2026-09-10

### D-011: Health semantics when an upstream is down?

- **Options considered**: A) 503 if any upstream fails B) 200 with `degraded` when Redis is healthy but an upstream is not C) 200 always if the process is up
- **Decision**: B — 503 only when Redis is down; 200 + `degraded` when the API and Redis are up but a configured provider fails its check
- **Rationale**: `prd.md` RF-01 checks API, Redis, and providers; the gateway can still serve cache hits if only one upstream is down
- **Date**: 2026-09-10

### D-012: Upstream timeout default?

- **Options considered**: A) 10s B) 30s C) Unlimited
- **Decision**: B — per-provider timeout via env, default 30 seconds; timeout triggers RF-04 fallback
- **Rationale**: `prd.md` RF-04 names timeout as a fallback trigger but does not set a value; 30s is a typical LLM HTTP bound
- **Date**: 2026-09-10

## Open questions

- none

## Owner approval

- Approved: yes
- Date: 2026-09-10
- Notes: Brief derived from the owner-authored kickoff `prd.md` (git `5854535`). D-001–D-012 close gaps the PRD left implicit so `/specify` can formalize REQs without re-asking covered topics. Owner may revise decisions before approving `spec.md`.
