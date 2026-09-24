# Benchmark: every tool, measured -- and what behaves badly

> **Status after Phase 14 Step 12 (24/09/2026):** 12 of the 14 are fixed, and 2 are closed by
> decision. `results.md` and `benchmark.json` now hold the run after the fixes. The findings
> below are kept as they were measured in Step 11. The table at the end gives each outcome.

Phase 14 Step 11, 24/09/2026. Harness: `uv run python scripts/benchmark.py` (about 10 minutes for
all three sizes). Raw figures: [results.md](results.md) (generated) and `benchmark.json`.
The step record, including the harness's own mistakes, is
docs/steps/phase14_step11_benchmark.md. **Nothing listed below has been fixed yet.**

## The test case

The harness generates one sales table whose answers are known in advance, at 1,000, 100,000 and
1,000,000 rows. Its planted traps:

- March 2024 holds no rows;
- 1% of rows are dated January 2025, outside the contract window;
- 0.5% of rows have no units and no revenue;
- East sells about 3 more units per order, and wholesale about 2 more;
- customers come from a pool of N/5, so some return and cohorts form.

It then does the following:

- calls all 29 MCP tools the way the agent calls them;
- runs all 27 analyses, each twice;
- draws every analysis that has a chart;
- makes 36 deliberately wrong calls;
- cleans a dirty table (`$1,234.50` amounts, `N/A`, padded text, dd/mm/yyyy dates);
- runs the web layer's Explore through all 27 analyses with its own default settings.

Every figure in every result file was compared with the same figure computed independently in
plain Python, using `statistics`, and `scipy` for F, t, Pearson and Spearman. The tolerance is
the rounding of the printed figure.

## Scorecard

| what | result |
|---|---|
| Numbers right against ground truth | **1,932 / 1,932** (600 at 1k, 666 at 100k, 666 at 1M) |
| Same answer twice (all 27 analyses, 3 sizes) | 81 / 81 identical result files, no result file overwritten |
| Slowest analysis at 1,000,000 rows | 0.41 s (cohort_retention); 0.97 s for top_n n=200 over 200,000 customers |
| Load 1,000,000 rows (66 MB CSV) | 1.6 s (confirm_ingest_spec) |
| Growth from 100k to 1M rows | never faster than linear: worst 8.5x for 10x the rows (that top_n); median 1.7x over 93 calls |
| Replies over the agent's 8,000-character read | 0 (largest: build_report 7,700, run_analysis 6,551) |
| Wrong calls answered with a crash | **1 of 36** (load_excel) |
| Wrong calls answered in over 2 s | 0 (slowest 0.31 s) |
| Explore defaults that run first time | **24 / 27** |
| Tools over 2 s at 100k rows | **3** (profile_dataset, profile_column, propose_cleaning_plan) |

The engine's arithmetic is sound at every size tested. What follows are the places where
behaviour, speed and guidance are not.

## Negative behaviour to fix

Ranked by what it costs a user; N14 was found last, in the repository after the run. Each item gives the measurement and how to reproduce it.

### High: a crash, a broken default, and slow profiling

**N1. load_excel crashes on a file that is not a workbook.** Passing a CSV to `load_excel`
raises `InvalidFileException` from openpyxl (`excel.py:284`) straight out of the MCP tool.
Step 10's S4 fixed this on the draft path (`propose_ingest_spec`, the web Upload screen); the
direct loader was never covered. This is the benchmark's only crash.

**N2. Explore's default settings are refused for 3 of 27 analyses.** period_compare,
growth_decomposition and mix_shift fail with `ANALYSIS_PARAMS_INVALID: '2025-01' is not a month
in this calendar` whenever the data runs past the contract window (seen at 1k and 100k). The
cause is `RealBackend._defaults` (`webapp/real_backend.py`): it takes the last two months present
in the data, not the last two months inside the window. A person clicking Run on the form's own
values gets a refusal.

**N3. Profiling and cleaning proposals are slow, and profile_column costs as much as the whole
table.**

