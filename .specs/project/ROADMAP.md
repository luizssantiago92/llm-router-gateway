# ROADMAP

| Milestone | Status | Notes |
| --- | --- | --- |
| Install Spec Guardrails (`python-platform`) | done | Doctor Process 100 / Brakes 100 |
| `/elicit` from `prd.md` | done | `.specs/features/llm-router-gateway/brief.md` |
| Project docs + README | done | Policy: update on every later PR (C-008) |
| `/specify` (`spec.md`) | done | `.specs/features/001-llm-router-gateway/spec.md` |
| Discuss + Design | done | `context.md` (D-001–D-012) + `design.md` (Ship + AI surfaces) |
| `/tasks` | done | T1–T13 + `task-graph.md` |
| Execute (`/loop`) | done | T1–T13; `app/` + Compose + pytest-asyncio |
| `/verify` | done | PASS after fix round 1; `.specs/features/001-llm-router-gateway/validation.md` |
| `/archive` | done | Domain truth: `.specs/domains/llm-router-gateway/spec.md` |
| Compose app + Redis | done | `docker-compose.yml` services `api` + `redis` (RNF-03) |
| Product README + docs index | done | Root README product-style; depth in `docs/` (C-008) |
| Gemini free-tier cloud + demo quota | done | Gemini adapter; `X-API-Key` + Redis daily quota; Ollama optional |
| Domain delta REQ-019–REQ-022 | done | Gemini default, demo API key, daily quota, Ollama optional |
| Demo smoke (Compose + Gemini chat) | done | Health `degraded` without Ollama; chat `provider=cloud` |
| README backlog for agents | done | **Still open** table + AD-006 demonstrative scope |
| Operator README sync | done | Quick start matches Gemini/quota/auth; Linux `host.docker.internal` |
| README accuracy pass | done | Compose interpolates tunables from `.env`; license/env/502 wording matches code |

## Feature candidates

| Slug | Goal |
| --- | --- |
| 001-llm-router-gateway | archived — v1 facade: cache, complexity routing, one-hop fallback, health |
| gemini-free-demo | done — merged #8; domain REQ-019–REQ-022 |

Deferred candidates (do not start without owner `feature-init`): streaming, production auth, semantic cache, RAG/tools, paid OpenAI path, K8s, hosted deploy, chat UI — see root README **Still open**.

## Completed

- **2026-09-11** `001-llm-router-gateway` — archived. Validation: `.specs/features/001-llm-router-gateway/validation.md`
  - Merged → `.specs/domains/llm-router-gateway/spec.md` (copied 18 requirement(s) from full spec)
- **2026-09-11** `gemini-free-demo` — merged #8; domain updated with REQ-019–REQ-022
- **2026-09-11** Local Compose smoke — Gemini chat OK; Docker Desktop + WSL2 required on Windows
- **2026-09-12** Operator README — env, auth, quota, `/docs`, and optional Ollama notes aligned with the shipped demo
- **2026-09-12** README accuracy pass — Compose interpolates tunables from `.env`; license and 502 wording match code
