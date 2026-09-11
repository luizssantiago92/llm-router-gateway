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
| Gemini free-tier cloud + demo quota | done | Gemini adapter; `X-API-Key` + Redis daily quota; Ollama + cache first line |

## Feature candidates

| Slug | Goal |
| --- | --- |
| 001-llm-router-gateway | archived — v1 facade: cache, complexity routing, one-hop fallback, health |
| gemini-free-demo | cloud = Gemini; `GATEWAY_API_KEY` + `CHAT_DAILY_LIMIT`; keep Ollama + cache |

## Completed

- **2026-09-11** `001-llm-router-gateway` — archived. Validation: `.specs/features/001-llm-router-gateway/validation.md`
  - Merged → `.specs/domains/llm-router-gateway/spec.md` (copied 18 requirement(s) from full spec)
