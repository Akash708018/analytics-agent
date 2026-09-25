# The engine suggests the contract; a person confirms it (25/09/2026)

Asked for after a review of how frontier tools settle aggregation: none of them fully automate it.
Chat tools re-guess every conversation; the accurate ones (Cortex Analyst, Genie, Pulse) get their
accuracy from a semantic layer someone approves; Power BI's Copilot summed temperatures because
its default was Sum. The design adopted: **the engine suggests and explains, a person confirms with
one click, and it asks only where the evidence is weak.** `Measure.agg` keeps no default.

Four parts, in the order they were proposed:

1. **Caveats the engine writes** (`contract/measured_caveats.py`, rules M1-M6): placeholders,
   blanks (grouped when they fall in the same rows, and explained by a dimension or flag value
   when they are exactly its rows), a few negatives, text dates in two formats, empty months,
   subtotal words. Stored as `DatasetContract.measured_caveats`, counted at proposal and again at
   confirmation (the payload's copy is discarded), printed on every result as "Measured when the
   contract was confirmed: ...". The person's own caveats stay, printed as declared.
2. **A suggested aggregation per measure with its reason** (`contract/suggest.py`, rules P1, R1,
   N1-N3, S1, D1, A1), strong / likely / unsure. Never applied by drafting: `unresolved` still
   holds every blank `agg`. The proposal text lists them with the answers to pass back; each open
   measure's question carries the suggestion or a plain question; a stated aggregation the engine
   reads otherwise on strong evidence is noted, not refused. The Contract screen shows each
   reading under its field, fills the strong ones on the person's click only, adds a "one value
   per" field (`measure_per`), and offers a detected ratio as a ratio-of-sums measure to tick.
3. **Snapshot columns** (S1): named like a balance or a stock level, suggested `none` as likely,
   saying why. A last-value aggregation is NOT built: it has to sum each entity's latest value
   inside every period an analysis groups by, which no single aggregate expression over AGG_SQL's
   shape can do; it is a change to the analyses' SQL, not to the contract, and a separate step.
4. **A bench** (`scripts/suggest_bench.py`, floor `tests/test_suggest_bench.py`).

## Measured

- Retail fixture (224,955 rows), the contract proposal: engine caveats say 'unknown' 3,471,
  customer_state blank 3,473, units below zero in 8, delivery_date 3,030 in another format,
  order_ts empty in 2024-09, and "courier, delivery_date, web_session_seconds and pages_viewed
  are blank in the same 67,417 row(s) -- exactly the rows where channel = 'Store'". Every count
  the review verified by hand, now produced without typing.
- Suggestions on retail: margin_pct = (line_revenue - line_cost) / line_revenue x 100 on 100.0%
  of 5,000 sampled rows (R1, with margin_pct_of_sums offered); order_shipping_fee sum per order_id,
  rep_monthly_salary mean per rep_id, web_session_seconds mean per order_id (P1); unit_price none
  (N2); line_revenue, line_cost sum (A1); stock_on_hand_at_order none, likely (S1).
- Cost: per-unit detection first used count(DISTINCT (id, m)) per measure, 3.93 s on retail;
  rewritten as one grouped min/max scan per identifier, 0.33 s, same results. Engine caveats first
  4.82 s (casting every text column to DATE was 4.72 s); a 2,000-row sample screen and one merged
  text scan, 0.77 s, same lines.
- Browser, real backend, retail with no contract: "Use the engine's 9 strong suggestion(s)" filled
  nine aggregations and their units; stock_on_hand_at_order stayed blank with its question;
  margin_pct_of_sums ticked went through "Check what's missing" with no exception and is not
  among the fields still needed (its definition is the formula).

## The bench

    uv run python scripts/suggest_bench.py --json docs/benchmark/suggest_bench/results.json

Four built datasets (6,000 rows each: shop lines, daily account balances, a clean payroll, places)
and the retail fixture; 30 labelled measures. Final run:

    strong   23: 23 right, 0 wrong, 0 no suggestion
    likely    5: 5 right, 0 wrong, 0 no suggestion
    unsure    2: 0 right, 0 wrong, 2 no suggestion
    strong precision 100.0%   likely precision 100.0%   strong coverage of labelled measures 79.3%
    caveats: 100.0% of expected found (missed none); every line recounted apart: 21 of 21 held,
             refuted none; false alarms on the clean table 0
    metamorphic (all four): shuffle=True, renamed columns keep every value rule and make no strong
             suggestion wrong, duplicated rows keep every unit, an appended 'Total' row is caught

What the bench found on its first runs, in order:

1. Renaming columns to c1..cn kept 0 of 4 value-based readings: the unit rule looked only at
   columns named like identifiers, and the ratio rule ran only after a name rule fired. Fixed: a
   text column with over 20 values may be a unit; the ratio search runs for every measure not
   settled as an amount, a unit's value or a code.
2. That exposed two more on the renamed table: quantity = line_amount / unit_price exactly, so the
   ratio rule called a count a rate (fixed: never for a whole-number column); and a renamed fee was
   "mean per order, strong" -- the unit is measured, but sum-or-mean is only in the name (fixed:
   without a name that says, P1 is likely, with its own question).
3. Bench errors, not engine errors: hours_worked was built constant per employee by accident (the
   engine's "per employee" was true of the data); the totals row's LIMIT 1 applied to the whole
   UNION; an abstention was graded as wrong; the renamed ratio label kept the old names.
4. Not fixed, on purpose: `deposits` gets no suggestion (the word is not in the lexicon). Adding the
   words a bench misses is fitting the bench; it stays a measured coverage gap.

The 9 caveat lines outside the expected lists (retail's blanks in rep_exit_date, return_reason
"exactly where is_returned = false", campaign_code, review_text, rating; negative line_revenue and
line_cost) all recounted true.

## Checks

    uv run pytest -q                      # 2139 passed, 1 skipped
    uv run --group ui pytest ui/tests     # 53 passed
    uv run python tests/test_phase8.py    # 99 passed, 0 failed, 2 skipped
    uv run python tests/test_phase9.py    # 19 passed, 0 failed, 0 skipped
    uv run python tests/test_phase10.py   # 35 passed, 0 failed, 1 skipped
    uv run python tests/test_phase11.py   # 26 passed, 0 failed, 0 skipped
    uv run python tests/test_phase12.py   # 36 passed, 0 failed, 0 skipped
    uv run python eval/run_eval.py        # SCORE: 76/76 (100%)

## Limits

- The bench is small and built here: labels are known by construction, so it measures the rules
  against the traps they were written for. A public-dataset set (50-100 tables) is the next
  measurement; nothing here claims a precision beyond these 30 measures.
- Engine caveats are counted when the contract is confirmed; a table cleaned afterwards drifts, and
  the drift caveat says so, but the counts are not retaken until the contract is confirmed again.
- A proposal on retail does about 1.1 s more work (caveats 0.77 s, suggestions 0.33 s); not cached.
