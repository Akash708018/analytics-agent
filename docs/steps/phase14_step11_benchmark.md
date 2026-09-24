# Phase 14 Step 11: a benchmark of every tool, and the list of what behaves badly

Opened 24/09/2026. Asked for: "prepare a test case and based on that create a benchmark for this
analytics tool, for only the tools available in this project; strictly monitor everything and
write down all the negative behaviour that needs to be fixed." Nothing is fixed in this step --
the deliverable is the benchmark and the list (docs/benchmark/BENCHMARK.md).

## What is measured (scripts/benchmark.py)

One generated sales table with ground truth known by construction, at 1,000 / 100,000 /
1,000,000 rows: order_id unique; order_date over 2023-2024 with March 2024 left EMPTY; 1% of rows
dated January 2025, outside the contract window; 0.5% of rows with no units and no revenue;
East sells ~3 more units per order than elsewhere; a two-valued `segment`; customers drawn from
a pool of N/5. The contract: window 2023-01-01..2024-12-31, units sum, unit_price none,
revenue sum.

Every one of the 29 MCP tools is called through server.py, as the agent calls it, and every
analysis of the 27 is run with fixed parameters. Per call: wall time, output characters,
whether an exception escaped. Per analysis: the result CSV compared cell by cell with the same
figure computed in plain Python (statistics, scipy for F / t / Pearson / Spearman), on the
in-window rows, tolerance = the rounding of the printed figure. Plus:

- determinism: each analysis run twice, result files compared;
- scaling: time at 1M over time at 100k (linear = 10x);
- output size against the agent's 8,000-character read (webapp/agent.py RESULT_CHARS);
- memory (peak RSS) and disk (workspace bytes) per size;
- refusal quality: a set of wrong calls; each must answer text with a NEXT STEP that names a
  real tool, and the NEXT STEP must be one that can resolve the stated WHY;
- cleaning: a small dirty table with known defects; the plan must find each, applying it must
  give the ground-truth total;
- the Postgres tools with no server running (this container has none): how long they take to
  refuse, and what they say;
- the web layer's Explore (RealBackend.run_analysis over the menu defaults).

A negative is anything the benchmark flags: WRONG (a number off ground truth), CRASH, SLOW
(over 2s at 100k rows, or scaling 1M/100k above 15x), BIG (over 8,000 characters), NONDET,
REFUSAL (no NEXT STEP, or one that cannot resolve the refusal), plus what I read in the outputs.

Expected, stated before the first run: numbers right everywhere (1,910 tests pin them; the
eval is 76/76); some outputs over 8,000 characters (profile_dataset and cohort_retention are
wide); loads at 1M rows the slowest call, near-linear; the Postgres tools refuse quickly;
result files are display-formatted text (seen while probing: "2,108,498.34", "25.7%") --
recorded as a negative whatever the run says.

## Commands

1. `uv run python scripts/benchmark.py --sizes 1000` -- the harness's own shakedown.
2. `uv run python scripts/benchmark.py` -- all three sizes; writes docs/benchmark/benchmark.json
   and docs/benchmark/BENCHMARK.md.
3. Triage every flag: tool fault or harness fault. A harness fault is fixed in the harness with
   the reason, as a numbered sub-step here.
4. Checks (six suites and the eval), records, commit.

## Results

### 1. Shakedown at 1,000 rows

First run: 560/581 checks right, and most of the flags were my harness's own faults. Each was fixed
in the harness and re-run:

1.1 NONDET on every analysis. A second run of the same call in the same second writes
    `<name>_<stamp>_2.csv`, and my mask did not cover the `_2`. The engine is right: no result
    file is overwritten (checked separately: top_n by region and then by channel in one second
    wrote two files).
1.2 bivariate: 20 WRONG. I binned half-open [from, to). The tool bins ranges of distinct
    values, closed at both ends, and its reply says so. Corrected in the harness.
1.3 group_compare and hypothesis_test each carry an extra row, "(all)" and "(no units)" --
    my loop read them as regions.
1.4 hypothesis_test: the p value is followed by the sentence's full stop, "1.94758e-14.".
1.5 profile_dataset writes a column per bullet, "  - units (BIGINT): ... 2 null", not per table
    row.
1.6 Cleaning, "MISSED qty / joined": 'N/A' is read as NULL at load, and dd/mm/yyyy is loaded as
    DATE, so there was nothing left to clean. The check now looks at the outcome: every date is
    compared with the date written.
