# Targeted regression and the LLM analyst benchmark

Three conclusions, kept apart on purpose: the engine's arithmetic is judged against independent references, the LLMs are judged by a rubric, and neither score is folded into the other.

## C1. The deterministic engine

- Defects tested: 13 (D1, D10, D11, D12, D13, D15, D16, D2, D3, D4, D5, D6-D9, H chart (harness)); fixed: 13; still failing: 0.
- Defect cases: 45 of 45 pass on the fixed code; 45 original failures reproduced on the original code.
- Controls: 33, changed 0 (no regression introduced).
- Suites on the final tree: engine 1996 passed; phases 8-12 55/0/3, 0/0/1, 0/0/1, 26/0/0, 36/0/0 (Olist clauses skip without Postgres); eval 76/76; UI 50; scenario 30/30; stress 4,336 records unchanged
- profile_column, median of four columns: 100,000 rows 0.8944 s -> 0.0711 s (12.58x); 1,000,000 rows 4.7486 s -> 0.1755 s (27.06x); 5,000,000 rows 23.4537 s -> 0.6929 s (33.85x); 10,000,000 rows 45.2674 s -> 1.3003 s (34.81x)
- propose_cleaning_plan at 1M rows: plan_dirty_1000000 23.0109 s -> 14.5126615 s (1.59x); plan_clean_1000000 16.2218295 s -> 7.7559404999999995 s (2.09x)
- Phase H on the fixed code: {"correctness": {"PASS": 20}, "reports": {"PASS": 10}, "ledgers": {"PASS": 10}, "charts": {"PASS": 10}}; calls {"OK": 164}. Concurrency isolation: PASS.
- Phase J on the fixed code: reproducibility PASS.
- Details: docs/benchmark/targeted_regression/summary.md.

## C2. LLM reasoning (Gemini vs Groq)

- Gemini `gemini-3.5-flash-lite`: planner 96.17, end-to-end 92.54, research 83.42, marketing 95.71; valid tool selection 99.17%, invalid calls 5.41%, unsupported claims 1.89%, causal overreach 23.81%; median latency 1.197 s, provider failures 0.
- Groq: not run -- groq: no response (URLError).
- The full table: docs/benchmark/llm_benchmark/comparison.md.

## C3. The complete analyst agent

The architecture -- a model plans, the plan is validated against the contract, the engine computes, the result is checked, the model explains -- was exercised end to end on one provider. The engine held every number it was asked for (C1); the model's contribution is measured separately (C2): its invalid calls were refused by the engine rather than answered wrongly, and every figure in an answer was checked against the engine's own output. A comparison between providers waits on Groq being reachable from the environment.

