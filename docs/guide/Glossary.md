# Glossary

| Term | Meaning |
| --- | --- |
| **Facade** | Public HTTP contract (`POST /v1/chat/completions`) that looks like OpenAI Chat Completions |
| **Cache hit** | Redis already has the SHA-256 identity; no upstream call; no quota |
| **Cache miss** | Identity absent; quota consumed; classify + provider call |
| **Simple / complex** | Evaluator classes a prompt; simple → local first; complex → cloud first |
| **One-hop fallback** | One retry on the opposite-tier adapter after retryable primary failure |
| **Retryable** | Timeout or HTTP status ≥ 500 (`ProviderError.is_retryable`) |
| **Quota** | Per-key daily Redis counter; default 5; UTC midnight reset |
| **Degraded** | `/health` 200 when Redis is up but at least one provider is down |
| **Demo key** | Shared `GATEWAY_API_KEY` sent as `X-API-Key` — not production auth |
| **Ship unit** | Docker Compose services `api` + `redis` |
| **Domain spec** | `.specs/domains/llm-router-gateway/spec.md` (REQ-001–REQ-022) |
| **C-008 / C-009** | Significant PRs update README + `docs/guide/` in the same PR |
| **Still open** | Agent-facing deferred backlog in the root README |

**Go deeper:** [concepts](concepts.md) · [Overview](Overview.md)
