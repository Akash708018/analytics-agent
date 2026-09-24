# Phase 14 Step 13: a cross-domain benchmark -- ten data domains, three sizes, stress tiers

Opened 24/09/2026. Asked for: a second benchmark across ten realistic domains (financial, HR,
sales, marketing, CRM, e-commerce, logistics, healthcare [synthetic], manufacturing, education)
at 1k / 100k / 1M rows, then 2M / 5M / 10M stress tiers, with independent correctness oracles,
wrong-call classification, performance, memory, scaling, concurrency, isolation and
reproducibility -- a benchmark, not a demo. Production code is NOT changed in this step.

## Design (scripts/domain_benchmark/)

- Every dataset is generated from a seed and a stored configuration. Anomalies are inserted
  deliberately and counted in the manifest: nulls, duplicate rows, duplicated business keys,
  outliers, extreme values, skew, rare and high-cardinality categories, constant and
  near-constant columns, imbalance, dates outside the window and missing dates, zeros,
  negatives, booleans and timestamps.
- The ORACLE reads the generated CSV with Python's csv module and computes every expected
  figure in plain Python plus scipy. It imports nothing from analytics_agent.
- Tool calls run in a WORKER SUBPROCESS per dataset. After every call it appends a JSONL
  record (flushed and fsynced), with wall time, RSS before and after, the per-call peak (the
  kernel's VmHWM, reset through /proc/self/clear_refs), response size and any exception with
  its stack trace. A worker that dies is recorded as a CRASH at the step it was in, and is
  restarted after that step.
- Each timed operation gets one cold run and 3 measured runs; the profiling calls at 1M rows
  get fewer, and the record says so. The application has no analysis cache (grep: the only
  lru_cache is the web agent's model list), so every call is recorded as CACHE_MISS.
- Principal workflow per dataset:
  1. check, preview, propose and confirm the ingest spec;
  2. profile_dataset, profile_column on every column, propose_cleaning_plan, apply only
     DROP_DUPLICATE_ROWS (the oracle drops the same exact duplicates), get_cleaning_ledger;
  3. propose_dataset_contract, first with the duplicated business key (a refusal is
     expected), then with the surrogate key; confirm;
  4. list, describe, workflow state, validate, run_analysis;
  5. every analysis in the domain x analysis matrix, each checked by the oracle;
  6. charts, read_result_file, build_report;
  7. the NOT_APPLICABLE attempts, classified;
  8. the high-cardinality N sweep.
- The compatibility matrix is built from the live registry, so a new analysis cannot escape:
  an analysis the matrix does not classify runs as UNCLASSIFIED and is reported.

## Predictions, stated before the first run

- Correctness: every figure right on the principal datasets, apart from what the probe already
  showed. One failure is already known and not fixed: mix_shift on a count_distinct measure
  over a text column raises DuckDB's BinderException out of the MCP tool, found by the
  aggregation probe while designing. Domains that declare such a measure will record it.
- Performance: every analysis under 1 s at 1M rows. propose_cleaning_plan the slowest call
  (about 5 s at 1M rows, Step 12), and profile_dataset and profile_column about 2 s at 1M.
- Stress: 2M and 5M complete; 10M is uncertain on 16 GB with no swap. The oracle at stress
  tiers is streaming, and only partial.
- Wrong calls: no process crash; at least one FAIL_EXCEPTION (the mix_shift binder error).

## Commands

1. Phase A: baseline tests, environment, git state.
2. Phases B to K: `uv run python scripts/domain_benchmark/run.py` (checkpointed). Then the
   benchmark's own tests: `uv run pytest -q tests/test_domain_benchmark.py`.
3. Final tests, git diff, records, commit.

## Results

### 1. Phase A: baseline, before any benchmark file existed

    commit 2d3d52f3667b3c920859f657addca7313f21bf3f   status_lines 0
    1947 passed in 123.41s (0:02:03)
    50 passed in 13.68s
    phase6: 36/0/0  phase8: 55/0/3  phase9: 0/0/1  phase10: 0/0/1  phase11: 26/0/0  phase12: 36/0/0
    SCORE: 76/76 (100%)

Machine: Intel Xeon @ 2.80GHz x 4, 16,095 MiB RAM, no swap, about 30 GB of free disk; Python
3.12.3; DuckDB 1.5.5.

### 2. Shakedown, and the harness's own faults (each fixed in the harness, never in src/)

Probes before building (aggregation types, test formats) found one defect in the product, kept
for the benchmark to record: mix_shift on a count_distinct measure over a text column raises
DuckDB's BinderException out of compute_analysis.

The smoke run (financial, 1k) gave 3,597 of 3,602 checks. All 5 misses were my conventions:

- the engine leaves an empty cross_tab cell, or a member absent from a period, blank rather
  than 0 -- its own documented rule;
- "df n/a" for a rank test.

After the fix: 3,609 of 3,609.

Run 1 of phases A, B and C, preserved outside the repository under _superseded/run1_*:

- **Harness faults**, each fixed:
  - 2.1 sample_adequacy: my power solve's bracket reached values where scipy's noncentral t
    returns NaN (ORACLE_ERROR).
  - 2.2 The NULL group of mix_shift is labelled "(no <dimension>)", not "(null)".
  - 2.3 A negative Welch t, and a negative Hedges' g, failed my regex.
  - 2.4 A zero MAD (discount is 60% zeros): the engine leaves the MAD fence blank rather than
    divide by zero. The oracle now requires the blank and the reply's reason.
  - 2.5 Two known answers were mine and wrong: 2024-11 is month 22 of the arithmetic trend
    (320, not 330), and 240 rows of a 1..9 cycle average 4.9625, not 5. The engine printed
    both correctly.
  - 2.6 The result files were deleted with each workspace, so a verification could not be
    repeated. They are now copied to the evidence directory first, and `--reverify` re-checks
    a unit from evidence and the regenerated dataset (sha256 checked) without calling a tool.
- **In the product**, kept as found: hypothesis_test with two zero-variance groups raises
  ZeroDivisionError out of compute_analysis (analysis/inferential.py:124, welch). Trace
  preserved.

The full run (run 2) starts from an empty checkpoint.
