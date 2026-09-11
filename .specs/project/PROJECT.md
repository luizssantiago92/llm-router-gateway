# PROJECT

## Vision

LLM Router Gateway is a **demonstrative** internal facade for chat-completion traffic: exact-match cache, complexity routing, one-hop failover, and a Gemini free-tier demo with daily quota. It is an academic / lab reference — not the production company chatbot. Useful patterns may be reused in Gold Queen; a real paid chatbot is a separate product later.

## Stack

- Python 3.10+, FastAPI, asyncio, httpx, Pydantic v2
- Redis (exact-match cache) via redis-py async
- Local: Ollama when available (optional); cloud: Google Gemini (demo / free tier)
- Docker Compose (app + Redis)
- Spec Guardrails with preset `python-platform`

## Constraints

- No secrets in git; upstream keys and local URLs via environment variables
- OpenAI-compatible public contract (facade); cloud upstream is Gemini for this demo
- Demo edge auth: shared `GATEWAY_API_KEY` via `X-API-Key` + daily chat quota (default 5)
- Non-streaming JSON only
- Exact-match cache only (no embeddings); cache hits do not consume quota
- Compose is the ship unit; no Kubernetes/Helm/Terraform in this demo
- Paid OpenAI / production multi-tenant chatbot deferred (see README **Still open**)

## Domain map

| Domain | Notes |
| --- | --- |
| llm-router-gateway | Domain truth REQ-001–REQ-022 in `.specs/domains/llm-router-gateway/spec.md` (v1 + Gemini demo delta) |
| gateway | HTTP facade, validation, observability headers, demo API key |
| cache | Redis SHA-256 identity, TTL, hit/miss semantics |
| routing | Complexity evaluator, local vs cloud adapters, fallback |
| quota | Daily Redis bucket per caller key |

## Documentation

Human docs: product-facing root `README.md` (includes agent backlog); technical depth in `docs/`. Every PR that changes product or setup updates those files plus this memory (see `docs/development.md` and `.cursor/rules/pr-documentation.mdc`, C-008).
