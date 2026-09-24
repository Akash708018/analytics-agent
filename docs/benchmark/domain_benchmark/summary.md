# Cross-domain benchmark: summary

Generated from `benchmark.json` and the files beside it by `scripts/domain_benchmark/summary.py`; no figure below is typed by hand. Healthcare data is entirely synthetic; nothing here is medical advice.

## Executive summary

| measure | value |
|---|---|
| domains | 10 / 10 |
| principal datasets | 30 |
| stress datasets run | 6 |
| calls executed | 12,763 |
| correctness checks attempted | 6,159,473 |
| checks passed | 6,159,473 |
| checks failed | 0 |
| verified calls skipped (no oracle / resource) | 114 |
| known-answer checks passed | 50 / 50 |
| warnings | 1,228 |
| errors | 37 |
| worker crashes | 0 |
| exceptions escaping a tool | 18 |
| timeouts | 0 |
| total benchmark runtime (s) | 11,966.600 |
| peak worker memory (MiB) | 4,240.900 |
| largest workspace (MiB) | 1,361.970 |

Machine: Intel(R) Xeon(R) Processor @ 2.80GHz x 4, 16095 MiB RAM, SwapTotal:             0 kB; Linux-6.18.44-fc-v37-x86_64-with-glibc2.39; Python 3.12.3; commit 2d3d52f3667b on claude/trusting-edison-en0jnk.

Defects by severity: CRITICAL 0, HIGH 35, MEDIUM 2, LOW 0

### Wrong answers (worse than crashes)

None observed.

## Correctness

By domain and scale (a skipped check is not a pass):

| domain | rows | calls verified | checks | passed | failed | calls skipped | correct % |
|---|---|---|---|---|---|---|---|
| crm | 1,000 | 47 | 9,524 | 9,524 | 0 | 0 | 100.000 |
| crm | 10,000 | 6 | 113 | 113 | 0 | 0 | 100.000 |
| crm | 100,000 | 47 | 301,398 | 301,398 | 0 | 0 | 100.000 |
| crm | 1,000,000 | 47 | 2,954,849 | 2,954,849 | 0 | 0 | 100.000 |
| ecommerce | 1,000 | 47 | 3,539 | 3,539 | 0 | 0 | 100.000 |
| ecommerce | 10,000 | 4 | 133 | 133 | 0 | 0 | 100.000 |
| ecommerce | 100,000 | 47 | 66,581 | 66,581 | 0 | 0 | 100.000 |
| ecommerce | 1,000,000 | 47 | 602,578 | 602,578 | 0 | 0 | 100.000 |
| education | 1,000 | 50 | 2,148 | 2,148 | 0 | 0 | 100.000 |
| education | 10,000 | 4 | 172 | 172 | 0 | 0 | 100.000 |
| education | 100,000 | 47 | 15,576 | 15,576 | 0 | 0 | 100.000 |
| education | 1,000,000 | 47 | 83,077 | 83,077 | 0 | 0 | 100.000 |
| financial | 1,000 | 47 | 3,640 | 3,640 | 0 | 0 | 100.000 |
| financial | 10,000 | 16 | 334 | 334 | 0 | 0 | 100.000 |
| financial | 100,000 | 47 | 66,567 | 66,567 | 0 | 0 | 100.000 |
| financial | 1,000,000 | 47 | 601,543 | 601,543 | 0 | 0 | 100.000 |
| healthcare | 1,000 | 50 | 1,678 | 1,678 | 0 | 0 | 100.000 |
| healthcare | 10,000 | 4 | 142 | 142 | 0 | 0 | 100.000 |
| healthcare | 100,000 | 47 | 10,172 | 10,172 | 0 | 0 | 100.000 |
| healthcare | 1,000,000 | 47 | 37,172 | 37,172 | 0 | 0 | 100.000 |
| hr | 1,000 | 43 | 2,885 | 2,885 | 0 | 0 | 100.000 |
| hr | 10,000 | 8 | 458 | 458 | 0 | 0 | 100.000 |
| hr | 100,000 | 46 | 37,724 | 37,724 | 0 | 0 | 100.000 |
| hr | 1,000,000 | 46 | 308,249 | 308,249 | 0 | 0 | 100.000 |
| logistics | 1,000 | 47 | 1,690 | 1,690 | 0 | 0 | 100.000 |
| logistics | 10,000 | 4 | 97 | 97 | 0 | 0 | 100.000 |
| logistics | 100,000 | 47 | 21,989 | 21,989 | 0 | 0 | 100.000 |
| logistics | 1,000,000 | 47 | 156,989 | 156,989 | 0 | 0 | 100.000 |
| logistics | 2,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| logistics | 5,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| logistics | 10,000,000 | 23 | 61 | 61 | 0 | 20 | 100.000 |
| manufacturing | 1,000 | 50 | 1,522 | 1,522 | 0 | 0 | 100.000 |
| manufacturing | 10,000 | 4 | 106 | 106 | 0 | 0 | 100.000 |
| manufacturing | 100,000 | 47 | 14,312 | 14,312 | 0 | 0 | 100.000 |
| manufacturing | 1,000,000 | 47 | 81,832 | 81,832 | 0 | 0 | 100.000 |
| marketing | 1,000 | 50 | 1,490 | 1,490 | 0 | 0 | 100.000 |
| marketing | 10,000 | 6 | 159 | 159 | 0 | 0 | 100.000 |
| marketing | 100,000 | 47 | 14,301 | 14,301 | 0 | 0 | 100.000 |
| marketing | 1,000,000 | 47 | 81,842 | 81,842 | 0 | 0 | 100.000 |
| sales | 1,000 | 45 | 3,372 | 3,372 | 0 | 0 | 100.000 |
| sales | 10,000 | 6 | 144 | 144 | 0 | 0 | 100.000 |
| sales | 100,000 | 45 | 66,468 | 66,468 | 0 | 0 | 100.000 |
| sales | 1,000,000 | 45 | 602,536 | 602,536 | 0 | 0 | 100.000 |
| sales | 2,000,000 | 21 | 63 | 63 | 0 | 18 | 100.000 |
| sales | 5,000,000 | 21 | 63 | 63 | 0 | 18 | 100.000 |
| sales | 10,000,000 | 21 | 63 | 63 | 0 | 18 | 100.000 |

