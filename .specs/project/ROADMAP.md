# ROADMAP

| Milestone | Status | Notes |
| --- | --- | --- |
| Install Spec Guardrails (`python-platform`) | done | Doctor Process 100 / Brakes 100 |
| `/elicit` from `prd.md` | done | `.specs/features/llm-router-gateway/brief.md` |
| Project docs + README | done | Policy: update on every later PR (C-008) |
| `/specify` (`spec.md`) | done | `.specs/features/001-llm-router-gateway/spec.md` (awaiting owner approval) |
| Discuss + Design | done | `context.md` (D-001–D-012) + `design.md` (Ship + AI surfaces) |
| Tasks → Execute → Verify | planned | pytest-asyncio: routing, cache, fallback |
| Compose app + Redis | planned | RNF-03 |

## Feature candidates

| Slug | Goal |
| --- | --- |
| 001-llm-router-gateway | v1 facade: cache, complexity routing, one-hop fallback, health |
