# Phase 12 Step 2 - recording what an analysis ran with

21/09/2026. Baseline 8a4a576. Measured before starting: 1714 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1; test_phase11.py 26/0/0.

## What this closes

P12-O1. "A reproduction appendix listing exact tool calls" has no source, because a written
result keeps its table and loses its parameters, its summary and its method note (P12-D3). The
answer chosen in Step 1 is the one the other five tiers already use: record the run.

Taking the calls as an argument to build_report was rejected and the reason is worth restating
here, because it is the tempting option: the appendix would then record what the agent says it
ran rather than what ran, which is a claim and the thing it describes written separately -- in
the one section whose whole purpose is that someone else can repeat the work.

## The shape it copies

`ensure_table` / `record` / `latest` / `history` per dataset, appended never updated, in a table
named with `BOOKKEEPING_PREFIX` so `state.py:197` keeps it out of the dataset list. Five modules
do this already: validate/runs, contract/store, clean/plan, clean/ledger, profile/runs. This is
`analysis/runs.py`, the sixth, and it deliberately looks like the others.

One table for analyses and charts rather than two. A chart run is an analysis run that also drew
something, so the chart columns are nullable on the same row -- which is also what links a PNG
to the analysis that produced it, and "findings with charts" needs that link as much as the
appendix needs the parameters.

## What a row holds

dataset_name, analysis_type, run_at, the parameters as given, the contract version it ran under,
the row count, the result path, and nullable chart kind and chart path. Plus the summary lines,
because the method note is the sentence saying what the numbers were computed over and P12-D3
measured it not surviving the call.

`AnalysisRun.call()` renders the exact invocation -- `compute_analysis(dataset_name="...",
analysis_type="top_n", dimension="region", measure="revenue", n=3)` -- which is the appendix's
line, and is only possible because the parameters are stored rather than inferred.

## Predictions

1. The parameters round-trip through JSON without loss: every analysis parameter in the tool
   signature is str, int or float.
2. Recording happens after success, so a refused call records nothing. The appendix lists what
   ran, not what was attempted.
3. `_produce` currently returns (gate, output) and strips Nones internally; it has to return the
   stripped parameters too, since those are what was actually passed.
4. `state.py:197` already filters `_`-prefixed tables, so the new table will not appear as a
   dataset and `get_workflow_state` will not list it.
5. At least one existing test will notice the new write -- something that counts tables in a
   workspace, or asserts what a fresh workspace contains. I expect one or two, not more.
6. Suite rises by the new tests plus whatever prediction 5 costs.

## Commands

1. Write `src/analytics_agent/analysis/runs.py`.
2. Record from `tools.compute_analysis` and `tools.render_chart`.
3. Unit tests for the record and the call renderer.
4. Full suite; fix whatever prediction 5 turns up.
5. Record as P12-D5 onward, close P12-O1, commit.

## Outputs

**1-2.** `analysis/runs.py`, 238 lines, max width 96, digest
`815ec11b216453089f79e97ea5f54a6eb4d083cd025ebd699302fab6441f9920`. `_produce` now returns the
stripped parameters as well, and both tools record after success.

**End to end, before any test was written:**

    compute_analysis  rows=3    drew=False
      call    : compute_analysis(dataset_name="clean_sales", analysis_type="top_n",
                dimension="region", measure="revenue", n=3)
      note    : 500 of 500 row(s) analysed.
      artifact: top_n_20260921-130048.csv
    render_chart      rows=5    drew=True
      call    : render_chart(dataset_name="clean_sales", analysis_type="frequency",
                chart="line", column="region", y="rows")
      note    : 500 of 500 row(s) analysed.
      artifact: frequency_20260921-130048.png

**3-4. Predictions, scored.** 1, 2, 3 and 4 held. **5 was wrong**: I expected one or two
existing tests to notice the new write and none did, which says nothing asserts what a workspace
contains after an analysis. The suite stayed at 1714 through the wiring and only moved when the
new tests arrived.

One test of mine failed and the failure was mine: it asked for `dimension="region"` against a
fixture whose columns are id, status, ts and amount, so the call was refused, nothing was
recorded, and `len(recorded) == 0`. That is prediction 2 working -- a refused call records
nothing -- read for a minute as the record being broken.

**5. Final.** Suite 1714 -> 1732: fifteen unit tests on the record and the call renderer, three
on the tools recording through it. Acceptance unchanged at 99/0/2, 19/0/0, 35/0/1, 26/0/0.