Total: 6,159,473 of 6,159,473 checks passed, 0 failed, 114 verified calls skipped.

Analyses with correctness failures: none

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
| propose_cleaning_plan | 143.384 | 144.027 | 144.671 | 2 |
| profile_dataset | 51.466 | 51.821 | 52.176 | 2 |
| profile_column | 48.429 | 50.217 | 52.004 | 2 |
| propose_dataset_contract | 15.190 | 19.687 | 23.909 | 4 |
| apply_cleaning_plan | 17.637 | 19.800 | 21.964 | 2 |
| confirm_ingest_spec | 17.905 | 19.294 | 20.683 | 2 |
| compute_analysis:top_n | 0.488 | 2.059 | 16.214 | 17 |
| render_chart | 0.556 | 1.394 | 9.727 | 28 |
| compute_analysis:frequency | 0.579 | 1.985 | 5.663 | 6 |
| compute_analysis:summary_stats | 3.259 | 3.997 | 4.736 | 2 |
| compute_analysis:correlation | 0.511 | 3.037 | 3.481 | 6 |
| compute_analysis:driver_analysis | 2.941 | 3.114 | 3.287 | 2 |
| compute_analysis:cohort_retention | 3.120 | 3.155 | 3.191 | 2 |
| compute_analysis:outlier_detection | 2.236 | 2.718 | 3.106 | 4 |
| compute_analysis:concentration | 0.578 | 0.955 | 2.979 | 4 |
| compute_analysis:pareto | 0.558 | 0.957 | 2.774 | 4 |
| describe_dataset | 2.562 | 2.599 | 2.636 | 2 |
| compute_analysis:repeat_behaviour | 2.400 | 2.503 | 2.605 | 2 |
| compute_analysis:distribution | 2.044 | 2.266 | 2.488 | 2 |
| compute_analysis:hypothesis_test | 0.631 | 0.920 | 2.111 | 8 |
| compute_analysis:group_compare | 0.774 | 1.529 | 2.023 | 6 |
| compute_analysis:mix_shift | 1.510 | 1.523 | 1.536 | 2 |
| compute_analysis:growth_decomposition | 1.464 | 1.487 | 1.510 | 2 |
| validate_dataset | 1.261 | 1.307 | 1.353 | 2 |
| compute_analysis:bivariate | 1.126 | 1.177 | 1.227 | 2 |
| compute_analysis:cross_tab | 0.923 | 1.006 | 1.102 | 4 |
| compute_analysis:effect_size | 0.663 | 0.929 | 1.001 | 6 |
| compute_analysis:confidence_interval | 0.857 | 0.915 | 0.995 | 4 |
| compute_analysis:sample_adequacy | 0.944 | 0.958 | 0.972 | 2 |
| compute_analysis:correlated_shift | 0.888 | 0.911 | 0.933 | 2 |
| compute_analysis:period_compare | 0.821 | 0.861 | 0.900 | 2 |
| compute_analysis:trend | 0.836 | 0.868 | 0.894 | 4 |
| compute_analysis:changepoint | 0.847 | 0.858 | 0.869 | 2 |
| compute_analysis:ranking_shift | 0.791 | 0.816 | 0.841 | 2 |
| compute_analysis:seasonality | 0.809 | 0.822 | 0.834 | 2 |
| compute_analysis:calendar_coverage | 0.828 | 0.830 | 0.832 | 2 |
| get_workflow_state | 0.422 | 0.443 | 0.464 | 2 |
| run_analysis | 0.436 | 0.437 | 0.437 | 2 |
| confirm_dataset_contract | 0.065 | 0.073 | 0.081 | 2 |
| build_report | 0.043 | 0.045 | 0.047 | 2 |
| get_cleaning_ledger | 0.033 | 0.033 | 0.034 | 2 |
| list_datasets | 0.024 | 0.024 | 0.024 | 2 |
| propose_ingest_spec | 0.005 | 0.005 | 0.006 | 2 |
| read_result_file | 0.001 | 0.001 | 0.001 | 2 |
| preview_file | 0.000 | 0.000 | 0.000 | 2 |
| check_file | 0.000 | 0.000 | 0.000 | 2 |

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
| 5000000->10000000 | 2.000 | 1.807 |