| call | 1k | 100k | 1M |
|---|---|---|---|
| profile_dataset | 0.10 s | 2.10 s | 5.88 s |
| profile_column (one column) | 0.09 s | 2.15 s | 5.94 s |
| propose_cleaning_plan | 0.26 s | 3.43 s | 8.45 s |
| any analysis, for comparison | 0.06-0.10 s | 0.08-0.15 s | 0.11-0.41 s |

The cause was measured at 100k rows:

- `column_stats` takes 0.09 s, and the numeric and text aggregates take 0.05 s each;
- the type-reading expressions (`table_profile._cast_exprs`) take 0.3-0.4 s per text column:
  six TRY_CAST candidates over every value of every text column, one of them 0.21 s alone;
- with six text columns that adds up to about 2 s;
- it is recomputed on every call, even for `region`, which has 4 distinct values;
- `profile_column` builds the full table profile first (`profile/tools.py:114`) to look at one
  column;
- propose_cleaning_plan pays the same cost and more.

The fix direction: read types over the distinct values rather than every row (or sample), and
let profile_column profile its own column.

### Medium: guidance that sends the agent the wrong way

**N4. A NEXT STEP that ignores its own WHY.** Four different refusals of `compute_analysis` all
end with the same fallback, `NEXT STEP: call compute_analysis(dataset_name="sales",
analysis_type="summary_stats")`:

- an analysis nobody registered ("regression");
- an argument the analysis does not take (`bins` to trend);
- an unknown grain ("fortnight");
- a period outside the window ("2025-01").

In each case the WHY names the fix: the valid names, the right arguments, the calendar's months.
The NEXT STEP should repeat the call with that fix. An agent that follows NEXT STEP literally
computes summary_stats instead of what was asked.

**N5. NEXT STEP = propose_dataset_contract where a new contract cannot help.**

- concentration over customer_id (199 groups, cap 49): the WHY says "top_n on customer_id says
  which of its groups matter", but the NEXT STEP says re-contract;
- a measure that is not a column (`profit`): no contract can declare a column that does not
  exist.

**N6. profile_dataset on a missing dataset points to a call that fails too.** Its NEXT STEP is
`describe_dataset(dataset_name="nope")`, which is refused for the same reason. It should say
`list_datasets()`, as describe_dataset and validate_dataset do.

**N7. get_cleaning_ledger does not notice a dataset that does not exist.** For "nope" it answers
"Nothing has been cleaned for nope. Every table is as it was loaded." That is false comfort.
Its NEXT STEP also carries a literal placeholder: `propose_cleaning_plan(dataset_name="...")`.

**N8. render_chart draws a chart that does not fit the result.** Asked for a heatmap of a trend,
it draws one, with `revenue (sum)` and `rows` on one colour scale, two quantities in different
units. A line was the right kind. Refusal is the answer here.

**N9. Every chart analysis is refused in the chart kind the menu names for it, until `y` is
given.**

- Affected: all 9 at every size (top_n, group_compare, distribution, ranking_shift, trend,
  seasonality, period_compare, growth_decomposition, mix_shift).
- The reason: the result carries a `rows` column beside the measure, so "this result offers 2:
  revenue (sum), rows. Name one with y."
- The cost: the agent loses a round trip on every chart.
- The web layer hides this with `pick_y=True`; the MCP tool has no such default.

### Low: output format

**N10. Result files are display text, not data.** Examples:

- totals keep their thousands separators (`"2,108,498.34"`);
- shares are percent strings (`25.7%`);
- signs are written in (`+0.631`);
- rounding is to display precision (Pearson r to 3 places, shares to 1).

Opened in a spreadsheet or read by another program, the numbers are strings and the precision is
gone. The benchmark had to parse them back. The tables are meant to be the record behind every
figure, and a machine-readable CSV beside the display table would keep that promise.

**N11. The report's "Key findings" are not findings.** build_report lists one line per recorded
analysis run: its scope line ("summary_stats: 989 of 1,000 row(s) analysed. 11 outside ...").
Repeated runs are repeated. At 75 runs the reply is 7,700 characters and grows with every run,
so at about 80 runs it passes the agent's 8,000-character read and the end of the reply is lost.

**N12. The run_analysis menu is 6,551 characters for a 10-column contract**, 82% of the agent's
read budget. A wider contract, with more measures or dimensions, will be cut off.

