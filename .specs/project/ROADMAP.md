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
| `/verify` | next | Fresh context; this Execute author must not write `validation.md` |
| Compose app + Redis | done | `docker-compose.yml` services `api` + `redis` (RNF-03) |

## Feature candidates

| Slug | Goal |
| --- | --- |
| 001-llm-router-gateway | v1 facade: cache, complexity routing, one-hop fallback, health |
