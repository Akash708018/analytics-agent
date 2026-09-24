# Phase 14 Step 12: fix what the benchmark found, without moving anything else

Opened 24/09/2026. Asked for: "fix the remaining gap without impacting the other field" -- the
14 negatives of Step 11 (docs/benchmark/BENCHMARK.md, P14-O13 to O26).

"Without impacting the other field" is the constraint every fix is judged by. Every figure the
tools produce today must come out identical: the 1,910 engine tests, the eval (76/76), the stress
rounds (CRASH 0; WRONG 10/3/8/0), the scenario matrix (30/30) and the benchmark's 1,932
ground-truth checks are re-run, and a changed result anywhere is a regression, not a side effect.

## Plan, per negative

- N3 speed (P14-O15). Measured causes (qtime probe, 100k rows): the profile's type reading is
  about 0.3-0.4 s per text column inside the one big SELECT; the cleaning plan's mixed-date test
  (a COALESCE of up to 16 TRY_STRPTIME formats) takes 0.95 s on customer_id and 0.89 s on
  order_id, and many smaller per-column scans follow it.
  - Profile: count the type readings over DISTINCT values weighted by their counts. The casts
    are a function of the value, so the counts are identical (measured below).
  - Cleaning plan: every share test is only ever compared with CONVERT_MIN_SHARE. Look at a
    sample first: if the sample alone holds more failures than the whole column may have and
    still reach the threshold, the answer is exactly "no". Otherwise count in full, as today.
    The same test with the same threshold, reached sooner.
- N1 (P14-O13): excel.load_excel turns a file openpyxl cannot open into LoadRefused, in the same
  words as the draft path (S4).
- N2 (P14-O14): Explore's period defaults are clipped to the contract window.
- N4 (P14-O16): an unknown analysis points at run_analysis (which lists them); a wrong argument
  set repeats the same analysis with its required arguments filled from the contract, instead
  of summary_stats.
- N5 (P14-O17): a group-cap refusal whose WHY names top_n gets that top_n call; an undeclared
  column that does not exist in the table gets describe_dataset (a contract cannot declare it);
  one that exists keeps propose_dataset_contract, which is right for it.
- N6 (P14-O18): "dataset not loaded" from column_stats points at list_datasets().
- N7 (P14-O19): get_cleaning_ledger refuses a dataset that is not loaded; no "..." placeholder.
- N8 (P14-O20): a heatmap only where every column is one quantity (cross_tab, cohort_retention).
  Found while reading the code: the heatmap DROPS empty cells and cuts every row to the
  shortest one, so a blank shifts the later values under the wrong labels, and a cohort
  triangle is cut to its youngest cohort's width. Empty cells now stay in place, blank.
- N9 (P14-O21): P11-D13 stands (the agent chooses y). Refined: when exactly one offered column
  carries the measure the caller named, the caller has chosen, and it is drawn.
- N11 (P14-O23): Key findings are each run's first substantive line, not its scope line; a
  repeated identical run is listed once; the list is capped, with the rest counted.
- N13 (P14-O25): LOAD before INSTALL (a cached extension needs no network), and a refusal that
  names the exact file and folder to use offline.
