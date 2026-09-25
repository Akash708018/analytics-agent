# analytics-agent

MCP server exposing data loading, profiling, cleaning and contract-gated analysis
to Claude Desktop. Phases 1-13 done, then Cleanup Steps 4-16; Phase 14
(Track B) in progress, Steps 1-14 done; Phase 15 (web cleaning + helper columns) planned, not
started (UI in ui/, on the fake backend or the engine with
ANALYTICS_UI_BACKEND=real;
`uv run --group ui streamlit run ui/app.py`; its 50 tests: `uv run --group ui pytest ui/tests`;
the behaviour matrix: `uv run python scripts/scenario_matrix.py` (30 checks);
the benchmark: `uv run python scripts/benchmark.py` (1,932 ground-truth checks at 1k/100k/1M rows;
its 14 negatives, P14-O13 to O26, closed at Step 12: 12 fixed, 2 by decision;
the cross-domain benchmark: `uv run python scripts/domain_benchmark/run.py` (hours; checkpointed,
data in /tmp/domain_benchmark_data; results docs/benchmark/domain_benchmark/);
the targeted regression of its 16 defects on two revisions: `uv run python
scripts/targeted_regression/run.py cases|hj|report` (needs the original tree as a worktree,
TR_ORIGINAL_SRC); the LLM benchmark: docs/benchmark/llm_benchmark/RUN.md);
the browser walk: `uv run --group ui --with playwright python scripts/browser_check.py`;
the demo: docs/DEMO.md). P14-O1 and P14-O2 closed at Step 5
(idle web workspaces expire; cleaning has a screen). The stress matrix's 14 bugs
(P14-O3 to O12) closed at Step 7; Step 8 fixed what remained and ran three more rounds of
anomalies to a round with no new bug. `docs/stress/REPORT.md`; re-run with
`uv run python scripts/stress_matrix.py --round all` (4 rounds, 95 datasets, 0 crashes; its
load-time "wrong" lines are text the suggested cleaning converts). Open: CL10-O2 (Gemini timeouts,
cause unmeasured), RF-O9 (unit-level values derived from rows), RF-O10 (coinciding blanks not
named) -- from the Cleanup Steps merged in from main on 25/09/2026. The agent's live check:
`uv run python scripts/agent_live.py` (needs keys in the gitignored .env). Otherwise nothing: P9-O4's feature half was closed by the user's
decision on 21/09/2026 (copy-first; in-place analysis is a later scaling item).

## Stack
Python >= 3.12 via `uv` -- run everything through `uv run`, never `pip install`.
DuckDB 1.5.5, FastMCP 3.4.7, psycopg 3, pydantic 2, openpyxl, PyYAML, scipy,
statsmodels, matplotlib 3.11.2 (backend Agg, set before the pyplot import). PostgreSQL 17 (Homebrew) on localhost:5432 serving `olist` and `testdb`.
Layout: `src/analytics_agent/{ingest,profile,clean,contract,validate,analysis,charts,report,util}`;
`server.py` registers MCP tools, `state.py` holds the workflow gate.
27 analyses across 7 tiers. An analysis's shape: `analysis/{registry,base,declared,stats}.py`.

## Verify before committing
All six, every time. Run the suite BEFORE committing, not after (C76: two commits
recorded a broken tree). Engine suite last measured 25/09/2026, after merging main's Cleanup
Steps 8-16 into Phase 14 Step 14; phases 8-10 at Step 4 (21/09) -- they need the Postgres
`olist` source, and without it their Olist clauses skip (55/0/3, 0/0/1, 0/0/1 in a container
lacking it):

    uv run pytest -q                      # 2104 passed
    uv run python tests/test_phase8.py    # 99 passed, 0 failed, 2 skipped
    uv run python tests/test_phase9.py    # 19 passed, 0 failed, 0 skipped
    uv run python tests/test_phase10.py   # 35 passed, 0 failed, 1 skipped
    uv run python tests/test_phase11.py   # 26 passed, 0 failed, 0 skipped
    uv run python tests/test_phase12.py   # 36 passed, 0 failed, 0 skipped

The eval harness is the seventh thing to run and the only one that answers
with a figure rather than pass/fail -- it exits zero on a wrong answer,
because a suite that must be 100% cannot carry a score (P13-D1):

    uv run python eval/run_eval.py        # SCORE: 76/76 (100%), 40 questions

