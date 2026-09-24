# Cross-domain benchmark: summary

Generated from `benchmark.json` and the files beside it by `scripts/domain_benchmark/summary.py`; no figure below is typed by hand. Healthcare data is entirely synthetic; nothing here is medical advice.

## Executive summary

| measure | value |
|---|---|
| domains | 10 / 10 |
| principal datasets | 30 |
| stress datasets run | 5 |
| calls executed | 12,840 |
| correctness checks attempted | 6,157,413 |
| checks passed | 6,157,385 |
| checks failed | 28 |
| verified calls skipped (no oracle / resource) | 96 |
| known-answer checks passed | 50 / 50 |
| warnings | 1,166 |
| errors | 107 |
| worker crashes | 0 |
| exceptions escaping a tool | 11 |
| timeouts | 0 |
| total benchmark runtime (s) | 8,404.200 |
| peak worker memory (MiB) | 3,627.200 |
| largest workspace (MiB) | 1,225.490 |

Machine: Intel(R) Xeon(R) Processor @ 2.80GHz x 4, 16095 MiB RAM, SwapTotal:             0 kB; Linux-6.18.44-fc-v37-x86_64-with-glibc2.39; Python 3.12.3; commit 2d3d52f3667b on claude/trusting-edison-en0jnk.

Defects by severity: CRITICAL 26, HIGH 49, MEDIUM 32, LOW 0

### Wrong answers (worse than crashes)