Ten worst scaling (time growth relative to data growth):

| domain | tool | analysis | rows | data x | time x | s before | s after |
|---|---|---|---|---|---|---|---|
| financial | confirm_dataset_contract |   | 100,000->1,000,000 | 10.000 | 37.571 | 0.033 | 1.249 |
| logistics | compute_analysis | frequency for_paging | 1,000,000->2,000,000 | 2.000 | 3.438 | 0.199 | 0.683 |
| logistics | compute_analysis | top_n n10 | 1,000,000->2,000,000 | 2.000 | 2.352 | 0.207 | 0.487 |
| logistics | compute_analysis | top_n n1000 | 1,000,000->2,000,000 | 2.000 | 2.337 | 0.216 | 0.504 |
| logistics | compute_analysis | correlation indep | 2,000,000->5,000,000 | 2.500 | 2.903 | 0.625 | 1.814 |
| sales | compute_analysis | top_n n1000 | 1,000,000->2,000,000 | 2.000 | 2.306 | 0.535 | 1.233 |
| sales | compute_analysis | concentration hi | 5,000,000->10,000,000 | 2.000 | 2.247 | 1.325 | 2.979 |
| logistics | compute_analysis | group_compare mean | 5,000,000->10,000,000 | 2.000 | 2.243 | 0.902 | 2.023 |
| logistics | compute_analysis | correlation  | 2,000,000->5,000,000 | 2.500 | 2.772 | 0.576 | 1.596 |
| logistics | confirm_ingest_spec |   | 5,000,000->10,000,000 | 2.000 | 2.197 | 9.416 | 20.683 |

## Memory

