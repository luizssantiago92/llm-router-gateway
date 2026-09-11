# Documentation

Human-facing project docs. Spec artifacts (requirements, tasks, validation) live under [`.specs/`](../.specs/STATE.md). Product kickoff is [`prd.md`](../prd.md).

| Page | Audience | Contents |
| --- | --- | --- |
| [Architecture](architecture.md) | Engineers | Request path, cache, router, fallback, Compose |
| [API](api.md) | Integrators | `POST /v1/chat/completions`, `GET /health`, headers, errors |
| [Development](development.md) | Contributors | Spec workflow, stack, documentation-on-every-PR policy |

## Spec memory (not duplicated here)

| Path | Role |
| --- | --- |
| [`.specs/project/PROJECT.md`](../.specs/project/PROJECT.md) | Vision, stack, constraints |
| [`.specs/project/ROADMAP.md`](../.specs/project/ROADMAP.md) | Milestones |
| [`.specs/project/CONSTITUTION.md`](../.specs/project/CONSTITUTION.md) | Standing principles |
| [`.specs/features/llm-router-gateway/brief.md`](../.specs/features/llm-router-gateway/brief.md) | Elicited requirements brief |
| [`.specs/features/001-llm-router-gateway/spec.md`](../.specs/features/001-llm-router-gateway/spec.md) | Testable REQs (v1) |
| [`.specs/features/001-llm-router-gateway/design.md`](../.specs/features/001-llm-router-gateway/design.md) | Components, Ship Surface, AI Surface |
| [`.specs/features/001-llm-router-gateway/tasks.md`](../.specs/features/001-llm-router-gateway/tasks.md) | T1–T13 Execute breakdown |

When a pull request changes behavior, setup, or status, update the matching page **and** the root [README](../README.md). Policy: [Development → Documentation on every PR](development.md#documentation-on-every-pr).
