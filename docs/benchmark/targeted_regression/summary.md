# Targeted regression: the Step 13 defects, before and after

Original revision `2d3d52f3667b3c920859f657addca7313f21bf3f` (the code the cross-domain benchmark measured); fixed revision `fc6ffd8847e9ef311a1219b2bc29c4a2fac79a52`. Python 3.12.3, DuckDB 1.5.5.

| measure | value |
|---|---|
| regression cases | 55 |
| product defects tested | 7 (D1, D12, D13, D2, D3, D6-D9, H chart (harness)) |
| defect cases whose original failure reproduced | 26 of 26 |
| defect cases passing on the fixed code | 26 of 26 |
| controls | 29, changed: 0 |
| cases failing | 0 |
| concurrency isolation (H, fixed code) | NOT_RUN |
| reproducibility (J, fixed code) | NOT_RUN |

## By case

| case | category | before | after | passed | expected |
|---|---|---|---|---|---|
| D1.exact_mix_shift | PRODUCT_DEFECT | EXCEPTION BinderException | REFUSED | yes | a refusal naming the column, its type and a runnable next step |
| D1.exact_outlier_detection | PRODUCT_DEFECT | EXCEPTION BinderException | REFUSED | yes | a refusal naming the column, its type and a runnable next step |
| D1.exact_correlation | PRODUCT_DEFECT | EXCEPTION BinderException | REFUSED | yes | a refusal naming the column, its type and a runnable next step |
| D1.exact_driver_analysis | PRODUCT_DEFECT | EXCEPTION BinderException | REFUSED | yes | a refusal naming the column, its type and a runnable next step |
| D1.control_text_count | CONTROL | OK | OK | yes | valid before and after, same answer |
| D1.control_text_count_distinct | CONTROL | OK | OK | yes | valid before and after, same answer |
| D1.control_numeric_sum | CONTROL | OK | OK | yes | valid before and after, same answer |
| D1.control_numeric_mean | CONTROL | OK | OK | yes | valid before and after, same answer |
| D1.control_numeric_median | CONTROL | OK | OK | yes | valid before and after, same answer |
| D2.both_zero_variance_hypothesis_test | PRODUCT_DEFECT | EXCEPTION ZeroDivisionError | OK | yes | a stated 'no test' with no manufactured p-value |
| D2.both_zero_variance_hypothesis_test_rank | PRODUCT_DEFECT | OK | OK | yes | unchanged |
| D2.both_zero_variance_effect_size | PRODUCT_DEFECT | EXCEPTION ZeroDivisionError | OK | yes | a stated 'no test' with no manufactured p-value |
| D2.a_zero_variance_only_hypothesis_test | CONTROL | OK | OK | yes | unchanged |
| D2.a_zero_variance_only_hypothesis_test_rank | CONTROL | OK | OK | yes | unchanged |
| D2.a_zero_variance_only_effect_size | CONTROL | OK | OK | yes | unchanged |
| D2.b_zero_variance_only_hypothesis_test | CONTROL | OK | OK | yes | unchanged |
| D2.b_zero_variance_only_hypothesis_test_rank | CONTROL | OK | OK | yes | unchanged |
| D2.b_zero_variance_only_effect_size | CONTROL | OK | OK | yes | unchanged |
| D2.identical_groups_hypothesis_test | CONTROL | OK | OK | yes | unchanged |
| D2.identical_groups_hypothesis_test_rank | CONTROL | OK | OK | yes | unchanged |
| D2.identical_groups_effect_size | CONTROL | OK | OK | yes | unchanged |
| D2.constant_same_value_hypothesis_test | PRODUCT_DEFECT | EXCEPTION ZeroDivisionError | OK | yes | a stated 'no test' with no manufactured p-value |
| D2.constant_same_value_hypothesis_test_rank | PRODUCT_DEFECT | EXCEPTION ZeroDivisionError | OK | yes | a stated 'no test' with no manufactured p-value |
| D2.constant_same_value_effect_size | PRODUCT_DEFECT | EXCEPTION ZeroDivisionError | OK | yes | a stated 'no test' with no manufactured p-value |
| D2.tiny_two_each_hypothesis_test | CONTROL | OK | OK | yes | unchanged |
| D2.tiny_two_each_hypothesis_test_rank | CONTROL | OK | OK | yes | unchanged |
| D2.tiny_two_each_effect_size | CONTROL | OK | OK | yes | unchanged |
| D2.normal_valid_hypothesis_test | CONTROL | OK | OK | yes | unchanged |
| D2.normal_valid_hypothesis_test_rank | CONTROL | OK | OK | yes | unchanged |
| D2.normal_valid_effect_size | CONTROL | OK | OK | yes | unchanged |
| D3.all_null_col_v_sum | PRODUCT_DEFECT | OK | REFUSED | yes | rejected at the contract, never reaching an analysis |
| D3.inf_nan_v_sum | PRODUCT_DEFECT | OK | REFUSED | yes | rejected at the contract, never reaching an analysis |
| D3.words_v_sum | PRODUCT_DEFECT | OK | REFUSED | yes | rejected at the contract, never reaching an analysis |
| D3.words_v_mean | PRODUCT_DEFECT | OK | REFUSED | yes | rejected at the contract, never reaching an analysis |
| D3.words_v_median | PRODUCT_DEFECT | OK | REFUSED | yes | rejected at the contract, never reaching an analysis |
| D3.words_v_count | CONTROL | OK | OK | yes | accepted and analysed, before and after |
| D3.words_v_count_distinct | CONTROL | OK | OK | yes | accepted and analysed, before and after |
| D3.words_w_sum | CONTROL | OK | OK | yes | accepted and analysed, before and after |
| D3.words_w_mean | CONTROL | OK | OK | yes | accepted and analysed, before and after |
| D3.words_w_median | CONTROL | OK | OK | yes | accepted and analysed, before and after |
| D12.parser_16_threads | PRODUCT_DEFECT | EXCEPTION IndexError | OK | yes | 16 threads, 3,200 parses, none swapped or raised |
| RECS.dup_rows_key | PRODUCT_DEFECT | REFUSED | REFUSED | yes | names the cleaning plan, runnable |
| RECS.correlation_one_measure | PRODUCT_DEFECT | REFUSED | REFUSED | yes | asks for a contract, not v against v |
| RECS.correlation_two_measures | PRODUCT_DEFECT | REFUSED | REFUSED | yes | measure v against w, runnable |
| RECS.corrupt_xlsx | PRODUCT_DEFECT | REFUSED | REFUSED | yes | does not send the same file back |
| RECS.only_result_file | PRODUCT_DEFECT | REFUSED | REFUSED | yes | the runnable path |
| RECS.nonexistent_dataset | CONTROL | REFUSED | REFUSED | yes | unchanged refusal and next step |
| RECS.invalid_chart | CONTROL | REFUSED | REFUSED | yes | unchanged refusal and next step |
| RECS.group_cap | CONTROL | REFUSED | REFUSED | yes | unchanged refusal and next step |
| PAGING.asked_200 | PRODUCT_DEFECT | OK | OK | yes | the same page, and the cap stated |
| PAGING.asked_200_first | PRODUCT_DEFECT | OK | OK | yes | the same page, and the cap stated |
| PAGING.asked_10_control | CONTROL | OK | OK | yes | unchanged, no cap note |
| PAGING.last_page | PRODUCT_DEFECT | OK | OK | yes | the same page, and the cap stated |
| CHART_ISOLATION.chart_ds_a | PRODUCT_DEFECT | OK | OK | yes | no value of the other dataset anywhere |
| CHART_ISOLATION.chart_ds_b | PRODUCT_DEFECT | OK | OK | yes | no value of the other dataset anywhere |

