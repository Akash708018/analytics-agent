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

### 3. Run 2, and the harness faults it found (2.7 to 2.19, each fixed in the harness)

Run 2 measured the original code throughout. src/ was not touched in this tree while it ran:
fixes were made in a separate worktree (section 4).

- 2.7 distribution: the engine gives integer measures integer-aligned bins, so the last bin
  is narrower. The oracle assumed equal widths. It now checks each count against the edges
  the result states, and records the unequal last bin as a finding (LOW, section 4).
- 2.8 sample_adequacy: two root-finders on one power curve agree to 1e-3 relative, not to the
  printed digit (ecommerce: 0.4206 printed, 0.420650 here).
- 2.9 The top_n and frequency oracles were quadratic, and a 1M unit stalled in the oracle, not
  the tool. I stopped the run at the D/E boundary, made both linear, and resumed from the
  checkpoint.
- 2.10 wait4's ru_maxrss carries the parent's high-water mark across fork+exec on Linux, so
  every worker "peaked" at the parent's size. The worker peak now comes from the per-call
  VmHWM records.
- 2.11 The stress gate scaled from the 1M tier. It asked 16.2 GB for sales 10M against 14.6
  free, and skipped it. The gate now scales from the largest completed tier, and sales 10M
  is re-gated.
- 2.12 G's adversarial dataset kept its exact duplicate rows. Its contract on record_id was
  rightly refused, so 17 wrong calls met the contract gate instead of their own fault. C001
  now runs before the contract, and dup_ids expects a refusal naming the contract.
- 2.13 The classifier credited only a few phrasings. "No test: ...", "undefined rather than"
  and the like are safe diagnoses. Dirty variants are now judged on every step, not only the
  first.
- 2.14 Welch's df printed as "2e+06" failed my regex. The regex now accepts it; the notation
  itself is a finding (section 4).
- 2.15 scipy's noncentral t returns NaN at 1M-row df. `_power` falls back to the normal
  approximation there.
- 2.16 "p < 1e-300." ends a sentence, and my parser read the period as part of the number.
- 2.17 Dirty plans were judged against 0 duplicates. Per-row noise makes most of the clean
  file's duplicates distinct, so the expectation is now each variant file's own exact
  repeats.
- 2.18 read_result_file serves at most 50 rows a page and says so, with the call for the next
  page. I asked for 200 and counted the stated cap as a failure.
- 2.19 H (repeat, traced, concurrency, isolation) and J (reproducibility) contracted on
  record_id without dropping duplicates first. Every contract was refused, so they measured
  gate refusals. C001 now runs first everywhere. Isolation now cleans all ten datasets in one
  workspace, and each ledger must hold exactly its own action with its own count. F, G, H,
  J and sales 10M are superseded in state.json with their reason, their evidence is moved
  to _superseded/run2_*, and they are re-run.
- 2.20 A call that raised wrote no result, and the oracle was handed None (an ORACLE_ERROR of
  KeyError). Such a call is now NOT_VERIFIED_NO_RESULT; its own record carries the exception.

### 4. Defects in the product, and their fixes (worktree branch step14-fixes-wip)

Every fix has a test in tests/test_domain_benchmark_defects.py (D1-D11) or
tests/test_date_prescreen_facts.py. Run against src/ as of f5dd3d4 (the code the benchmark
measured): `11 failed, 1 passed` (D12, added later: fails there, passes here) -- every D test fails there, and the one control (a key
repeated by distinct rows keeps the contract call) passes. The facts file cannot import there
(DATE_PREFIX is new), which is expected.

| id | found by | defect | fix |
|---|---|---|---|
| D1 | E, G | mix_shift over a count_distinct text measure raised BinderException | `_produce` turns Binder/Conversion/OutOfRange errors into ANALYSIS_NOT_POSSIBLE naming the column types |
| D2 | B_stat, G | hypothesis_test / effect_size on zero-variance groups raised ZeroDivisionError | a stated "No test" / "No effect size" |
| D3 | G | a VARCHAR column accepted as a sum measure, then every analysis raised | contract refuses a numeric aggregation of a text column, pointing to propose_cleaning_plan |
| D4 | H_concurrency | threads first using one workspace raced on CREATE TABLE (TransactionException) | `create_if_missing` retries at the schema and six lazy tables |
| D5 | I 5M | Mann-Whitney / Kruskal tie term overflowed INT64 | HUGEINT tie term |
| D6 | H, J, G | a key repeated only by exact duplicate rows got a `primary_key=[...]` template | names propose_cleaning_plan and the count |
| D7 | G | correlation with one declared measure suggested `against="..."`, or the measure itself | keeps the given arguments; asks for a contract when none is left |
| D8 | F | a corrupt .xlsx was sent back through propose_ingest_spec on the same file | says to re-save or export |
| D9 | G | `<one of: x>` when x was the only result file | the runnable path |
| D10 | C-E charts | cohort heatmap replies over 8,000 characters (49 series described) | first 12 described, the rest counted |
| D11 | E, I | Welch df "2e+06"; "equal-width" bins with a narrower last bin | df as a number; the narrow last bin stated |
| D12 | H_concurrency (rerun) | ten threads scoping one workspace: 2 raised IndexError from sql_guard's one shared parser connection. Run 2 met D4 first and never got here | one parser connection per thread |
| P1 | E, I | profile_column profiled the whole table (51 s a call at 10M) | profiles its own column; identical output on 24 of 24 columns |
| P2 | E | propose_cleaning_plan 13.6 s median at 1M: 16 date formats tried on id and label columns | an exact pre-screen (fuzzed: 0 of 140,232 parsed values screened out); 24.3 s to 11.8 s on financial 1M under load |
