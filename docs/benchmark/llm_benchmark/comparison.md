# Gemini vs Groq on the analytics engine

The handoff named 'Grok'; the product is configured for Groq (api.groq.com), and the user chose Groq on 24/09/2026. No other model is included.

- Gemini: model `gemini-3.5-flash-lite`, served gemini-3.5-flash-lite; now: available (gemini-3.5-flash-lite)
- Groq: model `None`, served -; now: NOT_RUN_PROVIDER_UNAVAILABLE (groq: no response (URLError))

| Metric | Gemini | Groq |
|---|---:|---:|
| Planner score | 96.17 | not run |
| End-to-end score | not run | not run |
| Intent accuracy | 85.83% | not run |
| Metric accuracy | 93.33% | not run |
| Dimension accuracy | 96.67% | not run |
| Time-period accuracy | 99.17% | not run |
| Valid tool-selection rate | 99.17% | not run |
| Planner step validity | 95.05% | not run |
| Invalid call rate | not run | not run |
| Tool efficiency | not run | not run |
| Redundant-call rate | not run | not run |
| Premature-stop rate | not run | not run |
| Over-analysis rate | not run | not run |
| Unsupported-claim rate | not run | not run |
| Causal-overreach rate | not run | not run |
| Research reasoning score | 83.42 | not run |
| Marketing subset score | 95.88 | not run |
| Median latency (s) | 1.284 | not run |
| P95 latency (s) | 3.629 | not run |
| Provider/rate-limit failures | 0 | 0 |
| JSON validity (planner) | 100.0% | not run |
| Items done: planner / e2e / research | 120 / 0 / 20 | 0 / 0 / 0 |

No winner is declared on writing style; every row above is a measured rate or a rubric score from scripts/llm_benchmark/run.py. Rate limits and provider errors are counted in their own row, not as reasoning failures.