- 1,000 rows: worker peak RSS median 355 MiB, max 365 MiB over 10 worker run(s)
- 100,000 rows: worker peak RSS median 503 MiB, max 568 MiB over 10 worker run(s)
- 1,000,000 rows: worker peak RSS median 1,118 MiB, max 1,413 MiB over 10 worker run(s)
- 2,000,000 rows: worker peak RSS median 1,518 MiB, max 1,697 MiB over 2 worker run(s)
- 5,000,000 rows: worker peak RSS median 2,349 MiB, max 2,512 MiB over 2 worker run(s)
- 10,000,000 rows: worker peak RSS median 3,934 MiB, max 4,241 MiB over 2 worker run(s)

RSS growth from the first to the last call of a worker (accumulation):

| unit | calls | first MiB | last MiB | max MiB | growth MiB |
|---|---|---|---|---|---|
| I_sales_10000000 | 197 | 246.450 | 506.320 | 517.780 | 259.870 |
| D_hr | 376 | 246.580 | 503.130 | 519.020 | 256.550 |
| I_logistics_10000000 | 199 | 246.660 | 501.850 | 510.830 | 255.190 |
| I_sales_5000000 | 197 | 246.570 | 499.340 | 511.080 | 252.770 |
| D_manufacturing | 363 | 246.490 | 497.090 | 498.120 | 250.600 |
| I_logistics_5000000 | 199 | 246.660 | 494.910 | 505.440 | 248.250 |
| D_education | 363 | 246.410 | 488.610 | 491.480 | 242.200 |
| I_sales_2000000 | 197 | 246.550 | 467.250 | 478.880 | 220.700 |
| I_logistics_2000000 | 199 | 246.620 | 462.900 | 477.710 | 216.280 |
| E_healthcare | 319 | 246.520 | 450.750 | 452.370 | 204.230 |

Python-tracked allocations (tracemalloc, repeated mixed analyses): peak per call min 0.08 MiB, max 3.88 MiB over 36 calls.

## Errors

| severity | tool | what | count |
|---|---|---|---|
| HIGH | compute_analysis | FAIL_EXCEPTION:  | 12 |
| HIGH | compute_analysis | BinderException: Binder Error: No functi | 11 |
| HIGH | read_result_file | 50 found | 5 |
| HIGH | compute_analysis | OutOfRangeException: Out of Range Error: | 4 |
| HIGH | compute_analysis | IndexError: list index out of range | 2 |
| HIGH | compute_analysis | ZeroDivisionError: both groups have zero | 1 |
| MEDIUM | compute_analysis | oracle_error | 1 |
| MEDIUM | apply_cleaning_plan | FAIL_MISLEADING_RESPONSE: BLOCKED: the p | 1 |

## Crashes

| # | domain | rows | tool | analysis | exception |
|---|---|---|---|---|---|
| 1 | - | 0 | compute_analysis | hypothesis_test | ZeroDivisionError: both groups have zero variance |
| 2 | - | 0 | compute_analysis | mix_shift | BinderException: Binder Error: No function matches the given name and argument types 'avg(VARCHAR)'. You might |
| 3 | - | 0 | compute_analysis | outlier_detection | BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, D |
| 4 | - | 0 | compute_analysis | correlation | BinderException: Binder Error: No function matches the given name and argument types 'corr(DOUBLE, VARCHAR)'.  |
| 5 | - | 0 | compute_analysis | driver_analysis | BinderException: Binder Error: No function matches the given name and argument types 'avg(VARCHAR)'. You might |
| 6 | - | 0 | compute_analysis | summary_stats | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 7 | - | 0 | compute_analysis | outlier_detection | BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, D |
| 8 | - | 0 | compute_analysis | trend | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 9 | - | 0 | compute_analysis | correlation | BinderException: Binder Error: No function matches the given name and argument types 'corr(BIGINT, VARCHAR)'.  |
| 10 | - | 0 | compute_analysis | summary_stats | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 11 | - | 0 | compute_analysis | outlier_detection | BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, D |
| 12 | - | 0 | compute_analysis | trend | BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might |
| 13 | - | 0 | compute_analysis | top_n | IndexError: list index out of range |
| 14 | - | 0 | compute_analysis | top_n | IndexError: list index out of range |
| 15 | sales | 10,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (34236401011344 * 5851188)! |
| 16 | sales | 10,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (34236401011344 * 5851188)! |
| 17 | sales | 5,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)! |
| 18 | sales | 5,000,000 | compute_analysis | hypothesis_test | OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)! |
| 20 | - | 0 | compute_analysis | hypothesis_test | FAIL_EXCEPTION:  |
| 22 | - | 0 | compute_analysis | mix_shift | FAIL_EXCEPTION:  |
| 23 | - | 0 | compute_analysis | outlier_detection | FAIL_EXCEPTION:  |
| 24 | - | 0 | compute_analysis | correlation | FAIL_EXCEPTION:  |
| 25 | - | 0 | compute_analysis | driver_analysis | FAIL_EXCEPTION:  |
| 26 | - | 0 | compute_analysis | summary_stats | FAIL_EXCEPTION:  |
| 27 | - | 0 | compute_analysis | outlier_detection | FAIL_EXCEPTION:  |
| 28 | - | 0 | compute_analysis | trend | FAIL_EXCEPTION:  |
| 29 | - | 0 | compute_analysis | correlation | FAIL_EXCEPTION:  |
| 30 | - | 0 | compute_analysis | summary_stats | FAIL_EXCEPTION:  |
| 31 | - | 0 | compute_analysis | outlier_detection | FAIL_EXCEPTION:  |
| 32 | - | 0 | compute_analysis | trend | FAIL_EXCEPTION:  |

