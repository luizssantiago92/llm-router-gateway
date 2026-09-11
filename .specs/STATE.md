# Project State & Decisions

## Active Feature
- Feature: 001-llm-router-gateway
- Phase: Specify
- Branch: cursor/specify-llm-router-gateway-e287

## Next Step (single item)
- [ ] Owner approves `.specs/features/001-llm-router-gateway/spec.md`, then `/tasks`

## Blockers
- none

## Deferred Ideas
- Streaming completions (D-009 — out of scope for v1)
- Edge authentication / API keys for callers (D-002)
- Semantic cache, rate limiting, multi-tenancy, RAG/tool-use
- vLLM and Anthropic happy-path adapters (protocol only in this design)

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
- **Decision**: Routes call a Provider protocol; Ollama and OpenAI are adapters; unit tests use fakes
- **Consequences**: Tasks must not call vendor SDKs from route modules