1.7 render_chart with the chart kind the menu names refused all nine analyses: "Name one with y".
    The harness now makes the first call as an agent would (no y), records the refusal as
    FRICTION, then calls again with y.
1.8 Refusal grading: a NEXT STEP that names a tool without parentheses ("call list_datasets to
    see") counts as naming it; a successful list_sources is not a refusal.

Second shakedown: 600/601 right, and the one miss was 1.3's second row. After that fix, the flags
that remained were the tool's own, not the harness's.

### 2. All three sizes

First full run: 1926/1930 right. The 4 misses were hypothesis_test at 100k and 1M, and they were
mine (2.1): at that size the reply reads "Statistic 1,623.2097, df 3, 98509, p < 1e-300.", with a
comma and a bound, and my regex found no statistic. Re-run:

    1932/1932 ground-truth checks right; 409 calls; 40 flags: FRICTION 27, REFUSED 6, REFUSAL 3, SLOW 3, CRASH 1

Predictions:

- numbers right everywhere -- right (600 / 666 / 666);
- some replies over 8,000 characters -- WRONG, none is: the largest is build_report at 7,700,
  then run_analysis at 6,551;
- the 1M load the slowest call -- WRONG: confirm_ingest_spec takes 1.6 s, while
  propose_cleaning_plan takes 8.5 s and profile_dataset and profile_column 5.9 s each;
- Postgres refuses quickly -- right (0.02-0.06 s), and it refuses before any server is reached:
  DuckDB's postgres extension cannot download here (HTTP 403);
- result files as display text -- confirmed (N10).

2.1 Harness: the hypothesis regex now reads commas and a "p < bound" (compared as scipy p below
    the bound).

### 3. Triage

Every remaining flag is the tool's own; there are no harness flags left. They are grouped as
negatives N1-N13 in docs/benchmark/BENCHMARK.md, with the causes that were measured:

- The SLOW three (N3) share one cause, measured at 100k:
  - column_stats takes 0.09 s;
  - the type-reading expressions take 0.3-0.4 s per text column (six TRY_CAST candidates over
    every value);
  - profile_column builds the whole table profile before it looks at one column.
  cProfile could not see any of this, because it does not count time spent inside DuckDB's
  execute; the expressions were timed one by one.
- The three REFUSED (N2) come from RealBackend._defaults, which takes the last two months present
  in the data rather than the last two inside the window.
- The three REFUSAL flags (N4, N5), plus the rest read from the refusal table by eye (N4-N7):
  a NEXT STEP that ignores its own WHY; propose_dataset_contract where no contract can help;
  profile_dataset pointing at a call that fails the same way; get_cleaning_ledger saying
  "nothing cleaned" for a dataset that does not exist.
- The single CRASH (N1): load_excel on a CSV. Step 10's S4 covered only the draft path.
- FRICTION 27 = 9 chart analyses x 3 sizes (N9).
- Read by eye rather than flagged: a heatmap of a trend drawn (N8); Key findings that are scope
  lines (N11); the run_analysis menu at 82% of the agent's read (N12); Postgres needing a
  download (N13).

3.1 BENCHMARK.md's first draft gave validate_dataset's outside-window counts as 1,100 and 10,636,
    and the growth from 100k to 1M as "at most 3x", all written before I read them. Measured:
    1,004 and 9,879; the worst growth is 8.5x (top_n n=200 over 200,000 customers, still linear)
    and the median 1.7x over 93 calls. Corrected before commit (C104).

3.2 After the full run, `git status` showed seven new directories, docs/contracts/bench*/. A
    confirmed contract is exported to docs/contracts/<workspace>/, and reset_workspace does not
    remove the export. That is the tool's behaviour (N14, P14-O26), but it was my harness
    that put them in the repository: the tests redirect store.EXPORT_DIR (P13-O2) and I had not.
    The harness now sets it to its temporary directory; the leftovers are deleted. Re-run at
    1k: "600/600 ground-truth checks right; 172 calls; 16 flags: FRICTION 9, REFUSAL 3,
    REFUSED 3, CRASH 1", with docs/contracts holding only clean_sales.yaml. The committed
    benchmark.json and results.md are the three-size run of command 2, restored after this
    1k re-run overwrote them.

Nothing in src/ was changed in this step: the request was to write the negatives down.

### 4. Checks

    1910 passed in 109.23s (0:01:49)
    50 passed in 13.58s
    phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
    SCORE: 76/76 (100%)
    benchmark: 1932/1932 ground-truth checks right; 40 flags -> negatives N1-N13, and N14 from 3.2 (P14-O13 to O26)