## Warnings

| category | count |
|---|---|
| slow_call | 979 |
| questionable_or_unverified_result | 148 |
| suspicious_scaling | 43 |
| excessive_response_size | 25 |
| unsupported_operation | 18 |
| irrelevant_or_unexecutable_recommendation | 15 |

## Behaviour under wrong and edge calls

| classification | calls |
|---|---|
| FAIL_EXCEPTION | 12 |
| FAIL_MISLEADING_RESPONSE | 1 |
| PASS_ACCEPTED | 21 |
| PASS_AUTOCORRECTED | 61 |
| PASS_SAFE_REJECTION | 154 |
| PASS_USEFUL_WARNING | 16 |

By family:

| family | classes |
|---|---|
| file_format | PASS_SAFE_REJECTION 10, PASS_AUTOCORRECTED 4, PASS_ACCEPTED 3 |
| not_applicable | PASS_SAFE_REJECTION 58, PASS_AUTOCORRECTED 2 |
| other | PASS_SAFE_REJECTION 35, PASS_AUTOCORRECTED 4, PASS_ACCEPTED 4, PASS_USEFUL_WARNING 3 |
| statistical | PASS_USEFUL_WARNING 6, PASS_ACCEPTED 6, PASS_AUTOCORRECTED 2, FAIL_EXCEPTION 1, PASS_SAFE_REJECTION 1 |
| temporal | PASS_AUTOCORRECTED 26, PASS_ACCEPTED 4, PASS_USEFUL_WARNING 3 |
| wrong_call | PASS_SAFE_REJECTION 50, PASS_AUTOCORRECTED 23, FAIL_EXCEPTION 11, PASS_ACCEPTED 4, PASS_USEFUL_WARNING 4, FAIL_MISLEADING_RESPONSE 1 |

Refusal message quality over 155 refusals: identifies the problem 155, names the parameter 49 (of 50 with a named parameter), explains what was expected 102, suggests a correction 155; NEXT STEP followed: WORKED 96, not followed 34, NOT_EXECUTED 23, REFUSED_SAME_REASON 2

## Charts

| verdict | count |
|---|---|
| PASS | 1,136 |
| REFUSED | 364 |

## Cleaning plans

| verdict | actions |
|---|---|
| valid | 45 |
| unnecessary | 4 |
- dirty variant format_noise: expected accept; actions 7; injected defects with no action: risk score %
- dirty variant bad_dates: expected warn; actions 1; injected defects with no action: none
- dirty variant duplicate_columns: expected either; actions 1; injected defects with no action: none
- dirty variant missing_header: expected warn; actions 0; injected defects with no action: none
- dirty variant reordered_extra: expected accept; actions 1; injected defects with no action: none

