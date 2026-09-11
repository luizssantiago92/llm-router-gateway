# Task Graph: 001-llm-router-gateway

DAG for Execute. Parallel groups share a letter; workers in the same group MUST have disjoint `Files`. Verify is a separate context after T12.

| Node | Depends on | Parallel group | Owner |
| --- | --- | --- | --- |
| T1 Scaffold async Python project harness | — | — | sequential |
| T2 Add environment-backed settings module | T1 | A | worker |
| T3 Add Pydantic chat request schemas | T1 | A | worker |
| T4 Add Provider protocol with fakes | T1 | A | worker |
| T5 Implement Redis exact-match cache | T2 | B | worker |
| T6 Implement prompt complexity evaluator | T2 | B | worker |
| T7 Implement Ollama local provider adapter | T2, T4 | B | worker |
| T8 Implement OpenAI cloud provider adapter | T2, T4 | B | worker |
| T9 Implement router with one-hop fallback | T4, T6 | — | sequential |
| T10 Add chat completions FastAPI route | T3, T5, T7, T8, T9 | C | worker |
| T13 Add offline routing eval harness | T9 | C | worker |
| T11 Add health check FastAPI route | T10 | D | worker |
| T12 Add Docker Compose ship unit | T10 | D | worker |
| Verify | T11, T12, T13 | — | verifier (clean context) |

```text
T1
 ├─ T2 ─┬─ T5 ─┐
 ├─ T3 ─┤      │
 └─ T4 ─┼─ T7 ─┼─ T9 ─┬─ T10 ─┬─ T11
        └─ T8 ─┘      │       └─ T12
        T6 ───────────┘       T13 (from T9, parallel with T10)
```

## Parallel groups

| Group | Tasks | Why it is safe |
| --- | --- | --- |
| A | T2, T3, T4 | After T1; disjoint files (`settings`, `schemas`, `providers/base`) |
| B | T5, T6, T7, T8 | After T2/T4; disjoint files (`cache`, `evaluator`, `ollama`, `openai`) |
| C | T10, T13 | After T9; route vs `tests/eval/` |
| D | T11, T12 | After T10; `health.py`+`main.py` vs Compose/Dockerfile. T11 depends on T10 so `app/main.py` overlap with T10 is sequential, not parallel |

## Stop rule

T9 reads evaluator + Provider protocol results, so it stays sequential after group B. T11 registers routes on `app/main.py` created by T10, so it cannot join group C.
