# Project State & Decisions

## Active Feature
- Feature: —
- Phase: —
- Branch: —

## Next Step (single item)
- [ ] No active feature — demo shipped. Next work only via `feature-init`, or reuse patterns in Gold Queen / a future company chatbot (see README **Still open**)

## Blockers
- none

## Deferred Ideas
- Streaming completions (D-009)
- Full multi-tenant auth (beyond shared `GATEWAY_API_KEY`)
- Semantic cache, multi-tenancy UI, RAG/tool-use
- Paid OpenAI happy path (separate product / real company chatbot)
- vLLM and Anthropic happy-path adapters
- Hosted deploy; Ollama in Compose; chat UI
- Authoritative list: root `README.md` → **Still open (agents: read this)**

## Decisions

### AD-001: Kickoff source of truth
- **Date**: 2026-09-10
- **Context**: First elicitation pass on a greenfield repo
- **Decision**: `prd.md` is the product kickoff of record; the requirements brief complements it and does not replace it
- **Consequences**: `/specify` derives REQs from the brief + PRD; do not re-ask D-001–D-012

### AD-002: Documentation on every PR
- **Date**: 2026-09-10
- **Context**: Owner asked that each PR update the README and keep project documentation current
- **Decision**: Standing policy C-008 — README + `docs/` + PROJECT/ROADMAP travel with every product/setup/status change
- **Consequences**: Agents follow `.cursor/rules/pr-documentation.mdc`; skip README only for purely internal diffs with no stale public status

### AD-003: In-process Provider protocol
- **Date**: 2026-09-11
- **Context**: Design for 001-llm-router-gateway
- **Decision**: Routes call a Provider protocol; adapters implement the same seam; unit tests use fakes
- **Consequences**: Tasks must not call vendor SDKs from route modules

### AD-004: Zero-cost demo cloud = Gemini + quota
- **Date**: 2026-09-11
- **Context**: Owner wants a Gold-Queen-style zero-cost demo; paid OpenAI path deferred to another project
- **Decision**: Default cloud adapter is Gemini (`GEMINI_API_KEY`); callers send `X-API-Key` (`GATEWAY_API_KEY`); Redis daily quota (`CHAT_DAILY_LIMIT`, default 5); cache hits do not consume; Ollama is optional (fallback to Gemini when local is down)
- **Consequences**: OpenAI removed from happy path; domain REQ-019–REQ-022; docs and Compose updated; 401/429 on the API contract

### AD-005: Default Gemini model id
- **Date**: 2026-09-11
- **Context**: `gemini-2.0-flash` shut down; Google migration points to 3.x Flash
- **Decision**: Default `GEMINI_MODEL` is `gemini-3.5-flash`; operators may override to `gemini-3.6-flash` via env when listed in AI Studio
- **Consequences**: Compose and settings defaults updated; `.env` may override without code change

### AD-006: This repo stays demonstrative
- **Date**: 2026-09-11
- **Context**: Owner will reuse interesting pieces in Gold Queen and later build a real company chatbot elsewhere
- **Decision**: Keep llm-router-gateway as the academic / zero-cost demo reference; do not grow production chatbot scope here without explicit `feature-init`
- **Consequences**: README **Still open** is the agent-facing backlog; production work belongs in other repos unless the owner says otherwise

### AD-007: Spec Guardrails-style guide + README in the same PR
- **Date**: 2026-09-12
- **Context**: Owner asked for README structure and a `docs/guide/` tree like Spec Guardrails, plus README updates on every significant PR
- **Decision**: Human docs live under `docs/guide/` (Overview, Quick-start, How-it-works, Architecture, API, Development, concepts, FAQ, Glossary, Limitations). Root README is the product entry. C-009: significant product/API/setup/architecture/status PRs update README + matching guide pages **in that same PR**
- **Consequences**: Agents follow `.cursor/rules/pr-documentation.mdc` and `CONTRIBUTING.md`; old `docs/architecture.md` / `api.md` / `development.md` are redirects

### AD-008: Operator README uses a numbered run path
- **Date**: 2026-09-14
- **Context**: Owner asked for a professional operator-facing README: jump links, numbered setup, first-success checks, and a repo map
- **Decision**: Root README uses TOC, numbered Prepare / Run / Verify, first-access checks, checklist, command cheat sheet, and an Explore table. Depth stays in `docs/guide/`
- **Consequences**: C-009 still applies; Quick-start.md mirrors the numbered path without duplicating OS installers