## Concurrency and state isolation

- separate x2: statuses {'OK': 2}; distinct result files 2 of 2
- shared x2: statuses {'OK': 2}; distinct result files 2 of 2
- separate x5: statuses {'OK': 5}; distinct result files 5 of 5
- shared x5: statuses {'OK': 5}; distinct result files 5 of 5
- separate x10: statuses {'OK': 10}; distinct result files 10 of 10
- shared x10: statuses {'OK': 10}; distinct result files 9 of 10
- same_dataset x10: statuses {'OK': 8, 'EXCEPTION': 2}; distinct result files 7 of 8
- isolation reports: 10 of 10 pass
- isolation ledgers: 10 of 10 pass
- isolation charts: 10 of 10 pass
- isolation correctness: 20 of 20 verified calls pass

## Reproducibility

| domain | rows | dataset identical | results identical | differ | status |
|---|---|---|---|---|---|
| financial | 1,000 | True | 12 | 0 | PASS |
| financial | 100,000 | True | 12 | 0 | PASS |
| crm | 1,000 | True | 12 | 0 | PASS |
| crm | 100,000 | True | 9 | 3 | FAIL |
| logistics | 1,000 | True | 12 | 0 | PASS |
| logistics | 100,000 | True | 12 | 0 | PASS |

## Domain observations

### Financial

- 1,000 rows: 3,640 of 3,640 checks pass, 0 fail
- 10,000 rows: 334 of 334 checks pass, 0 fail
- 100,000 rows: 66,567 of 66,567 checks pass, 0 fail
- 1,000,000 rows: 601,543 of 601,543 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  16.04s; profile_dataset  6.93s; profile_column  5.97s

### HR

- 1,000 rows: 2,885 of 2,885 checks pass, 0 fail
- 10,000 rows: 458 of 458 checks pass, 0 fail
- 100,000 rows: 37,724 of 37,724 checks pass, 0 fail
- 1,000,000 rows: 308,249 of 308,249 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  12.13s; profile_column  5.02s; profile_dataset  4.99s
- refused although classed REQUIRED/VALID/EDGE: pareto (VALID), concentration (VALID), repeat_behaviour (EDGE_CASE), cohort_retention (EDGE_CASE)

### Sales

- 1,000 rows: 3,372 of 3,372 checks pass, 0 fail
- 10,000 rows: 144 of 144 checks pass, 0 fail
- 100,000 rows: 66,468 of 66,468 checks pass, 0 fail
- 1,000,000 rows: 602,536 of 602,536 checks pass, 0 fail
- 2,000,000 rows: 63 of 63 checks pass, 0 fail
- 5,000,000 rows: 63 of 63 checks pass, 0 fail
- 10,000,000 rows: 63 of 63 checks pass, 0 fail
- errors: 6 (HIGH 6)
  - HIGH compute_analysis hypothesis_test 10000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (34236401011344 * 5851188)!
  - HIGH compute_analysis hypothesis_test 10000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (34236401011344 * 5851188)!
  - HIGH compute_analysis hypothesis_test 5000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)!
  - HIGH compute_analysis hypothesis_test 5000000: OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (8569190673124 * 2927318)!
  - HIGH read_result_file  2000000: 50 found
  - HIGH read_result_file  5000000: 50 found
- slowest at 1M rows: propose_cleaning_plan  15.71s; profile_dataset  5.58s; render_chart top_n 5.01s
- refused although classed REQUIRED/VALID/EDGE: pareto (REQUIRED), concentration (REQUIRED)

### Marketing

- 1,000 rows: 1,490 of 1,490 checks pass, 0 fail
- 10,000 rows: 159 of 159 checks pass, 0 fail
- 100,000 rows: 14,301 of 14,301 checks pass, 0 fail
- 1,000,000 rows: 81,842 of 81,842 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  10.40s; profile_column  5.03s; profile_dataset  5.02s

### CRM

