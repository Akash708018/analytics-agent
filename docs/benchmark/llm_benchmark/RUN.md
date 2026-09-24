# Running the LLM analyst benchmark (Gemini vs Groq)

Keys are read from the environment or the gitignored `.env` at the repository root
(`GEMINI_API_KEY`, `GROQ_API_KEY`). They are never written to any other file, log or result.
Groq needs `api.groq.com` in the environment's allowed network domains.

Progress is checkpointed per item under `/tmp/llm_benchmark/<provider>/<track>.jsonl`
(override with `LLM_BENCH_DATA`). Re-running a command resumes: finished items are kept, and
items that met a rate limit or a provider error are retried. Nothing is scored until `report`.

```
uv run python scripts/llm_benchmark/run.py setup            # ten 10k-row datasets, cleaned, contracted
uv run python scripts/llm_benchmark/run.py planner gemini   # 120 questions, no tools
uv run python scripts/llm_benchmark/run.py planner groq
uv run python scripts/llm_benchmark/run.py research gemini  # 20 frozen evidence packets
uv run python scripts/llm_benchmark/run.py research groq
uv run python scripts/llm_benchmark/run.py e2e gemini       # 40 questions, real engine calls
uv run python scripts/llm_benchmark/run.py e2e groq
uv run python scripts/llm_benchmark/run.py report           # writes every file in this folder
```

The end-to-end track runs the engine in this checkout, so it should run on the fixed revision
(after `step14-fixes-wip` is merged). The question bank and its gold annotations are
`scripts/llm_benchmark/questions.py` and `research.py`; the rubric is `score_plan`,
`score_e2e` and `score_research` in `run.py`, recomputed from the stored answers on every
report so that one rubric scores both providers.

Free-tier pacing: one request every 13 s to Gemini and every 3 s to Groq (`LLM_PACE_GEMINI`,
`LLM_PACE_GROQ`); the wait is outside every measured latency.
