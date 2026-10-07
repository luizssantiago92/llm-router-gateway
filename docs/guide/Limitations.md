# Limitations

This demo is documented like a product. That does **not** make it the company chatbot.

These limits stay in force:

- Gemini free-tier rate limits still apply
- a shared `X-API-Key` is not multi-tenant auth
- a green `pytest` run is not proof of production quality

| Item | Status | Notes |
| --- | --- | --- |
| Streaming (`stream: true`) | **deferred** | Rejected with 422 today (D-009) |
| Production edge auth | **deferred** | Only shared `GATEWAY_API_KEY` / `X-API-Key` |
| Multi-tenancy / per-tenant quotas | **deferred** | Single demo key + daily Redis bucket (UTC midnight) |
| Semantic / embedding cache | **deferred** | Exact-match SHA-256 only |
| Rate limits beyond daily quota | **deferred** | — |
| RAG / tools / function calling | **deferred** | — |
| Paid OpenAI (or other paid cloud) happy path | **deferred** | Separate product / company chatbot later |
| vLLM / Anthropic adapters (happy path) | **deferred** | Protocol-ready ideas only |
| Kubernetes / Helm / Terraform | **deferred** | Compose is the ship unit |
| Hosted deploy (Render, etc.) | **not started** | Optional for demos; Gold Queen already has deploy patterns |
| First-class Ollama in Compose | **not started** | Ollama stays external; optional on stronger machines |
| UI / chat frontend | **not started** | API-only demo |

Compose publishes the API and Redis on `127.0.0.1` only and requires `REDIS_PASSWORD`. The API image runs as a non-root user. That is local hardening for this demo, not a production network or identity review.

> A green `pytest` run means the suite passed — it is not proof this demo is a production chatbot.

**Owner roadmap (outside this repo):** (1) reuse interesting bits in [Gold Queen](https://github.com/luizssantiago92/gold-queen-api) → (2) later build a real company chatbot on paid/controlled infra → (3) keep **this** repository as the academic / zero-cost demonstrative reference.

Back: [Overview](Overview.md) · [Home](Home.md)
