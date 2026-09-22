# Retail fixture run: 50 graded cases against the engine

The user supplied, 22/09/2026, four files in ~/Downloads: `retail_fixture.csv` (224,955 records x 42
columns, 62 MB, seed 20260922), its generator `make_retail_fixture.py`, `answer_key.py` (pandas,
scipy, statsmodels, sklearn) and the key it wrote, `retail_test_cases.md` -- 50 cases in sections
A-L. This document runs them against the engine through server.py, the functions Claude Desktop
calls, in a throwaway workspace `retail_run`. Not the web assistant: a model's answer is one sample,
and this measures the product. No src/ change is made here; defects found are listed for a later
step.

Grading: PASS -- the key's figure, or the named refusal the case asks for. PARTIAL -- the right
behaviour with a different unit or an incomplete statement. FAIL -- a wrong figure given
confidently, or the trap the case names. GAP -- the capability is absent and the engine says so
by name (the key's own term); a GAP answered with a confident wrong number is a FAIL.

The key's convention: exact duplicates removed (224,955 -> 224,835), rating nulls '', 'NA', 'n/a',
'-'. Here that is two cleaning rounds: DROP_DUPLICATE_ROWS, then NORMALISE_MISSING on rating with
missing_values=['-'] and CONVERT_TYPE. sklearn is not installed, so answer_key.py is not re-run;
the key is the .md it wrote, spot-checked by DuckDB SQL (command 2).

The contract a careful person would confirm: grain line_id, primary_key [line_id]; date order_ts,
window 2023-01-01..2025-12-31; measures line_revenue, line_cost, units, unit_price (sum/sum/sum/
mean), discount_pct, delivery_days, rating, web_session_seconds, pages_viewed (mean), margin_pct,
order_shipping_fee, rep_monthly_salary, stock_on_hand_at_order (none -- ratio, order-level,
rep-level, snapshot), customer_id as a count_distinct measure for C4; dimensions category,
sub_category, channel, payment_method, region, customer_state, courier, city_tier,
customer_segment, sku, rep_id, rep_department, is_returned.

## Predictions, per case, before running

A1 PASS (DuckDB parses quoted newlines). A2 FAIL -- the sniffer reads 000435 as BIGINT. A3 PARTIAL
-- text, but no cleaning step: CONVERT_TYPE needs 90% to parse and nothing with a rupee sign does.
A4 PASS. A5 PARTIAL -- '-' and 'unknown' are named as NOT counted, and nothing says the Store blanks
are structural. A6 PARTIAL -- VARCHAR; a CONVERT_TYPE to DATE proposed with the 3,030 dd/mm values
counted as lost, not recognised as a second format. A7 PASS.
B1-B3 GAP -- validate_dataset has no range or cross-column rules. B4 PASS (nothing flagged).
C1-C3 PASS by refusal, because the contract declares them none -- the engine does not detect a
coarser grain itself. C4 PASS if count_distinct takes a text column. C5 GAP. C6 PARTIAL.
D1 PASS. D2 PASS, blank state as (null). D3, D4 GAP -- 500 SKUs and 34,836 customers exceed the
49-group cap (TooManyGroups names top_n). D5 FAIL -- cross_tab counts lines, the key counts orders.
E1 PASS. E2 PASS. E3 PARTIAL -- periods compared, the missing September not named inside 2024. E4
PASS. E5 PASS.
F1 PASS. F2 PASS. F3 PASS. F4 PARTIAL -- equal-width bins, not the key's.
G1 GAP -- global fence only. G2 PASS, the gap-adjacent split excluded. G3 PASS.
H1-H3, H5, H6 PARTIAL -- line level, where rating repeats within an order; H4 PASS (line level).
I1 PASS. I2 PARTIAL -- lines, not orders.
J1, J3, J4 GAP. J2 GAP by refusal (salary none). J5 PASS.
K1-K3 GAP, named (ANALYSIS_NOT_FOUND with the list). L1-L3 PASS.
Totals predicted: PASS 22, PARTIAL 12, FAIL 2, GAP 14.

## Commands

1. Baseline `uv run pytest -q`. Expected 1899 passed.
2. Key spot-checks in DuckDB SQL: rows 224,955; exact duplicates 120; deduplicated line_revenue
   total 1,289,929,075.88; 2024-09 empty; Maharashtra 213,869,488.73; D5 Online x UPI 28,281
   orders. Expected: all six equal the key.
3. A: check_file, load_csv, describe_dataset, profile_dataset, profile_column on sku,
   list_price_display, delivery_date, rating; propose_cleaning_plan.
4. Cleaning: dedup, then rating tokens and type. Expected 224,955 -> 224,835.
5. Contract as above, confirm. Then B (validate_dataset), C-J (compute_analysis), K (unknown
   analysis names), each reply saved to scratch and graded against the key.
6. L: size_warn.csv (~309 MB) and size_refuse.csv (~2.6 GB) in the scratchpad, per the key's
   commands; check_file and load_csv on each; both deleted after.
7. Records: this document's results, a decisions.md section, commit.

## Results

1. Baseline. `1899 passed in 92.33s`. As expected.
2. Key spot-checks, DuckDB SQL on the raw file: rows 224,955; exact duplicates 120; deduplicated
   line_revenue 1,289,929,075.88; 2024-09 rows 0; Maharashtra 213,869,488.73; Online x UPI orders
   28,281. All six equal the key.
3-6. Run through server.py in workspace retail_run; every reply saved to the scratchpad. The key has
   53 cases, not the 50 this plan said (A7 B4 C6 D5 E5 F4 G3 H6 I2 J5 K3 L3).
   3.0. Deviation from the plan: the rating cleaning declared missing_values=['n/a'], not ['-'] --
        the loader had already turned `-` and `NA` into NULL (A5), so `n/a` was the one token left.
        The key's convention holds either way: all four tokens are NULL after C006 and C004.
   3.1. contract v1 declared customer_id as a count_distinct measure (for C4); a column that is a
        measure leaves the dimensions, so D4, I1, I2 were refused "'customer_id' is not a declared
        dimension". contract v2: customer_id a dimension, order_id a count_distinct measure (D5).
        The two needs cannot share one contract.
   3.2. F4 was first called with measure and against reversed (my error: bivariate bins its
        measure); re-run as measure=delivery_days, against=rating.
   6.1. The refuse file is 2,595,199,347 bytes = 2.60 GB = 2.42 GiB, and SIZE_GATES.csv_refuse_bytes
        is 2,684,354,560 = 2.5 GiB. Prediction changed BEFORE running L2, from PASS to FAIL.

## Grades

| case | grade | what the engine did |
|---|---|---|
| A1 | PASS | 224,955 rows x 42 from the parser (224,982 physical lines) |
| A2 | PARTIAL | loaded as VARCHAR, 000435 intact -- but the cleaning plan offers C003 CONVERT_TYPE sku -> BIGINT as discarding nothing, and its NEXT STEP recommends approving it |
| A3 | PARTIAL | text; not flagged as numbers behind a currency sign; no cleaning step |
| A4 | PASS | 120 exact duplicates; line_id 224,835 distinct; after C001 unique, key verified at propose |
| A5 | FAIL | the loader's default nulls (`""`, `NA`, `N/A`, `-`, ...) turned rating's NA and - into NULL silently (60,578 nulls = 47,156 + 8,069 + 5,353); n/a survived (case-sensitive) and was reported; 'unknown' reported; the 67,417 Store blanks not called structural |
| A6 | PASS | "98.1% ... parse as DATE, 3,030 did not; '01/12/2024' ..."; the cast offered is flagged as discarding 3,030 |
| A7 | PASS | 35 of 36 months, 2024-09 absent, longest gap 1 |
| B1-B3 | GAP | validate_dataset has six contract checks; none covers units > 0, delivery after order, or rep exit |
| B4 | PASS | nothing flagged |
| C1 | PASS | no total column: "declared non-additive" |
| C2 | FAIL | (all) mean 71,692.20 -- the key's wrong, line-weighted figure; `none` stops a total, not a mean |
| C3 | PASS | no total column |
| C4 | PASS | 20,125 / 27,350 / 22,444; (all) 34,836 from rows |
| C5 | FAIL | summary_stats mean of margin_pct 25.79 -- the key's wrong figure; no ratio of sums (18.40%) |
| C6 | PARTIAL | cross_tab counts (Apparel 16,706 of 64,868); no rate column |
| D1 | PASS | exact: sums, means, shares |
| D2 | PASS | top 5 exact; (null) 20,240,461.67 as its own group |
| D3 | GAP | named: 500 groups over the 49 cap; NEXT STEP top_n |
| D4 | GAP | named: 34,836 groups over the cap |
| D5 | PASS | with order_id as a count_distinct measure: every cell exact, 150,000 orders (v1 counted lines, labelled "Cells count analysed rows") |
| E1 | PASS | 2024-09 blank not zero; endpoints, no fit |
| E2 | PASS | Nov 1.47 > Oct 1.38 > Dec 1.21; Sep "lost a month to a gap", 2 observed |
| E3 | FAIL | +244,905,471.67 (+67.6%) right, but "2024 covers 366 days ... 366 days of data" when 30 hold none; September never named |
| E4 | PASS | exact; contributions sum to 244,905,471.67 (same 366-day sentence) |
| E5 | PASS | all 14 ranks exact; blank state kept as rank 15 |
| F1 | PASS | +0.460/+0.441, -0.583/-0.584, +0.910/+0.864, -0.001/-0.001; pairs exact |
| F2 | PASS | courier 0.265, channel 0.228; order_id's 1.000 flagged as one-row-group arithmetic |
| F3 | PASS | 5,118.20 -> 6,669.01 = rate 1,549.60 + mix 1.04 + interaction 0.17 |
| F4 | PASS | per-day bins; 0 days 4.4645, days 1-2 pool to 4.0304 (key 4.030) |
| G1 | GAP | global Tukey 32,467 (the key's figure), not called errors; no within-group or ratio-to-list route |
| G2 | PASS | split after 2024-12, 0.0324 -> 0.1421; 2024-08 and 2024-09 excluded |
| G3 | PARTIAL | "do not break in the same place" -- units declared sum, so the series is volume (breaks 2025-09); the key's units per line breaks 2025-01. One aggregate per measure |
| H1 | PARTIAL | 3-group ANOVA (no way to pick two groups); line-level Store n 47,401 mean 4.4645 as the key's line level; repetition within orders not noticed |
| H2 | PARTIAL | line level F 2,356.93 vs order level 1,515.59 |
| H3 | PASS | "No detectable association ... not evidence they are independent" (line level chi2 20.03, p 0.067; key order level 10.81, p 0.545) |
| H4 | PASS | chi2 13,637.85, df 4 |
| H5 | PARTIAL | line level: rating 3.8275 [3.8232, 3.8318]; returned-line share 13.1%; key is per order |
| H6 | GAP | named: "No assessment: channel has 3 group(s) ... This compares two" |
| I1 | PASS | the key's 24 cells exact |
| I2 | FAIL | rows counted as events: repeat 89.135% vs 82.096%, busiest 939 vs 633 orders -- a two-line order "came back" |
| J1 | PARTIAL | 120 distinct reps; no attrition |
| J2 | FAIL | line-weighted department means (E-commerce 69,500.67 vs 69,264.29) |
| J3 | FAIL | r +0.316 over 224,835 line pairs vs +0.357 over 120 reps |
| J4 | GAP | no date difference into a measure (not run) |
| J5 | PASS | E0029 14,655,654.09; E0084 13,973,942.27; E0008 13,838,524.39 |
| K1-K3 | GAP | named: ANALYSIS_NOT_FOUND with the catalogue -- the key's pass for K |
| L1 | PARTIAL | warns and loads 1,124,775 rows; says "294.6 MB" (MiB), never the 250 MB threshold |
| L2 | FAIL | 2,595,199,347 bytes: "[WARN] ... 2.4 GB. Loading will work" -- the refuse gate is 2.5 GiB |
| L3 | PASS | "within limits. Safe to load." |

Totals: PASS 25, PARTIAL 9, FAIL 8, GAP 11 (of 53). Predicted (of a miscounted 50): 22 / 12 / 2 / 14.
Wrong predictions: A2 (FAIL -> PARTIAL: the loader kept text; the cleaning plan is the trap), A5
(PARTIAL -> FAIL), C2 and J2 (refusal -> FAIL: `none` shows a mean), C5 (GAP -> FAIL, same), D5
(FAIL -> PASS via a count_distinct measure), E3 (PARTIAL -> FAIL), F4 (PARTIAL -> PASS), H3 (PARTIAL
-> PASS), I2 (PARTIAL -> FAIL), J3 (not predicted -> FAIL), L2 (PASS -> FAIL, found before running).

## Findings, by what they cost

1. RF-1. A coarser-grain measure has no declaration. order_shipping_fee (order), rep_monthly_salary
   (rep), rating (order) and margin_pct (ratio) can only be `none`, which removes a total and
   leaves a mean -- and the mean is the trap: C2 71,692.20, C5 25.79, J2, J3; and the tests of H1-H5
   run on repeated rows. Needs a measure grain (aggregate per distinct order_id / rep_id first) and
   a ratio declaration (sum of one over sum of another). 7 cases.
2. RF-2. The size gates are GiB and say GB. The key's 2.60 GB file loads with a warning (L2); the
   warn message names neither threshold (L1).
3. RF-3. period_compare and growth_decomposition count calendar days as "days of data" -- "366 days"
   for a 2024 missing September (E3, E4). The months with no rows inside each period should be
   named, and the day count should be the days that hold rows.
4. RF-4. The loader nulls `-` and `NA` at load, silently and case-sensitively (A5). The load reply
   should say how many values each default token turned into NULL.
5. RF-5. The cleaning plan offers CONVERT_TYPE on a zero-padded fixed-width code as discarding
   nothing, and its NEXT STEP recommends it (A2) -- while the profile says "Fixed width usually
   means a code".
6. RF-6. repeat_behaviour and cohort sizes count rows as events; an event key (order_id) is needed
   (I2).
7. RF-7. validate_dataset has no rules beyond the key, dates and row count: no range (units > 0),
   no cross-column (delivery >= order, sale <= rep exit) (B1-B3).
8. RF-8. pareto and concentration refuse above 49 groups, though their answers are a few numbers
   (SKUs to 80%, top 1% share, HHI) that need no 500-row table (D3, D4).
9. RF-9. One aggregate per measure: "units per line" cannot be asked when units sums (G3); two
   groups of three cannot be tested alone (H1, H6); outliers cannot be sought within a group (G1).
10. RF-10. Smaller: no currency-number detection (A3), no rate column for a boolean (C6), no
    attrition or tenure (J1, J4).

MEASURED VALIDATION line: docs/decisions.md, section Retail fixture run.
