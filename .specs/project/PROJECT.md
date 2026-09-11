# PROJECT

## Vision

LLM Router Gateway is the single internal facade for chat-completion traffic. It cuts latency on repeated prompts, steers cheap work to local models, and survives an upstream 5xx or timeout with one automatic failover.

## Stack

- Python 3.10+, FastAPI, asyncio, httpx, Pydantic v2
- Redis (exact-match cache) via redis-py async
- Local default: Ollama when available (optional on light machines); cloud default: Google Gemini (demo / free tier)
- Docker Compose (app + Redis)
- Spec Guardrails with preset `python-platform`

## Constraints

- No secrets in git; upstream keys and local URLs via environment variables
- OpenAI-compatible public contract only (facade); cloud upstream is Gemini for the zero-cost demo
- Demo edge auth: shared `GATEWAY_API_KEY` via `X-API-Key` + daily chat quota (default 5)
- Non-streaming JSON only
- Exact-match cache only (no embeddings); cache hits do not consume quota
- Compose is the ship unit; no Kubernetes/Helm/Terraform in v1
- Paid OpenAI path deferred to a separate product/project

## Domain map

| Domain | Notes |
| --- | --- |
| llm-router-gateway | Domain truth REQ-001–REQ-022 in `.specs/domains/llm-router-gateway/spec.md` (v1 + Gemini demo delta) |
| gateway | HTTP facade, validation, observability headers |
| cache | Redis SHA-256 identity, TTL, hit/miss semantics |
| routing | Complexity evaluator, local vs cloud adapters, fallback |

## Documentation

Human docs: product-facing root `README.md`; technical depth in `docs/` (architecture, API, development). Every PR that changes product or setup updates those files plus this memory (see `docs/development.md` and `.cursor/rules/pr-documentation.mdc`, C-008).
