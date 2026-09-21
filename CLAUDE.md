# analytics-agent

MCP server exposing data loading, profiling, cleaning and contract-gated analysis
to Claude Desktop. Phases 1-10 done. Phase 11 (charts) is in progress: Steps 1-2
done -- matplotlib ground facts (P11-D1 to D7) and `charts/render.py`, the eight
kinds with null screening and a Rule 4 envelope (P11-D8 to D15). `render_chart`
is not wired to server.py yet; that is Step 3.

## Stack
Python >= 3.12 via `uv` -- run everything through `uv run`, never `pip install`.
DuckDB 1.5.5, FastMCP 3.4.7, psycopg 3, pydantic 2, openpyxl, PyYAML, scipy,
statsmodels, matplotlib 3.11.2 (backend Agg, set before the pyplot import). PostgreSQL 17 (Homebrew) on localhost:5432 serving `olist` and `testdb`.
Layout: `src/analytics_agent/{ingest,profile,clean,contract,validate,analysis,charts,report,util}`;
`server.py` registers MCP tools, `state.py` holds the workflow gate.
27 analyses across 7 tiers. An analysis's shape: `analysis/{registry,base,declared,stats}.py`.

## Verify before committing
All four, every time. Run the suite BEFORE committing, not after (C76: two commits
recorded a broken tree). Last measured 21/09/2026, after the open-item cleanup:

    uv run pytest -q                      # 1699 passed
    uv run python tests/test_phase8.py    # 99 passed, 0 failed, 2 skipped
    uv run python tests/test_phase9.py    # 19 passed, 0 failed, 0 skipped
    uv run python tests/test_phase10.py   # 35 passed, 0 failed, 1 skipped

The acceptance scripts are scripts, not pytest files -- `pytest` collects nothing
from them, so 1699 excludes them. The three skips are each deliberate and
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
state changed, then running all four checks above, reading them, and committing.

## Navigating the docs -- read narrowly
`docs/decisions.md` is 4,517 lines and append-only; the build guide is 1,104. Reading
either whole costs more than the work.

- **Open-item register: `docs/decisions.md:4438` to end.** Read it rather than grepping
  for `IS OPEN` -- closures were recorded two ways and a grep undercounts by half (C68).
  The register is superseded: it recorded the state before fixes in its own commit (C78).
  Read the "Cleanup Step 1" section at the END of the file for the current list.
- Decisions are `P<phase>-D<n>.`, open items `P<phase>-O<n> IS OPEN.`, corrections `C<n>.`
  Grep the identifier and read the surrounding lines; do not open the file.
- Build guide: tier lists at lines 589-627, phase ledger table at ~1005-1013.
- Prefer one command that answers a question over several that circle it. If the
  question is what a file contains, open the file.

## Note on AGENTS.md
`AGENTS.md` is a role spec for a *different* agent -- an executor that receives STEP
SPECs, makes no design decisions, and is forbidden from committing or editing
`decisions.md`. Its context-hygiene and no-claim-without-output rules apply here; its
role and scope fence do not. This file governs sessions that plan, decide and commit.
