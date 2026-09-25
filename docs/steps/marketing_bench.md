# Marketing data: the suggestions, the engine's caveats, the model filter and the numbers (25/09/2026)

Asked for: "more complex tests, specifically related to marketing data". `scripts/marketing_bench.py`
(floor: `tests/test_marketing_bench.py`) builds five tables with the traps marketing data carries --
derived ratios beside their counts (CTR, CPC, CPM, ROAS, conversion rate, frequency), distinct
counts that look additive (reach), a budget per campaign repeated per ad group and day, fractional
attribution credit, a follower level on a date, Google Analytics' own missing markers -- and runs
ad_daily end to end through server.py against SQL written in the script.

## First run, before any change (docs/benchmark/suggest_bench/marketing_before.json)

    strong 19: 17 right, 2 wrong (89.5%); strong coverage 54.3%; 10 of 35 measures unsure
    caveats: 66.7% of expected found -- '(not set)' and '(not provided)' missed
    filter, a model that sums everything: 17 right -> 26 right; 3 wrong AND marked checked
    end to end: 12 of 12 per-channel figures equal SQL; a total of ctr_pct refused

What it found, by cause:

1. The lexicon was retail's: conversions, delivered, opens, likes, posts, unsubscribes and
   transactions were unsure; cpm, reach and followers were not read at all.
2. bid_amount: sum per ad group, strong -- "amount" made a bid additive.
3. Attribution credit: a fraction in [0, 1], read as a rate (N3) and hard-blocked from a sum; the
   filter overruled a model's correct "sum" to "none". Its sum counts conversions.
4. '(not set)' and '(not provided)' -- Google Analytics' words for missing -- were not placeholders.
5. CPM (spend / impressions x 1000) matched no ratio form.
6. Clicks above impressions (a CTR over 100%) were not said.
7. Bench errors: the GA generator made session length and pageviews constant per user by accident
   (the engine's "per user" was true of the data); bid_amount is per ad group by construction and
   its label said otherwise; the verifier probe quoted a mean-of-rows CTR equal to the ratio of sums
   at two places, so there was nothing to catch.

## Changes

- `contract/suggest.py`: ratio and price words (rate, pct, ctr, cvr, cpc, cpm, cpa, roas, roi, aov,
  arpu, frequency, bid, ...) override amount words; marketing counts added to the additive words;
  U1 (reach, uniques, DAU/MAU, audience: none); followers, subscribers, list size as snapshots; the
  per-mille ratio form (CPM); A2 -- a fraction that sums to 1 within each value of a repeating
  identifier is credit, and adds (strong, measured); a fraction named as credit, likely.
- `contract/llm_filter.py`: N3 (a bare fraction) no longer blocks a sum -- evidence too weak to
  overrule; A2 overrules a model's none/mean on credit.
- `contract/measured_caveats.py`: '(not set)', 'not set', '(not provided)', 'not provided',
  '(unknown)' are placeholders ('(direct)', '(none)', '(other)' are real GA values and are not);
  M9 -- a rate above 100 (or a fraction above 1) where every other value is not.
- The ratio search screens pairs in Python on 64 rows before counting survivors in SQL: ad_daily
  took 7.81 s with every pair in SQL, 0.85 s screened, same results.

## Final run

    strong 28: 28 right, 0 wrong; strong coverage 80.0%; 1 unsure (pageviews)
    caveats: 100% of expected found; 9 of 9 lines recounted apart held
    filter, sum everything: 17 right / 18 wrong -> 33 right / 2 wrong, 0 wrong marked checked
    filter, live gpt-oss-120b: 20 right / 9 wrong / 6 blank -> 30 right / 0 wrong / 5 blank
    end to end: 12 of 12 per-channel CTR, ROAS and spend equal SQL; a total of ctr_pct refused;
      google ROAS 3.654 from sums vs 4.283 as a mean of rows (17% high); the verifier names 4.28
    the earlier bench (scripts/suggest_bench.py): unchanged, 29 of 29 strong right

The live model read the marketing ratios well (none on CTR, CPC, CPM, ROAS, reach, frequency) and
the per-unit structure badly: it put credit and attributed_value "per conversion_id" (both vary
within one) and called conversion_value "none" (it is one value per conversion, summed once each).
The data filter corrected all three. Its raw "wrong" on the ratios is partly the grading: the
model's answer has no field for a ratio of sums, which the filter adds.

One label was changed after seeing a result, and is said here: followers (and the earlier
bench's closing_balance) now accept mean as well as none. An average level is a standard figure
(average daily balance); the trap is the sum.

## Checks

    uv run pytest -q                      # 2161 passed, 1 skipped
    uv run --group ui pytest ui/tests     # 53 passed
    phases 8-12                           # 99/0/2, 19/0/0, 35/0/1, 26/0/0, 36/0/0
    uv run python eval/run_eval.py        # SCORE: 76/76 (100%)

## Not covered

Cross-column rules beyond "a rate over 100%" (conversions above clicks, spend without impressions),
currency mixing, time zones, attribution windows, and platform-reported conversions that overlap
across channels -- each needs a declared rule (the contract's `expectations`), not a count.