- 1,000 rows: 9,524 of 9,524 checks pass, 0 fail
- 10,000 rows: 113 of 113 checks pass, 0 fail
- 100,000 rows: 301,398 of 301,398 checks pass, 0 fail
- 1,000,000 rows: 2,954,849 of 2,954,849 checks pass, 0 fail
- errors: 1 (MEDIUM 1)
  - MEDIUM compute_analysis top_n 10000: None (0 of 0 checks failed)
- slowest at 1M rows: compute_analysis top_n 8.13s; propose_cleaning_plan  7.95s; render_chart top_n 7.64s

### E-commerce

- 1,000 rows: 3,539 of 3,539 checks pass, 0 fail
- 10,000 rows: 133 of 133 checks pass, 0 fail
- 100,000 rows: 66,581 of 66,581 checks pass, 0 fail
- 1,000,000 rows: 602,578 of 602,578 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  15.72s; render_chart top_n 5.56s; profile_column  4.44s

### Logistics

- 1,000 rows: 1,690 of 1,690 checks pass, 0 fail
- 10,000 rows: 97 of 97 checks pass, 0 fail
- 100,000 rows: 21,989 of 21,989 checks pass, 0 fail
- 1,000,000 rows: 156,989 of 156,989 checks pass, 0 fail
- 2,000,000 rows: 61 of 61 checks pass, 0 fail
- 5,000,000 rows: 61 of 61 checks pass, 0 fail
- 10,000,000 rows: 61 of 61 checks pass, 0 fail
- errors: 3 (HIGH 3)
  - HIGH read_result_file  10000000: 50 found
  - HIGH read_result_file  2000000: 50 found
  - HIGH read_result_file  5000000: 50 found
- slowest at 1M rows: propose_cleaning_plan  15.32s; apply_cleaning_plan  5.55s; profile_dataset  5.37s

### Healthcare (synthetic)

- 1,000 rows: 1,678 of 1,678 checks pass, 0 fail
- 10,000 rows: 142 of 142 checks pass, 0 fail
- 100,000 rows: 10,172 of 10,172 checks pass, 0 fail
- 1,000,000 rows: 37,172 of 37,172 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  10.53s; render_chart top_n 4.83s; profile_column  4.06s

### Manufacturing

- 1,000 rows: 1,522 of 1,522 checks pass, 0 fail
- 10,000 rows: 106 of 106 checks pass, 0 fail
- 100,000 rows: 14,312 of 14,312 checks pass, 0 fail
- 1,000,000 rows: 81,832 of 81,832 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  12.50s; profile_dataset  5.28s; profile_column  5.24s

### Education

- 1,000 rows: 2,148 of 2,148 checks pass, 0 fail
- 10,000 rows: 172 of 172 checks pass, 0 fail
- 100,000 rows: 15,576 of 15,576 checks pass, 0 fail
- 1,000,000 rows: 83,077 of 83,077 checks pass, 0 fail
- errors: 0 ()
- slowest at 1M rows: propose_cleaning_plan  14.66s; apply_cleaning_plan  5.91s; profile_column  5.23s

## Bottlenecks (measured)

Ten slowest calls:

| seconds | tool | analysis | domain | rows |
|---|---|---|---|---|
| 323.296 | propose_ingest_spec |  | - | 0 |
| 149.785 | propose_cleaning_plan |  | sales | 10,000,000 |
| 144.671 | propose_cleaning_plan |  | sales | 10,000,000 |
| 143.384 | propose_cleaning_plan |  | logistics | 10,000,000 |
| 142.383 | propose_cleaning_plan |  | logistics | 10,000,000 |
| 75.051 | propose_cleaning_plan |  | sales | 5,000,000 |
| 74.077 | propose_cleaning_plan |  | sales | 5,000,000 |
| 71.161 | propose_cleaning_plan |  | logistics | 5,000,000 |
| 71.089 | propose_cleaning_plan |  | logistics | 5,000,000 |
| 58.153 | profile_column |  | sales | 10,000,000 |

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
| 4,240.930 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,214.460 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,174.250 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,172.780 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,149.410 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,103.510 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,097.360 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,083.060 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,027.740 | profile_column |  | I_sales_10000000 | 10,000,000 |
| 4,013.980 | profile_column |  | I_sales_10000000 | 10,000,000 |

