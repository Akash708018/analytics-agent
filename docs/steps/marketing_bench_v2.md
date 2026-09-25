# Marketing bench, second round: funnels, subscriptions, experiments, claims, coupons (25/09/2026)

Asked for: "make it more complex, use a different aspect of marketing data".
`scripts/marketing_bench_v2.py` (floor: `tests/test_marketing_bench_v2.py`) builds six tables --
a CRM funnel with stage timestamps, monthly SaaS subscriptions, A/B-test exposures, platform-
reported conversions, coupon rows on orders in three currencies, and daily search rankings -- and
runs five of them end to end through server.py against SQL written in the script.

## First run, before any change (docs/benchmark/suggest_bench/marketing_v2_before.json)

    strong 14: 11 right, 3 wrong (78.6%); likely 9: 4 right, 5 wrong
    caveats: 14.3% of expected found
    filter, sum everything: 10 right -> 13 right, 7 wrong AND marked checked
    end to end: coupon fan-out de-duplicated exactly (a naive sum is up to 2.1x); the claimed
      total de-duplicated exactly (the claims sum 1.23x); a total of MRR refused. New MRR per plan
      wrong; the currency and contamination caveats absent from the replies.

Found, by cause:

1. MRR flows read as the level: new, expansion, contraction and churned MRR matched "mrr" (S1,
   none), and the filter blocked their correct sums.
2. order_revenue_local summed across INR, USD and AED.
3. discount_usd read as a rate ("discount"); discount_pct "one value per coupon_code" -- the role
   rules call any *_code an identifier, and a three-value code became a unit.
4. No caveat for: MQL dates before the lead existed; a deal amount on lost deals; users in both
   variants; orders claimed by several platforms; mixed currencies; dates in 2031 -- which also
   stretched the span and named 69 empty months.
5. Bench errors: conversion value per platform used the per-conversion measure, which the engine
   refuses by platform -- rightly, an order claimed twice would count in both; the result file's
   4-place rounding against a 1e-6 tolerance; CAC's label (one value per account is the right
   unit: counted per row it weights long-lived accounts).

## Changes

- `contract/suggest.py`: S2 -- a level's movement (new, expansion, contraction, churned, gained,
  lost...) adds; seats and licences are levels; C1 -- money beside a currency column with several
  codes, not named converted, is not summed; currency codes mark money; "discount" alone is not a
  rate; a code is not a unit unless it has more than 20 values; the ratio search ignores rows where
  the column is 0 (churned_mrr, 0 in 98% of rows, "equalled" contraction / anything) and never
  divides by a 0/1 flag (mrr / is_churned = mrr wherever the flag is 1), and does not re-read a
  column already read as adding up (expansion_mrr = mrr / seats here, and is still a flow).
- `contract/llm_filter.py`: C1 blocks a sum.
- `contract/measured_caveats.py`: M10 an event's identifier (at most 3 rows each, named as an
  identifier) under more than one value of a filled-in text category, for at most 30% of its
  values; M11 dates after today (and empty months stop at today); M12 mixed currencies (not for a
  percentage); M13 two dates in the order one always follows the other, except in at most 1% of
  rows; M14 a column blank in every row of one value but a few (a deal amount on a lost deal).
  The list is ordered by what makes a number wrong first, small unexplained blanks before large
  or explained ones; an explanation prefers a value to NULL and text to numbers, sorted rather than
  in the order the database returns groups; the overflow note says honestly what was left out.

Found on the way, by the earlier benches: M10 first counted against "values that repeat" (all
151 split users were all of them, so it said nothing), then flagged a time-varying 0/1 flag and
customers meeting several campaigns (noise); the severity order first pushed retail's
customer_state (3,473 blank -- the count this session began with) past the cap; the NULL
explanation was chosen by row order, and the bench's own recount wrote `= NULL`.

## Final run

    strong 14: 14 right; likely 10: 10 right; strong coverage 58.3% (the flows are "likely")
    caveats: 100% of expected found; 10 of 10 lines recounted apart held
    filter, sum everything: 10 right / 14 wrong -> 21 right / 3 wrong, 0 wrong marked checked
    filter, live gpt-oss-120b: 19 right / 4 wrong / 1 blank -> 23 right / 0 wrong / 1 blank
    end to end: 19 of 19 figures equal SQL -- revenue per channel once per order, value per
      platform as claimed, the de-duplicated total, conversion rate per variant, win rate per
      channel, new MRR per plan; a total of MRR refused; conversion value per platform refused;
      the currency, split and contamination caveats in the replies

The live model's two mistakes are the classic ones -- MRR summed across months, and
order_revenue_local summed across currencies -- and the filter overruled both. It read the
per-unit structure well this time (CAC and LTV per account, conversion value per conversion).

On the retail fixture the new rules now write two of the caveats the user typed on 25/09/2026:
"rep_exit_date is before order_ts in 112 row(s)" and "order_id falls under more than one
rep_manager_id for 24 value(s)".

## Checks

    uv run pytest -q                      # 2168 passed, 1 skipped
    uv run --group ui pytest ui/tests     # 53 passed
    phases 8-12                           # 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0
    uv run python eval/run_eval.py        # SCORE: 76/76 (100%)
    scripts/suggest_bench.py, scripts/marketing_bench.py -- exit 0, unchanged

## Not covered

MRR over time needs a last-value aggregation (sum across accounts at each month's end): the
engine refuses the total rather than give a wrong one. Sample-ratio mismatch in the experiment
needs the intended split, which is a declaration. Attribution windows, time zones and a
currency's rate on the day are not in any table here.