| # | domain | rows | analysis | expected | observed |
|---|---|---|---|---|---|
| 12 | ecommerce | 1,000 | sample_adequacy  | minimum detectable d = 0.4206504714341478 | 0.4206 (1 of 2 checks failed) |
| 13 | manufacturing | 1,000 | distribution  | bin 4 rows = 189 | 211 (6 of 13 checks failed) |
| 14 | crm | 100,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 15.2604, df 1.569e+04, p  |
| 15 | education | 100,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -1.8539, df 2.634e+04, p  |
| 17 | healthcare | 100,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -23.859, df 9.686e+04, p  |
| 18 | hr | 100,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.7679, df 1.847e+04, p  |
| 19 | manufacturing | 100,000 | distribution  | bin 3 rows = 30636 | 32,771 (8 of 13 checks failed) |
| 20 | marketing | 100,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.7413, df 5.555e+04, p  |
| 22 | crm | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 43.8571, df 1.594e+05, p  |
| 24 | ecommerce | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.1578, df 4.675e+04, p 0 |
| 26 | education | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.2756, df 2.603e+05, p 0 |
| 28 | healthcare | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -78.4531, df 9.637e+05, p |
| 30 | hr | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.4665, df 1.874e+05, p 0 |
| 35 | manufacturing | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -1.0274, df 9.334e+04, p  |
| 36 | marketing | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.1435, df 5.591e+05, p 0 |
| 38 | sales | 1,000,000 | hypothesis_test t | the reply states a statistic and a p value = Test: ... p ... |   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.2691, df 5.366e+04, p  |
| 98 | financial | 10,000 | None  | only its own dataset | {"dataset": "financial", "names_its_measure": false, "names_another_dataset": [], "status" |
| 99 | hr | 10,000 | None  | only its own dataset | {"dataset": "hr", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL |
| 100 | sales | 10,000 | None  | only its own dataset | {"dataset": "sales", "names_its_measure": false, "names_another_dataset": [], "status": "F |
| 101 | marketing | 10,000 | None  | only its own dataset | {"dataset": "marketing", "names_its_measure": false, "names_another_dataset": [], "status" |
| 102 | crm | 10,000 | None  | only its own dataset | {"dataset": "crm", "names_its_measure": false, "names_another_dataset": [], "status": "FAI |
| 103 | ecommerce | 10,000 | None  | only its own dataset | {"dataset": "ecommerce", "names_its_measure": false, "names_another_dataset": [], "status" |
| 104 | logistics | 10,000 | None  | only its own dataset | {"dataset": "logistics", "names_its_measure": false, "names_another_dataset": [], "status" |
| 105 | healthcare | 10,000 | None  | only its own dataset | {"dataset": "healthcare", "names_its_measure": false, "names_another_dataset": [], "status |
| 106 | manufacturing | 10,000 | None  | only its own dataset | {"dataset": "manufacturing", "names_its_measure": false, "names_another_dataset": [], "sta |
| 107 | education | 10,000 | None  | only its own dataset | {"dataset": "education", "names_its_measure": false, "names_another_dataset": [], "status" |

## Correctness

By domain and scale (a skipped check is not a pass):

| domain | rows | calls verified | checks | passed | failed | calls skipped | correct % |
|---|---|---|---|---|---|---|---|
| crm | 1,000 | 47 | 9,524 | 9,524 | 0 | 0 | 100.000 |
| crm | 100,000 | 47 | 301,391 | 301,390 | 1 | 0 | 100.000 |
| crm | 1,000,000 | 47 | 2,954,834 | 2,954,833 | 1 | 0 | 100.000 |
| ecommerce | 1,000 | 47 | 3,539 | 3,538 | 1 | 0 | 99.972 |
| ecommerce | 100,000 | 47 | 66,581 | 66,581 | 0 | 0 | 100.000 |
| ecommerce | 1,000,000 | 47 | 602,569 | 602,568 | 1 | 0 | 100.000 |
| education | 1,000 | 50 | 2,148 | 2,148 | 0 | 0 | 100.000 |
| education | 100,000 | 47 | 15,567 | 15,566 | 1 | 0 | 99.994 |
| education | 1,000,000 | 47 | 83,068 | 83,067 | 1 | 0 | 99.999 |
| financial | 1,000 | 47 | 3,640 | 3,640 | 0 | 0 | 100.000 |
| financial | 100,000 | 47 | 66,567 | 66,567 | 0 | 0 | 100.000 |
| financial | 1,000,000 | 47 | 601,543 | 601,543 | 0 | 0 | 100.000 |
| healthcare | 1,000 | 50 | 1,678 | 1,678 | 0 | 0 | 100.000 |
| healthcare | 100,000 | 47 | 10,165 | 10,164 | 1 | 0 | 99.990 |
| healthcare | 1,000,000 | 47 | 37,157 | 37,156 | 1 | 0 | 99.997 |
| hr | 1,000 | 43 | 2,885 | 2,885 | 0 | 0 | 100.000 |
| hr | 100,000 | 46 | 37,717 | 37,716 | 1 | 0 | 99.997 |
| hr | 1,000,000 | 46 | 308,240 | 308,239 | 1 | 0 | 100.000 |
| logistics | 1,000 | 47 | 1,690 | 1,690 | 0 | 0 | 100.000 |
| logistics | 100,000 | 47 | 21,989 | 21,989 | 0 | 0 | 100.000 |
| logistics | 1,000,000 | 47 | 156,971 | 156,971 | 0 | 0 | 100.000 |
| logistics | 2,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| logistics | 5,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| logistics | 10,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| manufacturing | 1,000 | 50 | 1,522 | 1,516 | 6 | 0 | 99.606 |
| manufacturing | 100,000 | 47 | 14,312 | 14,304 | 8 | 0 | 99.944 |
| manufacturing | 1,000,000 | 47 | 81,825 | 81,824 | 1 | 0 | 99.999 |
| marketing | 1,000 | 50 | 1,490 | 1,490 | 0 | 0 | 100.000 |
| marketing | 100,000 | 47 | 14,294 | 14,293 | 1 | 0 | 99.993 |
| marketing | 1,000,000 | 47 | 81,833 | 81,832 | 1 | 0 | 99.999 |
| sales | 1,000 | 45 | 3,372 | 3,372 | 0 | 0 | 100.000 |
| sales | 100,000 | 45 | 66,466 | 66,466 | 0 | 0 | 100.000 |
| sales | 1,000,000 | 45 | 602,527 | 602,526 | 1 | 0 | 100.000 |
| sales | 2,000,000 | 21 | 63 | 63 | 0 | 18 | 100.000 |
| sales | 5,000,000 | 21 | 63 | 63 | 0 | 18 | 100.000 |

Total: 6,157,385 of 6,157,413 checks passed, 28 failed, 96 verified calls skipped.

Analyses with correctness failures: hypothesis_test (13), distribution (2), sample_adequacy (1)

Known-answer fixtures: 50 of 50 passed.

Sorted vs shuffled input (identical tables required): trend_day PASS, trend_week PASS, trend_month PASS, season_month PASS, season_week PASS, season_flat PASS, cp_ramp PASS, coverage_day PASS

## Performance

### 1,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| render_chart | 0.046 | 0.178 | 4.700 | 142 |
| confirm_ingest_spec | 0.244 | 0.268 | 0.480 | 10 |
| propose_cleaning_plan | 0.249 | 0.305 | 0.377 | 10 |
| compute_analysis:top_n | 0.044 | 0.069 | 0.317 | 82 |
| propose_dataset_contract | 0.073 | 0.094 | 0.165 | 20 |
| profile_dataset | 0.096 | 0.127 | 0.150 | 10 |
| profile_column | 0.094 | 0.117 | 0.145 | 10 |
| compute_analysis:driver_analysis | 0.081 | 0.090 | 0.115 | 10 |
| apply_cleaning_plan | 0.077 | 0.094 | 0.113 | 10 |
| compute_analysis:sample_adequacy | 0.076 | 0.080 | 0.109 | 10 |
| validate_dataset | 0.094 | 0.100 | 0.107 | 10 |
| compute_analysis:effect_size | 0.064 | 0.071 | 0.095 | 30 |
| compute_analysis:hypothesis_test | 0.064 | 0.073 | 0.092 | 40 |
| compute_analysis:trend | 0.045 | 0.069 | 0.092 | 24 |
| compute_analysis:confidence_interval | 0.065 | 0.072 | 0.092 | 20 |
| compute_analysis:calendar_coverage | 0.069 | 0.071 | 0.092 | 10 |
| compute_analysis:group_compare | 0.046 | 0.073 | 0.090 | 30 |
| compute_analysis:outlier_detection | 0.071 | 0.074 | 0.090 | 20 |
| compute_analysis:frequency | 0.058 | 0.067 | 0.088 | 30 |
| compute_analysis:period_compare | 0.068 | 0.072 | 0.087 | 10 |
| compute_analysis:summary_stats | 0.067 | 0.078 | 0.086 | 10 |
| compute_analysis:seasonality | 0.067 | 0.071 | 0.085 | 10 |
| compute_analysis:cross_tab | 0.066 | 0.072 | 0.084 | 20 |
| compute_analysis:ranking_shift | 0.064 | 0.067 | 0.084 | 10 |
| compute_analysis:repeat_behaviour | 0.046 | 0.073 | 0.084 | 11 |
| compute_analysis:correlated_shift | 0.067 | 0.071 | 0.083 | 10 |
| compute_analysis:mix_shift | 0.066 | 0.073 | 0.083 | 10 |
| compute_analysis:pareto | 0.044 | 0.064 | 0.082 | 22 |
| compute_analysis:cohort_retention | 0.046 | 0.073 | 0.082 | 10 |
| compute_analysis:correlation | 0.046 | 0.070 | 0.082 | 28 |
| compute_analysis:growth_decomposition | 0.041 | 0.072 | 0.081 | 11 |
| compute_analysis:bivariate | 0.064 | 0.070 | 0.077 | 10 |
| compute_analysis:changepoint | 0.066 | 0.071 | 0.076 | 10 |
| compute_analysis:distribution | 0.064 | 0.069 | 0.076 | 10 |
| describe_dataset | 0.056 | 0.066 | 0.074 | 10 |
| compute_analysis:concentration | 0.041 | 0.064 | 0.072 | 20 |
| build_report | 0.044 | 0.047 | 0.069 | 10 |
| get_workflow_state | 0.051 | 0.055 | 0.060 | 10 |
| run_analysis | 0.042 | 0.045 | 0.055 | 10 |
| get_cleaning_ledger | 0.025 | 0.027 | 0.041 | 10 |
| confirm_dataset_contract | 0.032 | 0.035 | 0.040 | 10 |
| list_datasets | 0.021 | 0.023 | 0.026 | 10 |
| propose_ingest_spec | 0.005 | 0.005 | 0.006 | 10 |
| read_result_file | 0.000 | 0.000 | 0.001 | 10 |
| preview_file | 0.000 | 0.000 | 0.000 | 10 |
| check_file | 0.000 | 0.000 | 0.000 | 10 |

### 100,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| render_chart | 0.064 | 0.231 | 5.296 | 142 |
| propose_cleaning_plan | 1.699 | 2.355 | 3.081 | 10 |
| profile_dataset | 0.705 | 0.900 | 1.231 | 10 |
| profile_column | 0.686 | 0.913 | 1.225 | 10 |
| compute_analysis:top_n | 0.060 | 0.099 | 0.996 | 82 |
| propose_dataset_contract | 0.358 | 0.525 | 0.940 | 20 |
| apply_cleaning_plan | 0.544 | 0.735 | 0.858 | 10 |
| confirm_ingest_spec | 0.616 | 0.696 | 0.805 | 10 |
| compute_analysis:frequency | 0.078 | 0.093 | 0.456 | 30 |
| compute_analysis:summary_stats | 0.134 | 0.172 | 0.220 | 10 |
| describe_dataset | 0.131 | 0.156 | 0.204 | 10 |
| compute_analysis:driver_analysis | 0.129 | 0.160 | 0.189 | 10 |
| compute_analysis:cohort_retention | 0.115 | 0.146 | 0.172 | 10 |
| compute_analysis:group_compare | 0.063 | 0.114 | 0.160 | 30 |
| compute_analysis:outlier_detection | 0.121 | 0.136 | 0.159 | 20 |
| compute_analysis:pareto | 0.066 | 0.084 | 0.158 | 22 |
| compute_analysis:repeat_behaviour | 0.110 | 0.139 | 0.157 | 11 |
| compute_analysis:concentration | 0.066 | 0.085 | 0.156 | 20 |
| validate_dataset | 0.133 | 0.144 | 0.155 | 10 |
| compute_analysis:hypothesis_test | 0.086 | 0.109 | 0.154 | 40 |
| compute_analysis:growth_decomposition | 0.060 | 0.130 | 0.150 | 11 |
| compute_analysis:mix_shift | 0.120 | 0.126 | 0.148 | 10 |
| compute_analysis:correlation | 0.061 | 0.124 | 0.147 | 28 |
| compute_analysis:distribution | 0.098 | 0.125 | 0.144 | 10 |
| compute_analysis:sample_adequacy | 0.111 | 0.118 | 0.133 | 10 |
| compute_analysis:cross_tab | 0.095 | 0.117 | 0.130 | 20 |
| compute_analysis:trend | 0.059 | 0.095 | 0.128 | 24 |
| compute_analysis:confidence_interval | 0.097 | 0.106 | 0.126 | 20 |
| compute_analysis:bivariate | 0.089 | 0.094 | 0.123 | 10 |
| compute_analysis:effect_size | 0.089 | 0.105 | 0.122 | 30 |
| compute_analysis:correlated_shift | 0.097 | 0.101 | 0.119 | 10 |
| compute_analysis:changepoint | 0.092 | 0.104 | 0.118 | 10 |
| compute_analysis:seasonality | 0.091 | 0.099 | 0.117 | 10 |
| compute_analysis:period_compare | 0.092 | 0.098 | 0.115 | 10 |
| compute_analysis:ranking_shift | 0.089 | 0.096 | 0.112 | 10 |
| compute_analysis:calendar_coverage | 0.094 | 0.097 | 0.111 | 10 |
| get_workflow_state | 0.067 | 0.070 | 0.081 | 10 |
| run_analysis | 0.058 | 0.061 | 0.065 | 10 |
| build_report | 0.043 | 0.047 | 0.056 | 10 |
| get_cleaning_ledger | 0.024 | 0.026 | 0.040 | 10 |
| confirm_dataset_contract | 0.031 | 0.033 | 0.039 | 10 |
| list_datasets | 0.020 | 0.021 | 0.024 | 10 |
| propose_ingest_spec | 0.005 | 0.005 | 0.006 | 10 |
| read_result_file | 0.001 | 0.001 | 0.001 | 10 |
| preview_file | 0.000 | 0.000 | 0.000 | 10 |
| check_file | 0.000 | 0.000 | 0.000 | 10 |

### 1,000,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| propose_cleaning_plan | 7.952 | 13.582 | 16.036 | 10 |
| compute_analysis:top_n | 0.097 | 0.262 | 8.125 | 82 |
| render_chart | 0.103 | 0.341 | 7.639 | 142 |
| profile_dataset | 3.749 | 5.040 | 6.929 | 10 |
| profile_column | 3.795 | 5.026 | 5.967 | 10 |
| apply_cleaning_plan | 3.040 | 4.222 | 5.906 | 10 |
| confirm_ingest_spec | 2.410 | 3.428 | 4.383 | 10 |
| compute_analysis:frequency | 0.122 | 0.185 | 2.731 | 30 |
| propose_dataset_contract | 0.936 | 1.576 | 2.725 | 20 |
| confirm_dataset_contract | 0.033 | 0.036 | 1.249 | 10 |
| compute_analysis:pareto | 0.112 | 0.149 | 1.048 | 22 |
| compute_analysis:concentration | 0.107 | 0.151 | 1.013 | 20 |
| compute_analysis:summary_stats | 0.372 | 0.534 | 0.729 | 10 |
| compute_analysis:cohort_retention | 0.344 | 0.415 | 0.519 | 10 |
| describe_dataset | 0.303 | 0.382 | 0.506 | 10 |
| compute_analysis:outlier_detection | 0.302 | 0.369 | 0.491 | 20 |
| compute_analysis:driver_analysis | 0.327 | 0.398 | 0.476 | 10 |
| compute_analysis:correlation | 0.096 | 0.341 | 0.421 | 28 |
| compute_analysis:repeat_behaviour | 0.267 | 0.333 | 0.374 | 11 |
| compute_analysis:distribution | 0.285 | 0.311 | 0.350 | 10 |
| compute_analysis:hypothesis_test | 0.141 | 0.184 | 0.347 | 40 |
| compute_analysis:mix_shift | 0.219 | 0.236 | 0.286 | 10 |
| compute_analysis:group_compare | 0.128 | 0.227 | 0.283 | 30 |
| compute_analysis:growth_decomposition | 0.100 | 0.232 | 0.266 | 11 |
| validate_dataset | 0.222 | 0.238 | 0.252 | 10 |
| compute_analysis:cross_tab | 0.168 | 0.205 | 0.236 | 20 |
| compute_analysis:confidence_interval | 0.150 | 0.175 | 0.234 | 20 |
| compute_analysis:bivariate | 0.168 | 0.197 | 0.221 | 10 |
| compute_analysis:effect_size | 0.133 | 0.169 | 0.219 | 30 |
| compute_analysis:sample_adequacy | 0.170 | 0.197 | 0.215 | 10 |
| compute_analysis:calendar_coverage | 0.153 | 0.173 | 0.211 | 10 |
| compute_analysis:correlated_shift | 0.154 | 0.169 | 0.207 | 10 |
| compute_analysis:trend | 0.091 | 0.172 | 0.196 | 24 |
| compute_analysis:period_compare | 0.150 | 0.166 | 0.193 | 10 |
| compute_analysis:ranking_shift | 0.140 | 0.166 | 0.192 | 10 |
| compute_analysis:changepoint | 0.153 | 0.165 | 0.189 | 10 |
| compute_analysis:seasonality | 0.154 | 0.169 | 0.183 | 10 |
| get_workflow_state | 0.090 | 0.101 | 0.119 | 10 |
| run_analysis | 0.085 | 0.092 | 0.107 | 10 |
| build_report | 0.043 | 0.052 | 0.057 | 10 |
| get_cleaning_ledger | 0.024 | 0.026 | 0.039 | 10 |
| list_datasets | 0.021 | 0.021 | 0.023 | 10 |
| propose_ingest_spec | 0.005 | 0.005 | 0.009 | 10 |
| read_result_file | 0.000 | 0.001 | 0.001 | 10 |
| preview_file | 0.000 | 0.000 | 0.000 | 10 |
| check_file | 0.000 | 0.000 | 0.000 | 10 |

### 2,000,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| propose_cleaning_plan | 28.993 | 29.500 | 30.007 | 2 |
| profile_dataset | 10.341 | 10.427 | 10.514 | 2 |
| profile_column | 9.545 | 9.872 | 10.199 | 2 |
| apply_cleaning_plan | 6.956 | 7.444 | 7.933 | 2 |
| confirm_ingest_spec | 6.815 | 7.223 | 7.631 | 2 |
| render_chart | 0.154 | 0.436 | 6.000 | 28 |
| propose_dataset_contract | 3.483 | 4.148 | 4.805 | 4 |
| compute_analysis:top_n | 0.147 | 0.487 | 3.251 | 17 |
| compute_analysis:frequency | 0.160 | 0.546 | 1.439 | 6 |
| compute_analysis:summary_stats | 0.617 | 0.778 | 0.939 | 2 |
| compute_analysis:driver_analysis | 0.780 | 0.781 | 0.782 | 2 |
| describe_dataset | 0.658 | 0.711 | 0.764 | 2 |
| compute_analysis:outlier_detection | 0.505 | 0.521 | 0.686 | 4 |
| compute_analysis:cohort_retention | 0.667 | 0.676 | 0.684 | 2 |
| compute_analysis:correlation | 0.140 | 0.600 | 0.682 | 6 |
| compute_analysis:distribution | 0.486 | 0.528 | 0.570 | 2 |
| compute_analysis:concentration | 0.175 | 0.234 | 0.562 | 4 |
| compute_analysis:pareto | 0.169 | 0.226 | 0.524 | 4 |
| compute_analysis:repeat_behaviour | 0.482 | 0.498 | 0.513 | 2 |
| compute_analysis:hypothesis_test | 0.193 | 0.263 | 0.475 | 8 |
| compute_analysis:group_compare | 0.203 | 0.385 | 0.465 | 6 |
| compute_analysis:mix_shift | 0.375 | 0.383 | 0.391 | 2 |
| compute_analysis:growth_decomposition | 0.372 | 0.378 | 0.384 | 2 |
| compute_analysis:cross_tab | 0.258 | 0.285 | 0.354 | 4 |
| compute_analysis:bivariate | 0.256 | 0.304 | 0.352 | 2 |
| validate_dataset | 0.341 | 0.347 | 0.352 | 2 |
| compute_analysis:correlated_shift | 0.237 | 0.254 | 0.272 | 2 |
| compute_analysis:effect_size | 0.191 | 0.247 | 0.271 | 6 |
| compute_analysis:seasonality | 0.228 | 0.249 | 0.269 | 2 |
| compute_analysis:changepoint | 0.236 | 0.251 | 0.267 | 2 |
| compute_analysis:sample_adequacy | 0.260 | 0.261 | 0.261 | 2 |
| compute_analysis:trend | 0.225 | 0.244 | 0.257 | 4 |
| compute_analysis:confidence_interval | 0.234 | 0.244 | 0.253 | 4 |
| compute_analysis:ranking_shift | 0.231 | 0.239 | 0.247 | 2 |
| compute_analysis:calendar_coverage | 0.232 | 0.238 | 0.243 | 2 |
| compute_analysis:period_compare | 0.230 | 0.235 | 0.240 | 2 |
| get_workflow_state | 0.138 | 0.140 | 0.142 | 2 |
| run_analysis | 0.132 | 0.136 | 0.140 | 2 |
| build_report | 0.043 | 0.043 | 0.043 | 2 |
| confirm_dataset_contract | 0.038 | 0.038 | 0.039 | 2 |
| get_cleaning_ledger | 0.026 | 0.026 | 0.026 | 2 |
| list_datasets | 0.023 | 0.024 | 0.025 | 2 |
| propose_ingest_spec | 0.005 | 0.005 | 0.006 | 2 |
| read_result_file | 0.000 | 0.001 | 0.001 | 2 |
| preview_file | 0.000 | 0.000 | 0.000 | 2 |
| check_file | 0.000 | 0.000 | 0.000 | 2 |

### 5,000,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| propose_cleaning_plan | 71.089 | 73.070 | 75.051 | 2 |
| profile_dataset | 25.200 | 26.462 | 27.724 | 2 |
| profile_column | 23.578 | 24.580 | 25.581 | 2 |
| propose_dataset_contract | 8.730 | 10.536 | 12.517 | 4 |
| confirm_ingest_spec | 9.416 | 10.560 | 11.704 | 2 |
| apply_cleaning_plan | 8.957 | 9.759 | 10.562 | 2 |
| compute_analysis:top_n | 0.286 | 1.143 | 8.474 | 17 |
| render_chart | 0.315 | 0.815 | 7.676 | 28 |
| compute_analysis:frequency | 0.338 | 1.006 | 3.135 | 6 |
| compute_analysis:summary_stats | 1.633 | 1.944 | 2.255 | 2 |
| compute_analysis:correlation | 0.273 | 1.614 | 1.814 | 6 |
| compute_analysis:driver_analysis | 1.600 | 1.686 | 1.772 | 2 |
| compute_analysis:cohort_retention | 1.663 | 1.666 | 1.668 | 2 |
| compute_analysis:outlier_detection | 1.188 | 1.264 | 1.633 | 4 |
| describe_dataset | 1.473 | 1.520 | 1.566 | 2 |
| compute_analysis:pareto | 0.315 | 0.527 | 1.397 | 4 |
| compute_analysis:distribution | 1.045 | 1.192 | 1.339 | 2 |
| compute_analysis:concentration | 0.319 | 0.515 | 1.325 | 4 |
| compute_analysis:repeat_behaviour | 1.298 | 1.309 | 1.320 | 2 |
| compute_analysis:hypothesis_test | 0.385 | 0.533 | 1.134 | 8 |
| compute_analysis:group_compare | 0.422 | 0.832 | 1.033 | 6 |
| compute_analysis:mix_shift | 0.795 | 0.831 | 0.867 | 2 |
| compute_analysis:growth_decomposition | 0.797 | 0.827 | 0.856 | 2 |
| compute_analysis:bivariate | 0.628 | 0.669 | 0.710 | 2 |
| validate_dataset | 0.701 | 0.704 | 0.707 | 2 |
| compute_analysis:cross_tab | 0.533 | 0.561 | 0.630 | 4 |
| compute_analysis:effect_size | 0.397 | 0.508 | 0.552 | 6 |
| compute_analysis:sample_adequacy | 0.501 | 0.514 | 0.527 | 2 |
| compute_analysis:confidence_interval | 0.448 | 0.512 | 0.527 | 4 |
| compute_analysis:correlated_shift | 0.491 | 0.505 | 0.519 | 2 |
| compute_analysis:changepoint | 0.446 | 0.475 | 0.504 | 2 |
| compute_analysis:trend | 0.472 | 0.477 | 0.500 | 4 |
| compute_analysis:seasonality | 0.483 | 0.485 | 0.486 | 2 |
| compute_analysis:calendar_coverage | 0.469 | 0.474 | 0.480 | 2 |
| compute_analysis:ranking_shift | 0.455 | 0.457 | 0.459 | 2 |
| compute_analysis:period_compare | 0.456 | 0.458 | 0.459 | 2 |
| get_workflow_state | 0.245 | 0.257 | 0.269 | 2 |
| run_analysis | 0.245 | 0.245 | 0.245 | 2 |
| confirm_dataset_contract | 0.049 | 0.049 | 0.050 | 2 |
| build_report | 0.045 | 0.045 | 0.046 | 2 |
| get_cleaning_ledger | 0.028 | 0.028 | 0.029 | 2 |
| list_datasets | 0.022 | 0.022 | 0.023 | 2 |
| propose_ingest_spec | 0.005 | 0.005 | 0.005 | 2 |
| read_result_file | 0.001 | 0.001 | 0.001 | 2 |
| preview_file | 0.000 | 0.000 | 0.000 | 2 |
| check_file | 0.000 | 0.000 | 0.000 | 2 |

### 10,000,000 rows: median seconds per call, across domains

| tool / analysis | fastest domain | median domain | slowest domain | groups |
|---|---|---|---|---|
| propose_cleaning_plan | 143.384 | 143.384 | 143.384 | 1 |
| profile_dataset | 52.176 | 52.176 | 52.176 | 1 |
| profile_column | 52.004 | 52.004 | 52.004 | 1 |
| propose_dataset_contract | 23.728 | 23.819 | 23.909 | 2 |
| apply_cleaning_plan | 21.964 | 21.964 | 21.964 | 1 |
| confirm_ingest_spec | 20.683 | 20.683 | 20.683 | 1 |
| render_chart | 0.556 | 1.392 | 6.491 | 14 |
| compute_analysis:top_n | 0.600 | 1.950 | 4.559 | 8 |
| compute_analysis:correlation | 0.511 | 2.930 | 3.481 | 3 |
| compute_analysis:driver_analysis | 3.287 | 3.287 | 3.287 | 1 |
| compute_analysis:summary_stats | 3.259 | 3.259 | 3.259 | 1 |
| compute_analysis:cohort_retention | 3.191 | 3.191 | 3.191 | 1 |
| compute_analysis:outlier_detection | 2.533 | 2.718 | 2.903 | 2 |
| compute_analysis:repeat_behaviour | 2.605 | 2.605 | 2.605 | 1 |
| describe_dataset | 2.562 | 2.562 | 2.562 | 1 |
| compute_analysis:frequency | 0.579 | 1.763 | 2.207 | 3 |
| compute_analysis:hypothesis_test | 0.631 | 0.930 | 2.111 | 4 |
| compute_analysis:distribution | 2.044 | 2.044 | 2.044 | 1 |
| compute_analysis:group_compare | 0.774 | 1.566 | 2.023 | 3 |
| compute_analysis:mix_shift | 1.536 | 1.536 | 1.536 | 1 |
| compute_analysis:growth_decomposition | 1.464 | 1.464 | 1.464 | 1 |
| validate_dataset | 1.353 | 1.353 | 1.353 | 1 |
| compute_analysis:pareto | 0.650 | 0.957 | 1.265 | 2 |
| compute_analysis:concentration | 0.676 | 0.955 | 1.234 | 2 |
| compute_analysis:bivariate | 1.126 | 1.126 | 1.126 | 1 |
| compute_analysis:effect_size | 0.663 | 0.953 | 1.001 | 3 |
| compute_analysis:confidence_interval | 0.922 | 0.959 | 0.995 | 2 |
| compute_analysis:sample_adequacy | 0.944 | 0.944 | 0.944 | 1 |
| compute_analysis:cross_tab | 0.923 | 0.931 | 0.939 | 2 |
| compute_analysis:correlated_shift | 0.933 | 0.933 | 0.933 | 1 |
| compute_analysis:period_compare | 0.900 | 0.900 | 0.900 | 1 |
| compute_analysis:trend | 0.865 | 0.868 | 0.870 | 2 |
| compute_analysis:changepoint | 0.869 | 0.869 | 0.869 | 1 |
| compute_analysis:seasonality | 0.834 | 0.834 | 0.834 | 1 |
| compute_analysis:calendar_coverage | 0.828 | 0.828 | 0.828 | 1 |
| compute_analysis:ranking_shift | 0.791 | 0.791 | 0.791 | 1 |
| run_analysis | 0.436 | 0.436 | 0.436 | 1 |
| get_workflow_state | 0.422 | 0.422 | 0.422 | 1 |
| confirm_dataset_contract | 0.065 | 0.065 | 0.065 | 1 |
| build_report | 0.047 | 0.047 | 0.047 | 1 |
| get_cleaning_ledger | 0.033 | 0.033 | 0.033 | 1 |
| list_datasets | 0.024 | 0.024 | 0.024 | 1 |
| propose_ingest_spec | 0.006 | 0.006 | 0.006 | 1 |
| read_result_file | 0.001 | 0.001 | 0.001 | 1 |
| preview_file | 0.000 | 0.000 | 0.000 | 1 |
| check_file | 0.000 | 0.000 | 0.000 | 1 |

### The same analysis across domains at 1,000,000 rows (median seconds)

| tool | financial | hr | sales | marketing | crm | ecommerce | logistics | healthcare | manufacturing | education |
|---|---|---|---|---|---|---|---|---|---|---|
| apply_cleaning_plan | 5.036 | 4.011 | 4.266 | 3.911 | 3.040 | 4.178 | 5.554 | 4.039 | 4.654 | 5.906 |
| build_report | 0.046 | 0.054 | 0.047 | 0.055 | 0.049 | 0.057 | 0.053 | 0.052 | 0.052 | 0.043 |
| check_file | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| compute_analysis:bivariate | 0.217 | 0.168 | 0.206 | 0.221 | 0.189 | 0.186 | 0.202 | 0.175 | 0.203 | 0.192 |
| compute_analysis:calendar_coverage | 0.190 | 0.156 | 0.173 | 0.157 | 0.180 | 0.153 | 0.156 | 0.176 | 0.211 | 0.173 |
| compute_analysis:changepoint | 0.189 | 0.183 | 0.172 | 0.162 | 0.167 | 0.164 | 0.153 | 0.159 | 0.166 | 0.155 |
| compute_analysis:cohort_retention | 0.429 | 0.419 | 0.410 | 0.344 | 0.519 | 0.423 | 0.406 | 0.383 | 0.360 | 0.463 |
| compute_analysis:concentration | 0.159 | 0.131 | 0.107 | 0.145 | 0.147 | 0.120 | 0.133 | 0.125 | 0.134 | 0.136 |
| compute_analysis:confidence_interval | 0.227 | 0.171 | 0.189 | 0.150 | 0.183 | 0.166 | 0.167 | 0.172 | 0.150 | 0.158 |
| compute_analysis:correlated_shift | 0.207 | 0.166 | 0.158 | 0.159 | 0.170 | 0.180 | 0.168 | 0.154 | 0.181 | 0.182 |
| compute_analysis:correlation | 0.372 | 0.279 | 0.355 | 0.370 | 0.336 | 0.341 | 0.313 | 0.421 | 0.341 | 0.363 |
| compute_analysis:cross_tab | 0.219 | 0.221 | 0.203 | 0.194 | 0.206 | 0.222 | 0.168 | 0.185 | 0.182 | 0.221 |
| compute_analysis:distribution | 0.350 | 0.293 | 0.320 | 0.320 | 0.350 | 0.302 | 0.285 | 0.347 | 0.303 | 0.302 |
| compute_analysis:driver_analysis | 0.476 | 0.418 | 0.414 | 0.351 | 0.333 | 0.448 | 0.442 | 0.368 | 0.327 | 0.381 |
| compute_analysis:effect_size | 0.219 | 0.161 | 0.166 | 0.171 | 0.189 | 0.168 | 0.163 | 0.187 | 0.197 | 0.181 |
| compute_analysis:frequency | 0.167 | 0.129 | 0.130 | 0.155 | 0.123 | 0.137 | 0.128 | 0.122 | 0.140 | 0.129 |
| compute_analysis:group_compare | 0.274 | 0.283 | 0.266 | 0.280 | 0.233 | 0.271 | 0.221 | 0.260 | 0.208 | 0.222 |
| compute_analysis:growth_decomposition | 0.253 | 0.224 | 0.223 | 0.249 | 0.219 | 0.266 | 0.227 | 0.255 | 0.232 | 0.243 |
| compute_analysis:hypothesis_test | 0.224 | 0.173 | 0.187 | 0.168 | 0.178 | 0.175 | 0.200 | 0.162 | 0.193 | 0.184 |
| compute_analysis:mix_shift | 0.286 | 0.223 | 0.254 | 0.235 | 0.257 | 0.237 | 0.230 | 0.225 | 0.253 | 0.219 |
| compute_analysis:outlier_detection | 0.418 | 0.347 | 0.388 | 0.385 | 0.371 | 0.326 | 0.302 | 0.360 | 0.491 | 0.330 |
| compute_analysis:pareto | 0.150 | 0.131 | 0.112 | 0.137 | 0.147 | 0.121 | 0.140 | 0.123 | 0.139 | 0.142 |
| compute_analysis:period_compare | 0.193 | 0.161 | 0.170 | 0.183 | 0.150 | 0.163 | 0.166 | 0.165 | 0.169 | 0.166 |
| compute_analysis:ranking_shift | 0.187 | 0.166 | 0.158 | 0.192 | 0.169 | 0.160 | 0.150 | 0.140 | 0.166 | 0.165 |
| compute_analysis:repeat_behaviour | 0.374 | 0.284 | 0.351 | 0.290 | 0.340 | 0.296 | 0.335 | 0.333 | 0.339 | 0.301 |
| compute_analysis:sample_adequacy | 0.215 | 0.170 | 0.193 | 0.202 | 0.213 | 0.175 | 0.191 | 0.177 | 0.202 | 0.201 |
| compute_analysis:seasonality | 0.183 | 0.171 | 0.160 | 0.154 | 0.171 | 0.162 | 0.165 | 0.167 | 0.171 | 0.176 |
| compute_analysis:summary_stats | 0.729 | 0.619 | 0.549 | 0.694 | 0.459 | 0.445 | 0.372 | 0.485 | 0.571 | 0.520 |
| compute_analysis:top_n | 0.144 | 0.140 | 0.137 | 0.140 | 0.126 | 0.132 | 0.134 | 0.149 | 0.146 | 0.126 |
| compute_analysis:trend | 0.196 | 0.186 | 0.153 | 0.166 | 0.173 | 0.184 | 0.162 | 0.176 | 0.181 | 0.174 |
| confirm_dataset_contract | 1.249 | 0.037 | 0.034 | 0.046 | 0.033 | 0.034 | 0.052 | 0.036 | 0.036 | 0.034 |
| confirm_ingest_spec | 4.383 | 2.769 | 3.720 | 3.385 | 2.572 | 3.733 | 4.035 | 3.472 | 2.965 | 2.410 |
| describe_dataset | 0.506 | 0.345 | 0.377 | 0.390 | 0.303 | 0.389 | 0.420 | 0.342 | 0.363 | 0.386 |
| get_cleaning_ledger | 0.026 | 0.025 | 0.039 | 0.027 | 0.027 | 0.026 | 0.025 | 0.026 | 0.024 | 0.027 |
| get_workflow_state | 0.094 | 0.092 | 0.092 | 0.115 | 0.119 | 0.111 | 0.107 | 0.109 | 0.090 | 0.095 |
| list_datasets | 0.021 | 0.021 | 0.022 | 0.022 | 0.021 | 0.021 | 0.023 | 0.023 | 0.022 | 0.021 |
| preview_file | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| profile_column | 5.967 | 5.025 | 4.817 | 5.028 | 3.795 | 4.444 | 5.339 | 4.057 | 5.239 | 5.233 |
| profile_dataset | 6.929 | 4.985 | 5.583 | 5.019 | 3.749 | 4.298 | 5.375 | 3.976 | 5.285 | 5.061 |
| propose_cleaning_plan | 16.036 | 12.135 | 15.707 | 10.403 | 7.952 | 15.719 | 15.319 | 10.532 | 12.505 | 14.659 |
| propose_dataset_contract | 2.272 | 1.389 | 1.990 | 1.169 | 0.971 | 2.297 | 2.725 | 1.409 | 1.626 | 1.525 |
| propose_ingest_spec | 0.005 | 0.006 | 0.009 | 0.005 | 0.006 | 0.006 | 0.005 | 0.005 | 0.005 | 0.005 |
| read_result_file | 0.001 | 0.000 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| render_chart:cohort_retention | - | - | - | - | - | - | - | - | - | - |
| render_chart:correlation | - | - | - | - | - | - | - | - | - | - |
| render_chart:cross_tab | - | - | - | - | - | - | - | - | - | - |
| render_chart:distribution | - | - | - | - | - | - | - | - | - | - |
| render_chart:frequency | - | - | - | - | - | - | - | - | - | - |
| render_chart:group_compare | - | - | - | - | - | - | - | - | - | - |
| render_chart:mix_shift | - | - | - | - | - | - | - | - | - | - |
| render_chart:top_n | - | - | - | - | - | - | - | - | - | - |
| render_chart:trend | - | - | - | - | - | - | - | - | - | - |
| run_analysis | 0.093 | 0.085 | 0.090 | 0.107 | 0.102 | 0.104 | 0.089 | 0.087 | 0.100 | 0.091 |
| validate_dataset | 0.233 | 0.234 | 0.222 | 0.238 | 0.252 | 0.250 | 0.243 | 0.237 | 0.222 | 0.243 |

### profile_column at 1,000,000 rows by column type (seconds)

| column type | calls | median | max |
|---|---|---|---|
| bool | 14 | 4.983 | 5.959 |
| date | 19 | 4.888 | 6.113 |
| float | 58 | 5.138 | 6.046 |
| int | 21 | 4.946 | 5.322 |
| str | 88 | 5.134 | 6.515 |
| ts | 3 | 4.706 | 6.018 |

Slowest columns:

| domain | column | seconds |
|---|---|---|
| financial | record_id | 6.515 |
| financial | account_id | 6.499 |
| financial | transaction_id | 6.189 |
| financial | transaction_date | 6.113 |
| financial | category | 6.068 |
| financial | customer_id | 6.049 |
| financial | credit | 6.046 |
| financial | branch | 6.040 |
| financial | posted_at | 6.018 |
| financial | fiscal_period | 5.988 |

## Scaling

Median time growth over every tool and analysis measured at both sizes:

| rows | data growth | median time growth |
|---|---|---|
| 1000->100000 | 100.000 | 1.477 |
| 100000->1000000 | 10.000 | 1.804 |
| 1000000->2000000 | 2.000 | 1.518 |
| 2000000->5000000 | 2.500 | 2.055 |
| 5000000->10000000 | 2.000 | 1.813 |

Ten worst scaling (time growth relative to data growth):

| domain | tool | analysis | rows | data x | time x | s before | s after |
|---|---|---|---|---|---|---|---|
| financial | confirm_dataset_contract |   | 100,000->1,000,000 | 10.000 | 37.571 | 0.033 | 1.249 |
| logistics | compute_analysis | frequency for_paging | 1,000,000->2,000,000 | 2.000 | 3.438 | 0.199 | 0.683 |
| logistics | compute_analysis | top_n n10 | 1,000,000->2,000,000 | 2.000 | 2.352 | 0.207 | 0.487 |
| logistics | compute_analysis | top_n n1000 | 1,000,000->2,000,000 | 2.000 | 2.337 | 0.216 | 0.504 |
| logistics | compute_analysis | correlation indep | 2,000,000->5,000,000 | 2.500 | 2.903 | 0.625 | 1.814 |
| sales | compute_analysis | top_n n1000 | 1,000,000->2,000,000 | 2.000 | 2.306 | 0.535 | 1.233 |
| logistics | compute_analysis | group_compare mean | 5,000,000->10,000,000 | 2.000 | 2.243 | 0.902 | 2.023 |
| logistics | compute_analysis | correlation  | 2,000,000->5,000,000 | 2.500 | 2.772 | 0.576 | 1.596 |
| logistics | confirm_ingest_spec |   | 5,000,000->10,000,000 | 2.000 | 2.197 | 9.416 | 20.683 |
| logistics | compute_analysis | outlier_detection mean | 5,000,000->10,000,000 | 2.000 | 2.192 | 1.325 | 2.903 |

## Memory

- 1,000 rows: worker peak RSS median 355 MiB, max 365 MiB over 10 worker run(s)
- 100,000 rows: worker peak RSS median 503 MiB, max 568 MiB over 10 worker run(s)
- 1,000,000 rows: worker peak RSS median 1,118 MiB, max 1,413 MiB over 10 worker run(s)
- 2,000,000 rows: worker peak RSS median 1,518 MiB, max 1,697 MiB over 2 worker run(s)
- 5,000,000 rows: worker peak RSS median 2,349 MiB, max 2,512 MiB over 2 worker run(s)
- 10,000,000 rows: worker peak RSS median 3,627 MiB, max 3,627 MiB over 1 worker run(s)

RSS growth from the first to the last call of a worker (accumulation):

| unit | calls | first MiB | last MiB | max MiB | growth MiB |
|---|---|---|---|---|---|
| D_hr | 376 | 246.580 | 503.130 | 519.020 | 256.550 |
| I_logistics_10000000 | 199 | 246.660 | 501.850 | 510.830 | 255.190 |
| I_sales_5000000 | 197 | 246.570 | 499.340 | 511.080 | 252.770 |
| D_manufacturing | 363 | 246.490 | 497.090 | 498.120 | 250.600 |
| I_logistics_5000000 | 199 | 246.660 | 494.910 | 505.440 | 248.250 |
| D_education | 363 | 246.410 | 488.610 | 491.480 | 242.200 |
| I_sales_2000000 | 197 | 246.550 | 467.250 | 478.880 | 220.700 |
| I_logistics_2000000 | 199 | 246.620 | 462.900 | 477.710 | 216.280 |
| E_healthcare | 319 | 246.520 | 450.750 | 452.370 | 204.230 |
| E_logistics | 323 | 246.570 | 443.940 | 458.710 | 197.370 |

Python-tracked allocations (tracemalloc, repeated mixed analyses): peak per call min 0.08 MiB, max 1.13 MiB over 64 calls.

## Errors

| severity | tool | what | count |
|---|---|---|---|
| CRITICAL | compute_analysis | wrong_result | 16 |
| CRITICAL | charts | {"dataset": "financial", "names_its_meas | 1 |
| CRITICAL | charts | {"dataset": "hr", "names_its_measure": f | 1 |
| CRITICAL | charts | {"dataset": "sales", "names_its_measure" | 1 |
| CRITICAL | charts | {"dataset": "marketing", "names_its_meas | 1 |
| CRITICAL | charts | {"dataset": "crm", "names_its_measure":  | 1 |
| CRITICAL | charts | {"dataset": "ecommerce", "names_its_meas | 1 |
| CRITICAL | charts | {"dataset": "logistics", "names_its_meas | 1 |
| CRITICAL | charts | {"dataset": "healthcare", "names_its_mea | 1 |
| CRITICAL | charts | {"dataset": "manufacturing", "names_its_ | 1 |
| CRITICAL | charts | {"dataset": "education", "names_its_meas | 1 |
| HIGH | read_result_file | 50 found | 26 |
| HIGH | compute_analysis | FAIL_EXCEPTION:  | 8 |
| HIGH | compute_analysis | BinderException: Binder Error: No functi | 7 |
| HIGH | compute_analysis | OutOfRangeException: Out of Range Error: | 2 |
| HIGH | propose_cleaning_plan | dangerous: removes 18 exact duplicate(s) | 2 |
| HIGH | compute_analysis | ZeroDivisionError: both groups have zero | 1 |
| HIGH | compute_analysis | TransactionException: TransactionContext | 1 |
| HIGH | propose_cleaning_plan | dangerous: removes 3 exact duplicate(s); | 1 |
| HIGH | propose_cleaning_plan | dangerous: removes 6 exact duplicate(s); | 1 |
| MEDIUM | compute_analysis | FAIL_MISLEADING_RESPONSE: BLOCKED: analy | 18 |
| MEDIUM | compute_analysis | oracle_error | 12 |
| MEDIUM | render_chart | FAIL_MISLEADING_RESPONSE: BLOCKED: analy | 1 |
| MEDIUM | compute_analysis | FAIL_UNNECESSARY_REJECTION: BLOCKED: ana | 1 |

## Crashes

| # | domain | rows | tool | analysis | exception |
|---|---|---|---|---|---|
| 1 | - | 0 | compute_analysis | hypothesis_test | ZeroDivisionError: both groups have zero variance |
| 2 | - | 0 | compute_analysis | summary_stats | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 3 | - | 0 | compute_analysis | outlier_detection | BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, D |
| 4 | - | 0 | compute_analysis | trend | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 5 | - | 0 | compute_analysis | correlation | BinderException: Binder Error: No function matches the given name and argument types 'corr(BIGINT, VARCHAR)'.  |
| 6 | - | 0 | compute_analysis | summary_stats | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 7 | - | 0 | compute_analysis | outlier_detection | BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, D |
| 8 | - | 0 | compute_analysis | trend | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 9 | - | 0 | compute_analysis | top_n | TransactionException: TransactionContext Error: Catalog write-write conflict on create with "Schema\0main\0mai |
| 10 | sales | 5,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)! |
| 11 | sales | 5,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)! |
| 40 | - | 0 | compute_analysis | hypothesis_test | FAIL_EXCEPTION:  |
| 58 | - | 0 | compute_analysis | summary_stats | FAIL_EXCEPTION:  |
| 59 | - | 0 | compute_analysis | outlier_detection | FAIL_EXCEPTION:  |
| 60 | - | 0 | compute_analysis | trend | FAIL_EXCEPTION:  |
| 61 | - | 0 | compute_analysis | correlation | FAIL_EXCEPTION:  |
| 62 | - | 0 | compute_analysis | summary_stats | FAIL_EXCEPTION:  |
| 63 | - | 0 | compute_analysis | outlier_detection | FAIL_EXCEPTION:  |
| 64 | - | 0 | compute_analysis | trend | FAIL_EXCEPTION:  |

## Warnings

| category | count |
|---|---|
| slow_call | 885 |
| questionable_or_unverified_result | 139 |
| irrelevant_or_unexecutable_recommendation | 64 |
| suspicious_scaling | 37 |
| excessive_response_size | 25 |
| unsupported_operation | 16 |

## Behaviour under wrong and edge calls

| classification | calls |
|---|---|
| FAIL_EXCEPTION | 8 |
| FAIL_MISLEADING_RESPONSE | 19 |
| FAIL_UNNECESSARY_REJECTION | 1 |
| PASS_ACCEPTED | 25 |
| PASS_AUTOCORRECTED | 54 |
| PASS_SAFE_REJECTION | 147 |
| PASS_USEFUL_WARNING | 18 |

By family:

| family | classes |
|---|---|
| file_format | PASS_SAFE_REJECTION 10, PASS_AUTOCORRECTED 4, PASS_ACCEPTED 3 |
| not_applicable | PASS_SAFE_REJECTION 56, PASS_AUTOCORRECTED 2 |
| other | PASS_SAFE_REJECTION 35, PASS_ACCEPTED 8, PASS_AUTOCORRECTED 6, PASS_USEFUL_WARNING 6 |
| statistical | PASS_USEFUL_WARNING 6, PASS_ACCEPTED 6, PASS_AUTOCORRECTED 2, FAIL_EXCEPTION 1, PASS_SAFE_REJECTION 1 |
| temporal | PASS_AUTOCORRECTED 26, PASS_ACCEPTED 4, PASS_USEFUL_WARNING 3 |
| wrong_call | PASS_SAFE_REJECTION 45, FAIL_MISLEADING_RESPONSE 19, PASS_AUTOCORRECTED 14, FAIL_EXCEPTION 7, PASS_ACCEPTED 4, PASS_USEFUL_WARNING 3, FAIL_UNNECESSARY_REJECTION 1 |

Refusal message quality over 167 refusals: identifies the problem 167, names the parameter 28 (of 47 with a named parameter), explains what was expected 80, suggests a correction 167; NEXT STEP followed: WORKED 111, not followed 33, NOT_EXECUTED 22, REFUSED_SAME_REASON 1

## Charts

| verdict | count |
|---|---|
| PASS | 1,118 |
| REFUSED | 354 |

## Cleaning plans

| verdict | actions |
|---|---|
| valid | 40 |
| unnecessary | 4 |
| dangerous | 4 |
- dirty variant format_noise: expected accept; actions 7; injected defects with no action: risk score %
- dirty variant bad_dates: expected warn; actions 1; injected defects with no action: none
- dirty variant duplicate_columns: expected either; actions 1; injected defects with no action: none
- dirty variant missing_header: expected warn; actions 0; injected defects with no action: none
- dirty variant reordered_extra: expected accept; actions 1; injected defects with no action: none

## Concurrency and state isolation

- separate x2: statuses {'REFUSED': 2}; distinct result files 0 of 0
- shared x2: statuses {'EXCEPTION': 1, 'REFUSED': 1}; distinct result files 0 of 0
- separate x5: statuses {'REFUSED': 5}; distinct result files 0 of 0
- shared x5: statuses {'REFUSED': 5}; distinct result files 0 of 0
- separate x10: statuses {'REFUSED': 10}; distinct result files 0 of 0
- shared x10: statuses {'REFUSED': 10}; distinct result files 0 of 0
- same_dataset x10: statuses {'REFUSED': 10}; distinct result files 0 of 0
- isolation reports: 10 of 10 pass
- isolation ledgers: 10 of 10 pass
- isolation charts: 0 of 10 pass
- isolation correctness: 0 of 0 verified calls pass

## Reproducibility

| domain | rows | dataset identical | results identical | differ | status |
|---|---|---|---|---|---|
| financial | 1,000 | True | 0 | 0 | PASS |
| financial | 100,000 | True | 0 | 0 | PASS |
| crm | 1,000 | True | 0 | 0 | PASS |
| crm | 100,000 | True | 0 | 0 | PASS |
| logistics | 1,000 | True | 0 | 0 | PASS |
| logistics | 100,000 | True | 0 | 0 | PASS |

## Domain observations

### Financial

- 1,000 rows: 3,640 of 3,640 checks pass, 0 fail
- 100,000 rows: 66,567 of 66,567 checks pass, 0 fail
- 1,000,000 rows: 601,543 of 601,543 checks pass, 0 fail
- errors: 3 (HIGH 2, CRITICAL 1)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "financial", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  16.04s; profile_dataset  6.93s; profile_column  5.97s

### HR

- 1,000 rows: 2,885 of 2,885 checks pass, 0 fail
- 100,000 rows: 37,716 of 37,717 checks pass, 1 fail
- 1,000,000 rows: 308,239 of 308,240 checks pass, 1 fail
- errors: 6 (CRITICAL 3, HIGH 2, MEDIUM 1)
  - CRITICAL compute_analysis hypothesis_test 100000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.7679, df 1.847e+04, p 0.442539. (1 of 1 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.4665, df 1.874e+05, p 0.640887. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "hr", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  12.13s; profile_column  5.02s; profile_dataset  4.99s
- refused although classed REQUIRED/VALID/EDGE: pareto (VALID), concentration (VALID), repeat_behaviour (EDGE_CASE), cohort_retention (EDGE_CASE)

### Sales

- 1,000 rows: 3,372 of 3,372 checks pass, 0 fail
- 100,000 rows: 66,466 of 66,466 checks pass, 0 fail
- 1,000,000 rows: 602,526 of 602,527 checks pass, 1 fail
- 2,000,000 rows: 63 of 63 checks pass, 0 fail
- 5,000,000 rows: 63 of 63 checks pass, 0 fail
- errors: 10 (HIGH 6, MEDIUM 2, CRITICAL 2)
  - HIGH compute_analysis hypothesis_test 5000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)!
  - HIGH compute_analysis hypothesis_test 5000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)!
  - MEDIUM compute_analysis sample_adequacy 100000: None (0 of 0 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.2691, df 5.366e+04, p 0.787831. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - HIGH read_result_file  2000000: 50 found
- slowest at 1M rows: propose_cleaning_plan  15.71s; profile_dataset  5.58s; render_chart top_n 5.01s
- refused although classed REQUIRED/VALID/EDGE: pareto (REQUIRED), concentration (REQUIRED)

### Marketing

- 1,000 rows: 1,490 of 1,490 checks pass, 0 fail
- 100,000 rows: 14,293 of 14,294 checks pass, 1 fail
- 1,000,000 rows: 81,832 of 81,833 checks pass, 1 fail
- errors: 6 (CRITICAL 3, HIGH 2, MEDIUM 1)
  - CRITICAL compute_analysis hypothesis_test 100000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -0.7413, df 5.555e+04, p 0.458505. (1 of 1 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.1435, df 5.591e+05, p 0.885919. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "marketing", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  10.40s; profile_column  5.03s; profile_dataset  5.02s

### CRM

- 1,000 rows: 9,524 of 9,524 checks pass, 0 fail
- 100,000 rows: 301,390 of 301,391 checks pass, 1 fail
- 1,000,000 rows: 2,954,833 of 2,954,834 checks pass, 1 fail
- errors: 7 (CRITICAL 3, HIGH 3, MEDIUM 1)
  - CRITICAL compute_analysis hypothesis_test 100000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 15.2604, df 1.569e+04, p 3.33014e-52. (1 of 1 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 43.8571, df 1.594e+05, p < 1e-300. (1 of 1 checks failed)
  - MEDIUM compute_analysis hypothesis_test 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  1000: 50 found
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "crm", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: compute_analysis top_n 8.13s; propose_cleaning_plan  7.95s; render_chart top_n 7.64s

### E-commerce

- 1,000 rows: 3,538 of 3,539 checks pass, 1 fail
- 100,000 rows: 66,581 of 66,581 checks pass, 0 fail
- 1,000,000 rows: 602,568 of 602,569 checks pass, 1 fail
- errors: 6 (CRITICAL 3, HIGH 2, MEDIUM 1)
  - CRITICAL compute_analysis sample_adequacy 1000: 0.4206 (1 of 2 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.1578, df 4.675e+04, p 0.874595. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "ecommerce", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  15.72s; render_chart top_n 5.56s; profile_column  4.44s

### Logistics

- 1,000 rows: 1,690 of 1,690 checks pass, 0 fail
- 100,000 rows: 21,989 of 21,989 checks pass, 0 fail
- 1,000,000 rows: 156,971 of 156,971 checks pass, 0 fail
- 2,000,000 rows: 61 of 61 checks pass, 0 fail
- 5,000,000 rows: 61 of 61 checks pass, 0 fail
- 10,000,000 rows: 61 of 61 checks pass, 0 fail
- errors: 9 (HIGH 5, MEDIUM 3, CRITICAL 1)
  - MEDIUM compute_analysis hypothesis_test 1000000: None (0 of 0 checks failed)
  - MEDIUM compute_analysis hypothesis_test 1000000: None (0 of 0 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - HIGH read_result_file  10000000: 50 found
  - HIGH read_result_file  2000000: 50 found
  - HIGH read_result_file  5000000: 50 found
- slowest at 1M rows: propose_cleaning_plan  15.32s; apply_cleaning_plan  5.55s; profile_dataset  5.37s

### Healthcare (synthetic)

- 1,000 rows: 1,678 of 1,678 checks pass, 0 fail
- 100,000 rows: 10,164 of 10,165 checks pass, 1 fail
- 1,000,000 rows: 37,156 of 37,157 checks pass, 1 fail
- errors: 6 (CRITICAL 3, HIGH 2, MEDIUM 1)
  - CRITICAL compute_analysis hypothesis_test 100000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -23.859, df 9.686e+04, p 1.88274e-125. (1 of 1 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -78.4531, df 9.637e+05, p < 1e-300. (1 of 1 checks failed)
  - MEDIUM compute_analysis hypothesis_test 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "healthcare", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  10.53s; render_chart top_n 4.83s; profile_column  4.06s

### Manufacturing

- 1,000 rows: 1,516 of 1,522 checks pass, 6 fail
- 100,000 rows: 14,304 of 14,312 checks pass, 8 fail
- 1,000,000 rows: 81,824 of 81,825 checks pass, 1 fail
- errors: 6 (CRITICAL 4, HIGH 2)
  - CRITICAL compute_analysis distribution 1000: 211 (6 of 13 checks failed)
  - CRITICAL compute_analysis distribution 100000: 32,771 (8 of 13 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -1.0274, df 9.334e+04, p 0.304252. (1 of 1 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "manufacturing", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  12.50s; profile_dataset  5.28s; profile_column  5.24s

### Education

- 1,000 rows: 2,148 of 2,148 checks pass, 0 fail
- 100,000 rows: 15,566 of 15,567 checks pass, 1 fail
- 1,000,000 rows: 83,067 of 83,068 checks pass, 1 fail
- errors: 7 (CRITICAL 3, MEDIUM 2, HIGH 2)
  - CRITICAL compute_analysis hypothesis_test 100000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic -1.8539, df 2.634e+04, p 0.0637616. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 100000: None (0 of 0 checks failed)
  - CRITICAL compute_analysis hypothesis_test 1000000:   - Test: Welch's unequal-variance t-test (two-sided). Statistic 0.2756, df 2.603e+05, p 0.782847. (1 of 1 checks failed)
  - MEDIUM compute_analysis sample_adequacy 1000000: None (0 of 0 checks failed)
  - HIGH read_result_file  100000: 50 found
  - HIGH read_result_file  1000000: 50 found
  - CRITICAL charts  10000: {"dataset": "education", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- slowest at 1M rows: propose_cleaning_plan  14.66s; apply_cleaning_plan  5.91s; profile_column  5.23s

## Bottlenecks (measured)

Ten slowest calls:

| seconds | tool | analysis | domain | rows |
|---|---|---|---|---|
| 330.789 | propose_ingest_spec |  | - | 0 |
| 143.384 | propose_cleaning_plan |  | logistics | 10,000,000 |
| 142.383 | propose_cleaning_plan |  | logistics | 10,000,000 |
| 75.051 | propose_cleaning_plan |  | sales | 5,000,000 |
| 74.077 | propose_cleaning_plan |  | sales | 5,000,000 |
| 71.161 | propose_cleaning_plan |  | logistics | 5,000,000 |
| 71.089 | propose_cleaning_plan |  | logistics | 5,000,000 |
| 54.918 | profile_column |  | logistics | 10,000,000 |
| 54.890 | profile_dataset |  | logistics | 10,000,000 |
| 54.873 | profile_column |  | logistics | 10,000,000 |

Ten largest responses:

| characters | tool | analysis | domain | rows |
|---|---|---|---|---|
| 26,542 | preview_file |  | - | 0 |
| 11,033 | render_chart | cohort_retention | hr | 1,000,000 |
| 11,033 | render_chart | cohort_retention | hr | 1,000,000 |
| 11,033 | render_chart | cohort_retention | hr | 1,000,000 |
| 11,033 | render_chart | cohort_retention | hr | 1,000,000 |
| 11,019 | render_chart | cohort_retention | education | 1,000,000 |
| 11,019 | render_chart | cohort_retention | education | 1,000,000 |
| 11,019 | render_chart | cohort_retention | education | 1,000,000 |
| 11,019 | render_chart | cohort_retention | education | 1,000,000 |
| 10,694 | render_chart | cohort_retention | education | 100,000 |

Ten largest per-call memory peaks:

| peak MiB | tool | analysis | unit | rows |
|---|---|---|---|---|
| 3,627.240 | apply_cleaning_plan |  | I_logistics_10000000 | 10,000,000 |
| 3,199.510 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,193.140 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,170.120 | propose_cleaning_plan |  | I_logistics_10000000 | 10,000,000 |
| 3,164.970 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,159.280 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,154.540 | propose_cleaning_plan |  | I_logistics_10000000 | 10,000,000 |
| 3,138.650 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,125.180 | profile_column |  | I_logistics_10000000 | 10,000,000 |
| 3,102.790 | profile_column |  | I_logistics_10000000 | 10,000,000 |

Tools with most errors: compute_analysis 66, read_result_file 26, charts 10, propose_cleaning_plan 4, render_chart 1
Domains with most errors: None 41, sales 10, logistics 9, crm 7, education 7, ecommerce 6, manufacturing 6, healthcare 6
Tools with most warnings: profile_column 610, compute_analysis 91, render_chart 82, propose_cleaning_plan 66, profile_dataset 42, propose_dataset_contract 32, confirm_ingest_spec 16, apply_cleaning_plan 16

## Regression candidates

Every case below failed or guards a property the benchmark measured; each is small enough to run in the suite:

- [CRITICAL] compute_analysis sample_adequacy (analyses): 0.4206 (1 of 2 checks failed)
- [CRITICAL] compute_analysis distribution (analyses): 211 (6 of 13 checks failed)
- [CRITICAL] compute_analysis hypothesis_test (analyses):   - Test: Welch's unequal-variance t-test (two-sided). Statistic 15.2604, df 1.569e+04, p 3.33014e-52. (1 of 1 checks fa
- [CRITICAL] charts  (isolation): {"dataset": "financial", "names_its_measure": false, "names_another_dataset": [], "status": "FAIL"}
- [HIGH] compute_analysis hypothesis_test (stat_edges): ZeroDivisionError: both groups have zero variance
- [HIGH] compute_analysis summary_stats (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might need to a
- [HIGH] compute_analysis outlier_detection (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, DECIMAL(3,2
- [HIGH] compute_analysis trend (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might need to a
- [HIGH] compute_analysis correlation (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'corr(BIGINT, VARCHAR)'. You might 
- [HIGH] compute_analysis top_n (concurrency): TransactionException: TransactionContext Error: Catalog write-write conflict on create with "Schema\0main\0main\0Table\0
- [HIGH] compute_analysis hypothesis_test (analyses): OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)!
- [HIGH] compute_analysis hypothesis_test (zero_variance_t): FAIL_EXCEPTION: 
- [HIGH] compute_analysis summary_stats (t_all_null_col_summary): FAIL_EXCEPTION: 
- [HIGH] compute_analysis outlier_detection (t_all_null_col_outliers): FAIL_EXCEPTION: 
- [HIGH] compute_analysis trend (t_all_null_col_trend): FAIL_EXCEPTION: 
- [HIGH] compute_analysis correlation (t_all_null_col_corr): FAIL_EXCEPTION: 
- [HIGH] compute_analysis summary_stats (t_inf_nan_summary): FAIL_EXCEPTION: 
- [HIGH] compute_analysis outlier_detection (t_inf_nan_outliers): FAIL_EXCEPTION: 
- [HIGH] compute_analysis trend (t_inf_nan_trend): FAIL_EXCEPTION: 
- [HIGH] read_result_file  (read_result): 50 found
- [HIGH] propose_cleaning_plan  (clean): dangerous: removes 3 exact duplicate(s); the generator inserted 0 -- keep one of each of the 3 exactly duplicated row(s)
- [MEDIUM] compute_analysis sample_adequacy (analyses): None (0 of 0 checks failed)
- [MEDIUM] compute_analysis hypothesis_test (analyses): None (0 of 0 checks failed)
- [MEDIUM] compute_analysis top_n (nonexistent_column): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis top_n (misspelled_column): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis distribution (wrong_type_measure): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis top_n (empty_parameter): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis top_n (null_parameter): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis trend (incorrect_enum): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis ranking_shift (invalid_date_range): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis ranking_shift (start_after_end): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis group_compare (groupby_id): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis correlation (corr_same_column): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis hypothesis_test (invalid_stat_group): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis distribution (bins_zero): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis confidence_interval (confidence_out_of_range): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis hypothesis_test (unknown_method): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis regression (unknown_analysis): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis period_compare (period_outside_window): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] render_chart  (chart_unsupported): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'adv' requires a confirmed Dataset Contract. None exists.
WHY: without on
- [MEDIUM] compute_analysis summary_stats (t_dup_ids_summary): FAIL_UNNECESSARY_REJECTION: BLOCKED: analysis of 'dup_ids' requires a confirmed Dataset Contract. None exists.
WHY: with
- [MEDIUM] compute_analysis confidence_interval (t_dup_ids_ci): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'dup_ids' requires a confirmed Dataset Contract. None exists.
WHY: withou
- [MEDIUM] compute_analysis correlation (t_dup_ids_corr): FAIL_MISLEADING_RESPONSE: BLOCKED: analysis of 'dup_ids' requires a confirmed Dataset Contract. None exists.
WHY: withou
- [guard] the known-answer fixture (perfect +1/-1/0 correlation, arithmetic trend, changepoint, 80/20 Pareto, ranking, retention grid, identical and separated groups, imbalance, 10% missing, 4 duplicates)
- [guard] sorted vs shuffled input gives identical tables for every temporal analysis

## Final technical findings

Generated from the figures above; what they mean is discussed in docs/steps/phase14_step13_domain_benchmark.md.

- Correctness: 6,157,385 of 6,157,413 independent checks passed; 28 failed (hypothesis_test 13, distribution 2, sample_adequacy 1).
- Defects: CRITICAL 26, HIGH 49, MEDIUM 32, LOW 0.
- Largest dataset processed to completion on this machine: 10,000,000 rows
- Stress tiers skipped for resources: I_sales_10000000 (needed ~16227 MiB, had 14563 MiB)
- Median time growth 100k -> 1M: 1.80x for 10x rows.
- Peak worker memory: 3627.2 MiB.

