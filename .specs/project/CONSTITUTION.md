# Project Constitution

Governing principles for LLM Router Gateway. Feature-local decisions stay in the brief / `context.md` / `design.md`.

## Principles

### C-001: Spec before code
- Medium+ work MUST have an approved `spec.md` (and, for this Complex feature, an approved requirements brief) before production implementation.

### C-002: Evidence over narrative
- A feature is done only when `/verify` cites tests at `file:line` for each REQ. Do not weaken, skip, or delete tests to pass a gate.

### C-003: Async and strict I/O
- Gateway I/O MUST be async (FastAPI + asyncio + httpx + redis-py async). Request and response bodies MUST validate with Pydantic v2.

### C-004: Cache successes, not failures
- Only successful completions MAY be written to Redis. HTTP 5xx, timeouts, and 4xx MUST NOT be cached.

### C-005: One-hop resilience
- Primary provider 5xx or timeout MUST attempt the secondary provider once, then fail. No unbounded retries.

### C-006: Secrets stay out of git
- API keys, tokens, and runtime URLs MUST come from the environment. PRs MUST NOT add `.env` files with values.

### C-007: Observable origin
- Every completion response MUST expose cache status, gateway latency, and provider origin on JSON **and** headers.

### C-008: Documentation travels with the change
- Every pull request that changes product, setup, or status MUST update `README.md` and the matching `docs/` pages (see `docs/development.md`).

### C-009: Significant PRs ship README and guide docs together
- Extends C-008. Every pull request that changes product behavior, API, setup, architecture, or public status MUST update root `README.md` **in that same PR** (not a follow-up) and the matching pages under `docs/guide/`. Skip README only for purely internal diffs with no stale operator-facing text. Procedure: `CONTRIBUTING.md` and `docs/guide/Development.md`.

## Non-Negotiables

- No secrets in git
- No skipping structural Spec Guardrails gates
- Artifact language is English (code, tests, docs, `.specs/`, commits, PR bodies)

## Amendment

Supersede with a new C-NNN entry that references the old one — never edit history in place.