- N14 (P14-O26): reset_workspace also removes that workspace's contract exports
  (non-default workspaces only; the default's docs/contracts/*.yaml are version-controlled).
- N10 (P14-O22) and N12 (P14-O24) are NOT changed, with the reason recorded (step 5 below).

## Commands

1. Ground facts: tests/test_benchmark_fix_facts.py pins that distinct-weighted type counts equal
   row counts (NULL, blanks, tokens, mixed types) and that the sample disproof never reverses
   a threshold decision. Expected: all pass, on the first run.
2. The fixes, each with a test in tests/test_benchmark_fixes.py.
3. Benchmark again: `uv run python scripts/benchmark.py`. Expected: 1,932/1,932 still;
   profile_dataset, profile_column and propose_cleaning_plan under 2 s at 100k; no CRASH,
   REFUSED or REFUSAL flags; FRICTION down from 9 per size to the charts that offer a genuine
   choice.
4. Everything else: the six suites, UI tests, eval, stress rounds, scenario matrix -- each
   identical to Step 11's figures.
5. Records, commit.

## Results

### 1. Ground facts

    13 passed in 4.09s          (tests/test_benchmark_fix_facts.py; predicted: all pass)

Measured before building, at 100k and 1M rows (castexp probe), the current per-row reading
against the distinct-weighted one, identical counts each time:

    100000  order_id     current 0.370  distinct-weighted 0.115  identical=True
    100000  customer_id  current 0.374  distinct-weighted 0.034  identical=True
    100000  region       current 0.291  distinct-weighted 0.006  identical=True
    1000000 order_id     current 1.020  distinct-weighted 1.017  identical=True
    1000000 customer_id  current 1.020  distinct-weighted 0.229  identical=True
    1000000 region       current 0.813  distinct-weighted 0.009  identical=True

A unique column gains nothing at 1M rows, and loses nothing either.

### 2. The fixes

Query timer (a proxy around the connection, 100k rows), before -> after:

    profile_table  2.04s, 5 queries    -> 0.45s, 11 queries
    detect         3.39s, 127 queries  -> 1.57s (share tests sampled first)
                                       -> 0.96s, 139 queries (proposed_type's tests too)

Tests: tests/test_benchmark_fixes.py, 23. Run against the old src/ (stashed): 20 fail and 3 pass.
The 3 are guards for behaviour that must NOT move: an existing undeclared column still points
at the contract, a real choice of y is still the caller's, a cross_tab heatmap is still drawn.

2.1 A test of mine (the cross_tab heatmap) accepted "drawn or refused" -- C103's failure: a
    check that cannot fail. Rewritten on a second dimension, so it must draw.
2.2 Two existing checks drew summary_stats as a heatmap: tests/test_analysis_tools.py and
    Phase 11's acceptance clause 2. That is the chart N8 refuses (n, nulls, total and mean on
    one colour scale). Their point, that each kind of chart can be drawn, is kept: the unit test
    keeps grouped_bar, scatter and box, with the heatmap refusal pinned beside them; the
    acceptance clause's heatmap now comes from cross_tab. Phase 11 went 25/1 -> 26/0. Found by
    the checks, not predicted: I had not searched for summary_stats heatmaps before the change.
2.3 The first benchmark after the fixes held one REFUSAL flag, against my own new refusal:
    the heatmap's WHY said "a line or bar chart draws it" while its NEXT STEP offered the table.
    It now names the chart that fits, y included, and following it draws the chart (tested).
    The harness's WHY/NEXT comparison now counts only an analysis the WHY recommends ("top_n on
    X"), not one it mentions in passing -- Step 11's triage of the hypothesis_test case.
2.4 Stress rounds, compared record by record with the committed JSON: my first comparison
    keyed on field names the records do not have ('step', 'tool') and so compared each
    dataset's outcomes in list order rather than call by call. Redone on (dataset, stage, call),
    outcome and refusal reason: 0 differences in 4,336 records. The re-run JSON files differ only
    in timings and were restored rather than committed.

### 3. Benchmark again

    1932/1932 ground-truth checks right; 397 calls; 15 flags: FRICTION 15

Before (Step 11) -> after, seconds, from the two benchmark.json files:

    profile_dataset        100,000: 2.105 -> 0.438   1,000,000: 5.878 -> 2.237
    profile_column         100,000: 2.151 -> 0.481   1,000,000: 5.941 -> 2.221
    propose_cleaning_plan  100,000: 3.426 -> 1.195   1,000,000: 8.452 -> 5.337
    build_report reply     7,700 -> 2,407 characters
    flags                  REFUSAL 3, CRASH 1, FRICTION 27, REFUSED 6, SLOW 3 -> FRICTION 15
    web Explore refused    3 and 3 (1k, 100k) -> 0 and 0

Predictions:

- 1,932/1,932 -- right.
- The three slow calls under 2 s at 100k -- right (0.44, 0.48, 1.20).
- No CRASH, REFUSED or REFUSAL flags -- right in the end (2.3 held one).
- FRICTION down to genuine choices -- right: 5 per size. These are group_compare's eight
  statistics, distribution's edge beside its count, ranking_shift's and growth_decomposition's
  before and after, and mix_shift's eight parts. P11-D13 leaves each of them to the caller.

Not predicted, and still slow: propose_cleaning_plan at a million rows is 5.3 s. The cost left is
the unique id columns, which a sample cannot rule out. Every value of order_id has to be tried
against every type, and there are a million distinct values. It is recorded as the residual of
P14-O15.

### 4. Everything else, unchanged

    1947 passed in 122.36s (0:02:02)        (1910 + 13 facts + 23 fixes + 1 heatmap refusal)
    50 passed in 13.61s
    phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
    SCORE: 76/76 (100%)
    stress rounds: CRASH 0; WRONG 10 / 3 / 8 / 0 -- and 0 differences in 4,336 records, outcome
                   and refusal reason, call by call against the committed JSON
    scenario matrix: 30 checks: CRASH 0, WRONG 0, OK 30

### 5. Not changed, and why

- N10 (P14-O22), result files as display text. The analyses round and format each figure as
  they build their rows (27 row builders), and the file holds the same cells the reply's table
  shows. A numeric file means rewriting every row builder and every reply table. That touches
  every figure the eval and 1,910 tests read, which is the opposite of "without impacting the
  other field". Closed by decision (P14-D79); it is a later format change of its own.
- N12 (P14-O24), the run_analysis menu at 6,551 characters. It is under the web agent's
  8,000-character read. Its lines are what the agent chooses an analysis by, and shortening
  them changes what a model is told. Closed by decision (P14-D79), measured again by every
  benchmark run.
