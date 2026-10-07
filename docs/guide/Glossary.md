# Glossary

| Term | Meaning |
| --- | --- |
| **Facade** | Public HTTP contract (`POST /v1/chat/completions`) that looks like OpenAI Chat Completions |
| **Cache hit** | Redis already has the SHA-256 identity; no upstream call; no quota |
| **Cache miss** | Identity absent; quota consumed; classify + provider call |
| **Simple / complex** | Evaluator classes a prompt; simple → local first; complex → cloud first |
| **One-hop fallback** | One retry on the opposite-tier adapter after retryable primary failure |
| **Retryable** | Timeout, HTTP status ≥ 500, or an unexpected provider exception. A non-retryable 4xx is not hopped |
| **Quota** | Per-key daily Redis counter; default 5; UTC midnight reset. Fail-closed when Redis cannot update it |
| **Degraded** | `/health` 200 when Redis is up but at least one provider is down |
| **Live** | `/health/live` 200. The process answered. Dependencies are not probed |
| **Ready** | `/health/ready` 200 when Redis is up and at least one provider is up; otherwise 503 |
| **Demo key** | Shared `GATEWAY_API_KEY` sent as `X-API-Key` — not production auth |
| **Ship unit** | Docker Compose services `api` + `redis` |
| **Domain spec** | Archived requirements in `docs/history/domain-spec.md` (REQ-001–REQ-022) |

**Go deeper:** [concepts](concepts.md) · [Overview](Overview.md)
