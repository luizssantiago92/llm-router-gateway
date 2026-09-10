# PROJECT

## Vision

LLM Router Gateway is the single internal facade for chat-completion traffic. It cuts latency on repeated prompts, steers cheap work to local models, and survives an upstream 5xx or timeout with one automatic failover.

## Stack

- Python 3.10+, FastAPI, asyncio, httpx, Pydantic v2 (planned)
- Redis (exact-match cache) via redis-py async
- Local default: Ollama (Llama 3 8B class); cloud default: OpenAI
- Docker Compose (app + Redis)
- Spec Guardrails with preset `python-platform`

## Constraints

- No secrets in git; upstream keys and local URLs via environment variables
- OpenAI-compatible public contract only in v1 (no native Anthropic Messages schema)
- No caller authentication at the gateway edge in v1
- Non-streaming JSON only
- Exact-match cache only (no embeddings)
- Compose is the ship unit; no Kubernetes/Helm/Terraform in v1

## Domain map

| Domain | Notes |
| --- | --- |
| gateway | HTTP facade, validation, observability headers |
| cache | Redis SHA-256 identity, TTL, hit/miss semantics |
| routing | Complexity evaluator, local vs cloud adapters, fallback |

## Documentation

Human docs live in `docs/` and the root `README.md`. Every PR that changes product or setup updates those files (see `docs/development.md` and `.cursor/rules/pr-documentation.mdc`).
