# Documentation

Product overview, demo status, and the explicit backlog live in the root [README](../README.md) (**Still open (agents: read this)**). This folder holds technical depth.

| Page | Audience | Contents |
| --- | --- | --- |
| [Architecture](architecture.md) | Engineers | Request path, cache, router, fallback, Compose |
| [API](api.md) | Integrators | `POST /v1/chat/completions`, `GET /health`, headers, errors, quota |
| [Development](development.md) | Contributors | Stack, env, pytest, Compose, Spec Guardrails, C-008 |

**Go deeper**

- Product kickoff: [`prd.md`](../prd.md)
- Project memory: [`.specs/project/PROJECT.md`](../.specs/project/PROJECT.md) · [`ROADMAP.md`](../.specs/project/ROADMAP.md)
- Domain truth (REQ-001–REQ-022): [`.specs/domains/llm-router-gateway/spec.md`](../.specs/domains/llm-router-gateway/spec.md)
- Feature history: [`.specs/features/001-llm-router-gateway/`](../.specs/features/001-llm-router-gateway/spec.md)
- Session state: [`.specs/STATE.md`](../.specs/STATE.md)

When a pull request changes behavior, setup, or status, update the matching page **and** the root README (including the Still open table if scope changes). Policy: [Documentation on every PR](development.md#documentation-on-every-pr).