**N13. Postgres needs internet on first use.** DuckDB downloads its postgres extension the first
time it is used. On a machine without that access (this container: HTTP 403), describe_source,
query_source and load_postgres_table are all unusable. They refuse quickly (0.03-0.06 s) and say
why, so this is a deployment limitation, not a wrong answer. Bundling the extension would remove
it. A live Postgres server could not be benchmarked here.

**N14. reset_workspace leaves the workspace's contracts behind.** A contract confirmed through
MCP in any workspace but the default is exported to `docs/contracts/<workspace>/` for version
control. reset_workspace deletes the data and the stored contract, but not that export, so
the repository keeps YAML definitions of datasets that no longer exist. The benchmark's first
full run left seven such directories (found in `git status`, removed by hand). The harness now
sends its exports to a temporary directory. The web layer is not affected: it exports into the
workspace (P14-D19).

## Measured and fine

These were checked and found sound:

- **Correctness:** every analysis matches ground truth at every size. That includes:
  - the empty month, which is named, left blank rather than zero, and refused as a baseline with
    the reason;
  - the rows outside the window, which are excluded and counted, and flagged by
    validate_dataset (11 / 1,004 / 9,879);
  - the null rows, which are counted and shown.
- **Cleaning:** the dirty table came out right. Every amount was read (sum 986,960.62 exact), 25
  `N/A` became null, the padding was trimmed, and 400 of 400 dd/mm/yyyy dates were read as the
  dates written.
- **Stability:** there is no nondeterminism, and two results in one second get two files
  (`_2`).
- **Limits:** the refusals for the gate (no contract), reset without confirm, a path outside the
  workspace, and a non-unique key are all correct, all fast, and all name a working next call.
- **Resources:** peak memory of the whole process, harness included, was 346 / 422 / 968 MiB.
  The workspace held 3.1 / 4.7 / 19.6 MB after 78 files.

## After Step 12

The same harness was run again after the fixes: 1,932 / 1,932 figures right, and 15 flags
instead of 40. All 15 are FRICTION: charts where the choice of `y` is real, which P11-D13
leaves to the caller.

| # | outcome | measured |
|---|---|---|
| N1 | fixed | load_excel refuses a non-workbook and points at propose_ingest_spec |
| N2 | fixed | Explore defaults stay inside the window: 3 and 3 refused -> 0 and 0 |
| N3 | fixed at 100k; improved at 1M | profile_dataset 2.105 -> 0.438 s (1M: 5.878 -> 2.237); profile_column 2.151 -> 0.481 s (1M: 5.941 -> 2.221); propose_cleaning_plan 3.426 -> 1.195 s (1M: 8.452 -> 5.337, the unique id columns) |
| N4 | fixed | a wrong argument repeats the same analysis with its arguments filled; an unknown one points at run_analysis |
| N5 | fixed | a group cap points at top_n; a column that does not exist points at describe_dataset |
| N6 | fixed | a missing dataset points at list_datasets() |
| N7 | fixed | the ledger refuses a dataset that is not loaded; no "..." |
| N8 | fixed | a heatmap only for cross_tab and cohort_retention; empty cells stay in place (the old code shifted them) |
| N9 | fixed where the caller named the measure | trend, top_n, seasonality and period_compare draw without y; real choices still ask |
| N10 | closed by decision | result files stay the reply's table; see Step 12, section 5 |
| N11 | fixed | key findings are findings, one per distinct call, capped at 12: 7,700 -> 2,407 characters |
| N12 | closed by decision | 6,551 characters, under the 8,000-character read; re-measured every run |
| N13 | fixed as far as a machine can be | a cached extension loads with no network; offline, a downloaded file named in ANALYTICS_DUCKDB_POSTGRES_EXTENSION is installed |
| N14 | fixed | reset_workspace removes that workspace's contract exports |

Nothing else moved:

- the engine and UI suites pass (1947 and 50);
- the acceptance scripts are unchanged;
- the eval is 76/76;
- the scenario matrix is 30/30;
- the stress rounds' 4,336 records are identical call by call.

