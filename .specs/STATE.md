# Project State & Decisions

## Active Feature
- Feature: llm-router-gateway
- Phase: Elicit
- Branch: cursor/spec-guardrails-elicit-brief-e287

## Next Step (single item)
- [ ] Owner reviews `.specs/features/llm-router-gateway/brief.md` (canonical gate copy: `.specs/project/feature-briefs/llm-router-gateway/requirements-brief.md`), then `/specify`

## Blockers
- none

## Deferred Ideas
- Streaming completions (D-009 — out of scope for v1)
- Edge authentication / API keys for callers (D-002)
- Semantic cache, rate limiting, multi-tenancy, RAG/tool-use

## Decisions

### AD-001: Kickoff source of truth
- **Date**: 2026-09-10
- **Context**: First elicitation pass on a greenfield repo
- **Decision**: `prd.md` is the product kickoff of record; the requirements brief complements it and does not replace it
- **Consequences**: `/specify` derives REQs from the brief + PRD; do not re-ask D-001–D-012