The acceptance scripts are scripts, not pytest files -- `pytest` collects nothing
from them, so 2104 excludes them. The three skips are each deliberate and
recorded: ANALYSIS_RESULT_UNSOUND and the rendered MCP schema in phase8, the
non-finite screen in phase10. A skip is an outstanding clause, not a passing one
-- count them against this line, which is how C80 was found.

## Conventions
These are not stylistic. Each came from something going wrong.

- **Measure before you build.** Every phase opens with a ground-facts test file that
  pins what the libraries actually do, run before any code depends on it. See
  `tests/test_{stats,selector,cohort,duckdb_temporal}_facts.py`. Several Phase 10
  decisions exist only because a prediction was wrong.
- **State the expected output before running a command.** An expectation you have
  committed to is what turns a run into a measurement. When output differs, that is
  the result, not an obstacle: say the prediction was wrong, say what the real
  behaviour is, then decide. Never adjust the expectation after the fact.
- **No claim recorded as verified without its output.** A digest, a row count, a
  suite total -- if it is in `decisions.md`, a command printed it.
- **Files written by heredoc are confirmed by digest, not by tests they pass.** Run
  `shasum -a 256` and `wc -l` immediately after writing and record both.
- **Guard every edit.** A patch script asserts its target exists and matches exactly
  once before writing. An unguarded `.replace()` silently did nothing and left a call
  to an unimported name (C73). Rewrite a whole file with `cat >` rather than patching;
  never end a replacement literal on a quote character (C71).
- **Log self-corrections by name, with reasoning**, as `C<n>.` in `decisions.md` --
  see C61-C76. The recurring failure: a claim and the thing it describes, edited
  separately (a ledger row marked Done describing three steps earlier, a skip reason
  false for two phases, a commit message naming work the tree lacked, a docstring
  listing 21 of 27 analyses).
- **No linter.** `ruff` is not a dependency (the `.ruff_cache/` is stale); the only
  dev dependency is `pytest`. Line width is measured from the repo, not configured
  (max 105 in `src/` as of 21/09/2026).
- **No numpy or pandas in `src/` or `tests/`.** Both are transitive dependencies of
  statsmodels; a transitive dependency is not a licence to import it. The analysis
  tier reads with `fetchall` and no analysis materialises a column. scipy is used for
  distribution tails and one power solve, each on scalars.

## How a step runs
A step is one document and one commit. Write the plan to `docs/steps/phaseN_stepM_*.md`
BEFORE running anything; it holds numbered commands in order and is the record
afterwards -- paste each command's real output beneath it. When a command fails, the
fix is a numbered sub-step beneath it (`1.1`, `4.2`) with its own expected output, in
the same document -- never in chat only, never in another file. Close a step by
appending `P<n>-D<n>.` entries with their measured figures plus a `MEASURED VALIDATION`
line carrying digests and suite totals, updating the guide's ledger row if the phase's
state changed, then running all six checks and the eval above, reading them, and committing.

## Navigating the docs -- read narrowly
`docs/decisions.md` is ~6,400 lines and append-only; the build guide is 1,163. Reading
either whole costs more than the work.

- **Open-item register: `docs/decisions.md:4438` to end.** Read it rather than grepping
  for `IS OPEN` -- closures were recorded two ways and a grep undercounts by half (C68).
  The register is superseded: it recorded the state before fixes in its own commit (C78).
  The closing section of the most recent step, at the END of the file, carries the
  current state; the guide's phase ledger row summarises it.
- Decisions are `P<phase>-D<n>.`, open items `P<phase>-O<n> IS OPEN.`, corrections `C<n>.`
  Grep the identifier and read the surrounding lines; do not open the file.
- Build guide: tier lists at lines 590-628, Phase 15 at 994, phase ledger table at ~1059-1076.
- Prefer one command that answers a question over several that circle it. If the
  question is what a file contains, open the file.

## Note on AGENTS.md
`AGENTS.md` is a role spec for a *different* agent -- an executor that receives STEP
SPECs, makes no design decisions, and is forbidden from committing or editing
`decisions.md`. Its context-hygiene and no-claim-without-output rules apply here; its
role and scope fence do not. This file governs sessions that plan, decide and commit.