## profile_column, median seconds over four columns

| rows | before | after | speedup |
|---:|---:|---:|---:|

## Phases H and J

```
{
 "before": {
  "concurrency_correctness": {
   "PASS": 41,
   "ORACLE_ERROR": 1
  },
  "isolation": {
   "correctness": {
    "PASS": 20
   },
   "reports": {
    "PASS": 10
   },
   "ledgers": {
    "PASS": 10
   },
   "charts": {
    "PASS": 10
   }
  },
  "concurrency_calls": {
   "OK": 162,
   "EXCEPTION": 2
  },
  "concurrency_exceptions": [
   "IndexError: list index out of range"
  ],
  "H_repeat": {
   "OK": 196
  },
  "H_traced": {
   "OK": 36
  },
  "H_isolation": {
   "OK": 110
  }
 },
 "after": {}
}
```

## Benchmark (harness) defects, kept apart from product defects

- 2.1 BENCHMARK_DEFECT: sample_adequacy: my power solve's bracket reached values where scipy's noncentral t returns NaN (ORACLE_ERROR).
- 2.2 BENCHMARK_DEFECT: The NULL group of mix_shift is labelled "(no <dimension>)", not "(null)".
- 2.3 BENCHMARK_DEFECT: A negative Welch t, and a negative Hedges' g, failed my regex.
- 2.4 BENCHMARK_DEFECT: A zero MAD (discount is 60% zeros): the engine leaves the MAD fence blank rather than divide by zero. The oracle now requires the blank and the reply's reason.
- 2.5 BENCHMARK_DEFECT: Two known answers were mine and wrong: 2024-11 is month 22 of the arithmetic trend (320, not 330), and 240 rows of a 1..9 cycle average 4.9625, not 5. The engine printed both correctly.
- 2.6 BENCHMARK_DEFECT: The result files were deleted with each workspace, so a verification could not be repeated. They are now copied to the evidence directory first, and `--reverify` re-checks a unit from evidence and the regenerated dataset (sha256 checked) without calling a tool. - **In the product**, kept as found: h
- 2.7 BENCHMARK_DEFECT: distribution: the engine gives integer measures integer-aligned bins, so the last bin is narrower. The oracle assumed equal widths. It now checks each count against the edges the result states, and records the unequal last bin as a finding (LOW, section 4).
- 2.8 BENCHMARK_DEFECT: sample_adequacy: two root-finders on one power curve agree to 1e-3 relative, not to the printed digit (ecommerce: 0.4206 printed, 0.420650 here).
- 2.9 BENCHMARK_DEFECT: The top_n and frequency oracles were quadratic, and a 1M unit stalled in the oracle, not the tool. I stopped the run at the D/E boundary, made both linear, and resumed from the checkpoint.
- 2.10 BENCHMARK_DEFECT: wait4's ru_maxrss carries the parent's high-water mark across fork+exec on Linux, so every worker "peaked" at the parent's size. The worker peak now comes from the per-call VmHWM records.
- 2.11 BENCHMARK_DEFECT: The stress gate scaled from the 1M tier. It asked 16.2 GB for sales 10M against 14.6 free, and skipped it. The gate now scales from the largest completed tier, and sales 10M is re-gated.
- 2.12 BENCHMARK_DEFECT: G's adversarial dataset kept its exact duplicate rows. Its contract on record_id was rightly refused, so 17 wrong calls met the contract gate instead of their own fault. C001 now runs before the contract, and dup_ids expects a refusal naming the contract.
- 2.13 BENCHMARK_DEFECT: The classifier credited only a few phrasings. "No test: ...", "undefined rather than" and the like are safe diagnoses. Dirty variants are now judged on every step, not only the first.
- 2.14 BENCHMARK_DEFECT: Welch's df printed as "2e+06" failed my regex. The regex now accepts it; the notation itself is a finding (section 4).
- 2.15 BENCHMARK_DEFECT: scipy's noncentral t returns NaN at 1M-row df. `_power` falls back to the normal approximation there.
- 2.16 BENCHMARK_DEFECT: "p < 1e-300." ends a sentence, and my parser read the period as part of the number.
- 2.17 BENCHMARK_DEFECT: Dirty plans were judged against 0 duplicates. Per-row noise makes most of the clean file's duplicates distinct, so the expectation is now each variant file's own exact repeats.
- 2.18 BENCHMARK_DEFECT: read_result_file serves at most 50 rows a page and says so, with the call for the next page. I asked for 200 and counted the stated cap as a failure.
- 2.19 BENCHMARK_DEFECT: H (repeat, traced, concurrency, isolation) and J (reproducibility) contracted on record_id without dropping duplicates first. Every contract was refused, so they measured gate refusals. C001 now runs first everywhere. Isolation now cleans all ten datasets in one workspace, and each ledger must hold 
- 2.20 BENCHMARK_DEFECT: A call that raised wrote no result, and the oracle was handed None (an ORACLE_ERROR of KeyError). Such a call is now NOT_VERIFIED_NO_RESULT; its own record carries the exception.
- reverify BENCHMARK_DEFECT: preserved evidence re-judged with the corrected oracle, no tool called again (30 units; failed checks 28 at first judgement, 0 of 6,157,243 now)
