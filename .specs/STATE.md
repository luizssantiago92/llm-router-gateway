# Project State & Decisions

## Active Feature
- Feature: gemini-free-demo
- Phase: execute
- Branch: cursor/gemini-free-demo

## Next Step (single item)
- [ ] Land Gemini + demo quota PR; then archive/domain delta as needed

## Blockers
- none

## Deferred Ideas
- Streaming completions (D-009)
- Full multi-tenant auth (beyond shared `GATEWAY_API_KEY`)
- Semantic cache, multi-tenancy UI, RAG/tool-use
- Paid OpenAI happy path (separate product)
- vLLM and Anthropic happy-path adapters

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
- **Decision**: Default cloud adapter is Gemini (`GEMINI_API_KEY`); callers send `X-API-Key` (`GATEWAY_API_KEY`); Redis daily quota (`CHAT_DAILY_LIMIT`, default 5); cache hits do not consume; Ollama + exact-match cache remain first line
- **Consequences**: OpenAI removed from happy path; docs and Compose updated; 401/429 added to API contract
