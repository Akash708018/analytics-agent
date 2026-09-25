# Gemini vs Groq on the analytics engine

The handoff named 'Grok'; the product is configured for Groq (api.groq.com), and the user chose Groq on 24/09/2026. No other model is included.

- Gemini: model `gemini-3.5-flash-lite`, served gemini-3.5-flash-lite; now: available (gemini-3.5-flash-lite)
- Groq: model `None`, served -; now: NOT_RUN_PROVIDER_UNAVAILABLE (groq: no response (URLError))

| Metric | Gemini | Groq |
|---|---:|---:|
| Planner score | 96.17 | not run |
| End-to-end score | 92.54 | not run |
| Intent accuracy | 85.83% | not run |
| Metric accuracy | 93.33% | not run |
| Dimension accuracy | 96.67% | not run |
| Time-period accuracy | 99.17% | not run |
| Valid tool-selection rate | 99.17% | not run |
| Planner step validity | 95.05% | not run |
| Invalid call rate | 5.41% | not run |
| Tool efficiency | 0.9459 | not run |
| Redundant-call rate | 0.0% | not run |
| Premature-stop rate | 4.76% | not run |
| Over-analysis rate | 0.0% | not run |
| Unsupported-claim rate | 1.89% | not run |
| Causal-overreach rate | 23.81% | not run |
| Research reasoning score | 83.42 | not run |
| Marketing subset score | 95.71 | not run |
| Median latency (s) | 1.197 | not run |
| P95 latency (s) | 2.946 | not run |
| Provider/rate-limit failures | 0 | 0 |
| JSON validity (planner) | 100.0% | not run |
| Items done: planner / e2e / research | 120 / 21 / 20 | 0 / 0 / 0 |

No winner is declared on writing style; every row above is a measured rate or a rubric score from scripts/llm_benchmark/run.py. Rate limits and provider errors are counted in their own row, not as reasoning failures.
