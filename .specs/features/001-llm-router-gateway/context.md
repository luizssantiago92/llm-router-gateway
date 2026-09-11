# Context: 001-llm-router-gateway

Discuss ran inside Specify. Product gray areas were closed in `/elicit` (brief D-001–D-012) and folded into `spec.md` acceptance criteria. This file records those decisions so Specify does not re-ask them.

## D-001: What request/response schema does the facade speak?
- **Options considered**: A) OpenAI Chat Completions v1 B) Custom internal JSON C) Anthropic Messages as the public contract
- **Decision**: A
- **Rationale**: `prd.md` RF-01 names messages, temperature, max_tokens and the OpenAI-shaped path
- **Consequences**: REQ-001, REQ-002, REQ-003
- **Date**: 2026-09-10

## D-002: Does the gateway authenticate callers in v1?
- **Options considered**: A) No edge auth B) Shared API key header C) OAuth/OIDC
- **Decision**: A
- **Rationale**: Internal facade; identity was not in the PRD
- **Consequences**: REQ-016; Out of Scope edge auth
- **Date**: 2026-09-10

## D-003: What is hashed for the exact-match cache key?
- **Options considered**: A) Message contents only B) Messages + temperature + max_tokens C) Full body including routed model
- **Decision**: B
- **Rationale**: Sampling params change the completion; the gateway chooses the model
- **Consequences**: REQ-005
- **Date**: 2026-09-10

## D-004: What is the default cache TTL?
- **Options considered**: A) 60s B) 3600s C) No expiry
- **Decision**: B — `CACHE_TTL_SECONDS` default 3600
- **Rationale**: Configurable TTL required by RF-02
- **Consequences**: REQ-007
- **Date**: 2026-09-10

## D-005: How is simple vs complex decided?
- **Options considered**: A) Size only B) Keywords only C) Size threshold OR keywords
- **Decision**: C — word count > 150 or keyword match
- **Rationale**: RF-03 lists both signals
- **Consequences**: REQ-009, REQ-010, REQ-011
- **Date**: 2026-09-10

## D-006: Which concrete providers ship as defaults?
- **Options considered**: A) Ollama + OpenAI only B) vLLM + Anthropic only C) Pluggable adapters with A as the default pair
- **Decision**: C
- **Rationale**: Deterministic Compose and tests; other vendors stay adapter-ready
- **Consequences**: REQ-010, REQ-011
- **Date**: 2026-09-10

## D-007: What is the fallback pairing?
- **Options considered**: A) Always cloud B) Always local C) Opposite tier, one hop
- **Decision**: C
- **Rationale**: RF-04; one hop bounds latency and cost
- **Consequences**: REQ-012, REQ-013
- **Date**: 2026-09-10

## D-008: Observability — headers, payload, or both?
- **Options considered**: A) Payload B) Headers C) Both
- **Decision**: C
- **Rationale**: PRD §3 allows either; both serves clients and proxies
- **Consequences**: REQ-014
- **Date**: 2026-09-10

## D-009: Are streaming completions in v1?
- **Options considered**: A) SSE B) Buffer then return C) Out of scope
- **Decision**: C — reject `stream: true` with 422
- **Rationale**: Streaming changes cache and fallback semantics
- **Consequences**: REQ-003
- **Date**: 2026-09-10

## D-010: Are error responses cached?
- **Options considered**: A) Cache everything B) Cache only successful completions C) Cache 2xx and 4xx
- **Decision**: B
- **Rationale**: Caching faults would pin outages inside the TTL
- **Consequences**: REQ-008, REQ-013
- **Date**: 2026-09-10

## D-011: Health semantics when an upstream is down?
- **Options considered**: A) 503 if any upstream fails B) 200 degraded when Redis is up C) 200 always if the process is up
- **Decision**: B — 503 only when Redis is down
- **Rationale**: Cache hits can still be served
- **Consequences**: REQ-004
- **Date**: 2026-09-10

## D-012: Upstream timeout default?
- **Options considered**: A) 10s B) 30s C) Unlimited
- **Decision**: B — `UPSTREAM_TIMEOUT_SECONDS` default 30
- **Rationale**: Timeout is an RF-04 fallback trigger
- **Consequences**: REQ-012
- **Date**: 2026-09-10
