# Cleanup Step 16: the retail fixture's 53 cases, re-run after the fixes

The retail run (docs/steps/retail_fixture_run.md) graded PASS 25, PARTIAL 9, FAIL 8, GAP 11. Cleanup
Steps 12-15 closed RF-O1 to RF-O8. This runs the same 53 cases through server.py again. Nothing in
src/ changes here.

## The contract a careful person would now confirm

One contract serves both the key's line-level cases and its order-level ones, because a measure can
read another column: `rating` (mean, per line: F1, F2, F4) and `rating_order` (rating, mean, per
order_id: H1-H6); `customers` (customer_id, count_distinct: C4) and `orders` (order_id,
count_distinct: D5), so customer_id and order_id stay dimensions (D4, I1, I2). Per a unit:
order_shipping_fee per order_id; rep_monthly_salary, rep_performance_rating, rep_exit_date per
rep_id. gross_margin_pct a ratio; returned_rate over is_returned; units_per_line over units. Four
expectations (B1-B4). Cleaning as before, per the key: C001 dedup, n/a to NULL, rating to BIGINT.

## Predictions, before running

PASS 46, PARTIAL 3, FAIL 0, GAP 4.
- PARTIAL: A5 (tokens now counted, but the 67,417 Store blanks are still not called structural);
  H5 (the mean rating per order passes; "share of orders with any return" needs an order-level flag
  that varies across an order's lines and cannot be declared per order); J3 (r 0.3572 passes; the
  within-department regression is not an analysis here).
- GAP, named: J4 (tenure needs a derived column -- Phase 15); K1-K3 (Phase 16), which the key's own
  pass condition for K counts as passing.
- H3 stays line level (a chi-square counts rows); its pass condition is the wording, which held.

## Commands

1. Baseline `uv run pytest -q`. Expected 1943.
2. The run: scratchpad runner over all 53, replies saved; L on sparse files of the key's sizes.
3. Grade against the key; the table below.
4. Records, commit.

## Results

1. Baseline. `1943 passed`. As expected.
2. The run (scratchpad rerun.py; replies in rerun.json). All 53 ran; K1-K3 refused
   ANALYSIS_NOT_FOUND, as the key's pass condition for K wants.
   2.1. THE PREDICTION "FAIL 0" WAS WRONG ON THE FIRST RUN. I1's refusal half: cohort_retention keyed
        on order_id was ACCEPTED and said "Repeat rate 39.965%: 59,948 of 150,000 came back at least
        once" -- an order's lines counted as returns; the refusal fired only for a key distinct per
        ROW, and order_id repeats across lines. Its repeat rate also counted rows, so the customer
        grid's rate read 89.1% where the key's is 82.1%. Fixed: coming back is a second MOMENT
        (count(DISTINCT order_ts) > 1), and a key none of whose values spans two moments is refused
        by name, in cohort_retention and repeat_behaviour. Tests first: `3 failed`, then pass.
        Re-run: I1x "none of its 150,000 value(s) appears at more than one moment -- ... it names an
        event"; I1 "Repeat rate 82.096%: 28,599 of 34,836"; the grid unchanged. CL16-D1.
   2.2. Comparing run 1 with run 2 (file paths removed) found E4's "Gross movement exceeds the net
        change, so members moved against each other" present in one and absent in the other, with
        all five categories rising: growth_decomposition compared two float sums exactly, and
        DuckDB's threads add in no fixed order. A 0.1 + 0.2 + 0.3 fixture could not reproduce the
        flip (its test passed on the unfixed tree) -- recorded as a guard, not a falsification. The
        sentence now depends on directions: some rose and some fell. Run 3: absent. CL16-D2.
   2.3. The same comparison found A_plan's duplicate sample in a different order (no ORDER BY);
        the sample is now ordered.
   Suite `1947 passed` (1943 + 4).
3. Grades, run 3 (the committed tree):

