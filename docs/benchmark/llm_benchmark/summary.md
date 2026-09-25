# LLM analyst benchmark

Questions: 120 planner, 40 end-to-end, 20 frozen research cases, 17 in the marketing subset.
Fairness: temperature 0, at most 10 analytical calls, results cut at 6000 characters, retry policy analytics_agent.webapp.llm._request (identical for both).

## gemini

- model gemini-3.5-flash-lite; done 120/120 planner, 21/40 end-to-end, 20/20 research
- planner 96.17, end-to-end 92.54, research 83.42, marketing 95.71
- provider failures 0 (rate limits 0)

## groq

- model None; done 0/120 planner, 0/40 end-to-end, 0/20 research
- planner None, end-to-end None, research None, marketing None
- provider failures 0 (rate limits 0)

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
