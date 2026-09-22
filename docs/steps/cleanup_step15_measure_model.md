# Cleanup Step 15: a measure can belong to a coarser unit, be a ratio of sums, or read another column

Fourth fix step from the retail run, and the one most failures came from. Closes RF-O1 (C1, C2, C5,
J2, J3, H1-H5) and the G3, C6 and J1 findings.

## What was established before this document

- `none` stops a total and leaves a mean, and the mean of an order-level, rep-level or ratio column
  is the key's trap: C2 71,692.20 (per rep 72,026.67), C5 25.79% (ratio of sums 18.40%), J2, J3;
  and the tests of H1-H5 run on lines, where an order's rating repeats.
- A measure is its column: one aggregate per column, so "units per line" cannot be asked while units
  sums (G3); a BOOLEAN cannot be averaged at all.
- Every aggregate site has one shape, `AGG_SQL[agg].format(col=quote_identifier(name))` (11 sites);
  46 sites read the table as quote_identifier(scope.dataset_name).
- Measured (this step's first command): DuckDB refuses avg, stddev_samp and quantile_cont on
  BOOLEAN; sum and count work; CAST(b AS INTEGER) averages; SELECT * REPLACE keeps column order.

## The design

A. Measure gains `column` (the source column; default its own name), `per` (the columns whose value
   it is -- one value per order_id, per rep_id), and agg `ratio` with `numerator` and `denominator`
   (signed column lists, "-line_cost") and `scale`.
B. The scope reads a RELATION, not the table: `(SELECT * REPLACE (...), extras FROM t) AS t`, built
   once from the contract -- a BOOLEAN measure cast to INTEGER; an aliased measure as its own
   column; a ratio as STRUCT(n, d) with the scale in n. AGG_SQL['ratio'] is
   `sum({col}.n) / nullif(sum({col}.d), 0)`, so a ratio works wherever an aggregate does and nowhere
   a row value is needed. Scope.source replaces quote_identifier(scope.dataset_name) everywhere.
C. A call whose measure (or against) has `per` runs over one row per unit: the relation reduced to
   SELECT DISTINCT per, the measure(s), and the call's columns, in registry.narrowed as period and
   groups are. If a column the call needs varies within the unit, the call is refused naming it
   ("category varies within rep_id") -- counting a rep in several groups is the trap in another
   form. summary_stats computes a per-measure over its own units; driver_analysis ranks only the
   dimensions constant within the unit and names the rest.
D. At proposal, a `per` measure is verified constant within its unit, as a stated key is verified.

## Commands

1. Ground facts, tests/test_measure_model_facts.py: BOOLEAN aggregation; STRUCT field access inside
   sum; REPLACE order; DISTINCT over a unit. Expected as measured in the probe.
2. Baseline 1925. 3. Falsify: tests/test_measure_model.py. Expected all fail.
4. Apply. Expected 1925 + new, the facts included.
5. Live, retail, a contract with: order_shipping_fee sum per order_id; rep_monthly_salary mean per
   rep_id; rep_performance_rating mean per rep_id; rating mean per order_id; gross_margin_pct ratio
   (line_revenue - line_cost) / line_revenue x 100; returned_rate = is_returned, mean;
   units_per_line = units, mean; rep_exit_date count per rep_id. Expected: C1 6,271,191.00; C2
   72,026.67 over 120; C5 18.40; C6 Apparel 0.2575 ... Electronics 0.0660; G3 both at 2025-01; H1
   order level t 177.48 (Store 31,632, Online 47,293); H2 F 1,515.59; H5 3.8283 [3.8230, 3.8336];
   H6 d 0.0203; J1 30 of 120; J2 E-commerce 69,264.29 ... Key Accounts 110,760.00; J3 r 0.3572; and
   salary by category refused naming the variation.
6. Acceptance, eval, UI. 7. Records, commit.

## Results

1. Ground facts. tests/test_measure_model_facts.py `7 passed`: avg and stddev_samp on BOOLEAN raise
   BinderException; sum 2 and count 3; avg(CAST AS INTEGER) 2/3; REPLACE keeps order; a struct's
   fields sum inside an aggregate and divide to the ratio of sums (a 1000/3, b 1000/7); sum skips a
   NULL field; DISTINCT over a unit is 2 rows when constant and 3 when the value varies.
2. Baseline 1925.
3. Falsify. tests/test_measure_model.py: `1 failed, 10 errors` (setup: propose did not take the new
   answers). As expected.
4. Apply.
   4.1. The first test run took over 300 s and was stopped; its output showed the contract
        confirming and summary_stats failing on "returned_rate not found" -- the expected failure,
        slow only because ten tests each failed through the same setup.
   4.2. My mechanical switch to scope.source also rewrote relation_types' own fallback into a call
        to itself, and added `from .base import relation_types` to base.py -- a circular import.
        Both undone by hand; the switch is otherwise 46 sites in 28 files, listed by the script.
   4.3. test_scope.py's stand-in contract has no `measures`; measure_relation reads them with
        getattr, as nothing about a scope needs measures.
   Suite `1943 passed` (1925 + 11 + 7 facts).
5. Live, retail, contract with grains declared (per order_id: shipping fee, rating, delivery days,
   session seconds, pages; per rep_id: salary, performance, exit date; ratio gross_margin_pct;
   returned_rate over is_returned; units_per_line over units). The contract confirmed: every per
   measure verified constant within its unit on 224,835 rows.
     C1  order_shipping_fee sum 6,271,191 over 150,000 orders            key 6,271,191.00
     C2  rep_monthly_salary mean 72,026.6667 over 120                    key 72,026.67
     C5  gross_margin_pct 18.3983                                        key 18.40%
     C6  returned_rate Apparel 0.2575, Beauty 0.127, Electronics 0.066   key 25.75 / 12.70 / 6.60%
     G3  "Both break in the same place: discount_pct after 2024-12 and units_per_line after
         2024-12"                                                        key both at 2025-01
     H1  Welch t -177.4822; Online 47,293 3.5535, Store 31,632 4.4668    key 177.482, same n/means
     H2  F 1,515.5894                                                    key 1,515.59
     H5  3.8283 [3.823, 3.8336], n 105,089                               key identical
     H6  d 0.0204                                                        key 0.0203
     J1  rep_exit_date count 30, nulls 90 (120 reps)                     key 30 of 120
     J2  E-commerce 69,264.29, Key Accounts 110,760, (all) 72,026.67     key identical
     J3  r +0.357 over 120 rep_id units                                  key 0.3572
     salary by category: "category varies within rep_id: 120 rep_id unit(s) hold more than one
     category" -- refused, as designed.
   H6 differs in the fourth decimal (0.0204 against 0.0203); recorded, not adjusted. With rating
   declared per order, F1, F2 and F4 move to order level too -- the key computed those on lines;
   a contract without `per` on rating reproduces its line-level figures (the retail run's).
6. Acceptance 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0; eval 76/76; UI 37. As expected.

MEASURED VALIDATION line and digests: docs/decisions.md, section Cleanup Step 15.