| case | grade | the engine |
|---|---|---|
| A1 | PASS | 224,955 x 42 |
| A2 | PASS | text; "224,955 ... parse as BIGINT, but ... have leading zeros a number would drop -- a code"; no conversion offered |
| A3 | PASS | "read as numbers once the currency sign and thousands separators are removed"; C003 offered |
| A4 | PASS | 120 duplicates; key line_id verified after C001 |
| A5 | PARTIAL | "rating ('NA' 8,069, '-' 5,353)" said; 'unknown' 3,471 said; the 67,417 Store blanks still not called structural |
| A6 | PASS | 98.1% DATE, 3,030 did not, dd/mm examples; the cast is marked as losing them |
| A7 | PASS | 2024-09, longest gap 1 |
| B1-B4 | PASS | 8 (L0022845 ...), 13, 37, 0 |
| C1 | PASS | 6,271,191 over 150,000 orders |
| C2 | PASS | 72,026.67 over 120 reps |
| C3 | PASS | no total: declared non-additive |
| C4 | PASS | 20,125 / 27,350 / 22,444; (all) 34,836 |
| C5 | PASS | gross_margin_pct 18.3983 |
| C6 | PASS | Apparel 0.2575, Beauty 0.127, Grocery 0.0682, Home 0.0672, Electronics 0.066 |
| D1 | PASS | exact |
| D2 | PASS | exact, (null) 20,240,461.67 |
| D3 | PASS | 180 of 500 |
| D4 | PASS | top 1% (348) 12.56%, HHI 1.35, effective 7,426.6 |
| D5 | PASS | orders: Online x UPI 28,281, total 150,000 |
| E1 | PASS | 2024-09 blank, endpoints |
| E2 | PASS | Nov 1.47, Oct 1.38, Dec 1.21; Sep 2 of 3 |
| E3 | PASS | +67.6%, "2024 holds no rows in 2024-09 (11 of its 12 months hold rows), so its total reads low" |
| E4 | PASS | exact, sums to 244,905,471.67 |
| E5 | PASS | exact ranks |
| F1 | PASS | 0.460/0.441, -0.583/-0.584, 0.910/0.864, -0.001/-0.001, pairs exact |
| F2 | PASS | courier 0.265, channel 0.228, payment 0.000 |
| F3 | PASS | rate 1,549.60, mix 1.04, interaction 0.17 |
| F4 | PASS | 0 days 4.4645 ... 8 days 2.6266 |
| G1 | PASS | within category Tukey 8,294 vs 32,467 global, "the difference is the spread between groups" |
| G2 | PASS | after 2024-12, 0.0324 -> 0.1421; 2024-08/09 excluded |
| G3 | PASS | "Both break in the same place: ... after 2024-12" |
| H1 | PASS | order level: Welch t 177.48, Store 31,632 4.4668, Online 47,293 3.5535; g 1.2209 |
| H2 | PASS | F 1,515.59 |
| H3 | PASS | "No detectable association ... not evidence they are independent" (line level: chi2 20.03) |
| H4 | PASS | chi2 13,637.85, df 4 |
| H5 | PARTIAL | mean rating per order 3.8283 [3.823, 3.8336] exact; the share is of lines (13.1%), not orders with any return (18.5%) |
| H6 | PASS | d 0.0204 (key 0.0203), no observed power |
| I1 | PASS | grid exact; order_id refused as a key |
| I2 | PASS | 82.096%, busiest 633; median consecutive gap 86 (key 85: day boundaries against a floored timedelta) |
| J1 | PASS | rep_exit_date count 30 over 120 reps |
| J2 | PASS | exact per department |
| J3 | PARTIAL | r 0.357 over 120 reps; the within-department regression (~3,773 per point) is not an analysis here |
| J4 | GAP | tenure needs a derived column (Phase 15) |
| J5 | PASS | exact |
| K1-K3 | GAP | named refusals -- the key's pass for K |
| L1 | PASS | "309.0 MB, over the 250.0 MB warning threshold (files over 2.5 GB are refused)" |
| L2 | PASS | "2.6 GB, over the 2.5 GB limit" |
| L3 | PASS | "within limits" |

Totals: PASS 46, PARTIAL 3, FAIL 0, GAP 4 (of 53) -- from 25 / 9 / 8 / 11 before Steps 12-15.
As predicted, after 2.1; the first run of this step had I1 failing.

Still open, recorded in decisions.md: an order-level flag from line values ("any line returned",
H5); the structural blanks a profile could name (A5); regression and forecasting (J3, K, Phase 16);
derived dates (J4, Phase 15).

MEASURED VALIDATION line: docs/decisions.md, section Cleanup Step 16.
