# Phase 11 Step 4 - the acceptance script, and closing P11-O1

21/09/2026. Baseline b651915. Measured before starting: 1712 passed; test_phase8.py 99/0/2;
test_phase9.py 19/0/0; test_phase10.py 35/0/1.

This document is written before anything runs, which C84 records the previous step failing to do.

## What P11-O1 says, and what already exists

P11-O1: no acceptance script calls a Tier 3 to 7 analysis through the registered MCP tool. That
is why three green acceptance runs and 1,698 unit tests said nothing while eight analyses were
unreachable (C83).

tests/test_phase8.py clause four already calls `server.compute_analysis` directly -- P8-D76 -- and
proves that `column`, `dimension`, `measure`, `n` and the four period dates arrive under the right
names. It exercises Phase 8's nine, which take none of the nine parameters C83 named. So the
mechanism exists and the coverage does not.

## What this step builds

`tests/test_phase11.py`, the Phase 11 acceptance script, with three clauses:

1. Every parameter C83 named reaches its analysis through `server.compute_analysis`:
   `against`, `period`, `baseline`, `entity`, `second_dimension`, `method`, `confidence`,
   `alpha`, `power`.
2. All eight chart kinds through `server.render_chart`.
3. Rule 4 holds on a real chart: the file exists, begins with the PNG magic number, and the
   reply describes what is in it rather than naming it.

On the `clean_sales` CSV fixture, not Olist, so the script runs without Postgres. Its contract
declares measures revenue (sum), units (sum) and unit_price (none), dimensions region, channel
and product, and `order_date`, which is enough to reach every tier.

## Predictions

Written down before the run. The ones I would bet least on are 4, 9 and 10.

1. `correlation(measure="revenue", against="units")` passes, and would have refused before
   c1826b2 with ANALYSIS_PARAMS_INVALID.
2. `period_compare(measure="revenue", period=..., baseline=..., grain="month")` passes.
3. `growth_decomposition(measure="revenue", dimension="region", period, baseline, grain)` passes.
4. `repeat_behaviour(entity="region")` passes. Region has few values and is not distinct per
   row, which is the shape that analysis refuses.
5. `hypothesis_test(dimension="region", measure="revenue", method="auto")` passes.
6. `confidence_interval(measure="revenue", confidence=0.99)` passes, and "99%" appears.
7. `sample_adequacy(dimension="region", measure="revenue", power=0.8, alpha=0.05)` passes.
8. `effect_size(dimension="region", second_dimension="channel")` passes.
9. Of the eight chart kinds, the ones drawn from a single-measure result (bar on frequency,
   histogram on distribution, waterfall on growth_decomposition) render without `y`; the ones
   drawn from a multi-measure result (box and heatmap on summary_stats, grouped_bar and scatter
   on cross_tab or correlation) render without `y` too; and `line` needs `y` named on whatever
   it is pointed at. I expect at least one of these eight to be wrong.
10. Every rendered chart's file exists and starts with the PNG magic number, and the reply
    contains "You cannot see this image".

## Commands

1. Write tests/test_phase11.py. Expected: compiles.
2. Run it. Expected: the clauses above, with any wrong prediction recorded as wrong.
3. Record as P11-D23 onward; close P11-O1; update the guide's row 11 and CLAUDE.md.
4. All four checks, then commit.

## Outputs

**First run: 25 passed, 1 failed.** Prediction 4 was wrong. growth_decomposition failed, and not
with the parameter error this clause was built to catch:

    FAIL  period and baseline reach growth_decomposition
          (BLOCKED: the analysis produced a result that does not describe itself.)

Underneath it, a LostRows that refutes itself:

    growth_decomposition does not reconcile: the 5 member(s) of region contribute
    -1,539.88 against a change of -1,539.88 between 2024-01 and 2024-10.

The two numbers are identical on the page. `sum(contributions.values(), zero) != change` is
exact equality with both sides printed through number(), which rounds to four places. Exact is
right for DECIMAL and integer measures and wrong for every DOUBLE one -- measured,
`sum(revenue)` over the 500-row fixture is 1377896.8399999999. mix_shift already compared a
residual against a relative tolerance; growth_decomposition did not. Fixed, and the tolerance
now lives in base.py where both read it. C85 and P11-D23.

**Prediction 9 was wrong too, harmlessly.** It hedged that at least one of the eight chart kinds
would fail. All eight rendered first time. The hedge found nothing; the specific prediction found
a bug two phases old.

**Second run: 26 passed, 0 failed, 0 skipped.** All ten forwarding rows, all eight kinds, and
the eight Rule 4 checks on a real PNG (21,005 bytes, in workspace/<id>/charts/).

**Final.** Full suite 1712 -> 1714. Acceptance is four scripts now: 99/0/2, 19/0/0, 35/0/1,
26/0/0. P11-O1 closed.