Tools with most errors: compute_analysis 31, read_result_file 5, apply_cleaning_plan 1
Domains with most errors: None 27, sales 6, logistics 3, crm 1
Tools with most warnings: profile_column 649, compute_analysis 127, render_chart 92, propose_cleaning_plan 74, profile_dataset 44, propose_dataset_contract 36, confirm_ingest_spec 17, apply_cleaning_plan 17

## Regression candidates

Every case below failed or guards a property the benchmark measured; each is small enough to run in the suite:

- [HIGH] compute_analysis hypothesis_test (stat_edges): ZeroDivisionError: both groups have zero variance
- [HIGH] compute_analysis mix_shift (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'avg(VARCHAR)'. You might need to a
- [HIGH] compute_analysis outlier_detection (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'quantile_cont(VARCHAR, DECIMAL(3,2
- [HIGH] compute_analysis correlation (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'corr(DOUBLE, VARCHAR)'. You might 
- [HIGH] compute_analysis driver_analysis (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'avg(VARCHAR)'. You might need to a
- [HIGH] compute_analysis summary_stats (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might need to a
- [HIGH] compute_analysis trend (wrong_calls): BinderException: Binder Error: No function matches the given name and argument types 'sum(VARCHAR)'. You might need to a
- [HIGH] compute_analysis top_n (concurrency): IndexError: list index out of range
- [HIGH] compute_analysis hypothesis_test (analyses): OutOfRangeException: Out of Range Error: Overflow in multiplication of INT64 (34236401011344 * 5851188)!
- [HIGH] compute_analysis hypothesis_test (zero_variance_t): FAIL_EXCEPTION: 
- [HIGH] compute_analysis mix_shift (cd_mix_shift): FAIL_EXCEPTION: 
- [HIGH] compute_analysis outlier_detection (cd_outlier_detection): FAIL_EXCEPTION: 
- [HIGH] compute_analysis correlation (cd_correlation): FAIL_EXCEPTION: 
- [HIGH] compute_analysis driver_analysis (cd_driver_analysis): FAIL_EXCEPTION: 
- [HIGH] compute_analysis summary_stats (t_all_null_col_summary): FAIL_EXCEPTION: 
- [HIGH] compute_analysis outlier_detection (t_all_null_col_outliers): FAIL_EXCEPTION: 
- [HIGH] compute_analysis trend (t_all_null_col_trend): FAIL_EXCEPTION: 
- [HIGH] compute_analysis correlation (t_all_null_col_corr): FAIL_EXCEPTION: 
- [HIGH] compute_analysis summary_stats (t_inf_nan_summary): FAIL_EXCEPTION: 
- [HIGH] compute_analysis outlier_detection (t_inf_nan_outliers): FAIL_EXCEPTION: 
- [HIGH] compute_analysis trend (t_inf_nan_trend): FAIL_EXCEPTION: 
- [HIGH] read_result_file  (read_result): 50 found
- [MEDIUM] compute_analysis top_n (analyses): None (0 of 0 checks failed)
- [MEDIUM] apply_cleaning_plan  (apply_unknown_id): FAIL_MISLEADING_RESPONSE: BLOCKED: the plan for adv is out of date.
WHY: the table has lost 7 row(s) since this plan was
- [guard] the known-answer fixture (perfect +1/-1/0 correlation, arithmetic trend, changepoint, 80/20 Pareto, ranking, retention grid, identical and separated groups, imbalance, 10% missing, 4 duplicates)
- [guard] sorted vs shuffled input gives identical tables for every temporal analysis

## Final technical findings

Generated from the figures above; what they mean is discussed in docs/steps/phase14_step13_domain_benchmark.md.

- Correctness: 6,159,473 of 6,159,473 independent checks passed; 0 failed (none).
- Defects: CRITICAL 0, HIGH 35, MEDIUM 2, LOW 0.
- Largest dataset processed to completion on this machine: 10,000,000 rows
- Stress tiers skipped for resources: none
- Median time growth 100k -> 1M: 1.80x for 10x rows.
- Peak worker memory: 4240.9 MiB.

